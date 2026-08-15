"""Headless tests for the PlaygroundScreen UI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from app.screens.playground import PlaygroundScreen, GenerateWorker


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def _make_playground() -> PlaygroundScreen:
    screen = PlaygroundScreen(None)
    return screen


class TestPlaygroundUI:
    def test_has_prompt_field(self, app):
        screen = _make_playground()
        assert screen.prompt_field is not None
        assert screen.prompt_field.placeholderText() != ""

    def test_has_go_button(self, app):
        screen = _make_playground()
        assert screen.go_btn is not None
        assert screen.go_btn.text() == "Go"

    def test_has_status_label(self, app):
        screen = _make_playground()
        assert screen.status_label is not None

    def test_has_output_area(self, app):
        screen = _make_playground()
        assert screen.output_area is not None
        assert screen.output_area.isReadOnly()

    def test_actions_hidden_initially(self, app):
        screen = _make_playground()
        assert screen.try_again_btn.isHidden() is True
        assert screen.open_editor_btn.isHidden() is True

    def test_prompt_field_accepts_text(self, app):
        screen = _make_playground()
        screen.prompt_field.setText("make a snake game")
        assert screen.prompt_field.text() == "make a snake game"


class TestPlaygroundSlots:
    def test_empty_prompt_does_nothing(self, app):
        screen = _make_playground()
        screen.prompt_field.setText("")
        screen._on_generate()
        assert screen.status_label.text() == ""

    def test_set_status_running_disables_input(self, app):
        screen = _make_playground()
        screen._set_status("Working...", running=True)
        assert screen.prompt_field.isEnabled() is False
        assert screen.go_btn.isEnabled() is False

    def test_set_status_idle_enables_input(self, app):
        screen = _make_playground()
        screen._set_status("Working...", running=True)
        screen._set_status("", running=False)
        assert screen.prompt_field.isEnabled() is True
        assert screen.go_btn.isEnabled() is True

    def test_show_actions_makes_buttons_visible(self, app):
        screen = _make_playground()
        screen._show_actions()
        assert screen.try_again_btn.isHidden() is False
        assert screen.open_editor_btn.isHidden() is False

    def test_hide_actions_hides_buttons(self, app):
        screen = _make_playground()
        screen._show_actions()
        screen._hide_actions()
        assert screen.try_again_btn.isHidden() is True
        assert screen.open_editor_btn.isHidden() is True


class TestPlaygroundResult:
    def test_success_result_no_actions(self, app):
        screen = _make_playground()
        result = {
            "success": True,
            "output": "Hello!",
            "language": "python",
            "error": "",
            "provider": "cloud",
        }
        screen._on_result(result)
        assert "Done" in screen.status_label.text()

    def test_failure_result_shows_actions(self, app):
        screen = _make_playground()
        result = {
            "success": False,
            "output": "",
            "language": "",
            "error": "Provider failed",
            "provider": "cloud",
        }
        screen._on_result(result)
        assert screen.try_again_btn.isHidden() is False
        assert screen.open_editor_btn.isHidden() is False
        assert "Provider failed" in screen.status_label.text()

    def test_on_delta_appends_text(self, app):
        screen = _make_playground()
        screen._on_delta("hello ")
        screen._on_delta("world")
        assert "hello world" in screen.output_area.toPlainText()
