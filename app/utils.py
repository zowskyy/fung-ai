from __future__ import annotations

import json
import os
from pathlib import Path

SETTINGS_DIR = Path(os.environ.get("CREATOR_HOME", str(Path.home() / ".creator")))


def default_workspace_path() -> Path:
    return SETTINGS_DIR / "workspace"


def settings_file() -> Path:
    return SETTINGS_DIR / "settings.json"


def load_settings() -> dict:
    try:
        return json.loads(settings_file().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    settings_file().write_text(json.dumps(data, indent=2), encoding="utf-8")
