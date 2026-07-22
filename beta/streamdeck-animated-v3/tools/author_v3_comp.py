#!/usr/bin/env python3
"""Author the append-only APC40 Animated Twin V3 comparison composition (offline).

Strategy (surgical, append-only -- never mutates R1's 1..148 bytes):
  1. Byte-exact renamed clone of R1  -> APC40_Visual_Twin_V3_Base.avc
     (guaranteed to open; the rollback anchor; identical image to R1).
  2. Authored candidate  -> APC40_Visual_Twin_V3_Animated_Candidate.avc
     R1 text + TWO appended Add-blend layers whose deck-0 clips play the V3
     surface + chassis alpha MOVs.  Built by TEXT insertion so every original
     byte (148 layers, 203-shortcut-compatible structure, decks) is preserved;
     only new <Layer> and <Clip> nodes are added and the composition is renamed.

Layers are appended (indices 149, 150) so the 1..148 witness layers keep their
positions and the controller XML needs no change.  Bypassing 149 + 150 restores
the R1 image exactly.  Clip sources are VideoFormatReaderSource (native file
reader), matched to R1's own 7.27.1 clip skeleton for schema fidelity.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import re
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT.parents[1] / "compositions" / "APC40_Visual_QA_148.avc"
OUT_DIR = ROOT / "compositions"
MEDIA_WIN = r"C:\Art Projects\Res_Fable\react-kit-apc40-v2-overnight\beta\streamdeck-animated-v3\media"
SURFACE_MOV = MEDIA_WIN + r"\APC40_MKII_Animated_Twin_V3_Surface_Alpha.mov"
CHASSIS_MOV = MEDIA_WIN + r"\APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov"

R1_SHA256 = "91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99"

_uid = [1793000000000]


def fresh_uid():
    _uid[0] += 7
    return str(_uid[0])


def regen_uids(el):
    for e in el.iter():
        if e.get("uniqueId") is not None:
            e.set("uniqueId", fresh_uid())


def set_param(parent, tag, name, value):
    for e in parent.iter():
        if e.tag == tag and e.get("name") == name:
            e.set("value", value)
            return True
    return False


def build_layer(template_layer, name, color_id, layer_index):
    L = copy.deepcopy(template_layer)
    regen_uids(L)
    if L.get("layerIndex") is not None:      # renumber (template inherited 147)
        L.set("layerIndex", str(layer_index))
    set_param(L, "Param", "Name", name)
    set_param(L, "ParamChoice", "ColorId", str(color_id))
    set_param(L, "ParamRange", "Opacity", "1")
    set_param(L, "ParamChoice", "Bypassed", "0")
    set_param(L, "ParamChoice", "Solo", "0")
    # keep the Add mixer inherited from the R1 template
    return L


def build_clip(template_clip, layer_index, name, mov_path):
    C = copy.deepcopy(template_clip)
    C.set("layerIndex", str(layer_index))
    C.set("columnIndex", "0")
    C.set("uniqueId", fresh_uid())
    # drop the source-specific preload cache; Resolume regenerates on load
    for pd in C.findall("PreloadData"):
        C.remove(pd)
    regen_uids(C)
    set_param(C, "Param", "Name", name)
    # swap the primary source: text generator -> native video file reader
    vs = C.find(".//VideoSource")
    parent = vs.getparent()
    idx = list(parent).index(vs)
    parent.remove(vs)
    new_vs = etree.Element("VideoSource", name="VideoSource",
                           width="1920", height="1080", type="VideoFormatReaderSource")
    etree.SubElement(new_vs, "VideoFormatReaderSource", fileName=mov_path)
    parent.insert(idx, new_vs)
    # force the clip Transform to identity so the full-frame MOV lands 1:1
    tr = C.find(".//RenderPass[@name='Transform']")
    if tr is not None:
        for pr in tr.findall(".//ParamRange"):
            if pr.get("default") is not None:
                pr.set("value", pr.get("default"))
    return C


def frag(el, indent):
    """Serialize an element to indented text for insertion into the R1 source."""
    xml = etree.tostring(el, pretty_print=True).decode()
    return "".join(indent + ln + "\n" for ln in xml.rstrip("\n").splitlines())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", type=int, default=2, choices=(1, 2, 3))
    args = ap.parse_args()

    raw = R1.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == R1_SHA256, "R1 changed -- refusing"
    text = raw.decode("utf-8")

    tree = etree.parse(str(R1))
    r = tree.getroot()
    layer_tmpl = r.findall("Layer")[-1]
    clip_tmpl = r.findall(".//Deck")[0].find(".//Clip")

    # --- build the appended nodes (chassis first / lower, surface on top)
    specs = [
        ("V3 Chassis Frame", 3, CHASSIS_MOV),
        ("V3 Animated Surface", 5, SURFACE_MOV),
        ("V3 Accent Rail", 1, CHASSIS_MOV),
    ][:args.layers]

    layer_frags, clip_frags = [], []
    for i, (name, cid, mov) in enumerate(specs):
        layer_frags.append(frag(build_layer(layer_tmpl, name, cid, 148 + i), "\t"))
        clip_frags.append(frag(build_clip(clip_tmpl, 148 + i, name, mov), "\t\t"))

    # --- TEXT insertion: layers before <CrossFader ; clips before deck-0 </Deck>
    cf = text.index("<CrossFader")
    text2 = text[:cf] + "".join(layer_frags) + text[cf:]
    dend = text2.index("</Deck>")
    text2 = text2[:dend] + "".join(clip_frags) + text2[dend:]

    # --- rename composition (title bar + identity), like inject_apc40_v2
    name_match = re.search(r'<CompositionInfo name="([^"]*)"', text2)
    old_name = name_match.group(1)
    new_name = "APC40_Visual_Twin_V3_Animated_Candidate"
    text2 = text2.replace(old_name, new_name)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cand = OUT_DIR / "APC40_Visual_Twin_V3_Animated_Candidate.avc"
    cand.write_bytes(text2.encode("utf-8"))

    # --- byte-exact renamed base clone (rollback anchor)
    base_text = text.replace(old_name, "APC40_Visual_Twin_V3_Base")
    base = OUT_DIR / "APC40_Visual_Twin_V3_Base.avc"
    base.write_bytes(base_text.encode("utf-8"))

    # --- validate the candidate
    cr = etree.fromstring(text2.encode("utf-8"))
    nlayers = len(cr.findall("Layer"))
    nclips = len(cr.findall(".//Deck")[0].findall("Clip"))
    movs = [e.get("fileName") for e in cr.findall(".//VideoFormatReaderSource")]
    orig_texts = re.findall(r'<ParamText name="Text" value="([^"]*)"', text)
    kept = sum(1 for t in orig_texts if f'value="{t}"' in text2)
    report = {
        "candidate": str(cand),
        "base_clone": str(base),
        "layers": nlayers,
        "deck0_clips": nclips,
        "appended_layers": args.layers,
        "video_sources": movs,
        "original_148_texts_preserved": f"{kept}/{len(orig_texts)}",
        "r1_untouched_sha256_ok": hashlib.sha256(R1.read_bytes()).hexdigest() == R1_SHA256,
        "candidate_parses": True,
        "candidate_sha256": hashlib.sha256(text2.encode()).hexdigest(),
    }
    import json
    print(json.dumps(report, indent=1))
    assert nlayers == 148 + args.layers, nlayers
    assert nclips == 148 + args.layers, nclips
    assert kept == len(orig_texts), (kept, len(orig_texts))
    print("OK")


if __name__ == "__main__":
    main()
