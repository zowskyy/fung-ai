"""Build and write schema-validated animation_manifest.json content."""
import json
from pathlib import Path

from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR

_ANIMATION_SCHEMA = CONTRACTS_DIR / "animation_manifest.schema.json"


def export_animation_manifest(manifest_id: str, clips: list[dict]) -> dict:
    """Build a validated animation manifest dict from a list of clip dicts."""
    result = {
        "version": 1,
        "id": manifest_id,
        "clips": clips,
    }

    ok, message = schema_validator.validate_json(result, _ANIMATION_SCHEMA)
    if not ok:
        raise ValueError(message)

    return result


def write_animation_manifest(path: Path, manifest_id: str, clips: list[dict]) -> Path:
    """Export an animation manifest and write it to disk as JSON."""
    result = export_animation_manifest(manifest_id, clips)
    path.write_text(json.dumps(result, indent=2))
    return path
