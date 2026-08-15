"""Entry point variant WITHOUT the single-instance mutex guard.

Used only by CreatorNoGuard.spec / tools/audit_spawn.ps1 to reproduce and
debug the old "infinite windows" launch bug. Never use this for a normal
release build.
"""

import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("fungai")
    app.setOrganizationName("fungai")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
