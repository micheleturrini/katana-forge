"""
Real-Time Dynamic Frequency Response & Tone Analyzer.
Plots an interactive DSP-style frequency curve of the guitar tone stack,
Contour filters, and 10-band Graphic EQ in modern DAW visual style.
"""

import math
from typing import Optional
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath
)

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel


class DynamicToneAnalyzer(QWidget):
    """
    Real-time dynamic EQ spectrum visualizer.
    Calculates and renders the cumulative frequency response curve.
    """
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model

        self.setMinimumSize(220, 110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        # Connect to model parameter updates
        self.model.parameter_changed.connect(self._on_param_changed)
        self.model.patch_loaded.connect(lambda name: self.update())

    def _on_param_changed(self, name: str, val: int, display: str):
        # Only repaint if an EQ or tone parameter changed
        if any(prefix in name for prefix in [
            "preamp_bass", "preamp_middle", "preamp_treble", "preamp_presence",
            "contour", "eq1", "geq", "cab_resonance", "preamp_bright"
        ]):
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        w = self.width()
        h = self.height()

        # 1. Background slate card
        bg_rect = self.rect()
        painter.setPen(QPen(QColor(Theme.BORDER_SUBTLE), 1))
        painter.setBrush(QBrush(QColor(18, 20, 24)))
        painter.drawRoundedRect(bg_rect.adjusted(1, 1, -1, -1), 6, 6)

        # Margins inside display
        left_m = 36
        right_m = 12
        top_m = 16
        bot_m = 26

        plot_w = max(10, w - left_m - right_m)
        plot_h = max(10, h - top_m - bot_m)
        center_y = top_m + plot_h / 2.0

        # 2. Grid & Scales
        # Frequency markers: 100Hz, 1kHz, 10kHz
        freq_markers = [
            (100, "100Hz"),
            (500, "500"),
            (1000, "1kHz"),
            (5000, "5k"),
            (10000, "10kHz")
        ]

        min_f = 20.0
        max_f = 20000.0
        log_min = math.log10(min_f)
        log_max = math.log10(max_f)
        log_range = log_max - log_min

        font_sm = QFont("Inter", 7)
        painter.setFont(font_sm)

        # Vertical Freq Grid Lines
        for freq, label in freq_markers:
            frac = (math.log10(freq) - log_min) / log_range
            x = left_m + frac * plot_w
            painter.setPen(QPen(QColor(36, 42, 52, 160), 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(x), top_m, int(x), top_m + plot_h)
            painter.setPen(QColor(Theme.TEXT_MUTED))
            painter.drawText(int(x) - 15, top_m + plot_h + 3, 30, 12, Qt.AlignmentFlag.AlignCenter, label)

        # Horizontal dB Grid Lines: +12, 0, -12 dB
        db_markers = [(12, "+12"), (0, "0"), (-12, "-12")]
        max_db = 18.0
        for db_val, label in db_markers:
            y = center_y - (db_val / max_db) * (plot_h / 2.0)
            pen_style = Qt.PenStyle.SolidLine if db_val == 0 else Qt.PenStyle.DotLine
            color = QColor(60, 70, 85, 200) if db_val == 0 else QColor(36, 42, 52, 140)
            painter.setPen(QPen(color, 1, pen_style))
            painter.drawLine(left_m, int(y), left_m + plot_w, int(y))
            painter.setPen(QColor(Theme.TEXT_MUTED))
            painter.drawText(4, int(y) - 6, 28, 12, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # 3. Tone Parameters Calculation
        bass = self.model.get_param("preamp_bass", 50)
        mid = self.model.get_param("preamp_middle", 50)
        treb = self.model.get_param("preamp_treble", 50)
        pres = self.model.get_param("preamp_presence", 50)
        bright = self.model.get_param("preamp_bright", 0)

        # Contour
        c_sw = self.model.get_param("contour_sw", 0)
        c_type = self.model.get_param("contour_type", 0)

        # Graphic EQ (if enabled)
        eq_on = self.model.get_param("eq1_sw", 0)
        eq_type = self.model.get_param("eq1_type", 0)
        geq_offsets = {}
        if eq_on:
            bands = [
                (31.25, "geq_31"), (62.5, "geq_62"), (125, "geq_125"), (250, "geq_250"),
                (500, "geq_500"), (1000, "geq_1k"), (2000, "geq_2k"), (4000, "geq_4k"),
                (8000, "geq_8k"), (16000, "geq_16k")
            ]
            for f_band, k_name in bands:
                raw_val = self.model.get_param(k_name, 24)
                geq_offsets[f_band] = (raw_val - 24) * 0.5  # +/- 12dB

        # 4. Compute Dynamic Curve Points
        num_points = max(60, int(plot_w / 2))
        curve_points = []

        for i in range(num_points + 1):
            frac = i / float(num_points)
            f = 10 ** (log_min + frac * log_range)

            # Cumulative dB response
            db = 0.0

            # Bass Shelf (around 100Hz)
            g_bass = (bass - 50) * 0.22
            db += g_bass / (1.0 + (f / 130.0) ** 2)

            # Middle Bell (peak around 750Hz)
            g_mid = (mid - 50) * 0.20
            db += g_mid / (1.0 + 3.5 * ((f - 750.0) / 750.0) ** 2)

            # Treble Shelf (around 3kHz)
            g_treb = (treb - 50) * 0.22
            db += g_treb * ((f / 2600.0) ** 2) / (1.0 + (f / 2600.0) ** 2)

            # Presence (around 7.5kHz)
            g_pres = (pres - 50) * 0.16
            db += g_pres * ((f / 6000.0) ** 2) / (1.0 + (f / 6000.0) ** 2)

            if bright:
                db += 2.0 * ((f / 4000.0) ** 2) / (1.0 + (f / 4000.0) ** 2)

            # Contour shaping
            if c_sw:
                if c_type == 0:  # Type 1: scoop at 600Hz, slight bass punch
                    db -= 4.5 / (1.0 + 6.0 * ((f - 600.0) / 600.0) ** 2)
                    db += 1.8 / (1.0 + (f / 120.0) ** 2)
                elif c_type == 1:  # Type 2: scoop at 1.2kHz
                    db -= 5.0 / (1.0 + 5.0 * ((f - 1200.0) / 1200.0) ** 2)
                elif c_type == 2:  # Type 3: aggressive modern scoop at 800Hz
                    db -= 6.5 / (1.0 + 8.0 * ((f - 800.0) / 800.0) ** 2)
                    db += 2.5 * ((f / 7000.0) ** 2) / (1.0 + (f / 7000.0) ** 2)

            # Graphic EQ contribution
            if eq_on:
                for f_band, g_val in geq_offsets.items():
                    if g_val != 0:
                        db += g_val / (1.0 + 4.0 * ((f - f_band) / f_band) ** 2)

            # Map dB to Pixel Y
            y = center_y - (db / max_db) * (plot_h / 2.0)
            y = max(top_m + 1.0, min(top_m + plot_h - 1.0, y))
            x = left_m + frac * plot_w
            curve_points.append(QPointF(x, y))

        # 5. Render Glowing Translucent Area Fill Under Curve
        fill_path = QPainterPath()
        fill_path.moveTo(left_m, top_m + plot_h)
        for pt in curve_points:
            fill_path.lineTo(pt)
        fill_path.lineTo(left_m + plot_w, top_m + plot_h)
        fill_path.closeSubpath()

        grad = QLinearGradient(0, top_m, 0, top_m + plot_h)
        neon_color = QColor(0, 229, 255)  # Cyan DAW neon
        grad.setColorAt(0.0, QColor(0, 229, 255, 75))
        grad.setColorAt(0.7, QColor(0, 229, 255, 20))
        grad.setColorAt(1.0, QColor(0, 229, 255, 0))
        painter.fillPath(fill_path, QBrush(grad))

        # 6. Render Primary Glowing Curve Line
        curve_path = QPainterPath()
        if curve_points:
            curve_path.moveTo(curve_points[0])
            for pt in curve_points[1:]:
                curve_path.lineTo(pt)

        # Glow line
        painter.setPen(QPen(QColor(0, 229, 255, 60), 4))
        painter.drawPath(curve_path)

        # Sharp top line
        painter.setPen(QPen(QColor(0, 229, 255, 240), 2))
        painter.drawPath(curve_path)

        # 7. Corner Badge
        painter.setPen(QColor(Theme.TEXT_MUTED))
        font_badge = QFont("Inter", 8, QFont.Weight.Bold)
        painter.setFont(font_badge)
        painter.drawText(w - 150, 4, 140, 16, Qt.AlignmentFlag.AlignRight, "● LIVE TONE CURVE")
