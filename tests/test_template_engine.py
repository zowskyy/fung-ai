from __future__ import annotations

import json

import pytest

from core.template_engine import Template, TemplateError, discover_templates

TEMPLATES_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent / "templates"


def _make_template(tmp_path, fields=None, file_text="Hello {{greeting}}") -> "pathlib.Path":
    manifest = {
        "id": "demo",
        "name": "Demo",
        "fields": fields
        or [{"id": "greeting", "label": "Greeting", "type": "text", "default": "Hi"}],
        "files": [{"src": "out.txt.tmpl", "dest": "out.txt"}],
    }
    root = tmp_path / "demo"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "out.txt.tmpl").write_text(file_text, encoding="utf-8")
    return root


def test_render_fills_fields(tmp_path):
    template = Template.load(_make_template(tmp_path))
    out = template.render({"greeting": "there"})
    assert out["out.txt"] == "Hello there"


def test_render_validates_select(tmp_path):
    root = _make_template(
        tmp_path,
        fields=[
            {"id": "level", "label": "Level", "type": "select", "options": ["easy", "hard"]}
        ],
        file_text="{{level}}",
    )
    template = Template.load(root)
    with pytest.raises(Exception):
        template.render({"level": "impossible"})


def test_render_rejects_unknown_field(tmp_path):
    template = Template.load(_make_template(tmp_path))
    with pytest.raises(TemplateError):
        template.render({"unknown": "x"})


def test_discover_templates(tmp_path):
    _make_template(tmp_path)
    found = discover_templates(tmp_path)
    assert len(found) == 1
    assert found[0].manifest["id"] == "demo"


def test_real_platformer_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "2d-platformer")
    out = template.render(
        {
            "player_name": "Ziggy",
            "sky_color": "#000000",
            "ground_color": "#123456",
            "player_color": "#ABCDEF",
            "difficulty": "normal",
            "gravity": "normal",
        }
    )
    assert "Ziggy" in out["game.py"]
    assert "#ABCDEF" in out["game.py"]
    assert "{{" not in out["game.py"]


def test_real_rust_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "rust-number-guess")
    out = template.render(
        {
            "player_name": "Ziggy",
            "difficulty": "normal",
            "win_emoji": "🎉",
        }
    )
    assert "Ziggy" in out["src/main.rs"]
    assert "🎉" in out["src/main.rs"]
    assert "{{" not in out["src/main.rs"]
    assert "[dependencies]" in out["Cargo.toml"]


def test_real_java_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "java-number-guess")
    out = template.render(
        {
            "player_name": "Ziggy",
            "difficulty": "normal",
            "win_emoji": "🎉",
        }
    )
    assert "Ziggy" in out["Game.java"]
    assert "{{" not in out["Game.java"]


def test_real_cpp_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "cpp-number-guess")
    out = template.render(
        {
            "player_name": "Ziggy",
            "difficulty": "normal",
            "win_emoji": "🎉",
        }
    )
    assert "Ziggy" in out["game.cpp"]
    assert "{{" not in out["game.cpp"]


def test_real_python_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "python-number-guess")
    out = template.render(
        {
            "player_name": "Ziggy",
            "difficulty": "normal",
            "win_emoji": "🎉",
        }
    )
    assert "Ziggy" in out["game.py"]
    assert "{{" not in out["game.py"]


def test_real_javascript_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "javascript-number-guess")
    out = template.render(
        {
            "player_name": "Ziggy",
            "difficulty": "normal",
            "win_emoji": "🎉",
        }
    )
    assert "Ziggy" in out["game.js"]
    assert "{{" not in out["game.js"]


def test_real_kotlin_template_renders():
    templates = discover_templates(TEMPLATES_ROOT)
    template = next(t for t in templates if t.manifest["id"] == "kotlin-number-guess")
    out = template.render(
        {
            "player_name": "Ziggy",
            "difficulty": "normal",
            "win_emoji": "🎉",
        }
    )
    assert "Ziggy" in out["Game.kt"]
    assert "{{" not in out["Game.kt"]


def test_materialize_writes_files(tmp_path):
    template = Template.load(_make_template(tmp_path))
    files_dir = tmp_path / "project" / "files"
    written = template.materialize(files_dir, {"greeting": "Yo"})
    assert written
    assert (files_dir / "out.txt").read_text(encoding="utf-8") == "Hello Yo"


def test_token_regex_allows_hyphens_and_underscores(tmp_path):
    """TOKEN_RE should match field IDs with hyphens and underscores."""
    root = _make_template(
        tmp_path,
        fields=[
            {"id": "hero-name", "label": "Hero Name", "type": "text", "default": "Link"},
            {"id": "player_name", "label": "Player Name", "type": "text", "default": "Ziggy"},
        ],
        file_text="Hero: {{hero-name}}, Player: {{player_name}}",
    )
    template = Template.load(root)
    out = template.render({"hero-name": "Mario", "player_name": "Luigi"})
    assert "Mario" in out["out.txt"]
    assert "Luigi" in out["out.txt"]
    assert "{{" not in out["out.txt"]


def test_token_regex_rejects_invalid_chars(tmp_path):
    """TOKEN_RE should NOT match field IDs with slashes, spaces, or angle brackets."""
    root = _make_template(
        tmp_path,
        fields=[
            {"id": "hero/name", "label": "Hero", "type": "text", "default": "Link"},
        ],
        file_text="Invalid: {{hero/name}}",
    )
    template = Template.load(root)
    with pytest.raises(TemplateError, match="Invalid field name"):
        template.render({"hero/name": "Mario"})
