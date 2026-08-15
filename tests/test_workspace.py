from __future__ import annotations

import pytest

from sandbox.snapshots import list_snapshots, restore_snapshot, take_snapshot
from sandbox.workspace import Project, ProjectExistsError, list_projects


def test_create_and_list(tmp_path):
    workspace = tmp_path / "ws"
    project = Project.create(workspace, "My Game", "2d-platformer", {"x": 1})
    assert project.files_dir.is_dir()
    assert [p.name for p in list_projects(workspace)] == ["My Game"]


def test_duplicate_name_raises(tmp_path):
    workspace = tmp_path / "ws"
    Project.create(workspace, "My Game", "2d-platformer", {})
    with pytest.raises(ProjectExistsError):
        Project.create(workspace, "My Game", "2d-platformer", {})


def test_snapshot_restore(tmp_path):
    workspace = tmp_path / "ws"
    project = Project.create(workspace, "Game", "2d-platformer", {})
    (project.files_dir / "game.py").write_text("v1", encoding="utf-8")
    take_snapshot(project, "First")
    (project.files_dir / "game.py").write_text("v2", encoding="utf-8")
    snapshots = list_snapshots(project)
    assert len(snapshots) == 1
    restore_snapshot(project, snapshots[0].name)
    assert (project.files_dir / "game.py").read_text(encoding="utf-8") == "v1"


def test_save_fields_persists(tmp_path):
    workspace = tmp_path / "ws"
    project = Project.create(workspace, "Game", "2d-platformer", {"a": 1})
    project.save_fields({"a": 2})
    reopened = Project.open(project.root)
    assert reopened.data["fields"]["a"] == 2
