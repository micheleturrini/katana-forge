"""
Dialog for permanently storing / burning a preset to Boss Katana channel memory.
"""

from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QFrame,
    QGridLayout, QMessageBox, QCheckBox
)
from PyQt6.QtGui import QFont

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel


class WriteToAmpDialog(QDialog):
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.model = patch_model
        self.setWindowTitle("Save / Write Preset to Katana Memory")
        self.setFixedSize(520, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # Title
        lbl_title = QLabel("STORE PRESET TO HARDWARE MEMORY")
        lbl_title.setFont(QFont("Inter", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Theme.COLOR_AMP}; letter-spacing: 0.5px;")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "Select the destination hardware memory slot. This will permanently burn "
            "the current settings to your amplifier's internal flash memory."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(lbl_desc)

        # Patch Name row
        name_row = QHBoxLayout()
        lbl_name = QLabel("Preset Name:")
        lbl_name.setFont(QFont("Inter", 10, QFont.Weight.DemiBold))
        lbl_name.setStyleSheet(f"color: {Theme.TEXT_PRIMARY};")
        name_row.addWidget(lbl_name)

        self.txt_name = QLineEdit()
        self.txt_name.setText(self.model.patch_name)
        self.txt_name.setMaxLength(16)
        self.txt_name.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.txt_name.setFixedHeight(32)
        self.txt_name.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: #FFFFFF;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.COLOR_AMP};
            }}
        """)
        name_row.addWidget(self.txt_name)
        layout.addLayout(name_row)

        # Destination Visual Banner
        self.dest_card = QFrame()
        self.dest_card.setObjectName("TargetCard")
        self.dest_card.setStyleSheet("""
            background-color: #0E2818;
            border: 1px solid #30D158;
            border-radius: 6px;
        """)
        dest_card_layout = QHBoxLayout(self.dest_card)
        dest_card_layout.setContentsMargins(12, 8, 12, 8)

        self.lbl_target_banner = QLabel("TARGET:  ➔  BANK A — CH 1")
        self.lbl_target_banner.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.lbl_target_banner.setStyleSheet("color: #30D158; letter-spacing: 0.5px; border: none; background: transparent;")
        dest_card_layout.addWidget(self.lbl_target_banner)
        dest_card_layout.addStretch()

        layout.addWidget(self.dest_card)

        # Destination Channels Frame
        ch_frame = QFrame()
        ch_frame.setObjectName("CardFrame")
        ch_layout = QVBoxLayout(ch_frame)
        ch_layout.setContentsMargins(12, 10, 12, 10)
        ch_layout.setSpacing(10)

        lbl_dest = QLabel("SELECT HARDWARE DESTINATION:")
        lbl_dest.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_dest.setStyleSheet(f"color: {Theme.TEXT_MUTED}; letter-spacing: 0.5px;")
        ch_layout.addWidget(lbl_dest)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)
        self.btn_group.idClicked.connect(self._on_channel_selected)

        # 0: Panel Button (Amber theme)
        self.btn_panel = QPushButton("●  PANEL (Live Amp Settings)")
        self.btn_panel.setCheckable(True)
        self.btn_panel.setFixedHeight(30)
        self.btn_panel.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.btn_panel.setStyleSheet("""
            QPushButton {
                background-color: #16181E;
                border: 1px solid #282C35;
                border-radius: 4px;
                color: #8C93A0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #222630;
                border-color: #FF9500;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #2E1B0D;
                border: 2px solid #FF9500;
                color: #FFB340;
                font-weight: bold;
            }
        """)
        self.btn_group.addButton(self.btn_panel, 0)
        ch_layout.addWidget(self.btn_panel)

        # Bank A Row
        vbox_a = QVBoxLayout()
        vbox_a.setSpacing(4)
        lbl_ba_title = QLabel("BANK A")
        lbl_ba_title.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_ba_title.setStyleSheet("color: #30D158; letter-spacing: 0.5px;")
        vbox_a.addWidget(lbl_ba_title)

        row_a = QHBoxLayout()
        row_a.setSpacing(6)
        for i in range(1, 5):
            btn = QPushButton(f"CH {i}")
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #16181E;
                    border: 1px solid #282C35;
                    border-radius: 4px;
                    color: #8C93A0;
                }
                QPushButton:hover {
                    background-color: #222630;
                    border-color: #30D158;
                    color: #FFFFFF;
                }
                QPushButton:checked {
                    background-color: #0E2818;
                    border: 2px solid #30D158;
                    color: #FFFFFF;
                    font-weight: bold;
                }
            """)
            self.btn_group.addButton(btn, i)
            row_a.addWidget(btn)
            if i == 1:
                btn.setChecked(True)
        vbox_a.addLayout(row_a)
        ch_layout.addLayout(vbox_a)

        # Bank B Row
        vbox_b = QVBoxLayout()
        vbox_b.setSpacing(4)
        lbl_bb_title = QLabel("BANK B")
        lbl_bb_title.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_bb_title.setStyleSheet("color: #0A84FF; letter-spacing: 0.5px;")
        vbox_b.addWidget(lbl_bb_title)

        row_b = QHBoxLayout()
        row_b.setSpacing(6)
        for i in range(5, 9):
            btn = QPushButton(f"CH {i-4}")
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #16181E;
                    border: 1px solid #282C35;
                    border-radius: 4px;
                    color: #8C93A0;
                }
                QPushButton:hover {
                    background-color: #222630;
                    border-color: #0A84FF;
                    color: #FFFFFF;
                }
                QPushButton:checked {
                    background-color: #0A1C30;
                    border: 2px solid #0A84FF;
                    color: #FFFFFF;
                    font-weight: bold;
                }
            """)
            self.btn_group.addButton(btn, i)
            row_b.addWidget(btn)
        vbox_b.addLayout(row_b)
        ch_layout.addLayout(vbox_b)

        layout.addWidget(ch_frame)

        # Safe Audition Normalizer Option
        self.chk_safe_normalize = QCheckBox("🛡️ Normalizza volume a livello sicuro (42) prima di scrivere")
        self.chk_safe_normalize.setChecked(True)
        self.chk_safe_normalize.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        self.chk_safe_normalize.setStyleSheet("color: #30D158; padding: 2px 0px;")
        self.chk_safe_normalize.setToolTip(
            "Consigliato: garantisce che il canale non provochi mai esplosioni di volume\n"
            "quando selezionato tramite i pulsanti fisici del Boss Katana."
        )
        layout.addWidget(self.chk_safe_normalize)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_write = QPushButton("⚡ BURN TO AMP MEMORY")
        self.btn_write.setFixedHeight(34)
        self.btn_write.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.btn_write.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C0392B;
            }}
        """)
        self.btn_write.clicked.connect(self._do_write)
        btn_box.addWidget(self.btn_write)

        layout.addLayout(btn_box)

    def _on_channel_selected(self, ch_id: int):
        ch_meta = [
            ("PANEL (Live Amp Settings)", "#FF9500", "#2C1808"),
            ("BANK A — CH 1", "#30D158", "#0E2818"),
            ("BANK A — CH 2", "#30D158", "#0E2818"),
            ("BANK A — CH 3", "#30D158", "#0E2818"),
            ("BANK A — CH 4", "#30D158", "#0E2818"),
            ("BANK B — CH 1", "#0A84FF", "#0A1C30"),
            ("BANK B — CH 2", "#0A84FF", "#0A1C30"),
            ("BANK B — CH 3", "#0A84FF", "#0A1C30"),
            ("BANK B — CH 4", "#0A84FF", "#0A1C30")
        ]
        if 0 <= ch_id < len(ch_meta):
            name, border_col, bg_col = ch_meta[ch_id]
            self.lbl_target_banner.setText(f"TARGET:  ➔  {name}")
            self.lbl_target_banner.setStyleSheet(f"color: {border_col}; font-weight: bold; border: none; background: transparent;")
            self.dest_card.setStyleSheet(f"""
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 6px;
            """)

    def _do_write(self):
        ch_idx = self.btn_group.checkedId()
        name = self.txt_name.text().strip() or "My Preset"

        if not self.model.midi_backend or not self.model.midi_backend.is_connected():
            QMessageBox.warning(
                self, "Amplifier Not Connected",
                "Cannot write to hardware: Boss Katana MIDI is not connected.\n"
                "Please connect the amplifier via USB and select the MIDI port in the Header."
            )
            return

        safe_norm = self.chk_safe_normalize.isChecked()
        success = self.model.write_to_hardware_channel(ch_idx, name, safe_normalize=safe_norm)
        if success:
            ch_names = ["Panel", "Bank A Ch 1", "Bank A Ch 2", "Bank A Ch 3", "Bank A Ch 4",
                        "Bank B Ch 1", "Bank B Ch 2", "Bank B Ch 3", "Bank B Ch 4"]
            dest_name = ch_names[ch_idx] if ch_idx < len(ch_names) else f"Channel {ch_idx}"
            QMessageBox.information(
                self, "Write Succeeded",
                f"Preset '{name}' has been burned successfully to {dest_name} on your Boss Katana!"
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Write Failed", "An error occurred writing to Katana memory.")
