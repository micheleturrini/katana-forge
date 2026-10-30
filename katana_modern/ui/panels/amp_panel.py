"""
Preamp & Amplifier Module Inspector Panel.
Features categorized selector for standard models, variations, and all 28 Sneaky Amps,
rotary EQ controls, Bright/Solo switches, and expandable Custom Amp parameters.
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QFont

from katana_modern.ui.theme import Theme
from katana_modern.ui.components.rotary_knob import ModernKnob
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.amp_catalog import PREAMP_MODELS


class AmpPanel(QWidget):
    """
    Dedicated Preamp inspector with modern DAW styling.
    """
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.accent = Theme.COLOR_AMP

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # -------------------------------------------------------------
        # 1. Header Row: Preamp Model Selector + Power Switch
        # -------------------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        lbl_model = QLabel("AMPLIFIER MODEL:")
        lbl_model.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_model.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        header_row.addWidget(lbl_model)

        self.combo_model = QComboBox()
        self.combo_model.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        self.combo_model.setMinimumWidth(320)
        self.combo_model.setFixedHeight(34)
        self._populate_amp_models()
        self.combo_model.currentIndexChanged.connect(self._on_combo_changed)
        header_row.addWidget(self.combo_model)

        self.lbl_desc = QLabel("")
        self.lbl_desc.setFont(QFont("Inter", 10))
        self.lbl_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        header_row.addWidget(self.lbl_desc, 1)

        # Power Toggle
        self.btn_power = QPushButton("PREAMP ON")
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
        self.btn_power.toggled.connect(lambda chk: self.model.set_param("preamp_sw", 1 if chk else 0))
        header_row.addWidget(self.btn_power)

        layout.addLayout(header_row)

        # -------------------------------------------------------------
        # 2. Main Knobs Area (Tone Stack)
        # -------------------------------------------------------------
        tone_frame = QFrame()
        tone_frame.setObjectName("CardFrame")
        tone_layout = QHBoxLayout(tone_frame)
        tone_layout.setContentsMargins(14, 14, 14, 14)
        tone_layout.setSpacing(8)

        # Large Gain
        self.knob_gain = ModernKnob("Gain", 0, 120, 50, "", self.accent, diameter=72)
        self.knob_gain.value_changed.connect(lambda v: self.model.set_param("preamp_gain", v))
        tone_layout.addWidget(self.knob_gain)

        # Tone Stack: Bass, Middle, Treble, Presence
        self.knob_bass = ModernKnob("Bass", 0, 100, 50, "", self.accent, diameter=60)
        self.knob_bass.value_changed.connect(lambda v: self.model.set_param("preamp_bass", v))
        tone_layout.addWidget(self.knob_bass)

        self.knob_mid = ModernKnob("Middle", 0, 100, 50, "", self.accent, diameter=60)
        self.knob_mid.value_changed.connect(lambda v: self.model.set_param("preamp_middle", v))
        tone_layout.addWidget(self.knob_mid)

        self.knob_treble = ModernKnob("Treble", 0, 100, 50, "", self.accent, diameter=60)
        self.knob_treble.value_changed.connect(lambda v: self.model.set_param("preamp_treble", v))
        tone_layout.addWidget(self.knob_treble)

        self.knob_presence = ModernKnob("Presence", 0, 100, 50, "", self.accent, diameter=60)
        self.knob_presence.value_changed.connect(lambda v: self.model.set_param("preamp_presence", v))
        tone_layout.addWidget(self.knob_presence)

        # Large Volume
        self.knob_vol = ModernKnob("Volume", 0, 100, 60, "", self.accent, diameter=72)
        self.knob_vol.value_changed.connect(lambda v: self.model.set_param("preamp_volume", v))
        tone_layout.addWidget(self.knob_vol)

        # Auxiliary Switches & Solo
        aux_box = QVBoxLayout()
        aux_box.setSpacing(8)
        aux_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_bright = QPushButton("BRIGHT")
        self.btn_bright.setCheckable(True)
        self.btn_bright.setFixedWidth(80)
        self.btn_bright.setStyleSheet(self._button_toggle_style())
        self.btn_bright.toggled.connect(lambda chk: self.model.set_param("preamp_bright", 1 if chk else 0))
        aux_box.addWidget(self.btn_bright)

        self.btn_solo = QPushButton("SOLO")
        self.btn_solo.setCheckable(True)
        self.btn_solo.setFixedWidth(80)
        self.btn_solo.setStyleSheet(self._button_toggle_style())
        self.btn_solo.toggled.connect(lambda chk: self.model.set_param("preamp_solo_sw", 1 if chk else 0))
        aux_box.addWidget(self.btn_solo)

        tone_layout.addLayout(aux_box)

        self.knob_solo_lvl = ModernKnob("Solo Lvl", 0, 100, 50, "", self.accent, diameter=50)
        self.knob_solo_lvl.value_changed.connect(lambda v: self.model.set_param("preamp_solo_level", v))
        tone_layout.addWidget(self.knob_solo_lvl)

        layout.addWidget(tone_frame)

        # -------------------------------------------------------------
        # 3. Collapsible Advanced / Sneaky Parameters
        # -------------------------------------------------------------
        self.btn_expand_adv = QPushButton("▸ Advanced Custom Tone Shaping (Sneaky Amp Controls)")
        self.btn_expand_adv.setCheckable(True)
        self.btn_expand_adv.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {Theme.TEXT_SECONDARY};
                text-align: left;
                font-weight: bold;
                font-size: 11px;
                padding: 4px;
            }}
            QPushButton:hover {{
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.btn_expand_adv.toggled.connect(self._toggle_advanced)
        layout.addWidget(self.btn_expand_adv)

        self.adv_frame = QFrame()
        self.adv_frame.setObjectName("CardFrame")
        adv_layout = QHBoxLayout(self.adv_frame)
        adv_layout.setContentsMargins(14, 10, 14, 10)
        adv_layout.setSpacing(16)

        self.knob_bottom = ModernKnob("Custom Bottom", 0, 100, 50, "", self.accent, diameter=54)
        self.knob_bottom.value_changed.connect(lambda v: self.model.set_param("preamp_custom_bottom", v))
        adv_layout.addWidget(self.knob_bottom)

        self.knob_edge = ModernKnob("Custom Edge", 0, 100, 50, "", self.accent, diameter=54)
        self.knob_edge.value_changed.connect(lambda v: self.model.set_param("preamp_custom_edge", v))
        adv_layout.addWidget(self.knob_edge)

        self.knob_char = ModernKnob("Character", 0, 100, 50, "", self.accent, diameter=54)
        self.knob_char.value_changed.connect(lambda v: self.model.set_param("preamp_custom_char", v))
        adv_layout.addWidget(self.knob_char)

        adv_layout.addStretch()
        self.adv_frame.hide()
        layout.addWidget(self.adv_frame)

        layout.addStretch()

        # Connect to model reactive updates
        self.model.parameter_changed.connect(self._on_parameter_changed)
        self.model.patch_loaded.connect(self.sync_from_model)
        self.sync_from_model()

    def _populate_amp_models(self):
        self.combo_model.clear()
        categories = [
            "Standard",
            "MkII Variation",
            "Sneaky Clean",
            "Sneaky Crunch",
            "Sneaky Vintage Rock",
            "Sneaky High Gain",
            "Sneaky Metal"
        ]
        for cat in categories:
            for syx_id, info in PREAMP_MODELS.items():
                if info.category == cat:
                    prefix = "★ " if "Sneaky" in cat else ""
                    self.combo_model.addItem(f"{prefix}{info.name}  [{info.category}]", syx_id)

    def _on_combo_changed(self, index: int):
        if index >= 0:
            syx_id = self.combo_model.currentData()
            self.model.set_param("preamp_type", syx_id)
            info = PREAMP_MODELS.get(syx_id)
            if info:
                self.lbl_desc.setText(info.description)

    def _toggle_advanced(self, checked: bool):
        self.btn_expand_adv.setText(
            "▾ Advanced Custom Tone Shaping (Sneaky Amp Controls)" if checked
            else "▸ Advanced Custom Tone Shaping (Sneaky Amp Controls)"
        )
        self.adv_frame.setVisible(checked)

    def _button_toggle_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_SECONDARY};
                font-weight: 600;
                font-size: 11px;
                padding: 6px;
            }}
            QPushButton:hover {{
                border-color: {Theme.BORDER_FOCUS};
            }}
            QPushButton:checked {{
                background-color: {self.accent};
                border-color: {self.accent};
                color: #FFFFFF;
            }}
        """

    def _on_parameter_changed(self, name: str, val: int, display_str: str):
        if name == "preamp_sw":
            self.btn_power.setChecked(val > 0)
        elif name == "preamp_type":
            idx = self.combo_model.findData(val)
            if idx >= 0 and self.combo_model.currentIndex() != idx:
                self.combo_model.setCurrentIndex(idx)
        elif name == "preamp_gain":
            self.knob_gain.set_value_silent(val)
        elif name == "preamp_bass":
            self.knob_bass.set_value_silent(val)
        elif name == "preamp_middle":
            self.knob_mid.set_value_silent(val)
        elif name == "preamp_treble":
            self.knob_treble.set_value_silent(val)
        elif name == "preamp_presence":
            self.knob_presence.set_value_silent(val)
        elif name == "preamp_volume":
            self.knob_vol.set_value_silent(val)
        elif name == "preamp_bright":
            self.btn_bright.setChecked(val > 0)
        elif name == "preamp_solo_sw":
            self.btn_solo.setChecked(val > 0)
        elif name == "preamp_solo_level":
            self.knob_solo_lvl.set_value_silent(val)

    def sync_from_model(self):
        self.btn_power.setChecked(self.model.get_param("preamp_sw") > 0)
        self.knob_gain.set_value_silent(self.model.get_param("preamp_gain"))
        self.knob_bass.set_value_silent(self.model.get_param("preamp_bass"))
        self.knob_mid.set_value_silent(self.model.get_param("preamp_middle"))
        self.knob_treble.set_value_silent(self.model.get_param("preamp_treble"))
        self.knob_presence.set_value_silent(self.model.get_param("preamp_presence"))
        self.knob_vol.set_value_silent(self.model.get_param("preamp_volume"))
        self.btn_bright.setChecked(self.model.get_param("preamp_bright") > 0)
        self.btn_solo.setChecked(self.model.get_param("preamp_solo_sw") > 0)
        self.knob_solo_lvl.set_value_silent(self.model.get_param("preamp_solo_level"))

        m_id = self.model.get_param("preamp_type")
        idx = self.combo_model.findData(m_id)
        if idx >= 0:
            self.combo_model.setCurrentIndex(idx)
