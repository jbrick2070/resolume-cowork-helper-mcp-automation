# Res React Lexicon — an APC40 wordplay instrument

> **STATUS: BETA — awaiting a hardware test.**
> Built and played on the rig 2026-07-31 (Avenue 7.27.1 + Resolume MCP 7.26). Everything
> below was verified through the API and on the program output, but the **APC40 mkII itself
> has not been in the loop yet** — no pad has been physically pressed, no LED colour
> confirmed on hardware, no knob throw felt. Treat the controller map as designed-and-
> serialized, not as controller-verified. It does not join the stable release until Jeffrey
> plays it.

The whole controller becomes a sentence machine: 40 pads, 40 words, 512 grammatical
sentences. 100% native Text Block — no media, no FFGL, no Wire, nothing to install.

## Contents

```
beta/lexicon/
  compositions/  Res React Lexicon.avc          5 layers x 8 columns, 40 text clips,
                                                40 embedded pad images, 320 dashboard links
  controllers/   APC 40 MK II - Lexicon v1.xml  98 shortcuts, every physical control
  tools/         build_lexicon.py               regenerates the .avc; word lists live here
                 gen_preset.py                  regenerates the controller preset
                 inject_thumbs.py               writes the pad images into the .avc
  thumbs/        L1C1..L5C8.png                 the 40 pad images, one per word
  docs/          lexicon_pad_map.html           stage reference: word per pad + surface
```

## First test — what to check

1. Copy the `.avc` to `Documents\Resolume Avenue\Compositions\` and the `.xml` to
   `Documents\Resolume Avenue\Shortcuts\MIDI\`.
2. Preferences > MIDI: select the preset for **input AND output** (output lights the pads).
3. General Prefs: turn ON **"Update clip panels on external triggers"** — without it the
   track knobs will feel dead, because they follow the last-launched clip.
4. Open the comp. Check in this order:
   - do all 40 pads light, and does each row show its own colour?
   - does the top pad row fire Subject and the bottom row fire Field?
   - do the 5 faders control the 5 rows, top-to-bottom as expected?
   - turn track knob 1 slowly — a word should swell toward full-frame.
   - with audio running, does the Field row breathe on the bass and the Mark row snap on
     the highs?

Anything that misbehaves is a mapping question, not a rebuild — `gen_preset.py` regenerates
the whole preset in one run.

---

## 1. The idea

The whole APC40 mkII becomes a **sentence machine**.

Every one of the 40 grid pads is a word. The five pad rows are the five slots of a
sentence, stacked the way they appear on screen. Firing pads in different rows assembles
a line of text live:

```
        THE ARCHIVE          <- Subject   (top pad row)
        MISREADS             <- Verb
        A BORROWED NAME      <- Object
        ::                   <- Mark
   — — — — — — — —           <- Field     (bottom pad row, typographic ground)
```

8 subjects x 8 verbs x 8 objects = **512 grammatical sentences**, x 8 marks = 4096 lines,
over 8 typographic grounds. Every combination parses. Nothing on the surface is a
decoration — faders are grammar presence, knobs are typography, scene buttons drop a
slot out of the sentence.

The composition is **100% type**. Even the background layer is text: bands of repeating
glyphs (`— — —`, `· · ·`, `▓▒░`, `/// `). No video files, no third-party plugins, no
FFGL. It opens anywhere; 660 KB, almost all of that the 40 embedded pad images.

---

## 2. Files

| File | Goes to | Notes |
|---|---|---|
| `Res React Lexicon.avc` | `Documents\Resolume Avenue\Compositions\` | 5 layers x 8 columns, 40 text clips |
| `APC 40 MK II - Lexicon v1.xml` | `Documents\Resolume Avenue\Shortcuts\MIDI\` | 98 shortcuts, whole surface |
| `build_lexicon.py` | `Res_Fable\lexicon\` | regenerates the .avc; edit the word lists here |
| `inject_thumbs.py` | `Res_Fable\lexicon\` | writes the 40 pad images into the .avc |
| `thumbs\*.png` | `Res_Fable\lexicon\thumbs\` | the 40 pad images, one per word |
| `gen_preset.py` | `Res_Fable\lexicon\` | regenerates the preset |
| `lexicon_pad_map.html` | `Res_Fable\lexicon\` | stage reference: word per pad + whole surface |

Activate the preset in **Preferences > MIDI**, selecting it for **input AND output**
(output is what lights the pads).

---

## 3. Composition layout

Layers, bottom to top. Bottom is the render base; top is the last thing drawn.

| # | Layer | Blend | On-screen band | Colour | What it is |
|---|---|---|---|---|---|
| 1 | Field | Alpha | Y 0, size 2.2 | slate 7C8A9C | typographic ground |
| 2 | Subject | Screen | Y -270 (top) | warm white FFF4E0 | who |
| 3 | Verb | Screen | Y -50 | amber FFB020 | does what |
| 4 | Object | Screen | Y +140 | cyan 46E0FF | to what |
| 5 | Mark | Add | Y +330 (bottom) | magenta FF3CC8 | punctuation |

Position Y is pixels from centre, **+Y is down** — verified on the rig, see section 5.

Columns (scenes) 1-8: **Carrier · Drift · Grid · Chorus · Static · Dusk · Lattice · Null**

Every clip is a Text Block source carrying a per-clip **Bloom** and a per-clip
**WaveWarp** (amplitude 0 — silent until dialed). Layers 2-5 each carry their own Bloom
at Amount 0, mapped to a device knob.

Composition FX rack, **all bypassed on load**: Hue Rotate, Shift RGB, LoRez, Invert RGB,
Mirror Quad. Deliberately **no Trails and no Freeze at composition level** — that is the
pair that caused the infinite-freeze lock-up before.

---

## 4. Controller map

### Grid — 40 pads, 40 words

| Pad row | MIDI | Layer | Slot | LED |
|---|---|---|---|---|
| top | notes 32-39 ch1 | 2 | Subject | white |
| 2 | notes 24-31 ch1 | 3 | Verb | amber |
| 3 | notes 16-23 ch1 | 4 | Object | sky |
| 4 | notes 8-15 ch1 | 5 | Mark | pink |
| bottom | notes 0-7 ch1 | 1 | Field | violet |

Pad colour matches that slot's colour on screen, so the grid is a legend for the output.
Bright = playing, dim = loaded. This is the fix for the old counterintuitive row map
where content started at row 3 — here row order **is** layer order **is** reading order.

### The rest of the surface

| Control | MIDI | Does |
|---|---|---|
| Track Select 1-8 | note 51 ch1-8 | fire a whole sentence (column 1-8) |
| Scene Launch 1-5 | notes 82-86 | drop that grammar slot out (layer clear), aligned with the rows |
| Clip Stop 1-6 | note 52 ch1-6 | composition FX toggles: Hue, Shift RGB, LoRez, Invert, Mirror, All-FX |
| Activator 1-5 | note 48 ch1-5 | mute a grammar slot |
| Solo 1-5 | note 49 ch1-5 | isolate a grammar slot |
| Faders 1-5 | CC7 ch1-5 | how present each slot is |
| Master fader | CC14 | composition master |
| Crossfader | CC15 | crossfader phase |
| Device knobs 1-4 | CC16-19 | Hue · RGB Shift · Pixel Size · Bit Reduction |
| Device knobs 5-8 | CC20-23 | glow on Subject · Verb · Object · Mark |
| Track knobs 1-8 | CC48-55 | the selected clip's own dials (canonical translationType 4) |
| Big encoder | CC47 | selected clip transport position |
| Tap / Resync | notes 99 / 91 | tempo |
| Stop All | note 81 | disconnect all |
| Bank < > | notes 96 / 97 | previous / next column |

98 shortcuts. Every physical control on the APC40 mkII is assigned.

---

## 5. Verified on the rig 2026-07-31

Opened in Avenue 7.27.1 and played. Confirmed live:

- The sentence assembles and reads top to bottom: Subject / Verb / Object / Mark.
- **Text Block `Position Y` is pixels from centre and +Y is DOWN.** The first build had
  the stack inverted; the `LAYERS` table now carries the corrected values.
- Colour ints in the .avc are **ABGR** — the palette rendered exactly as specified.
- Composition FX rack loads bypassed. No freeze, no black frame.
- `∴` renders as a missing-glyph box in Resolume's Text Block font. Mark 7 is now `::`.
  Verified as rendering: `—` `·` `…` `▓▒░` `\` `#` `(` `)` `/` `+` `0`.

### Pad images

All 40 pads carry their own image — the word set in the slot's colour, with the slot name
and column tag. Generated by `inject_thumbs.py`, which writes them straight into the
composition's `EmbeddedThumbnail` blobs so they travel with the file.

Two things learned the hard way, both worth keeping:

- Resolume's **auto-generated** thumbnails came out blank for 6 of the 40 —
  `.` `?` `!` `∴` `\ \ \` `# # #` — even though every one of those clips renders fine on
  the main output. Blank thumbnails are byte-identical, so the grid had 6 duplicates.
- `clip thumbnail_upload` **displays** correctly but does **not** persist. It never wrote
  into the .avc, and no sidecar file appeared — the custom image is session-only and
  reverts on restart. The only durable route is writing the blob into the file.

The blob format: `encoding="LZF"`, 320x240, bitdepth 32, base64 of LZF-compressed raw
**BGRA** pixels (307,200 bytes uncompressed, ~2-3% after LZF). `inject_thumbs.py` carries
both a compressor and a decompressor and round-trip asserts every image before writing.

> **Saving from Avenue overwrites the injected thumbnails** with Resolume's own
> auto-generated set — including the 6 blanks. After any in-app save, re-run
> `python inject_thumbs.py "<saved>.avc" "Res React Lexicon.avc" BGRA` to put them back.

### Independence from the controller compositions

Checked against `APC40MKII_ELECTRIC_ZENTROPA_*`, `APC40_Visual_Twin_V2_*` and
`React Grid Map Test`: **zero shared clip names**. The Lexicon holds 0 video files,
0 FFGL plugins, 0 Wire generators and 0 media paths — 40 Text Block sources and nothing
else. 40 distinct clip names, 40 distinct pad images. It shares no content with the
controller-surface work.

---

## 6. The track knobs — now live

Probed on the rig rather than guessed. `parameter set_animation` with
`phase_source: dashboard` writes two co-operating species, and the probe corrected two
things memory had wrong:

```xml
<!-- the dial, in a <Params name="Dashboard"> block on the clip -->
<ParamRange name="Link 3" altName="Glow Out" T="DOUBLE" default="0.35" value="0.35">
    <PhaseSourceStatic name="PhaseSourceStatic"/>
</ParamRange>

<!-- the link, replacing that param's <PhaseSourceStatic/> -->
<DurationSource/>
<PhaseSourceDashboardLink name="PhaseSourceDashboardLink" phase="0.35"
                          linkId="/link3" linkName="Glow Out"/>
```

- The element carries `name="PhaseSourceDashboardLink"` — the previously documented form
  omitted it.
- Driving this through the MCP puts the **dial on the parent layer**, not the clip. The
  Lexicon puts dials on the **clip** (the shape a rig-saved file uses) so CC48-55 →
  `/composition/selectedclip/dashboard/linkN` reaches them and every pad brings its own
  knobs. 40 clips × 8 dials = **320 links**, all written offline.

`phase = (value - min) / (max - min)`. Ranges read off the rig:

| Dial | Param | Range | Default phase |
|---|---|---|---|
| 1 SIZE | Text Block Size | 0.5 – 10 | per row |
| 2 GLOW | Text Block Glow Out | 0 – 1 | per row |
| 3 BLOOM | Bloom Amount | 0 – 1 | 0.18 |
| 4 HALO | Bloom Size | 0 – 1 | 0.18 |
| 5 THRESH | Bloom Threshold | 0 – 1 | 0.45 |
| 6 WARP | WaveWarp Height | 0 – 1 | 0.00 |
| 7 RIPPLE | WaveWarp Width | 0 – 1 | 0.00 |
| 8 DRIFT | WaveWarp Speed | 0 – 1 | 0.15 |

**Position Y is deliberately not on a knob.** Its range is ±32768, so the whole usable
travel sits inside 0.492–0.508 of the throw — unplayable. The vertical band stays a design
constant; faders and scene buttons already give per-row control.

SIZE is sensitive near the bottom of its throw (1.0 sits at phase 0.05) and that is the
point — a small move takes one word from a line of text to the entire screen. Verified
live: dial 1 to 0.32 with a little WARP and BLOOM turns MISREADS into a full-frame amber
ribbon field while the other three rows stay crisp.

Turn on **General Prefs → "Update clip panels on external triggers"** so the knobs follow
the last-launched clip.

---

## 7. Audio

Field and Mark ride an **external FFT**; the three word rows never do, so the sentence
stays readable no matter what the music does.

| Row | Band | Gain | Fallback | Sweep floor |
|---|---|---|---|---|
| Field | bass 0–0.33 | +6 dB | 800 ms (breath) | 0.55 |
| Mark | highs 0.66–1.0 | +6 dB | 200 ms (snap) | 0.45 |

Driven via clip `Opacity` on `/audioengine/externalfft`. Set Avenue's audio input (the
VB-Cable chain). With no audio connected both rows simply sit at their sweep floor and
stay visible — nothing disappears.

---

## 8. One side effect worth knowing

Launching Avenue caused it to rewrite the MIDI preset that was active at the time —
`APC40MKII_ELECTRIC_ZENTROPA_BUTTONPULSE_FFT_v2.xml`. Avenue flushes the active preset
about 20 seconds after startup; that is its own behaviour, not an edit made here, but it
was triggered by the launch. The file is intact and valid — 203 shortcuts, name unchanged,
182,325 bytes — but its bytes differ from before. If you want the exact prior version back,
it is in OneDrive version history.

Every other file is untouched: **all 65 pre-existing compositions and the other 31 MIDI
presets are byte-identical to their pre-session SHA-256 hashes** (baselines kept in
`_baseline_comps.csv` / `_baseline_midi.csv`, re-verifiable any time).

Going forward this cannot recur for the old presets: the Lexicon comp requests
`APC 40 MK II - Lexicon v1`, so that is the preset Avenue will flush from now on.

---

## 9. Changing the words

All content lives in the `WORDS` table at the top of `build_lexicon.py` — five lists of
eight `(pad label, on-screen text)` pairs. Edit, run `python build_lexicon.py`, copy the
result over. The script validates XML, unique IDs, and clip/layer/column counts before it
writes, and it never touches any other file.

Pad labels are Title Case (what the deck grid shows); on-screen text is uppercase.

After editing words, the full cycle is:

```
python build_lexicon.py          # rebuild the composition
python inject_thumbs.py "Res React Lexicon.avc" "Res React Lexicon.avc" BGRA
```

`inject_thumbs.py` reads `thumbs\LxCy.png`, so regenerate any pad image whose word
changed. Both scripts validate XML, unique IDs and clip/layer/column counts before
writing, and neither touches any other file.
