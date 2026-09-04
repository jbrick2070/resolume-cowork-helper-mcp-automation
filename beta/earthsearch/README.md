# EarthSearch EP01 — two masters, one instrument

> **STATUS: BUILT AND RIG-VERIFIED — 2026-09-04.**
> 34/34 offline checks, 22/22 live checks against Resolume Avenue 7.27.1 with
> the APC40 mkII connected, including `drift = 0.00 ms over 20 s`.
> Not yet played by hand — see *What still needs a human* below.

The fifth instrument, and the first one that is not a clip launcher.

The four before it fired content: v1 wrote sentences, v2 quotations, v3
broadcast test signals, Nisei archival testimony. This one has **two clips**,
each 27 minutes long, and they never stop. Everything on the surface shapes the
*look* of a film that is already running.

---

## The show

*EarthSearch* is a 1981 BBC radio science-fiction serial: four young people
raised aboard a starship by two computers, ANGEL 1 and ANGEL 2, searching for a
lost Earth. It was heard, never seen.

Two independent AI renders of Episode 1 now exist — same 324 audio windows,
same 121-frame cut grid, entirely different pictures. The instrument runs both
at once and lets a performer dissolve between them over the original untouched
soundtrack.

---

## The problem this solves

A 27-minute source is the opposite of a VJ loop. One stray pad press and you
have restarted the film, in front of an audience, with no way to get the moment
back. Most of the design is about making that impossible rather than unlikely.

| | |
|---|---|
| The 5×8 pad grid | addresses the five **generative overlay** layers only. There is no pad on the surface that can reach a master. |
| Every layer | sets *Ignore Column Trigger*. No column action — from the preset or from a mis-click in Resolume's own UI — can connect, eject or restart anything. Rig-tested. |
| The preset | contains no seek binding, no `connectnextclip`, no column connect, no deck change, and no fader-start. The generator refuses to write one that does. |
| Starting | is one button carrying three clip-connect shortcuts on a single MIDI key. Measured at **0.00 ms drift over 20 s**. |

---

## Eight layers

| # | Layer | Content | Blend |
|---|---|---|---|
| 1 | `MASTER A` | V2 render, full length + audio | Alpha, crossfader bus **A** |
| 2 | `MASTER B` | V3 render, full length | Alpha, crossfader bus **B** |
| 3 | `SIGNAL` | oscilloscope and radiophonic traces | Add |
| 4 | `STARFIELD` | deep space | Screen |
| 5 | `GRID` | wireframe navigation charts | Add |
| 6 | `CAPTION` | system captions | Alpha |
| 7 | `FLARE` | light accents | Add |
| 8 | `SCOPE` | the live FFT readout | Add |

The crossfader is the A↔B dissolve. Faders 1–2 trim each master's level
independently; 3–7 bring in the overlays; 8 is the scope.

---

## 37 effects, five banks

`COLOUR` · `BROADCAST` · `LIGHT` · `SPACE` · `FRACTURE`, all loading bypassed.

**BROADCAST is the signature bank**, built on Resolume's **CRT** emulation —
it squeezes the picture into an emulated cathode-ray resolution and lights one
RGB triad per pixel. For a 1981 BBC serial rendered as television, that one
effect does more than any amount of colour grading. Alongside it: **Radar**,
**WarpSpeed**, **Dot Screen**, **Raster**, **Delay RGB**, **Static**, **Noisy**.

Each bank's dry/wet hangs off one composition dashboard link, which is what
lets **one press clean the entire chain** — five banks, five overlay layers and
the scope, all to zero, without touching playback.

---

## Audio reactivity that is actually measured

Composition FFT, driven by the programme audio **embedded in the master
itself**. No virtual cable, no second player, no routing — the analysis is
frame-locked to the picture by construction.

Bands and gains were measured against this episode's real soundtrack with
`tools/calibrate_fft.ps1`, and the measurements overturned the house recipe
card:

* **3–6 dB is far too quiet for a 1981 mono broadcast.** Every parameter moved
  under 6 % of its range. This source needs around 30 dB.
* **A 0.66–1.00 high band is dead here** — 9 % of range even at 42 dB. Pulled
  down to 0.58–0.82 the same band moves 86 %.
* Resolume's spectrum axis is perceptual, not linear.

Live depth and release per band sit on the Track Control knobs, with the SCOPE
layer as the readout.

---

## Everything on the surface has a job

**175 shortcuts across 149 physical controls. Nothing unmapped.**
See [`docs/APC40_CONTROL_MAP.md`](docs/APC40_CONTROL_MAP.md).

---

## Verified against the running application, not inferred

Resolume's REST API and OSC output were used to settle every uncertain
construct against the live application. That is also how a real bug was caught:
**Bloom's parameter is `amount`, not `brightness`** as an older preset in this
workspace claims — the parameter was renamed between Resolume versions, so the
old preset is evidence about an old Resolume.

`reference/` carries all 109 Avenue 7.27.1 video effects with their true XML
type names, uniqueTypeIds and parameters, harvested by adding every one of them
to a real composition through the REST API and parsing the result. Future packs
in this repo should read that file instead of guessing an id.

Two XML shapes were harvested live that this workspace had never written
before: `CrossFaderGroup` and `Ignore Column Trigger`.

---

## Media

Avenue **cannot open `.mkv` at all** (it gates readers by extension) and
**will not decode an MP3 audio stream in any container** — both measured here.
A straight remux produces a clip with no audio track, and Composition FFT then
has nothing to analyse, which fails silently.

The performance copies are `.mov` with the video **stream-copied bit-for-bit**
and the audio decoded to **PCM** — the exact decode of the original, no second
lossy generation. The `.mkv` archive masters and the original `.mp3` are
untouched, and the delivered soundtrack still comes from the untouched original
in Resolve.

Media is not in this repo. Paths are in
[`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) §3.

---

## Build

```bash
cd tools
python build_earthsearch.py        # the .avc
python gen_preset_earthsearch.py   # the MIDI preset
python make_control_map_doc.py     # the layout card
python validate_earthsearch.py     # 34 offline checks
```

Against a running Resolume (Webserver REST on 8080, OSC 7000/7001):

```bash
powershell -File tools/verify_on_rig.ps1   # 22 live checks incl. sync drift
python tools/harvest_osc_paths.py          # ask Resolume for its OSC addresses
```

---

## What still needs a human

* **Nobody has pressed the hardware.** Every path is proven to resolve and the
  preset loads and becomes active, but the buttons have not been played.
* **LED palette indices** are inherited from earlier packs in this repo and
  have not been eyeballed on the APC for *this* preset.
* **No frame-rate measurement** was taken with all 37 effects instantiated
  (bypassed) alongside two 1080p decodes.
* **The CAPTION layer's text** is a starting point, not an editorial decision.
  Editable in Resolume's own text field in two clicks.
* The imagery is AI-assisted interpretation of a radio serial. It is not
  documentation.
