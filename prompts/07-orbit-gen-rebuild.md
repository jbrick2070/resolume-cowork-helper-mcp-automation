# Prompt 07 - Rebuild Res React Orbit (generative edition)

Prereq: prompt 01 worked; the five manifests from this kit's `manifests/`
folder are on your machine. This rebuilds a five-deck exact-science space
set with zero clip files. Expect an hour of agent driving with save
confirmations.

---

Rebuild the "Res React Orbit" generative edition in Resolume from the five
manifest files at [PATH TO manifests/orbit_gen_O1..O5.json].

The shape: five deck tabs - O1 Physics, O2 Planets, O3 Stellar, O4
Galactic, O5 Cosmic. Four layers bottom-up: Bed (Alpha), Structure
(Screen), Body (Screen), Pulse (Add, with Bloom on the layer). Nine
columns per deck; every column is a real physical phenomenon; column 9 is
always the TRANSIT that ends the regime and jumps to the next deck. The
final transit is the Pale Blue Dot - the journey turns around and looks
home. Column order within a deck follows the shared energy contour
(1-2 open, 3 build, 4-5 peak, 6-7 comedown, 8 null, 9 transit); the
manifests' mood notes carry the science.

Method, per deck (deck 1 first, then duplicate its clean shell for the
others and rename):
1. Build/verify the layer stack and 9 columns, named per the manifest.
2. Load the Pulse row from the manifest's L4 cells - all native sources.
   If a cell names a source your Resolume does not have (e.g. "React
   Pulsar", "Golden Flicker Reel"), use the manifest's fallback or the
   nearest native equivalent, and note the substitution.
3. FFT-wire each Pulse cell's listed param: external FFT, the manifest's
   band / gain / fallback / floor exactly. Strobes floor at 0, everything
   else at 0.12.
4. Bed/Structure cells marked user_slot get the gen_fallback source for
   now; Body row stays dark until its owner feeds it (prompt 05).
5. Pixel-verify one column per deck (trigger, snapshot, describe), then
   settle 12 seconds and ask me to confirm a save BEFORE building the
   next deck. One deck per save. Never two structural ops back to back
   without a state re-read.

Deck-switching law you must respect: after creating a new deck, some
Resolume/MCP combinations cannot write clips into it until the comp has
been saved and reloaded - if your clip loads into a fresh deck 404, save
(with my OK), reload the comp (with my OK), and continue. Do not fight
it; it is not your bug.

VERIFY (me): five tabs, tap through each deck's columns with music -
five different physics regimes, one instrument. Then run prompt 03
against it for the matching APC40 layout, or use the shipped
"APC 40 MK II - Orbit v1" preset from controllers/.
