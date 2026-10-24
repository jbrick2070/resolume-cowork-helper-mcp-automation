#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preset_patch.py - bring an existing APC40 mkII preset up to the OPERATOR STANDARD without
rebuilding (or touching) its composition.

Why: the instrument packs are built from one control table (instrument.py), so they agree by
construction. Older presets (Dead Air, Dew Line, EarthSearch, the React family) were made
by earlier generators and disagree on a handful of controls the performer's hands expect to
be the same everywhere. This tool edits the preset XML in place of a rebuild, changes only the
controls named below, and writes a plain-English change log.

THE STANDARD (what every non-twin preset agrees on)
  TEMPO knob  CC13   FFT INPUT GAIN, global, relative (same knob in every composition)
  CUE LEVEL   CC47   relative: FX master over the four bank links, or TIME (composition speed)
                     in presets that have no composition dashboard
  UP / DOWN   n94/95 next / previous scene (column)
  RIGHT / LEFT n96/97 next / previous deck (when the composition has more than one deck)
  PLAY n91           open the show (scene 1)
  STOP n92           stop (eject)
  RECORD n93         blackout toggle        FOOTSWITCH CC64  momentary blackout
  STOP ALL n81       eject everything

Profiles
  instrument   presets made by the instrument builder at an earlier date (Dead Air, Dew Line,
               EarthSearch): swap UP/DOWN if they still have the old direction, TEMPO -> FFT gain,
               METRONOME -> FFT gain home, TAP -> TIME home, CUE LEVEL absolute -> relative.
  legacy       the React family (Lexicon, Nisei, TestCard, Orbit, React, SPECIMEN): fill the free
               standard controls, fix reversed arrows, replace the broken absolute scrub on CUE LEVEL
               with TIME, and keep everything else exactly as it was.

Nothing is written over the input: output goes to --out, plus <name>.changes.txt beside it.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import apc as A                       # noqa: E402
from resolume_build.instrument import FFT_GAIN            # noqa: E402

CC, NOTE = A.CC_MARKER, A.NOTE_MARKER
SPEED = "/composition/speed"
OFFON = {"Off": 0, "On": 127}
ONE = {"Off": 0, "On": 1}

# the standard controls, as keyword arguments for Preset.add
STD = {
    "fft_gain": dict(control="FFT GAIN (global input gain)", kind="cc", path=FFT_GAIN, shape="relative",
                     cc=13, group="FFT gain (global)", num_steps=128),
    "fft_home": dict(control="FFT GAIN home (0.5)", kind="note", path=FFT_GAIN, shape="ccrange", note=90,
                     group="FFT gain (global)", value_range=("0.5", "0.5"), init="0.5", led=OFFON),
    "time_home": dict(control="TIME home (1x)", kind="note", path=SPEED, shape="ccrange", note=99,
                      group="TIME home", value_range=("0.1", "0.1"), init="0.1", led=OFFON),
    "time_cue": dict(control="TIME (composition speed)", kind="cc", path=SPEED, shape="relative", cc=47,
                     group="Live FFT", num_steps=256),
    "next_scene": dict(control="NEXT SCENE", kind="note", path="/composition/connectnextcolumn",
                       shape="action1", note=94, group="Scenes", led=OFFON),
    "prev_scene": dict(control="PREVIOUS SCENE", kind="note", path="/composition/connectprevcolumn",
                       shape="action1", note=95, group="Scenes", led=OFFON),
    "next_deck": dict(control="NEXT DECK", kind="note", path="/composition/selectnextdeck",
                      shape="action11", note=96, group="Decks", led=ONE),
    "prev_deck": dict(control="PREVIOUS DECK", kind="note", path="/composition/selectprevdeck",
                      shape="action11", note=97, group="Decks", led=ONE),
    "open_show": dict(control="OPEN THE SHOW (scene 1)", kind="note", path="/composition/columns/1/connect",
                      shape="action11", note=91, group="Safety - open", led={"Off": 1, "On": 127}),
    "stop": dict(control="STOP (eject everything)", kind="note", path="/composition/disconnectall",
                 shape="action1", note=92, group="Safety - stop", led=OFFON),
    "blackout": dict(control="BLACKOUT", kind="note", path="/composition/bypassed", shape="boolparam",
                     note=93, group="Safety - blackout", led=OFFON),
    "footswitch": dict(control="Footswitch momentary BLACKOUT", kind="cc", path="/composition/bypassed",
                       shape="ccrange", cc=64, value_range=("0", "1"), init="0", group="Safety - blackout"),
    "resync": dict(control="Tempo resync", kind="note", path="/composition/tempocontroller/resync",
                   shape="action1", note=90, group="Tempo", led=OFFON),
}


def fxm(link):
    return dict(control="FX MASTER nudge (link %d)" % link, kind="cc", path="/composition/dashboard/link%d" % link,
                shape="relative", cc=47, group="FX master", num_steps=64)


def ident(kind, num, ch=1):
    return (kind, ch, num)


class Doc(object):
    """The preset text, its shortcuts, and the edits made to it."""

    def __init__(self, text):
        self.text = text
        self.log = []
        self.remove_idx = set()
        self.adds = []
        self.sc = []
        for m in re.finditer(r"[ \t]*<Shortcut\b.*?</Shortcut>[ \t]*\r?\n?", text, re.S):
            b = m.group(0)
            km = re.search(r'RawInputMessage key="(\d+)"', b)
            pm = re.search(r'name="InputPath" path="([^"]*)"', b)
            if not (km and pm):
                continue
            key = int(km.group(1))
            if key & CC:
                k = key - CC
                kind, num, ch = "cc", (k >> 8) & 0xFF, (k & 0x0F) + 1
            elif key & NOTE:
                k = key - NOTE
                kind, num, ch = "note", (k >> 8) & 0xFF, (k & 0x0F) + 1
            else:
                continue
            bm = re.search(r'behaviour="(\d+)"', b)
            self.sc.append(dict(span=m.span(), block=b, id=(kind, ch, num), path=pm.group(1),
                                behaviour=int(bm.group(1)) if bm else 0))
        self.max_uid = max([int(x) for x in re.findall(r'uniqueId="(\d+)"', text)] or [0])

    def at(self, kind, num, ch=1):
        return [s for i, s in enumerate(self.sc) if s["id"] == (kind, ch, num) and i not in self.remove_idx]

    def free(self, kind, num, ch=1):
        return not self.at(kind, num, ch)

    def drop(self, items, why):
        for s in items:
            self.remove_idx.add(self.sc.index(s))
        if items:
            self.log.append("removed  %-34s %s  (%s)" % (self.name_of(items[0]["id"]), ", ".join(
                sorted({s["path"].replace("/composition/", "") for s in items}))[:70], why))

    def add(self, spec, why):
        self.adds.append(dict(spec))
        s = dict(spec)
        self.log.append("added    %-34s %s  (%s)" % (self.name_of(ident(s["kind"], s.get("note", s.get("cc")))),
                                                    s["path"].replace("/composition/", ""), why))

    @staticmethod
    def name_of(i):
        kind, ch, num = i
        return A.PHYSICAL_NAMES.get((kind, ch, num), "%s ch%d %d" % (kind, ch, num))

    def result(self):
        out, last = [], 0
        for i, s in enumerate(self.sc):
            if i in self.remove_idx:
                out.append(self.text[last:s["span"][0]])
                last = s["span"][1]
        out.append(self.text[last:])
        text = "".join(out)
        if self.adds:
            P = A.Preset("patch", "0", id_base=self.max_uid)
            xml = []
            for spec in self.adds:
                spec = dict(spec)
                control, kind, path, shape = spec.pop("control"), spec.pop("kind"), spec.pop("path"), spec.pop("shape")
                sc = P.add(control, kind, path, shape, **spec)
                xml.append(P.shortcut_xml(sc))
            block = "\t\t<!-- OPERATOR STANDARD (preset_patch.py) -->\n" + "\n".join(xml) + "\n"
            end = text.rfind("</ShortcutManager>")
            if end < 0:
                raise SystemExit("no </ShortcutManager> in the preset")
            text = text[:end].rstrip("\t ") + block + "\t" + text[end:]
        ET.fromstring(text.encode("utf-8"))
        return text


def tempo_to_fft(d):
    t = d.at("cc", 13)
    old = [s for s in t if s["path"].endswith("tempocontroller/tempo")]
    if t and len(old) != len(t):
        d.log.append("skipped  TEMPO knob CC13 is mapped to something else; left alone")
        return
    if old:
        d.drop(old, "BPM is not used; the knob becomes the global FFT gain")
    d.add(STD["fft_gain"], "same knob on every composition")


def cue_relative(d, mode):
    """mode 'fxmaster': keep the four dashboard links but relative; 'time': composition speed."""
    c = d.at("cc", 47)
    if mode == "time":
        scrub = [s for s in c if "transport/position" in s["path"]]
        if len(scrub) != len(c):
            d.log.append("skipped  CUE LEVEL is mapped to something else; left alone")
            return
        d.drop(scrub, "an absolute scrub on a relative encoder jumps; speed is more useful")
        d.add(STD["time_cue"], "composition speed, relative: 1x is the start point")
    else:
        links = [s for s in c if "/composition/dashboard/link" in s["path"] and s["behaviour"] == 8]
        if not links:
            return
        d.drop(links, "CUE LEVEL is a relative encoder; an absolute mapping jumps")
        for s in links:
            n = int(re.search(r"link(\d+)", s["path"]).group(1))
            d.add(fxm(n), "relative, so it never jumps and is the recovery gesture after CLEAN")


def arrows_instrument(d):
    up, down = d.at("note", 94), d.at("note", 95)
    if up and down and up[0]["path"].endswith("connectprevcolumn") and down[0]["path"].endswith("connectnextcolumn"):
        d.drop(up, "old direction")
        d.drop(down, "old direction")
        d.add(STD["next_scene"], "UP walks forward")
        d.add(STD["prev_scene"], "DOWN walks back")


def arrows_legacy(d, decks):
    for key, nm in (("next_scene", 94), ("prev_scene", 95)):
        if d.free("note", nm):
            d.add(STD[key], "UP/DOWN walk the scenes in every preset")
    if decks:
        want = {96: ("next_deck", "selectnextdeck"), 97: ("prev_deck", "selectprevdeck")}
        for n, (key, tail) in want.items():
            cur = d.at("note", n)
            if cur and all(s["path"].endswith(tail) for s in cur):
                continue
            d.drop(cur, "RIGHT/LEFT walk the decks in every preset" if cur else "")
            d.add(STD[key], "RIGHT = next deck, LEFT = previous deck")


def buttons_instrument(d, time_knob):
    r = d.at("note", 90)
    if r and all(s["path"].endswith("tempocontroller/resync") for s in r):
        d.drop(r, "no BPM job")
        d.add(STD["fft_home"], "puts the global FFT gain back to the middle")
    t = d.at("note", 99)
    if time_knob and t and all(s["path"].endswith("tempocontroller/tempotap") for s in t):
        d.drop(t, "no BPM job")
        d.add(STD["time_home"], "puts composition speed back to 1x")


def show_legacy(d):
    p = d.at("note", 91)
    if p and all(s["path"].endswith("tempocontroller/resync") for s in p):
        d.drop(p, "PLAY opens the show in every preset")
        d.add(STD["open_show"], "scene 1")
        if d.free("note", 90):
            d.add(STD["resync"], "tempo resync keeps a home on METRONOME")
    for key, kind, n in (("stop", "note", 92), ("blackout", "note", 93), ("footswitch", "cc", 64)):
        if d.free(kind, n):
            d.add(STD[key], "free control; same job in every preset")



# ------------------------------------------------------------------ conformance --
def _paths(d, kind, num, ch=1):
    return [s["path"] for s in d.at(kind, num, ch)]


def _is(d, kind, num, tail):
    ps = _paths(d, kind, num)
    return bool(ps) and all(p.endswith(tail) for p in ps)


def _relative(d, kind, num):
    s = d.at(kind, num)
    return bool(s) and all(x["behaviour"] == 16392 for x in s)


# (label, test(doc, decks)) - the rules of the operator standard
RULES = [
    ("TEMPO = FFT gain, relative", lambda d, k: _is(d, "cc", 13, "audiodevicemanager/params/fftinputgain") and _relative(d, "cc", 13)),
    ("CUE LEVEL relative", lambda d, k: _relative(d, "cc", 47)),
    ("UP = next scene", lambda d, k: _is(d, "note", 94, "connectnextcolumn")),
    ("DOWN = previous scene", lambda d, k: _is(d, "note", 95, "connectprevcolumn")),
    ("RIGHT = next deck", lambda d, k: (not k.get("decks", True)) or _is(d, "note", 96, "selectnextdeck")),
    ("LEFT = previous deck", lambda d, k: (not k.get("decks", True)) or _is(d, "note", 97, "selectprevdeck")),
    ("PLAY opens scene 1", lambda d, k: any(p.endswith("columns/1/connect") for p in _paths(d, "note", 91))),
    ("STOP stops", lambda d, k: not d.free("note", 92)),
    ("RECORD = blackout", lambda d, k: _is(d, "note", 93, "composition/bypassed")),
    ("FOOTSWITCH = blackout", lambda d, k: _is(d, "cc", 64, "composition/bypassed")),
    ("STOP ALL = eject all", lambda d, k: _is(d, "note", 81, "disconnectall")),
    ("MASTER fader", lambda d, k: _is(d, "cc", 14, "composition/master")),
    ("CROSSFADER", lambda d, k: _is(d, "cc", 15, "crossfader/phase")),
]


def check(path, opts=None):
    d = Doc(open(path, encoding="utf-8").read())
    return [(label, bool(test(d, opts or {}))) for label, test in RULES]


PROFILES = {
    "instrument": lambda d, o: (arrows_instrument(d) if o.get("arrows", True) else None,
                                tempo_to_fft(d), cue_relative(d, "fxmaster"),
                                buttons_instrument(d, o.get("time_knob", True))),
    "legacy": lambda d, o: (tempo_to_fft(d), cue_relative(d, "time"), arrows_legacy(d, o.get("decks", True)),
                            show_legacy(d)),
}

def _resolume_dir(*parts):
    """Avenue's folder: $RESOLUME_DIR, else Documents (or OneDrive's Documents) / Resolume Avenue."""
    home = os.path.expanduser("~")
    for base in (os.environ.get("RESOLUME_DIR"), os.path.join(home, "OneDrive", "Documents", "Resolume Avenue"),
                 os.path.join(home, "Documents", "Resolume Avenue")):
        if base and os.path.isdir(base):
            return os.path.join(base, *parts)
    return os.path.join(home, "Documents", "Resolume Avenue", *parts)


MIDI = _resolume_dir("Shortcuts", "MIDI")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    ("Lexicon v1", os.path.join(MIDI, "APC 40 MK II - Lexicon v1.xml"), "legacy", dict(decks=False)),
    ("Lexicon v2", os.path.join(MIDI, "APC 40 MK II - Lexicon v2.xml"), "legacy", dict(decks=True)),
    ("Nisei v1", os.path.join(MIDI, "APC 40 MK II - Nisei v1.xml"), "legacy", dict(decks=True)),
    ("TestCard v1", os.path.join(MIDI, "APC 40 MK II - TestCard v1.xml"), "legacy", dict(decks=True)),
    ("Orbit v1", os.path.join(MIDI, "APC 40 MK II - Orbit v1.xml"), "legacy", dict(decks=True)),
    ("React v4.4", os.path.join(MIDI, "APC 40 MK II - React v4.4.xml"), "legacy", dict(decks=True)),
    ("SPECIMEN", os.path.join(MIDI, "APC 40 MK II - SPECIMEN.xml"), "legacy", dict(decks=True)),
    ("EarthSearch EP01", os.path.join(MIDI, "APC 40 MK II - EarthSearch EP01.xml"), "instrument",
     dict(arrows=False, time_knob=False)),
    ("Dead Air", os.path.join(ROOT, "packs", "dead-air", "APC 40 MK II - Dead Air.xml"), "instrument", {}),
    ("Dew Line", os.path.join(ROOT, "packs", "dew-line", "APC 40 MK II - Dew Line.xml"), "instrument", {}),
]


def patch_file(src, profile, opts, out_dir):
    text = open(src, encoding="utf-8").read()
    d = Doc(text)
    n_before = len(d.sc)
    PROFILES[profile](d, opts)
    new = d.result()
    n_after = len(Doc(new).sc)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, os.path.basename(src))
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(new)
    ids = re.findall(r'uniqueId="(\d+)"', new)
    assert len(ids) == len(set(ids)), "duplicate uniqueIds after patch"
    with open(dst[:-4] + ".changes.txt", "w", encoding="utf-8") as f:
        f.write("%s  (%s profile)\nshortcuts %d -> %d\n\n%s\n" % (os.path.basename(src), profile, n_before, n_after,
                                                                  "\n".join(d.log) or "nothing to change"))
    return dst, n_before, n_after, d.log


INSTRUMENT_PACKS = [("signal-lost", "Signal Lost"), ("studio-one", "Studio One"), ("library-hand", "The Library And The Hand"),
                    ("the-manual", "The Manual"), ("the-surface", "The Surface"), ("the-mixers", "The Mixers"),
                    ("dead-air", "Dead Air"), ("dew-line", "Dew Line")]


def run_check(a):
    rows = []
    files = [(a.file, a.file, {})] if a.file else (
        [(s, os.path.join(ROOT, "packs", s, "APC 40 MK II - %s.xml" % f), {}) for s, f in INSTRUMENT_PACKS]
        + [(n, p, o) for n, p, prof, o in TARGETS if prof == "legacy" or "EarthSearch" in n])
    for name, path, opts in files:
        if not os.path.exists(path):
            rows.append((name, None))
            continue
        rows.append((name, check(path, opts)))
    labels = [r[0] for r in RULES]
    print("%-18s %s" % ("preset", " ".join("%2d" % (i + 1) for i in range(len(labels)))))
    for name, res in rows:
        if res is None:
            print("%-18s missing" % name)
            continue
        print("%-18s %s   %d/%d" % (name, " ".join(" ." if ok else " X" for _, ok in res),
                                    sum(ok for _, ok in res), len(res)))
    print()
    for i, l in enumerate(labels):
        print("  %2d  %s" % (i + 1, l))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="folder for the patched presets and change logs")
    ap.add_argument("--check", action="store_true", help="only report how well each preset follows the standard")
    ap.add_argument("--only", help="comma list of target names (see TARGETS)")
    ap.add_argument("--file", help="patch one arbitrary preset instead of the table")
    ap.add_argument("--profile", choices=sorted(PROFILES), help="with --file")
    a = ap.parse_args()
    if a.check:
        run_check(a)
        return
    if not a.out:
        ap.error("--out is required unless --check")
    jobs = [(a.file, a.file, a.profile, {})] if a.file else TARGETS
    only = set(a.only.split(",")) if a.only else None
    for name, src, profile, opts in jobs:
        if only and name not in only:
            continue
        if not os.path.exists(src):
            print("%-18s MISSING %s" % (name, src))
            continue
        dst, nb, na, log = patch_file(src, profile, opts, a.out)
        print("%-18s %-10s shortcuts %3d -> %3d   %d change(s)" % (name, profile, nb, na, len(log)))
        for line in log:
            print("      " + line)


if __name__ == "__main__":
    main()
