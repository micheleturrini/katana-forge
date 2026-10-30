"""
AI Preset Engine for Boss Katana MkII.
Provides standardized JSON tone schema, Gemini prompt generation,
and robust JSON parsing with fuzzy model matching and Safe Audition leveling.
"""

import json
import re
from typing import Dict, Any, Tuple, Optional, List

from katana_modern.core.amp_catalog import (
    PREAMP_MODELS, BOOSTER_MODELS, MOD_MODELS, DELAY_MODELS, REVERB_MODELS
)
from katana_modern.core.patch_transmitter import calculate_safe_audition_volume


# -------------------------------------------------------------
# 1. Fuzzy Matching Helpers
# -------------------------------------------------------------
def match_preamp_type(name: str) -> int:
    name_clean = name.strip().lower()

    # 1. Exact match first across all models
    for mid, info in PREAMP_MODELS.items():
        if info.name.lower() == name_clean:
            return mid

    # 2. Prioritize specific boutique/sneaky amp keywords
    if "twin" in name_clean:
        return 0x09
    if "deluxe" in name_clean:
        return 0x0C
    if "pro crunch" in name_clean:
        return 0x0A
    if "plexi" in name_clean or "1959" in name_clean or "jmp" in name_clean:
        return 0x13
    if "rectifier" in name_clean or "r-fier" in name_clean or "recto" in name_clean:
        return 0x15
    if "boogie" in name_clean or "mesa" in name_clean or "bg" in name_clean:
        return 0x10
    if "ac30" in name_clean or "vox" in name_clean or "vo drive" in name_clean or "vo lead" in name_clean:
        return 0x0D
    if "matchless" in name_clean or "match" in name_clean:
        return 0x0F
    if "soldano" in name_clean or "slo" in name_clean or "higain stack" in name_clean:
        return 0x04

    # 3. Standard core types
    if "brown" in name_clean:
        return 0x17
    if "lead" in name_clean:
        return 0x18
    if "crunch" in name_clean:
        return 0x0B
    if "clean" in name_clean:
        return 0x08
    if "acoustic" in name_clean:
        return 0x01

    return 0x08  # Default Clean


def match_booster_type(name: str) -> int:
    name_clean = name.strip().lower()
    for mid, title in BOOSTER_MODELS.items():
        if name_clean in title.lower():
            return mid

    if "muff" in name_clean or "pi" in name_clean:
        return 0x14
    if "blues" in name_clean or "bd-2" in name_clean:
        return 0x0A
    if "tube" in name_clean or "screamer" in name_clean or "ts9" in name_clean or "ts808" in name_clean or "ts-9" in name_clean:
        return 0x0C
    if "klon" in name_clean or "centa" in name_clean or "centaur" in name_clean:
        return 0x17
    if "rat" in name_clean:
        return 0x0F
    if "fuzz" in name_clean:
        return 0x13
    if "metal zone" in name_clean or "mt-2" in name_clean:
        return 0x12
    if "distortion" in name_clean or "ds-1" in name_clean:
        return 0x0E
    if "clean boost" in name_clean:
        return 0x01
    if "treble" in name_clean:
        return 0x02

    return 0x0A  # Default Blues Driver


def match_delay_type(name: str) -> int:
    name_clean = name.strip().lower()
    for mid, title in DELAY_MODELS.items():
        if name_clean in title.lower():
            return mid

    if "analog" in name_clean or "dm-2" in name_clean:
        return 0x07
    if "tape" in name_clean or "space echo" in name_clean or "re-201" in name_clean:
        return 0x08
    if "reverse" in name_clean:
        return 0x06
    if "sde" in name_clean or "3000" in name_clean:
        return 0x0A
    if "modulat" in name_clean:
        return 0x09

    return 0x00  # Default Digital Delay


def match_reverb_type(name: str) -> int:
    name_clean = name.strip().lower()
    for mid, title in REVERB_MODELS.items():
        if name_clean in title.lower():
            return mid

    if "spring" in name_clean:
        return 0x05
    if "plate" in name_clean:
        return 0x04
    if "hall 2" in name_clean:
        return 0x03
    if "hall" in name_clean:
        return 0x02
    if "room" in name_clean:
        return 0x01
    if "modulat" in name_clean:
        return 0x06

    return 0x04  # Default Plate


# -------------------------------------------------------------
# 2. Gemini Prompt Generator
# -------------------------------------------------------------
STANDARD_SCHEMA_EXAMPLE = {
    "katana_ai_preset": {
        "name": "Nome Preset (max 16 car)",
        "artist": "Nome Artista / Band",
        "song": "Titolo Canzone",
        "part": "Solo / Riff / Intro Clean",
        "pickup": "Single-Coil / Humbucker",
        "description": "Breve descrizione del tono ricercato",
        "amp": {
            "type": "Clean | Crunch | Lead | Brown | Acoustic | Clean Twin | Deluxe Crunch | MS-1959 I+II | BG Lead | R-Fier Modern",
            "gain": 50,
            "bass": 50,
            "middle": 50,
            "treble": 50,
            "presence": 50,
            "volume": 42
        },
        "booster": {
            "enabled": True,
            "type": "Blues Driver | Tubescreamer | Muff Fuzz | Overdrive | Rat | Centa OD | Distortion | '60s Fuzz | Clean Boost",
            "drive": 45,
            "tone": 50,
            "bottom": 50,
            "effect_level": 45
        },
        "mod": {
            "enabled": False,
            "type": "2x2 Chorus | Phaser | Flanger | Tremolo | Uni-Vibe | Compressor",
            "level": 50
        },
        "delay": {
            "enabled": True,
            "type": "Digital Delay | Analog Delay | Tape Echo | Modulate Delay | SDE-3000",
            "time_ms": 380,
            "feedback": 30,
            "level": 35
        },
        "reverb": {
            "enabled": True,
            "type": "Plate | Hall 1 | Hall 2 | Room | Spring | Modulate",
            "time": 35,
            "tone": 50,
            "level": 40
        },
        "noise_suppressor": {
            "enabled": True,
            "threshold": 45,
            "release": 50
        },
        "cabinet": {
            "resonance": "Vintage | Modern | Deep",
            "air_feel": "Rec | Live | Blend"
        },
        "tone_tips": "Consigli su come suonare (es. uso del plettro, dinamica, posizione del tono della chitarra)"
    }
}


def build_gemini_prompt(
    song: str,
    artist: str,
    part: str = "Lead / Solo",
    pickup: str = "Any",
    extra_notes: str = ""
) -> str:
    """
    Creates an optimized, unambiguous prompt for Google Gemini to produce
    a 100% compliant Katana AI preset JSON block.
    """
    prompt = f"""Agisci come il massimo ingegnere del suono per chitarra ed esperto dell'amplificatore Boss Katana MkII.
Devi creare un preset sonoro perfetto, fedele e autentico per:

- Canzone: {song.strip() or 'Brano Rock'}
- Artista / Band: {artist.strip() or 'Chitarrista Leggendario'}
- Sezione / Ruolo sonoro: {part.strip() or 'Lead / Solo'}
- Pickup / Chitarra raccomandata: {pickup.strip() or 'Qualsiasi'}
{f'- Note speciali dell utente: {extra_notes.strip()}' if extra_notes.strip() else ''}

REGOLE CRITICHE DI OUTPUT:
1. Rispondi ESCLUSIVAMENTE con un blocco JSON valido che segue ESATTAMENTE lo schema sottostante.
2. Non inserire testo prima o dopo il blocco JSON (solo il JSON o ```json ... ```).
3. I valori numerici di manopola devono essere compresi tra 0 e 100 (0..100).
4. Il parametro "volume" dell'amp deve essere SEMPRE compreso tra 38 e 45 per garantire un ascolto sicuro e non provocare esplosioni acustiche.
5. Scegli accuratamente il tipo di amplificatore (amp.type), booster (booster.type), delay (delay.type) e riverbero (reverb.type) tra quelli disponibili nel Boss Katana MkII.

SCHEMA JSON STANDARD RICHIESTO:
```json
{json.dumps(STANDARD_SCHEMA_EXAMPLE, indent=2, ensure_ascii=False)}
```
Genera ora il JSON esatto per '{song}' di '{artist}':"""
    return prompt


# -------------------------------------------------------------
# 3. Robust JSON Response Parser
# -------------------------------------------------------------
def parse_gemini_preset(text: str) -> Tuple[bool, Dict[str, Any], str]:
    """
    Parses a response from Gemini, extracting the katana_ai_preset dictionary.
    Handles raw JSON, markdown-wrapped JSON (```json ... ```), and text containing JSON.
    """
    if not text or not text.strip():
        return False, {}, "Testo vuoto."

    cleaned = text.strip()

    # Step 1: Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fence_match:
        json_candidate = fence_match.group(1).strip()
    else:
        # Step 2: Find outermost { ... }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_candidate = cleaned[start:end+1]
        else:
            json_candidate = cleaned

    try:
        data = json.loads(json_candidate)
    except Exception as e:
        return False, {}, f"Errore nel parsing JSON: {str(e)}"

    # If wrapped in "katana_ai_preset", unwrap
    if "katana_ai_preset" in data and isinstance(data["katana_ai_preset"], dict):
        preset_data = data["katana_ai_preset"]
    elif isinstance(data, dict):
        preset_data = data
    else:
        return False, {}, "Struttura JSON non valida: atteso oggetto radice."

    # Validate essential fields
    if "amp" not in preset_data and "name" not in preset_data:
        return False, {}, "Il JSON non contiene sezioni 'amp' o 'name' valide per il Katana."

    return True, preset_data, "Success"


# -------------------------------------------------------------
# 4. Apply AI Preset to KatanaPatchModel
# -------------------------------------------------------------
def apply_ai_preset_to_model(preset: Dict[str, Any], model, safe_guard: bool = True) -> bool:
    """
    Applies the parsed AI preset data to the active KatanaPatchModel,
    activating the appropriate parameters, clamping volumes safely,
    and triggering real-time hardware audition.
    """
    try:
        model._history_enabled = False

        # Name & Memo
        raw_name = preset.get("name") or preset.get("song") or "AI Preset"
        model.patch_name = raw_name[:16].strip()

        artist = preset.get("artist", "")
        song = preset.get("song", "")
        part = preset.get("part", "")
        pickup = preset.get("pickup", "")
        desc = preset.get("description", "")
        tips = preset.get("tone_tips", "")

        memo_parts = []
        if song or artist:
            memo_parts.append(f"{song} - {artist}".strip(" -"))
        if part:
            memo_parts.append(f"Part: {part}")
        if pickup:
            memo_parts.append(f"Pickup: {pickup}")
        if desc:
            memo_parts.append(f"\n{desc}")
        if tips:
            memo_parts.append(f"\n💡 Tone Tips:\n{tips}")

        model.patch_memo = "\n".join(memo_parts)

        # 1. Preamp
        amp_data = preset.get("amp", {})
        if amp_data:
            model.set_param("preamp_sw", 1, send_sysex=False, record_history=False)
            amp_type_str = amp_data.get("type", "Clean")
            amp_id = match_preamp_type(amp_type_str)
            model.set_param("preamp_type", amp_id, send_sysex=False, record_history=False)

            gain = int(amp_data.get("gain", 50))
            model.set_param("preamp_gain", gain, send_sysex=False, record_history=False)
            model.set_param("preamp_bass", int(amp_data.get("bass", 50)), send_sysex=False, record_history=False)
            model.set_param("preamp_middle", int(amp_data.get("middle", 50)), send_sysex=False, record_history=False)
            model.set_param("preamp_treble", int(amp_data.get("treble", 50)), send_sysex=False, record_history=False)
            model.set_param("preamp_presence", int(amp_data.get("presence", 50)), send_sysex=False, record_history=False)

            raw_vol = int(amp_data.get("volume", 42))
            model._original_preset_volume = raw_vol

            if safe_guard:
                safe_vol = calculate_safe_audition_volume(raw_vol, gain=gain, ceiling=42, floor=36)
                model.set_param("preamp_volume", safe_vol, send_sysex=False, record_history=False)
                model._is_safe_normalized = (raw_vol != safe_vol)
            else:
                model.set_param("preamp_volume", raw_vol, send_sysex=False, record_history=False)

            # Ensure solo switches are OFF
            model.set_param("preamp_solo_sw", 0, send_sysex=False, record_history=False)

        # 2. Booster
        boost_data = preset.get("booster", {})
        if boost_data:
            sw = 1 if boost_data.get("enabled", False) else 0
            model.set_param("booster_sw", sw, send_sysex=False, record_history=False)
            b_type_str = boost_data.get("type", "Blues Driver")
            b_id = match_booster_type(b_type_str)
            model.set_param("booster_type", b_id, send_sysex=False, record_history=False)
            model.set_param("booster_drive", int(boost_data.get("drive", 50)), send_sysex=False, record_history=False)
            model.set_param("booster_tone", int(boost_data.get("tone", 50)), send_sysex=False, record_history=False)
            model.set_param("booster_bottom", int(boost_data.get("bottom", 50)), send_sysex=False, record_history=False)

            eff_lvl = int(boost_data.get("effect_level", 45))
            if safe_guard and eff_lvl > 50:
                eff_lvl = 50
            model.set_param("booster_effect_level", eff_lvl, send_sysex=False, record_history=False)
            model.set_param("booster_solo_sw", 0, send_sysex=False, record_history=False)

        # 3. Delay
        delay_data = preset.get("delay", {})
        if delay_data:
            sw = 1 if delay_data.get("enabled", False) else 0
            model.set_param("delay1_sw", sw, send_sysex=False, record_history=False)
            d_type_str = delay_data.get("type", "Digital Delay")
            d_id = match_delay_type(d_type_str)
            model.set_param("delay1_type", d_id, send_sysex=False, record_history=False)

            # Convert time_ms (e.g. 380ms -> delay1_time 38)
            t_ms = delay_data.get("time_ms")
            if t_ms is not None:
                d_time = max(1, min(100, int(t_ms / 10)))
            else:
                d_time = int(delay_data.get("time", 35))
            model.set_param("delay1_time", d_time, send_sysex=False, record_history=False)
            model.set_param("delay1_feedback", int(delay_data.get("feedback", 30)), send_sysex=False, record_history=False)
            model.set_param("delay1_level", int(delay_data.get("level", 40)), send_sysex=False, record_history=False)

        # 4. Reverb
        rev_data = preset.get("reverb", {})
        if rev_data:
            sw = 1 if rev_data.get("enabled", False) else 0
            model.set_param("reverb_sw", sw, send_sysex=False, record_history=False)
            r_type_str = rev_data.get("type", "Plate")
            r_id = match_reverb_type(r_type_str)
            model.set_param("reverb_type", r_id, send_sysex=False, record_history=False)
            model.set_param("reverb_time", int(rev_data.get("time", 35)), send_sysex=False, record_history=False)
            model.set_param("reverb_tone", int(rev_data.get("tone", 50)), send_sysex=False, record_history=False)
            model.set_param("reverb_level", int(rev_data.get("level", 40)), send_sysex=False, record_history=False)

        # 5. Noise Suppressor
        ns_data = preset.get("noise_suppressor", {})
        if ns_data:
            sw = 1 if ns_data.get("enabled", True) else 0
            model.set_param("ns_sw", sw, send_sysex=False, record_history=False)
            model.set_param("ns_threshold", int(ns_data.get("threshold", 45)), send_sysex=False, record_history=False)
            model.set_param("ns_release", int(ns_data.get("release", 50)), send_sysex=False, record_history=False)

        # 6. Cabinet & Line Out Air Feel
        cab_data = preset.get("cabinet", {})
        if cab_data:
            res_str = cab_data.get("resonance", "Vintage").lower()
            res_val = 0
            if "modern" in res_str:
                res_val = 1
            elif "deep" in res_str:
                res_val = 2
            model.set_param("cab_resonance", res_val, send_sysex=False, record_history=False)

            air_str = cab_data.get("air_feel", "Rec").lower()
            air_val = 0
            if "live" in air_str:
                air_val = 1
            elif "blend" in air_str:
                air_val = 2
            model.set_param("line_out_air_feel", air_val, send_sysex=False, record_history=False)

        # Set raw parameter set to None so model values take precedence
        model._raw_param_set = None

        model._history_enabled = True
        model._dirty = True
        model.patch_loaded.emit(model.patch_name)
        model.dirty_changed.emit(True)

        # Transmit to hardware for instant audition
        model.send_full_patch_to_hardware()
        return True

    except Exception as e:
        print(f"Error applying AI preset: {e}")
        model._history_enabled = True
        return False


# -------------------------------------------------------------
# 5. Export Active Model to Standardized AI JSON
# -------------------------------------------------------------
def export_model_to_ai_json(model) -> str:
    """
    Exports the active model settings into the standardized Katana Tone JSON format
    ready to be pasted into Gemini for analysis, tweaking, or sharing.
    """
    amp_id = model.get_param("preamp_type")
    amp_name = PREAMP_MODELS[amp_id].name if amp_id in PREAMP_MODELS else "Clean"

    boost_id = model.get_param("booster_type")
    boost_name = BOOSTER_MODELS[boost_id].split(" (")[0] if boost_id in BOOSTER_MODELS else "Blues Driver"

    delay_id = model.get_param("delay1_type")
    delay_name = DELAY_MODELS[delay_id].split(" (")[0] if delay_id in DELAY_MODELS else "Digital Delay"

    rev_id = model.get_param("reverb_type")
    rev_name = REVERB_MODELS[rev_id].split(" (")[0] if rev_id in REVERB_MODELS else "Plate"

    res_names = {0: "Vintage", 1: "Modern", 2: "Deep"}
    air_names = {0: "Rec", 1: "Live", 2: "Blend"}

    data = {
        "katana_ai_preset": {
            "name": model.patch_name,
            "memo": model.patch_memo,
            "amp": {
                "type": amp_name,
                "gain": model.get_param("preamp_gain"),
                "bass": model.get_param("preamp_bass"),
                "middle": model.get_param("preamp_middle"),
                "treble": model.get_param("preamp_treble"),
                "presence": model.get_param("preamp_presence"),
                "volume": model.get_param("preamp_volume")
            },
            "booster": {
                "enabled": bool(model.get_param("booster_sw")),
                "type": boost_name,
                "drive": model.get_param("booster_drive"),
                "tone": model.get_param("booster_tone"),
                "bottom": model.get_param("booster_bottom"),
                "effect_level": model.get_param("booster_effect_level")
            },
            "delay": {
                "enabled": bool(model.get_param("delay1_sw")),
                "type": delay_name,
                "time_ms": model.get_param("delay1_time") * 10,
                "feedback": model.get_param("delay1_feedback"),
                "level": model.get_param("delay1_level")
            },
            "reverb": {
                "enabled": bool(model.get_param("reverb_sw")),
                "type": rev_name,
                "time": model.get_param("reverb_time"),
                "tone": model.get_param("reverb_tone"),
                "level": model.get_param("reverb_level")
            },
            "noise_suppressor": {
                "enabled": bool(model.get_param("ns_sw")),
                "threshold": model.get_param("ns_threshold"),
                "release": model.get_param("ns_release")
            },
            "cabinet": {
                "resonance": res_names.get(model.get_param("cab_resonance"), "Vintage"),
                "air_feel": air_names.get(model.get_param("line_out_air_feel"), "Rec")
            }
        }
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
