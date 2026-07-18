# Grid-Map Test Comp — r1 hardened plan
(synthesis of Claude anchor + Codex, both grounded against react-kit; Claude Code + Antigravity pending)

## What it is
A **preset-agnostic APC40 mkII test composition**: generative clips that self-identify by their
hardware MIDI note, used exclusively to verify (a) the pad→function map and (b) the LED colour set.
Native sources only, no media files.

## The spine — the MIDI note is the test KEY (not a single "UID")
The pad's firmware note is the anchor, but it is NOT the same thing as the Resolume shortcut
`uniqueId` or the clip identity. Every pad carries an explicit **data contract** (one manifest row):
`pad_note · physical_row_col · resolume_target · shortcut_uniqueId · expected_velocity · kind(clip|fx)`.
Lead every clip's on-screen label with the **note**; layer/function is a secondary line.

## Structure — 32 clip pads + an 8-cell FX indicator strip (NOT 40 launch clips)
Both shipped comps are **4 layers** — the bottom row (notes 0–7) are FX **bypass toggles**, not
clip launchers, so those pads can never bring up a clip. So:
- **Rows 1–4 (notes 8–39): 32 self-identifying clips**, one per clip pad.
- **Row 5 (notes 0–7): FX indicators.** Press → the effect toggles → a *persistent on-screen
  indicator* for that effect changes (labelled note / function / expected velocity). Do not pretend
  these pads launch clips.

## Map freeze (do this before building)
Do not build from the asserted row map. Generate a **map-freeze table from the DECODED preset**
(read each shortcut's RawInputMessage note key, not the path order) and confirm with **one hardware
press test**. That decoded table is the single source of truth. (This is exactly the misread the
naive path-order read produces.)

## Colour check — two separate, unambiguous acceptance tests
Run the painter OFF, and check each source on its own:
1. **Resolume native feedback velocity == expected_velocity** (from the manifest).
2. **External direct LED (apc40_led_test.py) == expected_velocity.**
Ground APC40 LED behaviour ONLY in `apc40_led_test.py` — `apc_grid_painter.py` is the APC **mini**,
a different device. The clip's on-screen colour is the visual reference for both.

## Build path — one path only
**UI-specimen → diff → clone.** First make ONE Text Block clip in Avenue 7.27 (large note + row/col/
function text + solid colour fill) and confirm it renders as a single legible self-contained clip;
then clone that specimen into the 32 grid cells with per-cell text/colour. Drop the live-MCP path and
Text Animator/animation for v1 (reliability over motion).

## Deliverables
- The 40-row manifest (data contract above) — build both the clips and the colour checks off it.
- The test comp, cloned from the one specimen.
- A short runbook (load comp → select exact preset → run direct-LED test → press pads in note order →
  record mismatches) + failure taxonomy (wrong note / wrong Resolume target / wrong velocity /
  dim-only feedback / FX-state mismatch).

---
### Judgment log
- **Accepted:** FX-row split (32 clips + 8 indicators); note ≠ uniqueId, use a manifest contract;
  two-source colour check; single UI-clone build path; APC40 colour grounded only in apc40_led_test.py;
  drop animation/Text Animator.
- **Rejected (misread):** Codex "notes 0–7 = Bed" — it read clip paths in default order; the flipped
  React v4.4 has 0–7 = FX (verified by decoding the RawInputMessage keys).
- **Verify-at-build:** one Text Block specimen renders legibly in Avenue 7.27 before cloning;
  make_gen_avc.py lives in the repo *parent* (outside react-kit), so cite it by full path if reused.
