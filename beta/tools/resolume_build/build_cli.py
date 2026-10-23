#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_cli.py - build a complete pack from a bible + deck designs.

    python -m resolume_build.build_cli --bible B.json --decks D.json \
        --out packs/nightfield --theme nightfield --preset-id 2026101601 \
        --id-base 1790100000000

The rack colours are poured from the bible: across all five deck palettes
the darkest colour is "deep", the lightest is "paper", the two most
saturated non-red colours are the accents and the reddest is "alert".
"""
import argparse
import colorsys
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import pack as PACK           # noqa: E402
from resolume_build import racks as RACKS         # noqa: E402


def hex_rgb(h):
    h = h.lstrip("#")[:6]
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def pick_palette(bible):
    cols = []
    for d in bible["decks"]:
        for p in d.get("palette", []):
            try:
                r, g, b = hex_rgb(p["hex"])
            except Exception:
                continue
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            cols.append((p["hex"][:7], h, l, s))
    if not cols:
        return {}
    deep = min(cols, key=lambda c: c[2])[0]
    paper = max(cols, key=lambda c: c[2])[0]
    sat = sorted([c for c in cols if 0.15 < c[2] < 0.85], key=lambda c: -c[3])
    reds = [c for c in sat if c[1] < 0.06 or c[1] > 0.92]
    others = [c for c in sat if c not in reds]
    accent = (others[0][0] if others else (sat[0][0] if sat else "#ffb03a"))
    accent2 = next((c[0] for c in others[1:] if abs(c[1] - others[0][1]) > 0.12),
                   others[1][0] if len(others) > 1 else "#4fe3ff")
    alert = reds[0][0] if reds else "#ff3b2f"
    return {"deep": deep, "paper": paper, "accent": accent,
            "accent2": accent2, "alert": alert}


def row_colors_for(bible):
    """Pad-row LED families from the pack's overall hue."""
    return ["indigo", "cyan", "green", "amber", "white"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bible", required=True)
    ap.add_argument("--decks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--theme", default="nightfield")
    ap.add_argument("--preset-id", required=True)
    ap.add_argument("--id-base", type=int, required=True)
    ap.add_argument("--rows", default=None,
                    help="comma list of 5 LED colour families for pad rows")
    ap.add_argument("--scenes", default=None,
                    help="comma list of 5 LED colour families for scene pads")
    ap.add_argument("--notes", default="")
    ap.add_argument("--layer-blends", default=None,
                    help="per-layer blend overrides, e.g. 7:Add,6:Screen")
    a = ap.parse_args()
    with open(a.bible, encoding="utf-8") as f:
        bible = json.load(f)
    with open(a.decks, encoding="utf-8") as f:
        decks = json.load(f)
    if isinstance(decks, dict) and "decks" in decks:
        decks = decks["decks"]
    pal = pick_palette(bible)
    rack = RACKS.rack_for(pal, theme=a.theme)
    rows = a.rows.split(",") if a.rows else row_colors_for(bible)
    scenes = a.scenes.split(",") if a.scenes else None
    avc, preset, rep, counts = PACK.build_pack(
        bible, decks, rack, a.out, a.theme, a.preset_id, a.id_base,
        row_colors=rows, scene_colors=scenes, notes=a.notes,
        layer_blends=({int(k): v for k, v in (x.split(":", 1) for x in
                                               a.layer_blends.split(","))}
                      if a.layer_blends else None))
    from resolume_build import docs as DOCS
    manifest = json.load(open(os.path.join(a.out, "manifest.json"),
                              encoding="utf-8"))
    DOCS.write_docs(a.out, bible, manifest)
    with open(os.path.join(a.out, "bible.json"), "w", encoding="utf-8") as f:
        json.dump(bible, f, indent=1, ensure_ascii=False)
    with open(os.path.join(a.out, "decks.json"), "w", encoding="utf-8") as f:
        json.dump(decks, f, indent=1, ensure_ascii=False)
    print("palette:", pal)
    print("WROTE", avc)
    print("WROTE", preset)
    print(counts)
    print("repairs:", rep.repairs, "-> see", os.path.join(a.out,
                                                            "BUILD_REPORT.txt"))


if __name__ == "__main__":
    main()
