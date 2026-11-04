#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_film_layer.py - put the 20 Sume/HeyGen clips under the Studio One instrument.

Takes the built composition and its APC40 preset and writes a FILM edition:
  * a ninth layer, FILM, at the very bottom (layer 1), Alpha blend, crossfader
    side A, so BED (Add) and everything above it composite on top of the film;
  * one video clip per rendered scene in the matching deck column, 5.17 s,
    Play Mode = Ping Pong so every clip loops without a cut;
  * every existing layer and clip shifted up one index, and every layer path in
    the MIDI preset shifted the same way, so the APC40 plays exactly as before.

    python packs/studio-one/add_film_layer.py

Reads  packs/studio-one/media/S1_<deck>_<scene>_<slug>.mov (Alley DXV) or .mp4
Copies them to C:\\Resolume Clips\\studio_one and points the composition there
Writes packs/studio-one/Studio One - War Of The Worlds 1938 FILM.avc
       packs/studio-one/APC 40 MK II - Studio One FILM.xml
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from resolume_build import avc as AVC  # noqa: E402

AVC_IN = os.path.join(HERE, "Studio One - War Of The Worlds 1938.avc")
AVC_OUT = os.path.join(HERE, "Studio One - War Of The Worlds 1938 FILM.avc")
PRESET_IN = os.path.join(HERE, "APC 40 MK II - Studio One.xml")
PRESET_OUT = os.path.join(HERE, "APC 40 MK II - Studio One FILM.xml")
PRESET_NAME = "APC 40 MK II - Studio One FILM"
PRESET_ID = "2026110301"
MEDIA = os.path.join(HERE, "media")              # the repo's copy
LIBRARY = r"C:\Resolume Clips\studio_one"        # the performer's clip library: the composition points here
ID_BASE = 1792000800000          # clear of the builder's 1792000000000.. and preset 1792000900000..
W, H = 1920, 1080
PLAY_MODE_PING_PONG = 1          # Transport PlayMode: 0 Loop, 1 Ping Pong, 2 Play Once


def probe_seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout
    return float(out.strip() or 5.0)


class _Comp(object):
    """Just enough of AVC.Composition for Layer.xml()."""
    width, height = W, H
    dashboard = []


def film_layer_xml(ids):
    layer = AVC.Layer(_Comp(), 0, "FILM", "Alpha", 1.0, None, crossfader=1,
                      ignore_column=False, master=1.0, color_id=4, transition_ms=150)
    return layer.xml(ids)


def transport_xml(t, seconds):
    ind = "\t" * t
    ms = seconds * 1000.0
    return (
        '%s<Transport name="Transport">\n'
        '%s\t<Params name="Params">\n'
        '%s\t\t<ParamRange name="Position" T="DOUBLE" default="0" value="0">\n'
        '%s\t\t\t<DurationSource defaultDuration="%.9fs" />\n'
        '%s\t\t\t<PhaseSourceTransportTimeline name="PhaseSourceTransportTimeline" phase="0" '
        'defaultMillisecondsDuration="%.6f" defaultBeatsDuration="8">\n'
        '%s\t\t\t\t<Params name="Params">\n'
        '%s\t\t\t\t\t<ParamRange name="Max Distance" altName="Distance" T="DOUBLE" '
        'default="%.9f" value="2">\n'
        '%s\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t\t\t\t<ValueRange name="minMax" min="0" max="%.9f" />\n'
        '%s\t\t\t\t\t</ParamRange>\n'
        '%s\t\t\t\t\t<ParamRange name="BPM" T="DOUBLE" default="120" value="120">\n'
        '%s\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic" />\n'
        '%s\t\t\t\t\t</ParamRange>\n'
        '%s\t\t\t\t\t<ParamChoice name="PlayMode" T="INT32" default="0" value="%d" storeChoices="0" />\n'
        '%s\t\t\t\t</Params>\n'
        '%s\t\t\t\t<Beats_double name="Beats_double" numManualBeats="8" detectedTempo="-1" />\n'
        '%s\t\t\t</PhaseSourceTransportTimeline>\n'
        '%s\t\t\t<ValueRange name="minMax" min="0" max="%.6f" />\n'
        '%s\t\t</ParamRange>\n'
        '%s\t</Params>\n'
        '%s</Transport>'
        % (ind, ind, ind, ind, seconds, ind, ms, ind, ind, seconds, ind, ind, seconds, ind,
           ind, ind, ind, ind, PLAY_MODE_PING_PONG, ind, ind, ind, ind, ms, ind, ind, ind))


def film_clip_xml(ids, column, name, path, seconds, t=2):
    """A picture-only video clip on layer 0, the shape avc.Clip writes for file clips."""
    ind = "\t" * t
    e = AVC.esc
    p = ['%s<Clip name="Clip" uniqueId="%s" layerIndex="0" columnIndex="%d">' % (ind, ids(), column)]
    p.append('%s\t<PreloadData>' % ind)
    p.append('%s\t\t<VideoFile value="%s" />' % (ind, e(path)))
    p.append('%s\t</PreloadData>' % ind)
    p.append('%s\t<Params name="Params">' % ind)
    p.append('%s\t\t<Param name="Name" T="STRING" default="%s" value="%s" />' % (ind, e(name), e(name)))
    p.append('%s\t\t<ParamChoice name="TransportType" default="0" value="0" storeChoices="0" />' % ind)
    p.append('%s\t\t<ParamChoice name="ColorId" T="INT32" default="0" value="4" storeChoices="0" />' % ind)
    p.append('%s\t</Params>' % ind)
    p.append(transport_xml(t + 1, seconds))
    p.append('%s\t<ChoosableMixer name="Transition">' % ind)
    p.append('%s\t\t<VideoMixerStateID uniqueId="%s" />' % (ind, ids()))
    p.append('%s\t</ChoosableMixer>' % ind)
    p.append('%s\t<ClipView name="ClipView">' % ind)
    p.append('%s\t\t<FoldParams name="FoldParams" />' % ind)
    p.append('%s\t</ClipView>' % ind)
    p.append('%s\t<VideoTrack name="VideoTrack">' % ind)
    p.append('%s\t\t<Params name="Params">' % ind)
    p.append(AVC.prange(t + 3, "Opacity", 1, 1.0))
    p.append(AVC.prange(t + 3, "Width", W, W))
    p.append(AVC.prange(t + 3, "Height", H, H))
    for ch in ("RScale", "GScale", "BScale", "AScale"):
        p.append(AVC.pbool(t + 3, ch, True, default=True))
    p.append('%s\t\t</Params>' % ind)
    p.append('%s\t\t<RenderPass name="RenderPassChain">' % ind)
    p.append(AVC.transform_pass(t + 3, ids))
    p.append('%s\t\t</RenderPass>' % ind)
    p.append(AVC.mixer(t + 2, ids, "Blend", "Alpha"))
    p.append('%s\t\t<PrimarySource>' % ind)
    p.append('%s\t\t\t<VideoSource name="VideoSource" width="%d" height="%d" '
             'type="VideoFormatReaderSource">' % (ind, W, H))
    p.append('%s\t\t\t\t<VideoFormatReaderSource fileName="%s" />' % (ind, e(path)))
    p.append('%s\t\t\t</VideoSource>' % ind)
    p.append('%s\t\t</PrimarySource>' % ind)
    p.append('%s\t</VideoTrack>' % ind)
    p.append('%s</Clip>' % ind)
    return "\n".join(p)


def scene_clips():
    """{deck_index: [(column_index, clip_name, abs_path, seconds), ...]}"""
    out = {}
    names = os.listdir(MEDIA)
    for fn in sorted(names):
        m = re.match(r"S1_(\d)_(\d)_([a-z0-9_]+)\.(mp4|mov)$", fn, re.I)
        if not m:
            continue
        # prefer Alley's DXV .mov over the H.264 .mp4 when both exist
        if m.group(4).lower() == "mp4" and any(n.lower() == fn[:-4].lower() + ".mov" for n in names):
            continue
        deck, col, slug = int(m.group(1)) - 1, int(m.group(2)) - 1, m.group(3)
        src = os.path.join(MEDIA, fn)
        os.makedirs(LIBRARY, exist_ok=True)
        path = os.path.normpath(os.path.join(LIBRARY, fn))   # backslashes, as Avenue writes them
        if (not os.path.exists(path) or os.path.getsize(path) != os.path.getsize(src)
                or os.path.getmtime(path) < os.path.getmtime(src)):
            shutil.copy2(src, path)
        name = "Film " + slug.replace("_", " ").title()
        out.setdefault(deck, []).append((col, name[:18], path, probe_seconds(path)))
    return out


def main():
    src = open(AVC_IN, encoding="utf-8").read()
    ids = AVC._Ids(ID_BASE)
    clips = scene_clips()
    n_total = sum(len(v) for v in clips.values())

    # 1. shift every existing layer and clip up one index
    def bump(m):
        return '%slayerIndex="%d"' % (m.group(1), int(m.group(2)) + 1)
    xml = re.sub(r'(<(?:Layer|Clip) name="(?:Layer|Clip)" uniqueId="\d+" )layerIndex="(\d+)"', bump, src)
    n_layers = len(re.findall(r'<Layer name="Layer" ', xml))
    assert n_layers == 8, n_layers
    xml = xml.replace('numLayers="8"', 'numLayers="9"').replace('numLayersWithContent="8"',
                                                              'numLayersWithContent="9"')
    xml = xml.replace('value="APC 40 MK II - Studio One" />', 'value="%s" />' % PRESET_NAME, 1)

    # 2. the FILM layer goes in front of layer 1 (now layer 2)
    first_layer = xml.index('\t<Layer name="Layer" ')
    xml = xml[:first_layer] + film_layer_xml(ids) + "\n" + xml[first_layer:]

    # 3. the clips: in each deck, after its <Column> elements, before its first <Clip>
    def splice_deck(m):
        deck_xml = m.group(0)
        deck_index = int(m.group(1))
        rows = clips.get(deck_index, [])
        if not rows:
            return deck_xml
        at = deck_xml.index('\t\t<Clip name="Clip" ')
        block = "\n".join(film_clip_xml(ids, col, name, path, secs) for col, name, path, secs in rows)
        return deck_xml[:at] + block + "\n" + deck_xml[at:]
    xml = re.sub(r'\t<Deck name="Deck" uniqueId="\d+" [^>]*deckIndex="(\d)">.*?\n\t</Deck>',
                 splice_deck, xml, flags=re.S)
    assert xml.count('<VideoFormatReaderSource ') == n_total, (xml.count('<VideoFormatReaderSource '), n_total)
    with open(AVC_OUT, "w", encoding="utf-8", newline="") as f:
        f.write(xml)

    # 4. the preset: every /composition/layers/N/ path moves to N+1
    pre = open(PRESET_IN, encoding="utf-8").read()
    pre2 = re.sub(r'(/composition/layers/)(\d+)/', lambda m: "%s%d/" % (m.group(1), int(m.group(2)) + 1), pre)
    pre2 = pre2.replace('presetId="2026102302" name="APC 40 MK II - Studio One"',
                        'presetId="%s" name="%s"' % (PRESET_ID, PRESET_NAME), 1)
    assert PRESET_NAME in pre2[:400], "preset header not renamed"
    with open(PRESET_OUT, "w", encoding="utf-8", newline="") as f:
        f.write(pre2)

    print("film clips:", n_total, "in decks", sorted(clips))
    print("layers:", xml.count('<Layer name="Layer" '), " clips:", xml.count('<Clip name="Clip" '))
    print("preset layer refs:", sorted(set(re.findall(r'layers/(\d+)/', pre2)), key=int))
    print("WROTE", AVC_OUT)
    print("WROTE", PRESET_OUT)


if __name__ == "__main__":
    main()
