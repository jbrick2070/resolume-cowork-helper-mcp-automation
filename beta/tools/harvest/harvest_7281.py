#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harvest_7281.py - ask the running Resolume Avenue 7.28.1 what it actually has.

Opens every generator source into a clip and adds every video effect to a
layer through the REST API, reads the live JSON (names, ranges, defaults,
choice options), saves the composition and parses the XML Resolume wrote
(type names, uniqueTypeIds, parameter element kinds). Nothing is guessed.

Avenue 7.28.1 CRASHED when asked to save a layer carrying all 116 effects at
once (2026-10-16, BugSplat, composition reloaded fresh). So the harvest runs
in BATCHES: each batch adds a few effects, reads them, saves to its own
.avc, then removes them again - and the composition is checked between
batches so a crash is attributed to the batch that caused it.

Outputs (in out/ beside this file):
    sources.json / sources.avc         live JSON + saved XML for all sources
    effects_NN.json / effects_NN.avc   one pair per batch
    avenue_7281_library.json           merged: XML shape + JSON ranges

Run with Avenue open on a SCRATCH composition. It never saves the open
composition to its own file.

Usage:
    python harvest_7281.py sources
    python harvest_7281.py effects [--batch 10] [--only "Name,Name"]
    python harvest_7281.py parse
"""
import glob
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "http://127.0.0.1:8080/api/v1"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# Device-backed and routing sources are not generators; skip them.
SKIP_SOURCES = {"Avenue - Composition", "Integrated Camera",
                "OBS Virtual Camera", "aa", "ndi"}
# Loaded last and alone: AI-model effects and a 529-parameter monster.
SLOW_EFFECTS = {"Depth Estimation", "Depth Blur", "Depth Displace",
                "Depth Field", "Depth Pixelation", "Depth Shift",
                "Background Removal", "Auto Mask", "Shape Shifter 3D",
                "JuiceEditor"}


def req(method, path, body=None, timeout=60):
    data = None
    headers = {}
    if body is not None:
        if isinstance(body, str):
            data = body.encode("utf-8")
            headers["Content-Type"] = "text/plain"
        else:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers=headers)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        raw = resp.read()
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError:
            return raw.decode("utf-8", "replace")


def get(path):
    return req("GET", path)


def alive():
    try:
        return get("/product") is not None
    except Exception:
        return False


def save_to(avc, timeout=240):
    url = "file:///" + urllib.parse.quote(avc.replace("\\", "/"))
    if os.path.exists(avc):
        os.remove(avc)
    try:
        req("POST", "/composition/save", url, timeout=timeout)
    except Exception as exc:
        print("  save call: %s" % exc)
    for _ in range(timeout):
        if os.path.exists(avc) and os.path.getsize(avc) > 2000:
            time.sleep(1)
            return True
        time.sleep(1)
    return False


def jdump(obj, name):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


# ---------------------------------------------------------------- sources --
def harvest_sources():
    sources = [s for s in get("/sources")["video"]
               if s["name"] not in SKIP_SOURCES]
    print("%d generator sources" % len(sources))
    req("POST", "/composition/grow-to",
        {"column_count": max(len(sources), 8), "layer_count": 3})
    time.sleep(0.5)
    src_json = {}
    for i, s in enumerate(sources, start=1):
        uri = "source:///video/" + urllib.parse.quote(s["name"])
        try:
            req("POST", "/composition/layers/1/clips/%d/open" % i, uri)
        except Exception as exc:
            print("  OPEN FAILED %-26s %s" % (s["name"], exc))
            continue
        time.sleep(0.25)
        clip = get("/composition/layers/1/clips/%d" % i)
        src_json[s["name"]] = {"idstring": s["idstring"], "column": i,
                               "presets": s.get("presets", []),
                               "description": s.get("description", ""),
                               "clip": clip}
        v = (clip.get("video") or {}).get("sourceparams") or {}
        print("  src %-26s %2d params" % (s["name"], len(v)))
    jdump(src_json, "sources.json")
    ok = save_to(os.path.join(OUT, "sources.avc"))
    print("  saved sources.avc: %s" % ok)
    for i in range(1, len(sources) + 1):
        try:
            req("POST", "/composition/layers/1/clips/%d/clear" % i)
        except Exception:
            pass
    print("  alive after cleanup: %s" % alive())


# ---------------------------------------------------------------- effects --
def harvest_effects(batch_size, only=None):
    effects = [e["name"] for e in get("/effects")["video"]]
    if only:
        effects = [e for e in effects if e in only]
    effects.sort(key=lambda n: (n in SLOW_EFFECTS, n))
    done = set()
    for f in glob.glob(os.path.join(OUT, "effects_*.json")):
        with open(f, encoding="utf-8") as fh:
            done.update(json.load(fh).keys())
    todo = [e for e in effects if e not in done]
    print("%d effects, %d already harvested, %d to do"
          % (len(effects), len(done), len(todo)))
    batches = []
    cur = []
    for e in todo:
        if e in SLOW_EFFECTS:
            if cur:
                batches.append(cur)
                cur = []
            batches.append([e])
        else:
            cur.append(e)
            if len(cur) >= batch_size:
                batches.append(cur)
                cur = []
    if cur:
        batches.append(cur)
    existing = len(glob.glob(os.path.join(OUT, "effects_*.avc")))
    for bi, batch in enumerate(batches, start=existing + 1):
        if not alive():
            print("AVENUE NOT RESPONDING before batch %d (%s) - stopping"
                  % (bi, batch))
            return
        req("POST", "/composition/grow-to", {"layer_count": 3})
        before = len(get("/composition/layers/2")["video"]["effects"])
        print("batch %02d: %s" % (bi, ", ".join(batch)))
        for name in batch:
            uri = "effect:///video/" + urllib.parse.quote(name)
            try:
                req("POST", "/composition/layers/2/effects/video/add", uri,
                    timeout=120)
            except Exception as exc:
                print("  ADD FAILED %-26s %s" % (name, exc))
            time.sleep(0.2)
        time.sleep(0.8)
        layer2 = get("/composition/layers/2")
        live = layer2["video"]["effects"][before:]
        fx_json = {}
        for fx in live:
            nm = fx.get("display_name") or fx.get("name")
            fx_json[nm] = fx
            print("  fx  %-26s %3d params" % (nm, len(fx.get("params") or {})))
        avc = os.path.join(OUT, "effects_%02d.avc" % bi)
        ok = save_to(avc)
        print("  saved %s: %s  alive: %s" % (os.path.basename(avc), ok,
                                            alive()))
        if not alive():
            print("  AVENUE DIED saving batch %d: %s" % (bi, batch))
            jdump({"crashed_batch": batch}, "effects_%02d.CRASH.json" % bi)
            return
        if ok:
            jdump(fx_json, "effects_%02d.json" % bi)
        total = len(get("/composition/layers/2")["video"]["effects"])
        for off in range(total, before, -1):
            try:
                req("DELETE", "/composition/layers/2/effects/video/%d" % off)
            except Exception as exc:
                print("  delete %d: %s" % (off, exc))
        time.sleep(0.3)
    print("effects done; alive: %s" % alive())


# ------------------------------------------------------------------ parse --
def param_shape(el):
    d = {"tag": el.tag, "name": el.get("name"), "T": el.get("T"),
         "default": el.get("default"), "value": el.get("value")}
    if el.get("altName"):
        d["altName"] = el.get("altName")
    vr = el.find("ValueRange")
    if vr is not None:
        d["xml_min"], d["xml_max"] = vr.get("min"), vr.get("max")
    if el.tag == "ParamText":
        d["lines"] = True
    if el.tag == "ParamChoice":
        d["storeChoices"] = el.get("storeChoices")
    return d


def merge_json(shape, jparams):
    jp = jparams.get(shape["name"]) if jparams else None
    if not jp:
        return shape
    for k in ("valuetype", "min", "max", "in", "out", "options", "index"):
        if k in jp:
            shape[k] = jp[k]
    if "value" in jp:
        shape["live_value"] = jp["value"]
    return shape


def parse_all():
    lib = {"sources": {}, "effects": {}}
    sj_path = os.path.join(OUT, "sources.json")
    if os.path.exists(sj_path):
        with open(sj_path, encoding="utf-8") as f:
            src_json = json.load(f)
        root = ET.parse(os.path.join(OUT, "sources.avc")).getroot()
        lib["product"] = root.find("versionInfo").attrib
        by_col = {v["column"]: k for k, v in src_json.items()}
        for clip in root.find("Deck").findall("Clip"):
            if clip.get("layerIndex") != "0":
                continue
            col = int(clip.get("columnIndex")) + 1
            name = by_col.get(col, "col%d" % col)
            vs = clip.find("./VideoTrack/PrimarySource/VideoSource")
            if vs is None:
                continue
            rp = vs.find("RenderPass")
            entry = {"source_type": vs.get("type"),
                     "idstring": src_json.get(name, {}).get("idstring"),
                     "presets": src_json.get(name, {}).get("presets", []),
                     "description": src_json.get(name, {}).get("description")}
            if rp is None:
                entry["xml"] = None
                entry["raw"] = ET.tostring(vs, encoding="unicode")[:2000]
            else:
                jparams = ((src_json.get(name, {}).get("clip") or {})
                           .get("video") or {}).get("sourceparams") or {}
                entry.update({
                    "xml_name": rp.get("name"), "xml_type": rp.get("type"),
                    "uniqueTypeId": rp.get("uniqueTypeId"),
                    "params_written": [merge_json(param_shape(p), jparams)
                                       for p in rp.findall("./Params/*")],
                    "params_live": jparams})
            lib["sources"][name] = entry
    for avc in sorted(glob.glob(os.path.join(OUT, "effects_*.avc"))):
        jpath = avc[:-4] + ".json"
        if not os.path.exists(jpath):
            continue
        with open(jpath, encoding="utf-8") as f:
            fx_json = json.load(f)
        root = ET.parse(avc).getroot()
        layers = root.findall("Layer")
        chain = layers[1].find(
            "./VideoTrack/RenderPass[@name='RenderPassChain']")
        # Mask is written as type="Mask", not DryWetEffect, so take every
        # pass in the chain except the Transform.
        wraps = [w for w in chain.findall("RenderPass")
                 if w.get("type") != "TransformEffect"]
        # Resolume writes the XML name CamelCased ("Bright.Contrast" ->
        # BrightnessContrast), so match by ORDER: this batch's effects are
        # the last N wrappers in the chain, in the order they were added.
        names = list(fx_json.keys())
        wraps = wraps[-len(names):]
        assert len(wraps) == len(names), (avc, len(wraps), len(names))
        for disp, wrap in zip(names, wraps):
            inner = wrap.find("RenderPass")
            jparams = fx_json[disp].get("params") or {}
            lib["effects"][disp] = {
                "display_name": disp,
                "wrapper_type": wrap.get("type"),
                "xml_name": inner.get("name") if inner is not None else None,
                "xml_type": inner.get("type") if inner is not None else None,
                "uniqueTypeId": wrap.get("uniqueTypeId"),
                "inner_uniqueTypeId": (inner.get("uniqueTypeId")
                                       if inner is not None else None),
                "params_written": [merge_json(param_shape(p), jparams)
                                   for p in (inner.findall("./Params/*")
                                             if inner is not None else [])],
                "params_live": jparams,
                "wrapper_params": [param_shape(p)
                                   for p in wrap.findall("./Params/*")],
                "mixer": [m.get("name")
                          for m in wrap.findall("ChoosableMixer")],
                "batch_file": os.path.basename(avc)}
    jdump(lib, "avenue_7281_library.json")
    jdump(compact(lib), "dictionary_compact.json")
    print("library: %d sources, %d effects" % (len(lib["sources"]),
                                               len(lib["effects"])))
    return lib


def compact(lib):
    """Small per-item parameter dictionary for designers and validators."""
    def rows(jparams):
        out = []
        for pn, p in (jparams or {}).items():
            vt = p.get("valuetype")
            if vt == "ParamRange":
                out.append([pn, "range", p.get("min"), p.get("max"),
                            p.get("value")])
            elif vt == "ParamChoice":
                out.append([pn, "choice", p.get("options"), p.get("value")])
            elif vt == "ParamBoolean":
                out.append([pn, "bool", p.get("value")])
            elif vt == "ParamColor":
                out.append([pn, "color", p.get("value")])
            elif vt == "ParamText":
                out.append([pn, "text", p.get("value")])
            else:
                out.append([pn, vt, p.get("value")])
        return out
    d = {"sources": {}, "effects": {}}
    for n, s in lib["sources"].items():
        if "params_live" in s:
            d["sources"][n] = {"xml_name": s["xml_name"],
                               "presets": [p["name"] for p in s.get("presets", [])],
                               "params": rows(s["params_live"])}
    for n, e in lib["effects"].items():
        d["effects"][n] = {"xml_name": e["xml_name"],
                           "params": rows(e["params_live"])}
    return d



def main():
    os.makedirs(OUT, exist_ok=True)
    if not alive():
        raise SystemExit("REST API on 8080 not answering")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "parse"
    if cmd == "sources":
        harvest_sources()
    elif cmd == "effects":
        bs = 10
        only = None
        if "--batch" in sys.argv:
            bs = int(sys.argv[sys.argv.index("--batch") + 1])
        if "--only" in sys.argv:
            only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
        harvest_effects(bs, only)
    elif cmd == "parse":
        parse_all()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
