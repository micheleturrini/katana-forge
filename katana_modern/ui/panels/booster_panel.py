"""
Booster / Overdrive / Distortion Inspector Panel.
Features selection of all 23 Boss overdrive, distortion and fuzz models,
Drive, Tone, Bottom, Solo boost, and Direct Mix blending.
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
from katana_modern.core.amp_catalog import BOOSTER_MODELS


class BoosterPanel(QWidget):
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.accent = Theme.COLOR_BOOSTER

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        lbl = QLabel("BOOSTER TYPE:")
        lbl.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        header_row.addWidget(lbl)

        self.combo_type = QComboBox()
        self.combo_type.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.combo_type.setMinimumWidth(320)
        self.combo_type.setFixedHeight(34)
        for syx_id, name in BOOSTER_MODELS.items():
            self.combo_type.addItem(name, syx_id)
        self.combo_type.currentIndexChanged.connect(self._on_combo_changed)
        header_row.addWidget(self.combo_type, 1)

        self.btn_power = QPushButton("BOOSTER ON")
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
        self.btn_power.toggled.connect(lambda chk: self.model.set_param("booster_sw", 1 if chk else 0))
        header_row.addWidget(self.btn_power)

        layout.addLayout(header_row)

        # Knobs Frame
        knobs_frame = QFrame()
        knobs_frame.setObjectName("CardFrame")
        knobs_layout = QHBoxLayout(knobs_frame)
        knobs_layout.setContentsMargins(14, 14, 14, 14)
        knobs_layout.setSpacing(12)

        self.knob_drive = ModernKnob("Drive", 0, 120, 50, "", self.accent, diameter=68)
        self.knob_drive.value_changed.connect(lambda v: self.model.set_param("booster_drive", v))
        knobs_layout.addWidget(self.knob_drive)

        self.knob_tone = ModernKnob("Tone", 0, 100, 50, "", self.accent, diameter=60)
        self.knob_tone.value_changed.connect(lambda v: self.model.set_param("booster_tone", v))
        knobs_layout.addWidget(self.knob_tone)

        self.knob_bottom = ModernKnob("Bottom", 0, 100, 50, "", self.accent, diameter=60)
        self.knob_bottom.value_changed.connect(lambda v: self.model.set_param("booster_bottom", v))
        knobs_layout.addWidget(self.knob_bottom)

        self.knob_level = ModernKnob("Level", 0, 100, 50, "", self.accent, diameter=68)
        self.knob_level.value_changed.connect(lambda v: self.model.set_param("booster_effect_level", v))
        knobs_layout.addWidget(self.knob_level)

        self.knob_direct = ModernKnob("Direct Mix", 0, 100, 0, "%", self.accent, diameter=54)
        self.knob_direct.value_changed.connect(lambda v: self.model.set_param("booster_direct_mix", v))
        knobs_layout.addWidget(self.knob_direct)

        # Solo Section
        aux_box = QVBoxLayout()
        aux_box.setSpacing(6)
        aux_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_solo = QPushButton("SOLO SW")
        self.btn_solo.setCheckable(True)
        self.btn_solo.setFixedWidth(80)
        self.btn_solo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_SECONDARY};
                font-weight: 600;
                font-size: 11px;
                padding: 6px;
            }}
            QPushButton:checked {{
                background-color: {self.accent};
                color: #FFFFFF;
            }}
        """)
        self.btn_solo.toggled.connect(lambda chk: self.model.set_param("booster_solo_sw", 1 if chk else 0))
        aux_box.addWidget(self.btn_solo)

        knobs_layout.addLayout(aux_box)

        self.knob_solo_lvl = ModernKnob("Solo Lvl", 0, 100, 50, "", self.accent, diameter=52)
        self.knob_solo_lvl.value_changed.connect(lambda v: self.model.set_param("booster_solo_level", v))
        knobs_layout.addWidget(self.knob_solo_lvl)

        layout.addWidget(knobs_frame)
        layout.addStretch()

        self.model.parameter_changed.connect(self._on_parameter_changed)
        self.model.patch_loaded.connect(self.sync_from_model)
        self.sync_from_model()

    def _on_combo_changed(self, index: int):
        if index >= 0:
            syx_id = self.combo_type.currentData()
            self.model.set_param("booster_type", syx_id)

    def _on_parameter_changed(self, name: str, val: int, display_str: str):
        if name == "booster_sw":
            self.btn_power.setChecked(val > 0)
        elif name == "booster_type":
            idx = self.combo_type.findData(val)
            if idx >= 0 and self.combo_type.currentIndex() != idx:
                self.combo_type.setCurrentIndex(idx)
        elif name == "booster_drive":
            self.knob_drive.set_value_silent(val)
        elif name == "booster_tone":
            self.knob_tone.set_value_silent(val)
        elif name == "booster_bottom":
            self.knob_bottom.set_value_silent(val)
        elif name == "booster_effect_level":
            self.knob_level.set_value_silent(val)
        elif name == "booster_direct_mix":
            self.knob_direct.set_value_silent(val)
        elif name == "booster_solo_sw":
            self.btn_solo.setChecked(val > 0)
        elif name == "booster_solo_level":
            self.knob_solo_lvl.set_value_silent(val)

    def sync_from_model(self):
        self.btn_power.setChecked(self.model.get_param("booster_sw") > 0)
        self.knob_drive.set_value_silent(self.model.get_param("booster_drive"))
        self.knob_tone.set_value_silent(self.model.get_param("booster_tone"))
        self.knob_bottom.set_value_silent(self.model.get_param("booster_bottom"))
        self.knob_level.set_value_silent(self.model.get_param("booster_effect_level"))
        self.knob_direct.set_value_silent(self.model.get_param("booster_direct_mix"))
        self.btn_solo.setChecked(self.model.get_param("booster_solo_sw") > 0)
        self.knob_solo_lvl.set_value_silent(self.model.get_param("booster_solo_level"))

        m_id = self.model.get_param("booster_type")
        idx = self.combo_type.findData(m_id)
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
