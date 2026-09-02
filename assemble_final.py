#!/usr/bin/env python3
"""
Assemble final animation: concat graded clips, apply crossfades at location boundaries,
mux audio, and prepare for Godot integration.

Usage: python assemble_final.py --clips graded/ --audio-dir voiceovers/ --output final.mp4
"""
import argparse
import os
import sys
import subprocess
import csv
from pathlib import Path


def read_clip_order(pairs_csv):
    """Read expanded_pairs.csv to get clip order and timing."""
    clips = []
    with open(pairs_csv) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4:
                clip_id, frame_a, frame_b, frames = row[0], row[1], row[2], row[3]
                clips.append({
                    'id': clip_id,
                    'frame_a': frame_a,
                    'frame_b': frame_b,
                    'interp_frames': int(frames),
                    'duration_sec': int(frames) / 24.0  # 24fps default
                })
    return clips


def find_location_boundaries(clips):
    """Identify where location changes occur (need crossfade)."""
    boundaries = []
    for i in range(len(clips) - 1):
        curr_loc = clips[i]['id'].split('_')[0]
        next_loc = clips[i+1]['id'].split('_')[0]
        if curr_loc != next_loc:
            boundaries.append({
                'from_clip': i,
                'to_clip': i + 1,
                'from_loc': curr_loc,
                'to_loc': next_loc
            })
    return boundaries


def generate_concat_filter(clips, boundaries, crossfade_duration=0.5):
    """
    Generate FFmpeg complex filter for concat with crossfades at boundaries.

    Structure: [clip0][clip1]...[clipN] connected via xfade filters at boundaries.
    """
    fps = 24
    crossfade_frames = int(crossfade_duration * fps)

    if not boundaries:
        # Simple concat without crossfades
        filter_parts = []
        for i, clip in enumerate(clips):
            filter_parts.append(f"[{i}:v]")
        filter_parts.append(f"concat=n={len(clips)}:v=1:a=0[v]")
        return "".join(filter_parts)

    # Build filter with crossfades at boundaries
    filter_chain = []
    clip_idx = 0

    # Connect clips with xfade at each boundary
    segment_idx = 0
    for i, clip in enumerate(clips):
        filter_chain.append(f"[{i}:v]")

        # Check if this is a boundary
        if any(b['from_clip'] == i for b in boundaries):
            crossfade_ms = int(crossfade_frames / fps * 1000)
            filter_chain.append(
                f"[{i+1}:v]xfade=transition=fade:duration={crossfade_duration}:offset={clips[i]['duration_sec'] - crossfade_duration}[seg{segment_idx}];"
            )
            segment_idx += 1

    # Simple concat (adjust for boundary handling)
    filter_chain.append(f"concat=n={len(clips)}:v=1:a=0[v]")
    return "".join(filter_chain)


def create_ffmpeg_command(clips_dir, clip_list, audio_track, output_mp4, boundaries):
    """
    Generate FFmpeg command to:
    1. Concat video clips (with crossfades at boundaries)
    2. Mux audio track
    """
    # Build input list
    input_args = []
    for clip in clip_list:
        clip_path = os.path.join(clips_dir, f"{clip['id']}.mp4")
        input_args.extend(['-i', clip_path])

    # Add audio
    if audio_track and os.path.exists(audio_track):
        input_args.extend(['-i', audio_track])

    # Concat filter
    filter_complex = generate_concat_filter(clip_list, boundaries)

    # Output arguments
    output_args = [
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_mp4
    ]

    cmd = ['ffmpeg'] + input_args
    if filter_complex:
        cmd.extend(['-filter_complex', filter_complex])
    cmd.extend(output_args)

    return cmd


def main():
    ap = argparse.ArgumentParser(
        description='Assemble final animation from graded clips with audio sync'
    )
    ap.add_argument('--clips', default='graded', help='Directory with graded MP4 clips')
    ap.add_argument('--pairs', default='expanded_pairs.csv', help='Pairs CSV with clip order')
    ap.add_argument('--audio', help='Audio file (WAV/MP3/AAC) to mux')
    ap.add_argument('--output', default='final.mp4', help='Output MP4 path')
    ap.add_argument('--no-crossfade', action='store_true', help='Skip crossfades at boundaries')
    ap.add_argument('--dry-run', action='store_true', help='Print FFmpeg command without running')
    args = ap.parse_args()

    if not os.path.exists(args.clips):
        print(f"ERROR: clips directory not found: {args.clips}")
        sys.exit(1)

    if not os.path.exists(args.pairs):
        print(f"ERROR: pairs CSV not found: {args.pairs}")
        sys.exit(1)

    print(f"Reading clip order from {args.pairs}...")
    clips = read_clip_order(args.pairs)
    print(f"  Found {len(clips)} clips")

    boundaries = find_location_boundaries(clips) if not args.no_crossfade else []
    if boundaries:
        print(f"  Location boundaries (need crossfade): {len(boundaries)}")
        for b in boundaries:
            print(f"    {b['from_loc']} → {b['to_loc']} at clip {b['from_clip']}")

    # Verify all clip files exist
    print(f"\nVerifying clip files in {args.clips}...")
    missing = []
    for clip in clips:
        clip_path = os.path.join(args.clips, f"{clip['id']}.mp4")
        if not os.path.exists(clip_path):
            missing.append(clip['id'])

    if missing:
        print(f"  ERROR: {len(missing)} clips missing:")
        for cid in missing[:5]:
            print(f"    - {cid}.mp4")
        if len(missing) > 5:
            print(f"    ... and {len(missing) - 5} more")
        sys.exit(1)

    print(f"  ✓ All {len(clips)} clips present")

    # Calculate total duration
    total_duration = sum(c['duration_sec'] for c in clips)
    print(f"  Total duration: {total_duration:.1f}s ({int(total_duration // 60)}m {int(total_duration % 60)}s)")

    # Generate FFmpeg command
    print(f"\nGenerating FFmpeg command...")
    cmd = create_ffmpeg_command(args.clips, clips, args.audio, args.output, boundaries)

    if args.dry_run:
        print("  [DRY RUN] Would execute:")
        print("  " + " ".join(cmd))
        sys.exit(0)

    # Execute
    print(f"\nRunning FFmpeg assembly...")
    print(f"  Output: {args.output}")
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Assembly complete: {args.output}")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ FFmpeg failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
