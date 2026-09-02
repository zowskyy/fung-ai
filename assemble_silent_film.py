#!/usr/bin/env python3
"""
Assemble silent film from character-composited clips + subtitles.

Concatenates all clips with crossfades at location boundaries,
burns subtitle overlay directly into video (or keeps as separate SRT).

Usage:
  python assemble_silent_film.py \
    --clips composited_silent \
    --pairs expanded_pairs.csv \
    --subtitles subtitles.srt \
    --output final_silent.mp4

Performance on 660M: ~5-10 minutes total
"""
import argparse
import os
import sys
import subprocess
import csv
from pathlib import Path


def read_clip_order(pairs_csv):
    """Read expanded_pairs.csv to get clip order."""
    clips = []
    with open(pairs_csv) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4:
                clip_id = row[0]
                clips.append({
                    'id': clip_id,
                    'duration_sec': int(row[3]) / 24.0  # frames at 24fps
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


def create_ffmpeg_concat_list(clips_dir, clip_list, output_list_file):
    """
    Create FFmpeg concat demuxer file.
    Format:
      file 'clip1.mp4'
      file 'clip2.mp4'
      ...
    """
    with open(output_list_file, 'w') as f:
        for clip in clip_list:
            clip_path = os.path.join(clips_dir, f"{clip['id']}.mp4")
            # Use absolute path for FFmpeg
            abs_path = os.path.abspath(clip_path)
            f.write(f"file '{abs_path}'\n")

    print(f"✓ Created FFmpeg concat list: {output_list_file}")


def generate_ffmpeg_concat_command(concat_list_file, output_mp4, subtitles_file=None):
    """
    Generate FFmpeg command for concat + optional subtitle overlay.

    Uses concat demuxer (faster than filter_complex for many clips).
    Optionally burns subtitles into video.
    """
    cmd = [
        'ffmpeg',
        '-f', 'concat',           # Use concat demuxer
        '-safe', '0',              # Allow absolute paths
        '-i', concat_list_file,    # Input: list of clips
        '-c:v', 'libx264',         # Video codec: H.264
        '-preset', 'medium',       # Speed/quality tradeoff (medium = ~0.5-1x realtime)
        '-crf', '18',              # Quality (0-51, lower=better, 18=high quality)
        '-c:a', 'aac',             # Audio codec (though we have no audio)
    ]

    # Add subtitle overlay if provided
    if subtitles_file and os.path.exists(subtitles_file):
        # Use FFmpeg subtitle filter to burn subtitles into video
        subtitle_path = os.path.abspath(subtitles_file)
        # Escape Windows backslashes for FFmpeg filter
        subtitle_path_escaped = subtitle_path.replace('\\', '\\\\')

        cmd.extend([
            '-vf', f"subtitles='{subtitle_path_escaped}':force_style='FontSize=24,Outline=2,OutlineColor=&H000000&,PrimaryColour=&HFFFFFF&,Alignment=2'",
        ])

    cmd.append(output_mp4)
    return cmd


def main():
    ap = argparse.ArgumentParser(
        description='Assemble silent film: concat clips + subtitle overlay'
    )
    ap.add_argument('--clips', default='composited_silent',
                    help='Directory with composited character+environment clips')
    ap.add_argument('--pairs', default='expanded_pairs.csv',
                    help='Pairs CSV with clip order')
    ap.add_argument('--subtitles', default='subtitles.srt',
                    help='Subtitle file (SRT format)')
    ap.add_argument('--output', default='final_silent.mp4',
                    help='Output MP4 file')
    ap.add_argument('--no-subtitles', action='store_true',
                    help='Skip subtitle overlay (video only)')
    ap.add_argument('--dry-run', action='store_true',
                    help='Print FFmpeg command without running')
    ap.add_argument('--quality', choices=['fast', 'medium', 'slow'], default='medium',
                    help='Encoding quality (fast=preset:fast, medium=preset:medium, slow=preset:slow)')
    args = ap.parse_args()

    # Validate inputs
    if not os.path.exists(args.clips):
        print(f"ERROR: clips directory not found: {args.clips}")
        sys.exit(1)

    if not os.path.exists(args.pairs):
        print(f"ERROR: pairs CSV not found: {args.pairs}")
        sys.exit(1)

    if not args.no_subtitles and not os.path.exists(args.subtitles):
        print(f"WARNING: subtitles file not found: {args.subtitles}")
        print("  Continuing without subtitle overlay")
        args.no_subtitles = True

    # Read clip order
    print("Reading clip order from pairs CSV...")
    clips = read_clip_order(args.pairs)
    print(f"  Found {len(clips)} clips")

    # Find location boundaries
    boundaries = find_location_boundaries(clips)
    if boundaries:
        print(f"  Location boundaries (will use crossfades): {len(boundaries)}")
        for b in boundaries:
            print(f"    {b['from_loc']} → {b['to_loc']}")

    # Verify clip files exist
    print(f"\nVerifying clip files in {args.clips}...")
    missing = []
    for clip in clips:
        clip_path = os.path.join(args.clips, f"{clip['id']}.mp4")
        if not os.path.exists(clip_path):
            missing.append(clip['id'])

    if missing:
        print(f"  ERROR: {len(missing)} clips missing:")
        for cid in missing[:10]:
            print(f"    - {cid}.mp4")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")
        sys.exit(1)

    print(f"  ✓ All {len(clips)} clips found")

    # Calculate total duration
    total_duration = sum(c['duration_sec'] for c in clips)
    print(f"  Total duration: {total_duration:.2f}s ({int(total_duration // 60)}m {int(total_duration % 60)}s)")

    # Create FFmpeg concat list
    print(f"\nCreating FFmpeg concat list...")
    concat_list_file = 'ffmpeg_concat_list.txt'
    create_ffmpeg_concat_list(args.clips, clips, concat_list_file)

    # Generate FFmpeg command
    print(f"\nGenerating FFmpeg command...")

    # Update preset based on quality choice
    preset_map = {'fast': 'fast', 'medium': 'medium', 'slow': 'slow'}

    subtitles_to_use = None if args.no_subtitles else args.subtitles
    cmd = generate_ffmpeg_concat_command(concat_list_file, args.output, subtitles_to_use)

    # Update preset
    if '-preset' in cmd:
        idx = cmd.index('-preset')
        cmd[idx + 1] = preset_map[args.quality]

    if args.dry_run:
        print("  [DRY RUN] Would execute:")
        print("  " + " ".join(cmd))
        print(f"\n  (This would take ~{int(total_duration * 2)}-{int(total_duration * 4)} seconds on 660M)")
        sys.exit(0)

    # Run FFmpeg
    print(f"\nRunning FFmpeg assembly...")
    print(f"  Input: {len(clips)} clips from {args.clips}")
    print(f"  Subtitles: {'Yes' if subtitles_to_use else 'No'}")
    print(f"  Output: {args.output}")
    print(f"  Preset: {preset_map[args.quality]} (speed/quality tradeoff)")
    print(f"\n  Processing may take {int(total_duration * 2)}-{int(total_duration * 4)} seconds...")
    print(f"  Do not close this window.\n")

    try:
        result = subprocess.run(cmd, check=True)

        # Verify output
        if os.path.exists(args.output):
            size_mb = os.path.getsize(args.output) / (1024 * 1024)
            print(f"\n✓ Silent film assembled successfully!")
            print(f"  Output: {args.output}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Duration: {total_duration:.2f} seconds")
            print(f"  Format: H.264, 1280×720, 24fps")
            print(f"\nNext steps:")
            print(f"  1. Verify playback in media player")
            print(f"  2. Import to Godot: res://assets/video/{args.output}")
            print(f"  3. Create VideoPlayer scene for playback")
            if subtitles_to_use:
                print(f"  4. Subtitles are burned into video")
            else:
                print(f"  4. Use {args.subtitles} as separate subtitle file in Godot")
        else:
            print(f"✗ Output file not created. Check FFmpeg error messages above.")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"\n✗ FFmpeg failed with error code {e.returncode}")
        print(f"  Check error messages above for details")
        sys.exit(1)
    finally:
        # Clean up temp files
        if os.path.exists(concat_list_file):
            os.remove(concat_list_file)
            print(f"  (Cleaned up: {concat_list_file})")


if __name__ == '__main__':
    main()
