"""
Modern Dark DAW Theme Definition (Neural DSP / Helix Native Style).
Low-contrast deep charcoal palette, high-readability typography,
and signature module accent colors.
"""

from PyQt6.QtGui import QColor, QFont


class Theme:
    # Backgrounds
    BG_ROOT = "#0F1013"
    BG_PANEL = "#16181D"
    BG_CARD = "#1D2027"
    BG_CARD_HOVER = "#252932"
    BG_CARD_ACTIVE = "#2C313C"
    BG_INPUT = "#131418"

    # Borders
    BORDER_SUBTLE = "#2A2E38"
    BORDER_FOCUS = "#484F60"
    BORDER_GLOW = "#00FFA3"

    # Text
    TEXT_PRIMARY = "#EDF0F5"
    TEXT_SECONDARY = "#9BA1B0"
    TEXT_MUTED = "#606675"
    TEXT_DIM = "#424754"

    # Module Accents
    COLOR_BOOSTER = "#E67E22"   # Warm Amber / Orange
    COLOR_MOD = "#00CEC9"       # Vibrant Cyan
    COLOR_AMP = "#E74C3C"       # British Crimson Red
    COLOR_EQ = "#2ECC71"        # Emerald Green
    COLOR_FX = "#9B59B6"        # Deep Amethyst
    COLOR_DELAY = "#3498DB"     # Electric Blue
    COLOR_REVERB = "#6C5CE7"    # Ethereal Indigo
    COLOR_NS = "#95A5A6"        # Titanium Gray
    COLOR_MASTER = "#F1C40F"    # Gold

    # Status
    COLOR_CONNECTED = "#00FFA3"
    COLOR_DISCONNECTED = "#E74C3C"

    @staticmethod
    def qcolor(hex_str: str, alpha: int = 255) -> QColor:
        c = QColor(hex_str)
        c.setAlpha(alpha)
        return c


DARK_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {Theme.BG_ROOT};
    color: {Theme.TEXT_PRIMARY};
}}

QWidget {{
    font-family: 'Inter', 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
    color: {Theme.TEXT_PRIMARY};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {Theme.BG_ROOT};
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {Theme.BORDER_SUBTLE};
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {Theme.BORDER_FOCUS};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Push Buttons */
QPushButton {{
    background-color: {Theme.BG_CARD};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
    color: {Theme.TEXT_PRIMARY};
}}
QPushButton:hover {{
    background-color: {Theme.BG_CARD_HOVER};
    border-color: {Theme.BORDER_FOCUS};
}}
QPushButton:pressed {{
    background-color: {Theme.BG_CARD_ACTIVE};
}}
QPushButton:disabled {{
    background-color: {Theme.BG_INPUT};
    color: {Theme.TEXT_MUTED};
    border-color: transparent;
}}

/* Combo Boxes */
QComboBox {{
    background-color: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 6px 12px;
    color: {Theme.TEXT_PRIMARY};
    font-weight: 500;
}}
QComboBox:hover {{
    border-color: {Theme.BORDER_FOCUS};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {Theme.BG_PANEL};
    border: 1px solid {Theme.BORDER_SUBTLE};
    selection-background-color: {Theme.BG_CARD_ACTIVE};
    selection-color: {Theme.TEXT_PRIMARY};
    padding: 4px;
    outline: none;
}}

/* Line Edits */
QLineEdit {{
    background-color: {Theme.BG_INPUT};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 6px;
    padding: 6px 10px;
    color: {Theme.TEXT_PRIMARY};
    selection-background-color: {Theme.COLOR_AMP};
}}
QLineEdit:focus {{
    border-color: {Theme.BORDER_GLOW};
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 6px;
    background: {Theme.BG_INPUT};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {Theme.COLOR_AMP};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {Theme.TEXT_PRIMARY};
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: #FFFFFF;
}}

/* Group Boxes / Frames */
QFrame#PanelFrame {{
    background-color: {Theme.BG_PANEL};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 8px;
}}
QFrame#CardFrame {{
    background-color: {Theme.BG_CARD};
    border: 1px solid {Theme.BORDER_SUBTLE};
    border-radius: 8px;
}}
"""
