# APC40 mkII Animated Twin — V3 (Stream Deck–style controller twin)

Append-only, layout-faithful animation of the verified R1 visual twin. Every one
of the 148 physical controls becomes its own animated vector clip, matched to its
real silhouette and colour, kept strictly inside its own bounds. Deep Akai red
(`#b51d35`) is reserved for the chassis only — the controls keep the original
multicolour language. Black / transparent background, seamless 4-second loop.

Status: **software candidate — cold-open in Resolume to verify, then bless as V3.**
R1 and all prior verified candidates are byte-untouched; this lives entirely under
new paths in `beta/streamdeck-animated-v3/`.

## 1. What was built

| Artifact | Path |
|---|---|
| Full animated surface (all 148 controls) | `media/APC40_MKII_Animated_Twin_V3_Surface_Alpha.mov` |
| Deep-red chassis frame | `media/APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov` |
| 148 per-control clips (named after each control) | `media/clips/L###_<Control Name>.mov` |
| V3 comparison composition (R1 + 2 append layers) | `compositions/APC40_Visual_Twin_V3_Animated_Candidate.avc` |
| Byte-exact R1 clone (rollback anchor) | `compositions/APC40_Visual_Twin_V3_Base.avc` |
| Controller preset copy (identical, 203 shortcuts) | `controllers/APC 40 MK II - Visual QA V3 Animated.xml` |
| Preview loop / stills / contact sheet | `screenshots/` |
| Per-control colour + motion record | `build/animation_manifest_v3.json` |
| Collision / bounds QA | `docs/APC40_V3_COLLISION_QA.md` |

All ProRes 4444 with alpha (`yuva444p10le`), 1920×1080, 30 fps, 120-frame loop.

## 2. Layout fidelity

Geometry is not invented — it is read from the R1 twin. Every control's position,
silhouette and on-screen text come from `APC40_Visual_QA_148.avc` (148 layers) and
the resolved geometry (`beta/APC40_V2_GEOMETRY_20260719T231500Z.json`). Control
families and shapes:

- grid_pad ×40 — rounded clip pads
- scene_pad ×5, clip_stop ×8, track_select ×8, stop_all ×1, master_select ×1, secondary_text ×1
- track_button ×32 — record arm / solo / activator / crossfade A|B
- rotary ×16 (track + device knobs), small_rotary ×2 (cue, tempo) — circular dials with a swept indicator
- vertical_fader ×9 (8 track + master) — travelling thumb inside the slot
- crossfader ×1 — puck sliding A↔B
- small_button ×20 — transport / device / nav
- bank_polygon ×4 — directional arrows

Each clip reproduces the **same text content** as R1 (e.g. `G1-5 N0/C1`,
`TRACK1 CC48/C1 → 107`, `● N48/C1`, `X-FADE CC15/C1 █ 127`) rendered into the clip.

## 3. Colour language (from the original, not invented)

Colours are inherited from each R1 clip's own `ColorId` (1–5) so the twin keeps the
composition's real multicolour identity:

| ColorId | Meaning in the original | V3 colour |
|---|---|---|
| 1 | clip stop / record arm / stop-all | red `#e83c2e` |
| 2 | scene launch / activator / play | green `#3cd05a` |
| 3 | faders + knobs | amber `#f5aa22` |
| 4 | track/master select, stop | cyan `#28c8dc` |
| 5 | navigation / crossfader / cue / bank | blue `#5a78ff` |

Deep Akai red `#b51d35` is used **only** for the chassis layer (shell, dividers,
knob surrounds, fader/crossfader guides, section rails). No control is forced red.

## 4. Motion vocabulary (Tamagotchi / Stream Deck feel)

Bounded, seamless, readable. Text content and position never change — only light:

- tiles: breathing colour glow + a soft scan-highlight sweep + the MIDI token
  pulsing in its native colour (a status read-out "refreshing")
- knobs: indicator sweeps back and forth inside the knob circle (Rotation-Z feel)
- faders: illuminated thumb travels the slot (Position-Y); crossfader puck slides (Position-X)
- every control also carries a small blinking witness LED in its corner

## 5. Bounds & non-overlap (proven)

Bounds are enforced **structurally**: each element is drawn into a sub-tile of
exactly its geometry box and pasted at `box*SS`, so ink cannot leave the box. QA
(`tools/qa_collision_v3.py`) confirms across the loop: 0 real cross-control box
overlaps, 0 lit pixels outside any control box, and 0 shared pixels between the 13
tightest neighbour pairs. Verdict **PASS**. See `docs/APC40_V3_COLLISION_QA.md`.

## 6. Composition (append-only, ≤3 layers)

`APC40_Visual_Twin_V3_Animated_Candidate.avc` = a clone of R1 with **two** new
Add-blend layers appended above the 148 witnesses:

- Layer 149 `V3 Chassis Frame` → chassis MOV
- Layer 150 `V3 Animated Surface` → surface MOV

Layers 1–148 keep their exact positions and text, so the 203-shortcut controller
preset needs no change. Both new layers are Add blend at opacity 1.0. Bypassing
them restores the R1 image; the base clone is the guaranteed rollback.

## 7. Reproduce

```
python tools/render_apc40_animated_v3.py --frames 0 120   # (chunk if timing out)
python tools/render_apc40_animated_v3.py --encode
python tools/render_apc40_animated_v3.py --clips 0 148
python tools/qa_collision_v3.py
python tools/author_v3_comp.py --layers 2
```
