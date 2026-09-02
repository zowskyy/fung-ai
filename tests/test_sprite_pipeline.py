"""Tests for the NO SAND BEACH sprite sheet contract.

The sheet layout is a contract between two systems that never meet: Blender
writes pixels, Godot reads frame rectangles out of them. Nothing checks that
they agree -- a row rendered out of order produces a clip playing a neighbour's
frames, which looks like bad animation rather than an error. So the arithmetic
that turns a row/column layout into Rect2 regions is pinned here.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NSB = REPO / "godot_project" / "NO_SAND_BEACH"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, NSB / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


pipeline = _load_module("sprite_pipeline")


def shotlist_fixture(clips: dict) -> dict:
    return {
        "characters": {
            "a": {
                "actor_id": "a",
                "display_name": "A",
                "sequences": ["p"],
                "clips": clips,
                "clip_count": len(clips),
                "beat_count": 1,
            }
        },
        "unused_actions": [],
        "characters_without_clips": [],
        "totals": {"characters": 1, "distinct_clips": len(clips), "clip_assignments": len(clips)},
    }


def clip(motion: str, beats: int = 1) -> dict:
    return {"clip": "x", "motion_mode": motion, "actions": ["x"], "beats": [{}] * beats}


@pytest.fixture
def spec() -> dict:
    path = NSB / "scenes" / "capabilities" / "sprite_sheet_spec.json"
    return json.loads(path.read_text())


# --------------------------------------------------------------- frame budget


def test_frame_count_follows_motion_mode():
    sl = shotlist_fixture({
        "pose": clip("none"),
        "cycle": clip("in_place"),
        "stride": clip("planar_root_motion"),
    })
    result = pipeline.build_sheet_spec(sl)
    frames = {c["clip"]: c["frames"] for c in result["characters"]["a"]["clips"]}
    assert frames["pose"] == 4
    assert frames["cycle"] == 6
    assert frames["stride"] == 8


def test_one_shot_poses_do_not_loop():
    """Looping a collapse would replay it forever under the held cameras this film uses."""
    sl = shotlist_fixture({"collapse": clip("none"), "idle": clip("in_place")})
    result = pipeline.build_sheet_spec(sl)
    loops = {c["clip"]: c["loop"] for c in result["characters"]["a"]["clips"]}
    assert loops["collapse"] is False
    assert loops["idle"] is True


# ------------------------------------------------------------------- layout


def test_rows_are_padded_not_packed():
    """Sheet width is the widest clip, so a clip's frame count never shifts other rows.

    Packing would make every row's origin depend on every previous row's length,
    turning one clip's frame-count change into a silent remap of everything after it.
    """
    sl = shotlist_fixture({"pose": clip("none"), "stride": clip("planar_root_motion")})
    result = pipeline.build_sheet_spec(sl)
    char = result["characters"]["a"]
    assert char["columns"] == 8  # the widest clip, not 4 + 8
    assert char["rows"] == 2


def test_clip_rows_are_assigned_in_sorted_order():
    """Alphabetical ordering keeps the layout stable across regenerations."""
    sl = shotlist_fixture({"zebra": clip("none"), "alpha": clip("none"), "middle": clip("none")})
    result = pipeline.build_sheet_spec(sl)
    rows = [(c["clip"], c["row"]) for c in result["characters"]["a"]["clips"]]
    assert rows == [("alpha", 0), ("middle", 1), ("zebra", 2)]


def test_sheet_size_is_frame_size_times_grid():
    sl = shotlist_fixture({"a": clip("none"), "b": clip("in_place")})
    result = pipeline.build_sheet_spec(sl, frame_size=(100, 200))
    char = result["characters"]["a"]
    assert char["columns"] == 6
    assert char["sheet_size"] == [600, 400]


# ------------------------------------------------- frame region arithmetic


def test_frame_regions_walk_columns_within_the_clip_row():
    sl = shotlist_fixture({"a": clip("none"), "b": clip("none")})
    result = pipeline.build_sheet_spec(sl, frame_size=(100, 200))
    scene = pipeline.build_character_scene(result["characters"]["a"])

    # Row 0 (clip "a") sits at y=0; row 1 (clip "b") at y=200.
    assert "Rect2(0, 0, 100, 200), Rect2(100, 0, 100, 200)" in scene
    assert "Rect2(0, 200, 100, 200), Rect2(100, 200, 100, 200)" in scene


def test_every_clip_gets_exactly_its_frame_count_of_regions():
    sl = shotlist_fixture({"stride": clip("planar_root_motion")})
    result = pipeline.build_sheet_spec(sl)
    scene = pipeline.build_character_scene(result["characters"]["a"])
    frames_line = next(ln for ln in scene.splitlines() if ln.startswith("frames = "))
    assert frames_line.count("Rect2(") == 8


# ------------------------------------------------------------- scene output


def test_scene_is_a_gd_scene_not_a_resource():
    """CharacterAnimator extends Sprite2D, so its clips live in a node, not a .tres."""
    sl = shotlist_fixture({"idle": clip("in_place")})
    result = pipeline.build_sheet_spec(sl)
    scene = pipeline.build_character_scene(result["characters"]["a"])
    assert scene.startswith("[gd_scene ")
    assert '[node name="A" type="Sprite2D"]' in scene
    assert "character_animator.gd" in scene


def test_initial_animation_prefers_a_looping_clip():
    """A one-shot pose as the resting state would hold a dramatic frame forever."""
    sl = shotlist_fixture({"collapse": clip("none"), "stand_idle": clip("in_place")})
    result = pipeline.build_sheet_spec(sl)
    scene = pipeline.build_character_scene(result["characters"]["a"])
    assert 'initial_animation = &"stand_idle"' in scene


def test_initial_animation_falls_back_when_nothing_loops():
    """Extras often have a single one-shot clip and nothing to rest in."""
    sl = shotlist_fixture({"gavel": clip("none")})
    result = pipeline.build_sheet_spec(sl)
    scene = pipeline.build_character_scene(result["characters"]["a"])
    assert 'initial_animation = &"gavel"' in scene


def test_load_steps_counts_every_resource_entry():
    sl = shotlist_fixture({"a": clip("none"), "b": clip("in_place")})
    result = pipeline.build_sheet_spec(sl)
    scene = pipeline.build_character_scene(result["characters"]["a"])
    declared = int(scene.splitlines()[0].split("load_steps=")[1].split()[0])
    assert declared == scene.count("[ext_resource ") + scene.count("[sub_resource ")


def test_character_without_clips_is_refused():
    with pytest.raises(pipeline.SpriteSpecError):
        pipeline.build_character_scene(
            {"actor_id": "ghost", "frame_size": [10, 10], "clips": [], "sheet_path": "x"}
        )


# ------------------------------------------------------- the shipped film


def test_shipped_spec_covers_every_animated_character(spec):
    shotlist = json.loads(
        (NSB / "scenes" / "capabilities" / "animation_shotlist.json").read_text()
    )
    animated = {a for a, e in shotlist["characters"].items() if e["clip_count"] > 0}
    assert set(spec["characters"]) == animated


def test_every_shipped_character_builds_a_valid_scene(spec):
    for actor_id, character in spec["characters"].items():
        scene = pipeline.build_character_scene(character)
        assert scene.startswith("[gd_scene "), actor_id
        assert "initial_animation = &" in scene, actor_id


def test_shipped_sheets_reference_a_per_character_texture_path(spec):
    for actor_id, character in spec["characters"].items():
        assert character["sheet_path"].startswith("res://NO_SAND_BEACH/assets/characters/")
        assert actor_id in character["sheet_path"]


def test_no_clip_name_would_break_tscn_serialization(spec):
    """Clip names become StringName keys and sub_resource ids, so they must be bare."""
    for character in spec["characters"].values():
        for clip_entry in character["clips"]:
            assert re.fullmatch(r"[a-z0-9_]+", clip_entry["clip"]), clip_entry["clip"]


def test_committed_spec_is_current(spec):
    shotlist = json.loads(
        (NSB / "scenes" / "capabilities" / "animation_shotlist.json").read_text()
    )
    assert pipeline.build_sheet_spec(shotlist) == spec

    markdown = NSB / "SPRITE_SHEET_SPEC.md"
    assert markdown.is_file()
    assert markdown.read_text() == pipeline.render_spec_markdown(spec)
