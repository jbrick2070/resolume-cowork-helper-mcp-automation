#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
instrument.py - the standard eight-layer / five-deck APC40 mkII instrument
that every procedural pack in this workspace shares, as one control table.

The composition side (build_composition_skeleton) and the preset side
(build_apc_map) are generated from the same InstrumentSpec, so the shipped
.avc, the MIDI preset XML and the printed control map cannot disagree.

THE SURFACE, in one place
-------------------------
  Pad grid 5x8        rows 1-5 = layers 1-5 (BED BODY FIGURE LIGHT TEXT),
                      clip connect. Bottom row = layer 1.
  Scene Launch 1-5    connect columns 1-5 of the current deck (scenes)
  UP / DOWN           next / previous scene (column): UP walks right
  LEFT / RIGHT        previous / next DECK (world)
  Clip Stop ch1-8     eject layer 1-8
  Track Select ch1-8  select layer
  Activator ch1-8     layer live / muted (lit = live)
  Solo ch1-8          layer solo
  Record Arm ch1-8    FX bank 1 (8 latching toggles)
  Crossfade A/B ch1-8 FX bank 2 (8)
  Device row n58-65   FX bank 3 (8)
  PAN SENDS USER      FX bank 4 (6)      NUDGE- NUDGE+ SESSION REC
  PLAY                OPEN THE SHOW: column 1 + re-arm the SCOPE
  STOP                CLEAR THE GRID: eject layers 1-5 (beds survive)
  STOP ALL CLIPS      eject everything (disconnect all)
  RECORD              BLACKOUT toggle (reversible)
  BANK LOCK           CLEAN: all eight dashboard links to zero (FX off)
  SHIFT               re-arm the SCOPE
  METRONOME           FFT GAIN home (puts the global gain back to the middle)
  TAP TEMPO           TIME home (composition speed back to 1x)
  MASTER              select composition
  Faders ch1-8        layer master level     MASTER fader  composition master
  CROSSFADER          environment (A: BED BODY AURA) <-> figures (B: FIGURE
                      LIGHT TEXT). Centre = everything.
  Device knobs 1-8    dashboard links 1-8: four bank dry/wets, four macros
  Track knobs 1-8     live FFT: LOW/MID/HIGH depth + release, SCOPE depth,
                      TIME (composition speed 0..2x)
  CUE LEVEL           FX master over the four bank links (relative encoder)
  TEMPO knob          FFT INPUT GAIN, global (relative encoder). The same knob
                      on every composition; this instrument has no BPM job.
  FOOTSWITCH          momentary blackout
"""
from . import apc as A

LAYER_ROLES = ["BED", "BODY", "FIGURE", "LIGHT", "TEXT", "AURA", "GRAIN",
               "SCOPE"]
GRID_ROWS = 5                       # pad rows -> layers 1..5
XFADE_A = {1, 2, 6}                 # environment
XFADE_B = {3, 4, 5}                 # figures
SCOPE_LAYER = 8

BANK_SEATS = [
    ("RECORD ARM n48 ch%d", [("note", ch, 48) for ch in range(1, 9)]),
    ("CROSSFADE A/B n66 ch%d", [("note", ch, 66) for ch in range(1, 9)]),
    ("DEVICE n%d", [("note", 1, n) for n in range(58, 66)]),
    ("GLOBAL n%d", [("note", 1, n) for n in (87, 88, 89, 100, 101, 102)]),
]

FFT_GAIN = "/audiodevicemanager/params/fftinputgain"

FORBIDDEN_PATHS = [
    "transport/position",      # no scrubbing from the surface
    "composition/decks/",      # deck changes only via next/prev
    "selectedclip",            # nothing retargets on selection
]


class InstrumentSpec(object):
    """What a pack has to tell the instrument.

    layer_names     eight display names, in order
    row_colors      five LED colour families for the pad rows (apc.LED_RGB)
    banks           four lists of (label, effect_xml_name) - the composition
                    rack in surface order; bank 4 holds at most 6
    dashboard       eight link labels (1-4 are the banks, 5-8 macros)
    fft_anchor      {"low": (xml_name, param), "mid": ..., "high": ...}
    scope_anchor    (xml_name_of_scope_generator_param_path)  e.g.
                    "/composition/layers/8/clips/1/video/source/amplitude"
    preset_name, preset_id, id_base
    """

    def __init__(self, **kw):
        self.layer_names = kw["layer_names"]
        self.row_colors = kw["row_colors"]
        self.banks = kw["banks"]
        self.dashboard = kw["dashboard"]
        self.fft_anchor = kw["fft_anchor"]
        self.scope_anchor = kw.get("scope_anchor")
        self.preset_name = kw["preset_name"]
        self.preset_id = kw["preset_id"]
        self.id_base = kw["id_base"]
        self.scene_colors = kw.get("scene_colors", ["white"] * 5)
        assert len(self.layer_names) == 8
        assert len(self.banks) == 4 and len(self.banks[3]) <= 6
        assert all(len(b) <= 8 for b in self.banks)
        assert len(self.dashboard) == 8


def pslug(name):
    return "".join(ch.lower() for ch in name if ch.isalnum())


def build_apc_map(S, deck_clip_names=None):
    """Return an apc.Preset with every control on the surface mapped.

    deck_clip_names: optional {(layer1..5, col1..8): name} for the control-map
    document; the preset itself does not need it (pads address positions).
    """
    P = A.Preset(S.preset_name, S.preset_id, S.id_base)
    names = S.layer_names

    # ---- pad grid ------------------------------------------------------
    for row in range(1, GRID_ROWS + 1):
        fam = A.LED_RGB[S.row_colors[row - 1]]
        layer = row
        for col in range(1, 9):
            n = (row - 1) * 8 + (col - 1)
            cname = (deck_clip_names or {}).get((layer, col), "")
            P.add("Pad R%dC%d %s" % (row, col, cname), "note",
                  "/composition/layers/%d/clips/%d/connect" % (layer, col),
                  "clip", note=n, group="Pad grid",
                  note_text="%s layer, column %d" % (names[layer - 1], col),
                  led={"Connected": fam["on"],
                       "Connected & previewing": fam["on"],
                       "Disconnected": fam["dim"], "Previewing": fam["dim"],
                       "Empty": 0, "Off": 0})

    # ---- scenes --------------------------------------------------------
    for i, n in enumerate((82, 83, 84, 85, 86), start=1):
        fam = A.LED_RGB[S.scene_colors[i - 1]]
        P.add("SCENE %d" % i, "note", "/composition/columns/%d/connect" % i,
              "action11", note=n, group="Scenes",
              note_text="fires every layer's clip in column %d" % i,
              led={"Off": fam["dim"], "On": fam["on"]})
    # UP walks forward (to the right), DOWN walks back: the performer's choice, 2026-10-23
    P.add("NEXT SCENE", "note", "/composition/connectnextcolumn",
          "action1", note=94, group="Scenes", led={"Off": 0, "On": 127})
    P.add("PREVIOUS SCENE", "note", "/composition/connectprevcolumn",
          "action1", note=95, group="Scenes", led={"Off": 0, "On": 127})
    P.add("PREVIOUS DECK", "note", "/composition/selectprevdeck",
          "action11", note=97, group="Decks", led={"Off": 0, "On": 1},
          note_text="walks the deck tabs - each deck is a world")
    P.add("NEXT DECK", "note", "/composition/selectnextdeck",
          "action11", note=96, group="Decks", led={"Off": 0, "On": 1})

    # ---- per-track rows -------------------------------------------------
    for ch in range(1, 9):
        P.add("Eject %s" % names[ch - 1], "note",
              "/composition/layers/%d/clear" % ch, "action11", note=52,
              channel=ch, group="Eject layer", led={"Off": 0, "On": 1})
        P.add("Select %s" % names[ch - 1], "note",
              "/composition/layers/%d/select" % ch, "select", note=51,
              channel=ch, group="Select layer", led={"Off": 0, "On": 1})
        P.add("Mute %s" % names[ch - 1], "note",
              "/composition/layers/%d/bypassed" % ch, "bypass11", note=50,
              channel=ch, group="Mute layer", led={"Off": 1, "On": 0},
              note_text="lit = on air")
        P.add("Solo %s" % names[ch - 1], "note",
              "/composition/layers/%d/solo" % ch, "solo", note=49,
              channel=ch, group="Solo layer", led={"Off": 0, "On": 1})

    # ---- effect banks ---------------------------------------------------
    for bi, (label_fmt, seats) in enumerate(BANK_SEATS):
        bank = S.banks[bi]
        for (seat, (kind, ch, n)) in zip(bank, seats):
            label, xml_name = seat
            P.add("FX%d %s" % (bi + 1, label), "note",
                  "/composition/video/effects/%s/bypassed" % pslug(xml_name),
                  "boolparam", note=n, channel=ch,
                  group="FX bank %d - %s" % (bi + 1, S.dashboard[bi]),
                  note_text="composition effect %s (lit = active)" % xml_name,
                  led={"Off": 1, "On": 0})

    # ---- transport / safety ---------------------------------------------
    P.add("OPEN THE SHOW (scene 1)", "note", "/composition/columns/1/connect",
          "action11", note=91, group="Safety - open",
          note_text="scene 1 of the current deck", led={"Off": 1, "On": 127})
    P.add("OPEN THE SHOW (scope)", "note",
          "/composition/layers/%d/clips/1/connect" % SCOPE_LAYER, "clip",
          note=91, group="Safety - open",
          led={"Connected": 127, "Connected & previewing": 127,
               "Disconnected": 1, "Previewing": 1, "Empty": 0, "Off": 0})
    for ln in range(1, GRID_ROWS + 1):
        P.add("CLEAR THE GRID (%s)" % names[ln - 1], "note",
              "/composition/layers/%d/clear" % ln, "action11", note=92,
              group="Safety - clear grid",
              note_text="ejects the five pad layers; AURA/GRAIN/SCOPE stay",
              led={"Off": 0, "On": 127})
    P.add("EJECT EVERYTHING", "note", "/composition/disconnectall", "action1",
          note=81, group="Safety - stop all", led={"Off": 0, "On": 127},
          note_text="silk-screened STOP ALL CLIPS does what it says")
    P.add("BLACKOUT", "note", "/composition/bypassed", "boolparam", note=93,
          group="Safety - blackout", led={"Off": 0, "On": 127},
          note_text="reversible black; everything keeps running")
    for link in range(1, 9):
        P.add("CLEAN (link %d %s)" % (link, S.dashboard[link - 1]), "note",
              "/composition/dashboard/link%d" % link, "ccrange", note=103,
              group="Safety - clean", value_range=("0", "0"), init="0",
              note_text="all four banks dry, all four macros off",
              led={"Off": 0, "On": 127})
    P.add("Re-arm SCOPE", "note",
          "/composition/layers/%d/clips/1/connect" % SCOPE_LAYER, "clip",
          note=98, group="Scope",
          led={"Connected": 1, "Connected & previewing": 1,
               "Disconnected": 0, "Previewing": 0, "Empty": 0, "Off": 0})
    # No BPM job anywhere in this instrument (the music drives it through the
    # external FFT), so the tempo buttons become the two reset buttons for the
    # two global dials: FFT gain on the TEMPO knob, speed on Track knob 8.
    P.add("FFT GAIN home (0.5)", "note", FFT_GAIN, "ccrange", note=90,
          group="FFT gain (global)", value_range=("0.5", "0.5"), init="0.5",
          led={"Off": 0, "On": 127},
          note_text="one press puts the global FFT gain back to the middle; "
                    "the TEMPO knob trims it from there")
    P.add("TIME home (1x)", "note", "/composition/speed", "ccrange", note=99,
          group="TIME home", value_range=("0.1", "0.1"), init="0.1",
          led={"Off": 0, "On": 127},
          note_text="one press puts composition speed back to exactly 1x")
    P.add("Select composition", "note", "/composition/select", "selectcomp",
          note=80, group="Mixer", led={"Off": 0, "On": 1})

    # ---- faders ---------------------------------------------------------
    for ch in range(1, 9):
        P.add("Fader %d - %s" % (ch, names[ch - 1]), "cc",
              "/composition/layers/%d/master" % ch, "cc11", cc=7, channel=ch,
              group="Layer level", init="1")
    P.add("Master fader", "cc", "/composition/master", "cc1", cc=14,
          group="Master", init="1")
    P.add("CROSSFADE environment <-> figures", "cc",
          "/composition/crossfader/phase", "cc1", cc=15, group="Master",
          init="0.5",
          note_text="left: BED BODY AURA only. right: FIGURE LIGHT TEXT only. "
                    "centre: everything")

    # ---- knobs ----------------------------------------------------------
    for i in range(1, 9):
        P.add("Device knob %d - %s" % (i, S.dashboard[i - 1]), "cc",
              "/composition/dashboard/link%d" % i, "cc1", cc=15 + i,
              group="Banks and macros", init="1" if i <= 4 else "0")
    knobs = []
    for band in ("low", "mid", "high"):
        xml_name, param = S.fft_anchor[band]
        base = "/composition/video/effects/%s/effect/%s" % (pslug(xml_name),
                                                            pslug(param))
        knobs.append(("%s DEPTH (%s)" % (band.upper(), xml_name),
                      base + "/behaviour/gain", "0.5"))
        knobs.append(("%s RELEASE (%s)" % (band.upper(), xml_name),
                      base + "/behaviour/fallback", "0.4"))
    if S.scope_anchor:
        knobs.append(("SCOPE DEPTH", S.scope_anchor + "/behaviour/gain",
                      "0.5"))
    else:
        knobs.append(("SCOPE DEPTH (unused)", "/composition/dashboard/link8",
                      "0"))
    for i, (label, path, init) in enumerate(knobs[:7]):
        P.add("Track knob %d - %s" % (i + 1, label), "cc", path, "ccrange",
              cc=48 + i, group="Live FFT", init=init)
    # TIME: composition speed. Speed's range is 0..10; a shortcut ValueRange
    # is normalised over the parameter's own range, so 0..0.2 = 0..2x and the
    # knob's centre is exactly 1x.
    P.add("Track knob 8 - TIME (speed 0..2x)", "cc", "/composition/speed",
          "ccrange", cc=55, group="Live FFT", value_range=("0", "0.2"),
          init="0.5", note_text="every generator breathes faster or slower")
    # CUE LEVEL and TEMPO are the two free-spinning encoders (no LED ring).
    # Avenue's own MIDI-learn of CUE LEVEL in the performer's saved preset came
    # back RELATIVE (behaviour 2113544 carries the relative bit, step 1/128), so
    # the FX master is a relative nudge on all four bank links, not a position.
    for link in range(1, 5):
        P.add("FX MASTER nudge (link %d)" % link, "cc",
              "/composition/dashboard/link%d" % link, "relative", cc=47,
              group="FX master", num_steps=64,
              note_text="anticlockwise walks all four banks to the clean "
                        "picture, clockwise brings them back")
    P.add("Footswitch momentary BLACKOUT", "cc", "/composition/bypassed",
          "ccrange", cc=64, value_range=("0", "1"), init="0",
          group="Safety - blackout")
    # FFT INPUT GAIN: Avenue's global audio-analysis gain (Preferences > Audio,
    # path proven in the performer's own saved presets). It lives on the TEMPO
    # knob because that is the one knob every composition's preset leaves free
    # and the instrument has no BPM job. Relative, so it never jumps.
    P.add("FFT GAIN (global input gain)", "cc", FFT_GAIN, "relative", cc=13,
          group="FFT gain (global)", num_steps=128,
          note_text="turn up when the picture is too calm, down when it "
                    "slams; the same knob on every composition")
    return P


def control_map_markdown(P, title):
    """A printable control map from the preset's own table."""
    lines = ["# %s - APC40 mkII control map" % title, ""]
    group = None
    for sc in P.map:
        if sc["group"] != group:
            group = sc["group"]
            lines += ["", "## %s" % group, "",
                      "| control | physical | path | note |", "|---|---|---|---|"]
        lines.append("| %s | %s | `%s` | %s |" % (
            sc["control"], sc["physical"], sc["path"],
            sc.get("note_text", "")))
    return "\n".join(lines) + "\n"
