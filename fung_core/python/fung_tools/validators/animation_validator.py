"""Structural validation for animation_manifest.json content."""
import json
from pathlib import Path

from fung_tools.validators import schema_validator
from fung_tools.validators.schema_validator import CONTRACTS_DIR


def validate_manifest_structure(manifest: dict) -> list[str]:
    """Check clip id uniqueness and (defensively) positive frame_count/fps."""
    problems = []
    clips = manifest["clips"]

    seen_ids = set()
    for clip in clips:
        clip_id = clip["id"]
        if clip_id in seen_ids:
            problems.append(f"duplicate clip id '{clip_id}'")
        seen_ids.add(clip_id)

        if clip["frame_count"] <= 0:
            problems.append(f"clip '{clip_id}' has frame_count <= 0")
        if clip["fps"] <= 0:
            problems.append(f"clip '{clip_id}' has fps <= 0")

    return problems


def check_sprite_files_exist(manifest: dict, base_dir: Path) -> list[str]:
    """Warn for each clip whose sprite_sheet does not resolve to a real file.

    Separate from structural validation on purpose: placeholder art may not
    exist yet, and manifest validity must not depend on art files being present.
    """
    warnings = []
    for clip in manifest["clips"]:
        sprite_path = base_dir / clip["sprite_sheet"]
        if not sprite_path.exists():
            warnings.append(f"clip '{clip['id']}' sprite_sheet not found: {sprite_path}")
    return warnings


def validate_animation_file(path: Path) -> tuple[bool, list[str]]:
    """Validate an animation_manifest.json file against schema and structural rules."""
    ok, message = schema_validator.validate_file(path, CONTRACTS_DIR / "animation_manifest.schema.json")
    problems = [] if ok else [message]

    if ok:
        manifest = json.loads(path.read_text())
        problems.extend(validate_manifest_structure(manifest))

    return ok and not problems, problems
