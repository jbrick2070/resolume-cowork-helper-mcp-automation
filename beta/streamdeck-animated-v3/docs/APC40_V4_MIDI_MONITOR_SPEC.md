# APC40 V4 - Live MIDI monitor + per-control readouts (Wire spec)

Punch-list item 4, specced 2026-07-20. **Verdict: needs Wire.** This is the
first V4 deliverable. Everything below is out of reach for a pure-Avenue,
pre-rendered-clip twin and is written to be built directly against the Resolume
Wire MCP server (`mcp__Resolume_Wire_MCP_Server__*`).

## Why it cannot be done in V3 (no Wire)

The V3 twin is pre-rendered ProRes loops. A clip cannot know what MIDI value
just arrived, and Avenue has no node that turns an incoming CC/note into
displayed text: MIDI shortcuts map MIDI -> a parameter (opacity, rotationz,
connect), never MIDI -> a string on screen. A Text clip's content is static.
So a "last CC = value" ticker and per-control numeric readouts (the reference
HTML's `-> 107`, `# 127`, `<- 001`, lit tick counts, tip segment) are, by the
reference's own note, **V4 Wire-only**. V3 art stays value-agnostic (the bold
Tempo/Cue needle shipped in this build is the value-agnostic stand-in: it shows
that a knob is turning, not to what value).

Wire is the right tool: it has a MIDI input bundle (`Protocol: MIDI`), signal
math, and a `Texture Out` that Avenue can display as an FFGL / Spout source.

## Deliverable A - corner last-MIDI-event ticker

A small always-on overlay in one screen corner (bottom-left proposed, clear of
the chassis) reading the most recent MIDI event and its value, e.g.:

```
CC 47  001      (last continuous move: Cue Level)
N 92   ON       (last note: Stop)
```

Wire patch (node classes to confirm against the live `catalog` / `class`
tools when building - names below are by role):

1. **MIDI In** (Input category) - subscribe to the `APC40 mkII` port. Emits the
   raw stream: status, data1 (CC# / note#), data2 (value / velocity), channel.
2. **Event split / route** - separate CC (0xB0) from Note-on/off (0x90/0x80).
   Latch the last event of each kind (sample-and-hold on the Event flow).
3. **Address -> label map** - a small lookup (CC#/note# -> human name) built from
   `build/build_input_v3.json` (`raw_key` decodes to status+data1; the same
   decode this build used: low byte = status, next = CC/note number). Ship the
   table as a Wire string array or an embedded JSON the patch reads once.
4. **Format** - compose `"{kind} {num:3} {value:3}  {name}"`; zero-pad to keep
   the ticker from reflowing.
5. **Text render -> Texture Out** - mono font (DejaVu Sans Mono to match the
   twin), `#e6e6e6` on a 40 %-black plate, ~9-11 px. Fixed canvas (e.g.
   360x64) so dims are a load-time fact (serializer law 2/3 - never resize a
   live canvas).

Surface it in Avenue as a **new Add-blend overlay layer** carrying one clip
whose source is the Wire Texture Out (FFGL/Spout). **Cold-open law:** an FFGL
source instanced mid-session renders black - the ticker layer must exist in the
comp at cold-open (author it offline via the injector, same as the chassis
layer), never hot-added. Registration counts (`numLayers`/`numColumns` on
Composition and Deck) must be patched with the new layer (serializer law 1) or
Avenue silently drops it.

## Deliverable B - per-control live readouts (reference-HTML look)

Replace the value-agnostic Tier B caps with Wire-driven caps that show the real
value, matching `react-kit/docs/APC40_SURFACE_ANIMATION_REFERENCE.html`:

| Control | V3 (shipped, value-agnostic) | V4 (Wire, live) |
|---|---|---|
| Rotary knob | dim 12 o'clock detent | LED arc fills to value + tip segment + `-> NNN` numeral |
| Small rotary (Tempo/Cue) | bold needle + tip dot | position pip on the 270-deg arc + `<- NNN` numeral |
| Vertical fader | static thumb-cap | lit tick ladder (N of 11) + `# NNN` block |
| Crossfader | centred puck | puck tracks value + A/B lean + `# NNN` |

Geometry is already fixed and shared with V3 so the live art lands in the same
silhouettes: **15 arc segments on 270 deg, 11 fader ticks, 0.04u silhouette
insets**, `u` = control short edge. Palette: red #e83c2e / green #3cd05a /
amber #f5aa22 / cyan #28c8dc / blue #5a78ff; chassis #b51d35 never inside a
control. Each cap is its own Wire patch parameter (value 0..1 in) -> arc/ladder
geometry + numeral -> Texture Out, or one atlas patch with per-control regions.

Driving inputs already exist in the preset (no preset change): the same CCs this
build mapped - Cue = CC47 (opacity 0.35..1 + rotationz 0.125..0.875), Tempo =
CC13 (relative rotationz), device knobs CC48..55, track knobs CC16..23, faders
CC7 x8 channels, etc. Wire reads those CCs directly from MIDI In (it does not
need to go through Avenue's parameter).

## Deliverable C - note-off -> auto-unlatch preset species

Independent of Wire; belongs to V4 because it needs a rig-captured shortcut
specimen. Today the pressed/active column is toggle-style (press on, press off).
The goal: momentary controls light on note-on and clear on note-off
automatically. Method (per CONTROL_LOGIC section 6): in the Avenue UI, map one
control's note-on -> `clips/2/connect` and note-off -> `clips/1/connect`, save
the preset, diff against the current 203-shortcut preset to capture the exact
`behaviour`/`translationType`/`RawInputMessage` species, then clone that species
across the momentary controls with the offline injector. Until captured, the
column stays toggle (as shipped and blessed).

## Build order for V4

1. Capture the note-off species (C) - unblocks correct momentary behaviour,
   cheapest, no Wire.
2. Corner ticker (A) - one Wire patch, one overlay layer, proves the
   Wire->Avenue FFGL/Spout path and the cold-open discipline end to end.
3. Per-control readouts (B) - the largest surface; reuse A's MIDI-In + label
   table and the shared geometry constants.

## Guardrails carried from V3 (do not relearn the hard way)

- FFGL/Spout sources must be present at cold-open, not hot-added (renders black).
- Texture Out canvas dims are load-time facts; never resize a live canvas.
- Patch Composition/Deck registration counts when adding the overlay layer(s).
- Force Avenue + Wire onto the same GPU (RTX 5080) or Spout hands back a black
  frame (dual-GPU law).
- Start `avenue_pipe_bridge.py` before any Resolume MCP call; keep MIDI Output
  enabled in Preferences > MIDI for hardware LEDs.

## Deliverable C - corner audio waveform (added 2026-07-20 eve, Jeffrey)

A second small corner overlay (bottom-right proposed) showing a live scrolling
waveform of the audio Avenue is analysing, so the twin "truly records what's
going on". Same architecture as Deliverable A: Wire patch (Audio In ->
waveform/scope draw -> Texture Out at a fixed small canvas, e.g. 360x64),
surfaced as an offline-authored Add-blend overlay layer (FFGL cold-open law;
registration counts patched). Style: 1 px #e6e6e6 trace on 40%-black plate,
restrained; no dB numerals (numerals remain Deliverable B territory).

## Status 2026-07-20 eve

- Wire was NOT running during the unattended build window; A/B/C untouched.
- SHIPPED instead tonight (V3-legal): external-FFT opacity reactivity on all
  40 grid-pad layers, floor 0.55 (visible when quiet), gain +6 dB, fallback
  1200 ms - live-applied via API AND baked into the Spec_Candidate .avc
  (PhaseSourceFFT species from Res Fable Signal.avc; L1's omitted Opacity
  param inserted). Cold-open verified; pre-FFT comp backup at
  backups/Spec_Candidate_preFFT_20260720.avc.
- Next session: launch Wire, confirm node classes via catalog/class, build A
  (ticker) + C (waveform) as one patch with two Texture Outs or two patches;
  author overlay layers 151/152 offline via the injector.
