from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from app.widgets.markdown import MarkdownView


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_renders_bold_and_inline_code(app):
    view = MarkdownView()
    html = view._to_html("**bold** and `code`")
    assert "<b>bold</b>" in html
    assert "<code" in html


def test_renders_headers_and_lists(app):
    view = MarkdownView()
    html = view._to_html("# Title\n- one\n- two")
    assert "Title" in html
    assert "<li" in html


def test_renders_code_block(app):
    view = MarkdownView()
    html = view._to_html("```python\nprint(1)\n```")
    assert "print(1)" in html
    assert "<pre" in html


def test_append_and_clear(app):
    view = MarkdownView()
    view.set_markdown("first")
    view.append_markdown("second")
    assert "first" in view.toPlainText()
    assert "second" in view.toPlainText()
    view.clear()
    assert view.toPlainText() == ""
