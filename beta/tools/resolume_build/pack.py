#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pack.py - turn a creative bible + five deck designs into a complete pack:
the .avc, the APC40 mkII preset, the control map, the deck sheets and a
build report. Every value passes through the rig-harvested library; bad
values from a designer are repaired (clamped / dropped / substituted) and
every repair is written to the report rather than silently accepted.

    from resolume_build.pack import build_pack
    build_pack(bible, decks, rack, out_dir, slug, preset_id, id_base)
"""
import json
import os
import re

from . import avc as AVC
from . import apc as APC
from . import instrument as INST
from . import library as LIB

LAYER_BLENDS = {1: "Add", 2: "Add", 3: "Screen", 4: "Add", 5: "Alpha",
                6: "Overlay", 7: "Overlay", 8: "Add"}
LAYER_COLOR_IDS = {1: 4, 2: 3, 3: 1, 4: 2, 5: 5, 6: 4, 7: 3, 8: 1}
TEXT_SOURCES = {"Text Animator", "Text Block"}
MAX_LINE = 22
MAX_NAME = 18

# A safe stand-in per layer role when a designer names a source that does
# not exist. Logged, never silent.
FALLBACK_SOURCE = {1: ("Abstract Field", {"Octaves": 3.0, "Amplitude": 0.5,
                                          "Density": 0.4}),
                   2: ("Rings", {"Style": "Stroke", "Num Rings": 12.0,
                                 "Line Width": 0.04}),
                   3: ("Metaballs", {"Grid": 4.0, "Size": 0.3,
                                     "BG Color": "#00000000"}),
                   4: ("Gradient", {"Type": "Radial", "Color 1": "#00000000",
                                    "Color 2": "#ffffffff"}),
                   5: ("Text Animator", {"Text": "SIGNAL", "Size": 1.2,
                                         "Alignment": "Center"}),
                   6: ("Solid Color", {"Color": "#ffffffff"}),
                   7: ("Static", {"Mode": "Grayscale"}),
                   8: ("Sine Wave", {"Waves": 2.0, "Amplitude": 0.1})}


class Report(object):
    def __init__(self):
        self.lines = []
        self.repairs = 0

    def note(self, msg):
        self.lines.append(msg)

    def repair(self, msg):
        self.repairs += 1
        self.lines.append("REPAIR " + msg)

    def text(self):
        return "\n".join(self.lines) + "\n"


def _clean_text(s, rep, where, multiline=False):
    s = str(s).replace("\r", "")
    s = "".join(ch for ch in s if ord(ch) < 0x250 and (ch == "\n" or ord(ch) >= 32))
    lines = s.split("\n") if multiline else [s.replace("\n", " ")]
    out = []
    for ln in lines:
        if len(ln) > MAX_LINE:
            rep.repair("%s: text line %r cut to %d chars" % (where, ln,
                                                             MAX_LINE))
            ln = ln[:MAX_LINE].rstrip()
        out.append(ln)
    return "\n".join(out)


def _coerce_params(item, params, rep, where):
    """Validate against the library; clamp / drop / log instead of failing."""
    fixed = {}
    for k, v in (params or {}).items():
        try:
            spec = item.param(k)
        except KeyError:
            rep.repair("%s: %s has no parameter %r - dropped" % (
                where, item.display_name, k))
            continue
        if spec.kind == "text":
            v = _clean_text(v, rep, where, multiline=(
                item.display_name == "Text Block"))
        try:
            fixed[spec.name] = spec.coerce(v)
            continue
        except Exception as exc:
            pass
        # repair attempts
        if spec.kind == "range":
            try:
                fv = float(v)
                cv = min(max(fv, spec.min), spec.max)
                rep.repair("%s: %s/%s=%r clamped to %s" % (
                    where, item.display_name, spec.name, v, cv))
                fixed[spec.name] = cv
            except Exception:
                rep.repair("%s: %s/%s=%r not a number - dropped" % (
                    where, item.display_name, spec.name, v))
        elif spec.kind == "choice":
            opts = [o.lower() for o in spec.options]
            sv = str(v).lower()
            hit = [i for i, o in enumerate(opts) if sv in o or o in sv]
            if hit:
                rep.repair("%s: %s/%s=%r -> %r" % (
                    where, item.display_name, spec.name, v,
                    spec.options[hit[0]]))
                fixed[spec.name] = hit[0]
            else:
                rep.repair("%s: %s/%s=%r not an option - dropped" % (
                    where, item.display_name, spec.name, v))
        elif spec.kind == "color":
            rep.repair("%s: %s/%s=%r bad colour - dropped" % (
                where, item.display_name, spec.name, v))
        else:
            rep.repair("%s: %s/%s=%r dropped (%s)" % (
                where, item.display_name, spec.name, v, exc))
    return fixed


def _coerce_fft(item, fft, params, rep, where, bands):
    out = {}
    for k, spec_in in (fft or {}).items():
        try:
            spec = item.param(k)
        except KeyError:
            rep.repair("%s: fft on unknown %s/%s - dropped" % (
                where, item.display_name, k))
            continue
        if spec.kind != "range":
            rep.repair("%s: fft on non-range %s/%s - dropped" % (
                where, item.display_name, spec.name))
            continue
        if isinstance(spec_in, dict):
            band = str(spec_in.get("band", "mid")).lower()
            gain = float(spec_in.get("gain", 9.0))
            rel = float(spec_in.get("release", 500))
            floor = spec_in.get("floor", spec.min)
            ceil = spec_in.get("ceiling", spec.max)
        else:
            band, gain, rel, floor, ceil = spec_in
        if band not in bands:
            rep.repair("%s: fft band %r -> mid" % (where, band))
            band = "mid"
        gain = min(max(gain, 0.0), 24.0)
        rel = min(max(rel, 100.0), 2000.0)
        try:
            floor = float(floor)
            ceil = float(ceil)
        except Exception:
            rep.repair("%s: fft floor/ceiling not numbers - dropped" % where)
            continue
        lo, hi = spec.min, spec.max
        cf = min(max(floor, lo), hi)
        cc = min(max(ceil, lo), hi)
        if (cf, cc) != (floor, ceil):
            rep.repair("%s: fft %s range %s..%s clamped to %s..%s" % (
                where, spec.name, floor, ceil, cf, cc))
        if abs(cc - cf) < 1e-9:
            rep.repair("%s: fft %s has zero travel - dropped" % (where,
                                                                 spec.name))
            continue
        out[spec.name] = (band, gain, rel, cf, cc)
    return out


def safe_name(name):
    """Windows-safe file name (a colon makes an NTFS alternate stream)."""
    return re.sub(r'[<>:"/\\|?*]', " -", name).strip()


def build_pack(bible, decks, rack, out_dir, slug, preset_id, id_base,
               macros=None, bands=None, layer_blends=None, row_colors=None,
               scene_colors=None, notes=""):
    """Build everything. Returns (avc_path, preset_path, report)."""
    lib = LIB.Library()
    rep = Report()
    blends = dict(LAYER_BLENDS)
    blends.update(layer_blends or {})
    comp_name = bible["comp_name"]
    preset_name = "APC 40 MK II - %s" % bible["pack_name"]
    comp = AVC.Composition(comp_name, midi_preset=preset_name,
                           description=bible.get("tagline", ""),
                           id_base=id_base, bands=bands, lib=lib,
                           notes=notes)
    dashboard = [b["label"] for b in rack["banks"]] + [m["label"]
                                                        for m in rack["macros"]]
    assert len(dashboard) == 8, dashboard
    comp.dashboard = dashboard
    for i in range(5, 9):
        comp.dashboard_values[i] = 0.0

    # ---- composition rack ------------------------------------------------
    bank_seats = []
    for bi, bank in enumerate(rack["banks"], start=1):
        seats = []
        for e in bank["effects"]:
            item = lib.effect(e["effect"])
            where = "rack/%s/%s" % (bank["label"], e["label"])
            params = _coerce_params(item, e.get("params"), rep, where)
            fft = _coerce_fft(item, e.get("fft"), params, rep, where,
                              comp.bands)
            comp.add_effect(e["effect"], params, link=bi,
                            wet_max=e.get("wet_max"), fft=fft, bypassed=True)
            seats.append((e["label"], item.xml_name))
        bank_seats.append(seats)
    for mi, m in enumerate(rack["macros"], start=5):
        item = lib.effect(m["effect"])
        where = "macro/%s" % m["label"]
        params = _coerce_params(item, m.get("params"), rep, where)
        fft = _coerce_fft(item, m.get("fft"), params, rep, where, comp.bands)
        comp.add_effect(m["effect"], params, link=mi, wet_max=m.get("wet_max"),
                        fft=fft, bypassed=False)

    # ---- layers ------------------------------------------------------------
    names = INST.LAYER_ROLES
    layers = []
    for n in range(1, 9):
        xf = 1 if n in INST.XFADE_A else (2 if n in INST.XFADE_B else 0)
        layers.append(comp.add_layer(
            names[n - 1], blend=blends[n], opacity=1.0, crossfader=xf,
            ignore_column=(n == INST.SCOPE_LAYER), master=1.0,
            color_id=LAYER_COLOR_IDS[n]))

    # ---- decks ---------------------------------------------------------------
    sheets = []
    n_clips = 0
    for di, (dbible, design) in enumerate(zip(bible["decks"], decks)):
        cols = [str(c)[:14] for c in dbible["columns"]]
        deck = comp.add_deck(dbible["name"], cols,
                             column_colors=[(i % 5) + 1 for i in range(8)])
        grid = {}
        for c in (design or {}).get("clips", []):
            try:
                ln, col = int(c["layer"]), int(c["column"])
            except Exception:
                rep.repair("deck %s: clip without layer/column dropped"
                           % dbible["name"])
                continue
            if not (1 <= ln <= 8 and 1 <= col <= 8):
                rep.repair("deck %s: clip %r at L%s C%s out of grid" % (
                    dbible["name"], c.get("name"), ln, col))
                continue
            if (ln, col) in grid:
                rep.repair("deck %s: duplicate clip at L%d C%d (%r kept, %r "
                           "dropped)" % (dbible["name"], ln, col,
                                         grid[(ln, col)]["name"], c.get("name")))
                continue
            grid[(ln, col)] = c
        for ln in range(1, 9):
            for col in range(1, 9):
                where = "%s L%d C%d" % (dbible["name"], ln, col)
                c = grid.get((ln, col))
                if c is not None and c.get("file"):
                    # A video file clip: no generator to validate, only the
                    # file itself. Missing files are a repair, not a crash.
                    path = os.path.abspath(c["file"])
                    if not os.path.exists(path):
                        rep.repair("%s: file %r missing - filled with %s" % (
                            where, c["file"], FALLBACK_SOURCE[ln][0]))
                        c = None
                    else:
                        name = str(c.get("name") or os.path.basename(path))[:MAX_NAME]
                        if c.get("audio"):
                            # Avenue renames a clip that has an audio track to its
                            # file name (seen on 129 clips, 2026-10-23), so say so.
                            name = os.path.splitext(os.path.basename(path))[0]
                        opacity = min(max(float(c.get("opacity", 1.0)), 0.0), 1.0)
                        size = tuple(c.get("size") or (comp.width, comp.height))
                        deck.add_clip(layers[ln - 1], col - 1, name, "Blank", {},
                                      opacity=opacity, file=path, size=size,
                                      audio=bool(c.get("audio")),
                                      seconds=max(0.1, float(c.get("seconds", 5))))
                        n_clips += 1
                        sheets.append((di, dbible["name"], ln, names[ln - 1], col,
                                       cols[col - 1], name, "Video: " + os.path.basename(path),
                                       "", "", c.get("why", "")))
                        continue
                if c is None:
                    src, params = FALLBACK_SOURCE[ln]
                    rep.repair("%s: missing - filled with %s" % (where, src))
                    c = {"name": "%s %d" % (names[ln - 1].title(), col),
                         "source": src, "params": dict(params), "fft": {},
                         "effects": []}
                try:
                    item = lib.source(c.get("source", ""))
                except KeyError:
                    src, params = FALLBACK_SOURCE[ln]
                    rep.repair("%s: unknown source %r -> %s" % (
                        where, c.get("source"), src))
                    item = lib.source(src)
                    c = dict(c, params=dict(params), fft={}, effects=[])
                params = _coerce_params(item, c.get("params"), rep, where)
                if item.display_name in TEXT_SOURCES and "Text" not in params:
                    corpus = dbible.get("text_corpus") or ["SIGNAL"]
                    params["Text"] = _clean_text(corpus[(col - 1) % len(corpus)],
                                                 rep, where)
                    rep.repair("%s: text clip had no Text - used corpus" % where)
                fft = _coerce_fft(item, c.get("fft"), params, rep, where,
                                  comp.bands)
                effects = []
                for e in (c.get("effects") or [])[:2]:
                    try:
                        fitem = lib.effect(e.get("effect", ""))
                    except KeyError:
                        rep.repair("%s: clip effect %r unknown/banned - dropped"
                                   % (where, e.get("effect")))
                        continue
                    fparams = _coerce_params(fitem, e.get("params"), rep,
                                             where + "/" + fitem.display_name)
                    effects.append(comp.make_effect(fitem.display_name, fparams,
                                                    None, None, None, False))
                name = str(c.get("name") or item.display_name)[:MAX_NAME]
                try:
                    opacity = float(c.get("opacity", 1.0))
                except Exception:
                    opacity = 1.0
                opacity = min(max(opacity, 0.0), 1.0)
                deck.add_clip(layers[ln - 1], col - 1, name, item.display_name,
                              params, fft=fft, opacity=opacity,
                              effects=effects)
                n_clips += 1
                sheets.append((di, dbible["name"], ln, names[ln - 1], col,
                               cols[col - 1], name, item.display_name,
                               ", ".join("%s>%s" % (k, v[0]) for k, v in fft.items()),
                               ", ".join(e.item.display_name for e in effects),
                               c.get("why", "")))

    xml = comp.build()
    os.makedirs(out_dir, exist_ok=True)
    avc_path = os.path.join(out_dir, safe_name(comp_name) + ".avc")
    with open(avc_path, "w", encoding="utf-8", newline="") as f:
        f.write(xml)
    counts = comp.counts(xml)
    rep.note("composition: %s" % counts)

    # ---- preset ---------------------------------------------------------
    fft_anchor = rack["fft_anchor"]
    spec = INST.InstrumentSpec(
        layer_names=names, row_colors=row_colors or
        ["indigo", "cyan", "green", "amber", "white"],
        banks=bank_seats, dashboard=dashboard, fft_anchor=fft_anchor,
        scope_anchor="/composition/layers/8/clips/1/video/source/amplitude",
        preset_name=preset_name, preset_id=preset_id, id_base=id_base + 900000,
        scene_colors=scene_colors or ["white"] * 5)
    deck1_names = {(s[2], s[4]): s[6] for s in sheets if s[0] == 0 and s[2] <= 5}
    P = INST.build_apc_map(spec, deck1_names)
    pxml, preport = P.build(forbidden=INST.FORBIDDEN_PATHS)
    preset_path = os.path.join(out_dir, preset_name + ".xml")
    with open(preset_path, "w", encoding="utf-8", newline="") as f:
        f.write(pxml)
    rep.note("preset: %d shortcuts on %d physical controls; unmapped: %s; "
             "multi: %s" % (preport["shortcuts"], preport["physical"],
                            preport["missing"] or "none", preport["multi"]))

    # ---- docs -----------------------------------------------------------
    docs = os.path.join(out_dir, "docs")
    os.makedirs(docs, exist_ok=True)
    with open(os.path.join(docs, "CONTROL_MAP.md"), "w", encoding="utf-8") as f:
        f.write(INST.control_map_markdown(P, bible["pack_name"]))
    with open(os.path.join(docs, "DECKS.md"), "w", encoding="utf-8") as f:
        f.write(deck_sheets_markdown(bible, sheets))
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"bible": bible, "rack": rack, "counts": counts,
                   "preset": preport["shortcuts"], "repairs": rep.repairs,
                   "sheets": sheets}, f, indent=1)
    rep.note("repairs: %d" % rep.repairs)
    with open(os.path.join(out_dir, "BUILD_REPORT.txt"), "w",
              encoding="utf-8") as f:
        f.write(rep.text())
    return avc_path, preset_path, rep, counts


def deck_sheets_markdown(bible, sheets):
    out = ["# %s - deck sheets" % bible["pack_name"], "",
           bible.get("tagline", ""), ""]
    for di, d in enumerate(bible["decks"]):
        out += ["", "## Deck %d - %s" % (di + 1, d["name"]), "",
                d.get("world", ""), "",
                "Palette: " + ", ".join("%s %s" % (p["role"], p["hex"])
                                        for p in d.get("palette", [])), "",
                "| layer | " + " | ".join("%d %s" % (i + 1, c) for i, c in
                                          enumerate(d["columns"])) + " |",
                "|---|" + "---|" * 8]
        for ln in range(8, 0, -1):
            row = [s for s in sheets if s[0] == di and s[2] == ln]
            cells = []
            for col in range(1, 9):
                hit = [s for s in row if s[4] == col]
                if hit:
                    s = hit[0]
                    cells.append("%s<br><small>%s%s</small>" % (
                        s[6], s[7], (" / " + s[9]) if s[9] else ""))
                else:
                    cells.append("")
            out.append("| %d %s | %s |" % (ln, INST.LAYER_ROLES[ln - 1],
                                           " | ".join(cells)))
        out += ["", "Text corpus: " + " · ".join(d.get("text_corpus", [])), ""]
        for m in d.get("moments", []):
            out.append("- " + m)
    return "\n".join(out) + "\n"
