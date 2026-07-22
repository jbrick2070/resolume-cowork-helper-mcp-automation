#!/usr/bin/env python3
"""Render the APC40 mkII animated "controller twin" V3 surface (offline, deterministic).

Design contract (see docs/APC40_ANIMATED_V3_SPEC.md):
  * One novel animated vector clip per physical control, matched to that
    control's silhouette and rendered strictly INSIDE its own geometry box.
  * Bounds are enforced STRUCTURALLY: every control element is drawn into a
    sub-tile of exactly its box size (supersampled), then pasted at the box
    origin.  Ink physically cannot leave its control, so controls can never
    overlap -- the R1 geometry boxes are already collision-free at PADDING=4.
  * Multicolor language is inherited from the ORIGINAL composition's per-clip
    ColorId (1..5).  Deep Akai red #b51d35 is reserved for the chassis layer.
  * Same on-screen TEXT content as R1 is rendered into each clip.
  * Black / transparent background.  Seamless loop.

Outputs (under beta/streamdeck-animated-v3/):
  media/APC40_MKII_Animated_Twin_V3_Surface_Alpha.mov   full-frame ProRes4444 alpha
  media/APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov   deep-red chassis, ProRes4444 alpha
  media/clips/<Control Name>.mov                          148 small per-control clips
  screenshots/*.png                                       preview stills / contact sheet
  build/animation_manifest_v3.json                        per-control color+motion record

Usage:
  python render_apc40_animated_v3.py --preview          # a few stills on black, fast
  python render_apc40_animated_v3.py --full             # all frames + encode everything
  python render_apc40_animated_v3.py --full --no-clips  # surface+chassis only
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ----------------------------------------------------------------------------- config
W, H = 1920, 1080
FPS = 30
LOOP_SECONDS = 4
FRAMES = FPS * LOOP_SECONDS          # 120, seamless
SS = 2                                # supersample factor for anti-aliased vectors

ROOT = Path(__file__).resolve().parents[1]          # .../streamdeck-animated-v3
BUILD_INPUT = ROOT / "build" / "build_input_v3.json"
MEDIA = ROOT / "media"
CLIPS = MEDIA / "clips"
SHOTS = ROOT / "screenshots"
MANIFEST = ROOT / "build" / "animation_manifest_v3.json"
SCRATCH = Path(os.environ.get("V3_SCRATCH", "/sessions/ecstatic-eager-mayer/mnt/outputs/v3_frames"))

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# Vivid multicolor language derived from the ORIGINAL clip ColorId (1..5).
# 1 = stop / record / danger, 2 = play / activator / scene, 3 = faders+knobs,
# 4 = selects / master, 5 = navigation / crossfader / cue.
COLOR_BY_ID = {
    1: (232, 60, 46),     # red
    2: (60, 208, 90),     # green
    3: (245, 170, 34),    # amber
    4: (40, 200, 220),    # cyan
    5: (90, 120, 255),    # blue
}
WHITE = (238, 240, 245)
CHASSIS_RED = (181, 29, 53)          # #b51d35 deep Akai red -- chassis only
BG = (8, 7, 9)                        # matte for preview only; real output is transparent


# ----------------------------------------------------------------------------- helpers
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def fit_font(text, box_w, box_h, max_px):
    """Largest DejaVu mono bold that fits text in box (single line)."""
    size = max_px
    while size >= 6:
        f = ImageFont.truetype(FONT_PATH, size)
        l, t, r, b = f.getbbox(text)
        if (r - l) <= box_w and (b - t) <= box_h:
            return f, (r - l), (b - t)
        size -= 1
    f = ImageFont.truetype(FONT_PATH, 6)
    l, t, r, b = f.getbbox(text)
    return f, (r - l), (b - t)


def box_wh(box):
    x1, y1, x2, y2 = box
    return int(round(x2 - x1)), int(round(y2 - y1))


def new_tile(box):
    w, h = box_wh(box)
    w = max(1, w) * SS
    h = max(1, h) * SS
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def paste_tile(canvas, tile, box):
    """Paste an SS-sized element tile onto the supersampled canvas at box*SS.

    The canvas is W*SS x H*SS; tiles are built at box_wh*SS.  Pasting at
    box*SS keeps every element in register with the chassis, and the final
    downscale to (W, H) restores true position/size.  Ink stays inside its box.
    """
    x1, y1 = int(round(box[0] * SS)), int(round(box[1] * SS))
    w, h = box_wh(box)
    w, h = max(1, w) * SS, max(1, h) * SS
    if tile.size != (w, h):
        tile = tile.resize((w, h), Image.LANCZOS)
    canvas.alpha_composite(tile, (x1, y1))


def breath(frame, cycles, offset):
    return 0.5 + 0.5 * math.sin(2 * math.pi * (cycles * frame / FRAMES + offset))


def tri(frame, cycles, offset):
    """0..1 triangle wave, seamless over the loop."""
    p = (cycles * frame / FRAMES + offset) % 1.0
    return 2 * p if p < 0.5 else 2 * (1 - p)


def rgba(color, a):
    return (color[0], color[1], color[2], int(clamp(a, 0, 255)))


# ----------------------------------------------------------------------------- text
def draw_label(tile, text, color, box, frame, offset, dim=1.0):
    """Draw the control's text with an alive scan-highlight sweep + token pulse.

    The text CONTENT and position never change; only illumination animates.
    Two tokens (name / MIDI address) alternate emphasis so the label 'breathes'
    like a Tamagotchi read-out while staying legible.
    """
    w, h = tile.size
    pad = 2 * SS
    d = ImageDraw.Draw(tile)
    font, tw, th = fit_font(text, w - 2 * pad, h - 2 * pad, int(h * 0.60))
    tx = (w - tw) // 2
    ty = (h - th) // 2
    g = breath(frame, 1, offset)
    base_a = int((175 + 55 * g) * dim)
    # native-color halo: LED bloom + legibility on any tile colour
    for ox, oy in ((SS, 0), (-SS, 0), (0, SS), (0, -SS)):
        d.text((tx + ox, ty + oy), text, font=font, fill=rgba(color, int(70 * dim)), anchor="la")
    # crisp near-white body -- always readable
    d.text((tx, ty), text, font=font, fill=rgba(WHITE, base_a), anchor="la")
    # alive: the MIDI token (after the first space) pulses in native colour,
    # like a Tamagotchi status read-out refreshing.  Content never changes.
    if " " in text:
        head, tail = text.split(" ", 1)
        pulse = max(0.0, math.sin(2 * math.pi * (frame / FRAMES + offset)))
        if pulse > 0:
            hb = font.getbbox(head + " ")
            d.text((tx + (hb[2] - hb[0]), ty), tail, font=font,
                   fill=rgba(color, int(205 * pulse * dim)), anchor="la")
    # subtle scan-highlight sweep travelling across the label
    band = int((frame / FRAMES + offset * 0.5) % 1.0 * (w + 30 * SS)) - 15 * SS
    for dx in range(-5 * SS, 5 * SS):
        x = band + dx
        if 0 <= x < w:
            a = int(30 * dim * max(0.0, 1 - abs(dx) / (5 * SS)))
            d.line((x, pad, x, h - pad), fill=rgba(WHITE, a), width=1)


# ----------------------------------------------------------------------------- shapes
def draw_tile_bg(tile, color, frame, offset, radius, alpha_lo=26, alpha_hi=96, outline=True):
    w, h = tile.size
    d = ImageDraw.Draw(tile)
    g = breath(frame, 1, offset)
    fill_a = int(alpha_lo + (alpha_hi - alpha_lo) * g)
    d.rounded_rectangle((SS, SS, w - SS, h - SS), radius=max(2, radius * SS),
                        fill=rgba(color, fill_a))
    if outline:
        oa = int(120 + 100 * g)
        d.rounded_rectangle((SS, SS, w - SS, h - SS), radius=max(2, radius * SS),
                            outline=rgba(color, oa), width=max(1, SS))


def draw_witness_led(canvas, color, wbox, frame, offset):
    """Small blinking LED in the witness corner -- keeps the witness meaning alive."""
    tile = new_tile(wbox)
    w, h = tile.size
    d = ImageDraw.Draw(tile)
    g = breath(frame, 2, offset)
    r = min(w, h) * 0.42
    cx, cy = w / 2, h / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(color, int(80 + 150 * g)))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(WHITE, int(60 + 90 * g)), width=max(1, SS))
    paste_tile(canvas, tile, wbox)


# ----------------------------------------------------------------------------- controls
def render_pad(canvas, row, frame, family_radius=3, dim=1.0):
    color = COLOR_BY_ID[row["color_id"]]
    off = (row["layer"] * 0.137) % 1.0
    lbox = row["label_box"]
    tile = new_tile(lbox)
    draw_tile_bg(tile, color, frame, off, family_radius)
    draw_label(tile, row["text"], color, lbox, frame, off, dim=dim)
    paste_tile(canvas, tile, lbox)
    wb = row["witness_box"]
    if wb and wb != lbox:
        draw_witness_led(canvas, color, wb, frame, off)


def render_rotary(canvas, row, frame, small=False):
    color = COLOR_BY_ID[row["color_id"]]
    off = (row["layer"] * 0.137) % 1.0
    # knob art strictly inside the witness (knob) box
    kbox = row["witness_box"]
    ktile = new_tile(kbox)
    w, h = ktile.size
    d = ImageDraw.Draw(ktile)
    g = breath(frame, 1, off)
    m = 1 * SS
    d.ellipse((m, m, w - m, h - m), fill=rgba(color, int(30 + 60 * g)),
              outline=rgba(color, int(150 + 90 * g)), width=max(1, SS))
    # rotating indicator (Rotation Z feel), sweeps back and forth, stays inside knob
    ang = (-math.pi / 2) + (tri(frame, 1, off) - 0.5) * math.radians(280)
    cx, cy = w / 2, h / 2
    rr = min(w, h) * 0.34
    d.line((cx, cy, cx + math.cos(ang) * rr, cy + math.sin(ang) * rr),
           fill=rgba(WHITE, 230), width=max(1, SS + 1))
    d.ellipse((cx - 2 * SS, cy - 2 * SS, cx + 2 * SS, cy + 2 * SS), fill=rgba(WHITE, 200))
    paste_tile(canvas, ktile, kbox)
    # label below (own box)
    lbox = row["label_box"]
    ltile = new_tile(lbox)
    draw_label(ltile, row["text"], color, lbox, frame, off)
    paste_tile(canvas, ltile, lbox)


def render_fader(canvas, row, frame):
    color = COLOR_BY_ID[row["color_id"]]
    off = (row["layer"] * 0.137) % 1.0
    mbox = row["motion_box"] or row["witness_box"]
    tile = new_tile(mbox)
    w, h = tile.size
    d = ImageDraw.Draw(tile)
    # slot
    slot_w = max(6 * SS, int(w * 0.30))
    sx1 = (w - slot_w) // 2
    d.rounded_rectangle((sx1, 4 * SS, sx1 + slot_w, h - 4 * SS), radius=3 * SS,
                        outline=rgba(color, 150), width=max(1, SS))
    # travelling thumb (Position Y), stays inside slot
    thumb_h = max(10 * SS, int(h * 0.10))
    travel = (h - 8 * SS - thumb_h) * (1 - tri(frame, 1, off))
    ty = 4 * SS + int(travel)
    g = breath(frame, 2, off)
    d.rounded_rectangle((sx1 - 2 * SS, ty, sx1 + slot_w + 2 * SS, ty + thumb_h),
                        radius=3 * SS, fill=rgba(color, int(150 + 90 * g)),
                        outline=rgba(WHITE, 180), width=max(1, SS))
    paste_tile(canvas, tile, mbox)
    # small label box
    lbox = row["label_box"]
    ltile = new_tile(lbox)
    draw_tile_bg(ltile, color, frame, off, 3, alpha_lo=20, alpha_hi=70)
    draw_label(ltile, row["text"], color, lbox, frame, off)
    paste_tile(canvas, ltile, lbox)


def render_crossfader(canvas, row, frame):
    color = COLOR_BY_ID[row["color_id"]]
    off = (row["layer"] * 0.137) % 1.0
    mbox = row["motion_box"] or row["witness_box"]
    tile = new_tile(mbox)
    w, h = tile.size
    d = ImageDraw.Draw(tile)
    slot_h = max(6 * SS, int(h * 0.30))
    sy1 = (h - slot_h) // 2
    d.rounded_rectangle((4 * SS, sy1, w - 4 * SS, sy1 + slot_h), radius=3 * SS,
                        outline=rgba(color, 150), width=max(1, SS))
    puck_w = max(10 * SS, int(w * 0.10))
    travel = (w - 8 * SS - puck_w) * tri(frame, 1, off)
    px = 4 * SS + int(travel)
    g = breath(frame, 2, off)
    d.rounded_rectangle((px, sy1 - 2 * SS, px + puck_w, sy1 + slot_h + 2 * SS),
                        radius=3 * SS, fill=rgba(color, int(150 + 90 * g)),
                        outline=rgba(WHITE, 180), width=max(1, SS))
    paste_tile(canvas, tile, mbox)
    lbox = row["label_box"]
    ltile = new_tile(lbox)
    draw_label(ltile, row["text"], color, lbox, frame, off)
    paste_tile(canvas, ltile, lbox)


def render_bank(canvas, row, frame):
    color = COLOR_BY_ID[row["color_id"]]
    off = (row["layer"] * 0.137) % 1.0
    lbox = row["label_box"]
    tile = new_tile(lbox)
    w, h = tile.size
    d = ImageDraw.Draw(tile)
    g = breath(frame, 1, off)
    name = row["name"].lower()
    cx, cy = w / 2, h / 2
    s = min(w, h) * 0.32
    if "up" in name:
        pts = [(cx, cy - s), (cx - s, cy + s), (cx + s, cy + s)]
    elif "down" in name:
        pts = [(cx, cy + s), (cx - s, cy - s), (cx + s, cy - s)]
    elif "left" in name:
        pts = [(cx - s, cy), (cx + s, cy - s), (cx + s, cy + s)]
    else:
        pts = [(cx + s, cy), (cx - s, cy - s), (cx - s, cy + s)]
    d.polygon(pts, fill=rgba(color, int(120 + 110 * g)), outline=rgba(WHITE, 160))
    paste_tile(canvas, tile, lbox)
    wb = row["witness_box"]
    if wb and wb != lbox:
        draw_witness_led(canvas, color, wb, frame, off)


PROTO_RADIUS = {
    "grid_pad": 4, "scene_pad": 6, "clip_stop": 4, "track_select": 5,
    "track_button": 3, "small_button": 6, "secondary_text": 4, "stop_all": 6,
    "master_select": 5,
}


def render_control(canvas, row, frame):
    p = row["prototype"]
    if p in ("rotary", "small_rotary"):
        render_rotary(canvas, row, frame, small=(p == "small_rotary"))
    elif p == "vertical_fader":
        render_fader(canvas, row, frame)
    elif p == "crossfader":
        render_crossfader(canvas, row, frame)
    elif p == "bank_polygon":
        render_bank(canvas, row, frame)
    else:
        render_pad(canvas, row, frame, family_radius=PROTO_RADIUS.get(p, 4))


# ----------------------------------------------------------------------------- chassis
CHASSIS_LINES = [
    (112, 66, 1808, 66), (1808, 66, 1808, 1022), (112, 1022, 1808, 1022), (112, 66, 112, 1022),
    (1272, 174, 1272, 1010),
    (122, 261, 1260, 261), (122, 321, 1260, 321), (122, 381, 1260, 381), (122, 442, 1260, 442),
    (122, 506, 1260, 506), (122, 576, 1260, 576), (122, 640, 1260, 640), (122, 760, 1158, 760),
    (1284, 392, 1796, 392), (1284, 544, 1796, 544), (1284, 662, 1796, 662),
    (1284, 729, 1796, 729), (1284, 800, 1796, 800), (1284, 910, 1796, 910),
    (1284, 255, 1660, 255), (1284, 321, 1660, 321),
    (1397, 174, 1397, 380), (1534, 174, 1534, 380), (1660, 174, 1660, 380),
    (1463, 1019, 1730, 1019), (1463, 945, 1463, 1019), (1730, 945, 1730, 1019),
    (1278, 787, 1278, 1009),
    (256, 787, 256, 1009), (386, 787, 386, 1009), (516, 787, 516, 1009), (646, 787, 646, 1009),
    (775, 787, 775, 1009), (905, 787, 905, 1009), (1035, 787, 1035, 1009), (1157, 787, 1157, 1009),
]
CHASSIS_ELLIPSES = [
    (191, 152, 56, 50), (321, 152, 56, 50), (451, 152, 56, 50), (581, 152, 56, 50),
    (711, 152, 56, 50), (840, 152, 56, 50), (970, 152, 56, 50), (1100, 152, 56, 50),
    (1337, 483, 50, 42), (1467, 483, 50, 42), (1597, 483, 50, 42), (1727, 483, 50, 42),
    (1337, 605, 50, 43), (1467, 605, 50, 43), (1597, 605, 50, 43), (1727, 605, 50, 43),
    (1216, 732, 48, 50),
]
CHASSIS_CIRCLES = [(1727, 303, 24)]


def render_chassis(frame):
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    g = breath(frame, 1, 0.0)
    a = int(150 + 60 * g)
    col = rgba(CHASSIS_RED, a)
    sw = max(2, int(round(3 * SS)))
    for x1, y1, x2, y2 in CHASSIS_LINES:
        d.line((x1 * SS, y1 * SS, x2 * SS, y2 * SS), fill=col, width=sw)
    for cx, cy, rx, ry in CHASSIS_ELLIPSES:
        d.ellipse(((cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS),
                  outline=col, width=sw)
    for cx, cy, r in CHASSIS_CIRCLES:
        d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS),
                  outline=col, width=sw)
    return big.resize((W, H), Image.LANCZOS)


# ----------------------------------------------------------------------------- frames
def render_surface(rows, frame):
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    for row in rows:
        render_control(big, row, frame)
    return big.resize((W, H), Image.LANCZOS)


def on_matte(img):
    matte = Image.new("RGB", img.size, BG)
    matte.paste(img, mask=img.getchannel("A"))
    return matte


# ----------------------------------------------------------------------------- encode
def encode_prores(frame_dir, pattern, out_path, fps=FPS):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", str(frame_dir / pattern),
        "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
        str(out_path),
    ], check=True)


# ----------------------------------------------------------------------------- main
def build_manifest(rows):
    out = []
    for r in rows:
        out.append({
            "layer": r["layer"], "name": r["name"], "prototype": r["prototype"],
            "color_id": r["color_id"], "color_rgb": COLOR_BY_ID[r["color_id"]],
            "text": r["text"], "label_box": r["label_box"],
            "witness_box": r["witness_box"], "motion_box": r["motion_box"],
            "clip_file": f"media/clips/{safe_name(r)}.mov",
        })
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"canvas": [W, H], "fps": FPS, "frames": FRAMES,
               "palette": COLOR_BY_ID, "chassis_red": CHASSIS_RED,
               "controls": out}, open(MANIFEST, "w"), indent=1)


def safe_name(row):
    return f"L{row['layer']:03d}_{row['name']}".replace(" ", "_").replace("/", "-")


def encode_one_clip(row, surface_dir):
    """Crop the whole-control extent from the surface frames and encode a clip."""
    bs = [bb for bb in (row["label_box"], row["witness_box"], row["motion_box"]) if bb]
    b = [min(x[0] for x in bs), min(x[1] for x in bs),
         max(x[2] for x in bs), max(x[3] for x in bs)]
    x1, y1 = int(math.floor(b[0])) - 6, int(math.floor(b[1])) - 6
    x2, y2 = int(math.ceil(b[2])) + 6, int(math.ceil(b[3])) + 6
    x1 = max(0, x1); y1 = max(0, y1); x2 = min(W, x2); y2 = min(H, y2)
    if (x2 - x1) % 2:
        x2 -= 1
    if (y2 - y1) % 2:
        y2 -= 1
    cdir = Path("/tmp/v3_clip")
    if cdir.exists():
        shutil.rmtree(cdir)
    cdir.mkdir(parents=True, exist_ok=True)
    for f in range(FRAMES):
        Image.open(surface_dir / f"frame-{f:04d}.png").crop(
            (x1, y1, x2, y2)).save(cdir / f"frame-{f:04d}.png")
    CLIPS.mkdir(parents=True, exist_ok=True)
    encode_prores(cdir, "frame-%04d.png", CLIPS / f"{safe_name(row)}.mov")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--no-clips", action="store_true")
    ap.add_argument("--frames", nargs=2, type=int, metavar=("A", "B"),
                    help="render surface+chassis frames [A,B) to scratch")
    ap.add_argument("--encode", action="store_true",
                    help="encode surface+chassis masters from scratch frames")
    ap.add_argument("--clips", nargs=2, type=int, metavar=("A", "B"),
                    help="encode per-control clips for rows[A:B)")
    args = ap.parse_args()

    rows = json.load(open(BUILD_INPUT))
    SHOTS.mkdir(parents=True, exist_ok=True)
    build_manifest(rows)

    if args.frames:
        a, b = args.frames
        (SCRATCH / "surface").mkdir(parents=True, exist_ok=True)
        (SCRATCH / "chassis").mkdir(parents=True, exist_ok=True)
        for f in range(a, b):
            render_surface(rows, f).save(SCRATCH / "surface" / f"frame-{f:04d}.png", compress_level=1)
            render_chassis(f).save(SCRATCH / "chassis" / f"frame-{f:04d}.png", compress_level=1)
        print(f"frames [{a},{b}) rendered")
        return
    if args.encode:
        encode_prores(SCRATCH / "surface", "frame-%04d.png",
                      MEDIA / "APC40_MKII_Animated_Twin_V3_Surface_Alpha.mov")
        encode_prores(SCRATCH / "chassis", "frame-%04d.png",
                      MEDIA / "APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov")
        print("masters encoded ->", MEDIA)
        return
    if args.clips is not None:
        a, b = args.clips
        local_surface = Path("/tmp/v3_surface")
        local_surface.mkdir(parents=True, exist_ok=True)
        for f in range(FRAMES):          # sync frames to local disk once
            dst = local_surface / f"frame-{f:04d}.png"
            if not dst.exists():
                shutil.copy(SCRATCH / "surface" / f"frame-{f:04d}.png", dst)
        for r in rows[a:b]:
            encode_one_clip(r, local_surface)
        print(f"clips rows[{a}:{b}) encoded ->", CLIPS)
        return

    if args.preview or not args.full:
        for f in (0, 20, 40, 60):
            surf = render_surface(rows, f)
            chas = render_chassis(f)
            combo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            combo.alpha_composite(chas)
            combo.alpha_composite(surf)
            on_matte(combo).save(SHOTS / f"preview_full_frame{f:03d}.png")
        # crops of representative controls at frame 20
        surf = render_surface(rows, 20)
        chas = render_chassis(20)
        combo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        combo.alpha_composite(chas); combo.alpha_composite(surf)
        reps = {"grid_pad", "rotary", "vertical_fader", "crossfader", "scene_pad",
                "track_button", "small_button", "bank_polygon"}
        seen = set()
        for r in rows:
            if r["prototype"] in reps and r["prototype"] not in seen:
                seen.add(r["prototype"])
                b = r["motion_box"] or r["label_box"]
                x1, y1 = int(b[0]) - 12, int(b[1]) - 12
                x2, y2 = int(b[2]) + 12, int(b[3]) + 12
                on_matte(combo).crop((max(0, x1), max(0, y1), min(W, x2), min(H, y2))).save(
                    SHOTS / f"preview_crop_{r['prototype']}.png")
        print("preview stills ->", SHOTS)
        if not args.full:
            return

    # ----- full render
    fdir = SCRATCH
    if fdir.exists():
        shutil.rmtree(fdir)
    (fdir / "surface").mkdir(parents=True, exist_ok=True)
    (fdir / "chassis").mkdir(parents=True, exist_ok=True)
    for f in range(FRAMES):
        render_surface(rows, f).save(fdir / "surface" / f"frame-{f:04d}.png")
        render_chassis(f).save(fdir / "chassis" / f"frame-{f:04d}.png")
    encode_prores(fdir / "surface", "frame-%04d.png",
                  MEDIA / "APC40_MKII_Animated_Twin_V3_Surface_Alpha.mov")
    encode_prores(fdir / "chassis", "frame-%04d.png",
                  MEDIA / "APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov")
    print("surface + chassis MOV ->", MEDIA)

    if not args.no_clips:
        CLIPS.mkdir(parents=True, exist_ok=True)
        for r in rows:
            # a standalone per-control clip captures the WHOLE control extent
            # (e.g. a rotary's knob + its label), so crop the union of its boxes.
            bs = [bb for bb in (r["label_box"], r["witness_box"], r["motion_box"]) if bb]
            b = [min(x[0] for x in bs), min(x[1] for x in bs),
                 max(x[2] for x in bs), max(x[3] for x in bs)]
            # pad to even dims for ProRes
            x1, y1 = int(math.floor(b[0])) - 6, int(math.floor(b[1])) - 6
            x2, y2 = int(math.ceil(b[2])) + 6, int(math.ceil(b[3])) + 6
            x1 = max(0, x1); y1 = max(0, y1); x2 = min(W, x2); y2 = min(H, y2)
            if (x2 - x1) % 2: x2 -= 1
            if (y2 - y1) % 2: y2 -= 1
            cdir = SCRATCH / "clip"
            if cdir.exists():
                shutil.rmtree(cdir)
            cdir.mkdir(parents=True, exist_ok=True)
            for f in range(FRAMES):
                Image.open(fdir / "surface" / f"frame-{f:04d}.png").crop(
                    (x1, y1, x2, y2)).save(cdir / f"frame-{f:04d}.png")
            encode_prores(cdir, "frame-%04d.png", CLIPS / f"{safe_name(r)}.mov")
        print(f"{len(rows)} per-control clips ->", CLIPS)


if __name__ == "__main__":
    main()
