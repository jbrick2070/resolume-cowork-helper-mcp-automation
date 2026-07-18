# Control Logic — the law for building Resolume controller layouts in this kit

This is the authoritative ruleset that the layout prompts (`prompts/03-apc40-layout.md`,
`prompts/09-any-controller.md`) follow, and that **any agent generating a controller
preset for a Resolume comp MUST obey.** Distilled from a four-report deep-analysis
synthesis (`docs/APC40_Resolume_Synthesis_for_Cowork.md`) and the selected-clip
serializer spec (`docs/Resolume_SelectedClip_Dashboard_Forward_Spec.md`), both verified
against a real Avenue 7.27 rig.

Two goals, always: **(1) knobs that follow what's actually on screen, and (2) never ship
a footgun.** Everything below serves those two.

**The kit ships a Standard Layout** — narrative spec `docs/APC40_Standard_Layout.md`, picture
`docs/APC40_Standard_Layout.png`, and per-control detail `docs/APC40_Control_Map.xlsx`. The
layout prompt emits **two presets every time** — Ease-of-Use and Expert (§3) — plus that
spreadsheet, with every mapping tagged **PROVEN / DOC / PROPOSED** so nothing ships unverified.

---

## 0. NEVER emit these (debunked — do not implement even if asked)

- **Connected-clip dashboard aliases** — `/composition/layers/L/clips/connected/dashboard/linkK`
  (and `/active/`, `/connectedclip/`) **DO NOT EXIST**. If a user asks for "knobs on the
  connected/on-screen clip," give them §1 + §2, never an invented alias.
- **MIDI-button preset switching** — no evidence a shortcut can load another MIDI preset.
  Use two-tier banking (§2) for wide/deep control instead.
- **Fabricated XML schemas** — anything with `<MidiShortcut><MidiMessage><Status>` or a
  `target="3"` attribute is hallucinated. The serializer of record is a file Avenue 7.27
  itself saved (§6).

## 1. "Knobs follow what's on screen" is a PREFERENCE, not XML

Resolume: **General Preferences → "Update clip panels on external triggers"** (ON by
default). With it on, any MIDI-launched clip becomes the *selected* clip, so a knob bank
on `/composition/selectedclip/dashboard/link1..8` rides the **last-launched** clip with
zero extra XML. Put this in every layout card. If a user says "the knobs drift," check
this box first — the usual cause is that box being off, or mouse-selecting another clip
mid-set.

## 2. Two tiers — never let them collide

- **Tier A — Selected-clip dashboard:** `CC48–55 → /composition/selectedclip/dashboard/link1..8`.
  Clip-specific params; rides the on-screen clip via §1. Serializer shape is rig-proven
  (`translationType="4"`, `allowedTranslationTypes="7"`, `behaviour="8"`).
- **Tier B — Layer dashboards:** device knobs `CC16–23 → /composition/layers/L/dashboard/link1..8`.
  The layer **effect rack** — output-following *by construction* (survives clip swaps,
  column launches, Autopilot). Hardware-bank across layers with APC **Track Select**
  (Mode 0: CC16–23 transmit on the selected track's channel; Track Select itself is
  silent to Resolume; expect a position-dump snap on bank switch).
- **HARD RULE:** CC48–55 must **never** appear in both tiers. Assert it in validation.
- Layer / Group / Composition dashboards all exist — use them; they are not clip-only.

## 3. Profiles — pick per comp

**Ship two every time.** The layout prompt emits an **Ease-of-Use** preset (clip grid + faders
+ Track-Control knobs on the selected-clip dashboard — Tier A only, the community-standard knob
trick) and an **Expert** preset (adds Tier B layer dashboards, the FX punch row, scene looks,
transition faders, transport, and crossfader FX). **Generic** = Profile 3 below, the fallback
for a comp whose layers/clips aren't known yet. The three internal profiles compose these two
deliverables:

- **Profile 3 "layer-only" — the get-to-performing-fast default for ANY new/vibe comp.**
  Tier B only, no clip dashboards. 8 knobs on the focus layer's effect rack are *always
  correct* even before the clip-dashboard `.avc` transformer has run. Ship this instantly,
  upsell Tier A later.
- **Profile 1 "default"** — Tier A + Tier B + the §1 preference. The repo default once clip
  dashboards exist.
- **Profile 2 "deterministic"** — Profile 1 but with duplicated connect+select shortcut
  clones instead of relying on the preference (40 extra shortcuts; MIDI output OFF on the
  select clones so `/selected` feedback can't clobber pad `/connected` LED colors).

## 4. Canonical 8-slot dial scheme

`1 MIX · 2 RATE · 3 ENERGY · 4 COLOR · 5 SIZE · 6 SPACE · 7 TEXTURE · 8 MORPH`
(reorderable config array). Fill each slot per source/effect from the param maps.

- **Match parameters by EFFECT IDENTITY + EXACT NAME** — never a global name replace
  (`Speed`/`Opacity` collide on every source).
- **COLOR (Hue)** needs Saturation ≈ 0.75–1 and Brightness > 0, or the dial is inert on
  white/gray/black — the transformer must enforce this precondition when wiring a Hue link.
- **Blank a slot with no good param** by default (semantic integrity > knob utilization);
  filler is an opt-in flag.
- Bound every dial via the parameter's **`startStop`** range (not `defaultRange`).

## 5. Safety rails (defaults — enforce unless the user overrides per-comp)

| Rail | Default |
|---|---|
| **Trails `Feedback`** | 0–0.95, hard ceiling 0.97. **This is the freeze footgun: 1.0 = infinite lock.** |
| **Freeze effect** | Never a bare accidental pad; if mapped, momentary/clearly labeled, and NEVER paired with a feedback knob that can reach 1.0. |
| Strobe / Stroboscope rate | OFF knobs; BPM-synced + momentary ARM button (photosensitivity). |
| Any Speed | floor 0.05 (no dead-freeze), soft cap ~0.75. |
| Scale | floor ~0.10, cap ~3×. Density/Count floor 1. |
| Position X/Y | ±25% travel or off knobs (Text-Block crawl exempt). |
| Bloom | Amount ≤ 0.7, Threshold 0.15–0.95 (low-threshold + max-amount + Add/Screen = white-out). |
| Shift RGB offsets | ≈ ±0.08–0.12. Rings `Gap` ≤ 330°. |
| **Video Router `Input`** | enum → **button only**, and **exclude the router's own host layer** (self-input = recursive feedback, GPU spike). |
| Bed / bottom-layer MIX | optional floor 0.15 (`bed_blackout_guard`); other layers keep full range. |
| **Enum / boolean / Blend / Input** | **BUTTONS only, never `ParamRange` dials.** Keep an explicit exclusion list. |
| Geometry Pattern Maker | third-party (€25 Wire source) — gate behind an ownership check, never a shipped default. |

## 6. Serializer law (hard requirements)

1. The serializer of record = a file **this rig's Avenue 7.27 saved**. Reuse rig-proven
   shortcut blocks verbatim; do not "modernize" them toward any report's XML.
2. For any **new shortcut species** (clip-select, layer-dashboard dial, layer-select
   button): make ONE in the UI, save, quit, diff, **clone byte-for-byte** — change only
   the path L/C values, the MIDI key, and `uniqueId`. Preserve `behaviour`, translation
   attributes, sibling `…/connected`–`…/selected` state paths, and `NamedValues`/`Subtarget`.
3. Reference shapes: clip-launch `behaviour="1028"` (connect/connected quartet); dashboard
   dial `behaviour="8"`; selected-clip dashboard path `translationType="4"`.
4. `.avc` dashboard injection: `<Params name="Dashboard">` + `PhaseSourceDashboardLink
   linkId="/linkN"`; bounds via `startStop`.
5. **Validate every preset:** shortcut count = unique ids = unique MIDI keys; MIDI output
   OFF on select clones; no CC in both tiers. UTF-8 no BOM.

## 7. Grid orientation — decided (Pulse on top, FX at the bottom)

Rows are numbered physical top → bottom: **row 1 = L4 Pulse, row 2 = L3 Body, row 3 = L2
Structure, row 4 = L1 Bed, row 5 = FX punch row** (8 composition-FX toggles). Top physical row
= top on-screen layer; the bottom of the four-row block is Resolume Layer 1 — clips map to the
grid the way Ableton's session view does, so a pad's effect is obvious. The **effects row is
the bottom row**, a dedicated button row that never steals a clip pad, and it is safety-railed
(Freeze momentary, no Trails-feedback pad) so the old freeze footgun is gone. Whole-look launch
(composition columns) lives on the **Scene Launch** buttons; Bank ◀▶ pages further columns. The
old default put the FX row on top and pushed the visual layers down — retired. Print the
orientation on the layout card and confirm in Resolume (a top-row pad fires Pulse).

## 8. Verify every generated layout

- §1 preference ON → launch clip A then B; the knob bank follows.
- Pin a Trails dial to max → the image still decays (proves the 0.95 cap).
- Enum params are buttons, not dials; Video Router can't select its own layer.
- Save + cold restart + retest; diff the XML — links, ranges, uniqueIds, siblings survive.

---

*Full sources: `docs/APC40_Resolume_Synthesis_for_Cowork.md` (adjudicated 4-report
synthesis, conflict ledger, mechanism menu, profiles) and
`docs/Resolume_SelectedClip_Dashboard_Forward_Spec.md` (selected-clip serializer spec).*
