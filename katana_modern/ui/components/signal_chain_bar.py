"""
Horizontal Interactive Signal Chain Bar (Neural DSP / Helix Native Style).
Displays audio routing blocks with one-click bypass toggle, model subtitles,
and active block selection for the detail inspector.
"""

from typing import Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QVBoxLayout
)
from PyQt6.QtGui import QFont, QCursor

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.amp_catalog import (
    PREAMP_MODELS, BOOSTER_MODELS, MOD_MODELS, FX_MODELS, DELAY_MODELS, REVERB_MODELS
)


class ChainBlock(QFrame):
    """A single module block inside the signal chain."""
    clicked = pyqtSignal(str)           # module_id
    toggled = pyqtSignal(str, bool)     # module_id, is_active

    def __init__(
        self,
        module_id: str,
        title: str,
        accent_color: str,
        can_bypass: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.module_id = module_id
        self.title = title
        self.accent_color = accent_color
        self.can_bypass = can_bypass
        self._is_active = True
        self._is_selected = False
        self._subtitle = ""

        self.setFixedWidth(96)
        self.setFixedHeight(68)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # Top row: Title + Power Switch
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(4)

        self.lbl_title = QLabel(self.title)
        self.lbl_title.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()

        if self.can_bypass:
            self.btn_power = QPushButton("●")
            self.btn_power.setFixedSize(18, 18)
            self.btn_power.setFont(QFont("Inter", 10))
            self.btn_power.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.btn_power.clicked.connect(self._on_power_clicked)
            top_row.addWidget(self.btn_power)
        else:
            self.btn_power = None

        layout.addLayout(top_row)

        # Bottom row: Algorithm / Model Subtitle
        self.lbl_sub = QLabel("")
        self.lbl_sub.setFont(QFont("Inter", 8))
        self.lbl_sub.setWordWrap(False)
        layout.addWidget(self.lbl_sub)

        self._update_appearance()

    def set_active(self, active: bool):
        self._is_active = active
        self._update_appearance()

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._update_appearance()

    def set_subtitle(self, text: str):
        # Truncate clean
        if len(text) > 14:
            text = text[:13] + "…"
        self._subtitle = text
        self.lbl_sub.setText(text)

    def _on_power_clicked(self):
        new_state = not self._is_active
        self.set_active(new_state)
        self.toggled.emit(self.module_id, new_state)

    def mousePressEvent(self, event):
        self.clicked.emit(self.module_id)
        super().mousePressEvent(event)

    def _update_appearance(self):
        border_color = self.accent_color if self._is_selected else Theme.BORDER_SUBTLE
        border_width = "2px" if self._is_selected else "1px"
        bg = Theme.BG_CARD_ACTIVE if self._is_selected else Theme.BG_CARD

        if not self._is_active and self.can_bypass:
            title_color = Theme.TEXT_MUTED
            sub_color = Theme.TEXT_DIM
            power_style = f"background: transparent; color: {Theme.TEXT_DIM}; border: none;"
        else:
            title_color = Theme.TEXT_PRIMARY
            sub_color = self.accent_color
            power_style = f"background: transparent; color: {self.accent_color}; border: none; font-weight: bold;"

        self.setStyleSheet(f"""
            ChainBlock {{
                background-color: {bg};
                border: {border_width} solid {border_color};
                border-radius: 6px;
            }}
            ChainBlock:hover {{
                border-color: {self.accent_color};
            }}
        """)
        self.lbl_title.setStyleSheet(f"color: {title_color};")
        self.lbl_sub.setStyleSheet(f"color: {sub_color};")
        if self.btn_power:
            self.btn_power.setStyleSheet(power_style)


class SignalChainBar(QFrame):
    """
    Complete horizontal audio signal chain container with dynamic routing rearrangement.
    """
    module_selected = pyqtSignal(str)  # module_id

    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.setObjectName("PanelFrame")
        self.setFixedHeight(84)

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        # Dynamic inner container for audio blocks
        self.chain_container = QWidget()
        self.chain_layout = QHBoxLayout(self.chain_container)
        self.chain_layout.setContentsMargins(0, 0, 0, 0)
        self.chain_layout.setSpacing(4)
        root_layout.addWidget(self.chain_container, 1)

        # Create all module blocks once
        self.blocks: Dict[str, ChainBlock] = {
            "in": ChainBlock("in", "INPUT", Theme.TEXT_MUTED, can_bypass=False),
            "booster": ChainBlock("booster", "BOOST", Theme.COLOR_BOOSTER),
            "mod": ChainBlock("mod", "MOD", Theme.COLOR_MOD),
            "amp": ChainBlock("amp", "AMP", Theme.COLOR_AMP),
            "eq": ChainBlock("eq", "EQ", Theme.COLOR_EQ),
            "fx": ChainBlock("fx", "FX", Theme.COLOR_FX),
            "delay": ChainBlock("delay", "DELAY", Theme.COLOR_DELAY),
            "reverb": ChainBlock("reverb", "REVERB", Theme.COLOR_REVERB),
            "ns": ChainBlock("ns", "NS", Theme.COLOR_NS),
            "master": ChainBlock("master", "MASTER", Theme.COLOR_MASTER, can_bypass=False),
        }

        for bid, block in self.blocks.items():
            block.clicked.connect(self.select_module)
            block.toggled.connect(self._on_block_toggled)

        # Interactive Routing Customizer Pill Button
        self.btn_routing = QPushButton("🔀 Chain 1 ▾")
        self.btn_routing.setFixedHeight(68)
        self.btn_routing.setFixedWidth(132)
        self.btn_routing.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_routing.setToolTip("🔀 Personalizza Catena del Segnale (7 Topologie Hardware & Posizionamento Modulare)")
        self.btn_routing.setStyleSheet(f"""
            QPushButton {{
                background-color: #1A1F2C;
                border: 1px solid #FF9F0A;
                border-radius: 6px;
                color: #FFB340;
                font-weight: bold;
                padding: 4px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #262E40;
                border-color: #FFAE33;
                color: #FFFFFF;
            }}
        """)
        self.btn_routing.clicked.connect(self._open_routing_dialog)
        root_layout.addWidget(self.btn_routing)

        # Connect model signals
        self.model.parameter_changed.connect(self._on_parameter_changed)
        self.model.patch_loaded.connect(self.sync_from_model)

        # Build initial chain layout and select Amp
        self.rebuild_chain()
        self.select_module("amp")
        self.sync_from_model()

    def _open_routing_dialog(self):
        """Opens interactive signal chain customization dialog."""
        from katana_modern.ui.dialogs.chain_routing_dialog import SignalChainRoutingDialog
        dlg = SignalChainRoutingDialog(self.model, self)
        dlg.routing_changed.connect(lambda cid: self.rebuild_chain())
        dlg.exec()
        self.rebuild_chain()

    def rebuild_chain(self):
        """Rearranges horizontal chain blocks to reflect active hardware routing topology."""
        # 1. Clear existing layout items
        while self.chain_layout.count() > 0:
            item = self.chain_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        # 2. Get active blocks sequence
        ordered_block_ids = self.model.get_active_chain_blocks()

        # 3. Add widgets in new order with subtle arrow connectors
        for idx, bid in enumerate(ordered_block_ids):
            if bid in self.blocks:
                self.chain_layout.addWidget(self.blocks[bid])
                if idx < len(ordered_block_ids) - 1:
                    lbl_arr = QLabel("›")
                    lbl_arr.setFont(QFont("Inter", 11, QFont.Weight.Bold))
                    lbl_arr.setStyleSheet("color: #48484A; padding: 0 1px;")
                    self.chain_layout.addWidget(lbl_arr)

        # 4. Update routing button text
        from katana_modern.core.amp_catalog import CHAIN_ROUTES
        cid = self.model.get_param("chain_pattern", self.model.get_param("chain_position", 0))
        cid = max(0, min(6, cid))
        r_info = CHAIN_ROUTES[cid] if cid < len(CHAIN_ROUTES) else CHAIN_ROUTES[0]
        self.btn_routing.setText(f"⇄ {r_info['short_name']}\n(Modifica ▾)")

    def select_module(self, mod_id: str):
        for bid, b in self.blocks.items():
            b.set_selected(bid == mod_id)
        self.module_selected.emit(mod_id)

    def _on_block_toggled(self, mod_id: str, is_active: bool):
        sw_map = {
            "booster": "booster_sw",
            "mod": "mod_sw",
            "amp": "preamp_sw",
            "eq": "eq1_sw",
            "fx": "fx_sw",
            "delay": "delay1_sw",
            "reverb": "reverb_sw",
            "ns": "ns_sw",
        }
        if mod_id in sw_map:
            self.model.set_param(sw_map[mod_id], 1 if is_active else 0)

    def _on_parameter_changed(self, param_name: str, value: int, display_str: str):
        # Update switch states and subtitles dynamically
        if param_name == "preamp_sw" and "amp" in self.blocks:
            self.blocks["amp"].set_active(value > 0)
        elif param_name == "preamp_type" and "amp" in self.blocks:
            m_info = PREAMP_MODELS.get(value)
            self.blocks["amp"].set_subtitle(m_info.name if m_info else f"Model {value}")

        elif param_name == "booster_sw" and "booster" in self.blocks:
            self.blocks["booster"].set_active(value > 0)
        elif param_name == "booster_type" and "booster" in self.blocks:
            self.blocks["booster"].set_subtitle(BOOSTER_MODELS.get(value, "").split("(")[0].strip())

        elif param_name == "mod_sw" and "mod" in self.blocks:
            self.blocks["mod"].set_active(value > 0)
        elif param_name == "mod_type" and "mod" in self.blocks:
            self.blocks["mod"].set_subtitle(MOD_MODELS.get(value, "").split("(")[0].strip())

        elif param_name == "fx_sw" and "fx" in self.blocks:
            self.blocks["fx"].set_active(value > 0)
        elif param_name == "fx_type" and "fx" in self.blocks:
            self.blocks["fx"].set_subtitle(FX_MODELS.get(value, "").split("(")[0].strip())

        elif param_name == "delay1_sw" and "delay" in self.blocks:
            self.blocks["delay"].set_active(value > 0)
        elif param_name == "delay1_type" and "delay" in self.blocks:
            self.blocks["delay"].set_subtitle(DELAY_MODELS.get(value, "").split("(")[0].strip())

        elif param_name == "reverb_sw" and "reverb" in self.blocks:
            self.blocks["reverb"].set_active(value > 0)
        elif param_name == "reverb_type" and "reverb" in self.blocks:
            self.blocks["reverb"].set_subtitle(REVERB_MODELS.get(value, "").split("(")[0].strip())

        elif param_name == "eq1_sw" and "eq" in self.blocks:
            self.blocks["eq"].set_active(value > 0)
        elif param_name == "eq1_type" and "eq" in self.blocks:
            self.blocks["eq"].set_subtitle("Graphic" if value == 1 else "Parametric")

        elif param_name == "ns_sw" and "ns" in self.blocks:
            self.blocks["ns"].set_active(value > 0)

        elif param_name in ["chain_pattern", "chain_position", "chain_eq1_pos"]:
            self.rebuild_chain()

    def sync_from_model(self):
        """Refreshes all blocks to match current model state."""
        self.rebuild_chain()
        self.blocks["amp"].set_active(self.model.get_param("preamp_sw") > 0)
        m_info = PREAMP_MODELS.get(self.model.get_param("preamp_type"))
        self.blocks["amp"].set_subtitle(m_info.name if m_info else "Clean")

        self.blocks["booster"].set_active(self.model.get_param("booster_sw") > 0)
        self.blocks["booster"].set_subtitle(BOOSTER_MODELS.get(self.model.get_param("booster_type"), "Blues Driver").split("(")[0].strip())

        self.blocks["mod"].set_active(self.model.get_param("mod_sw") > 0)
        self.blocks["mod"].set_subtitle(MOD_MODELS.get(self.model.get_param("mod_type"), "Chorus").split("(")[0].strip())

        self.blocks["fx"].set_active(self.model.get_param("fx_sw") > 0)
        self.blocks["fx"].set_subtitle(FX_MODELS.get(self.model.get_param("fx_type"), "Compressor").split("(")[0].strip())

        self.blocks["delay"].set_active(self.model.get_param("delay1_sw") > 0)
        self.blocks["delay"].set_subtitle(DELAY_MODELS.get(self.model.get_param("delay1_type"), "Digital").split("(")[0].strip())

        self.blocks["reverb"].set_active(self.model.get_param("reverb_sw") > 0)
        self.blocks["reverb"].set_subtitle(REVERB_MODELS.get(self.model.get_param("reverb_type"), "Plate").split("(")[0].strip())

        self.blocks["eq"].set_active(self.model.get_param("eq1_sw") > 0)
        self.blocks["eq"].set_subtitle("Graphic" if self.model.get_param("eq1_type") == 1 else "Parametric")

        self.blocks["ns"].set_active(self.model.get_param("ns_sw") > 0)
        self.blocks["ns"].set_subtitle(f"Thresh {self.model.get_param('ns_threshold')}")

        self.blocks["in"].set_subtitle("Instrument")
        self.blocks["master"].set_subtitle(f"Vol {self.model.get_param('foot_volume')}%")
