"""
Signal Chain Routing Customizer Dialog for Boss Katana MkII.
Allows guitarist to choose from 7 hardware audio topologies and customize
modular positions of EQ (Pre vs Post Amp), Send/Return Loop, and Pedal FX.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QButtonGroup, QScrollArea, QWidget, QRadioButton
)
from PyQt6.QtGui import QFont, QColor

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.amp_catalog import CHAIN_ROUTES


class ChainCard(QFrame):
    """Clickable card displaying a signal chain topology."""
    selected = pyqtSignal(int)

    def __init__(self, route: dict, is_active: bool, parent=None):
        super().__init__(parent)
        self.route_id = route["id"]
        self.setObjectName("CardFrame")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Top row: Radio + Title + Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.radio = QRadioButton()
        self.radio.setChecked(is_active)
        self.radio.clicked.connect(lambda: self.selected.emit(self.route_id))
        top_row.addWidget(self.radio)

        lbl_title = QLabel(route["name"])
        lbl_title.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        top_row.addWidget(lbl_title)
        top_row.addStretch()

        badge = QLabel(route.get("badge", "MK2"))
        badge.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        badge.setStyleSheet("""
            background-color: #1A2230;
            border: 1px solid #0A84FF;
            color: #5AC8FA;
            border-radius: 3px;
            padding: 2px 6px;
        """)
        top_row.addWidget(badge)
        layout.addLayout(top_row)

        # Signal Flow Visual Diagram
        lbl_flow = QLabel(f"⇄  {route['summary']}")
        lbl_flow.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        lbl_flow.setStyleSheet("color: #FF9F0A; padding-left: 24px;")
        layout.addWidget(lbl_flow)

        # Description
        lbl_desc = QLabel(route["desc"])
        lbl_desc.setFont(QFont("Inter", 8))
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED}; padding-left: 24px;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        self.set_active(is_active)

    def mousePressEvent(self, event):
        self.selected.emit(self.route_id)
        super().mousePressEvent(event)

    def set_active(self, active: bool):
        self.radio.setChecked(active)
        if active:
            self.setStyleSheet(f"""
                QFrame#CardFrame {{
                    background-color: #16202A;
                    border: 2px solid {Theme.COLOR_AMP};
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#CardFrame {{
                    background-color: {Theme.BG_CARD};
                    border: 1px solid {Theme.BORDER_SUBTLE};
                    border-radius: 6px;
                }}
                QFrame#CardFrame:hover {{
                    border-color: {Theme.BORDER_FOCUS};
                }}
            """)


class SignalChainRoutingDialog(QDialog):
    """
    Modal interface for selecting chain routing topology and modular positioning.
    """
    routing_changed = pyqtSignal(int)

    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.setWindowTitle("🔀 Personalizzazione Catena del Segnale (Signal Chain Routing)")
        self.resize(720, 640)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_ROOT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header Title
        title_row = QHBoxLayout()
        lbl_icon = QLabel("⇄")
        lbl_icon.setFont(QFont("DejaVu Sans", 18, QFont.Weight.Bold))
        lbl_icon.setStyleSheet("color: #FF9F0A;")
        title_row.addWidget(lbl_icon)

        vbox_head = QVBoxLayout()
        vbox_head.setSpacing(2)
        lbl_title = QLabel("ROUTING CATENA EFFETTI BOSS KATANA MKII")
        lbl_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; letter-spacing: 0.5px;")
        vbox_head.addWidget(lbl_title)

        lbl_sub = QLabel("Scegli come disporre Booster, Modulazioni, FX, Delay e Preamplificatore nell'hardware DSP")
        lbl_sub.setFont(QFont("Inter", 9))
        lbl_sub.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        vbox_head.addWidget(lbl_sub)
        title_row.addLayout(vbox_head)
        title_row.addStretch()
        layout.addLayout(title_row)

        # Scrollable Chain Topologies list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
            }}
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(8)

        current_cid = self.model.get_param("chain_pattern", self.model.get_param("chain_position", 0))
        self.cards = []
        for route in CHAIN_ROUTES:
            card = ChainCard(route, is_active=(route["id"] == current_cid))
            card.selected.connect(self._on_chain_selected)
            scroll_layout.addWidget(card)
            self.cards.append(card)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # Modular Block Positions Section (EQ, Loop, Pedal FX)
        mod_frame = QFrame()
        mod_frame.setObjectName("CardFrame")
        mod_frame.setStyleSheet(f"""
            QFrame#CardFrame {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
                padding: 6px;
            }}
        """)
        mod_layout = QVBoxLayout(mod_frame)
        mod_layout.setContentsMargins(10, 8, 10, 8)
        mod_layout.setSpacing(8)

        lbl_mod_sec = QLabel("POSIZIONAMENTO MODULARE BLOCCHI")
        lbl_mod_sec.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_mod_sec.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; letter-spacing: 0.5px;")
        mod_layout.addWidget(lbl_mod_sec)

        # 1. EQ1 Position: Pre-Amp vs Post-Amp
        row_eq = QHBoxLayout()
        lbl_eq = QLabel("Posizione Equalizzatore (EQ1):")
        lbl_eq.setFont(QFont("Inter", 9))
        lbl_eq.setStyleSheet(f"color: {Theme.TEXT_MUTED}; min-width: 220px;")
        row_eq.addWidget(lbl_eq)

        self.btn_eq_pre = QPushButton("Amp In (Pre-Amp)")
        self.btn_eq_post = QPushButton("Amp Out (Post-Amp)")
        for b in [self.btn_eq_pre, self.btn_eq_post]:
            b.setCheckable(True)
            b.setFixedHeight(26)
            b.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            b.setStyleSheet(self._segmented_btn_style())

        self.grp_eq = QButtonGroup(self)
        self.grp_eq.setExclusive(True)
        self.grp_eq.addButton(self.btn_eq_pre, 0)
        self.grp_eq.addButton(self.btn_eq_post, 1)

        cur_eq = self.model.get_param("chain_eq1_pos", 1)
        if cur_eq == 0:
            self.btn_eq_pre.setChecked(True)
        else:
            self.btn_eq_post.setChecked(True)

        self.grp_eq.idClicked.connect(lambda v: self.model.set_param("chain_eq1_pos", v))
        row_eq.addWidget(self.btn_eq_pre)
        row_eq.addWidget(self.btn_eq_post)
        row_eq.addStretch()
        mod_layout.addLayout(row_eq)

        # 2. S/R Loop Position: Post Amp vs Post Reverb
        row_loop = QHBoxLayout()
        lbl_loop = QLabel("Send/Return Loop (S/R):")
        lbl_loop.setFont(QFont("Inter", 9))
        lbl_loop.setStyleSheet(f"color: {Theme.TEXT_MUTED}; min-width: 220px;")
        row_loop.addWidget(lbl_loop)

        self.btn_loop_postamp = QPushButton("Post Amp (FX Loop)")
        self.btn_loop_postrev = QPushButton("Post Reverb (Fine Catena)")
        for b in [self.btn_loop_postamp, self.btn_loop_postrev]:
            b.setCheckable(True)
            b.setFixedHeight(26)
            b.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            b.setStyleSheet(self._segmented_btn_style())

        self.grp_loop = QButtonGroup(self)
        self.grp_loop.setExclusive(True)
        self.grp_loop.addButton(self.btn_loop_postamp, 0)
        self.grp_loop.addButton(self.btn_loop_postrev, 1)

        cur_loop = self.model.get_param("chain_loop_pos", 0)
        if cur_loop == 0:
            self.btn_loop_postamp.setChecked(True)
        else:
            self.btn_loop_postrev.setChecked(True)

        self.grp_loop.idClicked.connect(lambda v: self.model.set_param("chain_loop_pos", v))
        row_loop.addWidget(self.btn_loop_postamp)
        row_loop.addWidget(self.btn_loop_postrev)
        row_loop.addStretch()
        mod_layout.addLayout(row_loop)

        layout.addWidget(mod_frame)

        # Close button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_close = QPushButton("Applica & Chiudi")
        btn_close.setFixedHeight(32)
        btn_close.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.COLOR_AMP};
                border: none;
                border-radius: 4px;
                color: #FFFFFF;
                font-weight: bold;
                padding: 4px 18px;
            }}
            QPushButton:hover {{
                background-color: #FF5A4D;
            }}
        """)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _on_chain_selected(self, cid: int):
        self.model.set_param("chain_pattern", cid)
        self.model.set_param("chain_position", cid)
        for card in self.cards:
            card.set_active(card.route_id == cid)
        self.routing_changed.emit(cid)

    def _segmented_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 3px;
                color: {Theme.TEXT_SECONDARY};
                padding: 2px 10px;
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
