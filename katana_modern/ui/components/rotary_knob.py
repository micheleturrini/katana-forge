"""
High-fidelity modern DAW Vector Rotary Knob.
Features vector arc rendering with neon glow, mouse drag control,
mouse wheel fine-tuning, and direct numeric input on double-click.
"""

import math
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient,
    QFont, QMouseEvent, QWheelEvent
)
from PyQt6.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QLabel

from katana_modern.ui.theme import Theme


class ModernKnob(QWidget):
    """
    Vector rotary dial with DAW ergonomics.
    """
    value_changed = pyqtSignal(int)  # new integer value

    def __init__(
        self,
        title: str,
        min_val: int = 0,
        max_val: int = 100,
        initial_val: int = 50,
        unit: str = "",
        accent_color: str = Theme.COLOR_AMP,
        diameter: int = 64,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.title = title
        self.min_val = min_val
        self.max_val = max_val
        self._value = initial_val
        self.unit = unit
        self.accent_color = accent_color
        self.diameter = diameter

        self._dragging = False
        self._last_y = 0
        self._drag_start_val = initial_val

        # Inline editor for double-click entry
        self._line_edit = QLineEdit(self)
        self._line_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._line_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                color: #FFFFFF;
                border: 1px solid {self.accent_color};
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
                padding: 1px;
            }}
        """)
        self._line_edit.hide()
        self._line_edit.returnPressed.connect(self._on_text_entered)
        self._line_edit.editingFinished.connect(self._on_editing_finished)

        # Widget sizing
        total_width = max(self.diameter + 24, 76)
        total_height = self.diameter + 38
        self.setFixedSize(total_width, total_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int):
        clamped = max(self.min_val, min(self.max_val, val))
        if clamped != self._value:
            self._value = clamped
            self.update()
            self.value_changed.emit(self._value)

    def set_value_silent(self, val: int):
        """Update value without emitting signal (for external model updates)."""
        clamped = max(self.min_val, min(self.max_val, val))
        if clamped != self._value:
            self._value = clamped
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._last_y = event.position().y()
            self._drag_start_val = self._value
            if self._line_edit.isVisible():
                self._line_edit.hide()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta_y = self._last_y - event.position().y()
            self._last_y = event.position().y()

            # Shift key gives 4x finer precision
            scale = 0.25 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1.0
            range_span = self.max_val - self.min_val
            step = (range_span / 120.0) * delta_y * scale

            new_val = round(self._value + step)
            self.value = new_val

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        step = 1 if abs(delta) < 120 else 2
        if delta > 0:
            self.value = self._value + step
        else:
            self.value = self._value - step
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # Open inline editor positioned over value text
        w = 48
        h = 18
        x = int((self.width() - w) / 2)
        y = int(self.height() - h - 2)
        self._line_edit.setGeometry(x, y, w, h)
        self._line_edit.setText(str(self._value))
        self._line_edit.selectAll()
        self._line_edit.show()
        self._line_edit.setFocus()

    def _on_text_entered(self):
        text = self._line_edit.text().strip()
        try:
            val = int(text)
            self.value = val
        except ValueError:
            pass
        self._line_edit.hide()

    def _on_editing_finished(self):
        self._line_edit.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        cx = w / 2.0
        cy = self.diameter / 2.0 + 16.0
        radius = self.diameter / 2.0

        # 1. Draw Title
        painter.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        painter.setPen(Theme.qcolor(Theme.TEXT_SECONDARY))
        title_rect = QRectF(0, 0, w, 14)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title.upper())

        # 2. Angle Calculations
        # 270 degree total arc: from 135 deg (bottom left) to 405 deg (bottom right)
        START_ANGLE = 135.0
        TOTAL_SPAN = 270.0
        val_norm = (self._value - self.min_val) / max(1, (self.max_val - self.min_val))
        active_span = TOTAL_SPAN * val_norm

        arc_rect = QRectF(cx - radius + 3, cy - radius + 3, (radius - 3) * 2, (radius - 3) * 2)

        # 3. Background Track Arc
        bg_pen = QPen(Theme.qcolor(Theme.BORDER_SUBTLE), 3.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        # Qt drawArc uses 1/16th of a degree, counter-clockwise from 3 o'clock (0 deg)
        # Angle conversion: -start_angle in Qt coords
        painter.drawArc(arc_rect, int((-START_ANGLE) * 16), int((-TOTAL_SPAN) * 16))

        # 4. Active Illuminated Track Arc
        if active_span > 0:
            accent_qcol = Theme.qcolor(self.accent_color)
            glow_pen = QPen(accent_qcol, 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(glow_pen)
            painter.drawArc(arc_rect, int((-START_ANGLE) * 16), int((-active_span) * 16))

        # 5. Knurled Metallic Cap Body
        cap_radius = radius - 7
        cap_rect = QRectF(cx - cap_radius, cy - cap_radius, cap_radius * 2, cap_radius * 2)

        # Radial Gradient for metallic depth
        grad = QRadialGradient(QPointF(cx - cap_radius * 0.25, cy - cap_radius * 0.25), cap_radius * 1.2)
        grad.setColorAt(0.0, Theme.qcolor("#2E333F"))
        grad.setColorAt(0.7, Theme.qcolor("#1B1E25"))
        grad.setColorAt(1.0, Theme.qcolor("#14161B"))

        painter.setPen(QPen(Theme.qcolor(Theme.BORDER_SUBTLE), 1.0))
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(cap_rect)

        # 6. Indicator Needle / Pointer
        curr_angle_deg = START_ANGLE + active_span
        curr_angle_rad = math.radians(curr_angle_deg)
        inner_r = cap_radius * 0.45
        outer_r = cap_radius * 0.85

        p1 = QPointF(cx + inner_r * math.cos(curr_angle_rad), cy + inner_r * math.sin(curr_angle_rad))
        p2 = QPointF(cx + outer_r * math.cos(curr_angle_rad), cy + outer_r * math.sin(curr_angle_rad))

        needle_pen = QPen(Theme.qcolor(self.accent_color), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(needle_pen)
        painter.drawLine(p1, p2)

        # 7. Value Label
        if not self._line_edit.isVisible():
            painter.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            painter.setPen(Theme.qcolor(Theme.TEXT_PRIMARY))
            val_str = f"{self._value}{' ' + self.unit if self.unit else ''}"
            val_rect = QRectF(0, cy + radius + 2, w, 16)
            painter.drawText(val_rect, Qt.AlignmentFlag.AlignCenter, val_str)
