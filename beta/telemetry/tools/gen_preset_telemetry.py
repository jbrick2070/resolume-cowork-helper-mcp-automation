# gen_preset_telemetry.py - build "APC 40 MK II - Telemetry v1.xml".
# NEW FILE ONLY. No existing preset is read-modify-written.
#
# THE FULL SURFACE. Every performance preset in this kit so far mapped ~98 of
# the APC40 mkII's 149 addressable controls; the diagnostic visual twins mapped
# 148. This preset is the first PERFORMANCE build to map all 149 - including
# the footswitch (CC64, never mapped by any preset in the kit, ever) and the
# relative tempo encoder (CC13, behaviour 16392, previously diagnostic-only).
#
# Shortcut species are cloned from rig-saved donors: clip-connect quartet /
# column / fader / selected-clip dashboard / trigger / bool / solo from
# "APC 40 MK II - React v4.4.xml" via the Lexicon generators; the relative
# encoder from "APC 40 MK II - Visual QA.xml" (behaviour="16392",
# numSteps="480"). Where the same action appears under two fingers that is
# deliberate and listed in MIRRORS below; validation enforces that every
# duplicated path is declared there and nowhere else.
import os, re
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'controllers', 'APC 40 MK II - Telemetry v1.xml')
CMAP = os.path.join(HERE, '..', 'docs', '_control_map.tsv')
NAME = 'APC 40 MK II - Telemetry v1'
DEV = 'APC40 mkII'

B = 1 << 56
def note_key(n, ch=1):
    return B + n * 256 + (0x90 + ch - 1)
def cc_key(c, ch=1):
    return 2 * B + c * 256 + (0xB0 + ch - 1)

_id = [1786800000000]
def nid():
    _id[0] += 1
    return str(_id[0])

def vel(v):
    return repr(v / 127.0)

S = []
CONTROL_MAP = []    # (control, kind, num, ch, action) for the doc + census
def add(x):
    S.append(x)

def rec(control, kind, num, ch, action, xml):
    CONTROL_MAP.append((control, kind, num, ch, action))
    add(xml)

# ---------------------------------------------------------------- species
def sc_connect(path, sibling, key, named):
    nv = '\n'.join('\t\t\t\t<Value first="%s" second="%s" />' % (k, v) for k, v in named)
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="" behaviour="1028" inputDeviceName="%s" outputDeviceName="%s">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="11" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="11" />\n'
'\t\t\t<ShortcutPath name="InputSiblingPath" path="%s" translationType="1" allowedTranslationTypes="-1" />\n'
'\t\t\t<ShortcutPath name="OutputSiblingPath" path="%s" translationType="1" allowedTranslationTypes="-1" />\n'
'\t\t\t<RawInputMessage key="%d" value="0" numSteps="128" />\n'
'\t\t\t<NamedValues>\n%s\n\t\t\t</NamedValues>\n'
'\t\t</Shortcut>' % (nid(), DEV, DEV, path, path, sibling, sibling, key, nv))

def pad_connect(lay, col, key, on_v, off_v):
    p = '/composition/layers/%d/clips/%d/connect' % (lay, col)
    sib = '/composition/layers/%d/clips/%d/connected' % (lay, col)
    named = [('Connected', vel(on_v)), ('Connected &amp; previewing', vel(on_v)),
             ('Disconnected', vel(off_v)), ('Empty', vel(off_v)),
             ('Off', '0'), ('Previewing', vel(off_v))]
    return sc_connect(p, sib, key, named)

def sc_column(col, key):
    path = '/composition/columns/%d/connect' % col
    sibling = '/composition/columns/%d/connected' % col
    nv = '\n'.join('\t\t\t\t<Value first="%s" second="%s" />' % (k, v) for k, v in
                   [('Connected', '1'), ('Disconnected', '0.5'), ('Empty', '0')])
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="" behaviour="1028" inputDeviceName="%s" outputDeviceName="%s">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="35" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="3" />\n'
'\t\t\t<ShortcutPath name="InputSiblingPath" path="%s" translationType="1" allowedTranslationTypes="-1" />\n'
'\t\t\t<ShortcutPath name="OutputSiblingPath" path="%s" translationType="1" allowedTranslationTypes="-1" />\n'
'\t\t\t<RawInputMessage key="%d" value="0" numSteps="128" />\n'
'\t\t\t<NamedValues>\n%s\n\t\t\t</NamedValues>\n'
'\t\t</Shortcut>' % (nid(), DEV, DEV, path, path, sibling, sibling, key, nv))

def sc_fader(path, key, value='1', allowed='11'):
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="" behaviour="8" inputDeviceName="%s" outputDeviceName="%s">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="%s" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="%s" />\n'
'\t\t\t<Subtarget type="5" optionIndex="-1" />\n'
'\t\t\t<RawInputMessage key="%d" value="%s" numSteps="128" />\n'
'\t\t</Shortcut>' % (nid(), DEV, DEV, path, allowed, path, allowed, key, value))

def sc_dashboard(n, key):
    p = '/composition/selectedclip/dashboard/link%d' % n
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="ParamRange" behaviour="8" inputDeviceName="%s" outputDeviceName="%s">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="4" allowedTranslationTypes="7"/>\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="4" allowedTranslationTypes="7"/>\n'
'\t\t\t<ShortcutPath name="InputSiblingPath" path="" translationType="1" allowedTranslationTypes="-1"/>\n'
'\t\t\t<ShortcutPath name="OutputSiblingPath" path="" translationType="1" allowedTranslationTypes="-1"/>\n'
'\t\t\t<Subtarget type="5" optionIndex="-1"/>\n'
'\t\t\t<ValueRange min="0" max="1"/>\n'
'\t\t\t<RawInputMessage key="%d" value="0" numSteps="128"/>\n'
'\t\t</Shortcut>' % (nid(), DEV, DEV, p, p, key))

def sc_trigger(path, key, off='0', on='1'):
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="" behaviour="1028" inputDeviceName="%s" outputDeviceName="%s">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="11" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="11" />\n'
'\t\t\t<RawInputMessage key="%d" value="0" numSteps="128" />\n'
'\t\t\t<NamedValues>\n'
'\t\t\t\t<Value first="Off" second="%s" />\n'
'\t\t\t\t<Value first="On" second="%s" />\n'
'\t\t\t</NamedValues>\n'
'\t\t</Shortcut>' % (nid(), DEV, DEV, path, path, key, off, on))

def sc_bool(path, key, off, on, allowed='11', node=''):
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="%s" behaviour="4">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="%s" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="%s" />\n'
'\t\t\t<RawInputMessage key="%d" value="0" numSteps="128" />\n'
'\t\t\t<NamedValues>\n'
'\t\t\t\t<Value first="Off" second="%s" />\n'
'\t\t\t\t<Value first="On" second="%s" />\n'
'\t\t\t</NamedValues>\n'
'\t\t</Shortcut>' % (nid(), node, path, allowed, path, allowed, key, off, on))

def sc_solo(layer, key):
    p = '/composition/layers/%d/solo' % layer
    sp = '/composition/layers/%d/soloed' % layer
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="" behaviour="4">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="3" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="3" />\n'
'\t\t\t<ShortcutPath name="InputSiblingPath" path="%s" translationType="1" allowedTranslationTypes="-1" />\n'
'\t\t\t<ShortcutPath name="OutputSiblingPath" path="%s" translationType="1" allowedTranslationTypes="-1" />\n'
'\t\t\t<RawInputMessage key="%d" value="0" numSteps="128" />\n'
'\t\t\t<NamedValues>\n'
'\t\t\t\t<Value first="Off" second="0.007874015748031496" />\n'
'\t\t\t\t<Value first="On" second="0.10236220472440945" />\n'
'\t\t\t</NamedValues>\n'
'\t\t</Shortcut>' % (nid(), p, p, sp, sp, key))

def sc_relative(path, key):
    """Relative encoder - cloned from the rig-saved Visual QA donor
    (behaviour 16392, 480 steps per revolution, input-only)."""
    return (
'\t\t<Shortcut name="Shortcut" uniqueId="%s" paramNodeName="ParamRange" behaviour="16392" inputDeviceName="%s">\n'
'\t\t\t<ShortcutPath name="InputPath" path="%s" translationType="1" allowedTranslationTypes="1" />\n'
'\t\t\t<ShortcutPath name="OutputPath" path="%s" translationType="1" allowedTranslationTypes="1" />\n'
'\t\t\t<Subtarget type="5" optionIndex="-1" />\n'
'\t\t\t<RawInputMessage key="%d" value="-0.0020833333333333333044" numSteps="480" />\n'
'\t\t</Shortcut>' % (nid(), DEV, path, path, key))

# ---------------------------------------------------------------- the surface
# Grid rows, top of the APC to the bottom; layer colour follows the on-screen
# row. Velocity pairs are the kit's proven LED palette.
ROWS = [
    (32, 5, 'READOUT', 3,  3),    # top pad row    -> layer 5, white
    (24, 4, 'STAMP',   52, 53),   #                -> layer 4, pink
    (16, 3, 'NEEDLE',  8,  9),    #                -> layer 3, amber
    (8,  2, 'TRACE',   36, 37),   #                -> layer 2, sky
    (0,  1, 'PAPER',   44, 45),   # bottom pad row -> layer 1, violet
]

add('\t\t<!-- GRID: 5 rows x 8 columns. Top row READOUT, then STAMP, NEEDLE, TRACE;\n'
    '\t\t     bottom row PAPER - top pad row is the top on-screen layer. -->')
for base, lay, role, on_v, off_v in ROWS:
    for c in range(8):
        rec('grid %s c%d' % (role, c + 1), 'NOTE', base + c, 1,
            'connect clip L%d C%d' % (lay, c + 1),
            pad_connect(lay, c + 1, note_key(base + c, 1), on_v, off_v))

add('\t\t<!-- TRACK SELECT 1-8 = fire a whole reading (column 1-8) -->')
for c in range(8):
    rec('track select %d' % (c + 1), 'NOTE', 51, c + 1,
        'connect column %d' % (c + 1), sc_column(c + 1, note_key(51, c + 1)))

add('\t\t<!-- SCENE LAUNCH 1-5 = lift the pen (layer clear), aligned with the rows -->')
for i, (base, lay, role, a, b) in enumerate(ROWS):
    rec('scene launch %d' % (i + 1), 'NOTE', 82 + i, 1,
        'clear layer %d (%s)' % (lay, role),
        sc_trigger('/composition/layers/%d/clear' % lay, note_key(82 + i, 1),
                   '0', '0.0078740157480314959537'))

rec('stop all clips', 'NOTE', 81, 1, 'disconnect all (power down)',
    sc_trigger('/composition/disconnectall', note_key(81, 1)))
rec('master select', 'NOTE', 80, 1, 'connect TEST CARD (L5 C8)',
    pad_connect(5, 8, note_key(80, 1), 3, 0))

add('\t\t<!-- CLIP STOP row = the instrument rack, eight comp FX toggles -->')
FXTOG = ['huerotate', 'shiftrgb', 'lorezeffect', 'invertrgb', 'mirrorquad',
         'twitcheffect', 'shiftglitch', 'vignette']
for i, fx in enumerate(FXTOG):
    rec('clip stop trk%d' % (i + 1), 'NOTE', 52, i + 1,
        'toggle comp FX %s' % fx,
        sc_bool('/composition/video/effects/%s/bypassed' % fx, note_key(52, i + 1),
                '0.023622047244094488', '0.10236220472440945',
                allowed='1', node='RangedParam[bool]'))

add('\t\t<!-- ACTIVATOR = power a channel down; 6-8 arm the row lamps (layer Bloom) -->')
for lay in (1, 2, 3, 4, 5):
    rec('activator trk%d' % lay, 'NOTE', 50, lay, 'bypass layer %d' % lay,
        sc_bool('/composition/layers/%d/bypassed' % lay, note_key(50, lay),
                '0.16535433070866143', '0.055118110236220472'))
for ch, lay, nick in ((6, 2, 'TRACE LAMP'), (7, 4, 'STAMP LAMP'), (8, 5, 'READOUT LAMP')):
    rec('activator trk%d' % ch, 'NOTE', 50, ch,
        'toggle layer %d Bloom (%s)' % (lay, nick),
        sc_bool('/composition/layers/%d/video/effects/bloom/bypassed' % lay,
                note_key(50, ch), '0.16535433070866143', '0.055118110236220472',
                allowed='1', node='RangedParam[bool]'))

add('\t\t<!-- SOLO = isolate a channel; 6-8 spotlight the verdict stamps -->')
for lay in (1, 2, 3, 4, 5):
    rec('solo trk%d' % lay, 'NOTE', 49, lay, 'solo layer %d' % lay,
        sc_solo(lay, note_key(49, lay)))
for ch, col in ((6, 1), (7, 3), (8, 5)):
    rec('solo trk%d' % ch, 'NOTE', 49, ch,
        'connect verdict stamp L4 C%d [mirror]' % col,
        pad_connect(4, col, note_key(49, ch), 52, 53))

add('\t\t<!-- RECORD ARM 1-5 = ROLL: auto-advance that row; 6-8 force instrument states -->')
for lay in (1, 2, 3, 4, 5):
    rec('record arm trk%d' % lay, 'NOTE', 48, lay,
        'connect next clip on layer %d' % lay,
        sc_trigger('/composition/layers/%d/connectnextclip' % lay, note_key(48, lay)))
for ch, col in ((6, 6), (7, 7), (8, 8)):
    rec('record arm trk%d' % ch, 'NOTE', 48, ch,
        'connect force-state L2 C%d [mirror]' % col,
        pad_connect(2, col, note_key(48, ch), 36, 37))

add('\t\t<!-- CROSSFADE A/B = the diagonal walk: eight presses build a full look -->')
DIAG = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (1, 6), (2, 7), (3, 8)]
for i, (lay, col) in enumerate(DIAG):
    rec('crossfade A/B trk%d' % (i + 1), 'NOTE', 66, i + 1,
        'connect diagonal L%d C%d [mirror]' % (lay, col),
        pad_connect(lay, col, note_key(66, i + 1), 1, 0))

add('\t\t<!-- BROADCAST DESK: the classic test signals and cue cards -->')
rec('pan', 'NOTE', 87, 1, 'connect TONE (L1 C6) [mirror]',
    pad_connect(1, 6, note_key(87, 1), 44, 45))
rec('sends', 'NOTE', 88, 1, 'connect BARS (L1 C7) [mirror]',
    pad_connect(1, 7, note_key(88, 1), 44, 45))
rec('user', 'NOTE', 89, 1, 'connect SNOW (L1 C8) [mirror]',
    pad_connect(1, 8, note_key(89, 1), 44, 45))
rec('metronome', 'NOTE', 90, 1, 'connect PILOT strobe (L4 C8) [mirror]',
    pad_connect(4, 8, note_key(90, 1), 52, 53))
rec('play', 'NOTE', 91, 1, 'resync',
    sc_trigger('/composition/tempocontroller/resync', note_key(91, 1)))
rec('stop', 'NOTE', 92, 1, 'composition bypass (SCREEN DARK)',
    sc_bool('/composition/bypassed', note_key(92, 1), '0.023622047244094488',
            '0.10236220472440945', allowed='1', node='RangedParam[bool]'))
rec('record', 'NOTE', 93, 1, 'connect SLATE (L5 C6) [mirror]',
    pad_connect(5, 6, note_key(93, 1), 3, 0))
rec('session rec', 'NOTE', 102, 1, 'connect DATA CARD (L3 C6) [mirror]',
    pad_connect(3, 6, note_key(102, 1), 8, 9))
rec('tap tempo', 'NOTE', 99, 1, 'tempo tap',
    sc_trigger('/composition/tempocontroller/tempotap', note_key(99, 1)))

add('\t\t<!-- PAPER FEED and CHANNEL DIAL -->')
rec('up', 'NOTE', 94, 1, 'previous column (feed paper back)',
    sc_trigger('/composition/connectprevcolumn', note_key(94, 1)))
rec('down', 'NOTE', 95, 1, 'next column (feed paper on)',
    sc_trigger('/composition/connectnextcolumn', note_key(95, 1)))
rec('nudge -', 'NOTE', 100, 1, 'previous column [mirror of up]',
    sc_trigger('/composition/connectprevcolumn', note_key(100, 1)))
rec('nudge +', 'NOTE', 101, 1, 'next column [mirror of down]',
    sc_trigger('/composition/connectnextcolumn', note_key(101, 1)))
rec('right', 'NOTE', 96, 1, 'next deck (next instrument)',
    sc_trigger('/composition/selectnextdeck', note_key(96, 1)))
rec('left', 'NOTE', 97, 1, 'previous deck (previous instrument)',
    sc_trigger('/composition/selectprevdeck', note_key(97, 1)))
rec('bank <', 'NOTE', 60, 1, 'previous deck [mirror of left]',
    sc_trigger('/composition/selectprevdeck', note_key(60, 1)))
rec('bank >', 'NOTE', 61, 1, 'next deck [mirror of right]',
    sc_trigger('/composition/selectnextdeck', note_key(61, 1)))
rec('shift', 'NOTE', 98, 1, 'connect SIGNAL LOST (L5 C7) [mirror]',
    pad_connect(5, 7, note_key(98, 1), 3, 0))
rec('bank', 'NOTE', 103, 1, 'connect CLEAN SHEET (L1 C1) [mirror]',
    pad_connect(1, 1, note_key(103, 1), 44, 45))

add('\t\t<!-- DEVICE ROW: jog the traces, arm the heavy FX, pull the detail -->')
rec('device <', 'NOTE', 58, 1, 'connect next clip on layer 3 [mirror]',
    sc_trigger('/composition/layers/3/connectnextclip', note_key(58, 1)))
rec('device >', 'NOTE', 59, 1, 'connect next clip on layer 4 [mirror]',
    sc_trigger('/composition/layers/4/connectnextclip', note_key(59, 1)))
rec('device on/off', 'NOTE', 62, 1, 'toggle comp FX bloom',
    sc_bool('/composition/video/effects/bloom/bypassed', note_key(62, 1),
            '0.023622047244094488', '0.10236220472440945',
            allowed='1', node='RangedParam[bool]'))
rec('device lock', 'NOTE', 63, 1, 'toggle comp FX wavewarp',
    sc_bool('/composition/video/effects/wavewarp/bypassed', note_key(63, 1),
            '0.023622047244094488', '0.10236220472440945',
            allowed='1', node='RangedParam[bool]'))
rec('clip/dev view', 'NOTE', 64, 1, 'toggle comp FX tunnel',
    sc_bool('/composition/video/effects/tunnel/bypassed', note_key(64, 1),
            '0.023622047244094488', '0.10236220472440945',
            allowed='1', node='RangedParam[bool]'))
rec('detail view', 'NOTE', 65, 1, 'connect CAL DIAL (L3 C8) [mirror]',
    pad_connect(3, 8, note_key(65, 1), 8, 9))

add('\t\t<!-- FADERS: five channel levels, three baseline trims, master, crossfade -->')
for lay in (1, 2, 3, 4, 5):
    rec('track fader %d' % lay, 'CC', 7, lay, 'layer %d opacity' % lay,
        sc_fader('/composition/layers/%d/video/opacity' % lay, cc_key(7, lay)))
for ch, col, nick in ((6, 6, 'TONE'), (7, 7, 'BARS'), (8, 8, 'SNOW')):
    rec('track fader %d' % ch, 'CC', 7, ch,
        'clip opacity trim %s (L1 C%d)' % (nick, col),
        sc_fader('/composition/layers/1/clips/%d/video/opacity' % col,
                 cc_key(7, ch)))
rec('master fader', 'CC', 14, 1, 'composition master',
    sc_fader('/composition/master', cc_key(14, 1), value='1', allowed='1'))
rec('crossfader', 'CC', 15, 1, 'crossfader phase',
    sc_fader('/composition/crossfader/phase', cc_key(15, 1), value='0.5', allowed='1'))

add('\t\t<!-- DEVICE KNOBS: the rack\'s own dials + the four row lamps -->')
KNOBS = [
    ('/composition/video/effects/huerotate/effect/huerotate', 'comp hue rotate'),
    ('/composition/video/effects/shiftrgb/effect/distance', 'comp RGB shift distance'),
    ('/composition/video/effects/lorezeffect/effect/pixelsize', 'comp pixel size'),
    ('/composition/video/effects/lorezeffect/effect/bitreduction', 'comp bit reduction'),
    ('/composition/layers/2/video/effects/bloom/effect/brightness', 'TRACE lamp brightness'),
    ('/composition/layers/3/video/effects/bloom/effect/brightness', 'NEEDLE lamp brightness'),
    ('/composition/layers/4/video/effects/bloom/effect/brightness', 'STAMP lamp brightness'),
    ('/composition/layers/5/video/effects/bloom/effect/brightness', 'READOUT lamp brightness'),
]
for i, (p, gloss) in enumerate(KNOBS):
    rec('device knob %d' % (i + 1), 'CC', 16 + i, 1, gloss,
        sc_fader(p, cc_key(16 + i, 1), value='0', allowed='1'))

add('\t\t<!-- TRACK KNOBS = the selected clip\'s own eight dials -->')
for i in range(8):
    rec('track knob %d' % (i + 1), 'CC', 48 + i, 1,
        'selected clip dashboard link %d' % (i + 1),
        sc_dashboard(i + 1, cc_key(48 + i, 1)))

add('\t\t<!-- THE ODD THREE: cue wheel, calibration screw, stomp pedal -->')
rec('cue level', 'CC', 47, 1, 'selected clip transport position',
    sc_fader('/composition/selectedclip/transport/position', cc_key(47, 1),
             value='0', allowed='1'))
rec('tempo', 'CC', 13, 1, 'RELATIVE: rotate CAL DIAL (L3 C8 transform)',
    sc_relative('/composition/layers/3/clips/8/video/effects/transform/rotationz',
                cc_key(13, 1)))
rec('footswitch', 'CC', 64, 1, 'THE STOMP: hold for RGB split (spring to 0)',
    sc_fader('/composition/video/effects/shiftrgb/effect/distance',
             cc_key(64, 1), value='0', allowed='1'))

# ---------------------------------------------------------------- assemble
doc = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<MidiShortcutPreset presetId="2026080701" name="%s">\n'
       '\t<versionInfo name="Resolume Avenue" majorVersion="7" minorVersion="27" microVersion="0" revision="14395" />\n'
       '\t<ShortcutManager name="MIDIShortcutManagerShortcuts">\n'
       '%s\n'
       '\t</ShortcutManager>\n'
       '</MidiShortcutPreset>\n' % (NAME, '\n'.join(S)))

# ---------------------------------------------------------------- validate
ET.fromstring(doc.encode('utf-8'))

# 1. Every physical control on the APC40 mkII surface, exactly once.
census = set()
for n in range(40):
    census.add(('NOTE', n, 1))
for n in range(82, 87):
    census.add(('NOTE', n, 1))
census.add(('NOTE', 81, 1)); census.add(('NOTE', 80, 1))
for ch in range(1, 9):
    for n in (48, 49, 50, 51, 52, 66):
        census.add(('NOTE', n, ch))
for n in (87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102,
          103, 58, 59, 60, 61, 62, 63, 64, 65):
    census.add(('NOTE', n, 1))
for c in range(48, 56):
    census.add(('CC', c, 1))
for c in range(16, 24):
    census.add(('CC', c, 1))
for ch in range(1, 9):
    census.add(('CC', 7, ch))
for c in (47, 13, 14, 15, 64):
    census.add(('CC', c, 1))
assert len(census) == 149

mapped = {(k, n, ch) for _, k, n, ch, _ in CONTROL_MAP}
assert mapped == census, ('surface census mismatch: missing %s extra %s'
                          % (sorted(census - mapped), sorted(mapped - census)))

keys = re.findall(r'RawInputMessage key="(\d+)"', doc)
assert len(keys) == len(CONTROL_MAP) == 149
assert len(keys) == len(set(keys)), 'duplicate MIDI keys'
ids = re.findall(r'uniqueId="(\d+)"', doc)
assert len(ids) == len(set(ids)), 'duplicate uniqueIds'

# 2. Tier rule: CC48-55 appear only as selected-clip dashboard links.
for m in re.finditer(r'<Shortcut\b.*?</Shortcut>', doc, re.S):
    blk = m.group(0)
    key = int(re.search(r'RawInputMessage key="(\d+)"', blk).group(1))
    if key >= 2 * B and 48 <= ((key - 2 * B) >> 8) <= 55:
        assert '/composition/selectedclip/dashboard/link' in blk, \
            'CC48-55 outside Tier A'

# 3. Every duplicated input path is a declared mirror - nothing sneaks in.
MIRRORS = {
    '/composition/connectprevcolumn': 2,        # up + nudge -
    '/composition/connectnextcolumn': 2,        # down + nudge +
    '/composition/selectnextdeck': 2,           # right + bank >
    '/composition/selectprevdeck': 2,           # left + bank <
    '/composition/layers/3/connectnextclip': 2, # rec arm 3 + device <
    '/composition/layers/4/connectnextclip': 2, # rec arm 4 + device >
    '/composition/layers/1/clips/1/connect': 3, # pad + A/B 1 + bank
    '/composition/layers/2/clips/2/connect': 2, # pad + A/B 2
    '/composition/layers/3/clips/3/connect': 2, # pad + A/B 3
    '/composition/layers/4/clips/4/connect': 2, # pad + A/B 4
    '/composition/layers/5/clips/5/connect': 2, # pad + A/B 5
    '/composition/layers/1/clips/6/connect': 3, # pad + A/B 6 + pan (TONE)
    '/composition/layers/2/clips/7/connect': 3, # pad + A/B 7 + rec arm 7
    '/composition/layers/3/clips/8/connect': 3, # pad + A/B 8 + detail (CAL)
    '/composition/layers/1/clips/7/connect': 2, # pad + sends (BARS)
    '/composition/layers/1/clips/8/connect': 2, # pad + user (SNOW)
    '/composition/layers/2/clips/6/connect': 2, # pad + rec arm 6
    '/composition/layers/2/clips/8/connect': 2, # pad + rec arm 8
    '/composition/layers/4/clips/1/connect': 2, # pad + solo 6
    '/composition/layers/4/clips/3/connect': 2, # pad + solo 7
    '/composition/layers/4/clips/5/connect': 2, # pad + solo 8
    '/composition/layers/4/clips/8/connect': 2, # pad + metronome (PILOT)
    '/composition/layers/5/clips/6/connect': 2, # pad + record (SLATE)
    '/composition/layers/5/clips/7/connect': 2, # pad + shift (SIGNAL LOST)
    '/composition/layers/5/clips/8/connect': 2, # pad + master (TEST CARD)
    '/composition/layers/3/clips/6/connect': 2, # pad + session (DATA CARD)
    '/composition/video/effects/shiftrgb/effect/distance': 2,  # knob 2 + stomp
}
from collections import Counter
paths = Counter(re.findall(r'name="InputPath" path="([^"]+)"', doc))
for p, c in paths.items():
    if c > 1:
        assert MIRRORS.get(p) == c, 'undeclared duplicate path %s x%d' % (p, c)
for p, c in MIRRORS.items():
    assert paths[p] == c, 'mirror %s expected x%d got x%d' % (p, c, paths[p])

open(OUT, 'w', encoding='utf-8', newline='').write(doc)
with open(CMAP, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('control\tkind\tnum\tchannel\taction\n')
    for control, kind, num, ch, action in CONTROL_MAP:
        fh.write('%s\t%s\t%d\t%d\t%s\n' % (control, kind, num, ch, action))

print('WROTE %s  %d bytes | shortcuts=%d  surface=%d/149  unique keys=%d'
      % (os.path.normpath(OUT), len(doc.encode('utf-8')), doc.count('<Shortcut '),
         len(mapped & census), len(set(keys))))
print('WROTE %s' % os.path.normpath(CMAP))
