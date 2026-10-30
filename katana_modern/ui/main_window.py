"""
Main Window for the Katana Modern Editor.
Integrates Header, Interactive Signal Chain, Modular Detail Inspector,
Collapsible Preset Librarian, and Permanent Lower Master & Cabinet Tone Dock
into a cohesive modern DAW experience (Neural DSP / Helix Native Style).
"""

import os
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QSplitter
)
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon

from katana_modern.ui.theme import Theme, DARK_STYLESHEET
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.midi_backend import KatanaMidiBackend

from katana_modern.ui.header_bar import HeaderBar
from katana_modern.ui.components.signal_chain_bar import SignalChainBar
from katana_modern.ui.components.master_cab_dock import MasterCabDock
from katana_modern.ui.sidebar.preset_librarian import PresetLibrarian

from katana_modern.ui.panels.amp_panel import AmpPanel
from katana_modern.ui.panels.booster_panel import BoosterPanel
from katana_modern.ui.panels.mod_panel import ModPanel
from katana_modern.ui.panels.fx_panel import FxPanel
from katana_modern.ui.panels.delay_panel import DelayPanel
from katana_modern.ui.panels.reverb_panel import ReverbPanel
from katana_modern.ui.panels.eq_panel import EqPanel
from katana_modern.ui.panels.ns_master_panel import NsMasterPanel


class KatanaMainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Katana Forge — MkII Tone Studio")
        self.resize(1260, 820)
        self.setMinimumSize(1024, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "app_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 1. Initialize Core Models & Hardware Backend
        self.midi_backend = KatanaMidiBackend(self)
        self.patch_model = KatanaPatchModel(self.midi_backend, self)

        # 2. Setup Central Widget and Main Layout
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        # 3. Header Bar
        self.header_bar = HeaderBar(self.patch_model, self.midi_backend, self)
        self.header_bar.toggle_sidebar_requested.connect(self._toggle_sidebar)
        root_layout.addWidget(self.header_bar)

        # 4. Interactive Signal Chain Bar
        self.chain_bar = SignalChainBar(self.patch_model, self)
        self.chain_bar.module_selected.connect(self._on_module_selected)
        root_layout.addWidget(self.chain_bar)

        # 5. Middle Splitter: [Sidebar (Librarian)] | [Center Container]
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(4)

        # Sidebar Librarian
        self.librarian = PresetLibrarian(self.patch_model, self.midi_backend, parent=self)
        self.splitter.addWidget(self.librarian)

        # Center Container (Top: Active Module Stack, Bottom: Permanent Master & Cabinet Dock)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)

        # Central Modular Container (Stacked Widget for detail panels)
        self.stack = QStackedWidget()
        self.stack.setObjectName("PanelFrame")

        # Instantiate Detail Panels
        self.panel_amp = AmpPanel(self.patch_model, self)
        self.panel_booster = BoosterPanel(self.patch_model, self)
        self.panel_mod = ModPanel(self.patch_model, self)
        self.panel_fx = FxPanel(self.patch_model, self)
        self.panel_delay = DelayPanel(self.patch_model, self)
        self.panel_reverb = ReverbPanel(self.patch_model, self)
        self.panel_eq = EqPanel(self.patch_model, self)
        self.panel_ns_master = NsMasterPanel(self.patch_model, self)

        # Add each panel once to the stack
        idx_amp = self.stack.addWidget(self.panel_amp)
        idx_booster = self.stack.addWidget(self.panel_booster)
        idx_mod = self.stack.addWidget(self.panel_mod)
        idx_fx = self.stack.addWidget(self.panel_fx)
        idx_delay = self.stack.addWidget(self.panel_delay)
        idx_reverb = self.stack.addWidget(self.panel_reverb)
        idx_eq = self.stack.addWidget(self.panel_eq)
        idx_ns_master = self.stack.addWidget(self.panel_ns_master)

        self.panel_indices = {
            "in": idx_amp,
            "amp": idx_amp,
            "booster": idx_booster,
            "mod": idx_mod,
            "fx": idx_fx,
            "delay": idx_delay,
            "reverb": idx_reverb,
            "eq": idx_eq,
            "ns": idx_ns_master,
            "master": idx_ns_master,
        }

        # Show Amp panel by default
        self.stack.setCurrentIndex(idx_amp)
        center_layout.addWidget(self.stack, 1)

        # Permanent Lower Master & Cabinet Tone Dock
        self.master_cab_dock = MasterCabDock(self.patch_model, self.midi_backend, self)
        center_layout.addWidget(self.master_cab_dock)

        self.splitter.addWidget(center_widget)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        root_layout.addWidget(self.splitter, 1)

        # 6. Global Shortcuts
        QShortcut(QKeySequence.StandardKey.Undo, self, self.patch_model.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self.patch_model.redo)
        QShortcut(QKeySequence("Ctrl+B"), self, self._toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+N"), self, self.header_bar._open_new_profile_dialog)
        QShortcut(QKeySequence("Ctrl+R"), self, self.chain_bar._open_routing_dialog)

        # Auto-connect to physical Katana if available
        self._auto_connect_katana()

    def _auto_connect_katana(self):
        """Attempts automatic connection to connected Boss Katana on startup."""
        devs = self.midi_backend.scan_devices()
        for name, port in devs:
            if "KATANA" in name.upper() and port != "virtual":
                self.midi_backend.connect_device(port, name)
                break

    def _toggle_sidebar(self):
        self.librarian.setVisible(not self.librarian.isVisible())

    def _on_module_selected(self, module_id: str):
        if module_id in self.panel_indices:
            idx = self.panel_indices[module_id]
            self.stack.setCurrentIndex(idx)

    def closeEvent(self, event):
        self.midi_backend.disconnect_device()
        super().closeEvent(event)
