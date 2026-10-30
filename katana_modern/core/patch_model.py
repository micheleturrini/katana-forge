"""
Central Reactive Patch Data Model for Boss Katana MkII.
Manages parameter states, address mapping, bidirectional MIDI synchronization,
undo/redo history, and Tone Studio (.tsl) export/import.
"""

from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from katana_modern.core.roland_sysex import create_dt1
from katana_modern.core.amp_catalog import (
    PREAMP_MODELS, BOOSTER_MODELS, MOD_MODELS, FX_MODELS, DELAY_MODELS, REVERB_MODELS
)


class ParameterDef:
    def __init__(
        self,
        name: str,
        section: str,
        address: List[int],
        min_val: int = 0,
        max_val: int = 100,
        default_val: int = 50,
        unit: str = "",
        value_labels: Optional[Dict[int, str]] = None
    ):
        self.name = name
        self.section = section
        self.address = address
        self.min_val = min_val
        self.max_val = max_val
        self.default_val = default_val
        self.unit = unit
        self.value_labels = value_labels or {}

    def format_value(self, val: int) -> str:
        if val in self.value_labels:
            return self.value_labels[val]
        if self.unit:
            return f"{val} {self.unit}"
        return str(val)


# Full Parameter Registry for Katana MkII
PARAM_DEFS: Dict[str, ParameterDef] = {
    # --- PREAMP ---
    "preamp_sw": ParameterDef("preamp_sw", "Preamp", [0x60, 0x00, 0x00, 0x20], 0, 1, 1, "", {0: "Off", 1: "On"}),
    "preamp_type": ParameterDef("preamp_type", "Preamp", [0x60, 0x00, 0x00, 0x21], 0, 32, 0x08, "",
                                {k: v.name for k, v in PREAMP_MODELS.items()}),
    "preamp_gain": ParameterDef("preamp_gain", "Preamp", [0x60, 0x00, 0x00, 0x22], 0, 120, 50, ""),
    "preamp_bass": ParameterDef("preamp_bass", "Preamp", [0x60, 0x00, 0x00, 0x24], 0, 100, 50, ""),
    "preamp_middle": ParameterDef("preamp_middle", "Preamp", [0x60, 0x00, 0x00, 0x25], 0, 100, 50, ""),
    "preamp_treble": ParameterDef("preamp_treble", "Preamp", [0x60, 0x00, 0x00, 0x26], 0, 100, 50, ""),
    "preamp_presence": ParameterDef("preamp_presence", "Preamp", [0x60, 0x00, 0x00, 0x27], 0, 100, 50, ""),
    "preamp_volume": ParameterDef("preamp_volume", "Preamp", [0x60, 0x00, 0x00, 0x28], 0, 100, 60, ""),
    "preamp_bright": ParameterDef("preamp_bright", "Preamp", [0x60, 0x00, 0x00, 0x29], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "preamp_solo_sw": ParameterDef("preamp_solo_sw", "Preamp", [0x60, 0x00, 0x00, 0x2B], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "preamp_solo_level": ParameterDef("preamp_solo_level", "Preamp", [0x60, 0x00, 0x00, 0x2C], 0, 100, 50, ""),

    # Preamp Custom / Advanced
    "preamp_custom_bottom": ParameterDef("preamp_custom_bottom", "Preamp", [0x60, 0x00, 0x00, 0x34], 0, 100, 50, ""),
    "preamp_custom_edge": ParameterDef("preamp_custom_edge", "Preamp", [0x60, 0x00, 0x00, 0x35], 0, 100, 50, ""),
    "preamp_custom_char": ParameterDef("preamp_custom_char", "Preamp", [0x60, 0x00, 0x00, 0x3A], 0, 100, 50, ""),

    # --- BOOSTER ---
    "booster_sw": ParameterDef("booster_sw", "Booster", [0x60, 0x00, 0x00, 0x10], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "booster_type": ParameterDef("booster_type", "Booster", [0x60, 0x00, 0x00, 0x11], 0, 23, 0x0A, "", BOOSTER_MODELS),
    "booster_drive": ParameterDef("booster_drive", "Booster", [0x60, 0x00, 0x00, 0x12], 0, 120, 50, ""),
    "booster_bottom": ParameterDef("booster_bottom", "Booster", [0x60, 0x00, 0x00, 0x13], 0, 100, 50, ""),
    "booster_tone": ParameterDef("booster_tone", "Booster", [0x60, 0x00, 0x00, 0x14], 0, 100, 50, ""),
    "booster_solo_sw": ParameterDef("booster_solo_sw", "Booster", [0x60, 0x00, 0x00, 0x15], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "booster_solo_level": ParameterDef("booster_solo_level", "Booster", [0x60, 0x00, 0x00, 0x16], 0, 100, 50, ""),
    "booster_effect_level": ParameterDef("booster_effect_level", "Booster", [0x60, 0x00, 0x00, 0x17], 0, 100, 50, ""),
    "booster_direct_mix": ParameterDef("booster_direct_mix", "Booster", [0x60, 0x00, 0x00, 0x18], 0, 100, 0, ""),

    # --- MOD (FX1) ---
    "mod_sw": ParameterDef("mod_sw", "Mod", [0x60, 0x00, 0x01, 0x00], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "mod_type": ParameterDef("mod_type", "Mod", [0x60, 0x00, 0x01, 0x01], 0, 40, 0x1D, "", MOD_MODELS),
    "mod_param1": ParameterDef("mod_param1", "Mod", [0x60, 0x00, 0x01, 0x02], 0, 100, 45, ""),
    "mod_param2": ParameterDef("mod_param2", "Mod", [0x60, 0x00, 0x01, 0x03], 0, 100, 55, ""),
    "mod_param3": ParameterDef("mod_param3", "Mod", [0x60, 0x00, 0x01, 0x04], 0, 100, 50, ""),
    "mod_level": ParameterDef("mod_level", "Mod", [0x60, 0x00, 0x01, 0x05], 0, 100, 70, ""),

    # --- FX (FX2) ---
    "fx_sw": ParameterDef("fx_sw", "FX", [0x60, 0x00, 0x03, 0x00], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "fx_type": ParameterDef("fx_type", "FX", [0x60, 0x00, 0x03, 0x01], 0, 40, 0x03, "", FX_MODELS),
    "fx_param1": ParameterDef("fx_param1", "FX", [0x60, 0x00, 0x03, 0x02], 0, 100, 50, ""),
    "fx_param2": ParameterDef("fx_param2", "FX", [0x60, 0x00, 0x03, 0x03], 0, 100, 50, ""),
    "fx_level": ParameterDef("fx_level", "FX", [0x60, 0x00, 0x03, 0x05], 0, 100, 75, ""),

    # --- DELAY 1 ---
    "delay1_sw": ParameterDef("delay1_sw", "Delay", [0x60, 0x00, 0x05, 0x00], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "delay1_type": ParameterDef("delay1_type", "Delay", [0x60, 0x00, 0x05, 0x01], 0, 10, 0x00, "", DELAY_MODELS),
    "delay1_time": ParameterDef("delay1_time", "Delay", [0x60, 0x00, 0x05, 0x02], 1, 100, 40, "ms*10"),
    "delay1_feedback": ParameterDef("delay1_feedback", "Delay", [0x60, 0x00, 0x05, 0x04], 0, 100, 25, ""),
    "delay1_level": ParameterDef("delay1_level", "Delay", [0x60, 0x00, 0x05, 0x06], 0, 100, 50, ""),

    # --- REVERB ---
    "reverb_sw": ParameterDef("reverb_sw", "Reverb", [0x60, 0x00, 0x05, 0x40], 0, 1, 1, "", {0: "Off", 1: "On"}),
    "reverb_type": ParameterDef("reverb_type", "Reverb", [0x60, 0x00, 0x05, 0x41], 0, 6, 0x04, "", REVERB_MODELS),
    "reverb_time": ParameterDef("reverb_time", "Reverb", [0x60, 0x00, 0x05, 0x42], 0, 100, 35, ""),
    "reverb_tone": ParameterDef("reverb_tone", "Reverb", [0x60, 0x00, 0x05, 0x44], 0, 100, 50, ""),
    "reverb_level": ParameterDef("reverb_level", "Reverb", [0x60, 0x00, 0x05, 0x46], 0, 100, 45, ""),

    # --- EQUALIZER 1 (Parametric / Graphic) ---
    "eq1_sw": ParameterDef("eq1_sw", "EQ", [0x60, 0x00, 0x00, 0x40], 0, 1, 0, "", {0: "Off", 1: "On"}),
    "eq1_type": ParameterDef("eq1_type", "EQ", [0x60, 0x00, 0x00, 0x41], 0, 1, 0, "", {0: "Parametric", 1: "Graphic"}),
    "eq1_low_gain": ParameterDef("eq1_low_gain", "EQ", [0x60, 0x00, 0x00, 0x43], 0, 40, 20, "dB"),
    "eq1_mid_gain": ParameterDef("eq1_mid_gain", "EQ", [0x60, 0x00, 0x00, 0x46], 0, 40, 20, "dB"),
    "eq1_high_gain": ParameterDef("eq1_high_gain", "EQ", [0x60, 0x00, 0x00, 0x4A], 0, 40, 20, "dB"),
    "eq1_level": ParameterDef("eq1_level", "EQ", [0x60, 0x00, 0x00, 0x4C], 0, 40, 20, "dB"),

    # Graphic EQ 10 Bands (31Hz..16kHz)
    "geq_31": ParameterDef("geq_31", "EQ", [0x60, 0x00, 0x00, 0x4D], 0, 48, 24, "dB"),
    "geq_62": ParameterDef("geq_62", "EQ", [0x60, 0x00, 0x00, 0x4E], 0, 48, 24, "dB"),
    "geq_125": ParameterDef("geq_125", "EQ", [0x60, 0x00, 0x00, 0x4F], 0, 48, 24, "dB"),
    "geq_250": ParameterDef("geq_250", "EQ", [0x60, 0x00, 0x00, 0x50], 0, 48, 24, "dB"),
    "geq_500": ParameterDef("geq_500", "EQ", [0x60, 0x00, 0x00, 0x51], 0, 48, 24, "dB"),
    "geq_1k": ParameterDef("geq_1k", "EQ", [0x60, 0x00, 0x00, 0x52], 0, 48, 24, "dB"),
    "geq_2k": ParameterDef("geq_2k", "EQ", [0x60, 0x00, 0x00, 0x53], 0, 48, 24, "dB"),
    "geq_4k": ParameterDef("geq_4k", "EQ", [0x60, 0x00, 0x00, 0x54], 0, 48, 24, "dB"),
    "geq_8k": ParameterDef("geq_8k", "EQ", [0x60, 0x00, 0x00, 0x55], 0, 48, 24, "dB"),
    "geq_16k": ParameterDef("geq_16k", "EQ", [0x60, 0x00, 0x00, 0x56], 0, 48, 24, "dB"),

    # --- NOISE SUPPRESSOR ---
    "ns_sw": ParameterDef("ns_sw", "NS", [0x60, 0x00, 0x05, 0x60], 0, 1, 1, "", {0: "Off", 1: "On"}),
    "ns_threshold": ParameterDef("ns_threshold", "NS", [0x60, 0x00, 0x05, 0x61], 0, 100, 45, ""),
    "ns_release": ParameterDef("ns_release", "NS", [0x60, 0x00, 0x05, 0x62], 0, 100, 50, ""),

    # --- CABINET & OUTPUT (Resonance, Line Out Air Feel, Contour, Mic, Master Level) ---
    "cab_resonance": ParameterDef("cab_resonance", "Cabinet", [0x60, 0x00, 0x06, 0x43], 0, 2, 0, "",
                                  {0: "Vintage", 1: "Modern", 2: "Deep"}),
    "line_out_air_feel": ParameterDef("line_out_air_feel", "Cabinet", [0x00, 0x00, 0x00, 0x29], 0, 2, 0, "",
                                      {0: "Rec", 1: "Live", 2: "Blend"}),
    "contour_sw": ParameterDef("contour_sw", "Cabinet", [0x60, 0x00, 0x06, 0x16], 0, 1, 0, "",
                               {0: "Off", 1: "On"}),
    "contour_type": ParameterDef("contour_type", "Cabinet", [0x60, 0x00, 0x06, 0x17], 0, 2, 0, "",
                                 {0: "Type 1", 1: "Type 2", 2: "Type 3"}),
    "master_level": ParameterDef("master_level", "Master", [0x60, 0x00, 0x05, 0x63], 0, 100, 50, ""),
    "cab_type": ParameterDef("cab_type", "Cabinet", [0x60, 0x00, 0x06, 0x44], 0, 3, 0, "",
                             {0: "1x12 Katana Open", 1: "2x12 Katana Closed", 2: "4x12 British Stack", 3: "4x12 American V30"}),
    "mic_type": ParameterDef("mic_type", "Cabinet", [0x00, 0x00, 0x01, 0x12], 0, 3, 0, "",
                             {0: "Dynamic 57", 1: "Dynamic 421", 2: "Condenser 451", 3: "Ribbon 121"}),
    "mic_distance": ParameterDef("mic_distance", "Cabinet", [0x00, 0x00, 0x01, 0x13], 0, 100, 50, ""),
    "mic_position": ParameterDef("mic_position", "Cabinet", [0x00, 0x00, 0x01, 0x14], 0, 100, 50, ""),

    # --- MASTER / CHAIN ---
    "foot_volume": ParameterDef("foot_volume", "Master", [0x60, 0x00, 0x05, 0x70], 0, 100, 100, ""),
    "chain_pattern": ParameterDef("chain_pattern", "Master", [0x60, 0x00, 0x06, 0x20], 0, 6, 0, "",
                                  {
                                      0: "Chain 1: Standard (Boost ➔ Amp ➔ Mod ➔ FX)",
                                      1: "Chain 2-1: Pre-Amp FX (Boost ➔ FX ➔ Amp ➔ Mod)",
                                      2: "Chain 3-1: Vintage Board (Boost ➔ Mod ➔ FX ➔ Amp)",
                                      3: "Chain 4-1: 70s Front Delay (Boost ➔ Mod ➔ FX ➔ Delay ➔ Amp)",
                                      4: "Chain 2-2: Mod-First Drive (Mod ➔ Boost ➔ Amp ➔ FX)",
                                      5: "Chain 3-2: Front-End Complete (Mod ➔ Boost ➔ FX ➔ Amp)",
                                      6: "Chain 4-2: Full Raw Front-End (Mod ➔ Boost ➔ FX ➔ Delay ➔ Amp)"
                                  }),
    "chain_position": ParameterDef("chain_position", "Master", [0x60, 0x00, 0x06, 0x20], 0, 6, 0, "",
                                   {0: "Chain 1", 1: "Chain 2-1", 2: "Chain 3-1", 3: "Chain 4-1", 4: "Chain 2-2", 5: "Chain 3-2", 6: "Chain 4-2"}),
    "chain_eq1_pos": ParameterDef("chain_eq1_pos", "Master", [0x60, 0x00, 0x06, 0x22], 0, 1, 1, "",
                                  {0: "Amp In (Pre-Amp)", 1: "Amp Out (Post-Amp)"}),
    "chain_loop_pos": ParameterDef("chain_loop_pos", "Master", [0x60, 0x00, 0x06, 0x21], 0, 1, 0, "",
                                   {0: "Post Amp", 1: "Post Reverb"}),
    "chain_pdl_pos": ParameterDef("chain_pdl_pos", "Master", [0x60, 0x00, 0x06, 0x23], 0, 1, 0, "",
                                  {0: "Guitar Input", 1: "Post Amp"}),
}

# Reverse lookup: address bytes tuple -> param name
ADDR_TO_PARAM = {tuple(p.address): name for name, p in PARAM_DEFS.items()}


class KatanaPatchModel(QObject):
    """
    Central reactive model storing the active preset state and handling undo/redo.
    """
    parameter_changed = pyqtSignal(str, int, str)   # param_name, new_val, display_str
    patch_loaded = pyqtSignal(str)                  # patch_name
    dirty_changed = pyqtSignal(bool)                # has_unsaved_changes
    safe_guard_status_changed = pyqtSignal(bool)    # safe audition enabled/disabled
    safe_guard_event = pyqtSignal(str, int, int)    # notification message, raw_val, safe_val

    def __init__(self, midi_backend=None, parent=None):
        super().__init__(parent)
        self.midi_backend = midi_backend
        self.patch_name = "New Preset"
        self.patch_memo = ""
        self._values: Dict[str, int] = {}
        self._dirty = False

        # Safe Audition & Loudness Normalizer settings
        self.safe_audition_enabled: bool = True
        self.safe_volume_ceiling: int = 42
        self.safe_volume_floor: int = 36
        self._original_preset_volume: int = 50
        self._is_safe_normalized: bool = False

        # Undo / Redo stacks
        self._undo_stack: List[Tuple[str, int, int]] = []
        self._redo_stack: List[Tuple[str, int, int]] = []
        self._history_enabled = True

        # Initialize defaults
        self.reset_to_defaults()

        # Connect to MIDI backend incoming SysEx
        if self.midi_backend:
            self.midi_backend.sysex_received.connect(self._handle_incoming_sysex)

    @property
    def is_dirty(self) -> bool:
        """Returns True if there are unsaved modifications."""
        return self._dirty

    def set_safe_audition_enabled(self, enabled: bool):
        self.safe_audition_enabled = enabled
        self.safe_guard_status_changed.emit(enabled)

    def reset_to_defaults(self):
        """Reset all parameters to clean default states."""
        self._history_enabled = False
        self.patch_name = "Clean Katana"
        for name, p in PARAM_DEFS.items():
            self.set_param(name, p.default_val, send_sysex=False)
        self._history_enabled = True
        self._dirty = False
        self.dirty_changed.emit(False)
        self.patch_loaded.emit(self.patch_name)

    def get_active_chain_blocks(self) -> List[str]:
        """Returns the module block IDs in order for the current routing topology."""
        from katana_modern.core.amp_catalog import CHAIN_ROUTES
        cid = self.get_param("chain_pattern", self.get_param("chain_position", 0))
        cid = max(0, min(6, cid))
        route = CHAIN_ROUTES[cid] if cid < len(CHAIN_ROUTES) else CHAIN_ROUTES[0]
        blocks = list(route["blocks"])

        # Check EQ position (0 = Pre-Amp/Amp In, 1 = Post-Amp/Amp Out)
        eq_pos = self.get_param("chain_eq1_pos", 1)
        if "eq" in blocks and "amp" in blocks:
            blocks.remove("eq")
            amp_idx = blocks.index("amp")
            if eq_pos == 0:
                blocks.insert(amp_idx, "eq")       # Place EQ right before Amp
            else:
                blocks.insert(amp_idx + 1, "eq")   # Place EQ right after Amp

        return blocks

    def create_new_profile(self, name: str, template: str = "clean") -> bool:
        """
        Initializes a brand new profile with a curated sound template and sets it active.
        Sends the new profile to Katana hardware immediately.
        """
        self._history_enabled = False
        self.patch_name = name.strip() or "Nuovo Profilo"

        # 1. Reset everything to baseline neutral defaults
        for pname, pdef in PARAM_DEFS.items():
            self._values[pname] = pdef.default_val

        # 2. Apply template specifics
        if template == "crunch":
            # Plexi / Blues warm crunch
            self._values.update({
                "preamp_sw": 1,
                "preamp_type": 0x09,  # Crunch
                "preamp_gain": 55,
                "preamp_bass": 48,
                "preamp_middle": 56,
                "preamp_treble": 58,
                "preamp_presence": 50,
                "preamp_volume": 40,
                "booster_sw": 1,
                "booster_type": 0x04,  # Natural OD
                "booster_drive": 38,
                "booster_tone": 50,
                "booster_effect_level": 50,
                "reverb_sw": 1,
                "reverb_type": 0x01,  # Spring
                "reverb_time": 30,
                "reverb_level": 30,
                "ns_sw": 1,
                "ns_threshold": 45,
                "chain_pattern": 0,
            })
        elif template == "lead":
            # High gain lead
            self._values.update({
                "preamp_sw": 1,
                "preamp_type": 0x0B,  # Lead / Brown
                "preamp_gain": 60,
                "preamp_bass": 46,
                "preamp_middle": 58,
                "preamp_treble": 52,
                "preamp_presence": 55,
                "preamp_volume": 38,
                "booster_sw": 1,
                "booster_type": 0x0A,  # T-Scream
                "booster_drive": 22,
                "booster_tone": 55,
                "booster_effect_level": 55,
                "delay1_sw": 1,
                "delay1_type": 0x01,  # Analog Delay
                "delay1_time": 42,
                "delay1_feedback": 30,
                "delay1_level": 35,
                "reverb_sw": 1,
                "reverb_type": 0x04,  # Plate
                "reverb_time": 35,
                "reverb_level": 35,
                "ns_sw": 1,
                "ns_threshold": 55,
                "chain_pattern": 0,
            })
        elif template == "ambient":
            # Ambient dream clean
            self._values.update({
                "preamp_sw": 1,
                "preamp_type": 0x08,  # Clean Katana
                "preamp_gain": 32,
                "preamp_bass": 50,
                "preamp_middle": 45,
                "preamp_treble": 62,
                "preamp_presence": 55,
                "preamp_volume": 40,
                "mod_sw": 1,
                "mod_type": 0x00,  # Chorus
                "mod_rate": 35,
                "mod_depth": 65,
                "delay1_sw": 1,
                "delay1_type": 0x04,  # Modulate Delay
                "delay1_time": 52,
                "delay1_feedback": 45,
                "delay1_level": 45,
                "reverb_sw": 1,
                "reverb_type": 0x04,  # Plate
                "reverb_time": 55,
                "reverb_level": 50,
                "ns_sw": 1,
                "ns_threshold": 35,
                "chain_pattern": 0,
            })
        elif template == "acoustic":
            # Acoustic simulator
            self._values.update({
                "preamp_sw": 1,
                "preamp_type": 0x07,  # Acoustic
                "preamp_gain": 35,
                "preamp_bass": 45,
                "preamp_middle": 52,
                "preamp_treble": 58,
                "preamp_presence": 60,
                "preamp_volume": 40,
                "reverb_sw": 1,
                "reverb_type": 0x02,  # Hall
                "reverb_time": 32,
                "reverb_level": 32,
                "chain_pattern": 0,
            })
        elif template == "blank":
            # Everything bypassed / flat
            self._values.update({
                "preamp_sw": 1,
                "preamp_type": 0x08,
                "preamp_gain": 50,
                "preamp_bass": 50,
                "preamp_middle": 50,
                "preamp_treble": 50,
                "preamp_presence": 50,
                "preamp_volume": 40,
                "booster_sw": 0,
                "mod_sw": 0,
                "fx_sw": 0,
                "delay1_sw": 0,
                "reverb_sw": 0,
                "eq1_sw": 0,
                "chain_pattern": 0,
            })
        elif template == "duplicate":
            # Keep existing parameters, only change name
            pass
        else: # "clean" default
            self._values.update({
                "preamp_sw": 1,
                "preamp_type": 0x08,  # Clean Katana
                "preamp_gain": 38,
                "preamp_bass": 50,
                "preamp_middle": 50,
                "preamp_treble": 55,
                "preamp_presence": 50,
                "preamp_volume": 40,
                "booster_sw": 0,
                "mod_sw": 0,
                "fx_sw": 0,
                "delay1_sw": 0,
                "reverb_sw": 1,
                "reverb_type": 0x04,  # Plate
                "reverb_time": 35,
                "reverb_level": 30,
                "ns_sw": 1,
                "ns_threshold": 40,
                "chain_pattern": 0,
            })

        # Ensure safe audition volume ceiling
        if self.safe_audition_enabled:
            vol = self._values.get("preamp_volume", 40)
            if vol > self.safe_volume_ceiling:
                self._values["preamp_volume"] = self.safe_volume_ceiling

        self._history_enabled = True
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._dirty = True
        self.dirty_changed.emit(True)
        self.patch_loaded.emit(self.patch_name)

        # Send immediately to Katana hardware so user can audition
        self.send_full_patch_to_hardware()
        return True

    def get_param(self, name: str, default: Optional[int] = None) -> int:
        if name in self._values:
            return self._values[name]
        if name in PARAM_DEFS:
            return PARAM_DEFS[name].default_val
        return default if default is not None else 0

    def get_formatted_param(self, name: str) -> str:
        val = self.get_param(name)
        if name in PARAM_DEFS:
            return PARAM_DEFS[name].format_value(val)
        return str(val)

    def set_param(self, name: str, value: int, send_sysex: bool = True, record_history: bool = True):
        if name not in PARAM_DEFS:
            return

        param_def = PARAM_DEFS[name]
        clamped_val = max(param_def.min_val, min(param_def.max_val, value))

        # Safe Audition Guard: protect against manual volume slider slips > 55
        if name == "preamp_volume" and self.safe_audition_enabled:
            if clamped_val > 55:
                clamped_val = 55
                self.safe_guard_event.emit("🛡️ Safe Audition: Capped manual volume at 55 for ear safety", value, 55)

        old_val = self._values.get(name, param_def.default_val)

        if old_val == clamped_val and name in self._values:
            return

        # Record history for undo/redo
        if self._history_enabled and record_history:
            self._undo_stack.append((name, old_val, clamped_val))
            self._redo_stack.clear()

        self._values[name] = clamped_val
        self._dirty = True
        self.dirty_changed.emit(True)

        display_str = param_def.format_value(clamped_val)
        self.parameter_changed.emit(name, clamped_val, display_str)

        # Transmit SysEx to Katana hardware
        if send_sysex and self.midi_backend and self.midi_backend.is_connected():
            packet = create_dt1(param_def.address, [clamped_val])
            self.midi_backend.send_sysex(packet)

    def undo(self):
        if not self._undo_stack:
            return
        name, old_val, new_val = self._undo_stack.pop()
        self._redo_stack.append((name, old_val, new_val))
        self.set_param(name, old_val, send_sysex=True, record_history=False)

    def redo(self):
        if not self._redo_stack:
            return
        name, old_val, new_val = self._redo_stack.pop()
        self._undo_stack.append((name, old_val, new_val))
        self.set_param(name, new_val, send_sysex=True, record_history=False)

    def send_full_patch_to_hardware(self):
        """
        Sends the complete patch to Katana hardware for instant audio audition.
        Crucial: Unlocks Editor Mode, switches active channel to PANEL, and sends
        the authentic 16-packet bulk patch data so the physical Katana immediately
        updates its DSP audio output!
        """
        if not self.midi_backend or not self.midi_backend.is_connected():
            return

        # 1. Clear backlog of any previous rapid patch switches
        if hasattr(self.midi_backend, 'clear_queue'):
            self.midi_backend.clear_queue()

        # 2. Crucial: Send Editor Mode ON (7F 00 00 01 = 01)
        # Without this, the physical Katana DSP ignores temporary buffer changes!
        from katana_modern.core.roland_sysex import create_editor_handshake, create_dt1, ADDR_CURRENT_CHANNEL
        self.midi_backend.send_sysex(create_editor_handshake())

        # 3. Crucial: Switch active channel to PANEL (Channel 0: 00 01 00 00 = 00)
        # If the amp is currently parked on a stored channel (Ch 1..4), it plays flash!
        # Switching to PANEL engages the temporary edit buffer so the new tone is heard!
        self.midi_backend.send_sysex(create_dt1(ADDR_CURRENT_CHANNEL, [0x00]))

        # 4. Build and send the 16 bulk patch packets (the full Katana patch buffer)
        try:
            from katana_modern.core.patch_transmitter import build_full_patch_sysex
            packets = build_full_patch_sysex(
                self,
                safe_audition=self.safe_audition_enabled,
                safe_volume_ceiling=self.safe_volume_ceiling,
                safe_volume_floor=self.safe_volume_floor
            )
            for pkt in packets:
                self.midi_backend.send_sysex(pkt)
        except Exception as e:
            print(f"Error sending bulk patch: {e}")
            # Fallback to individual parameters
            clean_name = (self.patch_name[:16]).ljust(16)
            name_bytes = [ord(c) for c in clean_name]
            for idx, b in enumerate(name_bytes):
                pkt = create_dt1([0x60, 0x00, 0x00, idx], [b])
                self.midi_backend.send_sysex(pkt)

            for pname, pdef in PARAM_DEFS.items():
                val = self.get_param(pname)
                if pname == "preamp_volume" and self.safe_audition_enabled and val > self.safe_volume_ceiling:
                    val = self.safe_volume_ceiling
                pkt = create_dt1(pdef.address, [val])
                self.midi_backend.send_sysex(pkt)

    def write_to_hardware_channel(
        self,
        channel_idx: int,
        name: Optional[str] = None,
        safe_normalize: bool = True
    ) -> bool:
        """
        Permanently commits the active patch to the specified Katana hardware channel.
        channel_idx: 0 = Panel, 1..4 = Bank A (Ch 1..4), 5..8 = Bank B (Ch 1..4)
        safe_normalize: If True, writes leveled safe volume so the amp never blasts on channel switch.
        """
        if name:
            self.patch_name = name
            self.patch_loaded.emit(self.patch_name)

        if not self.midi_backend or not self.midi_backend.is_connected():
            return False

        # Step 1: Ensure Editor Mode is ON
        from katana_modern.core.roland_sysex import create_editor_handshake, create_dt1, roland_checksum, ADDR_CURRENT_CHANNEL
        self.midi_backend.send_sysex(create_editor_handshake())

        # Step 2: Flush all parameters to temporary buffer via bulk packets
        try:
            from katana_modern.core.patch_transmitter import build_full_patch_sysex
            packets = build_full_patch_sysex(
                self,
                safe_audition=safe_normalize,
                safe_volume_ceiling=self.safe_volume_ceiling,
                safe_volume_floor=self.safe_volume_floor
            )
            for pkt in packets:
                self.midi_backend.send_sysex(pkt)
        except Exception:
            self.send_full_patch_to_hardware()

        # Step 3: Send Roland Flash Memory Commit SysEx: 7F 00 01 04 00 [channel_idx]
        payload = [0x7F, 0x00, 0x01, 0x04, 0x00, channel_idx]
        chk = roland_checksum(payload)
        commit_packet = bytes([0xF0, 0x41, 0x00, 0x00, 0x00, 0x00, 0x33, 0x12] + payload + [chk, 0xF7])
        self.midi_backend.send_sysex(commit_packet)

        # Step 4: Switch to that channel so the amp activates it immediately
        ch_pkt = create_dt1(ADDR_CURRENT_CHANNEL, [channel_idx])
        self.midi_backend.send_sysex(ch_pkt)

        self._dirty = False
        self.dirty_changed.emit(False)
        return True

    def _handle_incoming_sysex(self, packet: bytes):
        """Called when a SysEx packet is received from the Katana amp."""
        from katana_modern.core.roland_sysex import parse_sysex
        parsed = parse_sysex(packet)
        if not parsed:
            return

        cmd_type, addr, data, valid_chk = parsed
        if not valid_chk or cmd_type != 'DT1' or not data:
            return

        addr_tuple = tuple(addr)
        if addr_tuple in ADDR_TO_PARAM:
            param_name = ADDR_TO_PARAM[addr_tuple]
            new_val = data[0]
            # Update local value without re-sending SysEx to avoid echo loop
            self.set_param(param_name, new_val, send_sysex=False, record_history=False)
