# APC40 Visual Twin V2 — Comparison Handoff

Run ID: `20260719T204648Z`  ·  Branch: `codex/apc40-v2-overnight-compare`

## Verdict

**PARTIAL — comparison candidate ready for human test.** Automated QA reports
**21 PASS, 0 failures, 4 human gates open**. This attempt is a *positioning*
refinement of the verified `20260719T124750Z` candidate. The earlier verified
candidate and all its artifacts are untouched and remain the fallback.

Do not merge, open a PR, or change `main`. The comparison branch is pushed for
review only.

## What changed vs the verified 124750Z candidate

1. **Knob contours re-centered (the point of this attempt).** User feedback:
   *"I don't mind the styles of the lines but the positioning could be
   improved."* The prior rings were centered on the knob witness alone, sitting
   ~35–40 px too high and cutting off each rotated label. New rings enclose the
   knob **and** its rotated label group, anchored on the protected
   witness/label boxes and cross-checked against the measured green markup:
   - 8 track knobs: centered `cy≈174`, `rx 56 / ry 50` (was `cy≈122`).
   - 8 device knobs: `cy 483 / 605`, `rx 50 / ry 42–43` (was `cy 442 / 571`).
   - Cue: `(1216, 732, 48, 50)` (was `(1234, 716, 56, 62)`).
   - Tempo, all dividers, rails, and the crossfader base are unchanged (they
     already aligned to the labeled regions).
2. **Internal composition name fixed.** The verified candidate's file was named
   `…Compare…` but its internal `CompositionInfo`/`Param Name` still read
   `…Candidate_124750Z`, so Avenue's title bar could not distinguish the two.
   Both name fields now read `APC40_Visual_Twin_V2_Compare_20260719T204648Z`.
3. **Line style, Text Block calibration, FFT contract, crossfader base, and all
   R1 layers (1–148) are byte-for-byte unchanged.**

## Candidate & protection

| Item | Value |
|---|---|
| Candidate | `beta/compositions/APC40_Visual_Twin_V2_Compare_20260719T204648Z.avc` |
| Internal name | `APC40_Visual_Twin_V2_Compare_20260719T204648Z` |
| Candidate SHA-256 | `ec3a5447e9febee1f407ae59bfe9e1b44046b0b87d448aa9f8297182b756cc52` |
| R1 AVC (unchanged) | `91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99` |
| R1 controller XML, LF-normalized (unchanged) | `4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5` |

The candidate is a surgical copy of the verified 124750Z candidate: only the
chassis Text Block raster (layer 149) and the two composition-name fields
differ. Diff is confined to those spans; layers 1–148 are byte-identical, so
bypassing layers 149+150 restores R1 exactly.

## Geometry (deterministic)

- Artifact: `beta/APC40_V2_GEOMETRY_20260719T204648Z.json`
- Native text SHA-256: `d05a6efe843e0ea300eaf8570943ceb1830ba3ff96f0e751183d39e760198611`
- Primitives: `72` (`54` lines, `17` ellipses, `1` circle); collisions `0`.
- Grid `160×60` chars / effective dot grid `320×240`.
- Desired / occupied / clipped dots: `6622 / 5435 / 1187`; nonblank glyphs `2235`.
- Clipped-intent (protected-envelope) intersections: `79` — deliberate breaks
  where a ring crosses a knob or grid label; final vector/rendered/text-cell
  collisions are `0`.

## Visual verification (Avenue, this session)

The composition was loaded and column 1 triggered; a full-resolution capture of
Avenue's composition monitor confirms, in deep Akai red (`#b51d35`, no green):
rings cleanly enclosing every track knob, device knob, Cue, and Tempo label;
horizontal/vertical dividers framing the pad grid, scene, transport, device, and
navigation regions; scene underlines and left/track rails; and a bold crossfader
base under X-FADE. An offline overlay of the regenerated primitives on the
green-markup reference confirms the placement matches the user's marks.

## FFT contract (unchanged)

`composition_fft` on both added clips' `video/opacity`: band `0.00–0.33`, gain
`+3 dB`, fallback `1400 ms`, output `0.65–0.95`, exactly 2 nodes. Synthetic
floor vs peak is visibly distinct (composite `4762` px, isolated layer `4282`
px changed at 200×113). The range was restored exactly after the test; final ==
floor; get_animation confirms no stuck state. **Real-audio distinctness remains
a human gate** — the low band was silent during capture, so floor/peak were
forced via the output-range clamp, then restored.

## Evidence (7 frames, transport paused for determinism)

`beta/screenshots/apc40-v2-20260719T204648Z/`: `01-baseline` (= R1 bypass
state), `03-v2-fft-floor`, `03b-v2-decoration-layer-isolated`,
`04-v2-bypass-r1-restore`, `05-v2-fft-peak`, `05b-v2-decoration-layer-peak`,
`06-v2-final-restored`. Baseline == bypass and floor == final are byte-identical;
floor vs peak are distinct. (Live "APC40 Live" witnesses animate over time, so
frames were captured with the transport paused; it was restored to Play after.)

## Tooling

- `beta/tools/build_apc40_v2_geometry.py` — contour coordinates updated; grid,
  encoding, transform, and dividers unchanged.
- `beta/tools/inject_apc40_v2.py` — **new** offline, deterministic injector:
  swaps only the chassis raster into a source `.avc` and renames the
  composition to match the file. No Resolume runtime required, so it cannot
  disturb a live session.
- `beta/tools/validate_apc40_v2.py` — retargeted to this run; the R1 controller
  hash check is now LF-normalized (Windows checkouts store CRLF while the
  canonical hash is the LF digest).

## Open — HUMAN TEST REQUIRED

1. Cold-reopen the candidate and confirm geometry, FFT, playback, bypass, and
   all 150 clips persist.
2. Physical APC40 button / feedback-color / fader / knob / tempo / crossfader
   sweep.
3. Real-audio FFT: silence, low/bass, mid, high, accepted peak.
4. Matched elevated five-minute R1 vs V2 performance (≤ 10% frame-time
   regression).
