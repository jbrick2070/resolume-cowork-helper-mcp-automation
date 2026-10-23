# Res React Lexicon II — "Eighties-ism"

> **STATUS: BETA — opened once, never played. Not on hardware.**
> Built overnight 2026-08-06 from the XML up. Every claim below was verified against the
> *file format* — it parses, the IDs are unique, the counts hold, the shortcut paths match
> rig-proven donors.
>
> **2026-10-23:** opened for the first time, in Avenue 7.28.1, to photograph it for the
> [gallery](../../gallery/README.md#res-react-lexicon-ii---eighties-ism). It loaded, and columns on
> all five decks rendered their text (the frames are in the gallery; in several, lines from
> different rows overlap). That is all that was tested: no pad has been pressed, no shortcut
> exercised, no knob turned, and the APC40 was not in the loop.
>
> For the brave: it's two files. If it doesn't behave, everything is regenerable from `tools/`
> in one command.

The sequel to the [Lexicon](../lexicon/) sentence machine. Same instrument — five rows =
**SUBJECT / VERB / OBJECT / MARK / FIELD**, eight pads per row, every press-path writes a
line live at drum-fill speed — but the vocabulary is a **found-text corpus of 120 lines**
from the broadcast age: art-world slogans, film intertitles, agitprop, Rrose Sélavy French
wordplay. Sliced into cells, mixed with period television language.

**Five decks. Bank `<` `>` is a channel dial.**

| CH | Deck | Register | Sample fire |
|---|---|---|---|
| 01 | **Master** | everything mushed together | `AMERICA IS NOT AMERICA'S FLAG` |
| 02 | **Ad Break** | consumer broadcast | `TELEVISION DELIVERS PEOPLE` |
| 03 | **The Sermon** | truisms and commandments | `PEACE COMES AS NO SURPRISE — GOD` |
| 04 | **The Reel** | film language | `THE AUTHOR TOOK PITY ON A SIXTH PART OF THE WORLD` |
| 05 | **La Nuit** | French wordplay | `LA MOËLLE DE L'ÉPÉE DONNE UNE PAIRE DE CISEAUX` |

200 pads. 8×8×8 = **512 sentences per channel, 2,560 across the five**, over 8 marks and
8 grounds. **100% native Text Block** — no media, no FFGL, no Wire, no PNG pad images,
nothing to install. The whole pack is 2 MB.

## What's different from v1

- **Channel surf.** Bank `<` `>` = previous / next deck (`selectprevdeck` / `selectnextdeck`,
  wrapping). One 40-pad shortcut set drives all five decks — pad LEDs follow the active one.
- **True text generators, no thumbnails.** v1 shipped 40 injected PNG pad images because
  Resolume's auto-thumbnails came out blank for 6 of them. v2 has none: every pad is a live
  Text Block, so saving from Avenue can't clobber anything.
- **Colour and opacity on knobs.** Dial 3 = **BRIGHT** (text colour brightness, driven
  through the clip's own colour channels). Dial 4 = **FADE** (clip opacity) on the word
  rows, **THRESH** on Field and Mark — those two rows give their opacity to the audio.
  *Fonts on a knob are not possible:* Text Block exposes no font parameter in the file
  format, so colour, opacity and size are the knobbable axes.
- **Auto-sized type.** Each clip's Size is computed from its own character count and line
  count, so a 55-word manifesto and the word `HEAT` both land inside their band.
- Unchanged from v1: palette and LED map, FFT (Field breathes on bass, Mark snaps on highs,
  sweep floors keep both visible with no audio), comp FX rack bypassed on load, faders /
  scene launch / activator / solo / clip-stop.

## Contents

```
beta/lexicon-ii/
  compositions/  Res React Lexicon II.avc          5 decks x 5 layers x 8 columns,
                                                   200 Text Block clips, 1,600 dashboard links
  controllers/   APC 40 MK II - Lexicon v2.xml     98 shortcuts, every physical control
  tools/         lexicon2_content.py               THE WORDS — edit here
                 build_lexicon2.py                 regenerates the .avc + the manifest
                 gen_preset2.py                    regenerates the controller preset
                 gen_padmap2.py                    regenerates the pad map
                 TERMS_SOURCE.txt                  the 120-line source corpus
  docs/          lexicon2_pad_map.html             stage reference, all five channels
                 LEXICON_II_INSTRUMENT.md          the full build note
                 _grid_manifest.tsv                every pad: deck/row/column/size/source
```

Rebuild cycle: edit `tools/lexicon2_content.py` → `python build_lexicon2.py` →
`python gen_padmap2.py`. The build refuses to write unless the XML parses, IDs are unique,
counts hold, **every cell is a verbatim cut of a real source line**, and **all 120 source
lines are still on the grid**. 188 of the 200 pads are corpus cuts; 12 are added
broadcast-age words, marked `ADDED` in the manifest.

## First test — what to check

1. Copy the `.avc` to `Documents\Resolume Avenue\Compositions\` and the `.xml` to
   `Documents\Resolume Avenue\Shortcuts\MIDI\`.
2. Preferences > MIDI: select the preset for **input AND output** (output lights the pads).
3. General Prefs: turn ON **"Update clip panels on external triggers"**, or the track knobs
   feel dead — they follow the last-launched clip.
4. Open the comp and check in this order:
   - do five deck tabs appear, Master first?
   - fire Master column 1 — does the stack read top-to-bottom with the mark at the bottom?
   - **the two known risks:** does a long paragraph pad (Ad Break, column 6) wrap onto
     several lines, or render as one runaway line? And does **La Nuit** show its accents
     (`É È ë ô`) or missing-glyph boxes?
   - bank arrows — do they channel-surf all five decks and wrap around?
   - track knob 3 (BRIGHT) — does the text dim and lift?
   - with audio running, does the Field row breathe on the bass and the Mark row snap on
     the highs?

If the paragraphs run away, shrink `wrapChars` in the `LAYERS` table in `build_lexicon2.py`
and rebuild. If a glyph is missing, swap that cell's text in `lexicon2_content.py` and
rebuild. Both are one-line edits and one command.

## Provenance

The corpus was supplied as a list of found texts and used as given, minus three
AIDS-related lines removed at the author's request and two exact duplicates folded in.
Nothing was invented except the 12 marked broadcast words. Cells are verbatim cuts —
the build asserts it.
