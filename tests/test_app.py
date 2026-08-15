from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def test_main_window_smoke(app, tmp_path):
    window = MainWindow()
    window.workspace = tmp_path / "ws"
    window.workspace.mkdir(parents=True)
    window.show_home()
    assert window.stack.count() == 4
    window.close()


def test_wizard_discovers_real_template(app, tmp_path):
    window = MainWindow()
    window.workspace = tmp_path / "ws"
    window.workspace.mkdir(parents=True)
    window.show_wizard()
    assert any(t.manifest["id"] == "2d-platformer" for t in window.wizard.templates)
    window.close()
