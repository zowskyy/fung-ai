"""Tests for the NO SAND BEACH animation shot list.

The shot list is what the Blender side works from, so its failure mode is
expensive and quiet: if it under-reports, someone discovers a missing clip at
integration time; if it over-reports, someone animates a cycle the film never
plays. Both are days of wasted work, so the derivation is pinned here.

Two of these tests gate the film's content rather than the tool: every declared
character must actually animate, and every registered action must actually be
used. Both classes of problem are invisible in a beat sheet diff.
"""

from __future__ import annotations

import importlib.util
import json
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


shotlist_tool = _load_module("animation_shotlist")


@pytest.fixture
def registry() -> dict:
    path = NSB / "scenes" / "capabilities" / "nsb_capabilities.json"
    return json.loads(path.read_text())


@pytest.fixture
def beatsheets() -> list[dict]:
    paths = sorted((NSB / "scenes" / "beatsheets").glob("*.json"))
    return [json.loads(p.read_text()) for p in paths]


@pytest.fixture
def shotlist(beatsheets, registry) -> dict:
    return shotlist_tool.build_shotlist(beatsheets, registry)


# ------------------------------------------------------------- derivation


def test_action_beat_maps_to_its_registry_clip():
    """action_id is indirected through the registry -- 'rise' produces 'stand_up'."""
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "a", "display_name": "A"}],
        "beats": [{"type": "action", "beat_id": "b", "actor_id": "a", "action_id": "rise"}],
    }]
    registry = {
        "actions": [{"id": "rise", "animation_state": "stand_up", "motion_mode": "none"}]
    }
    result = shotlist_tool.build_shotlist(sheets, registry)
    assert "stand_up" in result["characters"]["a"]["clips"]
    assert result["characters"]["a"]["clips"]["stand_up"]["actions"] == ["rise"]


def test_dialogue_beat_implies_a_talk_clip_for_the_speaker():
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "a", "display_name": "A"}],
        "beats": [
            {"type": "dialogue", "beat_id": "b", "speaker_actor_id": "a", "dialogue_id": "d"}
        ],
    }]
    result = shotlist_tool.build_shotlist(sheets, {"actions": []})
    assert "talk" in result["characters"]["a"]["clips"]


def test_move_to_beat_takes_its_clip_from_locomotion_mode():
    """MoveToBeat names no action_id, so locomotion_mode is the only clip signal."""
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "a", "display_name": "A"}],
        "beats": [{"type": "move_to", "beat_id": "b", "actor_id": "a", "locomotion_mode": "walk"}],
    }]
    result = shotlist_tool.build_shotlist(sheets, {"actions": []})
    assert "walk" in result["characters"]["a"]["clips"]


def test_voiceover_actors_need_no_clips():
    """Narrators speak but are never on screen, so they must not enter the shot list."""
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "vo", "display_name": "VO", "actor_tags": ["voiceover"]}],
        "beats": [
            {"type": "dialogue", "beat_id": "b", "speaker_actor_id": "vo", "dialogue_id": "d"}
        ],
    }]
    result = shotlist_tool.build_shotlist(sheets, {"actions": []})
    assert "vo" not in result["characters"]


def test_a_clip_used_by_two_actions_is_reported_once_with_both_actions():
    """`enter` and `exit` both resolve to `walk`; that is one clip, not two."""
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "a", "display_name": "A"}],
        "beats": [
            {"type": "action", "beat_id": "b1", "actor_id": "a", "action_id": "enter"},
            {"type": "action", "beat_id": "b2", "actor_id": "a", "action_id": "exit"},
        ],
    }]
    registry = {"actions": [
        {"id": "enter", "animation_state": "walk"},
        {"id": "exit", "animation_state": "walk"},
    ]}
    result = shotlist_tool.build_shotlist(sheets, registry)
    clips = result["characters"]["a"]["clips"]
    assert list(clips) == ["walk"]
    assert sorted(clips["walk"]["actions"]) == ["enter", "exit"]


def test_clips_reached_without_an_action_id_are_not_called_unused():
    """The bug this guards: `walk` and `talk` are reached via move_to and dialogue.

    Reporting them as unused would tell an animator to skip the two most-used
    clips in the film.
    """
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "a", "display_name": "A"}],
        "beats": [
            {"type": "move_to", "beat_id": "b1", "actor_id": "a", "locomotion_mode": "walk"},
            {"type": "dialogue", "beat_id": "b2", "speaker_actor_id": "a", "dialogue_id": "d"},
        ],
    }]
    registry = {"actions": [
        {"id": "walk", "animation_state": "walk"},
        {"id": "talk", "animation_state": "talk"},
        {"id": "genuinely_dead", "animation_state": "nothing_uses_this"},
    ]}
    result = shotlist_tool.build_shotlist(sheets, registry)
    assert result["unused_actions"] == ["genuinely_dead"]


def test_declared_but_unanimated_actors_are_flagged():
    sheets = [{
        "plan_id": "p",
        "actors": [
            {"actor_id": "a", "display_name": "A"},
            {"actor_id": "bystander", "display_name": "Bystander"},
        ],
        "beats": [{"type": "dialogue", "beat_id": "b", "speaker_actor_id": "a",
                   "target_actor_id": "bystander", "dialogue_id": "d"}],
    }]
    result = shotlist_tool.build_shotlist(sheets, {"actions": []})
    assert result["characters_without_clips"] == ["bystander"]


def test_markdown_renders_every_character():
    sheets = [{
        "plan_id": "p",
        "actors": [{"actor_id": "a", "display_name": "Alice"}],
        "beats": [
            {"type": "dialogue", "beat_id": "b", "speaker_actor_id": "a", "dialogue_id": "d"}
        ],
    }]
    result = shotlist_tool.build_shotlist(sheets, {"actions": []})
    text = shotlist_tool.render_markdown(result)
    assert "Alice" in text
    assert "`talk`" in text


# ------------------------------------------------------- the shipped film


def test_every_declared_character_actually_animates(shotlist):
    """An actor bound to a plan but performing nothing would stand in frame dead.

    When this fails the fix is usually a missing beat, not a removed actor --
    see s01_14_held, added because Pure's age-7 design had no clip of its own
    while Earl's `hold_child` animated only Earl.
    """
    assert shotlist["characters_without_clips"] == [], (
        "actors declared but never animated: "
        + ", ".join(shotlist["characters_without_clips"])
    )


def test_no_registered_action_goes_unused(shotlist):
    """Dead registry entries invite animating clips the film never plays."""
    assert shotlist["unused_actions"] == [], (
        "registry actions no sequence uses: " + ", ".join(shotlist["unused_actions"])
    )


def test_protagonist_carries_the_heaviest_clip_load(shotlist):
    """Sanity check on the join: if Pure isn't the biggest role, the mapping broke."""
    by_clips = sorted(
        shotlist["characters"].items(), key=lambda kv: kv[1]["clip_count"], reverse=True
    )
    assert by_clips[0][0] == "pure"


def test_the_title_payoff_clip_exists_and_belongs_to_pure(shotlist):
    """Beat 6.02 is the film's title payoff; its clips must survive any refactor."""
    pure_clips = shotlist["characters"]["pure"]["clips"]
    assert "touch_sand" in pure_clips
    assert "kneel" in pure_clips


def test_committed_shotlist_is_current(shotlist):
    """Both outputs are committed, so a beat sheet edited without a regen fails here."""
    generated = NSB / "scenes" / "capabilities" / "animation_shotlist.json"
    assert generated.is_file()
    assert json.loads(generated.read_text()) == shotlist

    markdown = NSB / "ANIMATION_SHOTLIST.md"
    assert markdown.is_file()
    assert markdown.read_text() == shotlist_tool.render_markdown(shotlist)
