#!/usr/bin/env bash
# coherence_pass.sh — normalize look across clips so B&W grade is consistent
# and adjacent clips don't flicker (histogram match across boundaries, then grade).
#
# Usage: bash coherence_pass.sh clips/ graded/
set -euo pipefail
IN="${1:-clips}"; OUT="${2:-graded}"
mkdir -p "$OUT"

# Pass 1: measure mean luma of every clip, compute batch median
MEDIAN=$(python3 - "$IN" <<'EOF'
import cv2, glob, numpy as np, sys
vals = []
for p in sorted(glob.glob(sys.argv[1] + "/*.mp4")):
    cap = cv2.VideoCapture(p); ok, f = cap.read(); cap.release()
    if ok: vals.append(float(np.mean(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))))
print(float(np.median(vals)) if vals else 128.0)
EOF
)
echo "batch median luma: $MEDIAN"

# Pass 2: per-clip — B&W, match brightness toward median, add grain, subtle vignette
for f in "$IN"/*.mp4; do
  base=$(basename "$f")
  LUMA=$(python3 -c "
import cv2, numpy as np
cap = cv2.VideoCapture('$f'); ok, fr = cap.read(); cap.release()
print(float(np.mean(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY))) if ok else $MEDIAN)")
  GAIN=$(python3 -c "print(max(0.5, min(2.0, $MEDIAN / max($LUMA, 1.0))))")
  ffmpeg -y -loglevel error -i "$f" -vf "\
hue=s=0,\
eq=brightness=0:contrast=1.08,lutyuv=y='clip(val*${GAIN},0,255)',\
noise=alls=6:allf=t+u,\
vignette=PI/5" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p "$OUT/$base"
  echo "graded $base (luma $LUMA -> gain $GAIN)"
done
echo "done -> $OUT"
