from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path

AUTH_FILE = (
    Path(os.environ.get("CREATOR_HOME", str(Path.home() / ".creator"))) / "auth.json"
)

_AUTH_LOCK = threading.Lock()


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically: temp file -> flush -> fsync -> os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _load_credentials_unlocked() -> dict:
    """Load credentials without locking. Must be called with _AUTH_LOCK held."""
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_credentials() -> dict:
    with _AUTH_LOCK:
        return _load_credentials_unlocked()


def allow_ai_edits() -> bool:
    return bool(load_credentials().get("allow_edits", False))


def set_allow_edits(value: bool) -> None:
    with _AUTH_LOCK:
        data = _load_credentials_unlocked()
        data["allow_edits"] = bool(value)
        _atomic_write(AUTH_FILE, data)


def set_credentials(mode: str, **kwargs) -> None:
    with _AUTH_LOCK:
        data = {"mode": mode}
        data.update({k: v for k, v in kwargs.items() if v})
        _atomic_write(AUTH_FILE, data)


def clear_credentials() -> None:
    with _AUTH_LOCK:
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()


def get_cycle_index() -> int:
    with _AUTH_LOCK:
        data = _load_credentials_unlocked()
        return data.get("cycle_index", 0)


def set_cycle_index(index: int) -> None:
    with _AUTH_LOCK:
        data = _load_credentials_unlocked()
        data["cycle_index"] = index
        _atomic_write(AUTH_FILE, data)