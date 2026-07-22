# APC40 V3 SPEC clip set - QA (PASS)

Automated gates on the shipped movs + candidate comp. Full detail:
`APC40_V3_SPEC_QA.json`. Evidence: `screenshots/spec/` (per-family stills,
bounds overlays, idle wall composite).

| Gate | Result |
|---|---|
| Bounds (lit ink inside silhouette inset, shipped movs) | 0 violations |
| Loop seams (decoded wrap step) | 0 failures |
| Durations vs stated loop lengths | 0 mismatches |
| Chassis red #b51d35 inside controls | 0 hits |
| Legend static (glyph mask between frames) | 0 moved |
| Legend contrast (min luminance ratio) | 3.84 (floor 3.0; label line alone > 4.5, the 60%-alpha address line is contract-fixed) |
| Tile rect overlaps | 0 |
| Bed idle ghosts inside Tier A rects (by design, toggle fallback) | 98 |
| Idle wall red share | 0.1313 (< 0.30) |
| Pre-existing files modified | 0 |
| R1 sha pinned / candidate parses / BOM-free | True / True / True |

Verdict: **PASS**
