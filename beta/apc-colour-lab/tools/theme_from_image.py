#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
theme_from_image.py - turn a picture (an album sleeve, a poster, a photo, a swatch card)
into an APC40 mkII colour theme.

    python tools/theme_from_image.py cover.jpg                       # print the theme JSON
    python tools/theme_from_image.py cover.jpg --out cover.json --preview cover_preview.png
    python tools/theme_from_image.py --demo                          # make and use a procedural sleeve

Then run it on the pads (or the dry run):

    python -m apc_lab.live --dry-run --theme-file cover.json --theme cover
    ... or open apc40_colour_lab.html and use "Load theme (.json)".

How it works, all deterministic (the same picture always gives the same theme):
  1. shrink the picture and find its dominant colours with median cut;
  2. map each one to the NEAREST of the APC40 mkII's 128 LED colours in CIELAB (the pads can
     only show those 128; a sleeve's cream becomes the closest warm white or yellow);
  3. build a theme from them: the biggest lit colours become the 'on' colours of the three
     colour families, each with a darkened same-hue 'dim', and the next colour is what a playing
     pad breathes to; the empty pads get an ambient animation in the same colours, and a pad
     press throws a ring of them.

The mapping is the interesting part: it shows which of a sleeve's colours survive on 128 LEDs.
Needs Pillow and numpy; nothing else imports this module.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import numpy as np                                    # noqa: E402
from PIL import Image, ImageDraw                      # noqa: E402

from apc_lab import engine as E                       # noqa: E402

_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]])
_WHITE = np.array([0.95047, 1.0, 1.08883])

AMBIENTS = ("pulse", "rain", "scan", "flicker", "chase")
NEAR_BLACK_LUMA = 0.15           # an APC colour darker than this is not a "lit" colour


def srgb_to_lab(rgb):
    """(..., 3) array of 0-255 sRGB -> CIELAB (D65)."""
    c = np.asarray(rgb, dtype=float) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = (lin @ _M.T) / _WHITE
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16.0 / 116.0)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], axis=-1)


PALETTE = np.array(E.PALETTE, dtype=float)
PALETTE_LAB = srgb_to_lab(PALETTE)


def nearest_apc(rgb, skip=(0,)):
    """Index (0-127) of the APC LED colour closest to an RGB colour, by CIELAB distance."""
    d = ((PALETTE_LAB - srgb_to_lab(np.asarray(rgb, dtype=float))) ** 2).sum(axis=1)
    for s in skip:
        d[s] = np.inf
    return int(np.argmin(d))


def apc_luma(idx):
    return E.luma(E.PALETTE[idx])


def dim_of(idx):
    """A darker colour of the same hue: the nearest APC colour to 30% of this one."""
    return nearest_apc(PALETTE[idx] * 0.30)


def dominant_colours(im, n=8):
    """[(share 0-1, (r, g, b))...] biggest first, by median cut on a shrunken copy."""
    im = im.convert("RGB")
    im.thumbnail((96, 96))
    q = im.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()
    total = float(im.size[0] * im.size[1])
    found = sorted(q.getcolors(), key=lambda x: (-x[0], x[1]))
    return [(count / total, tuple(pal[i * 3:i * 3 + 3])) for count, i in found]


def apc_colours_of(im, n=8):
    """Dominant colours mapped onto the APC palette: [(share, rgb, apc index)] merged by index."""
    merged = {}
    order = []
    for share, rgb in dominant_colours(im, n):
        idx = nearest_apc(rgb)
        if idx not in merged:
            merged[idx] = [0.0, rgb]
            order.append(idx)
        merged[idx][0] += share
    out = sorted(order, key=lambda i: -merged[i][0])
    return [(merged[i][0], tuple(merged[i][1]), i) for i in out]


def theme_from_colours(mapped, name, source, ambient="pulse"):
    """Build a theme dict from [(share, rgb, apc idx)], biggest first."""
    lit = [i for _, _, i in mapped if apc_luma(i) > NEAR_BLACK_LUMA][:6]
    for filler in (3, 94, 13, 37):            # a picture with under three lit colours borrows a few
        if len(lit) >= 3:
            break
        if filler not in lit:
            lit.append(filler)
    pairs = []
    for k in range(3):
        on = lit[k % len(lit)]
        nxt = lit[(k + 1) % len(lit)]
        pairs.append([on, dim_of(on), nxt if nxt != on else 3])
    ring = lit[:4]
    dims = [dim_of(i) for i in lit[:2]]
    if ambient == "pulse":
        amb = {"kind": "pulse", "colours": [dims[0], lit[0]], "div": "1/2"}
    elif ambient == "flicker":
        amb = {"kind": "flicker", "colours": dims + ring[:2], "rate": 4, "density": 0.3}
    elif ambient == "chase":
        amb = {"kind": "chase", "colours": [lit[0], 0, lit[1 % len(lit)], 0], "rate": 3.5}
    else:                                      # rain, scan
        amb = {"kind": ambient, "colours": ring + dims[:1], "rate": 2.5}
    top = lit[1 % len(lit)]
    return {
        "name": name,
        "blurb": "Made from %s: its %d dominant colours mapped to the nearest of the APC40 mkII's 128 LED colours "
                 "(%s)." % (source, len(lit), ", ".join(str(i) for i in lit)),
        "remap": "pairs",
        "pairs": pairs,
        "playing": {"colour": top, "kind": "pulsing", "div": "1/2"},
        "ambient": amb,
        "touch": {"kind": "ripple", "colours": ring + [3], "div": "1/8", "step": 0.25},
        "scene": {"colour": lit[0], "kind": "pulsing", "div": "1/2", "secondary": top},
    }


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "", os.path.splitext(os.path.basename(text))[0].lower())
    return s or "theme"


def preview(mapped, path, size=(560, 150)):
    """A strip: the picture's own colour above the APC colour that stands in for it."""
    w, h = size
    img = Image.new("RGB", (w, h), (17, 17, 21))
    d = ImageDraw.Draw(img)
    n = len(mapped)
    cell = (w - 20) // max(1, n)
    for k, (_, rgb, idx) in enumerate(mapped):
        x = 10 + k * cell
        d.rounded_rectangle((x, 12, x + cell - 8, 62), 6, fill=tuple(rgb))
        d.rounded_rectangle((x, 76, x + cell - 8, 126), 6, fill=tuple(int(v) for v in E.PALETTE[idx]))
        d.text((x + 2, 130), "apc %d" % idx, fill=(150, 150, 160))
    img.save(path)


def demo_sleeve(path, size=320):
    """A procedural 'sleeve' (no copyright): sunset bands and a dark circle."""
    im = Image.new("RGB", (size, size))
    px = im.load()
    for y in range(size):
        t = y / float(size - 1)
        r = int(255 * (1 - 0.55 * t))
        g = int(80 + 150 * (0.5 - abs(t - 0.45)))
        b = int(70 + 160 * t)
        for x in range(size):
            px[x, y] = (r, g, b)
    d = ImageDraw.Draw(im)
    d.ellipse((size * 0.3, size * 0.25, size * 0.7, size * 0.65), fill=(20, 10, 40))
    d.rectangle((0, int(size * 0.78), size, size), fill=(10, 14, 60))
    im.save(path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?")
    ap.add_argument("--name", help="theme name (default: the file name)")
    ap.add_argument("--key", help="theme key (default: the file name, letters and digits only)")
    ap.add_argument("--ambient", choices=AMBIENTS, default="pulse", help="what the empty pads do")
    ap.add_argument("--colours", type=int, default=8, help="dominant colours to look for")
    ap.add_argument("--out", help="write the theme to this .json file")
    ap.add_argument("--preview", help="write a strip comparing the picture's colours with their APC matches (.png)")
    ap.add_argument("--demo", action="store_true", help="use a procedural sleeve image instead of a file")
    a = ap.parse_args(argv)
    if a.demo:
        media = os.path.join(ROOT, "docs", "media")
        os.makedirs(media, exist_ok=True)
        a.image = os.path.join(media, "example_sleeve.png")
        demo_sleeve(a.image)
        a.out = a.out or os.path.join(media, "example_sleeve_theme.json")
        a.preview = a.preview or os.path.join(media, "example_sleeve_colours.png")
    if not a.image:
        ap.error("give an image, or --demo")
    im = Image.open(a.image)
    mapped = apc_colours_of(im, a.colours)
    base = os.path.basename(a.image)
    key = a.key or slug(a.image)
    theme = theme_from_colours(mapped, a.name or re.sub(r"[_-]+", " ", os.path.splitext(base)[0]).title(), base, a.ambient)
    doc = {"key": key, "theme": theme}
    text = json.dumps(doc, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        print("wrote", a.out)
    else:
        print(text)
    if a.preview:
        preview(mapped, a.preview)
        print("wrote", a.preview)
    for share, rgb, idx in mapped:
        print("  %4.1f%%  #%02X%02X%02X  ->  apc %3d  #%02X%02X%02X" % (
            share * 100, rgb[0], rgb[1], rgb[2], idx, *[int(v) for v in E.PALETTE[idx]]), file=sys.stderr if not a.out else sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
