"""
Noise Suppressor & Master Routing Inspector Panel.
Controls Boss Noise Suppressor parameters, Foot/Master Volume,
and Katana MkII internal effect chain routing topology.
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
from katana_modern.core.amp_catalog import CHAIN_ROUTES


class NsMasterPanel(QWidget):
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.accent_ns = Theme.COLOR_NS
        self.accent_master = Theme.COLOR_MASTER

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # 1. Noise Suppressor Section
        ns_frame = QFrame()
        ns_frame.setObjectName("CardFrame")
        ns_layout = QVBoxLayout(ns_frame)
        ns_layout.setContentsMargins(16, 14, 16, 14)
        ns_layout.setSpacing(12)

        ns_header = QHBoxLayout()
        lbl_ns = QLabel("INTELLIGENT NOISE SUPPRESSOR (NS)")
        lbl_ns.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_ns.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        ns_header.addWidget(lbl_ns)
        ns_header.addStretch()

        self.btn_ns_power = QPushButton("NS ON")
        self.btn_ns_power.setCheckable(True)
        self.btn_ns_power.setFixedHeight(30)
        self.btn_ns_power.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {self.accent_ns};
                border-radius: 6px;
                color: {self.accent_ns};
                font-weight: bold;
                padding: 4px 14px;
            }}
            QPushButton:checked {{
                background-color: {self.accent_ns};
                color: #000000;
            }}
        """)
        self.btn_ns_power.toggled.connect(lambda chk: self.model.set_param("ns_sw", 1 if chk else 0))
        ns_header.addWidget(self.btn_ns_power)
        ns_layout.addLayout(ns_header)

        ns_knobs = QHBoxLayout()
        self.knob_threshold = ModernKnob("Threshold", 0, 100, 45, "", self.accent_ns, diameter=68)
        self.knob_threshold.value_changed.connect(lambda v: self.model.set_param("ns_threshold", v))
        ns_knobs.addWidget(self.knob_threshold)

        self.knob_release = ModernKnob("Release", 0, 100, 50, "", self.accent_ns, diameter=68)
        self.knob_release.value_changed.connect(lambda v: self.model.set_param("ns_release", v))
        ns_knobs.addWidget(self.knob_release)
        ns_knobs.addStretch()
        ns_layout.addLayout(ns_knobs)

        layout.addWidget(ns_frame)

        # 2. Master & Chain Routing Section
        master_frame = QFrame()
        master_frame.setObjectName("CardFrame")
        master_layout = QVBoxLayout(master_frame)
        master_layout.setContentsMargins(16, 14, 16, 14)
        master_layout.setSpacing(12)

        master_header = QHBoxLayout()
        lbl_master = QLabel("SIGNAL CHAIN ROUTING & MASTER")
        lbl_master.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_master.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        master_header.addWidget(lbl_master)
        master_header.addStretch()
        master_layout.addLayout(master_header)

        chain_row = QHBoxLayout()
        lbl_chain = QLabel("CHAIN ROUTING:")
        lbl_chain.setFont(QFont("Inter", 10, QFont.Weight.DemiBold))
        lbl_chain.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        chain_row.addWidget(lbl_chain)

        self.combo_chain = QComboBox()
        self.combo_chain.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.combo_chain.setMinimumWidth(380)
        for c in CHAIN_ROUTES:
            self.combo_chain.addItem(f"{c['name']}  ({c['summary']})", int(c['id']))
        self.combo_chain.currentIndexChanged.connect(self._on_chain_changed)
        chain_row.addWidget(self.combo_chain)

        btn_open_routing = QPushButton("🔀 Personalizza Catena...")
        btn_open_routing.setFixedHeight(30)
        btn_open_routing.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        btn_open_routing.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.COLOR_AMP};
                border-radius: 4px;
                color: {Theme.COLOR_AMP};
                padding: 3px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        btn_open_routing.clicked.connect(self._open_routing_dialog)
        chain_row.addWidget(btn_open_routing)
        chain_row.addStretch()
        master_layout.addLayout(chain_row)

        knobs_row = QHBoxLayout()
        self.knob_volume = ModernKnob("Foot / Patch Vol", 0, 100, 100, "%", self.accent_master, diameter=72)
        self.knob_volume.value_changed.connect(lambda v: self.model.set_param("foot_volume", v))
        knobs_row.addWidget(self.knob_volume)
        knobs_row.addStretch()
        master_layout.addLayout(knobs_row)

        layout.addWidget(master_frame)
        layout.addStretch()

        self.model.parameter_changed.connect(self._on_parameter_changed)
        self.model.patch_loaded.connect(self.sync_from_model)
        self.sync_from_model()

    def _open_routing_dialog(self):
        from katana_modern.ui.dialogs.chain_routing_dialog import SignalChainRoutingDialog
        dlg = SignalChainRoutingDialog(self.model, self)
        dlg.exec()

    def _on_chain_changed(self, index: int):
        if index >= 0:
            cid = self.combo_chain.currentData()
            self.model.set_param("chain_pattern", cid)
            self.model.set_param("chain_position", cid)

    def _on_parameter_changed(self, name: str, val: int, display_str: str):
        if name == "ns_sw":
            self.btn_ns_power.setChecked(val > 0)
        elif name == "ns_threshold":
            self.knob_threshold.set_value_silent(val)
        elif name == "ns_release":
            self.knob_release.set_value_silent(val)
        elif name == "foot_volume":
            self.knob_volume.set_value_silent(val)
        elif name in ["chain_pattern", "chain_position"]:
            idx = self.combo_chain.findData(val)
            if idx >= 0 and self.combo_chain.currentIndex() != idx:
                self.combo_chain.blockSignals(True)
                self.combo_chain.setCurrentIndex(idx)
                self.combo_chain.blockSignals(False)

    def sync_from_model(self):
        self.btn_ns_power.setChecked(self.model.get_param("ns_sw") > 0)
        self.knob_threshold.set_value_silent(self.model.get_param("ns_threshold"))
        self.knob_release.set_value_silent(self.model.get_param("ns_release"))
        self.knob_volume.set_value_silent(self.model.get_param("foot_volume"))

        cid = self.model.get_param("chain_pattern", self.model.get_param("chain_position", 0))
        idx = self.combo_chain.findData(cid)
        if idx >= 0:
            self.combo_chain.blockSignals(True)
            self.combo_chain.setCurrentIndex(idx)
            self.combo_chain.blockSignals(False)
