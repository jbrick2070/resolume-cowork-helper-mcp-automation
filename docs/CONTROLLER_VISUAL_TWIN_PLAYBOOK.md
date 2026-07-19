# Build Your Own Controller Visual Twin

The fastest way to build a large Resolume controller layout is not to map
every control by hand. Inventory every physical control once, prove one
shortcut specimen for each behavior, generate the repetition from manifests,
and physically test the result against the hardware.

This playbook is the human-facing guide. When you are ready to hand the build
to an agent, use the
[any-controller execution prompt](ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md).

## Choose the thing you are building

This repository contains two related products. Do not mix their rules without
declaring which product you want.

| Product | Purpose | Typical shortcut rule |
|---|---|---|
| Performance mapping | Launch clips and control the parameters used in a show | Usually one raw MIDI input per performance action |
| Visual QA twin | Mirror every physical control on screen so its state and movement can be tested | One physical input may deliberately fan out to wake, opacity, and motion |
| Both | A performance preset plus a separate diagnostic composition/preset | Keep the two artifacts separately named and validated |

The shipped 91-shortcut APC40 performance preset and the 148-control,
203-shortcut Visual QA twin are both correct. They solve different problems.

## The mental model that prevents most failures

Resolume connects only one clip per layer. If two indicators must be visible
at the same time, they need independent layers.

One physical control also does not necessarily equal one shortcut. A button
can need one connect record. An absolute fader or knob may need three records:

1. wake or connect the witness clip;
2. map value to witness opacity;
3. map value to the permanent Transform motion.

A relative encoder may need a wake record plus a relative motion record
instead of an absolute range. The accepted APC40 twin therefore has:

```text
120 button records + (27 absolute controls × 3) + (1 relative encoder × 2)
= 203 shortcut records for 148 physical controls
```

Every shortcut ID must still be unique. Repeated raw MIDI keys are allowed
only inside a declared multi-target group for one physical control, or for a
documented mode/bank distinction.

## Evidence labels

Use these labels in manifests, plans, and reports:

- `[RIG]` physically verified on the actual controller and computer;
- `[DOC]` supported by official manufacturer or Resolume documentation;
- `[INSPECT]` observed in a local file or runtime;
- `[TEST]` a bounded experiment that has not passed yet;
- `[IDEA]` a proposal, not a fact.

If an address or serializer field is unknown, mark it `UNVERIFIED`. Do not
turn memory, a product photo, or another model's confident prose into MIDI
authority.

## The shortest safe build order

1. **Freeze the baseline.** Record the composition, preset, counts, paths,
   hashes, process topology, resolution, active deck, and dirty/saved state.
2. **Inventory the hardware.** Record every control's full MIDI address,
   geometry, type, range, relative encoding, feedback capability, and evidence.
3. **Choose the final layer allocation.** In a new twin, put a static chassis
   below one witness layer per physical control. In an existing composition,
   append only; do not insert beneath protected layers.
4. **Create source-of-truth manifests.** Generate the workbook, XML, and QA
   expectations from them. The spreadsheet is a readable projection, not a
   second authority.
5. **Author one specimen per behavior in the target Avenue version.** Save it,
   diff it, and preserve its serializer shape.
6. **Run a small pilot.** Prove one button, one absolute fader, one absolute
   knob, one relative encoder, and every distinct LED species.
7. **Calibrate on the live monitor.** Measure Text Animator ink and movement;
   desktop font metrics and guessed Transform units are not enough.
8. **Generate the full candidate offline.** Change only the fields proven safe
   to vary, then validate semantic counts, IDs, paths, roles, and ranges.
9. **Install and physically sweep.** Test min/mid/max, both rotary directions,
   all-on state, overlap, feedback, and first-event wake behavior.
10. **Cold restart with permission.** Recheck the exact artifact and process
    topology. Seal hashes, screenshots, measurements, and rollback details.

Do not build 148 controls before the pilot proves the schema.

## Canonical control inventory

Use a JSON or CSV manifest with at least these fields:

| Field | Meaning |
|---|---|
| `control_id` | Stable identifier independent of layer number |
| `label` | Printed or approved concise display label |
| `family` / `section` | Grid, transport, track strip, device, navigation, and so on |
| `x`, `y`, `width`, `height` | Normalized physical geometry and witness footprint |
| `message_type` | Note, CC, pitch bend, aftertouch, or SysEx |
| `channel` | Part of the MIDI address, not optional metadata |
| `data1` | Note or CC number |
| `value_range` | Observed/documented input range |
| `encoding` | Absolute or the exact relative encoding |
| `mode` / `bank` | Context that changes the emitted address or meaning |
| `feedback` | Separate output address, palette, velocity, or SysEx contract |
| `led_capability` | RGB, fixed color, binary, intensity-only, or none |
| `evidence` / `source` | `[RIG]`, `[DOC]`, `[INSPECT]`, or unresolved |

Count the controls by family and reconcile the total with the physical panel.
A shifted function is a separate logical function, but it is still attached
to the same physical control.

### MIDI identity is more than a number

The full identity is at least:

```text
(message type, MIDI channel, data byte, mode/bank)
```

On the APC40, several per-track buttons share the same note number and use the
channel to identify the track. Dropping the channel collapses eight physical
controls into one apparent address.

## Geometry and layer allocation

Establish the final layer order before generating positional XML. Layer
indices are target addresses, so inserting or reordering later can invalidate
an otherwise correct preset.

For each control, store:

- its resting label bounds;
- its complete motion envelope;
- its rail, ring, or cell bounds;
- its maximum antialiased ink bounds;
- a protected padding derived from live measurement.

For rotating labels, endpoints are not always the largest footprint. Render
every realizable state or compute a conservative transformed-raster hull.

In clone mode:

- preserve all original layer numbers and shortcut targets;
- append visual-twin layers only;
- keep all decoration outside protected witness envelopes;
- require one obvious bypass that immediately restores the baseline.

## Prove shortcut species before cloning them

The serializer of record is a preset saved by the installed Avenue version.
Do not invent XML tags or “clean up” a working block.

Create one real UI-authored specimen for each species you need:

- button connect/toggle;
- fixed-color or RGB feedback;
- absolute fader wake, opacity, and Position Y;
- absolute knob wake, opacity, and Rotation Z;
- horizontal fader wake, opacity, and Position X;
- relative encoder wake and relative rotation;
- any special bank, shift, touch, or press behavior.

Diff the specimen against the baseline. Clone only the fields that the diff
proves may vary: target path, MIDI identity, unique ID, and verified range.
Preserve behavior flags, translation attributes, sibling state paths,
`NamedValues`, and `Subtarget` structure exactly.

### Visual-twin uniqueness contract

For a diagnostic twin:

- every shortcut ID is unique;
- every `(raw_key, role, input_path)` tuple is unique;
- a raw key may repeat only within its declared multi-target group or a
  documented mode/bank distinction;
- each group has its expected role count;
- every target resolves to the intended witness layer;
- protected baseline records remain byte-identical when that is the contract.

For performance presets, follow the stricter rules in
[Control Logic](CONTROL_LOGIC.md). Do not infer that the visual-twin fan-out
is appropriate for a performance action.

## Continuous controls: the failure that cost the most time

The first fader and first knob worked while the remaining controls appeared
dead. The working controls had wake, opacity, and motion mappings. The others
still pointed at an inert Text Animator Delay target.

The reusable rule is:

- **Absolute fader/knob:** wake + opacity + permanent Transform motion.
- **Relative encoder:** wake + relative motion; never pretend it is absolute.
- **First event:** must both wake the clip and apply the current value.
- **Connected state:** must not be trusted as the only persistence mechanism.

Restarting cannot create missing mappings. Inspect the active preset and its
semantic role histogram before restarting anything.

Calibrate Transform values on the rig. Resolume's serialized ranges may be
normalized, screen Y may run opposite the expected direction, and a value
that looks tiny in XML can represent a useful physical sweep.

## Buttons and hardware feedback

Treat input state and LED feedback as separate contracts.

- RGB pads need the documented velocity, channel, or SysEx palette.
- Fixed-color LEDs are not RGB just because the camera makes them look red.
- Non-addressable controls should not be promised a light.
- Test every LED species in the pilot: RGB, fixed amber, fixed blue, fixed
  red, intensity-only, and no-light as applicable.
- A visually correct on-screen label does not prove that hardware feedback is
  correct.

If one hardware button emits no MIDI event while its neighbors do, isolate it
in one MIDI monitor with Avenue closed. No event means the endpoint stays
provisional while hardware, USB, mode, or firmware is investigated.

## Live calibration and collision QA

Measure what Avenue actually renders. The APC40 build demonstrated that
offline font estimates could exceed a lane even when the source settings
looked reasonable.

Required visual tests:

- every button off and each button individually on;
- all buttons on simultaneously;
- every absolute control at minimum, midpoint, and maximum;
- every relative encoder in both directions and intermediate angles;
- combined worst-case motion hulls;
- screenshot at full output resolution;
- post-restart repeat of the accepted state.

Test actual label ink, not just control centers. A layout passes only when:

- no two live-label bounds intersect;
- no chassis, halo, or FFT decoration intersects a protected envelope;
- text remains legible at the accepted scale;
- bypassing additions restores the baseline.

## Avenue and MCP operating discipline

Follow the current [stability protocol](stability-protocol.md). Its stricter
limits override older handoffs.

Current operating limits:

- structural operations: one at a time, then read state back;
- ordinary independent writes: at most 8 operations per batch;
- file loads: one clip per call at a batch-of-4 cadence;
- after load bursts: allow the documented settle interval;
- verify writes by readback or capture because reads can be cached;
- ask before every save;
- ask before every restart or audio-routing change.

Reuse the existing bridge and MCP/gateway process set. Do not launch a fresh
STDIO server for every client session. Inventory PIDs, parents, executable
paths, and endpoints. If cleanup is approved, act on the exact stale PID;
never kill every process merely because its name matches.

Avenue caches loaded composition state. Do not hand-edit a loaded `.avc` to
change clip color, position, or trigger style. Apply those changes live,
verify them, then save only with permission.

## Common failures and their fixes

| What you see | Likely cause | What to do |
|---|---|---|
| Several track controls act like one | MIDI channel was dropped | Restore the full address tuple |
| One label ejects another | Two controls share a layer | Give each simultaneous witness its own layer |
| First fader works; the rest do nothing | Only the pilot has wake/opacity/motion | Compare semantic role groups, then regenerate from the proven specimen |
| A control works only after manually triggering its clip | Saved connected state was treated as logic | Add a wake mapping and retest the first event |
| Tempo or an endless encoder behaves wildly | Relative input was mapped as absolute | Identify and test the actual relative encoding |
| Fader travels backward or barely moves | Guessed Transform units/direction | Calibrate min/mid/max against live pixels |
| Labels collide only during a sweep | QA checked centers/rest states only | Test full ink and motion hulls simultaneously |
| LED hue disagrees with the hardware | Fixed LED was treated as RGB or inferred from a camera | Use protocol evidence plus physical test |
| XML loads but behavior changes | Serializer structure was invented or normalized | Clone a target-version UI specimen byte-for-byte |
| Candidate hash changes after Avenue saves it | Avenue normalized formatting or numbers | Compare both bytes and semantic records |
| Restart changes nothing | Mapping is absent or targets the wrong path | Inspect the active XML; restart is not a repair tool |
| A live edit appears ignored | Avenue cached the loaded `.avc` | Set it live and confirm by readback/capture |
| Random stale state or crashes | Duplicate automation processes or oversized batches | Reconcile topology and follow the stability protocol |

## Receipts and rollback

Every significant phase should leave a compact receipt:

- source and target paths, sizes, timestamps, and SHA-256 hashes;
- composition and preset names;
- controller, firmware, Avenue version, and MIDI mode;
- process topology;
- layer and shortcut counts;
- manifest and semantic-diff hashes;
- pilot results;
- physical sweep and collision screenshots;
- restart persistence result;
- rollback target and exact restoration steps;
- unresolved items and evidence labels.

Compare Avenue-normalized XML semantically as well as byte-for-byte. Preserve
protected records exactly when required, but allow harmless representation
differences only when counts, IDs, paths, behaviors, ranges, and role groups
remain equivalent.

## Definition of done

A controller visual twin is complete only when:

- every physical control is inventoried and reconciled;
- every simultaneously visible control owns an independent witness layer;
- every shortcut target and feedback path is accounted for;
- the pilot proves every behavior and LED species;
- continuous controls wake and move on their first event;
- all extreme-state and all-on collision tests pass;
- physical hardware feedback matches documented capability;
- the accepted preset survives a cold restart;
- the source composition and preset remain recoverable;
- the workbook, manifests, XML, screenshots, and receipts agree.

Do not claim a physical test that was not performed. Structural XML checks,
screen captures, and hardware sweeps prove different things.

## APC40 mkII worked example

The APC40 project is the case study behind these rules:

- [ready-to-open Visual QA composition](../compositions/APC40_Visual_QA_148.avc)
  — accepted 148-control result;
- [visual twin image](APC40_Visual_Twin.png) — complete active panel;
- [native address map](APC40_native_addresses.md) — channel-sensitive MIDI
  authority;
- [Visual QA control-map workbook](APC40_Visual_QA_Control_Map.xlsx) —
  readable control and shortcut projection;
- [accepted preset](../controllers/APC%2040%20MK%20II%20-%20Visual%20QA.xml) —
  203-shortcut implementation;
- [generic execution prompt](ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md) — adapt
  the method to another controller.

## Pick your next step

- **I only need a performance mapping:** use
  [`prompts/09-any-controller.md`](../prompts/09-any-controller.md).
- **I want the full on-screen visual twin:** use
  [`docs/ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md`](ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md).

For a public release, remove personal paths, PIDs, raw logs, private
screenshots, and backup artifacts. Ship the smallest complete set: guide,
manifest, readable map, validated preset, proof images, and rollback notes.
