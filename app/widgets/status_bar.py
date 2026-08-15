from __future__ import annotations

from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget

from app.theme import BORDER, BORDER_DIM, RED, TEXT, TEXT_MUTED, VERSION


class StatusBar(QWidget):
    """Bottom status bar mirroring opencode's titlebar status + footer.

    Shows: mode indicator (build/plan), active backend/model, a free-form
    status message, and the app version footer (like opencode's
    sidebar_footer "• OpenCode vX").
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        self.setStyleSheet(
            f"background: #0a0f0a; border-top: 1px solid {BORDER_DIM}; "
            f"font-family: Consolas, 'Courier New', monospace;"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(10)

        self.mode_label = QLabel("BUILD")
        self.mode_label.setStyleSheet(
            f"color: {BORDER}; font-weight: 700; font-size: 12px;"
        )
        layout.addWidget(self.mode_label)

        self.model_label = QLabel("no backend")
        self.model_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.model_label)

        layout.addStretch()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.version_label = QLabel(f"\u2022 fungai v{VERSION}")
        self.version_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.version_label)

    def set_mode(self, mode: str) -> None:
        text = mode.strip().lower()
        if text == "plan":
            self.mode_label.setText("PLAN")
            self.mode_label.setStyleSheet(
                f"color: {RED}; font-weight: 700; font-size: 12px;"
            )
        else:
            self.mode_label.setText("BUILD")
            self.mode_label.setStyleSheet(
                f"color: {BORDER}; font-weight: 700; font-size: 12px;"
            )

    def set_model(self, text: str) -> None:
        self.model_label.setText(text)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
