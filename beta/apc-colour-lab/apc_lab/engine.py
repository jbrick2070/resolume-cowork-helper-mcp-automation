#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.py - the colour lab's brain, with no I/O in it.

  Surface   what the APC40 mkII's pads would show for a stream of MIDI messages
            (the emulation the HTML demo draws, and the oracle the tests use).
  Router    sits between the controller and Resolume. It forwards every press
            untouched, re-colours Resolume's LED feedback through a theme, fills
            the pads Resolume leaves dark with an ambient animation, and answers
            each press with a touch effect. Everything it outputs is plain MIDI
            messages, so the same stream drives the demo and (through live.py)
            real hardware.

Everything here is a pure function of (messages in, time) so the Python engine
and its JavaScript port (demo/engine.js) can be checked against each other.
"""
import heapq
import json
import math
import os

from . import protocol as P

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "palette.json"), encoding="utf-8") as _f:
    PALETTE = json.load(_f)["colours"]
with open(os.path.join(HERE, "themes.json"), encoding="utf-8") as _f:
    _T = json.load(_f)
THEMES, THEME_ORDER = _T["themes"], _T["order"]

# The (on, dim) velocity pairs the packs' presets send, in hue order. Taken from
# resolume_build/apc.py LED_RGB; the colour NAMES there are a family off from the
# real LEDs (velocity 37 is azure, 45 is blue, 49 violet, 53 magenta, 57 rose),
# so this module indexes families by hue position, not by name.
FAMILIES = [(5, 6), (9, 10), (13, 14), (17, 18), (21, 22), (25, 26),
            (37, 38), (41, 42), (45, 46), (49, 50), (53, 54), (57, 58)]
FEEDBACK = {}
for _i, (_on, _dim) in enumerate(FAMILIES):
    FEEDBACK[_on] = (_i, "on")
    FEEDBACK[_dim] = (_i, "dim")
FEEDBACK[3] = (None, "on")        # white
FEEDBACK[2] = (None, "dim")


def hash01(a, b):
    """Deterministic 0..1 hash, bit-identical in demo/engine.js."""
    h = (a * 374761393 + b * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFFFF) / 0x1000000


def lerp(a, b, w):
    return [a[i] + (b[i] - a[i]) * w for i in range(3)]


def luma(rgb):
    return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255.0


# --------------------------------------------------------------- the surface --
class Surface(object):
    """What the pads show. Apply messages, then ask for a colour at a time."""

    def __init__(self):
        self.pads = {n: {"p": 0, "s": 0, "kind": "primary", "div": None, "t": 0.0}
                     for n in P.ALL_PADS}

    def apply(self, msg, t):
        kind, ch, note, vel = msg
        pad = self.pads.get(note)
        if pad is None or kind == P.CC:
            return
        mode, div = P.channel_to_mode(ch)
        if kind == P.NOTE_OFF or (kind == P.NOTE_ON and vel == 0):
            if mode == "primary":
                pad.update(p=0, s=0, kind="primary", div=None)
            else:
                pad.update(s=0, kind="primary", div=None)
            return
        if mode == "primary":
            pad.update(p=vel, s=0, kind="primary", div=None, t=t)   # resets any animation
        else:
            pad.update(s=vel, kind=mode, div=div, t=t)

    def rgb(self, note, t, bpm=120.0):
        pad = self.pads[note]
        prim, sec = PALETTE[pad["p"]], PALETTE[pad["s"]]
        if pad["kind"] == "primary":
            return list(prim)
        period = P.DIV_BEATS[pad["div"]] * 60.0 / bpm
        phase = (t - pad["t"]) / period
        if pad["kind"] == "oneshot":
            return list(sec) if 0 <= phase < 1 else list(prim)
        if pad["kind"] == "pulsing":
            return lerp(prim, sec, 0.5 - 0.5 * math.cos(2 * math.pi * phase))
        return list(sec) if (phase % 1.0) < 0.5 else list(prim)      # blinking


# ----------------------------------------------------------------- the router --
class Router(object):
    def __init__(self, theme="pack", bpm=120.0):
        self.bpm = bpm
        self.theme_key = theme
        self.base = {n: 0 for n in P.ALL_PADS}       # Resolume's feedback, raw velocity
        self.sent = {n: (0, None) for n in P.ALL_PADS}
        self.queue = []                              # (due, seq, msg)
        self.seq = 0
        self.presses = 0

    @property
    def theme(self):
        return THEMES[self.theme_key]

    def set_theme(self, key, t):
        self.theme_key = key
        return self.tick(t)

    # ---- the three inputs -------------------------------------------------
    def from_apc(self, msg, t):
        """A press from the controller. Returns (to_resolume, to_apc)."""
        out = []
        kind, ch, note, vel = msg
        if kind == P.NOTE_ON and vel > 0 and note in P.PAD_NOTES and ch == 1:
            self.presses += 1
            out = self._touch(note, t)
        return [msg], out

    def from_resolume(self, msg, t):
        """LED feedback from Resolume. Returns messages for the APC."""
        kind, ch, note, vel = msg
        if note in self.base and kind != P.CC:
            on = kind == P.NOTE_ON and vel > 0
            self.base[note] = vel if on else 0
            return self._refresh(note, t)
        return [msg]                                 # buttons, rings: untouched

    def tick(self, t):
        """Advance time: due touch messages, then ambient / re-theme diffs."""
        out = []
        while self.queue and self.queue[0][0] <= t:
            out.append(heapq.heappop(self.queue)[2])
        for note in P.ALL_PADS:
            out += self._refresh(note, t)
        return out

    # ---- what a pad should show ---------------------------------------------
    def desired(self, note, t):
        """(primary velocity, secondary or None); secondary = (vel, kind, div)."""
        v = self.base[note]
        th = self.theme
        if v:
            return self._remap(note, v, th)
        if note in P.SCENE_NOTES:
            return (0, None)
        return self._ambient(note, t, th)

    def _remap(self, note, v, th):
        mode = th["remap"]
        fam, state = FEEDBACK.get(v, (None, None))
        if mode == "identity" or state is None:
            return (v, None)
        playing = th.get("playing")
        sec = (playing["colour"], playing["kind"], playing["div"]) if playing and state == "on" else None
        if note in P.SCENE_NOTES and state == "on" and "scene" in th:
            s = th["scene"]
            return (s["colour"], (s["secondary"], s["kind"], s["div"]))
        if mode == "pairs":
            pairs = th["pairs"]
            pair = pairs[(fam if fam is not None else 0) % len(pairs)]
            if fam is None:                          # white keeps its brightness...
                sec = (pairs[0][0], playing["kind"], playing["div"]) if sec else None
                return (3 if state == "on" else 2, sec)   # ...and pulses to the theme's first colour
            if state != "on":
                return (pair[1], None)
            if playing:                              # the pair's own contrasting secondary
                sec = (pair[2], playing["kind"], playing["div"])
            return (pair[0], sec)
        greys = th["greys"]
        lum = luma(PALETTE[v])
        idx = 0 if lum < 0.12 else 1 if lum < 0.30 else 2 if lum < 0.50 else 3 if lum < 0.75 else 4
        if state == "on":
            idx = 4                                  # a playing pad is always the brightest grey
        else:
            idx = min(idx, 2)                        # loaded pads stay below it
        if mode == "luma-invert":
            idx = len(greys) - 1 - idx
        return (greys[idx], sec)

    def _ambient(self, note, t, th):
        a = th["ambient"]
        kind = a["kind"]
        col, row = P.pad_col_row(note)
        if kind == "none":
            return (0, None)
        if kind == "fill":
            return (a["colour"], None)
        cs = a["colours"]
        if kind == "pulse":
            return (cs[0], (cs[1], "pulsing", a["div"]))
        if kind == "stripes":
            return (cs[row % len(cs)], None)
        k = int(math.floor(t * a["rate"]))
        if kind == "flicker":
            if hash01(note, k) < a["density"]:
                return (cs[int(hash01(note + 101, k) * len(cs))], None)
            return (0, None)
        if kind == "chase":
            i = row * 8 + (col if row % 2 == 0 else 7 - col)
            return (cs[(i - k) % len(cs)], None)
        if kind == "rain":
            rel = (row + k + col * 3) % 10
            return (cs[rel], None) if rel < len(cs) else (0, None)
        if kind == "scan":
            d = abs(row - (k % 5))
            return (cs[d], None) if d < len(cs) else (0, None)
        return (0, None)

    # ---- diff emission ---------------------------------------------------------
    def _refresh(self, note, t):
        want = self.desired(note, t)
        have = self.sent[note]
        if want == have:
            return []
        out = []
        p, sec = want
        if p != have[0] or (sec is None and have[1] is not None) or sec != have[1]:
            out.append(P.on(1, note, p) if p else P.off(1, note))      # also cancels any animation
        if sec is not None:
            out.append(P.on(P.mode_to_channel(sec[1], sec[2]), note, sec[0]))
        self.sent[note] = want
        return out

    # ---- touch ---------------------------------------------------------------
    def _touch(self, note, t):
        tc = self.theme["touch"]
        kind = tc["kind"]
        if kind == "none":
            return []
        ch = P.mode_to_channel("oneshot", tc["div"])
        cs = tc["colours"]
        c0, r0 = P.pad_col_row(note)
        plan = []                                    # (delay, pad, colour)
        for m in P.PAD_NOTES:
            c, r = P.pad_col_row(m)
            dc, dr = abs(c - c0), abs(r - r0)
            if kind == "ripple":
                d = max(dc, dr)
                plan.append((d * tc["step"], m, cs[d % len(cs)]))
            elif kind == "cross" and (dc == 0 or dr == 0):
                d = dc + dr
                plan.append((d * tc["step"], m, cs[d % len(cs)]))
            elif kind == "invert":
                plan.append((0.0, m, cs[0] if self.base[m] else cs[1]))
        if kind == "sparkle":
            for j in range(tc["count"]):
                m = int(hash01(j + 1, self.presses) * 40)
                plan.append((hash01(j + 50, self.presses) * 0.35, m,
                             cs[int(hash01(j + 90, self.presses) * len(cs))]))
        out = []
        for delay, m, colour in sorted(plan, key=lambda x: (x[0], x[1])):
            msg = P.on(ch, m, colour)
            if delay <= 0:
                out.append(msg)
            else:
                self.seq += 1
                heapq.heappush(self.queue, (t + delay, self.seq, msg))
        return out


# ------------------------------------------------------------ rings and clock --
class RingMeter(object):
    """The 16 LED rings (8 track knobs, then 8 device knobs) as host-driven meters.

    In Mode 2 the host owns every LED, rings included. The ring style CC goes out
    once and again only when it changes; the value CC only when it changes, so a
    meter at 30 fps costs one CC per ring per change, not per frame.
    """

    def __init__(self):
        self.style = [None] * 16
        self.value = [None] * 16

    @staticmethod
    def _ccs(i):
        if i < 8:
            return P.TRACK_RING_VALUE_CC[i], P.TRACK_RING_STYLE_CC[i]
        return P.DEVICE_RING_VALUE_CC[i - 8], P.DEVICE_RING_STYLE_CC[i - 8]

    def set(self, i, level, style="volume"):
        """level 0..1 -> the CC messages that bring ring i to it."""
        out = []
        value_cc, style_cc = self._ccs(i)
        s = P.RING_STYLES[style]
        if self.style[i] != s:
            out.append(P.cc(1, style_cc, s))
            self.style[i] = s
        v = max(0, min(127, int(round(level * 127))))
        if self.value[i] != v:
            out.append(P.cc(1, value_cc, v))
            self.value[i] = v
        return out


def clock_ticks(t0, t1, bpm):
    """How many MIDI clock bytes (0xF8, 24 per quarter note) fall in (t0, t1]."""
    return int(math.floor(t1 * bpm * 24 / 60.0)) - int(math.floor(t0 * bpm * 24 / 60.0))
