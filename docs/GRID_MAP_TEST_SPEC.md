# APC40 Grid-Map Test Comp — hardened build spec
Self-contained. Hardened across a kibitz arc (r1 arc → r2 implementability → r3 wiring → r4
convergence): Claude anchors + Codex, each grounded against the real repo. Run history:
`kibitz-runs/2026-07-17-apc40-test-comp/`.

## Purpose
A **preset-agnostic, 100%-generative** test composition used exclusively to verify, on the
APC40 mkII + Resolume Avenue 7.27 rig: (1) the pad→function map and (2) the LED colour set.
Every grid pad is keyed to its hardware MIDI note. No media files.

## 1. Manifest — the single source of truth (emit JSON + a generated human table)
One row per pad, notes 0–39. Builder must **enumerate 0–39 and LEFT-JOIN** the parsed shortcuts,
synthesizing the gaps (notes 0 & 6 have no shortcut). Fields:
- `pad_note` (0–39) · `physical_row_col` (R1..R5·C1..C8) · `kind` = clip | fx | empty | blackout
- `resolume_target` (OSC path; null iff kind=empty) · `shortcut_uniqueId` (null iff empty; unique when present)
- `testable_on_screen` (true for clip + fx1–5; **false** for blackout + empty)
- `direct_led_velocity_0_127` + `direct_led_statuses_tested` [0x90,0x95] + `direct_led_status_selected` + `fx_painter_status` (0x96)
- `screen_color_rgb` + serialized `ParamColor` (the clip's on-screen background — RGB in the .avc, NOT a velocity)
- `resolume_feedback_values` = stateful normalized floats keyed by the EXACT NamedValues:
  `Connected`, `Connected & previewing`, `Disconnected`, `Empty`, `Previewing`, `Off` (these are NOT velocity/127)
- `state_polarity` = `bypassed_true_means_effect_off` for fx rows (report bypass-state, not "FX-on")

## 2. Map-freeze parser (implementable, exact)
For each `<Shortcut>` in the preset XML: include only if `(key & 0xFF) == 0x90` (note-on);
`note = (key >> 8) & 0x7F`; keep `note` in 0–39. This excludes CC/fader messages. Assert one
shortcut per expected pad role; confirm with **one hardware press test**; put decoded note + raw
key in every mismatch report. Expected for React v4.4 (flipped): notes 8–39 = clip launch (layers
1–4), notes 1–5 = FX bypass toggles, note 7 = `/composition/bypassed` (blackout), notes 0 & 6 = empty.

## 3. Velocity→screen-colour palette (FREEZE before cloning)
On-screen colour must match the pad LED, so freeze one 8-row table (per column):
`column · velocity(45,37,21,5,9,49,53,3) · colour_label · screen_color_rgb · serialized ParamColor int`.
If the ParamColor ints are unknown, add a build step: make/inspect one Avenue specimen per column
and record the values before any cloning.

## 4. FX row — per-kind behaviour (not "8 indicators")
notes 1–5 = comp-effect bypass toggles (visibly change the output); note 7 = comp blackout (screen
may intentionally go black — the direct-LED test is the only persistent signal, test it LAST and
restore `/composition/bypassed=false`); notes 0 & 6 = empty (dark, no shortcut).

## 5. Clip-clone builder (new, parameterized — do NOT call make_gen_avc.py as-is)
v1 invocation:
`builder --src "compositions/Res React Live Gen.avc" --out "compositions/Res React Grid Map Test.avc" --manifest manifest.json --specimen specimen.avc`
(Orbit is a separate later target.)
- Reuse only make_gen_avc.py's **parse + id-allocation** patterns. **Encoding: latin-1, preserve newlines.**
- Rewrite per clip: `uniqueId` (global-unique allocator), `layerIndex`, `columnIndex`, `ParamText`, `ParamColor`.
  Preserve byte-for-byte: source IDs, render-pass structure, `VideoMixerStateID`, other nested blocks.
- Gate on first diffing ONE saved Text Block specimen to capture its param schema.
- **Validation:** XML parses; introduces **no new duplicate `uniqueId`s** (the base comp legitimately
  repeats column ids across decks — a global dup assertion false-fails); exactly 32 clips on the correct
  (layer,column) per the frozen map; Text Block text non-empty; **no media refs** (no `VideoFile`, no `.mov`).
  Visual legibility = manual acceptance check.

## 6. Runbook (sequencing fixes the port + order conflicts)
1. **Direct-LED test FIRST**, before Avenue owns the MIDI-out port (else `apc40_led_test.py` exits on
   PORT BUSY). Give that script `--port-index`/`--port-name` (default = first "APC40" match); require
   verified exit codes 0/1/2.
2. Re-enable Resolume MIDI output; record "Update clip panels on external triggers" state; **painter STOPPED**.
3. Launch the exact high-contrast test clip: **note 8 (layer 1, column 1)**.
4. Test clip notes 8–39 against the live image.
5. Test FX notes 1–5 against the live image.
6. Test note 7 **blackout LAST**; restore `/composition/bypassed=false`.
7. Teardown: stop painters; restore comp + FX bypass states.
Failure taxonomy: wrong note / wrong target / wrong velocity / dim-only feedback / FX-state / blackout.

## 7. Verify-at-build checklist (do before/at build)
1. Text Block specimen schema (`ParamText`, `ParamColor`, bg/source colour) from Avenue 7.27.
2. Specimen renders legibly.
3. `apc40_led_test.py` (in the repo **parent**) path / CLI / selected port / return codes.
4. Which LED status byte is the accepted bright-solid on hardware: 0x90, 0x95, or 0x96.
5. Frozen velocity→RGB/`ParamColor` palette vs BOTH hardware LEDs and Avenue-rendered screen colour.
6. Decoded preset map (notes 1–5 FX, note 7 blackout, notes 0/6 empty).
7. Post-build `.avc`: parses, no new dup `uniqueId`s, exactly 32 test clips on the frozen map, non-empty
   text, no media refs.

## Build path
UI Text Block specimen → diff → deterministic clone. CUT for v1: live-MCP build, CSV output,
Text Animator/animation, `fx_row_paint.py` in the acceptance contract.
