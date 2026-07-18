# Grid-Map Test Comp — r2 hardened plan (implementability)
(r1 plan + Claude r2 anchor + Codex r2, grounded against react-kit)

## Manifest = the single source of truth (build clips + colour checks off it)
Emit as JSON/CSV **and** a human table. One row per grid pad (notes 0–39):

| field | meaning |
|---|---|
| `pad_note` | 0–39, hardware ground truth |
| `physical_row_col` | R1..R5 · C1..C8 |
| `kind` | `clip` \| `fx` \| `empty` \| `blackout` |
| `resolume_target` | OSC path (required unless `kind=empty`) |
| `shortcut_uniqueId` | preset shortcut id; **nullable only when `kind=empty`**; unique when present |
| `testable_on_screen` | true for clips + fx(1–5); **false** for blackout + empty |
| `direct_led_velocity_0_127` | the APC integer velocity the painter/direct-LED test sends (column scheme) |
| `resolume_feedback_values` | Resolume's **stateful normalized floats** keyed by state (`Connected`,`Disconnected`,`Empty`,`Previewing`,`Off`) — e.g. clip note 8 = Connected `0.3464…`, Empty `0.3543…`. These are NOT `velocity/127`. |

Clip pads have **no single "expected velocity"** — colour comes from clip STATE. Only the direct-LED
painter column scheme has one integer per pad.

## Map-freeze parser (exact, implementable)
From the preset XML, for each `<Shortcut>`: take `RawInputMessage key` (a packed int).
Include it **only if** `(key & 0xFF) == 0x90` (note-on); then `note = (key >> 8) & 0x7F`; keep
`note` in 0–39. This filters out CC/fader messages. Assert exactly one shortcut per expected pad
role, emit `{note, raw_key, resolume_target, kind}`, and confirm with **one hardware press test**.
Include decoded note + raw key in every mismatch report.

## FX row — per-kind behaviour (not "8 indicators")
- notes 1–5 = comp-effect bypass toggles → `testable_on_screen` (effect visibly changes).
- note 7 = **comp blackout** (`/composition/bypassed`) → screen may intentionally go black; the
  **direct-LED test is the only persistent signal**; test it LAST.
- notes 0, 6 = **empty** → dark, no shortcut, `shortcut_uniqueId=null`.

## Clip-clone contract (.avc — this is NOT covered by CONTROL_LOGIC's shortcut rules)
Generator interface: input = one saved Text Block **specimen clip**; per target = (deck, layer, column).
- **Rewrite:** `uniqueId` (via a global-unique allocator), `layerIndex`, `columnIndex`, the Text Block
  text param, the background colour param.
- **Preserve byte-for-byte:** source IDs, render-pass structure, `VideoMixerStateID` pattern, all
  other nested blocks.
- **Scaffold:** reuse `make_gen_avc.py`'s strip-and-fill on an existing 4×8 comp (strip clips, inject
  the 32 text clips) — do not hand-build the comp shell.
- **Post-build validation:** no duplicate `uniqueId`; exactly 32 clip placements on the right
  (layer,column) per the frozen map; Text Block params non-empty/legible.
- Gate all of this on first diffing ONE specimen to capture the Text Block param schema.

## Preflight + runbook
Preflight assertions before any test: APC40 visible; MIDI **input** enabled; MIDI **output** enabled;
the exact preset selected; **painter stopped**; "Update clip panels on external triggers" state recorded.
Then: load comp → run direct-LED test → press pads in note order → record mismatches by taxonomy
(wrong note / wrong target / wrong velocity / dim-only / FX-state / blackout).
Verify `apc40_led_test.py` (it lives in the repo **parent**) path + CLI + port-select + return codes
before making it a required acceptance test.

## Build path — one path
UI Text Block specimen → diff → deterministic clone (above). Live-MCP is CUT for v1.

---
### Judgment log (r2)
- **Accepted (all grounded):** stateful-float vs direct-velocity split; exact decode rule; per-kind FX
  model; `.avc` clip-clone contract + validation; preflight/runbook; nullable uniqueId for empty pads.
- Codex decoded the note keys correctly this round (the r1 "0–7=Bed" misread is resolved).
- **Verify-at-build:** Text Block param schema (from specimen); apc40_led_test.py CLI/returns.
