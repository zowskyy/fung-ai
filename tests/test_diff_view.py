from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from app.widgets.diff_view import DiffView


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_show_diff_renders_changes(app):
    view = DiffView()
    view.show_diff("game.py", "old line\n", "old line\nnew line\n")
    assert "game.py" in view.file_label.text()
    text = view.browser.toPlainText()
    assert "new line" in text
    assert "game.py" in text


def test_show_diff_no_changes(app):
    view = DiffView()
    view.show_diff("game.py", "same\n", "same\n")
    assert "No changes" in view.browser.toPlainText()
