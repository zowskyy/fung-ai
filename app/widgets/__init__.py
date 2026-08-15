from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.field_models import Field, FieldValidationError

from .context_panel import ContextPanel
from .diff_view import DiffView
from .markdown import MarkdownView
from .sidebar import SidebarWidget
from .tool_view import ToolExecutionView

Getter = Callable[[], object]
Setter = Callable[[object], None]


def build_field_form(
    fields: list[Field], values: dict[str, object]
) -> tuple[QWidget, Callable[[], dict], Callable[[dict], None]]:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    form = QFormLayout()
    editors: dict[str, tuple[QWidget, Getter, Setter]] = {}

    for field in fields:
        editor, getter, setter = _make_editor(field)
        editors[field.id] = (editor, getter, setter)
        label = QLabel(field.label)
        if field.help:
            label.setToolTip(field.help)
        form.addRow(label, editor)

    error_label = QLabel("")
    error_label.setStyleSheet("color: #ff2e44; font-family: Consolas, 'Courier New', monospace;")
    error_label.setWordWrap(True)
    form.addRow("", error_label)
    layout.addLayout(form)

    def get_values() -> dict:
        result = {}
        for field in fields:
            _, getter, _ = editors[field.id]
            result[field.id] = getter()
        return result

    def validate() -> dict:
        raw = get_values()
        result = {}
        try:
            for field in fields:
                result[field.id] = field.validate(raw.get(field.id, field.default))
        except FieldValidationError as exc:
            error_label.setText(str(exc))
            raise
        error_label.setText("")
        return result

    def set_values(new_values: dict) -> None:
        for field in fields:
            if field.id in new_values:
                _, _, setter = editors[field.id]
                setter(new_values[field.id])

    return container, validate, set_values


def _make_editor(field: Field) -> tuple[QWidget, Getter, Setter]:
    if field.type == "select":
        combo = QComboBox()
        combo.addItems(field.options)
        index = combo.findText(str(field.default))
        if index >= 0:
            combo.setCurrentIndex(index)
        return combo, combo.currentText, combo.setCurrentText

    if field.type == "color":
        line = QLineEdit(str(field.default))
        swatch = QPushButton()
        swatch.setFixedSize(28, 28)

        def _paint() -> None:
            color = QColor(line.text().strip() or "#000000")
            swatch.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #999; border-radius: 4px;"
            )

        def _pick() -> None:
            color = QColorDialog.getColor(
                QColor(line.text().strip() or "#000000"), swatch, f"Choose {field.label}"
            )
            if color.isValid():
                line.setText(color.name())
                _paint()

        swatch.clicked.connect(_pick)
        line.textChanged.connect(_paint)
        _paint()
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(swatch)
        row_layout.addWidget(line)
        return row, lambda: line.text().strip() or "#000000", lambda v: line.setText(str(v))

    if field.type == "number":
        uses_float = any(
            isinstance(v, float) for v in (field.min, field.max, field.default)
        )
        if uses_float:
            spin = QDoubleSpinBox()
            spin.setRange(
                float(field.min if field.min is not None else 0),
                float(field.max if field.max is not None else 1_000_000),
            )
            spin.setDecimals(2)
            spin.setValue(float(field.default or 0))
            return spin, spin.value, spin.setValue
        spin = QSpinBox()
        spin.setRange(
            int(field.min if field.min is not None else 0),
            int(field.max if field.max is not None else 1_000_000),
        )
        spin.setValue(int(field.default or 0))
        return spin, spin.value, spin.setValue

    if field.type == "textarea":
        text = QPlainTextEdit(str(field.default))
        text.setFixedHeight(140)
        return text, text.toPlainText, text.setPlainText

    line = QLineEdit(str(field.default))
    return line, line.text, line.setText


__all__ = [
    "build_field_form",
    "SidebarWidget",
    "MarkdownView",
    "DiffView",
    "ToolExecutionView",
    "ContextPanel",
]