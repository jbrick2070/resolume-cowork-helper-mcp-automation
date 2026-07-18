# compositions/

Ready-to-load, all-generative `.avc` files - zero file dependencies, open on
any Avenue/Arena 7 machine, no agent required.

## Res React Live Gen.avc (SHIPPED)

The original 6-deck tabbed performance master, gen edition: 6 decks x 4
layers x 8 columns of scene banks, FFT-wired generative Pulse rows, comp FX
rack, clip cells pre-filled with dressed generative placeholders (overwrite with your footage). Pairs with
`../controllers/APC 40 MK II - React v4.4.xml` (freeze-safe; grid, FX
punch row, next-deck on bottom scene-launch - same activation steps as the
Orbit preset, see ../controllers/INSTALL.md). This is the simpler of the
two comps - start here if Orbit's transit ritual is too much ceremony.

## Res React Orbit Gen.avc (SHIPPED)

The five-deck composition described by `../manifests/`, as one file:
5 decks x 4 layers x 9 columns, layer blends set (Alpha/Screen/Screen/Add),
Bloom on the Pulse layer, the bypassed 7-effect composition rack, and every
Pulse cell FFT-wired (external FFT, per-cell band/gain/fallback/floor).
100% generative sources - the custom-source cells ship as their native
fallbacks per the manifests. Every cell ships filled - non-Pulse rows carry generative
placeholders (varied sources, rotated palettes, effect dressing) meant to
be overwritten with YOUR footage: prompt 05 walks it.

PAIRED CONTROLLER PACK: load this comp, then activate
`../controllers/APC 40 MK II - Orbit v1.xml` (Preferences > MIDI, APC40
mkII as input AND output). Grid rows 1-4 = the four layers, row 5 = FX
punches, top scene-launch = TRANSIT (column 9), bottom = next deck. The
layout card in controllers/ explains every control. Full standard mapping +
provenance: ../docs/APC40_Standard_Layout.md and ../docs/APC40_Control_Map.xlsx.

QA state: verified on Avenue 7.27 - loads clean under its own name, all
five decks present, per-manifest cell contents, scene triggers composite
correctly, no missing sources.

Known issue (cosmetic): deck TAB ORDER displays in build order
(O1, O3, O2, O5, O4) rather than journey order - Avenue stores tab order
outside the composition XML's deck sequence. Fix in 30 seconds: drag the
tabs into O1..O5 order and save. The bottom-scene-launch deck cycling
follows whatever order your tabs are in.

First open on your machine: expect a short one-time wait while Avenue
generates thumbnails. The comp expects External FFT as the audio input
(Preferences > Audio) - that is what makes the Pulse row breathe.
