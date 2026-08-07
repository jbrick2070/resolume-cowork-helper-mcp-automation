# build_testcard.py - generate "Res React Test Card.avc", the broadcast-signal pack.
# NEW FILE ONLY. Derived from the rig-verified lexicon species (v1 verified
# 2026-07-31, v2 multi-deck + FFT verified live 2026-08-06). Latin-1 byte stream,
# UTF-8 for non-ASCII, ABGR colour ints, &#10; line breaks - all rig-proven today.
#
# v1 wrote sentences. v2 fired quotations. v3 is pure signal: every pad is a
# typographic test pattern, WaveWarp defaults are NONZERO so the surface moves
# the moment a pad lands, and three of the five rows ride the external FFT.
#
#   3 decks x 5 layers x 8 columns = 120 clips.
#     deck 1  Test Card  - calibration morning, clean geometry
#     deck 2  On Air     - dense, bright, fast
#     deck 3  Dead Air   - sparse late-night decay
#
# Rows (bottom->top on the layer stack, render base first):
#   Carrier (Alpha, bass FFT)  huge glyph ground, breathes
#   Sweep   (Screen)           long horizontal runs, warped hard
#   Tone    (Screen, mids FFT) mid-band digit/dot patterns
#   Pulse   (Add, highs FFT)   short bright hits, snaps on treble
#   Ident   (Add)              station idents - CH 01, ON AIR, SIGNAL LOST
#
# Glyph inventory: v1-verified renders (- . ... blocks \ # ( ) / + 0) plus plain
# ASCII. No box-drawing, no bullets - nothing outside what the rig has shown.
import re
import xml.etree.ElementTree as ET

OUT = 'Res React Test Card.avc'
COMP_NAME = 'Res React Test Card'
MIDI_PRESET = 'APC 40 MK II - TestCard v1'

_id = [1786300000000]
def nid():
    _id[0] += 1
    return str(_id[0])

def u(s):
    return s.encode('utf-8').decode('latin-1')

def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))

def abgr(r, g, b, a=255):
    return (a << 24) | (b << 16) | (g << 8) | r

# ---------------------------------------------------------------- palette
# Broadcast calibration colours. Carrier keeps the translucent slate that
# rig-rendered correctly in both prior packs.
COL = {
    'Carrier': abgr(0x7C, 0x8A, 0x9C, 0xC4),   # translucent slate
    'Sweep':   abgr(0xFF, 0xD2, 0x3F, 0xFF),   # test-card yellow
    'Tone':    abgr(0x3F, 0xE0, 0xC8, 0xFF),   # phosphor teal
    'Pulse':   abgr(0xFF, 0x5A, 0x36, 0xFF),   # tally orange-red
    'Ident':   abgr(0xF2, 0xF2, 0xF2, 0xFF),   # broadcast white
}

# width truth learned on the rig 2026-08-06: ~25 chars span the frame at Size 1.
CHARS_AT_1 = 25.0
SIZE_MIN, SIZE_MAX = 0.5, 10.0

# (name, blendName, blendType, posY, sizeCap, glow, warpH, warpW, warpSpeed)
# Texture rows may bleed off-frame on purpose; only Ident is fitted to width.
LAYERS = [
    ('Carrier', 'Alpha',  'A006',    0.0, 2.6, 0.20, 0.25, 0.30, 0.10),
    ('Sweep',   'Screen', 'A012', -300.0, 1.7, 0.25, 0.35, 0.50, 0.25),
    ('Tone',    'Screen', 'A012', -100.0, 1.3, 0.20, 0.15, 0.20, 0.40),
    ('Pulse',   'Add',    'A005',  150.0, 1.9, 0.50, 0.10, 0.60, 0.60),
    ('Ident',   'Add',    'A005',  360.0, 1.1, 0.60, 0.00, 0.00, 0.15),
]
ROW = [l[0] for l in LAYERS]

DECKS = ['Test Card', 'On Air', 'Dead Air']

COLUMNS = {
 'Test Card': ['Bars', 'Sweep', 'Grid', 'Tone', 'Dots', 'Cross', 'Ramp', 'Burst'],
 'On Air':    ['Cue', 'Take', 'Wide', 'Tight', 'Punch', 'Roll', 'Feed', 'Peak'],
 'Dead Air':  ['Snow', 'Hiss', 'Ghost', 'Drift', 'Fade', 'Hum', 'Ember', 'Off'],
}

# GRID[deck][row][col] = (pad label, on-screen pattern)
BLK = u('▓▒░')          # block-shade run, v1-verified
DOT = u('·')                      # middle dot
DSH = u('—')                      # em dash
ELL = u('…')                      # ellipsis

GRID = {
'Test Card': {
 'Carrier': [
   ('Full Bars',  BLK * 3 + u('▓')),
   ('Half Bars',  u('▓░') * 5),
   ('Grid',       '# # # # #'),
   ('Checker',    u('▓ ░ ▓ ░ ▓')),
   ('Dot Field',  (DOT + '  ') * 5),
   ('Cross',      '+  +  +  +  +'),
   ('Ramp',       u('░░▒▒▓▓')),
   ('Burst',      '(((  )))'),
 ],
 'Sweep': [
   ('Line',      DSH * 8),
   ('Rise',      '/ / / / / / / /'),
   ('Fall',      '\\ \\ \\ \\ \\ \\ \\ \\'),
   ('Zigzag',    '/\\/\\/\\/\\'),
   ('Fence',     '| | | | | | | |'),
   ('Rail',      '= = = = = = = ='),
   ('Under',     '_ _ _ _ _ _ _ _'),
   ('Long Dash', (DSH + ' ') * 6),
 ],
 'Tone': [
   ('Zeroes',   '0 0 0 0 0 0 0 0'),
   ('Binary',   '0 1 0 1 0 0 1 0'),
   ('KHz',      '4 4 1  4 4 1'),
   ('Sine',     '0 ( 0 ) 0 ( 0 )'),
   ('Count',    '1 2 3 4 5 6 7 8'),
   ('Level',    '- 12 - 18 - 24'),
   ('Hex',      '0 F 0 F 0 F'),
   ('Null',     '0 0 . . 0 0 . .'),
 ],
 'Pulse': [
   ('Tick',   '#'),
   ('Tock',   '# #'),
   ('Sync',   '+ +'),
   ('Blip',   '( )'),
   ('Spike',  '/ \\'),
   ('Twin',   '0 0'),
   ('Frame',  '( # )'),
   ('Dot',    DOT),
 ],
 'Ident': [
   ('CH 01',      'CH 01'),
   ('Test Card',  'TEST CARD F'),
   ('Colour',     'COLOUR 4:3'),
   ('Tone Id',    '1 KHZ TONE'),
   ('Clock',      '06:00:00'),
   ('Hold',       'PLEASE HOLD'),
   ('Trade',      'TRADE TEST'),
   ('Align',      'ALIGN  +  0'),
 ],
},
'On Air': {
 'Carrier': [
   ('Heavy Bars', u('▓') * 10),
   ('Strobe Grid','# # # # # # #'),
   ('Weave',      '/ \\ / \\ / \\ /'),
   ('Lattice',    '+ # + # + # +'),
   ('Rain',       '\\ ' * 7),
   ('Wall',       BLK * 4),
   ('Mesh',       '( ) ( ) ( ) ( )'),
   ('Surge',      u('▓▒▓▒▓▒▓')),
 ],
 'Sweep': [
   ('Fast Line',  DSH * 10),
   ('Double Rise','// // // // //'),
   ('Double Fall','\\\\ \\\\ \\\\ \\\\'),
   ('Saw',        '/\\/\\/\\/\\/\\'),
   ('Picket',     '| | | | | | | | |'),
   ('Hot Rail',   '= = = = = = = = ='),
   ('Score',      '_ _ _ _ _ _ _ _ _'),
   ('Streak',     DSH + DSH + ' ' + DSH + DSH + ' ' + DSH + DSH),
 ],
 'Tone': [
   ('All On',   '1 1 1 1 1 1 1 1'),
   ('Burst 8',  '8 8 8 8 8 8 8 8'),
   ('Rush',     '1 2 4 8 1 2 4 8'),
   ('Clip',     '0 DB 0 DB 0 DB'),
   ('Overmod',  '+ 6 + 6 + 6'),
   ('Carrier',  '( ( 0 ) ) ( ( 0 ) )'),
   ('Crc',      'F F F F F F'),
   ('Payload',  '0 1 1 0 1 0 0 1'),
 ],
 'Pulse': [
   ('Hit',     '# #'),
   ('Slam',    '# # #'),
   ('Rapid',   '+ + + +'),
   ('Flash',   '( ( ) )'),
   ('Jag',     '/ \\ /'),
   ('Deuce',   '0 0 0'),
   ('Bracket', '( # # )'),
   ('Ring',    '( ( ( ) ) )'),
 ],
 'Ident': [
   ('On Air',    'ON AIR'),
   ('Live',      'LIVE'),
   ('Rec',       'REC'),
   ('Take 1',    'TAKE 1'),
   ('Network',   'NETWORK FEED'),
   ('Satellite', 'VIA SATELLITE'),
   ('Peak',      'PEAK  + 6 DB'),
   ('Cue',       'CUE  CUE  CUE'),
 ],
},
'Dead Air': {
 'Carrier': [
   ('Thin Snow',  (DOT + ' ') * 6),
   ('Sparse',     DOT + '   ' + DOT + '   ' + DOT),
   ('Thin Grid',  '#   #   #'),
   ('Loose Weave','/   \\   /'),
   ('Ash',        u('░ ░ ░ ░')),
   ('Ember Grid', '+   +   +'),
   ('Last Bars',  u('▓▒░ ░▒▓')),
   ('Blank',      DOT),
 ],
 'Sweep': [
   ('Flatline',  DSH + DSH + DSH),
   ('Slow Rise', '/   /   /'),
   ('Slow Fall', '\\   \\   \\'),
   ('Wave Out',  '/\\   /\\'),
   ('Last Post', '|   |   |'),
   ('Cold Rail', '=   =   ='),
   ('Sub',       '_   _   _'),
   ('Tail',      DSH + ' ' + DOT + ' ' + DSH),
 ],
 'Tone': [
   ('Zero',     '0'),
   ('Null Duo', '0   0'),
   ('Faint',    '. 0 .'),
   ('Countdown','3   2   1'),
   ('Minus',    '- 40 DB'),
   ('Residue',  '0 . . . 0'),
   ('Hum 50',   '5 0 HZ'),
   ('Off Tone', '0 ' + ELL),
 ],
 'Pulse': [
   ('Last Tick', '#'),
   ('Echo',      '(   )'),
   ('Stray',     '+'),
   ('Skip',      '/ '),
   ('Spark',     DOT + ' ' + DOT),
   ('Lone Zero', '0'),
   ('Fossil',    '( 0 )'),
   ('Nothing',   ELL),
 ],
 'Ident': [
   ('Sign Off',    'SIGN OFF'),
   ('Signal Lost', 'SIGNAL LOST'),
   ('Stand By',    'PLEASE STAND BY'),
   ('No Signal',   'NO SIGNAL'),
   ('Close Down',  'CLOSEDOWN 01:30'),
   ('Anthem',      'ANTHEM' + ' ' + ELL),
   ('Static',      'TRANSMISSION ENDED'),
   ('Goodnight',   'GOODNIGHT'),
 ],
},
}

# ---------------------------------------------------------------- dashboard
# Same eight dials as both prior packs - the hand already knows this bank.
DIALS = ['Size', 'Glow Out', 'Amount', 'Size', 'Threshold', 'Height', 'Width', 'Speed']

def ps(indent, link=None):
    t = '\t' * indent
    if link is None:
        return '%s<PhaseSourceStatic name="PhaseSourceStatic"/>' % t
    n, name, phase = link
    return ('%s<DurationSource/>\n'
            '%s<PhaseSourceDashboardLink name="PhaseSourceDashboardLink" phase="%r" '
            'linkId="/link%d" linkName="%s"/>' % (t, t, phase, n, name))

def dashboard_block(phases):
    rows = []
    for i, (name, ph) in enumerate(zip(DIALS, phases), start=1):
        rows.append(
'\t\t\t\t<ParamRange name="Link %d" altName="%s" T="DOUBLE" default="%r" value="%r">\n'
'\t\t\t\t\t<PhaseSourceStatic name="PhaseSourceStatic"/>\n'
'\t\t\t\t</ParamRange>' % (i, name, ph, ph))
    return '\t\t\t<Params name="Dashboard">\n' + '\n'.join(rows) + '\n\t\t\t</Params>'

# ---------------------------------------------------------------- audio
# THREE FFT rows this time: Carrier breathes on bass, Tone shimmers on mids,
# Pulse snaps on highs. Sweep and Ident stay steady so the eye has an anchor.
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
FFT_LAYERS = {
    0: ('bass',  6.0, 800.0, 0.55),
    2: ('mids',  5.0, 500.0, 0.60),
    3: ('highs', 6.0, 200.0, 0.45),
}

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

# same rack as both prior packs, all bypassed on load; still no Trails/Freeze.
COMP_RACK = [('HueRotate', 'A128'), ('ShiftRGB', 'A153'), ('LoRezEffect', 'A142'),
             ('InvertRGB', 'A105'), ('MirrorQuad', 'A180')]

def clip(layer_i, col_i, label, text, size, posy, glow, color, warp):
    wh, ww, wspd = warp
    size_phase = (size - SIZE_MIN) / (SIZE_MAX - SIZE_MIN)
    phases = [size_phase, glow, 0.18, 0.18, 0.45, wh, ww, wspd]
    L = [(i + 1, DIALS[i], phases[i]) for i in range(8)]
    fx = '\n\t\t\t\t\t'.join([
        transform_pass(),
        bloom_pass(0.18, 0.45, 0.18, links=(L[2], L[4], L[3])),
        wavewarp_pass(wh, ww, wspd, links=(L[5], L[6], L[7]))])
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
deck_ids = [nid() for _ in DECKS]
parts = []
parts.append('<?xml version="1.0" encoding="utf-8"?>\n')
parts.append('<Composition name="Composition" uniqueId="%s" numDecks="%d" currentDeckIndex="0" '
             'numLayers="5" numColumns="8" compositionIsRelative="0">\n' % (nid(), len(DECKS)))
parts.append('\t<versionInfo name="Resolume Avenue" majorVersion="7" minorVersion="27" microVersion="1" revision="15990"/>\n')
parts.append('\t<CompositionInfo name="%s" description="broadcast test signals as an APC40 instrument" width="1920" height="1080">\n%s\t</CompositionInfo>\n'
             % (COMP_NAME, ''.join('\t\t<DeckInfo name="%s" id="%s" closed="0"/>\n' % (esc(n), i)
                                   for n, i in zip(DECKS, deck_ids))))
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

for i, spec in enumerate(LAYERS):
    nm, bn, bt = spec[0], spec[1], spec[2]
    passes = ['<RenderPass storage="0" name="Transform" type="TransformEffect" '
              'uniqueTypeId="17122039101699797593" uniqueId="%s" baseType="Effect">\n'
              '\t\t\t\t\t<View name="View" bCanBeDisabled="0" bCanBeRemoved="0"/>\n'
              '\t\t\t\t</RenderPass>' % nid()]
    if i > 0:
        passes.append(layer_bloom())
    parts.append(layer(i, nm, bn, bt, 1.0, '\n\t\t\t\t'.join(passes)) + '\n')

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
                 '\t\t</Params>\n' % (deck_ids[di], di, esc(deck)))
    for c, cname in enumerate(COLUMNS[deck]):
        parts.append('\t\t<Column uniqueId="%s" columnIndex="%d">\n'
                     '\t\t\t<Params name="Params">\n'
                     '\t\t\t\t<Param name="Name" T="STRING" default="Column #" value="%s"/>\n'
                     '\t\t\t</Params>\n'
                     '\t\t</Column>\n' % (nid(), c, esc(cname)))
    for c in range(8):
        for li, spec in enumerate(LAYERS):
            nm, posy, cap, glow = spec[0], spec[3], spec[4], spec[5]
            warp = (spec[6], spec[7], spec[8])
            label, text = GRID[deck][nm][c]
            # fit to the frame using the rig-measured width constant; texture
            # rows may hit their cap and bleed - that is the aesthetic. Ident
            # is always fitted so station text stays whole.
            size = max(SIZE_MIN, min(cap, CHARS_AT_1 / max(len(text), 1)))
            parts.append('\t\t' + clip(li, c, label, text, size, posy, glow,
                                       COL[nm], warp) + '\n')
            manifest.append((di, deck, li, nm, c, cname, label, text, size))
    parts.append('\t</Deck>\n')

parts.append('\t<Notes name="Notes">\n\t\t<Note text_size_multiplier="2" text_color_index="4" text=""/>\n\t</Notes>\n')
parts.append('</Composition>\n')

data = ''.join(parts)

# ---------------------------------------------------------------- validate
ET.fromstring(data.encode('latin-1'))
ids = re.findall(r'uniqueId="(\d+)"', data)
assert len(ids) == len(set(ids)), 'duplicate uniqueIds'
assert data.count('<Clip ') == 120, 'clip count %d' % data.count('<Clip ')
assert data.count('<Layer ') == 5
assert data.count('<Deck ') == 3
assert data.count('<Column ') == 24
assert data.count('BlockTextGenerator') == 120 * 2
assert data.count('<PhaseSourceFFT ') == 3 * 8 * 3, 'FFT clip count'
assert u('�') not in data
labels = [(d, r, l) for d, _, _, r, _, _, l, _, _ in manifest]
assert len(labels) == len(set(labels)), 'duplicate pad labels within a deck row'
open(OUT, 'w', encoding='latin-1', newline='').write(data)

with open('_testcard_manifest.tsv', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('deckIndex\tdeck\tlayerIndex\trow\tcol\tcolumn\tlabel\tsize\ttext\n')
    for di, deck, li, nm, c, cn, label, text, size in manifest:
        fh.write('%d\t%s\t%d\t%s\t%d\t%s\t%s\t%.3f\t%s\n'
                 % (di, deck, li, nm, c, cn, label, size,
                    text.encode('latin-1').decode('utf-8')))

print('WROTE %s  %d bytes | clips=%d decks=%d fft_rows=3 uniqueIds=%d'
      % (OUT, len(data.encode('latin-1')), data.count('<Clip '),
         data.count('<Deck '), len(ids)))
print('WROTE _testcard_manifest.tsv  %d rows' % len(manifest))
