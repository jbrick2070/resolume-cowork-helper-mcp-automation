# build_telemetry.py - generate "Res React Telemetry.avc" (The Measuring Room).
# NEW FILE ONLY. Reads telemetry_content.py read-only; never touches any
# existing composition or preset. Byte-level latin-1 round trip; non-ASCII text
# is UTF-8 encoded then carried as latin-1, exactly as the Lexicon builds do.
#
# Five decks = five instruments that measure the room's audio. Five layers =
# PAPER / TRACE / NEEDLE / STAMP / READOUT. 200 clips: 185 Text Block cells
# (block-element raster typography), plus per deck one StaticGenerator (SNOW),
# one StroboscopeGenerator (PILOT) and one ShaperGenerator (CAL DIAL) - all
# native sources, no media, no FFGL, no Wire.
#
# Serializer provenance: every emitted block clones a rig-saved donor shape -
# clip wrapper / Text Block / dashboard / FFT / Bloom / WaveWarp from the
# Lexicon II build (itself cloned from rig files), Shaper / Static /
# Stroboscope generator blocks from "Res React Orbit Gen.avc" and "Res React
# Live Gen.avc", Transform-with-params from "APC40_Visual_QA_148.avc".
import os, re, sys, io
import xml.etree.ElementTree as ET
from telemetry_content import DECKS, COLUMNS, GRID

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'compositions', 'Res React Telemetry.avc')
MANIFEST = os.path.join(HERE, '..', 'docs', '_grid_manifest.tsv')
COMP_NAME = 'Res React Telemetry'
MIDI_PRESET = 'APC 40 MK II - Telemetry v1'

# Flip to True and rebuild if the rig font draws boxes for the block glyphs.
ASCII_FALLBACK = False
FALLBACK = {
    '█': '#', '▓': '%', '▒': ':', '░': '.',
    '▁': '_', '▂': '_', '▃': '-', '▄': '-', '▅': '=', '▆': '=', '▇': '#',
    '▀': '-', '▌': '|', '▐': '|', '▛': '+', '▜': '+', '▙': '+', '▟': '+',
    '─': '-', '│': '|', '┼': '+', '╱': '/', '▲': '^', '·': '.', '˙': "'",
    '—': '-', '▸': '>',
}

# ---------------------------------------------------------------- id factory
_id = [1786500000000]
def nid():
    _id[0] += 1
    return str(_id[0])

# ---------------------------------------------------------------- helpers
def u(s):
    """Carry a python str into the latin-1 byte stream as UTF-8 bytes."""
    return s.encode('utf-8').decode('latin-1')

def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))

def abgr(r, g, b, a=255):
    return (a << 24) | (b << 16) | (g << 8) | r

def deglyph(s):
    if not ASCII_FALLBACK:
        return s
    return ''.join(FALLBACK.get(ch, ch) for ch in s)

# ---------------------------------------------------------------- geometry
# (row, blendName, blendType, posY, sizeCap, wrapChars, bandPx, glow, alpha)
ROWS = ['PAPER', 'TRACE', 'NEEDLE', 'STAMP', 'READOUT']   # layer 1..5
LAYERS = {
    'PAPER':   ('Alpha',  'A006',    0.0, 2.20, 44, 880, 0.15, 0xC4),
    'TRACE':   ('Screen', 'A012',  -40.0, 2.00, 34, 420, 0.35, 0xFF),
    'NEEDLE':  ('Screen', 'A012',  180.0, 1.30, 26, 240, 0.35, 0xFF),
    'STAMP':   ('Add',    'A005',  330.0, 2.00, 30, 240, 0.60, 0xFF),
    'READOUT': ('Screen', 'A012', -300.0, 1.20, 26, 220, 0.35, 0xFF),
}

# Text colour per (deck, row) - the five instruments each get a face.
PALETTE = {
 'THE EKG':       {'PAPER': (0x1E, 0x5A, 0x22), 'TRACE': (0x39, 0xFF, 0x14),
                   'NEEDLE': (0xB4, 0xFF, 0x9E), 'STAMP': (0xF0, 0xFF, 0x50),
                   'READOUT': (0xD8, 0xFF, 0xC8)},
 'THE RICHTER':   {'PAPER': (0x6A, 0x5A, 0x40), 'TRACE': (0xF5, 0xE9, 0xD0),
                   'NEEDLE': (0xE0, 0xC8, 0x90), 'STAMP': (0xFF, 0x3C, 0x28),
                   'READOUT': (0xF5, 0xE9, 0xD0)},
 'THE VU':        {'PAPER': (0x5A, 0x46, 0x14), 'TRACE': (0xFF, 0xB0, 0x20),
                   'NEEDLE': (0xFF, 0xD0, 0x60), 'STAMP': (0xFF, 0x2A, 0x2A),
                   'READOUT': (0xFF, 0xE6, 0xA0)},
 'THE POLYGRAPH': {'PAPER': (0x3C, 0x50, 0x6E), 'TRACE': (0x46, 0xA0, 0xFF),
                   'NEEDLE': (0x9E, 0xC8, 0xFF), 'STAMP': (0xFF, 0x30, 0x30),
                   'READOUT': (0xD2, 0xE6, 0xFF)},
 'THE GEIGER':    {'PAPER': (0x50, 0x46, 0x0A), 'TRACE': (0xFF, 0xE0, 0x20),
                   'NEEDLE': (0xFF, 0xF0, 0x8C), 'STAMP': (0xFF, 0x8C, 0x00),
                   'READOUT': (0xFF, 0xF4, 0xC8)},
}

# ---------------------------------------------------------------- typography
CHARS_AT_1 = 28.0
LINE_H_AT_1 = 115.0
SIZE_MIN, SIZE_MAX = 0.5, 10.0      # the source param's own range (rig-read)

def wrap(text, width):
    out, line = [], ''
    for w in text.split(' '):
        if line and len(line) + 1 + len(w) > width:
            out.append(line)
            line = w
        else:
            line = (line + ' ' + w) if line else w
    if line:
        out.append(line)
    return out or ['']

def fit(lines, cap, band):
    longest = max(len(l) for l in lines)
    by_width = CHARS_AT_1 / max(longest, 1)
    by_height = band / (len(lines) * LINE_H_AT_1)
    return round(max(SIZE_MIN, min(cap, by_width, by_height)), 4)

# ---------------------------------------------------------------- audio
# Every deck measures the room differently. (lo, hi, gain dB, fallback ms,
# sweep floor) per (deck, row); None = opacity stays with the hand.
# Per the FFT recipe card: bass PUMPS, mids TRAVEL, highs SPARKLE; +9 only for
# snap cells; floors keep the picture alive with no audio; strobes floor 0.
FFT_TABLE = {
 'THE EKG':       {'PAPER': (0.00, 0.33, 6.0, 1500.0, 0.55),
                   'TRACE': (0.00, 0.25, 9.0, 150.0, 0.12),      # the heartbeat
                   'NEEDLE': None,
                   'STAMP': (0.66, 1.00, 6.0, 200.0, 0.45),
                   'READOUT': None},
 'THE RICHTER':   {'PAPER': (0.00, 0.33, 6.0, 1800.0, 0.55),
                   'TRACE': (0.00, 0.33, 6.0, 1200.0, 0.30),     # ground swell
                   'NEEDLE': (0.33, 0.66, 6.0, 600.0, 0.25),
                   'STAMP': (0.66, 1.00, 6.0, 200.0, 0.45),
                   'READOUT': None},
 'THE VU':        {'PAPER': (0.00, 0.33, 3.0, 1500.0, 0.60),
                   'TRACE': (0.00, 0.33, 6.0, 400.0, 0.15),      # BASS column
                   'NEEDLE': (0.33, 0.66, 6.0, 400.0, 0.15),     # MID column
                   'STAMP': (0.66, 1.00, 6.0, 400.0, 0.15),      # HIGH column
                   'READOUT': None},
 'THE POLYGRAPH': {'PAPER': (0.00, 0.33, 6.0, 1500.0, 0.55),
                   'TRACE': (0.33, 0.66, 6.0, 800.0, 0.25),      # voice = lies
                   'NEEDLE': (0.33, 0.66, 6.0, 600.0, 0.20),
                   'STAMP': (0.66, 1.00, 6.0, 200.0, 0.45),
                   'READOUT': None},
 'THE GEIGER':    {'PAPER': (0.00, 0.33, 6.0, 1500.0, 0.55),
                   'TRACE': (0.33, 0.66, 6.0, 500.0, 0.20),
                   'NEEDLE': None,
                   'STAMP': (0.66, 1.00, 9.0, 100.0, 0.12),      # the clicks
                   'READOUT': None},
}
STROBE_FFT = (0.00, 0.25, 3.0, 100.0, 0.0)   # one per deck, recipe-card law

def ps(indent, link=None):
    t = '\t' * indent
    if link is None:
        return '%s<PhaseSourceStatic name="PhaseSourceStatic"/>' % t
    n, name, phase = link
    return ('%s<DurationSource/>\n'
            '%s<PhaseSourceDashboardLink name="PhaseSourceDashboardLink" phase="%r" '
            'linkId="/link%d" linkName="%s"/>' % (t, t, phase, n, name))

def dashboard_block(dials):
    rows = []
    for i, (name, ph) in enumerate(dials, start=1):
        rows.append(
'\t\t\t\t<ParamRange name="Link %d" altName="%s" T="DOUBLE" default="%r" value="%r">\n'
'\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t</ParamRange>' % (i, name, ph, ph))
    return '\t\t\t<Params name="Dashboard">\n' + '\n'.join(rows) + '\n\t\t\t</Params>'

def fft_opacity(lo, hi, gain, fallback, floor):
    mid = (lo + hi) / 2
    return (
'\t\t\t\t\t<ParamRange name="Opacity" T="DOUBLE" default="1" value="1">\n'
'\t\t\t\t\t\t<DurationSource/>\n'
'\t\t\t\t\t\t<PhaseSourceFFT name="PhaseSourceFFT" phase="0" linkId="/audioengine/externalfft">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t<ParamRange name="FrequencyRange" T="DOUBLE" default="0.5" value="%r">\n'
'\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t\t<ValueRange name="startStop" min="%r" max="%r"/>\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Gain" T="DOUBLE" default="0" value="%r">\n'
'\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Fallback" T="DOUBLE" default="1000" value="%r">\n'
'\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t</PhaseSourceFFT>\n'
'\t\t\t\t\t\t<ValueRange name="startStop" min="%r" max="1"/>\n'
'\t\t\t\t\t</ParamRange>\n' % (mid, lo, hi, gain, fallback, floor))

def opacity_link(link):
    return (
'\t\t\t\t\t<ParamRange name="Opacity" T="DOUBLE" default="1" value="1">\n'
'%s\n'
'\t\t\t\t\t</ParamRange>\n' % ps(6, link))

# ---------------------------------------------------------------- fx passes
def transform_pass(rotz=None, posx=None):
    """Bare clip Transform, optionally with serialized Rotation Z (the CAL
    dial's relative-encoder target) or Position X (the VU column shift).
    Param shapes cloned from APC40_Visual_QA_148.avc."""
    params = []
    if posx is not None:
        params.append(
'\t\t\t\t\t\t\t<ParamRange name="Position X" T="DOUBLE" default="0" value="%r">\n'
'\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t</ParamRange>' % posx)
    if rotz is not None:
        params.append(
'\t\t\t\t\t\t\t<ParamRange name="Rotation Z" T="DOUBLE" default="0" value="%r">\n'
'\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t</ParamRange>' % rotz)
    if params:
        body = ('\t\t\t\t\t\t<Params name="Params">\n%s\n\t\t\t\t\t\t</Params>\n'
                % '\n'.join(params))
    else:
        body = ''
    return ('<RenderPass storage="0" name="Transform" type="TransformEffect" '
            'uniqueTypeId="17122039101699797593" uniqueId="%s" baseType="Effect">\n'
            '%s\t\t\t\t\t\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0"/>\n'
            '\t\t\t\t\t</RenderPass>' % (nid(), body))

def bloom_pass(amount, threshold, size, links=(None, None, None)):
    return (
'<RenderPass storage="0" name="Bloom" type="DryWetEffect" uniqueTypeId="6980402605" uniqueId="%s" baseType="DryWetEffect">\n'
'\t\t\t\t\t\t<RenderPass name="Bloom" type="Bloom" uniqueTypeId="6980402605" uniqueId="%s" baseType="Effect" dwType="Effect">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Amount" T="DOUBLE" default="1" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Threshold" T="DOUBLE" default="0.9000000000000000222" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Size" T="DOUBLE" default="0.25" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t</RenderPass>\n'
'\t\t\t\t\t\t<ChoosableMixer name="Mixer">\n'
'\t\t\t\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t\t\t\t\t<RenderPass name="Alpha" type="Alpha" uniqueTypeId="A006" uniqueId="%s" baseType="Mixer"/>\n'
'\t\t\t\t\t\t</ChoosableMixer>\n'
'\t\t\t\t\t</RenderPass>' % (nid(), nid(), amount, ps(9, links[0]), threshold, ps(9, links[1]), size, ps(9, links[2]), nid(), nid()))

def wavewarp_pass(height, width, speed, links=(None, None, None)):
    return (
'<RenderPass storage="0" name="WaveWarp" type="DryWetEffect" uniqueTypeId="MWWP" uniqueId="%s" baseType="DryWetEffect">\n'
'\t\t\t\t\t\t<RenderPass name="WaveWarp" type="WaveWarp" uniqueTypeId="MWWP" uniqueId="%s" baseType="Effect" dwType="Effect">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Height" T="DOUBLE" default="0.20000000298023223877" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Width" T="DOUBLE" default="0.20000000298023223877" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Speed" T="DOUBLE" default="0.5" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t</RenderPass>\n'
'\t\t\t\t\t\t<ChoosableMixer name="Mixer">\n'
'\t\t\t\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t\t\t\t\t<RenderPass name="Alpha" type="Alpha" uniqueTypeId="A006" uniqueId="%s" baseType="Mixer"/>\n'
'\t\t\t\t\t\t</ChoosableMixer>\n'
'\t\t\t\t\t</RenderPass>' % (nid(), nid(), height, ps(9, links[0]), width, ps(9, links[1]), speed, ps(9, links[2]), nid(), nid()))

def layer_bloom():
    """Bloom on a layer - silent at Amount 0, brightness mappable to a knob."""
    return (
'<RenderPass storage="0" name="Bloom" type="DryWetEffect" uniqueTypeId="6980402605" uniqueId="%s" baseType="DryWetEffect">\n'
'\t\t\t\t\t<RenderPass name="Bloom" type="Bloom" uniqueTypeId="6980402605" uniqueId="%s" baseType="Effect" dwType="Effect">\n'
'\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t<ParamRange name="Amount" T="DOUBLE" default="1" value="0">\n'
'\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t<ParamRange name="Threshold" T="DOUBLE" default="0.9000000000000000222" value="0.4000000000000000222">\n'
'\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t<ParamRange name="Size" T="DOUBLE" default="0.25" value="0.25">\n'
'\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t</RenderPass>\n'
'\t\t\t\t\t<ChoosableMixer name="Mixer">\n'
'\t\t\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t\t\t\t<RenderPass name="Alpha" type="Alpha" uniqueTypeId="A006" uniqueId="%s" baseType="Mixer"/>\n'
'\t\t\t\t\t</ChoosableMixer>\n'
'\t\t\t\t</RenderPass>' % (nid(), nid(), nid(), nid()))

def simple_pass(name, type_id, indent, bypassed=1):
    t = '\t' * indent
    return (
'<RenderPass storage="0" name="%s" type="DryWetEffect" uniqueTypeId="%s" uniqueId="%s" baseType="DryWetEffect">\n'
'%s\t<Params name="Params">\n'
'%s\t\t<Param name="Bypassed" altName="Bypass" T="BOOL" default="0" value="%d"/>\n'
'%s\t</Params>\n'
'%s\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" uniqueId="%s" baseType="Effect" dwType="Effect"/>\n'
'%s\t<ChoosableMixer name="Mixer">\n'
'%s\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'%s\t\t<RenderPass name="Alpha" type="Alpha" uniqueTypeId="A006" uniqueId="%s" baseType="Mixer"/>\n'
'%s\t</ChoosableMixer>\n'
'%s</RenderPass>' % (name, type_id, nid(), t, t, bypassed, t, t, name, name, type_id, nid(),
                     t, t, nid(), t, nid(), t, t))

# The instrument rack. 8 toggles live on the Clip Stop row, Bloom / WaveWarp /
# Tunnel on the Device buttons. ShiftRGB ships ACTIVE at Distance 0 so the
# footswitch stomp works with nothing armed; everything else loads bypassed.
# No Trails and no Freeze anywhere - the infinite-freeze pair stays banned.
COMP_RACK = [
    ('HueRotate',    'A128', 1), ('ShiftRGB',   'A153', 0),
    ('LoRezEffect',  'A142', 1), ('InvertRGB',  'A105', 1),
    ('MirrorQuad',   'A180', 1), ('TwitchEffect', 'A183', 1),
    ('ShiftGlitch',  'MBSH', 1), ('Vignette',   'sy77', 1),
    ('Bloom',        '6980402605', 1), ('WaveWarp', 'MWWP', 1),
    ('Tunnel',       'sy04', 1),
]

# ---------------------------------------------------------------- sources
def color_param(name, rgb, alpha, link):
    """A ParamColor with channel sub-params; Brightness rides dashboard dial 3.
    Channel serialization cloned from the rig-saved TextGenerator donors."""
    r, g, b = rgb
    ci = abgr(r, g, b, alpha)
    ch = []
    for nm, v in (('Red', r / 255.0), ('Green', g / 255.0), ('Blue', b / 255.0)):
        ch.append(
'\t\t\t\t\t\t\t\t\t\t<ParamRange name="%s" T="DOUBLE" default="1" value="%r">\n'
'\t\t\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t\t\t</ParamRange>' % (nm, v))
    ch.append(
'\t\t\t\t\t\t\t\t\t\t<ParamRange name="Brightness" T="DOUBLE" default="1" value="1">\n'
'%s\n'
'\t\t\t\t\t\t\t\t\t\t</ParamRange>' % ps(11, link))
    return (
'<ParamColor name="%s" T="COLOR" default="4294967295" value="%d" channelmode="2" paletteEnabled="0" color="%d" interpolated="0">\n'
'\t\t\t\t\t\t\t\t\t<Params name="Channels">\n'
'%s\n'
'\t\t\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t\t\t</ParamColor>' % (name, ci, ci, '\n'.join(ch)))

def flat_color(name, rgba):
    ci = abgr(*rgba)
    return ('<ParamColor name="%s" T="COLOR" default="4294967295" value="%d" '
            'channelmode="2" paletteEnabled="0" color="%d" interpolated="0"/>'
            % (name, ci, ci))

def source_text(lines, size, posy, glow, rgb, alpha, links):
    """BlockTextGenerator - the Lexicon II donor, verbatim shape."""
    t = '&#10;'.join(esc(u(deglyph(l))) for l in lines)
    return (
'<RenderPass name="BlockTextGenerator" type="BlockTextGenerator" uniqueTypeId="3600113141201236715" uniqueId="%s" baseType="Generator">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t<ParamText name="Text" T="STRING" default="Resolume" value="%s">\n'
'\t\t\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t\t\t<Param name="Lines" T="STRING" default="Resolume" value="%s"/>\n'
'\t\t\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t\t\t</ParamText>\n'
'\t\t\t\t\t\t\t\t%s\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Size" T="DOUBLE" default="1" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Position Y" T="DOUBLE" default="0" value="%r">\n'
'\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamColor name="Outline Color" T="COLOR" default="4278190335" value="0" channelmode="2" paletteEnabled="0" color="0" interpolated="0"/>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Glow Out" T="DOUBLE" default="0" value="%r">\n'
'%s\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t</RenderPass>' % (nid(), t, t,
        color_param('Color', rgb, alpha, links['bright']), size,
        ps(9, links['size']), posy, glow, ps(9, links['glow'])))

def source_static():
    """StaticGenerator - Live Gen donor, all defaults (pure snow)."""
    return ('<RenderPass name="StaticGenerator" type="StaticGenerator" '
            'uniqueTypeId="MSTS" uniqueId="%s" baseType="Generator"/>' % nid())

def source_strobe(c1, c2, link):
    """StroboscopeGenerator - Live Gen donor; Color 1 gets brightness channels."""
    return (
'<RenderPass name="StroboscopeGenerator" type="StroboscopeGenerator" uniqueTypeId="MSTR" uniqueId="%s" baseType="Generator">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t%s\n'
'\t\t\t\t\t\t\t\t%s\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t</RenderPass>' % (nid(),
        color_param('Color 1', c1[:3], c1[3], link), flat_color('Color 2', c2)))

def source_shaper(color, outline, link):
    """ShaperGenerator - Orbit Gen donor; Color gets brightness channels."""
    return (
'<RenderPass name="ShaperGenerator" type="ShaperGenerator" uniqueTypeId="7946640550597690042" uniqueId="%s" baseType="Generator">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t%s\n'
'\t\t\t\t\t\t\t\t%s\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t</RenderPass>' % (nid(),
        color_param('Color', color[:3], color[3], link), flat_color('Outline Color', outline)))

# ---------------------------------------------------------------- clips
CLIP_NAME_DEFAULT = {'text': 'Text Block', 'static': 'Static',
                     'strobe': 'Stroboscope', 'shaper': 'Shaper'}

def clip(deck, row, layer_i, col_i, cell, manifest):
    kind = cell.get('kind', 'text')
    blend, btype, row_posy, row_cap, wrapw, band, glow, alpha = (
        LAYERS[row][0], LAYERS[row][1], LAYERS[row][2], LAYERS[row][3],
        LAYERS[row][4], LAYERS[row][5], LAYERS[row][6], LAYERS[row][7])
    if 'lines' in cell:
        lines = list(cell['lines'])
    elif 'text' in cell:
        lines = wrap(cell['text'], wrapw)
    else:
        lines = ['']
    label = cell.get('label') or lines[0]
    if len(label) > 34:
        label = label[:33] + '…'
    posy = cell.get('posY', row_posy)
    cap = cell.get('cap', row_cap)
    size = fit(lines, cap, band) if kind == 'text' else 1.0

    # FFT: 'row' follows the deck/layer table, 'none' hands opacity to dial 4,
    # 'strobe' is the one narrowed-bass snap cell per deck.
    fmode = cell.get('fft', 'row')
    recipe = FFT_TABLE[deck][row] if fmode == 'row' else (
        STROBE_FFT if fmode == 'strobe' else None)
    is_fft = recipe is not None

    size_phase = round((size - SIZE_MIN) / (SIZE_MAX - SIZE_MIN), 6)
    dial4 = ('Threshold', 0.45) if is_fft else ('Opacity', 1.0)
    dials = [('Size', size_phase), ('Glow Out', glow), ('Brightness', 1.0), dial4,
             ('Amount', 0.18), ('Height', 0.0), ('Width', 0.0), ('Speed', 0.15)]
    Lx = [(i + 1, nm, ph) for i, (nm, ph) in enumerate(dials)]
    links = {'size': Lx[0] if kind == 'text' else None,
             'glow': Lx[1] if kind == 'text' else None,
             'bright': Lx[2] if kind != 'static' else None}

    fx = '\n\t\t\t\t\t'.join([
        transform_pass(rotz=0.0 if kind == 'shaper' else None,
                       posx=cell.get('posX')),
        bloom_pass(0.18, 0.45, 0.18,
                   links=(Lx[4], Lx[3] if is_fft else None, None)),
        wavewarp_pass(0.0, 0.0, 0.15, links=(Lx[5], Lx[6], Lx[7]))])
    dash = dashboard_block(dials)
    if is_fft:
        presence = fft_opacity(*recipe)
    else:
        presence = opacity_link(Lx[3])

    rgb = PALETTE[deck][row]
    if kind == 'text':
        src = source_text(lines, size, posy, glow, rgb, alpha, links)
    elif kind == 'static':
        src = source_static()
    elif kind == 'strobe':
        src = source_strobe(cell['color1'], cell['color2'], links['bright'])
    else:
        src = source_shaper(cell['color'], cell['outline'], links['bright'])

    manifest.append((deck, layer_i + 1, row, col_i + 1, kind, label, size, posy,
                     len(lines), 'fft(%s)' % fmode if is_fft else 'hand'))
    return (
'<Clip name="Clip" uniqueId="%s" layerIndex="%d" columnIndex="%d">\n'
'\t\t\t<Params name="Params">\n'
'\t\t\t\t<Param name="Name" T="STRING" default="%s" value="%s"/>\n'
'\t\t\t\t<ParamChoice name="TransportType" default="0" value="0" storeChoices="0"/>\n'
'\t\t\t</Params>\n'
'%s\n'
'\t\t\t<Transport name="Transport">\n'
'\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t<ParamRange name="Position" T="DOUBLE" default="0" value="0">\n'
'\t\t\t\t\t\t<DurationSource/>\n'
'\t\t\t\t\t\t<PhaseSourceTransportTimeline name="PhaseSourceTransportTimeline" phase="0" defaultBeatsDuration="8">\n'
'\t\t\t\t\t\t\t<Params name="Params">\n'
'\t\t\t\t\t\t\t\t<ParamRange name="Max Distance" altName="Distance" T="DOUBLE" default="2" value="2">\n'
'\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t\t<ValueRange name="minMax" min="0" max="5"/>\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t\t<ParamRange name="BPM" T="DOUBLE" default="120" value="120">\n'
'\t\t\t\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t\t<Beats_double name="Beats_double" numManualBeats="8" detectedTempo="-1"/>\n'
'\t\t\t\t\t\t</PhaseSourceTransportTimeline>\n'
'\t\t\t\t\t\t<ValueRange name="minMax" min="0" max="5000"/>\n'
'\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t</Params>\n'
'\t\t\t</Transport>\n'
'\t\t\t<ChoosableMixer name="Transition">\n'
'\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t</ChoosableMixer>\n'
'\t\t\t<ClipView name="ClipView">\n'
'\t\t\t\t<FoldParams name="FoldParams"/>\n'
'\t\t\t</ClipView>\n'
'\t\t\t<VideoTrack name="VideoTrack">\n'
'\t\t\t\t<Params name="Params">\n'
'%s'
'\t\t\t\t\t<ParamRange name="Width" T="DOUBLE" default="1920" value="1920">\n'
'\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t<ParamRange name="Height" T="DOUBLE" default="1080" value="1080">\n'
'\t\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t\t</ParamRange>\n'
'\t\t\t\t\t<Param name="RScale" T="BOOL" default="1" value="1"/>\n'
'\t\t\t\t\t<Param name="GScale" T="BOOL" default="1" value="1"/>\n'
'\t\t\t\t\t<Param name="BScale" T="BOOL" default="1" value="1"/>\n'
'\t\t\t\t\t<Param name="AScale" T="BOOL" default="1" value="1"/>\n'
'\t\t\t\t</Params>\n'
'\t\t\t\t<RenderPass name="RenderPassChain">\n'
'\t\t\t\t\t%s\n'
'\t\t\t\t</RenderPass>\n'
'\t\t\t\t<ChoosableMixer name="Blend">\n'
'\t\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t\t</ChoosableMixer>\n'
'\t\t\t\t<PrimarySource>\n'
'\t\t\t\t\t<VideoSource storage="0" name="VideoSource" width="1920" height="1080" type="GeneratorVideoSource">\n'
'\t\t\t\t\t\t%s\n'
'\t\t\t\t\t</VideoSource>\n'
'\t\t\t\t</PrimarySource>\n'
'\t\t\t</VideoTrack>\n'
'\t\t</Clip>' % (nid(), layer_i, col_i, CLIP_NAME_DEFAULT[kind],
                 esc(u(deglyph(label))), dash, nid(), presence, fx, nid(), src))

def layer(idx, name, blend_name, blend_type, chain):
    return (
'\t<Layer name="Layer" uniqueId="%s" layerIndex="%d">\n'
'\t\t<Params name="Params">\n'
'\t\t\t<Param name="Name" T="STRING" default="Layer #" value="%s"/>\n'
'\t\t</Params>\n'
'\t\t<ClipTransition name="ClipTransition"/>\n'
'\t\t<LayerView name="LayerView" foldedControl="0">\n'
'\t\t\t<FoldParams name="FoldParams"/>\n'
'\t\t</LayerView>\n'
'\t\t<AudioTrack name="AudioTrack">\n'
'\t\t\t<AudioEffectChain name="AudioEffectChain"/>\n'
'\t\t</AudioTrack>\n'
'\t\t<VideoTrack name="VideoTrack">\n'
'\t\t\t<Params name="Params">\n'
'\t\t\t\t<ParamRange name="Opacity" T="DOUBLE" default="0.5" value="1">\n'
'\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t</ParamRange>\n'
'\t\t\t\t<ParamRange name="Width" T="DOUBLE" default="1920" value="1920">\n'
'\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t</ParamRange>\n'
'\t\t\t\t<ParamRange name="Height" T="DOUBLE" default="1080" value="1080">\n'
'\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t</ParamRange>\n'
'\t\t\t</Params>\n'
'\t\t\t<RenderPass name="RenderPassChain">\n'
'\t\t\t\t%s\n'
'\t\t\t</RenderPass>\n'
'\t\t\t<ChoosableMixer name="Blend">\n'
'\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t\t<RenderPass name="%s" type="%s" uniqueTypeId="%s" uniqueId="%s" baseType="Mixer"/>\n'
'\t\t\t</ChoosableMixer>\n'
'\t\t\t<ChoosableMixer name="Transition">\n'
'\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
'\t\t\t\t<RenderPass name="Alpha" type="Alpha" uniqueTypeId="A006" uniqueId="%s" baseType="Mixer"/>\n'
'\t\t\t</ChoosableMixer>\n'
'\t\t</VideoTrack>\n'
'\t</Layer>' % (nid(), idx, esc(name), chain,
               nid(), blend_name, blend_name, blend_type, nid(), nid(), nid()))

# ---------------------------------------------------------------- assemble
deck_ids = [nid() for _ in DECKS]
parts = []
parts.append('<?xml version="1.0" encoding="utf-8"?>\n')
parts.append('<Composition name="Composition" uniqueId="%s" numDecks="%d" currentDeckIndex="0" '
             'numLayers="5" numColumns="8" compositionIsRelative="0">\n' % (nid(), len(DECKS)))
parts.append('\t<versionInfo name="Resolume Avenue" majorVersion="7" minorVersion="27" microVersion="1" revision="15990"/>\n')
parts.append('\t<CompositionInfo name="%s" description="The Measuring Room: five instruments that measure the party" width="1920" height="1080">\n%s\t</CompositionInfo>\n'
             % (COMP_NAME, ''.join('\t\t<DeckInfo name="%s" id="%s" closed="0"/>\n'
                                   % (esc(u(n)), i) for n, i in zip(DECKS, deck_ids))))
parts.append('\t<Params name="Params">\n'
             '\t\t<Param name="Name" T="STRING" default="" value="%s"/>\n'
             '\t\t<ParamRange name="Speed" T="DOUBLE" default="1" value="1">\n'
             '\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
             '\t\t</ParamRange>\n'
             '\t\t<Param name="KeyboardShortcutPreset" T="STRING" default="" value="Default"/>\n'
             '\t\t<Param name="MidiShortcutPreset" T="STRING" default="" value="%s"/>\n'
             '\t\t<Param name="OscShortcutPreset" T="STRING" default="" value="OutputAllMessages"/>\n'
             '\t</Params>\n' % (COMP_NAME, MIDI_PRESET))
parts.append('\t<CompositionView name="CompositionView">\n'
             '\t\t<FoldParams name="FoldParams">\n'
             '\t\t\t<FoldState component="/compositionpropertiesdashboard" folded="0"/>\n'
             '\t\t</FoldParams>\n'
             '\t</CompositionView>\n')
parts.append('\t<AudioTrack name="AudioTrack">\n\t\t<AudioEffectChain name="AudioEffectChain"/>\n\t</AudioTrack>\n')
parts.append('\t<VideoTrack name="VideoTrack">\n'
             '\t\t<Params name="Params">\n'
             '\t\t\t<ParamRange name="Width" T="DOUBLE" default="1920" value="1920">\n'
             '\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
             '\t\t\t</ParamRange>\n'
             '\t\t\t<ParamRange name="Height" T="DOUBLE" default="1080" value="1080">\n'
             '\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
             '\t\t\t</ParamRange>\n'
             '\t\t</Params>\n'
             '\t\t<RenderPass name="RenderPassChain">\n'
             '\t\t\t<RenderPass storage="0" name="Transform" type="TransformEffect" '
             'uniqueTypeId="17122039101699797593" uniqueId="%s" baseType="Effect">\n'
             '\t\t\t\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0"/>\n'
             '\t\t\t</RenderPass>\n'
             '\t\t\t%s\n'
             '\t\t</RenderPass>\n'
             '\t</VideoTrack>\n' % (nid(), '\n\t\t\t'.join(
                 simple_pass(n, t, 3, bypassed=b) for n, t, b in COMP_RACK)))

for i, row in enumerate(ROWS):
    blend_name, blend_type = LAYERS[row][0], LAYERS[row][1]
    passes = ['<RenderPass storage="0" name="Transform" type="TransformEffect" '
              'uniqueTypeId="17122039101699797593" uniqueId="%s" baseType="Effect">\n'
              '\t\t\t\t\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0"/>\n'
              '\t\t\t\t</RenderPass>' % nid()]
    if i > 0:   # TRACE / NEEDLE / STAMP / READOUT get a mappable Bloom
        passes.append(layer_bloom())
    parts.append(layer(i, row, blend_name, blend_type, '\n\t\t\t\t'.join(passes)) + '\n')

parts.append('\t<CrossFader name="CrossFader">\n'
             '\t\t<Params name="Params">\n'
             '\t\t\t<ParamRange name="Phase" T="DOUBLE" default="0" value="0">\n'
             '\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
             '\t\t\t</ParamRange>\n'
             '\t\t</Params>\n'
             '\t\t<AudioTrack name="AudioTrack">\n\t\t\t<AudioEffectChain name="AudioEffectChain"/>\n\t\t</AudioTrack>\n'
             '\t\t<VideoTrack name="VideoTrack">\n'
             '\t\t\t<Params name="Params">\n'
             '\t\t\t\t<ParamRange name="Width" T="DOUBLE" default="1920" value="1920">\n'
             '\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
             '\t\t\t\t</ParamRange>\n'
             '\t\t\t\t<ParamRange name="Height" T="DOUBLE" default="1080" value="1080">\n'
             '\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
             '\t\t\t\t</ParamRange>\n'
             '\t\t\t</Params>\n'
             '\t\t\t<RenderPass name="RenderPassChain"/>\n'
             '\t\t\t<ChoosableMixer name="Blend mode">\n'
             '\t\t\t\t<VideoMixerStateID uniqueId="%s"/>\n'
             '\t\t\t\t<RenderPass name="Alpha" type="Alpha" uniqueTypeId="A006" uniqueId="%s" baseType="Mixer"/>\n'
             '\t\t\t</ChoosableMixer>\n'
             '\t\t</VideoTrack>\n'
             '\t</CrossFader>\n'
             '\t<TempoController name="TempoController"/>\n' % (nid(), nid()))

manifest = []
for di, deck in enumerate(DECKS):
    parts.append('\t<Deck name="Deck" uniqueId="%s" closed="0" numLayersWithContent="5" '
                 'numColumnsWithContent="8" numLayers="5" numColumns="8" deckIndex="%d">\n'
                 '\t\t<Params name="Params">\n'
                 '\t\t\t<Param name="Name" T="STRING" default="empty" value="%s"/>\n'
                 '\t\t</Params>\n' % (deck_ids[di], di, esc(u(deck))))
    for c, cname in enumerate(COLUMNS[deck]):
        parts.append('\t\t<Column uniqueId="%s" columnIndex="%d">\n'
                     '\t\t\t<Params name="Params">\n'
                     '\t\t\t\t<Param name="Name" T="STRING" default="Column #" value="%s"/>\n'
                     '\t\t\t</Params>\n'
                     '\t\t</Column>\n' % (nid(), c, esc(u(cname))))
    for c in range(8):
        for li, row in enumerate(ROWS):
            cells = GRID[deck][row]
            assert len(cells) == 8, '%s/%s has %d cells' % (deck, row, len(cells))
            parts.append('\t\t' + clip(deck, row, li, c, cells[c], manifest) + '\n')
    parts.append('\t</Deck>\n')

parts.append('\t<Notes name="Notes">\n\t\t<Note text_size_multiplier="2" text_color_index="4" text=""/>\n\t</Notes>\n')
parts.append('</Composition>\n')

data = ''.join(parts)

# ---------------------------------------------------------------- validate
ET.fromstring(data.encode('latin-1'))
ids = re.findall(r'uniqueId="(\d+)"', data)
assert len(ids) == len(set(ids)), 'duplicate uniqueIds'
assert data.count('<Clip ') == 200, 'clip count %d' % data.count('<Clip ')
assert data.count('<Layer ') == 5
assert data.count('<Deck ') == 5
assert data.count('<DeckInfo ') == 5
assert data.count('<Column ') == 40
assert data.count('BlockTextGenerator') == 185 * 2
assert data.count('StaticGenerator') == 5 * 2
assert data.count('StroboscopeGenerator') == 5 * 2
assert data.count('ShaperGenerator') == 5 * 2
assert data.count('<PhaseSourceFFT ') == sum(
    1 for _, _, _, _, _, _, _, _, _, m in manifest if m.startswith('fft'))
assert u('�') not in data
strobes = [m for m in manifest if m[9] == 'fft(strobe)']
assert len(strobes) == 5, 'exactly one strobe cell per deck, got %d' % len(strobes)
open(OUT, 'w', encoding='latin-1', newline='').write(data)

with io.open(MANIFEST, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('deck\tlayer\trow\tcolumn\tkind\tlabel\tsize\tposY\tlines\tpresence\n')
    for deck, li, row, c, kind, label, size, posy, nl, pres in manifest:
        fh.write('%s\t%d\t%s\t%d\t%s\t%s\t%.4f\t%.1f\t%d\t%s\n'
                 % (deck, li, row, c, kind, label, size, posy, nl, pres))

ffts = sum(1 for m in manifest if m[9].startswith('fft'))
print('WROTE %s  %d bytes | clips=%d decks=%d columns=%d uniqueIds=%d'
      % (os.path.normpath(OUT), len(data.encode('latin-1')), data.count('<Clip '),
         data.count('<Deck '), data.count('<Column '), len(ids)))
print('cells: %d text, 5 static, 5 strobe, 5 shaper | %d FFT-driven, %d hand-driven'
      % (185, ffts, 200 - ffts))
print('WROTE %s' % os.path.normpath(MANIFEST))
