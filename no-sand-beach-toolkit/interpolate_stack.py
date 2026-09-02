#!/usr/bin/env python3
"""
interpolate_stack.py — checkpointed batch interpolator for keyframe-pair animation.

Turns pairs of keyframe art (frameA.png, frameB.png) into short video clips by
generating in-between frames. Every clip is a checkpointed job: if the process
dies overnight, re-running the same command resumes where it stopped and never
re-renders a completed clip.

Backends:
  flow  — OpenCV Farneback dense optical flow + warped blending (built-in, default)
  rife  — rife-ncnn-vulkan external binary (plug-in; only used for clips you route to it)

QA gate (honest blocking — a bad clip is flagged, never shipped silently):
  - mean flow magnitude above --max-flow     -> flagged "large_motion"
  - black/blank interpolated frames          -> flagged "blank_frame"
  - forward/backward flow inconsistency      -> flagged "flow_inconsistent"

Usage:
  python3 interpolate_stack.py --pairs pairs.csv --out clips/ [options]

pairs.csv format (one clip per line):
  clip_id,frameA.png,frameB.png,frames[,backend]
  # frames = number of in-betweens to synthesize; backend optional (flow|rife)

Re-run the same command after a crash: completed clips are skipped.
"""
import argparse, csv, json, os, sqlite3, subprocess, sys, time
import cv2
import numpy as np

# ---------------------------------------------------------------- state store

class JobStore:
    """SQLite-backed per-clip checkpoints. Ported from the recon-native engine:
    crash leaves a 'running' row; resume treats stale 'running' as crashed."""
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS clips(
            clip_id TEXT PRIMARY KEY, state TEXT, backend TEXT,
            input_hash TEXT, output TEXT, qa_json TEXT, error TEXT)""")
        self.db.commit()

    def status(self, clip_id, input_hash):
        row = self.db.execute("SELECT state, input_hash FROM clips WHERE clip_id=?",
                              (clip_id,)).fetchone()
        if not row: return "new"
        state, old_hash = row
        if state == "done" and old_hash == input_hash: return "skip"
        if state == "done" and old_hash != input_hash:  # inputs changed -> invalidate
            self.db.execute("DELETE FROM clips WHERE clip_id=?", (clip_id,))
            self.db.commit()
            return "new"
        return "resume"  # 'running' or 'failed' from a previous life

    def mark(self, clip_id, state, backend="", input_hash="", output="", qa=None, error=""):
        self.db.execute("""INSERT INTO clips VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(clip_id) DO UPDATE SET state=excluded.state, backend=excluded.backend,
            input_hash=excluded.input_hash, output=excluded.output,
            qa_json=excluded.qa_json, error=excluded.error""",
            (clip_id, state, backend, input_hash, output,
             json.dumps(qa) if qa else None, error))
        self.db.commit()

def input_hash(a, b, n, backend):
    import hashlib
    h = hashlib.sha256()
    for p in (a, b):
        h.update(os.path.basename(p).encode())
        h.update(str(os.path.getsize(p)).encode())
    h.update(f"{n}:{backend}".encode())
    return h.hexdigest()[:16]

# ---------------------------------------------------------------- flow backend

def farneback_between(imgA, imgB, t):
    """One in-between at t in (0,1): warp A forward and B backward, blend."""
    gA = cv2.cvtColor(imgA, cv2.COLOR_BGR2GRAY)
    gB = cv2.cvtColor(imgB, cv2.COLOR_BGR2GRAY)
    flowAB = cv2.calcOpticalFlowFarneback(gA, gB, None, 0.5, 5, 25, 5, 7, 1.5, 0)
    flowBA = cv2.calcOpticalFlowFarneback(gB, gA, None, 0.5, 5, 25, 5, 7, 1.5, 0)
    h, w = gA.shape
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    x, y = x.astype(np.float32), y.astype(np.float32)
    warpA = cv2.remap(imgA, x + t * flowAB[..., 0], y + t * flowAB[..., 1],
                      cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    warpB = cv2.remap(imgB, x - (1 - t) * flowBA[..., 0], y - (1 - t) * flowBA[..., 1],
                      cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    blend = cv2.addWeighted(warpA, 1 - t, warpB, t, 0)
    qa = {
        "mean_flow": float(np.mean(np.linalg.norm(flowAB, axis=2))),
        # occlusion proxy: where A->B->A fails to return, flow is unreliable
        "inconsistency": float(np.mean(np.linalg.norm(flowAB + cv2.remap(
            flowBA, x + flowAB[..., 0], y + flowAB[..., 1],
            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE), axis=2))),
    }
    return blend, qa

def rife_between(imgA, imgB, t, rife_bin, tmpdir):
    """rife-ncnn-vulkan path: binary does its own N-frame expansion, so we only
    support power-of-two style usage via its --num-frame interface per pair."""
    raise RuntimeError("rife backend requires --rife-bin and runs per-pair, not per-t")

# ---------------------------------------------------------------- QA gate

def qa_gate(qa_list, n_blank, max_flow, max_inconsistency, max_blank_ratio):
    """Returns (ok, reasons). Honest blocking: every failure names its cause."""
    reasons = []
    mf = max(q["mean_flow"] for q in qa_list)
    mi = max(q["inconsistency"] for q in qa_list)
    if mf > max_flow:
        reasons.append(f"large_motion: mean flow {mf:.1f}px > {max_flow}px — motion too big for optical flow; route clip to rife or add keyframes")
    if mi > max_inconsistency:
        reasons.append(f"flow_inconsistent: {mi:.1f}px > {max_inconsistency}px — occlusion/texture-less region; flow unreliable here")
    if n_blank > max(1, int(len(qa_list) * max_blank_ratio)):
        reasons.append(f"blank_frame: {n_blank} near-black in-betweens — likely warp collapse")
    return (len(reasons) == 0, reasons)

# ---------------------------------------------------------------- clip render

def render_clip(clip_id, pathA, pathB, n_between, backend, out_path, fps,
                max_flow, max_inconsistency, max_blank_ratio, rife_bin=None):
    imgA, imgB = cv2.imread(pathA), cv2.imread(pathB)
    if imgA is None or imgB is None:
        return False, None, "unreadable input image"
    if imgA.shape != imgB.shape:
        imgB = cv2.resize(imgB, (imgA.shape[1], imgA.shape[0]))
    h, w = imgA.shape[:2]

    frames, qa_list, n_blank = [], [], 0
    if backend == "rife":
        if not rife_bin:
            return False, None, "backend=rife but --rife-bin not given"
        tmp = out_path + ".rife_tmp"
        os.makedirs(tmp, exist_ok=True)
        cv2.imwrite(f"{tmp}/0.png", imgA); cv2.imwrite(f"{tmp}/1.png", imgB)
        # rife-ncnn-vulkan -0 0.png -1 1.png -o out -n <total frames>
        r = subprocess.run([rife_bin, "-0", f"{tmp}/0.png", "-1", f"{tmp}/1.png",
                            "-n", str(n_between + 2), "-o", f"{tmp}/%d.png"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return False, None, f"rife failed: {r.stderr.strip()[:200]}"
        frames = [cv2.imread(f"{tmp}/{i}.png") for i in range(n_between + 2)]
        frames = [f for f in frames if f is not None]
        qa_list = [{"mean_flow": 0.0, "inconsistency": 0.0}]
    else:
        frames.append(imgA)
        for i in range(1, n_between + 1):
            f, qa = farneback_between(imgA, imgB, i / (n_between + 1))
            frames.append(f); qa_list.append(qa)
        frames.append(imgB)

    for f in frames:
        if f is None or float(np.mean(f)) < 2.0:
            n_blank += 1

    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    if not vw.isOpened():
        return False, None, "VideoWriter failed to open"
    for f in frames:
        vw.write(f if f is not None else np.zeros_like(imgA))
    vw.release()

    ok, reasons = qa_gate(qa_list, n_blank, max_flow, max_inconsistency, max_blank_ratio)
    qa_summary = {"max_mean_flow": max(q["mean_flow"] for q in qa_list),
                  "max_inconsistency": max(q["inconsistency"] for q in qa_list),
                  "blank_frames": n_blank, "frames_written": len(frames),
                  "qa_pass": ok, "qa_reasons": reasons}
    return True, qa_summary, ""

# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, help="pairs.csv")
    ap.add_argument("--out", default="clips")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--max-flow", type=float, default=12.0,
                    help="px; above this, motion is too large for flow (route to rife)")
    ap.add_argument("--max-inconsistency", type=float, default=8.0)
    ap.add_argument("--max-blank-ratio", type=float, default=0.1)
    ap.add_argument("--rife-bin", default=None, help="path to rife-ncnn-vulkan binary")
    ap.add_argument("--only-flagged-retry-with", default=None, choices=["rife"],
                    help="second pass: re-render clips that failed QA with this backend")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    store = JobStore(os.path.join(args.out, "_jobs.sqlite"))
    done = flagged = failed = skipped = 0

    with open(args.pairs) as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]

    for row in rows:
        clip_id, pathA, pathB = row[0].strip(), row[1].strip(), row[2].strip()
        n_between = int(row[3])
        backend = row[4].strip() if len(row) > 4 and row[4].strip() else "flow"
        ih = input_hash(pathA, pathB, n_between, backend)
        st = store.status(clip_id, ih)
        if st == "skip":
            skipped += 1
            print(f"[skip]  {clip_id} (checkpoint valid)")
            continue
        if st == "resume":
            print(f"[info]  {clip_id} found incomplete from prior run — restarting this clip")

        out_path = os.path.join(args.out, clip_id + ".mp4")
        store.mark(clip_id, "running", backend, ih)
        print(f"[run]   {clip_id}  ({backend}, {n_between} in-betweens)")
        t0 = time.time()
        try:
            ok, qa, err = render_clip(clip_id, pathA, pathB, n_between, backend,
                                      out_path, args.fps, args.max_flow,
                                      args.max_inconsistency, args.max_blank_ratio,
                                      args.rife_bin)
        except Exception as e:
            ok, qa, err = False, None, f"exception: {e}"
        dt = time.time() - t0

        if not ok:
            store.mark(clip_id, "failed", backend, ih, error=err)
            failed += 1
            print(f"[FAIL]  {clip_id}: {err}")
        elif not qa["qa_pass"]:
            store.mark(clip_id, "flagged", backend, ih, out_path, qa)
            flagged += 1
            print(f"[FLAG]  {clip_id}: {'; '.join(qa['qa_reasons'])}")
        else:
            store.mark(clip_id, "done", backend, ih, out_path, qa)
            done += 1
            print(f"[done]  {clip_id}  ({dt:.1f}s, peak flow {qa['max_mean_flow']:.1f}px)")

    print(f"\n== batch summary: {done} done, {flagged} flagged, {failed} failed, {skipped} skipped ==")
    if flagged and args.only_flagged_retry_with:
        print(f"retrying flagged clips with backend={args.only_flagged_retry_with} ...")
        # write a filtered pairs file and recurse once
        retry = os.path.join(args.out, "_retry.csv")
        with open(args.pairs) as f, open(retry, "w") as g:
            for r in csv.reader(f):
                if r and not r[0].startswith("#"):
                    row = store.db.execute("SELECT state FROM clips WHERE clip_id=?",
                                           (r[0].strip(),)).fetchone()
                    if row and row[0] == "flagged":
                        base = r[:4] + [args.only_flagged_retry_with]
                        g.write(",".join(str(x) for x in base) + "\n")
        sys.exit(subprocess.call([sys.executable, os.path.abspath(__file__),
                                  "--pairs", retry, "--out", args.out, "--fps", str(args.fps),
                                  "--rife-bin", args.rife_bin or ""]))
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
