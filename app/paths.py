from __future__ import annotations

import os
import sys
from pathlib import Path


def app_root() -> Path:
    """Project root when run from source, or the PyInstaller bundle root."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", str(Path(sys.executable).parent)))
    return Path(__file__).resolve().parent.parent


def templates_dir() -> Path:
    env = os.environ.get("CREATOR_TEMPLATES")
    if env:
        return Path(env)
    candidate = app_root() / "templates"
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError("Could not locate the templates/ folder.")


__all__ = ["app_root", "templates_dir"]
