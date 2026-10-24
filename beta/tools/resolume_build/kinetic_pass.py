#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kinetic_pass.py - the shared kinetic pass: what packs/the-mixers/design.py piloted on
2026-10-23, generalised so every pack applies the same rules.

    from resolume_build import kinetic_pass as KP
    decks = KP.pass_decks(decks, KP.default_motion("#3cc6d0ff"), report=print)
    bible.update(KP.BIBLE_EXTRA)

Rules (captions on layer 5 are never touched):
  * GRAIN clips that are plain texture (Static, Blank) become one moving texture per deck, in
    the pack's colour, on its own clock, with one FFT lift and slow Infinite Zoom travel.
  * Generators that were frozen move: Metaballs, Shaper noise, Sine Wave, Spiral, Line Scape.
  * Open rings turn a little with the mids; BODY and FIGURE punch a little on the lows.
  * Every FFT release is capped so hits snap back.
  * Then resolume_build.kinetic.clamp_clip applies the safety and GPU rules.
The levels are the ones grounded in research/GROUNDING_CHATGPT.md. Motion comes from the
music (external FFT) and from sources with their own clock; never from tempo-synced animation.
"""
from . import kinetic as K

TEXT_SOURCES = ("Text Block", "Text Animator")
CLEAR = "#00000000"
GRAIN_REPLACEABLE = ("Static", "Blank")      # GRAIN clips that are texture, not drawing


def fft(param, band, floor, ceiling, gain, release):
    return {param: {"band": band, "gain": gain, "release": release, "floor": floor, "ceiling": ceiling}}


def default_motion(colour, dim=None):
    """Six moving textures for the GRAIN layer, one per deck in turn, in the pack's own colour."""
    dim = dim or colour
    return [
        ("Moving Floor", "Line Scape",
         {"Tilt": 68.0, "Direction": 0.0, "Position Y": 8.0, "Speed": 0.6, "Height": 6.0, "Jagginess": 0.15,
          "Wobble": 0.1, "Attenuation": 120.0, "Line Width": 0.25, "Fuzzyness": 0.3, "Color": colour,
          "Show Knots": False}, fft("Height", "low", 4.0, 12.0, 9.0, 200), 0.3),
        ("Signal Tunnel", "Tunnelines",
         {"Line Width": 0.01, "Zoom": 1.5, "Vertical": 0.08, "Frequency": 0.25, "Horizontal": 0.09,
          "Color 1": colour, "Color 2": CLEAR}, fft("Zoom", "low", 1.2, 2.4, 10.0, 160), 0.32),
        ("Slow Spiral", "Spiral",
         {"Direction": "Clockwise", "Speed": 0.35, "Zoom": 1.0, "Leafs": 3, "Spread Even": 1.0, "Fuzzyness": 0.3,
          "Color": dim, "BG Color": CLEAR}, fft("Zoom", "low", 0.9, 1.4, 9.0, 180), 0.3),
        ("Scan Lines", "Sine Wave",
         {"Waves": 12, "Mode": "Line", "Line Width": 0.02, "Fuzzyness": 0.3, "Direction": "Horizontal",
          "Mirror": False, "Frequency": 2.0, "Main Speed": 3.0, "Modulator": 2.0, "Modulation Depth": 0.5,
          "Modulator Speed": 2.0, "Amplitude": 0.06, "Position": 0.5, "Color": dim, "BG Color": CLEAR},
         fft("Amplitude", "mid", 0.04, 0.2, 9.0, 160), 0.3),
        ("Tracking Bars", "Sine Wave",
         {"Waves": 3, "Mode": "Line", "Line Width": 0.08, "Fuzzyness": 0.6, "Direction": "Vertical",
          "Mirror": False, "Frequency": 1.0, "Main Speed": 6.0, "Modulator": 2.0, "Modulation Depth": 0.6,
          "Modulator Speed": 3.0, "Amplitude": 0.04, "Position": 0.5, "Color": colour, "BG Color": CLEAR},
         fft("Amplitude", "high", 0.02, 0.1, 9.0, 120), 0.28),
        ("Counter Spiral", "Spiral",
         {"Direction": "Anti-clockwise", "Speed": 0.3, "Zoom": 1.2, "Leafs": 2, "Spread Even": 1.0,
          "Fuzzyness": 0.3, "Color": colour, "BG Color": CLEAR}, fft("Zoom", "low", 1.0, 1.5, 9.0, 180), 0.28),
    ]


TRAVEL = {"effect": "Infinite Zoom",
          "params": {"Rotation Speed": 0.08, "Zoom": 0.0, "Range": 1.4, "Alpha": 0.75, "Num Slices": 3}}
# a tunnel has no clock of its own and is rotation-symmetric, so it travels inward instead
TRAVEL_TUNNEL = {"effect": "Infinite Zoom",
                 "params": {"Rotation Speed": 0.04, "Zoom": 0.03, "Range": 1.4, "Alpha": 0.75, "Num Slices": 3}}

# effects that stay on a whole layer, and clip crossfades per layer (bible keys pack.py reads)
LAYER_EFFECTS = {
    "2": [{"effect": "Wave Warp", "params": {"Mode": 0.0, "Width": 0.5, "Speed": 0.1, "Angle": 0.25,
                                             "Pin edges?": True},
           "fft": fft("Height", "mid", 0.005, 0.025, 4.0, 110)}],
    "3": [{"effect": "Trails", "params": {"Mode": "Lighten", "Feedback": 0.30}, "wet_max": 0.25}],
    "4": [{"effect": "Bloom", "params": {"Threshold": 0.8, "Iterations": 2, "Size": 0.15},
           "fft": fft("Amount", "low", 0.10, 0.30, 6.0, 150)}],
    "8": [{"effect": "Shift RGB", "params": {"Mode": "Shift X", "R": 1.0, "G": 0.0, "B": -1.0},
           "fft": fft("Distance", "high", 0.002, 0.008, 2.0, 100)}],
}
LAYER_TRANSITION_MS = {"1": 150, "2": 100, "3": 100, "4": 100, "6": 100, "7": 150, "8": 100}
BIBLE_EXTRA = {"layer_effects": LAYER_EFFECTS, "layer_transition_ms": LAYER_TRANSITION_MS}


def _snappy(f, cap=260):
    for spec in (f or {}).values():
        spec["release"] = min(float(spec.get("release", 500)), cap)


def _widen(f, param, factor):
    spec = (f or {}).get(param)
    if spec:
        spec["ceiling"] = spec["floor"] + (spec["ceiling"] - spec["floor"]) * factor


def kinetic_clip(c, motion=None):
    """One clip dict (design.py shape) -> the same clip, moving. `motion` is one default_motion()
    entry, used for GRAIN texture clips; None leaves GRAIN alone."""
    layer, src = c["layer"], c["source"]
    p = c.setdefault("params", {})
    c.setdefault("fft", {})
    c.setdefault("effects", [])
    if layer == 5:
        return c                                              # captions stay put
    if layer == 7 and src in GRAIN_REPLACEABLE and motion:
        name, msrc, mparams, mfft, op = motion
        return {"layer": 7, "column": c["column"], "name": name[:18], "source": msrc,
                "params": dict(mparams), "fft": {k: dict(v) for k, v in mfft.items()},
                "effects": [dict(*(((TRAVEL_TUNNEL if msrc == "Tunnelines" else TRAVEL),)),
                                 params=dict((TRAVEL_TUNNEL if msrc == "Tunnelines" else TRAVEL)["params"]))],
                "opacity": op, "why": "Kinetic pass: the room keeps moving."}
    if src == "Metaballs":
        p["Speed"] = max(float(p.get("Speed", 0.0)), 0.8)
        _widen(c["fft"], "Size", 2.0)
    elif src == "Shaper":
        p["Noise Speed"] = 0.6
        p["Noise Amount"] = max(float(p.get("Noise Amount", 0.0)), 0.04)
    elif src == "Sine Wave":
        p["Main Speed"] = max(float(p.get("Main Speed", 1.0)), 4.0)
        p["Modulator Speed"] = max(float(p.get("Modulator Speed", 1.0)), 2.0)
        _widen(c["fft"], "Amplitude", 1.8)
    elif src == "Spiral":
        p["Speed"] = max(float(p.get("Speed", 1.0)), 0.3)
    elif src == "Line Scape" and abs(float(p.get("Speed", 1.0))) < 0.5:
        p["Speed"] = 0.5 if float(p.get("Speed", 1.0)) >= 0 else -0.5
    elif src == "Rings" and float(p.get("Gap", 0.0)) > 0:          # open rings turn with the mids
        c["effects"].append({"effect": "Transform", "params": {"Rotation Z": 0.0},
                             "fft": fft("Rotation Z", "mid", -12.0, 12.0, 4.0, 110)})
    if layer in (2, 3) and src not in ("Solid Color", "Blank") + TEXT_SOURCES and len(c["effects"]) < 4:
        c["effects"].append({"effect": "Transform", "params": {"Scale": 100.0},
                             "fft": fft("Scale", "low", 100.0, 108.0 if layer == 3 else 104.0, 6.0, 150)})
    _snappy(c["fft"])
    return c


# Sources that run on their own clock, with the test for "fast enough to see". The live audit of 2026-10-23 found
# about a third of the columns in the diagram-style packs frozen, because their GRAIN layer is a drawn texture
# (Lines, Checkered) the pass leaves alone. A column with none of these gets a moving texture on its AURA layer.
CLOCKED = {
    "Line Scape": lambda p: abs(float(p.get("Speed", 1.0))) >= 0.3,
    "Spiral": lambda p: float(p.get("Speed", 1.0)) >= 0.2,
    "Metaballs": lambda p: float(p.get("Speed", 0.0)) >= 0.5,
    "Sine Wave": lambda p: float(p.get("Frequency", 0.0)) > 0.0 and float(p.get("Main Speed", 1.0)) >= 2.0,
}                                       # a Shaper's noise wobble is too small to count as a clock
AURA_LAYER = 6
AURA_OPACITY = 0.22


def has_self_motion(clips):
    """True when some clip on layers 1-4, 6 or 7 moves on its own clock (the SCOPE and the captions do not count)."""
    for c in clips:
        if c.get("layer") in (5, 8):
            continue
        if float(c.get("opacity", 1.0)) < 0.1:
            continue
        test = CLOCKED.get(c.get("source"))
        if test and test(c.get("params", {})):
            return True
        for e in c.get("effects") or []:                          # a travelling Infinite Zoom is a clock too
            if e.get("effect") == "Infinite Zoom" and abs(float(e.get("params", {}).get("Zoom", 0.0))) >= 0.02:
                return True
    return False


def aura_fill(clips, column, motion_entry):
    """The clip list of one column with a moving texture on a Blank (or missing) AURA layer; unchanged when AURA
    carries something, so a designed wash is never replaced."""
    name, msrc, mparams, mfft, _op = motion_entry
    aura = next((c for c in clips if c.get("layer") == AURA_LAYER), None)
    if aura is not None and aura.get("source") != "Blank":
        return clips, False
    new = {"layer": AURA_LAYER, "column": column, "name": name[:18], "source": msrc, "params": dict(mparams),
           "fft": {k: dict(v) for k, v in mfft.items()}, "effects": [dict(TRAVEL, params=dict(TRAVEL["params"]))],
           "opacity": AURA_OPACITY, "why": "Kinetic pass: a column with no clock of its own gets one."}
    return [c for c in clips if c is not aura] + [new], True


def pass_decks(decks, motion=None, report=lambda msg: None, still=()):
    """kinetic_clip + the safety clamps on every clip of every deck (deck dicts with 'clips');
    deck i uses motion[i % len(motion)]. `still` is a set of (deck index from 0, column from 1)
    pairs the designer made deliberately still (a held beat, a flat master): those columns get
    the safety clamps only, no motion. A column that still has no clock of its own after the pass
    gets one on its Blank AURA layer."""
    still = set(still)
    for i, d in enumerate(decks):
        m = motion[i % len(motion)] if motion else None
        out = []
        for c in d["clips"]:
            if (i, c.get("column")) in still:
                out.append(K.clamp_clip(c, report))
            else:
                out.append(K.clamp_clip(kinetic_clip(c, m), report))
        clocked = [e for e in (motion or []) if e[1] in CLOCKED]
        if clocked:
            alt = clocked[(i + 1) % len(clocked)]
            cols = sorted({c.get("column") for c in out})
            filled = 0
            for col in cols:
                if (i, col) in still:
                    continue
                cc = [c for c in out if c.get("column") == col]
                if has_self_motion(cc):
                    continue
                cc2, did = aura_fill(cc, col, alt)
                if did:
                    out = [c for c in out if c.get("column") != col] + [K.clamp_clip(c, report) for c in cc2]
                    filled += 1
            if filled:
                report("deck %d: %d columns without a clock of their own got an AURA texture" % (i + 1, filled))
        d["clips"] = out
    return decks
