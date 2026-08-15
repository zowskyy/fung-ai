from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ContextPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = None
        self._template = None
        self._file_click_callback: Callable[[str], None] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.title = QLabel("Context")
        self.title.setStyleSheet("font-weight: 600; font-size: 13px; color: #00ff66; font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.title)

        self.fields_label = QLabel("Active Fields")
        self.fields_label.setStyleSheet("font-weight: 600; font-size: 11px; color: #4f6b57; margin-top: 4px; font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.fields_label)

        self.fields_list = QListWidget()
        self.fields_list.setMaximumHeight(120)
        self.fields_list.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.fields_list)

        self.files_label = QLabel("Project Files")
        self.files_label.setStyleSheet("font-weight: 600; font-size: 11px; color: #4f6b57; margin-top: 4px; font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.files_label)

        self.files_list = QListWidget()
        self.files_list.setStyleSheet("font-size: 11px;")
        self.files_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        layout.addWidget(self.files_list, stretch=1)

        self.suggestions_label = QLabel("Recent Suggestions")
        self.suggestions_label.setStyleSheet("font-weight: 600; font-size: 11px; color: #4f6b57; margin-top: 4px; font-family: Consolas, 'Courier New', monospace;")
        layout.addWidget(self.suggestions_label)

        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(100)
        self.suggestions_list.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.suggestions_list)

        layout.addStretch()

    def set_file_click_callback(self, callback: Callable[[str], None]) -> None:
        self._file_click_callback = callback

    def update_context(self, project, template) -> None:
        self._project = project
        self._template = template

        self.fields_list.clear()
        if project:
            fields = project.data.get("fields", {})
            if fields:
                for key, value in fields.items():
                    item = QListWidgetItem(f"{key}: {value}")
                    item.setToolTip(f"Field: {key}")
                    self.fields_list.addItem(item)
            else:
                self.fields_list.addItem("(no fields set)")

        self.files_list.clear()
        if project and project.files_dir.exists():
            for file_path in project.files_dir.rglob("*"):
                if file_path.is_file():
                    rel = file_path.relative_to(project.files_dir)
                    item = QListWidgetItem(str(rel))
                    item.setData(Qt.UserRole, str(file_path))
                    item.setToolTip(f"Double-click to attach: {rel}")
                    self.files_list.addItem(item)

    def add_suggestion(self, text: str) -> None:
        self.suggestions_list.insertItem(0, text)
        while self.suggestions_list.count() > 10:
            self.suggestions_list.takeItem(self.suggestions_list.count() - 1)

    def _on_file_double_clicked(self, item: QListWidgetItem) -> None:
        if self._file_click_callback:
            file_path = item.data(Qt.UserRole)
            if file_path:
                self._file_click_callback(file_path)


__all__ = ["ContextPanel"]