#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_all.py - rebuild the shipped packs from their own bible.json + decks.json on the
current library (7.29), with each pack's original settings recovered from its files.

    python -m resolume_build.rebuild_all --check [--only slug,slug]   # build to a scratch dir, diff only
    python -m resolume_build.rebuild_all --write [--only slug,slug]   # overwrite the pack in place

--check proves the recovery: a pack rebuilt with no design change must differ from the shipped
file by nothing but what you changed on purpose. Recovered per pack: id base and preset id (from
the .avc / preset), layer blend overrides (read off the shipped layers' mixers), theme (SPEC).
"""
import argparse
import difflib
import glob
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from resolume_build import pack as PACK            # noqa: E402
from resolume_build import racks as RACKS          # noqa: E402
from resolume_build import build_cli as CLI        # noqa: E402
from resolume_build import spectral_pass as SP     # noqa: E402

# slug -> (folder, avc glob, theme). Theme is the rack theme the pack was built with.
SPEC = {
    "studio-one": ("studio-one", "Studio One - War Of The Worlds 1938.avc", "studio"),
    "dead-air": ("dead-air", "Dead Air Listening Posts.avc", "dead-air"),
    "dew-line": ("dew-line", "Dew Line - The Spinningwork.avc", "dew-line"),
    "library-hand": ("library-hand", "The Library And The Hand - GUSTO.avc", "library-hand"),
    "signal-lost": ("signal-lost", "Signal Lost - Transmission From Tomorrow.avc", "signal-lost"),
    "the-manual": ("the-manual", "The Manual - Avenue 7.28.1.avc", "the-manual"),
    "the-surface": ("the-surface", "The Surface - APC40 mkII + MIDI.avc", "the-surface"),
    "the-mixers": ("the-mixers", "The Mixers - V-4, MXPro, MX-1 + JVC.avc", "the-mixers"),
    "the-mixers-still": ("the-mixers-still", "The Mixers - V-4, MXPro, MX-1 + JVC.avc", "the-mixers"),
    "motion-dive": ("motion-dive", "Motion Dive Tokyo on APC40.avc", "motion-dive"),
}


def recover(folder, avc_name):
    avc = os.path.join(ROOT, "packs", folder, avc_name)
    head = open(avc, encoding="utf-8").read(4000)
    uid = int(re.search(r'<Composition [^>]*uniqueId="(\d+)"', head).group(1))
    root = ET.parse(avc).getroot()
    ndecks = int(root.get("numDecks"))
    preset = glob.glob(os.path.join(ROOT, "packs", folder, "APC 40 MK II - *.xml"))
    pid = None
    for p in sorted(preset, key=len):
        m = re.search(r'presetId="?(\d+)', open(p, encoding="utf-8").read(3000))
        if m:
            pid = m.group(1)
            break
    blends = {}
    for i, layer in enumerate(root.findall("Layer"), start=1):
        # the layer's own blend is the non-edge mixer: [fade, BLEND, fade] or [BLEND, fade]
        ms = [rp.get("name") for rp in layer.iter("RenderPass") if rp.get("baseType") == "Mixer"]
        if ms:
            blends[i] = ms[1] if len(ms) >= 3 else ms[0]
    return {"id_base": uid - (ndecks + 1), "preset_id": pid, "blends": blends}


def build(slug, out_dir, decks_path=None, spectral=False):
    folder, avc_name, theme = SPEC[slug]
    rec = recover(folder, avc_name)
    pdir = os.path.join(ROOT, "packs", folder)
    bible = json.load(open(os.path.join(pdir, "bible.json"), encoding="utf-8"))
    decks = json.load(open(decks_path or os.path.join(pdir, "decks.json"), encoding="utf-8"))
    if isinstance(decks, dict) and "decks" in decks:
        decks = decks["decks"]
    if spectral:
        SP.apply(decks, bible)
    pal = CLI.pick_palette(bible)
    rack = RACKS.rack_for(pal, theme=theme)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    blends = {k: v for k, v in rec["blends"].items()
              if PACK.LAYER_BLENDS.get(k, "Add") != v}
    avc, preset, rep, counts = PACK.build_pack(
        bible, decks, rack, out_dir, theme, rec["preset_id"], rec["id_base"],
        row_colors=CLI.row_colors_for(bible), layer_blends=blends)
    return avc, preset, rep, counts, rec, blends, decks


def diff(a, b, n=6):
    x = open(a, encoding="utf-8").read().splitlines()
    y = open(b, encoding="utf-8").read().splitlines()
    d = [l for l in difflib.unified_diff(x, y, lineterm="", n=0)
         if not l.startswith(("---", "+++", "@@"))]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--spectral", action="store_true", help="apply the Spectral pass to empty AURA slots")
    ap.add_argument("--scratch", default=os.path.join(ROOT, ".rebuild_scratch"))
    a = ap.parse_args()
    slugs = a.only.split(",") if a.only else [k for k in SPEC if k not in ("dew-line", "motion-dive")]
    for slug in slugs:
        out = os.path.join(a.scratch, slug)
        avc, preset, rep, counts, rec, blends, decks = build(slug, out, spectral=a.spectral)
        folder, avc_name, _ = SPEC[slug]
        old_avc = os.path.join(ROOT, "packs", folder, avc_name)
        old_xml = os.path.join(ROOT, "packs", folder, os.path.basename(preset))
        print("%s: %s repairs=%s recovered=%s overrides=%s" % (slug, counts, rep.repairs, rec["id_base"], blends))
        da = diff(old_avc, avc)
        dx = diff(old_xml, preset) if os.path.exists(old_xml) else ["(no shipped preset)"]
        print("  avc diff lines: %d   preset diff lines: %d" % (len(da), len(dx)))
        for l in (da + dx)[:12]:
            print("    " + l[:200])
        if a.write:
            shutil.copy2(avc, old_avc)          # compositions only: shipped presets carry later patches
            print("  WROTE", old_avc)
            if a.spectral:
                dj = os.path.join(ROOT, "packs", folder, "decks.json")
                json.dump({"decks": decks}, open(dj, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
