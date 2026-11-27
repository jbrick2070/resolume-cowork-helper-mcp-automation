# APC40 mkII Visual Twin V2 - Overnight Autonomous Build

You are taking over an existing, verified Resolume Avenue project. Work
autonomously for as long as useful tonight. Do not stop after planning: inspect,
implement, verify, refine, and leave a precise morning handoff. If one path is
blocked, continue with every safe offline or alternate task that does not depend
on it.

Create an active Codex goal for this job and continue until the objective is
complete or genuinely blocked.

## Mission

Create a separate **V2 beta candidate** of the verified APC40 mkII visual twin.
Keep all 148 control witnesses working exactly as they do in R1, then add a
recognizable, restrained APC40 chassis and bounded FFT-responsive visual
decoration. The controller remains the truth surface; decoration must never
cover, move, hide, recolor, or confuse a control witness.

This is Resolume **Avenue**, not Arena. R1 was verified on Avenue 7.27.1; the
rig may be running a newer build, so read the running version from the live
status and record it in the handoff rather than assuming it. Avenue exposes its
REST API through the named pipe `\\.\pipe\Resolume Avenue\rest-api`.

## Authoritative baseline - freeze it

Repository:

this kit's checkout; every path below is relative to its root.

Verified release commit:

`c0a318d` (on `main`)

R1 composition:

`compositions/APC40_Visual_QA_148.avc`

Expected SHA-256:

`91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99`

R1 MIDI preset:

`controllers/APC 40 MK II - Visual QA.xml`

Expected SHA-256:

`4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5`

Accepted R1 contract:

- 1920x1080;
- 148 layers, 148 native Text Animator clips, one column, three decks;
- 148 physical controls represented;
- 203 MIDI shortcut records and 148 unique raw MIDI keys;
- buttons toggle or behave according to the verified preset;
- absolute faders use wake + opacity + Position Y;
- absolute knobs use wake + opacity + Rotation Z;
- the crossfader uses wake + opacity + Position X;
- the relative tempo encoder uses wake + relative rotation;
- faders and ordinary knobs are white; tempo is red;
- fixed LED families remain faithful to the hardware, including blue `S`,
  red dot buttons, amber fixed-amber buttons, and white unlit/no-LED controls;
- no external media dependencies.

Before any mutation, hash both R1 files and inspect the live composition.
At the end, hash them again. They must remain byte-identical. Never overwrite,
rename, delete, re-save, or "clean up" either R1 file.

Read these before designing:

- `docs/CONTROLLER_VISUAL_TWIN_PLAYBOOK.md`
- `docs/stability-protocol.md`
- `docs/fft-recipe-card.md`
- `docs/APC40_Visual_QA_Control_Map.xlsx`
- `docs/APC40_native_addresses.md`
- `compositions/README.md`

Use this rig photo as the primary visual reference for the controller's real
proportions, spacing, control families, and illuminated color language:

`[PATH TO YOUR RIG PHOTO - attach it or give a local path; keep it out of the repo]`

Treat the photo as visual evidence, not as authority for unknown MIDI
addresses or serializer fields.

## Restore the shared MCP path safely

There must be exactly one shared HTTP gateway, one Arena MCP child (used through
the Avenue bridge), one Wire MCP child, and one Avenue pipe bridge. Never launch
per-session STDIO copies.

The gateway scripts and `avenue_pipe_bridge.py` are rig-local prerequisites that
live outside this repository; the paths below are this rig's. On another
machine, substitute your own locations before running anything.

First run the idempotent gateway startup and singleton check:

```powershell
Set-Location 'C:\Art Projects\Res_Fable\resolume-mcp-gateway'
.\scripts\Start-ResolumeMcpGateway.ps1
.\scripts\Get-ResolumeMcpGatewayHealth.ps1 -AssertSingleton
```

The MCP endpoints are already configured as:

- Arena/Avenue target: `http://127.0.0.1:8765/mcp` with
  `X-Resolume-Target: arena`
- Wire target: `http://127.0.0.1:8765/mcp` with
  `X-Resolume-Target: wire`

The gateway singleton check does not cover the pipe bridge, so check it
separately: look for an existing `python` process whose command line contains
`avenue_pipe_bridge.py`. Count Python processes only; the shell running the
query carries the same string in its own command line and must not be counted.
If exactly one exists, reuse it. If none exists, start exactly one hidden
process:

```powershell
Start-Process -FilePath python `
  -ArgumentList 'avenue_pipe_bridge.py' `
  -WorkingDirectory 'C:\Art Projects\Res_Fable' `
  -WindowStyle Hidden
```

Do not kill unrelated Node, Python, MCP, Codex, Claude, Avenue, or Wire
processes. Do not start a second gateway or bridge. If a singleton assertion
fails, diagnose exact executable paths and parent PIDs before touching
anything.

Then call the Arena MCP `status { action: "get" }`. It must report the current
Avenue composition. Empty/error means the bridge or Avenue connection is not
ready. The gateway's one Wire MCP child is normal even while the Wire
application is closed. Wire being closed is not a blocker, and Wire should
remain closed tonight.

Treat Avenue as a single-writer target. Subagents may inspect files, design,
calculate geometry, or run offline validation, but only the root agent may
mutate the live composition.

## Explicit permissions for tonight

I explicitly authorize you to:

- create and switch to the branch `codex/apc40-v2-overnight`;
- create a new V2 candidate by Save As or another non-destructive copy
  operation;
- save the **new V2 candidate** as often as needed;
- add up to three new append-only decorative/chassis layers to that candidate;
- write focused V2 source, validation, screenshot, and handoff files;
- commit and push the V2 branch after the automated gates pass.

This is explicit save permission only for newly named V2 artifacts. It is also
explicit confirmation to create the V2 candidate and add those append-only
layers.

I do **not** authorize:

- overwriting or saving R1;
- modifying or installing the verified R1 XML;
- deleting, clearing, or reordering any of the 148 witness layers;
- inserting a new layer underneath the R1 layers if that changes their target
  indices;
- quitting or restarting Avenue;
- installing or activating a new MIDI preset;
- merging or pushing V2 directly to `main`;
- claiming physical-controller tests that no human performed.

## Candidate names and location

Use:

`beta/compositions/APC40_Visual_Twin_V2_Candidate_<UTC-run-id>.avc`

The run ID makes the filename unique. Never overwrite an existing candidate.

If a new preset truly becomes necessary, generate it offline as:

`beta/controllers/APC 40 MK II - Visual Twin V2 Beta.xml`

Prefer keeping the accepted R1 preset unchanged and compatible. A new preset is
not justified merely because decorative layers were appended above the
existing layer range.

Keep working notes focused. Do not add Kibitz runs, model transcripts, raw
logs, giant audit dumps, or personal filesystem paths to the public repo.

## Non-negotiable implementation rules

1. Use modest MCP batches of roughly 16-30 independent operations.
2. After each meaningful wave, verify once with a monitor snapshot and relevant
   readback. Avenue reads can be stale; never trust only a write response.
3. Do not hand-edit `.avc` XML for clip position, color, trigger style, or other
   state Avenue caches. Make those changes live through the MCP, then save the
   V2 candidate.
4. One playing clip per layer remains the law. Do not combine independent
   witnesses onto one layer.
5. Existing layers 1-148 and every current shortcut target must retain their
   identity and behavior.
6. New layers must be append-only above the protected range and require no new
   MIDI mappings.
7. Do not attach FFT or new effects to any of the 148 witnesses.
8. Do not add composition effects or an Effect Clip that processes the entire
   verified instrument.
9. No feedback loops, Trails, Freeze, strobe, accumulating state, full-screen
   white flashes, or one FFT listener per control.
10. Keep the new visual system immediately bypassable by ejecting or bypassing
    only the added layers.
11. Before every live mutation and save, verify that the active composition is
    the uniquely named V2 candidate, never R1.
12. After every candidate save, re-hash both immutable R1 files.

## V2 visual target

Make the output read more clearly as an APC40 mkII without obscuring the live
labels. Favor a dark, geometry-only chassis with:

- a restrained outer shell;
- the 8x5 pad field;
- scene-launch column;
- track-button rows;
- eight fader rails and endpoints;
- eight track-control knob rings;
- eight device-control knob rings;
- master and crossfader guides;
- section dividers and small hardware accents.

Do not duplicate button names, numbers, values, or MIDI addresses in the
chassis. The existing Text Animator witnesses remain the only labels.

Use native Avenue sources/effects tonight. Do not launch or edit Wire, and do
not create a mandatory Wire dependency. A future Wire implementation may be
designed in notes only. Do not use a bitmap plate or external video.

Because the chassis layers sit above the frozen R1 layer range, use transparent
line geometry, negative space, masks, and low opacity. A top-layer chassis may
not cross any witness's resting box or complete motion envelope.

## FFT target

FFT is decoration, never state. Start with one decorative/chassis layer. Add a
second or third band only if each has a distinct, useful role and the
performance and obstruction gates still pass.

FFT may modulate only bounded opacity or luminance on new decorative layers.
It may not modulate their position, scale, rotation, geometry extent, hue,
blur, or any witness parameter.

Use these only as hypotheses to calibrate against the live Avenue UI:

| Band | Desired region | Maximum role |
|---|---:|---|
| Low | approximately 45-160 Hz | slow shell breath or bounded chassis opacity |
| Mid | approximately 180-2,000 Hz | restrained section-divider energy |
| High | approximately 3,500-12,000 Hz | sparse edge trace or short highlight |

If Avenue exposes bands by a non-Hz UI, report the observed selection rather
than inventing a Hz conversion. Favor opacity/brightness changes with a
nonzero silence floor. Geometry must not expand into protected witness
envelopes. Keep the accepted peak subtle enough that every white, red, blue,
amber, and RGB witness remains legible.

## Build loop

### 1. Preflight

- Confirm the worktree is clean, that `c0a318d` is an ancestor of `HEAD`, and
  that no commit after `c0a318d` touches either R1 file.
- Hash and semantically inspect R1.
- Record live composition name, layer/clip/column/deck counts, resolution,
  active preset, FPS/frame time, and current process topology.
- Create the V2 branch.

If the worktree is unexpectedly dirty, do not discard or overwrite anything.
Identify ownership, preserve it, and use a safe worktree or stop only the
conflicting mutation.

### 2. Create the candidate

- Make a separately named V2 copy.
- Open the V2 candidate and verify that all 148 witnesses and the R1 preset
  still resolve correctly before adding anything.
- Record the candidate's initial hash and counts.

### 3. Derive protected geometry

- Use the workbook, current transforms, and live monitor measurement.
- Define a protected rectangle and full motion envelope for every witness.
- Include fader endpoints, crossfader endpoints, and complete knob rotation
  hulls.
- Store this as deterministic, repo-relative JSON for automated collision
  checks.

### 4. Add the smallest useful chassis

- Read the Resolume content-creation technique before creating visuals.
- Add one geometry layer and inspect it.
- Refine only after a snapshot proves the previous wave.
- Keep total new layers at three or fewer.
- Update thumbnails after changes where required.

### 5. Add bounded FFT

- Establish silence behavior first.
- Test each band in isolation.
- Test the accepted peak with all witnesses visible.
- Remove or bypass any behavior that reduces readability or causes a material
  frame-rate regression.

### 6. Automated QA

At minimum verify:

- R1 files are still byte-identical;
- existing layer indices and all 203 shortcut targets are unchanged;
- candidate has exactly 148 protected witness layers plus 1-3 append-only
  decoration layers;
- every added layer has no MIDI shortcut;
- all controls visible at once;
- faders at minimum, midpoint, and maximum;
- knobs at both rotation extremes;
- crossfader at both endpoints;
- chassis only;
- FFT silence;
- each FFT band alone;
- accepted FFT peak with all witnesses visible;
- instant bypass restores the R1 image;
- machine collision count is zero at every tested state;
- no external media paths;
- before/after FPS and frame time are measured over comparable intervals.

Use a 10% frame-time regression as the provisional rejection threshold. If the
candidate exceeds it, simplify or remove decorative processing until it passes.

Hardware cannot be certified while I am asleep. Mark the controller sweep and
audio calibration as `OPEN - HUMAN TEST REQUIRED`, not passed.

Hard-stop live mutation if an R1 hash changes, the active path is ambiguous,
the source composition is dirty or uncertain, protected pixels overlap,
existing witness semantics drift, a live write cannot be verified, the Avenue
control path is unavailable, or duplicate gateway/bridge/vendor processes
cannot be resolved safely. Continue useful offline work and leave exact
evidence; never improvise around a hard stop.

### 7. Repository and handoff

- Add only the usable V2 candidate, deterministic geometry/validation source,
  concise instructions, and a small set of representative screenshots.
- Run file-format and semantic validators.
- Ensure no absolute personal path appears in a public artifact.
- Re-open generated spreadsheet or structured files if any were changed.
- Commit and push only `codex/apc40-v2-overnight`; do not merge it.

## Persistence

Do not stop merely because Wire is closed, an optional effect is missing, or a
single visual idea fails. Fall back to native Avenue, reduce scope, and keep
the verified core intact. Make steady, reversible progress. If the live MCP
path fails three times after exact diagnostics, continue with offline geometry,
validators, documentation, and a prepared implementation sequence. Never fill
missing evidence with guesses.

## Morning handoff

Leave one short report containing:

1. verdict: candidate ready for human test, partial, or blocked;
2. exact V2 file path and SHA-256;
3. branch and commit hash;
4. exact additions and their bypass method;
5. R1 before/after hashes;
6. layer, clip, shortcut, and external-media counts;
7. collision states tested and intersection count;
8. baseline versus V2 FPS/frame time;
9. links to the most useful screenshots;
10. every open test;
11. a numbered five-minute morning test:
    - open candidate;
    - select the verified R1 preset;
    - trigger column 1 if needed;
    - sweep all faders;
    - rotate all knobs and tempo;
    - sweep the crossfader;
    - press each button family;
    - play silence, bass, midrange, and high-frequency material;
    - confirm zero overlap and readable colors;
    - promote or merge only after I explicitly approve the tested candidate.

The overnight success condition is not "more effects." It is a reversible V2
candidate that looks unmistakably like an APC40 mkII, preserves all 148
verified control witnesses, stays readable at every extreme, and is ready for
a short physical acceptance test in the morning.
