"""Round-trip tests for fung_tools.exporters: export, then re-validate independently."""
from pathlib import Path

import pytest

from fung_tools.exporters import animation_exporter, encounter_exporter, world_exporter
from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR


def test_export_world_round_trip():
    """A small grid + spawns exports to a world dict that independently re-validates."""
    grid = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
    spawns = [{"id": "player_spawn", "x": 1, "y": 1, "type": "player"}]

    result = world_exporter.export_world(grid, spawns, world_id="test_world", seed=7)

    ok, message = schema_validator.validate_json(result, CONTRACTS_DIR / "world.schema.json")
    assert ok, message
    assert result["width"] == 3
    assert result["height"] == 3
    assert result["tiles"] == [1, 1, 1, 1, 0, 1, 1, 1, 1]


def test_export_world_accepts_numpy_grid():
    """A numpy 2D array is normalized to list-of-lists before flattening."""
    np = pytest.importorskip("numpy")
    grid = np.array([[0, 0], [0, 0]])
    spawns = [{"id": "player_spawn", "x": 0, "y": 0, "type": "player"}]

    result = world_exporter.export_world(grid, spawns)

    ok, message = schema_validator.validate_json(result, CONTRACTS_DIR / "world.schema.json")
    assert ok, message


def test_export_encounter_round_trip():
    """export_encounter produces a dict that independently re-validates."""
    result = encounter_exporter.export_encounter(
        encounter_id="test_encounter",
        entity="test_entity_01",
        spawn_point="boss_spawn",
        narrative_id="test_narrative",
        difficulty=1.5,
    )

    ok, message = schema_validator.validate_json(result, CONTRACTS_DIR / "encounter.schema.json")
    assert ok, message


def test_export_encounter_omits_narrative_id_when_none():
    """narrative_id is omitted entirely (not null) when not supplied."""
    result = encounter_exporter.export_encounter(
        encounter_id="test_encounter",
        entity="test_entity_01",
        spawn_point="boss_spawn",
    )

    assert "narrative_id" not in result
    ok, message = schema_validator.validate_json(result, CONTRACTS_DIR / "encounter.schema.json")
    assert ok, message


def test_export_animation_manifest_round_trip():
    """export_animation_manifest produces a dict that independently re-validates."""
    clips = [
        {"id": "idle", "sprite_sheet": "res://art/idle.png", "frame_count": 4, "fps": 6, "loop": True},
    ]
    result = animation_exporter.export_animation_manifest("test_animset", clips)

    ok, message = schema_validator.validate_json(result, CONTRACTS_DIR / "animation_manifest.schema.json")
    assert ok, message


def test_export_animation_manifest_raises_on_invalid_clip():
    """Missing a required clip field surfaces as a ValueError from self-validation."""
    clips = [{"id": "idle", "sprite_sheet": "res://art/idle.png"}]  # missing frame_count, fps
    with pytest.raises(ValueError):
        animation_exporter.export_animation_manifest("test_animset", clips)


def test_write_world_writes_valid_json(tmp_path: Path):
    """write_world writes a file that re-validates when read back."""
    grid = [[0, 0], [0, 0]]
    spawns = [{"id": "player_spawn", "x": 0, "y": 0, "type": "player"}]
    out_path = tmp_path / "world.json"

    world_exporter.write_world(out_path, grid, spawns)

    ok, message = schema_validator.validate_file(out_path, CONTRACTS_DIR / "world.schema.json")
    assert ok, message
