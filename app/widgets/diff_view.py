from __future__ import annotations

import difflib
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class DiffView(QWidget):
    """Inline unified diff viewer with color-coded additions/deletions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #00ff66; font-family: Consolas, 'Courier New', monospace;")
        header.addWidget(self.file_label)
        header.addStretch()
        self.close_btn = QPushButton("\u2715")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet(
            "QPushButton { border: none; color: #4f6b57; font-size: 14px; font-family: Consolas, monospace; }"
            "QPushButton:hover { color: #ff2e44; }"
        )
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        layout.addLayout(header)

        self.browser = QTextBrowser()
        self.browser.setReadOnly(True)
        self.browser.setStyleSheet(
            "QTextBrowser { background: #0a0f0a; border: 1px solid #0b3d22; "
            "border-radius: 6px; padding: 8px; font-family: Consolas, monospace; font-size: 12px; }"
        )
        layout.addWidget(self.browser)

        self.hide()

    def show_diff(self, filename: str, old_text: str, new_text: str) -> None:
        self.file_label.setText(filename)
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}"))

        if not diff:
            self.browser.setHtml('<div style="color: #4f6b57;">No changes detected.</div>')
            self.show()
            return

        html_parts = ['<div style="font-family: Consolas, monospace; font-size: 12px;">']
        for line in diff:
            escaped = escape(line.rstrip("\n"))
            if line.startswith("+++") or line.startswith("---"):
                html_parts.append(f'<div style="font-weight: 700; color: #00ff66;">{escaped}</div>')
            elif line.startswith("@@"):
                html_parts.append(f'<div style="color: #ff2e44; font-style: italic;">{escaped}</div>')
            elif line.startswith("+"):
                html_parts.append(
                    f'<div style="background: #0b3d22; color: #00ff66; padding: 1px 4px; '
                    f'margin: 0 -4px; border-radius: 2px;">{escaped}</div>'
                )
            elif line.startswith("-"):
                html_parts.append(
                    f'<div style="background: #1a0608; color: #ff2e44; padding: 1px 4px; '
                    f'margin: 0 -4px; border-radius: 2px;">{escaped}</div>'
                )
            else:
                html_parts.append(f'<div style="color: #4f6b57;">{escaped}</div>')
        html_parts.append("</div>")

        self.browser.setHtml("\n".join(html_parts))
        self.show()

    def show_version_diff(self, filename: str, old_text: str, new_text: str) -> None:
        self.show_diff(filename, old_text, new_text)
