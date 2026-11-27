# Res React Telemetry — "The Measuring Room"

> **STATUS: BETA — completely untested. Not on hardware, and not yet on a screen.**
> Built 2026-08-07 from the XML up. Every claim below was verified against the *file
> format* — it parses, the IDs are unique, the counts hold, every shortcut species and
> generator block clones a rig-saved donor — but the composition **has not been opened
> in Resolume even once**. No pad has been pressed, no trace has been drawn, no pedal
> has been pressed. Its sibling [`../lexicon-ii/`](../lexicon-ii/) has since been opened
> once; this one has not.
>
> On 2026-11-27 the preset was brought up to the kit's
> [operator standard](../OPERATOR_STANDARD.md) (13 of 13 rules, built into the
> generator). That change is as untested as the rest.
>
> For the brave: it's two files and about ninety seconds to find out. Everything is
> regenerable from `tools/`.

Five decks = **five fictional instruments, all pointed at the same room**. Whatever the
music does, the machines report it — the FFT is not a garnish here, it is the subject:

| CH | Instrument | What it measures | FFT personality |
|---|---|---|---|
| 01 | **THE EKG** | the room's pulse | trace snaps on a **narrowed bass gate** (+9 dB, 150 ms) |
| 02 | **THE RICHTER** | the room's ground motion | trace **swells on the bass** (1200 ms fall) |
| 03 | **THE VU** | the mix itself | **BASS / MID / HIGH columns — a live 3-band analyzer** |
| 04 | **THE POLYGRAPH** | whether the room is lying | needles **ride the mids** (the voice) |
| 05 | **THE GEIGER** | how hot the floor is | stamps **click on the highs** (+9 dB, 100 ms) |

Rows are the anatomy of a chart recorder, bottom to top: **PAPER / TRACE / NEEDLE /
STAMP / READOUT**. 200 clips, **100% native generators** — 185 Text Block cells drawn in
block-element raster typography (`█▓▒░ ▁▂▇ ┼─│` — text as framebuffer), plus per deck
one **SNOW** (Static), one **PILOT** (Stroboscope, the deck's single bass-gated strobe)
and one **CAL DIAL** (Shaper). No media, no FFGL, no Wire, nothing to install.

## The surface

- **The whole surface.** All **149 physical controls** are mapped, one shortcut on
  each. The build fails if even one address is missing.
- **The operator standard, built in.** The controls that mean the same thing on every
  pack mean it here too: the **tempo knob** is the FFT INPUT GAIN — on a pack whose
  subject is the FFT, the one knob that decides how hard the room drives every
  instrument — **Cue Level** is TIME (the paper speed), **▲ ▼** walk the columns,
  **◀ ▶** walk the decks, **Play** opens the show, **Stop** stops, and **Record** and
  the **footswitch** are blackout. The generator asserts all thirteen rules before it
  writes; see [`../OPERATOR_STANDARD.md`](../OPERATOR_STANDARD.md).
- **What the first build had instead.** As built on 2026-08-07 the tempo knob turned
  the CAL DIAL and the footswitch was an RGB-split stomp. The standard claims both
  controls on every pack, so they were given up. The RGB split is still on Device
  Knob 2 (ShiftRGB ships active at Distance 0, so the knob works with nothing armed);
  the CAL DIAL keeps its Rotation Z in the composition with no control bound to it.

## The desk, in instrument-speak

- **Grid** — top row READOUT, then STAMP, NEEDLE, TRACE; bottom row PAPER. LED colours
  per row: white / pink / amber / sky / violet.
- **Track Select 1–8** fires a whole reading (column). Columns 1–5 escalate each
  instrument from calm to catastrophe; 6–8 are CAL / UTILITY / SNOW.
- **Scene Launch 1–5** lifts the pen (clears the aligned row). **Stop All** powers the
  desk down. **Master** drops the TEST CARD.
- **Play** opens the show (column 1). **Stop** stops (ejects everything, as Stop All
  does). **Record** = SCREEN DARK, a blackout toggle; the **footswitch** is the same
  blackout for as long as it is held.
- **Clip Stop row** = the instrument rack: HueRotate, ShiftRGB, LoRez, InvertRGB,
  MirrorQuad, Twitch, ShiftGlitch, Vignette. Bloom / WaveWarp / Tunnel arm from the
  device buttons. No Trails, no Freeze — the infinite-freeze pair stays banned.
- **Activator 1–5** = channel power; **6–8** = row lamps (layer Bloom). **Solo 1–5**
  isolates; **6–8** spotlight verdict stamps. **Rec Arm 1–5** = ROLL (auto-advance a
  row); **6–8** force the FLAT CAL / OFF SCALE / SATURATED states.
- **A/B row** = the diagonal walk: eight presses left to right build a complete look
  with one finger.
- **Pan / Sends / User** = the classic test signals: TONE, BARS, SNOW — and faders
  6–8 are their trim pots. **Shift** = SIGNAL LOST. **Metronome** = tempo resync,
  **Tap Tempo** = tap.
- **◀ ▶ / Bank < >** = the instrument dial (deck surf, wraps). **▲ ▼ / Nudge** = paper
  feed (▲ and Nudge + next column, ▼ and Nudge - previous).
- **Track knobs 1–8** = the selected clip's own dials: GAIN, PHOSPHOR, EXCITE,
  PAPER/TRIG, HALO, QUAKE H, QUAKE W, SWEEP. **Device knobs** = rack dials + row lamp
  brightness. **Tempo knob** = FFT INPUT GAIN. **Cue Level** = TIME, the paper speed
  (composition speed). Both are relative, so neither jumps.

Deliberate button **mirrors** (same cue under a second finger) are all declared and
machine-checked — see `docs/_control_map.tsv`, every row tagged.

## Contents

```
beta/telemetry/
  compositions/  Res React Telemetry.avc            5 decks x 5 layers x 8 columns,
                                                    200 native-generator clips, 118 on the FFT
  controllers/   APC 40 MK II - Telemetry v1.xml    149 shortcuts - the full surface
  tools/         telemetry_content.py               THE CELLS - edit here
                 build_telemetry.py                 regenerates the .avc + the manifest
                 gen_preset_telemetry.py            regenerates the preset + control map
                 gen_padmap_telemetry.py            regenerates the pad map
  docs/          telemetry_pad_map.html             stage reference, all five instruments
                 TELEMETRY_INSTRUMENT.md            the full build note
                 _grid_manifest.tsv                 every pad: deck/row/col/kind/FFT
                 _control_map.tsv                   every one of the 149 controls
```

Rebuild cycle: edit `tools/telemetry_content.py` → `python build_telemetry.py` →
`python gen_preset_telemetry.py` → `python gen_padmap_telemetry.py`. The builds refuse
to write unless the XML parses, IDs and MIDI keys are unique, the clip and generator
counts hold, exactly one strobe cell exists per deck, **every one of the 149 surface
addresses is mapped**, every duplicated path is a declared mirror, and the thirteen
operator-standard rules hold.

## First test — what to check

1. Copy the `.avc` to `Documents\Resolume Avenue\Compositions\` and the `.xml` to
   `Documents\Resolume Avenue\Shortcuts\MIDI\`.
2. Preferences > MIDI: select the preset for **input AND output** (output lights the pads).
3. General Prefs: turn ON **"Update clip panels on external triggers"**, or the track
   knobs feel dead — they follow the last-launched clip.
4. Audio: set Avenue's **audio input device** — the whole point is external FFT
   reacting to the room.
5. Open the comp and check in this order:
   - five instrument tabs, THE EKG first?
   - fire EKG column 1 — paper low, trace centre, verdict at the bottom, caption on top?
   - **the known risk:** do the block glyphs (`█ ▓ ░ ▁ ▇ ┼ ─ │ ▲`) render, or come out
     as missing-glyph boxes? If boxes: flip `ASCII_FALLBACK = True` in
     `build_telemetry.py`, rebuild, recopy — every glyph has an ASCII stand-in.
   - with music: EKG trace snapping on kicks? VU deck showing three breathing columns?
     kill the audio — everything should decay to a readable floor, nothing to black.
   - the standard: with music playing, does the tempo knob make every instrument
     livelier and calmer (FFT gain)? does Record black the screen and bring it back,
     and the footswitch black it only while held? do ▲ ▼ walk the columns forward and
     back, and do all six buttons around the grid arrows do something?
6. If a paragraph runs away or a raster overflows its band, shrink that row's
   `wrapChars`/`band` in `LAYERS` in `build_telemetry.py` and rebuild — one line,
   one command.
