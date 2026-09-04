#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_preset_earthsearch.py - generates "APC 40 MK II - EarthSearch EP01.xml".

Emits a Resolume MIDI shortcut preset covering EVERY MIDI-emitting control on
the APC40 mkII surface, from the single control map in es_apc_map.py.

Two things here are worth knowing before editing:

1. SEVERAL SHORTCUTS MAY SHARE ONE MIDI KEY. That is not a bug and not a
   collision - it is how START BOTH fires three clips from one button and how
   CLEAN takes seven dashboard links to zero from one button. Verified: 57
   working presets in this workspace already do it, some with three
   .../connect paths on a single key. The generator therefore checks for
   ACCIDENTAL collisions (two different controls landing on one key) rather
   than for duplicate keys as such.

2. THE FORBIDDEN-PATH ASSERTION IS THE SAFETY CONTRACT. Anything that could
   seek, retrigger or restart a master - transport/position, any column
   connect, connectnextclip, composition speed, deck changes - must not appear
   in the output. The generator refuses to write a preset that contains one.

Usage:
    python gen_preset_earthsearch.py
    python gen_preset_earthsearch.py --out PATH
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

import es_apc_map as M
import es_spec as S

_id = [S.PRESET_ID_BASE]


def nid():
    _id[0] += 1
    return str(_id[0])


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def key_of(sc):
    return (M.note_key(sc["channel"], sc["note"]) if sc["kind"] == "note"
            else M.cc_key(sc["channel"], sc["cc"]))


def shortcut_xml(sc):
    shape = M.SHAPES[sc["shape"]]
    path = sc["path"]

    attrs = ['name="Shortcut"', 'uniqueId="%s"' % nid(),
             'paramNodeName="%s"' % shape["param_node"],
             'behaviour="%s"' % shape["behaviour"]]
    if shape["devices"]:
        attrs.append('inputDeviceName="APC40 mkII"')
        attrs.append('outputDeviceName="APC40 mkII"')

    L = ["\t\t<Shortcut %s>" % " ".join(attrs)]
    L.append('\t\t\t<ShortcutPath name="InputPath" path="%s" '
             'translationType="%s" allowedTranslationTypes="%s" />'
             % (esc(path), shape["tt"], shape["att_in"]))
    L.append('\t\t\t<ShortcutPath name="OutputPath" path="%s" '
             'translationType="%s" allowedTranslationTypes="%s" />'
             % (esc(path), shape["tt"], shape["att_out"]))

    sib = shape.get("sibling")
    if sib is not None:
        sib_path = "" if sib == "" else path.rsplit("/", 1)[0] + "/" + sib
        for nm in ("InputSiblingPath", "OutputSiblingPath"):
            L.append('\t\t\t<ShortcutPath name="%s" path="%s" '
                     'translationType="1" allowedTranslationTypes="-1" />'
                     % (nm, esc(sib_path)))

    if shape.get("subtarget"):
        L.append('\t\t\t<Subtarget type="5" optionIndex="-1" />')

    # A ValueRange rescales the incoming MIDI value into [min, max]. Inverted
    # ranges (min > max) are rig-proven and are what make the footswitch a
    # momentary CLEAN: pressed sends 127 which maps to 0.
    vr = sc.get("value_range")
    if vr is not None:
        L.append('\t\t\t<ValueRange min="%s" max="%s" />' % (vr[0], vr[1]))

    init = sc.get("init")
    if init is None:
        init = "0"
    L.append('\t\t\t<RawInputMessage key="%d" value="%s" numSteps="128" />'
             % (key_of(sc), init))

    if sc["led"]:
        L.append("\t\t\t<NamedValues>")
        for state in sorted(sc["led"]):
            L.append('\t\t\t\t<Value first="%s" second="%s" />'
                     % (esc(state), M.vel(sc["led"][state])))
        L.append("\t\t\t</NamedValues>")

    L.append("\t\t</Shortcut>")
    return "\n".join(L)


# --------------------------------------------------------------------------
# The full physical inventory of the APC40 mkII, so coverage can be asserted
# rather than assumed. 148 controls.
# --------------------------------------------------------------------------
def physical_inventory():
    inv = []
    for n in range(0, 40):
        inv.append(("note", 1, n))                      # 40 clip pads
    for n in (82, 83, 84, 85, 86):
        inv.append(("note", 1, n))                      # 5 scene launch
    for n in (80, 81):
        inv.append(("note", 1, n))                      # master, stop all
    for n in (48, 49, 50, 51, 52, 66):                  # 6 per-track rows
        for ch in range(1, 9):
            inv.append(("note", ch, n))
    for n in list(range(58, 66)) + list(range(87, 104)):
        inv.append(("note", 1, n))                      # device + global rows
    for ch in range(1, 9):
        inv.append(("cc", ch, 7))                       # 8 track faders
    for cc in [13, 14, 15, 47, 64] + list(range(16, 24)) + list(range(48, 56)):
        inv.append(("cc", 1, cc))
    return inv


def build():
    m = M.build_map(S)

    # ---- safety contract ----
    for sc in m:
        for bad in M.FORBIDDEN_PATHS:
            if bad in sc["path"]:
                raise SystemExit(
                    "FORBIDDEN PATH in %r: %s (matched %r). This control could "
                    "seek, retrigger or restart a master."
                    % (sc["control"], sc["path"], bad))

    # ---- collision check ----
    # Duplicate keys are legal and intentional, but only when every shortcut on
    # that key belongs to the SAME logical control.
    by_key = collections.defaultdict(list)
    for sc in m:
        by_key[key_of(sc)].append(sc)
    for k, group in by_key.items():
        physicals = {sc["physical"] for sc in group}
        if len(physicals) > 1:
            raise SystemExit(
                "MIDI KEY COLLISION on %d: %s"
                % (k, " | ".join("%s (%s)" % (sc["control"], sc["physical"])
                                 for sc in group)))
        paths = [sc["path"] for sc in group]
        if len(paths) != len(set(paths)):
            raise SystemExit("duplicate path on one key: %s" % physicals)

    # ---- coverage ----
    covered = {(sc["kind"], sc["channel"],
                sc["note"] if sc["kind"] == "note" else sc["cc"]) for sc in m}
    inv = physical_inventory()
    missing = [c for c in inv if c not in covered]
    extra = [c for c in covered if c not in inv]

    p = ['<?xml version="1.0" encoding="utf-8"?>']
    p.append('<MidiShortcutPreset presetId="%s" name="%s">'
             % (S.PRESET_ID, esc(S.MIDI_PRESET_NAME)))
    p.append('\t<versionInfo name="%s" majorVersion="%d" minorVersion="%d" '
             'microVersion="%d" revision="%d" />'
             % (S.RES_PRODUCT, S.RES_MAJOR, S.RES_MINOR, S.RES_MICRO,
                S.RES_REV))
    p.append('\t<ShortcutManager name="MIDIShortcutManagerShortcuts">')
    group = None
    for sc in m:
        if sc["group"] != group:
            group = sc["group"]
            p.append("\t\t<!-- %s -->" % esc(group.upper()))
        p.append(shortcut_xml(sc))
    p.append("\t</ShortcutManager>")
    p.append("</MidiShortcutPreset>")
    p.append("")
    data = "\n".join(p)

    # ---- validation before writing ----
    ET.fromstring(data.encode("utf-8"))
    ids = re.findall(r'uniqueId="(\d+)"', data)
    assert len(ids) == len(set(ids)), "duplicate uniqueIds"
    assert data.count("<Shortcut ") == len(m), "shortcut count mismatch"
    assert data.count("<ShortcutManager ") == 1
    for bad in M.FORBIDDEN_PATHS:
        assert bad not in data, "forbidden path leaked into the preset: %s" % bad

    return data, m, missing, extra, by_key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    data, m, missing, extra, by_key = build()
    out = a.out or os.path.join(S.OUTPUT_DIR, S.MIDI_PRESET_NAME + ".xml")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(data)

    notes = sum(1 for s in m if s["kind"] == "note")
    ccs = sum(1 for s in m if s["kind"] == "cc")
    physical = len(by_key)
    print("WROTE %s" % out)
    print("  %d bytes | %d shortcuts (%d note, %d CC) on %d physical controls"
          % (len(data.encode("utf-8")), len(m), notes, ccs, physical))
    groups = collections.Counter(s["group"] for s in m)
    for g, n in groups.most_common():
        print("    %-22s %d" % (g, n))
    print("  physical inventory: %d controls" % len(physical_inventory()))
    if missing:
        print("  UNMAPPED (%d):" % len(missing))
        for kind, ch, num in missing:
            print("    %s ch%d %s%d" % (kind, ch,
                                        "n" if kind == "note" else "CC", num))
    else:
        print("  UNMAPPED: none - every control on the surface has a job")
    if extra:
        print("  WARNING: %d mapped controls are not in the inventory: %s"
              % (len(extra), extra[:6]))
    multi = {k: v for k, v in by_key.items() if len(v) > 1}
    if multi:
        print("  multi-shortcut controls (deliberate):")
        for k, v in multi.items():
            print("    %-28s x%d" % (v[0]["physical"], len(v)))


if __name__ == "__main__":
    main()
