# gen_preset.py - build "APC 40 MK II - Lexicon v1.xml" for the Res React Lexicon comp.
# NEW FILE ONLY. Every shortcut block is cloned byte-for-byte from a species observed in
# the rig-saved "APC 40 MK II - React v4.4.xml"; only path / MIDI key / uniqueId / LED
# values change. No existing preset is read-modify-written.
import re
import xml.etree.ElementTree as ET

OUT = 'APC 40 MK II - Lexicon v1.xml'
NAME = 'APC 40 MK II - Lexicon v1'
DEV = 'APC40 mkII'

B = 1 << 56
def note_key(n, ch=1):
    return B + n * 256 + (0x90 + ch - 1)
def cc_key(c, ch=1):
    return 2 * B + c * 256 + (0xB0 + ch - 1)

_id = [1785400000000]
def nid():
    _id[0] += 1
    return str(_id[0])

def vel(v):
    return repr(v / 127.0)

S = []
def add(x):
    S.append(x)

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
# grid rows, top of the APC to the bottom. Row note base -> comp layer + LED colour.
ROWS = [
    (32, 2, 'Subject', 3,  3),   # top pad row     -> layer 2, white
    (24, 3, 'Verb',    8,  9),   #                 -> layer 3, amber
    (16, 4, 'Object',  36, 37),  #                 -> layer 4, sky
    (8,  5, 'Mark',    52, 53),  #                 -> layer 5, pink
    (0,  1, 'Field',   44, 45),  # bottom pad row  -> layer 1, violet
]

add('\t\t<!-- GRID: 5 rows x 8 columns = the sentence. Top row Subject, then Verb, Object,\n'
    '\t\t     Mark; bottom row Field. Row colour matches the on-screen colour of that slot. -->')
for base, lay, role, on_v, off_v in ROWS:
    for c in range(8):
        p = '/composition/layers/%d/clips/%d/connect' % (lay, c + 1)
        sib = '/composition/layers/%d/clips/%d/connected' % (lay, c + 1)
        named = [('Connected', vel(on_v)), ('Connected &amp; previewing', vel(on_v)),
                 ('Disconnected', vel(off_v)), ('Empty', vel(off_v)),
                 ('Off', '0'), ('Previewing', vel(off_v))]
        add(sc_connect(p, sib, note_key(base + c, 1), named))

add('\t\t<!-- TRACK SELECT 1-8 = fire a whole sentence (column 1-8) -->')
for c in range(8):
    add(sc_column('/composition/columns/%d/connect' % (c + 1),
                  '/composition/columns/%d/connected' % (c + 1), note_key(51, c + 1)))

add('\t\t<!-- SCENE LAUNCH 1-5 = drop that grammar slot out (layer clear), aligned with the rows -->')
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

add('\t\t<!-- ACTIVATOR = mute a grammar slot, SOLO = isolate it -->')
for base, lay, role, a, b in ROWS:
    add(sc_bool('/composition/layers/%d/bypassed' % lay, note_key(48, lay),
                '0.16535433070866143', '0.055118110236220472'))
for base, lay, role, a, b in ROWS:
    add(sc_solo(lay, note_key(49, lay)))

add('\t\t<!-- FADERS 1-5 = how present each grammar slot is. 8 = crossfade-free master trim -->')
for lay in (1, 2, 3, 4, 5):
    add(sc_fader('/composition/layers/%d/video/opacity' % lay, cc_key(7, lay)))
add(sc_fader('/composition/master', cc_key(14, 1), value='1', allowed='1'))
add(sc_fader('/composition/crossfader/phase', cc_key(15, 1), value='0.5', allowed='1'))

add('\t\t<!-- DEVICE KNOBS 1-4 = composition FX. 5-8 = glow per grammar slot -->')
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

add('\t\t<!-- TRACK KNOBS 1-8 = the selected clip\'s own dials (canonical translationType 4) -->')
for i in range(8):
    add(sc_dashboard(i + 1, cc_key(48 + i, 1)))

add('\t\t<!-- TRANSPORT -->')
add(sc_fader('/composition/selectedclip/transport/position', cc_key(47, 1), value='0', allowed='1'))
add(sc_trigger('/composition/tempocontroller/tempotap', note_key(99, 1)))
add(sc_trigger('/composition/tempocontroller/resync', note_key(91, 1)))
add(sc_trigger('/composition/disconnectall', note_key(81, 1)))
add(sc_trigger('/composition/connectnextcolumn', note_key(96, 1)))
add(sc_trigger('/composition/connectprevcolumn', note_key(97, 1)))

# ---------------------------------------------------------------- assemble
doc = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<MidiShortcutPreset presetId="2026073101" name="%s">\n'
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
open(OUT, 'w', encoding='utf-8', newline='').write(doc)
print('WROTE %s  %d bytes | shortcuts=%d  unique MIDI keys=%d'
      % (OUT, len(doc.encode('utf-8')), doc.count('<Shortcut '), len(set(keys))))
