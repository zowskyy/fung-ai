"""Playground screen — one prompt field, one Go button, zero friction.

This is the kid-friendly entry point: type what you want, press Go,
watch it generate + run. No settings, no project wizard, no bloat.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.theme import (
    BG,
    BORDER,
    BORDER_DIM,
    NEON_GREEN,
    NEON_GREEN_DIM,
    RED,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
)


class GenerateWorker(QThread):
    """Runs AI generation + execution in a background thread."""

    status = Signal(str)
    delta = Signal(str)
    result = Signal(dict)  # {success, output, language, error, provider}

    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self) -> None:
        try:
            from ai.executor import execute_prompt
            result = execute_prompt(
                self.prompt,
                on_status=self.status.emit,
                on_delta=self.delta.emit,
            )
            self.result.emit(result)
        except Exception as exc:
            self.result.emit({
                "success": False,
                "output": "",
                "language": "",
                "error": str(exc),
                "provider": "",
            })


class PlaygroundScreen(QWidget):
    """Single-prompt kid-friendly UI.

    Layout:
      [ centered prompt field ]
      [ Generate button ]
      [ status line ]
      [ output area ]
      [ action buttons: try again / open editor ]
    """

    def __init__(self, window):
        super().__init__()
        self.window = window
        self._worker: GenerateWorker | None = None
        self._last_result: dict | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- spacer top ---
        root.addStretch(2)

        # --- centered content column ---
        col = QVBoxLayout()
        col.setContentsMargins(60, 0, 60, 0)
        col.setSpacing(16)

        # title
        title = QLabel("What do you want to build?")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: {NEON_GREEN}; font-size: 22px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        col.addWidget(title)

        subtitle = QLabel("Type anything — a game, a calculator, a story. We'll build it for you.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 13px; "
            f"background: transparent; border: none;"
        )
        col.addWidget(subtitle)

        col.addSpacing(8)

        # prompt input
        prompt_row = QHBoxLayout()
        prompt_row.setSpacing(8)
        self.prompt_field = QLineEdit()
        self.prompt_field.setPlaceholderText(
            "e.g. a snake game, a calculator, a quiz about space..."
        )
        self.prompt_field.setMinimumHeight(48)
        self.prompt_field.setStyleSheet(
            f"QLineEdit {{"
            f"  background: #0a0f0a; color: {NEON_GREEN};"
            f"  border: 2px solid {BORDER_DIM}; border-radius: 8px;"
            f"  padding: 8px 16px; font-size: 16px;"
            f"  selection-background-color: #0b3d22;"
            f"}}"
            f"QLineEdit:focus {{ border-color: {BORDER}; }}"
        )
        self.prompt_field.returnPressed.connect(self._on_generate)
        prompt_row.addWidget(self.prompt_field)

        self.go_btn = QPushButton("Go")
        self.go_btn.setFixedSize(80, 48)
        self.go_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: {BORDER_DIM}; color: {NEON_GREEN};"
            f"  border: 2px solid {BORDER}; border-radius: 8px;"
            f"  font-size: 16px; font-weight: bold;"
            f"}}"
            f"QPushButton:hover {{ background: #0d5a2e; }}"
            f"QPushButton:pressed {{ background: #0b3d22; }}"
            f"QPushButton:disabled {{ color: {TEXT_MUTED}; border-color: {BORDER_DIM}; }}"
        )
        self.go_btn.clicked.connect(self._on_generate)
        prompt_row.addWidget(self.go_btn)
        col.addLayout(prompt_row)

        # status line
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            f"color: {TEXT_DIM}; font-size: 12px; "
            f"background: transparent; border: none; padding: 4px;"
        )
        col.addWidget(self.status_label)

        col.addSpacing(4)

        # output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setMinimumHeight(120)
        self.output_area.setMaximumHeight(300)
        self.output_area.setStyleSheet(
            f"QTextEdit {{"
            f"  background: #060a06; color: {TEXT};"
            f"  border: 1px solid {BORDER_DIM}; border-radius: 6px;"
            f"  padding: 8px; font-family: Consolas, 'Courier New', monospace;"
            f"  font-size: 13px;"
            f"}}"
        )
        col.addWidget(self.output_area)

        # action row (hidden until result)
        self.action_row = QHBoxLayout()
        self.action_row.setSpacing(8)
        self.try_again_btn = QPushButton("Try again")
        self.try_again_btn.setStyleSheet(
            f"QPushButton {{ background: #0b3d22; color: {NEON_GREEN};"
            f"  border: 1px solid {BORDER_DIM}; border-radius: 6px;"
            f"  padding: 6px 16px; font-size: 13px; }}"
            f"QPushButton:hover {{ background: #0d5a2e; }}"
        )
        self.try_again_btn.clicked.connect(self._on_generate)
        self.action_row.addWidget(self.try_again_btn)

        self.open_editor_btn = QPushButton("Open in editor")
        self.open_editor_btn.setStyleSheet(
            f"QPushButton {{ background: #0a0f0a; color: {TEXT_DIM};"
            f"  border: 1px solid {BORDER_DIM}; border-radius: 6px;"
            f"  padding: 6px 16px; font-size: 13px; }}"
            f"QPushButton:hover {{ background: #0d5a2e; color: {NEON_GREEN}; }}"
        )
        self.open_editor_btn.clicked.connect(self._open_in_editor)
        self.action_row.addWidget(self.open_editor_btn)
        self.action_row.addStretch()
        col.addLayout(self.action_row)
        self._hide_actions()

        root.addLayout(col, stretch=3)

        # spacer bottom
        root.addStretch(1)

    # --- slots ---

    def _on_generate(self) -> None:
        prompt = self.prompt_field.text().strip()
        if not prompt:
            return
        self._hide_actions()
        self.output_area.clear()
        self._set_status("Generating...", running=True)
        self._worker = GenerateWorker(prompt, parent=self)
        self._worker.status.connect(self._on_status)
        self._worker.delta.connect(self._on_delta)
        self._worker.result.connect(self._on_result)
        self._worker.start()

    def _on_status(self, msg: str) -> None:
        self._set_status(msg)

    def _on_delta(self, chunk: str) -> None:
        from PySide6.QtGui import QTextCursor
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        self.output_area.setTextCursor(cursor)

    def _on_result(self, result: dict) -> None:
        self._last_result = result
        self._set_status("", running=False)
        if result["success"]:
            self.status_label.setText(
                f"  Done — {result['language']} via {result['provider']}"
            )
            self.status_label.setStyleSheet(
                f"color: {NEON_GREEN}; font-size: 12px; "
                f"background: transparent; border: none; padding: 4px;"
            )
        else:
            self.status_label.setText(
                f"  {result['error'][:120]}"
            )
            self.status_label.setStyleSheet(
                f"color: {RED}; font-size: 12px; "
                f"background: transparent; border: none; padding: 4px;"
            )
            self._show_actions()

    def _open_in_editor(self) -> None:
        if self._last_result and self._last_result.get("language"):
            self.window.show_wizard()

    def _set_status(self, text: str, running: bool = False) -> None:
        self.status_label.setText(text)
        self.prompt_field.setEnabled(not running)
        self.go_btn.setEnabled(not running)
        if running:
            self.status_label.setStyleSheet(
                f"color: {TEXT_DIM}; font-size: 12px; "
                f"background: transparent; border: none; padding: 4px;"
            )

    def _show_actions(self) -> None:
        self.try_again_btn.setVisible(True)
        self.open_editor_btn.setVisible(True)

    def _hide_actions(self) -> None:
        self.try_again_btn.setVisible(False)
        self.open_editor_btn.setVisible(False)
