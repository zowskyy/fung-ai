#!/usr/bin/env python3
"""
Coherence pass: histogram matching + grain/vignette for cross-clip consistency.
Reads interpolated clips, normalizes luminance, applies expressionist aesthetic.
"""
import cv2
import numpy as np
import os
import sys
from pathlib import Path
import sqlite3

def get_clip_luma(video_path):
    """Extract median luminance from middle frame of video."""
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count // 2)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    # Convert to YUV, extract Y (luminance)
    yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    return np.median(yuv[:, :, 0])

def apply_histogram_match(frame, target_luma):
    """Adjust frame luminance to match target via histogram scaling."""
    yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
    current_luma = np.median(yuv[:, :, 0])

    if current_luma < 10:  # Avoid division by zero
        return frame

    # Scale luminance channel
    scale = target_luma / current_luma
    yuv[:, :, 0] = np.clip(yuv[:, :, 0] * scale, 0, 255).astype(np.uint8)

    return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

def apply_grain_vignette(frame, grain_strength=0.08, vignette_strength=0.15):
    """Add film grain and vignette for expressionist aesthetic."""
    h, w = frame.shape[:2]

    # Film grain
    grain = np.random.normal(0, grain_strength * 255, frame.shape).astype(np.int16)
    frame_grain = np.clip(frame.astype(np.int16) + grain, 0, 255).astype(np.uint8)

    # Vignette (radial fade to black)
    X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
    radius = np.sqrt(X**2 + Y**2)
    vignette = 1.0 - (radius / radius.max()) * vignette_strength
    vignette = np.clip(vignette, 0, 1)

    # Apply vignette to all channels
    for c in range(3):
        frame_grain[:, :, c] = (frame_grain[:, :, c] * vignette).astype(np.uint8)

    return frame_grain

def process_clip(input_path, output_path, target_luma):
    """Process single clip: histogram match + grain/vignette."""
    cap = cv2.VideoCapture(input_path)

    if not cap.isOpened():
        print(f"  ERROR: Could not open {input_path}")
        return False

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Setup output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Apply histogram matching
        frame = apply_histogram_match(frame, target_luma)

        # Apply grain + vignette
        frame = apply_grain_vignette(frame)

        out.write(frame)
        frame_num += 1

        if frame_num % 30 == 0:
            print(f"    {frame_num}/{frame_count} frames", end='\r', flush=True)

    cap.release()
    out.release()
    print(f"    ✓ {os.path.basename(output_path)}")
    return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python coherence_pass.py <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    os.makedirs(output_dir, exist_ok=True)

    print(f"Coherence pass: {input_dir} → {output_dir}\n")

    # Find all clips
    clip_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.mp4')])
    print(f"Found {len(clip_files)} clips")

    # Calculate batch median luminance
    print("\nAnalyzing luminance...")
    luma_values = []
    for clip_file in clip_files:
        clip_path = os.path.join(input_dir, clip_file)
        luma = get_clip_luma(clip_path)
        if luma is not None:
            luma_values.append(luma)
            print(f"  {clip_file}: {luma:.1f}")

    batch_median = np.median(luma_values)
    print(f"\nBatch median luminance: {batch_median:.2f}")

    # Process each clip
    print("\nApplying histogram matching + grain/vignette...")
    success_count = 0
    for clip_file in clip_files:
        input_path = os.path.join(input_dir, clip_file)
        output_path = os.path.join(output_dir, clip_file)

        if process_clip(input_path, output_path, batch_median):
            success_count += 1

    print(f"\n✓ Coherence pass complete: {success_count}/{len(clip_files)} clips processed")
    print(f"Output: {output_dir}/")

if __name__ == "__main__":
    main()
