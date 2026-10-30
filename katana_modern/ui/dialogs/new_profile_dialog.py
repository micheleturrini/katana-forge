"""
New Profile / Preset Creation Dialog for Boss Katana MkII.
Provides intuitive sonic starting templates (Clean Canvas, Vintage Crunch,
High-Gain Lead, Ambient Space, Acoustic, or Duplicate Current) with clear
3-step workflow guidance for guitarists.
"""

from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QRadioButton, QButtonGroup, QScrollArea, QWidget
)
from PyQt6.QtGui import QFont, QCursor

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel


TEMPLATES = [
    {
        "id": "clean",
        "name": "★ Clean Canvas (Neutro da Zero)",
        "desc": "Preamplificatore Clean naturale, EQ flat neutrale a 50, riverbero leggero. Il punto di partenza ideale per modellare il tuo suono personalizzato passo dopo passo.",
        "badge": "RACCOMANDATO"
    },
    {
        "id": "crunch",
        "name": "◆ Vintage Crunch (Plexi / Blues Rock)",
        "desc": "Crunch dinamico e reattivo al tocco, overdrive caldo Blues Driver pronto all'uso, riverbero Spring.",
        "badge": "BLUES / ROCK"
    },
    {
        "id": "lead",
        "name": "▲ High-Gain Lead (Metal / Solo)",
        "desc": "Ampli Brown/Lead con sustain infinito, Tube Screamer attivo come booster, Analog Delay e Noise Suppressor tarato.",
        "badge": "METAL / SOLO"
    },
    {
        "id": "ambient",
        "name": "◈ Ambient Space (Dreamy Clean)",
        "desc": "Suono spaziale profondo: Clean cristallino arricchito da Stereo Chorus, Delay modulato e Riverbero Plate avvolgente.",
        "badge": "AMBIENT"
    },
    {
        "id": "acoustic",
        "name": "♪ Acoustic Resonance (Chitarra Acustica)",
        "desc": "Emulazione cassa armonica per chitarre acustiche ed elettroacustiche con compressione morbida e riverbero Hall.",
        "badge": "ACOUSTIC"
    },
    {
        "id": "blank",
        "name": "○ Inizializza Tutto Bypassed (Flat)",
        "desc": "Tutti i pedali ed effetti spenti in bypass, manopole a 50, volume di sicurezza a 40.",
        "badge": "MINIMAL"
    },
    {
        "id": "duplicate",
        "name": "⎘ Duplica Profilo Attuale",
        "desc": "Copia esattamente tutte le regolazioni sonore del profilo attualmente in ascolto per sperimentare una variante senza rischiare di sovrascrivere l'originale.",
        "badge": "CLONA"
    },
]


class TemplateCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, tpl: dict, is_selected: bool, parent=None):
        super().__init__(parent)
        self.tpl_id = tpl["id"]
        self.setObjectName("CardFrame")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.radio = QRadioButton()
        self.radio.setChecked(is_selected)
        self.radio.clicked.connect(lambda: self.clicked.emit(self.tpl_id))
        top_row.addWidget(self.radio)

        lbl_title = QLabel(tpl["name"])
        lbl_title.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        top_row.addWidget(lbl_title)
        top_row.addStretch()

        badge = QLabel(tpl["badge"])
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

        lbl_desc = QLabel(tpl["desc"])
        lbl_desc.setFont(QFont("Inter", 8))
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_MUTED}; padding-left: 24px;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        self.set_selected(is_selected)

    def mousePressEvent(self, event):
        self.clicked.emit(self.tpl_id)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.radio.setChecked(selected)
        if selected:
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


class NewProfileDialog(QDialog):
    """
    User-friendly modal dialog to create a new profile from scratch or template.
    """
    profile_created = pyqtSignal(str)

    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.setWindowTitle("✨ Crea Nuovo Profilo / Preset")
        self.resize(680, 620)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_ROOT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header Title
        head_row = QHBoxLayout()
        lbl_icon = QLabel("★")
        lbl_icon.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        lbl_icon.setStyleSheet("color: #30D158;")
        head_row.addWidget(lbl_icon)

        vbox_head = QVBoxLayout()
        vbox_head.setSpacing(2)
        lbl_title = QLabel("CREA UN NUOVO PROFILO")
        lbl_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; letter-spacing: 0.5px;")
        vbox_head.addWidget(lbl_title)

        lbl_sub = QLabel("Inizia con una tela pulita o scegli un template sonoro configurato")
        lbl_sub.setFont(QFont("Inter", 9))
        lbl_sub.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        vbox_head.addWidget(lbl_sub)
        head_row.addLayout(vbox_head)
        head_row.addStretch()
        layout.addLayout(head_row)

        # 3-Step Workflow Banner
        guide_box = QFrame()
        guide_box.setStyleSheet("""
            background-color: #151A24;
            border: 1px solid #1E293B;
            border-radius: 6px;
            padding: 8px 12px;
        """)
        g_layout = QHBoxLayout(guide_box)
        g_layout.setContentsMargins(4, 4, 4, 4)
        g_layout.setSpacing(8)

        lbl_g1 = QLabel("<b>1. Crea Profilo</b><br><span style='color:#8C93A0;font-size:10px;'>Nome e punto di partenza</span>")
        lbl_garr1 = QLabel("➔")
        lbl_garr1.setStyleSheet("color: #FF7043; font-weight: bold;")
        lbl_g2 = QLabel("<b>2. Modifica Suono</b><br><span style='color:#8C93A0;font-size:10px;'>Manopole, blocchi e catena</span>")
        lbl_garr2 = QLabel("➔")
        lbl_garr2.setStyleSheet("color: #FF7043; font-weight: bold;")
        lbl_g3 = QLabel("<b>3. Salva nell'Ampli</b><br><span style='color:#30D158;font-size:10px;'>Pulsante <b>Burn to Amp</b></span>")

        for l in [lbl_g1, lbl_g2, lbl_g3]:
            l.setFont(QFont("Inter", 8))
            l.setTextFormat(Qt.TextFormat.RichText)

        g_layout.addWidget(lbl_g1)
        g_layout.addWidget(lbl_garr1)
        g_layout.addWidget(lbl_g2)
        g_layout.addWidget(lbl_garr2)
        g_layout.addWidget(lbl_g3)
        g_layout.addStretch()
        layout.addWidget(guide_box)

        # Name Input Field
        name_vbox = QVBoxLayout()
        name_vbox.setSpacing(4)
        lbl_name = QLabel("NOME DEL PROFILO:")
        lbl_name.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_name.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        name_vbox.addWidget(lbl_name)

        self.txt_name = QLineEdit()
        self.txt_name.setText("Mio Preset")
        self.txt_name.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.txt_name.setFixedHeight(34)
        self.txt_name.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 4px 10px;
                color: #FFFFFF;
            }}
            QLineEdit:focus {{
                border-color: {Theme.COLOR_AMP};
            }}
        """)
        self.txt_name.selectAll()
        name_vbox.addWidget(self.txt_name)
        layout.addLayout(name_vbox)

        # Template Selection Section
        lbl_tpl_title = QLabel("PUNTO DI PARTENZA (TEMPLATE SONORO):")
        lbl_tpl_title.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_tpl_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; margin-top: 4px;")
        layout.addWidget(lbl_tpl_title)

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
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        scroll_layout.setSpacing(6)

        self.selected_template = "clean"
        self.cards = []
        for tpl in TEMPLATES:
            card = TemplateCard(tpl, is_selected=(tpl["id"] == self.selected_template))
            card.clicked.connect(self._on_template_selected)
            scroll_layout.addWidget(card)
            self.cards.append(card)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # Bottom Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Annulla")
        btn_cancel.setFixedHeight(32)
        btn_cancel.setFont(QFont("Inter", 9))
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 4px 14px;
                color: {Theme.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                color: #FFFFFF;
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_row.addStretch()

        self.btn_create = QPushButton("Crea Profilo e Inizia ad Audizionare")
        self.btn_create.setFixedHeight(34)
        self.btn_create.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.btn_create.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.COLOR_AMP};
                border: none;
                border-radius: 4px;
                color: #FFFFFF;
                font-weight: bold;
                padding: 4px 20px;
            }}
            QPushButton:hover {{
                background-color: #FF5A4D;
            }}
        """)
        self.btn_create.clicked.connect(self._create_profile)
        btn_row.addWidget(self.btn_create)

        layout.addLayout(btn_row)

    def _on_template_selected(self, tpl_id: str):
        self.selected_template = tpl_id
        for card in self.cards:
            card.set_selected(card.tpl_id == tpl_id)
        # Suggest template-based name if default
        if self.txt_name.text() in ["Mio Preset", "Custom Clean", "Vintage Crunch", "High-Gain Lead", "Ambient Space", "Acoustic Sim"]:
            tpl_names = {
                "clean": "Custom Clean",
                "crunch": "Vintage Crunch",
                "lead": "High-Gain Lead",
                "ambient": "Ambient Space",
                "acoustic": "Acoustic Sim",
                "blank": "Init Flat",
                "duplicate": f"{self.model.patch_name} Copy"
            }
            if tpl_id in tpl_names:
                self.txt_name.setText(tpl_names[tpl_id])
                self.txt_name.selectAll()

    def _create_profile(self):
        name = self.txt_name.text().strip() or "Nuovo Profilo"
        self.model.create_new_profile(name, self.selected_template)
        self.profile_created.emit(name)
        self.accept()
