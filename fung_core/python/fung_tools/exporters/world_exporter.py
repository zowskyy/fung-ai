"""Build and write schema-validated world.json content."""
import json
from pathlib import Path

from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR

_WORLD_SCHEMA = CONTRACTS_DIR / "world.schema.json"


def export_world(grid, spawns: list[dict], world_id: str = "generated_world", seed: int = 0) -> dict:
    """Flatten a 2D grid (list-of-lists or numpy array) into a validated world dict."""
    if hasattr(grid, "tolist"):
        grid = grid.tolist()

    height = len(grid)
    width = len(grid[0])
    tiles = [cell for row in grid for cell in row]

    result = {
        "version": 1,
        "id": world_id,
        "seed": seed,
        "width": width,
        "height": height,
        "tiles": tiles,
        "spawns": spawns,
    }

    ok, message = schema_validator.validate_json(result, _WORLD_SCHEMA)
    if not ok:
        raise ValueError(message)

    return result


def write_world(path: Path, grid, spawns: list[dict], world_id: str = "generated_world", seed: int = 0) -> Path:
    """Export a world and write it to disk as JSON."""
    result = export_world(grid, spawns, world_id=world_id, seed=seed)
    path.write_text(json.dumps(result, indent=2))
    return path
