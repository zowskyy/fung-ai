#!/usr/bin/env python3
"""
Generate intermediate keyframes by blending adjacent frames.
Splits large-motion transitions (27-110px) into smaller steps.

Example: beach_v1 (27px) -> beach_v2 becomes:
  beach_v1 -> beach_v1_5 -> beach_v2 (two 13-14px steps)
"""
import cv2
import numpy as np
from pathlib import Path
import sys

def blend_frames(frame_a, frame_b, alpha=0.5):
    """Linear blend: alpha=0 is frame_a, alpha=1 is frame_b."""
    return cv2.addWeighted(frame_a, 1-alpha, frame_b, alpha, 0)

def gen_intermediates(locations_and_motions):
    """
    Generate intermediate frames for high-motion pairs.
    locations_and_motions: list of (location, v_start, v_end, mean_flow)
    """
    generated = []

    for location, v_start, v_end, flow_px in locations_and_motions:
        src_start = f"{location}_v{v_start}.png"
        src_end = f"{location}_v{v_end}.png"

        # Determine how many intermediate frames needed
        # Target: split large motion into ~10-12px steps (slightly above threshold)
        num_intermediates = max(0, int(np.ceil(flow_px / 13.0)) - 1)

        if num_intermediates == 0:
            print(f"  {location}_v{v_start}-v{v_end}: {flow_px:.1f}px → 1 direct interpolation")
            continue

        print(f"  {location}_v{v_start}-v{v_end}: {flow_px:.1f}px → split into {num_intermediates+1} steps")

        try:
            img_start = cv2.imread(src_start)
            img_end = cv2.imread(src_end)

            if img_start is None or img_end is None:
                print(f"    ERROR: could not load {src_start} or {src_end}")
                continue

            # Generate intermediate frames
            for i in range(1, num_intermediates + 1):
                alpha = i / (num_intermediates + 1)
                intermediate = blend_frames(img_start, img_end, alpha)

                # Save as location_vX_5, location_vX_75, etc.
                interp_name = f"{location}_v{v_start}_{int(100*alpha)}.png"
                cv2.imwrite(interp_name, intermediate)
                generated.append((location, v_start, v_end, i, interp_name))
                print(f"    ✓ {interp_name}")

        except Exception as e:
            print(f"    ERROR: {e}")

    return generated

def update_pairs_csv(original_csv, intermediates_generated):
    """
    Rewrite pairs.csv to use intermediate frames.
    For each high-motion pair, create sub-pairs.
    """
    # Read original pairs
    pairs = []
    with open(original_csv) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) == 4:
                pairs.append(tuple(parts))

    # Build mapping of (location, v_start, v_end) -> intermediates
    inter_map = {}
    for loc, v_start, v_end, step, fname in intermediates_generated:
        key = (loc, v_start, v_end)
        if key not in inter_map:
            inter_map[key] = []
        inter_map[key].append((step, fname))

    # Rewrite pairs.csv with intermediate frames
    new_pairs = []
    for clip_id, frame_a, frame_b, frames_str in pairs:
        # Extract location and versions from frame names
        # e.g., "beach_v1.png" -> location="beach", version=1
        try:
            parts_a = frame_a.replace(".png", "").split("_")
            location = "_".join(parts_a[:-1])  # e.g., "beach"
            v_start = int(parts_a[-1][1])  # e.g., v1 -> 1

            parts_b = frame_b.replace(".png", "").split("_")
            v_end = int(parts_b[-1][1])  # e.g., v2 -> 2

            key = (location, v_start, v_end)

            if key in inter_map:
                # High-motion pair: use intermediates
                sorted_inter = sorted(inter_map[key], key=lambda x: x[0])

                # v_start -> intermediate_1
                new_pairs.append((
                    f"{clip_id}_a",
                    frame_a,
                    sorted_inter[0][1],
                    "10"
                ))

                # intermediate -> v_end (or next intermediate)
                for i, (step, inter_fname) in enumerate(sorted_inter):
                    if i < len(sorted_inter) - 1:
                        next_fname = sorted_inter[i+1][1]
                    else:
                        next_fname = frame_b

                    new_pairs.append((
                        f"{clip_id}_{chr(ord('b') + i)}",
                        inter_fname,
                        next_fname,
                        "10"
                    ))
            else:
                # Low-motion pair: keep as-is
                new_pairs.append((clip_id, frame_a, frame_b, frames_str))

        except Exception as e:
            print(f"  WARNING: could not parse {clip_id}: {e}")
            new_pairs.append((clip_id, frame_a, frame_b, frames_str))

    # Write updated CSV
    with open("expanded_pairs.csv", "w") as f:
        for clip_id, frame_a, frame_b, frames_str in new_pairs:
            f.write(f"{clip_id},{frame_a},{frame_b},{frames_str}\n")

    print(f"\n✓ Updated pairs written to expanded_pairs.csv")
    print(f"  Original: {len(pairs)} pairs")
    print(f"  Expanded: {len(new_pairs)} pairs")

def main():
    print("Generating intermediate keyframes for high-motion transitions...\n")

    # High-motion pairs identified from QA report
    # (location, v_start, v_end, observed_mean_flow_px)
    high_motion_pairs = [
        ("beach", 1, 2, 27.3),   # 2.3x threshold
        ("beach", 2, 3, 32.7),   # 2.7x threshold
        ("beach", 3, 4, 68.1),   # 5.7x threshold
        ("car", 1, 2, 58.5),     # 4.9x threshold
        ("car", 2, 3, 62.0),     # 5.2x threshold
        ("car", 3, 4, 78.3),     # 6.5x threshold
        ("forest", 1, 2, 77.5),  # 6.5x threshold
        ("forest", 2, 3, 40.7),  # 3.4x threshold
        ("forest", 3, 4, 69.3),  # 5.8x threshold
        ("kitchen", 1, 2, 56.7), # 4.7x threshold
        ("kitchen", 2, 3, 66.0), # 5.5x threshold
        ("kitchen", 3, 4, 58.3), # 4.9x threshold
        ("park", 1, 2, 96.3),    # 8.0x threshold
        ("park", 2, 3, 65.1),    # 5.4x threshold
        ("park", 3, 4, 73.0),    # 6.1x threshold
        ("schoolyard", 1, 2, 108.7), # 9.1x threshold
        ("schoolyard", 2, 3, 110.1), # 9.2x threshold
    ]

    intermediates = gen_intermediates(high_motion_pairs)
    print(f"\n✓ Generated {len(intermediates)} intermediate frames")

    # Update pairs CSV
    print("\nUpdating pairs.csv with intermediate frames...")
    update_pairs_csv("full_batch.csv", intermediates)

if __name__ == "__main__":
    main()
