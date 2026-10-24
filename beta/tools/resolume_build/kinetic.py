#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kinetic.py - the safety and cost rules a kinetic pass must obey, as code.

    from resolume_build import kinetic
    clip = kinetic.clamp_clip(clip, report)      # one clip dict, as design.py builds them

Numbers come from research/KINETIC_VJ_DEEP_RESEARCH.md (ITU-R BT.1702 / Ofcom / WCAG 2.3.1: no more
than three flashes a second over more than a quarter of the frame, no saturated-red flashing, no
strobe run longer than five seconds; seizure risk peaks at 10-20 Hz) and from the GPU notes in the
same report, checked 2026-10-23 against harvest/out (every parameter below exists with that range).
The performer's rule: motion comes from the external FFT and from sources with their own clock, not
from tempo-synced parameter animation.
"""

# Highest value a parameter (or an FFT ceiling on it) may take. Stroboscope / Strobe Frequency is
# 0..1 on this build; 0.35 keeps a flash-fading strobe near the three-flashes-a-second guideline.
PARAM_CAPS = {
    ("Stroboscope", "Frequency"): 0.35,
    ("Strobe", "Frequency"): 0.35,
    ("Stop Motion", "Frequency"): 0.55,
    ("Radial Cloner", "Clones"): 12.0,
    ("Linear Cloner", "Clones"): 10.0,
    ("Linear Cloner", "Tails"): 3.0,
    ("Grid Cloner", "Columns"): 6.0,
    ("Grid Cloner", "Rows"): 6.0,
    ("Iterate", "Iterations"): 0.45,
    ("Infinite Zoom", "Num Slices"): 8.0,
    ("Bloom", "Iterations"): 3.0,
    ("Sparkles", "Amount"): 800.0,
    ("Snowy", "Amount"): 120.0,           # harvest tops out at 200 on this build
    ("Goo", "Resolution"): 48.0,
    ("Trails", "Feedback"): 0.82,
}
# Parameters that must be at least this much, so captions stay readable.
PARAM_FLOORS = {
    ("Text Block", "Size"): 0.5,
    ("Text Animator", "Size"): 0.5,
}
FORCE = {("Stroboscope", "Fade"): True}
STROBE_SOURCES = ("Stroboscope",)
STROBE_EFFECTS = ("Strobe", "Stop Motion")
HEAVY_EFFECTS = ("Radial Cloner", "Linear Cloner", "Grid Cloner", "Iterate", "Infinite Zoom",
                 "Stingy Sphere", "Particle System")
MAX_STROBE_OPACITY = 0.45            # a strobing clip never fills the frame at full brightness
MAX_HEAVY_PER_CLIP = 1
MAX_EFFECTS_LOW_LAYERS = 2           # layers 1-4 carry the picture; keep their chains short


def _hex_rgb(colour):
    s = str(colour).lstrip("#")
    if len(s) < 6:
        return None
    try:
        return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return None


def is_saturated_red(colour):
    rgb = _hex_rgb(colour)
    return bool(rgb) and rgb[0] > 0.80 and rgb[1] < 0.20 and rgb[2] < 0.20


def soften_red(colour):
    """A saturated red becomes an amber of the same brightness (G raised to 0.32)."""
    rgb = _hex_rgb(colour)
    if not rgb:
        return colour
    alpha = str(colour).lstrip("#")[6:8] or "ff"
    return "#%02x%02x%02x%s" % (int(rgb[0] * 255), int(max(rgb[1], 0.32) * 255), int(rgb[2] * 255), alpha)


def _cap_params(name, params, fft, report, where):
    for (n, p), cap in PARAM_CAPS.items():
        if n != name:
            continue
        if p in params and float(params[p]) > cap:
            report("%s: %s/%s %s -> %s (kinetic cap)" % (where, n, p, params[p], cap))
            params[p] = cap
        spec = (fft or {}).get(p)
        if spec and float(spec.get("ceiling", 0)) > cap:
            report("%s: fft ceiling %s/%s %s -> %s (kinetic cap)" % (where, n, p, spec["ceiling"], cap))
            spec["ceiling"] = cap
            spec["floor"] = min(float(spec.get("floor", 0)), cap)
    for (n, p), lo in PARAM_FLOORS.items():
        if n == name and p in params and float(params[p]) < lo:
            report("%s: %s/%s %s -> %s (readability floor)" % (where, n, p, params[p], lo))
            params[p] = lo
    for (n, p), v in FORCE.items():
        if n == name and params.get(p) != v:
            params[p] = v
            report("%s: %s/%s forced to %r" % (where, n, p, v))


# A Stroboscope at or below this Frequency is a slow lamp (a breathing ON AIR light), not a flash:
# even if 1.0 meant 60 flashes a second it would stay at or under three. Slow lamps keep their
# designed opacity and colour; every faster strobe is capped.
SLOW_LAMP_FREQUENCY = 0.05


def _is_strobing(clip):
    if clip["source"] in STROBE_SOURCES:
        f = float(clip.get("params", {}).get("Frequency", 0.5))
        driven = (clip.get("fft") or {}).get("Frequency")
        if driven:
            f = max(f, float(driven.get("ceiling", 0.0)))
        return f > SLOW_LAMP_FREQUENCY
    return any(e.get("effect") in STROBE_EFFECTS for e in clip.get("effects") or [])


def clamp_clip(clip, report=lambda msg: None, where=None):
    """Apply every rule to one clip dict in place and return it. `report` gets one line per change."""
    where = where or "L%s C%s %s" % (clip.get("layer"), clip.get("column"), clip.get("name"))
    params = clip.setdefault("params", {})
    _cap_params(clip["source"], params, clip.get("fft"), report, where)
    effects = clip.get("effects") or []
    heavy = 0
    kept = []
    for e in effects:
        name = e.get("effect", "")
        _cap_params(name, e.setdefault("params", {}), e.get("fft"), report, where)
        if name in HEAVY_EFFECTS:
            heavy += 1
            if heavy > MAX_HEAVY_PER_CLIP:
                report("%s: second heavy effect %s dropped" % (where, name))
                continue
        kept.append(e)
    if clip.get("layer", 5) <= 4 and len(kept) > MAX_EFFECTS_LOW_LAYERS:
        report("%s: %d effects on a picture layer -> %d" % (where, len(kept), MAX_EFFECTS_LOW_LAYERS))
        kept = kept[:MAX_EFFECTS_LOW_LAYERS]
    clip["effects"] = kept
    if _is_strobing(clip):
        if float(clip.get("opacity", 1.0)) > MAX_STROBE_OPACITY:
            report("%s: strobing clip opacity %s -> %s" % (where, clip.get("opacity"), MAX_STROBE_OPACITY))
            clip["opacity"] = MAX_STROBE_OPACITY
        for k, v in list(params.items()):
            if k.startswith("Color") and is_saturated_red(v):
                params[k] = soften_red(v)
                report("%s: strobing %s was saturated red -> amber" % (where, k))
    return clip


def clamp_deck(deck, report=lambda msg: None):
    deck["clips"] = [clamp_clip(c, report) for c in deck["clips"]]
    return deck
