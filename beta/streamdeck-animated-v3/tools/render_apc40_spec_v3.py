#!/usr/bin/env python3
"""Render the APC40 mkII V3 SPEC clip set (restrained set, contract-conformant).

Contract: react-kit/docs/APC40_SURFACE_ANIMATION_CONCEPTS.md (recommended picks,
decided V3 roadmap) + APC40_SURFACE_ANIMATION_REFERENCE.html (look target).
Supersedes the motion vocabulary of render_apc40_animated_v3.py (scan-sweeps,
token pulses, travelling thumbs, back-and-forth knob needles) which predates the
contract. Append-only: writes NEW files beside the old ones, touches nothing.

What it renders (under beta/streamdeck-animated-v3/):
  media/clips_spec/<family>/L###_<Name>__<state>.mov   per-control tiles
      Tier A (pads, scene, stop, select, track buttons, bank arrows,
              transport/small buttons, stop-all, master select, secondary):
              __idle  seamless full-sine loop at the stated length
              __active seamless latched loop  OR  __fire single-envelope loop
              (one attack/decay event + settled tail; period = stated loop
              length, so the event repeats at 0.14-0.2 Hz, far below 2 Hz)
      Tier B (rotary, small_rotary, vertical_fader, crossfader):
              __static value-agnostic caps only (knob cap with detent index,
              fader thumb-cap, centered crossfader puck). No text, no
              numerals, no tip segment, no lit tick counts.
  media/APC40_MKII_V3_TierB_Bed_Alpha.mov   full-frame STATIC bed:
      15-segment/270 deg knob arcs (uniform dim), fader slots + 11 uniform
      ticks, crossfader slot + centre detent, and every Tier B legend FIXED
      (labels can never move with live posy/rotz because they are not in the
      driven clips). Zero value readouts.
  build/spec_manifest_v3.json   per-control record incl. tile rects + Position
      X/Y values for the offline injector (pixel-true: pos = centre - (960,540)).
  screenshots/spec/             evidence stills (idle + active per family)

Geometry contract shared with V4 (do not drift): 15 arc segments on 270 deg,
11 fader ticks, 0.04u silhouette insets, u = control short edge.

Encoding: ProRes 4444 + alpha (yuva444p10le) - in-repo precedent. DXV3 HQ was
requested but the local ffmpeg's dxv encoder is DXT1-only with no alpha, so
ProRes stands (Resolume reads it; transcode to DXV in Alley later if wanted).

Usage:
  python render_apc40_spec_v3.py --families grid_pad          # one family
  python render_apc40_spec_v3.py --all                        # everything
  python render_apc40_spec_v3.py --bed                        # bed layer only
  python render_apc40_spec_v3.py --evidence                   # stills only
  python render_apc40_spec_v3.py --selftest                   # seam + law checks
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ constants
W, H = 1920, 1080
FPS = 30
SS = 3                                   # supersample for crisp small tiles

ROOT = Path(__file__).resolve().parents[1]
BUILD_INPUT = ROOT / "build" / "build_input_v3.json"
CLIPS = ROOT / "media" / "clips_spec"
BED_MOV = ROOT / "media" / "APC40_MKII_V3_TierB_Bed_Alpha.mov"
MANIFEST = ROOT / "build" / "spec_manifest_v3.json"
SHOTS = ROOT / "screenshots" / "spec"

FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

# State palette (contract). Chassis #b51d35 must NEVER appear here.
COLOR_BY_ID = {
    1: (232, 60, 46),    # red    #e83c2e
    2: (60, 208, 90),    # green  #3cd05a
    3: (245, 170, 34),   # amber  #f5aa22
    4: (40, 200, 220),   # cyan   #28c8dc
    5: (90, 120, 255),   # blue   #5a78ff
}
# Per-layer TRUE colors decoded from R1's text clips (Avenue stores COLOR as
# ABGR, not ARGB - the old 5-color COLOR_BY_ID mapping was a backwards decode;
# Jeffrey confirmed R1's rendered scheme is the correct one, 2026-07-20 eve).
ROW_COLORS_PATH = ROOT / "build" / "r1_layer_colors.json"
ROW_COLORS = json.load(open(ROW_COLORS_PATH))


def row_color(row):
    return tuple(ROW_COLORS[str(row["layer"])])

LEGEND = (230, 230, 230)     # #e6e6e6
KNOCKOUT = (12, 12, 12)      # #0c0c0c
BASE = (16, 16, 16)          # #101010 unlit surface
CAP_BODY = (22, 22, 22)      # thumb/puck body #161616-ish
CAP_RIM = (42, 42, 42)       # #2a2a2a

# V4-only readout glyphs - must never be baked into V3 art. Full census of
# R1's texts: 8 direction arrows + block/floor bars precede the numerals.
READOUT_GLYPHS = ("→", "←", "↑", "↓", "↖", "↗", "↘", "↙", "█", "▁")

# QA hook: render without any legend ink (glyph-mask isolation). Set from the
# QA harness via `render_apc40_spec_v3.TEXT_OFF = True`; never set in builds.
TEXT_OFF = False

# Display gain baked at export (Jeffrey's call, 2026-07-20): the contract's
# restrained 22-35% idle levels read near-black on the rig's monitor in a lit
# room. 3x lifts every lit element (rim 30%->90%, glows 66-90%) with ratios
# preserved until clamp; the chassis keeps its own designed level.
DISPLAY_GAIN = 3.0
IDLE_GAIN = 1.5      # idle = quiet empty buttons; the press pops at full gain

# Idle Tier A controls are EMPTY buttons (Jeffrey, 2026-07-20): the legend
# (name + MIDI address) appears only on the pressed/active/fire art.
def legend_on(state):
    return state not in ("idle",)

TIER_B = {"rotary", "small_rotary", "vertical_fader", "crossfader"}

# Play / Record / Session carry a HARDWARE-style circular LED floating a smidge
# ABOVE the key (Jeffrey, 2026-07-20 eve): green for Play, red for Record and
# Session, lit on press only. The tile grows upward to hold it (comp re-inject).
TRANSPORT_LED_LAYERS = (118, 120, 142)
TRANSPORT_LED_EXT = 20          # canvas px added above the key
TRANSPORT_LED_R = 6             # canvas px LED radius (12 px dia - reads at size)
TRANSPORT_LED_GAP = 4           # canvas px clear gap between LED and key top

# Knob enclosure rings, from the verified V2 chassis geometry
# (render_apc40_animated_v3.py CHASSIS_ELLIPSES / CHASSIS_CIRCLES; the rings
# that were re-centred in V2 to enclose knob + label). cx, cy, rx, ry.
KNOB_RINGS = [
    (191, 152, 56, 50), (321, 152, 56, 50), (451, 152, 56, 50), (581, 152, 56, 50),
    (711, 152, 56, 50), (840, 152, 56, 50), (970, 152, 56, 50), (1100, 152, 56, 50),
    (1337, 483, 50, 42), (1467, 483, 50, 42), (1597, 483, 50, 42), (1727, 483, 50, 42),
    (1337, 605, 50, 43), (1467, 605, 50, 43), (1597, 605, 50, 43), (1727, 605, 50, 43),
    (1216, 732, 48, 50),
    (1727, 303, 24, 24),                       # tempo small rotary (circle)
]
CHASSIS_STROKE = 3

# Stated loop lengths (seconds) per concept pick.
LOOPS = {
    "grid_pad":      {"idle": 6, "active": 2},          # 1A Ember Bed
    "scene_pad":     {"idle": 5, "fire": 5},            # 2A Soft Core
    "clip_stop":     {"idle": 7, "fire": 7},            # 3A Quiet Rim
    "stop_all":      {"idle": 7, "fire": 7},            # 3A Quiet Rim
    "track_select":  {"idle": 3, "active": 3},          # 4A Solid Latch
    "master_select": {"idle": 3, "active": 3},          # 4A Solid Latch
    "track_button":  {"idle": 4, "active": 4},          # 5A LED Dome
    "bank_polygon":  {"idle": 5, "fire": 5},            # 10B Directional Nudge
    "small_button":  {"idle": 6, "active": 2},          # 11A Standby Rim
    "secondary_text": {"idle": 6, "active": 2},         # 11A Standby Rim
    "rotary":        {"static": 1},
    "small_rotary":  {"static": 1},
    "vertical_fader": {"static": 1},
    "crossfader":    {"static": 1},
}


# ------------------------------------------------------------------ helpers
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def sine01(f, frames, cycles=1, phase=0.0):
    """0..1 full-sine, seamless: f % frames makes the wrap frame bit-exact
    (a raw f=frames evaluates the cosine at a float-jittered angle, which can
    flip a .5 rounding - the L046-53 seam bug)."""
    return 0.5 - 0.5 * math.cos(2 * math.pi * (cycles * (f % frames) / frames + phase))


def rgba(c, a):
    return (c[0], c[1], c[2], int(clamp(round(a), 0, 255)))


def font_fit(path, text, box_w, box_h, start):
    size = start
    while size >= 6:
        f = ImageFont.truetype(path, size)
        l, t, r, b = f.getbbox(text)
        if (r - l) <= box_w and (b - t) <= box_h:
            return f
        size -= 1
    return ImageFont.truetype(path, 6)


def split_legend(text):
    """'G1-5 N0/C1' -> ('G1-5', 'N0/C1'); readout tokens are dropped."""
    for g in READOUT_GLYPHS:
        if g in text:
            text = text.split(g)[0].strip()
    parts = text.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


class Tile:
    """Supersampled RGBA tile for one control rect; ink cannot leave it."""

    def __init__(self, rect):
        self.rect = rect                       # (x1, y1, x2, y2) canvas px
        self.w = max(2, int(round(rect[2] - rect[0])))
        self.h = max(2, int(round(rect[3] - rect[1])))
        self.img = Image.new("RGBA", (self.w * SS, self.h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.u = min(self.w, self.h)           # control short edge, canvas px

    def s(self, v):                            # canvas px -> tile px
        return v * SS

    def out(self):
        return self.img.resize((self.w, self.h), Image.LANCZOS)


def radial_field(w, h, cx, cy, radius):
    """1 at centre -> 0 at radius, clamped. (h, w) float array."""
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(radius, 1e-6)
    return np.clip(1.0 - d, 0.0, 1.0)


def paste_field(tile, field, color, alpha, mask=None):
    """Composite a scalar field (0..1) as `color` with peak `alpha` (0..255)."""
    a = (field * alpha).astype(np.uint8)
    if mask is not None:
        a = np.minimum(a, mask)
    rgb = np.zeros((a.shape[0], a.shape[1], 4), np.uint8)
    rgb[..., 0], rgb[..., 1], rgb[..., 2], rgb[..., 3] = color[0], color[1], color[2], a
    tile.img.alpha_composite(Image.fromarray(rgb, "RGBA"))


def rr_mask(w, h, radius, inset):
    """uint8 mask of a rounded rect inset by `inset` px (tile-space)."""
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        (inset, inset, w - 1 - inset, h - 1 - inset), radius=max(1, radius), fill=255)
    return np.array(m)


def ellipse_mask(w, h, inset):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse((inset, inset, w - 1 - inset, h - 1 - inset), fill=255)
    return np.array(m)


# ------------------------------------------------------------------ shared art
def draw_base(t: Tile, radius_u=0.09, fill=BASE, rim=None, rim_a=0):
    """Unlit base plate fills the silhouette; any lit rim strokes INSIDE the
    0.04u inset (bounds law - lit elements never touch the silhouette edge)."""
    r = max(2 * SS, int(t.s(t.u * radius_u)))
    t.d.rounded_rectangle((0, 0, t.img.width - 1, t.img.height - 1),
                          radius=r, fill=rgba(fill, 255))
    if rim is not None and rim_a > 0:
        ins = inset_px(t)
        t.d.rounded_rectangle((ins, ins, t.img.width - 1 - ins,
                               t.img.height - 1 - ins),
                              radius=max(2, r - ins), outline=rgba(rim, rim_a),
                              width=SS)
    return r


def inset_px(t: Tile):
    return max(1, int(round(0.04 * t.u))) * SS


def draw_witness(t: Tile, row, color, state, f, frames, loop_s):
    """Corner pin LED - DISABLED (Jeffrey, 2026-07-20): no corner indicator dots
    anywhere; buttons simply turn on/off. Kept as a no-op so every caller (and
    the bed's idle ghosts, which re-use these renderers) drops the pin at once."""
    return
    wb = row.get("witness_box")
    lb = row["label_box"]
    if not wb or wb == lb or wb == row.get("motion_box"):
        return
    # witness rect in tile space (tile rect may not be label_box for banks)
    rx1, ry1 = t.rect[0], t.rect[1]
    x1, y1, x2, y2 = ((wb[0] - rx1) * SS, (wb[1] - ry1) * SS,
                      (wb[2] - rx1) * SS, (wb[3] - ry1) * SS)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    r = (x2 - x1) * 0.32
    if state == "active":
        cyc = max(1, round(loop_s / 2))
        a = 178 + 77 * sine01(f, frames, cyc, 0.25)      # 70..100%
    else:
        a = 217                                          # on, steady 85%
    t.d.ellipse((cx - r - SS, cy - r - SS, cx + r + SS, cy + r + SS),
                fill=rgba(color, a * 0.25))              # 1px soft halo
    t.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(color, a))


def draw_legend2(t: Tile, label, addr, color_label, a_label, a_addr,
                 cy_frac=0.5, plate=0.0, addr_color=None):
    """Two-line static PRESSED legend centred at cy_frac of tile height.

    Only ever called for lit states (idle Tier A is legend-free), so it is
    tuned for the press: larger glyphs, a dark contrast stroke under light
    labels so they hold up over a bright glow, and a lifted address line.
    (Punch-list item 3, 2026-07-20.) The glyphs stay static frame-to-frame -
    only their size/contrast changed - so the 'legend moved' gate is untouched."""
    if TEXT_OFF:
        return
    w, h = t.img.width, t.img.height
    # Contrast pass (Jeffrey, 2026-07-20 eve): every pressed label + MIDI
    # address must be easily readable against its background - bigger start
    # size, heavier dark stroke under light glyphs, brighter address line.
    f1 = font_fit(FONT_SANS, label or " ", int(w * 0.90), int(h * 0.56), int(t.s(17)))
    f2 = font_fit(FONT_MONO, addr or " ", int(w * 0.90), int(h * 0.42),
                  max(7, int(f1.size * 0.74)))
    # light labels (white) ride over vivid glows -> a dark stroke lifts
    # contrast hard; dark knockout labels (on a bright fill) need none.
    light = sum(color_label) > 300
    sw = SS + 1 if light else 0
    sf = (0, 0, 0, 240) if light else None
    if light:
        a_label = 255
    a_addr = max(a_addr, 215)
    b1 = f1.getbbox(label) if label else (0, 0, 0, 0)
    b2 = f2.getbbox(addr) if addr else (0, 0, 0, 0)
    h1, h2 = b1[3] - b1[1], b2[3] - b2[1]
    gap = SS * 2 if (label and addr) else 0
    total = h1 + gap + h2
    cy = h * cy_frac
    top = cy - total / 2
    if plate > 0:
        pad = 3 * SS
        t.d.rectangle((0, top - pad, w, top + total + pad),
                      fill=(0, 0, 0, int(255 * plate)))
    if label:
        t.d.text(((w - (b1[2] - b1[0])) / 2 - b1[0], top - b1[1]), label,
                 font=f1, fill=rgba(color_label, a_label),
                 stroke_width=sw, stroke_fill=sf)
    if addr:
        ac = addr_color if addr_color is not None else color_label
        t.d.text(((w - (b2[2] - b2[0])) / 2 - b2[0], top + h1 + gap - b2[1]), addr,
                 font=f2, fill=rgba(ac, a_addr), stroke_width=sw, stroke_fill=sf)


# ------------------------------------------------------------------ Tier A
def tile_rect(row):
    """Whole-control tile rect. Pads even so ProRes is happy."""
    proto = row["prototype"]
    if proto in ("rotary", "small_rotary"):
        cx, cy, rx, ry = knob_ring(row)
        r = min(rx, ry)
        x1, y1, x2, y2 = cx - r, cy - r, cx + r, cy + r
    else:
        boxes = [row["label_box"]]
        wb = row.get("witness_box")
        if wb:
            boxes.append(wb)
        mb = row.get("motion_box")
        if mb:
            boxes.append(mb)
        x1 = min(b[0] for b in boxes)
        y1 = min(b[1] for b in boxes)
        x2 = max(b[2] for b in boxes)
        y2 = max(b[3] for b in boxes)
    x1, y1 = int(math.floor(x1)), int(math.floor(y1))
    x2, y2 = int(math.ceil(x2)), int(math.ceil(y2))
    if row["layer"] in TRANSPORT_LED_LAYERS:
        y1 -= TRANSPORT_LED_EXT                  # room for the floating LED
    if (x2 - x1) % 2:
        x2 += 1
    if (y2 - y1) % 2:
        y2 += 1
    return (x1, y1, x2, y2)


def knob_ring(row):
    lb = row["label_box"]
    cx0, cy0 = (lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2
    best = min(KNOB_RINGS, key=lambda e: (e[0] - cx0) ** 2 + (e[1] - cy0) ** 2)
    return best


def render_grid_pad(row, state, f, frames, loop_s):
    """1A Ember Bed. Idle: radial breath 22->30%. Active: 55->70% at 2 s."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    rad = draw_base(t, 0.13, rim=color, rim_a=89)               # 1px rim 35%
    ins = inset_px(t)
    mask = rr_mask(t.img.width, t.img.height, rad, ins)
    fld = radial_field(t.img.width, t.img.height,
                       t.img.width / 2, t.img.height / 2, t.s(t.u) * 0.75)
    if state == "idle":
        # Main buttons stay subtly ALIVE (Jeffrey, 2026-07-20 eve): a quiet
        # opacity glow, well under the old 22-30% ember; comp-side FFT adds the
        # music link. All other families idle as STATIC faint outlines.
        a = 30 + 16 * sine01(f, frames, 1, off)                 # ~12..18%
    else:
        a = 140 + 38 * sine01(f, frames, 1, off)                # 55..70%
    paste_field(t, fld, color, a, mask)
    lab, addr = split_legend(row["text"])
    if legend_on(state):
        draw_legend2(t, lab, addr, LEGEND, 229, 153, plate=0.40)
    draw_witness(t, row, color, "active" if state == "active" else "on",
                 f, frames, loop_s)
    return t.out()


def render_scene(row, state, f, frames, loop_s):
    """2A Soft Core. Idle: core 18->28%. Fire: widen bloom 75% -> settle."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    rad = draw_base(t, 0.18, rim=color, rim_a=64)
    ins = inset_px(t)
    mask = rr_mask(t.img.width, t.img.height, rad, ins)
    w, h = t.img.width, t.img.height
    xx = np.abs(np.mgrid[0:h, 0:w][1] - w / 2) / (w / 2)
    if state == "idle":
        # STATIC faint outline only at rest (Jeffrey, 2026-07-20 eve): the rim
        # from draw_base is the whole idle statement; no core, no motion.
        core = np.zeros((h, w))
        a = 0
    else:
        # single envelope: 100 ms attack to 75% widening 0.5->0.8, 600 ms release
        s = f / FPS
        if s <= 0.1:
            k = s / 0.1
            amp, width = 46 + (191 - 46) * k, 0.5 + 0.3 * k
        elif s <= 0.7:
            k = (s - 0.1) / 0.6
            k = 1 - (1 - k) ** 2
            amp, width = 191 + (59 - 191) * k, 0.8 - 0.3 * k
        else:
            amp, width = 46, 0.5                                 # settled tail == frame 0
        core = np.clip(1.0 - xx / max(width * 1.8, 1e-3), 0, 1)
        a = amp
    paste_field(t, core, color, a, mask)
    lab, addr = split_legend(row["text"])
    if legend_on(state):
        draw_legend2(t, lab, addr, LEGEND, 229, 153)
    draw_witness(t, row, color, "active" if state == "fire" else "on",
                 f, frames, loop_s)
    return t.out()


def render_stop(row, state, f, frames, loop_s):
    """3A Quiet Rim. Idle: rim 30% +/-8%, interior 4%. Fire: one envelope."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    if state == "idle":
        rim_a = 255 * 0.30          # STATIC faint outline at rest, no interior
        int_a = 0
    else:
        s = f / FPS
        if s <= 0.15:
            k = s / 0.15
            rim_a, int_a = 77 + 178 * k, 10 + 46 * k
        elif s <= 1.05:
            k = (s - 0.15) / 0.9
            k = 1 - (1 - k) ** 2
            rim_a, int_a = 255 - 178 * k, 56 - 46 * k
        else:
            rim_a, int_a = 77, 10                                # idle mean tail
    rad = max(2 * SS, int(t.s(t.u * 0.18)))
    t.d.rounded_rectangle((0, 0, t.img.width - 1, t.img.height - 1), radius=rad,
                          fill=rgba(BASE, 255))
    ins = inset_px(t)
    t.d.rounded_rectangle((ins, ins, t.img.width - 1 - ins, t.img.height - 1 - ins),
                          radius=rad, fill=rgba(color, int_a))
    t.d.rounded_rectangle((ins, ins, t.img.width - 1 - ins, t.img.height - 1 - ins),
                          radius=rad, outline=rgba(color, rim_a), width=SS)
    lab, addr = split_legend(row["text"])
    if legend_on(state):
        draw_legend2(t, lab, addr, LEGEND, 229, 153)
    draw_witness(t, row, color, "active" if state == "fire" else "on",
                 f, frames, loop_s)
    return t.out()


def render_select(row, state, f, frames, loop_s):
    """4A Solid Latch. Unselected: dark + rim 25%, colored legend.
    Selected: fill 85% micro-breath 80-88%, knockout legend."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    rad = max(2 * SS, int(t.s(t.u * 0.18)))
    t.d.rounded_rectangle((0, 0, t.img.width - 1, t.img.height - 1), radius=rad,
                          fill=rgba(BASE, 255))
    ins = inset_px(t)
    lab, addr = split_legend(row["text"])
    if state == "idle":
        t.d.rounded_rectangle((ins, ins, t.img.width - 1 - ins, t.img.height - 1 - ins),
                              radius=rad, outline=rgba(color, 64), width=SS)
        draw_witness(t, row, color, "on", f, frames, loop_s)
    else:
        a = 204 + 20 * (2 * sine01(f, frames, 1, off) - 1)       # 80..88%
        t.d.rounded_rectangle((ins, ins, t.img.width - 1 - ins, t.img.height - 1 - ins),
                              radius=rad, fill=rgba(color, a),
                              outline=rgba(color, 255), width=SS)
        draw_legend2(t, lab, addr, KNOCKOUT, 255, 230, addr_color=KNOCKOUT)
        draw_witness(t, row, color, "active", f, frames, loop_s)
    return t.out()


def render_track_button(row, state, f, frames, loop_s):
    """5A LED Dome. Off: base 6%, glyph 40%. On: dome 90% +/-5% breath."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    rad = draw_base(t, 0.16)
    ins = inset_px(t)
    mask = rr_mask(t.img.width, t.img.height, rad, ins)
    lab, addr = split_legend(row["text"])
    if state == "idle":
        # STATIC faint outline at rest (no wash), matching the other families.
        t.d.rounded_rectangle((ins, ins, t.img.width - 1 - ins,
                               t.img.height - 1 - ins),
                              radius=rad, outline=rgba(color, 64), width=SS)
        glyph_col, glyph_a = LEGEND, 102                         # 40%
    else:
        base_amt = np.ones(mask.shape) * (46 / 230)              # 18% base
        paste_field(t, base_amt, color, 230, mask)
        dome = radial_field(t.img.width, t.img.height,
                            t.img.width / 2, t.img.height * 0.40, t.s(t.u) * 0.40)
        a = 218 + 12 * (2 * sine01(f, frames, 1, off) - 1)       # 90% +/-5
        paste_field(t, dome, color, a, mask)
        glyph_col, glyph_a = (234, 255, 239), 255
    # glyph = LED hotspot, upper-centre; address below on the dark base zone
    if TEXT_OFF or not legend_on(state):
        draw_witness(t, row, color, "active" if state == "active" else "on",
                     f, frames, loop_s)
        return t.out()
    w2, h2 = t.img.width, t.img.height
    # pressed (active) legend gets a dark contrast stroke (item 3). track-button
    # geometry is fixed (the address hugs the corner witness cell), so we lift
    # contrast WITHOUT enlarging - no new collision. idle stays byte-identical.
    press = state == "active"
    lsw, lsf = (SS, (0, 0, 0, 224)) if press else (0, None)
    f1 = font_fit(FONT_SANS, lab, int(w2 * 0.6), int(h2 * 0.5), int(t.s(13)))
    f2 = font_fit(FONT_MONO, addr, int(w2 * 0.92), int(h2 * 0.28),
                  max(6, int(f1.size * 0.5)))
    b1 = f1.getbbox(lab)
    b2 = f2.getbbox(addr)
    t.d.text(((w2 - (b1[2] - b1[0])) / 2 - b1[0],
              h2 * 0.36 - (b1[3] - b1[1]) / 2 - b1[1]), lab,
             font=f1, fill=rgba(glyph_col, glyph_a), stroke_width=lsw, stroke_fill=lsf)
    t.d.text(((w2 - (b2[2] - b2[0])) / 2 - b2[0],
              h2 * 0.86 - (b2[3] - b2[1]) - b2[1]), addr,
             font=f2, fill=rgba((215, 215, 215), 215 if state == "active" else 120),
             stroke_width=lsw, stroke_fill=lsf)
    draw_witness(t, row, color, "active" if state == "active" else "on",
                 f, frames, loop_s)
    return t.out()


def render_bank(row, state, f, frames, loop_s):
    """10B Directional Nudge. Lit geometry inset 0.12u; press = 0.05u nudge
    + 60% bloom, single event; text never translates."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    w, h = t.img.width, t.img.height
    name = row["name"].lower()
    ins = t.s(0.12 * t.u)
    cx, cy = w / 2, h / 2
    sx, sy = (w / 2 - ins), (h / 2 - ins)
    if "up" in name:
        pts0 = [(cx, cy - sy), (cx - sx, cy + sy), (cx + sx, cy + sy)]
        dvec = (0, -1)
    elif "down" in name:
        pts0 = [(cx, cy + sy), (cx - sx, cy - sy), (cx + sx, cy - sy)]
        dvec = (0, 1)
    elif "left" in name:
        pts0 = [(cx - sx, cy), (cx + sx, cy - sy), (cx + sx, cy + sy)]
        dvec = (-1, 0)
    else:
        pts0 = [(cx + sx, cy), (cx - sx, cy - sy), (cx - sx, cy + sy)]
        dvec = (1, 0)
    if state == "idle":
        out_a = 255 * 0.45          # STATIC faint outline at rest
        fill_a = 0
        shift = 0.0
    else:
        s = f / FPS
        if s <= 0.15:
            k = math.sin((s / 0.15) * math.pi / 2)               # ease-out travel
            shift = 0.05 * t.u * k
        elif s <= 0.30:
            k = math.cos(((s - 0.15) / 0.15) * math.pi / 2)      # ease-in back
            shift = 0.05 * t.u * k
        else:
            shift = 0.0
        if s <= 0.12:                                            # 120 ms attack
            env = s / 0.12
        elif s <= 0.52:                                          # 400 ms decay
            env = 1 - (s - 0.12) / 0.4
        else:
            env = 0.0
        fill_a = 153 * env                                       # 60% bloom
        out_a = 255 * (0.45 + 0.55 * env)
    dx, dy = t.s(shift) * dvec[0], t.s(shift) * dvec[1]
    pts = [(x + dx, y + dy) for x, y in pts0]
    if fill_a > 0:
        t.d.polygon(pts, fill=rgba(color, fill_a))
    t.d.polygon(pts, outline=rgba(color, out_a), width=max(1, int(1.5 * SS)))
    lab, addr = split_legend(row["text"])
    # text fixed at the triangle's visual centroid (never translates); the
    # address rides the triangle's wide zone so it cannot cross the outline
    if TEXT_OFF or not legend_on(state):
        draw_witness(t, row, color, "active" if state == "fire" else "on",
                     f, frames, loop_s)
        return t.out()
    w2, h2 = t.img.width, t.img.height
    if "up" in name:
        ly, ay, gx = 0.55, 0.82, 0.5
    elif "down" in name:
        ly, ay, gx = 0.35, 0.60, 0.5
    elif "left" in name:
        ly, ay, gx = 0.40, 0.66, 0.58
    else:
        ly, ay, gx = 0.40, 0.66, 0.42
    f1 = font_fit(FONT_SANS, lab, int(w2 * 0.5), int(h2 * 0.4), int(t.s(11)))
    f2 = font_fit(FONT_MONO, addr, int(w2 * 0.86), int(h2 * 0.3),
                  max(6, int(f1.size * 0.55)))
    b1 = f1.getbbox(lab)
    b2 = f2.getbbox(addr)
    # contrast pass: fire-state legends get the dark stroke + brighter address
    t.d.text((w2 * gx - (b1[2] - b1[0]) / 2 - b1[0],
              h2 * ly - (b1[3] - b1[1]) / 2 - b1[1]), lab,
             font=f1, fill=rgba(LEGEND, 255),
             stroke_width=SS, stroke_fill=(0, 0, 0, 240))
    t.d.text((w2 * gx - (b2[2] - b2[0]) / 2 - b2[0],
              h2 * ay - (b2[3] - b2[1]) / 2 - b2[1]), addr,
             font=f2, fill=rgba(LEGEND, 215),
             stroke_width=SS, stroke_fill=(0, 0, 0, 240))
    draw_witness(t, row, color, "active" if state == "fire" else "on",
                 f, frames, loop_s)
    return t.out()


def render_transport(row, state, f, frames, loop_s):
    """11A Standby Rim. Idle: white rim 20% (+/-3%). Latched: color rim 90%,
    interior 25% fill breathing 22-28% at 2 s; legend stays white."""
    t = Tile(tile_rect(row))
    color = row_color(row)
    off = (row["layer"] * 0.137) % 1.0
    if row.get("prototype") == "secondary_text":
        # L119 is NOT a real transport button on this APC40 (Jeffrey, 2026-07-20):
        # the stop is STOP ALL, and PLAY/REC/SESSION carry an indicator light
        # above the key. Render it as ONLY that on/off indicator LED - no button
        # box, no label - dim when idle, lit when the connect toggles it on.
        if state == "idle":
            return t.out()      # truly EMPTY at rest (Jeffrey, 2026-07-20 eve)
        w, h = t.img.width, t.img.height
        cx, cy = w / 2, h / 2
        rr = min(w, h) * 0.34
        a = 178 + 77 * sine01(f, frames, max(1, round(loop_s / 2)), 0.25)
        t.d.ellipse((cx - rr - SS, cy - rr - SS, cx + rr + SS, cy + rr + SS),
                    fill=rgba(color, a * 0.25))
        t.d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=rgba(color, a))
        return t.out()
    indicator = row["layer"] in TRANSPORT_LED_LAYERS       # Play / Record / Session
    ext = t.s(TRANSPORT_LED_EXT) if indicator else 0       # LED headroom (tile px)
    key_h = t.img.height - ext                             # key box below the LED
    ku = min(t.w, t.h - (TRANSPORT_LED_EXT if indicator else 0))  # key short edge
    rad = max(2 * SS, int(t.s(ku * 0.18)))
    ins = max(1, int(round(0.04 * ku))) * SS
    t.d.rounded_rectangle((0, ext, t.img.width - 1, t.img.height - 1), radius=rad,
                          fill=rgba(BASE, 255))
    if state == "idle":
        rim_a = 255 * 0.20          # STATIC faint outline at rest
        t.d.rounded_rectangle((ins, ext + ins, t.img.width - 1 - ins,
                               t.img.height - 1 - ins),
                              radius=rad, outline=rgba((255, 255, 255), rim_a), width=SS)
    elif indicator:
        # press = key face lights WHITE (Jeffrey, 2026-07-20); label knocks out.
        wf = 255 * (0.90 + 0.05 * (2 * sine01(f, frames, 1, off) - 1))
        t.d.rounded_rectangle((ins, ext + ins, t.img.width - 1 - ins,
                               t.img.height - 1 - ins),
                              radius=rad, fill=rgba((245, 245, 245), wf),
                              outline=rgba((255, 255, 255), 255), width=SS)
    else:
        fill_a = 255 * (0.25 + 0.03 * (2 * sine01(f, frames, 1, off) - 1))
        t.d.rounded_rectangle((ins, ext + ins, t.img.width - 1 - ins,
                               t.img.height - 1 - ins),
                              radius=rad, fill=rgba(color, fill_a),
                              outline=rgba(color, 230), width=SS)
    lab, addr = split_legend(row["text"])
    if legend_on(state):
        key_cy_frac = (ext + key_h / 2) / t.img.height     # centre of the KEY box
        if indicator:
            draw_legend2(t, lab, addr, KNOCKOUT, 255, 220, addr_color=KNOCKOUT,
                         cy_frac=key_cy_frac)
        else:
            draw_legend2(t, lab, addr, LEGEND, 229, 153)
    # Play / Record / Session: HARDWARE-style circular LED floating a smidge
    # ABOVE the key with a clear gap (Jeffrey, 2026-07-20 eve): GREEN for Play,
    # RED for Record + Session; nothing at idle, lit on press.
    if indicator and state != "idle":
        led = (44, 230, 44) if row["layer"] == 118 else (226, 59, 59)  # pure green, not aquamarine
        rr = t.s(TRANSPORT_LED_R)
        cx = t.img.width / 2
        cy = ext - t.s(TRANSPORT_LED_GAP) - rr              # gap below LED bottom
        t.d.ellipse((cx - rr - 2 * SS, cy - rr - 2 * SS,
                     cx + rr + 2 * SS, cy + rr + 2 * SS),
                    fill=rgba(led, 56))                     # soft halo
        t.d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=rgba(led, 255))
        t.d.ellipse((cx - rr * 0.45, cy - rr * 0.55, cx + rr * 0.15, cy - rr * 0.05),
                    fill=rgba((255, 255, 255), 140))        # specular = domed LED
    return t.out()


# ------------------------------------------------------------------ Tier B caps
def render_knob_cap(row, state, f, frames, loop_s):
    """Value-agnostic knob cap. No arc (arc is static, in the bed), no text,
    no numerals - still contract-clean.

    Two species:
      rotary (16 grid knobs) - restrained detent index at 12 o'clock, as blessed.
      small_rotary (Cue CC47 / Tempo CC13) - these two caps are DRIVEN: the
        preset turns their Transform rotationz (Cue also its opacity 0.35->1).
        A thin centred detent reads as no motion when the hardware turns, so the
        driven caps get a bold, SINGLE-SIDED needle + rim + tip dot: the tip dot
        travelling the rim is the clearest possible turn cue, the asymmetry makes
        direction unambiguous, and the brighter body lets Cue's opacity swing
        read as well. (Punch-list item 1, 2026-07-20.)"""
    t = Tile(tile_rect(row))
    color = row_color(row)
    if row["prototype"] == "rotary":
        color = (240, 138, 36)      # hardware amber LED ring (Jeffrey) -
                                    # all 16 grid knobs; Tempo/Cue keep R1 colors
    w, h = t.img.width, t.img.height
    cx, cy = w / 2, h / 2
    ins = inset_px(t)
    knob_r = min(w, h) / 2 - t.s(CHASSIS_STROKE) - ins
    # Jeffrey 2026-07-20: extend the bold reads-on-turn needle to the 16 grid
    # rotaries too (they ride the same rotationz CCs), for one consistent knob
    # family. Both rotary species now use the driven treatment.
    driven = row["prototype"] in ("small_rotary", "rotary")
    if driven:
        disc_r = knob_r * 0.72
        t.d.ellipse((cx - disc_r, cy - disc_r, cx + disc_r, cy + disc_r),
                    fill=rgba((13, 13, 13), 255), outline=rgba(color, 255),
                    width=SS + 1)
        tip = disc_r * 0.90                                  # needle tip radius
        # single-sided needle: a short stub past centre, long reach to the rim
        t.d.line((cx, cy + disc_r * 0.16, cx, cy - tip),
                 fill=rgba(color, 255), width=SS + 2)
        dot = max(2 * SS, disc_r * 0.17)                     # bright tip witness
        t.d.ellipse((cx - dot, cy - tip - dot, cx + dot, cy - tip + dot),
                    fill=rgba(color, 255))
        hub = max(SS, disc_r * 0.14)                         # pivot reads as centre
        t.d.ellipse((cx - hub, cy - hub, cx + hub, cy + hub), fill=rgba(color, 255))
    else:
        disc_r = knob_r * 0.55
        t.d.ellipse((cx - disc_r, cy - disc_r, cx + disc_r, cy + disc_r),
                    fill=rgba((13, 13, 13), 255), outline=rgba(CAP_RIM, 255),
                    width=SS)
        t.d.line((cx, cy - disc_r * 0.92, cx, cy - disc_r * 0.45),
                 fill=rgba(color, 115), width=max(2, SS))
    return t.out()


def render_fader_cap(row, state, f, frames, loop_s):
    """Value-agnostic thumb-cap (0.9u wide, amber top edge). No text."""
    lane = row["motion_box"]
    lw = lane[2] - lane[0]
    cap_w = int(lw * 0.9)
    cap_h = 24
    lb = row["label_box"]
    cx = (lane[0] + lane[2]) / 2
    cy = (lb[1] + lb[3]) / 2
    rect = (int(cx - cap_w / 2), int(cy - cap_h / 2),
            int(cx - cap_w / 2) + (cap_w + cap_w % 2),
            int(cy - cap_h / 2) + cap_h)
    t = Tile(rect)
    color = row_color(row)
    w, h = t.img.width, t.img.height
    t.d.rounded_rectangle((0, SS * 2, w - 1, h - 1), radius=3 * SS,
                          fill=rgba(CAP_BODY, 255), outline=rgba(CAP_RIM, 255), width=SS)
    t.d.line((SS * 2, SS * 2, w - 1 - SS * 2, SS * 2), fill=rgba(color, 230),
             width=SS * 2)                                       # amber top edge 90%
    t.d.line((w * 0.2, h * 0.55, w * 0.8, h * 0.55), fill=rgba((60, 60, 60), 255),
             width=SS)                                           # grip line
    return t.out()


def render_xfader_cap(row, state, f, frames, loop_s):
    """Value-agnostic puck at the centre detent. No halo, no text."""
    lane = row["motion_box"]
    cy = (lane[1] + lane[3]) / 2
    cx = (lane[0] + lane[2]) / 2                                 # centre = detent
    pw, ph = 24, int((lane[3] - lane[1]) * 0.9)
    ph += ph % 2
    rect = (int(cx - pw / 2), int(cy - ph / 2),
            int(cx - pw / 2) + pw, int(cy - ph / 2) + ph)
    t = Tile(rect)
    w, h = t.img.width, t.img.height
    t.d.rounded_rectangle((0, 0, w - 1, h - 1), radius=3 * SS,
                          fill=rgba((20, 20, 20), 255), outline=rgba(CAP_RIM, 255),
                          width=SS)
    t.d.line((w / 2, h * 0.18, w / 2, h * 0.82), fill=rgba((70, 70, 70), 255), width=SS)
    return t.out()


RENDERERS = {
    "grid_pad": render_grid_pad,
    "scene_pad": render_scene,
    "clip_stop": render_stop,
    "stop_all": render_stop,
    "track_select": render_select,
    "master_select": render_select,
    "track_button": render_track_button,
    "bank_polygon": render_bank,
    "small_button": render_transport,
    "secondary_text": render_transport,
    "rotary": render_knob_cap,
    "small_rotary": render_knob_cap,
    "vertical_fader": render_fader_cap,
    "crossfader": render_xfader_cap,
}


# ------------------------------------------------------------------ Tier B bed
def render_bed(rows, all_rows=None):
    """Full-frame STATIC bed: knob arcs, fader slots + 11 ticks, crossfader
    slot + centre detent, all Tier B legends (fixed, readout-free) - PLUS a
    static idle image of every Tier A control at its breath mean, so a
    toggled-off control shows calm idle art instead of a hole."""
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    if all_rows:
        for row in all_rows:
            p = row["prototype"]
            if p in TIER_B:
                continue
            loop_s = LOOPS[p]["idle"]
            frames = int(FPS * loop_s)
            tile = RENDERERS[p](row, "idle", frames // 4, frames, loop_s)
            ta = np.array(tile)
            # grid pads: keep the bed ghost FAINT so the reactive (FFT) clip on
            # top is the dominant pad light and its beat swing is visible; all
            # other Tier A controls keep the calm half-alpha idle ghost.
            div = 8 if p == "grid_pad" else 2
            ta[..., 3] = ta[..., 3] // div        # ghost at IDLE_GAIN net
            tile = Image.fromarray(ta, "RGBA")
            rect = tile_rect(row)
            up = tile.resize((tile.width * SS, tile.height * SS), Image.NEAREST)
            big.alpha_composite(up, (rect[0] * SS, rect[1] * SS))
    d = ImageDraw.Draw(big)

    def text2(cx, top, label, addr, color, a1=229, a2=180, max_w=120, start=13):
        f1 = font_fit(FONT_SANS, label or " ", max_w * SS, 18 * SS, start * SS)
        f2 = font_fit(FONT_MONO, addr or " ", max_w * SS, 13 * SS,
                      max(7 * SS, int(f1.size * 0.72)))
        b1 = f1.getbbox(label)
        d.text((cx * SS - (b1[2] - b1[0]) / 2 - b1[0], top * SS - b1[1]), label,
               font=f1, fill=rgba(color, a1))
        y2 = top + (b1[3] - b1[1]) / SS + 2
        if addr:
            b2 = f2.getbbox(addr)
            d.text((cx * SS - (b2[2] - b2[0]) / 2 - b2[0], y2 * SS - b2[1]), addr,
                   font=f2, fill=rgba(color, a2))

    for row in rows:
        p = row["prototype"]
        color = row_color(row)
        if p == "rotary":
            color = (240, 138, 36)          # amber arcs match the amber caps
        lab, addr = split_legend(row["text"])
        if p in ("rotary", "small_rotary"):
            cx, cy, rx, ry = knob_ring(row)
            R = (min(rx, ry) - CHASSIS_STROKE - max(1, int(0.04 * 2 * min(rx, ry)))) * SS
            # 15 segments on 270 deg (start 135 deg, step 270/14), uniform dim;
            # stroke ~= reference ratio (4/55 of R), not the fat 0.05*2R blobs
            for j in range(15):
                a = math.radians(135 + j * (270 / 14))
                x1 = cx * SS + 0.66 * R * math.cos(a)
                y1 = cy * SS + 0.66 * R * math.sin(a)
                x2 = cx * SS + 0.84 * R * math.cos(a)
                y2 = cy * SS + 0.84 * R * math.sin(a)
                d.line((x1, y1, x2, y2), fill=rgba(color, 77),
                       width=max(2, int(round(0.073 * R))))
            # legend inside the arc's clear zone: safe width = the chord of the
            # segment inner circle at the text band (+/-11 px), not just the
            # hub disc - roughly 55 px on the big knobs instead of 42
            lb = row["label_box"]
            r_in = 0.66 * R / SS
            if r_in >= 20:
                chord = 2 * math.sqrt(max(r_in * r_in - 11 * 11, 1)) * 0.95
                text2((lb[0] + lb[2]) / 2, lb[1] + 1, lab, addr, LEGEND,
                      max_w=int(min(lb[2] - lb[0], chord)))
            else:
                # tiny ring (tempo): the legend can never be legible inside -
                # place it just below the ring in free chassis space
                text2(cx, cy + min(rx, ry) + 6, lab, addr, LEGEND, max_w=70)
        elif p == "vertical_fader":
            m = row["motion_box"]
            lane_cx = (m[0] + m[2]) / 2
            slot_w = 26
            sx1, sx2 = lane_cx - slot_w / 2, lane_cx + slot_w / 2
            sy1, sy2 = m[1] + 6, m[3] - 52
            d.rounded_rectangle((sx1 * SS, sy1 * SS, sx2 * SS, sy2 * SS),
                                radius=4 * SS, outline=rgba((64, 64, 64), 220),
                                width=SS)                    # neutral rails (ref #222)
            # 11 uniform ticks, right inner edge - value-agnostic (all equal)
            for i in range(11):
                ty = sy1 + 6 + (sy2 - sy1 - 12) * i / 10
                d.line(((sx2 - 8) * SS, ty * SS, (sx2 - 2) * SS, ty * SS),
                       fill=rgba(color, 64), width=SS)
            text2(lane_cx, sy2 + 10, lab, addr, LEGEND, max_w=int(m[2] - m[0]))
        elif p == "crossfader":
            m = row["motion_box"]
            cy = (m[1] + m[3]) / 2
            sx1, sx2 = m[0] + 4, m[2] - 4
            sh = 20
            d.rounded_rectangle((sx1 * SS, (cy - sh / 2) * SS, sx2 * SS,
                                 (cy + sh / 2) * SS), radius=5 * SS,
                                outline=rgba((64, 64, 64), 220), width=SS)
            dcx = (sx1 + sx2) / 2                                 # centre detent 45%
            d.line((dcx * SS, (cy - sh / 2 + 3) * SS, dcx * SS, (cy + sh / 2 - 3) * SS),
                   fill=rgba(color, 115), width=2 * SS)
            text2((sx1 + sx2) / 2, m[1] - 26, lab, addr, LEGEND, max_w=200)
    return big.resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ encode/io
def premultiply(img, gain=None):
    """Flatten onto black, alpha = 255 (alpha-proof for Add layers).

    Rig-proven chain: straight-alpha frames display translucent elements at
    full intensity, and PRE-multiplied frames get UN-premultiplied (rgb/a)
    back to full intensity - Avenue recovers straight rgb and its Add blend
    uses that rgb regardless of alpha. The only encoding that survives every
    interpretation is composite-over-black with opaque alpha: rgb carries
    exactly the authored contribution, and there is no alpha to divide by.
    On an additive wall over a black comp this is visually identical to true
    transparency."""
    # Premultiplied rgb with TRUE alpha kept (rig-proven final form):
    # - straight alpha -> Avenue displays translucent elements at full rgb
    # - opaque flatten -> full-frame layers OCCLUDE everything beneath
    # - premult rgb + true alpha -> correct levels AND correct transparency
    if gain is None:
        gain = DISPLAY_GAIN
    a = np.array(img, np.uint32)
    for c in range(3):
        a[..., c] = np.minimum((a[..., c] * a[..., 3] // 255) * gain, 255).astype(np.uint32)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def encode(frame_dir, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
         "-i", str(frame_dir / "f-%04d.png"), "-c:v", "prores_ks",
         "-profile:v", "4", "-pix_fmt", "yuva444p10le", str(out_path)],
        check=True)


def safe_name(row):
    return f"L{row['layer']:03d}_{row['name']}".replace(" ", "_").replace("/", "-")


def states_for(row):
    p = row["prototype"]
    if p in TIER_B:
        return ["static"]
    kinds = LOOPS[p]
    return ["idle"] + [k for k in ("active", "fire") if k in kinds]


def render_clip(row, state, workdir):
    p = row["prototype"]
    loop_s = LOOPS[p]["static" if state == "static" else state]
    frames = 30 if state == "static" else int(FPS * loop_s)
    fn = RENDERERS[p]
    fdir = workdir / "frames"
    if fdir.exists():
        shutil.rmtree(fdir)
    fdir.mkdir(parents=True)
    first = None
    for f in range(frames):
        img = fn(row, state, f, frames, loop_s)
        if f == 0:
            first = img.copy()
        g = IDLE_GAIN if state == "idle" else DISPLAY_GAIN
        premultiply(img, g).save(fdir / f"f-{f:04d}.png", compress_level=1)
    # seam check: frame `frames` must equal frame 0 (all looping states)
    seam_ok = True
    if state in ("idle", "active", "fire"):
        wrap = fn(row, state, frames, frames, loop_s)
        seam_ok = (np.array_equal(np.array(wrap), np.array(first)))
    fam_dir = CLIPS / p
    fam_dir.mkdir(parents=True, exist_ok=True)
    out = fam_dir / f"{safe_name(row)}__{state}.mov"
    encode(fdir, out)
    return out, frames, seam_ok, first


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--bed", action="store_true")
    ap.add_argument("--evidence", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--layers", nargs=2, type=int, default=None,
                    help="only rows with layer in [A,B] (chunked runs)")
    ap.add_argument("--states", nargs="*", default=None,
                    help="only re-render these states (e.g. active fire static); "
                         "unchanged states stay byte-identical for the regress gate")
    args = ap.parse_args()

    rows = json.load(open(BUILD_INPUT))
    if args.layers:
        rows_sel = [r for r in rows if args.layers[0] <= r["layer"] <= args.layers[1]]
    else:
        rows_sel = rows
    if args.families:
        rows_sel = [r for r in rows_sel if r["prototype"] in args.families]

    if args.bed or args.all:
        tb = [r for r in rows if r["prototype"] in TIER_B]
        bed = render_bed(tb, all_rows=rows)
        with tempfile.TemporaryDirectory() as td:
            fdir = Path(td)
            bed_pm = premultiply(bed)
            for f in range(30):
                bed_pm.save(fdir / f"f-{f:04d}.png", compress_level=1)
            encode(fdir, BED_MOV)
        SHOTS.mkdir(parents=True, exist_ok=True)
        matte = Image.new("RGB", bed.size, (0, 0, 0))
        matte.paste(bed, mask=bed.getchannel("A"))
        matte.save(SHOTS / "bed_full.png")
        print("bed ->", BED_MOV)

    if args.all or args.families:
        manifest = {"canvas": [W, H], "fps": FPS, "palette": COLOR_BY_ID,
                    "controls": []}
        prev_states = {}
        if MANIFEST.exists():
            manifest = json.load(open(MANIFEST))
            have = {c["layer"] for c in manifest["controls"]}
            prev_states = {c["layer"]: c.get("states", {}) for c in manifest["controls"]}
        else:
            have = set()
        seam_fail = []
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td)
            for row in rows_sel:
                # seed from the existing manifest so a --states run preserves the
                # states it did NOT re-render (they stay byte-identical on disk).
                rec = {"layer": row["layer"], "name": row["name"],
                       "prototype": row["prototype"], "color_id": row["color_id"],
                       "text": row["text"], "tier": "B" if row["prototype"] in TIER_B else "A",
                       "states": dict(prev_states.get(row["layer"], {})) if args.states else {}}
                for st in states_for(row):
                    if args.states and st not in args.states:
                        continue
                    out, frames, ok, first = render_clip(row, st, wd)
                    tr = (tile_rect(row) if row["prototype"] not in
                          ("vertical_fader", "crossfader") else None)
                    if row["prototype"] == "vertical_fader" or row["prototype"] == "crossfader":
                        tr = first and None
                    # tile rect from the actual rendered art
                    if not ok:
                        seam_fail.append((row["layer"], st))
                    rec["states"][st] = {
                        "file": str(out.relative_to(ROOT)).replace("\\", "/"),
                        "frames": frames, "seconds": frames / FPS,
                        "seam_ok": ok}
                # tile rect + injector Position values
                if row["prototype"] == "vertical_fader":
                    lane = row["motion_box"]
                    lb = row["label_box"]
                    cw = int((lane[2] - lane[0]) * 0.9)
                    rect = (int((lane[0] + lane[2]) / 2 - cw / 2),
                            int((lb[1] + lb[3]) / 2 - 12),
                            int((lane[0] + lane[2]) / 2 - cw / 2) + cw + cw % 2,
                            int((lb[1] + lb[3]) / 2 - 12) + 24)
                elif row["prototype"] == "crossfader":
                    lane = row["motion_box"]
                    ph = int((lane[3] - lane[1]) * 0.9)
                    ph += ph % 2
                    rect = (int((lane[0] + lane[2]) / 2 - 12),
                            int((lane[1] + lane[3]) / 2 - ph / 2),
                            int((lane[0] + lane[2]) / 2 - 12) + 24,
                            int((lane[1] + lane[3]) / 2 - ph / 2) + ph)
                else:
                    rect = tile_rect(row)
                cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
                rec["tile_rect"] = list(rect)
                rec["position_x"] = cx - W / 2
                rec["position_y"] = cy - H / 2
                manifest["controls"] = [c for c in manifest["controls"]
                                        if c["layer"] != row["layer"]] + [rec]
                print(f"L{row['layer']:03d} {row['prototype']:14s} "
                      f"{' '.join(rec['states'])}")
        manifest["controls"].sort(key=lambda c: c["layer"])
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        json.dump(manifest, open(MANIFEST, "w"), indent=1)
        if seam_fail:
            raise SystemExit(f"SEAM FAIL: {seam_fail}")
        print(f"{len(rows_sel)} controls -> {CLIPS}  (manifest {MANIFEST.name})")

    if args.evidence:
        SHOTS.mkdir(parents=True, exist_ok=True)
        seen = set()
        for row in rows:
            p = row["prototype"]
            if p in seen:
                continue
            seen.add(p)
            for st in states_for(row):
                loop_s = LOOPS[p]["static" if st == "static" else st]
                frames = 30 if st == "static" else int(FPS * loop_s)
                peak = {"idle": frames // 4, "active": frames // 4,
                        "fire": int(0.12 * FPS), "static": 0}[st]
                img = RENDERERS[p](row, st, peak, frames, loop_s)
                matte = Image.new("RGB", img.size, (0, 0, 0))
                matte.paste(img, mask=img.getchannel("A"))
                matte = matte.resize((img.width * 3, img.height * 3), Image.NEAREST)
                matte.save(SHOTS / f"{p}__{st}.png")
        print("evidence stills ->", SHOTS)

    if args.selftest:
        errs = []
        # 1. no chassis red anywhere near any control tile
        target = np.array([181, 29, 53])
        for row in rows_sel:
            for st in states_for(row):
                loop_s = LOOPS[row["prototype"]]["static" if st == "static" else st]
                frames = 30 if st == "static" else int(FPS * loop_s)
                img = np.array(RENDERERS[row["prototype"]](row, st, frames // 3,
                                                           frames, loop_s))
                # a deliberate CHASSIS_RED draw keeps the exact source rgb in
                # RGBA space; antialiased state-red fringes do not get near it
                lit = img[..., 3] > 64
                if lit.any():
                    d = np.abs(img[..., :3].astype(int) - target).sum(axis=-1)
                    if (lit & (d < 12)).any():
                        errs.append(f"chassis-red pixels: L{row['layer']} {st}")
        # 2. Tier B text strings carry no readouts (they carry no text at all)
        for row in rows_sel:
            if row["prototype"] in TIER_B:
                lab, addr = split_legend(row["text"])
                for g in READOUT_GLYPHS:
                    if g in lab + addr:
                        errs.append(f"readout glyph in Tier B legend: L{row['layer']}")
        print("SELFTEST", "PASS" if not errs else f"FAIL {errs[:8]}")
        if errs:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
