# Resolume Avenue 7.27 — Selected-Clip Dashboard Forward Specification

**Purpose:** implementation handoff for wiring eight APC40 mkII knobs to the currently selected clip's Dashboard dials and batch-populating clip dashboards by editing the MIDI shortcut preset and `.avc` XML.

**Evidence labels**

- **CONFIRMED:** stated by Resolume documentation or directly shown in an official address list/release note.
- **OBSERVED:** present in a real Avenue 7.27 file or a captured shortcut-preset fragment.
- **HYPOTHESIS:** not yet observed in the exact required context. Keep it as a selectable implementation strategy and settle it with the listed test.
- **NEGATIVE CONTROL:** useful for comparison, but not expected to satisfy follow-selection behavior.

## Executive decision

The architecture is valid: Resolume natively supports shortcuts targeting the selected Clip panel entity, and clips have their own eight-dial dashboards.

The best candidate shortcut addresses are:

```text
/composition/selectedclip/dashboard/link1
/composition/selectedclip/dashboard/link2
/composition/selectedclip/dashboard/link3
/composition/selectedclip/dashboard/link4
/composition/selectedclip/dashboard/link5
/composition/selectedclip/dashboard/link6
/composition/selectedclip/dashboard/link7
/composition/selectedclip/dashboard/link8
```

Treat the literal `selectedclip/dashboard/linkN` serialization as **HYPOTHESIS M1**, not as settled fact. Resolume documents all the pieces, but no public MIDI preset specimen has yet shown that exact combined path.

Before batch-editing the 3.5 MB composition, create two tiny UI-authored specimens:

1. One MIDI shortcut mapped to Clip Dashboard Link 1 with Target = **Selected Clip**.
2. One clip whose non-default-valued parameter is linked to Clip Dashboard Link 1.

Those two specimens settle every load-bearing uncertainty below.

## A. Address grammar

### Confirmed forms

The official absolute clip-dashboard form is:

```text
/composition/layers/L/clips/C/dashboard/linkN
```

Layer and clip indexes are 1-based. There is no deck or column token in the control address. The [official OSC address list](https://resolume.com/download/Manual/OSC/OSC%20list.txt) prints `/composition/layers/1/clips/1/dashboard/link1` through `link8` verbatim.

Resolume also documents relative selected-entity aliases, including `/composition/selectedlayer/...`, and explains that a relative address follows the currently selected entity. See the [OSC manual](https://resolume.com/support/en/osc).

### Selected-clip candidate

By composing the confirmed selected-entity grammar with the confirmed dashboard suffix, the selected-clip candidate is:

```text
/composition/selectedclip/dashboard/linkN
```

**Semantics:** selected means the clip currently displayed in the Clip panel. It is not necessarily the last clip launched or currently connected. Verify whether APC clip-launch changes selection on the performance machine.

## B. MIDI shortcut serialization: keep three strategies

Resolume documents three shortcut targets: **By Position**, **This Clip**, and **Selected Clip**. It states that Selected Clip is the default for shortcuts made on the Clip panel. This confirms the desired behavior is native. See the [MIDI Shortcuts manual](https://resolume.com/support/en/midi-shortcuts).

What remains unresolved is how a Selected Clip shortcut is represented in the preset XML.

### Strategy M1 — selected alias path (preferred first test)

```xml
<Shortcut name="Shortcut"
          uniqueId="1789000000000001"
          paramNodeName=""
          behaviour="8">
  <ShortcutPath name="InputPath"
                path="/composition/selectedclip/dashboard/link1"
                translationType="1"
                allowedTranslationTypes="1"/>
  <ShortcutPath name="OutputPath"
                path="/composition/selectedclip/dashboard/link1"
                translationType="1"
                allowedTranslationTypes="1"/>
  <Subtarget type="5" optionIndex="-1"/>
  <RawInputMessage key="144115188075868336"
                   value="0"
                   numSteps="128"/>
</Shortcut>
```

This is the minimal mutation of the known composition-dashboard shortcut. Change **both** paths. Retain the existing shortcut `uniqueId`, `RawInputMessage`, `behaviour`, `Subtarget`, translation settings and device attributes when modifying a real entry.

### Strategy M2 — clone a UI-authored Selected Clip specimen (canonical)

Map knob 1 to Clip Dashboard Link 1 in Avenue 7.27, explicitly choose Target = Selected Clip, quit Avenue, then inspect the preset. Clone the complete entry seven times, changing only:

- `link1` to `link2…link8` wherever the specimen places it;
- the MIDI key/CC;
- the new shortcut `uniqueId` only if new entries are being created.

Do not normalize `behaviour`, `Subtarget`, `paramNodeName` or `allowedTranslationTypes`; preserve exactly what 7.27 writes.

### Strategy M3 — positional/custom-output specimen (negative control)

A real forum specimen contains:

```xml
<Shortcut name="Shortcut"
          uniqueId="1705477263295"
          paramNodeName="ParamRange"
          behaviour="26"
          hasCustomOutputPath="1">
  <ShortcutPath name="InputPath"
                path="/composition/layers/1/clips/8/dashboard/link1"
                translationType="1"
                allowedTranslationTypes="7"/>
  <ShortcutPath name="OutputPath"
                path="/custom-variable/Clip_Hue/value"
                translationType="1"
                allowedTranslationTypes="-1"/>
  <Subtarget type="5" optionIndex="-1"/>
  <RawInputMessage key="432345564227567616" value="0"/>
</Shortcut>
```

Source: [forum thread with captured XML](https://resolume.com/forum/viewtopic.php?t=23104).

This proves that hardcoded clip-dashboard paths and `behaviour="26"` exist. It does **not** prove that a Selected Clip shortcut is always serialized this way: the captured shortcut was created for one specific clip and used a custom OSC output path. Use it only as a negative control or structural comparison.

### MIDI key sequence

For the user's existing channel-1 CC mapping:

```text
Knob 1 / CC48: 144115188075868336
Knob 2 / CC49: 144115188075868592
Knob 3 / CC50: 144115188075868848
Knob 4 / CC51: 144115188075869104
Knob 5 / CC52: 144115188075869360
Knob 6 / CC53: 144115188075869616
Knob 7 / CC54: 144115188075869872
Knob 8 / CC55: 144115188075870128
```

For this preset, each successive CC increments the key by 256. Do not generalize the high-bit encoding to other message classes or custom-output shortcuts.

### Acceptance test for M1/M2/M3

Use separate preset copies, never three entries bound to the same CC simultaneously.

1. Select clip A; move knob 1; only A's Link 1 and linked parameter should change.
2. Select clip B; move the same knob; only B should change.
3. Re-select A; confirm MIDI output/LED-ring feedback reflects A's stored value.
4. Launch B without selecting it; establish whether control remains on A or follows the launched clip.
5. Save, quit and reload; repeat steps 1–4.

The first strategy that passes all five is the production strategy. M2 is authoritative if its XML differs from M1.

## C. Clip dashboard placement

The real 7.27 composition shows this invariant at Composition and Layer scope:

```text
Params[name="Params"]
Params[name="Dashboard"]
remaining entity children...
```

All observed clips without populated dashboards begin:

```text
Params[name="Params"]
Transport
ChoosableMixer / ClipView / VideoTrack...
```

### Placement P1 — immediately after clip Params (strong hypothesis)

```xml
<Clip name="Clip" uniqueId="..." layerIndex="0" columnIndex="0">
  <Params name="Params">
    ...
  </Params>

  <Params name="Dashboard">
    ...
  </Params>

  <Transport name="Transport">
    ...
  </Transport>
  ...
</Clip>
```

This is the preferred batch insertion point.

### Placement P2 — before VideoTrack (weak fallback)

Some earlier research described the dashboard only as being before `VideoTrack`. If P1 is dropped or ignored during round-trip, test placing it immediately before `VideoTrack`. Do not insert both blocks.

### Canonical settlement

Create one clip dashboard in the UI, copy the clip, and paste the clipboard into a text editor. A Resolume team member documents the clip-XML clipboard workflow in this [forum thread](https://resolume.com/forum/viewtopic.php?t=11423). The UI-authored fragment overrides P1 and P2.

## D. Dashboard and linked-parameter XML

### Dashboard block

`name="Link N"` uses a capital L and a space. `linkId="/linkN"` uses lowercase and no space. Link IDs are entity-local; independent layers already reuse `/link1`, `/link3` and `/link8` without collisions.

```xml
<Params name="Dashboard">
  <ParamRange name="Link 1"
              altName="Scale W"
              T="DOUBLE"
              default="DIAL_DEFAULT_PHASE"
              value="DIAL_CURRENT_PHASE">
    <PhaseSourceStatic name="PhaseSourceStatic"/>
  </ParamRange>
  <!-- Repeat Link 2 through Link 8. -->
</Params>
```

Dashboard dials and dashboard-link phase sources carry no `uniqueId`. Do not invent one.

### Sparse linked parameter — normal case

Preserve the parameter's real-unit `default` and `value`. Replace its static phase source with one `DurationSource` followed by one dashboard link.

```xml
<ParamRange name="Scale W" T="DOUBLE" default="100" value="100">
  <DurationSource/>
  <PhaseSourceDashboardLink name="PhaseSourceDashboardLink"
                            phase="0.1"
                            linkId="/link2"
                            linkName="Scale W"/>
</ParamRange>
```

Seven of eight observed live links use this sparse form and have no `ValueRange` children.

### Parameter that already has ranges

Keep every existing `ValueRange` unchanged and in its existing order:

```xml
<ParamRange name="Position X" T="DOUBLE" default="0" value="0">
  <DurationSource/>
  <PhaseSourceDashboardLink name="PhaseSourceDashboardLink"
                            phase="0.5"
                            linkId="/link8"
                            linkName="Position X"/>
  <ValueRange name="defaultRange" min="-1920" max="1920"/>
  <ValueRange name="minMax" min="-32768" max="32768"/>
  <ValueRange name="startStop" min="-1920" max="1920"/>
</ParamRange>
```

**Production rule:** do not add a `ValueRange` triplet to a parameter that did not already contain it. When a target parameter is omitted because it is at its default value, copy the complete parameter fragment from a UI-generated specimen of the same parameter and context.

## E. Phase-to-value formula

For the simple, non-inverted, full-dial case:

```text
value = minimum + phase * (maximum - minimum)
phase = clamp((value - minimum) / (maximum - minimum), 0, 1)
```

Observed examples:

| Parameter | Range | Real value | Phase |
|---|---:|---:|---:|
| Position X | -1920…1920 | 0 | 0.5 |
| Rotation Z | -180…180 | 0 | 0.5 |
| Scale W | 0…1000 | 100 | 0.1 |
| Bloom Amount | 0…1 | 1 | 1 |
| Bloom Size | 0…1 | 0.25 | 0.25 |

Resolume documents the normalized Scale and Rotation ranges in the [OSC manual](https://resolume.com/support/en/osc).

For dashboard Dial Range `[r0,r1]`:

```text
u = clamp((dashboard_phase - r0) / (r1 - r0), 0, 1)
if inverted: u = 1 - u
value = parameter_in + u * (parameter_out - parameter_in)
```

### Range-source hypotheses

- **R1, preferred:** `startStop` stores the effective parameter In/Out points.
- **R2:** `defaultRange` remains the effective mapping range and `startStop` serves another animation role.
- **R3:** when neither is present, the component's intrinsic/native range applies.

All current samples either omit the ranges or have equal `defaultRange` and `startStop`, so they cannot distinguish R1 from R2.

**Settling test:** in the UI, narrow Position X's Dashboard-linked parameter In/Out to `-200…600`, save, and see which XML range changes. Then test Invert and Dial Range once each. Use that writer output as the script's schema.

### Dashboard dial `default` hypotheses

All observed links have parameter current value equal to parameter default, so the samples do not prove what the dashboard dial's `default` means when those values differ.

- **D1:** dial `default` and `value` are both initialized to the parameter's current phase on first link.
- **D2:** dial `default` is the parameter-default phase; dial `value` and link `phase` are the current phase.

The official 7.23.1 fix says dashboard dials should receive the current parameter value on first drop, but does not say whether it changes both XML attributes. See [issue #23603 in the 7.23 release notes](https://resolume.com/blog/30807).

**Settling test:** set Scale W to 250 while its default remains 100, then link it in the UI. If the intrinsic range is 0…1000, inspect whether the dial saves `default="0.25"` or `default="0.1"`; its `value` and link `phase` should be `0.25`.

## F. Coder implementation contract

Implement the transformer with explicit strategies rather than hidden guesses:

```text
--shortcut-strategy alias | ui-specimen | positional-experimental
--dashboard-placement after-params | before-videotrack | ui-specimen
--dial-default current | parameter-default | ui-specimen
--range-source startstop | default-range | intrinsic | preserve-only
--dry-run
```

Recommended production defaults after specimen capture:

```text
shortcut-strategy = ui-specimen
dashboard-placement = ui-specimen, otherwise after-params
dial-default = ui-specimen
range-source = preserve-only
```

For each clip:

1. Resolve exactly one target parameter for each Link 1–8.
2. Find or create the clip's direct-child Dashboard block at the selected placement.
3. Ensure exactly one dashboard `ParamRange` per `Link N`.
4. If the target parameter exists, preserve all its attributes and `ValueRange` children.
5. Remove only its existing phase source; do not retain `PhaseSourceStatic` beside the dashboard link.
6. Ensure one `DurationSource` precedes one `PhaseSourceDashboardLink`.
7. If the target parameter is absent, insert only a same-version, same-context UI-authored parameter specimen. Otherwise skip and log it.
8. Do not create IDs for Dashboard dials, `DurationSource`, `PhaseSourceDashboardLink`, `ParamRange` or `Params`.
9. If duplicating an element that already carries `uniqueId`, mint a fresh instance ID and preserve all cross-references. Do not alter `uniqueTypeId`.
10. Make the transform idempotent: a second run must produce zero semantic changes.

The dry-run report should include:

```text
clip uniqueId / layerIndex / columnIndex
dashboard created or reused
Link N -> parameter path
old phase source -> new phase source
native/effective range used
current value -> calculated phase
created-from-specimen / preserved / skipped reason
```

Abort the batch if any of these occur:

- malformed XML;
- duplicate Link N in one clip dashboard;
- more than one phase source on a parameter;
- a missing target parameter without an approved specimen;
- phase outside 0…1 before clamping;
- duplicate newly minted shortcut or entity IDs;
- output clip count differs from input clip count.

## G. Safe round-trip protocol

1. Fully close Avenue.
2. Copy the composition and named shortcut preset; never edit `Default` or the gig original.
3. Preserve `<?xml version="1.0" encoding="utf-8"?>`; observed 7.27 files are plain UTF-8 XML without BOM, not gzip.
4. Validate the edited XML before launch:

   ```powershell
   $null = [xml](Get-Content -Raw -Encoding UTF8 .\EditedCopy.avc)
   ```

5. Test one clip and one knob first.
6. Load the edited copy, verify the UI and control behavior, Save As a third filename, quit, reopen, and test again.
7. Diff the round-tripped file. Attribute order and floating-point formatting may change; dropped Dashboard or phase-source nodes are failures.
8. Only then run the idempotent batch transformer against another copy of the complete composition.
9. Keep the original through at least the next show.

Attribute order is insignificant XML, but Resolume's child order is private and should be preserved. Self-closing empty tags are valid and appear in Avenue-written files. See the [XML specification](https://www.w3.org/TR/xml/).

## H. Native shortcuts and alternatives

- A golden clip can be stored as clipboard XML or in a preset deck, then pasted and have its media replaced. This workflow is described by a Resolume team member in the [effect-combination forum thread](https://resolume.com/forum/viewtopic.php?t=11423).
- There is no documented one-click “apply this complete Dashboard to all existing clips” command.
- Parameter Animation Presets are real, but they are documented for animation modes/envelopes, not complete dashboard-link sets. See the [7.23 release notes](https://resolume.com/blog/30807).
- Avenue 7.27's REST/MCP interface cannot create MIDI mappings or read/modify Dashboard dials. See the [official MCP limitations](https://resolume.com/support/en/mcp-servers).
- If the eight controls can be layer-generic, a Layer Dashboard is substantially simpler. Keep clip dashboards only when each clip genuinely needs different parameter targets.

## Final implementation order

1. Generate the Selected Clip MIDI specimen and the non-default-value Clip Dashboard specimen in Avenue 7.27.
2. Record which hypotheses M1/M2, P1/P2, R1/R2 and D1/D2 the writer resolves.
3. Build a two-clip scratch composition and three separate preset variants.
4. Select A/B repeatedly, verify knob input and LED output, Save As and reload.
5. Build the eight-link golden clip.
6. Run the transformer in dry-run mode and inspect every skipped/created parameter.
7. Transform a copy, round-trip through Avenue, and run the transformer a second time to prove idempotency.
8. Promote only the round-tripped, reopened copy to the gig workflow.

## Primary sources

- [Resolume MIDI Shortcuts manual](https://resolume.com/support/en/midi-shortcuts)
- [Resolume OSC manual](https://resolume.com/support/en/osc)
- [Official OSC address list](https://resolume.com/download/Manual/OSC/OSC%20list.txt)
- [Resolume Dashboard manual](https://resolume.com/support/en/dashboard)
- [7.23 release notes: parameter presets, shortcut-preset persistence, dashboard-current-value fix](https://resolume.com/blog/30807)
- [Official Arena/Avenue MCP limitations](https://resolume.com/support/en/mcp-servers)
- [Captured positional/custom-output dashboard shortcut XML](https://resolume.com/forum/viewtopic.php?t=23104)
- [Resolume team clipboard-XML/preset-deck workflow](https://resolume.com/forum/viewtopic.php?t=11423)
- [Avenue 7.27 composition used for observed XML shapes](https://github.com/jbrick2070/resolume-cowork-helper-mcp-automation/blob/e8d4df48f45ac960ea683a93a6b32635a98b9095/compositions/Res%20React%20Live%20Gen.avc)
- [Independent public composition sample](https://github.com/tijnisfijn/Resolume-Composition-Converter/blob/c5a29ef3f6bf79111c8d83663b0c36b61c00a55a/test-data/UpscaleComp.avc)

