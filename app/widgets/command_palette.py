from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.theme import BORDER, BORDER_DIM, BG, TEXT


class CommandPalette(QDialog):
    """Ctrl+P command palette, mirroring opencode's command palette."""

    def __init__(self, commands, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.setMinimumWidth(420)
        self.setStyleSheet(
            f"QDialog {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 6px; }}"
        )
        self._commands = list(commands)
        self._selected = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Type a command...")
        self.filter.setStyleSheet(
            f"QLineEdit {{ background: {BG}; border: 1px solid {BORDER_DIM}; "
            f"border-radius: 4px; padding: 6px; color: {TEXT}; "
            f"font-family: Consolas, 'Courier New', monospace; }}"
        )
        self.filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter)

        self.list = QListWidget()
        self.list.setStyleSheet(
            f"QListWidget {{ background: {BG}; border: none; outline: 0; "
            f"font-family: Consolas, 'Courier New', monospace; }}"
            f"QListWidget::item {{ padding: 6px 8px; border-radius: 4px; color: {TEXT}; }}"
            f"QListWidget::item:selected {{ background: {BORDER_DIM}; color: {TEXT}; }}"
        )
        self.list.itemActivated.connect(self._activate)
        layout.addWidget(self.list)

        self._apply_filter("")
        self.filter.setFocus()

    def _apply_filter(self, text: str) -> None:
        self.list.clear()
        q = text.strip().lower()
        for title, callback in self._commands:
            if q in title.lower():
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, callback)
                self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Down and not self.list.hasFocus():
            self.list.setFocus()
        super().keyPressEvent(event)

    def _activate(self, item=None) -> None:
        if item is None:
            item = self.list.currentItem()
        if item is None:
            return
        self._selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def run_selected(self) -> None:
        if self._selected is not None:
            self._selected()
