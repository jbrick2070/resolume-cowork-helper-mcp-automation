#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
library.py - the rig-harvested vocabulary of Resolume Avenue 7.28.1.

Reads harvest/out/avenue_7281_library.json (written by harvest/harvest_7281.py
from the running application) and exposes it as typed objects, so a builder
can never write a parameter name, type id or choice that Resolume does not
have. Nothing here is guessed; if it is not in the harvest, it does not exist.

    lib = Library()
    src = lib.source("Metaballs")        # xml_name, xml_type, tid, params
    fx  = lib.effect("Bloom")            # xml_name, xml_type, tid, params
    src.check({"Size": 0.3, "Color": "#ff0000"})   # raises on anything wrong
    slug("Hue Rotate") -> "huerotate"    # Resolume's OSC/REST address slug

Colours: Resolume's ParamColor uint32 is A<<24 | B<<16 | G<<8 | R (ABGR),
confirmed again on this rig: Tunnelines "Color 1" is #ff2222ff in the REST
JSON and 4280427263 = 0xFF2222FF in the XML Resolume wrote.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIBRARY_JSON = os.path.join(ROOT, "harvest", "out", "avenue_7281_library.json")

PRODUCT = ("Resolume Avenue", 7, 28, 1, 26535)

# Effects that must never be written into a pack. Shape Shifter 3D carries
# 529 parameters and crashed Avenue 7.28.1 on save (twice, 2026-10-16).
# Mask / LUT / UV Map need a file. The AI depth chain and keyers are stock
# but pointless on flat generative content and heavy on the GPU.
BANNED_EFFECTS = {"Shape Shifter 3D", "JuiceEditor", "Mask", "LUT", "UV Map",
                  "Keystone", "Keystone Crop", "Keystone Mask", "Crop",
                  "ChromaKey", "Background Removal", "Auto Mask",
                  "Depth Blur", "Depth Displace", "Depth Estimation",
                  "Depth Field", "Depth Pixelation", "Depth Shift"}

# STOCK ONLY (performer's instruction, 2026-10-16): nothing third-party.
# The React FFGL plugins are this workspace's own, the plain-uuid Wire
# patches are the performer's, JuiceEditor is JuiceBar's. Resolume-shipped
# Wire content carries a "c_" uuid and is stock.
THIRD_PARTY = {"React Pulsar", "React Video Musi", "React Anamorphic",
               "React Gate", "React Scanline", "JuiceEditor",
               "Golden Flicker Reel", "aa", "ndi"}
BANNED_EFFECTS |= THIRD_PARTY

# Text choices Resolume stores by NAME, not index (rig-saved compositions:
# <ParamChoice name="Font" T="STRING" default="Arial" value="Bahnschrift">).
# Only the TEXT generators' Font / Style - Rings also has a "Style" and
# writing that as a string made it load as its default (found 2026-10-16).
STRING_CHOICES = {"Font", "Style"}
_STRING_CHOICE_MARKERS = {"Arial", "Bold", "Regular", "Italic"}

# Choice parameters whose XML index order differs from the REST options
# order. Probed on the rig by writing every index and reading back what
# loaded (harvest/out/choice_enum_probe.json). Key: "<param>|<options
# joined by comma>" -> {option name: xml index}; options not listed are
# identity. Text Animator "Range" is reversed; Geometry Pattern Maker
# "Bloom Mode" shifts from index 20.
with open(os.path.join(ROOT, "harvest", "out", "choice_overrides.json"),
          encoding="utf-8") as _f:
    CHOICE_OVERRIDES = json.load(_f)


def is_string_choice(spec):
    return (spec.name in STRING_CHOICES and spec.options
            and any(o in _STRING_CHOICE_MARKERS for o in spec.options))


def xml_choice_index(spec, json_index):
    """The index Resolume expects in the XML for this option."""
    key = "%s|%s" % (spec.name, ",".join(spec.options or []))
    table = CHOICE_OVERRIDES.get(key)
    if table:
        return table.get(spec.options[json_index], json_index)
    return json_index


def slug(name):
    """Resolume's address slug: lowercase, non-alphanumerics stripped.

    Derived from the XML type/name Resolume writes ("Hue Rotate" in the
    browser is HueRotate in the file -> huerotate). Rig-proven across every
    MIDI preset in this workspace.
    """
    return "".join(ch.lower() for ch in name if ch.isalnum())


def abgr(r, g, b, a=255):
    return (a << 24) | (b << 16) | (g << 8) | r


def color_u32(value):
    """'#rrggbb' / '#rrggbbaa' / (r,g,b[,a]) / int -> Resolume uint32."""
    if isinstance(value, int):
        return value
    if isinstance(value, (tuple, list)):
        r, g, b = value[:3]
        a = value[3] if len(value) > 3 else 255
        return abgr(int(r), int(g), int(b), int(a))
    s = str(value).strip().lstrip("#")
    if len(s) == 6:
        s += "ff"
    if len(s) != 8:
        raise ValueError("bad colour %r" % value)
    r, g, b, a = (int(s[i:i + 2], 16) for i in (0, 2, 4, 6))
    return abgr(r, g, b, a)


def u32_to_hex(v):
    r, g, b, a = v & 255, (v >> 8) & 255, (v >> 16) & 255, (v >> 24) & 255
    return "#%02x%02x%02x%02x" % (r, g, b, a)


class ParamSpec(object):
    __slots__ = ("name", "kind", "min", "max", "default", "options",
                 "valuetype")

    def __init__(self, name, live):
        self.name = name
        self.valuetype = live.get("valuetype")
        self.kind = {"ParamRange": "range", "ParamChoice": "choice",
                     "ParamBoolean": "bool", "ParamColor": "color",
                     "ParamText": "text"}.get(self.valuetype, "other")
        self.min = live.get("min")
        self.max = live.get("max")
        self.options = live.get("options")
        self.default = live.get("value")

    def default_index(self):
        if self.kind != "choice":
            return None
        try:
            return xml_choice_index(self, self.options.index(self.default))
        except (ValueError, AttributeError):
            return 0

    def coerce(self, value):
        """Validate and normalise a user value for this parameter."""
        if self.kind == "range":
            v = float(value)
            if self.min is not None and (v < self.min - 1e-9
                                         or v > self.max + 1e-9):
                raise ValueError("%s=%r outside [%s..%s]"
                                 % (self.name, value, self.min, self.max))
            return v
        if self.kind == "choice":
            if isinstance(value, bool):
                raise ValueError("%s: bool given for a choice" % self.name)
            if isinstance(value, int):
                if not 0 <= value < len(self.options):
                    raise ValueError("%s: index %d out of range"
                                     % (self.name, value))
                return value
            opts_l = [o.lower() for o in self.options]
            if str(value).lower() not in opts_l:
                raise ValueError("%s=%r not in %s" % (self.name, value,
                                                      self.options))
            return opts_l.index(str(value).lower())
        if self.kind == "bool":
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "on")
            return bool(value)
        if self.kind == "color":
            return color_u32(value)
        if self.kind == "text":
            return str(value)
        raise ValueError("%s: parameter kind %s cannot be set from a file"
                         % (self.name, self.valuetype))

    def describe(self):
        if self.kind == "range":
            return "%s range [%s..%s] default %s" % (self.name, self.min,
                                                    self.max, self.default)
        if self.kind == "choice":
            return "%s choice %s default %s" % (self.name, self.options,
                                                self.default)
        return "%s %s default %s" % (self.name, self.kind, self.default)


class Item(object):
    """A source or an effect: XML identity plus its parameter specs."""

    def __init__(self, display_name, entry, is_effect):
        self.display_name = display_name
        self.is_effect = is_effect
        self.xml_name = entry.get("xml_name")
        self.xml_type = entry.get("xml_type")
        self.tid = entry.get("uniqueTypeId")
        self.inner_tid = entry.get("inner_uniqueTypeId") or self.tid
        self.wrapper_type = entry.get("wrapper_type", "DryWetEffect")
        self.source_type = entry.get("source_type")
        self.presets = [p["name"] if isinstance(p, dict) else p
                        for p in entry.get("presets", [])]
        live = entry.get("params_live") or {}
        self.params = {}
        for pname, p in live.items():
            if is_effect and pname == "Opacity":
                continue        # the wrapper's dry/wet, handled separately
            self.params[pname] = ParamSpec(pname, p)
        # Default attribute values Resolume itself wrote for colours.
        self.xml_defaults = {p["name"]: p.get("default")
                             for p in entry.get("params_written", [])
                             if p.get("name")}

    @property
    def slug(self):
        return slug(self.xml_name)

    def param(self, name):
        if name not in self.params:
            close = [p for p in self.params if p.lower() == name.lower()]
            if close:
                return self.params[close[0]]
            raise KeyError("%s has no parameter %r. It has: %s"
                           % (self.display_name, name,
                              ", ".join(sorted(self.params))))
        return self.params[name]

    def check(self, values):
        """Return {canonical name: coerced value}; raise on anything wrong."""
        out = {}
        for k, v in (values or {}).items():
            spec = self.param(k)
            out[spec.name] = spec.coerce(v)
        return out


class Library(object):
    def __init__(self, path=LIBRARY_JSON):
        with open(path, encoding="utf-8") as f:
            self.raw = json.load(f)
        self.sources = {n: Item(n, e, False)
                        for n, e in self.raw["sources"].items()
                        if e.get("xml_name") and n not in THIRD_PARTY}
        self.effects = {n: Item(n, e, True)
                        for n, e in self.raw["effects"].items()
                        if e.get("xml_name") and n not in BANNED_EFFECTS}
        self._by_slug = {}
        for it in list(self.sources.values()) + list(self.effects.values()):
            self._by_slug.setdefault(it.slug, it)

    def source(self, name):
        if name in self.sources:
            return self.sources[name]
        for n, it in self.sources.items():
            if slug(n) == slug(name) or it.slug == slug(name):
                return it
        raise KeyError("unknown source %r. Known: %s"
                       % (name, ", ".join(sorted(self.sources))))

    def effect(self, name):
        if name in self.effects:
            return self.effects[name]
        for n, it in self.effects.items():
            if slug(n) == slug(name) or it.slug == slug(name):
                return it
        if name in BANNED_EFFECTS:
            raise KeyError("effect %r is banned (crashes Avenue or needs a "
                           "file)" % name)
        raise KeyError("unknown effect %r. Known: %s"
                       % (name, ", ".join(sorted(self.effects))))

    def version_info_xml(self, indent="\t"):
        n, ma, mi, mc, rev = PRODUCT
        return ('%s<versionInfo name="%s" majorVersion="%d" minorVersion="%d" '
                'microVersion="%d" revision="%d" />' % (indent, n, ma, mi, mc,
                                                        rev))


if __name__ == "__main__":
    lib = Library()
    print("%d sources, %d effects" % (len(lib.sources), len(lib.effects)))
    for n in sorted(lib.sources):
        s = lib.sources[n]
        print("SRC %-24s %-22s %s" % (n, s.xml_type, s.tid))
