# gen_padmap2.py - render lexicon2_pad_map.html from _grid_manifest.tsv.
# The manifest is the single source of truth (written by build_lexicon2.py);
# this script never hand-holds a word list of its own.
import io, html

ROWCOL = {'Subject': '#FFF4E0', 'Verb': '#FFB020', 'Object': '#46E0FF',
          'Mark': '#FF3CC8', 'Field': '#7C8A9C'}
ROWNOTE = {'Subject': 'notes 32-39', 'Verb': 'notes 24-31', 'Object': 'notes 16-23',
           'Mark': 'notes 8-15', 'Field': 'notes 0-7'}
ORDER = ['Subject', 'Verb', 'Object', 'Mark', 'Field']   # top pad row to bottom

decks, cols, grid, added = [], {}, {}, set()
for i, ln in enumerate(io.open('_grid_manifest.tsv', encoding='utf-8')):
    if i == 0 or not ln.strip():
        continue
    di, deck, li, row, ci, col, size, posy, nl, src, text = ln.rstrip('\n').split('\t')
    if deck not in decks:
        decks.append(deck)
        cols[deck] = [''] * 8
        grid[deck] = {r: [''] * 8 for r in ORDER}
    cols[deck][int(ci)] = col
    grid[deck][row][int(ci)] = text
    if src == 'ADDED':
        added.add((deck, row, int(ci)))

P = []
P.append('<!doctype html><meta charset="utf-8"><title>Res React Lexicon II — pad map</title>\n'
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
' padding:9px 7px;min-height:56px;display:flex;flex-direction:column;justify-content:center;text-align:center}\n'
'.w{color:var(--c);font-weight:650;font-size:12.5px;line-height:1.25;word-break:break-word}\n'
'.pad.long .w{font-size:10px;font-weight:500}\n'
'.pad.add{border-style:dashed}\n'
'.legend{display:flex;gap:44px;margin-top:26px;flex-wrap:wrap}\n'
'.legend h3{font-size:12px;color:#8b8b98;font-weight:600;margin:0 0 7px;letter-spacing:.06em}\n'
'ul{margin:0;padding:0;list-style:none;font-size:12.5px;color:#c9c9d4}\n'
'li{padding:1.5px 0} li b{color:#8b8b98;display:inline-block;width:18px}\n'
'.note{margin-top:22px;color:#6c6c7a;font-size:11.5px;max-width:820px;line-height:1.6}\n'
'</style>\n'
'<h1>Res React Lexicon II — Eighties-ism · pad map</h1>\n'
'<div class="sub">APC40 mkII · 5 decks × 40 pads · 120 found texts, sliced · '
'dashed border = added broadcast word · Bank &lt; &gt; = channel surf</div>\n')

for deck in decks:
    P.append('<h2>CH %02d · %s<span>Bank arrows cycle channels</span></h2>\n'
             % (decks.index(deck) + 1, html.escape(deck.upper())))
    P.append('<div class="grid"><div></div>')
    for i, cn in enumerate(cols[deck]):
        P.append('<div class="col">%d<span style="display:block;color:#5d5d6b;font-size:10px">%s</span></div>'
                 % (i + 1, html.escape(cn)))
    for row in ORDER:
        c = ROWCOL[row]
        P.append('<div class="rowlabel"><b style="color:%s">%s</b><span>%s</span></div>'
                 % (c, row, ROWNOTE[row]))
        for i in range(8):
            text = grid[deck][row][i]
            cls = 'pad'
            if len(text) > 40:
                cls += ' long'
            if (deck, row, i) in added:
                cls += ' add'
            P.append('<div class="%s" style="--c:%s"><div class="w">%s</div></div>'
                     % (cls, c, html.escape(text)))
    P.append('</div>\n')

P.append(
'<div class="legend">\n'
'<div><h3>TRACK KNOBS 1–8 · per pad</h3><ul><li><b>1</b> SIZE</li><li><b>2</b> GLOW</li>'
'<li><b>3</b> BRIGHT (colour)</li><li><b>4</b> FADE · word rows / THRESH · Field+Mark</li>'
'<li><b>5</b> BLOOM</li><li><b>6</b> WARP</li><li><b>7</b> RIPPLE</li><li><b>8</b> DRIFT</li></ul></div>\n'
'<div><h3>SURFACE</h3><ul>\n'
'<li><b>▸</b> Track Select 1–8 — fire a whole column</li>\n'
'<li><b>▸</b> Scene Launch 1–5 — drop that row out</li>\n'
'<li><b>▸</b> Clip Stop 1–6 — comp FX toggles</li>\n'
'<li><b>▸</b> Activator / Solo 1–5 — mute / isolate a row</li>\n'
'<li><b>▸</b> Faders 1–5 — presence per row</li>\n'
'<li><b>▸</b> Bank &lt; &gt; — CHANNEL SURF (prev / next deck)</li>\n'
'</ul></div>\n'
'<div><h3>AUDIO</h3><ul>\n'
'<li><b>▸</b> Field row rides the <b>bass</b></li>\n'
'<li><b>▸</b> Mark row rides the <b>highs</b></li>\n'
'<li><b>▸</b> External FFT — set Avenue audio input</li>\n'
'<li><b>▸</b> Subject/Verb/Object stay static, always legible</li>\n'
'</ul></div></div>\n'
'<div class="note">Every included line from the source list appears somewhere on these five grids, whole or as a '
'verbatim cut — 188 of the 200 pads are cuts from the corpus, 12 are added broadcast-age words (dashed). '
'Preset <b>APC 40 MK II - Lexicon v2</b> — select it for input <i>and</i> output so the pads light.</div>\n')

io.open('lexicon2_pad_map.html', 'w', encoding='utf-8', newline='\n').write(''.join(P))
print('WROTE lexicon2_pad_map.html')
