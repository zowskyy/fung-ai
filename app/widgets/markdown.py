from __future__ import annotations

import re
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget


class MarkdownView(QWidget):
    """Renders markdown text with syntax highlighting for code blocks."""

    _CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    _INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
    _BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
    _ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
    _HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    _UL_ITEM_RE = re.compile(r"^[-*]\s+(.+)$", re.MULTILINE)
    _OL_ITEM_RE = re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE)
    _LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(
            "QTextBrowser { background: transparent; border: none; padding: 4px; }"
        )
        layout.addWidget(self.browser)

    def set_markdown(self, text: str) -> None:
        self.browser.setHtml(self._to_html(text))

    def append_markdown(self, text: str) -> None:
        cursor = self.browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        html = self._to_html(text)
        cursor.insertHtml(html + "<br>")
        self.browser.setTextCursor(cursor)
        self.browser.ensureCursorVisible()

    def clear(self) -> None:
        self.browser.clear()

    def toPlainText(self) -> str:
        return self.browser.toPlainText()

    def _to_html(self, text: str) -> str:
        parts = []
        last_end = 0

        for match in self._CODE_BLOCK_RE.finditer(text):
            if match.start() > last_end:
                parts.append(self._render_inline(text[last_end:match.start()]))
            lang = match.group(1) or ""
            code = escape(match.group(2).rstrip("\n"))
            parts.append(
                f'<pre style="background:#0a0f0a; color:#00ff66; padding:12px; '
                f'border:1px solid #0b3d22; border-radius:4px; '
                f'font-family:Consolas,monospace; font-size:12px; '
                f'margin:8px 0;">{code}</pre>'
            )
            last_end = match.end()

        if last_end < len(text):
            parts.append(self._render_inline(text[last_end:]))

        return "".join(parts)

    def _render_inline(self, text: str) -> str:
        text = escape(text)

        def replace_bold(m):
            return f'<b>{m.group(1)}</b>'
        text = self._BOLD_RE.sub(replace_bold, text)

        def replace_italic(m):
            return f'<i>{m.group(1)}</i>'
        text = self._ITALIC_RE.sub(replace_italic, text)

        def replace_inline_code(m):
            return (
                f'<code style="background:#0a0f0a; color:#00ff66; padding:2px 6px; '
                f'border:1px solid #0b3d22; border-radius:3px; '
                f'font-family:Consolas,monospace; font-size:12px;">{m.group(1)}</code>'
            )
        text = self._INLINE_CODE_RE.sub(replace_inline_code, text)

        def replace_link(m):
            return f'<a href="{m.group(2)}" style="color:#ff2e44;">{m.group(1)}</a>'
        text = self._LINK_RE.sub(replace_link, text)

        lines = text.split("\n")
        result = []
        in_ul = False
        in_ol = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_ul:
                    result.append("</ul>")
                    in_ul = False
                if in_ol:
                    result.append("</ol>")
                    in_ol = False
                result.append("<br>")
                continue

            header_match = self._HEADER_RE.match(stripped)
            if header_match:
                level = len(header_match.group(1))
                size = max(14, 22 - (level - 1) * 2)
                result.append(
                    f'<div style="font-size:{size}px; font-weight:700; margin:8px 0 4px 0; '
                    f'color:#00ff66;">{header_match.group(2)}</div>'
                )
                continue

            ul_match = self._UL_ITEM_RE.match(stripped)
            if ul_match:
                if not in_ul:
                    result.append('<ul style="margin:4px 0; padding-left:20px;">')
                    in_ul = True
                result.append(f'<li style="margin:2px 0;">{ul_match.group(1)}</li>')
                continue

            ol_match = self._OL_ITEM_RE.match(stripped)
            if ol_match:
                if not in_ol:
                    result.append('<ol style="margin:4px 0; padding-left:20px;">')
                    in_ol = True
                result.append(f'<li style="margin:2px 0;">{ol_match.group(1)}</li>')
                continue

            if in_ul:
                result.append("</ul>")
                in_ul = False
            if in_ol:
                result.append("</ol>")
                in_ol = False

            result.append(f'<div style="margin:2px 0;">{stripped}</div>')

        if in_ul:
            result.append("</ul>")
        if in_ol:
            result.append("</ol>")

        return "\n".join(result)
