import os
import sys
import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("CREATOR_HOME", tempfile.mkdtemp(prefix="creator-test-"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def _cleanup_qt():
    """Quit any Qt application so pytest's process tree exits cleanly."""
    yield
    app = QApplication.instance()
    if app is not None:
        app.quit()
