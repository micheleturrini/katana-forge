"""
Lower-Right & Bottom Master Dock for Katana Modern FX FloorBoard.
Houses:
1. Cabinet & Speaker Simulation, Resonance & Line Out Air Feel.
2. Real-Time Dynamic Frequency Response Curve Visualizer.
3. Master Output Section, Quick Solo, and Preset Notes/Memo.
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QButtonGroup, QTextEdit, QSizePolicy
)
from PyQt6.QtGui import QFont

from katana_modern.ui.theme import Theme
from katana_modern.ui.components.rotary_knob import ModernKnob
from katana_modern.ui.components.tone_analyzer import DynamicToneAnalyzer
from katana_modern.core.patch_model import KatanaPatchModel


class MasterCabDock(QFrame):
    """
    Permanent Lower Studio Dock occupying the bottom/bottom-right of the interface.
    """
    def __init__(self, patch_model: KatanaPatchModel, midi_backend=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.midi_backend = midi_backend

        self.setObjectName("PanelFrame")
        self.setFixedHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 8)
        root_layout.setSpacing(10)

        # =============================================================
        # 1. LEFT CARD: Cabinet, Resonance, Line Out & Contour
        # =============================================================
        cab_card = QFrame()
        cab_card.setObjectName("CardFrame")
        cab_card.setFixedWidth(290)
        cab_layout = QVBoxLayout(cab_card)
        cab_layout.setContentsMargins(10, 8, 10, 8)
        cab_layout.setSpacing(6)

        # Title
        lbl_cab = QLabel("CABINET & LINE OUT AIR")
        lbl_cab.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_cab.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        cab_layout.addWidget(lbl_cab)

        # Cabinet Model Selector
        self.combo_cab = QComboBox()
        self.combo_cab.setFont(QFont("Inter", 9))
        self.combo_cab.setFixedHeight(26)
        self.combo_cab.addItem("1x12 Katana Open Back", 0)
        self.combo_cab.addItem("2x12 Katana Closed Back", 1)
        self.combo_cab.addItem("4x12 British 1960 Stack", 2)
        self.combo_cab.addItem("4x12 American V30 Cab", 3)
        self.combo_cab.currentIndexChanged.connect(
            lambda idx: self.model.set_param("cab_type", self.combo_cab.currentData())
        )
        cab_layout.addWidget(self.combo_cab)

        # Cab Resonance Selector (Vintage / Modern / Deep)
        row_res = QHBoxLayout()
        row_res.setSpacing(4)
        lbl_res = QLabel("Resonance:")
        lbl_res.setFont(QFont("Inter", 8))
        lbl_res.setStyleSheet(f"color: {Theme.TEXT_MUTED}; min-width: 65px;")
        row_res.addWidget(lbl_res)

        self.btn_res_group = QButtonGroup(self)
        self.btn_res_group.setExclusive(True)
        res_names = [("Vintage", 0), ("Modern", 1), ("Deep", 2)]
        self.res_buttons = []
        for name, val in res_names:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            btn.setStyleSheet(self._segmented_btn_style())
            btn.clicked.connect(lambda checked, v=val: self.model.set_param("cab_resonance", v))
            self.btn_res_group.addButton(btn, val)
            row_res.addWidget(btn)
            self.res_buttons.append(btn)
        cab_layout.addLayout(row_res)

        # Line Out Air Feel (Rec / Live / Blend)
        row_air = QHBoxLayout()
        row_air.setSpacing(4)
        lbl_air = QLabel("Air Feel:")
        lbl_air.setFont(QFont("Inter", 8))
        lbl_air.setStyleSheet(f"color: {Theme.TEXT_MUTED}; min-width: 65px;")
        row_air.addWidget(lbl_air)

        self.btn_air_group = QButtonGroup(self)
        self.btn_air_group.setExclusive(True)
        air_names = [("Rec", 0), ("Live", 1), ("Blend", 2)]
        self.air_buttons = []
        for name, val in air_names:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            btn.setStyleSheet(self._segmented_btn_style())
            btn.clicked.connect(lambda checked, v=val: self.model.set_param("line_out_air_feel", v))
            self.btn_air_group.addButton(btn, val)
            row_air.addWidget(btn)
            self.air_buttons.append(btn)
        cab_layout.addLayout(row_air)

        # Contour (Off / Type 1 / Type 2 / Type 3)
        row_con = QHBoxLayout()
        row_con.setSpacing(4)
        lbl_con = QLabel("Contour:")
        lbl_con.setFont(QFont("Inter", 8))
        lbl_con.setStyleSheet(f"color: {Theme.TEXT_MUTED}; min-width: 65px;")
        row_con.addWidget(lbl_con)

        self.btn_con_group = QButtonGroup(self)
        self.btn_con_group.setExclusive(True)
        con_names = [("Off", -1), ("T1", 0), ("T2", 1), ("T3", 2)]
        self.con_buttons = []
        for name, val in con_names:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            btn.setStyleSheet(self._segmented_btn_style())
            btn.clicked.connect(lambda checked, v=val: self._on_contour_clicked(v))
            self.btn_con_group.addButton(btn)
            row_con.addWidget(btn)
            self.con_buttons.append(btn)
        cab_layout.addLayout(row_con)

        root_layout.addWidget(cab_card)

        # =============================================================
        # 2. CENTER: Real-Time Dynamic Frequency Analyzer Graph
        # =============================================================
        self.analyzer = DynamicToneAnalyzer(self.model, self)
        root_layout.addWidget(self.analyzer, 1)

        # =============================================================
        # 3. RIGHT CARD: Master Output, Macro Knobs & Preset Notes
        # =============================================================
        master_card = QFrame()
        master_card.setObjectName("CardFrame")
        master_card.setFixedWidth(360)
        master_layout = QVBoxLayout(master_card)
        master_layout.setContentsMargins(10, 8, 10, 8)
        master_layout.setSpacing(6)

        # Header Title Row
        row_mtitle = QHBoxLayout()
        lbl_master = QLabel("MASTER & PATCH NOTES")
        lbl_master.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_master.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        row_mtitle.addWidget(lbl_master)
        row_mtitle.addStretch()

        self.lbl_safe_status = QLabel("🛡️ Anti-Blast: ON")
        self.lbl_safe_status.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.lbl_safe_status.setStyleSheet("""
            background-color: #12281B;
            border: 1px solid #30D158;
            border-radius: 4px;
            color: #30D158;
            padding: 2px 6px;
        """)
        self.lbl_safe_status.setToolTip("Safe Audition Guard is ACTIVE: anti-blast volume leveling enabled.")
        row_mtitle.addWidget(self.lbl_safe_status)
        master_layout.addLayout(row_mtitle)

        # Dials Row
        dials_row = QHBoxLayout()
        dials_row.setSpacing(8)

        self.knob_master = ModernKnob("Master", 0, 100, 50, "", Theme.COLOR_AMP, diameter=52)
        self.knob_master.value_changed.connect(lambda v: self.model.set_param("master_level", v))
        dials_row.addWidget(self.knob_master)

        self.knob_presence = ModernKnob("Presence", 0, 100, 50, "", Theme.COLOR_AMP, diameter=52)
        self.knob_presence.value_changed.connect(lambda v: self.model.set_param("preamp_presence", v))
        dials_row.addWidget(self.knob_presence)

        # Solo switch & level
        solo_vbox = QVBoxLayout()
        solo_vbox.setSpacing(4)
        solo_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_solo = QPushButton("SOLO")
        self.btn_solo.setCheckable(True)
        self.btn_solo.setFixedSize(54, 26)
        self.btn_solo.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_solo.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_SECONDARY};
                padding: 2px;
            }}
            QPushButton:hover {{
                border-color: {Theme.BORDER_FOCUS};
            }}
            QPushButton:checked {{
                background-color: #FF3B30;
                border-color: #FF3B30;
                color: #FFFFFF;
            }}
        """)
        self.btn_solo.toggled.connect(lambda chk: self.model.set_param("preamp_solo_sw", 1 if chk else 0))
        solo_vbox.addWidget(self.btn_solo)

        self.knob_solo = ModernKnob("Solo Lvl", 0, 100, 50, "", "#FF3B30", diameter=42)
        self.knob_solo.value_changed.connect(lambda v: self.model.set_param("preamp_solo_level", v))
        solo_vbox.addWidget(self.knob_solo)
        dials_row.addLayout(solo_vbox)

        # Patch Notes Text Box
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Preset notes & memo...")
        self.txt_notes.setFont(QFont("Inter", 8))
        self.txt_notes.setFixedWidth(110)
        self.txt_notes.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                padding: 4px;
            }}
        """)
        self.txt_notes.textChanged.connect(self._on_notes_changed)
        dials_row.addWidget(self.txt_notes)

        master_layout.addLayout(dials_row)
        root_layout.addWidget(master_card)

        # Connect to model updates
        self.model.parameter_changed.connect(self._on_param_changed)
        self.model.patch_loaded.connect(self.sync_from_model)
        self.model.safe_guard_status_changed.connect(self._on_safe_guard_changed)
        self._on_safe_guard_changed(self.model.safe_audition_enabled)
        self.sync_from_model()

    def _on_safe_guard_changed(self, enabled: bool):
        if enabled:
            self.lbl_safe_status.setText("🛡️ Anti-Blast: ON")
            self.lbl_safe_status.setStyleSheet("""
                background-color: #12281B;
                border: 1px solid #30D158;
                border-radius: 4px;
                color: #30D158;
                padding: 2px 6px;
            """)
            self.lbl_safe_status.setToolTip("Safe Audition Guard is ACTIVE: anti-blast volume leveling enabled.")
        else:
            self.lbl_safe_status.setText("⚠️ Guard: OFF")
            self.lbl_safe_status.setStyleSheet("""
                background-color: #301616;
                border: 1px solid #FF453A;
                border-radius: 4px;
                color: #FF453A;
                padding: 2px 6px;
            """)
            self.lbl_safe_status.setToolTip("WARNING: Safe Audition Guard is OFF.")

    def _on_contour_clicked(self, val: int):
        if val == -1:
            self.model.set_param("contour_sw", 0)
        else:
            self.model.set_param("contour_sw", 1)
            self.model.set_param("contour_type", val)

    def _on_notes_changed(self):
        self.model.patch_memo = self.txt_notes.toPlainText()

    def _segmented_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 3px;
                color: {Theme.TEXT_SECONDARY};
                padding: 1px 4px;
            }}
            QPushButton:hover {{
                border-color: {Theme.BORDER_FOCUS};
            }}
            QPushButton:checked {{
                background-color: {Theme.COLOR_AMP};
                border-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """

    def _on_param_changed(self, name: str, val: int, display: str):
        if name == "cab_resonance":
            for idx, btn in enumerate(self.res_buttons):
                btn.setChecked(idx == val)
        elif name == "line_out_air_feel":
            for idx, btn in enumerate(self.air_buttons):
                btn.setChecked(idx == val)
        elif name == "contour_sw" or name == "contour_type":
            c_sw = self.model.get_param("contour_sw")
            c_type = self.model.get_param("contour_type")
            if not c_sw:
                self.con_buttons[0].setChecked(True)
            else:
                target = c_type + 1
                if 0 <= target < len(self.con_buttons):
                    self.con_buttons[target].setChecked(True)
        elif name == "master_level":
            self.knob_master.set_value_silent(val)
        elif name == "preamp_presence":
            self.knob_presence.set_value_silent(val)
        elif name == "preamp_solo_sw":
            self.btn_solo.setChecked(val > 0)
        elif name == "preamp_solo_level":
            self.knob_solo.set_value_silent(val)
        elif name == "cab_type":
            idx = self.combo_cab.findData(val)
            if idx >= 0:
                self.combo_cab.setCurrentIndex(idx)

    def sync_from_model(self):
        res = self.model.get_param("cab_resonance", 0)
        for idx, btn in enumerate(self.res_buttons):
            btn.setChecked(idx == res)

        air = self.model.get_param("line_out_air_feel", 0)
        for idx, btn in enumerate(self.air_buttons):
            btn.setChecked(idx == air)

        c_sw = self.model.get_param("contour_sw", 0)
        c_type = self.model.get_param("contour_type", 0)
        if not c_sw:
            self.con_buttons[0].setChecked(True)
        else:
            target = c_type + 1
            if 0 <= target < len(self.con_buttons):
                self.con_buttons[target].setChecked(True)

        self.knob_master.set_value_silent(self.model.get_param("master_level", 50))
        self.knob_presence.set_value_silent(self.model.get_param("preamp_presence", 50))
        self.btn_solo.setChecked(self.model.get_param("preamp_solo_sw", 0) > 0)
        self.knob_solo.set_value_silent(self.model.get_param("preamp_solo_level", 50))

        # Notes
        self.txt_notes.blockSignals(True)
        self.txt_notes.setPlainText(getattr(self.model, "patch_memo", ""))
        self.txt_notes.blockSignals(False)
