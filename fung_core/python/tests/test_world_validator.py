"""Tests for fung_tools.validators.world_validator."""
import json
from pathlib import Path

from fung_tools.validators import world_validator

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "cave_boss"


def _load_cave_world() -> dict:
    return json.loads((EXAMPLES_DIR / "cave_world.json").read_text())


def test_valid_world_has_no_problems():
    """The real cave_world.json example is structurally valid."""
    world = _load_cave_world()
    assert world_validator.validate_world_structure(world) == []


def test_disconnected_spawn_is_reported():
    """Walling off the boss spawn from the player spawn is caught by BFS reachability."""
    world = _load_cave_world()

    # cave_world.json is a 5x5 room bordered by walls, open floor from (1,1) to (3,3).
    # Wall off column x=2 (rows 1-3) to split the room, isolating boss_spawn at (3,3)
    # from player_spawn at (1,1).
    width = world["width"]
    tiles = list(world["tiles"])
    for y in (1, 2, 3):
        tiles[y * width + 2] = 1
    world["tiles"] = tiles

    problems = world_validator.validate_world_structure(world)
    assert any("boss_spawn" in p and "not reachable" in p for p in problems)
