from __future__ import annotations

import time
from html import escape

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ToolExecutionCard(QWidget):
    """A collapsible card showing a single tool execution (run, edit, git)."""

    def __init__(self, command: str, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._start_time = time.time()
        self._exit_code: int | None = None

        self.setStyleSheet(
            "ToolExecutionCard { background: #0a0f0a; border: 1px solid #0b3d22; "
            "border-radius: 4px; margin: 4px 0; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self.status_dot = QLabel("\u25cf")
        self.status_dot.setStyleSheet("color: #4f6b57; font-size: 10px;")
        self.status_dot.setFixedWidth(16)
        header.addWidget(self.status_dot)

        self.command_label = QLabel(f"$ {command}")
        self.command_label.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12px; color: #00ff66; font-weight: 600;"
        )
        header.addWidget(self.command_label, stretch=1)

        self.duration_label = QLabel("")
        self.duration_label.setStyleSheet("font-size: 11px; color: #4f6b57;")
        header.addWidget(self.duration_label)

        self.toggle_btn = QPushButton("\u25bc")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setStyleSheet(
            "QPushButton { border: none; color: #4f6b57; font-size: 10px; }"
            "QPushButton:hover { color: #00ff66; }"
        )
        self.toggle_btn.clicked.connect(self._toggle)
        header.addWidget(self.toggle_btn)

        layout.addLayout(header)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(200)
        self.output.setStyleSheet(
            "QPlainTextEdit { background: #050805; border: 1px solid #0b3d22; "
            "border-radius: 4px; padding: 4px; font-family: Consolas, monospace; font-size: 11px; color: #00ff66; }"
        )
        layout.addWidget(self.output)

    def append_line(self, line: str) -> None:
        self.output.appendPlainText(line)

    def finish(self, exit_code: int) -> None:
        self._exit_code = exit_code
        elapsed = time.time() - self._start_time
        self.duration_label.setText(f"{elapsed:.1f}s")
        if exit_code == 0:
            self.status_dot.setText("\u2713")
            self.status_dot.setStyleSheet("color: #00ff66; font-size: 12px;")
        else:
            self.status_dot.setText("\u2717")
            self.status_dot.setStyleSheet("color: #ff2e44; font-size: 12px;")

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self.output.setVisible(self._expanded)
        self.toggle_btn.setText("\u25bc" if self._expanded else "\u25b6")


class ToolExecutionView(QWidget):
    """Displays a list of tool execution cards for the Run tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.header = QLabel("")
        self.header.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #4f6b57; padding: 4px 0;"
        )
        layout.addWidget(self.header)

        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(4)
        layout.addLayout(self.cards_layout)
        layout.addStretch()

        self._cards: list[ToolExecutionCard] = []

    def add_execution(self, command: str) -> ToolExecutionCard:
        card = ToolExecutionCard(command)
        self._cards.append(card)
        self.cards_layout.addWidget(card)
        self.header.setText(f"Executions ({len(self._cards)})")
        return card

    def clear(self) -> None:
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()
        self.header.setText("")
