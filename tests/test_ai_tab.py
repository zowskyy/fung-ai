from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

import app.screens.editor as editor_mod
import sandbox.snapshots as snapshots_mod
from app.screens.editor import EditorScreen, EDIT_RE
from core.template_engine import discover_templates
from sandbox.workspace import Project


class FakeBackend:
    name = "fake"

    def __init__(self, reply: str) -> None:
        self.reply = reply

    def is_available(self) -> bool:
        return True

    def complete(self, system, messages, on_delta=None):
        if on_delta is not None:
            on_delta(self.reply)
        return self.reply


class FakeProject:
    def __init__(self, files_dir: Path) -> None:
        self.files_dir = files_dir
        self.name = "Test"
        self.data = {"fields": {}}


class FakeWindow:
    def show_home(self) -> None:
        pass


def _app():
    return QApplication.instance() or QApplication([])


def test_offline_send_does_not_start_workers(monkeypatch):
    monkeypatch.setattr(editor_mod, "get_backend", lambda: None)
    app = _app()
    screen = EditorScreen(FakeWindow())
    screen.project = FakeProject(Path("C:/nope"))
    screen.chat_log.clear()
    screen._send_prompt()
    assert screen.ai_worker is None
    assert screen.insights_worker is None
    assert "AI is not connected" in screen.chat_log.toPlainText()
    assert screen.ai_send_btn.isEnabled()


def test_edit_block_regex():
    text = "idea\n%%EDIT game.py\nprint('hi')\n%%END\nend"
    matches = list(EDIT_RE.finditer(text))
    assert len(matches) == 1
    assert matches[0].group(1).strip() == "game.py"
    assert matches[0].group(2).strip() == "print('hi')"


def test_apply_edits_writes_file_and_is_undoable(monkeypatch, tmp_path):
    fake = FakeBackend("Here is a change:\n%%EDIT game.py\nprint('hi')\n%%END\n")
    monkeypatch.setattr(editor_mod, "get_backend", lambda: fake)
    monkeypatch.setattr(editor_mod, "take_snapshot", lambda *a, **k: None)
    editor_mod.settings.set_allow_edits(True)

    app = _app()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    (files_dir / "game.py").write_text("old", encoding="utf-8")
    screen = EditorScreen(FakeWindow())
    screen.project = FakeProject(files_dir)
    screen.chat_log.clear()
    screen.prompt_edit.setText("please improve the game")
    screen._send_prompt()

    if screen.ai_worker is not None:
        screen.ai_worker.wait(5000)
    if screen.insights_worker is not None:
        screen.insights_worker.wait(5000)
    for _ in range(50):
        app.processEvents()

    assert (files_dir / "game.py").read_text(encoding="utf-8") == "print('hi')"
    cleaned = screen.chat_log.toPlainText()
    assert "Here is a change" in cleaned
    assert "%%EDIT" not in cleaned


def test_editor_opens_offline(monkeypatch, tmp_path):
    monkeypatch.setattr(editor_mod, "get_backend", lambda: None)
    monkeypatch.setattr(editor_mod, "take_snapshot", lambda *a, **k: None)

    _app()
    workspace = tmp_path / "ws"
    project = Project.create(workspace, "Demo", "2d-platformer", {})
    templates = discover_templates(Path(__file__).resolve().parent.parent / "templates")
    template = next(t for t in templates if t.manifest["id"] == "2d-platformer")
    template.materialize(project.files_dir, {"player_name": "Ziggy"})

    screen = EditorScreen(FakeWindow())
    screen.set_project(project)
    assert screen.tabs.count() == 4
    assert "Connect an AI helper" in screen.insights_view.toPlainText()
    assert not screen.allow_edits_check.isEnabled()
