"""Tests for the NO SAND BEACH ScenePlan builder.

The builder emits Godot ``.tres`` resources that no CI runner here can load --
there is no Godot binary in this environment. So these tests carry the weight
that a real editor import would: they check the generated text against the
addon's actual GDScript contracts (script paths must exist on disk, beat fields
must match the ``@export`` names) and they check the Python validator against
the same ERROR rules ``ScenePlanValidator`` enforces.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NSB = REPO / "godot_project" / "NO_SAND_BEACH"
ADDON = REPO / "godot_project" / "addons" / "scene_animator"


def _load_builder():
    """Import the builder by path -- it lives under the Godot project, not a package.

    The module must be registered in ``sys.modules`` before execution: it uses
    ``@dataclass`` under ``from __future__ import annotations``, and dataclasses
    resolves those string annotations by looking its own module back up there.
    """
    spec = importlib.util.spec_from_file_location(
        "scene_plan_builder", NSB / "tools" / "scene_plan_builder.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = _load_builder()


@pytest.fixture
def registry() -> dict:
    return json.loads((NSB / "scenes" / "capabilities" / "nsb_capabilities.json").read_text())


def beatsheets() -> list[Path]:
    return sorted((NSB / "scenes" / "beatsheets").glob("*.json"))


def minimal_plan(**overrides) -> dict:
    plan = {
        "plan_id": "test_plan",
        "actors": [{"actor_id": "a", "display_name": "A"}],
        "beats": [
            {"type": "wait", "beat_id": "b1", "duration_seconds": 1.0, "next_beat_id": "b2"},
            {"type": "end", "beat_id": "b2"},
        ],
    }
    plan.update(overrides)
    return plan


# ---------------------------------------------------------------- validator


def test_minimal_plan_is_valid():
    assert builder.validate_plan(minimal_plan()).is_valid


def test_empty_plan_is_an_error():
    result = builder.validate_plan(minimal_plan(beats=[]))
    assert not result.is_valid
    assert any(i.code == "empty_plan" for i in result.errors)


def test_duplicate_beat_id_is_an_error():
    plan = minimal_plan(
        beats=[
            {"type": "wait", "beat_id": "dupe", "duration_seconds": 1.0},
            {"type": "wait", "beat_id": "dupe", "duration_seconds": 1.0},
        ]
    )
    result = builder.validate_plan(plan)
    assert any(i.code == "duplicate_beat_id" for i in result.errors)


def test_duplicate_actor_id_is_an_error():
    plan = minimal_plan(actors=[{"actor_id": "a"}, {"actor_id": "a"}])
    assert any(i.code == "duplicate_actor_id" for i in builder.validate_plan(plan).errors)


def test_dangling_next_beat_is_an_error():
    plan = minimal_plan(
        beats=[{"type": "wait", "beat_id": "b1", "next_beat_id": "nowhere"}]
    )
    assert any(i.code == "dangling_next" for i in builder.validate_plan(plan).errors)


def test_dialogue_without_speaker_is_an_error():
    plan = minimal_plan(
        beats=[{"type": "dialogue", "beat_id": "d1", "dialogue_id": "x"}]
    )
    assert any(i.code == "missing_speaker" for i in builder.validate_plan(plan).errors)


def test_action_without_actor_is_an_error():
    plan = minimal_plan(beats=[{"type": "action", "beat_id": "a1", "action_id": "idle"}])
    assert any(i.code == "missing_actor" for i in builder.validate_plan(plan).errors)


def test_all_beats_disabled_is_an_error():
    plan = minimal_plan(
        beats=[{"type": "wait", "beat_id": "b1", "enabled": False}]
    )
    assert any(i.code == "no_enabled_beats" for i in builder.validate_plan(plan).errors)


def test_unreachable_beat_is_a_warning_not_an_error():
    """Orphan beats are runnable-but-suspicious, matching the addon's severity."""
    plan = minimal_plan(
        beats=[
            {"type": "wait", "beat_id": "b1", "duration_seconds": 1.0},
            {"type": "wait", "beat_id": "orphan", "duration_seconds": 1.0},
        ]
    )
    result = builder.validate_plan(plan)
    assert result.is_valid
    assert any(i.code == "unreachable_beat" for i in result.warnings)


def test_unknown_action_is_an_error_against_a_registry(registry):
    plan = minimal_plan(
        beats=[
            {"type": "action", "beat_id": "a1", "actor_id": "a", "action_id": "nope"}
        ]
    )
    assert any(i.code == "unknown_action" for i in builder.validate_plan(plan, registry).errors)


def test_unknown_camera_mode_is_an_error_against_a_registry(registry):
    plan = minimal_plan(beats=[{"type": "camera", "beat_id": "c1", "camera_mode_id": "nope"}])
    errors = builder.validate_plan(plan, registry).errors
    assert any(i.code == "unknown_camera_mode" for i in errors)


def test_missing_registry_only_warns():
    result = builder.validate_plan(minimal_plan())
    assert result.is_valid
    assert any(i.code == "no_capability_registry" for i in result.warnings)


# ---------------------------------------------------------------- generation


def test_unknown_beat_type_refuses_to_build():
    with pytest.raises(builder.BuildError, match="unknown type"):
        builder.build_tres(minimal_plan(beats=[{"type": "teleport", "beat_id": "x"}]))


def test_build_emits_only_the_beat_types_used():
    """A plan of waits shouldn't drag in the dialogue or camera scripts."""
    text = builder.build_tres(minimal_plan())
    assert "wait_beat.gd" in text
    assert "end_beat.gd" in text
    assert "dialogue_beat.gd" not in text
    assert "camera_beat.gd" not in text


def test_stringname_and_string_fields_serialize_differently():
    text = builder.build_tres(minimal_plan())
    assert 'plan_id = &"test_plan"' in text  # StringName
    assert 'display_name = "A"' in text  # plain String


def test_load_steps_counts_every_resource_entry():
    text = builder.build_tres(minimal_plan())
    header = text.splitlines()[0]
    declared = int(header.split("load_steps=")[1].split()[0])
    actual = text.count("[ext_resource ") + text.count("[sub_resource ") + 1
    assert declared == actual


def test_quotes_in_prose_are_escaped():
    """Beat notes carry dialogue with quotation marks; unescaped they'd corrupt the file."""
    plan = minimal_plan(
        beats=[{"type": "wait", "beat_id": "b1", "note": 'She said "that\'s on you".'}]
    )
    text = builder.build_tres(plan)
    assert r"\"that's on you\"" in text


# ------------------------------------------------- contracts against the addon


def test_every_referenced_script_exists_on_disk():
    """Catches a typo'd res:// path that would fail only at Godot import time."""
    for spec in builder.BEAT_TYPES.values():
        rel = spec["script"].removeprefix("res://")
        assert (REPO / "godot_project" / rel).is_file(), f"missing {spec['script']}"


def test_beat_fields_match_the_gdscript_exports():
    """Every field the builder emits must be a real @export on the beat class."""
    for beat_type, spec in builder.BEAT_TYPES.items():
        rel = spec["script"].removeprefix("res://")
        source = (REPO / "godot_project" / rel).read_text()
        exported = {
            line.split("var ")[1].split(":")[0].split(" ")[0].strip()
            for line in source.splitlines()
            if line.strip().startswith("@export") and "var " in line
        }
        # Multi-line @export_enum declarations put `var` on the next line.
        for i, line in enumerate(source.splitlines()):
            if line.strip().startswith("var ") and i > 0:
                prev = source.splitlines()[i - 1].strip()
                if prev.startswith("@export"):
                    exported.add(line.split("var ")[1].split(":")[0].split(" ")[0].strip())
        for _, (tres_field, _kind) in spec["fields"].items():
            assert tres_field in exported, f"{beat_type}: '{tres_field}' is not an @export"


def test_base_fields_match_scene_beat_exports():
    source = (ADDON / "data" / "scene_beat.gd").read_text()
    exported = {
        line.split("var ")[1].split(":")[0].split(" ")[0].strip()
        for line in source.splitlines()
        if line.strip().startswith("@export") and "var " in line
    }
    for _, (tres_field, _kind) in builder.BASE_FIELDS.items():
        assert tres_field in exported, f"'{tres_field}' is not an @export on SceneBeat"


# ------------------------------------------------------- the shipped content


@pytest.mark.parametrize("path", beatsheets(), ids=lambda p: p.stem)
def test_shipped_beatsheet_validates_clean(path, registry):
    """Every beat sheet in the film must have zero errors AND zero warnings.

    Warnings are held to zero here (stricter than the addon's "valid" bar)
    because every warning class in this validator -- unreachable beats, unknown
    actors -- signals a real authoring mistake in a linear film sequence.
    """
    plan = json.loads(path.read_text())
    result = builder.validate_plan(plan, registry)
    assert result.is_valid, "\n".join(str(i) for i in result.errors)
    assert not result.warnings, "\n".join(str(i) for i in result.warnings)


@pytest.mark.parametrize("path", beatsheets(), ids=lambda p: p.stem)
def test_shipped_beatsheet_builds(path):
    text = builder.build_tres(json.loads(path.read_text()))
    assert text.startswith("[gd_resource ")
    assert "[resource]" in text


@pytest.mark.parametrize("path", beatsheets(), ids=lambda p: p.stem)
def test_shipped_beatsheet_ends_in_an_end_beat(path):
    """A film sequence has to terminate, or the director never emits scene_finished."""
    plan = json.loads(path.read_text())
    assert plan["beats"][-1]["type"] == "end"


@pytest.mark.parametrize("path", beatsheets(), ids=lambda p: p.stem)
def test_committed_tres_is_current(path):
    """The .tres on disk must match what the builder produces from the beat sheet.

    Both are committed, so this catches a beat sheet edited without a rebuild.
    """
    plan = json.loads(path.read_text())
    generated = NSB / "scenes" / "plans" / f"{path.stem}.tres"
    assert generated.is_file(), f"{generated.name} has not been generated yet"
    assert generated.read_text() == builder.build_tres(plan), (
        f"{generated.name} is stale -- rebuild it with:\n"
        f"  python3 tools/scene_plan_builder.py build {path} {generated}"
    )


def test_capability_registry_builds_and_covers_every_referenced_id(registry):
    """No plan may reference an action or camera mode the registry doesn't define."""
    text = builder.build_capability_registry(registry)
    assert "SceneCapabilityRegistry" in text

    action_ids = {a["id"] for a in registry["actions"]}
    camera_ids = {c["id"] for c in registry["camera_modes"]}
    for path in beatsheets():
        for beat in json.loads(path.read_text())["beats"]:
            if beat["type"] == "action":
                assert beat["action_id"] in action_ids, f"{path.name}: {beat['action_id']}"
            elif beat["type"] == "camera":
                cam = beat["camera_mode_id"]
                assert cam in camera_ids, f"{path.name}: {cam}"
