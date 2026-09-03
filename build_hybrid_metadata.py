#!/usr/bin/env python3
"""
Build comprehensive metadata for No Sand Beach 5-minute silent film.
Maps all 99 graded clips to the 5-minute script with hybrid pacing.
Characters: Pure (protagonist), Del (mother), Shadow (brother), E (father).
"""
import json
from pathlib import Path

# Graded clips structure (from coherence_pass output)
clips_by_location = {
    "beach": [
        "beach_01_a", "beach_01_b", "beach_01_c",
        "beach_02_a", "beach_02_b", "beach_02_c",
        "beach_03_a", "beach_03_b", "beach_03_c", "beach_03_d", "beach_03_e", "beach_03_f",
    ],  # 12 clips
    "car": [
        "car_01_a", "car_01_b", "car_01_c", "car_01_d", "car_01_e",
        "car_02_a", "car_02_b", "car_02_c", "car_02_d", "car_02_e",
        "car_03_a", "car_03_b", "car_03_c", "car_03_d", "car_03_e", "car_03_f", "car_03_g",
    ],  # 17 clips
    "forest": [
        "forest_01_a", "forest_01_b", "forest_01_c", "forest_01_d", "forest_01_e", "forest_01_f",
        "forest_02_a", "forest_02_b", "forest_02_c", "forest_02_d",
        "forest_03_a", "forest_03_b", "forest_03_c", "forest_03_d", "forest_03_e", "forest_03_f",
    ],  # 16 clips
    "kitchen": [
        "kitchen_01_a", "kitchen_01_b", "kitchen_01_c", "kitchen_01_d", "kitchen_01_e",
        "kitchen_02_a", "kitchen_02_b", "kitchen_02_c", "kitchen_02_d", "kitchen_02_e", "kitchen_02_f",
        "kitchen_03_a", "kitchen_03_b", "kitchen_03_c", "kitchen_03_d", "kitchen_03_e",
    ],  # 16 clips
    "park": [
        "park_01_a", "park_01_b", "park_01_c", "park_01_d", "park_01_e", "park_01_f", "park_01_g", "park_01_h",
        "park_02_a", "park_02_b", "park_02_c", "park_02_d", "park_02_e", "park_02_f",
        "park_03_a", "park_03_b", "park_03_c", "park_03_d", "park_03_e", "park_03_f",
    ],  # 20 clips
    "schoolyard": [
        "schoolyard_01_a", "schoolyard_01_b", "schoolyard_01_c", "schoolyard_01_d", "schoolyard_01_e",
        "schoolyard_01_f", "schoolyard_01_g", "schoolyard_01_h", "schoolyard_01_i",
        "schoolyard_02_a", "schoolyard_02_b", "schoolyard_02_c", "schoolyard_02_d", "schoolyard_02_e",
        "schoolyard_02_f", "schoolyard_02_g", "schoolyard_02_h", "schoolyard_02_i",
    ],  # 18 clips
}

# Flatten clip list
all_clips = []
for location in ["beach", "car", "forest", "kitchen", "park", "schoolyard"]:
    all_clips.extend(clips_by_location[location])

print(f"Total clips: {len(all_clips)}")

# Define acts with timing and clip counts (adjusted to exactly 99 clips)
acts = [
    {
        "name": "Prologue: No Sand",
        "start_time": 0,
        "end_time": 38,
        "duration": 38,
        "clips_count": 10,
        "clip_duration": 3.8,
        "location": "beach",
        "characters": ["pure", None],
        "description": "Child Pure, ocean billboard, Delia working, empty rent jar"
    },
    {
        "name": "The Wound",
        "start_time": 38,
        "end_time": 75,
        "duration": 37,
        "clips_count": 12,
        "clip_duration": 3.08,
        "location": "car",
        "characters": ["pure", "shadow", "e"],
        "description": "Earl's death, police light, apartment silence, key ring"
    },
    {
        "name": "The Cage",
        "start_time": 75,
        "end_time": 116,
        "duration": 41,
        "clips_count": 14,
        "clip_duration": 2.93,
        "location": "forest",
        "characters": ["pure", None],
        "description": "Years passing, arrest, court, prison, code glowing"
    },
    {
        "name": "The Door",
        "start_time": 116,
        "end_time": 157,
        "duration": 41,
        "clips_count": 15,
        "clip_duration": 2.73,
        "location": "kitchen",
        "characters": ["pure", "del", "shadow"],
        "description": "Interview hope, rejection email, apartment desperation, shared meal"
    },
    {
        "name": "The Seduction",
        "start_time": 157,
        "end_time": 204,
        "duration": 47,
        "clips_count": 16,
        "clip_duration": 2.94,
        "location": "park",
        "characters": ["pure", None],
        "description": "App building, identity rewrite, office ascent, sand on desk, memory blur"
    },
    {
        "name": "The Glitch",
        "start_time": 204,
        "end_time": 235,
        "duration": 31,
        "clips_count": 14,
        "clip_duration": 2.21,
        "location": "schoolyard",
        "characters": ["pure", "e"],
        "description": "Code crash, missed calls, E appears, glitch overlay, memory archive",
        "note": "FAST PACING - candidate for interpolation"
    },
    {
        "name": "The Collapse",
        "start_time": 235,
        "end_time": 266,
        "duration": 31,
        "clips_count": 10,
        "clip_duration": 3.1,
        "location": "kitchen",
        "characters": ["pure", "del", "shadow"],
        "description": "Collapse, key ring, embracing, reconciliation, Del's line"
    },
    {
        "name": "Sand",
        "start_time": 266,
        "end_time": 300,
        "duration": 34,
        "clips_count": 8,
        "clip_duration": 4.25,
        "location": "beach",
        "characters": ["pure", "del", "shadow", None],
        "description": "Beach walk, barefoot sand, coding class, wisdom, family"
    }
]

# Verify clip count
total_clips_needed = sum(a["clips_count"] for a in acts)
print(f"Clips needed: {total_clips_needed}, available: {len(all_clips)}")

# Character metadata
characters_data = {
    "pure": {
        "id": "pure",
        "name": "Pure (protagonist)",
        "role": "7-year-old to 31-year-old; emotional core of story",
        "ages": {
            "child": "pureteen.png",
            "teen_grief": "pure.png",
            "teen_arrest": "pureteen.png",
            "prisoner": "pure.png",
            "released": "pureteen.png",
            "seduced": "pureyoung1.png",
            "dissolving": "pure.png",
            "collapsed": "pureyoung1.png",
            "elder": "pureolder1.png"
        }
    },
    "del": {
        "id": "del",
        "name": "Del (mother)",
        "role": "Delia; three jobs, exhausted love, emotional anchor",
        "images": {"primary": "mama.png"}
    },
    "shadow": {
        "id": "shadow",
        "name": "Shadow (brother)",
        "role": "Marcus; witness, protector, resentment, reconciliation",
        "ages": {
            "child": "purebrother.png",
            "grief": "purebrother.png",
            "struggle": "purebrother2.png",
            "embrace": "purebrother5.png",
            "peace": "purebrother6.png"
        }
    },
    "e": {
        "id": "e",
        "name": "E (father)",
        "role": "Earl; dead, glitching, warning, memory",
        "images": {"glitch": "puredadglitch.jpg"}
    }
}

# Build scenes by distributing clips across acts
scenes = []
clip_index = 0
current_time = 0

for act_idx, act in enumerate(acts):
    act_clips = all_clips[clip_index : clip_index + act["clips_count"]]
    clip_duration = act["clip_duration"]

    for local_idx, clip_id in enumerate(act_clips):
        scene_time = act["start_time"] + (local_idx * clip_duration)
        scene_end = scene_time + clip_duration

        # Assign character based on act
        if act["name"] == "Prologue: No Sand":
            if local_idx < 4:
                char_id = "pure"
                image = "pureteen.png"
                pose = "child_looking_horizon"
            elif local_idx < 8:
                char_id = "del"
                image = "mama.png"
                pose = "working_exhausted"
            else:
                char_id = "shadow"
                image = "purebrother.png"
                pose = "watching"

        elif act["name"] == "The Wound":
            if local_idx < 5:
                char_id = "pure"
                image = "pure.png"
                pose = "grief_close_up"
            elif local_idx < 10:
                char_id = "e"
                image = "puredadglitch.jpg"
                pose = "glitch_presence"
            else:
                char_id = "shadow"
                image = "purebrother.png"
                pose = "shared_trauma"

        elif act["name"] == "The Cage":
            char_id = "pure"
            if local_idx < 5:
                image = "pureteen.png"
                pose = "arrested_teen"
            elif local_idx < 12:
                image = "pure.png"
                pose = "prison_focused"
            else:
                image = "pure.png"
                pose = "code_glowing"

        elif act["name"] == "The Door":
            if local_idx < 5:
                char_id = "pure"
                image = "pureteen.png"
                pose = "interview_hope"
            elif local_idx < 11:
                char_id = "del"
                image = "mama.png"
                pose = "counting_cash"
            else:
                char_id = "shadow"
                image = "purebrother2.png"
                pose = "cooking_nothing"

        elif act["name"] == "The Seduction":
            char_id = "pure"
            if local_idx < 8:
                image = "pureyoung1.png"
                pose = "app_building"
            elif local_idx < 14:
                image = "pureyoung1.png"
                pose = "identity_rewrite"
            else:
                image = "pureyoung1.png"
                pose = "office_success"

        elif act["name"] == "The Glitch":
            if local_idx < 10:
                char_id = "pure"
                image = "pure.png"
                pose = "code_crash"
            else:
                char_id = "e"
                image = "puredadglitch.jpg"
                pose = "glitch_warning"

        elif act["name"] == "The Collapse":
            if local_idx < 4:
                char_id = "pure"
                image = "pureyoung1.png"
                pose = "collapsed"
            elif local_idx < 8:
                char_id = "del"
                image = "mama.png"
                pose = "holding_hand"
            else:
                char_id = "shadow"
                image = "purebrother5.png"
                pose = "embracing"

        elif act["name"] == "Sand":
            if local_idx < 4:
                char_id = "pure"
                image = "pureolder1.png"
                pose = "barefoot_sand"
            elif local_idx < 8:
                char_id = "del"
                image = "mama.png"
                pose = "family_together"
            else:
                char_id = "shadow"
                image = "purebrother6.png"
                pose = "peace"

        else:
            char_id = None
            image = None
            pose = None

        scene = {
            "clip_id": clip_id,
            "act": act_idx + 1,
            "act_name": act["name"],
            "location": act["location"],
            "character_id": char_id,
            "image": image,
            "position": {"x": 640, "y": 540, "scale": 1.0},
            "pose": pose,
            "emotion": act["name"].split(":")[1].strip().lower() if ":" in act["name"] else "neutral",
            "timing": {
                "start": round(scene_time, 2),
                "end": round(scene_end, 2),
                "duration": round(clip_duration, 2)
            },
            "notes": f"{act['name']} - {local_idx + 1}/{len(act_clips)} clips"
        }

        scenes.append(scene)

    clip_index += act["clips_count"]

# Build metadata
metadata = {
    "metadata": {
        "title": "No Sand Beach — Silent Film",
        "format": "silent_film_with_character_animation",
        "total_duration_seconds": 300,
        "total_scenes": len(scenes),
        "total_acts": len(acts),
        "pacing_strategy": "hybrid: poetic holds + variable cuts",
        "subtitle_file": "subtitles.srt",
        "production_notes": "5-minute silent film; character poses communicate emotion and gesture; Glitch section flagged for optional interpolation"
    },
    "characters": list(characters_data.values()),
    "acts": acts,
    "scenes": scenes
}

# Write metadata
output_file = "character_metadata_silent.json"
with open(output_file, "w") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"\n✓ Built comprehensive metadata: {output_file}")
print(f"  Total scenes: {len(scenes)}")
print(f"  Total duration: 5 minutes (300 seconds)")
print(f"  Characters: {len(characters_data)}")
print(f"\nAct breakdown:")
for i, act in enumerate(acts, 1):
    print(f"  Act {i}: {act['name']:<30} {act['clips_count']:>2} clips ({act['duration']:>3}s)")
print(f"\nInterpolation candidates:")
print(f"  - The Glitch (3:20-4:00): rapid cuts for disorientation")
print(f"  - The Door (1:45-2:30): rejection montage")

with open("metadata_summary.txt", "w") as f:
    f.write("NO SAND BEACH — METADATA SUMMARY\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Total duration: 5 minutes (300 seconds)\n")
    f.write(f"Total clips: {len(scenes)}\n")
    f.write(f"Characters: {len(characters_data)}\n\n")
    f.write("ACTS:\n")
    for i, act in enumerate(acts, 1):
        f.write(f"\nAct {i}: {act['name']}\n")
        f.write(f"  Time: {act['start_time']}-{act['end_time']}s\n")
        f.write(f"  Clips: {act['clips_count']}\n")
        f.write(f"  Pace: {act['clip_duration']:.1f}s per clip\n")
        f.write(f"  Description: {act['description']}\n")
        if "note" in act:
            f.write(f"  Note: {act['note']}\n")

print(f"\n✓ Summary written to metadata_summary.txt")
