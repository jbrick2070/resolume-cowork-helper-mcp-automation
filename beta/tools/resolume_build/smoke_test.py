#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
smoke_test.py - prove the XML dialect on the running rig before building
anything big: one deck, three layers, a clip of every tricky kind (Wire
generator with choices, text, colours, FFT, a clip-level effect), two
composition effects on dashboard links. Opens it in Avenue and reads every
written value back through REST.

    python -m resolume_build.smoke_test
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build.avc import Composition          # noqa: E402
from resolume_build import rig                      # noqa: E402
from resolume_build.library import u32_to_hex       # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke.avc")


def main():
    comp = Composition("Smoke Test", midi_preset="",
                       description="dialect probe", id_base=1799000000000)
    comp.dashboard = ["COLOUR", "SPACE", "OVERLAYS"]
    comp.add_effect("Bloom", {"Threshold": 0.66, "Size": 0.31}, link=1,
                    wet_max=0.8, fft={"Amount": ("mid", 9.0, 600, 0.2, 0.6)})
    comp.add_effect("Tunnel", {"Twist": 0.37}, link=2)
    comp.add_effect("CRT", {"Columns": 640.0, "Rows": 200.0, "Vignette": 30.0},
                    link=1)
    bed = comp.add_layer("BED", blend="Add", opacity_link=3, crossfader=1,
                         color_id=2)
    body = comp.add_layer("BODY", blend="Screen", opacity=0.75, crossfader=2,
                          ignore_column=True, color_id=3)
    text = comp.add_layer("TEXT", blend="Alpha", color_id=4,
                          effects=[("Vignette", {"Size": 0.4}, None, None)])
    d = comp.add_deck("Probe", ["One", "Two", "Three"])
    d.add_clip(bed, 0, "Abstract", "Abstract Field",
               {"Octaves": 4.0, "Amplitude": 0.7, "Density": 0.3},
               fft={"Amplitude": ("low", 9.0, 400, 0.3, 0.9)})
    d.add_clip(bed, 1, "Geometry", "Geometry Pattern Maker",
               {"Shape Types": "Hexagon", "Line Ammount": 22.0,
                "Innter Color 1": "#38ffa8", "Outer Color 1": "#ff3b2f",
                "Mask Intersect": False})
    d.add_clip(bed, 2, "Tunnel", "Tunnelines",
               {"Color 1": "#ffb03a", "Color 2": "#1b2a6b", "Zoom": 2.5,
                "Line Width": 0.03})
    d.add_clip(body, 0, "Blobs", "Metaballs",
               {"Grid": 6.0, "Size": 0.2, "Blend": "Average",
                "Color": "#4fe3ff", "BG Color": "#00000000"},
               fft={"Radius": ("high", 12.0, 300, 0.3, 0.9)})
    d.add_clip(body, 1, "Strobe", "Stroboscope",
               {"Frequency": 0.2, "Fade": True, "Color 1": "#e8eef2"})
    d.add_clip(body, 2, "Rings", "Rings",
               {"Num Rings": 7.0, "Style": "Stroke", "Color 1": "#38ffa8",
                "Color 2": "#00000000"},
               effects=[("Kaleidoscope", {"Angles": 0.5}, None, None)])
    d.add_clip(text, 0, "Caption", "Text Animator",
               {"Text": "NIGHT FIELD", "Font": "Consolas", "Style": "Bold",
                "Size": 1.4, "Alignment": "Center", "Color": "#ffb03a",
                "Position Y": -300.0})
    d.add_clip(text, 1, "Block", "Text Block",
               {"Text": "ONE\nTWO\nTHREE", "Font": "Impact",
                "Color": "#ff3b2f", "Size": 2.0})
    d.add_clip(text, 2, "Static", "Static", {"Mode": "Two-tone"})
    xml = comp.build()
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(xml)
    print("wrote", OUT, comp.counts(xml))

    if "--no-rig" in sys.argv:
        return
    if not rig.ensure_running():
        raise SystemExit("Avenue not reachable")
    ok = rig.open_composition(OUT, expect_name="Smoke Test", timeout=90)
    print("opened:", ok, "alive:", rig.alive())
    time.sleep(2)
    c = rig.composition()
    print("layers", len(c["layers"]), "columns", len(c["columns"]),
          "decks", [d["name"]["value"] for d in c["decks"]])
    print("comp effects:", [e.get("name") for e in c["video"]["effects"]])
    for e in c["video"]["effects"]:
        if e.get("name") in ("Bloom", "CRT", "Tunnel"):
            ps = e.get("params") or {}
            print("  ", e["name"], "bypassed=", e.get("bypassed", {}).get("value"),
                  {k: ps[k]["value"] for k in ("Threshold", "Size", "Amount",
                                                "Columns", "Rows", "Vignette",
                                                "Twist") if k in ps},
                  "mixer opacity:", (e.get("mixer") or {}).get("Opacity", {}).get("value"))
    for li, L in enumerate(c["layers"], start=1):
        print("layer %d %-6s blend=%s xf=%s ign=%s master=%s opacity=%s fx=%s" % (
            li, L["name"]["value"],
            (L["video"]["mixer"].get("Blend Mode") or {}).get("value"),
            L["crossfadergroup"]["value"], L["ignorecolumntrigger"]["value"],
            L["master"]["value"], L["video"]["opacity"]["value"],
            [e.get("name") for e in L["video"]["effects"]]))
    want = {
        (1, 1): ["Octaves", "Amplitude", "Density"],
        (1, 2): ["Shape Types", "Line Ammount", "Innter Color 1",
                 "Outer Color 1", "Mask Intersect"],
        (1, 3): ["Color 1", "Color 2", "Zoom", "Line Width"],
        (2, 1): ["Grid", "Size", "Blend", "Color", "Radius"],
        (2, 2): ["Frequency", "Fade", "Color 1"],
        (2, 3): ["Num Rings", "Style", "Color 1"],
        (3, 1): ["Text", "Font", "Style", "Size", "Alignment", "Color",
                 "Position Y"],
        (3, 2): ["Text", "Font", "Color", "Size"],
        (3, 3): ["Mode"],
    }
    for (l, col), names in want.items():
        sp, cj = rig.source_params(l, col)
        vals = {n: (sp.get(n) or {}).get("value") for n in names}
        fx = [e.get("name") for e in (cj.get("video") or {}).get("effects", [])]
        print("clip L%d C%d %-10s %s fx=%s" % (l, col, cj["name"]["value"],
                                              vals, fx))
    ph = c["crossfader"]["phase"]["value"]
    print("crossfader phase", ph, "dashboard",
          {k: v["value"] for k, v in c["dashboard"].items()})


if __name__ == "__main__":
    main()
