"""
Equalizer Module Inspector Panel.
Features 10-band Graphic EQ with interactive vertical faders (31Hz to 16kHz),
Parametric EQ controls, and overall EQ level trimming.
"""

from typing import Optional, Dict
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSlider, QStackedWidget
)
from PyQt6.QtGui import QFont

from katana_modern.ui.theme import Theme
from katana_modern.ui.components.rotary_knob import ModernKnob
from katana_modern.core.patch_model import KatanaPatchModel


class BandFader(QWidget):
    """Vertical EQ Slider with frequency label and dB readout."""
    def __init__(self, freq_label: str, param_name: str, model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.freq_label = freq_label
        self.param_name = param_name
        self.model = model
        self.setFixedWidth(56)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 4, 2, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # dB readout
        self.lbl_db = QLabel("0 dB")
        self.lbl_db.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.lbl_db.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_db.setStyleSheet(f"color: {Theme.COLOR_EQ};")
        layout.addWidget(self.lbl_db)

        # Vertical Slider (0 to 48, center 24 = 0 dB)
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setRange(0, 48)
        self.slider.setValue(24)
        self.slider.setFixedHeight(120)
        self.slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                width: 6px;
                background: {Theme.BG_INPUT};
                border-radius: 3px;
            }}
            QSlider::sub-page:vertical {{
                background: {Theme.BG_INPUT};
                border-radius: 3px;
            }}
            QSlider::add-page:vertical {{
                background: {Theme.COLOR_EQ};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {Theme.TEXT_PRIMARY};
                height: 14px;
                margin-left: -4px;
                margin-right: -4px;
                border-radius: 7px;
            }}
            QSlider::handle:vertical:hover {{
                background: #FFFFFF;
            }}
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider, 0, Qt.AlignmentFlag.AlignCenter)

        # Frequency Label
        lbl_freq = QLabel(self.freq_label)
        lbl_freq.setFont(QFont("Inter", 8, QFont.Weight.DemiBold))
        lbl_freq.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        lbl_freq.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_freq)

    def _on_slider_changed(self, val: int):
        db_val = (val - 24) * 0.5
        sign = "+" if db_val > 0 else ""
        self.lbl_db.setText(f"{sign}{db_val:.1f} dB")
        self.model.set_param(self.param_name, val)

    def set_value_silent(self, val: int):
        self.slider.blockSignals(True)
        self.slider.setValue(val)
        self.slider.blockSignals(False)
        db_val = (val - 24) * 0.5
        sign = "+" if db_val > 0 else ""
        self.lbl_db.setText(f"{sign}{db_val:.1f} dB")


class EqPanel(QWidget):
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.accent = Theme.COLOR_EQ

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        lbl = QLabel("EQUALIZER MODE:")
        lbl.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        header_row.addWidget(lbl)

        self.btn_mode_geq = QPushButton("10-BAND GRAPHIC")
        self.btn_mode_geq.setCheckable(True)
        self.btn_mode_geq.setChecked(True)
        self.btn_mode_geq.setFixedHeight(32)
        self.btn_mode_geq.clicked.connect(lambda: self._set_mode(1))
        header_row.addWidget(self.btn_mode_geq)

        self.btn_mode_peq = QPushButton("PARAMETRIC")
        self.btn_mode_peq.setCheckable(True)
        self.btn_mode_peq.setFixedHeight(32)
        self.btn_mode_peq.clicked.connect(lambda: self._set_mode(0))
        header_row.addWidget(self.btn_mode_peq)

        header_row.addStretch()

        self.btn_power = QPushButton("EQ ON")
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
                color: #000000;
            }}
        """)
        self.btn_power.toggled.connect(lambda chk: self.model.set_param("eq1_sw", 1 if chk else 0))
        header_row.addWidget(self.btn_power)

        layout.addLayout(header_row)

        # Stacked Views: Graphic vs Parametric
        self.stack = QStackedWidget()

        # Page 0: Graphic EQ
        geq_frame = QFrame()
        geq_frame.setObjectName("CardFrame")
        geq_layout = QHBoxLayout(geq_frame)
        geq_layout.setContentsMargins(12, 10, 12, 10)
        geq_layout.setSpacing(4)

        self.faders: Dict[str, BandFader] = {}
        bands = [
            ("31 Hz", "geq_31"), ("62 Hz", "geq_62"), ("125 Hz", "geq_125"),
            ("250 Hz", "geq_250"), ("500 Hz", "geq_500"), ("1 kHz", "geq_1k"),
            ("2 kHz", "geq_2k"), ("4 kHz", "geq_4k"), ("8 kHz", "geq_8k"),
            ("16 kHz", "geq_16k")
        ]
        for freq_lbl, pname in bands:
            fader = BandFader(freq_lbl, pname, self.model)
            geq_layout.addWidget(fader)
            self.faders[pname] = fader

        geq_layout.addSpacing(16)
        self.knob_geq_lvl = ModernKnob("EQ Level", 0, 40, 20, "dB", self.accent, diameter=60)
        self.knob_geq_lvl.value_changed.connect(lambda v: self.model.set_param("eq1_level", v))
        geq_layout.addWidget(self.knob_geq_lvl)

        self.stack.addWidget(geq_frame)

        # Page 1: Parametric EQ
        peq_frame = QFrame()
        peq_frame.setObjectName("CardFrame")
        peq_layout = QHBoxLayout(peq_frame)
        peq_layout.setContentsMargins(16, 16, 16, 16)
        peq_layout.setSpacing(16)

        self.knob_low_gain = ModernKnob("Low Gain", 0, 40, 20, "dB", self.accent, diameter=64)
        self.knob_low_gain.value_changed.connect(lambda v: self.model.set_param("eq1_low_gain", v))
        peq_layout.addWidget(self.knob_low_gain)

        self.knob_mid_gain = ModernKnob("Mid Gain", 0, 40, 20, "dB", self.accent, diameter=64)
        self.knob_mid_gain.value_changed.connect(lambda v: self.model.set_param("eq1_mid_gain", v))
        peq_layout.addWidget(self.knob_mid_gain)

        self.knob_hi_gain = ModernKnob("High Gain", 0, 40, 20, "dB", self.accent, diameter=64)
        self.knob_hi_gain.value_changed.connect(lambda v: self.model.set_param("eq1_high_gain", v))
        peq_layout.addWidget(self.knob_hi_gain)

        self.knob_peq_lvl = ModernKnob("Overall Level", 0, 40, 20, "dB", self.accent, diameter=64)
        self.knob_peq_lvl.value_changed.connect(lambda v: self.model.set_param("eq1_level", v))
        peq_layout.addWidget(self.knob_peq_lvl)

        peq_layout.addStretch()
        self.stack.addWidget(peq_frame)

        layout.addWidget(self.stack)
        layout.addStretch()

        self.model.parameter_changed.connect(self._on_parameter_changed)
        self.model.patch_loaded.connect(self.sync_from_model)
        self.sync_from_model()

    def _set_mode(self, mode: int):
        # mode: 1 = Graphic, 0 = Parametric
        self.model.set_param("eq1_type", mode)
        self.btn_mode_geq.setChecked(mode == 1)
        self.btn_mode_peq.setChecked(mode == 0)
        self.stack.setCurrentIndex(0 if mode == 1 else 1)

    def _on_parameter_changed(self, name: str, val: int, display_str: str):
        if name == "eq1_sw":
            self.btn_power.setChecked(val > 0)
        elif name == "eq1_type":
            self._set_mode(val)
        elif name in self.faders:
            self.faders[name].set_value_silent(val)
        elif name == "eq1_level":
            self.knob_geq_lvl.set_value_silent(val)
            self.knob_peq_lvl.set_value_silent(val)
        elif name == "eq1_low_gain":
            self.knob_low_gain.set_value_silent(val)
        elif name == "eq1_mid_gain":
            self.knob_mid_gain.set_value_silent(val)
        elif name == "eq1_high_gain":
            self.knob_hi_gain.set_value_silent(val)

    def sync_from_model(self):
        self.btn_power.setChecked(self.model.get_param("eq1_sw") > 0)
        eq_type = self.model.get_param("eq1_type")
        self._set_mode(eq_type)

        for pname, fader in self.faders.items():
            fader.set_value_silent(self.model.get_param(pname))

        lvl = self.model.get_param("eq1_level")
        self.knob_geq_lvl.set_value_silent(lvl)
        self.knob_peq_lvl.set_value_silent(lvl)
        self.knob_low_gain.set_value_silent(self.model.get_param("eq1_low_gain"))
        self.knob_mid_gain.set_value_silent(self.model.get_param("eq1_mid_gain"))
        self.knob_hi_gain.set_value_silent(self.model.get_param("eq1_high_gain"))
