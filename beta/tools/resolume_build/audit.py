#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit.py - the offline robustness audit for a composition (.avc) and the APC40 preset it selects.

    python -m resolume_build.audit "packs/signal-lost/Signal Lost - Transmission From Tomorrow.avc" \
        [--preset "packs/signal-lost/APC 40 MK II - Signal Lost.xml"]
    python -m resolume_build.audit --all            # every pack under packs/ plus the older compositions

No Avenue needed: it reads the files. What it checks (FAIL means a performer could be hurt or left
with a dead control; WARN means look at it; INFO is a fact):

  structure   XML parses; unique ids; deck/layer/column counts agree; every cell has a source
  safety      strobe sources and effects stay under the flash caps (kinetic.py), no strobe fills the
              frame, saturated red never strobes, the heavy-effect and chain-length limits hold
  fft         every FFT binding points at the audio engine, with sane gain, fall-back and range
  look        clip opacity in 0..1, no NaN, no text smaller than the readable floor
  preset      every shortcut resolves to something that exists in this composition (layer, clip,
              column, effect, dashboard link, FFT anchor), the standard's 13 rules pass, and the
              preset the composition selects exists

Exit code 0 when nothing FAILs.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import kinetic as K                  # noqa: E402
from resolume_build import preset_patch as PP            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIDI = PP.MIDI
LAYER_NAMES = ["BED", "BODY", "FIGURE", "LIGHT", "TEXT", "AURA", "GRAIN", "SCOPE"]
DASH_NAMES = ["COLOUR", "TEXTURE", "SPACE", "FRACTURE", "GLOW", "ECHO", "FRINGE", "VOID"]
GLOBAL_PATHS = {
    "/composition/speed", "/composition/master", "/composition/bypassed", "/composition/crossfader/phase",
    "/composition/disconnectall", "/composition/select", "/composition/selectnextdeck", "/composition/selectprevdeck",
    "/composition/connectnextcolumn", "/composition/connectprevcolumn", "/audiodevicemanager/params/fftinputgain",
    "/composition/tempocontroller/tempo", "/composition/tempocontroller/tempotap", "/composition/tempocontroller/resync",
}
MAX_CLIP_EFFECTS = 4
TEXT_SOURCES = ("TextBlock", "TextAnimator")


def slug(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def fnum(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


class Report(object):
    def __init__(self, name):
        self.name = name
        self.rows = []                    # (level, check, detail)
        self.counts = collections.Counter()

    def add(self, level, check, detail=""):
        self.rows.append((level, check, detail))
        self.counts[level] += 1

    def ok(self, check, detail=""):
        self.add("PASS", check, detail)

    def text(self, verbose=False):
        out = ["== %s" % self.name]
        for level, check, detail in self.rows:
            if level == "PASS" and not verbose:
                continue
            out.append("  %-5s %-34s %s" % (level, check, detail))
        out.append("  -> %d pass, %d warn, %d fail" % (self.counts["PASS"], self.counts["WARN"], self.counts["FAIL"]))
        return "\n".join(out)


def params_of(node):
    """{name: element} for the direct parameter children of a Params block."""
    d = {}
    for p in node.findall("Params"):
        for c in p:
            nm = c.get("name")
            if nm:
                d[nm] = c
    return d


def pvalue(el):
    return None if el is None else el.get("value")


def fft_of(el):
    """The FFT binding of a parameter element, as a dict, or None."""
    f = el.find("PhaseSourceFFT")
    if f is None:
        return None
    pp = params_of(f)
    vr = el.find("ValueRange")
    fr = pp.get("FrequencyRange")
    frv = fr.find("ValueRange") if fr is not None else None
    return dict(link=f.get("linkId"), gain=fnum(pvalue(pp.get("Gain"))), fallback=fnum(pvalue(pp.get("Fallback"))),
                band_lo=fnum(frv.get("min")) if frv is not None else None, band_hi=fnum(frv.get("max")) if frv is not None else None,
                lo=fnum(vr.get("min")) if vr is not None else None, hi=fnum(vr.get("max")) if vr is not None else None,
                value=fnum(el.get("value")))


class Clip(object):
    pass


def read_clips(root):
    clips = []
    for deck in root.iter("Deck"):
        di = int(deck.get("deckIndex", "0"))
        for c in deck.iter("Clip"):
            k = Clip()
            k.deck, k.layer, k.col = di, int(c.get("layerIndex", "0")) + 1, int(c.get("columnIndex", "0")) + 1
            cp = params_of(c)
            k.name = pvalue(cp.get("Name")) or ""
            vt = c.find("VideoTrack")
            k.opacity = None
            k.effects = []
            k.src = None
            k.src_params = {}
            if vt is not None:
                vp = params_of(vt)
                k.opacity = fnum(pvalue(vp.get("Opacity")))
                chain = vt.find("RenderPass")
                if chain is not None:
                    for rp in chain.findall("RenderPass"):
                        if rp.get("name") == "Transform":
                            continue
                        k.effects.append(rp)
                ps = vt.find("PrimarySource")
                if ps is not None:
                    gen = ps.find(".//RenderPass")
                    if gen is not None:
                        k.src = gen.get("type") or gen.get("name")
                        k.src_params = params_of(gen)
            clips.append(k)
    return clips


def effect_params(rp):
    """Parameters of an effect RenderPass, looking one level into the DryWet wrapper."""
    d = dict(params_of(rp))
    inner = rp.find("RenderPass")
    if inner is not None:
        d.update(params_of(inner))
    return d


def effect_name(rp):
    inner = rp.find("RenderPass")
    return (inner.get("type") if inner is not None and inner.get("type") not in (None, "WireEffect")
            else rp.get("name")) or rp.get("name") or ""


def audit_comp(avc, preset=None, quiet_pass=True):
    name = os.path.basename(avc)
    R = Report(name)
    try:
        tree = ET.parse(avc)
    except ET.ParseError as e:
        R.add("FAIL", "xml parses", str(e))
        return R
    root = tree.getroot()
    R.ok("xml parses", "%.1f MB" % (os.path.getsize(avc) / 1048576.0))

    # ---- structure
    ids = [e.get("uniqueId") for e in root.iter() if e.get("uniqueId")]
    dup = [i for i, n in collections.Counter(ids).items() if n > 1]
    nd, nl, nc = (int(root.get(a, "0")) for a in ("numDecks", "numLayers", "numColumns"))
    decks = list(root.iter("Deck"))
    layers = [l for l in root.iter("Layer")]
    R.add("PASS" if len(decks) == nd else "FAIL", "deck count", "%d decks (header says %d)" % (len(decks), nd))
    R.add("PASS" if len(layers) == nl else "FAIL", "layer count", "%d layers (header says %d)" % (len(layers), nl))
    clips = read_clips(root)
    want = nd * nl * nc
    R.add("PASS" if len(clips) == want else "WARN", "cells filled", "%d clips of %d cells" % (len(clips), want))
    comp_params = params_of(root)
    lnames = [pvalue(params_of(l).get("Name")) for l in layers]
    instrument = lnames[:8] == LAYER_NAMES
    R.add(("FAIL" if instrument else "WARN") if dup else "PASS", "unique ids",
          ("%d duplicated, e.g. %s" % (len(dup), dup[:3])) if dup else "%d ids" % len(ids))
    nosrc = [c for c in clips if not c.src]
    if instrument:
        R.add("FAIL" if nosrc else "PASS", "every clip has a source",
              ("%d without, e.g. deck %d layer %d col %d" % (len(nosrc), nosrc[0].deck + 1, nosrc[0].layer, nosrc[0].col)) if nosrc else "")
    else:
        R.add("INFO", "empty cells", "%d of %d (a sparse grid is normal outside the instrument)" % (len(nosrc), len(clips)))
    R.add("INFO", "layers", " ".join(str(n) for n in lnames))
    dash = root.find("Params[@name='Dashboard']")
    dnames = [p.get("altName") for p in dash] if dash is not None else []
    if instrument:
        R.add("PASS" if dnames == DASH_NAMES else "WARN", "dashboard names",
              "standard" if dnames == DASH_NAMES else " ".join(map(str, dnames)))
        grain = next((l for l in layers if pvalue(params_of(l).get("Name")) == "GRAIN"), None)
        if grain is not None:
            bl = grain.find("VideoTrack/ChoosableMixer[@name='Blend']/RenderPass")
            if bl is not None and bl.get("name") != "Add":
                R.add("INFO", "GRAIN blend", "%s (newer packs use Add)" % bl.get("name"))
    speed = fnum(pvalue(comp_params.get("Speed")))
    R.add("PASS" if speed is not None and abs(speed - 1.0) < 1e-6 else "WARN", "composition speed at load", str(speed))

    # ---- safety
    strobe_bad, fills, redstrobe, heavy_bad, chain_bad, text_small = [], [], [], [], [], []
    for c in clips:
        where = "deck %d L%d C%d %s" % (c.deck + 1, c.layer, c.col, c.name[:18])
        sname = slug(c.src or "")
        strobing = False
        for (nm, pn), cap in K.PARAM_CAPS.items():
            if slug(nm) == sname and pn in c.src_params:
                el = c.src_params[pn]
                f = fft_of(el)
                v = max([x for x in (fnum(el.get("value")), f["hi"] if f else None) if x is not None] or [0.0])
                if v > cap + 1e-9:
                    strobe_bad.append("%s %s %s=%.2f>%.2f" % (where, c.src, pn, v, cap))
        if sname in [slug(s) for s in K.STROBE_SOURCES] and "Frequency" in c.src_params:
            fv = fnum(pvalue(c.src_params["Frequency"]), 0.0)
            strobing = fv > K.SLOW_LAMP_FREQUENCY
        efx = []
        heavy = 0
        for rp in c.effects:
            en = effect_name(rp)
            efx.append(en)
            ep = effect_params(rp)
            byp = ep.get("Bypassed")
            bypassed = byp is not None and pvalue(byp) == "1"
            if bypassed:
                continue
            for (nm, pn), cap in K.PARAM_CAPS.items():
                if slug(nm) == slug(en) and pn in ep:
                    el = ep[pn]
                    f = fft_of(el)
                    v = max([x for x in (fnum(el.get("value")), f["hi"] if f else None) if x is not None] or [0.0])
                    if v > cap + 1e-9:
                        strobe_bad.append("%s %s %s=%.2f>%.2f" % (where, en, pn, v, cap))
            if slug(en) in [slug(s) for s in K.STROBE_EFFECTS]:
                strobing = True
            if slug(en) in [slug(s) for s in K.HEAVY_EFFECTS]:
                heavy += 1
        if heavy > K.MAX_HEAVY_PER_CLIP:
            heavy_bad.append("%s %d heavy effects" % (where, heavy))
        if len(c.effects) > MAX_CLIP_EFFECTS:
            chain_bad.append("%s %d effects" % (where, len(c.effects)))
        if c.layer <= 4 and len([e for e in efx]) > K.MAX_EFFECTS_LOW_LAYERS + 2:
            chain_bad.append("%s long chain on a picture layer" % where)
        if strobing and (c.opacity or 0.0) > K.MAX_STROBE_OPACITY + 1e-9:
            fills.append("%s opacity %.2f" % (where, c.opacity))
        if strobing:
            col = c.src_params.get("Color")
            if col is not None:
                try:
                    argb = int(col.get("value", "0"))
                    rgb = "#%02x%02x%02x" % (argb & 255, (argb >> 8) & 255, (argb >> 16) & 255)   # stored as ABGR
                    if K.is_saturated_red(rgb):
                        redstrobe.append(where)
                except ValueError:
                    pass
        if sname in TEXT_SOURCES and "Size" in c.src_params:
            sz = fnum(pvalue(c.src_params["Size"]), 1.0)
            if sz < K.PARAM_FLOORS.get(("Text Block", "Size"), 0.5):
                text_small.append("%s size %.2f" % (where, sz))
    for label, bad in (("strobe / cloner / bloom caps", strobe_bad), ("no strobe fills the frame", fills),
                       ("no saturated-red strobe", redstrobe), ("one heavy effect per clip", heavy_bad),
                       ("effect chain length", chain_bad), ("text above the readable floor", text_small)):
        R.add(("FAIL" if instrument else "WARN") if bad else "PASS", label,
              ("%d, e.g. %s" % (len(bad), "; ".join(bad[:3]))) if bad else "")

    # ---- fft
    fft_n, bad_link, bad_gain, bad_fb, bad_band, bad_rng, nan_vals, hot_gain = 0, [], [], [], [], [], [], []
    for el in root.iter("ParamRange"):
        f = fft_of(el)
        if f is None:
            continue
        fft_n += 1
        if not (f["link"] or "").startswith("/audioengine/"):
            bad_link.append(el.get("name"))
        if f["gain"] is not None and not (0.0 <= f["gain"] <= 100.0):
            bad_gain.append("%s gain %s" % (el.get("name"), f["gain"]))
        elif f["gain"] is not None and f["gain"] > 20.0:
            hot_gain.append(el.get("name"))
        if f["fallback"] is not None and not (0.0 <= f["fallback"] <= 3000.0):
            bad_fb.append("%s fallback %s" % (el.get("name"), f["fallback"]))
        if f["band_lo"] is not None and not (0.0 <= f["band_lo"] < f["band_hi"] <= 1.0 + 1e-9):
            bad_band.append("%s band %s..%s" % (el.get("name"), f["band_lo"], f["band_hi"]))
        if f["lo"] is not None and f["hi"] is not None and f["lo"] > f["hi"]:
            bad_rng.append("%s range %s..%s" % (el.get("name"), f["lo"], f["hi"]))
    for el in root.iter("ParamRange"):
        v = el.get("value", "")
        if v.lower() in ("nan", "inf", "-inf"):
            nan_vals.append(el.get("name"))
    R.add("INFO", "fft bindings", "%d%s" % (fft_n, (", %d with gain above 20" % len(hot_gain)) if hot_gain else ""))
    for label, bad in (("fft link is the audio engine", bad_link), ("fft gain 0..100", bad_gain), ("fft fall-back 0..3000", bad_fb),
                       ("fft band inside 0..1", bad_band), ("fft floor below ceiling", bad_rng), ("no NaN values", nan_vals)):
        R.add("FAIL" if bad else "PASS", label, ("%d, e.g. %s" % (len(bad), "; ".join(map(str, bad[:3])))) if bad else "")
    bad_op = [c for c in clips if c.opacity is not None and not (0.0 <= c.opacity <= 1.0)]
    R.add("FAIL" if bad_op else "PASS", "clip opacity 0..1", "%d out of range" % len(bad_op) if bad_op else "")

    # ---- preset
    midi_name = pvalue(comp_params.get("MidiShortcutPreset")) or ""
    pre = preset
    if not pre and midi_name:
        for d in (os.path.dirname(avc), MIDI):
            p = os.path.join(d, midi_name + ".xml")
            if os.path.exists(p):
                pre = p
                break
    if midi_name and not pre:
        R.add("WARN", "selected preset exists", "%s is not installed or next to the composition" % midi_name)
    if pre:
        R.add("PASS", "selected preset exists", os.path.basename(pre))
        audit_preset(R, root, pre, nl, nc, nd, instrument)
    return R


def comp_effect_slugs(root):
    out = {}
    vt = root.find("VideoTrack")
    chain = vt.find("RenderPass") if vt is not None else None
    if chain is not None:
        for rp in chain.findall("RenderPass"):
            out[slug(rp.get("name") or "")] = rp
    return out


def audit_preset(R, root, pre, nl, nc, nd, instrument):
    try:
        ptree = ET.parse(pre)
    except ET.ParseError as e:
        R.add("FAIL", "preset parses", str(e))
        return
    sc = list(ptree.getroot().iter("Shortcut"))
    ids = [s.get("uniqueId") for s in sc]
    dup = len(ids) - len(set(ids))
    R.add("FAIL" if dup else "PASS", "preset ids unique", "%d shortcuts%s" % (len(sc), (", %d duplicate ids" % dup) if dup else ""))
    fx = comp_effect_slugs(root)
    layers = list(root.iter("Layer"))
    dead = []
    anchors = []
    for s in sc:
        pe = s.find("ShortcutPath[@name='InputPath']")
        path = pe.get("path") if pe is not None else ""
        m = re.match(r"/composition/layers/(\d+)(/.*)?$", path)
        if m:
            n = int(m.group(1))
            if not 1 <= n <= nl:
                dead.append(path)
                continue
            mm = re.match(r"/composition/layers/\d+/clips/(\d+)/", path)
            if mm and not 1 <= int(mm.group(1)) <= nc:
                dead.append(path)
            continue
        m = re.match(r"/composition/columns/(\d+)/connect$", path)
        if m:
            if not 1 <= int(m.group(1)) <= nc:
                dead.append(path)
            continue
        m = re.match(r"/composition/dashboard/link(\d+)$", path)
        if m:
            if not 1 <= int(m.group(1)) <= 8:
                dead.append(path)
            continue
        m = re.match(r"/composition/video/effects/([^/]+)/(.*)$", path)
        if m:
            if m.group(1) not in fx:
                dead.append(path)
            elif "behaviour/" in m.group(2):
                anchors.append((path, m.group(1), m.group(2)))
            continue
        if path in GLOBAL_PATHS or path.startswith("/composition/selectedclip/") or path.startswith("/composition/tempocontroller/"):
            continue
        dead.append(path)
    R.add("FAIL" if dead else "PASS", "every shortcut resolves", ("%d dead, e.g. %s" % (len(dead), "; ".join(sorted(set(dead))[:3]))) if dead else "")
    # FFT anchors: the effect parameter the knob trims must carry an FFT binding
    bad_anchor = []
    for path, es, rest in anchors:
        rp = fx[es]
        pm = re.match(r"effect/([^/]+)/behaviour/(gain|fallback)$", rest)
        if not pm:
            continue
        ep = effect_params(rp)
        el = next((v for k, v in ep.items() if slug(k) == pm.group(1)), None)
        if el is None or el.find("PhaseSourceFFT") is None:
            bad_anchor.append(path.replace("/composition/video/effects/", ""))
    R.add("FAIL" if bad_anchor else "PASS", "fft knobs trim a real binding", ("%d, e.g. %s" % (len(bad_anchor), "; ".join(bad_anchor[:3]))) if bad_anchor else "%d anchors" % len(anchors))
    # the standard's 13 rules
    res = PP.check(pre, {"decks": nd > 1})
    failed = [l for l, ok in res if not ok]
    R.add("PASS" if not failed else "WARN", "operator standard", "13/13" if not failed else "%d/%d, missing: %s" % (
        len(res) - len(failed), len(res), ", ".join(failed)))


def find_all():
    out = []
    for slug_ in ("signal-lost", "studio-one", "library-hand", "the-manual", "the-surface", "the-mixers", "dead-air", "dew-line"):
        g = [p for p in glob.glob(os.path.join(ROOT, "packs", slug_, "*.avc"))]
        if g:
            out.append(g[0])
    cd = PP._resolume_dir("Compositions")
    for f in ("EarthSearch_EP01_Live_Mix.avc", "Res React Lexicon.avc", "Res React Lexicon II.avc", "Res React Nisei.avc",
              "Res React Test Card.avc", "Res React Orbit.avc", "Res React Live Gen SPECIMEN.avc"):
        p = os.path.join(cd, f)
        if os.path.exists(p):
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("avc", nargs="?")
    ap.add_argument("--preset")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--json", help="write the findings as JSON to this path")
    a = ap.parse_args()
    files = find_all() if a.all else [a.avc]
    if not files or files == [None]:
        ap.error("give a composition or --all")
    reports = [audit_comp(f, a.preset if not a.all else None) for f in files]
    for r in reports:
        print(r.text(a.verbose))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump([dict(name=r.name, rows=r.rows, counts=dict(r.counts)) for r in reports], f, indent=1)
    print()
    print("%-52s %5s %5s %5s" % ("composition", "pass", "warn", "fail"))
    for r in reports:
        print("%-52s %5d %5d %5d" % (r.name[:52], r.counts["PASS"], r.counts["WARN"], r.counts["FAIL"]))
    sys.exit(1 if any(r.counts["FAIL"] for r in reports) else 0)


if __name__ == "__main__":
    main()
