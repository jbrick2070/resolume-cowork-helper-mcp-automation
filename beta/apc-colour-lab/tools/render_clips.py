#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_clips.py - turn the engine into pictures for the README: one looping GIF per theme
and a contact sheet of every theme.

    python tools/render_clips.py                    # all themes -> docs/media/
    python tools/render_clips.py --themes darkside,pulsar --fps 12

These are the EMULATED pads (apc_lab.engine.Surface fed by apc_lab.engine.Router), drawn with
Pillow. They are not photographs of a controller: they show the messages the router would
send, using the display approximations of the Akai palette. The pad grid is the demo's
fake Resolume (one clip playing per layer, the rest dark, so each theme's ambient shows),
with two pad presses and one scene-launch press during the loop.

Needs Pillow (pip install pillow). The GIFs are a development aid; nothing else imports this.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from apc_lab import engine as E          # noqa: E402
from apc_lab import protocol as P        # noqa: E402

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont   # noqa: E402

ROW_FAMILIES = [(49, 50), (37, 38), (21, 22), (9, 10), (3, 2)]     # what a pack sends per layer row
EMPTY = {4: (6, 7)}                                                # the full pack leaves two slots empty
PLAYING = [0, 3, 5, 1, 6]

PAD, GAP, SCENE_GAP, MARGIN, TITLE_H = 30, 6, 16, 16, 28
SS = 2                                                             # supersampling for smooth corners
BG, UNLIT = (17, 17, 21), (31, 31, 36)


def _font(size):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


class FakeResolume(object):
    """The demo's stand-in for Resolume: tells the router which pads are lit."""

    def __init__(self, router, grid):
        self.router, self.grid = router, grid
        self.playing, self.column = list(PLAYING), -1

    def feedback(self, t):
        out = []
        for r in range(5):
            on, dim = ROW_FAMILIES[r]
            for c in range(8):
                n = r * 8 + c
                if self.grid == "sparse" and self.playing[r] != c:
                    m = P.off(1, n)
                elif c in EMPTY.get(r, ()):
                    m = P.off(1, n)
                else:
                    m = P.on(1, n, on if self.playing[r] == c else dim)
                out += self.router.from_resolume(m, t)
        for i in range(5):
            out += self.router.from_resolume(P.on(1, 82 + i, 3 if self.column == i else 2), t)
        return out

    def press(self, note, t):
        _, out = self.router.from_apc(P.on(1, note, 127), t)
        if note >= 82:
            self.column = note - 82
            self.playing = [note - 82] * 5
        else:
            self.playing[note // 8] = note % 8
            self.column = -1
        return out + self.feedback(t)


def layout():
    gw = 8 * PAD + 7 * GAP + SCENE_GAP + PAD
    gh = 5 * PAD + 4 * GAP
    return gw, gh, 2 * MARGIN + gw, 2 * MARGIN + TITLE_H + gh


def pad_box(col, row):
    x = MARGIN + col * (PAD + GAP) + (SCENE_GAP - GAP if col == 8 else 0)
    y = MARGIN + TITLE_H + (4 - row) * (PAD + GAP)
    return x, y, x + PAD, y + PAD


def draw_frame(surface, t, bpm, title):
    _, _, w, h = layout()
    bg = Image.new("RGB", (w * SS, h * SS), BG)
    glow = Image.new("RGB", (w * SS, h * SS), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    colours = {}
    for n in P.ALL_PADS:
        rgb = tuple(int(round(x)) for x in surface.rgb(n, t, bpm))
        colours[n] = rgb
        if max(rgb) > 70:
            x0, y0, x1, y1 = [v * SS for v in pad_box(*P.pad_col_row(n))]
            pad_ = 5 * SS
            gd.rounded_rectangle((x0 - pad_, y0 - pad_, x1 + pad_, y1 + pad_), 9 * SS,
                                 fill=tuple(int(c * 0.55) for c in rgb))
    glow = glow.filter(ImageFilter.GaussianBlur(7 * SS))
    img = ImageChops.add(bg, glow)
    d = ImageDraw.Draw(img)
    for n in P.ALL_PADS:
        rgb = colours[n]
        box = [v * SS for v in pad_box(*P.pad_col_row(n))]
        d.rounded_rectangle(box, 6 * SS, fill=rgb if max(rgb) > 0 else UNLIT)
        if max(rgb) == 0:
            d.rounded_rectangle(box, 6 * SS, outline=(44, 44, 50), width=SS)
    d.text((MARGIN * SS, (MARGIN - 4) * SS), title, font=_font(14 * SS), fill=(225, 225, 232))
    small = "%g bpm" % bpm
    f = _font(11 * SS)
    d.text((w * SS - MARGIN * SS - d.textlength(small, font=f), (MARGIN - 2) * SS), small, font=f, fill=(120, 120, 132))
    return img.resize((w, h), Image.LANCZOS)


def frames_for(key, seconds, fps, bpm, grid):
    router = E.Router(key, bpm)
    surface = E.Surface()
    res = FakeResolume(router, grid)
    title = E.THEMES[key]["name"]
    events = [(2.5, 18), (5.5, 29), (8.0, 84)]                     # two pad presses, then a scene launch
    pending = list(events)
    for m in res.feedback(0.0):
        surface.apply(m, 0.0)
    frames = []
    for i in range(int(seconds * fps)):
        t = i / float(fps)
        out = []
        while pending and pending[0][0] <= t:
            out += res.press(pending.pop(0)[1], t)
        out += router.tick(t)
        for m in out:
            surface.apply(m, t)
        frames.append((t, draw_frame(surface, t, bpm, title)))
    return frames


def save_gif(frames, path, fps):
    # One palette for the whole loop: identical pixels then stay identical between frames, so
    # Pillow writes only the region that changed and the file stays small.
    sample = [f for i, (_, f) in enumerate(frames) if i % 4 == 0]
    w, h = sample[0].size
    strip = Image.new("RGB", (w, h * len(sample)))
    for i, f in enumerate(sample):
        strip.paste(f, (0, i * h))
    master = strip.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = [f.quantize(palette=master, dither=Image.Dither.NONE) for _, f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / fps), loop=0,
                optimize=False, disposal=1)


def contact_sheet(stills, path, cols=3):
    w, h = stills[0].size
    rows = (len(stills) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), BG)
    for i, im in enumerate(stills):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(path, optimize=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--themes", help="comma list of theme keys (default: all)")
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "media"))
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--bpm", type=float, default=P.DEFAULT_BPM)
    ap.add_argument("--still-at", type=float, default=3.1, help="time of the contact-sheet still (just after a press)")
    ap.add_argument("--no-gifs", action="store_true")
    a = ap.parse_args()
    keys = a.themes.split(",") if a.themes else list(E.THEME_ORDER)
    os.makedirs(a.out, exist_ok=True)
    stills = []
    for key in keys:
        grid = "full" if key == "pack" else "sparse"
        frames = frames_for(key, a.seconds, a.fps, a.bpm, grid)
        still = min(frames, key=lambda tf: abs(tf[0] - a.still_at))[1]
        stills.append(still)
        if not a.no_gifs:
            path = os.path.join(a.out, key + ".gif")
            save_gif(frames, path, a.fps)
            print("%-11s %3d frames  %5.0f KB  %s" % (key, len(frames), os.path.getsize(path) / 1024.0, path))
    sheet = os.path.join(a.out, "themes.png")
    contact_sheet(stills, sheet)
    print("contact sheet", sheet, "%.0f KB" % (os.path.getsize(sheet) / 1024.0))


if __name__ == "__main__":
    main()
