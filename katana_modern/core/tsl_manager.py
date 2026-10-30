"""
Tone Studio Library (.tsl) and SysEx patch file manager.
Handles reading and writing Boss Katana MkII and MkI JSON presets and multi-patch livesets.
"""

import json
import os
from typing import Dict, Any, List, Optional
from katana_modern.core.patch_model import KatanaPatchModel


def get_tsl_patches(filepath: str) -> List[Dict[str, Any]]:
    """
    Inspects a .tsl file and returns metadata for all individual patches contained inside.
    Supports both MkII format ('data[0]') and MkI format ('patchList').
    """
    patches = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            root = json.load(f)

        # 1. Format MkII ('data' array)
        if "data" in root and root["data"] and isinstance(root["data"][0], list):
            bundle_name = root.get("name", os.path.splitext(os.path.basename(filepath))[0])
            for idx, p in enumerate(root["data"][0]):
                raw_name = p.get("paramSet", {}).get("UserPatch%PatchName", [])
                name = ""
                if raw_name:
                    chars = []
                    for h in raw_name:
                        try:
                            c = chr(int(h, 16))
                            if 32 <= ord(c) <= 126:
                                chars.append(c)
                        except Exception:
                            pass
                    name = "".join(chars).strip()

                memo_val = p.get("memo", "")
                memo_str = memo_val.get("memo", "") if isinstance(memo_val, dict) else str(memo_val or "")

                if not name:
                    name = memo_str if memo_str else (bundle_name if len(root["data"][0]) == 1 else f"Patch {idx + 1}")

                patches.append({
                    "index": idx,
                    "name": name,
                    "memo": memo_str,
                    "bundle_name": bundle_name,
                    "format": "mk2"
                })

        # 2. Format MkI ('patchList' array)
        elif "patchList" in root and isinstance(root["patchList"], list):
            bundle_name = root.get("liveSetData", {}).get("name") if isinstance(root.get("liveSetData"), dict) else None
            if not bundle_name:
                bundle_name = os.path.splitext(os.path.basename(filepath))[0]

            for idx, p in enumerate(root["patchList"]):
                name = p.get("name")
                if not name and p.get("logPatchName"):
                    name = p.get("logPatchName", "").split(":")[-1]
                if not name:
                    name = p.get("params", {}).get("patchname", "")
                if not name:
                    name = bundle_name if len(root["patchList"]) == 1 else f"Patch {idx + 1}"

                note_val = p.get("note") or p.get("memo") or ""

                patches.append({
                    "index": idx,
                    "name": str(name).strip(),
                    "memo": str(note_val).strip(),
                    "bundle_name": bundle_name,
                    "format": "mk1"
                })

    except Exception as e:
        print(f"Error inspecting TSL file {filepath}: {e}")

    return patches


def load_tsl(filepath: str, model: KatanaPatchModel, patch_index: int = 0) -> bool:
    """
    Loads a patch from a .tsl JSON preset file into the patch model.
    Supports MkII and MkI formats, and multi-patch bundle indexing.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            root = json.load(f)

        # -------------------------------------------------------------
        # 1. BOSS KATANA MkII Format ('data')
        # -------------------------------------------------------------
        if "data" in root and root["data"] and isinstance(root["data"][0], list):
            patches = root["data"][0]
            if patch_index >= len(patches):
                patch_index = 0
            patch_node = patches[patch_index]
            param_set = patch_node.get("paramSet", {})
            model._raw_param_set = param_set

            # Patch Name
            raw_name = param_set.get("UserPatch%PatchName", [])
            if raw_name:
                chars = []
                for h in raw_name:
                    try:
                        c = chr(int(h, 16))
                        if 32 <= ord(c) <= 126:
                            chars.append(c)
                    except Exception:
                        pass
                model.patch_name = "".join(chars).strip() or root.get("name", "Preset")
            else:
                model.patch_name = root.get("name", "Preset")

            # Memo / Notes
            memo_val = patch_node.get("memo", "")
            model.patch_memo = memo_val.get("memo", "") if isinstance(memo_val, dict) else str(memo_val or "")

            # Disable undo recording during bulk load
            model._history_enabled = False

            # Patch_0 (Booster, Preamp, EQ1)
            p0 = param_set.get("UserPatch%Patch_0", [])
            if len(p0) >= 29:
                # Booster
                model.set_param("booster_sw", int(p0[0], 16), send_sysex=False, record_history=False)
                model.set_param("booster_type", int(p0[1], 16), send_sysex=False, record_history=False)
                model.set_param("booster_drive", int(p0[2], 16), send_sysex=False, record_history=False)
                model.set_param("booster_bottom", int(p0[3], 16), send_sysex=False, record_history=False)
                model.set_param("booster_tone", int(p0[4], 16), send_sysex=False, record_history=False)
                model.set_param("booster_solo_sw", 0 if model.safe_audition_enabled else int(p0[5], 16), send_sysex=False, record_history=False)
                model.set_param("booster_solo_level", int(p0[6], 16), send_sysex=False, record_history=False)
                b_eff_lvl = int(p0[7], 16)
                if model.safe_audition_enabled and b_eff_lvl > 50:
                    b_eff_lvl = 50
                model.set_param("booster_effect_level", b_eff_lvl, send_sysex=False, record_history=False)
                model.set_param("booster_direct_mix", int(p0[8], 16), send_sysex=False, record_history=False)

                # Preamp
                model.set_param("preamp_sw", int(p0[16], 16), send_sysex=False, record_history=False)
                model.set_param("preamp_type", int(p0[17], 16), send_sysex=False, record_history=False)
                gain = int(p0[18], 16)
                model.set_param("preamp_gain", gain, send_sysex=False, record_history=False)
                model.set_param("preamp_bass", int(p0[20], 16), send_sysex=False, record_history=False)
                model.set_param("preamp_middle", int(p0[21], 16), send_sysex=False, record_history=False)
                model.set_param("preamp_treble", int(p0[22], 16), send_sysex=False, record_history=False)
                model.set_param("preamp_presence", int(p0[23], 16), send_sysex=False, record_history=False)

                raw_vol = int(p0[24], 16)
                model._original_preset_volume = raw_vol
                if model.safe_audition_enabled:
                    from katana_modern.core.patch_transmitter import calculate_safe_audition_volume
                    safe_vol = calculate_safe_audition_volume(
                        raw_vol,
                        gain=gain,
                        ceiling=model.safe_volume_ceiling,
                        floor=model.safe_volume_floor
                    )
                    model.set_param("preamp_volume", safe_vol, send_sysex=False, record_history=False)
                    model._is_safe_normalized = (raw_vol != safe_vol)
                    if raw_vol != safe_vol:
                        model.safe_guard_event.emit(
                            f"🛡️ Leveled: Vol {raw_vol} → {safe_vol}", raw_vol, safe_vol
                        )
                else:
                    model.set_param("preamp_volume", raw_vol, send_sysex=False, record_history=False)
                    model._is_safe_normalized = False

                model.set_param("preamp_bright", int(p0[25], 16), send_sysex=False, record_history=False)
                model.set_param("preamp_solo_sw", 0 if model.safe_audition_enabled else int(p0[27], 16), send_sysex=False, record_history=False)
                model.set_param("preamp_solo_level", int(p0[28], 16), send_sysex=False, record_history=False)

            if len(p0) >= 71:
                # EQ 1
                model.set_param("eq1_sw", int(p0[48], 16), send_sysex=False, record_history=False)
                model.set_param("eq1_type", int(p0[49], 16), send_sysex=False, record_history=False)
                model.set_param("eq1_low_gain", int(p0[51], 16), send_sysex=False, record_history=False)
                model.set_param("eq1_mid_gain", int(p0[54], 16), send_sysex=False, record_history=False)
                model.set_param("eq1_high_gain", int(p0[58], 16), send_sysex=False, record_history=False)
                model.set_param("eq1_level", int(p0[60], 16), send_sysex=False, record_history=False)
                bands = ["geq_31", "geq_62", "geq_125", "geq_250", "geq_500", "geq_1k", "geq_2k", "geq_4k", "geq_8k", "geq_16k"]
                for b_idx, bname in enumerate(bands):
                    if 61 + b_idx < len(p0):
                        model.set_param(bname, int(p0[61 + b_idx], 16), send_sysex=False, record_history=False)

            # MOD (FX1)
            fx1 = param_set.get("UserPatch%Fx(1)", [])
            if len(fx1) >= 6:
                model.set_param("mod_sw", int(fx1[0], 16), send_sysex=False, record_history=False)
                model.set_param("mod_type", int(fx1[1], 16), send_sysex=False, record_history=False)
                model.set_param("mod_param1", int(fx1[2], 16), send_sysex=False, record_history=False)
                model.set_param("mod_param2", int(fx1[3], 16), send_sysex=False, record_history=False)
                model.set_param("mod_level", int(fx1[5], 16), send_sysex=False, record_history=False)

            # FX (FX2)
            fx2 = param_set.get("UserPatch%Fx(2)", [])
            if len(fx2) >= 6:
                model.set_param("fx_sw", int(fx2[0], 16), send_sysex=False, record_history=False)
                model.set_param("fx_type", int(fx2[1], 16), send_sysex=False, record_history=False)
                model.set_param("fx_param1", int(fx2[2], 16), send_sysex=False, record_history=False)
                model.set_param("fx_param2", int(fx2[3], 16), send_sysex=False, record_history=False)
                model.set_param("fx_level", int(fx2[5], 16), send_sysex=False, record_history=False)

            # Delay 1
            dd1 = param_set.get("UserPatch%Delay(1)", [])
            if len(dd1) >= 7:
                model.set_param("delay1_sw", int(dd1[0], 16), send_sysex=False, record_history=False)
                model.set_param("delay1_type", int(dd1[1], 16), send_sysex=False, record_history=False)
                model.set_param("delay1_time", int(dd1[2], 16), send_sysex=False, record_history=False)
                model.set_param("delay1_feedback", int(dd1[4], 16), send_sysex=False, record_history=False)
                model.set_param("delay1_level", int(dd1[6], 16), send_sysex=False, record_history=False)

            # Reverb & Noise Suppressor (Patch_1)
            p1 = param_set.get("UserPatch%Patch_1", [])
            if len(p1) >= 7:
                model.set_param("reverb_sw", int(p1[0], 16), send_sysex=False, record_history=False)
                model.set_param("reverb_type", int(p1[1], 16), send_sysex=False, record_history=False)
                model.set_param("reverb_time", int(p1[2], 16), send_sysex=False, record_history=False)
                model.set_param("reverb_tone", int(p1[4], 16), send_sysex=False, record_history=False)
                model.set_param("reverb_level", int(p1[6], 16), send_sysex=False, record_history=False)

            if len(p1) >= 67:
                model.set_param("ns_sw", 1 if int(p1[64], 16) > 0 else 0, send_sysex=False, record_history=False)
                model.set_param("ns_threshold", int(p1[65], 16), send_sysex=False, record_history=False)
                model.set_param("ns_release", int(p1[66], 16), send_sysex=False, record_history=False)

            # Cabinet & Output defaults/fallbacks
            model.set_param("cab_resonance", 0, send_sysex=False, record_history=False)
            model.set_param("line_out_air_feel", 0, send_sysex=False, record_history=False)

        # -------------------------------------------------------------
        # 2. BOSS KATANA MkI Format ('patchList')
        # -------------------------------------------------------------
        elif "patchList" in root and isinstance(root["patchList"], list):
            model._raw_param_set = None
            patches = root["patchList"]
            if patch_index >= len(patches):
                patch_index = 0
            p = patches[patch_index]
            params = p.get("params", {})

            # Patch Name
            name = p.get("name")
            if not name and p.get("logPatchName"):
                name = p.get("logPatchName", "").split(":")[-1]
            if not name:
                name = params.get("patchname", "")
            if not name:
                name = root.get("liveSetData", {}).get("name") if isinstance(root.get("liveSetData"), dict) else "Preset"
            model.patch_name = str(name).strip() or "Preset"

            # Memo / Notes
            model.patch_memo = str(p.get("note") or p.get("memo") or "")

            # Disable undo recording during bulk load
            model._history_enabled = False

            # Booster (od_ds_*)
            model.set_param("booster_sw", int(params.get("od_ds_on_off", 0)), send_sysex=False, record_history=False)
            model.set_param("booster_type", int(params.get("od_ds_type", 0)), send_sysex=False, record_history=False)
            model.set_param("booster_drive", int(params.get("od_ds_drive", 50)), send_sysex=False, record_history=False)
            model.set_param("booster_bottom", int(params.get("od_ds_bottom", 50)), send_sysex=False, record_history=False)
            model.set_param("booster_tone", int(params.get("od_ds_tone", 50)), send_sysex=False, record_history=False)
            model.set_param("booster_solo_sw", 0 if model.safe_audition_enabled else int(params.get("od_ds_solo_sw", 0)), send_sysex=False, record_history=False)
            model.set_param("booster_solo_level", int(params.get("od_ds_solo_level", 50)), send_sysex=False, record_history=False)
            b_eff_lvl = int(params.get("od_ds_effect_level", 50))
            if model.safe_audition_enabled and b_eff_lvl > 50:
                b_eff_lvl = 50
            model.set_param("booster_effect_level", b_eff_lvl, send_sysex=False, record_history=False)
            model.set_param("booster_direct_mix", int(params.get("od_ds_direct_mix", 0)), send_sysex=False, record_history=False)

            # Preamp (preamp_a_*)
            model.set_param("preamp_sw", int(params.get("preamp_a_on_off", 1)), send_sysex=False, record_history=False)
            model.set_param("preamp_type", int(params.get("preamp_a_type", 0)), send_sysex=False, record_history=False)
            gain = int(params.get("preamp_a_gain", 50))
            model.set_param("preamp_gain", gain, send_sysex=False, record_history=False)
            model.set_param("preamp_bass", int(params.get("preamp_a_bass", 50)), send_sysex=False, record_history=False)
            model.set_param("preamp_middle", int(params.get("preamp_a_middle", 50)), send_sysex=False, record_history=False)
            model.set_param("preamp_treble", int(params.get("preamp_a_treble", 50)), send_sysex=False, record_history=False)
            model.set_param("preamp_presence", int(params.get("preamp_a_presence", 50)), send_sysex=False, record_history=False)

            raw_vol = int(params.get("preamp_a_level", 50))
            model._original_preset_volume = raw_vol
            if model.safe_audition_enabled:
                from katana_modern.core.patch_transmitter import calculate_safe_audition_volume
                safe_vol = calculate_safe_audition_volume(
                    raw_vol,
                    gain=gain,
                    ceiling=model.safe_volume_ceiling,
                    floor=model.safe_volume_floor
                )
                model.set_param("preamp_volume", safe_vol, send_sysex=False, record_history=False)
                model._is_safe_normalized = (raw_vol != safe_vol)
                if raw_vol != safe_vol:
                    model.safe_guard_event.emit(
                        f"🛡️ Leveled: Vol {raw_vol} → {safe_vol}", raw_vol, safe_vol
                    )
            else:
                model.set_param("preamp_volume", raw_vol, send_sysex=False, record_history=False)
                model._is_safe_normalized = False

            model.set_param("preamp_bright", int(params.get("preamp_a_bright", 0)), send_sysex=False, record_history=False)
            model.set_param("preamp_solo_sw", 0 if model.safe_audition_enabled else int(params.get("preamp_a_solo_sw", 0)), send_sysex=False, record_history=False)
            model.set_param("preamp_solo_level", int(params.get("preamp_a_solo_level", 50)), send_sysex=False, record_history=False)

            # Equalizer (eq_*)
            model.set_param("eq1_sw", int(params.get("eq_on_off", 0)), send_sysex=False, record_history=False)
            model.set_param("eq1_type", int(params.get("eq_type", 0)), send_sysex=False, record_history=False)
            model.set_param("eq1_low_gain", int(params.get("eq_low_gain", 20)), send_sysex=False, record_history=False)
            model.set_param("eq1_mid_gain", int(params.get("eq_low_mid_gain", 20)), send_sysex=False, record_history=False)
            model.set_param("eq1_high_gain", int(params.get("eq_high_gain", 20)), send_sysex=False, record_history=False)
            model.set_param("eq1_level", int(params.get("eq_level", 20)), send_sysex=False, record_history=False)

            geq_map = {
                "geq_31": "eq_geq_31hz", "geq_62": "eq_geq_62hz", "geq_125": "eq_geq_125hz",
                "geq_250": "eq_geq_250hz", "geq_500": "eq_geq_500hz", "geq_1k": "eq_geq_1khz",
                "geq_2k": "eq_geq_2khz", "geq_4k": "eq_geq_4khz", "geq_8k": "eq_geq_8khz",
                "geq_16k": "eq_geq_16khz"
            }
            for modern_k, mk1_k in geq_map.items():
                if mk1_k in params:
                    model.set_param(modern_k, int(params[mk1_k]), send_sysex=False, record_history=False)

            # Mod (fx1_*)
            model.set_param("mod_sw", int(params.get("fx1_on_off", 0)), send_sysex=False, record_history=False)
            model.set_param("mod_type", int(params.get("fx1_fx_type", 0)), send_sysex=False, record_history=False)

            # FX (fx2_*)
            model.set_param("fx_sw", int(params.get("fx2_on_off", 0)), send_sysex=False, record_history=False)
            model.set_param("fx_type", int(params.get("fx2_fx_type", 0)), send_sysex=False, record_history=False)

            # Delay (delay_*)
            model.set_param("delay1_sw", int(params.get("delay_on_off", 0)), send_sysex=False, record_history=False)
            model.set_param("delay1_type", int(params.get("delay_type", 0)), send_sysex=False, record_history=False)
            # Katana delay time in Mk1 is in ms, convert to 10ms scale if needed
            dtime = int(params.get("delay_delay_time", 400))
            model.set_param("delay1_time", max(1, min(100, dtime // 10)), send_sysex=False, record_history=False)
            model.set_param("delay1_feedback", int(params.get("delay_f_back", 25)), send_sysex=False, record_history=False)
            model.set_param("delay1_level", int(params.get("delay_effect_level", 50)), send_sysex=False, record_history=False)

            # Reverb (reverb_*)
            model.set_param("reverb_sw", int(params.get("reverb_on_off", 0)), send_sysex=False, record_history=False)
            model.set_param("reverb_type", int(params.get("reverb_type", 0)), send_sysex=False, record_history=False)
            model.set_param("reverb_time", int(params.get("reverb_time", 35)), send_sysex=False, record_history=False)
            model.set_param("reverb_level", int(params.get("reverb_effect_level", 45)), send_sysex=False, record_history=False)

            # Noise Suppressor (ns1_*)
            model.set_param("ns_sw", int(params.get("ns1_on_off", 1)), send_sysex=False, record_history=False)
            model.set_param("ns_threshold", int(params.get("ns1_threshold", 45)), send_sysex=False, record_history=False)
            model.set_param("ns_release", int(params.get("ns1_release", 50)), send_sysex=False, record_history=False)

            # Cabinet & Mic params
            if "preamp_a_sp_type" in params:
                model.set_param("cab_type", int(params["preamp_a_sp_type"]), send_sysex=False, record_history=False)
            if "preamp_a_mic_type" in params:
                model.set_param("mic_type", int(params["preamp_a_mic_type"]), send_sysex=False, record_history=False)
            if "preamp_a_mic_dis" in params:
                model.set_param("mic_distance", int(params["preamp_a_mic_dis"]), send_sysex=False, record_history=False)
            if "preamp_a_mic_pos" in params:
                model.set_param("mic_position", int(params["preamp_a_mic_pos"]), send_sysex=False, record_history=False)
        else:
            return False

        # Finalize load
        model._history_enabled = True
        model._undo_stack.clear()
        model._redo_stack.clear()
        model._dirty = False
        model.dirty_changed.emit(False)
        model.patch_loaded.emit(model.patch_name)
        return True

    except Exception as e:
        print(f"Error loading TSL file {filepath}: {e}")
        return False


def save_tsl(filepath: str, model: KatanaPatchModel) -> bool:
    """Saves the current patch model into a valid .tsl file."""
    try:
        # Build hex name array padded to 16 bytes
        name_clean = model.patch_name[:16]
        name_hex = [f"{ord(c):02X}" for c in name_clean]
        while len(name_hex) < 16:
            name_hex.append("20")  # space

        # Construct Patch_0 (72 bytes)
        p0 = ["00"] * 72
        p0[0] = f"{model.get_param('booster_sw'):02X}"
        p0[1] = f"{model.get_param('booster_type'):02X}"
        p0[2] = f"{model.get_param('booster_drive'):02X}"
        p0[3] = f"{model.get_param('booster_bottom'):02X}"
        p0[4] = f"{model.get_param('booster_tone'):02X}"
        p0[5] = f"{model.get_param('booster_solo_sw'):02X}"
        p0[6] = f"{model.get_param('booster_solo_level'):02X}"
        p0[7] = f"{model.get_param('booster_effect_level'):02X}"
        p0[8] = f"{model.get_param('booster_direct_mix'):02X}"

        p0[16] = f"{model.get_param('preamp_sw'):02X}"
        p0[17] = f"{model.get_param('preamp_type'):02X}"
        p0[18] = f"{model.get_param('preamp_gain'):02X}"
        p0[20] = f"{model.get_param('preamp_bass'):02X}"
        p0[21] = f"{model.get_param('preamp_middle'):02X}"
        p0[22] = f"{model.get_param('preamp_treble'):02X}"
        p0[23] = f"{model.get_param('preamp_presence'):02X}"
        p0[24] = f"{model.get_param('preamp_volume'):02X}"
        p0[25] = f"{model.get_param('preamp_bright'):02X}"
        p0[27] = f"{model.get_param('preamp_solo_sw'):02X}"
        p0[28] = f"{model.get_param('preamp_solo_level'):02X}"

        p0[48] = f"{model.get_param('eq1_sw'):02X}"
        p0[49] = f"{model.get_param('eq1_type'):02X}"
        p0[51] = f"{model.get_param('eq1_low_gain'):02X}"
        p0[54] = f"{model.get_param('eq1_mid_gain'):02X}"
        p0[58] = f"{model.get_param('eq1_high_gain'):02X}"
        p0[60] = f"{model.get_param('eq1_level'):02X}"

        bands = ["geq_31", "geq_62", "geq_125", "geq_250", "geq_500", "geq_1k", "geq_2k", "geq_4k", "geq_8k", "geq_16k"]
        for idx, bname in enumerate(bands):
            p0[61 + idx] = f"{model.get_param(bname):02X}"

        # Construct Patch_1 (91 bytes: Reverb + NS)
        p1 = ["00"] * 91
        p1[0] = f"{model.get_param('reverb_sw'):02X}"
        p1[1] = f"{model.get_param('reverb_type'):02X}"
        p1[2] = f"{model.get_param('reverb_time'):02X}"
        p1[4] = f"{model.get_param('reverb_tone'):02X}"
        p1[6] = f"{model.get_param('reverb_level'):02X}"

        p1[64] = "01" if model.get_param('ns_sw') > 0 else "00"
        p1[65] = f"{model.get_param('ns_threshold'):02X}"
        p1[66] = f"{model.get_param('ns_release'):02X}"

        # Delay 1 (26 bytes)
        dd1 = ["00"] * 26
        dd1[0] = f"{model.get_param('delay1_sw'):02X}"
        dd1[1] = f"{model.get_param('delay1_type'):02X}"
        dd1[2] = f"{model.get_param('delay1_time'):02X}"
        dd1[4] = f"{model.get_param('delay1_feedback'):02X}"
        dd1[6] = f"{model.get_param('delay1_level'):02X}"

        # Fx1 / Mod (128 bytes)
        fx1 = ["00"] * 128
        fx1[0] = f"{model.get_param('mod_sw'):02X}"
        fx1[1] = f"{model.get_param('mod_type'):02X}"
        fx1[2] = f"{model.get_param('mod_param1'):02X}"
        fx1[3] = f"{model.get_param('mod_param2'):02X}"
        fx1[5] = f"{model.get_param('mod_level'):02X}"

        # Fx2 (128 bytes)
        fx2 = ["00"] * 128
        fx2[0] = f"{model.get_param('fx_sw'):02X}"
        fx2[1] = f"{model.get_param('fx_type'):02X}"
        fx2[2] = f"{model.get_param('fx_param1'):02X}"
        fx2[3] = f"{model.get_param('fx_param2'):02X}"
        fx2[5] = f"{model.get_param('fx_level'):02X}"

        tsl_dict = {
            "name": model.patch_name,
            "formatRev": "0001",
            "device": "KATANA MkII",
            "data": [[
                {
                    "memo": model.patch_memo or "Saved with Katana Modern Editor",
                    "paramSet": {
                        "UserPatch%PatchName": name_hex,
                        "UserPatch%Patch_0": p0,
                        "UserPatch%Fx(1)": fx1,
                        "UserPatch%Fx(2)": fx2,
                        "UserPatch%Delay(1)": dd1,
                        "UserPatch%Patch_1": p1,
                    }
                }
            ]]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tsl_dict, f, indent=2)

        model._dirty = False
        model.dirty_changed.emit(False)
        return True

    except Exception as e:
        print(f"Error saving TSL file {filepath}: {e}")
        return False
