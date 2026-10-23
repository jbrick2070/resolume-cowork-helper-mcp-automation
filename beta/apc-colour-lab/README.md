# APC40 mkII Colour Lab

A proof of concept for making the APC40 mkII's MIDI do more than Resolume's own feedback does.

**Open [`apc40_colour_lab.html`](apc40_colour_lab.html)** (one file, no network). It is an emulated APC40 mkII beside the raw colours Resolume would send, nine
themes, a live MIDI monitor and a tempo slider. Click the pads.

## The idea

On the RGB pads (the 40 clip pads, notes 0-39, and the 5 Scene Launch pads, notes 82-86) the note-on **velocity picks the colour** from a fixed
128-entry palette and the note-on **channel picks an animation** that the controller then runs by itself:

| MIDI channel | Animation | Rates (MIDI clock ticks, 24 per quarter note) |
|---|---|---|
| 1 | primary colour, static | |
| 2-6 | one-shot to a secondary colour | 1/24 · 1/16 · 1/8 · 1/4 · 1/2 (4 · 6 · 12 · 24 · 48 ticks) |
| 7-11 | pulsing between primary and secondary | same |
| 12-16 | blinking between primary and secondary | same |

So two messages per pad make it breathe or blink with no further traffic. Resolume's MIDI shortcut feedback can only send one velocity per state; a **router
on the LED path** can do much more:

* **Re-theme any pack** without rebuilding its preset: green playing / dim green loaded becomes pumpkin and violet, red and green, or pure greys.
* **Fill the dark pads** with an ambient show (flicker, marquee chase, falling petals, a scan line) that Resolume knows nothing about.
* **Answer every press** with a ripple, a cross, a sparkle or a full-grid inversion, as one-shot messages timed by the controller.
* **Host the rings** as meters: 16 LED rings, ring style set once, value only when it changes.
* **Be the MIDI clock** the animations need.

## Themes

Pack colours (the baseline) · Halloween · Christmas · Valentine's · Stars & Stripes · Dia de Muertos · Synthwave · Newsprint (black and white) · Inverse (black and white
as a negative). They are plain data in [`apc_lab/themes.json`](apc_lab/themes.json): velocities from the real palette, plus a remap rule, an ambient animation and a touch effect.

## What is verified, and what is not

| | |
|---|---|
| Message encoding, channel/animation table, palette, SysEx bytes | 40 unit tests, checked against Akai's protocol v1.2 and Ableton's own APC40 mkII skin |
| Python engine = JavaScript engine | `tools/parity.py`: 54 scenarios, 31,677 messages, 0 differences |
| The demo page | rendered and clicked in a browser; Halloween, Christmas, Dia de Muertos, Newsprint and Inverse were looked at, the other four are covered by the tests only |
| **The animations on real hardware** | **not tested.** Avenue holds the APC's ports and no loopback driver is installed |

Open questions that only a rig test can settle (the Akai document does not say):

1. Do the pads follow a host MIDI clock (`0xF8`, 24 per quarter note), and what tempo do they use without one? Push 2's equivalent documentation says 120 bpm.
2. Which way a one-shot runs (secondary then back to primary, as emulated here), and whether a note on channel 1 always cancels an animation.
3. Whether the Scene Launch pads animate like the clip pads.

`python -m apc_lab.live --dry-run` prints the exact bytes the router would send without opening a port; `--list` names the ports.

## Running it

```
python -m pytest tests                 # 40 tests
python tools/parity.py                 # Python engine vs demo/engine.js
python tools/build_demo.py             # rebuild apc40_colour_lab.html
python -m apc_lab.live --dry-run --theme halloween
```

## On the rig

The router must sit on the LED path, so it has to own the controller's ports (or share them).

```
 APC40 mkII --presses--> router --forwarded--> [virtual "to-res"]   --> Resolume MIDI in
 APC40 mkII <--LEDs----- router <--feedback--- [virtual "from-res"] <-- Resolume MIDI out
```

* **Mode 2.** The controller wakes in Mode 0 after every power cycle. Send `F0 47 7F 29 60 00 04 42 00 00 00 F7` so the host owns every LED, rings included. The repo's
  current presets assume Mode 1; the router and the preset must agree on a single owner of the LEDs.
* **Virtual ports.** loopMIDI is not installed on this rig. Windows MIDI Services (`midisrv`) is running on build 26200 and may allow a second client on the APC itself;
  that is untested. See [`docs/CHATAIGNE.md`](docs/CHATAIGNE.md) for hosting this in Chataigne, which is installed here (1.10.3).

## Findings along the way

* `resolume_build/apc.py` names its LED velocities a hue family off the real LEDs (velocity 37 is azure, 45 is blue, 49 violet, 53 magenta, 57 rose). The velocities are
  right and the packs are unaffected; only the colour *names* are misleading.
* Reading the community Chataigne APC40 module's source, it appears to pass its pad "mode" enum (0-15) straight to `sendNoteOn` as a Chataigne channel (1-16), which would put every
  animation one channel early on the wire. Untested. Hosting this lab in Chataigne should use its plain MIDI module, not that enum.

## Credits and licence

Palette: Akai APC40 Mk2 Communications Protocol v1.2, cross-checked against Ableton's `RGB_COLOR_TABLE` and
[cunabula27's APC40-MkII-Chataigne-Module](https://github.com/cunabula27/APC40-MkII-Chataigne-Module) (GPL-3.0, not included here). Code: the repository's licence.
