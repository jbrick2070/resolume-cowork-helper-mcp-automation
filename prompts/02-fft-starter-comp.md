# Prompt 02 - FFT Starter Comp (the 4-layer instrument)

Prereq: prompt 01 worked. Expect 20-40 minutes of agent driving. You will be
asked to confirm saves - that is by design.

---

Build me a 4-layer FFT-reactive VJ composition in Resolume, from the current
comp (do NOT create a new composition - work in this one after I confirm
I have nothing unsaved).

Structure (bottom to top):
- Layer 1 "Bed" - blend Alpha, opacity 1.0. Slow textures.
- Layer 2 "Structure" - blend Screen, opacity 1.0. Geometry.
- Layer 3 "Body" - blend Screen, opacity 1.0. The witness row - leave its
  clips empty; I will feed it my own footage later.
- Layer 4 "Pulse" - blend Add, opacity 1.0, add a Bloom effect on the layer.
  This is the audio-reactive row.

8 columns named for an energy arc: Open, Groove, Build, Peak, Comedown,
Deep, Art, Null. Then per column, load ONE native generative source into
Pulse (all different: Lines, Rings, Spiral, Stroboscope, Tunnelines,
Metaballs, Geometry Pattern Maker, Line Scape) and one slow generative
into Bed (Abstract Field / Gradient / Solid Color variants).

FFT-wire every Pulse cell's clip opacity: audio-reactive animation,
external FFT, band split bass 0-0.33 / mids 0.33-0.66 / highs 0.66-1.0.
Peak column gets the Stroboscope on bass with a floor of 0; everything
else floors at 0.12 so cells never go fully dark. Fallback times: fast
cells 100-400 ms, slow cells up to 1800 ms.

Guardrails (non-negotiable):
- Batches of at most 8 ops; after each load batch, wait 12 seconds, then
  ask me to confirm a save before saving.
- One structural op at a time with a re-read after.
- Verify with pixels: after building, trigger the Peak column and take a
  monitor snapshot; describe what you see; if a layer is black, debug it
  before calling this done.

VERIFY (me, human): play music, trigger each column left to right - the
set should rise and fall like a set. Tap tempo by hand; nothing here
assumes a numeric BPM.
