# External Review Prompt — APC40 Text Animator, FFT, and Chassis R1

You are a senior Resolume Avenue 7.27.1 architect, live-visual designer, and
performance engineer. Review an existing, working APC40 mkII visual instrument
and propose a technically grounded R1 enhancement. Be creatively ambitious,
but do not implement or modify anything.

The goal is not to replace the instrument. The goal is to add a realistic,
audio-reactive APC40 chassis and restrained energy around a fully working
control surface.

## Read these files first

Primary grounding:

- `docs/APC40_Visual_QA_HANDOFF.md`
- `docs/APC40_Standard_Layout.md`
- `docs/APC40_Resolume_Synthesis_for_Cowork.md`
- `docs/APC40_Visual_QA_Control_Map.xlsx`
- `docs/APC40_visual_qa_manifest.json`
- `docs/APC40_visual_qa_live_controls.json`
- `docs/APC40_visual_qa_geometry.json`
- `docs/APC40_visual_qa_calibration.json`
- `docs/APC40_visual_qa_build_manifest.json`
- `scripts/generate_apc40_visual_qa.py`
- `scripts/render_apc40_live_overlay.py`
- `docs/2026-07-18-apc40-animated-visual-qa/artifacts/physical_qa_full_panel_all_controls.png`
- `docs/2026-07-18-apc40-animated-visual-qa/artifacts/physical_qa_continuous_sweep_fullscreen.png`
- `docs/2026-07-18-apc40-animated-visual-qa/artifacts/continuous_white_tempo_red_live_fix.png`
- `docs/2026-07-18-apc40-animated-visual-qa/artifacts/record_arm_red_live_fix.png`

Official Resolume references:

- `https://resolume.com/support/en/parameter-animation`
- `https://resolume.com/support/dashboard`
- `https://resolume.com/support/en/6/sources`
- `https://resolume.com/support/en/7/preferences`
- `https://resolume.com/support/effects`
- `https://resolume.com/support/en/layers`

## Existing composition — treat this as a real instrument

This is Resolume **Avenue 7.27.1**, not Arena.

The saved composition is `APC40_Visual_QA_148`:

- 1920 × 1080;
- one column;
- 148 independent layers;
- one Text Animator clip per physical APC40 mkII control;
- 120 button witnesses;
- 28 continuous-control witnesses;
- 203 accepted MIDI shortcut records;
- all 28 physical faders and knobs successfully swept on the controller;
- moving fader labels and rotating knob labels already work;
- the all-controls-on view has been visually checked for collisions.

The accepted MIDI build is `B1-728792218d26e596`. The installed shortcut
preset SHA-256 is:

`4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5`

The latest saved color language is:

- RGB grid witnesses retain their column colors;
- fixed amber controls remain amber;
- Solo `S` witnesses are blue;
- Record Arm `●` witnesses are dedicated red;
- every normal fader and knob witness is white;
- Tempo is red because it is a relative continuous stepper.

Each existing Text Animator clip owns its permanent Transform. The current
motion, scale, rotation, opacity, text, MIDI address, and color all communicate
real controller state. They are functional surfaces, not decorative content.

## Non-negotiable baseline lock

Design for a separately named clone. Do not change the saved V1.

The review must prescribe this gated clone workflow, even though the review
itself is read-only:

1. Before cloning, record the source composition's full path, size, timestamp,
   SHA-256, resolution, deck/column/layer counts, layer fingerprint, active
   MIDI preset name and SHA-256, and a baseline screenshot hash.
2. Record the exact Avenue and bridge process IDs. Reuse the existing bridge
   and MCP server; never launch a duplicate. If a later build requires a
   restart, identify and stop only the exact stale PID, then prove that one
   Avenue process and one bridge process remain.
3. Create a separately named clone only after explicit user approval. Record a
   pre-mutation clone fingerprint and prove that the clone, not V1, is active.
4. Require separate approval before the first mutation, every save, any
   process restart, and any install or activation step.
5. Allocate only append-only layers 149–151. Fingerprint layers 1–148 before
   and after the build and require a byte- or semantic-equivalent layer
   manifest.
6. After a permitted cold restart, recheck process counts, composition
   fingerprint, original layer fingerprints, new-layer count and order,
   bypass state, and active preset hash.

Do not propose:

- changing or regenerating the accepted MIDI XML;
- changing, renaming, deleting, inserting between, or repurposing layers 1–148;
- moving an enhancement layer below layer 1, because that would shift every
  positionally addressed MIDI layer;
- changing any existing control's Text, Color, Transform, Opacity, animation
  source, trigger style, or connect mapping;
- attaching FFT to any existing witness;
- making an existing MIDI witness pulse, move, resize, blur, or disappear from
  audio;
- composition-wide effects that process the entire verified instrument;
- an Effect Clip that processes all layers beneath it;
- one effect or FFT listener per control;
- duplicate labels, MIDI addresses, numbers, button names, or value text in a
  new chassis layer;
- custom plugins, ISF, external MIDI watchers, or guessed XML in R1.

MIDI remains state truth. Audio is decoration only.

The target must be a fully disposable enhancement. With all new layers at zero
opacity, bypassed, or ejected, the protected V1 pixels and interaction must be
identical to the recorded baseline. A review recommendation that cannot prove
that property is not acceptable.

## The design question

What is the strongest additive R1 that makes this look more like a real APC40
mkII while keeping every existing surface readable, unobstructed, responsive,
and correctly mapped?

Explore all of these:

1. a geometry-only APC40 chassis or technical outline;
2. restrained low-, mid-, and high-band FFT behaviors;
3. safe Text Animator parameters that could be used on a **new** decorative
   clip;
4. native Resolume sources and clip-scoped effects;
5. a Resolume Wire polygon/vector source;
6. a transparent pre-rendered outline asset;
7. rounded rectangles for pads and buttons, circles/arcs for knobs, thin rails
   for faders, section dividers, corner details, and the outer chassis;
8. subtle reactive halos, traces, scanning highlights, or energy wakes that
   reinforce the hardware layout without becoming a generic music visualizer.

Anything is fair game inside the clone if it passes the safety, performance,
and rollback gates below.

## Required Text Animator and effect audit

Inspect the actual 7.27.1 source/effect parameter surface. Produce a matrix for
every plausible FFT target on a new decorative clip, including at least:

- Clip Video Opacity;
- Text Animator Opacity;
- Outline Width;
- Outline Color;
- Glow In;
- Glow Out;
- Animated Outline Width;
- Animated Glow In;
- Animated Glow Out;
- Size;
- Spacing X/Y;
- source Position X/Y;
- source Rotation;
- Transform Scale, Position, and Rotation;
- any relevant parameter on native Rings, Lines, Line Scape, Slice Outline, or
  other installed sources/effects;
- one optional clip-scoped Bloom or equivalent, if it is justified.

For every parameter, report:

- exact live UI name;
- exact Avenue parameter path or the bounded live inspection needed to obtain
  it;
- exact scope and target;
- whether the parameter accepts an FFT phase source in Avenue 7.27.1;
- whether that fact is documented, locally inspected, or still needs a live
  test;
- recommended minimum and maximum;
- hard clamp and value units as exposed by Avenue;
- visual role;
- silence behavior;
- accepted-peak behavior;
- risk of obstruction, clipping, brightness wash, or state ambiguity;
- keep / test / reject.

Do not merely say “any parameter can use FFT.” Decide which parameters are
safe and useful here. Reject geometry animation that can cross a protected
control surface.

Prefer driving the new clip's **Video Opacity** before touching internal text
geometry. If another parameter is better, prove why.

For any kept parameter, require a monotonic, bounded response across silence,
nominal music, and the accepted peak. Reject animated position, scale,
rotation, blur, glow radius, outline width, or source geometry unless its
complete output envelope is machine-proven to remain outside every protected
rectangle. Opacity-only modulation is the default-safe design.

## Required low / mid / high FFT plan

Give both a musical target and a Resolume implementation target.

Use these as starting hypotheses, not unverified facts:

| Band | Musical target | Initial visual role |
|---|---:|---|
| Low | approximately 45–160 Hz | outer chassis breath, slow shared halo, or overall decorative opacity |
| Mid | approximately 180–2,000 Hz | section-outline energy, pad-zone body, or restrained ring expansion |
| High | approximately 3,500–12,000 Hz | thin trace, edge sparkle, or fast scanning accent |

For each band, specify:

- the intended instruments or musical events;
- the actual FFT selection method exposed by Avenue;
- observed frequency or normalized UI limits;
- gain;
- fall/release;
- input and output range;
- nonzero silence floor, if appropriate;
- hard output clamp;
- maximum permitted brightness;
- exact decorative alpha or luminance ceiling at the accepted peak;
- how to prevent low, mid, and high layers from all responding identically;
- a test-tone procedure and a real-music procedure.

If Avenue does not expose exact hertz values, say so. Report the desired
acoustic band separately from the observed UI selection. Never fabricate a
hertz-to-normalized-position conversion.

Suggested release directions to evaluate:

- low: slow and weighty, roughly 600–1,200 ms;
- mid: musical and readable, roughly 300–700 ms;
- high: quick but not strobing, roughly 100–300 ms.

These are design hypotheses. Correct them if rig evidence supports a better
choice.

The calibration procedure must capture the observed Avenue selector value,
gain, fall/release, input minimum/maximum, output minimum/maximum, silence
floor, peak clamp, and source audio level in a machine-readable record. Test
each band in isolation before combining them. A band fails if silence creates
unintended flicker, a neighboring isolated band produces a materially similar
response, the accepted peak exceeds its clamp, or any witness pixel changes
inside a protected rectangle.

## Chassis and polygon challenge

Propose at least four architectures and rank them:

1. **One-layer outline:** one transparent geometry-only APC40 chassis with
   static line work and one bounded FFT opacity response.
2. **Three-band chassis:** outer shell on low, section geometry on mid, and one
   sparse highlight trace on high.
3. **Wire vector source:** rounded rectangles, circles/arcs, rails, and section
   boundaries generated procedurally in one Wire patch.
4. **Transparent rendered asset:** a carefully aligned geometry-only alpha
   plate, optionally energized by one clip-scoped effect.

You may add a stronger fifth architecture if it is coherent and buildable.

For each architecture, state:

- exact new-layer count;
- whether it is native Avenue, Wire, or media;
- how it aligns to the existing 1920 × 1080 control geometry;
- the exact coordinate source, line-width range, maximum alpha, and maximum
  reactive extent;
- how it avoids duplicating existing text;
- how it stays visually behind the controls even though append-only layers
  render above layers 1–148;
- how it uses transparency, line placement, masks, negative space, and blend
  mode;
- expected GPU and VRAM cost;
- bypass method;
- cold-restart persistence risk;
- why it looks like an APC40 rather than a generic HUD.

Every architecture must be expressible as deterministic geometry or a hashed
alpha asset. It must define a static maximum-extent mask containing every
pixel the chassis or its FFT response can ever draw. That mask, not a single
pretty screenshot, is the collision-test input. If a source or effect cannot
provide a finite maximum-extent mask, reject it for R1.

## Protected-surface and non-overlap contract

The existing labels and their full travel envelopes are protected surfaces.

The enhancement must remain safe when:

- all 120 button witnesses are on;
- every vertical fader is at minimum;
- every vertical fader is at maximum;
- the crossfader is fully left and fully right;
- all 17 ordinary knobs are at both rotation extremes;
- all eight device knobs are at both rotation extremes;
- Cue and Tempo are at their meaningful extremes;
- all controls are visible simultaneously;
- FFT is silent;
- FFT is at its accepted peak.

Required rules:

- zero new text inside the controller surface;
- zero duplicate control labels or MIDI addresses;
- zero chassis lines crossing any live-label bounding box;
- zero reactive geometry entering a protected bounding box at any FFT value;
- zero nontransparent enhancement pixels anywhere inside the padded protected
  rectangles, so V1 pixels within those rectangles remain unchanged;
- no full-screen white or additive wash;
- no strobe;
- no opacity response that hides or materially reduces existing witness
  contrast;
- no new MIDI shortcuts on enhancement layers;
- bypassing all R1 layers must restore V1 pixels and interaction immediately.

Use the manifest, geometry JSON, calibration, and extreme-state screenshots to
derive protected rectangles. Do not eyeball this.

Build the protected-surface union from every button-on state and every sampled
continuous-control envelope, not only the resting labels. Include a documented
pixel safety margin for antialiasing, glow, outline, and calibration error.
Rasterize the chassis maximum-extent mask and every FFT band at silence,
nominal, and accepted peak. Intersect each alpha mask with the padded protected
union and require exactly zero intersecting pixels.

The proposed collision report must be machine-readable and include the input
manifest hashes, geometry hash, output resolution, safety margin, tested state
IDs, per-state intersection count, maximum alpha in protected regions, and an
overall pass/fail. The screenshot set remains supporting evidence; it cannot
override a failed mask test.

## Layer and effect budget

Target one enhancement layer. Allow up to three only if low/mid/high separation
creates a clearly better result.

Budget:

- maximum three append-only layers;
- exact allowed range is layers 149–151, with stable names and manifest IDs;
- maximum one optional clip-scoped effect per enhancement layer;
- no layer or composition effects on layers 1–148;
- no per-control effects;
- no Trails, feedback, Freeze, or other accumulating state in R1;
- no layer insertion or positional remapping;
- one obvious UI bypass for every enhancement layer.

The review must account for each candidate layer in a deterministic layer
manifest: index, stable ID, name, source, source hash or Wire patch hash,
Transform, blend mode, opacity clamp, FFT settings, effect settings, bypass,
and maximum-extent mask hash. Enhancement layers receive no MIDI shortcuts.

## Evidence language

Tag every claim:

- `[RIG]` physically verified on this setup;
- `[DOC]` supported by official documentation;
- `[INSPECT]` verified in a local file or the live 7.27.1 runtime;
- `[TEST]` requires a bounded specimen;
- `[IDEA]` creative proposal.

Community suggestions are useful ideas, not technical evidence.

## Required output

Use this exact structure:

### VERDICT

Is the concept buildable without weakening V1? Answer yes, yes-with-fixes, or
no, followed by one sentence.

### EXISTING COMPOSITION FACTS

Summarize the actual Text Animator architecture and baseline invariants. Flag
anything in this prompt that the inspected files contradict.

### CLONE AND MUTATION GATES

Give the exact source and clone fingerprint fields, approval points,
append-only layer allocation, process hygiene, save/restart checks, and
post-restart proof required of a future operator. The review itself remains
read-only.

### TEXT ANIMATOR / EFFECT FFT MATRIX

Provide the complete parameter matrix requested above.

### LOW / MID / HIGH BAND PLAN

Provide exact proposed settings, evidence labels, calibration steps, silence
behavior, and peak behavior.

### RANKED CHASSIS ARCHITECTURES

Rank at least four options with scope, source/effect choice, layer count,
performance cost, obstruction risk, bypass, and persistence.

### STRONGEST COHERENT R1

Choose exactly one architecture and no more than three FFT behaviors. Explain
why they form one visual language.

### BUILD SPEC

Give a numbered, operator-ready build sequence for a separately named clone.
Identify every new layer, source, parameter, value/range, FFT band, effect,
blend mode, hard clamp, maximum-extent mask, and bypass. Include the approval
gates, source/clone fingerprints, process checks, deterministic layer manifest,
and restart receipt. Mark every unproven operation `[TEST]`.

### PROTECTED-SURFACE TEST

Specify a machine-checkable collision test using the manifest and extreme
states. Require a padded protected union, maximum-extent alpha masks, zero
intersecting pixels, and a deterministic JSON collision report. Include the
required screenshots.

### AUDIO TEST

Specify silence, sine-tone, pink-noise, isolated-band, and real-music tests.

### PERFORMANCE GATE

Specify before/after FPS and frame-time comparison, acceptable regression,
visual latency, and failure conditions.

### MACHINE-CHECKABLE RECEIPTS

Define the schemas and deterministic inputs for an R1 build manifest, layer
manifest, protected-surface mask manifest, collision report, audio-calibration
report, performance report, screenshot manifest, and rollback receipt. Require
schema versions, stable IDs, relative artifact paths, and SHA-256 hashes.

### ROLLBACK

Explain both:

1. instant visual rollback by bypassing/ejecting the append-only layers; and
2. structural rollback by discarding the clone or deleting only its appended
   layers, then proving the original 148-layer layout, preset hash, composition
   hash, and baseline protected pixels are intact.

### CUT THESE IDEAS

Name and reject anything noisy, generic, ambiguous, disproportionate, or
likely to obstruct the instrument.

### OPEN TESTS

List every parameter, source, effect, FFT range, serializer, or performance
claim still requiring live verification.

## Prohibited actions

Do not control Resolume, start or stop processes, edit `.avc`, edit XML, modify
the repository, generate media, install software, or save a composition.

Return review text only.
