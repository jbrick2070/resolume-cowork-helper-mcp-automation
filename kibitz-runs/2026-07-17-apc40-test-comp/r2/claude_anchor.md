ANCHOR REVIEW — r2 (coding plan / implementability)
Reviewer: Claude (driver + panelist), grounded against react-kit + the r1 plan.

VERDICT: yes-with-fixes. The UI-specimen→clone plan is implementable, but three things are
under-specified enough to stall a build.

MUST-FIX BEFORE BUILD:
1. [Build path / specimen] Cloning needs the Text Block source's exact param schema — the
   text-string param name AND the background/colour param — which is unknown until ONE specimen
   is saved and diffed. Gate all cloning on first capturing that param map from the specimen
   (make-one-save-diff). Do not write clone code against an assumed schema.
2. [Manifest / expected colour] For the 32 CLIP pads there is NO single "expected velocity":
   a clip pad's LED comes from column/clip-STATE feedback (playing/loaded/empty), not a fixed
   NamedValues velocity the way the FX toggles do. Split the manifest colour field into
   `column_velocity` (the painter/column scheme, keyed by note%8) vs `state_feedback` (Resolume's
   playing/loaded/empty colours). Only FX pads + painter columns have a single expected velocity.
3. [Placement after flip] The clone must put clip content on the correct (layer, column) so
   pressing note X shows the matching label. Derive (layer, column) from the FROZEN decoded map
   table (RawInputMessage note → target), never from row order. Ship the map-freeze table first.

SHOULD-FIX:
4. [Comp scaffold] Specimen-clone produces a CLIP; you still need the 4-layer × 8-column comp
   shell. Reuse make_gen_avc.py's strip-and-fill pattern: take an existing 4×8 comp, strip its
   clips, inject the 32 text clips. Don't hand-build the comp scaffold.
5. [FX indicators — implementation gap] The 8 FX-state indicators are not clips on the FX pads.
   Spec concretely how each reads effect on/off (a small always-on indicator layer per comp
   effect, driven by the effect's bypass state) — currently hand-wavy for a builder.

CUT: none new.

[ASSUMPTION] Text Block exposes a settable text-string param + an addressable background/colour in
the .avc — unverified until the specimen is diffed.
