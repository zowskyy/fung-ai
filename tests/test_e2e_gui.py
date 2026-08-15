from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

import app.screens.editor as editor_mod
from ai import settings as ai_settings
from app.paths import templates_dir
from app.screens.settings import SettingsDialog
from app.widgets.command_palette import CommandPalette
from core.template_engine import discover_templates
from sandbox.workspace import Project


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def _make_project(workspace: Path, template_id: str = "python-number-guess") -> Project:
    workspace.mkdir(parents=True, exist_ok=True)
    templates = discover_templates(templates_dir())
    template = next(t for t in templates if t.manifest["id"] == template_id)
    project = Project.create(workspace, "demo", template.manifest["id"], {"player_name": "Ziggy"})
    template.materialize(project.files_dir, {"player_name": "Ziggy"})
    return project


def test_gui_wizard_creates_project(app, tmp_path):
    from app.main_window import MainWindow

    window = MainWindow()
    window.workspace = tmp_path / "ws"
    window.show_wizard()
    template = next(
        t for t in window.wizard.templates if t.manifest["id"] == "python-number-guess"
    )
    window.wizard._select(template)
    window.wizard.field_validate = lambda: {
        "player_name": "Ziggy",
        "difficulty": "normal",
        "win_emoji": "X",
    }
    window.wizard.name_edit.setText("demo")
    window.wizard._next()

    assert window.current_project is not None
    assert (window.current_project.files_dir / "game.py").exists()
    assert window.stack.currentWidget() is window.editor
    window.close()


def test_gui_ai_edit_and_undo_redo(app, tmp_path, monkeypatch):
    from app.main_window import MainWindow

    window = MainWindow()
    window.workspace = tmp_path / "ws"
    project = _make_project(window.workspace)
    window.open_project(project)
    ai_settings.set_allow_edits(True)
    window.editor.set_mode("build")

    class FakeBackend:
        name = "fake"

        def is_available(self):
            return True

        def complete(self, system, messages, on_delta=None):
            reply = "Sure:\n%%EDIT game.py\nprint('edited')\n%%END\n"
            if on_delta is not None:
                on_delta(reply)
            return reply

    monkeypatch.setattr(editor_mod, "get_backend", lambda: FakeBackend())
    monkeypatch.setattr(editor_mod, "take_snapshot", lambda *a, **k: None)

    window.editor.prompt_edit.setText("change it")
    window.editor._send_prompt()
    if window.editor.ai_worker is not None:
        window.editor.ai_worker.wait(5000)
    if window.editor.insights_worker is not None:
        window.editor.insights_worker.wait(5000)
    for _ in range(60):
        app.processEvents()

    assert "edited" in (project.files_dir / "game.py").read_text()

    window.editor._undo_edit()
    assert "edited" not in (project.files_dir / "game.py").read_text()

    window.editor._redo_edit()
    assert "edited" in (project.files_dir / "game.py").read_text()
    window.close()


def test_gui_run_and_stop(app, tmp_path, monkeypatch):
    from app.main_window import MainWindow

    window = MainWindow()
    window.workspace = tmp_path / "ws"
    project = _make_project(window.workspace)
    (project.files_dir / "game.py").write_text("print('hello fungai')\n", encoding="utf-8")
    window.open_project(project)
    monkeypatch.setattr(editor_mod, "get_backend", lambda: None)
    monkeypatch.setattr(editor_mod, "notify_complete", lambda *a, **k: None)

    window.editor.run_current()
    worker = window.editor.run_worker
    assert worker is not None
    worker.wait(15000)
    for _ in range(40):
        app.processEvents()

    assert "hello fungai" in window.editor.output.toPlainText()
    assert "Finished" in window.editor.output.toPlainText()
    window.close()


def test_gui_plan_mode_requires_permission(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from app.main_window import MainWindow

    window = MainWindow()
    window.workspace = tmp_path / "ws"
    project = _make_project(window.workspace)
    (project.files_dir / "game.py").write_text("print('hello fungai')\n", encoding="utf-8")
    window.open_project(project)
    monkeypatch.setattr(editor_mod, "get_backend", lambda: None)
    monkeypatch.setattr(editor_mod, "notify_complete", lambda *a, **k: None)

    captured = {}
    monkeypatch.setattr(
        QMessageBox,
        "question",
        staticmethod(
            lambda *a, **k: captured.setdefault("called", True) or QMessageBox.StandardButton.No
        ),
    )

    window.editor.set_mode("plan")
    window.editor.run_current()

    assert captured.get("called") is True
    assert window.editor.run_worker is None or not window.editor.run_worker.isRunning()
    window.close()


def test_gui_what_changed_diff(app, tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git not available")

    from app.main_window import MainWindow
    from repo.git_manager import RepoManager

    window = MainWindow()
    window.workspace = tmp_path / "ws"
    project = _make_project(window.workspace)
    window.open_project(project)

    repo = RepoManager(project.files_dir)
    repo.ensure()
    repo.save_version("v1")
    (project.files_dir / "game.py").write_text("print('changed')\n", encoding="utf-8")
    repo.save_version("v2")

    window.editor._refresh_versions()
    window.editor.versions_list.setCurrentRow(0)
    window.editor._what_changed()
    app.processEvents()

    assert "game.py" in window.editor.diff_view.file_label.text()
    # The diff viewer rendered the unified diff from the real git repo.
    assert "print('changed')" in window.editor.diff_view.browser.toPlainText()
    window.close()


def test_gui_settings_cycle_index(app):
    ai_settings.set_allow_edits(True)
    ai_settings.set_cycle_index(0)

    dialog = SettingsDialog()
    dialog.allow_edits.setChecked(False)
    dialog.cycle_index.setValue(7)
    dialog._save()

    assert ai_settings.allow_ai_edits() is False
    assert ai_settings.get_cycle_index() == 7

    ai_settings.set_allow_edits(True)
    ai_settings.set_cycle_index(0)


def test_gui_command_palette(app):
    called: list[str] = []

    palette = CommandPalette(
        [
            ("Run current project", lambda: called.append("run")),
            ("Go home", lambda: called.append("home")),
        ]
    )
    palette._apply_filter("run")
    assert palette.list.count() == 1
    palette.list.setCurrentRow(0)
    palette._activate()
    assert palette._selected is not None
    palette.run_selected()

    assert called == ["run"]
