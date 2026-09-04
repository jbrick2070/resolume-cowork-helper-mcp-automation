# APC40 mkII — EarthSearch EP01 control map

Generated from `build/es_apc_map.py`. Do not hand-edit — rebuild with
`python make_control_map_doc.py`.

Preset: **APC 40 MK II - EarthSearch EP01**  ·  composition: **EarthSearch_EP01_Live_Mix**

**175 shortcuts across 149 physical controls. Nothing on the surface is unmapped.**

---

## The three controls that matter

| | Button | What it does |
|---|---|---|
| **START BOTH @ 00:00** | `PLAY` | Fires MASTER A, MASTER B and the SCOPE together at frame zero. Measured at 0.00 ms drift over 20 s on the rig. This is the only control that starts a master. |
| **STOP / RESET BOTH** | `STOP` | Ejects every layer. Both masters return to 00:00. |
| **CLEAN / ALL FX OFF** | `STOP ALL CLIPS` *or* `BANK LOCK` | Takes all five effect banks, every overlay layer and the scope to zero in one press. Playback is not touched. |

Two more ways to reach a clean image: the **Cue Level** knob sweeps the same thing continuously, and the **footswitch** does it as a momentary — hold for clean, release to bring everything back.

`RECORD` is **BLACKOUT** — reversible black, playback continues underneath.

---

## Why no pad can wreck the show

* The 5×8 pad grid addresses **only** the five generative overlay layers. There is no pad that can reach either master.
* **Every** layer sets *Ignore Column Trigger*, so no column action — from this preset or from a mis-click in Resolume's own UI — can connect, eject or restart anything.
* There is **no seek or scrub binding anywhere** in the preset.
* **No layer has fader-start**, so no fader move can trigger a clip.

---

## The pad grid — generative overlays

Physical row 1 is the bottom row. Each row is one layer; each column is one clip on it.

**Row 5 — layer 7 `FLARE`** (Add blend, alert)

| col | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| clip | AMBER WASH | PHOSPHOR WASH | SIGNAL WASH | BONE FLASH | RED ALERT | TAPE GRAIN | PLASMA | SHAPER |
| note | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |

**Row 4 — layer 6 `CAPTION`** (Alpha blend, bone)

| col | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| clip | CAP EARTHSEARCH | CAP EPISODE ONE | CAP ANGEL 1 | CAP ANGEL 2 | CAP CHALLENGER | CAP SYSTEM | CAP CREW | CAP END |
| note | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |

**Row 3 — layer 5 `GRID`** (Add blend, amber)

| col | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| clip | NAV GRID | HORIZON | SCAN BARS | TERRAIN | CHART | VECTOR RISE | SECTOR | APPROACH |
| note | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |

**Row 2 — layer 4 `STARFIELD`** (Screen blend, signal)

| col | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| clip | STARFIELD | NEBULA | ORBIT RINGS | PLANET | PHOTONIC DRIVE | ION CLOUD | JUMP | DEBRIS |
| note | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |

**Row 1 — layer 3 `SIGNAL`** (Add blend, phosphor)

| col | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| clip | CARRIER WAVE | VOICE PRINT | TELEMETRY | ANGEL ONE | ANGEL TWO | DISTRESS | DEEP SIGNAL | INTERFERENCE |
| note | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |

---

## Effect banks

All 37 effects load **bypassed**. Lit pad = effect is active.

### COLOUR — RECORD ARM row (n48, ch1-8)

| # | control | Resolume effect | OSC path |
|---|---|---|---|
| 1 | **TINT** | Tint | `/composition/video/effects/tint/bypassed` |
| 2 | **COLORIZE** | Colorize | `/composition/video/effects/colorize/bypassed` |
| 3 | **DRIFT** | HueRotate | `/composition/video/effects/huerotate/bypassed` |
| 4 | **LEVELS** | Levels | `/composition/video/effects/levels/bypassed` |
| 5 | **EXPOSURE** | Exposure | `/composition/video/effects/exposure/bypassed` |
| 6 | **SATURATION** | Saturation | `/composition/video/effects/saturation/bypassed` |
| 7 | **POSTERIZE** | Posterize | `/composition/video/effects/posterize/bypassed` |
| 8 | **NEGATIVE** | InvertRGB | `/composition/video/effects/invertrgb/bypassed` |

Bank intensity: **Device knob 1**. CLEAN drives it to zero.

### BROADCAST — CROSSFADER A/B row (n66, ch1-8)

| # | control | Resolume effect | OSC path |
|---|---|---|---|
| 1 | **CRT** | CRT | `/composition/video/effects/crt/bypassed` |
| 2 | **GRAIN** | StaticEffect | `/composition/video/effects/staticeffect/bypassed` |
| 3 | **NOISE** | NoisyEffect | `/composition/video/effects/noisyeffect/bypassed` |
| 4 | **DOT SCREEN** | DotScreen | `/composition/video/effects/dotscreen/bypassed` |
| 5 | **RASTER** | Raster | `/composition/video/effects/raster/bypassed` |
| 6 | **BIT CRUSH** | LoRezEffect | `/composition/video/effects/lorezeffect/bypassed` |
| 7 | **RGB DELAY** | DelayRGB | `/composition/video/effects/delayrgb/bypassed` |
| 8 | **FRINGE** | ShiftRGB | `/composition/video/effects/shiftrgb/bypassed` |

Bank intensity: **Device knob 2**. CLEAN drives it to zero.

### LIGHT — DEVICE buttons (n58-65)

| # | control | Resolume effect | OSC path |
|---|---|---|---|
| 1 | **BLOOM** | Bloom | `/composition/video/effects/bloom/bypassed` |
| 2 | **ECHO** | Trails | `/composition/video/effects/trails/bypassed` |
| 3 | **RAYS** | RadialBlur | `/composition/video/effects/radialblur/bypassed` |
| 4 | **BLUR** | Blur | `/composition/video/effects/blur/bypassed` |
| 5 | **SPARKLE** | Sparkles | `/composition/video/effects/sparkles/bypassed` |
| 6 | **HEAT** | Heat | `/composition/video/effects/heat/bypassed` |
| 7 | **HOLD** | Freeze | `/composition/video/effects/freeze/bypassed` |
| 8 | **ITERATE** | Iterate | `/composition/video/effects/iterate/bypassed` |

Bank intensity: **Device knob 3**. CLEAN drives it to zero.

### SPACE — n87, n94-97, n100-102

| # | control | Resolume effect | OSC path |
|---|---|---|---|
| 1 | **WAVE** | WaveWarp | `/composition/video/effects/wavewarp/bypassed` |
| 2 | **RIPPLE** | Ripples | `/composition/video/effects/ripples/bypassed` |
| 3 | **DISPLACE** | Displace | `/composition/video/effects/displace/bypassed` |
| 4 | **TUNNEL** | Tunnel | `/composition/video/effects/tunnel/bypassed` |
| 5 | **WARPSPEED** | WarpSpeed | `/composition/video/effects/warpspeed/bypassed` |
| 6 | **MIRROR QUAD** | MirrorQuad | `/composition/video/effects/mirrorquad/bypassed` |
| 7 | **POLAR** | PolarKaleido | `/composition/video/effects/polarkaleido/bypassed` |
| 8 | **ZOOM** | InfiniteZoom | `/composition/video/effects/infinitezoom/bypassed` |

Bank intensity: **Device knob 4**. CLEAN drives it to zero.

### FRACTURE — SCENE LAUNCH 1-5 (n82-86)

| # | control | Resolume effect | OSC path |
|---|---|---|---|
| 1 | **TEAR** | ShiftGlitch | `/composition/video/effects/shiftglitch/bypassed` |
| 2 | **TWITCH** | TwitchEffect | `/composition/video/effects/twitcheffect/bypassed` |
| 3 | **EDGE** | EdgeDetection | `/composition/video/effects/edgedetection/bypassed` |
| 4 | **FACET** | Triangulate | `/composition/video/effects/triangulate/bypassed` |
| 5 | **RADAR** | Radar | `/composition/video/effects/radar/bypassed` |

Bank intensity: **Device knob 5**. CLEAN drives it to zero.

---

## Faders and knobs

| Control | Target | Home |
|---|---|---|
| Track fader 1 | `MASTER A` level | up |
| Track fader 2 | `MASTER B` level | up |
| Track fader 3 | `SIGNAL` level | down |
| Track fader 4 | `STARFIELD` level | down |
| Track fader 5 | `GRID` level | down |
| Track fader 6 | `CAPTION` level | down |
| Track fader 7 | `FLARE` level | down |
| Track fader 8 | `SCOPE` level | down |
| Master fader | composition master | up |
| **Crossfader** | **A ↔ B dissolve.** MASTER A is on bus A, MASTER B on bus B. Hard left is pure A, hard right pure B, everything between is a true dissolve. | left (pure A) |
| Cue Level | FX MASTER sweep — anticlockwise is a clean image | up |
| Tempo knob | BPM reference for animation only; the masters run on their own timeline and are unaffected | — |
| Footswitch | momentary CLEAN | — |

### Device Control knobs — bank intensity

| Knob | Link | Drives |
|---|---|---|
| 1 | link1 **COLOUR** | dry/wet of every effect in the COLOUR bank |
| 2 | link2 **BROADCAST** | dry/wet of every effect in the BROADCAST bank |
| 3 | link3 **LIGHT** | dry/wet of every effect in the LIGHT bank |
| 4 | link4 **SPACE** | dry/wet of every effect in the SPACE bank |
| 5 | link5 **FRACTURE** | dry/wet of every effect in the FRACTURE bank |
| 6 | link6 **OVERLAYS** | video opacity of all five generative overlay layers |
| 7 | link7 **SCOPE** | video opacity of the live FFT readout layer |
| 8 | link8 **SPARE** | unassigned macro, free for the performer |

### Track Control knobs — live FFT control

This is what makes the audio reactivity playable rather than baked. Watch the SCOPE layer and tune depth and release mid-episode without stopping.

| Knob | Control | Path |
|---|---|---|
| 1 | LOW DEPTH | `/composition/video/effects/trails/effect/feedback/behaviour/gain` |
| 2 | LOW RELEASE | `/composition/video/effects/trails/effect/feedback/behaviour/fallback` |
| 3 | MID DEPTH | `/composition/video/effects/bloom/effect/amount/behaviour/gain` |
| 4 | MID RELEASE | `/composition/video/effects/bloom/effect/amount/behaviour/fallback` |
| 5 | HIGH DEPTH | `/composition/video/effects/shiftrgb/effect/distance/behaviour/gain` |
| 6 | HIGH RELEASE | `/composition/video/effects/shiftrgb/effect/distance/behaviour/fallback` |
| 7 | HUEROTATE DEPTH | `/composition/video/effects/huerotate/effect/huerotate/behaviour/gain` |
| 8 | WAVEWARP DEPTH | `/composition/video/effects/wavewarp/effect/height/behaviour/gain` |

---

## Mixer rows

| Row | Note | Function |
|---|---|---|
| TRACK/CLIP STOP | n52 ch1-8 | eject that layer. ch1/ch2 stop a master — use START BOTH to bring both back in sync |
| TRACK SELECTION | n51 ch1-8 | select that layer |
| ACTIVATOR | n50 ch1-8 | mute that layer (lit = on air) |
| SOLO | n49 ch1-8 | solo that layer |

| Button | Function |
|---|---|
| MASTER n80 | Select composition |
| SENDS n88 | MASTER A blend mode — cycles A's blend - Alpha for a dissolve, Add or Screen for a light composite |
| USER n89 | MASTER B blend mode — cycles B's blend - this is how you get the additive and light blends the brief asks for |
| METRONOME n90 | Tempo resync |
| TAP TEMPO n99 | Tap tempo — the masters are timeline-locked, so tempo only affects BPM-synced animation - never playback |
| SHIFT n98 | Re-arm SCOPE — brings the FFT readout back if it was ejected. Touches nothing else. |
| TEMPO CC13 (relative encoder) | Tempo knob — BPM reference for animation only. The masters run on their own timeline and are not affected. |

---

## FFT map

Composition FFT (`/audioengine/compositionfft`) analyses the composition's own audio, which here is the original programme audio embedded in MASTER A. It is frame-locked to the picture by construction — no virtual audio cable, no second transport, nothing to drift.

| Band | Range | What lives there |
|---|---|---|
| LOW | 0.00–0.30 | music stings, room tone |
| MID | 0.32–0.62 | speech - the working band |
| HIGH | 0.58–0.82 | sibilance, tape hiss |

| Effect | Parameter | Band | Gain | Release | Floor → ceiling |
|---|---|---|---|---|---|
| BLOOM | Amount | MID | 30 dB | 1200 ms | 0.14 → 0.44 |
| ECHO | Feedback | LOW | 27 dB | 1600 ms | 0.42 → 0.66 |
| DRIFT | Hue Rotate | MID | 30 dB | 1100 ms | 0 → 0.045 |
| WAVE | Height | MID | 26 dB | 900 ms | 0.03 → 0.095 |
| FRINGE | Distance | HIGH | 36 dB | 500 ms | 0.015 → 0.07 |
| RIPPLE | Amplitude Both | HIGH | 30 dB | 700 ms | 0.02 → 0.085 |
| ITERATE | StartOpacity | MID | 30 dB | 800 ms | 0.28 → 0.58 |
| BIT CRUSH | Dither | HIGH | 34 dB | 600 ms | 0.1 → 0.42 |

Every one of these is an effect *parameter* inside an effect that loads bypassed. FFT cannot reach a transport, a trigger, a column or a deck — and none of the dry/wet mixes is FFT-driven, because those belong to the dashboard links so CLEAN can always reach them.

---

## Deliberately unmapped

* **Knob LED ring CCs (CC24-31, CC56-63)** — Output-only ring value/style messages, not inputs. In APC Mode 1 the rings follow their value CCs automatically.
