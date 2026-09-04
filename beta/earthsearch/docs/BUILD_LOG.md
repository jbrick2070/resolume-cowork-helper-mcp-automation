# EarthSearch EP01 Live Mix — build log / handoff

**Status: BUILT AND VERIFIED ON THE RIG.** Written incrementally so the build
can be resumed cold by any agent or human. Read top to bottom.

Built 2026-09-03/04 against Resolume **Avenue 7.27.1.15990** with the APC40
mkII connected.

---

## 1. Deliverables

All inside `C:\Art Projects\Res_Fable\earthsearch\`:

| Artefact | Path |
|---|---|
| Composition | `output/EarthSearch_EP01_Live_Mix.avc` |
| MIDI preset | `output/APC 40 MK II - EarthSearch EP01.xml` |
| Control map | `docs/APC40_CONTROL_MAP.md` |
| Run sheet | `docs/RUN_SHEET.md` |
| FFT & audio | `docs/FFT_AND_AUDIO_ROUTING.md` |
| Build sources | `build/*.py` |
| Rig test | `build/verify_on_rig.ps1` |
| Path prover | `build/verify_paths_osc.py`, `build/harvest_osc_paths.py` |
| Live-harvested reference | `reference/avenue_7271_*.json` |

Installed copies (what Resolume actually reads):

```
C:\Users\jeffr\OneDrive\Documents\Resolume Avenue\Shortcuts\MIDI\APC 40 MK II - EarthSearch EP01.xml
C:\Users\jeffr\OneDrive\Documents\Resolume Avenue\Compositions\EarthSearch_EP01_Live_Mix.avc
```

---

## 2. What was asked for

From `FABEL_RESOLUME_EP01_LIVE_PERFORMANCE_BRIEF.md` plus clarifications given
live during the build:

1. Exactly two full-length ~30 min masters on two layers, starting together at
   frame zero and staying in sync.
2. Switching clips is not the point — one control starts both, most buttons are
   for effects.
3. Sliders do the A↔B mix.
4. Every APC40 button, pad, knob and fader has a useful documented job.
5. No ordinary pad may launch, seek, retrigger or restart a master.
6. Strong, tasteful FFT reactivity from the programme audio, low/mid/high to
   complementary parameters. FFT must never trigger clips or disturb sync.
7. Deliberately separated START BOTH / STOP-RESET BOTH / CLEAN-ALL-FX-OFF.
8. DXV only if straightforward; later confirmed unnecessary — real-time
   playback of the remuxes is the plan.
9. Generative effect clips in the EarthSearch register and colour scheme.
10. Live FFT awareness on screen.
11. Original programme audio editorially protected; Resolume output is
    video-only and the untouched audio is restored in Resolve.

---

## 3. Media — DONE

All four candidate masters: 1920×1080, **24 fps**, h264-in-Matroska,
**1630.708 s = 27:10.708 = 39 137 frames**, mono MP3 32 kHz. Identical
durations and an identical audio-stream MD5 across all three versions, so
frame-zero alignment is structural.

### Two hard findings that forced the media shape

1. **Avenue 7.27.1 cannot open `.mkv` at all.** It gates readers by file
   extension; its three readers accept `.mov .mp4 .avi .gif .wmv` /
   `.asf .wma .wmv .avi .m4a .m4v .mov .mp4 .3g2 .3gp .3gp2 .3gpp` / `.mpeg`.
   `mkv` appears nowhere. (It bundles an ffmpeg with the matroska demuxer, but
   never reaches it.)
2. **Avenue will not decode an MP3 audio stream in ANY container.** Tested
   three ways on this rig: `.mov`+mp3-copy loads with **no audio track at all**;
   `.mov`+PCM and `.mp4`+AAC both load with one. Without an audio track,
   Composition FFT has nothing to analyse and every reactive parameter sits
   pinned at its floor — which is exactly what the first build did.

### What shipped

```
C:\Users\jeffr\Documents\ComfyUI\output\otr\obs\earthsearch\resolume\
  EarthSearch_EP01_MASTER_V2.mov   2 370 311 051 bytes
  EarthSearch_EP01_MASTER_V3.mov   2 353 672 901 bytes
  EarthSearch_EP01_MASTER_V4.mov   3 034 691 632 bytes   (spare, not used)
```

`ffmpeg -map 0:v:0 -map 0:a:0 -c:v copy -c:a pcm_s16le`. Video is a **bit-exact
stream copy** — 39 137 frames, verified. Audio is the **PCM decode of the
original MP3**: no re-encode, no second lossy generation, nothing processed.
The `.mkv` archive masters and the original `.mp3` are untouched.

The earlier `.mp4` remuxes are still on disk and are also bit-identical video;
they are just silent to Resolume, so the composition points at the `.mov`s.

**DXV is not needed** — confirmed with the performer. `build_earthsearch.py
--dxv` still exists to repoint at `resolume\dxv\*.mov` if it is ever wanted.

### Which two versions, and why it is not a matter of taste

**A = V2, B = V3.** Both are independent 324-shot re-renders of the *same* 324
audio windows, each a straight concatenation of 121-frame units, so their cuts
land on identical timestamps to the millisecond — a fader between them is a
pure content A/B with no double-cutting. V2 is prompt-led identity; V3 is
reference-conditioned identity, giving a genuinely different composition, shot
scale and colour bias in every window.

**V4 must not be paired with either.** It is not a third render — it is the
V2/V3 hybrid Resolve edit, so it is V2's picture for ~95 % of the runtime, and
it is quantised to a *different* cut grid that runs progressively earlier than
V2/V3 (0 frames at the head, 67 frames = 2.79 s by the tail).

---

## 4. Architecture

### Layers, bottom-up

| # | Name | Content | Blend | Crossfader | Opens at |
|---|---|---|---|---|---|
| 1 | `MASTER A` | V2, full length + audio | Alpha | **bus A** | master 1.0 |
| 2 | `MASTER B` | V3, full length, audio muted | Alpha | **bus B** | master 1.0 |
| 3 | `SIGNAL` | 8 generative clips | Add | – | master 0.0 |
| 4 | `STARFIELD` | 8 generative clips | Screen | – | master 0.0 |
| 5 | `GRID` | 8 generative clips | Add | – | master 0.0 |
| 6 | `CAPTION` | 8 generative clips | Alpha | – | master 0.0 |
| 7 | `FLARE` | 8 generative clips | Add | – | master 0.0 |
| 8 | `SCOPE` | live FFT readout | Add | – | master 0.0 |

**The 5×8 pad grid addresses layers 3–7 only.** There is no pad on the surface
that can reach a master — the rule is structural, not a convention.

**Every layer sets Ignore Column Trigger**, so no column action — from the
preset or from a mis-click in Resolume's own UI — can connect, eject or restart
anything. Verified on the rig: a column trigger leaves both masters playing.

B's clip audio is muted (−192 dB). A and B carry the *same* programme audio;
two coherent copies of one mono track can comb-filter at sample level and the
FFT would then analyse an artefact rather than the score.

### The three separated controls

| Control | APC button | How |
|---|---|---|
| **START BOTH @ 00:00** | `PLAY` (n91) | 3 shortcuts on one key: clip-connect on layers 1, 2, 8 |
| **STOP / RESET BOTH** | `STOP` (n92) | `/composition/disconnectall` |
| **CLEAN / ALL FX OFF** | `STOP ALL CLIPS` (n81) **and** `BANK LOCK` (n103) | 7 shortcuts on one key driving dashboard links 1–7 to zero |

Plus **Cue Level (CC47)** as a continuous FX-master sweep and **the footswitch
(CC64)** as a momentary clean (inverted ValueRange: press = clean, release =
back).

There is **no seek/scrub binding anywhere** and **no fader-start on any layer**,
so no fader move can trigger a clip.

### The effect rack — 37 effects in five banks

`COLOUR` (8) · `BROADCAST` (8) · `LIGHT` (8) · `SPACE` (8) · `FRACTURE` (5).
All load **bypassed**. Each bank's dry/wet is gated by one composition
dashboard link, which is what lets one gesture clean the whole chain.

`BROADCAST` is the signature bank, built around Resolume's **CRT** effect —
cathode-ray-tube emulation that squeezes the picture into an emulated CRT
resolution and lights one RGB triad per pixel. For a 1981 BBC radio serial
rendered as television, that one effect does more than any amount of grading.
Also in the pack: **Radar**, **WarpSpeed**, **Dot Screen**, **Raster**,
**Delay RGB**, **Static**, **Noisy**.

---

## 5. Rig-verified vocabulary

Resolume's REST API (Preferences → Webserver, port 8080) and OSC output
(port 7001) were used to settle every uncertain construct against the running
application rather than by inference.

**Live-harvested reference, committed to `reference/`:** all 109 Avenue 7.27.1
video effects were added to a real composition through the REST API and the
result saved and parsed, giving authoritative `type` / `uniqueTypeId` /
parameter names. Plus the full `/effects` and `/sources` catalogues.

### Facts established on the rig

| Question | Answer |
|---|---|
| OSC slug rule | `lowercase(XML type name)`, non-alphanumerics stripped. Resolume writes the XML *type* as the display name. Confirmed for all 37 rack effects by capturing Resolume's own OSC output. |
| Bloom's Amount | `/composition/video/effects/bloom/effect/amount` — **not** `brightness`. An older preset in this workspace says `brightness`; that is evidence about an older Resolume. Caught and fixed. |
| Crossfader A/B bus | `<ParamChoice name="CrossFaderGroup" T="INT32" default="0" value="1"/>` (0 None, 1 A, 2 B). Never written before in this workspace; set live and read back. |
| Column protection | `<Param name="Ignore Column Trigger" T="BOOL" default="0" value="1"/>`. Set on **all** layers. |
| Blend mode | The `ChoosableMixer` needs an explicit `Blend Mode` ParamChoice — Add (67464114) is the default, so a layer meant to dissolve would silently sum. |
| Clip audio | Needs `<AudioFile>` in PreloadData **and** an `<AudioTrack>` with `<AudioFileSource>`. Without it, no audio decoder, no FFT. |
| FFT link | `/audioengine/compositionfft` (not `externalfft`) — analyses the composition's own audio, so it is frame-locked to the picture with zero routing. |
| Multi-shortcut keys | Legal and already used by 57 presets in this workspace, up to 3 shortcuts per key including `.../connect`. This is what makes one-button START BOTH and CLEAN possible. |
| OSC input scaling | Normalises 0..1 into each parameter's own range. Probes must be 0..1. |

---

## 6. FFT — measured, not guessed

`build/calibrate_fft.ps1` sweeps gain per band and reports how much of each
parameter's output range the band actually uses, against this episode's real
soundtrack.

| Band | Range | Gain | Measured span of output range |
|---|---|---|---|
| LOW | 0.00–0.30 | 27 dB | ~23 % |
| MID | 0.32–0.62 | 30 dB | ~70 % |
| HIGH | 0.58–0.82 | 30–36 dB | ~86 % |

What the measurements changed:

* **The house recipe card's 3–6 dB is far too quiet for this source.** At 6 dB
  every parameter moved less than 6 % of its range — invisible.
* **A 0.66–1.00 "high" band is dead on this material** — 9 % of range even at
  42 dB. The top tenth of the spectrum is empty in a 40 kbps mono broadcast.
  Pulled down to 0.58–0.82 it moves 86 % at 36 dB.
* Resolume's spectrum axis is perceptual, not linear — the mid band responds
  strongly despite the source being lowpassed well below the linear midpoint.

Eight composition parameters are FFT-driven (bloom, feedback, colour drift,
warp, chroma fringe, ripple, iterate, dither), plus eleven on the generative
overlays and three on the SCOPE readout. **None is on a transport, a trigger or
an effect's dry/wet** — the dry/wets belong to the dashboard links so CLEAN can
always reach them.

Live FFT control is on the eight Track Control knobs: per-band DEPTH
(`.../behaviour/gain`) and RELEASE (`.../behaviour/fallback`).

---

## 7. Rig acceptance test — 22/22 PASSED

`powershell -File build/verify_on_rig.ps1`

```
PASS  composition name / 8 layers / 8 columns / 38 comp effects
PASS  CRT, Radar, WarpSpeed present
PASS  all 8 layers ignore column triggers
PASS  no layer has fader-start
PASS  MASTER A on crossfader bus A / MASTER B on bus B
PASS  disconnect-all clears every layer
PASS  MASTER A / MASTER B / SCOPE connect on one press
PASS  both start together          A=3005 ms B=3005 ms
PASS  drift stays under one frame  worst = 0.00 ms over 20 s
PASS  masters survive a column trigger, and keep playing through it
PASS  overlay launches leave the masters running
PASS  all seven CLEAN links reach zero
PASS  CLEAN did not touch playback
```

Also verified: the MIDI preset loads without warnings and becomes the active
preset (`activePresets.xml` shows it), and the APC40 mkII is detected
(`MIDI port APC40 mkII now has control surface Akai APC40 mkII`).

---

## 8. Build commands

```bash
cd "C:/Art Projects/Res_Fable/earthsearch/build"
python build_earthsearch.py           # the .avc
python gen_preset_earthsearch.py      # the MIDI preset
python make_control_map_doc.py        # docs/APC40_CONTROL_MAP.md
python validate_earthsearch.py        # offline checks on both artefacts
powershell -File verify_on_rig.ps1    # live acceptance test
python harvest_osc_paths.py           # ask Resolume for its own OSC addresses
```

Different pairing: `python build_earthsearch.py --a V2 --b V4` (warns).

---

## 9. Install

1. Close Resolume.
2. Copy the preset to
   `…\OneDrive\Documents\Resolume Avenue\Shortcuts\MIDI\` (already done).
3. Copy the composition to `…\Compositions\` (already done).
4. Start Resolume, open the composition. It selects its own MIDI preset.
5. **Preferences → MIDI**: `APC40 mkII` enabled as **input AND output**
   (output is what drives the pad colours).
6. Press **PLAY**. Both masters start together at 00:00.

---

## 10. Open items

- [ ] **Push target.** "Push the pack to the Resolume MCP repo" — this
      workspace has both `resolume-mcp-broker/` and `resolume-mcp-gateway/`.
      **Confirm which before pushing.** Not pushed.
- [ ] Physical button test with hands on the APC. Every path is proven to
      resolve, but nobody has pressed the hardware.
- [ ] `/composition/master` accepted MIDI in 44 prior presets and Resolume
      emits that exact address, but it does not accept OSC *input*. Harmless
      here; noted so nobody re-tests it and thinks it is broken.
- [ ] The CAPTION layer's text is a starting point, not an editorial decision.
      Every string is editable in Resolume's own text field.
