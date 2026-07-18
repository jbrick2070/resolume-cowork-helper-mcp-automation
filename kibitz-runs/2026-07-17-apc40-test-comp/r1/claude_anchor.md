ANCHOR REVIEW — r1 (high-level arc / creative coherence)
Reviewer: Claude (driver + panelist), grounded against the real repo.

VERDICT: yes-with-fixes. The concept (a 100%-gen self-identifying grid keyed to the MIDI note)
is coherent and serves the debug goal, but it has one silent-failure gap (the FX row), an
ambiguous colour-check premise, and an unresolved build path that currently blocks it.

MUST-FIX BEFORE BUILD:
1. [Core concept + Row 5] The plan says every one of the 40 pads gets a clip that fires when
   pressed. FALSE for the bottom row: notes 0–7 are FX **bypass toggles** (behaviour="4" in the
   preset), not clip-launchers — pressing them toggles a composition effect and connects NO
   clip. So 8 of the 40 "self-identifying clips" never appear when their pad is pressed; the
   test silently does nothing for the whole FX row. Fix: scope the clip-grid test to the 32
   CLIP pads (rows 1–4) explicitly, and test the FX row a different way (the effect's own
   visible change on the output), or drop row-5 clips entirely.
2. [Debug job 2 — colour set] "clip background == pad LED colour" conflates TWO colour sources
   that don't agree: Resolume native feedback (dim ~10%, on-change) and the painter (bright
   100%, static). The plan never says which the on-screen colour is compared against, so a
   "mismatch" is uninterpretable. Fix: define exact test conditions — e.g. "painter OFF; does
   the native pad LED match the clip's on-screen colour on trigger?" One source at a time.
3. [Build path] The whole thing is blocked on the open "specimen-clone vs live-MCP" question.
   Given the serializer law + the "comp open ⇒ don't file-edit" write law, the specimen-clone
   path needs a Text Block donor that doesn't exist yet, and the MCP path carries mid-session
   write footguns. Fix: pick ONE path + name its single prerequisite so the concept isn't stuck.

SHOULD-FIX:
4. [Note map labels] The plan hard-codes the flipped React v4.4 map (Pulse=top). The LIVE preset
   in the Resolume MIDI folder lags the repo copy unless re-copied, so "R1=Pulse" labels can be
   wrong for whatever preset is actually loaded. Fix: make the comp **preset-agnostic** — lead
   with the NOTE (hardware ground truth), make layer/function a secondary line.
5. [Scope — three jobs] The comp is asked to (a) map notes, (b) check colour, (c) be the
   velocity→colour reference. State that the **note is primary**; colour is a secondary overlay,
   so the design doesn't over-index on colour fidelity.

OPTIONAL: a tiny always-on "last-note received" HUD layer would make the note-map test instant.

CUT THESE:
6. [Wavy / animation] Motion adds render cost and zero debug value; static labels read better on
   a fast-flashing grid. Safe to cut for a test tool.
7. [FX effect-name labels] Given #1, labelling row-5 clips "Hue Rotate" etc. is misleading (they
   won't show). Cut effect names from clip content.

[ASSUMPTION] the live MIDI-folder preset may lag the flipped repo copy; the comp's comp-FX rack
has 5 effects + blackout (read from the preset's targets, not fully from the comp file itself).
