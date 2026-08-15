from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.theme import BORDER, BORDER_DIM, RED, TEXT_MUTED, ASCII_FUNGAI
from runners.detector import Toolchain, detect_all


class HomeScreen(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        banner = QLabel(ASCII_FUNGAI)
        banner.setObjectName("ascii_banner")
        banner.setStyleSheet(
            f"QLabel#ascii_banner {{ color: {BORDER}; background: transparent; "
            f"font-family: Consolas, 'Courier New', monospace; font-size: 13px; "
            f"font-weight: 700; letter-spacing: 1px; }}"
        )
        layout.addWidget(banner)

        subtitle = QLabel(
            "Make things without code. Pick a kit, answer a few questions, run it, and keep versions."
        )
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        create_btn = QPushButton("+  Create a new project")
        create_btn.setObjectName("primary")
        create_btn.setMinimumHeight(46)
        create_btn.clicked.connect(window.show_wizard)
        layout.addWidget(create_btn, alignment=Qt.AlignLeft)

        tools_label = QLabel("Tools on this computer")
        tools_label.setObjectName("section")
        layout.addWidget(tools_label)
        self.tools_row = QHBoxLayout()
        self.tools_row.setSpacing(8)
        layout.addLayout(self.tools_row)

        layout.addStretch()

    def refresh(self) -> None:
        while self.tools_row.count():
            item = self.tools_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for tool in detect_all():
            self.tools_row.addWidget(self._tool_pill(tool))

    def _tool_pill(self, tool: Toolchain) -> QLabel:
        if tool.available:
            text = f"{tool.name} [ok]"
            color = BORDER
            fg = "#050805"
        else:
            text = f"{tool.name} [missing]"
            color = RED
            fg = "#050805"
        label = QLabel(text)
        label.setStyleSheet(
            f"background:{color}; color:{fg}; border:1px solid {BORDER_DIM}; "
            f"border-radius:4px; padding:4px 12px; font-family: Consolas, monospace; font-size:12px;"
        )
        if not tool.available and tool.install_hint:
            label.setToolTip(tool.install_hint)
        return label
