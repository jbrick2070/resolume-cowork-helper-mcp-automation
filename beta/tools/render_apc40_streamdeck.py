#!/usr/bin/env python3
"""Render transparent animated APC40 MKII Stream Deck button outlines.

This source deliberately contains no text.  It sits behind the original R1
labels and MIDI witnesses, turning their existing cells into tactile, gently
animated red buttons without replacing any of the controller's typography.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SECONDS = 1920, 1080, 30, 10
RED = (181, 29, 53)
FONT = "C:/Windows/Fonts/arialbd.ttf"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "beta" / "media" / "APC40_MKII_StreamDeck_Outlines_Alpha.mov"
PREVIEW = ROOT / "beta" / "screenshots" / "apc40-streamdeck-outlines-preview.png"
FRAMES = ROOT / "beta" / "media" / "_apc40_streamdeck_outline_frames"


def face(draw, box, title, midi, phase, selected=False, shape="pad"):
    """Draw an animated clip in the matching APC40 control silhouette."""
    glow = 0.35 + 0.65 * max(0.0, math.sin(phase))
    alpha = int(70 + glow * 145)
    x1, y1, x2, y2 = box
    radius = 10
    # Dark face deliberately occludes the static witness beneath it: the
    # animated clip, including its own red MIDI caption, is the visible label.
    if shape == "knob":
        draw.ellipse(box, fill=(7, 6, 8, 238), outline=(*RED, alpha // 2), width=8)
        draw.ellipse((x1 + 6, y1 + 6, x2 - 6, y2 - 6), outline=(*RED, alpha), width=3)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        angle = phase * .7 - math.pi / 2
        draw.line((cx, cy, cx + math.cos(angle) * (x2 - x1) * .3, cy + math.sin(angle) * (y2 - y1) * .3), fill=(*RED, 235), width=4)
    elif shape == "fader":
        draw.rounded_rectangle(box, 8, fill=(7, 6, 8, 238), outline=(*RED, alpha), width=4)
        travel = (y2 - y1 - 28) * (.5 + .4 * math.sin(phase))
        draw.rounded_rectangle((x1 + 7, y1 + 8 + travel, x2 - 7, y1 + 28 + travel), 5, fill=(*RED, 230))
    else:
        radius = 3 if shape == "pad" else 10
        draw.rounded_rectangle(box, radius, fill=(7, 6, 8, 238), outline=(*RED, alpha // 2), width=8)
        draw.rounded_rectangle((x1 + 6, y1 + 6, x2 - 6, y2 - 6), max(1, radius - 2), outline=(*RED, alpha), width=3)
    pulse_y = int(math.sin(phase) * 2)
    title_font = ImageFont.truetype(FONT, 19)
    midi_font = ImageFont.truetype(FONT, 13)
    draw.text(((x1 + x2) / 2, (y1 + y2) / 2 - 8 + pulse_y), title, font=title_font, fill=(*RED, 255), anchor="mm")
    draw.text(((x1 + x2) / 2, (y1 + y2) / 2 + 14 + pulse_y), midi, font=midi_font, fill=(235, 74, 94, 255), anchor="mm")
    if selected:
        draw.line((x1 + 14, y2 - 11, x2 - 14, y2 - 11), fill=(*RED, 235), width=4)


def render(frame: int) -> Image.Image:
    t = frame / FPS
    image = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Clip matrix: exact controller-like eight columns by five rows.
    left, top, cw, ch, gap = 118, 260, 126, 52, 19
    # Eight upper-track rotary clips preserve the APC40's circular knob row.
    for column in range(8):
        x = left + column * (cw + gap) + 27
        face(draw, (x, 118, x + 72, 190), f"TRACK {column + 1}", f"CC{48 + column}", t * 1.8 + column * .5, shape="knob")
    for row in range(5):
        for column in range(8):
            x = left + column * (cw + gap)
            y = top + row * (ch + gap)
            selected = (int(t * 2) + row * 3) % 8 == column
            note = 39 - row * 8 - column
            face(draw, (x, y, x + cw, y + ch), f"G{column + 1}-{row + 1}", f"N{note}/C1", t * 2.5 + column * .36 + row * .55, selected, "pad")

    # Scene launch row, transport/select strip, and bottom mixer controls.
    for row in range(5):
        y = top + row * (ch + gap)
        face(draw, (1196, y, 1297, y + ch), f"SCENE {row + 1}", f"N{82 + row}/C1", t * 2.5 + row * .55, row == int(t) % 5, "scene")
    for column in range(8):
        x = left + column * (cw + gap)
        face(draw, (x, 605, x + cw, 657), f"STOP {column + 1}", f"N{52}/C{column + 1}", t * 2.2 + column * .32, shape="pad")
        face(draw, (x, 673, x + cw, 725), f"SEL {column + 1}", f"N{51}/C{column + 1}", t * 2.2 + column * .32 + .8, shape="pad")
    # Device and navigation target clusters, deliberately compact so labels
    # stay unobscured and remain the visual authority.
    for row in range(2):
        for column in range(4):
            x, y = 1375 + column * 122, 452 + row * 119
            face(draw, (x, y, x + 72, y + 72), "DEV", f"CC{16 + column + row * 4}", t * 2 + column + row, shape="knob")
    face(draw, (1370, 775, 1840, 875), "NAVIGATION / DEVICE", "CC58–65 / CH1", t * 1.7, True)
    face(draw, (1470, 955, 1775, 1030), "X-FADE", "CC15 / CH1", t * 1.7 + 1, True)
    # Eight fader clips retain their tall APC40 form rather than becoming cards.
    for column in range(8):
        x = 135 + column * 145
        face(draw, (x, 780, x + 72, 1000), f"FADER {column + 1}", f"CC7/C{column + 1}", t * 1.45 + column * .4, shape="fader")
    # short animated rails indicate scan/selection without covering text
    scan = int(120 + ((t % 2.5) / 2.5) * 1010)
    draw.line((scan, 234, min(scan + 60, 1140), 234), fill=(*RED, 190), width=4)
    return image


def main():
    FRAMES.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    for frame in range(FPS * SECONDS):
        image = render(frame)
        if frame == 0:
            # composite only for inspection; the video itself is transparent.
            matte = Image.new("RGB", (W, H), (8, 7, 9))
            matte.paste(image, mask=image.getchannel("A"))
            matte.save(PREVIEW)
        image.save(FRAMES / f"frame-{frame:04d}.png")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(FRAMES / "frame-%04d.png"),
        "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", str(OUT),
    ], check=True)
    print(OUT)


if __name__ == "__main__":
    main()
