"""Structural validation for world.json content beyond basic schema checks."""
import json
from collections import deque
from pathlib import Path

from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR


def validate_world_structure(world: dict) -> list[str]:
    """Check tile count, spawn bounds, player presence, and reachability."""
    problems = []
    width = world["width"]
    height = world["height"]
    tiles = world["tiles"]
    spawns = world["spawns"]

    if len(tiles) != width * height:
        problems.append(
            f"tiles length {len(tiles)} does not equal width*height ({width}*{height}={width * height})"
        )

    for spawn in spawns:
        x, y = spawn["x"], spawn["y"]
        if not (0 <= x < width):
            problems.append(f"spawn '{spawn['id']}' has x={x} out of bounds [0,{width})")
        if not (0 <= y < height):
            problems.append(f"spawn '{spawn['id']}' has y={y} out of bounds [0,{height})")

    player_spawns = [s for s in spawns if s.get("type") == "player"]
    if not player_spawns:
        problems.append("no spawn with type 'player' found")

    if player_spawns and len(tiles) == width * height:
        player = player_spawns[0]
        reachable = _flood_fill(tiles, width, height, player["x"], player["y"])
        for spawn in spawns:
            if spawn is player:
                continue
            if (spawn["x"], spawn["y"]) not in reachable:
                problems.append(
                    f"spawn '{spawn['id']}' at ({spawn['x']},{spawn['y']}) "
                    "is not reachable from the player spawn"
                )

    return problems


def _flood_fill(tiles: list[int], width: int, height: int, start_x: int, start_y: int) -> set[tuple[int, int]]:
    """4-directional BFS over floor tiles (value 0) starting at (start_x, start_y)."""
    def is_floor(x: int, y: int) -> bool:
        if not (0 <= x < width and 0 <= y < height):
            return False
        return tiles[y * width + x] == 0

    visited: set[tuple[int, int]] = set()
    if not is_floor(start_x, start_y):
        return visited

    queue = deque([(start_x, start_y)])
    visited.add((start_x, start_y))
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if is_floor(nx, ny) and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    return visited


def validate_world_file(path: Path) -> tuple[bool, list[str]]:
    """Validate a world.json file against schema and structural rules."""
    ok, message = schema_validator.validate_file(path, CONTRACTS_DIR / "world.schema.json")
    problems = [] if ok else [message]

    if ok:
        world = json.loads(path.read_text())
        problems.extend(validate_world_structure(world))

    return ok and not problems, problems
