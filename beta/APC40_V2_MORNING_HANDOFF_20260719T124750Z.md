# APC40 Visual Twin V2 — Morning Handoff

Run ID: `20260719T124750Z`

## Verdict

**PARTIAL — software candidate ready for human test.**

Automated QA reports **21 PASS, 0 failures, and 3 explicit human gates
open**. The saved candidate, immutable R1 hashes, append-only structure, MIDI
contract, deterministic collision geometry, representative visual evidence,
FFT configuration, external-media scan, and MCP singleton topology pass.

Physical APC40 behavior, real-audio calibration, and matched performance remain
**OPEN — HUMAN TEST REQUIRED**. A cold reopen/persistence check is also open.
Do not promote or merge this candidate until those checks pass and the user
explicitly approves promotion.

## Candidate and Git receipt

- Absolute path:
  `C:\Art Projects\Res_Fable\react-kit-apc40-v2-overnight\beta\compositions\APC40_Visual_Twin_V2_Candidate_20260719T124750Z.avc`
- Repository path:
  `beta/compositions/APC40_Visual_Twin_V2_Candidate_20260719T124750Z.avc`
- Composition name:
  `APC40_Visual_Twin_V2_Candidate_20260719T124750Z`
- SHA-256:
  `52e20cf4b530979573eacd3f57d5995bbd6f7706b07b79ccc4b07713cdb473dd`
- Branch: `codex/apc40-v2-overnight`
- Candidate/artifact commit:
  `7b0086415cf80995a399055f1aca77bd2cc371d1`
- Push state: that artifact commit is confirmed on
  `origin/codex/apc40-v2-overnight`.
- Starting `main` / `origin/main`:
  `c0a318da260b58c12c8545fe43a091bbbbc966c6`

The handoff may be committed later than the immutable candidate/artifact commit
so it can record that exact hash.

## R1 protection receipt

Both canonical R1 files were hashed before mutation and after the final V2
save. They remain byte-identical.

| Protected file | Before SHA-256 | After SHA-256 |
|---|---|---|
| `compositions/APC40_Visual_QA_148.avc` | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` |
| `controllers/APC 40 MK II - Visual QA.xml` | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` |

## Exact V2 addition and bypass

Only one append-only layer was added above the frozen R1 range:

- Layer 149 / clip 149, column 1: `V2 Chassis Low FFT`
- Native source: `Text Block` / `BlockTextGenerator`
- Font: `Cascadia Mono`, Regular
- Color: `#557f96ff`
- Text size: `0.5`
- Source Scale: `0.28`
- Line width: `5000`
- Transform: X `13`, Y `0`, Scale `50`, Scale W `204`, Scale H `170`
- Blend: `Add`
- Layer opacity: `1.0`
- Audio track: none
- Effects: mandatory clip Transform only
- Added MIDI shortcuts: `0`
- External media: `0`

For instant rollback, toggle **Bypass** on layer 149. Bypass restores the R1
image; unbypass restores V2. No protected layer needs to change.
Final live readback shows layer 149 active, not soloed, not bypassed, with its
thumbnail regenerated and all 149 clips playing.

## Reconciled counts

| Item | Count |
|---|---:|
| Resolution | 1920 × 1080 |
| Decks / columns / groups | 3 / 1 / 0 |
| Layers / clips | 149 / 149 |
| Frozen R1 layers / added layers | 148 / 1 |
| Generator video sources | 149 |
| MIDI shortcut records / unique shortcut IDs | 203 / 203 |
| Raw MIDI messages / unique raw keys | 203 / 148 |
| Added MIDI shortcuts / external media | 0 / 0 |

The first 148 layer and clip identities, sources, mappings, and static witness
semantics pass the validator. Save-time fader, rotary, crossfader, and mixer
current values are explicitly enumerated as runtime state in the QA JSON; no
semantic mismatch was found.

## Geometry and collision QA

The native Text Block encodes the chassis as Unicode Braille:

- Glyph grid: `160 × 60`
- Effective dot grid: `320 × 240`
- Vector primitives: `54`
- Primitives represented: `54`
- Desired dots: `5382`
- Occupied dots: `5377`
- Deliberately clipped dots: `5`
- Nonblank glyphs: `2221`
- Empty primitives: `0`
- Vector, dot, and native text-cell collisions: `0`

All 148 controls are protected across 295 label, witness, and motion boxes.
Machine intersections are zero for the resting/all-visible state, complete
fader motion envelopes, complete knob rotation hulls, both crossfader
endpoints, chassis-only, the synthetic low-band peak, and layer-149 bypass.
The corresponding physical sweeps remain open for a human.

## FFT contract

FFT affects only layer-149 clip opacity:

- Phase source: composition FFT (`/audioengine/compositionfft`)
- Avenue normalized low-band selection: value `0.165`, range `0.00–0.33`
- Gain: `+3 dB`
- Fallback: `1400 ms`
- Output opacity: `0.35–0.62`
- FFT nodes: `1`
- Geometry, position, scale, rotation, extent, hue, color, and blur modulation:
  none
- R1 witness modulation: none

The screenshots verify the configured nonzero floor and synthetic accepted
peak. A fresh MCP live-motion sample after the final repair measured `0.00`.
An earlier user report of motion is not treated as certification: real silence,
bass, midrange, high-frequency, and accepted-peak audio calibration remains
**OPEN — HUMAN TEST REQUIRED**.

## Visual evidence and metrics

- [R1 witness baseline](screenshots/apc40-v2-20260719T124750Z/01-r1-witnesses-candidate-baseline.png)
- [FFT silence composite](screenshots/apc40-v2-20260719T124750Z/03-v2-fft-silence-composite.png)
- [FFT silence, layer 149 isolated](screenshots/apc40-v2-20260719T124750Z/03b-v2-fft-silence-layer.png)
- [Layer-149 bypass / exact R1 restoration](screenshots/apc40-v2-20260719T124750Z/04-v2-bypass-r1-restore.png)
- [Synthetic low-band peak, all witnesses](screenshots/apc40-v2-20260719T124750Z/05-v2-low-band-peak-envelope.png)
- [Synthetic low-band peak, layer 149 isolated](screenshots/apc40-v2-20260719T124750Z/05b-v2-low-band-peak-layer.png)
- [Final restored silence state](screenshots/apc40-v2-20260719T124750Z/06-v2-final-restored.png)

Baseline and bypass captures are file- and pixel-identical: `0` changed pixels,
MAE `0`, MSE `0`, and maximum channel difference `0`.

Silence versus synthetic peak changed `5163 / 22600` pixels (`22.8451%`):
MAE `0.40938`, MSE `1.69761`, maximum channel difference `18`, and PSNR
`45.8324 dB`. Isolated-layer mean luma rose from `4.63027` to `4.97923`.
The final restored capture is byte-identical to the silence capture.

## Runtime singleton receipt

| Process | Count | PID | State |
|---|---:|---:|---|
| HTTP MCP gateway | 1 | 49776 | healthy; queue depth 0 |
| Arena MCP child | 1 | 46912 | ready; parent is gateway |
| Wire MCP child | 1 | 20828 | ready; parent is gateway |
| Avenue pipe bridge | 1 | 66752 | active |
| Resolume Avenue | 1 | 45652 | exact V2 candidate active |
| Resolume Wire application | 0 | — | closed is valid |

The gateway reported 49 persistent MCP sessions; these are sessions, not
duplicate server processes.
Resolume reported no critical diagnostic issue; the sole warning was the
expected high count of additive witness layers.

## Performance gate

**OPEN — HUMAN TEST REQUIRED / privilege blocked.**

- Baseline UI observation: `23.9 FPS`
- Implied frame time: `41.841 ms`
- Comparable V2 FPS/frame time: unavailable
- Frame-time regression: unavailable
- Provisional rejection threshold: more than `10%`

The UI observation is context only and cannot pass the gate. Non-elevated
PresentMon returned no samples because the user is not in `Performance Log
Users`. Run matched elevated five-minute R1 and V2 captures after the cold
reopen, then accept only if V2 frame time regresses by no more than 10%.

## Automated QA

The structured receipt is
[`APC40_V2_QA_20260719T124750Z.json`](APC40_V2_QA_20260719T124750Z.json).
It reports **21 PASS, 0 failures, 3 human gates open**. The candidate and R1
AVC files, controller XML, geometry JSON, seven PNGs, Python sources, external
media, personal paths, and live singleton topology were validated.

## Open tests

- **OPEN — HUMAN TEST REQUIRED:** cold-open the saved candidate and confirm
  persistence after Resolume restart.
- **OPEN — HUMAN TEST REQUIRED:** complete the APC40 button, fader, knob,
  tempo, crossfader, LED, feedback-color, toggle, and momentary sweep.
- **OPEN — HUMAN TEST REQUIRED:** play real silence, bass/low, midrange, and
  high-frequency material and calibrate the accepted peak.
- **OPEN — HUMAN TEST REQUIRED:** collect matched elevated five-minute R1/V2
  PresentMon intervals and enforce the 10% frame-time gate.

## Five-minute morning test

1. Open the exact V2 candidate above. Confirm its name, 149 layers, one column,
   three decks, and one instance of every runtime singleton.
2. Select `APC 40 MK II - Visual QA`; do not install or modify another XML.
3. Trigger column 1 if needed and confirm all 149 clips are playing.
4. Bypass layer 149, confirm exact R1 restoration, then unbypass it.
5. Sweep every track and master fader through minimum, midpoint, and maximum;
   confirm full travel, readability, and zero chassis intersection.
6. Rotate every ordinary/device knob to both extremes and Tempo in both
   directions; confirm bounded relative behavior and zero intersection.
7. Sweep the crossfader to both endpoints and press every button family;
   confirm toggle/momentary behavior plus LED and feedback colors.
8. Play silence, bass/low, midrange, and high-frequency material; confirm the
   visible silence floor, bounded low-band response, and no unintended
   mid/high response.
9. Confirm all white, red, blue, amber, and RGB witnesses remain readable at
   accepted peak with zero overlap.
10. Record PASS/FAIL for every open item. **Do not promote or merge until all
    gates pass and the user explicitly approves promotion.**
