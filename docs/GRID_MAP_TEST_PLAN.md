# Grid-Map Test Comp — design spec (for kibitz)

## Goal
A simple **5×8 grid of 100% generative clips** that makes it trivial to debug, on the
APC40 mkII + Resolume **Avenue 7.27** rig, two things at once:
1. the **pad → clip note mapping** (which physical pad fires which layer/column/note), and
2. the **LED colour feedback** (does each pad's LED colour match what it should be),
for the flipped **React v4.4** preset (Pulse on top, FX punch on the bottom).

## Design spine — the MIDI note IS the UID
Every APC40 mkII pad has a fixed firmware **MIDI note** (grid = notes 0–39, bottom-left = 0,
increasing left→right then bottom→top; top-left = 32, top-right = 39). That note is the
button's **UID** *and* its **LED address** — you light pad N by sending note-on N with
velocity = colour. So one number is the single key for both the mapping test and the colour
test. The comp is built off that spine: everything is keyed to the pad's note.

## Core concept
Each of the 40 grid buttons (5×8) gets its **own unique generative clip** whose content
identifies exactly which button it is — keyed to that pad's note. Press a pad → its clip
announces its note / row / col / function, painted in that pad's LED colour. **Unique content
per button is the whole point:** no two clips look alike, so a mis-mapped pad is obvious at a
glance, and the clip's colour vs the pad's LED is a one-press colour check.

## Hard constraints
- **100% generative** — Resolume native sources only (Text Block / Text Animator + a solid
  colour). **No media files** (kit ethos: zero clip files ship).
- Avenue 7.27, offline, local, no paid services.
- Must match the flipped React v4.4 note map:
  - Row 1 (top, notes 32–39) = **L4 Pulse** clips 1–8
  - Row 2 (24–31) = **L3 Body** · Row 3 (16–23) = **L2 Structure** · Row 4 (8–15) = **L1 Bed**
  - Row 5 (bottom, 0–7) = **FX punch** (comp-FX bypass toggles; cols 1 & 7 currently empty, col 8 = comp blackout)
- **Serializer law:** build by make-one-in-UI-save-diff-clone, never fabricated XML.

## Content per clip (self-identifying)
- MIDI **note** (large), physical **Row·Col**, **function** (e.g. "Pulse clip 1" / "FX: Hue Rotate" / "empty").
- Background = the column's exact **APC velocity colour**, so on-screen colour == pad LED colour.
  - APC column velocities (rig-confirmed, from apc40_led_test.py): `[45,37,21,5,9,49,53,3]`
    = blue, cyan, green, red, orange, purple, magenta, white.

## The two debug jobs it must serve
1. **Note map:** press pad → screen shows that pad's note/pos → confirm mapping (or reveal a mismatch instantly).
2. **Colour set:** the clip background = the intended pad LED colour; compare to what the APC
   actually shows. Doubles as the velocity→colour reference. (Note Resolume's own feedback is
   dim ~10% and on-change; a painter or feedback-bridge is the bright path.)

## Open questions for the panel
- **Text Block vs Text Animator** for legible static labels in Avenue 7.27 — gotchas, params, perf?
- **FX row:** those pads toggle comp effects, not clips, so they won't launch a test clip. How
  should the test surface FX-toggle state instead (visible tint from the effect itself? a
  dedicated indicator layer?) without breaking the "each pad self-identifies" idea?
- **Build path** given the write laws: (a) one Text Block specimen → file-clone 40× (like
  make_gen_avc.py), or (b) build live via the Resolume MCP? Trade-offs, risks, which is safer?
- Make the colour check **rigorous / unambiguous** — idle vs playing brightness, dim Resolume
  feedback vs painted 100%, so a mismatch is obvious not ambiguous.
- **Simpler?** Anything that achieves the same debug value with fewer moving parts.

## Repo context (for grounding)
- Preset: `controllers/APC 40 MK II - React v4.4.xml` (flipped; grid note map already decoded).
- Comps: `compositions/Res React Live Gen.avc`, `Res React Orbit Gen.avc` (100% gen, FFT-wired).
- Law: `docs/CONTROL_LOGIC.md`. Colour/painter facts: `../apc_grid_painter.py`, `../apc40_led_test.py`.
