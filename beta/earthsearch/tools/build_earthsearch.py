#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_earthsearch.py - generates "EarthSearch_EP01_Live_Mix.avc".

Every XML shape here was verified against files Resolume itself wrote - rig-
saved 7.27.1 compositions in this workspace and Resolume Avenue's own shipped
presets - rather than guessed. In particular:

  * the VideoFormatReaderSource file-clip anatomy and its TWO path fields,
  * the GeneratorVideoSource anatomy and ParamColor / ParamText encodings,
  * the timeline TransportType dialect used for a 27-minute file,
  * the ChoosableMixer Blend Mode ParamChoice (Add 67464114 is the DEFAULT, so
    a layer that must dissolve rather than sum has to say Alpha explicitly),
  * PhaseSourceFFT with linkId="/audioengine/compositionfft",
  * PhaseSourceDashboardLink,
  * the Layer "Master" ParamRange.

Usage:
    python build_earthsearch.py
    python build_earthsearch.py --a V2 --b V3
    python build_earthsearch.py --dxv          # point at the DXV placeholders
    python build_earthsearch.py --allow-missing
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

import es_spec as S

_id = [S.ID_BASE]


def nid():
    _id[0] += 1
    return str(_id[0])


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def num(v):
    """Emit a double the way Resolume tolerates: plain, full precision."""
    if isinstance(v, int):
        return str(v)
    return repr(float(v))


# --------------------------------------------------------------------------
# Small emitters
# --------------------------------------------------------------------------
def static(t):
    return "%s<PhaseSourceStatic name=\"PhaseSourceStatic\" />" % ("\t" * t)


def prange(t, name, default, value, body=None, extra=""):
    ind = "\t" * t
    body = static(t + 1) if body is None else body
    return ('%s<ParamRange name="%s" T="DOUBLE" default="%s" value="%s"%s>\n'
            '%s\n%s</ParamRange>' % (ind, esc(name), default, value, extra,
                                     body, ind))


def pbool(t, name, value, default="0", alt=None):
    ind = "\t" * t
    a = ' altName="%s"' % esc(alt) if alt else ""
    return ('%s<Param name="%s"%s T="BOOL" default="%s" value="%d" />'
            % (ind, esc(name), a, default, 1 if value else 0))


def pcolor(t, name, value, default=4294967295):
    ind = "\t" * t
    return ('%s<ParamColor name="%s" T="COLOR" default="%d" value="%d" '
            'channelmode="2" paletteEnabled="0" color="%d" interpolated="0" />'
            % (ind, esc(name), default, value, value))


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


def dashboard_link(t, name, default, value, link_no, link_name):
    """A ParamRange driven by a composition dashboard link.

    Rig-verified shape from "Res Fable Live Gen SPECIMEN.avc". One link can be
    referenced by any number of parameters, which is exactly what makes the
    CLEAN control possible without inventing a shortcut species.
    """
    ind = "\t" * t
    return ('%s<ParamRange name="%s" T="DOUBLE" default="%s" value="%s">\n'
            '%s\t<PhaseSourceDashboardLink name="PhaseSourceDashboardLink" '
            'phase="%s" linkId="/link%d" linkName="%s" />\n'
            '%s</ParamRange>' % (ind, esc(name), default, value, ind, value,
                                 link_no, esc(link_name), ind))


def fft_prange(t, name, default, band, gain_db, fallback_ms, floor, ceiling):
    """A ParamRange driven by Composition FFT.

    linkId is /audioengine/compositionfft, NOT externalfft: composition FFT
    analyses the composition's own audio, which here is the original programme
    audio embedded in the masters and decoded by the same clip that draws the
    picture. It is therefore frame-locked to the image by construction - no
    virtual audio cable, no second transport, nothing to drift.

    The inner FrequencyRange/startStop is the BAND. The outer startStop is the
    OUTPUT range the band sweeps the parameter through: min is what you see in
    silence, max is what you see at full. Neither can reach transport.
    """
    lo, hi = S.BANDS[band]
    mid = (lo + hi) / 2.0
    ind = "\t" * t
    return (
        '%s<ParamRange name="%s" T="DOUBLE" default="%s" value="%s">\n'
        '%s\t<DurationSource />\n'
        '%s\t<PhaseSourceFFT name="PhaseSourceFFT" phase="0" '
        'linkId="/audioengine/compositionfft">\n'
        '%s\t\t<Params name="Params">\n'
        '%s\t\t\t<ParamRange name="FrequencyRange" T="DOUBLE" default="0.5" '
        'value="%s">\n'
        '%s\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t\t<ValueRange name="startStop" min="%s" max="%s" />\n'
        '%s\t\t\t</ParamRange>\n'
        '%s\t\t\t<ParamRange name="Gain" T="DOUBLE" default="0" value="%s">\n'
        '%s\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t</ParamRange>\n'
        '%s\t\t\t<ParamRange name="Fallback" T="DOUBLE" default="1000" '
        'value="%s">\n'
        '%s\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t</ParamRange>\n'
        '%s\t\t</Params>\n'
        '%s\t</PhaseSourceFFT>\n'
        '%s\t<ValueRange name="startStop" min="%s" max="%s" />\n'
        '%s</ParamRange>' % (
            ind, esc(name), default, num(floor),
            ind, ind, ind, ind, num(mid), ind, ind, num(lo), num(hi), ind,
            ind, num(gain_db), ind, ind,
            ind, num(fallback_ms), ind, ind,
            ind, ind, ind, num(floor), num(ceiling), ind))


def transform_pass(t):
    ind = "\t" * t
    return ('%s<RenderPass storage="0" name="Transform" type="TransformEffect" '
            'uniqueTypeId="%s" uniqueId="%s" baseType="Effect">\n'
            '%s\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0" />\n'
            '%s</RenderPass>' % (ind, S.TYPE_TRANSFORM, nid(), ind, ind))


def mixer(t, mixer_name, blend=None):
    """A ChoosableMixer.

    When a blend is named, BOTH the Blend Mode ParamChoice and the mixer
    RenderPass are written. Omitting the ParamChoice is the trap: Resolume's
    own default is Add (67464114), so a layer meant to dissolve would silently
    sum instead.
    """
    ind = "\t" * t
    parts = ['%s<ChoosableMixer name="%s">' % (ind, esc(mixer_name))]
    if blend:
        parts.append('%s\t<Params name="Params">' % ind)
        parts.append('%s\t\t<ParamChoice name="Blend Mode" T="UINT64" '
                     'default="%s" value="%s" storeChoices="0" />'
                     % (ind, S.BLEND_CHOICE_DEFAULT, S.BLEND_CHOICE[blend]))
        parts.append('%s\t</Params>' % ind)
    parts.append('%s\t<VideoMixerStateID uniqueId="%s" />' % (ind, nid()))
    if blend:
        parts.append('%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
                     'uniqueId="%s" baseType="Mixer" />'
                     % (ind, blend, blend, S.BLEND_TYPES[blend], nid()))
    parts.append('%s</ChoosableMixer>' % ind)
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Effects
# --------------------------------------------------------------------------
def effect_pass(t, label, eff_key, values, link_no, fft_params=None):
    """One composition-rack effect.

    Loads BYPASSED, so the composition opens on the untouched picture. Its
    DryWetEffect Opacity is on the bank's dashboard link, which is how one
    fader gesture can take the whole rack to dry.

    fft_params maps an inner parameter name to
    (band, gain_db, fallback_ms, floor, ceiling). It is deliberately never the
    wrapper Opacity: that must stay on the dashboard link or CLEAN could not
    reach this effect.
    """
    fft_params = fft_params or {}
    xml_type, tid, known = S.EFFECT_LIBRARY[eff_key]
    ind = "\t" * t

    inner = []
    ordered = [p for p in known if p in values or p in fft_params]
    for pname in ordered:
        if pname in fft_params:
            band, gain, fall, floor, ceil = fft_params[pname]
            inner.append(fft_prange(t + 3, pname, num(values.get(pname, floor)),
                                    band, gain, fall, floor, ceil))
        else:
            inner.append(prange(t + 3, pname, num(values[pname]),
                                num(values[pname])))

    body = []
    # The RenderPass name is the EFFECT KEY, not the human label: Resolume
    # derives the OSC address from the display name, so the name written here
    # is exactly what /composition/video/effects/<slug>/bypassed resolves to.
    # The human label lives in the control-map document instead.
    body.append('%s<RenderPass storage="0" name="%s" type="DryWetEffect" '
                'uniqueTypeId="%s" uniqueId="%s" baseType="DryWetEffect">'
                % (ind, esc(eff_key), tid, nid()))
    body.append('%s\t<Params name="Params">' % ind)
    body.append(pbool(t + 2, "Bypassed", True, alt="Bypass"))
    body.append(dashboard_link(t + 2, "Opacity", "1", "1", link_no,
                               S.COMP_DASHBOARD[link_no - 1][1]))
    body.append('%s\t</Params>' % ind)
    if inner:
        body.append('%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
                    'uniqueId="%s" baseType="Effect" dwType="Effect">'
                    % (ind, esc(eff_key), xml_type, tid, nid()))
        body.append('%s\t\t<Params name="Params">' % ind)
        body.extend(inner)
        body.append('%s\t\t</Params>' % ind)
        body.append('%s\t</RenderPass>' % ind)
    else:
        body.append('%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
                    'uniqueId="%s" baseType="Effect" dwType="Effect" />'
                    % (ind, esc(eff_key), xml_type, tid, nid()))
    body.append(mixer(t + 1, "Mixer", "Alpha"))
    body.append('%s</RenderPass>' % ind)
    return "\n".join(body)


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------
def transport_block(t, seconds, ms):
    """Timeline transport (TransportType 0) at the clip's own natural rate.

    BPM sync is deliberately not used anywhere in this composition: a 27-minute
    drama tempo-stretched to a BPM grid would neither stay at 24 fps nor stay
    in sync with its own soundtrack.
    """
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
        'T="DOUBLE" default="5" value="2">\n'
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


# --------------------------------------------------------------------------
# Clips
# --------------------------------------------------------------------------
def clip_head(t, name, layer_index, column_index, color_id, preload=None,
              with_audio=False):
    ind = "\t" * t
    p = ['%s<Clip name="Clip" uniqueId="%s" layerIndex="%d" columnIndex="%d">'
         % (ind, nid(), layer_index, column_index)]
    if preload:
        p.append('%s\t<PreloadData>' % ind)
        # An AudioFile entry alongside the VideoFile is what tells Resolume the
        # clip has a soundtrack. Without it the clip loads video-only and the
        # composition FFT has nothing to analyse - found the hard way on this
        # rig, where the first build produced a silent, non-reactive comp.
        if with_audio:
            p.append('%s\t\t<AudioFile value="%s" />' % (ind, esc(preload)))
        p.append('%s\t\t<VideoFile value="%s" />' % (ind, esc(preload)))
        p.append('%s\t</PreloadData>' % ind)
    p.append('%s\t<Params name="Params">' % ind)
    p.append('%s\t\t<Param name="Name" T="STRING" default="%s" value="%s" />'
             % (ind, esc(name), esc(name)))
    p.append('%s\t\t<ParamChoice name="TransportType" default="0" value="0" '
             'storeChoices="0" />' % ind)
    p.append('%s\t\t<ParamChoice name="ColorId" T="INT32" default="0" '
             'value="%d" storeChoices="0" />' % (ind, color_id))
    p.append('%s\t</Params>' % ind)
    return p


def audio_track(t, media_path, volume_db):
    """A clip's audio track.

    Shape harvested from a clip Resolume built itself from this exact media.
    The AudioFileSource instantiates the FFMPEG audio decoder, and that decoder
    is what feeds Composition FFT. Volume is in dB; 0 is unity.
    """
    ind = "\t" * t
    return ('%s<AudioTrack name="AudioTrack">\n'
            '%s\t<Params name="Params">\n'
            '%s\t\t<ParamRange name="Volume" T="DOUBLE" default="0" '
            'value="%s">\n'
            '%s\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
            '%s\t\t</ParamRange>\n'
            '%s\t</Params>\n'
            '%s\t<AudioEffectChain name="AudioEffectChain" />\n'
            '%s\t<PrimarySource>\n'
            '%s\t\t<AudioFileSource FileName="%s" />\n'
            '%s\t</PrimarySource>\n'
            '%s</AudioTrack>' % (ind, ind, ind, num(volume_db), ind, ind, ind,
                                 ind, ind, ind, esc(media_path), ind, ind))


def clip_tail_open(t, opacity_block, ascale, audio_block=None):
    ind = "\t" * t
    p = []
    p.append('%s\t<ChoosableMixer name="Transition">' % ind)
    p.append('%s\t\t<VideoMixerStateID uniqueId="%s" />' % (ind, nid()))
    p.append('%s\t</ChoosableMixer>' % ind)
    p.append('%s\t<ClipView name="ClipView">' % ind)
    p.append('%s\t\t<FoldParams name="FoldParams" />' % ind)
    p.append('%s\t</ClipView>' % ind)
    if audio_block:
        p.append(audio_block)
    p.append('%s\t<VideoTrack name="VideoTrack">' % ind)
    p.append('%s\t\t<Params name="Params">' % ind)
    if opacity_block:
        p.append(opacity_block)
    p.append(prange(t + 3, "Width", str(S.WIDTH), str(S.WIDTH)))
    p.append(prange(t + 3, "Height", str(S.HEIGHT), str(S.HEIGHT)))
    for ch in ("RScale", "GScale", "BScale"):
        p.append(pbool(t + 3, ch, True, default="1"))
    p.append(pbool(t + 3, "AScale", ascale, default="1" if ascale else "0"))
    p.append('%s\t\t</Params>' % ind)
    p.append('%s\t\t<RenderPass name="RenderPassChain">' % ind)
    p.append(transform_pass(t + 3))
    p.append('%s\t\t</RenderPass>' % ind)
    p.append('%s\t\t<ChoosableMixer name="Blend">' % ind)
    p.append('%s\t\t\t<VideoMixerStateID uniqueId="%s" />' % (ind, nid()))
    p.append('%s\t\t</ChoosableMixer>' % ind)
    return p


def clip_master(t, name, media_path, layer_index, color_id,
                audio_volume_db=0.0):
    """One full-length master.

    Both path fields carry the identical bare Windows path - PreloadData is
    what Resolume uses to find and relink, VideoFormatReaderSource is what it
    plays. They must agree or a relink half-works.

    EmbeddedThumbnail is deliberately omitted so Resolume regenerates
    thumbnails on first open rather than us shipping stale ones.
    """
    ind = "\t" * t
    p = clip_head(t, name, layer_index, 0, color_id, preload=media_path,
                  with_audio=True)
    p.append(transport_block(t + 1, S.MASTER_SECONDS, S.MASTER_MS))
    p.extend(clip_tail_open(t, None, ascale=False,
                            audio_block=audio_track(t + 1, media_path,
                                                    audio_volume_db)))
    p.append('%s\t\t<PrimarySource>' % ind)
    p.append('%s\t\t\t<VideoSource name="VideoSource" width="%d" height="%d" '
             'type="VideoFormatReaderSource">' % (ind, S.WIDTH, S.HEIGHT))
    p.append('%s\t\t\t\t<VideoFormatReaderSource fileName="%s" />'
             % (ind, esc(media_path)))
    p.append('%s\t\t\t</VideoSource>' % ind)
    p.append('%s\t\t</PrimarySource>' % ind)
    p.append('%s\t</VideoTrack>' % ind)
    p.append('%s</Clip>' % ind)
    return "\n".join(p)


def clip_generator(t, name, gen_type, values, fft_params, layer_index,
                   column_index, color_id):
    """One procedural overlay clip.

    No media file, so nothing to relink, nothing to transcode, and nothing that
    can drift: a generator has no recorded transport to fall out of step with.
    """
    ind = "\t" * t
    tid = S.GENERATOR_LIBRARY[gen_type]
    p = clip_head(t, name, layer_index, column_index, color_id)
    p.append(transport_block(t + 1, 5, 5000))
    p.extend(clip_tail_open(t, prange(t + 3, "Opacity", "1", "1"), ascale=True))
    p.append('%s\t\t<PrimarySource>' % ind)
    p.append('%s\t\t\t<VideoSource storage="0" name="VideoSource" width="%d" '
             'height="%d" type="GeneratorVideoSource">'
             % (ind, S.WIDTH, S.HEIGHT))
    p.append('%s\t\t\t\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" '
             'uniqueId="%s" baseType="Generator">'
             % (ind, gen_type, gen_type, tid, nid()))
    p.append('%s\t\t\t\t\t<Params name="Params">' % ind)
    for pname, val in values.items():
        if pname in fft_params:
            continue
        if pname in ("Text",):
            p.append(ptext(t + 6, pname, val))
        elif "Color" in pname:
            p.append(pcolor(t + 6, pname, val))
        elif pname in ("Mirror", "Animated"):
            p.append(pbool(t + 6, pname, bool(val), default="1"))
        else:
            p.append(prange(t + 6, pname, num(val), num(val)))
    for pname, (band, gain, fall, floor, ceil) in fft_params.items():
        p.append(fft_prange(t + 6, pname, num(values.get(pname, floor)),
                            band, gain, fall, floor, ceil))
    p.append('%s\t\t\t\t\t</Params>' % ind)
    p.append('%s\t\t\t\t</RenderPass>' % ind)
    p.append('%s\t\t\t</VideoSource>' % ind)
    p.append('%s\t\t</PrimarySource>' % ind)
    p.append('%s\t</VideoTrack>' % ind)
    p.append('%s</Clip>' % ind)
    return "\n".join(p)


# --------------------------------------------------------------------------
# Layer
# --------------------------------------------------------------------------
def layer(index, name, blend, opacity, color_id, kind, master_level,
          xfade_group, ignore_column):
    t = 1
    ind = "\t" * t
    p = []
    p.append('%s<Layer name="Layer" uniqueId="%s" layerIndex="%d">'
             % (ind, nid(), index))
    p.append('%s\t<Params name="Params">' % ind)
    p.append('%s\t\t<Param name="Name" T="STRING" default="Layer #" '
             'value="%s" />' % (ind, esc(name)))
    p.append('%s\t\t<ParamChoice name="ColorId" T="INT32" default="0" '
             'value="%d" storeChoices="0" />' % (ind, color_id))
    # CrossFaderGroup 1=A, 2=B. Shape harvested from the live rig: this
    # workspace had never written the param, so it was set through the REST API
    # on a real composition and the XML read back. With the base master on bus
    # A and the alternate on bus B, the APC's physical crossfader is a genuine
    # A/B dissolve and the two layer faders stay free for independent level.
    if xfade_group:
        p.append('%s\t\t<ParamChoice name="CrossFaderGroup" T="INT32" '
                 'default="0" value="%d" storeChoices="0" />'
                 % (ind, xfade_group))
    # Ignore Column Trigger, also harvested live. Set on the OVERLAY layers
    # only. Rig-tested asymmetry: a layer that ignores column triggers ignores
    # ALL of them including the START column, so setting it on the masters
    # would break START BOTH. On the overlays it means the pad grid is the sole
    # authority over overlay content and no column action can disturb it.
    if ignore_column:
        p.append(pbool(t + 2, "Ignore Column Trigger", True))
    # Explicitly OFF. Nothing may auto-fire when the composition is opened -
    # the performer presses START BOTH, and only then.
    p.append(pbool(t + 2, "Trigger first clip on load", False,
                   alt="Trigger First Clip On Play"))
    p.append(prange(t + 2, "Master", "1", num(master_level)))
    p.append('%s\t</Params>' % ind)
    # Duration 0: a transition would mean the two masters do not begin on the
    # same frame.
    p.append('%s\t<ClipTransition name="ClipTransition">' % ind)
    p.append('%s\t\t<Params name="Params">' % ind)
    p.append(prange(t + 3, "Duration", "0", "0"))
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
    # Overlay and scope layers put their opacity on a dashboard link so CLEAN
    # can take them off screen in the same gesture that dries the FX rack. The
    # two masters keep a plain static opacity: CLEAN must never touch picture.
    if kind == S.KIND_OVERLAY:
        p.append(dashboard_link(t + 3, "Opacity", "0.5", "1", 6, "OVERLAYS"))
    elif kind == S.KIND_SCOPE:
        p.append(dashboard_link(t + 3, "Opacity", "0.5", "1", 7, "SCOPE"))
    else:
        p.append(prange(t + 3, "Opacity", "0.5", num(opacity)))
    p.append(prange(t + 3, "Width", str(S.WIDTH), str(S.WIDTH)))
    p.append(prange(t + 3, "Height", str(S.HEIGHT), str(S.HEIGHT)))
    p.append('%s\t\t</Params>' % ind)
    p.append('%s\t\t<RenderPass name="RenderPassChain">' % ind)
    p.append(transform_pass(t + 3))
    p.append('%s\t\t</RenderPass>' % ind)
    p.append(mixer(t + 2, "Blend", blend))
    p.append(mixer(t + 2, "Transition", "Alpha"))
    p.append('%s\t</VideoTrack>' % ind)
    p.append('%s</Layer>' % ind)
    return "\n".join(p)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------
def build(version_a, version_b, use_dxv=False, allow_missing=False):
    path_of = S.master_dxv if use_dxv else S.master_media
    media = {1: path_of(version_a), 2: path_of(version_b)}

    missing = [p for p in media.values() if not os.path.exists(p)]
    if missing and not allow_missing:
        sys.stderr.write("\nMaster media not found:\n")
        for m in missing:
            sys.stderr.write("  %s\n" % m)
        sys.stderr.write("\nRun build/remux_masters.py first, or pass "
                         "--allow-missing to build placeholders anyway.\n")
        raise SystemExit(2)

    # Which FFT parameters belong to which composition-rack effect.
    fft_by_effect = {}
    for (label, eff, param, band, gain, fall, floor, ceil, _why) in S.FFT_MAP:
        fft_by_effect.setdefault(label, {})[param] = (band, gain, fall,
                                                      floor, ceil)

    deck_id = nid()
    p = []
    p.append('<?xml version="1.0" encoding="utf-8"?>')
    p.append('<Composition name="Composition" uniqueId="%s" numDecks="1" '
             'currentDeckIndex="0" numLayers="%d" numColumns="%d" '
             'compositionIsRelative="0">'
             % (nid(), S.NUM_LAYERS, S.NUM_COLUMNS))
    p.append('\t<versionInfo name="%s" majorVersion="%d" minorVersion="%d" '
             'microVersion="%d" revision="%d" />'
             % (S.RES_PRODUCT, S.RES_MAJOR, S.RES_MINOR, S.RES_MICRO,
                S.RES_REV))
    p.append('\t<CompositionInfo name="%s" description="%s" width="%d" '
             'height="%d">' % (
                 esc(S.COMP_NAME),
                 esc("EarthSearch Episode 1 live mix. Two full-length "
                     "masters (A=%s, B=%s) locked at frame zero, five "
                     "generative overlay layers and a live FFT scope. The "
                     "pad grid cannot reach the masters." % (version_a,
                                                             version_b)),
                 S.WIDTH, S.HEIGHT))
    p.append('\t\t<DeckInfo name="%s" id="%s" closed="0" />'
             % (esc(S.DECK_NAME), deck_id))
    p.append('\t</CompositionInfo>')

    p.append('\t<Params name="Params">')
    p.append('\t\t<Param name="Name" T="STRING" default="" value="%s" />'
             % esc(S.COMP_NAME))
    p.append(prange(2, "Speed", "1", "1"))
    p.append('\t\t<Param name="KeyboardShortcutPreset" T="STRING" default="" '
             'value="Default" />')
    p.append('\t\t<Param name="MidiShortcutPreset" T="STRING" default="" '
             'value="%s" />' % esc(S.MIDI_PRESET_NAME))
    p.append('\t\t<Param name="OscShortcutPreset" T="STRING" default="" '
             'value="OutputAllMessages" />')
    p.append('\t</Params>')

    # The eight composition dashboard links. All open at 1 (fully wet) so the
    # instrument is ready; the effects themselves are bypassed, so "wet" costs
    # nothing until a pad is pressed.
    p.append('\t<Params name="Dashboard">')
    for (link_no, label, _what) in S.COMP_DASHBOARD:
        p.append('\t\t<ParamRange name="Link %d" altName="%s" T="DOUBLE" '
                 'default="1" value="1">' % (link_no, esc(label)))
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

    # Composition FX rack - all bypassed on load.
    p.append('\t<VideoTrack name="VideoTrack">')
    p.append('\t\t<Params name="Params">')
    p.append(prange(3, "Width", str(S.WIDTH), str(S.WIDTH)))
    p.append(prange(3, "Height", str(S.HEIGHT), str(S.HEIGHT)))
    p.append('\t\t</Params>')
    p.append('\t\t<RenderPass name="RenderPassChain">')
    p.append(transform_pass(3))
    link_of_bank = {b: n for n, b in S.LINK_BANK.items()}
    for (bank, label, eff_key, values) in S.COMP_RACK:
        p.append(effect_pass(3, label, eff_key, values,
                             link_of_bank[bank],
                             fft_by_effect.get(label)))
    p.append('\t\t</RenderPass>')
    p.append('\t</VideoTrack>')

    for (idx, name, blend, opacity, cid, kind, xg, ign) in S.LAYERS:
        master_level = 1.0 if kind == S.KIND_MASTER else 0.0
        p.append(layer(idx, name, blend, opacity, cid, kind, master_level,
                       xg, ign))

    p.append('\t<CrossFader name="CrossFader">')
    p.append('\t\t<Params name="Params">')
    p.append(prange(3, "Phase", "0", "0"))
    p.append('\t\t</Params>')
    p.append('\t\t<AudioTrack name="AudioTrack">')
    p.append('\t\t\t<AudioEffectChain name="AudioEffectChain" />')
    p.append('\t\t</AudioTrack>')
    p.append('\t\t<VideoTrack name="VideoTrack">')
    p.append('\t\t\t<Params name="Params">')
    p.append(prange(4, "Width", str(S.WIDTH), str(S.WIDTH)))
    p.append(prange(4, "Height", str(S.HEIGHT), str(S.HEIGHT)))
    p.append('\t\t\t</Params>')
    p.append('\t\t\t<RenderPass name="RenderPassChain" />')
    p.append(mixer(3, "Blend mode", "Alpha"))
    p.append('\t\t</VideoTrack>')
    p.append('\t</CrossFader>')
    p.append('\t<TempoController name="TempoController" />')

    # Deck. Column 1 carries the two masters and the scope; columns 1-8 carry
    # the overlay content on layers 3-7.
    p.append('\t<Deck name="Deck" uniqueId="%s" closed="0" '
             'numLayersWithContent="%d" numColumnsWithContent="%d" '
             'numLayers="%d" numColumns="%d" deckIndex="0">'
             % (deck_id, S.NUM_LAYERS, S.NUM_COLUMNS, S.NUM_LAYERS,
                S.NUM_COLUMNS))
    p.append('\t\t<Params name="Params">')
    p.append('\t\t\t<Param name="Name" T="STRING" default="empty" '
             'value="%s" />' % esc(S.DECK_NAME))
    p.append('\t\t</Params>')
    for i, cname in enumerate(S.COLUMN_NAMES):
        p.append('\t\t<Column uniqueId="%s" columnIndex="%d">' % (nid(), i))
        p.append('\t\t\t<Params name="Params">')
        p.append('\t\t\t\t<Param name="Name" T="STRING" default="Column #" '
                 'value="%s" />' % esc(cname))
        p.append('\t\t\t\t<ParamChoice name="ColorId" T="INT32" default="0" '
                 'value="%d" storeChoices="0" />' % (5 if i == 0 else 1))
        p.append('\t\t\t</Params>')
        p.append('\t\t</Column>')

    n_master = n_gen = 0
    # Column-major, matching Resolume's own ordering.
    for col in range(S.NUM_COLUMNS):
        for (idx, name, blend, opacity, cid, kind, _xg, _ign) in S.LAYERS:
            if kind == S.KIND_MASTER:
                if col != 0:
                    continue
                ver = version_a if idx == 0 else version_b
                # A and B carry the SAME programme audio. Both decode, but B's
                # is held at silence: two coherent copies of one mono track can
                # comb-filter at sample level, and the FFT would then be
                # analysing an artefact rather than the score. A is the base
                # layer and always runs, so the analysis source is stable.
                # Unmute B in its clip audio tab if you ever run it alone.
                vol = 0.0 if idx == 0 else -192.0
                p.append(clip_master(2, "%s  %s" % (name, ver),
                                     media[idx + 1], idx, cid,
                                     audio_volume_db=vol))
                n_master += 1
            else:
                clips = S.OVERLAY_CLIPS.get(idx, [])
                if col >= len(clips):
                    continue
                cname, gen, values, fftp = clips[col]
                p.append(clip_generator(2, cname, gen, values, fftp, idx,
                                        col, cid))
                n_gen += 1
    p.append('\t</Deck>')

    p.append('\t<Notes name="Notes">')
    p.append('\t\t<Note text_size_multiplier="2" text_color_index="4" '
             'text="%s" />' % esc(
                 "EarthSearch EP01. PLAY (n91) starts BOTH masters at 00:00. "
                 "STOP ALL CLIPS (n81) stops and resets both. Cue Level knob "
                 "to zero is CLEAN / ALL FX OFF. The 5x8 pad grid addresses "
                 "the five generative overlay layers only - no pad can touch "
                 "either master. FFT is Composition FFT, so it follows the "
                 "programme audio in the masters with no routing."))
    p.append('\t</Notes>')
    p.append('</Composition>')
    p.append('')

    data = "\n".join(p)

    # ---- validation before anything is written ----
    ET.fromstring(data.encode("utf-8"))
    ids = re.findall(r'uniqueId="(\d+)"', data)
    assert len(ids) == len(set(ids)), "duplicate uniqueIds"
    assert data.count("<Layer ") == S.NUM_LAYERS
    assert data.count("<Column ") == S.NUM_COLUMNS
    assert data.count("<Deck ") == 1
    assert n_master == 2, "expected exactly 2 master clips, got %d" % n_master
    assert data.count("VideoFormatReaderSource") == 4, \
        "expected 2 file clips x 2 path fields"
    assert data.count("<PreloadData>") == 2
    assert data.count("EmbeddedThumbnail") == 0
    assert "externalfft" not in data, "must use composition FFT"
    assert data.count('linkId="/audioengine/compositionfft"') == \
        len(S.FFT_MAP) + sum(len(f) for cl in S.OVERLAY_CLIPS.values()
                             for (_n, _g, _v, f) in cl), "FFT node count"
    # Nothing that could disturb playback may carry an FFT phase source.
    # Resolume WILL let you put one on a Transport Position or a Speed - those
    # are ParamRanges like any other - so this is a real check, not a
    # formality. (A generator's own "Position" parameter is a different thing
    # entirely and is legitimately reactive, hence matching on the Transport
    # block rather than on the parameter name.)
    for m in re.finditer(r'<Transport name="Transport">(.*?)</Transport>',
                         data, re.S):
        assert "PhaseSourceFFT" not in m.group(1), "FFT inside a Transport!"
    # Composition Speed and the dashboard live before the first VideoTrack.
    # A generator's own "Speed" parameter is a different thing and is
    # legitimately reactive, so the check is positional, not by name.
    head = data[:data.index("<VideoTrack")]
    assert "PhaseSourceFFT" not in head, "FFT on composition Speed/dashboard!"

    return data, n_master, n_gen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=S.DEFAULT_A, choices=["V2", "V3", "V4"])
    ap.add_argument("--b", default=S.DEFAULT_B, choices=["V2", "V3", "V4"])
    ap.add_argument("--dxv", action="store_true")
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.a == a.b:
        raise SystemExit("A and B must be different masters.")
    if "V4" in (a.a, a.b):
        sys.stderr.write(
            "WARNING: V4 is the hybrid Resolve edit, not a third render. It "
            "is V2's picture for ~95% of the runtime AND it sits on a "
            "different cut grid that runs up to 2.79 s earlier than V2/V3. "
            "Pairing it is not recommended. Building anyway.\n")

    data, n_master, n_gen = build(a.a, a.b, use_dxv=a.dxv,
                                  allow_missing=a.allow_missing)
    out = a.out or os.path.join(S.OUTPUT_DIR, S.COMP_FILE)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(data)

    print("WROTE %s" % out)
    print("  %d bytes | layers=%d columns=%d  masters=%d (A=%s B=%s) "
          "generative=%d  comp effects=%d  FFT nodes=%d"
          % (len(data.encode("utf-8")), S.NUM_LAYERS, S.NUM_COLUMNS,
             n_master, a.a, a.b, n_gen, len(S.COMP_RACK),
             data.count("PhaseSourceFFT")))


if __name__ == "__main__":
    main()
