# Grid-Map Test Comp — r3 hardened plan (wiring / integration / sequencing)
(r2 plan + Codex r3, grounded against react-kit + the parent repo)

## Manifest builder (fixes the empty-pad join)
Enumerate notes **0–39**, LEFT-JOIN the parsed shortcuts, and synthesize the missing ones:
notes 0 & 6 → `kind=empty, shortcut_uniqueId=null, resolume_target=null, resolume_feedback_values=null`.
Never iterate only `<Shortcut>` rows (that silently drops 0 & 6).

Manifest colour now carries THREE distinct representations (they are not interchangeable):
- `direct_led_velocity_0_127` + `raw_status` (the APC LED integer + note-on channel — note the scripts
  disagree: `apc40_led_test.py` uses 0x90/0x95, `fx_row_paint.py` uses 0x96; record which).
- `screen_color_rgb` / serialized `ParamColor` — the clip's on-screen background (RGB ranges in the
  `.avc`, NOT an APC velocity). Add an explicit velocity→RGB palette lookup.
- `resolume_feedback_values` — the preset's stateful normalized floats, keyed by the EXACT NamedValues
  keys incl. `Connected & previewing`.
- `state_polarity=bypassed_true_means_effect_off` for FX rows; report bypass-state, not "FX-on".

## Runbook sequencing (fixes the port + order conflicts)
1. **Direct-LED test FIRST**, before Avenue owns the MIDI out port (or close Resolume MIDI output for
   this step) — the script opens the port directly and exits on PORT BUSY otherwise.
2. Re-enable Resolume MIDI output. Record "Update clip panels on external triggers" state. Painter STOPPED.
3. Launch a known visible clip; test clip notes 8–39 against the live image.
4. Test FX notes 1–5 against that live image.
5. Test note 7 **blackout LAST**, then explicitly restore `/composition/bypassed=false`.
6. **Teardown:** stop painters, restore comp + FX bypass states, optionally clear LEDs.
Add `--port-index`/`--port-name` to `apc40_led_test.py` (it currently just grabs the first "APC40"),
or drop port-select from the acceptance criteria.

## Clip-clone builder (fixes the generator wiring)
- Write a NEW parameterized builder `--src --out --manifest --specimen`; reuse only make_gen_avc.py's
  **parse + id-allocation** patterns (it is hard-coded for the Orbit source/deck map — do not call it as-is).
- **Encoding:** read/write `.avc` as **latin-1**, preserve newlines (matches make_gen_avc.py; protects
  opaque embedded data).
- **Validation:** assert no *newly introduced* duplicate uniqueIds (the base comp legitimately repeats
  column ids across decks — a global dup assertion false-fails); assert 32 clips on the correct
  (layer,column) per the frozen map; assert Text Block text non-empty. Visual legibility = manual check.

## Unchanged from r2
Decode rule `(key&0xFF)==0x90; note=(key>>8)&0x7F; 0–39`; per-kind FX model; UI-specimen→diff→clone;
32 clips + FX handled per-kind; map-freeze + one hardware press.

---
### Judgment log (r3)
- **Accepted (all grounded):** enumerate-and-left-join for empty pads; port-conflict reordering;
  three-way colour representation + polarity + previewing state; new parameterized latin-1 builder;
  new-dup-only validation; port-select CLI. **CUT:** CSV (JSON + table only); automated legibility.
- Process note: r3 anchor folded into direct grounding (every Codex claim cited a real line and
  verified — port-busy, latin-1, cross-deck dup ids, notes 0/6 empty, bypassed polarity).
