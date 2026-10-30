"""
Definitions, catalog metadata and categorizations for Boss Katana MkII
Includes all standard amp models, variations, the 28 hidden 'Sneaky Amps' (GT-100 legacy),
and comprehensive overdrive, modulation, fx, delay and reverb models.
"""

from typing import Dict, List, NamedTuple, Any


class ModelInfo(NamedTuple):
    sysex_id: int
    name: str
    category: str
    description: str


# ---------------------------------------------------------
# PREAMP MODELS (Standard + Variations + 28 Sneaky Amps)
# ---------------------------------------------------------
PREAMP_MODELS: Dict[int, ModelInfo] = {
    # Standard Katana Types
    0x01: ModelInfo(0x01, "Acoustic", "Standard", "Acoustic guitar optimized clean preamp"),
    0x08: ModelInfo(0x08, "Clean", "Standard", "Transparent natural clean tone"),
    0x0B: ModelInfo(0x0B, "Crunch", "Standard", "Responsive vintage crunch edge-of-breakup"),
    0x18: ModelInfo(0x18, "Lead", "Standard", "Singing high-gain lead sound"),
    0x17: ModelInfo(0x17, "Brown", "Standard", "Signature EVH brown sound, rich harmonics"),

    # MkII Variations
    0x1C: ModelInfo(0x1C, "Var [Acoustic]", "MkII Variation", "Acoustic variation with enhanced dynamic top end"),
    0x1D: ModelInfo(0x1D, "Var [Clean]", "MkII Variation", "Bright sparkle American clean"),
    0x1E: ModelInfo(0x1E, "Var [Crunch]", "MkII Variation", "Modern British voiced punchy crunch"),
    0x1F: ModelInfo(0x1F, "Var [Lead]", "MkII Variation", "Mid-focused modern high gain lead"),
    0x20: ModelInfo(0x20, "Var [Brown]", "MkII Variation", "Modernized high-definition brown stack"),

    # Sneaky Amps: Clean & Vintage
    0x00: ModelInfo(0x00, "Natural Clean", "Sneaky Clean", "Ultra linear clean studio tone"),
    0x09: ModelInfo(0x09, "Clean Twin", "Sneaky Clean", "Fender Twin Reverb 2x12 1965 Blackface"),
    0x0A: ModelInfo(0x0A, "Pro Crunch", "Sneaky Clean", "Fender Pro Reverb vintage warm breakup"),
    0x0C: ModelInfo(0x0C, "Deluxe Crunch", "Sneaky Clean", "Fender Deluxe Reverb 1965 tone"),
    0x02: ModelInfo(0x02, "Combo Crunch", "Sneaky Crunch", "Fender Tweed Bassman combo"),
    0x03: ModelInfo(0x03, "Stack Crunch", "Sneaky Crunch", "Marshall JMP 50W half stack crunch"),
    0x0D: ModelInfo(0x0D, "VO Drive", "Sneaky Crunch", "Vox AC-30 Top Boost channel overdrive"),
    0x0E: ModelInfo(0x0E, "VO Lead", "Sneaky Crunch", "Vox AC-30 with Brian May treble booster"),
    0x0F: ModelInfo(0x0F, "Match Drive", "Sneaky Crunch", "Matchless D/C-30 boutique chiming overdrive"),

    # Sneaky Amps: Classic Rock & Plexi
    0x12: ModelInfo(0x12, "MS-1959 I", "Sneaky Vintage Rock", "Marshall 1959 Super Lead Plexi Channel 1 (Normal)"),
    0x13: ModelInfo(0x13, "MS-1959 I+II", "Sneaky Vintage Rock", "Marshall 1959 Plexi with jumpered inputs (Ch1+Ch2)"),
    0x05: ModelInfo(0x05, "Power Drive", "Sneaky Vintage Rock", "Class-A power stage saturated crunch"),

    # Sneaky Amps: High Gain & Boutique
    0x10: ModelInfo(0x10, "BG Lead", "Sneaky High Gain", "Mesa/Boogie Mark IIc+ high gain lead"),
    0x11: ModelInfo(0x11, "BG Drive", "Sneaky High Gain", "Mesa/Boogie Mark IV lead drive channel"),
    0x04: ModelInfo(0x04, "HiGain Stack", "Sneaky High Gain", "Soldano SLO-100 Super Lead Overdrive"),
    0x16: ModelInfo(0x16, "T-Amp Lead", "Sneaky High Gain", "Hughes & Kettner TriAmp 3 Lead"),
    0x06: ModelInfo(0x06, "Extreme Lead", "Sneaky High Gain", "Ultra high gain compressed singing lead"),

    # Sneaky Amps: Modern Metal
    0x14: ModelInfo(0x14, "R-Fier Vintage", "Sneaky Metal", "Mesa/Boogie Dual Rectifier (Channel 2 Vintage)"),
    0x15: ModelInfo(0x15, "R-Fier Modern", "Sneaky Metal", "Mesa/Boogie Dual Rectifier (Channel 3 Modern High Gain)"),
    0x07: ModelInfo(0x07, "Core Metal", "Sneaky Metal", "Boss ML-2 Metal Core modern low-end thrash"),
}


# ---------------------------------------------------------
# BOOSTER / OVERDRIVE / DISTORTION
# ---------------------------------------------------------
BOOSTER_MODELS: Dict[int, str] = {
    0x00: "Mid Boost (Clean Boost with mid bump)",
    0x01: "Clean Boost (Flat response booster)",
    0x02: "Treble Boost (Dallas Rangemaster)",
    0x03: "Crunch OD (Warm mild overdrive)",
    0x04: "Natural OD (Transparent dynamic OD)",
    0x05: "Warm OD (Tubey smooth overdrive)",
    0x06: "Fat DS (Thick distortion with low end punch)",
    0x08: "Metal DS (Aggressive metal distortion)",
    0x09: "OCT Fuzz (Octavia upper octave fuzz)",
    0x0A: "Blues Driver (Boss BD-2)",
    0x0B: "Overdrive (Boss OD-1 vintage)",
    0x0C: "Tubescreamer (Ibanez TS-808)",
    0x0D: "Turbo OD (Boss OD-2 Turbo)",
    0x0E: "Distortion (Boss DS-1)",
    0x0F: "Rat (ProCo RAT 2)",
    0x10: "GuV DS (Marshall Guv'nor)",
    0x11: "DST+ (MXR Distortion+)",
    0x12: "Metal Zone (Boss MT-2)",
    0x13: "'60s Fuzz (Fuzz Face vintage)",
    0x14: "Muff Fuzz (Electro-Harmonix Big Muff Pi)",
    0x15: "HM-2 (Boss HM-2 Heavy Metal Swedish chainsaw)",
    0x16: "Metal Core (Boss ML-2)",
    0x17: "Centa OD (Klon Centaur Professional Overdrive)",
}


# ---------------------------------------------------------
# MODULATION (FX1)
# ---------------------------------------------------------
MOD_MODELS: Dict[int, str] = {
    0x00: "T-Wah (Touch Wah envelope)",
    0x01: "Auto Wah (LFO sweep wah)",
    0x02: "Pedal Wah",
    0x03: "Compressor",
    0x04: "Limiter",
    0x06: "Graphic EQ",
    0x07: "Parametric EQ",
    0x09: "Guitar Sim (Single to Hum / Hum to Single)",
    0x0A: "Slow Gear (Boss SG-1 auto volume swell)",
    0x0C: "Wave Synth (Monophonic analog synth)",
    0x0E: "Octave (Boss OC-2 dual octave)",
    0x0F: "Pitch Shifter",
    0x10: "Harmonist (Intelligent pitch harmonizer)",
    0x12: "Acoustic Processor",
    0x13: "Phaser (Boss PH-3)",
    0x14: "Flanger (Boss BF-3)",
    0x15: "Tremolo (Boss TR-2)",
    0x16: "Rotary (Leslie 147 rotating speaker)",
    0x17: "Uni-Vibe (Shin-ei Uni-Vibe)",
    0x19: "Slicer (Boss SL-20 rhythmic chopper)",
    0x1A: "Vibrato (Boss VB-2 pitch vibrato)",
    0x1B: "Ring Modulator",
    0x1C: "Humanizer (Vocal formant talk box)",
    0x1D: "2x2 Chorus (Stereo dimensional chorus)",
    0x1F: "Acoustic Sim (Electric to Acoustic)",
    0x23: "Phaser 90E (MXR Phase 90 Script)",
    0x24: "Flanger 117E (Electro-Harmonix Electric Mistress)",
    0x25: "Wah 95E (Dunlop CryBaby GCB95)",
    0x26: "Chorus CE-1 (Roland Jazz Chorus / Boss CE-1)",
    0x27: "Heavy Octave",
    0x28: "Pedal Bend (DigiTech Whammy)",
}


# ---------------------------------------------------------
# EFFECTS (FX2)
# ---------------------------------------------------------
FX_MODELS: Dict[int, str] = {
    0x00: "T-Wah",
    0x01: "Auto Wah",
    0x02: "Pedal Wah",
    0x03: "Compressor",
    0x04: "Limiter",
    0x06: "Graphic EQ",
    0x07: "Parametric EQ",
    0x09: "Guitar Sim",
    0x0A: "Slow Gear",
    0x0C: "Wave Synth",
    0x0E: "Octave",
    0x0F: "Pitch Shifter",
    0x10: "Harmonist",
    0x12: "Acoustic Processor",
    0x13: "Phaser",
    0x14: "Flanger",
    0x15: "Tremolo",
    0x16: "Rotary",
    0x17: "Uni-Vibe",
    0x19: "Slicer",
    0x1A: "Vibrato",
    0x1B: "Ring Mod",
    0x1C: "Humanizer",
    0x1D: "2x2 Chorus",
    0x1F: "Acoustic Sim",
    0x23: "Phaser 90E",
    0x24: "Flanger 117E",
    0x25: "Wah 95E",
    0x26: "Chorus CE-1",
    0x27: "Heavy Octave",
    0x28: "Pedal Bend",
}


# ---------------------------------------------------------
# DELAY MODELS
# ---------------------------------------------------------
DELAY_MODELS: Dict[int, str] = {
    0x00: "Digital Delay (Crystal clear digital)",
    0x01: "Pan Delay (Ping-pong stereo delay)",
    0x02: "Stereo Delay",
    0x03: "Dual Series",
    0x04: "Dual Parallel",
    0x05: "Dual L/R",
    0x06: "Reverse Delay (Backwards psychedelic)",
    0x07: "Analog Delay (Boss DM-2 Bucket Brigade warmth)",
    0x08: "Tape Echo (Roland RE-201 Space Echo)",
    0x09: "Modulate Delay (Delay with lush chorus mod)",
    0x0A: "SDE-3000 (Roland SDE-3000 80s rackmount legend)",
}


# ---------------------------------------------------------
# REVERB MODELS
# ---------------------------------------------------------
REVERB_MODELS: Dict[int, str] = {
    0x00: "Ambience (Small acoustic space)",
    0x01: "Room (Cozy studio room reflection)",
    0x02: "Hall 1 (Warm concert hall)",
    0x03: "Hall 2 (Expansive symphonic hall)",
    0x04: "Plate (EMT-140 metallic studio plate)",
    0x05: "Spring ('63 Fender combo spring tank)",
    0x06: "Modulate (Ethereal shimmering reverb)",
}


# ---------------------------------------------------------
# SIGNAL CHAIN ROUTES (Boss Katana MkII Hardware Topologies)
# ---------------------------------------------------------
CHAIN_ROUTES: List[Dict[str, Any]] = [
    {
        "id": 0,
        "name": "Chain 1: Standard Studio",
        "short_name": "Chain 1: Standard",
        "desc": "Il routing classico: Booster prima dell'amplificatore, Modulazioni ed FX nel loop effetti post-ampli.",
        "blocks": ["in", "booster", "amp", "mod", "eq", "fx", "delay", "reverb", "ns", "master"],
        "summary": "In ➔ Boost ➔ Amp ➔ Mod ➔ EQ ➔ FX ➔ Delay ➔ Rev",
        "badge": "CLASSIC"
    },
    {
        "id": 1,
        "name": "Chain 2-1: Pre-Amp FX",
        "short_name": "Chain 2-1: FX Pre-Amp",
        "desc": "FX posto prima del preamplificatore (ideale per compressore, autowah, pitch shifter), modulazioni post-ampli.",
        "blocks": ["in", "booster", "fx", "amp", "mod", "eq", "delay", "reverb", "ns", "master"],
        "summary": "In ➔ Boost ➔ FX ➔ Amp ➔ Mod ➔ EQ ➔ Delay ➔ Rev",
        "badge": "STUDIO"
    },
    {
        "id": 2,
        "name": "Chain 3-1: Vintage Pedalboard",
        "short_name": "Chain 3-1: Vintage Board",
        "desc": "Booster, Modulazione ed FX tutti prima dell'amplificatore, esattamente come in una classica pedaliera analogica.",
        "blocks": ["in", "booster", "mod", "fx", "amp", "eq", "delay", "reverb", "ns", "master"],
        "summary": "In ➔ Boost ➔ Mod ➔ FX ➔ Amp ➔ EQ ➔ Delay ➔ Rev",
        "badge": "VINTAGE"
    },
    {
        "id": 3,
        "name": "Chain 4-1: 70s Front Delay",
        "short_name": "Chain 4-1: Tape Delay",
        "desc": "Anche il Delay entra prima dell'ampli: ideale per sonorità slapback anni '70, eco a nastro e shoegaze psichedelico.",
        "blocks": ["in", "booster", "mod", "fx", "delay", "amp", "eq", "reverb", "ns", "master"],
        "summary": "In ➔ Boost ➔ Mod ➔ FX ➔ Delay ➔ Amp ➔ EQ ➔ Rev",
        "badge": "RETRO"
    },
    {
        "id": 4,
        "name": "Chain 2-2: Mod-First Drive (Hendrix)",
        "short_name": "Chain 2-2: Mod-First",
        "desc": "Modulazione prima del Booster/Overdrive: emula un Uni-Vibe o Phaser vintage che pilota un pedale Fuzz distorto.",
        "blocks": ["in", "mod", "booster", "amp", "eq", "fx", "delay", "reverb", "ns", "master"],
        "summary": "In ➔ Mod ➔ Boost ➔ Amp ➔ EQ ➔ FX ➔ Delay ➔ Rev",
        "badge": "HENDRIX"
    },
    {
        "id": 5,
        "name": "Chain 3-2: Front-End Complete",
        "short_name": "Chain 3-2: Front Complete",
        "desc": "Modulazione ➔ Boost ➔ FX tutti posti in serie prima del preamplificatore Katana.",
        "blocks": ["in", "mod", "booster", "fx", "amp", "eq", "delay", "reverb", "ns", "master"],
        "summary": "In ➔ Mod ➔ Boost ➔ FX ➔ Amp ➔ EQ ➔ Delay ➔ Rev",
        "badge": "ANALOG"
    },
    {
        "id": 6,
        "name": "Chain 4-2: Full Raw Front-End",
        "short_name": "Chain 4-2: Full Raw",
        "desc": "Tutti i blocchi effetti (Mod, Boost, FX, Delay) posti a monte prima del preamplificatore.",
        "blocks": ["in", "mod", "booster", "fx", "delay", "amp", "eq", "reverb", "ns", "master"],
        "summary": "In ➔ Mod ➔ Boost ➔ FX ➔ Delay ➔ Amp ➔ EQ ➔ Rev",
        "badge": "RAW"
    },
]
