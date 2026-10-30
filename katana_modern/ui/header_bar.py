"""
Application Header & Hardware Status Bar.
Contains patch name editing, MIDI device connection manager,
undo/redo quick actions, and sidebar toggle.
"""

import os
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QWidget, QMessageBox
)
from PyQt6.QtGui import QFont, QPixmap, QIcon

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.midi_backend import KatanaMidiBackend


class CompactComboBox(QComboBox):
    """QComboBox with constrained size hints to prevent layout blowout on long item labels."""
    def minimumSizeHint(self) -> QSize:
        return QSize(125, 28)

    def sizeHint(self) -> QSize:
        return QSize(125, 28)


class BrandWidget(QWidget):
    """Clickable brand anchor widget with fixed size hint."""
    def minimumSizeHint(self) -> QSize:
        return QSize(158, 36)

    def sizeHint(self) -> QSize:
        return QSize(158, 36)


class HeaderBar(QFrame):
    """
    Top-level application bar managing connectivity, preset branding, and global actions.
    """
    toggle_sidebar_requested = pyqtSignal()

    def __init__(
        self,
        patch_model: KatanaPatchModel,
        midi_backend: KatanaMidiBackend,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.model = patch_model
        self.midi = midi_backend

        self.setObjectName("PanelFrame")
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # 1. App Logo & Brand Identity (Top-Left Anchor)
        brand_widget = BrandWidget()
        brand_widget.setFixedWidth(158)
        brand_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        brand_widget.setToolTip(
            "⚡ KATANA FORGE — MkII Tone Studio\n"
            "Ambiente avanzato di sound design per Boss Katana MkII\n"
            "Clicca per informazioni sul programma"
        )
        brand_widget.mousePressEvent = lambda ev: self._open_about_dialog()
        brand_lay = QHBoxLayout(brand_widget)
        brand_lay.setContentsMargins(0, 0, 0, 0)
        brand_lay.setSpacing(6)

        # Vector/PNG Logo
        self.lbl_logo = QLabel()
        self.lbl_logo.setFixedSize(32, 32)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "app_logo_32.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            self.lbl_logo.setPixmap(pix)
            self.lbl_logo.setScaledContents(True)
        brand_lay.addWidget(self.lbl_logo)

        # Title & Subtitle Stack
        vbox_titles = QVBoxLayout()
        vbox_titles.setContentsMargins(0, 0, 0, 0)
        vbox_titles.setSpacing(0)

        lbl_brand_title = QLabel("KATANA FORGE")
        lbl_brand_title.setFont(QFont("Inter", 10, QFont.Weight.Black))
        lbl_brand_title.setStyleSheet("color: #FFFFFF; letter-spacing: 0.6px;")
        vbox_titles.addWidget(lbl_brand_title)

        lbl_brand_sub = QLabel("MKII TONE STUDIO")
        lbl_brand_sub.setFont(QFont("Inter", 7, QFont.Weight.Bold))
        lbl_brand_sub.setStyleSheet(f"color: {Theme.COLOR_AMP}; letter-spacing: 0.3px;")
        vbox_titles.addWidget(lbl_brand_sub)

        brand_lay.addLayout(vbox_titles)
        layout.addWidget(brand_widget)

        # Subtle Vertical Divider
        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet(f"background-color: {Theme.BORDER_SUBTLE}; margin: 8px 3px;")
        layout.addWidget(divider)

        # 2. Sidebar Toggle Button
        self.btn_sidebar = QPushButton("☰")
        self.btn_sidebar.setFixedSize(28, 28)
        self.btn_sidebar.setFont(QFont("Inter", 12))
        self.btn_sidebar.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {Theme.BG_CARD_HOVER};
                border-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        self.btn_sidebar.setToolTip("Toggle Preset Librarian Sidebar")
        self.btn_sidebar.clicked.connect(self.toggle_sidebar_requested.emit)
        layout.addWidget(self.btn_sidebar)

        layout.addSpacing(2)

        # 3. Patch Name Editor (Editable inline)
        lbl_name_tag = QLabel("PATCH:")
        lbl_name_tag.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_name_tag.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        layout.addWidget(lbl_name_tag)

        self.txt_patch_name = QLineEdit()
        self.txt_patch_name.setText(self.model.patch_name)
        self.txt_patch_name.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        self.txt_patch_name.setFixedWidth(118)
        self.txt_patch_name.setFixedHeight(28)
        self.txt_patch_name.textChanged.connect(self._on_patch_name_edited)
        layout.addWidget(self.txt_patch_name)

        # Quick New Profile Button
        self.btn_new_patch = QPushButton("+ Nuovo")
        self.btn_new_patch.setFixedHeight(28)
        self.btn_new_patch.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_new_patch.setToolTip("Crea un nuovo profilo da zero o da un template sonoro (Ctrl+N)")
        self.btn_new_patch.setStyleSheet("""
            QPushButton {
                background-color: #1A281E;
                border: 1px solid #30D158;
                border-radius: 4px;
                color: #30D158;
                padding: 2px 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #24382A;
                border-color: #40E369;
                color: #FFFFFF;
            }
        """)
        self.btn_new_patch.clicked.connect(self._open_new_profile_dialog)
        layout.addWidget(self.btn_new_patch)

        # Dirty Indicator
        self.lbl_dirty = QLabel("")
        self.lbl_dirty.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.lbl_dirty.setStyleSheet(f"color: {Theme.COLOR_BOOSTER};")
        layout.addWidget(self.lbl_dirty)

        layout.addStretch()

        # 4. Safe Audition Guard & Level Normalizer Controls
        self.btn_safe_guard = QPushButton("🛡️ SAFE: ON")
        self.btn_safe_guard.setFixedHeight(28)
        self.btn_safe_guard.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_safe_guard.setToolTip(
            "🛡️ SAFE AUDITION GUARD & LEVEL NORMALIZER (ACTIVE)\n"
            "• Protects against ear and speaker damage from volume blasts\n"
            "• Automatically normalizes preset volume between 36 and 42\n"
            "• Disables sudden solo switch boosts and volume clipping\n"
            "• Equalizes clean and high-gain presets to identical comfortable loudness\n"
            "• Click to toggle or view safety status"
        )
        self.btn_safe_guard.clicked.connect(self._toggle_safe_guard)
        self._update_safe_guard_style(self.model.safe_audition_enabled)
        layout.addWidget(self.btn_safe_guard)

        layout.addSpacing(2)

        # 5. Action Buttons: Audition & Write to Amp
        self.btn_send = QPushButton("⚡ Audition")
        self.btn_send.setFixedHeight(28)
        self.btn_send.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 3px 6px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                border-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        self.btn_send.setToolTip("Send active patch to Katana edit buffer to audition sound live")
        self.btn_send.clicked.connect(self._send_patch_to_amp)
        layout.addWidget(self.btn_send)

        self.btn_write = QPushButton("Burn to Amp")
        self.btn_write.setFixedHeight(28)
        self.btn_write.setMinimumWidth(94)
        self.btn_write.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_write.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.COLOR_AMP};
                color: {Theme.COLOR_AMP};
                border-radius: 4px;
                font-weight: bold;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        self.btn_write.setToolTip("Permanently save / burn current patch into Katana Channel memory")
        self.btn_write.clicked.connect(self._open_write_dialog)
        layout.addWidget(self.btn_write)

        layout.addSpacing(2)

        # 6. Gemini AI Assistant Button
        self.btn_ai_tone = QPushButton("✨ AI Tone")
        self.btn_ai_tone.setFixedHeight(28)
        self.btn_ai_tone.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_ai_tone.setStyleSheet("""
            QPushButton {
                background-color: #211538;
                border: 1px solid #BF5AF2;
                color: #D67AFF;
                border-radius: 4px;
                padding: 3px 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #321F54;
                border-color: #E295FF;
                color: #FFFFFF;
            }
        """)
        self.btn_ai_tone.setToolTip("✨ Gemini AI Tone Assistant\nCrea prompt per qualsiasi canzone o importa preset JSON da Gemini")
        self.btn_ai_tone.clicked.connect(self._open_ai_tone_dialog)
        layout.addWidget(self.btn_ai_tone)

        layout.addSpacing(2)

        # 7. Undo / Redo Buttons
        undo_redo_style = f"""
            QPushButton {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                padding: 0px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {Theme.BORDER_FOCUS};
                background-color: {Theme.BG_CARD_HOVER};
            }}
        """
        self.btn_undo = QPushButton("↶")
        self.btn_undo.setFixedSize(26, 28)
        self.btn_undo.setFont(QFont("DejaVu Sans", 10))
        self.btn_undo.setStyleSheet(undo_redo_style)
        self.btn_undo.setToolTip("Undo last change (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.model.undo)
        layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↷")
        self.btn_redo.setFixedSize(26, 28)
        self.btn_redo.setFont(QFont("DejaVu Sans", 10))
        self.btn_redo.setStyleSheet(undo_redo_style)
        self.btn_redo.setToolTip("Redo change (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.model.redo)
        layout.addWidget(self.btn_redo)

        layout.addSpacing(4)

        # 8. MIDI Hardware Port Selector & Connect Button
        lbl_midi = QLabel("MIDI:")
        lbl_midi.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_midi.setStyleSheet(f"color: {Theme.TEXT_MUTED};")
        layout.addWidget(lbl_midi)

        self.combo_ports = CompactComboBox()
        self.combo_ports.setFixedHeight(28)
        self.combo_ports.setFixedWidth(115)
        self.combo_ports.setFont(QFont("Inter", 8))
        self.combo_ports.setToolTip("Seleziona la porta MIDI del Katana (KATANA MkII hw:1,0,0)")
        self._populate_ports()
        layout.addWidget(self.combo_ports)

        self.btn_rescan = QPushButton("↻")
        self.btn_rescan.setFixedSize(26, 28)
        self.btn_rescan.setFont(QFont("Inter", 10))
        self.btn_rescan.setToolTip("Riscansiona porte MIDI USB (Hot-plug Katana)")
        self.btn_rescan.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_SECONDARY};
                padding: 0px;
            }}
            QPushButton:hover {{
                border-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        self.btn_rescan.clicked.connect(self._rescan_midi_ports)
        layout.addWidget(self.btn_rescan)

        self.btn_connect = QPushButton("CONNECT")
        self.btn_connect.setFixedHeight(28)
        self.btn_connect.setFixedWidth(78)
        self.btn_connect.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_connect.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 2px 4px;
            }}
        """)
        self.btn_connect.clicked.connect(self._toggle_connection)
        layout.addWidget(self.btn_connect)

        # Connection Status Badge
        self.lbl_led = QLabel("○ OFFLINE")
        self.lbl_led.setFixedHeight(28)
        self.lbl_led.setFixedWidth(74)
        self.lbl_led.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_led.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.lbl_led.setStyleSheet(f"""
            background-color: #202022;
            border: 1px solid #3A3A3C;
            border-radius: 4px;
            color: {Theme.COLOR_DISCONNECTED};
            font-size: 9px;
            font-weight: bold;
            padding: 3px 4px;
        """)
        layout.addWidget(self.lbl_led)

        # Background hot-plug detection timer (detects Katana when plugged in)
        self._hotplug_timer = QTimer(self)
        self._hotplug_timer.setInterval(2000)
        self._hotplug_timer.timeout.connect(self._check_hotplug)
        self._hotplug_timer.start()

        # Connect model signals
        self.model.patch_loaded.connect(self._on_model_patch_loaded)
        self.model.dirty_changed.connect(self._on_dirty_changed)
        self.model.safe_guard_status_changed.connect(self._on_safe_guard_status_changed)
        self.model.safe_guard_event.connect(self._on_safe_guard_event)
        self.midi.connected_changed.connect(self._on_midi_connected_changed)

    def _update_safe_guard_style(self, enabled: bool):
        if enabled:
            self.btn_safe_guard.setText("🛡️ SAFE: ON")
            self.btn_safe_guard.setStyleSheet("""
                QPushButton {
                    background-color: #12281B;
                    border: 1px solid #30D158;
                    color: #30D158;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1A3927;
                    border-color: #40E369;
                    color: #FFFFFF;
                }
            """)
        else:
            self.btn_safe_guard.setText("⚠️ SAFE: OFF")
            self.btn_safe_guard.setStyleSheet("""
                QPushButton {
                    background-color: #301616;
                    border: 1px solid #FF453A;
                    color: #FF453A;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #441F1F;
                    border-color: #FF6961;
                    color: #FFFFFF;
                }
            """)

    def _toggle_safe_guard(self):
        if self.model.safe_audition_enabled:
            res = QMessageBox.warning(
                self,
                "Disattivare Safe Audition?",
                "⚠️ ATTENZIONE: Disabilitando la protezione Safe Audition, i preset della community "
                "potranno inviare livelli di volume non controllati all'amplificatore (fino al 100% "
                "con boost Solo attivi).\n\n"
                "Questo potrebbe causare un'esplosione violenta di volume e danneggiare altoparlanti "
                "o l'udito se il Master dell'amplificatore è regolato alto!\n\n"
                "Sei davvero sicuro di voler disattivare la protezione Safe Audition?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if res == QMessageBox.StandardButton.Yes:
                self.model.set_safe_audition_enabled(False)
                self.lbl_safe_badge.setText("")
        else:
            self.model.set_safe_audition_enabled(True)
            self.lbl_safe_badge.setText("🛡️ Safe Audition re-engaged")

    def _on_safe_guard_status_changed(self, enabled: bool):
        self._update_safe_guard_style(enabled)

    def _on_safe_guard_event(self, msg: str, raw_val: int, safe_val: int):
        self.lbl_safe_badge.setText(msg)

    def _send_patch_to_amp(self):
        """Sends all active patch parameters to the Katana temporary edit buffer."""
        self.model.send_full_patch_to_hardware()

    def _open_new_profile_dialog(self):
        """Opens dialog to create a new profile from scratch or sonic template."""
        from katana_modern.ui.dialogs.new_profile_dialog import NewProfileDialog
        dlg = NewProfileDialog(self.model, self)
        dlg.exec()

    def _open_write_dialog(self):
        """Opens dialog to permanently burn the active patch to a hardware channel."""
        from katana_modern.ui.dialogs.write_dialog import WriteToAmpDialog
        dlg = WriteToAmpDialog(self.model, self)
        dlg.exec()

    def _open_ai_tone_dialog(self):
        """Opens Gemini AI Tone Assistant dialog."""
        from katana_modern.ui.dialogs.ai_tone_dialog import AIToneAssistantDialog
        dlg = AIToneAssistantDialog(self.model, self)
        dlg.exec()

    def _populate_ports(self):
        prev_port = self.combo_ports.currentData()
        self.combo_ports.blockSignals(True)
        self.combo_ports.clear()
        devs = self.midi.scan_devices()

        # Selection priority:
        # 1. Currently active connected port if connected
        # 2. Previous port if it was physical and still available
        # 3. First physical Katana port found
        # 4. Fallback to index 0
        active_port = self.midi._device_port if self.midi.is_connected() else None
        selected_idx = -1

        for idx, (dname, port) in enumerate(devs):
            self.combo_ports.addItem(dname, port)
            if active_port and port == active_port:
                selected_idx = idx
            elif selected_idx == -1 and prev_port and prev_port != "virtual" and port == prev_port:
                selected_idx = idx
            elif selected_idx == -1 and port != "virtual" and "KATANA" in dname.upper():
                selected_idx = idx

        if selected_idx == -1:
            selected_idx = 0

        self.combo_ports.setCurrentIndex(selected_idx)
        self.combo_ports.blockSignals(False)

    def sync_connected_port(self, port_str: str):
        """Called externally to align combo_ports with newly connected hardware port."""
        idx = self.combo_ports.findData(port_str)
        if idx >= 0:
            self.combo_ports.blockSignals(True)
            self.combo_ports.setCurrentIndex(idx)
            self.combo_ports.blockSignals(False)

    def _rescan_midi_ports(self):
        """Manual click on ↻ button."""
        self._populate_ports()
        port = self.combo_ports.currentData()
        name = self.combo_ports.currentText()
        if port and port != "virtual" and not self.midi.is_connected():
            self.midi.connect_device(port, name)

    def _check_hotplug(self):
        """Periodic background check for newly plugged Katana USB cable."""
        if not self.midi.is_connected() or self.midi.simulation_mode:
            devs = self.midi.scan_devices()
            has_real_katana = any("KATANA" in d[0].upper() and d[1] != "virtual" for d in devs)
            if has_real_katana:
                # Amp plugged in while app was running in offline or simulation mode!
                self._populate_ports()
                if not self.midi.is_connected() or self.midi.simulation_mode:
                    for dname, port in devs:
                        if "KATANA" in dname.upper() and port != "virtual":
                            self.midi.connect_device(port, dname)
                            break

    def _toggle_connection(self):
        if self.midi.is_connected() and not self.midi.simulation_mode:
            self.midi.disconnect_device()
        else:
            # Rescan to catch any freshly plugged hardware
            self._populate_ports()
            port = self.combo_ports.currentData()
            name = self.combo_ports.currentText()

            # If user has a real Katana available in the combo, pick the real hardware!
            if port == "virtual":
                for idx in range(self.combo_ports.count()):
                    p = self.combo_ports.itemData(idx)
                    if p and p != "virtual":
                        self.combo_ports.setCurrentIndex(idx)
                        port = p
                        name = self.combo_ports.itemText(idx)
                        break

            if port == "virtual":
                res = QMessageBox.question(
                    self,
                    "Katana non rilevato",
                    "⚠️ Nessun amplificatore BOSS Katana rilevato via USB.\n\n"
                    "Verifica che:\n"
                    "1. L'amplificatore Katana sia acceso.\n"
                    "2. Il cavo USB sia collegato saldamente al PC.\n\n"
                    "Vuoi continuare in modalità SIMULAZIONE OFFLINE?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if res != QMessageBox.StandardButton.Yes:
                    return

            self.midi.connect_device(port, name)

    def _on_midi_connected_changed(self, connected: bool, name: str):
        if connected:
            self.btn_connect.setText("DISCONNECT")
            port = self.midi._device_port

            # Ensure combo box is synchronized to active port
            self.sync_connected_port(port)

            if self.midi.simulation_mode or port == "virtual":
                self.btn_connect.setStyleSheet("""
                    QPushButton {
                        background-color: #2E1B0D;
                        border: 1px solid #FF9500;
                        color: #FFB340;
                        font-weight: bold;
                        padding: 2px 4px;
                    }
                """)
                self.lbl_led.setText("○ SIMULATED")
                self.lbl_led.setStyleSheet("""
                    background-color: #2E1B0D;
                    border: 1px solid #FF9500;
                    border-radius: 4px;
                    color: #FFB340;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 3px 4px;
                """)
                self.lbl_led.setToolTip("Modalità Simulazione Offline: Katana non connesso fisicamente. Premi ↻ per rilevare l'ampli.")
            else:
                self.btn_connect.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #12281B;
                        border: 1px solid {Theme.COLOR_CONNECTED};
                        color: {Theme.COLOR_CONNECTED};
                        font-weight: bold;
                        padding: 2px 4px;
                    }}
                """)
                self.lbl_led.setText("● CONNECTED")
                self.lbl_led.setStyleSheet(f"""
                    background-color: #12281B;
                    border: 1px solid {Theme.COLOR_CONNECTED};
                    border-radius: 4px;
                    color: {Theme.COLOR_CONNECTED};
                    font-size: 9px;
                    font-weight: bold;
                    padding: 3px 4px;
                """)
                self.lbl_led.setToolTip(f"Connesso all'hardware reale BOSS Katana MkII: {port}")

            self.combo_ports.setEnabled(False)
            self.btn_rescan.setEnabled(False)
        else:
            self.btn_connect.setText("CONNECT")
            self.btn_connect.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.BG_CARD};
                    border: 1px solid {Theme.BORDER_SUBTLE};
                    border-radius: 4px;
                    padding: 2px 4px;
                }}
            """)
            self.lbl_led.setText("○ OFFLINE")
            self.lbl_led.setStyleSheet(f"""
                background-color: #202022;
                border: 1px solid #3A3A3C;
                border-radius: 4px;
                color: {Theme.COLOR_DISCONNECTED};
                font-size: 9px;
                font-weight: bold;
                padding: 3px 4px;
            """)
            self.lbl_led.setToolTip("Disconnesso. Seleziona la porta e premi CONNECT.")
            self.combo_ports.setEnabled(True)
            self.btn_rescan.setEnabled(True)

    def _on_patch_name_edited(self, text: str):
        self.model.patch_name = text.strip()
        self.model.dirty_changed.emit(True)

    def _on_model_patch_loaded(self, name: str):
        self.txt_patch_name.blockSignals(True)
        self.txt_patch_name.setText(name)
        self.txt_patch_name.blockSignals(False)
        self.lbl_dirty.setText("")

    def _on_dirty_changed(self, dirty: bool):
        self.lbl_dirty.setText("● edited" if dirty else "")

    def _open_about_dialog(self):
        """Shows informative modal about Katana Forge."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Informazioni su Katana Forge")
        dlg.resize(480, 340)
        dlg.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.BG_ROOT};
                color: {Theme.TEXT_PRIMARY};
            }}
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(14)

        head_row = QHBoxLayout()
        lbl_icon = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "app_logo_64.png")
        if os.path.exists(logo_path):
            lbl_icon.setPixmap(QPixmap(logo_path))
        head_row.addWidget(lbl_icon)

        head_vbox = QVBoxLayout()
        head_vbox.setSpacing(2)
        lbl_t = QLabel("KATANA FORGE")
        lbl_t.setFont(QFont("Inter", 14, QFont.Weight.Black))
        lbl_t.setStyleSheet("color: #FFFFFF; letter-spacing: 1.5px;")
        head_vbox.addWidget(lbl_t)

        lbl_s = QLabel("MKII TONE STUDIO — v2.4")
        lbl_s.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        lbl_s.setStyleSheet(f"color: {Theme.COLOR_AMP};")
        head_vbox.addWidget(lbl_s)
        head_row.addLayout(head_vbox)
        head_row.addStretch()
        lay.addLayout(head_row)

        desc = QLabel(
            "<b>Katana Forge</b> è l'ambiente avanzato di progettazione sonora in stile DAW "
            "per amplificatori <b>Boss Katana MkII</b> (50 / 100 / Head / Artist).<br><br>"
            "• <b>7 Topologie di Routing Catena Hardware</b> con diagrammi di flusso dinamici<br>"
            "• <b>28 Sneaky Amps</b> leggendari Roland/Boss integrati nel catalogo<br>"
            "• <b>Safe Audition Guard & Level Normalizer</b> anti-esplosioni di volume<br>"
            "• <b>Gemini AI Tone Assistant</b> per generare timbri musicali da testo<br>"
            "• Sincronizzazione SysEx bidirezionale in tempo reale e scrittura permanente nei canali"
        )
        desc.setFont(QFont("Inter", 9))
        desc.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; line-height: 140%;")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        lay.addStretch()
        btn_close = QPushButton("Chiudi")
        btn_close.setFixedHeight(32)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        btn_close.clicked.connect(dlg.accept)
        lay.addWidget(btn_close)

        dlg.exec()
