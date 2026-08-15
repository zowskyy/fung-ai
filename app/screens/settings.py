from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from ai import settings
from app.theme import BORDER, BORDER_DIM, TEXT, TEXT_MUTED


class SettingsDialog(QDialog):
    """Settings dialog, mirroring opencode's Ctrl+, settings surface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self.setStyleSheet(
            f"QDialog {{ background: #050805; border: 1px solid {BORDER_DIM}; }}"
            f"QLabel {{ color: {TEXT}; font-family: Consolas, 'Courier New', monospace; }}"
            f"QCheckBox {{ color: {TEXT}; spacing: 8px; "
            f"font-family: Consolas, 'Courier New', monospace; }}"
            f"QSpinBox {{ background: #0a0f0a; border: 1px solid {BORDER_DIM}; "
            f"border-radius: 4px; padding: 4px; color: {TEXT}; "
            f"font-family: Consolas, 'Courier New', monospace; }}"
        )

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.allow_edits = QCheckBox("Allow AI to edit project files")
        self.allow_edits.setChecked(settings.allow_ai_edits())
        form.addRow("", self.allow_edits)

        self.cycle_index = QSpinBox()
        self.cycle_index.setRange(0, 99)
        self.cycle_index.setValue(settings.get_cycle_index())
        form.addRow("Model rotation index", self.cycle_index)

        self.theme_label = QLabel("fungai terminal (black / neon-green / red)")
        self.theme_label.setStyleSheet(f"color: {TEXT_MUTED};")
        form.addRow("Theme", self.theme_label)

        self.auth_label = QLabel("API keys live in ~/.creator/auth.json\n(bring your own key)")
        self.auth_label.setStyleSheet(f"color: {TEXT_MUTED};")
        form.addRow("Credentials", self.auth_label)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self) -> None:
        settings.set_allow_edits(self.allow_edits.isChecked())
        settings.set_cycle_index(self.cycle_index.value())
        self.accept()
