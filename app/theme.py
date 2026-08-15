from __future__ import annotations

# Terminal / CRT aesthetic for Creator -> "fungai"
# Minimalist black background, neon-green text, red accents.

FONT = "Consolas, 'Courier New', monospace"
VERSION = "1.0.0"

# Palette
BG = "#050805"
PANEL = "#0a0f0a"
PANEL2 = "#0d130d"
BORDER = "#00ff66"          # neon green
BORDER_DIM = "#0b3d22"
TEXT = "#00ff66"            # neon green
TEXT_DIM = "#36a85a"
TEXT_MUTED = "#4f6b57"
RED = "#ff2e44"
RED_BG = "#1a0608"
RED_BORDER = "#ff2e44"
SELECT_BG = "#0b3d22"

ASCII_FUNGAI = r"""
   ╔═══════════╗
   ║  ┌─────┐  ║
   ║  │ ◆◆◆ │  ║  FUNGAI
   ║  └─────┘  ║  NEON
   ╚═══════════╝
"""

# Pure neon green (glow effect)
NEON_GREEN = "#00ff66"
NEON_GREEN_BRIGHT = "#33ff99"
NEON_GREEN_DIM = "#00cc55"


APP_QSS = f"""
QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: {FONT};
    font-size: 13px;
}}
QLabel {{ color: {TEXT}; }}
QLabel#title {{
    font-size: 26px; font-weight: 700; color: {TEXT};
    font-family: {FONT};
}}
QLabel#section {{
    font-size: 14px; font-weight: 700; color: {TEXT};
    border-bottom: 1px solid {BORDER_DIM}; padding-bottom: 4px; margin-top: 10px;
    font-family: {FONT};
}}
QLabel#muted {{ color: {TEXT_MUTED}; }}
QLabel#card_title {{ font-size: 15px; font-weight: 700; color: {TEXT}; }}

QPushButton {{
    background-color: {PANEL};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 8px 14px;
    font-family: {FONT};
    font-size: 13px;
}}
QPushButton:hover {{ background-color: {SELECT_BG}; }}
QPushButton:pressed {{ background-color: {BORDER}; color: {BG}; }}
QPushButton:disabled {{ color: {TEXT_DIM}; border-color: {BORDER_DIM}; }}

QPushButton#primary {{
    background-color: {BORDER}; color: {BG}; border: 2px solid {BORDER};
    font-weight: 700; border-radius: 4px;
}}
QPushButton#primary:hover {{
    background-color: #1aff77; border-color: #1aff77;
    box-shadow: 0 0 20px rgba(0, 255, 102, 0.8);
}}
QPushButton#primary:pressed {{ background-color: #00cc55; }}
QPushButton#primary:disabled {{ background-color: {SELECT_BG}; color: {TEXT_DIM}; border-color: {BORDER_DIM}; }}

QPushButton#card {{
    background-color: {PANEL}; border: 1px solid {BORDER_DIM};
    border-radius: 6px; padding: 8px; text-align: left;
}}
QPushButton#card:hover {{ border-color: {BORDER}; background-color: {SELECT_BG}; }}

QPushButton#card_row {{
    background-color: {PANEL2}; border: 1px solid {BORDER_DIM};
    border-radius: 4px; text-align: left; padding: 6px 12px;
}}
QPushButton#card_row:hover {{ border-color: {BORDER}; }}

QPushButton#danger {{
    background-color: {RED_BG}; color: {RED}; border: 1px solid {RED_BORDER};
    border-radius: 4px; padding: 8px 14px; font-family: {FONT};
}}
QPushButton#danger:hover {{ background-color: {RED}; color: {BG}; }}

QLineEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {PANEL}; border: 1px solid {BORDER_DIM}; border-radius: 4px;
    padding: 6px; color: {TEXT}; font-family: {FONT};
    selection-background-color: {BORDER}; selection-color: {BG};
}}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus {{ border: 1px solid {BORDER}; }}
QPlainTextEdit {{ background-color: {BG}; }}

QListWidget {{ background-color: transparent; border: none; outline: 0; }}
QListWidget::item {{
    padding: 6px 8px; border-radius: 4px; margin: 1px 0; color: {TEXT_DIM};
}}
QListWidget::item:selected {{ background-color: {SELECT_BG}; color: {TEXT}; }}
QListWidget::item:hover {{ background-color: {PANEL2}; }}

QTabWidget::pane {{ border: 1px solid {BORDER_DIM}; border-radius: 4px; background: {BG}; }}
QTabBar::tab {{
    padding: 8px 18px; color: {TEXT_MUTED}; background: {PANEL};
    border: 1px solid {BORDER_DIM}; border-bottom: none;
    border-top-left-radius: 4px; border-top-right-radius: 4px;
    font-family: {FONT};
}}
QTabBar::tab:selected {{ color: {TEXT}; background: {BG}; border-color: {BORDER}; }}
QTabBar::tab:hover {{ color: {TEXT}; }}

QCheckBox {{ color: {TEXT}; spacing: 8px; font-family: {FONT}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border: 1px solid {BORDER}; background: {PANEL};
}}
QCheckBox::indicator:checked {{ background: {BORDER}; }}

QTextBrowser {{ background: transparent; border: none; color: {TEXT}; }}

QScrollBar:vertical {{ background: {PANEL}; width: 10px; }}
QScrollBar::handle:vertical {{
    background: {BORDER_DIM}; border-radius: 5px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {BORDER}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QFrame {{ border: none; }}
"""


def apply_theme(app) -> None:
    app.setStyleSheet(APP_QSS)
