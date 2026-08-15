from __future__ import annotations

import json
import os
from pathlib import Path

AUTH_FILE = (
    Path(os.environ.get("CREATOR_HOME", str(Path.home() / ".creator"))) / "auth.json"
)


def load_credentials() -> dict:
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def allow_ai_edits() -> bool:
    return bool(load_credentials().get("allow_edits", False))


def set_allow_edits(value: bool) -> None:
    data = load_credentials()
    data["allow_edits"] = bool(value)
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_credentials(mode: str, **kwargs) -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"mode": mode}
    data.update({k: v for k, v in kwargs.items() if v})
    AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def clear_credentials() -> None:
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()


def get_cycle_index() -> int:
    try:
        if AUTH_FILE.exists():
            data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
            return data.get("cycle_index", 0)
    except (OSError, json.JSONDecodeError):
        pass
    return 0


def set_cycle_index(index: int) -> None:
    try:
        data = {}
        if AUTH_FILE.exists():
            data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        data["cycle_index"] = index
        AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except (OSError, json.JSONDecodeError):
        pass
