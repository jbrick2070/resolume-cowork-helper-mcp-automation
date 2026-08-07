# build_lexicon2.py - generate "Res React Lexicon II.avc" (Eighties-ism pack).
# NEW FILE ONLY. Reads TERMS_SOURCE.txt + lexicon2_content.py read-only; never
# writes to any existing composition or preset. Byte-level latin-1 round trip;
# non-ASCII text is UTF-8 encoded then carried as latin-1, as in v1.
#
# v1 was a grammar machine with invented words. v2 keeps the machine - five rows
# = SUBJECT / VERB / OBJECT / MARK / FIELD, eight pads per row - and feeds it the
# supplied found-text corpus, sliced, plus added broadcast-age vocabulary:
#
#   5 decks x 5 layers x 8 columns = 200 clips, all Text Block generators.
#   Deck 1 MASTER    - every register mushed together (the good one)
#   Deck 2 AD BREAK  - consumer broadcast        Deck 4 THE REEL - film language
#   Deck 3 THE SERMON- truisms and commandments  Deck 5 LA NUIT  - French wordplay
#
# The build asserts that EVERY included term in TERMS_SOURCE.txt appears on the
# grid, whole or as a verbatim cut. No PNG thumbnails - true text generators only.
import re, sys, io
import xml.etree.ElementTree as ET
from lexicon2_content import DECKS, COLUMNS, GRID

OUT = 'Res React Lexicon II.avc'
COMP_NAME = 'Res React Lexicon II'
MIDI_PRESET = 'APC 40 MK II - Lexicon v2'
TERMS = 'TERMS_SOURCE.txt'

# ---------------------------------------------------------------- id factory
_id = [1786100000000]
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

# ---------------------------------------------------------------- palette
# Unchanged from v1: pad LEDs and screen already agree, muscle memory carries.
RGB = {
    'Field':   (0x7C, 0x8A, 0x9C, 0xC4),
    'Subject': (0xFF, 0xF4, 0xE0, 0xFF),
    'Verb':    (0xFF, 0xB0, 0x20, 0xFF),
    'Object':  (0x46, 0xE0, 0xFF, 0xFF),
    'Mark':    (0xFF, 0x3C, 0xC8, 0xFF),
}
COL = {k: abgr(*v) for k, v in RGB.items()}

# ---------------------------------------------------------------- typography
# At Text Block Size 1.0 roughly CHARS_AT_1 characters span the 1920 frame and a
# line occupies LINE_H_AT_1 px. Every clip's Size derives from these, so a Vertov
# manifesto and the word HEAT both land inside their band. Retune here, rebuild.
CHARS_AT_1 = 28.0
LINE_H_AT_1 = 115.0
SIZE_MIN, SIZE_MAX = 0.5, 10.0      # the source param's own range (rig-read)

# Position Y is pixels from centre and +Y is DOWN - verified on the rig 2026-07-31.
# (name, blendName, blendType, opacity, posY, sizeCap, wrapChars, bandPx, glow)
LAYERS = [
    ('Field',   'Alpha',  'A006', 1.0,    0.0, 2.20, 44, 880, 0.15),
    ('Subject', 'Screen', 'A012', 1.0, -270.0, 1.35, 22, 260, 0.35),
    ('Verb',    'Screen', 'A012', 1.0,  -50.0, 1.20, 26, 220, 0.35),
    ('Object',  'Screen', 'A012', 1.0,  140.0, 1.20, 26, 260, 0.35),
    ('Mark',    'Add',    'A005', 1.0,  330.0, 2.00, 30, 240, 0.60),
]
ROWS = ['Subject', 'Verb', 'Object', 'Mark', 'Field']   # reading order
LAYER_OF = {'Field': 0, 'Subject': 1, 'Verb': 2, 'Object': 3, 'Mark': 4}

def wrap(text, width):
    """Greedy word wrap; never splits a word."""
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
    """Largest Size keeping the longest line inside the frame and the block
    inside its band."""
    longest = max(len(l) for l in lines)
    by_width = CHARS_AT_1 / max(longest, 1)
    by_height = band / (len(lines) * LINE_H_AT_1)
    return round(max(SIZE_MIN, min(cap, by_width, by_height)), 4)

# ---------------------------------------------------------------- term audit
def norm(s):
    s = s.casefold()
    for a, b in (('’', "'"), ('‘', "'"), ('–', '-'), ('—', '-'),
                 ('…', '...')):
        s = s.replace(a, b)
    return ' '.join(s.split())

def load_terms():
    inc, exc = [], []
    for ln in io.open(TERMS, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if not ln.strip() or ln.startswith('#'):
            continue
        if ln.startswith('-'):
            exc.append(tuple(ln[1:].split('\t', 1)))
        else:
            inc.append(ln)
    return inc, exc

INCLUDED, EXCLUDED = load_terms()
INC_SET = set(INCLUDED)

cells = []          # (deck, row, col, text, src)
for d in DECKS:
    for r in ROWS:
        row = GRID[d][r]
        assert len(row) == 8, '%s/%s has %d cells' % (d, r, len(row))
        for c, (text, src) in enumerate(row):
            cells.append((d, r, c, text, src))
assert len(cells) == 200

bad_src = sorted({s for _, _, _, _, s in cells if s is not None and s not in INC_SET})
assert not bad_src, 'cell srcs not in TERMS_SOURCE included list:\n  ' + '\n  '.join(bad_src)
bad_cut = [(d, r, c, t) for d, r, c, t, s in cells
           if s is not None and norm(t) not in norm(s)]
assert not bad_cut, 'cells that are not verbatim cuts of their src:\n  ' + \
    '\n  '.join('%s/%s/%d: %r' % x for x in bad_cut)
covered = {s for _, _, _, _, s in cells if s is not None}
missing = [t for t in INCLUDED if t not in covered]
assert not missing, '%d terms not covered by any cell:\n  ' % len(missing) + \
    '\n  '.join(missing)

# ---------------------------------------------------------------- dashboard
# Eight dials on every pad. 1-3 and 5-8 are identical everywhere; dial 4 is
# FADE (clip opacity) on the word rows and THRESH (bloom threshold) on Field and
# Mark, whose opacity belongs to the FFT. altNames are written per clip, so the
# software labels each dial correctly either way.
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

# ---------------------------------------------------------------- audio
# Field rides the bass, Mark rides the highs - the ground breathes, the stamp
# snaps. Subject/Verb/Object stay static: the sentence must stay readable no
# matter what the music does. Sweep floors keep both rows visible with no audio.
FFT_BANDS = {'bass': (0.0, 0.33), 'mids': (0.33, 0.66), 'highs': (0.66, 1.0)}

def fft_opacity(band, gain, fallback, floor):
    lo, hi = FFT_BANDS[band]
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
    """Word rows: clip opacity on dashboard dial 4 (FADE)."""
    return (
'\t\t\t\t\t<ParamRange name="Opacity" T="DOUBLE" default="1" value="1">\n'
'%s\n'
'\t\t\t\t\t</ParamRange>\n' % ps(6, link))

# layerIndex -> (band, gain, fallback ms, sweep floor)
FFT_LAYERS = {0: ('bass', 6.0, 800.0, 0.55), 4: ('highs', 6.0, 200.0, 0.45)}

# ---------------------------------------------------------------- templates
def transform_pass():
    return ('<RenderPass storage="0" name="Transform" type="TransformEffect" '
            'uniqueTypeId="17122039101699797593" uniqueId="%s" baseType="Effect">\n'
            '\t\t\t\t\t\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0"/>\n'
            '\t\t\t\t\t</RenderPass>' % nid())

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
    """Bloom on a text layer - silent at Amount 0, mappable to a device knob."""
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

# No Trails and no Freeze at composition level - that pair caused the
# infinite-freeze lock-up before. Carried over from v1.
COMP_RACK = [('HueRotate', 'A128'), ('ShiftRGB', 'A153'), ('LoRezEffect', 'A142'),
             ('InvertRGB', 'A105'), ('MirrorQuad', 'A180')]

def color_param(ckey, link):
    """Text colour with channel sub-params; Brightness rides dashboard dial 3."""
    r, g, b, a = RGB[ckey]
    ci = COL[ckey]
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
'<ParamColor name="Color" T="COLOR" default="4294967295" value="%d" channelmode="2" paletteEnabled="0" color="%d" interpolated="0">\n'
'\t\t\t\t\t\t\t\t\t<Params name="Channels">\n'
'%s\n'
'\t\t\t\t\t\t\t\t\t</Params>\n'
'\t\t\t\t\t\t\t\t</ParamColor>' % (ci, ci, '\n'.join(ch)))

def clip(layer_i, col_i, label, lines, size, posy, glow, ckey):
    is_fft = layer_i in FFT_LAYERS
    size_phase = round((size - SIZE_MIN) / (SIZE_MAX - SIZE_MIN), 6)
    dial4 = ('Threshold', 0.45) if is_fft else ('Opacity', 1.0)
    dials = [('Size', size_phase), ('Glow Out', glow), ('Brightness', 1.0), dial4,
             ('Amount', 0.18), ('Height', 0.0), ('Width', 0.0), ('Speed', 0.15)]
    L = [(i + 1, nm, ph) for i, (nm, ph) in enumerate(dials)]
    fx = '\n\t\t\t\t\t'.join([
        transform_pass(),
        bloom_pass(0.18, 0.45, 0.18,
                   links=(L[4], L[3] if is_fft else None, None)),
        wavewarp_pass(0.0, 0.0, 0.15, links=(L[5], L[6], L[7]))])
    dash = dashboard_block(dials)
    if is_fft:
        band, gain, fb, floor = FFT_LAYERS[layer_i]
        presence = fft_opacity(band, gain, fb, floor)
    else:
        presence = opacity_link(L[3])
    t = '&#10;'.join(esc(u(l)) for l in lines)
    return (
'<Clip name="Clip" uniqueId="%s" layerIndex="%d" columnIndex="%d">\n'
'\t\t\t<Params name="Params">\n'
'\t\t\t\t<Param name="Name" T="STRING" default="Text Block" value="%s"/>\n'
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
'\t\t\t\t\t\t<RenderPass name="BlockTextGenerator" type="BlockTextGenerator" uniqueTypeId="3600113141201236715" uniqueId="%s" baseType="Generator">\n'
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
'\t\t\t\t\t\t</RenderPass>\n'
'\t\t\t\t\t</VideoSource>\n'
'\t\t\t\t</PrimarySource>\n'
'\t\t\t</VideoTrack>\n'
'\t\t</Clip>' % (nid(), layer_i, col_i, esc(u(label)), dash, nid(), presence, fx,
                 nid(), nid(), t, t, color_param(ckey, L[2]), size, ps(9, L[0]),
                 posy, glow, ps(9, L[1])))

def layer(idx, name, blend_name, blend_type, opacity, chain):
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
'\t\t\t\t<ParamRange name="Opacity" T="DOUBLE" default="0.5" value="%r">\n'
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
'\t</Layer>' % (nid(), idx, esc(name), opacity, chain,
               nid(), blend_name, blend_name, blend_type, nid(), nid(), nid()))

# ---------------------------------------------------------------- assemble
deck_ids = [nid() for _ in DECKS]
parts = []
parts.append('<?xml version="1.0" encoding="utf-8"?>\n')
parts.append('<Composition name="Composition" uniqueId="%s" numDecks="%d" currentDeckIndex="0" '
             'numLayers="5" numColumns="8" compositionIsRelative="0">\n' % (nid(), len(DECKS)))
parts.append('\t<versionInfo name="Resolume Avenue" majorVersion="7" minorVersion="27" microVersion="1" revision="15990"/>\n')
parts.append('\t<CompositionInfo name="%s" description="Eighties-ism: 120 found texts on the APC40, sliced and channel-surfed" width="1920" height="1080">\n%s\t</CompositionInfo>\n'
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
                 simple_pass(n, t, 3) for n, t in COMP_RACK)))

for i, (nm, bn, bt, op, *_rest) in enumerate(LAYERS):
    passes = ['<RenderPass storage="0" name="Transform" type="TransformEffect" '
              'uniqueTypeId="17122039101699797593" uniqueId="%s" baseType="Effect">\n'
              '\t\t\t\t\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0"/>\n'
              '\t\t\t\t</RenderPass>' % nid()]
    if i > 0:   # text layers get a mappable Bloom, silent until dialed up
        passes.append(layer_bloom())
    parts.append(layer(i, nm, bn, bt, op, '\n\t\t\t\t'.join(passes)) + '\n')

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
        for row_name in ('Field', 'Subject', 'Verb', 'Object', 'Mark'):
            li = LAYER_OF[row_name]
            spec = LAYERS[li]
            posy, cap, wrapw, band, glow = spec[4], spec[5], spec[6], spec[7], spec[8]
            text, src = GRID[deck][row_name][c]
            lines = wrap(text, wrapw)
            size = fit(lines, cap, band)
            y = posy
            if row_name == 'Mark' and len(lines) > 1:
                y = posy - (len(lines) - 1) * 55.0     # keep tall stamps on screen
            label = text if len(text) <= 34 else text[:33] + '…'
            parts.append('\t\t' + clip(li, c, label, lines, size, y, glow, row_name) + '\n')
            manifest.append((di, deck, li, row_name, c, COLUMNS[deck][c],
                             text, src, size, y, len(lines)))
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
assert data.count('BlockTextGenerator') == 200 * 2
assert u('�') not in data
open(OUT, 'w', encoding='latin-1', newline='').write(data)

with io.open('_grid_manifest.tsv', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('deckIndex\tdeck\tlayerIndex\trow\tcolumnIndex\tcolumn\tsize\tposY\tlines\tsrc\ttext\n')
    for di, deck, li, nm, c, cn, text, src, size, y, nl in manifest:
        fh.write('%d\t%s\t%d\t%s\t%d\t%s\t%.4f\t%.1f\t%d\t%s\t%s\n'
                 % (di, deck, li, nm, c, cn, size, y, nl,
                    'ADDED' if src is None else src, text))

added = sum(1 for _, _, _, _, s in cells if s is None)
print('WROTE %s  %d bytes | clips=%d decks=%d columns=%d uniqueIds=%d'
      % (OUT, len(data.encode('latin-1')), data.count('<Clip '),
         data.count('<Deck '), data.count('<Column '), len(ids)))
print('coverage: %d/%d source terms on the grid | %d cells verbatim cuts, %d added 80s words'
      % (len(covered & INC_SET), len(INCLUDED), 200 - added, added))
print('excluded: ' + ', '.join('%s (%s)' % (t, r) for r, t in EXCLUDED))
print('WROTE _grid_manifest.tsv')
