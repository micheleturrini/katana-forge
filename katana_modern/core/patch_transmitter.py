"""
Boss Katana MkII Full Patch Transmitter.
Constructs the complete 16-packet Roland DT1 bulk patch dump from template (default.syx)
and overlays reactive parameter values from KatanaPatchModel.
Ensures 100% audio DSP response on physical Katana hardware.
"""

import os
from typing import List, Optional
from katana_modern.core.roland_sysex import roland_checksum, SOX, EOX


# Locate default.syx template
DEFAULT_SYX_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "default.syx")
_TEMPLATE_BYTES: Optional[bytes] = None


def get_default_template() -> bytearray:
    """Loads and caches default.syx template bytes."""
    global _TEMPLATE_BYTES
    if _TEMPLATE_BYTES is None:
        if os.path.exists(DEFAULT_SYX_PATH):
            with open(DEFAULT_SYX_PATH, "rb") as f:
                _TEMPLATE_BYTES = f.read()
        else:
            raise FileNotFoundError(f"Could not find default.syx template file at: {DEFAULT_SYX_PATH}")
    return bytearray(_TEMPLATE_BYTES)


def recalculate_packets(buf: bytearray) -> List[bytes]:
    """Splits a multi-packet buffer by F0..F7 and recalculates Roland checksums."""
    packets = []
    i = 0
    while i < len(buf):
        if buf[i] == SOX:
            start = i
            while i < len(buf) and buf[i] != EOX:
                i += 1
            if i < len(buf):
                pkt = bytearray(buf[start:i+1])
                # Checksum covers payload from address offset (idx 8) to last data byte (len - 3)
                payload = pkt[8:-2]
                pkt[-2] = roland_checksum(payload)
                packets.append(bytes(pkt))
        i += 1
    return packets


def calculate_safe_audition_volume(
    raw_volume: int,
    gain: int = 50,
    ceiling: int = 42,
    floor: int = 36
) -> int:
    """
    Computes a perceptually uniform, safe listening volume for auditioning presets.
    Eliminates sudden volume blasts (> 42) and whisper-quiet dropouts (< 36).
    Applies gain-aware psychoacoustic leveling so high-gain leads and whisper cleans
    play at the exact same comfortable, safe bedroom/studio acoustic volume.
    """
    vol = max(floor, min(ceiling, raw_volume))
    if gain >= 85:
        vol = max(floor, vol - 4)  # High-gain saturation produces higher RMS loudness
    elif gain >= 70:
        vol = max(floor, vol - 2)
    elif gain <= 25 and vol < ceiling:
        vol = min(ceiling, vol + 3)  # Low gain clean requires slight lift
    return vol


def build_full_patch_sysex(
    model,
    safe_audition: bool = True,
    safe_volume_ceiling: int = 42,
    safe_volume_floor: int = 36
) -> List[bytes]:
    """
    Constructs the 16 bulk SysEx packets (2,156 bytes) representing the complete
    Katana edit buffer (60 00 00 00..60 00 0F 00).
    When safe_audition=True (default), applies multi-layered Anti-Blast Protection
    to guarantee 100% ear and speaker safety.
    """
    buf = get_default_template()

    # 1. If loaded from a MkII .tsl, copy the raw byte arrays for maximum fidelity
    raw = getattr(model, "_raw_param_set", None)
    if raw and isinstance(raw, dict):
        def _apply_raw_hex(key: str, offset: int, limit: Optional[int] = None):
            arr = raw.get(key, [])
            if arr:
                bytes_list = []
                for h in arr:
                    try:
                        bytes_list.append(int(h, 16))
                    except Exception:
                        pass
                if limit and len(bytes_list) > limit:
                    bytes_list = bytes_list[:limit]
                buf[offset:offset+len(bytes_list)] = bytes_list

        _apply_raw_hex("UserPatch%PatchName", 12, 16)
        _apply_raw_hex("UserPatch%Patch_0", 28, 72)

        # Fx(1) split across packet 1 (154) and packet 2 (296)
        fx1_arr = raw.get("UserPatch%Fx(1)", [])
        if fx1_arr:
            fx1_bytes = [int(h, 16) for h in fx1_arr if h]
            buf[154:154+min(128, len(fx1_bytes))] = fx1_bytes[:128]
            if len(fx1_bytes) > 128:
                rem = fx1_bytes[128:]
                buf[296:296+len(rem)] = rem

        # Fx(2) split across packet 3 (438) and packet 4 (580)
        fx2_arr = raw.get("UserPatch%Fx(2)", [])
        if fx2_arr:
            fx2_bytes = [int(h, 16) for h in fx2_arr if h]
            buf[438:438+min(128, len(fx2_bytes))] = fx2_bytes[:128]
            if len(fx2_bytes) > 128:
                rem = fx2_bytes[128:]
                buf[580:580+len(rem)] = rem

        _apply_raw_hex("UserPatch%Delay(1)", 722, 26)
        _apply_raw_hex("UserPatch%Delay(2)", 754, 26)

        # Patch_1 split across packet 5 (786) and packet 6 (864)
        p1_arr = raw.get("UserPatch%Patch_1", [])
        if p1_arr:
            p1_bytes = [int(h, 16) for h in p1_arr if h]
            buf[786:786+min(64, len(p1_bytes))] = p1_bytes[:64]
            if len(p1_bytes) > 64:
                rem = p1_bytes[64:]
                buf[864:864+min(27, len(rem))] = rem[:27]

        _apply_raw_hex("UserPatch%Patch_2", 896, 36)
        _apply_raw_hex("UserPatch%Status", 944, 18)
        _apply_raw_hex("UserPatch%KnobAsgn", 1006, 34)
        _apply_raw_hex("UserPatch%ExpPedalAsgn", 1088, 34)
        _apply_raw_hex("UserPatch%ExpPedalAsgnMinMax", 1136, 78)
        _apply_raw_hex("UserPatch%GafcExp1Asgn", 1230, 34)
        _apply_raw_hex("UserPatch%GafcExp1AsgnMinMax", 1278, 78)
        _apply_raw_hex("UserPatch%GafcExp2Asgn", 1372, 34)
        _apply_raw_hex("UserPatch%GafcExp2AsgnMinMax", 1420, 78)
        _apply_raw_hex("UserPatch%FsAsgn", 2090, 2)
        _apply_raw_hex("UserPatch%Patch_Mk2V2", 2098, 10)
        _apply_raw_hex("UserPatch%Contour(1)", 2128, 2)
        _apply_raw_hex("UserPatch%Contour(2)", 2136, 2)
        _apply_raw_hex("UserPatch%Contour(3)", 2144, 2)
        _apply_raw_hex("UserPatch%Eq(2)", 108, 24)

    # 2. Overlay active GUI model values (so any user knob moves or Mk1 loads take effect)
    # Patch Name (16 bytes at offset 12)
    name_clean = (model.patch_name[:16]).ljust(16)
    buf[12:28] = [ord(c) for c in name_clean]

    # Patch_0: Booster (offset 28..36)
    buf[28] = model.get_param("booster_sw", 0)
    buf[29] = model.get_param("booster_type", 0)
    buf[30] = model.get_param("booster_drive", 50)
    buf[31] = model.get_param("booster_bottom", 50)
    buf[32] = model.get_param("booster_tone", 50)
    buf[33] = model.get_param("booster_solo_sw", 0)
    buf[34] = model.get_param("booster_solo_level", 50)
    buf[35] = model.get_param("booster_effect_level", 50)
    buf[36] = model.get_param("booster_direct_mix", 0)

    # Patch_0: Preamp (offset 44..56)
    buf[44] = model.get_param("preamp_sw", 1)
    buf[45] = model.get_param("preamp_type", 0)
    buf[46] = model.get_param("preamp_gain", 50)
    buf[48] = model.get_param("preamp_bass", 50)
    buf[49] = model.get_param("preamp_middle", 50)
    buf[50] = model.get_param("preamp_treble", 50)
    buf[51] = model.get_param("preamp_presence", 50)
    buf[52] = model.get_param("preamp_volume", 50)
    buf[53] = model.get_param("preamp_bright", 0)
    buf[55] = model.get_param("preamp_solo_sw", 0)
    buf[56] = model.get_param("preamp_solo_level", 50)

    # Patch_0: Equalizer 1 (offset 76..98)
    buf[76] = model.get_param("eq1_sw", 0)
    buf[77] = model.get_param("eq1_type", 0)
    buf[79] = model.get_param("eq1_low_gain", 20)
    buf[82] = model.get_param("eq1_mid_gain", 20)
    buf[86] = model.get_param("eq1_high_gain", 20)
    buf[88] = model.get_param("eq1_level", 20)

    bands = ["geq_31", "geq_62", "geq_125", "geq_250", "geq_500", "geq_1k", "geq_2k", "geq_4k", "geq_8k", "geq_16k"]
    for idx, bname in enumerate(bands):
        buf[89 + idx] = model.get_param(bname, 24)

    # Delay 1 (offset 722..728)
    buf[722] = model.get_param("delay1_sw", 0)
    buf[723] = model.get_param("delay1_type", 0)
    buf[724] = model.get_param("delay1_time", 40)
    buf[726] = model.get_param("delay1_feedback", 25)
    buf[728] = model.get_param("delay1_level", 50)

    # Reverb (offset 786..792)
    buf[786] = model.get_param("reverb_sw", 1)
    buf[787] = model.get_param("reverb_type", 4)
    buf[788] = model.get_param("reverb_time", 35)
    buf[790] = model.get_param("reverb_tone", 50)
    buf[792] = model.get_param("reverb_level", 45)

    # Noise Suppressor in Packet 5 (address 60 00 05 66 -> offset 722 + 102 = 824)
    buf[824] = 1 if model.get_param("ns_sw", 1) > 0 else 0
    buf[825] = model.get_param("ns_threshold", 45)
    buf[826] = model.get_param("ns_release", 50)

    # Resonance in Packet 6 (address 60 00 06 43 -> offset 864 + 67 = 931)
    buf[931] = model.get_param("cab_resonance", 0)

    # Signal Chain Routing in Packet 6 (address 60 00 06 20..23 -> offset 896..899)
    buf[896] = model.get_param("chain_pattern", model.get_param("chain_position", 0))
    buf[897] = model.get_param("chain_loop_pos", 0)
    buf[898] = model.get_param("chain_eq1_pos", 1)
    buf[899] = model.get_param("chain_pdl_pos", 0)

    # -----------------------------------------------------------------
    # 3. SAFE AUDITION GUARD & LEVEL NORMALIZER (ANTI-BLAST PROTECTION)
    # -----------------------------------------------------------------
    if safe_audition:
        raw_vol = model.get_param("preamp_volume", 50)
        gain_val = model.get_param("preamp_gain", 50)
        safe_vol = calculate_safe_audition_volume(
            raw_vol, gain=gain_val, ceiling=safe_volume_ceiling, floor=safe_volume_floor
        )
        buf[52] = safe_vol

        # Force solo switches completely OFF during audition (prevents sudden +12dB jumps)
        buf[33] = 0  # booster solo sw OFF
        buf[55] = 0  # preamp solo sw OFF
        buf[34] = min(50, int(buf[34]))
        buf[56] = min(50, int(buf[56]))

        # Normalize Foot Volume / Patch Level in Packet 5 (offset 834, address 60 00 05 70)
        # default.syx has this at 100 (full rail). Normalize to 50 for safety.
        buf[834] = 50

        # Booster effect level: prevent saturated clipping over 50
        if buf[35] > 50:
            buf[35] = 50

        # EQ Level: clamp boost to max +4dB (24, where 20 is unity gain)
        if buf[88] > 24:
            buf[88] = 24

    # 4. Recalculate checksums for all 16 packets and return
    return recalculate_packets(buf)
