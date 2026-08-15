"""Build and write schema-validated encounter.json content."""
import json
from pathlib import Path

from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR

_ENCOUNTER_SCHEMA = CONTRACTS_DIR / "encounter.schema.json"


def export_encounter(
    encounter_id: str,
    entity: str,
    spawn_point: str,
    narrative_id: str | None = None,
    difficulty: float = 0.0,
) -> dict:
    """Build a validated encounter dict, omitting narrative_id when None."""
    result = {
        "version": 1,
        "id": encounter_id,
        "entity": entity,
        "spawn_point": spawn_point,
        "difficulty": difficulty,
    }
    if narrative_id is not None:
        result["narrative_id"] = narrative_id

    ok, message = schema_validator.validate_json(result, _ENCOUNTER_SCHEMA)
    if not ok:
        raise ValueError(message)

    return result


def write_encounter(path: Path, **kwargs) -> Path:
    """Export an encounter and write it to disk as JSON."""
    result = export_encounter(**kwargs)
    path.write_text(json.dumps(result, indent=2))
    return path
