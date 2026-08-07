# gen_padmap_telemetry.py - render telemetry_pad_map.html, the stage reference.
# Reads docs/_grid_manifest.tsv (written by build_telemetry.py) for the cells
# and telemetry_content.py for the column names.
import io, os, html
from telemetry_content import DECKS, COLUMNS

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, '..', 'docs', '_grid_manifest.tsv')
OUT = os.path.join(HERE, '..', 'docs', 'telemetry_pad_map.html')

# Pad LED colours (constant across decks - the preset's row palette).
ROWCOL = {'READOUT': '#F2F2F2', 'STAMP': '#FF3CC8', 'NEEDLE': '#FFB020',
          'TRACE': '#46E0FF', 'PAPER': '#9B7CF0'}
ROWNOTE = {'READOUT': 'notes 32-39', 'STAMP': 'notes 24-31', 'NEEDLE': 'notes 16-23',
           'TRACE': 'notes 8-15', 'PAPER': 'notes 0-7'}
ORDER = ['READOUT', 'STAMP', 'NEEDLE', 'TRACE', 'PAPER']   # top pad row to bottom

grid, kinds, pres = {}, {}, {}
for i, ln in enumerate(io.open(MANIFEST, encoding='utf-8')):
    if i == 0 or not ln.strip():
        continue
    deck, li, row, ci, kind, label, size, posy, nl, presence = ln.rstrip('\n').split('\t')
    grid.setdefault(deck, {r: [''] * 8 for r in ORDER})[row][int(ci) - 1] = label
    kinds.setdefault(deck, {})[(row, int(ci) - 1)] = kind
    pres.setdefault(deck, {})[(row, int(ci) - 1)] = presence

P = []
P.append('<!doctype html><meta charset="utf-8"><title>Res React Telemetry — pad map</title>\n'
'<style>\n'
':root{color-scheme:dark}\n'
'body{background:#0a0a0c;color:#e8e8ee;font:14px/1.45 ui-sans-serif,system-ui,Segoe UI,sans-serif;margin:0;padding:28px 32px}\n'
'h1{font-size:20px;margin:0 0 2px;letter-spacing:.02em}\n'
'h2{font-size:15px;margin:30px 0 8px;color:#c9c9d4;letter-spacing:.05em}\n'
'h2 span{color:#5d5d6b;font-weight:400;font-size:12px;margin-left:10px}\n'
'.sub{color:#8b8b98;font-size:13px;margin-bottom:10px}\n'
'.grid{display:grid;grid-template-columns:120px repeat(8,1fr);gap:6px}\n'
'.col{font-size:11px;color:#8b8b98;text-align:center;padding-bottom:2px}\n'
'.rowlabel{display:flex;flex-direction:column;justify-content:center;font-size:12px;padding-right:10px}\n'
'.rowlabel span{color:#5d5d6b;font-size:10px}\n'
'.pad{border:1px solid color-mix(in srgb,var(--c) 34%,#0a0a0c);border-radius:7px;background:\n'
' linear-gradient(180deg,color-mix(in srgb,var(--c) 9%,#0a0a0c),#0a0a0c);\n'
' padding:9px 7px;min-height:56px;display:flex;flex-direction:column;justify-content:center;text-align:center;position:relative}\n'
'.w{color:var(--c);font-weight:650;font-size:12.5px;line-height:1.25;word-break:break-word}\n'
'.pad.gen{border-style:dashed}\n'
'.pad .fft{position:absolute;top:4px;right:6px;font-size:9px;color:#5d5d6b}\n'
'.legend{display:flex;gap:44px;margin-top:26px;flex-wrap:wrap}\n'
'.legend h3{font-size:12px;color:#8b8b98;font-weight:600;margin:0 0 7px;letter-spacing:.06em}\n'
'ul{margin:0;padding:0;list-style:none;font-size:12.5px;color:#c9c9d4}\n'
'li{padding:1.5px 0} li b{color:#8b8b98;display:inline-block;min-width:18px}\n'
'.note{margin-top:22px;color:#6c6c7a;font-size:11.5px;max-width:860px;line-height:1.6}\n'
'</style>\n'
'<h1>Res React Telemetry — The Measuring Room · pad map</h1>\n'
'<div class="sub">APC40 mkII · 5 instruments × 40 pads · every one of the 149 physical controls does something · '
'dashed border = non-text generator (SNOW / PILOT / CAL DIAL) · ~ = cell rides the FFT</div>\n')

INSTRUMENT_TAG = {
    'THE EKG': 'heartbeat snaps on a narrowed bass gate',
    'THE RICHTER': 'the ground swells on the bass',
    'THE VU': 'BASS / MID / HIGH columns = a live 3-band analyzer',
    'THE POLYGRAPH': 'the needles ride the mids - the voice is the lie',
    'THE GEIGER': 'the clicks sparkle on the highs',
}

for deck in DECKS:
    P.append('<h2>CH %02d · %s<span>%s</span></h2>\n'
             % (DECKS.index(deck) + 1, html.escape(deck),
                html.escape(INSTRUMENT_TAG[deck])))
    P.append('<div class="grid"><div></div>')
    for i, cn in enumerate(COLUMNS[deck]):
        P.append('<div class="col">%d<span style="display:block;color:#5d5d6b;font-size:10px">%s</span></div>'
                 % (i + 1, html.escape(cn)))
    for row in ORDER:
        c = ROWCOL[row]
        P.append('<div class="rowlabel"><b style="color:%s">%s</b><span>%s</span></div>'
                 % (c, row, ROWNOTE[row]))
        for i in range(8):
            label = grid[deck][row][i]
            cls = 'pad'
            if kinds[deck][(row, i)] != 'text':
                cls += ' gen'
            fft = '<span class="fft">~</span>' if pres[deck][(row, i)].startswith('fft') else ''
            P.append('<div class="%s" style="--c:%s">%s<div class="w">%s</div></div>'
                     % (cls, c, fft, html.escape(label)))
    P.append('</div>\n')

P.append(
'<div class="legend">\n'
'<div><h3>TRACK KNOBS 1–8 · per pad</h3><ul><li><b>1</b> GAIN (size)</li><li><b>2</b> PHOSPHOR (glow)</li>'
'<li><b>3</b> EXCITE (brightness)</li><li><b>4</b> PAPER (fade) / TRIG (threshold) on FFT cells</li>'
'<li><b>5</b> HALO (bloom)</li><li><b>6</b> QUAKE H</li><li><b>7</b> QUAKE W</li><li><b>8</b> SWEEP</li></ul></div>\n'
'<div><h3>SURFACE — ALL 149</h3><ul>\n'
'<li><b>▸</b> Track Select 1–8 — fire a whole reading (column)</li>\n'
'<li><b>▸</b> Scene Launch 1–5 — lift the pen (clear that row)</li>\n'
'<li><b>▸</b> Clip Stop 1–8 — the instrument rack (8 comp FX)</li>\n'
'<li><b>▸</b> Activator 1–5 / 6–8 — channel power / row lamps</li>\n'
'<li><b>▸</b> Solo 1–5 / 6–8 — isolate / verdict spotlights</li>\n'
'<li><b>▸</b> Rec Arm 1–5 / 6–8 — ROLL a row / force states</li>\n'
'<li><b>▸</b> A/B row — the diagonal walk (8 presses = a look)</li>\n'
'<li><b>▸</b> Pan / Sends / User — TONE / BARS / SNOW</li>\n'
'<li><b>▸</b> ◀ ▶ + Bank &lt; &gt; — instrument dial (decks)</li>\n'
'<li><b>▸</b> ▲ ▼ + Nudge — paper feed (columns)</li>\n'
'<li><b>▸</b> Faders 6–8 — TONE / BARS / SNOW trims</li>\n'
'<li><b>▸</b> Tempo knob — RELATIVE calibration screw (CAL DIAL)</li>\n'
'<li><b>▸</b> Footswitch — THE STOMP (hold for RGB split)</li>\n'
'</ul></div>\n'
'<div><h3>AUDIO — WHAT MEASURES WHAT</h3><ul>\n'
'<li><b>~</b> EKG trace — narrowed bass, +9 dB, 150 ms snap</li>\n'
'<li><b>~</b> Richter trace — bass swell, 1200 ms fall</li>\n'
'<li><b>~</b> VU columns — bass / mids / highs, one band each</li>\n'
'<li><b>~</b> Polygraph needles — the mids (the voice)</li>\n'
'<li><b>~</b> Geiger stamps — highs, +9 dB, 100 ms clicks</li>\n'
'<li><b>~</b> PILOT strobes — one per deck, bass-gated, floor 0</li>\n'
'<li><b>▸</b> External FFT — set Avenue\'s audio input device</li>\n'
'</ul></div></div>\n'
'<div class="note">Five fictional instruments, all pointed at the same room: whatever the music does, the machines '
'report it. 185 pads are native Text Block rasters (block-element typography); per deck one SNOW (Static), one '
'PILOT (Stroboscope) and one CAL DIAL (Shaper). Preset <b>APC 40 MK II - Telemetry v1</b> — select it for input '
'<i>and</i> output so the pads light. Mirrored buttons (marked in _control_map.tsv) are deliberate: the same cue '
'under a second finger.</div>\n')

io.open(OUT, 'w', encoding='utf-8', newline='\n').write(''.join(P))
print('WROTE %s' % os.path.normpath(OUT))
