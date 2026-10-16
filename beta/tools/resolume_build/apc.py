#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apc.py - emits a Resolume MIDI shortcut preset for the Akai APC40 mkII from a
control table, and asserts that every MIDI-emitting control on the surface
has a job.

Every shortcut SHAPE (behaviour code, paramNodeName, translationType,
allowedTranslationTypes) was harvested from presets that have run on this
rig: the EarthSearch, Lexicon II, Nisei and React v4.4 presets. A shape is
only used if it appears in at least one of them.

Physical addresses: apc40mkii-kit/docs/APC40_native_addresses.md.

    from resolume_build.apc import Preset, note_key
    p = Preset("APC 40 MK II - Night Field", "2026101601", id_base=...)
    p.add("Pad R1C1", "Clip Launch row 1 col 1", "note",
          "/composition/layers/1/clips/1/connect", "clip", note=0,
          led={"Connected": 21, "Disconnected": 22, "Empty": 0, "Off": 0})
    xml, report = p.build(forbidden=["transport/position"])
"""
import collections
import re
import xml.etree.ElementTree as ET

NOTE_MARKER = 72057594037927936        # 2**56
CC_MARKER = 144115188075855872         # 2**57


def note_key(channel, note):
    return NOTE_MARKER + (note << 8) + (0x90 + channel - 1)


def cc_key(channel, cc):
    return CC_MARKER + (cc << 8) + (0xB0 + channel - 1)


def vel(v):
    """Resolume stores LED velocity as velocity/127 at full double precision."""
    return repr(v / 127.0)


# APC40 mkII RGB palette indices that read well on the pads. Only the 40 clip
# pads and the 5 Scene Launch pads speak this palette; every other button LED
# is binary (0 off, anything else on).
LED_RGB = {
    "red":     {"on": 5,  "dim": 6},
    "orange":  {"on": 9,  "dim": 10},
    "amber":   {"on": 9,  "dim": 10},
    "yellow":  {"on": 13, "dim": 14},
    "lime":    {"on": 17, "dim": 18},
    "green":   {"on": 21, "dim": 22},
    "mint":    {"on": 25, "dim": 26},
    "cyan":    {"on": 37, "dim": 38},
    "sky":     {"on": 41, "dim": 42},
    "blue":    {"on": 45, "dim": 46},
    "indigo":  {"on": 49, "dim": 50},
    "violet":  {"on": 53, "dim": 54},
    "magenta": {"on": 57, "dim": 58},
    "pink":    {"on": 57, "dim": 58},
    "white":   {"on": 3,  "dim": 2},
    "bone":    {"on": 3,  "dim": 2},
}

SHAPES = {
    "clip":      dict(behaviour="1028", param_node="", tt="1", att_in="11",
                      att_out="11", devices=True, sibling="connected"),
    "action11":  dict(behaviour="1028", param_node="", tt="1", att_in="11",
                      att_out="11", devices=True, sibling=None),
    "action1":   dict(behaviour="1028", param_node="", tt="1", att_in="1",
                      att_out="1", devices=True, sibling=None),
    "select":    dict(behaviour="1028", param_node="", tt="1", att_in="3",
                      att_out="3", devices=True, sibling="selected"),
    "selectcomp": dict(behaviour="1028", param_node="", tt="1", att_in="1",
                       att_out="1", devices=True, sibling=None),
    "bypass11":  dict(behaviour="4", param_node="", tt="1", att_in="11",
                      att_out="11", devices=False, sibling=None),
    "solo":      dict(behaviour="4", param_node="", tt="1", att_in="3",
                      att_out="3", devices=False, sibling="soloed"),
    "boolparam": dict(behaviour="4", param_node="RangedParam[bool]", tt="1",
                      att_in="1", att_out="1", devices=False, sibling=None),
    "cc11":      dict(behaviour="8", param_node="", tt="1", att_in="11",
                      att_out="11", devices=True, sibling=None,
                      subtarget=True),
    "cc1":       dict(behaviour="8", param_node="", tt="1", att_in="1",
                      att_out="1", devices=True, sibling=None,
                      subtarget=True),
    "ccrange":   dict(behaviour="8", param_node="ParamRange", tt="1",
                      att_in="1", att_out="1", devices=True, sibling=None,
                      subtarget=True),
    "relative":  dict(behaviour="16392", param_node="", tt="1", att_in="1",
                      att_out="1", devices=True, sibling=None),
}


def physical_inventory():
    """Every MIDI-emitting control on the APC40 mkII: 148 of them."""
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


PHYSICAL_NAMES = {
    ("note", 1, 80): "MASTER n80", ("note", 1, 81): "STOP ALL CLIPS n81",
    ("note", 1, 82): "SCENE LAUNCH 1 n82", ("note", 1, 83): "SCENE LAUNCH 2 n83",
    ("note", 1, 84): "SCENE LAUNCH 3 n84", ("note", 1, 85): "SCENE LAUNCH 4 n85",
    ("note", 1, 86): "SCENE LAUNCH 5 n86",
    ("note", 1, 58): "DEVICE < n58", ("note", 1, 59): "DEVICE > n59",
    ("note", 1, 60): "BANK < n60", ("note", 1, 61): "BANK > n61",
    ("note", 1, 62): "DEVICE ON/OFF n62", ("note", 1, 63): "DEVICE LOCK n63",
    ("note", 1, 64): "CLIP/DEV VIEW n64", ("note", 1, 65): "DETAIL VIEW n65",
    ("note", 1, 87): "PAN n87", ("note", 1, 88): "SENDS n88",
    ("note", 1, 89): "USER n89", ("note", 1, 90): "METRONOME n90",
    ("note", 1, 91): "PLAY n91", ("note", 1, 92): "STOP n92",
    ("note", 1, 93): "RECORD n93", ("note", 1, 94): "UP n94",
    ("note", 1, 95): "DOWN n95", ("note", 1, 96): "RIGHT n96",
    ("note", 1, 97): "LEFT n97", ("note", 1, 98): "SHIFT n98",
    ("note", 1, 99): "TAP TEMPO n99", ("note", 1, 100): "NUDGE - n100",
    ("note", 1, 101): "NUDGE + n101", ("note", 1, 102): "SESSION REC n102",
    ("note", 1, 103): "BANK LOCK n103",
    ("cc", 1, 13): "TEMPO knob CC13", ("cc", 1, 14): "MASTER fader CC14",
    ("cc", 1, 15): "CROSSFADER CC15", ("cc", 1, 47): "CUE LEVEL CC47",
    ("cc", 1, 64): "FOOTSWITCH CC64",
}
for _n in range(40):
    PHYSICAL_NAMES[("note", 1, _n)] = "PAD row %d col %d n%d" % (
        _n // 8 + 1, _n % 8 + 1, _n)
for _ch in range(1, 9):
    for _n, _lab in ((48, "RECORD ARM"), (49, "SOLO"), (50, "ACTIVATOR"),
                     (51, "TRACK SELECT"), (52, "CLIP STOP"),
                     (66, "CROSSFADE A/B")):
        PHYSICAL_NAMES[("note", _ch, _n)] = "%s n%d ch%d" % (_lab, _n, _ch)
    PHYSICAL_NAMES[("cc", _ch, 7)] = "TRACK FADER CC7 ch%d" % _ch
for _i in range(8):
    PHYSICAL_NAMES[("cc", 1, 16 + _i)] = "DEVICE knob %d CC%d" % (_i + 1,
                                                                 16 + _i)
    PHYSICAL_NAMES[("cc", 1, 48 + _i)] = "TRACK knob %d CC%d" % (_i + 1,
                                                                48 + _i)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


class Preset(object):
    def __init__(self, name, preset_id, id_base, version=(7, 28, 1, 26535),
                 product="Resolume Avenue"):
        self.name = name
        self.preset_id = preset_id
        self._id = id_base
        self.version = version
        self.product = product
        self.map = []

    def nid(self):
        self._id += 1
        return str(self._id)

    def add(self, control, kind, path, shape, note=None, cc=None, channel=1,
            led=None, value_range=None, init=None, group="", note_text="",
            physical=None):
        key = (kind, channel, note if kind == "note" else cc)
        self.map.append(dict(
            control=control, physical=physical or PHYSICAL_NAMES.get(
                key, "%s ch%d %s" % (kind, channel, key[2])),
            kind=kind, path=path, shape=shape, note=note, cc=cc,
            channel=channel, led=led or {}, value_range=value_range,
            init=init, group=group, note_text=note_text))
        return self.map[-1]

    @staticmethod
    def key_of(sc):
        return (note_key(sc["channel"], sc["note"]) if sc["kind"] == "note"
                else cc_key(sc["channel"], sc["cc"]))

    def shortcut_xml(self, sc):
        shape = SHAPES[sc["shape"]]
        path = sc["path"]
        attrs = ['name="Shortcut"', 'uniqueId="%s"' % self.nid(),
                 'paramNodeName="%s"' % shape["param_node"],
                 'behaviour="%s"' % shape["behaviour"]]
        if shape["devices"]:
            attrs.append('inputDeviceName="APC40 mkII"')
            attrs.append('outputDeviceName="APC40 mkII"')
        X = ["\t\t<Shortcut %s>" % " ".join(attrs)]
        X.append('\t\t\t<ShortcutPath name="InputPath" path="%s" '
                 'translationType="%s" allowedTranslationTypes="%s" />'
                 % (esc(path), shape["tt"], shape["att_in"]))
        X.append('\t\t\t<ShortcutPath name="OutputPath" path="%s" '
                 'translationType="%s" allowedTranslationTypes="%s" />'
                 % (esc(path), shape["tt"], shape["att_out"]))
        sib = shape.get("sibling")
        if sib is not None:
            sib_path = path.rsplit("/", 1)[0] + "/" + sib
            for nm in ("InputSiblingPath", "OutputSiblingPath"):
                X.append('\t\t\t<ShortcutPath name="%s" path="%s" '
                         'translationType="1" allowedTranslationTypes="-1" />'
                         % (nm, esc(sib_path)))
        if shape.get("subtarget"):
            X.append('\t\t\t<Subtarget type="5" optionIndex="-1" />')
        vr = sc.get("value_range")
        if vr is not None:
            X.append('\t\t\t<ValueRange min="%s" max="%s" />' % (vr[0], vr[1]))
        init = sc.get("init")
        X.append('\t\t\t<RawInputMessage key="%d" value="%s" numSteps="128" />'
                 % (self.key_of(sc), "0" if init is None else init))
        if sc["led"]:
            X.append("\t\t\t<NamedValues>")
            for state in sorted(sc["led"]):
                X.append('\t\t\t\t<Value first="%s" second="%s" />'
                         % (esc(state), vel(sc["led"][state])))
            X.append("\t\t\t</NamedValues>")
        X.append("\t\t</Shortcut>")
        return "\n".join(X)

    def build(self, forbidden=()):
        m = self.map
        for sc in m:
            for bad in forbidden:
                if bad in sc["path"]:
                    raise SystemExit("FORBIDDEN PATH in %r: %s (matched %r)"
                                     % (sc["control"], sc["path"], bad))
        by_key = collections.defaultdict(list)
        for sc in m:
            by_key[self.key_of(sc)].append(sc)
        for k, group in by_key.items():
            physicals = {sc["physical"] for sc in group}
            if len(physicals) > 1:
                raise SystemExit("MIDI KEY COLLISION on %d: %s" % (
                    k, " | ".join("%s (%s)" % (sc["control"], sc["physical"])
                                  for sc in group)))
            paths = [sc["path"] for sc in group]
            if len(paths) != len(set(paths)):
                raise SystemExit("duplicate path on one key: %s" % physicals)
        covered = {(sc["kind"], sc["channel"],
                    sc["note"] if sc["kind"] == "note" else sc["cc"])
                   for sc in m}
        inv = physical_inventory()
        missing = [c for c in inv if c not in covered]
        extra = [c for c in covered if c not in inv]

        ma, mi, mc, rev = self.version
        p = ['<?xml version="1.0" encoding="utf-8"?>']
        p.append('<MidiShortcutPreset presetId="%s" name="%s">'
                 % (self.preset_id, esc(self.name)))
        p.append('\t<versionInfo name="%s" majorVersion="%d" minorVersion="%d" '
                 'microVersion="%d" revision="%d" />'
                 % (self.product, ma, mi, mc, rev))
        p.append('\t<ShortcutManager name="MIDIShortcutManagerShortcuts">')
        group = None
        for sc in m:
            if sc["group"] != group:
                group = sc["group"]
                p.append("\t\t<!-- %s -->" % esc(group.upper()))
            p.append(self.shortcut_xml(sc))
        p.append("\t</ShortcutManager>")
        p.append("</MidiShortcutPreset>")
        p.append("")
        data = "\n".join(p)
        ET.fromstring(data.encode("utf-8"))
        ids = re.findall(r'uniqueId="(\d+)"', data)
        assert len(ids) == len(set(ids)), "duplicate uniqueIds"
        assert data.count("<Shortcut ") == len(m)
        for bad in forbidden:
            assert bad not in data
        multi = {v[0]["physical"]: len(v) for k, v in by_key.items()
                 if len(v) > 1}
        report = dict(shortcuts=len(m), physical=len(by_key),
                      notes=sum(1 for s in m if s["kind"] == "note"),
                      ccs=sum(1 for s in m if s["kind"] == "cc"),
                      inventory=len(inv),
                      missing=["%s ch%d %s%d" % (k, ch, "n" if k == "note"
                                                 else "CC", n)
                               for (k, ch, n) in missing],
                      extra=extra, multi=multi,
                      groups=collections.Counter(s["group"] for s in m))
        return data, report
