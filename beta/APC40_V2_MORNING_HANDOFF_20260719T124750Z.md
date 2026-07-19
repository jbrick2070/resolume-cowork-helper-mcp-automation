# APC40 Visual Twin V2 — Morning Handoff

Run ID: `20260719T124750Z`

## Verdict

**PARTIAL — software candidate ready for human test.**

The saved candidate, R1 integrity, append-only structure, MIDI contract,
collision geometry, visual evidence, FFT configuration, external-media scan,
and MCP singleton topology pass automated QA. Physical APC40 behavior, real
audio calibration, a cold reopen, and comparable elevated performance capture
remain **OPEN — HUMAN TEST REQUIRED**. Do not promote or merge this candidate
until those checks pass and the user explicitly approves promotion.

## Candidate and Git receipt

- Current absolute path:
  `C:\Art Projects\Res_Fable\react-kit-apc40-v2-overnight\beta\compositions\APC40_Visual_Twin_V2_Candidate_20260719T124750Z.avc`
- Repository path:
  `beta/compositions/APC40_Visual_Twin_V2_Candidate_20260719T124750Z.avc`
- Composition name:
  `APC40_Visual_Twin_V2_Candidate_20260719T124750Z`
- Candidate SHA-256:
  `3727adb8973f63f8988014e1b29efc03e6018900474e0ca502901f94d1883329`
- Branch: `codex/apc40-v2-overnight`
- Candidate/artifact commit:
  `2c926629e0dffab5a1ad7ace5399e15acecfcad0`
- Starting `main`/`origin/main` commit:
  `c0a318da260b58c12c8545fe43a091bbbbc966c6`
- Push target: `origin/codex/apc40-v2-overnight`

This handoff is intentionally a later documentation commit so it can contain
the immutable candidate/artifact commit hash above. After pulling the branch,
`git rev-parse HEAD` identifies the handoff receipt commit.

## R1 protection receipt

Both canonical R1 files were hashed before mutation and again after the final
candidate save. They remain byte-identical and were never overwritten,
renamed, installed, or cleaned up.

| Protected file | Before SHA-256 | After SHA-256 | Result |
|---|---|---|---|
| `compositions/APC40_Visual_QA_148.avc` | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` | PASS |
| `controllers/APC 40 MK II - Visual QA.xml` | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` | PASS |

The validator reads the canonical on-rig R1 paths because a linked worktree
checkout may normalize XML line endings even when Git correctly reports the
tracked controller file as unchanged.

## Exact V2 addition

Only one layer was appended above the frozen R1 range:

- Layer 149: `V2 Chassis Low FFT`
- Clip 149 / column 1: `V2 Chassis Low FFT`
- Source: native `Text Block` / `BlockTextGenerator`
- Font dependency: installed `Cascadia Mono`, Regular
- Text color: `#557f96ff`
- Source size: `0.5`
- Source line width: `5000`
- Transform: X `-21`, Y `0`, Scale `50`, Scale W `184`, Scale H `181`
- Layer opacity: `1.0`
- Blend: `Add`
- Added MIDI shortcuts: `0`
- Added effects: only the mandatory clip Transform
- External media: `0`

The chassis is generated from deterministic, clipped ASCII geometry. It adds a
subtle controller shell, section separators, rotary surrounds, eight track
fader guides, a master guide, and a crossfader guide without entering any
protected R1 label, witness, or full-motion envelope.

Instant rollback is the layer-149 **Bypass** toggle. Bypassing layer 149 restores
the accepted R1 image; unbypass restores V2. No R1 layer needs to be changed.

## Reconciled counts

| Item | Count |
|---|---:|
| Resolution | 1920 × 1080 |
| Decks | 3 |
| Columns | 1 |
| Groups | 0 |
| Layers | 149 |
| Frozen R1 layers | 148 |
| Added layers | 1 |
| Clips | 149 |
| Generator video sources | 149 |
| MIDI shortcut records | 203 |
| Unique shortcut IDs | 203 |
| Raw MIDI messages | 203 |
| Unique raw MIDI keys | 148 |
| Added MIDI shortcuts | 0 |
| External media files | 0 |

The first 148 layer IDs, names, colors, render-pass behavior, clip IDs, source
IDs/types, and static witness configuration match R1 semantically. The receipt
also documents two accepted save-time current-value differences that do not
change behavior: one transition-mixer runtime value and one audio numeric
serialization drift of at most `0.0001`.

## FFT contract

FFT affects decoration only:

- Target: clip 149 video opacity
- Phase source: composition FFT (`/audioengine/compositionfft`)
- Avenue normalized band selection: value `0.165`, range `0.00–0.33`
- Gain: `+3 dB`
- Fallback: `1400 ms`
- Output opacity: `0.12–0.28`
- Value behavior: forward (`>`)
- Nonzero silence floor: `0.12`
- Bounded accepted peak: `0.28`
- Geometry modulation: none
- Position/scale/rotation/extent modulation: none
- Hue/color/blur modulation: none
- R1 witness modulation: none

The low-band accepted peak was synthesized only to prove the configured output
envelope and capture visual evidence. Real bass, midrange, and high-frequency
isolation remains a human audio test.

## Collision QA

The deterministic geometry artifact protects all 148 controls with 4 px
padding around 295 distinct label/witness/motion boxes. It contains 54 vector
primitives and 830 surviving native text cells.

| State | Method | Intersections | Human status |
|---|---|---:|---|
| Resting / all visible | Saved composite plus protected geometry | 0 | Automated PASS |
| Track and master faders min/mid/max | Full protected motion boxes | 0 | Physical sweep OPEN |
| Ordinary and device knobs at both extremes | Full rotary motion hulls | 0 | Physical sweep OPEN |
| Crossfader at both endpoints | Full protected motion box | 0 | Physical sweep OPEN |
| Chassis-only silence floor | Isolated layer capture | 0 | Automated PASS |
| Implemented low-band accepted peak | Isolated layer and full composite | 0 | Real-audio peak OPEN |
| Layer-149 bypass | R1 baseline/bypass comparison | 0 | Automated PASS |

Vector collisions: `0`. Native text-cell collisions: `0`.

## Visual evidence

- [R1 witness baseline](screenshots/apc40-v2-20260719T124750Z/01-r1-witnesses-candidate-baseline.png)
- [FFT silence composite](screenshots/apc40-v2-20260719T124750Z/03-v2-fft-silence-composite.png)
- [FFT silence, layer 149 isolated](screenshots/apc40-v2-20260719T124750Z/03b-v2-fft-silence-layer.png)
- [Layer-149 bypass / R1 restoration](screenshots/apc40-v2-20260719T124750Z/04-v2-bypass-r1-restore.png)
- [Synthetic low-band accepted peak, all witnesses](screenshots/apc40-v2-20260719T124750Z/05-v2-low-band-peak-envelope.png)
- [Synthetic low-band accepted peak, layer 149 isolated](screenshots/apc40-v2-20260719T124750Z/05b-v2-low-band-peak-layer.png)
- [Final restored silence state](screenshots/apc40-v2-20260719T124750Z/06-v2-final-restored.png)

Baseline versus bypass quantitative comparison:

- PSNR: `47.2251 dB`
- MAE: `0.24109`
- MSE: `1.23189`
- Maximum channel difference: `36`
- Changed pixels: `3325 / 22600` (`14.712%`)

This is a near-identical restoration at monitor-capture scale; the residual is
capture/render antialiasing noise. Silence-to-peak composite changed 435 pixels.
The isolated chassis mean luma increased from `0.65999` to `0.67183`. The final
restored composite is byte-identical to the silence composite. Motion analysis
under silence measured `0.00`, confirming the chassis geometry is static.

Resolume reported no critical diagnostics. Its one warning was the expected
high count of additive witness layers. The loaded-file inventory was empty.

## Runtime singleton receipt

Final observed topology:

| Process | Count | PID | Parent / state |
|---|---:|---:|---|
| HTTP MCP gateway | 1 | 49776 | healthy, ready, queue depth 0 |
| Arena MCP child | 1 | 46912 | parent 49776, ready |
| Wire MCP child | 1 | 20828 | parent 49776, ready |
| Avenue pipe bridge | 1 | 66752 | active |
| Resolume Avenue | 1 | 45652 | exact V2 candidate active |
| Resolume Wire application | 0 | — | closed is valid |

The singleton check distinguishes persistent MCP sessions from actual server
processes. No duplicate bridge, gateway, Arena child, Wire child, or Avenue
application was running.

## Performance gate

**OPEN — HUMAN TEST REQUIRED / privilege blocked.**

- Baseline UI observation: `23.9 FPS` (context only)
- Implied frame time: `41.841 ms`
- Comparable V2 FPS/frame time: unavailable
- Computed regression: unavailable
- Rejection threshold: more than `10%` frame-time regression

PresentMon v1.7 is installed at:

`C:\Program Files\NVIDIA Corporation\FrameViewSDK\bin\PresentMon_x64.exe`

The unattended, non-elevated capture exited without samples; the current user
is not in `Performance Log Users`. Therefore neither performance pass nor
regression percentage is claimed.

Run each composition for five comparable minutes from an elevated PowerShell:

```powershell
$pm = 'C:\Program Files\NVIDIA Corporation\FrameViewSDK\bin\PresentMon_x64.exe'
$avenuePid = (Get-Process -Name Avenue | Select-Object -First 1).Id
& $pm --process_id $avenuePid --timed 300 --terminate_after_timed `
  --output_stdout --no_console_stats --no_track_input `
  --session_name APC40_R1_5m |
  Set-Content -LiteralPath "$env:USERPROFILE\Desktop\apc40-r1-5m.csv"
```

Repeat after opening V2, changing both `R1` labels above to `V2`. Calculate:

```powershell
$r1 = (Import-Csv "$env:USERPROFILE\Desktop\apc40-r1-5m.csv" |
  Measure-Object -Property MsBetweenPresents -Average).Average
$v2 = (Import-Csv "$env:USERPROFILE\Desktop\apc40-v2-5m.csv" |
  Measure-Object -Property MsBetweenPresents -Average).Average
$regressionPercent = 100 * (($v2 / $r1) - 1)
```

Accept only when `$regressionPercent -le 10`.

## Automated QA reproduction

From the repository root:

```powershell
python beta/tools/build_apc40_v2_geometry.py --check
python beta/tools/validate_apc40_v2.py `
  --canonical-r1-root 'C:\Art Projects\Res_Fable\react-kit' --check
```

The structured receipt is
[`beta/APC40_V2_QA_20260719T124750Z.json`](APC40_V2_QA_20260719T124750Z.json).
It reports 21 automated checks passed, zero failures, and three explicit human
gates open. Both generated JSON files were reopened and parsed; both Python
tools compile; the AVC and controller XML parse; no personal path, secret
marker, URL, or external-media reference was found.

## Open tests

- **OPEN — HUMAN TEST REQUIRED:** cold-open the saved candidate and confirm
  persistence after Resolume restart.
- **OPEN — HUMAN TEST REQUIRED:** complete APC40 button, fader, knob, tempo,
  crossfader, LED, feedback-color, toggle, and momentary behavior sweep.
- **OPEN — HUMAN TEST REQUIRED:** play silence, isolated bass/low, midrange,
  and high-frequency material and confirm only the intended low band breathes.
- **OPEN — HUMAN TEST REQUIRED:** confirm readability of white, red, blue,
  amber, and RGB witnesses at a real output size.
- **OPEN — HUMAN TEST REQUIRED:** collect matched elevated 5-minute R1/V2
  PresentMon intervals and enforce the 10% frame-time gate.

## Five-minute morning controller test

1. Open the exact V2 candidate above; confirm the exact composition name,
   149 layers, one column, three decks, and one instance of every runtime
   singleton.
2. Select `APC 40 MK II - Visual QA`; do not install or modify another XML.
3. Trigger column 1 if needed and confirm all 149 clips are playing.
4. Toggle Bypass on layer 149: confirm the accepted R1 image returns instantly,
   then unbypass and confirm the chassis returns.
5. Sweep every track fader and the master fader through minimum, midpoint, and
   maximum; verify full travel and zero chassis intersection.
6. Rotate every ordinary/device knob to both extremes and rotate Tempo in both
   directions; verify bounded relative behavior and zero intersection.
7. Sweep the crossfader to both endpoints, then press every button family;
   verify toggle/momentary behavior plus LED and feedback color families.
8. Play silence, bass/low, midrange, and high-frequency material; confirm a
   visible floor at silence, bounded low-band breathing, and no unintended
   mid/high response.
9. Confirm all controls remain readable at accepted peak, including white,
   red, blue, amber, and RGB witnesses; confirm no overlap anywhere.
10. Record PASS/FAIL for each open item. Promote or merge only after all pass
    and the user explicitly approves promotion.
