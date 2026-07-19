# APC40 Visual Twin V2 — Morning Handoff

Run ID: `20260719T124750Z`

## Verdict

**PARTIAL — software candidate ready for human test.**

Automated QA reports **22 PASS, 0 failures, and 4 human gates open**. The saved
candidate, immutable R1 hashes, append-only structure, MIDI contract,
deterministic collision geometry, seven-frame visual evidence, bounded FFT
configuration, external-media scan, and exact MCP singleton topology pass.

Cold reopen, the physical APC40 sweep, real-audio calibration, and matched
performance remain **OPEN — HUMAN TEST REQUIRED**. Do not promote, merge, open a
PR, or change `main` until all four tests pass and the user explicitly approves
promotion.

## Candidate and Git receipt

- Candidate:
  `beta/compositions/APC40_Visual_Twin_V2_Candidate_20260719T124750Z.avc`
- Composition name: `APC40_Visual_Twin_V2_Candidate_20260719T124750Z`
- Candidate SHA-256:
  `ceaf9d54a7891c835f2bc8b43df83af9478b2a94f4349ad61a716858cf05c013`
- Branch: `codex/apc40-v2-overnight`
- Tested candidate/artifact commit:
  `5402da4291449ba6eece4868bc1f3451479fb19f`
- Push receipt: the tested artifact commit equals
  `origin/codex/apc40-v2-overnight`.

This handoff is intentionally committed after the tested artifacts so it can
record their exact commit.

## R1 protection receipt

Both canonical R1 files remain byte-identical before and after the final V2
save.

| Protected file | Before SHA-256 | After SHA-256 |
|---|---|---|
| `compositions/APC40_Visual_QA_148.avc` | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` |
| `controllers/APC 40 MK II - Visual QA.xml` | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` |

## Exact V2 additions and bypass

Two append-only layers sit above the frozen R1 range:

- Layer 149 / clip 149: `V2 Chassis Low FFT`
  - Native `Text Block` / `BlockTextGenerator`
  - Cascadia Mono, Regular
  - Fill and outline: deep Akai red `#b51d35ff`
  - Outline Width `0.32`
  - Text size `0.5`, source scale `0.28`, line width `5000`
  - Transform X `13`, Y `0`, Scale `50`, Scale W `204`, Scale H `170`
  - Add blend, layer opacity `1.0`
  - No audio track, external media, added MIDI, or effects beyond Transform
- Layer 150 / clip 150: `V2 Crossfader Base`
  - Native `Solid Color`, deep Akai red `#b51d35ff`
  - Transform X `637`, Y `480`, Scale `100`, Scale W `13.9`, Scale H `0.5`
  - Rectangle center `[1597,1020]`, size `266.88 × 5.4`
  - Bounds `[1463.56,1017.3,1730.44,1022.7]`
  - Add blend, layer opacity `1.0`
  - No audio track, external media, added MIDI, or effects beyond Transform

The user's green strokes were placement markup only. **No green decoration is
present in the candidate.**

For instant rollback, toggle **Bypass** on layers 149 and 150. Bypassing both
restores the R1 image byte-for-byte; unbypassing both restores V2. No protected
layer changes.

## Reconciled counts

| Item | Count |
|---|---:|
| Resolution | 1920 × 1080 |
| Decks / active-deck columns / groups | 3 / 1 / 0 |
| Inactive-deck clips | 0 / 0 |
| Layers / clips | 150 / 150 |
| Frozen R1 layers / added layers | 148 / 2 |
| MIDI shortcut records / unique raw MIDI keys | 203 / 148 |
| Added MIDI shortcuts / external media | 0 / 0 |

The first 148 layer and clip identities, sources, mappings, and static witness
semantics match R1.

## Geometry and collision QA

- Geometry artifact:
  `beta/APC40_V2_GEOMETRY_20260719T124750Z.json`
- Geometry SHA-256:
  `a1c40e586179b8fda4111291c450c2bb71046214d72ac74b0c5519f78bb2dd00`
- Native Text SHA-256:
  `8507f7b5017405bb738281b3105daf67c24f3201c0ca5c39dd4b6f28f512ee4b`
- Glyph grid / effective dot grid: `160 × 60` / `320 × 240`
- Primitives: `72` represented, `0` empty
- Primitive kinds: `54` lines, `17` ellipses, `1` circle
- Clipping-enabled primitives: `35`
- Expected pre-clipping protected-envelope intersections: `45`
- Desired / clipped / retained dots: `6640 / 749 / 5891`
- Nonblank glyphs: `2334`
- Unexpected vector collisions: `0`
- Rendered-dot collisions: `0`
- Text-cell collisions: `0`
- Solid crossfader-base collisions: `0`

The `45` intersections are input intent paths rejected by deterministic
protection clipping; they are not output collisions. Final vector, rendered,
text-cell, motion-envelope, and crossfader-base collisions are zero. The visible
breaks in large contours around labels are therefore intentional protection,
not missing geometry.

## FFT contract

FFT affects clip opacity only on the two new decoration layers:

- Phase source: composition FFT (`/audioengine/compositionfft`)
- Low-band range / selected value: `0.00–0.33` / `0.165`
- Gain: `+3 dB`
- Fallback: `1400 ms`
- Output opacity: `0.65–0.95`
- FFT nodes: exactly `2`, one per added clip
- Geometry, position, scale, rotation, extent, hue, color, blur, and R1 witness
  modulation: none

The synthetic floor and peak frames prove a bounded visual response. The saved
floor frame equals the final restored frame byte-for-byte, proving the synthetic
peak test left no ghosting or stuck endpoint state. Real-audio response remains
an open human gate.

## Visual evidence

- [R1 witness baseline](screenshots/apc40-v2-20260719T124750Z/01-r1-witnesses-candidate-baseline.png)
- [FFT floor composite](screenshots/apc40-v2-20260719T124750Z/03-v2-fft-silence-composite.png)
- [FFT floor, layer 149 isolated](screenshots/apc40-v2-20260719T124750Z/03b-v2-fft-silence-layer.png)
- [Both V2 layers bypassed / exact R1 restoration](screenshots/apc40-v2-20260719T124750Z/04-v2-bypass-r1-restore.png)
- [Synthetic low-band peak composite](screenshots/apc40-v2-20260719T124750Z/05-v2-low-band-peak-envelope.png)
- [Synthetic low-band peak, layer 149 isolated](screenshots/apc40-v2-20260719T124750Z/05b-v2-low-band-peak-layer.png)
- [Final restored floor](screenshots/apc40-v2-20260719T124750Z/06-v2-final-restored.png)

Baseline versus bypass is file- and pixel-identical: `0` changed pixels. Floor
versus final restored is also file- and pixel-identical.

Composite floor versus peak changed `3704 / 22600` pixels (`16.38938%`), with
MAE `0.111460`, MSE `0.191077`, maximum channel difference `9`, and PSNR
`55.3187 dB`. The isolated layer changed `3347 / 22600` pixels (`14.80973%`),
with MAE `0.087080`, MSE `0.108378`, maximum difference `5`, and PSNR
`57.7814 dB`.

The isolated mean luma was `3.232016` at floor and `3.178647` at peak. Arena's
downsampled alpha-composited monitor is not a monotonic opacity meter, so
accepted-range increase is proved by the exact numeric FFT contract, not luma.

## Runtime singleton receipt

| Process | Count | PID | State |
|---|---:|---:|---|
| HTTP MCP gateway | 1 | 49776 | healthy, ready, queue depth 0 |
| Arena MCP child | 1 | 46912 | ready; parent is gateway |
| Wire MCP child | 1 | 20828 | ready; parent is gateway |
| Avenue pipe bridge | 1 | 66752 | active |
| Resolume Avenue | 1 | 45652 | exact V2 candidate active |
| Resolume Wire application | 0 | — | closed is valid |

The gateway reported `109` persistent MCP sessions. Sessions are not duplicate
server processes.

## Performance gate

**OPEN — HUMAN TEST REQUIRED.**

- Baseline UI context: `23.9 FPS` / `41.841 ms`
- Comparable V2 result: unavailable
- Provisional rejection threshold: more than `10%` frame-time regression

The UI value is context only and cannot pass the gate. Collect matched elevated
five-minute R1 and V2 intervals after the cold reopen.

## Automated QA

The structured receipt is
[`APC40_V2_QA_20260719T124750Z.json`](APC40_V2_QA_20260719T124750Z.json).
Generation and immediate `--check` both report **22 PASS, 0 failures, 4 human
gates open**, with runtime enabled. Both Python tools pass `py_compile`;
builder generation/check, validator generation/check, `git diff --check`, exact
staged-scope review, personal-path scanning, and local/remote artifact-commit
parity pass.

## Open tests

1. **OPEN — HUMAN TEST REQUIRED:** with explicit restart authorization,
   cold-open the candidate and verify geometry, FFT, playback, bypass, and all
   150 clips persist.
2. **OPEN — HUMAN TEST REQUIRED:** complete the APC40 button, feedback-color,
   fader, knob, tempo, and crossfader sweep.
3. **OPEN — HUMAN TEST REQUIRED:** play real silence, low/bass, midrange,
   high-frequency, and accepted-peak material.
4. **OPEN — HUMAN TEST REQUIRED:** collect matched elevated five-minute R1/V2
   performance intervals and enforce the 10% frame-time threshold.

## Five-minute morning test

1. After explicitly authorizing the restart gate, cold-open the exact candidate
   above. Confirm its name, 150 layers, one active column, three decks, empty
   inactive decks, and one instance of every runtime singleton.
2. Select the verified `APC 40 MK II - Visual QA` preset; do not install or
   modify another XML.
3. Trigger column 1 if needed and confirm all 150 clips play and controller
   feedback is ready.
4. Bypass layers 149 and 150, confirm exact R1 restoration, then unbypass both.
5. Sweep every track and master fader through minimum, midpoint, and maximum;
   confirm full travel, readability, and zero chassis intersection.
6. Rotate every ordinary/device knob to both extremes and Tempo in both
   directions; confirm bounded relative behavior and zero intersection.
7. Sweep the crossfader to both endpoints and press every button family;
   confirm toggle/momentary behavior plus LED and feedback colors.
8. Play silence, bass/low, midrange, and high-frequency material; confirm the
   visible silence floor, bounded low-band response, and no unintended mid/high
   response.
9. Confirm every white, red, blue, amber, and RGB witness remains readable at
   accepted peak with zero overlap. Capture matched five-minute R1/V2
   performance and reject more than 10% frame-time regression.
10. Record PASS/FAIL for all four open gates. **Do not promote, merge, open a PR,
    or change `main` until every gate passes and the user explicitly approves
    promotion.**
