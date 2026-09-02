#!/usr/bin/env python3
"""
qa_report.py — batch QA + contact sheets so 105 clips can be reviewed in minutes.

1. Validates every clip in the output dir against the job DB (flagged/failed
   clips are listed with their reasons).
2. Builds a tiled contact sheet (middle frame of every clip, labeled) so you
   can eyeball the whole batch in one image.
3. Checks cross-clip luminance drift (flicker between adjacent clips).

Usage: python3 qa_report.py --out clips/ [--sheet contact.png]
"""
import argparse, glob, json, os, sqlite3, sys
import cv2
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="clips")
    ap.add_argument("--sheet", default="contact_sheet.png")
    ap.add_argument("--cols", type=int, default=7)
    ap.add_argument("--thumb", type=int, default=240, help="thumbnail width px")
    ap.add_argument("--max-luma-drift", type=float, default=12.0,
                    help="max allowed mean-luminance jump between adjacent clips (0-255)")
    args = ap.parse_args()

    db = sqlite3.connect(os.path.join(args.out, "_jobs.sqlite"))
    rows = db.execute("SELECT clip_id, state, qa_json, error FROM clips ORDER BY clip_id").fetchall()

    print("== clip states ==")
    problems = []
    for cid, state, qa_json, err in rows:
        if state == "done":
            print(f"  ok      {cid}")
        elif state == "flagged":
            reasons = json.loads(qa_json)["qa_reasons"]
            problems.append(cid)
            for r in reasons: print(f"  FLAG    {cid}: {r}")
        else:
            problems.append(cid)
            print(f"  {state.upper():7} {cid}: {err}")

    # middle-frame thumbnails for the contact sheet
    thumbs, labels = [], []
    for cid, state, _, _ in rows:
        p = os.path.join(args.out, cid + ".mp4")
        if not os.path.exists(p): continue
        cap = cv2.VideoCapture(p)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, n // 2)
        ok, fr = cap.read(); cap.release()
        if not ok: continue
        h, w = fr.shape[:2]
        th = cv2.resize(fr, (args.thumb, int(args.thumb * h / w)))
        col = (0, 200, 0) if state == "done" else (0, 0, 255)
        cv2.rectangle(th, (0, 0), (th.shape[1], 18), (0, 0, 0), -1)
        cv2.putText(th, f"{cid} [{state}]", (3, 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)
        thumbs.append(th); labels.append(cid)

    if thumbs:
        tw, thh = args.thumb, max(t.shape[0] for t in thumbs)
        rows_n = (len(thumbs) + args.cols - 1) // args.cols
        sheet = np.full((rows_n * thh, args.cols * tw, 3), 30, np.uint8)
        for i, t in enumerate(thumbs):
            r, c = divmod(i, args.cols)
            sheet[r*thh:r*thh+t.shape[0], c*tw:(c+1)*tw] = t
        cv2.imwrite(args.sheet, sheet)
        print(f"\ncontact sheet -> {args.sheet}  ({len(thumbs)} clips, one glance)")

    # cross-clip luminance drift (adjacent in pairs.csv order = adjacent in film)
    lumas = []
    for cid, state, _, _ in rows:
        p = os.path.join(args.out, cid + ".mp4")
        if not os.path.exists(p): continue
        cap = cv2.VideoCapture(p)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0); _, first = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n - 1)); _, last = cap.read()
        cap.release()
        if first is not None and last is not None:
            lumas.append((cid, float(np.mean(last)), float(np.mean(first))))
    print("\n== cross-clip luminance drift (end of N vs start of N+1) ==")
    drift_bad = 0
    for (c1, end1, _), (c2, _, start2) in zip(lumas, lumas[1:]):
        d = abs(end1 - start2)
        mark = "  <-- FLICKER RISK" if d > args.max_luma_drift else ""
        if d > args.max_luma_drift: drift_bad += 1
        print(f"  {c1} -> {c2}: Δ {d:.1f}{mark}")

    print(f"\n== QA summary: {len(problems)} problem clip(s), {drift_bad} flicker-risk boundary(ies) ==")
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
