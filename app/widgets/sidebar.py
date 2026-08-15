from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from runners.detector import detect_all
from sandbox.workspace import Project, list_projects


class SidebarWidget(QWidget):
    """Persistent left sidebar with project list, search, and toolchain status."""

    project_selected = Signal(object)  # emits Project
    new_project_clicked = Signal()
    file_activated = Signal(str)  # emits absolute file path

    def __init__(self, workspace, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self._all_projects: list[Project] = []
        self.setFixedWidth(240)
        self.setStyleSheet(
            "QWidget { background: #0a0f0a; border-right: 1px solid #0b3d22; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(8)

        header = QLabel("fungai")
        header.setObjectName("sidebar_header")
        header.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #00ff66; padding: 4px 0; "
            "font-family: Consolas, 'Courier New', monospace;"
        )
        layout.addWidget(header)

        new_btn = QPushButton("+ New Project")
        new_btn.setObjectName("sidebar_new_btn")
        new_btn.setStyleSheet(
            "QPushButton { background: #00ff66; color: #050805; border: none; "
            "border-radius: 4px; padding: 8px 12px; font-weight: 700; text-align: center; "
            "font-family: Consolas, 'Courier New', monospace; }"
            "QPushButton:hover { background: #1aff77; }"
        )
        new_btn.clicked.connect(self.new_project_clicked.emit)
        layout.addWidget(new_btn)

        projects_label = QLabel("Projects")
        projects_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #4f6b57; margin-top: 8px;")
        layout.addWidget(projects_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search projects...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_projects)
        self.search_input.setStyleSheet(
            "QLineEdit { background: #0a0f0a; border: 1px solid #0b3d22; border-radius: 4px; "
            "padding: 4px 8px; font-size: 12px; color: #00ff66; "
            "font-family: Consolas, 'Courier New', monospace; }"
        )
        layout.addWidget(self.search_input)

        self.project_list = QListWidget()
        self.project_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; padding: 0; "
            "outline: 0; font-family: Consolas, 'Courier New', monospace; }"
            "QListWidget::item { padding: 6px 8px; border-radius: 4px; margin: 1px 0; color: #36a85a; }"
            "QListWidget::item:selected { background: #0b3d22; color: #00ff66; }"
            "QListWidget::item:hover { background: #0d130d; }"
        )
        self.project_list.currentRowChanged.connect(self._on_project_clicked)
        layout.addWidget(self.project_list, stretch=1)

        tools_label = QLabel("Toolchains")
        tools_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #4f6b57; margin-top: 8px;")
        layout.addWidget(tools_label)

        self.tools_container = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_container)
        self.tools_layout.setContentsMargins(0, 0, 0, 0)
        self.tools_layout.setSpacing(4)
        layout.addWidget(self.tools_container)

        files_label = QLabel("Files")
        files_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #4f6b57; margin-top: 8px;")
        layout.addWidget(files_label)
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(160)
        self.files_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; padding: 0; outline: 0; "
            "font-family: Consolas, 'Courier New', monospace; }"
            "QListWidget::item { padding: 4px 8px; border-radius: 4px; color: #36a85a; }"
            "QListWidget::item:selected { background: #0b3d22; color: #00ff66; }"
            "QListWidget::item:hover { background: #0d130d; }"
        )
        self.files_list.itemDoubleClicked.connect(self._on_file_clicked)
        layout.addWidget(self.files_list)

        layout.addStretch()

        from app.theme import TEXT_MUTED, VERSION
        self.footer = QLabel(f"\u2022 fungai v{VERSION}")
        self.footer.setStyleSheet(
            f"font-size: 11px; color: {TEXT_MUTED}; font-family: Consolas, 'Courier New', monospace;"
        )
        layout.addWidget(self.footer)

    def refresh(self) -> None:
        self._all_projects = list_projects(self.workspace)
        self._populate_list(self._all_projects)

        while self.tools_layout.count():
            item = self.tools_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for tool in detect_all():
            pill = self._tool_pill(tool)
            self.tools_layout.addWidget(pill)
        self.tools_layout.addStretch()

        self.files_list.clear()
        window = self.window()
        project = getattr(window, "current_project", None)
        if project is not None and getattr(project, "files_dir", None) is not None:
            files_dir = project.files_dir
            if files_dir.exists():
                for path in sorted(files_dir.rglob("*")):
                    if path.is_file():
                        item = QListWidgetItem(str(path.relative_to(files_dir)))
                        item.setData(Qt.ItemDataRole.UserRole, str(path))
                        self.files_list.addItem(item)

    def _populate_list(self, projects: list[Project]) -> None:
        self.project_list.clear()
        active_root = None
        if hasattr(self.window(), "current_project") and self.window().current_project is not None:
            active_root = self.window().current_project.root

        for project in projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.UserRole, project)
            self.project_list.addItem(item)
            if active_root is not None and project.root == active_root:
                self.project_list.setCurrentItem(item)

    def _filter_projects(self, text: str) -> None:
        if not text.strip():
            self._populate_list(self._all_projects)
            return
        filtered = [
            p for p in self._all_projects
            if text.lower() in p.name.lower()
        ]
        self._populate_list(filtered)

    def _tool_pill(self, tool):
        label = QLabel()
        if tool.available:
            label.setText(f"{tool.name} [ok]")
            color = "#00ff66"
            fg = "#050805"
        else:
            label.setText(f"{tool.name} [missing]")
            color = "#ff2e44"
            fg = "#050805"
        label.setStyleSheet(
            f"background: {color}; color: {fg}; border: 1px solid #0b3d22; "
            f"border-radius: 4px; padding: 3px 8px; font-size: 11px; "
            f"font-family: Consolas, 'Courier New', monospace;"
        )
        if not tool.available and tool.install_hint:
            label.setToolTip(tool.install_hint)
        return label

    def _on_project_clicked(self, row: int) -> None:
        if row < 0:
            return
        item = self.project_list.item(row)
        if item is not None:
            project = item.data(Qt.UserRole)
            if project is not None:
                self.project_selected.emit(project)

    def _on_file_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.file_activated.emit(path)

    def highlight_project(self, project: Project) -> None:
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            if item is not None and item.data(Qt.UserRole) is not None:
                if item.data(Qt.UserRole).root == project.root:
                    self.project_list.setCurrentItem(item)
                    return
