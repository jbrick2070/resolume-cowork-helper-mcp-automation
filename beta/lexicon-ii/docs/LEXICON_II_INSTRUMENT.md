# Res React Lexicon II — Eighties-ism

**Built 2026-08-05 overnight. New files only — no existing composition or preset was
opened for writing.** Successor pack to `lexicon/` (v1); the machine is unchanged,
the words are a found-text corpus.

---

## 1. The idea

v1 was a grammar machine with invented words. v2 keeps the machine — five rows =
**SUBJECT / VERB / OBJECT / MARK / FIELD**, eight pads per row, every press-path
builds a line live — and feeds it the supplied corpus of 120 found texts
(art-world slogans, film intertitles, agitprop, Rrose Sélavy French wordplay),
**sliced and diced**, mixed with added broadcast-age vocabulary.

One composition, **five decks** — channel surfing:

| CH | Deck | Register |
|---|---|---|
| 01 | **Master** | every register mushed together — the good one |
| 02 | **Ad Break** | consumer broadcast: TELEVISION DELIVERS PEOPLE |
| 03 | **The Sermon** | truisms & commandments: TASTE IS THE ENEMY OF ART |
| 04 | **The Reel** | film language: intertitles, Vertov, THE END |
| 05 | **La Nuit** | French wordplay: L'ASPIRANT HABITE JAVEL |

5 decks × 40 pads = **200 clips, all true Text Block generators** — no video files,
no PNG renders, no plugins. Every included line from `TERMS_SOURCE.txt` appears
somewhere on the grids, whole or as a verbatim cut: **120/120 covered, 188 of 200
pads are cuts from the corpus, 12 are added 80s words** (the build asserts this and
fails if a term goes missing). Excluded per instruction: the three AIDS-related
lines, plus two duplicates.

Sample fired lines: `AMERICA IS NOT AMERICA'S FLAG` · `TELEVISION PROTECT ME FROM
WHAT I WANT` · `THE AUTHOR TOOK PITY ON A SIXTH PART OF THE WORLD — Suddenly…` ·
`LES DENTS DES FEMMES S'ARRÊTE DE COULER BELLE`.

## 2. Files

| File | Goes to | Notes |
|---|---|---|
| `Res React Lexicon II.avc` | `Documents\Resolume Avenue\Compositions\` | 5 decks × 5 layers × 8 columns |
| `APC 40 MK II - Lexicon v2.xml` | `Documents\Resolume Avenue\Shortcuts\MIDI\` | 98 shortcuts (input AND output) |
| `TERMS_SOURCE.txt` | here | the corpus; `-` lines are excluded with reason |
| `lexicon2_content.py` | here | the 200 cells — edit words here |
| `build_lexicon2.py` | here | regenerates the .avc + `_grid_manifest.tsv` |
| `gen_preset2.py` / `gen_padmap2.py` | here | regenerate preset / pad map |
| `lexicon2_pad_map.html` | here | stage reference, all five decks |

Rebuild cycle: edit `lexicon2_content.py` → `python build_lexicon2.py` →
`python gen_padmap2.py`. The build validates XML, unique IDs, counts, verbatim-cut
substrings, and full corpus coverage before writing.

## 3. What changed vs v1

- **Channel surf.** Bank `<` `>` = previous / next deck (`selectprevdeck` /
  `selectnextdeck`, the proven donor paths; they wrap). Column stepping is gone —
  Track Select 1-8 still fires whole columns.
- **New dial bank** (track knobs, per selected clip, canonical translationType 4):

  | Dial | v1 | v2 |
  |---|---|---|
  | 1 | SIZE | SIZE |
  | 2 | GLOW | GLOW |
  | 3 | BLOOM | **BRIGHT** — text colour brightness (colour on a knob) |
  | 4 | HALO | **FADE** (clip opacity) on word rows / **THRESH** on Field+Mark |
  | 5 | THRESH | BLOOM |
  | 6-8 | WARP · RIPPLE · DRIFT | unchanged |

  Dial 3 drives the `Brightness` channel inside the clip's `ParamColor` (the
  rig-saved Channels species). Dial 4 can't be opacity on Field/Mark because the
  **FFT owns their opacity** — those rows label it THRESH (bloom threshold), and
  the altNames are written per clip so the software shows the right label either way.
  Composition Hue Rotate stays on device knob 1 for hue sweeps across everything.
- **Fonts on a knob: not possible in this file format.** Text Block exposes no
  font parameter in any donor XML, and dashboard links only drive numeric ranges.
  Colour (BRIGHT + Hue Rotate), opacity (FADE) and size are the knobbable axes.
- **Multi-line text.** Long texts are hard-wrapped with `&#10;` character
  references and auto-sized so each block fits its band (a Vertov manifesto and
  the word HEAT both land). *Rendering of embedded newlines in Text Block is
  unverified on the rig* — if a paragraph renders as one long line, rebuild with
  `python build_lexicon2.py --nowrap`… (v2 note: the flag was dropped; if this
  bites, shrink `wrapChars` per row in `LAYERS` instead and rebuild). French
  accents (é è ë …) are also first-time glyphs for this font — QA on load.
- Everything else is v1 verbatim: palette/LED map, FFT (Field=bass breath 800 ms,
  Mark=highs snap 200 ms, sweep floors keep both visible with no audio),
  comp FX rack bypassed on load, no Trails/Freeze pair, faders/scene/activator/
  solo/clip-stop map identical.

## 3b. Verified + deliberate choices (verify-panel pass, 2026-08-05)

A three-agent panel (machine contract / donor XML species / grammar) reviewed the
build: **0 blockers**. Applied: The Reel verbs went past-tense (agreement-neutral
intertitle register), La Nuit normalized to 3sg with column 0 as its one
column-aligned plural fire (`LES DENTS DES FEMMES SONT DES OBJETS SI CHARMANTS`),
Master `WATCHES` → `WATCHED`, derived cells now carry the source's curly
apostrophes / en-dashes. Deliberate keeps: `/audioengine/externalfft` (the
rig-verified v1 id — the donor's `compositionfft` is a different, internal
source); Field's translucent slate alpha (v1 palette); lowercase
`housing is a human right` as the sincere closer under the Amen column; a handful
of surreal Master pairings (`THE UNEMPLOYED IS…`) as accepted mush-deck noise.

## 4. First-load QA (morning checklist)

1. Copy both files in, select the v2 preset for input **and** output.
2. Load the comp — check the five deck tabs appear, Master first.
3. Fire Master column 1; confirm the stack reads top-to-bottom and the Mark
   stamps at the bottom.
4. Check a paragraph Field pad (Ad Break col 6 — the consumer line): does it wrap?
   If it's one long line → shrink `wrapChars` / see §3.
5. Check La Nuit for accented glyphs (É È ë ô). Any missing-glyph boxes → swap
   the cell text in `lexicon2_content.py`, rebuild.
6. Bank arrows: channel-surf all five decks, wrap-around.
7. Track knobs 1-8 on a selected clip: SIZE, GLOW, BRIGHT, FADE/THRESH, BLOOM,
   WARP, RIPPLE, DRIFT (enable "Update clip panels on external triggers").
8. Saving from Avenue will regenerate thumbnails — that's fine here (no injected
   images in v2, text thumbs are Resolume's own).
