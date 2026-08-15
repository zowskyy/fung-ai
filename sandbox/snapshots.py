from __future__ import annotations

import shutil
import time
from pathlib import Path

from .workspace import Project


def take_snapshot(project: Project, note: str = "") -> str:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    version_dir = project.versions_dir / stamp
    version_dir.mkdir(parents=True, exist_ok=True)
    for child in project.files_dir.iterdir():
        if child.is_dir():
            shutil.copytree(child, version_dir / child.name)
        else:
            shutil.copy2(child, version_dir / child.name)
    (version_dir / "note.txt").write_text(note or stamp, encoding="utf-8")
    return stamp


def list_snapshots(project: Project) -> list[Path]:
    if not project.versions_dir.is_dir():
        return []
    return sorted(d for d in project.versions_dir.iterdir() if d.is_dir())


def restore_snapshot(project: Project, stamp: str) -> None:
    version_dir = project.versions_dir / stamp
    if not version_dir.is_dir():
        raise FileNotFoundError(f"No saved version '{stamp}'.")
    if project.files_dir.exists():
        shutil.rmtree(project.files_dir)
    project.files_dir.mkdir(parents=True)
    for child in version_dir.iterdir():
        if child.name == "note.txt":
            continue
        if child.is_dir():
            shutil.copytree(child, project.files_dir / child.name)
        else:
            shutil.copy2(child, project.files_dir / child.name)
