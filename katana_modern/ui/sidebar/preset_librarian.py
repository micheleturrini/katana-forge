"""
Collapsible Preset Librarian Sidebar (Neural DSP / Helix Style).
Manages hardware amplifier memory channels (Panel, Bank A 1-4, Bank B 1-4),
hierarchical .tsl preset browsing (bundles, single patches, and search),
instant audition SysEx sync to hardware, and Tone Studio import/export.
"""

import os
import glob
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QFrame,
    QFileDialog, QMessageBox, QGridLayout
)
from PyQt6.QtGui import QFont, QColor

from katana_modern.ui.theme import Theme
from katana_modern.core.patch_model import KatanaPatchModel
from katana_modern.core.tsl_manager import load_tsl, save_tsl, get_tsl_patches
from katana_modern.core.roland_sysex import create_dt1, ADDR_CURRENT_CHANNEL


class PresetLibrarian(QFrame):
    """
    Sidebar preset explorer and hardware channel switcher.
    """
    channel_selected = pyqtSignal(int)  # 0=Panel, 1..4=Bank A, 5..8=Bank B

    def __init__(
        self,
        patch_model: KatanaPatchModel,
        midi_backend,
        patches_root_dir: str = "saved_patches",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.model = patch_model
        self.midi_backend = midi_backend
        self.patches_root = patches_root_dir

        self.setObjectName("PanelFrame")
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header Title
        title_row = QHBoxLayout()
        lbl_title = QLabel("LIBRARIAN")
        lbl_title.setFont(QFont("Inter", 11, QFont.Weight.Bold))
        lbl_title.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; letter-spacing: 1px;")
        title_row.addWidget(lbl_title)
        title_row.addStretch()

        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setFixedSize(26, 26)
        self.btn_refresh.setFont(QFont("Inter", 11))
        self.btn_refresh.setToolTip("Rescan Presets")
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 4px;
                padding: 0px;
                color: {Theme.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                border-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        self.btn_refresh.clicked.connect(self.reload_patches)
        title_row.addWidget(self.btn_refresh)

        layout.addLayout(title_row)

        # Quick New Profile Action Tile
        self.btn_new_profile = QPushButton("+ NUOVO PROFILO")
        self.btn_new_profile.setFixedHeight(32)
        self.btn_new_profile.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.btn_new_profile.setToolTip("Crea un nuovo profilo da zero o da un template (Ctrl+N)")
        self.btn_new_profile.setStyleSheet("""
            QPushButton {
                background-color: #12281B;
                border: 1px solid #30D158;
                border-radius: 5px;
                color: #30D158;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #1A3826;
                border-color: #40E369;
                color: #FFFFFF;
            }
        """)
        self.btn_new_profile.clicked.connect(self._open_new_profile_dialog)
        layout.addWidget(self.btn_new_profile)

        # 3-step Workflow Quick Guide Banner
        box_guide = QFrame()
        box_guide.setStyleSheet("""
            background-color: #151821;
            border: 1px dashed #2A3345;
            border-radius: 5px;
            padding: 4px;
        """)
        guide_lay = QVBoxLayout(box_guide)
        guide_lay.setContentsMargins(6, 4, 6, 4)
        guide_lay.setSpacing(2)

        lbl_g_title = QLabel("GUIDA RAPIDA:")
        lbl_g_title.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_g_title.setStyleSheet("color: #FF9F0A;")
        guide_lay.addWidget(lbl_g_title)

        lbl_steps = QLabel("1. Clicca <b>+ Nuovo Profilo</b><br>2. Regola manopole & catena<br>3. Premi <b>Burn to Amp</b> per salvarlo")
        lbl_steps.setFont(QFont("Inter", 8))
        lbl_steps.setTextFormat(Qt.TextFormat.RichText)
        lbl_steps.setStyleSheet("color: #8C93A0;")
        guide_lay.addWidget(lbl_steps)
        layout.addWidget(box_guide)

        # -------------------------------------------------------------
        # 1. Hardware Channels Section (Panel, Bank A, Bank B)
        # -------------------------------------------------------------
        hw_header_row = QHBoxLayout()
        lbl_hw = QLabel("AMP HARDWARE CHANNELS")
        lbl_hw.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_hw.setStyleSheet(f"color: {Theme.TEXT_MUTED}; letter-spacing: 0.5px;")
        hw_header_row.addWidget(lbl_hw)
        hw_header_row.addStretch()

        self.lbl_active_channel_readout = QLabel("● PANEL")
        self.lbl_active_channel_readout.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.lbl_active_channel_readout.setStyleSheet("color: #FF9500;")
        hw_header_row.addWidget(self.lbl_active_channel_readout)
        layout.addLayout(hw_header_row)

        hw_frame = QFrame()
        hw_frame.setObjectName("CardFrame")
        hw_vbox = QVBoxLayout(hw_frame)
        hw_vbox.setContentsMargins(6, 6, 6, 6)
        hw_vbox.setSpacing(5)

        self.channel_buttons: List[QPushButton] = []

        # Panel Button (Wide top button with Amber accent)
        btn_panel = QPushButton("●  PANEL (Live Knobs)")
        btn_panel.setCheckable(True)
        btn_panel.setFixedHeight(26)
        btn_panel.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        btn_panel.setStyleSheet("""
            QPushButton {
                background-color: #16181E;
                border: 1px solid #282C35;
                border-radius: 4px;
                color: #8C93A0;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #20242D;
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
        btn_panel.clicked.connect(lambda: self._select_channel(0))
        hw_vbox.addWidget(btn_panel)
        self.channel_buttons.append(btn_panel)

        # Bank A Row (Green theme)
        row_a = QHBoxLayout()
        row_a.setSpacing(4)
        lbl_ba = QLabel("BANK A")
        lbl_ba.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_ba.setFixedWidth(52)
        lbl_ba.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ba.setStyleSheet("""
            background-color: #102417;
            border: 1px solid #30D158;
            border-radius: 3px;
            color: #30D158;
            padding: 2px 0px;
        """)
        row_a.addWidget(lbl_ba)

        for i in range(1, 5):
            btn = QPushButton(f"CH {i}")
            btn.setCheckable(True)
            btn.setFixedHeight(25)
            btn.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #16181E;
                    border: 1px solid #282C35;
                    border-radius: 3px;
                    color: #8C93A0;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #20242D;
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
            btn.clicked.connect(lambda checked, ch=i: self._select_channel(ch))
            row_a.addWidget(btn)
            self.channel_buttons.append(btn)
        hw_vbox.addLayout(row_a)

        # Bank B Row (Blue theme)
        row_b = QHBoxLayout()
        row_b.setSpacing(4)
        lbl_bb = QLabel("BANK B")
        lbl_bb.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_bb.setFixedWidth(52)
        lbl_bb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_bb.setStyleSheet("""
            background-color: #0D1E33;
            border: 1px solid #0A84FF;
            border-radius: 3px;
            color: #0A84FF;
            padding: 2px 0px;
        """)
        row_b.addWidget(lbl_bb)

        for i in range(5, 9):
            btn = QPushButton(f"CH {i-4}")
            btn.setCheckable(True)
            btn.setFixedHeight(25)
            btn.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #16181E;
                    border: 1px solid #282C35;
                    border-radius: 3px;
                    color: #8C93A0;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #20242D;
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
            btn.clicked.connect(lambda checked, ch=i: self._select_channel(ch))
            row_b.addWidget(btn)
            self.channel_buttons.append(btn)
        hw_vbox.addLayout(row_b)

        btn_panel.setChecked(True)
        layout.addWidget(hw_frame)

        # -------------------------------------------------------------
        # 2. Patch Search Bar
        # -------------------------------------------------------------
        lbl_lib = QLabel("PRESET LIBRARY (.TSL)")
        lbl_lib.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        lbl_lib.setStyleSheet(f"color: {Theme.TEXT_MUTED}; margin-top: 4px;")
        layout.addWidget(lbl_lib)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search presets & bundles...")
        self.txt_search.setFont(QFont("Inter", 9))
        self.txt_search.setFixedHeight(28)
        self.txt_search.textChanged.connect(self._filter_patches)
        layout.addWidget(self.txt_search)

        # -------------------------------------------------------------
        # 3. Hierarchical Preset Tree (Bundles + Single Patches)
        # -------------------------------------------------------------
        self.tree_patches = QTreeWidget()
        self.tree_patches.setHeaderHidden(True)
        self.tree_patches.setAnimated(True)
        self.tree_patches.setIndentation(14)
        self.tree_patches.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {Theme.BG_INPUT};
                border: 1px solid {Theme.BORDER_SUBTLE};
                border-radius: 6px;
                padding: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QTreeWidget::item {{
                padding: 4px 6px;
                border-radius: 4px;
                color: {Theme.TEXT_PRIMARY};
            }}
            QTreeWidget::item:hover {{
                background-color: {Theme.BG_CARD_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {Theme.BG_CARD_ACTIVE};
                border: 1px solid {Theme.COLOR_AMP};
                color: #FFFFFF;
                font-weight: bold;
            }}
        """)
        self.tree_patches.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self.tree_patches, 1)

        # -------------------------------------------------------------
        # 4. Action Buttons: Store to Amp, Import, Export
        # -------------------------------------------------------------
        self.btn_store = QPushButton("STORE TO AMP CHANNEL")
        self.btn_store.setFont(QFont("Inter", 9, QFont.Weight.Bold))
        self.btn_store.setFixedHeight(30)
        self.btn_store.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.BG_CARD};
                border: 1px solid {Theme.COLOR_AMP};
                color: {Theme.COLOR_AMP};
                font-weight: bold;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {Theme.COLOR_AMP};
                color: #FFFFFF;
            }}
        """)
        self.btn_store.clicked.connect(self._store_to_amp)
        layout.addWidget(self.btn_store)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self.btn_import = QPushButton("Import")
        self.btn_import.setFixedHeight(26)
        self.btn_import.setFont(QFont("Inter", 8))
        self.btn_import.setToolTip("Import a Tone Studio .tsl preset file")
        self.btn_import.clicked.connect(self._import_tsl)
        btn_row.addWidget(self.btn_import)

        self.btn_export = QPushButton("Export")
        self.btn_export.setFixedHeight(26)
        self.btn_export.setFont(QFont("Inter", 8))
        self.btn_export.setToolTip("Export current tone to .tsl preset file")
        self.btn_export.clicked.connect(self._export_tsl)
        btn_row.addWidget(self.btn_export)

        self.btn_ai = QPushButton("✨ AI")
        self.btn_ai.setFixedHeight(26)
        self.btn_ai.setFont(QFont("Inter", 8, QFont.Weight.Bold))
        self.btn_ai.setStyleSheet("""
            QPushButton {
                background-color: #211538;
                border: 1px solid #BF5AF2;
                color: #D67AFF;
                border-radius: 4px;
                padding: 2px 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #321F54;
                color: #FFFFFF;
            }
        """)
        self.btn_ai.setToolTip("Gemini AI Tone Assistant: genera toni per qualsiasi canzone")
        self.btn_ai.clicked.connect(self._open_ai_assistant)
        btn_row.addWidget(self.btn_ai)

        layout.addLayout(btn_row)

        self.reload_patches()

    def _store_to_amp(self):
        from katana_modern.ui.dialogs.write_dialog import WriteToAmpDialog
        dlg = WriteToAmpDialog(self.model, self)
        dlg.exec()

    def _open_ai_assistant(self):
        from katana_modern.ui.dialogs.ai_tone_dialog import AIToneAssistantDialog
        dlg = AIToneAssistantDialog(self.model, self)
        dlg.exec()

    def _select_channel(self, channel_idx: int):
        for idx, btn in enumerate(self.channel_buttons):
            btn.setChecked(idx == channel_idx)

        # Update active channel readout label with dedicated color scheme
        ch_meta = [
            ("PANEL", "#FF9500"),
            ("BANK A — CH 1", "#30D158"), ("BANK A — CH 2", "#30D158"),
            ("BANK A — CH 3", "#30D158"), ("BANK A — CH 4", "#30D158"),
            ("BANK B — CH 1", "#0A84FF"), ("BANK B — CH 2", "#0A84FF"),
            ("BANK B — CH 3", "#0A84FF"), ("BANK B — CH 4", "#0A84FF")
        ]
        if 0 <= channel_idx < len(ch_meta):
            name, color = ch_meta[channel_idx]
            self.lbl_active_channel_readout.setText(f"● {name}")
            self.lbl_active_channel_readout.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Transmit Channel Select SysEx if connected
        if self.midi_backend and self.midi_backend.is_connected():
            packet = create_dt1(ADDR_CURRENT_CHANNEL, [channel_idx])
            self.midi_backend.send_sysex(packet)

        self.channel_selected.emit(channel_idx)

    def reload_patches(self):
        """Scans saved_patches folder, parses bundles and single patches."""
        self.tree_patches.clear()
        if not os.path.exists(self.patches_root):
            return

        pattern = os.path.join(self.patches_root, "**", "*.tsl")
        files = glob.glob(pattern, recursive=True)
        files.sort(key=lambda x: os.path.basename(x).lower())

        for fpath in files:
            try:
                patch_list = get_tsl_patches(fpath)
                if not patch_list:
                    continue

                if len(patch_list) == 1:
                    # Single patch: show directly as top-level leaf
                    p = patch_list[0]
                    item = QTreeWidgetItem(self.tree_patches, [f"♪  {p['name']}"])
                    item.setData(0, Qt.ItemDataRole.UserRole, {
                        "path": fpath,
                        "index": 0,
                        "is_bundle": False,
                        "name": p['name']
                    })
                else:
                    # Multi-patch liveset/bundle: create expandable parent node
                    bundle_title = patch_list[0]["bundle_name"]
                    parent_item = QTreeWidgetItem(self.tree_patches, [f"📁  {bundle_title} ({len(patch_list)})"])
                    parent_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "path": fpath,
                        "index": -1,
                        "is_bundle": True,
                        "name": bundle_title
                    })
                    parent_item.setForeground(0, QColor(Theme.TEXT_SECONDARY))

                    for p in patch_list:
                        child = QTreeWidgetItem(parent_item, [f"♪  {p['name']}"])
                        child.setData(0, Qt.ItemDataRole.UserRole, {
                            "path": fpath,
                            "index": p["index"],
                            "is_bundle": False,
                            "name": p['name']
                        })

            except Exception as e:
                print(f"Error indexing {fpath}: {e}")

    def _filter_patches(self, text: str):
        query = text.lower().strip()
        root = self.tree_patches.invisibleRootItem()

        for i in range(root.childCount()):
            parent = root.child(i)
            data = parent.data(0, Qt.ItemDataRole.UserRole) or {}

            if data.get("is_bundle"):
                parent_match = query in data.get("name", "").lower()
                child_matches = 0

                for j in range(parent.childCount()):
                    child = parent.child(j)
                    c_data = child.data(0, Qt.ItemDataRole.UserRole) or {}
                    c_match = parent_match or (query in c_data.get("name", "").lower())
                    child.setHidden(not c_match)
                    if c_match:
                        child_matches += 1

                parent.setHidden(child_matches == 0)
                if child_matches > 0 and query:
                    parent.setExpanded(True)
                elif not query:
                    parent.setExpanded(False)

            else:
                match = query in data.get("name", "").lower()
                parent.setHidden(not match)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        if data.get("is_bundle"):
            item.setExpanded(not item.isExpanded())
            return

        # Leaf patch clicked: load and audition immediately
        fpath = data.get("path")
        idx = data.get("index", 0)

        if fpath and os.path.exists(fpath):
            success = load_tsl(fpath, self.model, patch_index=idx)
            if success:
                # Transmit full audition buffer to connected Katana hardware
                self.model.send_full_patch_to_hardware()
                for i, btn in enumerate(self.channel_buttons):
                    btn.setChecked(i == 0)

    def _open_new_profile_dialog(self):
        """Opens dialog to create a new profile from scratch or sonic template."""
        from katana_modern.ui.dialogs.new_profile_dialog import NewProfileDialog
        dlg = NewProfileDialog(self.model, self)
        dlg.exec()

    def _import_tsl(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Tone Studio Preset", self.patches_root, "Tone Studio (*.tsl);;All Files (*)"
        )
        if path:
            if load_tsl(path, self.model, patch_index=0):
                self.model.send_full_patch_to_hardware()
                self.reload_patches()
                QMessageBox.information(self, "Preset Imported", f"Successfully loaded '{self.model.patch_name}'")

    def _export_tsl(self):
        default_filename = f"{self.model.patch_name.replace(' ', '_')}.tsl"
        dest_path, _ = QFileDialog.getSaveFileName(
            self, "Export Tone Studio Preset", os.path.join(self.patches_root, default_filename),
            "Tone Studio (*.tsl);;All Files (*)"
        )
        if dest_path:
            if not dest_path.endswith(".tsl"):
                dest_path += ".tsl"
            if save_tsl(dest_path, self.model):
                self.reload_patches()
                QMessageBox.information(self, "Preset Exported", f"Preset saved to:\n{dest_path}")
