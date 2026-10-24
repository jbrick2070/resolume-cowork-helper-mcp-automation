#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
caption_fit.py - fit every caption inside the frame by measuring it on the running Avenue, not by guessing.

    python -u -m resolume_build.caption_fit "packs/dead-air/Dead Air Listening Posts.avc" --out packs/dead-air/caption_fit.json

Opens a TEMPORARY copy, solos the TEXT layer and, for each deck and column, measures the text's bounding box. If it
touches the frame margin it changes Size and Position live (nothing is saved), measures again, and repeats until the
box is inside the margin. The result is a table {"d<deck>c<col>": {"Size": s, "Position X": x, "Position Y": y}} that
the builder applies on top of captions.convert() when it is stored in the pack's bible as "caption_fit".
The audio does not matter. It takes the screen for a few minutes.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import gallery, rig, screen            # noqa: E402
from resolume_build.before_after import temp_copy, land, expected_captions   # noqa: E402
from resolume_build.live_audit import grab                 # noqa: E402

LAYER = 5
LO, HI = 0.04, 0.96            # the box must sit inside these fractions of the frame
MIN_SIZE = 0.55


def measure(hwnd, settle=0.8):
    time.sleep(settle)
    f = grab(hwnd, 3, 6)
    best = max(f, key=lambda x: float((x > 0.12).sum()))
    ys, xs = np.where(best > 0.12)
    if len(xs) < 12:
        return None
    h, w = best.shape
    return dict(x0=xs.min() / w, x1=(xs.max() + 1) / w, y0=ys.min() / h, y1=(ys.max() + 1) / h)


def inside(b):
    return b is not None and b["x0"] >= LO - 0.015 and b["y0"] >= LO - 0.015 and b["x1"] <= HI + 0.015 and b["y1"] <= HI + 0.015


def setp(sp, name, value):
    rig.put("/parameter/by-id/%d" % sp[name]["id"], {"value": float(value)})


def fit_one(hwnd, col):
    clip = rig.get("/composition/layers/%d/clips/%d" % (LAYER, col))
    sp = clip["video"]["sourceparams"]
    if "Size" not in sp or "Position Y" not in sp:
        return None
    size0, x0_, y0_ = float(sp["Size"]["value"]), float(sp.get("Position X", {}).get("value", 0.0)), float(sp["Position Y"]["value"])
    size, x, y = size0, x0_, y0_
    for _ in range(8):
        b = measure(hwnd)
        if inside(b):
            return dict(Size=round(size, 3), **{"Position X": round(x, 1), "Position Y": round(y, 1)}), True
        if b is None:                                     # invisible: do not guess, leave it for a person
            break
        w, h = b["x1"] - b["x0"], b["y1"] - b["y0"]
        touching = b["y0"] <= 0.003 or b["y1"] >= 0.997 or b["x0"] <= 0.003 or b["x1"] >= 0.997
        k = 1.0
        if w > HI - LO or h > HI - LO or touching:         # too big, or clipped (so the true size is larger than seen)
            k = min((HI - LO) / max(w, 1e-3), (HI - LO) / max(h, 1e-3), 0.85 if touching else 1.0) * 0.96
        if k < 1.0 and size > MIN_SIZE:
            size = max(MIN_SIZE, size * k)
            setp(sp, "Size", size)
            continue
        # fits in size: slide it inside the margin (pixels; Position is in composition pixels, y down)
        dx = (LO - b["x0"]) * 1920 if b["x0"] < LO else (HI - b["x1"]) * 1920 if b["x1"] > HI else 0.0
        dy = (LO - b["y0"]) * 1080 if b["y0"] < LO else (HI - b["y1"]) * 1080 if b["y1"] > HI else 0.0
        if not (dx or dy):
            return dict(Size=round(size, 3), **{"Position X": round(x, 1), "Position Y": round(y, 1)}), True
        x, y = x + dx, y + dy
        setp(sp, "Position Y", y)
        if "Position X" in sp:
            setp(sp, "Position X", x)
    return dict(Size=round(size, 3), **{"Position X": round(x, 1), "Position Y": round(y, 1)}), False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("avc")
    ap.add_argument("--out", required=True)
    ap.add_argument("--decks", default="")
    ap.add_argument("--deck-json", required=True, help="the pack's decks.json, to prove each cell is the one measured")
    a = ap.parse_args()
    decks = {int(x) for x in a.decks.split(",")} if a.decks else None
    expected = expected_captions(a.deck_json)
    path = temp_copy(a.avc, "fit")
    c = gallery.open_and_wait(path, timeout=900)
    if not c:
        raise SystemExit("did not open")
    gallery.reveal(c)
    rig.post("/composition/disconnect-all")
    time.sleep(2.5)
    hwnd = screen.avenue_hwnd()
    screen.bring_to_front(hwnd)
    screen.pin(hwnd)
    table, bad = {}, []
    for deck in range(1, len(c["decks"]) + 1):
        if decks and deck not in decks:
            continue
        for col in range(1, len(c["columns"]) + 1):
            if not land(deck, col, expected.get((deck, col))):
                print("deck %d col %d  did not land; skipped" % (deck, col), flush=True)
                continue
            rig.put("/composition/layers/%d" % LAYER, {"solo": {"value": True}})
            res = fit_one(hwnd, col)
            rig.put("/composition/layers/%d" % LAYER, {"solo": {"value": False}})
            if res is None:
                continue
            vals, ok = res
            table["d%dc%d" % (deck, col)] = vals
            if not ok:
                bad.append("d%dc%d" % (deck, col))
            print("deck %d col %d  Size %.2f  X %.0f  Y %.0f  %s" % (deck, col, vals["Size"], vals["Position X"], vals["Position Y"],
                                                                     "ok" if ok else "NOT FITTED"), flush=True)
    rig.post("/composition/disconnect-all")
    screen.pin(hwnd, False)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(table, f, indent=1)
    print("wrote %s (%d captions, %d not fitted: %s)" % (a.out, len(table), len(bad), bad), flush=True)


if __name__ == "__main__":
    main()
