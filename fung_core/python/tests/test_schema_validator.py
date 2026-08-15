"""Tests for fung_tools.validators.schema_validator against real example data."""
import json
from pathlib import Path

import pytest

from fung_tools.validators import schema_validator

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples" / "cave_boss"
CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"

EXAMPLE_TO_SCHEMA = {
    "cave_world.json": "world.schema.json",
    "cave_boss_entity.json": "entity.schema.json",
    "animation_manifest.json": "animation_manifest.schema.json",
    "narrative_sequence.json": "narrative.schema.json",
    "cave_encounter.json": "encounter.schema.json",
    "replay.json": "replay.schema.json",
    "project.json": "project.schema.json",
}


@pytest.mark.parametrize("example_name,schema_name", EXAMPLE_TO_SCHEMA.items())
def test_example_validates_against_schema(example_name, schema_name):
    """Every example file validates against its matching schema."""
    ok, message = schema_validator.validate_file(
        EXAMPLES_DIR / example_name, CONTRACTS_DIR / schema_name
    )
    assert ok, message


def test_missing_required_key_fails_validation(tmp_path):
    """Removing a required key from a valid example causes validation to fail."""
    data = json.loads((EXAMPLES_DIR / "cave_world.json").read_text())
    del data["width"]

    broken_path = tmp_path / "broken_world.json"
    broken_path.write_text(json.dumps(data))

    ok, message = schema_validator.validate_file(broken_path, CONTRACTS_DIR / "world.schema.json")
    assert not ok
    assert message
