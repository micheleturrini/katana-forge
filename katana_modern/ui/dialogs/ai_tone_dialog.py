"""
Gemini AI Tone Assistant Dialog.
Provides interactive prompt generation for famous songs/artists,
instant JSON response parsing, and direct hardware audition with Safe Audition leveling.
"""

from typing import Optional
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices, QClipboard
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QTabWidget, QWidget,
    QFrame, QMessageBox, QApplication, QScrollArea
)

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.ai_preset_engine import (
    build_gemini_prompt, parse_gemini_preset, apply_ai_preset_to_model, export_model_to_ai_json
)


class AIToneAssistantDialog(QDialog):
    """
    AI Tone Assistant modal dialog.
    """
    def __init__(self, patch_model: KatanaPatchModel, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model = patch_model
        self.parsed_preset_data = None

        self.setWindowTitle("Gemini AI Tone Assistant - Boss Katana")
        self.setFixedSize(720, 640)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_PANEL};
                color: {Theme.TEXT_PRIMARY};
            }}
            QTabWidget::pane {{
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
                background-color: {Theme.BG_CARD};
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                color: {Theme.TEXT_SECONDARY};
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {Theme.BG_CARD};
                border-color: #BF5AF2;
                color: #FFFFFF;
            }}
            QLineEdit, QTextEdit, QComboBox {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                padding: 6px;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: #BF5AF2;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Header Title
        head_row = QHBoxLayout()
        lbl_icon = QLabel("✨")
        lbl_icon.setFont(QFont("Inter", 18))
        head_row.addWidget(lbl_icon)

        title_vbox = QVBoxLayout()
        lbl_title = QLabel("GEMINI AI TONE ASSISTANT")
        lbl_title.setFont(QFont("Inter", 13, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #D67AFF; letter-spacing: 1px;")
        title_vbox.addWidget(lbl_title)

        lbl_sub = QLabel("Chiedi a Gemini di generare il tono perfetto per qualsiasi canzone e importalo all'istante nel tuo Katana.")
        lbl_sub.setFont(QFont("Inter", 9))
        lbl_sub.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        title_vbox.addWidget(lbl_sub)
        head_row.addLayout(title_vbox)
        head_row.addStretch()

        layout.addLayout(head_row)

        # Main Tabs
        self.tabs = QTabWidget()
        self.tab_generator = QWidget()
        self.tab_importer = QWidget()
        self.tab_exporter = QWidget()

        self._setup_generator_tab()
        self._setup_importer_tab()
        self._setup_exporter_tab()

        self.tabs.addTab(self.tab_generator, "🔮 Crea Prompt per Gemini")
        self.tabs.addTab(self.tab_importer, "📥 Importa Risposta Gemini")
        self.tabs.addTab(self.tab_exporter, "📤 Esporta Preset per AI")
        layout.addWidget(self.tabs)

        # Bottom Bar
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.btn_close = QPushButton("Chiudi")
        self.btn_close.setFixedHeight(32)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 4px 16px;
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        self.btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(self.btn_close)
        layout.addLayout(bottom_row)

    # -------------------------------------------------------------
    # TAB 1: PROMPT GENERATOR
    # -------------------------------------------------------------
    def _setup_generator_tab(self):
        vbox = QVBoxLayout(self.tab_generator)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        # Quick Song Pills
        lbl_presets = QLabel("SUGGERIMENTI RAPIDI (Clicca per pre-compilare):")
        lbl_presets.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_presets.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        vbox.addWidget(lbl_presets)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips = [
            ("Pink Floyd - Comfortably Numb", "Pink Floyd", "Comfortably Numb", "Second Solo", "Stratocaster / Single-Coil al Ponte"),
            ("Guns N' Roses - Sweet Child", "Guns N' Roses", "Sweet Child O' Mine", "Intro Solo", "Les Paul / Humbucker al Manico"),
            ("Metallica - Enter Sandman", "Metallica", "Enter Sandman", "Main Riff", "Humbucker ad Alto Output"),
            ("SRV - Texas Flood", "Stevie Ray Vaughan", "Texas Flood", "Blues Solo", "Stratocaster / Neck Single-Coil"),
        ]

        for label, artist, song, part, pickup in chips:
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setFont(QFont("Inter", 8))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.BG_INPUT};
                    border: 1px solid {Theme.BORDER_SUBTLE};
                    border-radius: 12px;
                    padding: 2px 8px;
                    color: {Theme.TEXT_SECONDARY};
                }}
                QPushButton:hover {{
                    border-color: #BF5AF2;
                    color: #FFFFFF;
                }}
            """)
            btn.clicked.connect(lambda chk, a=artist, s=song, p=part, pk=pickup: self._fill_generator(a, s, p, pk))
            chips_row.addWidget(btn)
        chips_row.addStretch()
        vbox.addLayout(chips_row)

        # Input Fields Grid
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        vbox_song = QVBoxLayout()
        lbl_song = QLabel("Titolo Canzone:")
        lbl_song.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        vbox_song.addWidget(lbl_song)
        self.txt_song = QLineEdit()
        self.txt_song.setPlaceholderText("es. Comfortably Numb")
        self.txt_song.textChanged.connect(self._update_generated_prompt)
        vbox_song.addWidget(self.txt_song)
        row1.addLayout(vbox_song)

        vbox_artist = QVBoxLayout()
        lbl_artist = QLabel("Artista / Band:")
        lbl_artist.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        vbox_artist.addWidget(lbl_artist)
        self.txt_artist = QLineEdit()
        self.txt_artist.setPlaceholderText("es. Pink Floyd")
        self.txt_artist.textChanged.connect(self._update_generated_prompt)
        vbox_artist.addWidget(self.txt_artist)
        row1.addLayout(vbox_artist)
        vbox.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)

        vbox_part = QVBoxLayout()
        lbl_part = QLabel("Sezione / Ruolo Sonoro:")
        lbl_part.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        vbox_part.addWidget(lbl_part)
        self.txt_part = QLineEdit()
        self.txt_part.setPlaceholderText("es. Assolo finale / Riff / Intro acustica")
        self.txt_part.textChanged.connect(self._update_generated_prompt)
        vbox_part.addWidget(self.txt_part)
        row2.addLayout(vbox_part)

        vbox_pk = QVBoxLayout()
        lbl_pk = QLabel("Pickup / Tipo Chitarra:")
        lbl_pk.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        vbox_pk.addWidget(lbl_pk)
        self.combo_pickup = QComboBox()
        self.combo_pickup.addItem("Qualsiasi / Standard")
        self.combo_pickup.addItem("Stratocaster / Single-Coil al Ponte")
        self.combo_pickup.addItem("Les Paul / Humbucker al Ponte")
        self.combo_pickup.addItem("Strat / Single-Coil al Manico (Blues)")
        self.combo_pickup.addItem("Telecaster / Twang")
        self.combo_pickup.addItem("Humbucker Moderno ad Alto Output (Metal)")
        self.combo_pickup.addItem("Chitarra Acustica / Piezo")
        self.combo_pickup.currentIndexChanged.connect(self._update_generated_prompt)
        vbox_pk.addWidget(self.combo_pickup)
        row2.addLayout(vbox_pk)
        vbox.addLayout(row2)

        # Generated Prompt Preview
        lbl_prev = QLabel("ANTEPRIMA PROMPT PER GEMINI (Include Schema JSON e Catalogo Katana):")
        lbl_prev.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_prev.setStyleSheet(f"color: {Theme.TEXT_MUTED}; margin-top: 4px;")
        vbox.addWidget(lbl_prev)

        self.txt_prompt_preview = QTextEdit()
        self.txt_prompt_preview.setReadOnly(True)
        self.txt_prompt_preview.setFont(QFont("Monospace", 9))
        self.txt_prompt_preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: #A0C0E0;
            }}
        """)
        vbox.addWidget(self.txt_prompt_preview, 1)

        # Action Buttons
        btn_action_row = QHBoxLayout()
        btn_action_row.setSpacing(10)

        self.btn_copy_prompt = QPushButton("📋 COPIA PROMPT PER GEMINI")
        self.btn_copy_prompt.setFixedHeight(36)
        self.btn_copy_prompt.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.btn_copy_prompt.setStyleSheet("""
            QPushButton {
                background-color: #BF5AF2;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D67AFF;
            }
        """)
        self.btn_copy_prompt.clicked.connect(self._copy_prompt_to_clipboard)
        btn_action_row.addWidget(self.btn_copy_prompt)

        self.btn_open_gemini = QPushButton("🌐 Apri gemini.google.com")
        self.btn_open_gemini.setFixedHeight(36)
        self.btn_open_gemini.setFont(QFont("Inter", 9, QFont.Weight.DemiBold))
        self.btn_open_gemini.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid #BF5AF2;
                border-radius: 6px;
                padding: 6px 14px;
                color: #D67AFF;
            }}
            QPushButton:hover {{
                background-color: #26163D;
                color: #FFFFFF;
            }}
        """)
        self.btn_open_gemini.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://gemini.google.com")))
        btn_action_row.addWidget(self.btn_open_gemini)

        vbox.addLayout(btn_action_row)

        # Initial prompt build
        self.txt_song.setText("Comfortably Numb")
        self.txt_artist.setText("Pink Floyd")
        self.txt_part.setText("Second Solo")
        self._update_generated_prompt()

    def _fill_generator(self, artist: str, song: str, part: str, pickup: str):
        self.txt_artist.setText(artist)
        self.txt_song.setText(song)
        self.txt_part.setText(part)
        idx = self.combo_pickup.findText(pickup)
        if idx != -1:
            self.combo_pickup.setCurrentIndex(idx)
        self._update_generated_prompt()

    def _update_generated_prompt(self):
        song = self.txt_song.text().strip()
        artist = self.txt_artist.text().strip()
        part = self.txt_part.text().strip()
        pickup = self.combo_pickup.currentText()
        prompt = build_gemini_prompt(song, artist, part, pickup)
        self.txt_prompt_preview.setText(prompt)

    def _copy_prompt_to_clipboard(self):
        text = self.txt_prompt_preview.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.btn_copy_prompt.setText("✓ PROMPT COPIATO NEGLI APPUNTI!")
        self.btn_copy_prompt.setStyleSheet("""
            QPushButton {
                background-color: #30D158;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
        """)

    # -------------------------------------------------------------
    # TAB 2: IMPORTER (PASTE & AUDITION)
    # -------------------------------------------------------------
    def _setup_importer_tab(self):
        vbox = QVBoxLayout(self.tab_importer)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        paste_hdr = QHBoxLayout()
        lbl_in = QLabel("INCOLLA QUI IL JSON O LA RISPOSTA DI GEMINI:")
        lbl_in.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_in.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        paste_hdr.addWidget(lbl_in)
        paste_hdr.addStretch()

        btn_paste = QPushButton("📋 Incolla da Appunti")
        btn_paste.setFixedHeight(24)
        btn_paste.setFont(QFont("Inter", 8))
        btn_paste.clicked.connect(self._paste_clipboard)
        paste_hdr.addWidget(btn_paste)
        vbox.addLayout(paste_hdr)

        self.txt_gemini_input = QTextEdit()
        self.txt_gemini_input.setPlaceholderText(
            "Incolla qui il JSON generato da Gemini (anche con testo markdown ```json ... ```)\n"
            "L'app estrarrà automaticamente tutti i parametri Katana e li verificherà con Safe Audition."
        )
        self.txt_gemini_input.setFont(QFont("Monospace", 9))
        self.txt_gemini_input.textChanged.connect(self._on_input_changed)
        vbox.addWidget(self.txt_gemini_input, 1)

        # Parsed Tone Preview Card
        self.preview_card = QFrame()
        self.preview_card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        prev_layout = QVBoxLayout(self.preview_card)
        prev_layout.setContentsMargins(8, 6, 8, 6)
        prev_layout.setSpacing(4)

        self.lbl_prev_title = QLabel("Nessun preset valido incollato.")
        self.lbl_prev_title.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.lbl_prev_title.setStyleSheet("color: #8C93A0;")
        prev_layout.addWidget(self.lbl_prev_title)

        self.lbl_prev_details = QLabel("Incolla un JSON per visualizzare i dettagli.")
        self.lbl_prev_details.setFont(QFont("Inter", 8))
        self.lbl_prev_details.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        prev_layout.addWidget(self.lbl_prev_details)

        self.lbl_prev_tips = QLabel("")
        self.lbl_prev_tips.setFont(QFont("Inter", 8))
        self.lbl_prev_tips.setStyleSheet("color: #D67AFF; font-style: italic;")
        self.lbl_prev_tips.setWordWrap(True)
        prev_layout.addWidget(self.lbl_prev_tips)

        vbox.addWidget(self.preview_card)

        # Load / Audition Action Button
        self.btn_apply = QPushButton("⚡ CARICA && AUDIZIONA SUBITO SULL'AMPLI")
        self.btn_apply.setFixedHeight(38)
        self.btn_apply.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.btn_apply.setEnabled(False)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #30D158;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40E369;
            }
            QPushButton:disabled {
                background-color: #2A2D35;
                color: #6C7280;
            }
        """)
        self.btn_apply.clicked.connect(self._apply_ai_preset)
        vbox.addWidget(self.btn_apply)

    def _paste_clipboard(self):
        cb = QApplication.clipboard()
        text = cb.text()
        if text:
            self.txt_gemini_input.setText(text)

    def _on_input_changed(self):
        text = self.txt_gemini_input.toPlainText()
        ok, data, err = parse_gemini_preset(text)
        if ok:
            self.parsed_preset_data = data
            self.btn_apply.setEnabled(True)

            name = data.get("name") or data.get("song") or "AI Preset"
            artist = data.get("artist", "")
            amp = data.get("amp", {})
            boost = data.get("booster", {})
            delay = data.get("delay", {})
            rev = data.get("reverb", {})

            amp_info = f"Amp: {amp.get('type', 'Clean')} (Gain {amp.get('gain', 50)})"
            boost_info = f"Booster: {boost.get('type', 'None')}" if boost.get("enabled") else "Booster: OFF"
            delay_info = f"Delay: {delay.get('type', 'Digital')} ({delay.get('time_ms', 350)}ms)" if delay.get("enabled") else "Delay: OFF"
            rev_info = f"Reverb: {rev.get('type', 'Plate')}" if rev.get("enabled") else "Reverb: OFF"

            self.lbl_prev_title.setText(f"✓ PRESET RICONOSCIUTO: {name} {'(' + artist + ')' if artist else ''}")
            self.lbl_prev_title.setStyleSheet("color: #30D158; font-weight: bold;")

            self.lbl_prev_details.setText(f"• {amp_info}   • {boost_info}   • {delay_info}   • {rev_info}")

            tips = data.get("tone_tips") or data.get("description") or ""
            self.lbl_prev_tips.setText(f"★ Suggerimenti: {tips}" if tips else "")

            self.preview_card.setStyleSheet("""
                QFrame {
                    background-color: #0E2818;
                    border: 1px solid #30D158;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:
            self.parsed_preset_data = None
            self.btn_apply.setEnabled(False)
            self.lbl_prev_title.setText("In attesa di JSON valido...")
            self.lbl_prev_title.setStyleSheet("color: #8C93A0;")
            self.lbl_prev_details.setText(err if text.strip() else "Incolla un blocco JSON da Gemini per verificare.")
            self.lbl_prev_tips.setText("")
            self.preview_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {Theme.BG_INPUT};
                    border: 1px solid {Theme.BORDER_SUBTLE};
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)

    def _apply_ai_preset(self):
        if not self.parsed_preset_data:
            return

        success = apply_ai_preset_to_model(self.parsed_preset_data, self.model, safe_guard=True)
        if success:
            QMessageBox.information(
                self,
                "Preset AI Caricato con Successo!",
                f"Il preset '{self.model.patch_name}' è stato applicato all'editor e inviato in tempo reale al tuo Boss Katana!\n\n"
                f"🛡️ Safe Audition Guard attivo: il volume è stato regolato in modo sicuro (<= 42) per proteggere il tuo ascolto."
            )
            self.accept()
        else:
            QMessageBox.critical(self, "Errore", "Si è verificato un errore nell'applicazione dei parametri.")

    # -------------------------------------------------------------
    # TAB 3: EXPORTER (REVERSE PROMPT)
    # -------------------------------------------------------------
    def _setup_exporter_tab(self):
        vbox = QVBoxLayout(self.tab_exporter)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(8)

        lbl_desc = QLabel(
            "Questo è il preset attualmente aperto nell'editor convertito nel formato standard Katana JSON.\n"
            "Puoi copiarlo e incollarlo in Gemini per chiedere consigli, modifiche o analisi timbriche."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setFont(QFont("Inter", 9))
        lbl_desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
        vbox.addWidget(lbl_desc)

        self.txt_export_preview = QTextEdit()
        self.txt_export_preview.setReadOnly(True)
        self.txt_export_preview.setFont(QFont("Monospace", 9))
        self.txt_export_preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: #A0C0E0;
            }}
        """)
        vbox.addWidget(self.txt_export_preview, 1)

        # Refresh with current model values
        json_str = export_model_to_ai_json(self.model)
        self.txt_export_preview.setText(json_str)

        btn_copy_export = QPushButton("📋 COPIA JSON PER GEMINI")
        btn_copy_export.setFixedHeight(34)
        btn_copy_export.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        btn_copy_export.setStyleSheet("""
            QPushButton {
                background-color: #BF5AF2;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D67AFF;
            }
        """)
        btn_copy_export.clicked.connect(self._copy_export_to_clipboard)
        vbox.addWidget(btn_copy_export)

    def _copy_export_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_export_preview.toPlainText())
        QMessageBox.information(
            self, "Copiato!", "Il JSON del preset attivo è stato copiato negli appunti.\nIncollalo in Gemini!"
        )
