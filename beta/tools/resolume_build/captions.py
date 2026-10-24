#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
captions.py - make every caption a Text Block at a placement that was measured on Avenue 7.28.1.

The two quiet packs (Dead Air, Dew Line) were generated before the text placement was measured. They use Text
Animator for their captions, written as if Position X / Y were offsets from the frame centre, and the live audit
of 2026-10-23 found those captions invisible or off the frame. A Text Block places like this (measured on the rig):

  * Position X is the CENTRE of the Line Width box; Alignment only justifies lines inside it.
  * AlignmentVertically picks the FRAME EDGE the block is aligned to (Top / Center / Bottom) and Position Y is an
    offset DOWNWARD from that edge.

So a caption written as "its (align, valign) corner sits at (x, y) pixels from the centre, y down" is translated by
place(). convert() rewrites each layer-5 Text Animator clip of a deck as a Text Block that way, keeping the text,
font, colour and size. Opt in with bible["caption_blocks"] = true (pack.py).
"""
TEXT_LINE_W = 1400.0
HALF_H = 540.0
NL = chr(10)


def place(align, valign, x, y, line_w=TEXT_LINE_W):
    """(Position X, Position Y, AlignmentVertically) for a Text Block whose (align, valign) corner is at (x, y)."""
    bx = x + line_w / 2.0 if align == "Left" else x - line_w / 2.0 if align == "Right" else x
    by = y - HALF_H if valign == "Bottom" else y + HALF_H if valign == "Top" else y
    return bx, by, valign


def wrap(s, n=22):
    out = []
    for line in str(s).split(NL):
        cur = ""
        for w in line.split(" "):
            if cur and len(cur) + 1 + len(w) > n:
                out.append(cur)
                cur = w
            else:
                cur = (cur + " " + w) if cur else w
        out.append(cur)
    return NL.join(out)


def to_block(p):
    """Text Animator parameters -> Text Block parameters at the same intended corner."""
    align = p.get("Alignment", "Left")
    valign = p.get("AlignmentVertically", "Bottom")
    x, y = float(p.get("Position X", 0.0)), float(p.get("Position Y", 0.0))
    bx, by, bv = place(align, valign, x, y)
    return {"Text": wrap(p.get("Text", "")), "Font": p.get("Font", "Consolas"), "Style": p.get("Style", "Regular"),
            "Color": p.get("Color", "#ffffffff"), "Size": float(p.get("Size", 0.9)), "Alignment": align,
            "AlignmentVertically": bv, "Line Width": TEXT_LINE_W, "Position X": bx, "Position Y": by,
            "Spacing Y": 12.0, "Outline Width": 0.0, "Glow In": 0.0, "Glow Out": 0.0}


# Measured on the rig. At Size 1.0 a monospace caption (Cascadia Mono, Consolas, OCR A) is about 50 px per character and
# 93 px per line (with Spacing Y 12). The proportional display faces the quiet packs use (Baskerville, Bodoni, ...) run
# about 62 px and 125 px, read off the live audit of Dead Air on 2026-10-23. Both scale with Size.
MONO = ("Cascadia", "Consolas", "OCR", "Courier", "Lucida Console")
CHAR_W, LINE_H = 50.0, 93.0
FRAME_W, FRAME_H, MARGIN = 1920.0, 1080.0, 40.0


def metrics(font):
    return (50.0, 93.0) if any(m.lower() in str(font).lower() for m in MONO) else (62.0, 125.0)


def extent(p):
    """(width, height) in pixels of the caption box, including the wrapping Avenue does at Line Width."""
    cw, lh = metrics(p.get("Font", ""))
    s = float(p.get("Size", 1.0))
    line_w = float(p.get("Line Width", TEXT_LINE_W))
    rows, widest = 0, 0.0
    for line in str(p.get("Text", "")).split(NL):
        w = len(line) * cw * s
        rows += max(1, int(-(-w // line_w)))
        widest = max(widest, min(w, line_w))
    return widest, rows * lh * s


def top_bottom(p, h):
    """(top, bottom) in frame pixels of a Text Block's box, from Position Y and AlignmentVertically."""
    v, y = p.get("AlignmentVertically", "Center"), float(p.get("Position Y", 0.0))
    if v == "Bottom":
        return FRAME_H + y - h, FRAME_H + y
    if v == "Top":
        return y, y + h
    return FRAME_H / 2.0 + y - h / 2.0, FRAME_H / 2.0 + y + h / 2.0


def fit(p, report=lambda m: None, where=""):
    """Shrink the caption until it needs no extra wrapping and fits the frame (down to Size 0.6), then nudge it inside
    the margin."""
    cw, lh = metrics(p.get("Font", ""))
    line_w = float(p.get("Line Width", TEXT_LINE_W))
    natural = len(str(p.get("Text", "")).split(NL))
    size0 = size = float(p.get("Size", 1.0))
    while size > 0.6:
        p["Size"] = size
        w, h = extent(p)
        rows = round(h / (lh * size))
        if rows <= natural and h <= FRAME_H - 2 * MARGIN:
            break
        size = round(size - 0.05, 3)
    p["Size"] = size
    w, h = extent(p)
    top, bottom = top_bottom(p, h)
    y = float(p.get("Position Y", 0.0))
    dy = 0.0
    if top < MARGIN:
        dy = MARGIN - top
    elif bottom > FRAME_H - MARGIN:
        dy = (FRAME_H - MARGIN) - bottom
    if dy:
        p["Position Y"] = y + dy
    return p


def convert(decks, report=lambda m: None, layer=5, fit_all=True, table=None):
    n = m = k = 0
    for di, d in enumerate(decks):
        for c in d.get("clips", []):
            if c.get("layer") != layer or c.get("source") not in ("Text Animator", "Text Block"):
                continue
            where = "deck %d col %s" % (di + 1, c.get("column"))
            if c["source"] == "Text Animator":
                c["params"] = to_block(c.get("params", {}))
                c["source"] = "Text Block"
                n += 1
            if fit_all:
                before = (c["params"].get("Size"), c["params"].get("Position Y"))
                fit(c["params"], lambda msg: None, where)
                if before != (c["params"].get("Size"), c["params"].get("Position Y")):
                    m += 1
            measured = (table or {}).get("d%dc%s" % (di + 1, c.get("column")))
            if measured:                                  # sizes and positions measured on the rig win over the model
                c["params"].update({kk: vv for kk, vv in measured.items() if kk in ("Size", "Position X", "Position Y")})
                k += 1
    if n or m or k:
        report("captions: %d Text Animators rewritten as Text Blocks, %d fitted by the size model, %d from rig measurements"
               % (n, m, k))
    return decks
