"""Structural validation for replay.json content."""
import json
import re
from pathlib import Path

from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR

_HASH_PATTERN = re.compile(r"^[a-f0-9]{64}$")


def validate_replay_structure(replay: dict) -> list[str]:
    """Check frame order in input_sequence and final_hash format."""
    problems = []

    last_frame = None
    for entry in replay["input_sequence"]:
        frame = entry["frame"]
        if last_frame is not None and frame < last_frame:
            problems.append(
                f"input_sequence frame {frame} is out of order (comes after {last_frame})"
            )
            break
        last_frame = frame

    if not _HASH_PATTERN.match(replay["final_hash"]):
        problems.append(f"final_hash '{replay['final_hash']}' does not match ^[a-f0-9]{{64}}$")

    return problems


def validate_replay_file(path: Path) -> tuple[bool, list[str]]:
    """Validate a replay.json file against schema and structural rules."""
    ok, message = schema_validator.validate_file(path, CONTRACTS_DIR / "replay.schema.json")
    problems = [] if ok else [message]

    if ok:
        replay = json.loads(path.read_text())
        problems.extend(validate_replay_structure(replay))

    return ok and not problems, problems
