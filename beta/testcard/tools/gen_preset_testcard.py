# gen_preset_testcard.py - build "APC 40 MK II - TestCard v1.xml".
# NEW FILE ONLY. Every shortcut species is the rig-proven form from the Lexicon
# presets (v1 verified 2026-07-31, v2 loaded live 2026-08-06); only paths, MIDI
# keys, uniqueIds and LED velocities differ. Bank arrows are the v4.2-verified
# deck surf (selectprevdeck / selectnextdeck).
import re
import xml.etree.ElementTree as ET

OUT = 'APC 40 MK II - TestCard v1.xml'
NAME = 'APC 40 MK II - TestCard v1'
DEV = 'APC40 mkII'

B = 1 << 56
def note_key(n, ch=1):
    return B + n * 256 + (0x90 + ch - 1)
def cc_key(c, ch=1):
    return 2 * B + c * 256 + (0xB0 + ch - 1)

_id = [1786500000000]
def nid():
    _id[0] += 1
    return str(_id[0])

def vel(v):
    return repr(v / 127.0)

S = []
def add(x):
    S.append(x)

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

def sc_column(path, sibling, key):
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

# ---------------------------------------------------------------- surface map
# Grid rows top->bottom. Signal-flow order: Ident on top row (station voice),
# then Pulse, Tone, Sweep; Carrier on the bottom row as the ground.
# LED velocities: (on, off) pairs in APC40 palette space.
ROWS = [
    (32, 5, 'Ident',   3,  3),   # top row    -> layer 5, white
    (24, 4, 'Pulse',   5,  6),   #            -> layer 4, red-orange
    (16, 3, 'Tone',    36, 37),  #            -> layer 3, teal (proven sky pair)
    (8,  2, 'Sweep',   13, 14),  #            -> layer 2, yellow
    (0,  1, 'Carrier', 44, 45),  # bottom row -> layer 1, slate violet
]

add('\t\t<!-- GRID: 5 rows x 8 columns of test signal. Ident on top like a station\n'
    '\t\t     card; Carrier on the bottom row as the ground. LED = row colour. -->')
for base, lay, role, on_v, off_v in ROWS:
    for c in range(8):
        p = '/composition/layers/%d/clips/%d/connect' % (lay, c + 1)
        sib = '/composition/layers/%d/clips/%d/connected' % (lay, c + 1)
        named = [('Connected', vel(on_v)), ('Connected &amp; previewing', vel(on_v)),
                 ('Disconnected', vel(off_v)), ('Empty', vel(off_v)),
                 ('Off', '0'), ('Previewing', vel(off_v))]
        add(sc_connect(p, sib, note_key(base + c, 1), named))

add('\t\t<!-- TRACK SELECT 1-8 = fire a whole signal (column) -->')
for c in range(8):
    add(sc_column('/composition/columns/%d/connect' % (c + 1),
                  '/composition/columns/%d/connected' % (c + 1), note_key(51, c + 1)))

add('\t\t<!-- SCENE LAUNCH 1-5 = kill that band (layer clear), aligned with the rows -->')
for i, (base, lay, role, a, b) in enumerate(ROWS):
    add(sc_trigger('/composition/layers/%d/clear' % lay, note_key(82 + i, 1),
                   '0', '0.0078740157480314959537'))

add('\t\t<!-- CLIP STOP row = composition FX toggles (all bypassed on load) -->')
FXTOG = ['huerotate', 'shiftrgb', 'lorezeffect', 'invertrgb', 'mirrorquad']
for i, fx in enumerate(FXTOG):
    add(sc_bool('/composition/video/effects/%s/bypassed' % fx, note_key(52, i + 1),
                '0.023622047244094488', '0.10236220472440945',
                allowed='1', node='RangedParam[bool]'))
add(sc_bool('/composition/bypassed', note_key(52, 6), '0.023622047244094488',
            '0.10236220472440945', allowed='1', node='RangedParam[bool]'))

add('\t\t<!-- ACTIVATOR = mute a band, SOLO = isolate it -->')
for base, lay, role, a, b in ROWS:
    add(sc_bool('/composition/layers/%d/bypassed' % lay, note_key(48, lay),
                '0.16535433070866143', '0.055118110236220472'))
for base, lay, role, a, b in ROWS:
    add(sc_solo(lay, note_key(49, lay)))

add('\t\t<!-- FADERS 1-5 = band presence. Master + crossfader as ever -->')
for lay in (1, 2, 3, 4, 5):
    add(sc_fader('/composition/layers/%d/video/opacity' % lay, cc_key(7, lay)))
add(sc_fader('/composition/master', cc_key(14, 1), value='1', allowed='1'))
add(sc_fader('/composition/crossfader/phase', cc_key(15, 1), value='0.5', allowed='1'))

add('\t\t<!-- DEVICE KNOBS 1-4 = comp FX. 5-8 = glow per band (Sweep/Tone/Pulse/Ident) -->')
KNOBS = [
    (16, '/composition/video/effects/huerotate/effect/huerotate'),
    (17, '/composition/video/effects/shiftrgb/effect/distance'),
    (18, '/composition/video/effects/lorezeffect/effect/pixelsize'),
    (19, '/composition/video/effects/lorezeffect/effect/bitreduction'),
    (20, '/composition/layers/2/video/effects/bloom/effect/brightness'),
    (21, '/composition/layers/3/video/effects/bloom/effect/brightness'),
    (22, '/composition/layers/4/video/effects/bloom/effect/brightness'),
    (23, '/composition/layers/5/video/effects/bloom/effect/brightness'),
]
for cc, p in KNOBS:
    add(sc_fader(p, cc_key(cc, 1), value='0', allowed='1'))

add('\t\t<!-- TRACK KNOBS 1-8 = selected clip dials: SIZE GLOW BLOOM HALO THRESH WARP RIPPLE DRIFT -->')
for i in range(8):
    add(sc_dashboard(i + 1, cc_key(48 + i, 1)))

add('\t\t<!-- TRANSPORT + DECK SURF -->')
add(sc_fader('/composition/selectedclip/transport/position', cc_key(47, 1), value='0', allowed='1'))
add(sc_trigger('/composition/tempocontroller/tempotap', note_key(99, 1)))
add(sc_trigger('/composition/tempocontroller/resync', note_key(91, 1)))
add(sc_trigger('/composition/disconnectall', note_key(81, 1)))
add(sc_trigger('/composition/selectprevdeck', note_key(96, 1)))
add(sc_trigger('/composition/selectnextdeck', note_key(97, 1)))

doc = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<MidiShortcutPreset presetId="2026080601" name="%s">\n'
       '\t<versionInfo name="Resolume Avenue" majorVersion="7" minorVersion="27" microVersion="0" revision="14395" />\n'
       '\t<ShortcutManager name="MIDIShortcutManagerShortcuts">\n'
       '%s\n'
       '\t</ShortcutManager>\n'
       '</MidiShortcutPreset>\n' % (NAME, '\n'.join(S)))

ET.fromstring(doc.encode('utf-8'))
keys = re.findall(r'RawInputMessage key="(\d+)"', doc)
dupes = sorted(k for k in set(keys) if keys.count(k) > 1)
assert not dupes, 'duplicate MIDI keys: %s' % dupes
ids = re.findall(r'uniqueId="(\d+)"', doc)
assert len(ids) == len(set(ids)), 'duplicate uniqueIds'
n = doc.count('<Shortcut ')
assert n == 98, 'expected 98 shortcuts, got %d' % n
open(OUT, 'w', encoding='utf-8', newline='').write(doc)
print('WROTE %s  %d bytes | shortcuts=%d  unique MIDI keys=%d'
      % (OUT, len(doc.encode('utf-8')), n, len(set(keys))))
