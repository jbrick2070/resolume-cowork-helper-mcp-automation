# Res React Telemetry — the build note

The Measuring Room: five fictional instruments on one APC40, all measuring the same
signal — the room. Built 2026-08-07, entirely from the XML up, **never yet opened in
Resolume**. This note records what was built, which donors every block clones, and
where the risk is.

## 1. The idea

The kit's packs so far have been about *language* (Lexicon: a sentence machine;
Lexicon II: a found-text channel dial) or *pictures* (Live Gen, Orbit Gen). Telemetry
is about the **FFT itself**: every deck is an instrument whose entire fiction is
"I am measuring the music". The audio analysis isn't decorating the content — it *is*
the content. A VU meter that actually meters, an EKG that actually beats.

Second experiment: **raster typography**. All 185 text cells are native Text Block
generators, but the text is Unicode block elements and box drawing — `█▓▒░`,
`▁▂▃▅▇`, `┼─│▲` — so the Text Block becomes a character-cell framebuffer. Graph paper,
seismic needles, VU bars, click fields: drawn in type, no media, no plugins.

## 2. Structure

- 5 decks × 5 layers × 8 columns = **200 clips**.
- Layers, bottom→top: **PAPER** (Alpha, the bed) / **TRACE** (Screen) / **NEEDLE**
  (Screen) / **STAMP** (Add, the hot verdicts) / **READOUT** (Screen, captions).
- Columns 1–5 escalate each instrument (RESTING → DEFIB, CALM → THE BIG ONE,
  -20 dB → RED…); columns 6–8 are the service bay: CAL cards, utility states, SNOW.
- Fixed service coordinates shared by every deck (so one hardware button works on all
  five): TONE (L1C6), BARS (L1C7), SNOW (L1C8), DATA CARD (L3C6), CAL DIAL (L3C8),
  PILOT (L4C8), SLATE (L5C6), SIGNAL LOST (L5C7), TEST CARD (L5C8).

## 3. FFT wiring (the star of the pack)

External FFT (`/audioengine/externalfft`), per the house recipe card. 118 of the 200
cells ride the audio; per-deck personalities, table in `build_telemetry.py`:

| Deck | PAPER | TRACE | NEEDLE | STAMP |
|---|---|---|---|---|
| EKG | bass 6dB/1500ms/.55 | **bass 0–.25, +9dB, 150ms/.12** | static | highs 6/200/.45 |
| RICHTER | bass 6/1800/.55 | bass 6/1200/.30 | mids 6/600/.25 | highs 6/200/.45 |
| VU | bass 3/1500/.60 | **bass 6/400/.15** | **mids 6/400/.15** | **highs 6/400/.15** |
| POLYGRAPH | bass 6/1500/.55 | mids 6/800/.25 | mids 6/600/.20 | highs 6/200/.45 |
| GEIGER | bass 6/1500/.55 | mids 6/500/.20 | static | **highs +9dB/100ms/.12** |

- READOUT stays static everywhere — captions must be legible no matter what the music
  does (the Lexicon word-row rule).
- The VU deck's three rows are shifted into three screen columns by clip Transform
  `Position X` (−520 / 0 / +520) — the deck IS a 3-band analyzer.
- One strobe per deck (PILOT, L4C8): narrowed bass 0–0.25, gain +3, fallback 100 ms,
  floor 0 — the recipe-card strobe law, and the build asserts exactly five exist.
- Service cells are hand-driven (`fft='none'`) so the trim faders and readability hold.
- Sweep floors everywhere else keep every instrument visible with no audio.

## 4. The full surface (149/149)

`gen_preset_telemetry.py` builds every shortcut from one central table, then asserts
the decoded key set equals the complete APC40 mkII census — 40 pads, 5 scene, stop-all,
master, 6×8 per-track buttons, the 25 global buttons, 8+8 knobs, cue, tempo, 8 faders,
master fader, crossfader, footswitch. `docs/_control_map.tsv` is generated from the
same table; the census layout itself is documented in
`../../../docs/APC40_native_addresses.md`.

Where the proven action vocabulary is smaller than the surface, the same cue appears
under a second finger as a declared **mirror** (e.g. Nudge mirrors the ▲▼ paper feed,
Bank < > mirrors the ◀▶ instrument dial, Pan/Sends/User re-fire the TONE/BARS/SNOW
pads). Validation fails on any duplicated path that is not in the `MIRRORS` allowlist,
and on any allowlisted mirror whose count drifts.

Notable choices:

- **CC13 (tempo)** is a hardware *relative* encoder — mapped through the rig-proven
  `behaviour="16392"` / `numSteps="480"` species (donor: the Visual QA preset) to the
  CAL DIAL clip's `transform/rotationz`. First performance use in the kit.
- **CC64 (footswitch)** had never been mapped in any preset here. It drives comp
  ShiftRGB `distance` as a plain dial shortcut: 127 on press, 0 on release = a
  momentary RGB split. ShiftRGB is the one rack effect shipped **active** (at
  Distance 0, i.e. invisible) so the pedal works from a cold load; its Clip Stop
  toggle can still bypass it to lock the pedal out.
- **Comp rack** (all bypassed on load except ShiftRGB): HueRotate, ShiftRGB, LoRez,
  InvertRGB, MirrorQuad, Twitch, ShiftGlitch, Vignette on the Clip Stop row;
  Bloom / WaveWarp / Tunnel on Device On/Off / Lock / Clip-Dev. **No Trails, no
  Freeze** anywhere — the freeze-lock footgun stays banned.
- Tier rule held: CC48–55 exist only as `/composition/selectedclip/dashboard/linkN`
  (translationType 4), asserted.

## 5. Serializer provenance

Every emitted block is a clone of a shape some rig-saved file already contains:

| Block | Donor |
|---|---|
| Clip wrapper, Text Block, dashboard, FFT-on-opacity, Bloom, WaveWarp, layer/deck/comp scaffolding | Lexicon II build (itself cloned from rig-saved React v4.4-era files) |
| ShaperGenerator | `Res React Orbit Gen.avc` (25 rig-played instances) |
| StaticGenerator, StroboscopeGenerator | `Res React Live Gen.avc` |
| Transform with serialized `Position X` / `Rotation Z` | `APC40_Visual_QA_148.avc` |
| ParamColor with channel sub-params (Brightness on a dashboard dial) | Lexicon II Text Block + rig-saved TextGenerator instances |
| Relative-encoder shortcut (`behaviour="16392"`) | `APC 40 MK II - Visual QA.xml` |
| All other shortcut species | React v4.4 via the Lexicon generators |

Resolume serializes sparsely — params not written take their defaults — so the
generator blocks carry only rig-observed parameter names; nothing is invented.

## 6. Known risks, ranked

1. **Block glyphs.** `█▓▒░▁▂▃▅▇┼─│▲▛▜▙▟` are first-time glyphs for the rig font, the
   same class of risk as Lexicon II's French accents. Mitigation shipped:
   `ASCII_FALLBACK = True` in `build_telemetry.py` swaps every glyph for an ASCII
   stand-in, one line + one rebuild.
2. **Shaper default look.** The CAL DIAL relies on the Shaper's default shape (only
   colours are serialized, as in the Orbit donors). If the default is a centred disc
   the rotation may read poorly — the risk is a boring dial, not a broken comp.
3. **Relative encoder vs. this comp.** The 16392 species is rig-proven against a QA
   twin's clip; here it points at a performance clip's transform. Same path grammar,
   untested pairing.
4. **Footswitch polarity.** CC64 sends 127 down / 0 up on the mkII per the protocol
   doc; if a unit inverts, the stomp becomes press-to-clean. Annoying, not dangerous.
5. **VU geometry.** The −520/0/+520 column offsets and bar sizes are computed, not
   seen. Worst case the columns crowd; retune `posX` in `telemetry_content.py`.

## 7. What would make it v2

- Per-deck LED palettes if the single-preset LED map proves too monochrome per row.
- A sixth "OSCILLOSCOPE" deck once someone confirms how far the raster trick stretches.
- Swapping the POLYGRAPH stamp row to a second narrowed band (voice sibilance) after
  hearing it in a real room.
