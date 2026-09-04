#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
es_spec.py - the single source of truth for the EarthSearch EP01 live mix.

The composition builder, the APC40 mkII preset generator, the control-map
document generator and the validator all import this module, so the .avc, the
MIDI preset XML and the printed control map can never drift apart. Change the
instrument here; rebuild all four artefacts.

Nothing in here writes files.

DESIGN CONTRACT (from the performer's brief - do not violate silently)
----------------------------------------------------------------------
  1. EXACTLY TWO full-length masters on the two bottom layers. They start
     together at frame zero and stay in sync for the whole episode.
  2. NO control that a performer touches in the ordinary course of playing may
     launch, seek, retrigger or restart a master. The 5x8 pad grid does not
     address layers 1-2 AT ALL, so this is structural, not a convention.
     There is no seek/scrub binding anywhere in the preset.
  3. Exactly one START BOTH, one STOP / RESET BOTH, one CLEAN / ALL FX OFF,
     all physically separated from the expressive controls.
  4. FFT drives effect and source PARAMETERS ONLY, never transport, never a
     trigger. Resolume can only attach a phase source to a <ParamRange>, and
     the only ParamRanges that could disturb playback (Transport Position,
     Speed) are deliberately left on PhaseSourceStatic.
  5. Every effect loads BYPASSED and every overlay layer loads at opacity 0,
     so the composition opens on the untouched picture.
  6. The original programme audio is editorially protected. Resolume decodes
     it, analyses it, and never writes it.

EVERY XML CONSTRUCT USED HERE WAS HARVESTED FROM A FILE RESOLUME ITSELF WROTE
- rig-saved .avc files in this workspace, the 104 working MIDI presets in this
workspace, and Resolume Avenue 7.27.1's own shipped presets under
C:\\Program Files\\Resolume Avenue\\default\\Presets\\. Nothing is guessed.
Resolume was not running during the build; see ../HANDOFF.md section 5.
"""

import os

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
PACK_DIR = os.path.dirname(BUILD_DIR)
OUTPUT_DIR = os.path.join(PACK_DIR, "output")
DOCS_DIR = os.path.join(PACK_DIR, "docs")

COMP_NAME = "EarthSearch_EP01_Live_Mix"
COMP_FILE = COMP_NAME + ".avc"
MIDI_PRESET_NAME = "APC 40 MK II - EarthSearch EP01"

WIDTH, HEIGHT = 1920, 1080
FPS = 24

# Both masters are 1630.708 s (27:10.708) = 39137 frames at 24 fps, to the
# millisecond. Verified with ffprobe on all three candidates. Identical
# durations are what make frame-zero alignment structural rather than hopeful.
MASTER_SECONDS = 1630.708
MASTER_MS = 1630708

# Distinct uniqueId base so EarthSearch ids can never collide with the Nisei
# (1787100000000+), Rafu Signal (1787900000000+) or Lexicon compositions.
ID_BASE = 1788400000000
PRESET_ID_BASE = 1788400900000
PRESET_ID = "2026090301"

RES_PRODUCT = "Resolume Avenue"
RES_MAJOR, RES_MINOR, RES_MICRO, RES_REV = 7, 27, 1, 15990

# --------------------------------------------------------------------------
# Media
# --------------------------------------------------------------------------
SOURCE_DIR = r"C:\Users\jeffr\Documents\ComfyUI\output\otr\obs\earthsearch"
MEDIA_DIR = os.path.join(SOURCE_DIR, "resolume")
DXV_DIR = os.path.join(MEDIA_DIR, "dxv")

# The untouched archive masters. Alley / ffmpeg read these; nothing writes them.
MASTER_SOURCES = {
    "V2": os.path.join(SOURCE_DIR, "episode01-v2",
                       "series1-episode1-v2-original-audio-master.mkv"),
    "V3": os.path.join(SOURCE_DIR, "episode01-v3",
                       "series1-episode1-v3-original-audio-master.mkv"),
    "V4": os.path.join(SOURCE_DIR, "episode01-v4",
                       "Earthsearch-Episode-1-V4-Dialogue-Inserts-"
                       "original-audio-master.mkv"),
}

# Programme audio, for reference. NOT loaded into Resolume: the masters carry
# this same audio embedded, and Composition FFT analyses it from the clip
# itself, which is frame-locked to the picture by construction. See
# docs/FFT_AND_AUDIO_ROUTING.md.
PROGRAMME_AUDIO = r"D:\earthsearch\EarthSearch09of10\EarthSearch 01of10.mp3"


def master_media(version):
    """The performance copy of a master.

    .mov with the video stream COPIED bit-for-bit from the .mkv archive master
    and the audio decoded to PCM. Two rig-measured facts forced this shape:

      * Avenue 7.27.1 gates readers by file extension and .mkv is on none of
        the three lists, so the archive masters cannot be opened directly.
      * Avenue will not decode an MP3 audio stream in ANY container. Tested on
        this rig: .mov+mp3 loads with NO audio track at all, while .mov+PCM and
        .mp4+AAC both load with one. Without an audio track the composition FFT
        has nothing to analyse and every reactive parameter sits at its floor.

    PCM rather than AAC because PCM is the exact decode of the original MP3 -
    no second lossy generation, nothing added, nothing processed. The archive
    .mkv masters and the original .mp3 are untouched, and the delivered
    soundtrack still comes from the untouched original in Resolve.
    """
    return os.path.join(MEDIA_DIR, "EarthSearch_EP01_MASTER_%s.mov" % version)


# Kept so an older composition can still be pointed back at the MP4 remuxes.
def master_mp4(version):
    return os.path.join(MEDIA_DIR, "EarthSearch_EP01_MASTER_%s.mp4" % version)


def master_dxv(version):
    return os.path.join(DXV_DIR, "EarthSearch_EP01_MASTER_%s.mov" % version)


# A = bottom / base, B = top / alternate.
#
# V2 + V3 is the correct pair and it is not a matter of taste. Both are
# independent 324-shot re-renders of the SAME 324 audio windows, each a
# straight concatenation of 121-frame units, so their cuts land on identical
# timestamps to the millisecond - a fader between them is a pure content A/B
# with no double-cutting. V4 is NOT a third render: it is the V2/V3 hybrid
# Resolve edit, so it is V2's picture for ~95% of the runtime AND it is
# quantised to a different cut grid that runs progressively earlier than V2/V3
# (0 frames at the head, 67 frames = 2.79 s by the tail). Pairing V4 with V2
# gives you the same picture twice; pairing it with either gives you drifting
# cuts. Ship V2/V3.
DEFAULT_A = "V2"
DEFAULT_B = "V3"

VERSION_ROLE = {
    "V2": "Variety / Action - independent 324-shot render, prompt-led "
          "identity, the documented dramatic base of the edit",
    "V3": "Character Continuity - the same 324 windows re-rendered through "
          "reference-conditioned identity masters; different composition, "
          "shot scale and colour bias for every window",
    "V4": "Hybrid Resolve edit master - NOT a third render, and on a "
          "different cut grid. Do not pair it with V2 or V3.",
}

# --------------------------------------------------------------------------
# THE EARTHSEARCH PALETTE
#
# A 1981 BBC radio science-fiction serial, heard not seen: four children raised
# by two shipboard computers, hunting a lost Earth. The visual register the
# generative overlays aim at is the television of that moment - phosphor
# terminals, oscilloscope traces, wireframe navigation charts, Radiophonic
# Workshop tape - laid over the rendered picture as instrumentation, never as
# decoration.
#
# ParamColor stores ARGB packed into one uint32.
# --------------------------------------------------------------------------
def argb(a, r, g, b):
    return (a << 24) | (r << 16) | (g << 8) | b


PALETTE = {
    "void":      argb(255, 0x05, 0x07, 0x0C),   # deep space black-blue
    "phosphor":  argb(255, 0x38, 0xFF, 0xA8),   # ANGEL terminal green
    "amber":     argb(255, 0xFF, 0xB0, 0x3A),   # CRT amber
    "signal":    argb(255, 0x4F, 0xE3, 0xFF),   # telemetry cyan
    "bone":      argb(255, 0xE8, 0xEE, 0xF2),   # bone white
    "alert":     argb(255, 0xFF, 0x3B, 0x2F),   # distress red
    "indigo":    argb(255, 0x1B, 0x2A, 0x6B),   # deep indigo
    "rust":      argb(255, 0xB4, 0x5A, 0x28),   # oxidised hull
    "black":     argb(255, 0x00, 0x00, 0x00),
    "clear":     argb(0, 0, 0, 0),
}

# --------------------------------------------------------------------------
# Magic uniqueTypeIds - load-bearing. A wrong id makes Resolume silently drop
# the element.
# --------------------------------------------------------------------------
TYPE_TRANSFORM = "17122039101699797593"

BLEND_TYPES = {          # RenderPass type -> uniqueTypeId
    "Alpha": "A006", "Add": "A005", "Screen": "A012",
    "Multiply": "A011", "Lighten": "A013", "LumaKey": "A009",
}
# The ChoosableMixer ALSO needs an explicit Blend Mode ParamChoice. Without it
# Resolume falls back to its default, which is Add (67464114) - so a layer that
# must dissolve rather than sum would silently sum. Values rig-verified from
# build_gen_src.avc and build_livegen_src.avc.
BLEND_CHOICE = {"Add": "67464114", "Alpha": "67464115",
                "Screen": "67464212", "LumaKey": "67464118"}
BLEND_CHOICE_DEFAULT = "67464114"

# EFFECT_LIBRARY: the XML name (which is ALSO what the OSC slug derives from)
# -> (xml type attribute, uniqueTypeId, [parameter names as Resolume writes]).
#
# Harvested LIVE from this rig: every one of Avenue 7.27.1's 109 video effects
# was added to a real composition through the REST API, the result saved, and
# the XML parsed. The type strings and ids below are Resolume's own output, not
# a transcription. Reference: ../reference/avenue_7271_effect_library.json.
#
# That harvest also settled the OSC slug rule for good. Resolume writes the
# effect's XML TYPE name as its display name ("Hue Rotate" in the browser is
# HueRotate in the file), and every rig-proven MIDI preset in this workspace
# addresses it as lowercase(type) with non-alphanumerics stripped: huerotate,
# lorezeffect, shiftrgb, mirrorquad, invertrgb, bloom, trails, freeze,
# vignette, bendoscope. So slug(name) below is exact, not inferred.
#
# CRT and WarpSpeed both carry type="WireEffect" but get distinct display
# names, so their slugs are crt and warpspeed - no collision.
EFFECT_LIBRARY = {
    # --- COLOUR ----------------------------------------------------------
    "Tint":          ("Tint",          "A179", []),
    "Colorize":      ("Colorize",      "A103", ["GreysTolerance", "Contrast"]),
    "HueRotate":     ("HueRotate",     "A128", ["Hue Rotate"]),
    "Levels":        ("Levels",        "A141", []),
    "Exposure":      ("Exposure",      "A134", []),
    "Saturation":    ("Saturation",    "A110", []),
    "Posterize":     ("Posterize",     "A109", []),
    "InvertRGB":     ("InvertRGB",     "A105", []),
    # --- BROADCAST -------------------------------------------------------
    "CRT":           ("WireEffect",
                      "c_be77e0d5-1404-4399-b8ae-7cdd64cba5ab", []),
    "StaticEffect":  ("StaticEffect",  "MSTF", []),
    "NoisyEffect":   ("NoisyEffect",   "A185", []),
    "DotScreen":     ("DotScreen",     "A176", []),
    "Raster":        ("Raster",        "872041778225", []),
    "LoRezEffect":   ("LoRezEffect",   "A142", ["Pixel Size", "Bit Reduction",
                                                "Dither"]),
    "DelayRGB":      ("DelayRGB",      "A152", []),
    "ShiftRGB":      ("ShiftRGB",      "A153", ["Distance"]),
    # --- LIGHT -----------------------------------------------------------
    "Bloom":         ("Bloom",         "6980402605", ["Amount", "Threshold",
                                                      "Size"]),
    "Trails":        ("Trails",        "A111", ["Feedback"]),
    "RadialBlur":    ("RadialBlur",    "sy03", ["Steps", "Distance"]),
    "Blur":          ("Blur",          "A140", []),
    "Sparkles":      ("Sparkles",      "A188", ["Size"]),
    "Heat":          ("Heat",          "A107", []),
    "Freeze":        ("Freeze",        "A132", []),
    "Iterate":       ("Iterate",       "sy13", ["TransformStrength",
                                                "Iterations", "StartOpacity",
                                                "OpacityChange", "Scale"]),
    # --- SPACE -----------------------------------------------------------
    "WaveWarp":      ("WaveWarp",      "MWWP", ["Height", "Width", "Speed"]),
    "Ripples":       ("Ripples",       "sy05", ["Frequency H", "Frequency V",
                                                "Amplitude Both", "Phase"]),
    "Displace":      ("Displace",      "A131", []),
    "Tunnel":        ("Tunnel",        "sy04", ["Speed", "Twist"]),
    "WarpSpeed":     ("WireEffect",
                      "c_d6ae9f13-8177-4423-a808-18173a3db933", []),
    "MirrorQuad":    ("MirrorQuad",    "A180", []),
    "PolarKaleido":  ("PolarKaleido",  "A190", []),
    "InfiniteZoom":  ("InfiniteZoom",  "P205", ["Zoom"]),
    # --- FRACTURE --------------------------------------------------------
    "ShiftGlitch":   ("ShiftGlitch",   "MBSH", ["Frequency", "Vertical",
                                                "Horizontal", "Size"]),
    "TwitchEffect":  ("TwitchEffect",  "A183", ["Global Twitch", "Max Pos Y",
                                                "Pos Frequency",
                                                "Max RGB Shift",
                                                "RGB Frequency"]),
    "EdgeDetection": ("EdgeDetection", "MEDG", []),
    "Triangulate":   ("Triangulate",   "A182", []),
    "Radar":         ("Radar",         "J004", []),
}

# Generator sources. uniqueTypeIds confirmed against the live /sources catalog
# (../reference/avenue_7271_sources_catalog.json); XML type names confirmed
# against rig-saved compositions. Every one is a GeneratorVideoSource.
GENERATOR_LIBRARY = {
    "SineWave":           "9011349750094602",
    "Metaballs":          "844752396506092017",
    "Rings":              "8642267115",
    "Spiral":             "884102460919",
    "Lines":              "P201",
    "LineScape":          "P204",
    "Checkered":          "736772465707583394",
    "Gradient":           "A401",
    "SolidColor":         "A403",
    "StaticGenerator":    "MSTS",
    "TextGenerator":      "11421072728336491440",
    "BlockTextGenerator": "3600113141201236715",
    "ShaperGenerator":    "7946640550597690042",
    "FFGLGenerator":      "FPLS",
    "TestCard":           "9114371295504994",
}


def slug(name):
    """Resolume's OSC slug: lowercase, non-alphanumerics stripped.

    Confirmed exactly by the live harvest documented above.
    """
    return "".join(ch.lower() for ch in name if ch.isalnum())


# No overrides. An older preset in this workspace binds Bloom as
# .../bloom/effect/brightness, and that WAS carried into an early draft of this
# build - but asking the running rig settled it: with the composition open and
# OSC output on, nudging Bloom's Amount makes Resolume emit
#   /composition/video/effects/bloom/effect/amount
# The parameter was renamed between Resolume versions, so the old preset is
# evidence about an old Resolume, not about this one. build/harvest_osc_paths.py
# reproduces the check for any parameter.
PARAM_SLUG_OVERRIDE = {}


def param_slug(effect_name, param):
    return PARAM_SLUG_OVERRIDE.get((effect_name, param), slug(param))


# --------------------------------------------------------------------------
# THE COMPOSITION FX RACK - 37 effects in five named banks, one bank per row
# of the APC40's surface.
#
# The rack sits on the BLENDED A+B output, so it treats the episode as one
# picture. Everything loads BYPASSED and at a cinematic default, never a demo
# default: this is a 27-minute drama in which dialogue-driven story information
# has to survive every treatment.
#
# BROADCAST is the signature bank. CRT is Resolume's cathode-ray-tube
# emulation - it squeezes the picture into an emulated CRT resolution space and
# lights one R,G,B triad per pixel. For a 1981 BBC radio serial rendered as
# television, that one effect does more work than any amount of colour grading,
# and it is why this bank sits on the top pad row where a hand falls first.
#
# (bank, control label, effect key, {param: value})
# --------------------------------------------------------------------------
BANK_COLOUR = "COLOUR"
BANK_BROADCAST = "BROADCAST"
BANK_LIGHT = "LIGHT"
BANK_SPACE = "SPACE"
BANK_FRACTURE = "FRACTURE"
BANK_ORDER = [BANK_COLOUR, BANK_BROADCAST, BANK_LIGHT, BANK_SPACE,
              BANK_FRACTURE]

COMP_RACK = [
    (BANK_COLOUR, "TINT",       "Tint",       {}),
    (BANK_COLOUR, "COLORIZE",   "Colorize",   {"Contrast": 0.5,
                                               "GreysTolerance": 0.3}),
    (BANK_COLOUR, "DRIFT",      "HueRotate",  {"Hue Rotate": 0.0}),
    (BANK_COLOUR, "LEVELS",     "Levels",     {}),
    (BANK_COLOUR, "EXPOSURE",   "Exposure",   {}),
    (BANK_COLOUR, "SATURATION", "Saturation", {}),
    (BANK_COLOUR, "POSTERIZE",  "Posterize",  {}),
    (BANK_COLOUR, "NEGATIVE",   "InvertRGB",  {}),

    (BANK_BROADCAST, "CRT",        "CRT",          {}),
    (BANK_BROADCAST, "GRAIN",      "StaticEffect", {}),
    (BANK_BROADCAST, "NOISE",      "NoisyEffect",  {}),
    (BANK_BROADCAST, "DOT SCREEN", "DotScreen",    {}),
    (BANK_BROADCAST, "RASTER",     "Raster",       {}),
    (BANK_BROADCAST, "BIT CRUSH",  "LoRezEffect",  {"Pixel Size": 0.055,
                                                    "Bit Reduction": 0.14}),
    (BANK_BROADCAST, "RGB DELAY",  "DelayRGB",     {}),
    (BANK_BROADCAST, "FRINGE",     "ShiftRGB",     {}),

    (BANK_LIGHT, "BLOOM",   "Bloom",      {"Threshold": 0.72, "Size": 0.30}),
    (BANK_LIGHT, "ECHO",    "Trails",     {}),
    (BANK_LIGHT, "RAYS",    "RadialBlur", {"Steps": 0.40, "Distance": 0.10}),
    (BANK_LIGHT, "BLUR",    "Blur",       {}),
    (BANK_LIGHT, "SPARKLE", "Sparkles",   {"Size": 0.30}),
    (BANK_LIGHT, "HEAT",    "Heat",       {}),
    (BANK_LIGHT, "HOLD",    "Freeze",     {}),
    (BANK_LIGHT, "ITERATE", "Iterate",    {"TransformStrength": 0.12,
                                           "Iterations": 0.20,
                                           "OpacityChange": 0.35,
                                           "Scale": 0.48}),

    (BANK_SPACE, "WAVE",        "WaveWarp",     {"Width": 0.10,
                                                 "Speed": 0.08}),
    (BANK_SPACE, "RIPPLE",      "Ripples",      {"Frequency H": 0.30,
                                                 "Frequency V": 0.30,
                                                 "Phase": 0.0}),
    (BANK_SPACE, "DISPLACE",    "Displace",     {}),
    (BANK_SPACE, "TUNNEL",      "Tunnel",       {"Speed": 0.52,
                                                 "Twist": 0.50}),
    (BANK_SPACE, "WARPSPEED",   "WarpSpeed",    {}),
    (BANK_SPACE, "MIRROR QUAD", "MirrorQuad",   {}),
    (BANK_SPACE, "POLAR",       "PolarKaleido", {}),
    (BANK_SPACE, "ZOOM",        "InfiniteZoom", {"Zoom": 0.5}),

    (BANK_FRACTURE, "TEAR",   "ShiftGlitch",   {"Frequency": 0.22,
                                                "Vertical": 0.10,
                                                "Horizontal": 0.50,
                                                "Size": 0.28}),
    (BANK_FRACTURE, "TWITCH", "TwitchEffect",  {"Global Twitch": 0.32,
                                                "Max Pos Y": 0.05,
                                                "Pos Frequency": 0.20,
                                                "Max RGB Shift": 0.10,
                                                "RGB Frequency": 0.20}),
    (BANK_FRACTURE, "EDGE",   "EdgeDetection", {}),
    (BANK_FRACTURE, "FACET",  "Triangulate",   {}),
    (BANK_FRACTURE, "RADAR",  "Radar",         {}),
]


def comp_rack_bank(bank):
    return [e for e in COMP_RACK if e[0] == bank]


# --------------------------------------------------------------------------
# LAYERS
#
# Eight layers, which is exactly the APC40's channel count, so every per-track
# strip control (fader, activator, solo, select, clip-stop) has a real layer to
# act on and nothing on the surface is decorative.
#
#   1  MASTER A   the base version                    <- video master
#   2  MASTER B   the alternate version               <- video master
#   3-7 SIGNAL / STARFIELD / GRID / CAPTION / FLARE   <- generative overlays,
#                                                       one per pad-grid row
#   8  SCOPE      the live FFT readout                <- always available
#
# Layer 2 is ALPHA at opacity 0, so raising it is a true dissolve A -> B.
# Additive and light blends are one button away (the blend-mode cycle) rather
# than the default, because Add-blending two full-frame 1080p pictures sums
# toward white.
#
# (index0, name, blend, opacity, colorId, kind)
# --------------------------------------------------------------------------
KIND_MASTER = "master"
KIND_OVERLAY = "overlay"
KIND_SCOPE = "scope"

# CrossFaderGroup: 0 None, 1 A, 2 B. Harvested from the live rig, not guessed -
# this workspace had never written the param before, so it was set through the
# REST API on the real composition and the resulting XML read back:
#   <ParamChoice name="CrossFaderGroup" T="INT32" default="0" value="1"
#                storeChoices="0" />
# With A on the base master and B on the alternate, the APC's physical
# crossfader is a true A/B bus rather than a decorative control, and the two
# layer faders stay free for independent level.
#
# Ignore Column Trigger: also harvested live -
#   <Param name="Ignore Column Trigger" T="BOOL" default="0" value="1" />
# It is set on the five OVERLAY layers, not on the masters. That asymmetry is
# deliberate and was determined by testing on the rig: a layer that ignores
# column triggers ignores ALL of them, including the START column, so setting
# it on the masters would break START BOTH. Set on the overlays instead, it
# means the pad grid is the sole authority over overlay content and no column
# action can disturb what the performer has built up there.
#
# (index0, name, blend, opacity, colorId, kind, crossfader group,
#  ignore column trigger)
LAYERS = [
    (0, "MASTER A",  "Alpha",  1.00, 5, KIND_MASTER,  1, True),
    (1, "MASTER B",  "Alpha",  1.00, 2, KIND_MASTER,  2, True),
    (2, "SIGNAL",    "Add",    0.00, 1, KIND_OVERLAY, 0, True),
    (3, "STARFIELD", "Screen", 0.00, 4, KIND_OVERLAY, 0, True),
    (4, "GRID",      "Add",    0.00, 3, KIND_OVERLAY, 0, True),
    (5, "CAPTION",   "Alpha",  0.00, 1, KIND_OVERLAY, 0, True),
    (6, "FLARE",     "Add",    0.00, 2, KIND_OVERLAY, 0, True),
    (7, "SCOPE",     "Add",    0.00, 3, KIND_SCOPE,   0, True),
]
NUM_LAYERS = len(LAYERS)
NUM_COLUMNS = 8

# The pad grid addresses layers 3-7 ONLY. Physical pad row 1 (bottom) = layer 3.
# Layers 1 and 2 are unreachable from the pad grid by construction, which is how
# "no pad may restart a master" is guaranteed rather than merely intended.
PAD_ROW_LAYER = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}

# EVERY layer sets Ignore Column Trigger, so a column trigger cannot connect,
# eject or restart anything anywhere in this composition. That is what makes
# the "no ordinary control may restart a master" rule structural rather than a
# convention: even a mis-click on a column header in Resolume's own UI is
# inert.
#
# START BOTH therefore does NOT use a column. It is one physical button
# carrying THREE shortcuts on the same MIDI key - one clip-connect per master
# plus the scope. Both halves of that are rig-verified: 57 working presets in
# this workspace already share a single MIDI key across up to three shortcuts
# including multiple .../connect paths, and connecting the two masters as
# separate events was measured on this rig at 0.0 ms drift after 8 seconds.
#
# The columns are now pure storage for the pad grid. They are named for the
# overlay material each holds so the grid reads left to right as a journey.
START_COLUMN = 1
COLUMN_NAMES = [
    "MAKE CONTACT", "APPROACH", "TELEMETRY", "DEEP FIELD",
    "TRANSMISSION", "ALARM", "DESCENT", "SILENCE",
]
# The layers START BOTH connects, in order: the two masters and the FFT scope.
START_LAYERS = [1, 2, 8]
DECK_NAME = "EarthSearch EP01"

# The overlay layers deliberately carry NO effect racks of their own. Every
# treatment lives in the composition rack, downstream of the blend, so one
# CLEAN gesture reaches all of it and the performer has one mental model of
# where effects live instead of three.

# --------------------------------------------------------------------------
# THE GENERATIVE OVERLAY CLIPS - 40 of them, five layers of eight.
#
# All procedural: no media files, no relinking, no disk cost, and they cannot
# fall out of sync with anything because they are not transports of recorded
# material. They exist to put EarthSearch's own instrumentation over the
# rendered picture - phosphor terminals, oscilloscope traces, navigation
# charts, Radiophonic tape hiss - rather than generic VJ content.
#
# Every one loads on a layer at opacity 0, and every layer is Add/Screen/Alpha
# chosen so that raising it reads as light ON the picture, not instead of it.
#
# Text on the CAPTION layer is a starting point, not an editorial decision:
# every string is editable in Resolume's own text field in two clicks.
#
# (layer index0, column1..8, clip name, generator type, {param: value},
#  {param: (band, gain_db, fallback_ms, floor, ceiling)} FFT bindings)
# --------------------------------------------------------------------------
P = PALETTE

OVERLAY_CLIPS = {
    # ---- layer 3  SIGNAL - oscilloscope and radiophonic traces (Add) -----
    2: [
        ("CARRIER WAVE",   "SineWave", {"Color": P["phosphor"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.12, "Frequency": 0.10,
                                        "Amplitude": 0.16, "Waves": 1.0,
                                        "Main Speed": 0.30}, {}),
        ("VOICE PRINT",    "SineWave", {"Color": P["signal"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.10, "Frequency": 0.22,
                                        "Amplitude": 0.10, "Waves": 2.0,
                                        "Main Speed": 0.45},
         {"Amplitude": ("mid", 30.0, 700, 0.06, 0.34)}),
        ("TELEMETRY",      "SineWave", {"Color": P["amber"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.06, "Frequency": 0.55,
                                        "Amplitude": 0.07, "Waves": 4.0,
                                        "Main Speed": 0.80}, {}),
        ("ANGEL ONE",      "SineWave", {"Color": P["phosphor"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.09, "Frequency": 0.33,
                                        "Amplitude": 0.13, "Waves": 3.0,
                                        "Modulation Depth": 3.0,
                                        "Main Speed": 0.55}, {}),
        ("ANGEL TWO",      "SineWave", {"Color": P["signal"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.09, "Frequency": 0.41,
                                        "Amplitude": 0.13, "Waves": 3.0,
                                        "Modulation Depth": 5.0,
                                        "Main Speed": 0.62}, {}),
        ("DISTRESS",       "SineWave", {"Color": P["alert"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.16, "Frequency": 0.08,
                                        "Amplitude": 0.22, "Waves": 1.0,
                                        "Main Speed": 0.18},
         {"Line Width": ("low", 27.0, 1200, 0.10, 0.30)}),
        ("DEEP SIGNAL",    "SineWave", {"Color": P["indigo"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.20, "Frequency": 0.04,
                                        "Amplitude": 0.30, "Waves": 1.0,
                                        "Main Speed": 0.10}, {}),
        ("INTERFERENCE",   "Lines",    {"Color": P["bone"],
                                        "Fuzzyness": 0.70, "Width": 0.06,
                                        "Amount": 24.0, "Rotation": 0.0,
                                        "Position": 0.5},
         {"Width": ("high", 34.0, 400, 0.02, 0.12)}),
    ],
    # ---- layer 4  STARFIELD - deep space (Screen) ------------------------
    3: [
        ("STARFIELD",      "Metaballs", {"Color": P["bone"],
                                         "BG Color": P["clear"],
                                         "Size": 0.10, "Fuzzyness": 0.04,
                                         "Speed": 0.18, "Radius": 0.75,
                                         "Distance": 0.80, "Grid": 8.0}, {}),
        ("NEBULA",         "Metaballs", {"Color": P["indigo"],
                                         "BG Color": P["clear"],
                                         "Size": 0.75, "Fuzzyness": 0.45,
                                         "Speed": 0.08, "Radius": 0.50,
                                         "Distance": 0.40, "Grid": 2.0}, {}),
        ("ORBIT RINGS",    "Rings",     {"Color 1": P["signal"],
                                         "Color 2": P["clear"],
                                         "Num Rings": 7.0,
                                         "Line Width": 0.05,
                                         "Spacing": 0.42, "Size": 0.9},
         {"Size": ("low", 27.0, 1400, 0.82, 1.02)}),
        ("PLANET",         "Spiral",    {"Color": P["rust"],
                                         "BG Color": P["clear"],
                                         "Speed": 0.14, "Zoom": 0.55,
                                         "Fuzzyness": 0.35}, {}),
        ("PHOTONIC DRIVE", "Rings",     {"Color 1": P["amber"],
                                         "Color 2": P["clear"],
                                         "Num Rings": 16.0,
                                         "Line Width": 0.03,
                                         "Spacing": 0.16, "Size": 1.0},
         {"Spacing": ("mid", 30.0, 500, 0.12, 0.30)}),
        ("ION CLOUD",      "Metaballs", {"Color": P["phosphor"],
                                         "BG Color": P["clear"],
                                         "Size": 0.45, "Fuzzyness": 0.30,
                                         "Speed": 0.30, "Radius": 0.45,
                                         "Distance": 0.55, "Grid": 3.0}, {}),
        ("JUMP",           "Spiral",    {"Color": P["signal"],
                                         "BG Color": P["clear"],
                                         "Speed": 0.72, "Zoom": 0.85,
                                         "Fuzzyness": 0.12},
         {"Speed": ("high", 34.0, 350, 0.55, 0.95)}),
        ("DEBRIS",         "Metaballs", {"Color": P["amber"],
                                         "BG Color": P["clear"],
                                         "Size": 0.16, "Fuzzyness": 0.06,
                                         "Speed": 0.40, "Radius": 0.65,
                                         "Distance": 0.70, "Grid": 6.0}, {}),
    ],
    # ---- layer 5  GRID - wireframe navigation (Add) ----------------------
    4: [
        ("NAV GRID",       "LineScape", {"Color": P["phosphor"]}, {}),
        ("HORIZON",        "Lines",     {"Color": P["phosphor"],
                                         "Fuzzyness": 0.20, "Width": 0.03,
                                         "Amount": 9.0, "Rotation": 0.0,
                                         "Position": 0.5}, {}),
        ("SCAN BARS",      "Lines",     {"Color": P["amber"],
                                         "Fuzzyness": 0.10, "Width": 0.02,
                                         "Amount": 40.0, "Rotation": 0.0,
                                         "Position": 0.5},
         {"Position": ("mid", 28.0, 900, 0.35, 0.65)}),
        ("TERRAIN",        "LineScape", {"Color": P["signal"]}, {}),
        ("CHART",          "Checkered", {"Color 1": P["clear"],
                                         "Color 2": P["indigo"]}, {}),
        ("VECTOR RISE",    "Lines",     {"Color": P["signal"],
                                         "Fuzzyness": 0.30, "Width": 0.04,
                                         "Amount": 14.0, "Rotation": 0.25,
                                         "Position": 0.5}, {}),
        ("SECTOR",         "Checkered", {"Color 1": P["clear"],
                                         "Color 2": P["phosphor"]}, {}),
        ("APPROACH",       "LineScape", {"Color": P["amber"]}, {}),
    ],
    # ---- layer 6  CAPTION - system captions (Alpha) ----------------------
    5: [
        ("CAP EARTHSEARCH", "TextGenerator", {"Text": "EARTHSEARCH",
                                              "Color": P["phosphor"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.55, "Opacity": 1.0,
                                              "Position Y": 0.0}, {}),
        ("CAP EPISODE ONE", "TextGenerator", {"Text": "EPISODE ONE",
                                              "Color": P["bone"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.35, "Opacity": 1.0,
                                              "Position Y": 0.0}, {}),
        ("CAP ANGEL 1",     "TextGenerator", {"Text": "ANGEL 1",
                                              "Color": P["phosphor"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.30, "Opacity": 1.0,
                                              "Position X": -0.35,
                                              "Position Y": -0.35}, {}),
        ("CAP ANGEL 2",     "TextGenerator", {"Text": "ANGEL 2",
                                              "Color": P["signal"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.30, "Opacity": 1.0,
                                              "Position X": 0.35,
                                              "Position Y": -0.35}, {}),
        ("CAP CHALLENGER",  "TextGenerator", {"Text": "CHALLENGER",
                                              "Color": P["amber"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.34, "Opacity": 1.0,
                                              "Position Y": 0.35}, {}),
        ("CAP SYSTEM",      "BlockTextGenerator", {"Text": "SYSTEM READY",
                                                   "Color": P["phosphor"],
                                                   "Outline Color": P["clear"],
                                                   "Size": 0.5,
                                                   "Scale": 0.8}, {}),
        ("CAP CREW",        "TextGenerator", {"Text": "TELSON  SHARNA  "
                                                      "ASTRA  DARV",
                                              "Color": P["bone"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.26, "Opacity": 1.0,
                                              "Position Y": 0.40}, {}),
        ("CAP END",         "TextGenerator", {"Text": "END OF TRANSMISSION",
                                              "Color": P["alert"],
                                              "Outline Color": P["clear"],
                                              "Size": 0.32,
                                              "Opacity": 1.0}, {}),
    ],
    # ---- layer 7  FLARE - light accents (Add) ----------------------------
    6: [
        ("AMBER WASH",     "Gradient",   {"Color 1": P["amber"],
                                          "Color 2": P["clear"],
                                          "Dither": 0.3}, {}),
        ("PHOSPHOR WASH",  "Gradient",   {"Color 1": P["phosphor"],
                                          "Color 2": P["clear"],
                                          "Dither": 0.3}, {}),
        ("SIGNAL WASH",    "Gradient",   {"Color 1": P["signal"],
                                          "Color 2": P["clear"],
                                          "Dither": 0.3}, {}),
        ("BONE FLASH",     "SolidColor", {"Color": P["bone"]}, {}),
        ("RED ALERT",      "SolidColor", {"Color": P["alert"]}, {}),
        ("TAPE GRAIN",     "StaticGenerator", {}, {}),
        ("PLASMA",         "FFGLGenerator",   {"Level": 0.45, "Period": 0.40,
                                               "Stack": 0.5, "Beam": 0.4,
                                               "Dispersion": 0.25,
                                               "Glow": 0.35},
         {"Glow": ("low", 27.0, 1200, 0.20, 0.55)}),
        ("SHAPER",         "ShaperGenerator", {"Color": P["indigo"],
                                               "Outline Color": P["signal"]},
         {}),
    ],
    # ---- layer 8  SCOPE - the live FFT readout (Add) ---------------------
    #
    # One clip, in the START column, so it arms with the masters and is always
    # a fader away. Three parameters on three bands: the trace's height follows
    # speech, its weight follows the score's low end, and its frequency follows
    # the highs. It is a working instrument, not decoration - it is how the
    # performer SEES what the FFT is doing before deciding to open a treatment.
    7: [
        ("FFT SCOPE",      "SineWave", {"Color": P["phosphor"],
                                        "BG Color": P["clear"],
                                        "Line Width": 0.08, "Frequency": 0.20,
                                        "Amplitude": 0.10, "Waves": 2.0,
                                        "Mirror": 1, "Main Speed": 0.35},
         {"Amplitude": ("mid",  32.0,  350, 0.04, 0.42),
          "Line Width": ("low",  27.0,  600, 0.05, 0.20),
          "Frequency":  ("high", 34.0,  300, 0.15, 0.55)}),
    ],
}

# --------------------------------------------------------------------------
# FFT
#
# Rig-verified construct, and CRUCIALLY the link id is
#   /audioengine/compositionfft
# not externalfft. Composition FFT analyses the composition's own audio, which
# here IS the programme audio, embedded in the masters and decoded by the same
# clip that draws the picture. It is therefore frame-locked to the image by
# construction: no virtual audio cable, no second transport, no drift, and it
# keeps working if the operator changes audio devices. 801 uses across 19
# rig-saved compositions in this workspace.
#
# BANDS: Resolume's spectrum is normalised 0..1.
# WEIGHTING: EarthSearch is a band-limited 1981 BBC radio drama - overwhelmingly
# dialogue, no kick drum. Speech energy lives in the MID band, so mid carries
# the work here; low is reserved for the Radiophonic music stings and highs for
# a single gentle sparkle. A club-style bass-heavy map would sit dead for
# twenty minutes at a time.
#
# GAIN in dB (-48..48): 3 dB on geometry, 6 dB on opacity/glow/texture. Never
# 9 dB on this show, and never a strobe.
# FALLBACK in ms (100..2000): long. Nothing here snaps.
# --------------------------------------------------------------------------
# MEASURED ON THIS RIG against this episode's actual soundtrack, not copied
# from a club preset. build/calibrate_fft.ps1 sweeps gain per band and reports
# how much of each parameter's output range the band actually uses.
#
# What the measurements showed, and why these numbers are what they are:
#   * Resolume's spectrum axis is perceptual, not linear - the mid band
#     responds strongly even though a 40 kbps mono MP3 is lowpassed well below
#     the linear midpoint.
#   * The top tenth of the spectrum (0.90-1.00) is genuinely empty on this
#     source. A 0.66-1.00 "high" band moved 9% of its range even at 42 dB.
#     Pulled down to 0.58-0.82 it moves 86% at 36 dB.
#   * A 1981 radio drama needs FAR more gain than music does. At the 3-6 dB
#     the house recipe card suggests for club material, every parameter here
#     moved less than 6% of its range - invisible.
BANDS = {
    "low":  (0.0,  0.30),   # room tone, Radiophonic stings, the ship
    "mid":  (0.32, 0.62),   # speech - the working band of this episode
    "high": (0.58, 0.82),   # consonants and tape brightness
}
BAND_LABEL = {"low": "LOW  (0.00-0.33)  music stings, room tone",
              "mid": "MID  (0.33-0.66)  speech - the working band",
              "high": "HIGH (0.66-1.00)  sibilance, tape hiss"}

# Composition-rack FFT bindings.
# (effect label, effect type, param, band, gain dB, fallback ms,
#  floor, ceiling, rationale)
FFT_MAP = [
    ("BLOOM",  "Bloom",     "Amount",      "mid",  30.0, 1200, 0.14, 0.44,
     "Speech lifts the analogue glow. Floor 0.14 keeps the glow alive in "
     "silence so it reads as a lamp, not a gate."),
    ("ECHO",   "Trails",    "Feedback",    "low",  27.0, 1600, 0.42, 0.66,
     "The Radiophonic score's low end lengthens the feedback tail. Ceiling "
     "0.66: above ~0.75 Trails smears the faces the story depends on."),
    ("DRIFT",  "HueRotate", "Hue Rotate",  "mid",  30.0, 1100, 0.0, 0.045,
     "Voice drifts the palette by at most ~16 degrees of hue. Felt, never "
     "seen as a rainbow."),
    ("WAVE",   "WaveWarp",  "Height",      "mid",  26.0,  900, 0.03, 0.095,
     "Mid energy breathes the frame. Ceiling 0.095 stays under the point "
     "where faces distort."),
    ("FRINGE", "ShiftRGB",  "Distance",    "high", 36.0,  500, 0.015, 0.070,
     "Sibilance and incidental highs put a broadcast fringe on edges."),
    ("RIPPLE", "Ripples",   "Amplitude Both", "high", 30.0, 700, 0.02, 0.085,
     "Highs shimmer the surface. Tiny, so text and faces stay readable."),
    ("ITERATE", "Iterate",  "StartOpacity", "mid",  30.0,  800, 0.28, 0.58,
     "Speech modulates how strongly the recursive copies register - the "
     "holographic element, held well below full."),
    ("BIT CRUSH", "LoRezEffect", "Dither", "high", 34.0, 600, 0.10, 0.42,
     "Highs move the dither, which is the closest thing in the chain to "
     "analogue signal texture. Deliberately NOT the wrapper Opacity: every "
     "effect's dry/wet stays on its bank's dashboard link, or CLEAN could not "
     "reach it."),
]

# Live FFT control on the surface, via the rig-verified behaviour paths
# .../behaviour/gain (dB) and .../behaviour/fallback (ms). One anchor
# parameter per band gets its depth and release on a knob, so the performer can
# re-tune the reactivity mid-episode without stopping.
FFT_BAND_ANCHOR = {
    "low":  ("ECHO",   "Trails",    "Feedback"),
    "mid":  ("BLOOM",  "Bloom",     "Amount"),
    "high": ("FRINGE", "ShiftRGB",  "Distance"),
}

# --------------------------------------------------------------------------
# COMPOSITION DASHBOARD - the eight global macro links.
#
# A dashboard link is referenced by MANY parameters at once via
#   <PhaseSourceDashboardLink linkId="/linkN">
# (shape rig-verified in "Res Fable Live Gen SPECIMEN.avc"). That one-to-many
# property is what makes CLEAN possible without inventing a shortcut species:
# links 1-5 each gate one whole bank's dry/wet, and the CLEAN control is a
# single physical fader carrying FIVE shortcuts on ONE MIDI key - one per bank
# link - so one gesture takes the entire experimental chain to zero without
# touching playback, bypass state, or either master's transport.
#
# Resolume exposes exactly eight composition links, so the rack is gated by
# bank rather than per effect.
# (link, label, what it drives)
# --------------------------------------------------------------------------
COMP_DASHBOARD = [
    (1, "COLOUR",    "dry/wet of every effect in the COLOUR bank"),
    (2, "BROADCAST", "dry/wet of every effect in the BROADCAST bank"),
    (3, "LIGHT",     "dry/wet of every effect in the LIGHT bank"),
    (4, "SPACE",     "dry/wet of every effect in the SPACE bank"),
    (5, "FRACTURE",  "dry/wet of every effect in the FRACTURE bank"),
    (6, "OVERLAYS",  "video opacity of all five generative overlay layers"),
    (7, "SCOPE",     "video opacity of the live FFT readout layer"),
    (8, "SPARE",     "unassigned macro, free for the performer"),
]
LINK_BANK = {1: BANK_COLOUR, 2: BANK_BROADCAST, 3: BANK_LIGHT,
             4: BANK_SPACE, 5: BANK_FRACTURE}
# The links CLEAN drives to zero in one gesture.
CLEAN_LINKS = [1, 2, 3, 4, 5, 6, 7]
