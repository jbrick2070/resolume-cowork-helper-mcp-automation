#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
avc.py - emits a Resolume Avenue 7.28.1 composition (.avc) from a plain
Python description, using only XML shapes Resolume itself has written on this
rig (harvest/out/*.avc, the EarthSearch / Lexicon II / Nisei compositions).

    from resolume_build.avc import Composition
    comp = Composition("Night Field", midi_preset="APC 40 MK II - X")
    comp.dashboard = ["COLOUR", "BROADCAST", ...]          # up to 8
    comp.add_effect("Bloom", {"Threshold": 0.7}, link=3, wet_max=0.8,
                    fft={"Amount": ("mid", 9.0, 600, 0.2, 0.6)})
    L = comp.add_layer("BED", blend="Add", opacity_link=6, crossfader=1,
                       ignore_column=False)
    D = comp.add_deck("Deep Field", columns=["Contact", ...])
    D.add_clip(L, 0, "Starfield", "Metaballs", {"Size": 0.02},
               fft={"Radius": ("low", 9.0, 400, 0.4, 0.9)})
    xml = comp.build()

FFT: every reactive ParamRange gets a PhaseSourceFFT. The link is
/audioengine/externalfft (the audio INPUT device - VB-CABLE on this rig) by
default; pass fft_link="compositionfft" for a composition whose clips carry
their own audio. The inner FrequencyRange is the band; the outer startStop is
the output range in the parameter's own units.

Safety invariants asserted at build():
  * every uniqueId unique; XML well-formed
  * no PhaseSourceFFT inside any <Transport> or on composition Speed
  * layer / column / deck counts match
"""
import re
import xml.etree.ElementTree as ET

from . import library as L

# Blend modes: harvested live on 2026-10-16 by setting every one of the 62
# modes on a layer through REST and reading the XML Resolume saved
# (harvest/out/blend_modes_7281.json). Add is the default and gets no
# ParamChoice. Keys are Resolume's display names ("Soft Light", "Luma Key").
import json as _json
import os as _os
with open(_os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "harvest", "out",
        "blend_modes_7281.json"), encoding="utf-8") as _f:
    _BLENDS = _json.load(_f)
BLEND_TYPES = {k: (v[1][0], v[1][1], v[1][2]) for k, v in _BLENDS.items()}
BLEND_CHOICE = {k: v[0] for k, v in _BLENDS.items() if v[0]}
BLEND_CHOICE_DEFAULT = "67464114"
TYPE_TRANSFORM = "17122039101699797593"

DEFAULT_BANDS = {"low": (0.0, 0.18), "mid": (0.2, 0.55), "high": (0.55, 0.9)}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def num(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    return repr(float(v))


class _Ids(object):
    def __init__(self, base):
        self.n = base

    def __call__(self):
        self.n += 1
        return str(self.n)


# ---------------------------------------------------------------- emitters --
def static(t):
    return "%s<PhaseSourceStatic name=\"PhaseSourceStatic\" />" % ("\t" * t)


def prange(t, name, default, value, body=None, alt=None):
    ind = "\t" * t
    a = ' altName="%s"' % esc(alt) if alt else ""
    body = static(t + 1) if body is None else body
    return ('%s<ParamRange name="%s"%s T="DOUBLE" default="%s" value="%s">\n'
            '%s\n%s</ParamRange>' % (ind, esc(name), a, num(default),
                                     num(value), body, ind))


def pbool(t, name, value, default=False, alt=None):
    ind = "\t" * t
    a = ' altName="%s"' % esc(alt) if alt else ""
    return ('%s<Param name="%s"%s T="BOOL" default="%d" value="%d" />'
            % (ind, esc(name), a, 1 if default else 0, 1 if value else 0))


def pcolor(t, name, value, default=None):
    ind = "\t" * t
    d = value if default is None else default
    return ('%s<ParamColor name="%s" T="COLOR" default="%d" value="%d" '
            'channelmode="2" paletteEnabled="0" color="%d" interpolated="0" />'
            % (ind, esc(name), int(d), int(value), int(value)))


def pchoice(t, name, value, default=0, T="INT32"):
    ind = "\t" * t
    return ('%s<ParamChoice name="%s" T="%s" default="%s" value="%s" '
            'storeChoices="0" />' % (ind, esc(name), T, default, value))


def ptext(t, name, value):
    ind = "\t" * t
    return ('%s<ParamText name="%s" T="STRING" default="Resolume" '
            'value="%s">\n'
            '%s\t<Params name="Params">\n'
            '%s\t\t<Param name="Lines" T="STRING" default="Resolume" '
            'value="%s" />\n'
            '%s\t</Params>\n'
            '%s</ParamText>' % (ind, esc(name), esc(value), ind, ind,
                                esc(value), ind, ind))


def dashboard_body(t, value, link_no, link_name, wet_max=None):
    ind = "\t" * t
    vr = ("" if wet_max is None else
          '\n%s<ValueRange name="startStop" min="0" max="%s" />'
          % (ind, num(wet_max)))
    return ('%s<PhaseSourceDashboardLink name="PhaseSourceDashboardLink" '
            'phase="%s" linkId="/link%d" linkName="%s" />%s'
            % (ind, num(value), link_no, esc(link_name), vr))


def fft_body(t, band, gain_db, fallback_ms, floor, ceiling, bands, link):
    lo, hi = bands[band]
    mid = (lo + hi) / 2.0
    ind = "\t" * t
    return (
        '%s<DurationSource />\n'
        '%s<PhaseSourceFFT name="PhaseSourceFFT" phase="0" '
        'linkId="/audioengine/%s">\n'
        '%s\t<Params name="Params">\n'
        '%s\t\t<ParamRange name="FrequencyRange" T="DOUBLE" default="0.5" '
        'value="%s">\n'
        '%s\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t<ValueRange name="startStop" min="%s" max="%s" />\n'
        '%s\t\t</ParamRange>\n'
        '%s\t\t<ParamRange name="Gain" T="DOUBLE" default="0" value="%s">\n'
        '%s\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t</ParamRange>\n'
        '%s\t\t<ParamRange name="Fallback" T="DOUBLE" default="1000" '
        'value="%s">\n'
        '%s\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t</ParamRange>\n'
        '%s\t</Params>\n'
        '%s</PhaseSourceFFT>\n'
        '%s<ValueRange name="startStop" min="%s" max="%s" />' % (
            ind, ind, link, ind, ind, num(mid), ind, ind, num(lo), num(hi),
            ind, ind, num(gain_db), ind, ind, ind, num(fallback_ms), ind,
            ind, ind, ind, ind, num(floor), num(ceiling)))


def transform_pass(t, ids):
    ind = "\t" * t
    return ('%s<RenderPass storage="0" name="Transform" type="TransformEffect" '
            'uniqueTypeId="%s" uniqueId="%s" baseType="Effect">\n'
            '%s\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0" />\n'
            '%s</RenderPass>' % (ind, TYPE_TRANSFORM, ids(), ind, ind))


def mixer(t, ids, mixer_name, blend=None):
    ind = "\t" * t
    parts = ['%s<ChoosableMixer name="%s">' % (ind, esc(mixer_name))]
    if blend and blend not in BLEND_TYPES:
        raise ValueError("unknown blend mode %r; known: %s"
                         % (blend, ", ".join(sorted(BLEND_TYPES))))
    if blend and blend in BLEND_CHOICE:
        parts.append('%s\t<Params name="Params">' % ind)
        parts.append('%s\t\t<ParamChoice name="Blend Mode" T="UINT64" '
                     'default="%s" value="%s" storeChoices="0" />'
                     % (ind, BLEND_CHOICE_DEFAULT, BLEND_CHOICE[blend]))
        parts.append('%s\t</Params>' % ind)
    parts.append('%s\t<VideoMixerStateID uniqueId="%s" />' % (ind, ids()))
    if blend:
        nm, ty, tid = BLEND_TYPES[blend]
        parts.append('%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
                     'uniqueId="%s" baseType="Mixer" />'
                     % (ind, nm, ty, tid, ids()))
    parts.append('%s</ChoosableMixer>' % ind)
    return "\n".join(parts)


def transport_block(t, seconds=5, ms=5000):
    ind = "\t" * t
    return (
        '%s<Transport name="Transport">\n'
        '%s\t<Params name="Params">\n'
        '%s\t\t<ParamRange name="Position" T="DOUBLE" default="0" value="0">\n'
        '%s\t\t\t<DurationSource defaultDuration="%ds" />\n'
        '%s\t\t\t<PhaseSourceTransportTimeline '
        'name="PhaseSourceTransportTimeline" phase="0" '
        'defaultMillisecondsDuration="%d" defaultBeatsDuration="8">\n'
        '%s\t\t\t\t<Params name="Params">\n'
        '%s\t\t\t\t\t<ParamRange name="Max Distance" altName="Distance" '
        'T="DOUBLE" default="2" value="2">\n'
        '%s\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t\t\t\t<ValueRange name="minMax" min="0" max="5" />\n'
        '%s\t\t\t\t\t</ParamRange>\n'
        '%s\t\t\t\t\t<ParamRange name="BPM" T="DOUBLE" default="120" '
        'value="120">\n'
        '%s\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t\t\t</ParamRange>\n'
        '%s\t\t\t\t</Params>\n'
        '%s\t\t\t\t<Beats_double name="Beats_double" numManualBeats="8" '
        'detectedTempo="-1" />\n'
        '%s\t\t\t</PhaseSourceTransportTimeline>\n'
        '%s\t\t\t<ValueRange name="minMax" min="0" max="%d" />\n'
        '%s\t\t</ParamRange>\n'
        '%s\t</Params>\n'
        '%s</Transport>' % (
            ind, ind, ind, ind, int(seconds), ind, ms, ind, ind, ind, ind,
            ind, ind, ind, ind, ind, ind, ind, ind, ms, ind, ind, ind))


# ----------------------------------------------------------------- objects --
class ParamBlock(object):
    """Emits the <Params> body for a source or effect from checked values."""

    def __init__(self, item, values, fft, bands, fft_link):
        self.item = item
        self.values = item.check(values or {})
        self.fft = {}
        for pname, spec in (fft or {}).items():
            p = item.param(pname)
            if p.kind != "range":
                raise ValueError("FFT on %s/%s: only range parameters can "
                                 "be audio-driven" % (item.display_name, pname))
            band, gain, fall, floor, ceil = spec
            if band not in bands:
                raise ValueError("unknown band %r" % band)
            for v in (floor, ceil):
                p.coerce(v)
            self.fft[p.name] = (band, gain, fall, floor, ceil)
        self.bands = bands
        self.fft_link = fft_link

    def lines(self, t):
        out = []
        item = self.item
        for pname, v in self.values.items():
            spec = item.params[pname]
            if pname in self.fft:
                continue
            if spec.kind == "range":
                out.append(prange(t, pname, spec.default
                                  if spec.default is not None else v, v))
            elif spec.kind == "choice" and L.is_string_choice(spec):
                out.append(pchoice(t, pname, esc(spec.options[v]),
                                   esc(spec.default), T="STRING"))
            elif spec.kind == "choice":
                out.append(pchoice(t, pname, L.xml_choice_index(spec, v),
                                   spec.default_index()))
            elif spec.kind == "bool":
                out.append(pbool(t, pname, v, default=bool(spec.default)))
            elif spec.kind == "color":
                d = item.xml_defaults.get(pname)
                out.append(pcolor(t, pname, v,
                                  int(d) if d is not None else None))
            elif spec.kind == "text":
                out.append(ptext(t, pname, v))
        for pname, (band, gain, fall, floor, ceil) in self.fft.items():
            spec = item.params[pname]
            start = self.values.get(pname, floor)
            out.append(prange(t, pname, spec.default
                              if spec.default is not None else start, start,
                              body=fft_body(t + 1, band, gain, fall, floor,
                                            ceil, self.bands, self.fft_link)))
        return out


class Effect(object):
    def __init__(self, comp, item, values, link, wet_max, fft, bypassed,
                 display_name=None):
        self.item = item
        self.block = ParamBlock(item, values, fft, comp.bands, comp.fft_link)
        self.link = link
        self.wet_max = wet_max
        self.bypassed = bypassed
        self.display_name = display_name
        self.comp = comp

    def xml(self, t, ids):
        ind = "\t" * t
        it = self.item
        body = []
        name = it.xml_name
        body.append('%s<RenderPass storage="0" name="%s" type="%s" '
                    'uniqueTypeId="%s" uniqueId="%s" baseType="DryWetEffect">'
                    % (ind, esc(name), it.wrapper_type, it.tid, ids()))
        body.append('%s\t<Params name="Params">' % ind)
        body.append(pbool(t + 2, "Bypassed", self.bypassed, alt="Bypass"))
        if self.link:
            lname = self.comp.dashboard[self.link - 1]
            # The written value MUST equal the link's value at load: Resolume
            # applies a dashboard link only when it moves, so a macro whose
            # link opens at 0 but whose Opacity is written as 1 sits fully
            # wet until the knob is touched. Seen on the rig as a permanent
            # vignette over every scene.
            lv = float(self.comp.dashboard_values.get(self.link, 1))
            ov = lv if self.wet_max is None else lv * float(self.wet_max)
            body.append(prange(t + 2, "Opacity", 1, ov,
                               body=dashboard_body(t + 3, lv, self.link, lname,
                                                   self.wet_max)))
        elif self.wet_max is not None:
            body.append(prange(t + 2, "Opacity", 1, self.wet_max))
        body.append('%s\t</Params>' % ind)
        inner = self.block.lines(t + 3)
        if inner:
            body.append('%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
                        'uniqueId="%s" baseType="Effect" dwType="Effect">'
                        % (ind, esc(name), it.xml_type, it.inner_tid, ids()))
            body.append('%s\t\t<Params name="Params">' % ind)
            body.extend(inner)
            body.append('%s\t\t</Params>' % ind)
            body.append('%s\t</RenderPass>' % ind)
        else:
            body.append('%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
                        'uniqueId="%s" baseType="Effect" dwType="Effect" />'
                        % (ind, esc(name), it.xml_type, it.inner_tid, ids()))
        body.append(mixer(t + 1, ids, "Mixer", "Alpha"))
        body.append('%s</RenderPass>' % ind)
        return "\n".join(body)


class Layer(object):
    def __init__(self, comp, index, name, blend, opacity, opacity_link,
                 crossfader, ignore_column, master, color_id,
                 trigger_first=False, transition_ms=0, effects=None):
        self.comp = comp
        self.index = index
        self.name = name
        self.blend = blend
        self.opacity = opacity
        self.opacity_link = opacity_link
        self.crossfader = crossfader
        self.ignore_column = ignore_column
        self.master = master
        self.color_id = color_id
        self.trigger_first = trigger_first
        self.transition_ms = transition_ms
        self.effects = effects or []

    @property
    def number(self):
        return self.index + 1

    def xml(self, ids):
        t = 1
        ind = "\t" * t
        p = ['%s<Layer name="Layer" uniqueId="%s" layerIndex="%d">'
             % (ind, ids(), self.index)]
        p.append('%s\t<Params name="Params">' % ind)
        p.append('%s\t\t<Param name="Name" T="STRING" default="Layer #" '
                 'value="%s" />' % (ind, esc(self.name)))
        p.append('%s\t\t<ParamChoice name="ColorId" T="INT32" default="0" '
                 'value="%d" storeChoices="0" />' % (ind, self.color_id))
        if self.crossfader:
            p.append('%s\t\t<ParamChoice name="CrossFaderGroup" T="INT32" '
                     'default="0" value="%d" storeChoices="0" />'
                     % (ind, self.crossfader))
        if self.ignore_column:
            p.append(pbool(t + 2, "Ignore Column Trigger", True))
        p.append(pbool(t + 2, "Trigger first clip on load", self.trigger_first,
                       alt="Trigger First Clip On Play"))
        p.append(prange(t + 2, "Master", 1, self.master))
        p.append('%s\t</Params>' % ind)
        p.append('%s\t<ClipTransition name="ClipTransition">' % ind)
        p.append('%s\t\t<Params name="Params">' % ind)
        p.append(prange(t + 3, "Duration", 0, self.transition_ms / 1000.0))
        p.append('%s\t\t</Params>' % ind)
        p.append('%s\t</ClipTransition>' % ind)
        p.append('%s\t<LayerView name="LayerView" foldedControl="0">' % ind)
        p.append('%s\t\t<FoldParams name="FoldParams" />' % ind)
        p.append('%s\t</LayerView>' % ind)
        p.append('%s\t<AudioTrack name="AudioTrack">' % ind)
        p.append('%s\t\t<AudioEffectChain name="AudioEffectChain" />' % ind)
        p.append('%s\t</AudioTrack>' % ind)
        p.append('%s\t<VideoTrack name="VideoTrack">' % ind)
        p.append('%s\t\t<Params name="Params">' % ind)
        if self.opacity_link:
            lname = self.comp.dashboard[self.opacity_link - 1]
            p.append(prange(t + 3, "Opacity", 0.5, 1,
                            body=dashboard_body(t + 4, 1, self.opacity_link,
                                                lname)))
        else:
            p.append(prange(t + 3, "Opacity", 0.5, self.opacity))
        p.append(prange(t + 3, "Width", self.comp.width, self.comp.width))
        p.append(prange(t + 3, "Height", self.comp.height, self.comp.height))
        p.append('%s\t\t</Params>' % ind)
        p.append('%s\t\t<RenderPass name="RenderPassChain">' % ind)
        p.append(transform_pass(t + 3, ids))
        for fx in self.effects:
            p.append(fx.xml(t + 3, ids))
        p.append('%s\t\t</RenderPass>' % ind)
        p.append(mixer(t + 2, ids, "Blend", self.blend))
        p.append(mixer(t + 2, ids, "Transition", "Alpha"))
        p.append('%s\t</VideoTrack>' % ind)
        p.append('%s</Layer>' % ind)
        return "\n".join(p)


class Clip(object):
    def __init__(self, comp, layer, column, name, item, values, fft,
                 color_id, opacity, effects, seconds, blend):
        self.comp = comp
        self.layer = layer
        self.column = column
        self.name = name
        self.item = item
        self.block = ParamBlock(item, values, fft, comp.bands, comp.fft_link)
        self.color_id = color_id
        self.opacity = opacity
        self.effects = effects or []
        self.seconds = seconds
        self.blend = blend

    def xml(self, ids, t=2):
        ind = "\t" * t
        it = self.item
        p = ['%s<Clip name="Clip" uniqueId="%s" layerIndex="%d" '
             'columnIndex="%d">' % (ind, ids(), self.layer.index, self.column)]
        p.append('%s\t<Params name="Params">' % ind)
        p.append('%s\t\t<Param name="Name" T="STRING" default="%s" '
                 'value="%s" />' % (ind, esc(self.name), esc(self.name)))
        p.append('%s\t\t<ParamChoice name="TransportType" default="0" '
                 'value="0" storeChoices="0" />' % ind)
        p.append('%s\t\t<ParamChoice name="ColorId" T="INT32" default="0" '
                 'value="%d" storeChoices="0" />' % (ind, self.color_id))
        p.append('%s\t</Params>' % ind)
        p.append(transport_block(t + 1, self.seconds, int(self.seconds * 1000)))
        p.append('%s\t<ChoosableMixer name="Transition">' % ind)
        p.append('%s\t\t<VideoMixerStateID uniqueId="%s" />' % (ind, ids()))
        p.append('%s\t</ChoosableMixer>' % ind)
        p.append('%s\t<ClipView name="ClipView">' % ind)
        p.append('%s\t\t<FoldParams name="FoldParams" />' % ind)
        p.append('%s\t</ClipView>' % ind)
        p.append('%s\t<VideoTrack name="VideoTrack">' % ind)
        p.append('%s\t\t<Params name="Params">' % ind)
        p.append(prange(t + 3, "Opacity", 1, self.opacity))
        p.append(prange(t + 3, "Width", self.comp.width, self.comp.width))
        p.append(prange(t + 3, "Height", self.comp.height, self.comp.height))
        for ch in ("RScale", "GScale", "BScale", "AScale"):
            p.append(pbool(t + 3, ch, True, default=True))
        p.append('%s\t\t</Params>' % ind)
        p.append('%s\t\t<RenderPass name="RenderPassChain">' % ind)
        p.append(transform_pass(t + 3, ids))
        for fx in self.effects:
            p.append(fx.xml(t + 3, ids))
        p.append('%s\t\t</RenderPass>' % ind)
        p.append(mixer(t + 2, ids, "Blend", self.blend))
        p.append('%s\t\t<PrimarySource>' % ind)
        p.append('%s\t\t\t<VideoSource storage="0" name="VideoSource" '
                 'width="%d" height="%d" type="%s">'
                 % (ind, self.comp.width, self.comp.height,
                    it.source_type or "GeneratorVideoSource"))
        inner = self.block.lines(t + 6)
        if inner:
            p.append('%s\t\t\t\t<RenderPass name="%s" type="%s" '
                     'uniqueTypeId="%s" uniqueId="%s" baseType="Generator">'
                     % (ind, esc(it.xml_name), it.xml_type, it.tid, ids()))
            p.append('%s\t\t\t\t\t<Params name="Params">' % ind)
            p.extend(inner)
            p.append('%s\t\t\t\t\t</Params>' % ind)
            p.append('%s\t\t\t\t</RenderPass>' % ind)
        else:
            p.append('%s\t\t\t\t<RenderPass name="%s" type="%s" '
                     'uniqueTypeId="%s" uniqueId="%s" baseType="Generator" />'
                     % (ind, esc(it.xml_name), it.xml_type, it.tid, ids()))
        p.append('%s\t\t\t</VideoSource>' % ind)
        p.append('%s\t\t</PrimarySource>' % ind)
        p.append('%s\t</VideoTrack>' % ind)
        p.append('%s</Clip>' % ind)
        return "\n".join(p)


class Deck(object):
    def __init__(self, comp, index, name, columns, column_colors=None):
        self.comp = comp
        self.index = index
        self.name = name
        self.columns = list(columns)
        self.column_colors = column_colors or [1] * len(columns)
        self.clips = {}
        self.deck_id = None

    def add_clip(self, layer, column, name, source, values=None, fft=None,
                 color_id=None, opacity=1.0, effects=None, seconds=5,
                 blend=None):
        if isinstance(layer, int):
            layer = self.comp.layers[layer]
        item = self.comp.lib.source(source)
        fx = [self.comp.make_effect(*e) if isinstance(e, tuple) else e
              for e in (effects or [])]
        clip = Clip(self.comp, layer, column, name, item, values, fft,
                    layer.color_id if color_id is None else color_id,
                    opacity, fx, seconds, blend)
        if (layer.index, column) in self.clips:
            raise ValueError("deck %s already has a clip at layer %d col %d"
                             % (self.name, layer.number, column + 1))
        self.clips[(layer.index, column)] = clip
        return clip

    def xml(self, ids):
        n_layers = len(self.comp.layers)
        n_cols = len(self.columns)
        p = ['\t<Deck name="Deck" uniqueId="%s" closed="0" '
             'numLayersWithContent="%d" numColumnsWithContent="%d" '
             'numLayers="%d" numColumns="%d" deckIndex="%d">'
             % (self.deck_id, n_layers, n_cols, n_layers, n_cols, self.index)]
        p.append('\t\t<Params name="Params">')
        p.append('\t\t\t<Param name="Name" T="STRING" default="empty" '
                 'value="%s" />' % esc(self.name))
        p.append('\t\t</Params>')
        for i, cname in enumerate(self.columns):
            p.append('\t\t<Column uniqueId="%s" columnIndex="%d">' % (ids(), i))
            p.append('\t\t\t<Params name="Params">')
            p.append('\t\t\t\t<Param name="Name" T="STRING" default="Column #" '
                     'value="%s" />' % esc(cname))
            p.append('\t\t\t\t<ParamChoice name="ColorId" T="INT32" default="0" '
                     'value="%d" storeChoices="0" />' % self.column_colors[i])
            p.append('\t\t\t</Params>')
            p.append('\t\t</Column>')
        for col in range(n_cols):
            for layer in self.comp.layers:
                clip = self.clips.get((layer.index, col))
                if clip is not None:
                    p.append(clip.xml(ids))
        p.append('\t</Deck>')
        return "\n".join(p)


class Composition(object):
    def __init__(self, name, width=1920, height=1080, midi_preset="",
                 description="", id_base=1790000000000, fft_link="externalfft",
                 bands=None, lib=None, notes="", speed=1.0):
        self.name = name
        self.width = width
        self.height = height
        self.midi_preset = midi_preset
        self.description = description
        self.ids = _Ids(id_base)
        self.fft_link = fft_link
        self.bands = dict(bands or DEFAULT_BANDS)
        self.lib = lib or L.Library()
        self.notes = notes
        self.speed = speed
        self.dashboard = []        # up to 8 link labels
        self.dashboard_values = {} # link -> value at load (default 1)
        self.effects = []          # composition rack
        self.layers = []
        self.decks = []
        self.crossfader_phase = 0.0
        self.master = 1.0

    # ---- construction -------------------------------------------------
    def make_effect(self, name, values=None, link=None, wet_max=None,
                    fft=None, bypassed=True):
        item = self.lib.effect(name)
        if link is not None and not (1 <= link <= len(self.dashboard)):
            raise ValueError("effect %s: dashboard link %r not defined"
                             % (name, link))
        return Effect(self, item, values, link, wet_max, fft, bypassed)

    def add_effect(self, name, values=None, link=None, wet_max=None, fft=None,
                   bypassed=True):
        fx = self.make_effect(name, values, link, wet_max, fft, bypassed)
        self.effects.append(fx)
        return fx

    def add_layer(self, name, blend="Add", opacity=1.0, opacity_link=None,
                  crossfader=0, ignore_column=False, master=1.0, color_id=1,
                  trigger_first=False, transition_ms=0, effects=None):
        if opacity_link is not None and not (1 <= opacity_link
                                             <= len(self.dashboard)):
            raise ValueError("layer %s: dashboard link %r not defined"
                             % (name, opacity_link))
        fx = [self.make_effect(*e) if isinstance(e, tuple) else e
              for e in (effects or [])]
        layer = Layer(self, len(self.layers), name, blend, opacity,
                      opacity_link, crossfader, ignore_column, master,
                      color_id, trigger_first, transition_ms, fx)
        self.layers.append(layer)
        return layer

    def add_deck(self, name, columns, column_colors=None):
        deck = Deck(self, len(self.decks), name, columns, column_colors)
        self.decks.append(deck)
        return deck

    # ---- build ----------------------------------------------------------
    def build(self):
        ids = self.ids
        n_cols = max(len(d.columns) for d in self.decks)
        for d in self.decks:
            d.deck_id = ids()
        p = ['<?xml version="1.0" encoding="utf-8"?>']
        p.append('<Composition name="Composition" uniqueId="%s" numDecks="%d" '
                 'currentDeckIndex="0" numLayers="%d" numColumns="%d" '
                 'compositionIsRelative="0">'
                 % (ids(), len(self.decks), len(self.layers), n_cols))
        p.append(self.lib.version_info_xml())
        p.append('\t<CompositionInfo name="%s" description="%s" width="%d" '
                 'height="%d">' % (esc(self.name), esc(self.description),
                                   self.width, self.height))
        for d in self.decks:
            p.append('\t\t<DeckInfo name="%s" id="%s" closed="0" />'
                     % (esc(d.name), d.deck_id))
        p.append('\t</CompositionInfo>')
        p.append('\t<Params name="Params">')
        p.append('\t\t<Param name="Name" T="STRING" default="" value="%s" />'
                 % esc(self.name))
        p.append(prange(2, "Speed", 1, self.speed))
        p.append('\t\t<Param name="KeyboardShortcutPreset" T="STRING" '
                 'default="" value="Default" />')
        p.append('\t\t<Param name="MidiShortcutPreset" T="STRING" default="" '
                 'value="%s" />' % esc(self.midi_preset))
        p.append('\t\t<Param name="OscShortcutPreset" T="STRING" default="" '
                 'value="OutputAllMessages" />')
        p.append('\t</Params>')
        if self.dashboard:
            p.append('\t<Params name="Dashboard">')
            for i, label in enumerate(self.dashboard, start=1):
                v = self.dashboard_values.get(i, 1)
                p.append('\t\t<ParamRange name="Link %d" altName="%s" '
                         'T="DOUBLE" default="1" value="%s">'
                         % (i, esc(label), num(v)))
                p.append(static(3))
                p.append('\t\t</ParamRange>')
            p.append('\t</Params>')
        p.append('\t<CompositionView name="CompositionView">')
        p.append('\t\t<FoldParams name="FoldParams">')
        p.append('\t\t\t<FoldState component="/compositionpropertiesdashboard" '
                 'folded="0" />')
        p.append('\t\t</FoldParams>')
        p.append('\t</CompositionView>')
        p.append('\t<AudioTrack name="AudioTrack">')
        p.append('\t\t<AudioEffectChain name="AudioEffectChain" />')
        p.append('\t</AudioTrack>')
        p.append('\t<VideoTrack name="VideoTrack">')
        p.append('\t\t<Params name="Params">')
        p.append(prange(3, "Width", self.width, self.width))
        p.append(prange(3, "Height", self.height, self.height))
        p.append('\t\t</Params>')
        p.append('\t\t<RenderPass name="RenderPassChain">')
        p.append(transform_pass(3, ids))
        for fx in self.effects:
            p.append(fx.xml(3, ids))
        p.append('\t\t</RenderPass>')
        p.append('\t</VideoTrack>')
        for layer in self.layers:
            p.append(layer.xml(ids))
        p.append('\t<CrossFader name="CrossFader">')
        p.append('\t\t<Params name="Params">')
        p.append(prange(3, "Phase", 0, self.crossfader_phase))
        p.append('\t\t</Params>')
        p.append('\t\t<AudioTrack name="AudioTrack">')
        p.append('\t\t\t<AudioEffectChain name="AudioEffectChain" />')
        p.append('\t\t</AudioTrack>')
        p.append('\t\t<VideoTrack name="VideoTrack">')
        p.append('\t\t\t<Params name="Params">')
        p.append(prange(4, "Width", self.width, self.width))
        p.append(prange(4, "Height", self.height, self.height))
        p.append('\t\t\t</Params>')
        p.append('\t\t\t<RenderPass name="RenderPassChain" />')
        p.append(mixer(3, ids, "Blend mode", "Alpha"))
        p.append('\t\t</VideoTrack>')
        p.append('\t</CrossFader>')
        p.append('\t<TempoController name="TempoController" />')
        for d in self.decks:
            p.append(d.xml(ids))
        p.append('\t<Notes name="Notes">')
        p.append('\t\t<Note text_size_multiplier="2" text_color_index="4" '
                 'text="%s" />' % esc(self.notes))
        p.append('\t</Notes>')
        p.append('</Composition>')
        p.append('')
        data = "\n".join(p)
        self._validate(data, n_cols)
        return data

    def _validate(self, data, n_cols):
        ET.fromstring(data.encode("utf-8"))
        ids = re.findall(r'uniqueId="(\d+)"', data)
        assert len(ids) == len(set(ids)), "duplicate uniqueIds"
        assert data.count("<Layer ") == len(self.layers)
        assert data.count("<Deck ") == len(self.decks)
        assert data.count("<DeckInfo ") == len(self.decks)
        assert data.count("<Column ") == sum(len(d.columns)
                                             for d in self.decks)
        for m in re.finditer(r'<Transport name="Transport">(.*?)</Transport>',
                             data, re.S):
            assert "PhaseSourceFFT" not in m.group(1), "FFT inside Transport"
        head = data[:data.index("<VideoTrack")]
        assert "PhaseSourceFFT" not in head, "FFT on composition Speed"
        for name in L.BANNED_EFFECTS:
            xml_name = self.lib.raw["effects"].get(name, {}).get("xml_name")
            if xml_name:
                assert ('name="%s" type="DryWetEffect"' % xml_name) not in data, \
                    "banned effect %s in output" % name

    def counts(self, data):
        return {"layers": len(self.layers), "decks": len(self.decks),
                "clips": data.count("<Clip "),
                "comp_effects": len(self.effects),
                "fft_nodes": data.count("PhaseSourceFFT"),
                "bytes": len(data.encode("utf-8"))}
