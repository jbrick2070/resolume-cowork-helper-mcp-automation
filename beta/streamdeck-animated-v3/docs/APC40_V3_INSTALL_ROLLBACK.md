# APC40 Animated Twin V3 — install, verify, roll back

Everything here is new and append-only. R1 (`APC40_Visual_QA_148.avc` +
`APC 40 MK II - Visual QA.xml`) and all prior V2/StreamDeck candidates are
byte-untouched.

## A. Open the candidate (2 min)

1. Keep the media where it is:
   `beta/streamdeck-animated-v3/media/…Surface_Alpha.mov` and `…Chassis_Alpha.mov`
   (the composition references these absolute paths).
2. Open `compositions/APC40_Visual_Twin_V3_Animated_Candidate.avc` in Resolume
   Avenue 7.27.1.
3. The MIDI preset is unchanged — keep using the installed
   `APC 40 MK II - Visual QA.xml` (or the identical copy in this folder's
   `controllers/`). No re-map needed; layers 1–148 kept their indices.

VERIFY (the four human gates, same as prior V2 candidates):
- cold-open shows 150 layers; layers 149 `V3 Chassis Frame` + 150 `V3 Animated
  Surface` play the two MOVs, the 148 witness labels below are intact and readable;
- toggle each grid pad / fader / knob / crossfader and confirm feedback still lands
  on the right witness;
- bypass layers 149 + 150 → the image returns to the R1 twin exactly.

## B. If the candidate misbehaves — manual insertion (also 2 min)

The candidate's two video layers were authored offline, so cold-open is the test.
If anything looks wrong, rebuild the two layers by hand on the guaranteed-safe base:

1. Open `compositions/APC40_Visual_Twin_V3_Base.avc` (a byte-exact renamed R1 — it
   is the R1 twin, so it always opens).
2. Add a new layer at the **top** of the stack (above layer 148). Drag
   `media/APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov` onto its clip 1.
3. Add one more top layer, drag `…Surface_Alpha.mov` onto its clip 1.
4. Set both new layers' blend mode to **Add**, opacity 100%.
5. Save As a new name (do not overwrite R1 or the base).

Because the layers sit above 148 and use Add blend, the witness labels and MIDI map
are untouched — exactly the append-only pattern the StreamDeck handoff used.

## C. Per-control clips (optional library)

`media/clips/` holds 148 standalone loops, each named after its control
(`L102_Track_Knob_1.mov`, `L144_Crossfader.mov`, …). Drop any of them onto their own
layer/clip if you want to drive a single control's animation independently. Each is
a full-control crop and loops seamlessly.

## D. Rollback (instant)

- In the candidate: **bypass layers 149 + 150** → R1 image restored.
- Or just open `APC40_Visual_Twin_V3_Base.avc` (= R1) or the original
  `APC40_Visual_QA_148.avc`.
- Nothing to undo on disk: R1, the controller preset, and all prior candidates were
  never written to. Delete the `streamdeck-animated-v3/` folder to remove V3 wholly.
