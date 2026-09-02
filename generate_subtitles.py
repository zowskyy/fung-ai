#!/usr/bin/env python3
"""
Generate subtitle files (SRT/VTT) for silent film from story breakdown.
Creates timing-accurate subtitles for all 21 chapters.

Usage: python generate_subtitles.py --output subtitles.srt
       python generate_subtitles.py --format vtt --output subtitles.vtt
"""
import argparse
import sys
from datetime import timedelta


def seconds_to_timestamp(seconds, fmt='srt'):
    """Convert seconds to SRT (HH:MM:SS,mmm) or VTT (HH:MM:SS.mmm) format."""
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, secs = divmod(remainder, 60)
    millis = int((td.total_seconds() % 1) * 1000)

    if fmt == 'vtt':
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    else:  # srt
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_subtitles():
    """Create subtitle data for all 21 chapters."""
    # Timing: each clip is ~10 frames at 24fps = 0.41667 seconds
    # 99 clips total, 5 chapters per location, 21 chapters total
    # Clip duration: ~0.41 seconds each

    subtitles = [
        {
            "chapter": 1,
            "start": 0.0,
            "end": 0.41,
            "text": "Ten miles from the ocean.\nNever touched the sand.",
        },
        {
            "chapter": 2,
            "start": 0.41,
            "end": 0.82,
            "text": "Mom worked three jobs.\nShe never complained.",
        },
        {
            "chapter": 3,
            "start": 0.82,
            "end": 1.23,
            "text": "We didn't go to the beach.\nThe beach wasn't for us.",
        },
        {
            "chapter": 4,
            "start": 1.23,
            "end": 1.64,
            "text": "My father died when I was seven.",
        },
        {
            "chapter": 5,
            "start": 1.64,
            "end": 2.05,
            "text": "Shot in a ditch\nwith seventeen dollars.",
        },
        {
            "chapter": 6,
            "start": 2.05,
            "end": 2.46,
            "text": "He loved us.\nHe loved the street more.",
        },
        {
            "chapter": 7,
            "start": 2.46,
            "end": 2.87,
            "text": "Got arrested as a kid.\nStupid stuff.",
        },
        {
            "chapter": 8,
            "start": 2.87,
            "end": 3.28,
            "text": "Then at twenty-one,\nI was framed.",
        },
        {
            "chapter": 9,
            "start": 3.28,
            "end": 3.69,
            "text": "Learned to code\non a broken computer.",
        },
        {
            "chapter": 10,
            "start": 3.69,
            "end": 4.10,
            "text": "Interview goes great.\nThen: background check.",
        },
        {
            "chapter": 11,
            "start": 4.10,
            "end": 4.51,
            "text": "Door after door\nslams shut.",
        },
        {
            "chapter": 12,
            "start": 4.51,
            "end": 4.92,
            "text": "I'm drowning.",
        },
        {
            "chapter": 13,
            "start": 4.92,
            "end": 5.33,
            "text": "I built an app.\nCalled it No Sand Beach.",
        },
        {
            "chapter": 14,
            "start": 5.33,
            "end": 5.74,
            "text": "Rewrote my background.\nGave myself a fake degree.",
        },
        {
            "chapter": 15,
            "start": 5.74,
            "end": 6.15,
            "text": "Got the job.\nGot the office.\nGot the view.",
        },
        {
            "chapter": 16,
            "start": 6.15,
            "end": 6.56,
            "text": "I forgot my mother's laugh.\nI forgot my brother's voice.",
        },
        {
            "chapter": 17,
            "start": 6.56,
            "end": 6.97,
            "text": "I was becoming\na stranger to myself.",
        },
        {
            "chapter": 18,
            "start": 6.97,
            "end": 7.38,
            "text": "Dad appeared as a glitch:\n\"You're killing her by becoming someone else.\"",
        },
        {
            "chapter": 19,
            "start": 7.38,
            "end": 7.79,
            "text": "I collapsed on the office floor.\nMom held my hand.\nMarcus came.\nWe reconciled.",
        },
        {
            "chapter": 20,
            "start": 7.79,
            "end": 8.20,
            "text": "I deleted it. Line by line.\nGot my real memories back.",
        },
        {
            "chapter": 21,
            "start": 8.20,
            "end": 8.61,
            "text": "Touched the sand.\n\nLove isn't a subscription.\nIt's the ground under your feet.\n\nYou don't have to erase who you are.",
        },
    ]

    return subtitles


def write_srt(subtitles, output_file):
    """Write subtitles in SRT format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subtitles, 1):
            start = seconds_to_timestamp(sub['start'], fmt='srt')
            end = seconds_to_timestamp(sub['end'], fmt='srt')
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{sub['text']}\n")
            f.write("\n")

    print(f"✓ Written {len(subtitles)} subtitles to {output_file} (SRT format)")


def write_vtt(subtitles, output_file):
    """Write subtitles in WebVTT format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for sub in subtitles:
            start = seconds_to_timestamp(sub['start'], fmt='vtt')
            end = seconds_to_timestamp(sub['end'], fmt='vtt')
            f.write(f"{start} --> {end}\n")
            f.write(f"{sub['text']}\n")
            f.write("\n")

    print(f"✓ Written {len(subtitles)} subtitles to {output_file} (WebVTT format)")


def write_json(subtitles, output_file):
    """Write subtitles in JSON format (for Godot integration)."""
    import json

    data = {
        "title": "No Sand Beach — Silent Film",
        "format": "subtitle_track",
        "total_chapters": len(subtitles),
        "total_duration_seconds": subtitles[-1]['end'],
        "subtitles": subtitles
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Written {len(subtitles)} subtitles to {output_file} (JSON format)")


def main():
    ap = argparse.ArgumentParser(
        description='Generate subtitle files for No Sand Beach silent film'
    )
    ap.add_argument('--format', choices=['srt', 'vtt', 'json'], default='srt',
                    help='Subtitle format (default: srt)')
    ap.add_argument('--output', default='subtitles.srt',
                    help='Output file path')
    ap.add_argument('--godot', action='store_true',
                    help='Generate both JSON (for Godot) and SRT (for testing)')
    args = ap.parse_args()

    print("Generating subtitle data for 21 chapters...")
    subtitles = create_subtitles()

    if args.godot:
        # Generate both JSON and SRT
        json_output = args.output.replace('.srt', '_godot.json')
        write_json(subtitles, json_output)
        write_srt(subtitles, args.output)
    else:
        if args.format == 'srt':
            write_srt(subtitles, args.output)
        elif args.format == 'vtt':
            write_vtt(subtitles, args.output)
        elif args.format == 'json':
            write_json(subtitles, args.output)

    print(f"\nSubtitle summary:")
    print(f"  Chapters: {len(subtitles)}")
    print(f"  Duration: {subtitles[-1]['end']:.2f} seconds")
    print(f"  Format: {args.format}")
    print(f"  Output: {args.output}")


if __name__ == '__main__':
    main()
