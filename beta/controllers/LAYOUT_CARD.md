# APC40 mkII — Standard Layout Card (print me)

> **Beta performance layout:** this card does not describe the verified
> 148-control Visual QA twin.

Full spec: `../../docs/APC40_Standard_Layout.md` · picture:
`../../docs/APC40_Standard_Layout.png` · every control + provenance:
`../../docs/APC40_Control_Map.xlsx` · law: `../../docs/CONTROL_LOGIC.md`

**Authoritative presets:** `APC 40 MK II - React v4.4.xml` (pairs with the Live comp) and
`APC 40 MK II - Orbit v1.xml` (pairs with the Space/Orbit comp). Older versions retired.

**Activation:** Resolume Preferences > MIDI > enable "APC40 mkII" as INPUT and OUTPUT (output
= pad-colour feedback), then select the preset. Also turn ON General Preferences > "Update
clip panels on external triggers" so the Track-knob dashboards follow the clip you launch.

Convention: **SOLID = documented / rig-proven · DASHED = proposed, capture a UI specimen first.**

## Clip grid (5×8 pads) — top row = top layer

- Row 1 (top) = **L4 Pulse** clips 1–8
- Row 2 = **L3 Body** · Row 3 = **L2 Structure** · Row 4 = **L1 Bed** (bottom of the block = Layer 1)
- Row 5 (bottom) = **FX PUNCH ROW** — 8 composition-FX toggles, punch in / out. Freeze is
  momentary; there is no Trails-feedback pad (that was the freeze footgun, removed). This FX
  row is the Expert preset; Ease-of-Use leaves the bottom row as clip/look launch.
- Columns 1–8 = the 8 clips per layer; pad colours are per-column feedback.

## Scene launch (right edge) + knobs

- **Scene Launch** = whole-look launch (composition columns, Ableton-style). Bank ◀▶ pages
  further columns. **Stop All Clips** ejects everything.
- **Track Control knobs** → selected-clip dashboard 1–8 (rides what's on screen). *PROVEN.*
- **Device Control knobs** → layer dashboards 1–8, banked across layers by Track Select.

## Faders, crossfader, transport

- **Faders 1–4** = Layer Master (numeric order: 1 = Bed/L1 … 4 = Pulse/L4). **5–8** = layer
  transition duration, clamped 0–2 s (Expert). **Master** = composition master.
- **Crossfader** = DRY ⟷ Performance FX (Crossfader Phase; excludes opacity/Freeze/blackout/strobe).
- **Transport / utility:** Play (fwd/pause) · Stop (eject all) · Record (output) · Session
  (latched blackout) · Tap Tempo · Nudge −/+ · Bank ◀▶ (columns) · Shift (CLEAN-FX reset).
- Channel-strip buttons: Clip Stop = eject layer · Activator = layer on (LED lit = visible)
  · Solo = layer solo · Rec-Arm = Comp-FX arm 1–8.

> Fader order (Bed → Pulse, left to right) is the reverse of the grid stack (Pulse on top).
> Deliberate — tape-label the faders.

## Orbit (Space) preset — deck variant

The Orbit comp is a five-deck space set; its column order IS the energy arc (1–2 open, 3
build, 4–5 peak, 6–7 comedown, 8 art, 9 transit). On `Orbit v1`, the Scene Launch top button
fires column 9 (the transit) and the bottom button jumps to the next deck. Tap tempo on the
Resolume side; audio reactivity is FFT on external input — set your audio device before doors.

## Preset status

`React v4.4` and `Orbit v1` are the proven, freeze-safe presets. The **Standard orientation
above** (Pulse to the true top row, FX punch to the bottom) is the target the docs and image
now specify; where a shipping XML still uses the prior orientation, re-confirm in Resolume
before a gig — launch a top-row pad and check it fires **Pulse**. Re-flipping is not a blind
index edit: moving the FX row off the top swaps two rows' shortcut *species* (clip-launch
quartet ↔ effect-toggle), so do it in the Resolume UI or via a tested transform.
