"""
Effects (FX2) Inspector Panel.
Features selection of dynamic and special FX (Compressor, Auto-Wah, Pitch Shifter, Octave, etc.)
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame
)
from PyQt6.QtGui import QFont

from katana_modern.ui.theme import Theme
from katana_modern.ui.components.rotary_knob import ModernKnob
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.amp_catalog import FX_MODELS


class FxPanel(QWidget):
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.accent = Theme.COLOR_FX

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        lbl = QLabel("FX TYPE:")
        lbl.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        header_row.addWidget(lbl)

        self.combo_type = QComboBox()
        self.combo_type.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.combo_type.setMinimumWidth(320)
        self.combo_type.setFixedHeight(34)
        for syx_id, name in FX_MODELS.items():
            self.combo_type.addItem(name, syx_id)
        self.combo_type.currentIndexChanged.connect(self._on_combo_changed)
        header_row.addWidget(self.combo_type, 1)

        self.btn_power = QPushButton("FX ON")
        self.btn_power.setCheckable(True)
        self.btn_power.setFixedHeight(34)
        self.btn_power.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {self.accent};
                border-radius: 6px;
                color: {self.accent};
                font-weight: bold;
                padding: 4px 14px;
            }}
            QPushButton:checked {{
                background-color: {self.accent};
                color: #FFFFFF;
            }}
        """)
        self.btn_power.toggled.connect(lambda chk: self.model.set_param("fx_sw", 1 if chk else 0))
        header_row.addWidget(self.btn_power)

        layout.addLayout(header_row)

        # Knobs Frame
        knobs_frame = QFrame()
        knobs_frame.setObjectName("CardFrame")
        knobs_layout = QHBoxLayout(knobs_frame)
        knobs_layout.setContentsMargins(16, 16, 16, 16)
        knobs_layout.setSpacing(16)

        self.knob_p1 = ModernKnob("Param 1 / Sens", 0, 100, 50, "", self.accent, diameter=68)
        self.knob_p1.value_changed.connect(lambda v: self.model.set_param("fx_param1", v))
        knobs_layout.addWidget(self.knob_p1)

        self.knob_p2 = ModernKnob("Param 2 / Tone", 0, 100, 50, "", self.accent, diameter=68)
        self.knob_p2.value_changed.connect(lambda v: self.model.set_param("fx_param2", v))
        knobs_layout.addWidget(self.knob_p2)

        self.knob_lvl = ModernKnob("Effect Level", 0, 100, 75, "", self.accent, diameter=68)
        self.knob_lvl.value_changed.connect(lambda v: self.model.set_param("fx_level", v))
        knobs_layout.addWidget(self.knob_lvl)

        knobs_layout.addStretch()
        layout.addWidget(knobs_frame)
        layout.addStretch()

        self.model.parameter_changed.connect(self._on_parameter_changed)
        self.model.patch_loaded.connect(self.sync_from_model)
        self.sync_from_model()

    def _on_combo_changed(self, index: int):
        if index >= 0:
            syx_id = self.combo_type.currentData()
            self.model.set_param("fx_type", syx_id)

    def _on_parameter_changed(self, name: str, val: int, display_str: str):
        if name == "fx_sw":
            self.btn_power.setChecked(val > 0)
        elif name == "fx_type":
            idx = self.combo_type.findData(val)
            if idx >= 0 and self.combo_type.currentIndex() != idx:
                self.combo_type.setCurrentIndex(idx)
        elif name == "fx_param1":
            self.knob_p1.set_value_silent(val)
        elif name == "fx_param2":
            self.knob_p2.set_value_silent(val)
        elif name == "fx_level":
            self.knob_lvl.set_value_silent(val)

    def sync_from_model(self):
        self.btn_power.setChecked(self.model.get_param("fx_sw") > 0)
        self.knob_p1.set_value_silent(self.model.get_param("fx_param1"))
        self.knob_p2.set_value_silent(self.model.get_param("fx_param2"))
        self.knob_lvl.set_value_silent(self.model.get_param("fx_level"))

        m_id = self.model.get_param("fx_type")
        idx = self.combo_type.findData(m_id)
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
