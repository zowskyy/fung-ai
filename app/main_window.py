from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.screens.editor import EditorScreen
from app.screens.home import HomeScreen
from app.screens.settings import SettingsDialog
from app.screens.wizard import WizardScreen
from app.theme import APP_QSS
from app.utils import default_workspace_path
from app.widgets.command_palette import CommandPalette
from app.widgets.sidebar import SidebarWidget
from app.widgets.status_bar import StatusBar
from sandbox.workspace import Project

_APP_QSS = APP_QSS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("fungai")
        self.resize(1100, 700)
        self.setStyleSheet(_APP_QSS)

        self.workspace = default_workspace_path()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.current_project: Project | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = SidebarWidget(self.workspace, parent=self)
        self.sidebar.project_selected.connect(self.open_project)
        self.sidebar.new_project_clicked.connect(self.show_wizard)
        self.sidebar.file_activated.connect(
            lambda path: self.editor._attach_file_from_panel(path)
        )
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.home = HomeScreen(self)
        self.wizard = WizardScreen(self)
        self.editor = EditorScreen(self)
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.wizard)
        self.stack.addWidget(self.editor)
        body.addWidget(self.stack, stretch=1)

        root_layout.addLayout(body, stretch=1)

        self.status_bar = StatusBar(self)
        root_layout.addWidget(self.status_bar)

        self.sidebar.refresh()
        self.show_home()

    def _open_palette(self) -> None:
        commands = [
            ("New project", self.show_wizard),
            ("Go home", self.show_home),
            ("Toggle sidebar", self._toggle_sidebar),
            ("Open settings", self._open_settings),
            ("Switch to Build mode", lambda: self.editor.set_mode("build")),
            ("Switch to Plan mode", lambda: self.editor.set_mode("plan")),
            ("Cycle model variant", self._cycle_model_variant),
            ("Run current project", lambda: self.editor.run_current()),
            ("Rename session", lambda: self.editor.rename_current()),
            ("Quit fungai", self.close),
        ]
        palette = CommandPalette(commands, self)
        if palette.exec() == CommandPalette.Accepted:
            palette.run_selected()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()

    def _cycle_model_variant(self) -> None:
        from ai import settings as ai_settings

        idx = ai_settings.get_cycle_index()
        ai_settings.set_cycle_index(idx + 1)
        self.editor._refresh_ai_status()
        self.status_bar.set_status(f"Model variant -> {idx + 1}")

    def _toggle_sidebar(self) -> None:
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def keyPressEvent(self, event) -> None:
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_P:
            self._open_palette()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_B:
            self._toggle_sidebar()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_N:
            self.show_wizard()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Q:
            self.close()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_R:
            self.editor.rename_current()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Comma:
            self._open_settings()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_T:
            self._cycle_model_variant()
            return
        if event.key() == Qt.Key_F2:
            self._open_palette()
            return
        super().keyPressEvent(event)

    def show_home(self) -> None:
        self.home.refresh()
        self.sidebar.refresh()
        self.status_bar.set_status("Home")
        self.stack.setCurrentWidget(self.home)

    def show_wizard(self) -> None:
        self.wizard.refresh()
        self.stack.setCurrentWidget(self.wizard)

    def open_project(self, project: Project) -> None:
        self.current_project = project
        self.editor.set_project(project)
        self.sidebar.highlight_project(project)
        self.stack.setCurrentWidget(self.editor)

    def closeEvent(self, event) -> None:
        self.editor.shutdown()
        super().closeEvent(event)
