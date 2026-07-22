#!/usr/bin/env python3
"""Offline injector: wire the V3 SPEC clip set into a candidate copy of the comp.

Pattern precedent: inject_apc40_v2.py / author_v3_comp.py - all changes by text
surgery on a COPY of the R1 bytes; R1 and every prior candidate stay untouched.

What it builds (compositions/APC40_Visual_Twin_V3_Spec_Candidate.avc):
  * layers 1-148 keep their indices, MIDI paths, and blend - only each deck-0
    clip's content changes:
      - TextBlock generator  ->  VideoFormatReaderSource (per-control mov)
      - column 0 = idle (Tier A) / static cap (Tier B)
      - Transform Position X/Y = tile centre - (960, 540); Scale/W/H = 100
      - clip Param name="Name" set (deck label law: the Param, not the
        attribute; CompositionInfo is a decoy)
  * a second deck Column ("States"), and per Tier A control a column-1 clip
    playing the active/fire mov. Not MIDI-mapped (the note-off -> clips/2
    species has no rig specimen yet); trigger manually or via a future preset.
  * appended layer 149 "V3 Tier B Bed" (static arcs/slots/ticks/legends) and
    layer 150 "V3 Chassis Frame" (reused blessed chassis MOV), Add blend.
  * composition renamed in BOTH name fields (composition Param "Name" +
    CompositionInfo), per the .avc name-field law.

The 203-shortcut controller preset is untouched and keeps working: all its
paths land on layers 1-148 / clips/1 (column 0).

Usage:  python inject_apc40_v3_spec.py [--check-only]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from author_v3_comp import build_layer, build_clip, frag, R1, R1_SHA256  # noqa: E402
from lxml import etree                                                   # noqa: E402

MANIFEST = ROOT / "build" / "spec_manifest_v3.json"
OUT = ROOT / "compositions" / "APC40_Visual_Twin_V3_Spec_Candidate.avc"
NEW_NAME = "APC40_Visual_Twin_V3_Spec_Candidate"

# Media plays from the rig's canonical local clip folder (fresh, never-
# rewritten paths - Avenue renders those reliably; the in-repo media/ tree
# stays the append-only source of truth, mirrored there by robocopy).
MEDIA_WIN = r"C:\Resolume Clips\APC40_V3"
BED_MOV_WIN = MEDIA_WIN + r"\APC40_MKII_V3_TierB_Bed_Alpha.mov"
CHASSIS_MOV_WIN = MEDIA_WIN + r"\APC40_MKII_V3_Chassis_Premult_Alpha.mov"

_uid = [1795000000000]
NL = "\r\n"          # R1 is uniformly CRLF (23686 lines) - keep it that way


def fresh_uid():
    _uid[0] += 7
    return str(_uid[0])


def win_path(rel):
    # manifest paths are repo-relative ("media/clips_spec/..."); the play
    # mirror at MEDIA_WIN holds the CONTENTS of media/
    rel = rel[6:] if rel.startswith("media/") else rel
    return MEDIA_WIN + "\\" + rel.replace("/", "\\")


def set_first(pattern, repl, s, required=True, tag=""):
    out, n = re.subn(pattern, repl, s, count=1)
    if required and n != 1:
        raise SystemExit(f"surgery failed: {tag or pattern}")
    return out


def video_source_block(width, height, file_win, indent="\t\t\t\t"):
    # exact shape of an Avenue-saved file clip (specimen: build_gen_src.avc) -
    # no storage attribute, width/height = the file's native dims
    return (f'<VideoSource name="VideoSource" width="{width}" '
            f'height="{height}" type="VideoFormatReaderSource">{NL}'
            f'{indent}\t<VideoFormatReaderSource fileName="{file_win}"/>{NL}'
            f'{indent}</VideoSource>')


def rewrite_clip(block, rec, state_key):
    """Text surgery on one original clip block: source, name, transform."""
    st = rec["states"][state_key]
    tw = rec["tile_rect"][2] - rec["tile_rect"][0]
    th = rec["tile_rect"][3] - rec["tile_rect"][1]
    # 1. swap the stale thumbnail cache for a specimen-faithful file preload
    #    (Avenue-saved video clips carry <PreloadData><VideoFile value=.../>)
    pm = re.search(r"(\r?\n(\s*))<PreloadData>.*?</PreloadData>", block, flags=re.S)
    if pm:
        rep = (f"{pm.group(1)}<PreloadData>{NL}{pm.group(2)}\t"
               f'<VideoFile value="{win_path(st["file"])}"/>{NL}'
               f"{pm.group(2)}</PreloadData>")
        block = block[:pm.start()] + rep + block[pm.end():]
    # 2. clip deck label - the clip's own Param name="Name" (first in block)
    label = f"{rec['name']} - {state_key}"
    block = set_first(r'(<Param name="Name" T="STRING" default="[^"]*" value=")[^"]*(")',
                      rf"\g<1>{label}\g<2>", block, tag="clip name")
    # 2b. trigger style stays R1's TOGGLE (Jeffrey's call): press = active
    # clip lights, press again = disconnect. The bed carries a static idle
    # image of every control, so a toggled-off control falls back to its calm
    # idle look instead of a hole.
    # 3. swap the primary source: TextBlock generator -> native file reader
    m = re.search(r"<VideoSource .*?</VideoSource>", block, flags=re.S)
    if not m:
        raise SystemExit("surgery failed: VideoSource")
    block = block[:m.start()] + video_source_block(tw, th, win_path(st["file"])) \
        + block[m.end():]
    # 3b. clip video-track canvas = the file's native dims (Avenue renders the
    # canvas 1:1 in comp space; a 1920x1080 canvas would stretch small tiles -
    # the fit bug seen on the rig cold-open of the first spec candidate).
    # Tempered anchor: the 27 CC-fanned clips serialize Opacity before Width
    # inside the VideoTrack Params, so Width is not always first.
    for pname, val in (("Width", tw), ("Height", th)):
        block, n = re.subn(
            rf'(<VideoTrack name="VideoTrack">(?:(?!</Params>).)*?'
            rf'<ParamRange name="{pname}" T="DOUBLE" default="[^"]*" value=")[^"]*(")',
            rf"\g<1>{val}\g<2>", block, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"surgery failed: videotrack {pname}")
    # 3c. normalize any stale CC-fanned clip opacity (saved mid-performance
    # values like 0.82 would dim caps at cold-open) back to 1
    block = re.sub(
        r'(<VideoTrack name="VideoTrack">(?:(?!</Params>).)*?'
        r'<ParamRange name="Opacity" T="DOUBLE" default="1" value=")[^"]*(")',
        r"\g<1>1\g<2>", block, count=1, flags=re.S)
    # 4. Transform: pixel-true placement, native scale.
    # Avenue omits a ParamRange whose stored value equals its default (the 9
    # stop clips sit at y-centre 540, so Position Y is absent) - set when
    # present, skip when absent-and-default, insert otherwise.
    defaults = {"Position X": 0, "Position Y": 0,
                "Scale": 100, "Scale W": 100, "Scale H": 100}
    for pname, val in (("Position X", rec["position_x"]),
                       ("Position Y", rec["position_y"]),
                       ("Scale", 100), ("Scale W", 100), ("Scale H", 100)):
        v = f"{val:g}"
        pat = rf'(<ParamRange name="{pname}" T="DOUBLE" default="[^"]*" value=")[^"]*(")'
        if re.search(pat, block):
            block = set_first(pat, rf"\g<1>{v}\g<2>", block, tag=f"transform {pname}")
        elif abs(float(val) - defaults[pname]) < 1e-9:
            continue
        else:
            tm = re.search(
                r'(<RenderPass storage="0" name="Transform"[^>]*>\r?\n(\t*)<Params name="Params">\r?\n)',
                block)
            if not tm:
                raise SystemExit(f"surgery failed: Transform Params ({pname})")
            ins = (f'{tm.group(2)}\t<ParamRange name="{pname}" T="DOUBLE" '
                   f'default="{defaults[pname]:g}" value="{v}">{NL}'
                   f'{tm.group(2)}\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>{NL}'
                   f'{tm.group(2)}\t</ParamRange>{NL}')
            block = block[:tm.end(1)] + ins + block[tm.end(1):]
    return block


def make_fullframe_clip(template_block, layer_index, name, mov_win, column):
    """Full-frame clip (bed / chassis) cloned from a REWRITTEN tile block.

    The lxml-authored clip skeleton (author_v3_comp.build_clip) loads and
    connects but renders BLACK on the rig; a rewritten R1 clip block is the
    proven-to-render species (verified live: the same mov loaded through the
    normal clip-open path renders). Clone that species and swap file, canvas,
    layer, and transform."""
    block = template_block
    old_file = re.search(r'<VideoFormatReaderSource fileName="([^"]*)"', block).group(1)
    block = block.replace(old_file, mov_win)
    block = set_first(r'(<Clip name="Clip" uniqueId="\d+" layerIndex=")\d+(")',
                      rf"\g<1>{layer_index}\g<2>", block, tag="ff layerIndex")
    block = set_first(r'(layerIndex="\d+" columnIndex=")\d+(")',
                      rf"\g<1>{column}\g<2>", block, tag="ff columnIndex")
    block = re.sub(r'uniqueId="\d+"', lambda m: f'uniqueId="{fresh_uid()}"', block)
    block = set_first(r'(<Param name="Name" T="STRING" default="[^"]*" value=")[^"]*(")',
                      rf"\g<1>{name}\g<2>", block, tag="ff name")
    block = set_first(r'(<VideoSource name="VideoSource" width=")\d+(" height=")\d+(")',
                      r"\g<1>1920\g<2>1080\g<3>", block, tag="ff source dims")
    for pname, val in (("Width", 1920), ("Height", 1080)):
        block, n = re.subn(
            rf'(<VideoTrack name="VideoTrack">(?:(?!</Params>).)*?'
            rf'<ParamRange name="{pname}" T="DOUBLE" default="[^"]*" value=")[^"]*(")',
            rf"\g<1>{val}\g<2>", block, count=1, flags=re.S)
        if n != 1:
            raise SystemExit(f"ff canvas {pname}")
    for pname in ("Position X", "Position Y"):
        block = re.sub(
            rf'(<ParamRange name="{pname}" T="DOUBLE" default="[^"]*" value=")[^"]*(")',
            r"\g<1>0\g<2>", block, count=1)
    return block


def make_active_clone(block, rec, state_key):
    """Column-1 clone of a rewritten block, fresh uids, active/fire source."""
    block = set_first(r'(<Clip name="Clip" uniqueId="\d+" layerIndex="\d+" columnIndex=")0(")',
                      r"\g<1>1\g<2>", block, tag="columnIndex")
    block = re.sub(r'uniqueId="\d+"', lambda m: f'uniqueId="{fresh_uid()}"', block)
    idle_key = "idle" if "idle" in rec["states"] else "static"
    old_file = win_path(rec["states"][idle_key]["file"])
    new_file = win_path(rec["states"][state_key]["file"])
    if old_file not in block:
        raise SystemExit("surgery failed: clone source path")
    block = block.replace(old_file, new_file)
    block = set_first(r'(<Param name="Name" T="STRING" default="[^"]*" value=")[^"]*(")',
                      rf"\g<1>{rec['name']} - {state_key}\g<2>", block, tag="clone name")
    return block


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    raw = R1.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == R1_SHA256, "R1 changed - refusing"
    assert raw[:1] == b"<", "R1 must be BOM-free"
    text = raw.decode("utf-8")
    manifest = json.load(open(MANIFEST))
    recs = {c["layer"]: c for c in manifest["controls"]}
    assert len(recs) == 148, f"manifest has {len(recs)} controls"

    # media existence gate (fail before touching anything)
    missing = []
    for c in manifest["controls"]:
        for st in c["states"].values():
            if not (ROOT / st["file"]).exists():
                missing.append(st["file"])
    for p in (ROOT / "media" / "APC40_MKII_V3_TierB_Bed_Alpha.mov",
              ROOT / "media" / "APC40_MKII_V3_Chassis_Premult_Alpha.mov"):
        if not p.exists():
            missing.append(str(p))
    if missing:
        raise SystemExit(f"missing media ({len(missing)}): {missing[:5]}")
    if args.check_only:
        print("check-only: all media present, R1 sha OK")
        return

    # ---- rewrite the 148 column-0 clips
    out_parts = []
    pos = 0
    n_rewritten = 0
    clip_re = re.compile(
        r'<Clip name="Clip" uniqueId="\d+" layerIndex="(\d+)" columnIndex="0">')
    actives = []
    ff_template = None
    for m in clip_re.finditer(text):
        end = text.index("</Clip>", m.start()) + len("</Clip>")
        block = text[m.start():end]
        layer = int(m.group(1)) + 1
        rec = recs.get(layer)
        if rec is None:
            continue
        state0 = "idle" if "idle" in rec["states"] else "static"
        new_block = rewrite_clip(block, rec, state0)
        if ff_template is None:
            ff_template = new_block
        state1 = next((s for s in ("active", "fire") if s in rec["states"]), None)
        # COLUMN SWAP (Jeffrey, 2026-07-20): the preset's 148 connects target
        # clips/1 (column 0) - putting the ACTIVE/FIRE state there makes every
        # hardware press visibly light its control. The idle wall lives in
        # column 1 (trigger it to reset). Tier B statics sit in both columns.
        active_block = make_active_clone(new_block, rec, state1 or state0)
        active_block = set_first(r'(layerIndex="\d+" columnIndex=")1(")',
                                 r"\g<1>0\g<2>", active_block, tag="swap active col")
        idle_block = set_first(r'(layerIndex="\d+" columnIndex=")0(")',
                               r"\g<1>1\g<2>", new_block, tag="swap idle col")
        out_parts.append(text[pos:m.start()])
        out_parts.append(active_block)
        pos = end
        n_rewritten += 1
        actives.append(idle_block)
    out_parts.append(text[pos:])
    text2 = "".join(out_parts)
    assert n_rewritten == 148, f"rewrote {n_rewritten}/148 clips"

    # ---- normalize stale per-layer state from R1's last session (saved layer
    # opacity 0.79 / master 0.75 on a few layers would dim their controls at
    # cold-open; no preset shortcut targets layer params, so this is safe)
    def normalize_layer(m):
        b = m.group(0)
        b = re.sub(r'(<ParamRange name="Opacity" T="DOUBLE" default="1" value=")[^"]*(")',
                   r"\g<1>1\g<2>", b)
        b = re.sub(r'(<ParamRange name="Master" T="DOUBLE" default="1" value=")[^"]*(")',
                   r"\g<1>1\g<2>", b)
        return b
    text2 = re.sub(r"<Layer .*?</Layer>", normalize_layer, text2, flags=re.S)

    # ---- second column. After the column swap: column 1 (index 0, MIDI-wired)
    # = "Pressed" active states; column 2 (index 1) = "APC40 Live" idle wall.
    cm = re.search(r"<Column uniqueId=\"\d+\" columnIndex=\"0\">.*?</Column>\r?\n",
                   text2, flags=re.S)
    col = cm.group(0)
    col2 = col.replace('columnIndex="0"', 'columnIndex="1"')
    col2 = re.sub(r'uniqueId="\d+"', lambda m: f'uniqueId="{fresh_uid()}"', col2)
    col2 = re.sub(r'(<Param name="Name" T="STRING" default="[^"]*" value=")[^"]*(")',
                  r"\g<1>APC40 Live\g<2>", col2, count=1)
    text2 = text2[:cm.end()] + "\t\t" + col2 + text2[cm.end():]
    ncol1 = re.sub(r'(<Param name="Name" T="STRING" default="[^"]*" value=")[^"]*(")',
                   r"\g<1>Pressed\g<2>", col, count=1)
    text2 = text2.replace(col, ncol1, 1)

    # ---- column-1 active clips (before </Deck>)
    dend = text2.index("</Deck>")
    text2 = text2[:dend] + "".join(b + NL + "\t\t" for b in actives) + text2[dend:]

    # ---- appended layers 149 + 150. Layers keep the author-precedent clone
    # (rig-proven: the bed rendered fine on layer 149 via a live clip-open).
    # Their CLIPS clone the rewritten-tile species instead - the lxml-authored
    # clip skeleton loads but renders BLACK on the rig.
    tree = etree.fromstring(text2.encode("utf-8"))
    layer_tmpl = tree.findall("Layer")[-1]
    specs = [("V3 Tier B Bed", 3, BED_MOV_WIN), ("V3 Chassis Frame", 5, CHASSIS_MOV_WIN)]
    layer_frags, clip_frags = [], []
    for i, (name, cid, mov) in enumerate(specs):
        layer_frags.append(
            frag(build_layer(layer_tmpl, name, cid, 148 + i), "\t").replace("\n", NL))
        for col in (0, 1):
            clip_frags.append("\t\t" + make_fullframe_clip(
                ff_template, 148 + i, name, mov, col) + NL)
    cf = text2.index("<CrossFader")
    text2 = text2[:cf] + "".join(layer_frags) + text2[cf:]
    dend = text2.index("</Deck>")
    text2 = text2[:dend] + "".join(clip_frags) + text2[dend:]

    # ---- registration counts: Avenue trusts these attrs at load and silently
    # DROPS any layer/column nodes beyond them (proven on the rig - the first
    # spec candidate cold-opened with 148 layers / 1 column, both appends gone)
    text2 = set_first(r'(<Composition [^>]* numLayers=")148(")', r"\g<1>150\g<2>",
                      text2, tag="root numLayers")
    text2 = set_first(r'(<Composition [^>]* numColumns=")1(")', r"\g<1>2\g<2>",
                      text2, tag="root numColumns")
    text2 = set_first(r'(<Deck [^>]*numLayersWithContent=")148(")', r"\g<1>150\g<2>",
                      text2, tag="deck numLayersWithContent")
    text2 = set_first(r'(<Deck [^>]*numColumnsWithContent=")1(")', r"\g<1>2\g<2>",
                      text2, tag="deck numColumnsWithContent")
    text2 = set_first(r'(<Deck [^>]* numLayers=")148(")', r"\g<1>150\g<2>",
                      text2, tag="deck numLayers")
    text2 = set_first(r'(<Deck [^>]* numColumns=")1(")', r"\g<1>2\g<2>",
                      text2, tag="deck numColumns")

    # ---- rename BOTH comp name fields (global replace covers Param + Info)
    old_name = re.search(r'<CompositionInfo name="([^"]*)"', text2).group(1)
    text2 = text2.replace(old_name, NEW_NAME)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = text2.encode("utf-8")
    assert data[:1] == b"<", "would write a BOM"
    OUT.write_bytes(data)

    # ---- validate
    cr = etree.fromstring(data)
    nlayers = len(cr.findall("Layer"))
    deck0 = cr.findall(".//Deck")[0]
    nclips = len(deck0.findall("Clip"))
    ncols = len(deck0.findall("Column"))
    srcs = [e.get("fileName") for e in cr.findall(".//VideoFormatReaderSource")]
    uids = re.findall(r'uniqueId="(\d+)"', text2)
    root_attrs = re.search(r'<Composition [^>]*>', text2).group(0)
    deck_attrs = re.search(r'<Deck [^>]*>', text2).group(0)
    report = {
        "candidate": str(OUT),
        "layers": nlayers,
        "deck0_columns": ncols,
        "deck0_clips": nclips,
        "col0_rewritten": n_rewritten,
        "col1_active_clips": len(actives),
        "video_sources": len(srcs),
        "registration": {"root": root_attrs, "deck0": deck_attrs[:160]},
        "unique_ids_unique": len(uids) == len(set(uids)),
        "r1_untouched": hashlib.sha256(R1.read_bytes()).hexdigest() == R1_SHA256,
        "utf8_no_bom": data[:1] == b"<",
        "candidate_sha256": hashlib.sha256(data).hexdigest(),
    }
    print(json.dumps(report, indent=1))
    assert nlayers == 150, nlayers
    assert ncols == 2, ncols
    assert nclips == 148 + len(actives) + 4, nclips
    assert len(actives) == 148, len(actives)
    assert report["unique_ids_unique"]
    assert 'numLayers="150"' in root_attrs and 'numColumns="2"' in root_attrs
    assert 'numLayers="150"' in deck_attrs and 'numColumns="2"' in deck_attrs
    print("OK")


if __name__ == "__main__":
    main()
