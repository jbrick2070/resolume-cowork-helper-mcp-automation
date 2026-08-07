# Res React Test Card — broadcast signals for the APC40 mkII

> **STATUS: BETA — rig-verified via API on 2026-08-06, the day it was built.**
> Loaded in Avenue 7.27.1, all three decks fired live, WaveWarp motion confirmed on the
> program output. The APC40 hardware itself has not yet been in the loop — LED colours
> and knob feel are designed, not hand-verified.

The third instrument. v1 ([lexicon](../lexicon/)) wrote sentences, v2
([lexicon-ii](../lexicon-ii/)) fired quotations — this one is **pure signal**. Every pad
is a typographic test pattern, and unlike the word packs the surface **moves on its own**:
every clip ships with live WaveWarp, and three of the five rows ride the external FFT.

| Row (grid, top→bottom) | Layer | Colour | FFT |
|---|---|---|---|
| **Ident** | 5 (top, Add) | broadcast white | — steady station voice |
| **Pulse** | 4 (Add) | tally orange-red | **highs** — snaps |
| **Tone** | 3 (Screen) | phosphor teal | **mids** — shimmers |
| **Sweep** | 2 (Screen) | test-card yellow | — steady anchor |
| **Carrier** | 1 (bottom, Alpha) | translucent slate | **bass** — breathes |

**Three decks, Bank `<` `>` to surf:** `Test Card` (calibration morning) → `On Air`
(dense, bright, fast) → `Dead Air` (late-night decay: SIGNAL LOST, PLEASE STAND BY,
GOODNIGHT). 120 pads. Pad LED colours match the row's on-screen colour.

100% native Text Block generators — no media, no FFGL, no plugins, ~1 MB.

## Surface (98 shortcuts — every physical control)

Same layout as both Lexicon packs: grid = patterns, track select = fire a column,
scene launch = kill a band, activator/solo = mute/isolate, faders = band presence,
clip stop = comp FX toggles (Hue / RGB / LoRez / Invert / Mirror / all), device knobs =
FX + per-band glow, track knobs = SIZE · GLOW · BLOOM · HALO · THRESH · **WARP · RIPPLE ·
DRIFT** (the last three actually matter here — they're live, not parked at zero).

## Install

1. `compositions/Res React Test Card.avc` → `Documents\Resolume Avenue\Compositions\`
2. `controllers/APC 40 MK II - TestCard v1.xml` → `Documents\Resolume Avenue\Shortcuts\MIDI\`
   (select for input **and** output in Preferences > MIDI)
3. General Prefs: **"Update clip panels on external triggers"** ON.
4. Feed Avenue audio and the Carrier breathes on bass, Tone on mids, Pulse on highs.
   With no audio everything sits at its sweep floor and stays visible.

Rebuild: edit the `GRID` table in `tools/build_testcard.py`, run it, done. The build
refuses to write unless the XML parses, IDs are unique and all counts hold.
