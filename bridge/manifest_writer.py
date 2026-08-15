"""Atomic JSON writing and reproducibility manifest management."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def atomic_write_json(path: str | Path, data: dict[str, Any]) -> None:
    """Write JSON atomically: write to .tmp, then replace original."""
    path = Path(path)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def atomic_write_text(path: str | Path, text: str) -> None:
    """Write text file atomically."""
    path = Path(path)
    temp_path = path.with_suffix(".tmp")

    try:
        with open(temp_path, "w") as f:
            f.write(text)
        os.replace(temp_path, path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def read_json(path: str | Path) -> dict[str, Any]:
    """Read JSON file."""
    with open(path) as f:
        return json.load(f)


def ensure_dir(path: str | Path) -> Path:
    """Create directory if it doesn't exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(name: str, max_len: int = 200) -> str:
    """Sanitize a filename: remove path traversal, etc."""
    import re
    # Remove any path separators or traversal attempts
    name = name.replace("\\", "_").replace("/", "_")
    name = re.sub(r"\.{2,}", "_", name)  # Remove .. sequences
    # Keep only safe characters
    name = re.sub(r"[^\w\-.]", "_", name)
    return name[:max_len]
