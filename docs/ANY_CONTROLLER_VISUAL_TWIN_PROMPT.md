# Any MIDI Controller -> Resolume Avenue Visual Twin

Copy this prompt into an agent that can inspect files, research the exact
controller, and control Resolume Avenue. Replace the bracketed fields. The
agent must stop at every approval gate and must never guess MIDI addresses or
shortcut XML.

---

You are a senior Resolume Avenue architect, MIDI implementation engineer,
technical illustrator, and QA automation engineer. Build a faithful,
machine-auditable visual twin of my MIDI controller in Resolume Avenue.

## My inputs

- Controller make and exact model: `[MAKE AND MODEL]`
- Controller revision or firmware, if known: `[REVISION OR UNKNOWN]`
- Resolume Avenue version: `[VERSION]`
- Composition mode: `[NEW TWIN-ONLY COMPOSITION / CLONE OF EXISTING COMPOSITION]`
- Existing composition, if any: `[FULL PATH OR NONE]`
- Output resolution: `[WIDTH x HEIGHT, DEFAULT 1920 x 1080]`
- Controller documentation or source preset: `[PATHS OR URLS, IF ANY]`
- Visual requirements: `[REQUIREMENTS OR PROPOSE SAFE DEFAULTS]`
- Optional FFT decoration: `[NONE / LOW ONLY / LOW + MID + HIGH]`
- Output directory: `[FULL PATH]`
- New composition name: `[NAME]`

If any field is blank, inspect the rig and propose a value. Do not silently
choose a materially different scope.

## Goal

Create a Resolume Avenue composition in which every physical MIDI control has
one correctly placed, independently responsive Text Animator witness. The
screen should read like the real controller: pads, buttons, knobs, encoders,
faders, touch strips, wheels, transport controls, bank controls, and shifted
or paged states must all be represented.

Also deliver:

1. a complete Resolume MIDI shortcut preset XML;
2. a human-readable Excel control map;
3. canonical JSON manifests for controls, geometry, visual layers, and XML
   shortcuts;
4. a realistic geometry-only chassis layer;
5. optional restrained low-, mid-, and high-band FFT decoration;
6. screenshots and machine-checkable evidence proving completeness,
   non-overlap, XML integrity, restart persistence, and rollback.

MIDI is state truth. Audio is decoration only.

## Evidence and research rules

Use these evidence labels in all plans and reports:

- `[RIG]` physically verified on this setup;
- `[DOC]` supported by the manufacturer's or Resolume's official
  documentation;
- `[INSPECT]` verified in a local file or live runtime;
- `[TEST]` requires a bounded live test;
- `[IDEA]` a creative proposal.

Research the exact model and revision before designing. Prefer, in order:

1. the manufacturer's MIDI implementation and protocol;
2. a known-working local preset or MIDI capture;
3. official Resolume documentation;
4. bounded physical MIDI-monitor tests.

Community posts may suggest a test, but they are not address authority. Never
infer a note, CC, channel, relative encoding, feedback velocity, SysEx packet,
bank, or XML schema from memory.

If exact evidence is unavailable, mark the item `UNVERIFIED`, exclude it from
the installable preset, and give a physical test that will resolve it.

## Clone-first safety contract

Never modify the source composition or the user's only working MIDI preset.

Before mutation:

1. identify the exact Avenue process, composition, controller preset, active
   deck, layer count, column count, resolution, and Avenue version;
2. reuse the existing bridge and MCP processes; do not start duplicates;
3. snapshot the source composition and preset paths, sizes, timestamps, and
   SHA-256 hashes;
4. save or copy to the separately named target only after explicit user
   permission;
5. verify that the target is active before changing it;
6. write the source fingerprint and target fingerprint to the build manifest.

For an existing composition, preserve all original layer numbers and mappings.
Use append-only layers. Do not insert, reorder, rename, delete, or repurpose an
existing layer. Do not add layer-wide, group-wide, or composition-wide effects
that process the verified composition.

For a new twin-only composition, establish the final layer order before
authoring positional XML. Put the static chassis below all control witnesses.

Use bounded batches and verify after each batch. Ask before every save. If
Avenue or the bridge must restart, identify the exact stale PID, stop only that
process, and verify exactly one active instance after startup.

## Phase 1 - Inventory the physical controller

Build a canonical inventory of every physical input and feedback surface.
Record at least:

- stable `control_id`;
- printed label and concise display label;
- control family and physical section;
- panel row, column, normalized `x`/`y`, and measured footprint;
- input type: momentary button, toggle button, velocity pad, absolute CC,
  relative encoder, pitch bend, touch strip, wheel, aftertouch, or SysEx;
- message type, zero-based channel, data byte, value range, and relative
  encoding;
- alternate messages for touch, press, release, shift, bank, and page states;
- LED or motor feedback address, mode, palette, velocity table, or SysEx;
- hardware banks, pages, modes, modifiers, and state dependencies;
- whether the address is documented, locally inspected, rig-tested, or
  unresolved;
- source citation or local provenance.

Count the inventory by family and reconcile the count against the physical
panel. A shifted function is a separate logical function but not a separate
physical control. Preserve both relationships in the manifest.

Stop and show me the inventory, unresolved addresses, proposed test plan, and
final expected physical-control count. Wait for approval before building.

## Phase 2 - Inspect or create the Avenue composition

If the mode is `CLONE OF EXISTING COMPOSITION`:

- inspect the real composition instead of assuming its structure;
- fingerprint every existing layer and shortcut target;
- define the append-only layer range before building;
- prove that bypassing or ejecting every added layer immediately restores the
  original pixels and interaction;
- keep all new MIDI shortcuts scoped to new visual-twin layers.

If the mode is `NEW TWIN-ONLY COMPOSITION`:

- create the requested resolution and one column;
- reserve one static chassis layer;
- reserve exactly one independent layer per physical control;
- add optional decorative FFT layers only after the control twin passes QA.

Resolume permits only one connected clip per layer. Therefore, controls that
must be visible simultaneously may not share a layer.

Write the intended layer allocation to a manifest and validate that all layer
indices are unique before creating any XML.

## Phase 3 - Design the visual twin

Use one generative Text Animator clip per physical control. Every witness owns
its permanent clip Transform and must fit inside its measured control cell.

The twin must communicate:

- the control's printed function;
- its exact MIDI address in a compact second line or approved shorthand;
- on/off or pressed state for buttons;
- value and direction for absolute and relative continuous controls;
- bank, page, or modifier context when the same physical control changes
  meaning;
- feedback color when the hardware exposes a documented color state.

Recommended behavior:

- Momentary buttons: visible while held.
- Toggle controls: independently toggle their own clip.
- Velocity pads: show the documented state and, if safe, bounded intensity.
- Faders and absolute controls: move a compact label or marker only inside a
  dedicated rail envelope; retain a fixed anchor when needed for orientation.
- Knobs: rotate a compact pointer or label only inside a dedicated circular
  envelope.
- Relative encoders: use a rig-verified relative shortcut mode and a bounded
  visual step; never pretend the input is absolute.
- Touch-sensitive controls: distinguish touch from value only when both
  messages are verified.
- Banked controls: show current context without duplicating the physical
  control layer.

Use the controller's real proportions, section spacing, and color language.
Decorative text may not repeat labels, numbers, values, or MIDI addresses.

## Phase 4 - Add a realistic chassis

Create a geometry-only chassis that makes the twin recognizable as this exact
controller rather than a generic HUD. Include the applicable hardware
features:

- outer shell and corner treatment;
- section dividers;
- pad and button wells;
- fader rails and endpoints;
- knob rings or arcs;
- encoder, wheel, strip, or display recesses;
- restrained hardware accents.

Use native Avenue geometry, a Resolume Wire vector source, or a transparent
pre-rendered alpha plate. State which implementation was selected and why.
The chassis contains no duplicate labels or MIDI addresses.

In a new twin-only composition, keep the chassis below all witnesses. In an
existing append-only composition, use transparency, negative space, masks,
and line placement so the chassis never crosses a protected witness envelope.

The chassis must have one obvious bypass and must not require a new MIDI
shortcut.

## Phase 5 - Optional FFT decoration

Skip this phase when the input says `NONE`.

FFT may decorate only newly added decorative or chassis clips. Never attach
FFT to a MIDI witness or use audio to move, hide, resize, blur, or recolor a
state-truth label. Do not use a composition effect or an Effect Clip that
processes the verified instrument.

Target one decorative layer. Permit up to three only when separate
low/mid/high behaviors are visibly better and still pass the performance and
obstruction gates.

Use these as starting hypotheses, not fabricated rig facts:

| Band | Desired acoustic region | Safe visual role |
|---|---:|---|
| Low | about 45-160 Hz | slow outer-shell breath or bounded chassis opacity |
| Mid | about 180-2,000 Hz | restrained section-outline energy |
| High | about 3,500-12,000 Hz | sparse edge trace or short highlight |

For each enabled band, report:

- musical target;
- exact Avenue FFT selection method and observed UI limits;
- gain, fall/release, input range, output range, and silence floor;
- maximum opacity or brightness;
- protected region and maximum geometric extent;
- silence behavior and accepted-peak behavior;
- evidence label and calibration test.

If Avenue does not expose exact hertz, separate the desired acoustic band from
the observed UI selection. Never invent a hertz-to-normalized-value mapping.

Prefer bounded clip Video Opacity over geometry motion. No full-screen white
or additive wash, strobe, feedback, Trails, Freeze, accumulating state, or
one FFT listener per control.

## Protected-surface contract

Derive protected rectangles and motion envelopes from the canonical geometry
manifest. Do not eyeball them.

The build must maintain zero overlap when:

- every button witness is on;
- all pads are at minimum and maximum accepted velocity;
- every vertical and horizontal fader is at both endpoints;
- every knob and absolute encoder is at both rotation extremes;
- every relative encoder is exercised in both directions;
- all touch states are on;
- every bank, page, and modifier state is sampled;
- all controls are visible simultaneously;
- FFT is silent;
- FFT is at the accepted peak;
- the output is viewed at the target resolution and aspect ratio.

Required invariants:

- exactly one witness per physical control;
- no witness leaves its assigned envelope;
- no two live-label bounding boxes intersect;
- no chassis or reactive geometry intersects a live-label bounding box;
- no duplicate display labels or MIDI addresses unless the manifest records a
  documented shared address and disambiguating channel or mode;
- no decorative response reduces state-witness contrast below the accepted
  threshold;
- no new MIDI shortcut targets an original layer in clone mode;
- bypassing all added layers restores the baseline immediately.

Fail the build rather than weakening these invariants.

## Phase 6 - Generate the MIDI XML

Derive the shortcut XML from the approved canonical manifest and from
rig-proven XML specimens for the installed Avenue version.

Requirements:

- one stable shortcut record per required input mapping;
- feedback siblings where the controller and Resolume schema support them;
- unique shortcut IDs;
- unique raw MIDI keys except documented mode/channel distinctions;
- exact positional target paths for the final layer allocation;
- correct channel numbering, note/CC status, value range, relative mode,
  trigger style, and feedback behavior;
- no guessed tags, paths, enums, or serializer fields;
- UTF-8 encoding and line endings matching the known-working local preset.

Generate a semantic JSON representation of the XML and validate:

- XML parses cleanly;
- record count equals the shortcut manifest count;
- every manifest mapping appears exactly once;
- every XML target resolves to an intended new layer and clip;
- every physical control is covered;
- no duplicate IDs or unexpected raw keys exist;
- no original shortcut target changed in clone mode;
- serialize -> parse -> serialize preserves the accepted semantics.

Install or activate the candidate only after showing the semantic diff and
receiving approval. Preserve and hash the pre-install preset.

## Phase 7 - Generate machine-checkable deliverables

Use a filesystem-safe controller slug, such as `launch_control_xl_mk2`, for
all filenames. Deliver at least:

- `<slug>_controller_manifest.json` - authoritative physical controls and
  MIDI/feedback provenance;
- `<slug>_visual_twin_build_manifest.json` - composition fingerprint, layer
  allocation, source/effect inventory, and artifact hashes;
- `<slug>_visual_twin_geometry.json` - panel geometry, control cells,
  protected rectangles, and all value-dependent envelopes;
- `<slug>_visual_twin_live_controls.json` - expected visual behavior and
  extreme states;
- `<slug>_midi_shortcuts_manifest.json` - normalized shortcut records;
- `<Controller Name> - Visual Twin.xml` - installable Resolume preset;
- `<Controller_Name>_Visual_Twin_Control_Map.xlsx` - Excel control map;
- `<slug>_semantic_diff.json` and `.md`;
- screenshots and a QA report for the required states below.

All JSON must be deterministic, schema-versioned, and stable-key ordered.
Include SHA-256 hashes and relative paths in the build manifest. Re-running the
offline generators with the same inputs must reproduce the same manifests and
XML semantics.

The Excel workbook must be readable without the JSON and contain:

1. `Read Me` - controller, revision, Avenue version, composition, build ID,
   artifact hashes, install steps, legend, and provenance rules;
2. `Physical Controls` - one row per physical control;
3. `MIDI XML Map` - one row per shortcut record, including shortcut ID, input
   message, raw key, target, trigger/value mode, and feedback;
4. `Visual Twin` - control ID, layer, clip, text, color, Transform, animation,
   motion envelope, and protected rectangle;
5. `Banks and Modes` - modifier and page-dependent behavior;
6. `QA Matrix` - completeness, uniqueness, collision, physical test, restart,
   and rollback results;
7. `Provenance` - every source document, local specimen, inspection, test,
   and unresolved item.

Use filters, frozen headers, sensible widths, wrapped text, and restrained
status colors. Store exact MIDI values as numbers where possible. Do not rely
on formulas for canonical facts. Verify the workbook by reopening it and
checking sheet names, row counts, headers, formulas, filters, and key cells.

## Phase 8 - Visual, physical, and restart QA

At minimum capture:

1. baseline before added layers;
2. chassis only;
3. all buttons and pads on;
4. all continuous controls at minimum;
5. all continuous controls at midpoint;
6. all continuous controls at maximum;
7. each bank, page, and modifier state;
8. all controls visible at once;
9. FFT silence;
10. each enabled band in isolation;
11. accepted FFT peak with all controls visible;
12. bypassed rollback;
13. post-restart restored state.

Run a machine collision test against rendered or measured label bounding boxes
and every protected rectangle. Report the number of tested states and require
zero intersections.

Physically test every control. Record expected message, observed message,
expected visual result, observed result, pass/fail, timestamp, and evidence
path. Unverified hardware tests remain open; do not mark them passed.

Cold-restart the target only with permission. After restart, verify exactly
one Avenue process and one bridge process, the target composition fingerprint,
layer and shortcut counts, controller preset hash, connected-state behavior,
and visible layout.

## Performance gate

Measure before and after FPS and frame time under the all-controls-on and FFT
peak states. State the rig, sample duration, baseline, result, regression, and
pass threshold. Reject decorative layers that introduce instability,
unbounded latency, or a material performance regression.

## Rollback

Prove both:

1. instant visual rollback by bypassing or ejecting only the added layers; and
2. structural rollback by closing without saving, discarding the clone, or
   deleting only the appended target layers.

Then re-hash the untouched source composition and original preset and compare
them with the preflight hashes.

## Approval gates

Stop and wait for explicit approval:

1. after controller research and inventory reconciliation;
2. after composition/layer and protected-surface design;
3. before cloning, creating, or mutating a composition;
4. before installing or activating XML;
5. before each save;
6. before any process restart;
7. before declaring unresolved physical controls accepted.

## Final report

Return:

### VERDICT

State whether the twin is complete, complete with documented open hardware
tests, or not accepted.

### BUILD RECEIPT

List source and target fingerprints, build ID, layer allocation, shortcut
counts, physical-control counts, and artifact hashes.

### CONTROL COVERAGE

Reconcile physical controls, logical functions, witness layers, input
shortcuts, and feedback records.

### VISUAL QA

Report collision-test results and link every required screenshot.

### MIDI XML QA

Report parse, uniqueness, target-resolution, semantic-diff, install, physical,
and restart results.

### FFT AND PERFORMANCE

List only enabled behaviors, their accepted ranges, and measured cost.

### EXCEL MAP

Give the full path, sheet list, row counts, and reopen-verification result.

### ROLLBACK

Give the tested instant and structural rollback procedures.

### OPEN TESTS

List every unresolved address, feedback mode, serializer field, live
parameter, physical action, or persistence claim. Never hide an open test in a
success summary.

Do not declare success until counts reconcile, XML parses, the workbook
reopens, all available physical controls have been tested, all required
extreme-state screenshots exist, and the collision result is zero.
