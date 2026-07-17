# Prompt 08 - Your Topic, Full Pack (the one-paste set builder)

The go-ready version of "make your own pack": paste this with your topic
filled in and your agent designs, builds, wires, and controller-maps a
complete APC40-optimized set about it. Prereq: prompt 01 worked. Expect
1-2 hours with save confirmations. Have this kit's files on your machine -
the agent will read them as its spec.

---

Build me a complete, performable, APC40-optimized Resolume set about:
[YOUR TOPIC - e.g. the deep ocean, fungal networks, the history of
Detroit techno, Roman engineering, the human heart]

First, read your reference material from this kit's folder at
[PATH TO THIS KIT'S FOLDER]: the manifest schema in manifests/orbit_gen_O1.json,
the FFT convention in docs/fft-recipe-card.md, and the safety rules in
docs/stability-protocol.md. Those three files govern everything below.

PHASE 1 - DESIGN ON PAPER FIRST (no Resolume writes):
1. Break my topic into 1 to 5 "regimes" - coherent sub-worlds, each one
   deck. (Start with ONE deck if unsure; the format scales.)
2. Per deck, design 9 columns where EVERY column is a real, nameable thing
   from the topic - no filler scenes. Order them by the energy contour,
   NOT by chronology or logic: columns 1-2 open, 3 builds, 4-5 PEAK, 6-7
   comedown, 8 null/art, 9 TRANSIT (the scene that ends the regime and
   hands off to the next deck). Chronology lives in the placards.
3. Write the manifests in the kit's JSON schema: per cell a NATIVE
   generative source (no files), and for the reactive Pulse row an FFT
   spec per the recipe card - band by what the visual does (bass=pumps,
   mids=travels, highs=sparkles), one strobe max per deck on narrowed
   bass with floor 0, everything else floored 0.12, fallbacks by feel
   speed. No source repeats within a deck's Pulse row.
4. Write a placard per scene: 2-3 dry sentences, real names, real dates,
   real numbers, a citation. If you cannot cite it, pick a scene you can.
5. APC40 OPTIMIZATION CHECK - THE 4x8 BANK RULE, verify it now: the APC40
   mkII clip grid is a 4-row x 8-column bank, and the composition must be
   SHAPED TO IT, not adapted to it later. That means: exactly 4 layers
   (Bed-Alpha / Structure-Screen / Body-Screen / Pulse-Add+Bloom, bottom
   to top) so every layer owns one pad row with zero scrolling; exactly 8
   performance columns under the pads, so the whole deck is playable
   without ever banking sideways; column 9 exists but lives OFF the grid,
   reserved for TRANSIT on the top scene-launch button. One pad = one
   cell, always, on every deck - switching decks re-skins the same 32
   pads, which is how muscle memory transfers across the whole set.
   Also: 5-8 composition effects in a bypassed rack (they become the
   row-5 punch buttons and two device knobs). If a design choice breaks
   any of this, change the design, not the constraint.
6. Show me the full design - manifests + placards + a one-line pitch per
   deck - and STOP for my approval.

PHASE 2 - BUILD (after my OK, one deck per save):
7. Build per the stability protocol, no exceptions: structural ops one at
   a time with re-reads; native-source loads in batches of 8 max; settle
   12 seconds then ask me to confirm each save; pixel-verify one triggered
   column per deck with a monitor snapshot before calling it done. If a
   fresh deck refuses clip loads, save + reload the comp (with my OK) and
   continue - that is a known engine behavior, not your bug.
8. Wire every Pulse cell's FFT exactly per your manifest: external FFT,
   band, gain, fallback, floor.

PHASE 3 - THE CONTROLLER (this is why the constraints existed):
9. Author my "APC 40 MK II - [TOPIC] v1" preset XML per prompt 03's method:
   pads = grid positionally with a distinct color per column, row 5 = the
   FX rack punches in order, top scene-launch = column 9 TRANSIT, bottom
   scene-launch = next deck, faders = layer opacities + master, knobs 1
   and 4 = the two most playable FX params (tell me which you chose).
   Validate: shortcut count = unique ids = unique MIDI keys. Write it
   UTF-8 no BOM, CRLF, and tell me where to put it.
10. Hand me the finished pack as files: manifests/, placards.md, the
    preset XML, and a 10-line layout card. That folder plus this kit's
    docs IS a publishable pack - no clips, no personal paths.

VERIFY (me): load the preset, play music, tap through every deck 1->9 and
jump regimes with transit-then-next-deck. It should feel like one
instrument that happens to know [MY TOPIC] cold.
