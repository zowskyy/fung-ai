#!/usr/bin/env python3
"""
Generate comprehensive character metadata for all 99 silent film clips.
Maps clips to characters and poses based on story narrative progression.
"""
import json
from pathlib import Path

# Define clip structure from graded directory (from coherence_pass output)
clips_by_location = {
    "beach": [
        "beach_01_a", "beach_01_b", "beach_01_c",
        "beach_02_a", "beach_02_b", "beach_02_c",
        "beach_03_a", "beach_03_b", "beach_03_c", "beach_03_d", "beach_03_e", "beach_03_f",
    ],
    "car": [
        "car_01_a", "car_01_b", "car_01_c", "car_01_d", "car_01_e",
        "car_02_a", "car_02_b", "car_02_c", "car_02_d", "car_02_e",
        "car_03_a", "car_03_b", "car_03_c", "car_03_d", "car_03_e", "car_03_f", "car_03_g",
    ],
    "forest": [
        "forest_01_a", "forest_01_b", "forest_01_c", "forest_01_d", "forest_01_e", "forest_01_f",
        "forest_02_a", "forest_02_b", "forest_02_c", "forest_02_d",
        "forest_03_a", "forest_03_b", "forest_03_c", "forest_03_d", "forest_03_e", "forest_03_f",
    ],
    "kitchen": [
        "kitchen_01_a", "kitchen_01_b", "kitchen_01_c", "kitchen_01_d", "kitchen_01_e",
        "kitchen_02_a", "kitchen_02_b", "kitchen_02_c", "kitchen_02_d", "kitchen_02_e", "kitchen_02_f",
        "kitchen_03_a", "kitchen_03_b", "kitchen_03_c", "kitchen_03_d", "kitchen_03_e",
    ],
    "park": [
        "park_01_a", "park_01_b", "park_01_c", "park_01_d", "park_01_e", "park_01_f", "park_01_g", "park_01_h",
        "park_02_a", "park_02_b", "park_02_c", "park_02_d", "park_02_e", "park_02_f",
        "park_03_a", "park_03_b", "park_03_c", "park_03_d", "park_03_e", "park_03_f",
    ],
    "schoolyard": [
        "schoolyard_01_a", "schoolyard_01_b", "schoolyard_01_c", "schoolyard_01_d", "schoolyard_01_e",
        "schoolyard_01_f", "schoolyard_01_g", "schoolyard_01_h", "schoolyard_01_i",
        "schoolyard_02_a", "schoolyard_02_b", "schoolyard_02_c", "schoolyard_02_d", "schoolyard_02_e",
        "schoolyard_02_f", "schoolyard_02_g", "schoolyard_02_h", "schoolyard_02_i",
    ],
}

# Timing: ~0.41 seconds per clip (99 clips = 8.6 seconds total)
# 21 chapters across 99 clips = ~4.7 clips per chapter
# Actual distribution: chapters spread across locations

# Character pose sequences for each emotional beat
poses_by_character = {
    "protagonist": {
        "child_innocent": "pureteen.png",        # Chapters 1-3: young, searching
        "grief": "pure.png",                      # Chapters 4-6: close-up, sad
        "prison_determined": "pure.png",          # Chapters 7-9: intense, focused
        "desperate": "pureteen.png",              # Chapters 10-12: exhausted, searching
        "seduction": "pureyoung1.png",            # Chapters 13-15: confident, tempted
        "dissolution": "pure.png",                # Chapters 16-18: breaking, forgetting
        "collapse": "pureyoung1.png",             # Chapters 19-20: vulnerable, healing
        "elder_wisdom": "pureolder1.png",         # Chapter 21: wise, grounded
    }
}

# Map chapters to locations and character focus
chapter_mapping = {
    # Chapters 1-3: Beach (Setup)
    1: {"location": "beach", "clips": slice(0, 4), "chapter_clips": 4, "character_id": "protagonist", "image": "pureteen.png", "emotion": "nostalgic", "pose": "standing_looking_distant"},
    2: {"location": "beach", "clips": slice(4, 8), "chapter_clips": 4, "character_id": "mother", "image": "mama.png", "emotion": "sacrifice", "pose": "working_exhausted"},
    3: {"location": "beach", "clips": slice(8, 12), "chapter_clips": 4, "character_id": "brother", "image": "purebrother.png", "emotion": "resentment", "pose": "standing_watching"},

    # Chapters 4-6: Car (Father's death)
    4: {"location": "car", "clips": slice(0, 4), "chapter_clips": 4, "character_id": "protagonist", "image": "pure.png", "emotion": "grief", "pose": "close_up_grief"},
    5: {"location": "car", "clips": slice(4, 9), "chapter_clips": 5, "character_id": "father", "image": "puredadglitch.jpg", "emotion": "haunting", "pose": "glitch_memory"},
    6: {"location": "car", "clips": slice(9, 13), "chapter_clips": 4, "character_id": "brother", "image": "purebrother.png", "emotion": "shared_trauma", "pose": "standing_grief"},

    # Chapters 7-9: Forest (Prison, learning)
    7: {"location": "forest", "clips": slice(0, 5), "chapter_clips": 5, "character_id": "protagonist", "image": "pure.png", "emotion": "determined", "pose": "close_up_intense"},
    8: {"location": "forest", "clips": slice(5, 11), "chapter_clips": 6, "character_id": "protagonist", "image": "pure.png", "emotion": "focused", "pose": "close_up_coding"},
    9: {"location": "forest", "clips": slice(11, 16), "chapter_clips": 5, "character_id": None, "image": None, "emotion": "isolation", "pose": "environment_only"},

    # Chapters 10-12: Kitchen (Return, desperation)
    10: {"location": "kitchen", "clips": slice(0, 5), "chapter_clips": 5, "character_id": "mother", "image": "mama.png", "emotion": "exhaustion", "pose": "working"},
    11: {"location": "kitchen", "clips": slice(5, 11), "chapter_clips": 6, "character_id": "brother", "image": "purebrother2.png", "emotion": "resentment", "pose": "standing_resentful"},
    12: {"location": "kitchen", "clips": slice(11, 16), "chapter_clips": 5, "character_id": "protagonist", "image": "pureteen.png", "emotion": "drowning", "pose": "desperate"},

    # Chapters 13-15: Park (The app, seduction)
    13: {"location": "park", "clips": slice(0, 7), "chapter_clips": 7, "character_id": "protagonist", "image": "pureyoung1.png", "emotion": "determined", "pose": "confident"},
    14: {"location": "park", "clips": slice(7, 13), "chapter_clips": 6, "character_id": "protagonist", "image": "pureyoung1.png", "emotion": "seduction", "pose": "beautiful_lie"},
    15: {"location": "park", "clips": slice(13, 20), "chapter_clips": 7, "character_id": "protagonist", "image": "pureyoung1.png", "emotion": "pride", "pose": "success"},

    # Chapters 16-18: Schoolyard (Glitch, dissolution)
    16: {"location": "schoolyard", "clips": slice(0, 6), "chapter_clips": 6, "character_id": "protagonist", "image": "pure.png", "emotion": "forgetting", "pose": "fragmented"},
    17: {"location": "schoolyard", "clips": slice(6, 12), "chapter_clips": 6, "character_id": "protagonist", "image": "pure.png", "emotion": "dissolution", "pose": "breaking"},
    18: {"location": "schoolyard", "clips": slice(12, 18), "chapter_clips": 6, "character_id": "father", "image": "puredadglitch.jpg", "emotion": "warning", "pose": "glitch_warning"},
}

# Build complete scene list
scenes = []
clip_index = 0

for chapter_num in sorted(chapter_mapping.keys()):
    chapter_info = chapter_mapping[chapter_num]
    location = chapter_info["location"]
    clips_slice = chapter_info["clips"]

    location_clips = clips_by_location[location]
    chapter_clips_list = location_clips[clips_slice]

    for clip_id in chapter_clips_list:
        # Calculate subtitle timing (each clip ~0.41 seconds, 99 clips = 8.6 seconds)
        clip_time = clip_index * 0.41
        clip_end = (clip_index + 1) * 0.41

        scene = {
            "clip_id": clip_id,
            "chapter": chapter_num,
            "location": location,
            "character_id": chapter_info["character_id"],
            "image": chapter_info["image"],
            "position": {"x": 640, "y": 540, "scale": 1.0},
            "pose": chapter_info["pose"],
            "emotion": chapter_info["emotion"],
            "subtitle_timing": {"start": round(clip_time, 2), "end": round(clip_end, 2)},
            "notes": f"Chapter {chapter_num}: {chapter_info['emotion']}"
        }

        scenes.append(scene)
        clip_index += 1

# Build complete metadata
metadata = {
    "metadata": {
        "title": "No Sand Beach — Silent Film",
        "format": "silent_film_with_character_animation",
        "chapters": 21,
        "locations": 6,
        "total_scenes": len(scenes),
        "total_duration_seconds": 8.61,
        "subtitle_file": "subtitles.srt",
        "notes": "All 99 clips with character pose variants per emotional beat. Silent film: character gesture + text subtitles communicate the story."
    },
    "characters": [
        {
            "id": "protagonist",
            "name": "Pure (protagonist)",
            "role": "Narrator, main character, age progression",
            "images": {
                "teen": "pureteen.png",
                "intimate": "pure.png",
                "young_adult": "pureyoung1.png",
                "elder": "pureolder1.png"
            }
        },
        {
            "id": "mother",
            "name": "Delia (mother)",
            "role": "Sacrificial presence, love, family anchor",
            "images": {"primary": "mama.png"}
        },
        {
            "id": "brother",
            "name": "Marcus (brother)",
            "role": "Sibling trauma, resentment, reconciliation",
            "images": {
                "grieving": "purebrother.png",
                "resentful": "purebrother2.png",
                "reconciling": "purebrother5.png",
                "peace": "purebrother6.png"
            }
        },
        {
            "id": "father",
            "name": "Earl (father, glitch)",
            "role": "Memory, haunting, warning, absence",
            "images": {"glitch": "puredadglitch.jpg"}
        }
    ],
    "scenes": scenes
}

# Write metadata
output_file = "character_metadata_silent.json"
with open(output_file, "w") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"✓ Generated comprehensive metadata: {output_file}")
print(f"  Total scenes: {len(scenes)}")
print(f"  Chapters: {metadata['metadata']['chapters']}")
print(f"  Duration: {metadata['metadata']['total_duration_seconds']}s")
print(f"  Characters: {len(metadata['characters'])}")
print(f"\nChapter summary:")
for ch in sorted(chapter_mapping.keys()):
    print(f"  Chapter {ch}: {chapter_mapping[ch]['character_id']} - {chapter_mapping[ch]['emotion']}")
