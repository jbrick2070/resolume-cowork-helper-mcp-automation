# build_nisei.py — generate "Res React Nisei.avc"
#
# The fourth instrument. v1 wrote grammar, v2 fired found-text quotations,
# v3 was broadcast test signals. This one is ARCHIVAL: testimony, poetry,
# documents, and places from the Japanese American experience — built for
# a Nisei Week pitch to Little Tokyo venues.
#
# 3 decks x 5 layers x 8 columns = 120 clips, all native Text Block.
#   Deck 1  Little Tokyo  — pre-war community, home, the promise
#   Deck 2  Executive Order — evacuation, camps, testimony, poetry
#   Deck 3  Nisei Week    — return, redress, celebration, continuity
#
# Rows (bottom->top):
#   Ground  (Alpha, bass FFT)  large texture: dates, kanji-roman, numbers
#   Archive (Screen)           places, documents, institutional names
#   Voice   (Screen, mids FFT) testimony, poetry, first-person excerpts
#   Signal  (Add, highs FFT)   short words, calls, commands
#   Title   (Add)              headings, identifiers
#
# TEXT SOURCES — all public domain or fair use:
#   - Executive Order 9066 (US government, PD)
#   - "Instructions to All Persons of Japanese Ancestry" posted notice (US gov, PD)
#   - CWRIC "Personal Justice Denied" report (US gov publication, PD / CC0)
#   - Camp senryu translations from NPS article (US gov publication, PD)
#   - Short fair-use excerpts from Portland Assembly Center senryu collection
#   - Factual place names, dates, camp names (not copyrightable)
#   - Widely-used Japanese community phrases (shikata ga nai, gaman, etc.)
#
# Species: rig-verified testcard/lexicon lineage. Latin-1 byte stream, ABGR
# colour ints, dashboard dials, FFT on 3 rows, WaveWarp (subtle — archival
# register, not broadcast chaos).

import re
import xml.etree.ElementTree as ET

OUT = 'Res React Nisei.avc'
COMP_NAME = 'Res React Nisei'
MIDI_PRESET = 'APC 40 MK II - Nisei v1'

_id = [1787100000000]
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
# Archival warmth, not broadcast neon. Ground=night indigo, Archive=amber,
# Voice=pearl white, Signal=vermillion, Title=festival gold.
COL = {
    'Ground':  abgr(0x1A, 0x1A, 0x4D, 0xC4),
    'Archive': abgr(0xD4, 0xA0, 0x50, 0xFF),
    'Voice':   abgr(0xE8, 0xE8, 0xEE, 0xFF),
    'Signal':  abgr(0xCC, 0x33, 0x33, 0xFF),
    'Title':   abgr(0xE6, 0xC8, 0x50, 0xFF),
}

CHARS_AT_1 = 25.0
SIZE_MIN, SIZE_MAX = 0.5, 10.0

# (name, blendName, blendType, posY, sizeCap, glow, warpH, warpW, warpSpeed)
# WaveWarp is SUBTLE here — gentle archival sway, not broadcast chaos.
LAYERS = [
    ('Ground',  'Alpha',  'A006',    0.0, 2.4, 0.15, 0.08, 0.10, 0.06),
    ('Archive', 'Screen', 'A012', -280.0, 1.5, 0.20, 0.05, 0.08, 0.04),
    ('Voice',   'Screen', 'A012',  -80.0, 1.2, 0.25, 0.06, 0.10, 0.05),
    ('Signal',  'Add',    'A005',  170.0, 1.8, 0.45, 0.04, 0.15, 0.08),
    ('Title',   'Add',    'A005',  370.0, 1.0, 0.55, 0.00, 0.00, 0.03),
]
ROW = [l[0] for l in LAYERS]

DECKS = ['Little Tokyo', 'Executive Order', 'Nisei Week']

COLUMNS = {
 'Little Tokyo':     ['Roots', 'Harbor', 'Market', 'Family', 'Festival', 'Dance', 'Garden', 'Promise'],
 'Executive Order':  ['The Order', 'The Notice', 'Evacuate', 'Assembly', 'The Camp', 'The Fence', 'Senryu', 'Endure'],
 'Nisei Week':       ['Return', 'Rebuild', 'Redress', 'Apology', 'Remember', 'Festival', 'Continue', 'Celebrate'],
}

DOT = u('·')

# ---------------------------------------------------------------- content
# GRID[deck][row][col] = (pad_label, on_screen_text)
# Voice row texts are sourced — see header comment for provenance.
GRID = {
'Little Tokyo': {
 'Ground': [
   ('Year One',    '1 8 8 4'),
   ('Terminal',    'TERMINAL ISLAND'),
   ('City Market', 'CITY MARKET'),
   ('Issei',       'I S S E I'),
   ('Founded',     '1 9 3 4'),
   ('Obon',        'O B O N'),
   ('Nihonmachi',  'NIHONMACHI'),
   ('Nisei',       'N I S E I'),
 ],
 'Archive': [
   ('First St',    'EAST FIRST STREET'),
   ('San Pedro',   'SAN PEDRO HARBOR'),
   ('Seventh',     'SEVENTH AND CENTRAL'),
   ('Boyle Hts',   'BOYLE HEIGHTS'),
   ('August 13',   'AUGUST 13'),
   ('First Block', 'FIRST STREET CLOSED'),
   ('Sawtelle',    'SAWTELLE'),
   ('Los Angeles', 'LOS ANGELES'),
 ],
 'Voice': [
   ('Home',        'WE MADE OUR HOME HERE'),
   ('Boats',       'FRESH FROM THE BOATS EACH MORNING'),
   ('Wholesale',   'PRODUCE FOR THE WHOLE CITY'),
   ('Together',    'ISSEI AND NISEI TOGETHER'),
   ('Solidarity',  'ETHNIC SOLIDARITY'),
   ('Ondo',        'ONDO DANCING FOR ALL AGES'),
   ('Garden',      'A GARDEN IN THE CITY'),
   ('Americans',   'WE WERE AMERICANS'),
 ],
 'Signal': [
   ('Dai Ichi',   'DAI ICHI'),
   ('Harbor',     'HARBOR'),
   ('Market',     'MARKET'),
   ('Kazoku',     'KAZOKU'),
   ('Matsuri',    'MATSURI'),
   ('Odori',      'ODORI'),
   ('Hana',       'HANA'),
   ('Yakusoku',   'YAKUSOKU'),
 ],
 'Title': [
   ('Little Tokyo', 'LITTLE TOKYO'),
   ('Terminal Is',  'TERMINAL ISLAND'),
   ('Produce Row',  'PRODUCE ROW'),
   ('Family',       'FAMILY'),
   ('Nisei Week',   'NISEI WEEK'),
   ('Ondo',         'ONDO'),
   ('Japantown',    'JAPANTOWN'),
   ('The Promise',  'THE PROMISE'),
 ],
},
'Executive Order': {
 'Ground': [
   ('Feb 19',     'FEB 19 1942'),
   ('April',      'APRIL 1942'),
   ('120000',     '1 2 0 0 0 0'),
   ('Santa Anita','SANTA ANITA'),
   ('Manzanar',   'MANZANAR'),
   ('Heart Mtn',  'HEART MOUNTAIN'),
   ('Tule Lake',  'TULE LAKE'),
   ('Minidoka',   'MINIDOKA'),
 ],
 'Archive': [
   ('EO 9066',    'EXECUTIVE ORDER 9066'),
   ('Def Command','WESTERN DEFENSE COMMAND'),
   ('Control Stn','CIVIL CONTROL STATION'),
   ('Asm Center', 'ASSEMBLY CENTER'),
   ('WRA',        'WAR RELOCATION AUTHORITY'),
   ('Guard Tower','GUARD TOWER'),
   ('Seg Center', 'SEGREGATION CENTER'),
   ('442nd',      '442ND REGIMENTAL COMBAT TEAM'),
 ],
 'Voice': [
   ('Any All',    'ANY OR ALL PERSONS'),
   ('Instruct',   'INSTRUCTIONS TO ALL PERSONS OF JAPANESE ANCESTRY'),
   ('Noon',       'EVACUATED BY TWELVE O CLOCK NOON'),
   ('Risk',       'AT THE SOLE RISK OF THE OWNER'),
   ('Dreams',     'ONLY IN DREAMS A WORLD OF FREEDOM'),
   ('Guns',       'WHY WERE THE GUNS POINTED INWARD'),
   ('Never Asked','THEY NEVER ASKED JUST PUT US AWAY'),
   ('Barbed Wire','BEYOND THE BARBED WIRE A GLOW OF NEON LIGHTS'),
 ],
 'Signal': [
   ('Order',     'ORDER'),
   ('Notice',    'NOTICE'),
   ('Evacuate',  'EVACUATE'),
   ('Report',    'REPORT'),
   ('Fence',     'FENCE'),
   ('Wire',      'BARBED WIRE'),
   ('Senryu',    'SENRYU'),
   ('Gaman',     'GAMAN'),
 ],
 'Title': [
   ('The Order',  'THE ORDER'),
   ('The Notice', 'THE NOTICE'),
   ('Exclusion',  'CIVILIAN EXCLUSION'),
   ('Assembly',   'ASSEMBLY'),
   ('The Camp',   'THE CAMP'),
   ('The Fence',  'THE FENCE'),
   ('Poetry',     'POETRY'),
   ('Go Broke',   'GO FOR BROKE'),
 ],
},
'Nisei Week': {
 'Ground': [
   ('Dec 1944',   'DEC 18 1944'),
   ('1949',       '1 9 4 9'),
   ('Aug 1988',   'AUG 10 1988'),
   ('HR 442',     'H R 4 4 2'),
   ('Feb 19',     'FEB 19'),
   ('Ondo Beat',  'O N D O'),
   ('Generations','SANSEI YONSEI GOSEI'),
   ('2026',       '2 0 2 6'),
 ],
 'Archive': [
   ('Rescission', 'RESCISSION ORDER'),
   ('Revival',    'LITTLE TOKYO'),
   ('Civil Lib',  'CIVIL LIBERTIES ACT'),
   ('Congress',   '100TH CONGRESS'),
   ('Day of Rem', 'DAY OF REMEMBRANCE'),
   ('Village Plz','JAPANESE VILLAGE PLAZA'),
   ('JANM',       'JAPANESE AMERICAN NATIONAL MUSEUM'),
   ('Home',       'LITTLE TOKYO'),
 ],
 'Voice': [
   ('Gates Open', 'THE GATES OPENED'),
   ('Revived',    'NISEI WEEK REVIVED'),
   ('Prejudice',  'RACE PREJUDICE WAR HYSTERIA'),
   ('Injustice',  'A GRAVE INJUSTICE WAS DONE'),
   ('Never Again','NEVER AGAIN'),
   ('Celebrate',  'CELEBRATE HERITAGE AND CULTURE'),
   ('Next Gen',   'THE NEXT GENERATION'),
   ('Kodomo',     'KODOMO NO TAME NI'),
 ],
 'Signal': [
   ('Return',    'RETURN'),
   ('Rebuild',   'REBUILD'),
   ('Redress',   'REDRESS'),
   ('Gomen',     'GOMEN NASAI'),
   ('Remember',  'REMEMBER'),
   ('Dance',     'MATSURI'),
   ('Tsuzuku',   'TSUZUKU'),
   ('Omedeto',   'OMEDETO'),
 ],
 'Title': [
   ('The Return', 'THE RETURN'),
   ('Rebuilt',    'REBUILT'),
   ('Justice',    'PERSONAL JUSTICE DENIED'),
   ('The Apology','THE APOLOGY'),
   ('Remember',   'REMEMBER'),
   ('Festival',   'NISEI WEEK'),
   ('Continuity', 'CONTINUITY'),
   ('Okaeri',     'OKAERI'),
 ],
},
}

# ---------------------------------------------------------------- dashboard
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

FFT_LAYERS = {
    0: ('bass',  5.0, 1000.0, 0.60),
    2: ('mids',  4.0,  600.0, 0.65),
    3: ('highs', 5.0,  300.0, 0.50),
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
parts.append('\t<CompositionInfo name="%s" description="archival testimony and community voices for Nisei Week" width="1920" height="1080">\n%s\t</CompositionInfo>\n'
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
labels = [(d, r, l) for d, _, _, r, _, _, l, _, _ in manifest]
assert len(labels) == len(set(labels)), 'duplicate pad labels within a deck row'
open(OUT, 'w', encoding='latin-1', newline='').write(data)

with open('_nisei_manifest.tsv', 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('deckIndex\tdeck\tlayerIndex\trow\tcol\tcolumn\tlabel\tsize\ttext\n')
    for di, deck, li, nm, c, cn, label, text, size in manifest:
        fh.write('%d\t%s\t%d\t%s\t%d\t%s\t%s\t%.3f\t%s\n'
                 % (di, deck, li, nm, c, cn, label, size, text))

print('WROTE %s  %d bytes | clips=%d decks=%d fft_rows=3 uniqueIds=%d'
      % (OUT, len(data.encode('latin-1')), data.count('<Clip '),
         data.count('<Deck '), len(ids)))
print('WROTE _nisei_manifest.tsv  %d rows' % len(manifest))
