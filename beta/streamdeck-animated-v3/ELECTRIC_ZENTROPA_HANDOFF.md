# Electric Zentropa - Handoff (late 2026-07-21)

## What was wrong, and the real root cause
The buggy `APC40_Electric_Zentropa.avc` and its `_FLIP` sibling both broke on the
continuous controls. Two root causes:

1. **FFT bleeding onto the knobs.** In the buggy builds the knob rotation/opacity
   picked up an audio-FFT phase source, which overrode the physical MIDI - so the
   knobs "danced" on their own and choked when you tried to turn them. Jeffrey
   called this correctly. **Rule going forward: knobs = MIDI only (static phase
   source). FFT belongs on the grid pads only.**
2. **Two identical "static" clips per continuous layer** (col 1 + col 2). The
   open-state connected them inconsistently and they drifted, so a MIDI CC pointed
   at one clip was a coin-flip. This is why single-clip preset edits kept
   "working then stopping."

Saving the release comp twice during troubleshooting ALSO corrupted it
(1675088 -> 1729915 bytes), which is why the release stopped turning while the
untouched FLIP still turned.

## What is now in place (this file's directory + repo)
- **compositions/APC40_Electric_Zentropa.avc** - REBUILT from the known-good
  master `backups/Spec_Candidate_GOLDEN_MASTER_20260721.avc` (the comp Jeffrey
  confirmed "works great"). Knob rotation + opacity verified `static` (no FFT).
  Bed (L149), Chassis (L150), Sine Wave (L151), Title (L152) all triggered on.
  Internal CompositionInfo name = `APC40_Electric_Zentropa` (matches filename,
  no BOM). Size 1544988.
- **controllers/APC 40 MK II - Electric Zentropa.xml** - clean 203-shortcut
  preset (no BOM). NOTE: this preset was authored against the FLIPPED layout.
- Backups kept: `.PREDUAL`, `.PREFADERFIX` preset snapshots in the Shortcuts/MIDI
  folder; the GOLDEN_MASTER is untouched.

## THE ONE THING TO VERIFY NEXT SESSION (do not skip)
The rebuilt comp came from Spec_Candidate, which pairs with the
**`APC 40 MK II - Visual QA V3 Animated`** preset - NOT necessarily the
`Electric Zentropa` preset. Before committing to git:
1. Open `compositions/APC40_Electric_Zentropa.avc`.
2. Try each preset in Shortcuts and confirm which one makes pads (press->pressed),
   knobs (turn), and faders (travel) ALL work on THIS comp.
3. Ship THAT preset as the paired `.xml`, and fix the README "MIDI preset" section
   to name it. Right now the README names the Electric Zentropa preset - reconcile.

## Naming discipline (Jeffrey's call - enforce every write)
Internal CompositionInfo name MUST match the filename. Current mismatches to fix:
- `APC40_Electric_Zentropa_FLIP.avc` -> internal name is `APC40_Electric_Zentropa`
  (should be `..._FLIP`).
- The GOLDEN_MASTER file's internal name is `APC40_Visual_Twin_V3_Spec_Candidate`
  (expected - it is the Spec Candidate snapshot).

## Not done (deliberately, unattended)
- **No git commit/push.** The .avc file was replaced in the working tree only;
  review + commit after verifying the preset pairing above.
- Social promo images already delivered in chat (1080x1080 + 1200x630).
- Wire "APC40 FFT Driver" patch moved out of the Wire Patches folder to
  `Documents\Resolume Wire\_disabled_APC40_FFT_Driver` so it stops showing in the
  Effects library (repo copy under wire/ is untouched).


## Remaining polish: button "breathing bed" idle state
The saved release baked a mid-test state where a batch of toggle buttons were left
on their ACTIVE clip, so the comp opens showing "on" faces instead of the breathing
idle beds. Column map in THIS comp (confirmed on layer 54 Track Select 1):
- **Column 1 = active/on** face
- **Column 2 = idle/breathing** bed

Fix (do with a stable connection, in the verify session):
1. Trigger **column 2 (idle)** on all button + grid layers (1-93, 118-142, 146-147)
   to set the clean breathing default. Do NOT trigger a full-column scene - that
   would move the knob/fader layers (94-117, 143-145, 148) and re-break their MIDI
   mapping. Keep those on their current working clip.
2. Re-trigger bed L149/col1, chassis L150/col1, sine L151, title L152/col1.
3. save_as over compositions/APC40_Electric_Zentropa.avc, verify internal name
   still = APC40_Electric_Zentropa and no BOM.
Then this is the clean, shippable open-state.


## CLARIFIED (Jeffrey, direct): the button IDLE BEDS are COLUMN 2 and do NOT appear
Precise symptom: the **column-2 "APC40" idle beds** (breathing button beds) are
missing on open. The button layers are connected to **column 1 (active/on face)**
instead of **column 2 (idle bed)**. So at rest you see the "on" faces, never the
breathing beds.

DESIRED DEFAULT open-state for button layers = **column 2 (idle bed) connected**,
with the preset's toggle shortcut flipping to column 1 (active) on press.

Do this in the new window:
1. Connect **column 2** on every BUTTON layer so the idle beds are the resting
   state. Button layers = 41-93 (Scene Launch, Clip Stop, Track Select, Record Arm,
   Solo, Activator, Crossfade A B) and 118-142 + 146-147 (transport + mode buttons).
   Grid pads 1-40 already show correctly - leave them. Do NOT touch knob/fader
   layers 94-117, 143-145, 148 (their MIDI mapping is clip-specific and working).
2. Keep bed L149/col1, chassis L150/col1, sine L151, title L152/col1 connected.
3. save_as over compositions/APC40_Electric_Zentropa.avc; verify internal name =
   APC40_Electric_Zentropa, no BOM.
This gives the breathing-bed idle default Jeffrey wants.
