#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_pack.py - open a built pack on the running Avenue and read back what
Resolume actually loaded: structure, every deck, every clip's source and
parameters, the rack, the layers. Mismatches are listed; nothing is assumed.

    python -m resolume_build.verify_pack --avc "packs/x/Comp.avc" \
        --bible B.json --decks D.json [--snapshots DIR]

Opening replaces whatever is open in Avenue - run only with the user's
permission for that.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import rig                    # noqa: E402
from resolume_build import library as LIB         # noqa: E402
from resolume_build import pack as PACK           # noqa: E402
from resolume_build import instrument as INST     # noqa: E402


def close(a, b, tol=1e-3):
    try:
        return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
    except Exception:
        return str(a) == str(b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--avc", required=True)
    ap.add_argument("--bible", required=True)
    ap.add_argument("--decks", required=True)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--layer-blends", default=None,
                    help="the same overrides the pack was built with, e.g. 7:Add")
    ap.add_argument("--connect", action="store_true",
                    help="connect each column before reading it back")
    ap.add_argument("--sample", type=int, default=0,
                    help="check only every Nth clip (0 = all)")
    a = ap.parse_args()
    bible = json.load(open(a.bible, encoding="utf-8"))
    decks = json.load(open(a.decks, encoding="utf-8"))
    if isinstance(decks, dict) and "decks" in decks:
        decks = decks["decks"]
    lib = LIB.Library()
    rep = PACK.Report()

    if not rig.ensure_running():
        raise SystemExit("Avenue not reachable")
    if not a.no_open:
        ok = rig.open_composition(a.avc, expect_name=bible["comp_name"],
                                  timeout=240)
        print("opened:", ok)
    time.sleep(2)
    c = rig.composition()
    fails = []
    checks = 0

    def check(name, cond, detail=""):
        nonlocal checks
        checks += 1
        if not cond:
            fails.append("%s  %s" % (name, detail))
        print("%s  %s %s" % ("PASS" if cond else "FAIL", name, detail))

    check("composition name", c["name"]["value"] == bible["comp_name"],
          c["name"]["value"])
    check("8 layers", len(c["layers"]) == 8, len(c["layers"]))
    check("8 columns", len(c["columns"]) == 8, len(c["columns"]))
    deck_names = [d["name"]["value"] for d in c["decks"]]
    check("5 decks", deck_names == [d["name"] for d in bible["decks"]],
          deck_names)
    fx = [e.get("name") for e in c["video"]["effects"]]
    check("rack size 35 (34 + Transform)", len(fx) == 35, len(fx))
    byp = {e.get("name"): (e.get("bypassed") or {}).get("value")
           for e in c["video"]["effects"] if e.get("name") != "Transform"}
    check("30 bank effects bypassed", sum(1 for v in byp.values() if v) == 30,
          sum(1 for v in byp.values() if v))
    check("4 macros armed", sum(1 for v in byp.values() if v is False) == 4)
    blends = dict(PACK.LAYER_BLENDS)
    if a.layer_blends:
        blends.update({int(k): v for k, v in (x.split(":", 1) for x in
                                               a.layer_blends.split(","))})
    for i, L in enumerate(c["layers"], start=1):
        want_xf = "A" if i in INST.XFADE_A else ("B" if i in INST.XFADE_B
                                                  else "None")
        check("layer %d %s" % (i, L["name"]["value"]),
              L["name"]["value"] == INST.LAYER_ROLES[i - 1]
              and L["crossfadergroup"]["value"] == want_xf
              and L["ignorecolumntrigger"]["value"] == (i == 8)
              and L["video"]["mixer"]["Blend Mode"]["value"]
              == blends[i],
              "xf=%s ign=%s blend=%s" % (L["crossfadergroup"]["value"],
                                         L["ignorecolumntrigger"]["value"],
                                         L["video"]["mixer"]["Blend Mode"]["value"]))
    dash = {k: v["value"] for k, v in c["dashboard"].items()}
    check("dashboard 1-4 at 1, 5-8 at 0",
          all(dash["Link %d" % i] == 1.0 for i in range(1, 5))
          and all(dash["Link %d" % i] == 0.0 for i in range(5, 9)), dash)

    # ---- every clip in every deck ----
    n = 0
    mism = 0
    name_mism = 0
    for di, design in enumerate(decks):
        rig.deck_select(di + 1)
        # A deck switch is not instantaneous: poll until the column names are
        # this deck's before reading anything from it.
        want_cols = [str(c)[:14] for c in bible["decks"][di]["columns"]]
        for _ in range(40):
            time.sleep(0.5)
            cc = rig.composition()
            if [x["name"]["value"] for x in cc["columns"]] == want_cols:
                break
        else:
            print("  deck %d did not switch (columns %s)" % (
                di + 1, [x["name"]["value"] for x in cc["columns"]]))
        # Clip objects are re-created after the switch; the first reads can
        # return a neighbour's clip. Settle, and re-read on any mismatch.
        time.sleep(3.0)
        grid = {(int(cl["layer"]), int(cl["column"])): cl
                for cl in design.get("clips", [])}
        for col in range(1, 9):
            # Unconnected clips can report another deck's source parameters
            # when both decks hold the same generator in that slot (seen
            # 2026-10-23); the loaded clip itself is right. Connect the
            # column (and the SCOPE, which ignores column triggers) first.
            if a.connect:
                rig.post("/composition/columns/%d/connect" % col)
                rig.post("/composition/layers/8/clips/%d/connect" % col)
                time.sleep(1.5)
            for ln in range(1, 9):
                n += 1
                if a.sample and n % a.sample:
                    continue
                cl = grid.get((ln, col))
                sp, cj = rig.source_params(ln, col)
                live_name = (cj.get("name") or {}).get("value")
                if not live_name:
                    time.sleep(1.0)
                    sp, cj = rig.source_params(ln, col)
                    live_name = (cj.get("name") or {}).get("value")
                if cl is None:
                    continue
                want_name = str(cl.get("name") or cl.get("source"))[:PACK.MAX_NAME]
                if live_name != want_name:
                    time.sleep(1.5)
                    sp, cj = rig.source_params(ln, col)
                    live_name = (cj.get("name") or {}).get("value")
                if live_name != want_name:
                    name_mism += 1
                    if name_mism <= 20:
                        print("  NAME deck %d L%d C%d want %r got %r"
                              % (di + 1, ln, col, want_name, live_name))
                try:
                    item = lib.source(cl["source"])
                except KeyError:
                    continue
                want = PACK._coerce_params(item, cl.get("params"), rep,
                                           "verify")

                def diffs(sp):
                    out = []
                    for k, v in want.items():
                        spec = item.params[k]
                        if k not in sp:
                            # conditional parameter (Gradient Dither only
                            # when Stepped, Text Delay only when Animated):
                            # Resolume does not expose it, so it cannot be
                            # read back.
                            continue
                        live = (sp.get(k) or {}).get("value")
                        if spec.kind == "color":
                            ok = str(live).lower() == LIB.u32_to_hex(v).lower()
                        elif spec.kind == "choice":
                            ok = str(live) == str(spec.options[v])
                        elif spec.kind == "bool":
                            ok = bool(live) == bool(v)
                        elif spec.kind == "text":
                            ok = str(live) == str(v)
                        else:
                            ok = live is not None and close(live, v)
                            # A connected clip with music playing sits
                            # anywhere in its FFT floor..ceiling.
                            f = (cl.get("fft") or {}).get(k)
                            if not ok and live is not None and isinstance(f, dict):
                                lo = max(min(f["floor"], f["ceiling"]), spec.min)
                                hi = min(max(f["floor"], f["ceiling"]), spec.max)
                                ok = lo - 1e-3 <= float(live) <= hi + 1e-3
                        if not ok:
                            out.append((k, v, live))
                    return out

                bad = diffs(sp)
                # After a deck switch the clip name can update before its
                # source parameters do (seen 2026-10-23: deck 2 read deck
                # 1's values under deck 2's names). Settle and re-read
                # before calling anything a mismatch.
                for _ in range(3):
                    if not bad:
                        break
                    time.sleep(1.5)
                    sp, cj = rig.source_params(ln, col)
                    bad = diffs(sp)
                for k, v, live in bad:
                    mism += 1
                    if mism <= 40:
                        print("  MISMATCH deck %d L%d C%d %s/%s want %r "
                              "got %r" % (di + 1, ln, col,
                                          item.display_name, k, v, live))
        print("deck %d %-18s checked" % (di + 1, bible["decks"][di]["name"]))
    check("clip names match", name_mism == 0, "%d mismatches" % name_mism)
    check("clip parameters match (%d clips)" % n, mism == 0,
          "%d mismatches" % mism)
    rig.deck_select(1)
    print("\n%d checks, %d failed" % (checks, len(fails)))
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
