#!/usr/bin/env python3
"""
Audio sync: pulls chapter voiceovers from ElevenLabs flows, concatenates with
proper timing, and prepares for final video mux.

Expects ElevenLabs flow_ids for each of the 21 chapters.
"""
import argparse
import json
import os
import sys
from pathlib import Path


def load_voiceover_manifest(manifest_path):
    """
    Load voiceover manifest JSON with structure:
    {
      "chapters": [
        {"chapter": 1, "location": "beach", "flow_id": "...", "duration_sec": 15.2},
        ...
      ]
    }
    """
    if not os.path.exists(manifest_path):
        print(f"ERROR: manifest not found: {manifest_path}")
        return None

    with open(manifest_path) as f:
        manifest = json.load(f)

    return manifest.get('chapters', [])


def validate_voiceover_manifest(chapters):
    """Verify all required fields present."""
    required_fields = ['chapter', 'location', 'flow_id', 'duration_sec']
    for i, ch in enumerate(chapters):
        for field in required_fields:
            if field not in ch:
                print(f"ERROR: chapter {i} missing field '{field}'")
                return False
    return True


def create_concat_demuxer(audio_files, output_demuxer):
    """
    Create FFmpeg concat demuxer file for audio:
    file 'ch01_voiceover.wav'
    file 'ch02_voiceover.wav'
    ...
    """
    with open(output_demuxer, 'w') as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")

    print(f"✓ Created concat demuxer: {output_demuxer}")


def generate_concat_command(demuxer_file, output_audio):
    """Generate FFmpeg command to concatenate audio files."""
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', demuxer_file,
        '-c', 'aac',
        '-b:a', '128k',
        output_audio
    ]
    return cmd


def create_voiceover_manifest_template():
    """Generate template manifest for user to fill in."""
    template = {
        "chapters": [
            {
                "chapter": 1,
                "location": "beach",
                "flow_id": "FLOW_ID_FROM_ELEVENLABS",
                "duration_sec": 0.0,
                "character": "protagonist",
                "voice_id": "VOICE_ID_FROM_ELEVENLABS"
            },
            {
                "chapter": 2,
                "location": "car",
                "flow_id": "FLOW_ID_FROM_ELEVENLABS",
                "duration_sec": 0.0,
                "character": "protagonist",
                "voice_id": "VOICE_ID_FROM_ELEVENLABS"
            }
        ],
        "notes": [
            "Fill in flow_id from ElevenLabs flows for each chapter",
            "Fill in duration_sec by checking the generated audio files",
            "character and voice_id are optional but recommended for voice consistency"
        ]
    }
    return template


def main():
    ap = argparse.ArgumentParser(
        description='Sync voiceovers from ElevenLabs with animation timeline'
    )
    ap.add_argument('--manifest', default='voiceover_manifest.json',
                    help='JSON manifest with chapter voiceover metadata')
    ap.add_argument('--audio-dir', default='voiceovers',
                    help='Directory containing downloaded audio files')
    ap.add_argument('--output', default='voiceover_master.wav',
                    help='Output concatenated audio file')
    ap.add_argument('--create-template', action='store_true',
                    help='Generate template manifest and exit')
    ap.add_argument('--validate-only', action='store_true',
                    help='Validate manifest without running FFmpeg')
    args = ap.parse_args()

    if args.create_template:
        template = create_voiceover_manifest_template()
        manifest_path = args.manifest
        with open(manifest_path, 'w') as f:
            json.dump(template, f, indent=2)
        print(f"✓ Created template manifest: {manifest_path}")
        print(f"  Edit this file and fill in flow_ids from ElevenLabs")
        return 0

    # Load and validate manifest
    chapters = load_voiceover_manifest(args.manifest)
    if not chapters:
        print(f"ERROR: could not load chapters from {args.manifest}")
        sys.exit(1)

    if not validate_voiceover_manifest(chapters):
        sys.exit(1)

    print(f"✓ Loaded {len(chapters)} chapters from {args.manifest}")

    # Check audio files exist
    os.makedirs(args.audio_dir, exist_ok=True)
    print(f"\nVerifying audio files in {args.audio_dir}...")

    audio_files = []
    for ch in chapters:
        # Expected format: ch01_voiceover.wav, ch02_voiceover.wav, etc.
        audio_file = os.path.join(args.audio_dir, f"ch{ch['chapter']:02d}_voiceover.wav")
        if os.path.exists(audio_file):
            size_mb = os.path.getsize(audio_file) / (1024*1024)
            print(f"  ✓ ch{ch['chapter']:02d}: {size_mb:.1f}MB")
            audio_files.append(audio_file)
        else:
            print(f"  ✗ ch{ch['chapter']:02d}: NOT FOUND")
            print(f"    Expected: {audio_file}")

    if len(audio_files) != len(chapters):
        print(f"\nWARNING: only {len(audio_files)}/{len(chapters)} audio files found")
        print("  Run ElevenLabs voiceover generation first")
        if not args.validate_only:
            sys.exit(1)

    if args.validate_only:
        print("\n✓ Validation complete")
        return 0

    # Create concat demuxer
    demuxer_file = 'audio_concat.txt'
    create_concat_demuxer(audio_files, demuxer_file)

    # Generate FFmpeg command
    print(f"\nConcatenating {len(audio_files)} audio files...")
    cmd = generate_concat_command(demuxer_file, args.output)

    print(f"  Output: {args.output}")
    import subprocess
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✓ Audio concatenated: {args.output}")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ FFmpeg failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
