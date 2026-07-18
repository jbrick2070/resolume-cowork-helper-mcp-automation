# APC40 mkII ↔ Resolume 7.27 — Four-Report Synthesis for the Coder (Cowork)

**Consumer:** Cowork, working the git repo that (1) ships baked-in default APC40 mkII mappings and (2) generates prompts/logic for users who AI-generate ("vibe") their own compositions and vibe-code APC40 shortcuts tailored to those comps.
**Therefore:** this is not a single crowned architecture. It is an adjudicated fact base plus a menu of validated mechanisms and three assembleable profiles. The generator picks per-comp; the repo ships one as default.

**Inputs synthesized:**
- **Report A** — "Architecture & Parameter Scheme" (per-layer connected-clip recommendation)
- **Report B** — "Bottom line" (evidence-labeled, 7.27 installer-inspected)
- **Report C** — two-bank hybrid (this thread's prior deliverable; hardware-banking design)
- **Report D** — "Advanced Resolume Control Architecture" (Hybrid Focus deep-research)

**Evidence tags:** `[DOC]` documented (manual / Akai protocol / release notes, cited) · `[RIG]` confirmed live on Jeffrey's rig · `[INSPECT]` Report B's inspection of the official 7.27 installer bundle (trust, spot-check once) · `[TEST]` plausible, must be rig-verified before code depends on it · `[X]` debunked — never implement.

---

## 1. Conflict ledger — adjudicated claims

The coder should treat this table as overriding any statement inside the individual reports.

| # | Claim | A | B | C | D | Verdict |
|---|---|---|---|---|---|---|
| 1 | `/composition/layers/L/clips/connected/dashboard/linkK` (or `/active/`, `/connectedclip/`) exists as a MIDI/OSC alias | asserts, with a fabricated manual quote | denies, from official OSC list | denies, forum staff answer t=19135 | denies | **`[X]` Does not exist.** A's entire primary architecture and its "documented" citation are hallucinated. Never emit these paths. |
| 2 | Layer / Group / Composition dashboards exist | denies ("dashboards are clip-bound") | affirms | affirms, manual cite | affirms | **`[DOC]` They exist** (resolume.com/support/en/dashboard: "top of the Clip, Layer, Group and Composition panels"). A is wrong. |
| 3 | A preference makes selection follow externally triggered clips | not mentioned | "Update panels on external triggers" | not found (proposed shortcut duplication instead) | "Update Clip Panel on Trigger" | **`[DOC]` Confirmed this session.** General Preferences → **"Update clip panels on external triggers"** (resolume.com/support/en/preferences#clip-panel; multiple forum threads use this exact name). It appears to be ON by default — users ask how to turn it *off*. **This is the native select-follows-trigger.** C's duplication and OSC-bridge become fallbacks, not primaries. Practical corollary: the original "knobs drift" symptom likely came from mouse-selecting other clips mid-set, column-launch ambiguity, or this box being unchecked — check the box before writing any code. |
| 4 | Column launch focuses the clip in the currently *selected layer* | — | "Resolume does not document which clip wins" | — | asserts as documented | **`[TEST]`** Not found in the clips or preferences manual pages this session. Treat as undocumented behavior: verify on rig; if it holds, it upgrades the layer-select + column-launch macro to reliable. Do not hard-code assumptions about it. |
| 5 | Shortcut XML schema | `<MidiShortcut><MidiMessage><Status>` | `<Shortcut behaviour><ShortcutPath><RawInputMessage>` (from bundled 7.27 presets) | same family as B `[RIG]` | `target="3"` attribute, A-style nodes | **B/C shape is real** (`[RIG]` + `[INSPECT]` + forum t=23104). **A's and D's XML blocks are fabricated schema — quarantine.** D's *concept* survives as the real UI Target dropdown (This / Selected), but its serialization is wrong. Rule: the serializer of record is a file Avenue 7.27 itself saved on this rig. |
| 6 | APC40 mkII Track Select buttons can be mapped to `/composition/layers/L/select` | — | — | Mode 0: **they emit no MIDI at all** `[DOC]` Akai protocol v1.2 | assumes they transmit | **C is right for Mode 0** (power-up default): Track Select is silent; it re-channels the Device knobs (track N → MIDI ch N) and dumps knob positions on switch. D's layer-focus macro is still implementable — but the buttons must be ones that actually transmit in Mode 0 (Clip Stop / Activator / Solo / Rec-Arm rows send notes on per-track channels `[DOC]`), or APC mini pads, or run Mode 1/2 via sysex and forfeit hardware knob banking. |
| 7 | One MIDI input → multiple shortcuts | — | allowed; warns about MIDI-output feedback | allowed, forum-cited | — | **`[DOC]` Allowed.** Caveat: 7.22 fix list #14453 ("Mapping the same MIDI CCs multiple times can make Resolume lag a lot") — fixed, but keep duplication modest and **disable MIDI output on `select` duplicates** so `/selected` feedback can't clobber the pad's `/connected` LED colors (B). |
| 8 | Trails Feedback cap | 0.85 | 0.95 (abs 0.97) | 0.95 | 0.95 | **Default 0.95**, generator-configurable, absolute ceiling 0.97. |
| 9 | Slot with no good parameter: fill with transform vs leave blank | fills | **blank** | fills with transform | **blank** | **Default = blank** (semantic integrity beats knob utilization; 2-vs-1 among the reports and the better argument). Ship C's transform-fill as an opt-in generator flag `fill_empty_slots_with_transform`. |
| 10 | Geometry Pattern Maker is stock | implied stock | **third-party €25 Wire source** (get-juicebar.com), with UI misspellings "Line Ammount", "Gloabal rot" | assumed in use | implied stock | **B's finding governs the repo:** never bake GPM into shipped defaults; gate it behind an ownership check in the vibe flow. Jeffrey's own comp may keep it. |
| 11 | Layer transport proxies follow the connected clip | — | `/composition/layers/L/speed`, `/direction`, `/playmode`, `/position` proxy the playing clip `[DOC]` | — | — | **Real and useful** — the only *native* connected-clip-following control surface, but transport-only (no source/effect params). Valid RATE-class target. |
| 12 | `/composition/selectedlayer/dashboard/linkK` | — | plausible per relative-address pattern, not in static OSC list — generate via UI, accept only if it round-trips | — | — | **`[TEST]`** exactly as B specifies. Absolute `/composition/layers/L/dashboard/linkK` is the no-inference fallback `[DOC]`. (7.22 fix #22694 "Midi mapping for clips with Selected Layer not working" confirms Selected-Layer targeting is a real, maintained feature.) |
| 13 | Switch entire MIDI mapping presets from a MIDI button (A's wide/deep mode idea) | asserts | — | — | — | **`[TEST], likely `[X]`** — no evidence preset-loading is a mappable shortcut. Do not build on it; the same wide/deep effect is achieved with the two-tier design below. |

---

## 2. Validated mechanism menu

Seven mechanisms survive scrutiny. They compose; they are not rivals.

**M1 — Native selection-follow `[DOC]`.** Preferences → General → "Update clip panels on external triggers" = ON. Every individually MIDI-launched clip becomes the selected clip; the existing `[RIG]` CC48–55 → `/composition/selectedclip/dashboard/link1..8` bank then rides the last-launched clip with zero new XML. Limits (B): "last triggered" ≠ "most visually dominant"; Beat-Snap-queued clips may grab selection before they're visible; column launches are ambiguous (ledger #4).

**M2 — Explicit focus taps `[DOC path]`.** `/composition/layers/L/clips/C/select` changes selection without retriggering. Best home: APC mini mk2 as a 4×8 select-only matrix (B's layout: Body row nearest performer), or a spare APC40 button row. Feedback path `/composition/layers/L/clips/C/selected`. This is the disambiguator after column launches and the "steal focus without relaunching" gesture.

**M3 — Duplicate connect+select shortcuts.** Deterministic select-follows-trigger without relying on the preference: clone each pad's `connect` Shortcut, retarget to `select`, new `uniqueId`, MIDI output off on the clone (ledger #7). More XML (40 clones), fully offline. Use when a build must not depend on a user preference state.

**M4 — Layer dashboards, absolute paths `[DOC]`.** `/composition/layers/L/dashboard/link1..8`. Guaranteed output-following for anything layer-generic (the effect rack): layer effects process whatever clip is playing, surviving clip swaps, Autopilot, and columns. Never co-assign CC48–55 here — a second physical bank is mandatory (B).

**M5 — Mode 0 hardware knob banking `[DOC]` (C's contribution, Akai protocol v1.2).** Device Control knobs CC16–23 transmit on the channel of the selected track; Track Select 1–4 is therefore a zero-software bank switch across the four layers' dashboards (M4 targets). Caveats: position dump on switch (params snap to physical pot positions — treat bank-switch as a deliberate gesture; Resolume has no soft takeover), and Track Select itself is silent to Resolume (ledger #6).

**M6 — Layer transport proxies `[DOC]`** (`/composition/layers/L/speed` etc.) — native connected-clip-follow for tempo/direction/position only. Good fader or secondary-knob targets.

**M7 — Local OSC bridge (last-resort fallback, offline, free).** Watch `/composition/layers/*/clips/*/connected` feedback, echo `/select` back in (~25 lines of python-osc). Only needed if both M1 and M3 fail some edge the rig test exposes. Log raw connected-state ints before filtering `[TEST]`.

**Non-viable, never emit:** connected-clip dashboard aliases (ledger #1); selectedlayer→clip parameter tunneling (B: layer scope only); MIDI-loaded preset switching (ledger #13); A/D XML schemas (ledger #5).

---

## 3. Three assembleable profiles

The repo ships Profile 1 as default. The vibe-flow generator selects (or lets the user select) among all three.

**Profile 1 — "Default" (repo-baked preset + comp template).**
M1 (preference ON, documented in README since it's user-state, not file-state) + Tier A: CC48–55 → `selectedclip/dashboard/link1..8` (the `[RIG]`-proven blocks, kept verbatim as serializer source) + Tier B: Device CC16–23 ch1–4 → `layers/1..4/dashboard/link1..8` with M5 hardware banking + M2 focus taps on the APC mini (or Solo/Clip-Stop row if no mini). Best hands-on feel per hardware dollar; matches the four-layer Bed/Structure/Body/Pulse template.

**Profile 2 — "Deterministic."**
Profile 1 with M3 replacing M1 (duplicated connect+select clones), for users who can't or won't manage the preference, or rigs where panel-update side effects (preview clobbering) matter. Costs 40 extra shortcuts; generator emits them mechanically.

**Profile 3 — "Layer-only minimal" (the vibe-comp safe default).**
M4 + M5 only: no clip dashboards at all. For arbitrary AI-generated comps where per-clip dashboard injection hasn't run yet (or sources are unknown/third-party), 8 knobs on the focus layer's effect rack is *always correct by construction*. The generator can ship this instantly for any comp, then upsell Tier A once the .avc transformer has populated clip dashboards. This is the right first rung for "get to performing fast."

---

## 4. Canonical semantic scheme (generator schema, not hard-code)

**Slot roles — canonical labels = Report B's** (they anchor the only installer-inspected data set): `1 MIX · 2 RATE · 3 ENERGY · 4 COLOR · 5 SIZE · 6 SPACE · 7 TEXTURE · 8 MORPH`. C's and D's orderings are alternate skins; implement the layout as a config array so vibe users can reorder without touching mapping logic.

**Canonical data = Report B's source & effect tables** (7.27-installer-inspected spellings, including GPM's misspellings). Carry them into the repo as `param_maps/sources.yaml` + `param_maps/effects.yaml` verbatim from B, with these synthesis deltas:

- Where **D disagrees with B on a parameter's existence** (e.g., D lists a `Speed` for Lines/Static/Test Card where B's inspection found none), **B wins**; D's entries go into a `candidates_unverified` field, promotable only after the rig's own .avc dump confirms them.
- **D's uniquely good adds to keep:** Video Router self-feedback hazard (see §5); Text Block Tracking-as-MIX / Leading-as-density abstraction (nice alternate skin); Rings `Gap` as MORPH agrees with B.
- **Color rule `[INSPECT]`:** "COLOR" links the nested `ParamColor → Params "Channels" → ParamRange "Hue"`; precondition Saturation ≈ 0.75–1 and Brightness > 0 or the Hue dial is inert on white/gray/black. The transformer must enforce the precondition when it wires a Hue link.
- **Enum/boolean rule:** `Mode`, `Type`, Blend, `Input` (Video Router), Stroboscope `Fade`, bypasses → **buttons only, never `ParamRange` dials.** The transformer's current ParamRange-only design is the correct guard; add an explicit exclusion list so the generator can't be prompted into wiring a choice param to a knob.
- **Blank-slot policy:** default blank (ledger #9); `fill_empty_slots_with_transform: true` re-enables C's Opacity/Scale/Rot-Z/Pos fillers.
- **Ground-truthing loop:** the transformer already parses .avc — add a `dump-params` subcommand that emits every source's actual `ParamRange`/`ParamChoice`/color-channel names from the user's own file. That dump reconciles the YAML per-rig and is the *only* authority for vibe-comps containing sources none of the four reports covered.

**Tier B default rack (per layer, identical ×4, effect order upstream→downstream):** Wave Warp → LoRez → Shift RGB → Hue Rotate → Bloom → Trails → CRT → Vignette (C's reasoning: warp before pixelation, Trails after Bloom smears the glow, CRT+Vignette as final "display glass"). Dial slots follow B's layer-rack table (MIX = layer opacity, ENERGY = Trails `Feedback` capped, COLOR = Hue Rotate, SIZE = LoRez `Pixel Size`, MORPH = Shift RGB `Distance` `[DOC]` — the one effect param name the manual itself confirms). **Strobe is never in the default rack** — momentary ARM button only.

---

## 5. Safety rails (generator defaults, all overridable per-comp)

Bounding mechanism `[DOC]`: dashboard links expose parameter In/Out points, inversion, and Dial Range (resolume.com/support/en/dashboard). In XML, bound the observed `startStop` range, not `defaultRange` `[INSPECT]`; harvest exact attribute names by save-diffing one UI-made example on the target rig before batching `[RIG-procedure]`.

| Rail | Default | Source |
|---|---|---|
| Trails `Feedback` | 0–0.95, hard ceiling 0.97 | ledger #8 |
| Strobe / Stroboscope rate | **off knobs entirely**; BPM-synced + momentary bypass button; if forced onto a knob, cap below the ~15–25 Hz photosensitivity band and mix ≤ ~30% | B + D, Resolume's own strobe warning |
| Any Speed | floor 0.05 (no dead-freeze), soft cap ~0.75 | C + D |
| Density/Count | floor 1 element | C |
| Scale | floor ~0.10, cap ~3× (generator-tunable per source) | C + D |
| Position X/Y | ±25% travel, or off knobs (Text Block crawl exempt) | C |
| Bed-layer MIX | optional floor 0.15 (`bed_blackout_guard: true`); other layers keep full range — to-black is a legit accent move | C, refined by B's floor idea |
| Bloom | Amount 0–0.7ish, Threshold 0.15–0.95; low-threshold + max-amount + Add/Screen = white-out | B |
| Shift RGB channel offsets | ≈ ±0.08–0.12 | B |
| LoRez / Vignette | recognizability caps per B; `Black BG` fixed off | B |
| **Video Router `Input`** | **enum → buttons only; generator must exclude the router's own host layer from selectable inputs** (self-input = instant recursive feedback loop, GPU spike) | D's catch, merged with B's enum rule |
| Rings `Gap` | cap ~330° | B |
| Tunnelines `Zoom` / Gradient `Size` | floors 0.2 / 0.05 | B |

---

## 6. Serializer fidelity rules (hard requirements for the coder)

1. **Serializer of record = files this rig's Avenue 7.27 saved.** The `[RIG]` `selectedclip` blocks are canonical for dial shortcuts; do not "modernize" them toward bundled-preset shapes or any report's XML.
2. For any shortcut species with no rig exemplar yet (clip-select, layer-dashboard dial, layer-select button): **create one instance in the 7.27 UI, save, quit, diff, clone that node** — changing only path L/C values, the MIDI key, and `uniqueId` (fresh unique values; timestamps fine, forum t=23104). Preserve `RawInputMessage` keys, sibling `…/connected`–`…/selected` state paths, `behaviour`, translation attributes, and any `NamedValues`/`Subtarget` blocks byte-for-byte `[INSPECT]`.
3. Known-real reference shapes from B's installer inspection (spot-check against a rig save before use): clip-launch `behaviour="1028"` with connect/connected sibling quartet; dashboard dial `behaviour="8"`; the clip-select quartet is `select`/`selected` in the same pattern — **no bundled preset contains one, so rule 2 applies before batching.**
4. `.avc` injection stays as `[RIG]`-proven: `<Params name="Dashboard">` + `PhaseSourceDashboardLink linkId="/linkN"`; bounds via `startStop`; match parameters by **effect identity + exact name**, never global name replace (`Speed`/`Opacity` collide everywhere) `[INSPECT]`.
5. MIDI output OFF on every `select` clone (LED feedback protection, ledger #7); assert in CI that CC48–55 never appear in both tiers.

## 7. Vibe-flow prompt & logic requirements (the generator)

**Parse before prompting** (from the user's .avc): layer count/names/blend modes; sources present per clip (flag non-stock, e.g., GPM); existing dashboards/links; deck count. **Elicit only what parsing can't give:** hero-layer intent, controller inventory (APC40 alone vs + mini), strobe tolerance, blank-vs-fill preference, Profile choice (default Profile 3 → upgrade to 1 after transformer pass).
**Always-on generator behaviors:** safety rails §5 on by default; enum exclusion list enforced regardless of prompt phrasing; emit the §8 verification checklist customized to the produced mapping; emit the `dump-params` reconciliation report whenever a source is missing from `sources.yaml`; refuse to emit ledger-`[X]` paths even if a user prompt asks for "connected clip knobs" — explain and route to Profile 3 or M2 instead. **Prompt-language note:** users will say "make the knobs control what's on screen"; the generator's internal translation is *"M1/M3 + M2 for the clip tier, M4/M5 for the guarantee tier"* — bake that mapping into the system prompt so the model never re-derives (and re-hallucinates) an alias.

## 8. Unified verification protocol (mechanism-keyed)

1. **MIDI monitor:** CC48–55 fixed channel; Device CC16–23 channel follows Track Select 1→4 (confirms Mode 0 / M5).
2. **M1:** preference box ON → pad-launch A, dial moves A and panel shows A; launch B, dial moves B. Negative control: box OFF → dial stays on mouse-selected clip (proves the preference is the causal agent — B's design).
3. **Column test (ledger #4):** launch full columns repeatedly; record which clip wins selection; test D's selected-layer hypothesis by pre-selecting a layer (via an M2 button) then column-launching. Document; don't contract on it.
4. **M2:** focus taps retarget dials without retriggering playback; check across all 6 decks (by-position validity).
5. **M3 (if built):** duplicate-clone pass of test 2 with the preference OFF; confirm no LED clobber, no lag with 40 clones.
6. **M4/M5:** clips on layers 1+3; Track Select 1 vs 3 isolates the effect knobs per layer; note the position-dump snap.
7. **Bounds:** Trails dial pinned at max 30 s → image still decays; save-diff harvests `startStop` attributes for the transformer.
8. **Timing edges:** Beat Snap, long transitions, Autopilot — when does selection actually move (press vs connect)?
9. **Round trip:** save comp + preset, cold restart, retest 2/4/6; diff XML; confirm links, ranges, uniqueIds, siblings survive.

## 9. Report scorecard (for weighing these documents later)

- **A:** architecture built on a nonexistent alias with a fabricated citation; also wrongly denies layer/comp dashboards; fake XML. Salvage: the wide/deep two-mode *concept* (realized here via the two tiers), basic A/B test skeleton. **Lowest trust.**
- **B:** highest rigor — OSC-list + installer inspection, real serializer shapes, the preference, selectedlayer verify-path, transport proxies, GPM finding, nested-Hue rule, `startStop` bounding, blank-slot doctrine. **Canonical data source.**
- **C:** verified the negative space (no connected alias, forum-staff cite), multi-shortcut legality, Akai Mode 0 protocol facts (banking + silent Track Select + position dump), OSC-bridge fallback, effect-chain ordering, `dump-params` reconciliation idea. **Canonical for hardware behavior**; superseded on select-follows (preference beats duplication as primary).
- **D:** right about the preference; contributed the Video Router recursion hazard, numeric bounds, layer-focus performance macro (needs C's button correction), Text Block abstraction. Weak on XML (fabricated) and on ledger #4 (asserted-as-documented). **Good ideas, verify everything mechanical.**

## 10. Sources (this synthesis's own fact-checks)

- resolume.com/support/en/preferences#clip-panel — "Update clip panels on external triggers" (ledger #3)
- resolume.com/support/en/dashboard — clip/layer/group/comp dashboards; In/Out + Dial Range; RGB Shift `Distance`
- resolume.com/support/en/midi-shortcuts — behaviours; per-device identity
- Resolume forum t=19135 (no connected-clip dashboard mapping), t=21154 (`/select` endpoint), t=11038 (multi-map), t=23104 (dashboard-link shortcut XML + uniqueId), t=19521 (connected-state feedback)
- Resolume 7.22 release notes — fixes #14453 (duplicate-CC lag) and #22694 (Selected Layer MIDI target)
- Akai *APC40 Mk2 Communications Protocol v1.2* — Mode 0 channel banking, silent Track Select, position dump
