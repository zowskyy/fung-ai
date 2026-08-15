"""Generic JSON Schema loading and validation helpers."""
import json
from pathlib import Path

import jsonschema

CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts"


def load_schema(schema_path: Path) -> dict:
    """Read and parse a JSON schema file."""
    return json.loads(schema_path.read_text())


def validate_json(data: dict, schema_path: Path) -> tuple[bool, str]:
    """Validate a dict against a schema file, returning (ok, message)."""
    schema = load_schema(schema_path)
    try:
        jsonschema.validate(data, schema)
    except jsonschema.exceptions.ValidationError as e:
        path = e.json_path if hasattr(e, "json_path") else str(e.path)
        return False, f"{e.message} (at {path})"
    return True, ""


def validate_file(json_path: Path, schema_path: Path) -> tuple[bool, str]:
    """Load JSON from a file and validate it against a schema file."""
    try:
        data = json.loads(json_path.read_text())
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {json_path}: {e}"
    return validate_json(data, schema_path)
