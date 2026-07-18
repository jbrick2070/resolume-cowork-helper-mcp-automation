# Prompt 03 - APC40 mkII Layout Builder (the party trick)

Prereq: a comp you like (prompt 02 or your own). Your agent WRITES TWO CONTROLLER
PRESETS for it - an Ease-of-Use preset (grid + faders + Track-Control knobs on the
selected-clip dashboard) and an Expert preset (the full rig) - plus a control-map
spreadsheet, following the kit's Standard Layout (`docs/APC40_Standard_Layout.md`) and the
control law (`docs/CONTROL_LOGIC.md`). This is the "I did not know an agent could do that"
moment, and it ships with guardrails so it can't freeze your output the way a naive mapping can.

---

Read `docs/CONTROL_LOGIC.md` first - it is the LAW for this task. Obey its
safety rails, use its two-tier knob design, and never emit anything it lists as
debunked (there is no "connected clip dashboard" address - do not invent one).
Then generate a complete "APC 40 MK II" MIDI preset XML for my current Resolume
composition. Do not touch Resolume while writing - this is a file job.

STEP 1 - READ my comp via the MCP: layer count / names / blend modes, column
count / names, composition effects, and each clip's source + effects. Flag any
non-stock source (e.g. Geometry Pattern Maker is a third-party Wire source - do
not assume I own it).

STEP 2 - AUTHOR the preset per CONTROL_LOGIC.md:

- GRID: pads mirror the clip grid positionally, top row = top on-screen layer.
  Standard orientation (print it on the layout card): row 1 = top layer ... row 4 =
  Resolume Layer 1, and the BOTTOM row = the FX punch row (composition-FX toggles,
  safety-railed - Freeze momentary, no Trails-feedback pad) in the Expert preset; Ease-of-Use
  leaves the bottom row as clip/look launch. Whole-look launch goes on the Scene Launch
  buttons, never a clip row. Clip-launch shortcuts use
  `behaviour="1028"` with the connect/connected sibling quartet.
- COLOR FEEDBACK: per-column pad colors via the APC40 mkII velocity table;
  playing/queued states come free from Resolume.
- KNOBS - two tiers, NEVER colliding (CONTROL_LOGIC section 2):
  - Tier A: `CC48-55 -> /composition/selectedclip/dashboard/link1..8`. Rides the
    on-screen clip via the "Update clip panels on external triggers" preference
    (tell me to turn it on). Serializer shape: `behaviour="8"`,
    `translationType="4"`, `allowedTranslationTypes="7"`.
  - Tier B: device knobs `CC16-23 -> /composition/layers/L/dashboard/link1..8`
    (the layer effect rack; hardware-bank across layers with Track Select).
  - If clip dashboards are not populated yet, ship Tier B only (Profile 3) - it
    is correct by construction. Assert CC48-55 never appear in both tiers.
  - Use the canonical 8-slot scheme (MIX/RATE/ENERGY/COLOR/SIZE/SPACE/TEXTURE/
    MORPH); match params by EFFECT IDENTITY + EXACT NAME; apply ALL section-5
    safety rails.
- SAFETY (non-negotiable, CONTROL_LOGIC section 5): Trails `Feedback` capped at
  0.95 (never a dial that can reach 1.0 = infinite freeze); Strobe off knobs
  (momentary ARM only); enum / boolean / Blend / Video-Router `Input` -> BUTTONS
  only, never dials; Video Router must exclude its own host layer. Effect-bypass
  toggles are fine as recoverable punches, but do NOT bury a bare Freeze where it
  gets mashed by accident, and do NOT pair Trails with an uncapped feedback knob.
  (That exact pairing is the footgun this kit removed.)
- Scene launch column: composition looks (whole-column launch); Stop All Clips =
  eject all. (Orbit's transit + next-deck is a per-comp variant - say which you used.)
- Faders: 1-4 = Layer Master (numeric order, Bed=1 ... Pulse=4); 5-8 = layer transition
  duration clamped 0-2 s (Expert) or unmapped (Ease); master = comp master; crossfader =
  DRY<->Performance-FX phase (Expert) or native crossfader (Ease).
- SERIALIZER LAW (CONTROL_LOGIC section 6): reuse rig-proven shortcut blocks
  verbatim. For any shortcut species you have no exemplar for (clip-select,
  layer-dashboard dial, layer-select button), have me make ONE in the Resolume
  UI, save, and you diff + clone it byte-for-byte - changing only path L/C, the
  MIDI key, and `uniqueId`. Never emit a fabricated schema.
- Every shortcut: unique id + unique MIDI key. Validate before finishing:
  shortcut count = unique ids = unique MIDI keys; no CC in both tiers; MIDI
  output OFF on any select clones.

STEP 3 - WRITE both presets as UTF-8 without BOM, CRLF line endings, into files I can
drop into Resolume's MIDI preset folder (name them "... - Ease" and "... - Expert"), and
update `docs/APC40_Control_Map.xlsx` so every control's row shows both presets with its
provenance (PROVEN / DOC / PROPOSED). Then print: total shortcut count per preset, the
validation counts, which safety rails you applied, and a layout card of what every control
does (including the grid orientation).

VERIFY (me): Preferences > MIDI enable "APC40 mkII" as input AND output, select
the preset; General Preferences > "Update clip panels on external triggers" = ON.
The grid lights in my column colors within ~2 seconds. Launch a clip and turn a
Tier-A knob - it should ride what is on screen. Pin a Trails dial to max - the
image still decays, it does not freeze. If a pad launches the WRONG clip, the
grid orientation is flipped - tell your agent, it is a 5-minute fix.
