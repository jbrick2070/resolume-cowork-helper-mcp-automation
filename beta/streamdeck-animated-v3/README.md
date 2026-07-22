# APC40 mkII Animated Twin — V3 (append-only candidate)

A layout-faithful, multicolour, **animated** version of the verified R1 APC40 visual
twin. Each of the 148 controls is its own animated vector clip, matched to its real
silhouette/colour and kept strictly inside its bounds; deep Akai red `#b51d35` is
used only for the chassis. Black background, seamless 4 s loop.

Built entirely under this folder. R1, the R1 controller preset, and every prior
V2 / StreamDeck candidate are byte-untouched. Not yet promoted — cold-open and bless.

## MIDI preset

Use `APC 40 MK II - Visual QA V3 Animated` from `controllers/` with
`compositions/APC40_Electric_Zentropa.avc`. Do not use the retired Electric
Zentropa preset, which targets the abandoned FLIP layout.

- `docs/APC40_ANIMATED_V3_SPEC.md` — what it is + how it was built
- `docs/APC40_V3_INSTALL_ROLLBACK.md` — open / verify / manual fallback / rollback
- `docs/APC40_V3_COLLISION_QA.md` — non-overlap & bounds proof (PASS)
- `compositions/` — `…V3_Animated_Candidate.avc` (R1 + 2 append layers), `…V3_Base.avc` (R1 clone)
- `controllers/` — identical R1 preset copy (203 shortcuts, no new mappings)
- `media/` — surface + chassis MOVs, `clips/` = 148 per-control loops
- `screenshots/` — `APC40_V3_animated_preview_loop.mp4`, contact sheet, stills
- `tools/` — `render_apc40_animated_v3.py`, `qa_collision_v3.py`, `author_v3_comp.py`
- `build/` — `build_input_v3.json`, `animation_manifest_v3.json`

Palette (from the original per-clip ColorId): 1 red · 2 green · 3 amber · 4 cyan ·
5 blue. Deep Akai red `#b51d35` = chassis only.
