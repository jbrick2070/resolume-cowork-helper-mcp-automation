export const meta = {
  name: 'deck-designer',
  description: 'One agent per deck writes all 64 generative clips from the bible and the rig-harvested parameter dictionary; a taste critic checks each deck and a repair pass applies the fixes',
  phases: [
    { title: 'Design', detail: 'one agent per deck, 64 clips each' },
    { title: 'Critique', detail: 'critic per deck, then a repair pass' },
  ],
}

// args: { pack, decks: [{index, name, slug, path}], dict_path, layer_blends }
const LB = args.layer_blends

const CLIP_SCHEMA = {
  type: 'object',
  properties: {
    deck: { type: 'string' },
    clips: { type: 'array', minItems: 64, maxItems: 64, items: { type: 'object', properties: {
      layer: { type: 'integer', minimum: 1, maximum: 8 },
      column: { type: 'integer', minimum: 1, maximum: 8 },
      name: { type: 'string' },
      source: { type: 'string' },
      params: { type: 'object' },
      fft: { type: 'object' },
      effects: { type: 'array', items: { type: 'object', properties: { effect: { type: 'string' }, params: { type: 'object' } }, required: ['effect', 'params'] } },
      opacity: { type: 'number' },
      why: { type: 'string' },
    }, required: ['layer', 'column', 'name', 'source', 'params', 'fft', 'effects', 'why'] } },
  },
  required: ['deck', 'clips'],
}

const RULES = `ARCHITECTURE: 8 layers x 8 columns = 64 clips. Columns are SCENES in journey order (the deck's "columns" list). Layers, bottom to top, with their fixed blend modes:
  1 BED    (blend ${LB[1]})  the environment, full-frame, slow
  2 BODY   (blend ${LB[2]})  the main structural generator
  3 FIGURE (blend ${LB[3]})  the character / the thing in the room
  4 LIGHT  (blend ${LB[4]})  flares, strobes, lamps, flicker
  5 TEXT   (blend ${LB[5]})  ONE text clip per column, from the deck's text_corpus (Text Animator one line <= 22 chars, or Text Block multi-line with \\n)
  6 AURA   (blend ${LB[6]})  a colour wash / grade field (Gradient, Solid Color at low clip opacity, Abstract Field)
  7 GRAIN  (blend ${LB[7]})  texture (Static at low clip opacity, Checkered fine grids, Lines dense, Abstract Field dots)
  8 SCOPE  (blend ${LB[8]})  the FFT readout: a Sine Wave oscilloscope in the deck's paper/accent colour. Put the SAME scope clip in all 8 columns (vary only colour/position). Give it fft on Amplitude (mid), Line Width (low), Frequency (high).
Rows 1-5 are played from pads and must each be a strong, self-sufficient visual; rows 6-8 only arrive with a scene and should be subtle. A scene (column) must COMPOSE: the 8 clips in a column are designed together, and the 8 columns must read as a journey (opening -> build -> peak -> comedown, or whatever the deck's arc is). Every cell must be filled: if the bible says a layer is "Blank" in a column, still give it a quiet, nearly invisible clip (e.g. Solid Color at opacity 0.05, or a Gradient with both colours transparent-ish) so the grid has no holes.

EVERY clip: { layer, column, name (<= 18 chars, Title Case, specific), source (EXACT display name from the dictionary), params (ONLY parameter names that exist for that source; values inside the given ranges; choices by option name; colours as #rrggbb or #rrggbbaa; text as a string), fft ({ "<param>": { "band": "low|mid|high", "gain": dB 3-15, "release": ms 150-1500, "floor": value, "ceiling": value } } - range parameters only, floor/ceiling inside the parameter's range, 0-2 bindings per clip, around 40% of clips should have one), effects ([] or up to 2 of { "effect": EXACT display name, "params": {...} } baked onto the clip for a signature look - Kaleidoscope on a BODY, Trails on a FIGURE, Mirror Quad, Edge Detection, Polkadot, Radial Cloner...; use on at most a third of clips), opacity (optional, 0-1, default 1), why (one short sentence) }.

STOCK ONLY. The bible may mention React Pulsar, React Gate, React Anamorphic, Golden Flicker Reel, Piano triggers, BPM-synced or timeline animation. None of those exist here. Substitute: a pulsar ridgeline = Line Scape (Tilt 0-12, Height 2-8, Line Width thin, Jagginess 0.3-0.7, Show Knots false, Attenuation 200+) or stacked Sine Wave (Waves 8-16, Mode Line, Mirror false); film flicker = Stroboscope at clip opacity 0.1-0.3 with Fade true, or Static on GRAIN; a slow rise = FFT instead; a BPM flash = Stroboscope Frequency 0.05-0.15. Generators animate only through their own Speed-type parameters; reactivity comes only from the fft field.

RULES THAT MAKE IT LOOK GOOD (learned on this rig):
- Every generator's BG Color (where it exists) must be transparent #00000000 on layers 2-8 so the layers stack; the BED may be opaque.
- Metaballs: Size 0.02-0.06 = points/stars/dew; 0.3-0.8 = clouds. Grid 8-16 for many; 2-4 for few. Speed 0.05-0.4 slow, 1-4 fast. Radius 0.3-0.9.
- Rings: Style Stroke, Line Width 0.02-0.08 for fine geometry; Gap 0-360 opens rings into arcs; Rotation Step alternates; Num Rings up to 50 = radar/web.
- Lines: Amount 1-100, Width 0.01-0.1 thin; Rotation in degrees; Fuzzyness 0.1-0.4 soft, 0 hard.
- Line Scape: Tilt 20-45, Height 4-14, Attenuation 150-300 for a horizon; Show Knots false unless you want knots.
- Sine Wave: Waves 1-32, Line Width 0.03-0.2, Amplitude 0.05-0.4; Mode Fill = a solid curtain.
- Spiral: Leafs 1-5, Zoom 0.3-1.5, Speed 0.1-1; Distortion 0-100 bends it; Ramification 0-2 branches it.
- Tunnelines: Zoom 0.5-3, Line Width 0.005-0.05, Frequency 0-1 line density, Vertical/Horizontal 0-0.3 drift.
- Geometry Pattern Maker: Shape Types, Line Ammount 6-30, Inner/Outer Scale, two colour pairs; the richest stock generator - use it for BODY often, different shapes per scene.
- Abstract Field: Octaves 1-6, Amplitude, Density - smoke, nebula, fog, fields. Great BED. It has no colour parameters: it is grey; colour it with a clip effect (Tint or Colorize) when needed.
- Gradient: Type Radial with Color 1 transparent in the centre and Color 2 at the edge = a vignette wash; Horizontal/Vertical = sky; Angular = a sweep.
- Stroboscope: Frequency 0.05-0.3 slow pulses, 0.6-1 harsh; Fade true softens. LIGHT only; Color 2 transparent #00000000 so the OFF phase is clear, not black.
- Text Animator: Size 0.6-2.2 (about 22 chars fit at size 1), Position X/Y are PIXELS from centre (+Y is down), Alignment Center. Keep text off dead centre on most columns (Position Y -380 or +380) so it does not sit on the FIGURE. Text Block: 2-4 short lines with \\n, Line Width 1400, Size 1-2.5.
- Checkered: Num X 16-96 / Num Y 9-54 for graph paper; one colour transparent.
- Static: Mode Grayscale or Two-tone; full-frame noise - clip opacity 0.08-0.25 on GRAIN.
- Solid Color on AURA: clip opacity 0.15-0.4 or it washes everything out.
- Colours: use the deck palette; BED carries the deep colour, FIGURE and LIGHT the accents, TEXT the paper/bone colour or the accent.
- FFT: lows drive size/radius/amplitude/line width (the body of the sound); mids drive density/brightness/speed-ish things; highs drive fine detail: fuzzyness, frequency, dither, line counts. NEVER bind Position, Rotation, Text, or anything that would snap the whole picture. Gains 6-12 dB typical; release 300-900 ms; floor = the silent look, ceiling = the loud look - keep ceilings tasteful.`

function designPrompt(deck) {
  return `You are designing every clip of ONE deck of a live generative Resolume Avenue 7.28.1 instrument for the pack "${args.pack}". Return JSON only (validated by schema).

FIRST, read these two files with the Read tool:
  1. ${deck.path}  - this deck's creative bible (world, palette, scene names, layer notes, moments, text corpus) plus the pack's FFT philosophy.
  2. ${args.dict_path}  - the parameter dictionary: for every stock source and effect, [name, "range", min, max, default], [name, "choice", options, default], [name, "bool", default], [name, "color", default], [name, "text", default]. Use ONLY names and values from it.

${RULES}

Return { deck: "${deck.name}", clips: [64 entries covering every (layer 1-8, column 1-8) exactly once] }.`
}

const CRIT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string' },
    issues: { type: 'array', items: { type: 'object', properties: { layer: { type: 'integer' }, column: { type: 'integer' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['layer', 'column', 'problem', 'fix'] } },
  },
  required: ['verdict', 'issues'],
}

phase('Design')
const results = await pipeline(
  args.decks,
  (deck) => agent(designPrompt(deck), { label: `design:${deck.slug}`, phase: 'Design', schema: CLIP_SCHEMA }),
  async (design, deck) => {
    if (!design) return null
    const crit = await agent(`You are a ruthless but constructive visual critic reviewing ONE deck of generative Resolume clips for taste, scene composition and feasibility. First Read the deck bible at ${deck.path} and the parameter dictionary at ${args.dict_path}. The 64 clips: ${JSON.stringify(design.clips)}.
Find up to 12 concrete problems: a column that does not compose (two full-frame opaque things fighting), a FIGURE that is just another field, a text string over 22 chars or with emoji, a colour far from the palette without reason, an FFT binding that will strobe or snap (Position, Rotation, big travel), a parameter name or option that is NOT in the dictionary, a value outside its range, a clip that will be invisible (opacity ~0, size 0, the only colour transparent), a BED too busy to sit under five layers, a GRAIN or Solid Color clip at opacity 1 (whiteout), a column with an empty cell. For each: layer, column, problem, fix (a precise param change). verdict: one sentence on the deck as a whole.`,
      { label: `critique:${deck.slug}`, phase: 'Critique', schema: CRIT_SCHEMA })
    if (!crit || !crit.issues || crit.issues.length === 0) return { design, crit }
    const repaired = await agent(`Apply these fixes to the deck design and return the COMPLETE corrected design (same JSON shape, all 64 clips, every (layer, column) exactly once). Do not change clips that were not criticised unless a fix requires it. Keep every rule: exact source names, parameter names, options and ranges from the dictionary at ${args.dict_path} (Read it if unsure), colours #rrggbb, text <= 22 chars ASCII.
FIXES: ${JSON.stringify(crit.issues)}
DESIGN: ${JSON.stringify(design)}`,
      { label: `repair:${deck.slug}`, phase: 'Critique', schema: CLIP_SCHEMA })
    return { design: repaired || design, crit }
  },
)
return { decks: results.map(r => r && r.design), critiques: results.map(r => r && r.crit) }
