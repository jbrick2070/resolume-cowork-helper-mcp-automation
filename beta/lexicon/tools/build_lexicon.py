# build_lexicon.py - generate "Res React Lexicon.avc" from verified donor blocks.
# NEW FILE ONLY. Reads donors read-only; never writes to any existing composition.
# Byte-level latin-1 round trip; non-ASCII text is UTF-8 encoded then carried as latin-1.
import re, sys, json
import xml.etree.ElementTree as ET

OUT = 'Res React Lexicon.avc'
COMP_NAME = 'Res React Lexicon'
MIDI_PRESET = 'APC 40 MK II - Lexicon v1'

# ---------------------------------------------------------------- id factory
_id = [1785200000000]
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
CLEAR = 0
COL = {
    'Field':   abgr(0x7C, 0x8A, 0x9C, 0xC4),
    'Subject': abgr(0xFF, 0xF4, 0xE0, 0xFF),
    'Verb':    abgr(0xFF, 0xB0, 0x20, 0xFF),
    'Object':  abgr(0x46, 0xE0, 0xFF, 0xFF),
    'Mark':    abgr(0xFF, 0x3C, 0xC8, 0xFF),
}

# ---------------------------------------------------------------- content
COLUMNS = ['Carrier', 'Drift', 'Grid', 'Chorus', 'Static', 'Dusk', 'Lattice', 'Null']

# Position Y is in pixels from centre and +Y is DOWN - verified on the rig 2026-07-31.
LAYERS = [
    # (name, blendName, blendType, opacity, size, posY, glow, colorKey)
    ('Field',   'Alpha',  'A006', 1.0, 2.2,    0.0, 0.15, 'Field'),
    ('Subject', 'Screen', 'A012', 1.0, 1.0,  -270.0, 0.35, 'Subject'),
    ('Verb',    'Screen', 'A012', 1.0, 1.15,  -50.0, 0.35, 'Verb'),
    ('Object',  'Screen', 'A012', 1.0, 1.0,   140.0, 0.35, 'Object'),
    ('Mark',    'Add',    'A005', 1.0, 2.4,   330.0, 0.60, 'Mark'),
]

# text[layerIndex][columnIndex] = (pad label, on-screen text)
WORDS = [
    [   # Field - typographic texture, one band of repeating glyphs
        ('Carrier Line',    u('— — — — — — — —')),
        ('Dot Drift',       u('·  ·  ·  ·  ·  ·  ·  ·')),
        ('Plus Grid',       '+  +  +  +  +  +  +  +'),
        ('Paren Chorus',    '(  (  (  (  )  )  )  )'),
        ('Block Static',    u('▓▒░▓▒░▓▒░▓')),
        ('Backslash Dusk',  '\\  \\  \\  \\  \\  \\  \\  \\'),
        ('Hash Lattice',    '#  #  #  #  #  #  #  #'),
        ('Zero Null',       '0  0  0  0  0  0  0  0'),
    ],
    [   # Subject
        ('The Signal',    'THE SIGNAL'),
        ('Every Machine', 'EVERY MACHINE'),
        ('The Chorus',    'THE CHORUS'),
        ('A Slow Comet',  'A SLOW COMET'),
        ('The Archive',   'THE ARCHIVE'),
        ('Nobody',        'NOBODY'),
        ('The Blue Hour', 'THE BLUE HOUR'),
        ('This Circuit',  'THIS CIRCUIT'),
    ],
    [   # Verb
        ('Remembers',  'REMEMBERS'),
        ('Dissolves',  'DISSOLVES'),
        ('Rehearses',  'REHEARSES'),
        ('Forgives',   'FORGIVES'),
        ('Broadcasts', 'BROADCASTS'),
        ('Misreads',   'MISREADS'),
        ('Orbits',     'ORBITS'),
        ('Answers',    'ANSWERS'),
    ],
    [   # Object
        ('The Static',      'THE STATIC'),
        ('A Borrowed Name', 'A BORROWED NAME'),
        ('Every Exit',      'EVERY EXIT'),
        ('The Long Night',  'THE LONG NIGHT'),
        ('Its Own Echo',    'ITS OWN ECHO'),
        ('The First Tape',  'THE FIRST TAPE'),
        ('Nothing At All',  'NOTHING AT ALL'),
        ('The Next Room',   'THE NEXT ROOM'),
    ],
    [   # Mark
        ('Period',    '.'),
        ('Question',  '?'),
        ('Bang',      '!'),
        ('Dash',      u('—')),
        ('Ellipsis',  u('…')),
        ('Parens',    '( )'),
        ('Therefore', '::'),
        ('Slashes',   '///'),
    ],
]


# ---------------------------------------------------------------- dashboard
# Eight dials, identical on all 40 pads, so muscle memory carries across the grid.
# Ranges were read off the rig: Size 0.5-10, everything else 0-1. Position Y is
# +/-32768 and therefore useless on a knob - it is a design constant instead.
DIALS = ['Size', 'Glow Out', 'Amount', 'Size', 'Threshold', 'Height', 'Width', 'Speed']
DIAL_LABELS = ['SIZE', 'GLOW', 'BLOOM', 'HALO', 'THRESH', 'WARP', 'RIPPLE', 'DRIFT']

def ps(indent, link=None):
    """Phase source for a ParamRange: static, or a dashboard link."""
    t = '\t' * indent
    if link is None:
        return '%s<PhaseSourceStatic name="PhaseSourceStatic"/>' % t
    n, name, phase = link
    return ('%s<DurationSource/>\n'
            '%s<PhaseSourceDashboardLink name="PhaseSourceDashboardLink" phase="%r" '
            'linkId="/link%d" linkName="%s"/>' % (t, t, phase, n, name))

def dashboard_block(phases):
    """Clip-level dial bank. default == value == the param's current phase."""
    rows = []
    for i, (name, ph) in enumerate(zip(DIALS, phases), start=1):
        rows.append(
'\t\t\t\t<ParamRange name="Link %d" altName="%s" T="DOUBLE" default="%r" value="%r">\n'
'\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t</ParamRange>' % (i, name, ph, ph))
    return '\t\t\t<Params name="Dashboard">\n' + '\n'.join(rows) + '\n\t\t\t</Params>'

# ---------------------------------------------------------------- audio
# Field and Mark ride an external FFT so the ground breathes and the punctuation
# snaps. The three word rows stay static - the sentence must stay readable.
# Sweep floors are high enough that the comp still reads with no audio connected.
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

COMP_RACK = [('HueRotate', 'A128'), ('ShiftRGB', 'A153'), ('LoRezEffect', 'A142'),
             ('InvertRGB', 'A105'), ('MirrorQuad', 'A180')]


def clip(layer_i, col_i, label, text, size, posy, glow, color):
    size_phase = (size - 0.5) / 9.5          # source Size range is 0.5 - 10
    phases = [size_phase, glow, 0.18, 0.18, 0.45, 0.0, 0.0, 0.15]
    L = [(i + 1, DIALS[i], phases[i]) for i in range(8)]
    fx = '\n\t\t\t\t\t'.join([
        transform_pass(),
        bloom_pass(0.18, 0.45, 0.18, links=(L[2], L[4], L[3])),
        wavewarp_pass(0.0, 0.0, 0.15, links=(L[5], L[6], L[7]))])
    dash = dashboard_block(phases)
    fft = ''
    if layer_i in FFT_LAYERS:
        band, gain, fb, floor = FFT_LAYERS[layer_i]
        fft = fft_opacity(band, gain, fb, floor)
    t = esc(text)
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
'\t\t\t\t\t\t\t\t<ParamColor name="Color" T="COLOR" default="4294967295" value="%d" channelmode="2" paletteEnabled="0" color="%d" interpolated="0"/>\n'
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
'\t\t</Clip>' % (nid(), layer_i, col_i, esc(label), dash, nid(), fft, fx, nid(), nid(),
                 t, t, color, color, size, ps(9, L[0]), posy, glow, ps(9, L[1])))

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
deck_id = nid()
parts = []
parts.append('<?xml version="1.0" encoding="utf-8"?>\n')
parts.append('<Composition name="Composition" uniqueId="%s" numDecks="1" currentDeckIndex="0" '
             'numLayers="5" numColumns="8" compositionIsRelative="0">\n' % nid())
parts.append('\t<versionInfo name="Resolume Avenue" majorVersion="7" minorVersion="27" microVersion="1" revision="15990"/>\n')
parts.append('\t<CompositionInfo name="%s" description="APC40 wordplay instrument - every pad is a word" width="1920" height="1080">\n'
             '\t\t<DeckInfo name="Lexicon" id="%s" closed="0"/>\n'
             '\t</CompositionInfo>\n' % (COMP_NAME, deck_id))
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

# ---- deck
parts.append('\t<Deck name="Deck" uniqueId="%s" closed="0" numLayersWithContent="5" '
             'numColumnsWithContent="8" numLayers="5" numColumns="8" deckIndex="0">\n'
             '\t\t<Params name="Params">\n'
             '\t\t\t<Param name="Name" T="STRING" default="empty" value="Lexicon"/>\n'
             '\t\t</Params>\n' % deck_id)
for c, cname in enumerate(COLUMNS):
    parts.append('\t\t<Column uniqueId="%s" columnIndex="%d">\n'
                 '\t\t\t<Params name="Params">\n'
                 '\t\t\t\t<Param name="Name" T="STRING" default="Column #" value="%s"/>\n'
                 '\t\t\t</Params>\n'
                 '\t\t</Column>\n' % (nid(), c, esc(cname)))
for c in range(8):
    for li, (nm, bn, bt, op, size, posy, glow, ckey) in enumerate(LAYERS):
        label, text = WORDS[li][c]
        parts.append('\t\t' + clip(li, c, label, text, size, posy, glow, COL[ckey]) + '\n')
parts.append('\t</Deck>\n')
parts.append('\t<Notes name="Notes">\n\t\t<Note text_size_multiplier="2" text_color_index="4" text=""/>\n\t</Notes>\n')
parts.append('</Composition>\n')

data = ''.join(parts)

# ---------------------------------------------------------------- validate
ET.fromstring(data.encode('latin-1'))
ids = re.findall(r'uniqueId="(\d+)"', data)
assert len(ids) == len(set(ids)), 'duplicate uniqueIds'
assert data.count('<Clip ') == 40, 'clip count %d' % data.count('<Clip ')
assert data.count('<Layer ') == 5
assert data.count('<Column ') == 8
assert data.count('BlockTextGenerator') == 40 * 2
assert '�' not in data
open(OUT, 'w', encoding='latin-1', newline='').write(data)
print('WROTE %s  %d bytes | clips=%d layers=%d columns=%d uniqueIds=%d'
      % (OUT, len(data.encode('latin-1')), data.count('<Clip '), data.count('<Layer '),
         data.count('<Column '), len(ids)))
