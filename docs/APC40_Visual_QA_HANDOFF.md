# APC40 mkII → Resolume Visual QA Overlay — Handoff Spec

For the next coder. This is a **forward spec**, not a status log. Build to the acceptance
criteria below; improve the idea freely, but do not ship until all four criteria pass 100%.

---

## The idea

A Resolume Avenue overlay that mirrors the physical APC40 mkII. **Every** control (button,
fader, knob) has one on-screen text indicator placed where that control physically sits on the
hardware. Press a button → its label appears; press again → it disappears. Move a knob/fader →
its label appears and reflects how far it's moved; return to rest → it disappears. The result is
a live "what am I touching, and is it mapped right" HUD — and a complete MIDI-map verifier.

---

## Acceptance criteria (must all be 100% — this is the definition of done)

1. **Complete.** Every APC40 mkII control has exactly one indicator. Nothing unlabeled, nothing missed.
2. **No overlap.** Indicators sit at their mirrored panel positions and never collide — even when many are active at once.
3. **Buttons = true on/off.** Press shows the label, press again hides it (toggle). Any number can be on at the same time.
4. **Knobs & faders serve the same purpose.** They appear when touched, hide at rest, and their brightness/size tracks the value — so a knob/fader communicates "I'm active + here's my state" just like a button communicates on/off.

Ship test: screenshot a full sweep, overlay it on a photo of the panel — every label on its
control, none overlapping. Then press every button (toggles) and move every knob/fader (appears,
tracks value, hides at rest).

---

## Single source of truth for addresses (do not guess)

**`react-kit/docs/APC40_native_addresses.md`** (+ `.svg` / `.png`) — every control's note/CC,
**channel**, and physical position, decoded from `APC 40 MK II - React v4.4.xml` and verified
against the official Akai APC40 Mk2 Communications Protocol v1.2. Use it. The hard rules:

- Grid = notes 0-39, ch1. **Bottom** row = 0-7 … **top** row = 32-39.
- Per-track buttons share ONE note; the **MIDI channel (1-8) = the track**:
  clip-stop 52, track-select 51, activator 50, solo 49, record-arm 48, crossfade A/B 66.
- Scene 82-86; Stop All Clips 81; Master 80. Transport/device notes per the table
  (Play 91, Stop 92, Rec 93, Metronome 90, Tap 99, Nudge± 100/101, Shift 98, arrows 94-97, etc.).
- Faders = **CC7 on ch1-8** (one CC, channel = track); Master fader CC14; Crossfader CC15;
  Cue CC47; Track knobs CC48-55; Device knobs CC16-23; Tempo CC13 (relative).

---

## Architecture — one control = one layer

Resolume plays only **one clip per layer**, so two indicators on the same layer evict each other.
For "many on at once," every control gets its **own layer**, each holding one generative
**Text Animator** clip (no media files). Per clip: a Transform effect (Position X/Y + Scale),
center alignment, and the control's label text.

---

## Positioning — mirror the panel, guarantee no overlap

- Transform coordinates are **pixels from screen center**: `(0,0)` = center; **+X = right, +Y = down**
  (verified empirically via the MCP — top of screen is negative Y). Edges ≈ ±960 X, ±540 Y at 1080p.
- Map each control's normalized panel position `(nx, ny)` in `[0,1]` to:
  `PosX = (nx - 0.5) × 1720`, `PosY = (ny - 0.5) × 980` (the 1720/980 keeps a margin off the edges).
- **Scale per group** so each label stays inside its control's cell (grid pads big; dense device
  buttons small — e.g., grid 100%, small buttons 40-55%). Text must not spill into a neighbor.
- Set live via MCP: `parameter set target:clip parameter:"video/effect1/Position X"` / `Position Y` / `Scale`.

---

## Buttons — on/off (criterion 3)

Set every button layer's clip to **Toggle** trigger style. Press → connect (show), press → eject (hide):

```
parameter { action:"set", target:"clip", layer:L, column:1, parameter:"triggerstyle", choice:"Toggle" }
```

---

## Knobs & faders — persistent label, reacts IN PLACE (criterion 4)

Continuous controls hold their value, so the system may need the CC layer to stay connected (always
on) just to render. That's fine — let the label **persist**: always visible, parked in its fixed
spot (its "lane"). The reaction is an **in-place appearance change**: turning the knob or moving
the fader **changes the label's color** (or brightness / outline / glow) — but it **never moves,
resizes big, or flies around**. Stays in its lane = no overlap (criterion 2) and the panel stays
readable, while movement still proves the control works.

- **Default:** label always on, dim/neutral at rest; **movement shifts its color** (cycle hue, or dim→bright), settling back when the control stops.
- **Do not** try to encode the exact value — just react. Color-cycling on movement can't be "off," because it asserts no measurement.
- Vary the reaction if you like: hue cycle, outline color, glow, a brightness pulse — anything that changes *where it sits*.

**Skip (not worth the calibration, and they risk moving the label):** level bars, position-travel,
exact LED rings, numeric 0-127, value-proportional opacity. A later bonus at most, never required.

**Implementation notes:**
- CC layers stay **connected** (auto-connect on load) with opacity up so the label persists; do **not** Toggle them.
- Map the CC → a **color / brightness parameter of the label**, not its position or scale.
- A clean "shift then settle" envelope is fiddly in Resolume alone — it's the natural job for
  **Chataigne (the Baton layer)**: turn a raw CC change into a timed color/brightness pulse in place.
  Persistent-label + react-in-place is exactly the behavior Baton is meant to add.

---

## MIDI shortcut file (positional; edit the file directly)

Shortcuts are a plain XML preset — the API/MCP cannot write it; edit the `.xml` directly, then
reload it in Resolume (Shortcuts → MIDI). Targets are **positional** so they work on any comp:

- Button → `/composition/layers/L/clips/1/connect` (with `.../connected` as the feedback sibling).
- Knob/fader → `/composition/layers/L/video/opacity`.
- `RawInputMessage key = 2^56 + (data1<<8) + status`; note-on ch_n status = `0x90+(n-1)`, CC = `0xB0+(n-1)`.
  Per-track controls = same note/CC, the channel is what differs.

---

## Build discipline (hard-won)

- Set clip **state** (position, color, text, trigger style) **live via the Resolume Arena MCP**
  (`avenue_pipe_bridge.py` must be running). Do **not** hand-edit the `.avc` for color/transform —
  Resolume caches those on load and ignores them (proven). Save (Ctrl+S / MCP save) only with the user's OK.
- Batch MCP ops (~16-60 per call). Regression-check after each batch.

---

## Existing assets (start here, don't rebuild from scratch)

- **Composition:** the live 145-layer Visual QA comp in `…/Resolume Avenue/Compositions/`.
- **Active preset:** `APC 40 MK II - Visual QA.xml` (OneDrive Shortcuts/MIDI + `react-kit/controllers/`).
- **Ground-truth preset:** `react-kit/controllers/APC 40 MK II - React v4.4.xml`.
- **Address reference:** `react-kit/docs/APC40_native_addresses.{md,svg,png}` ← the authoritative map.
- **Bridge:** `C:\Art Projects\Res_Fable\avenue_pipe_bridge.py` (run before any MCP call).
- Generator/diagnostic scripts live in the Antigravity scratch folder (145-layer setup, toggle,
  scale, alignment, duplicate-key check). Reuse them; the master is `generate_145_midi_shortcuts.py`.

---

## Definition of done (checklist)

- [ ] Every control from `APC40_native_addresses.md` has an indicator layer — count matches, none missing.
- [ ] Full-sweep screenshot overlaid on the panel: every label on its control, zero overlap.
- [ ] Every button toggles on/off; several can be on simultaneously without evicting each other.
- [ ] Every knob/fader clip is auto-connected; moving it fades its label in proportional to value, hides at rest.
- [ ] Per-track rows confirmed by MIDI monitor (note fixed, channel = track 1-8).
- [ ] Preset reloads clean; composition saved.
