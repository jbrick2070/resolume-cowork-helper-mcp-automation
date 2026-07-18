# APC40 mkII — Standard Layout (authoritative)

The one layout the kit ships and the layout prompts generate. It maps **every** surface
control, keeps effects off the clip grid's main flow, and is implementable with Avenue
7.27.1's native MIDI shortcuts. It supersedes the older "FX row on top" arrangement.

Companion files (same folder):

- `APC40_Control_Map.xlsx` — every control × preset, with MIDI, OSC target, mode, safety
  rail, and a **provenance** column. The verification reference: nothing here is taken on faith.
- `APC40_Standard_Layout.png` / `.svg` — the readable one-page picture of this layout.
- `CONTROL_LOGIC.md` — the law (serializer rules, safety rails, debunked paths). This spec
  obeys it.

---

## 1. Two presets, every time

Any run of `prompts/03-apc40-layout.md` emits **two** presets plus the control-map
spreadsheet, so a user can start easy and grow into the full rig without re-mapping:

- **Ease-of-Use** — load-and-go. The clip grid, the faders, and the 8 Track-Control knobs
  wired to the **selected-clip dashboard 1–8**. That knob trick is the whole point: find a
  useful parameter, drop it on a clip's dashboard, and the same 8 knobs control it on every
  clip you launch. Portable to any comp, nothing to hand-build.
- **Expert** — the full rig. Everything Ease-of-Use has, plus banked layer-dashboard knobs,
  an FX punch row, scene-look launch, layer transition faders, full transport, and a
  performance-FX crossfader. Every control does something.
- **Generic** — the "no assumptions about your layer names" fallback the generator ships for
  an arbitrary vibe comp: Tier-B layer dashboards only, which are correct by construction
  before any per-clip work has run.

## 2. Provenance — SOLID vs DASHED

Every mapping in the spreadsheet and the image is tagged so the layout can be checked
against reality, not trusted blindly:

- **PROVEN** (SOLID) — confirmed on the rig, or already shipping in preset v4.4. Trust it.
- **DOC** — documented in the Resolume manual or the Akai APC40 mkII Communications Protocol
  v1.2. Real, spot-check once.
- **PROPOSED** (DASHED) — the function is decided, but the exact shortcut XML still needs a
  UI specimen (make-one-save-diff-clone, `CONTROL_LOGIC.md` §6) before code depends on it.

This is the same solid-fact / dashed-inference convention the studio uses everywhere, and
it is the answer to the fair community critique that AI mappings can "just make stuff up."

## 3. Grid orientation (decided)

Rows are numbered physical top → bottom:

| Row | Assignment |
|---|---|
| 1 (top) | **L4 Pulse** — clips 1–8 |
| 2 | **L3 Body** — clips 1–8 |
| 3 | **L2 Structure** — clips 1–8 |
| 4 | **L1 Bed** — clips 1–8 |
| 5 (bottom) | **FX punch row** — 8 composition-FX toggles |

Top physical row = top visual layer; the bottom of the four-row block is Resolume Layer 1.
Clips map cleanly to the grid the way Ableton's session view does, so it is obvious what each
pad launches. The **effects row lives on the bottom** — a dedicated button row, never
stealing a clip pad from the main flow, and the earlier freeze footgun is gone because the
FX toggles are safety-railed (Freeze momentary, no Trails-feedback on a pad). The FX punch row
is the **Expert** preset; in **Ease-of-Use** the bottom row stays clip/look launch, keeping the
grid pure.

**Whole-look launch** (Resolume columns / Ableton-style "scenes") is on the **Scene Launch
buttons** to the right of the grid; Bank ◀▶ pages to columns beyond the first five.

## 4. Control map by zone (summary)

The exhaustive per-control detail, with MIDI numbers and provenance, is in
`APC40_Control_Map.xlsx`. Summary:

- **Track Control knobs (CC48–55)** → selected-clip dashboard links 1–8. *PROVEN.* Rides the
  on-screen clip via the "Update clip panels on external triggers" preference.
- **Device Control knobs (CC16–23)** → layer dashboard links 1–8 (Tier B), hardware-banked
  across layers by Track Select. Output-following by construction.
- **Clip grid** → §3.
- **Scene Launch** → composition looks 1–5; **Stop All Clips** ejects everything.
- **Faders 1–4** → Layer Master (numeric mixer order: 1=Bed/L1 … 4=Pulse/L4). **Faders 5–8**
  → per-layer transition duration, range clamped 0–2 s. **Master fader** → composition master.
- **Channel-strip buttons** → Clip Stop = eject layer · Activator = layer on (LED lit =
  visible) · Solo = layer solo · Record Arm = Composition-FX arm 1–8 (mirrors the Device knobs).
- **Crossfader** → DRY ⟷ Performance FX via Crossfader Phase (drives FX 4–7; excludes master
  opacity, Freeze, blackout, strobe, and unrestricted feedback). Native A/B-bus crossfading is
  a later option, only after the comp is rebuilt into two A/B layer groups.
- **Transport / utility** → Play (fwd/pause), Stop (eject all), Record (output), Session
  (latched blackout), Tap Tempo, Nudge −/+, Bank ◀▶ (columns), Shift (standalone CLEAN-FX
  reset — native presets can't do Shift+chords, so it is one flat button).

> Note on the mixer order: vertical controls mirror the screen stack (Pulse on top), but the
> horizontal faders use standard ascending channel order (Fader 1 = Bed/L1). Tape-label the
> faders — that mismatch is the most likely live-confusion point.

## 5. Safety rails (always on)

Enforced by default, overridable per comp (`CONTROL_LOGIC.md` §5 is the full table):

- **Trails Feedback** 0–0.95 (ceiling 0.97). 1.0 = infinite-freeze lock — the footgun this
  kit removed.
- **Freeze** momentary only; never a bare pad; never paired with a feedback knob that reaches 1.0.
- **Strobe** off knobs; BPM-synced + momentary ARM (photosensitivity).
- **Enum / boolean / Blend / Video-Router Input** → buttons only, never dials; the Video
  Router may never select its own host layer (recursive feedback).
- **Crossfader FX** exclude opacity / Freeze / blackout / strobe / feedback.
- **Faders 5–8** transition range clamped 0–2 s.

## 6. Implementation status (the loose ends, stated)

- **Authoritative presets:** `controllers/APC 40 MK II - React v4.4.xml` (selected-clip knobs,
  freeze-safe) and `controllers/APC 40 MK II - Orbit v1.xml`. Older versions retired.
- **PROVEN and shippable now:** the Ease-of-Use core (grid launch + selected-clip knobs +
  faders). This is preset v4.4's proven material.
- **DOC (documented, lower-risk):** the Tier-B layer-dashboard mechanism (CC16–23, Track-Select
  banking), output recording, tap tempo, and the blackout — documented in the Resolume manual or
  Akai protocol; spot-check once.
- **PROPOSED, needs a rig-captured shortcut specimen before the XML is trusted:** the species we
  have no rig exemplar for — the layer-dashboard **dial** serialization, transition-duration
  faders, Ignore-Column-Trigger, Crossfader-Phase FX, BPM nudge. Capture one of each in the
  Resolume UI, save, diff, and clone byte-for-byte (`CONTROL_LOGIC.md` §6). The control-map
  spreadsheet's **Provenance** column is the authority, per control.
- **Grid re-orientation** (Pulse to the true top row, FX punch to the bottom) is a
  deterministic remap of existing proven clip-launch shortcuts. It is the classic "5-minute
  fix," and should be confirmed in Resolume (launch a top-row pad → it fires Pulse).

## 7. Build & verify

Generate with `prompts/03-apc40-layout.md` (which now always emits both presets + the
spreadsheet). Validate every preset per `CONTROL_LOGIC.md` §5/§8: shortcut count = unique ids
= unique MIDI keys; no CC in both tiers; UTF-8 no BOM; the "Update clip panels on external
triggers" preference ON; Trails dial pinned to max still decays; a top-row pad fires the top
layer. The spreadsheet's **Verify Checklist** tab is the printable version of this.
