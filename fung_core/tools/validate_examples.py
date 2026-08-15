"""CLI to validate every example JSON file against its inferred contract schema."""
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = TOOLS_DIR.parent / "examples"
PYTHON_DIR = TOOLS_DIR.parent / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from fung_tools.validators import animation_validator, replay_validator, schema_validator, world_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR

# Order matters: more specific substrings must be checked before shorter ones
# they contain (e.g. "animation_manifest" before nothing else conflicts, but
# this ordering keeps future additions safe).
SCHEMA_RULES = [
    ("animation_manifest", "animation_manifest.schema.json"),
    ("encounter", "encounter.schema.json"),
    ("entity", "entity.schema.json"),
    ("narrative", "narrative.schema.json"),
    ("replay", "replay.schema.json"),
    ("world", "world.schema.json"),
    ("project", "project.schema.json"),
]

STRUCTURAL_VALIDATORS = {
    "world.schema.json": world_validator.validate_world_file,
    "animation_manifest.schema.json": animation_validator.validate_animation_file,
    "replay.schema.json": replay_validator.validate_replay_file,
}


def infer_schema_name(filename: str) -> str | None:
    """Return the schema filename matching the first substring found in filename."""
    for substring, schema_name in SCHEMA_RULES:
        if substring in filename:
            return schema_name
    return None


def validate_example(path: Path, schema_name: str) -> tuple[bool, list[str]]:
    """Dispatch to a structural validator if one exists, else plain schema validation."""
    structural = STRUCTURAL_VALIDATORS.get(schema_name)
    if structural is not None:
        return structural(path)
    ok, message = schema_validator.validate_file(path, CONTRACTS_DIR / schema_name)
    return ok, [] if ok else [message]


def main() -> int:
    passed = 0
    total = 0

    for path in sorted(EXAMPLES_DIR.rglob("*.json")):
        rel_path = path.relative_to(EXAMPLES_DIR)
        schema_name = infer_schema_name(path.name)
        if schema_name is None:
            print(f"SKIP {rel_path}: no schema could be inferred from filename")
            continue

        total += 1
        ok, problems = validate_example(path, schema_name)
        if ok:
            passed += 1
            print(f"PASS {rel_path}")
        else:
            print(f"FAIL {rel_path}: {problems[0]}")
            for problem in problems[1:]:
                print(f"    {problem}")

    print(f"{passed}/{total} examples valid")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
