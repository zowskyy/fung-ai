#!/usr/bin/env python3
"""
Character animation integration for silent film: overlays character PNG images onto
environment clips with per-scene positioning, scale, and opacity.

Uses FFmpeg drawtext and overlay filters to composite static character images
at specified positions onto environment video frames.

Silent film workflow:
- Each scene maps to one character image (PNG file)
- Position (x, y, scale) controls placement and size
- Character pose variants (different PNG files) communicate emotion
- No audio sync required (pure silent film with text subtitles)
"""
import argparse
import json
import os
import sys
import subprocess
from pathlib import Path


def load_character_metadata(metadata_path):
    """Load character animation metadata JSON for silent film."""
    if not os.path.exists(metadata_path):
        print(f"ERROR: metadata not found: {metadata_path}")
        return None

    try:
        with open(metadata_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON in {metadata_path}: {e}")
        return None


def validate_character_metadata(metadata):
    """Validate character metadata structure."""
    if 'characters' not in metadata or 'scenes' not in metadata:
        print("ERROR: metadata missing 'characters' or 'scenes' key")
        return False

    # Build character ID set (allowing null for environment-only scenes)
    char_ids = {c['id'] for c in metadata['characters']}

    for scene in metadata['scenes']:
        character_id = scene.get('character_id')
        # character_id can be None for environment-only shots, but if present must be valid
        if character_id is not None and character_id not in char_ids:
            print(f"ERROR: scene '{scene['clip_id']}' references unknown character '{character_id}'")
            return False

    return True


def generate_ffmpeg_overlay_command(scene_metadata, char_image_path, env_video, output_video):
    """
    Generate FFmpeg command to overlay static character PNG onto environment video.

    Uses scale2ref and overlay filters to place character image at specified position.
    """
    pos = scene_metadata['position']
    if not pos or pos.get('scale') is None:
        print(f"  WARNING: scene '{scene_metadata['clip_id']}' missing position/scale, skipping character overlay")
        return None

    scale = pos['scale']
    x = int(pos['x'])
    y = int(pos['y'])

    # Character will occupy approximately 30% of frame width
    # Scale is multiplier (1.0 = original size of character PNG)
    # Use scale2ref to scale character to reference video dimensions
    char_scale = 0.3 * scale  # 30% of frame = 384px (of 1280)

    filter_complex = (
        f"[1:v]scale=w=iw*{char_scale}:h=ih*{char_scale},setsar=1[char];"
        f"[0:v][char]overlay=x={x}:y={y}:enable='isnan(prev_selected_t)+gte(t\\,0)'[v]"
    )

    cmd = [
        'ffmpeg',
        '-i', env_video,               # [0] environment video
        '-loop', '1',                  # Loop image for duration of video
        '-i', char_image_path,         # [1] character PNG (looped to match video length)
        '-filter_complex', filter_complex,
        '-pix_fmt', 'yuv420p',        # Compatibility
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',
        '-shortest',                   # End at shortest input (the video)
        output_video
    ]

    return cmd


def main():
    ap = argparse.ArgumentParser(
        description='Overlay character PNG images onto environment clips (silent film workflow)'
    )
    ap.add_argument('--metadata', default='character_metadata_silent.json',
                    help='Character metadata JSON (silent film format)')
    ap.add_argument('--env-clips', default='graded',
                    help='Directory with environment video clips')
    ap.add_argument('--char-clips', default='characters',
                    help='Directory with character PNG images')
    ap.add_argument('--output-dir', default='composited_silent',
                    help='Output directory for composited clips')
    ap.add_argument('--validate-only', action='store_true',
                    help='Validate metadata without processing')
    ap.add_argument('--micro-test', metavar='CLIP_ID',
                    help='Test with single clip before full batch')
    args = ap.parse_args()

    # Load and validate metadata
    metadata = load_character_metadata(args.metadata)
    if not metadata:
        sys.exit(1)

    if not validate_character_metadata(metadata):
        sys.exit(1)

    print(f"✓ Loaded character metadata: {args.metadata}")
    print(f"  Characters: {len(metadata['characters'])}")
    print(f"  Scenes: {len(metadata['scenes'])}")

    if args.validate_only:
        print("✓ Metadata validation passed")
        return 0

    # Micro-test or full batch
    if args.micro_test:
        scenes = [s for s in metadata['scenes'] if s['clip_id'] == args.micro_test]
        if not scenes:
            print(f"ERROR: clip '{args.micro_test}' not in metadata")
            sys.exit(1)
        print(f"\n[MICRO TEST] Processing single clip: {args.micro_test}")
    else:
        scenes = metadata['scenes']
        print(f"\n[FULL BATCH] Processing {len(scenes)} scenes")

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"\nOverlaying characters onto environment clips...")
    print(f"  Environment clips: {args.env_clips}")
    print(f"  Character images: {args.char_clips}")
    print(f"  Output: {args.output_dir}\n")

    skipped = 0
    processed = 0
    failed = 0

    for i, scene in enumerate(scenes, 1):
        clip_id = scene['clip_id']
        character_id = scene.get('character_id')
        image_file = scene.get('image')

        env_path = os.path.join(args.env_clips, f"{clip_id}.mp4")
        output_path = os.path.join(args.output_dir, f"{clip_id}.mp4")

        # Check environment clip exists
        if not os.path.exists(env_path):
            print(f"  [{i}/{len(scenes)}] ✗ {clip_id}: environment clip not found")
            failed += 1
            continue

        # Handle environment-only scenes (no character)
        if character_id is None or image_file is None:
            print(f"  [{i}/{len(scenes)}] ⊕ {clip_id}: environment only (no character)")
            # Just copy environment clip to output
            cmd = ['ffmpeg', '-i', env_path, '-c', 'copy', output_path]
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                skipped += 1
            except subprocess.CalledProcessError as e:
                print(f"      ✗ FFmpeg error: {e.stderr.decode()[:100]}")
                failed += 1
            continue

        # Get character image path
        char_path = os.path.join(args.char_clips, image_file)
        if not os.path.exists(char_path):
            print(f"  [{i}/{len(scenes)}] ⚠ {clip_id}: character image not found ({image_file})")
            failed += 1
            continue

        print(f"  [{i}/{len(scenes)}] Processing {clip_id}...", end=' ', flush=True)

        # Generate and execute FFmpeg command
        cmd = generate_ffmpeg_overlay_command(scene, char_path, env_path, output_path)
        if cmd is None:
            print("✗ (invalid position)")
            failed += 1
            continue

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, timeout=300)
            print(f"✓")
            processed += 1
        except subprocess.CalledProcessError as e:
            print(f"✗ FFmpeg error")
            print(f"      {e.stderr.decode()[:200]}")
            failed += 1
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout (>300s)")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Character integration complete:")
    print(f"  ✓ Processed: {processed}")
    print(f"  ⊕ Environment only: {skipped}")
    print(f"  ✗ Failed: {failed}")
    print(f"  Total: {len(scenes)}")
    print(f"\nOutput: {args.output_dir}/")
    print(f"{'='*60}")

    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
