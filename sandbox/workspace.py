from __future__ import annotations

import json
import re
import time
from pathlib import Path


class ProjectExistsError(ValueError):
    pass


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "project"


class Project:
    def __init__(self, root: Path, data: dict):
        self.root = root
        self.data = data

    @property
    def files_dir(self) -> Path:
        return self.root / "files"

    @property
    def versions_dir(self) -> Path:
        return self.root / "versions"

    @property
    def name(self) -> str:
        return str(self.data.get("name", self.root.name))

    @classmethod
    def create(cls, workspace: Path, name: str, template_id: str, fields: dict) -> "Project":
        project_dir = workspace / slugify(name)
        if project_dir.exists():
            raise ProjectExistsError(f"A project named '{name}' already exists.")
        project_dir.mkdir(parents=True)
        data = {
            "name": name,
            "template": template_id,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fields": fields,
        }
        project_dir.joinpath("project.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
        (project_dir / "files").mkdir()
        (project_dir / "versions").mkdir()
        return cls(project_dir, data)

    @classmethod
    def open(cls, root: Path) -> "Project":
        data = json.loads((root / "project.json").read_text(encoding="utf-8"))
        return cls(root, data)

    def save_fields(self, fields: dict) -> None:
        self.data["fields"] = fields
        (self.root / "project.json").write_text(
            json.dumps(self.data, indent=2), encoding="utf-8"
        )


def list_projects(workspace: Path) -> list[Project]:
    if not workspace.is_dir():
        return []
    projects = []
    for child in sorted(workspace.iterdir()):
        if child.is_dir() and (child / "project.json").exists():
            projects.append(Project.open(child))
    return projects
