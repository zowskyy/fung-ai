from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .field_models import Field, FieldValidationError

TOKEN_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class TemplateError(ValueError):
    pass


class Template:
    def __init__(self, root: Path, manifest: dict):
        self.root = root
        self.manifest = manifest
        self.fields = [Field.from_dict(f) for f in manifest.get("fields", [])]
        self.name = str(manifest.get("name", root.name))
        self.description = str(manifest.get("description", ""))
        self.language = str(manifest.get("language", ""))
        self.icon = str(manifest.get("icon", "box"))

    @property
    def field_map(self) -> dict[str, Field]:
        return {f.id: f for f in self.fields}

    @classmethod
    def load(cls, root: Path) -> "Template":
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            raise TemplateError(f"No manifest.json in {root}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TemplateError(f"Invalid manifest.json in {root}: {exc}")
        return cls(root, manifest)

    def validate_values(self, values: dict[str, Any]) -> dict[str, Any]:
        unknown = set(values) - set(self.field_map)
        if unknown:
            raise TemplateError(
                f"Unknown field{'s' if len(unknown) > 1 else ''}: {', '.join(sorted(unknown))}"
            )
        result = {}
        for field in self.fields:
            result[field.id] = field.validate(values.get(field.id, field.default))
        return result

    def render(self, values: dict[str, Any]) -> dict[str, str]:
        validated = self.validate_values(values)
        rendered: dict[str, str] = {}
        for entry in self.manifest.get("files", []):
            src = self.root / entry["src"]
            if not src.exists():
                raise TemplateError(f"Template file missing: {entry['src']}")
            text = src.read_text(encoding="utf-8")
            for name in TOKEN_RE.findall(text):
                if name not in validated:
                    raise TemplateError(
                        f"Unknown field '{{{{{name}}}}}' used in {entry['src']}"
                    )
            rendered[entry["dest"]] = TOKEN_RE.sub(
                lambda m: str(validated[m.group(1)]), text
            )
        return rendered

    def run_command(self) -> list[str]:
        run = self.manifest.get("run", {})
        command = str(run.get("command", "python"))
        args = [str(a) for a in run.get("args", [])]
        return [command, *args]

    def materialize(self, files_dir: Path, values: dict[str, Any]) -> list[Path]:
        files_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for dest, content in self.render(values).items():
            target = files_dir / dest
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(target)
        return written


def discover_templates(templates_dir: Path) -> list[Template]:
    if not templates_dir.is_dir():
        return []
    templates = []
    for child in sorted(templates_dir.iterdir()):
        if child.is_dir() and (child / "manifest.json").exists():
            try:
                templates.append(Template.load(child))
            except (TemplateError, FieldValidationError):
                continue
    return templates
