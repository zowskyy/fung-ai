# No Sand Beach — Interpolation Toolkit

Built and tested end-to-end on synthetic B&W expressionistic keyframes. Requires only **Python + OpenCV + ffmpeg** on your machine (all free, all local — no GPU, no cloud, no accounts).

## Files

| File | What it does |
|---|---|
| `interpolate_stack.py` | Checkpointed batch renderer: keyframe pairs → video clips. Resume-after-crash built in. |
| `qa_report.py` | Batch QA + labeled contact sheet (review 105 clips in one image) + cross-clip flicker check |
| `coherence_pass.sh` | Batch B&W grade: histogram-matches clips to the batch median (kills boundary flicker), grain, vignette |

## Workflow

```bash
# 1. list your keyframe pairs
#    pairs.csv:  clip_id,frameA.png,frameB.png,frames[,backend]
#    frames = in-betweens to synthesize (10 ≈ 0.5s at 24fps)

# 2. day-1 test: put your 3 WORST-CASE pairs (biggest motion) in a small csv first
python3 interpolate_stack.py --pairs worst_case.csv --out clips_test

# 3. full overnight batch — if it dies at 3am, run the SAME command again;
#    completed clips are skipped, the interrupted clip restarts
python3 interpolate_stack.py --pairs pairs.csv --out clips

# 4. morning: one-glance QA
python3 qa_report.py --out clips --sheet contact.png
#    exit code != 0 if any clip is flagged/failed; reasons printed per clip

# 5. flagged clips → retry with RIFE (once rife-ncnn-vulkan binary is on PATH):
python3 interpolate_stack.py --pairs pairs.csv --out clips \
    --rife-bin /path/to/rife-ncnn-vulkan --only-flagged-retry-with rife

# 6. grade + de-flicker
bash coherence_pass.sh clips/ graded/

# 7. assemble (plain ffmpeg concat; audio mux as usual)
```

## The QA gate (honest blocking, per clip)

| Flag | Meaning | Fix |
|---|---|---|
| `large_motion` | Peak mean flow > 12px — too much motion for optical flow | route clip to `rife`, or add intermediate keyframes |
| `flow_inconsistent` | Forward/backward flow disagreement — occlusion or flat texture | route to `rife`; RIFE handles occlusion properly |
| `blank_frame` | Near-black in-betweens — warp collapse | inspect pair; usually a bad keyframe |

Thresholds are CLI flags (`--max-flow` etc.) — tune them on YOUR day-1 worst-case test, not on my synthetic defaults.

## Verified behavior (test evidence from build)

- 4-pair batch: 3 clean clips rendered, worst-case pair **flagged with reason, not shipped** ✅
- Rerun: completed clips skip with zero re-render; flagged clip retries ✅
- Real `kill -9` at 4s into a 12-clip batch: DB showed `running` on the interrupted clip; resume skipped the 2 done, restarted the interrupted one, completed all 12 ✅
- QA report: correct per-clip states, contact sheet generated, luminance drift measured (Δ1.2–1.5, no flicker risk) ✅
- Coherence pass: all clips histogram-matched to batch median, grain+vignette applied, frame counts preserved ✅

**Not tested here:** RIFE backend (no AMD GPU in this environment) — the CLI path is wired, but first run on your 660M is its real test. Optical-flow quality on your actual art style — that's what the day-1 worst-case test is for.

## Tuning notes for your art

- B&W expressionist style helps: grain + high contrast gives Farneback texture to track. Flat black regions are where it will fail — the `flow_inconsistent` check exists for exactly that.
- If many clips flag `large_motion`: your keyframes are too far apart in motion space. Rule of thumb: keep per-pair displacement under ~10% of frame width for flow; beyond that, RIFE.
- `--fps 24` default; `frames=10` gives ~0.5 s clips. Longer holds: duplicate the end keyframe as its own pair with 0-motion rather than inflating in-betweens.
