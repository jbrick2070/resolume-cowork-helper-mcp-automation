# fable-kit

**An AI agent can build your Resolume compositions and your customized
controller shortcut layouts.** This kit proves it: FFT-reactive comps built
scene by scene, a complete APC40 mkII shortcut layout authored and validated
(91 mappings, grid colors and all), even custom FFGL plugins - plus the
exact copy-paste prompts to make it happen on YOUR machine with YOUR clips.
Nothing to buy; bring Resolume Avenue/Arena 7, a controller, and an agent
(Claude Code / Cowork) with a Resolume MCP.

> Tested on Resolume Avenue 7.27 + Resolume MCP 7.26, Windows 11.
> Version drift is real; pin your expectations here.

<!-- TODO before publish: 3 GIFs - (1) the APC grid lighting up in column
colors, (2) a deck playing with FFT response, (3) an agent building the
layout live. Screenshots sell this better than any paragraph. -->

## What this is

The generative-only edition of **Res Fable Orbit** - a five-deck
exact-science space set (Physics / Planets / Stellar / Galactic / Cosmic).
Every column is a real physical phenomenon with a placard citing the real
dates and numbers; column 9 of every deck is the TRANSIT to the next regime;
the last transit is the Pale Blue Dot. Zero clip files ship - every reactive
cell is a native Resolume generative source, FFT-wired, and the manifests
mark exactly where your own footage plugs in. Your clips, your rights, your
set.

## Repo tree

```
fable-kit/
  manifests/    orbit_gen_O1..O5.json - the five decks as machine-readable
                specs: per cell source, FFT band/gain/fallback/floor, mood
                notes, user slots, native fallbacks for custom sources
  prompts/      01-first-contact      - verify the agent<->Resolume loop (5 min)
                02-fft-starter-comp   - build a 4-layer reactive instrument
                03-apc40-layout       - agent WRITES your controller preset
                04-apc-mini-painter   - dual-surface rig + grid painter script
                05-your-clips         - curate + wire YOUR library, safely
                06-custom-ffgl        - build a plugin from the FFGL SDK
                07-orbit-gen-rebuild  - rebuild this whole set from manifests/
                08-your-topic-pack    - ANY topic -> full 4x8-bank-optimized set
                09-any-controller     - bring your own hardware; agent researches
                                        its banks/colors and maps to it
  controllers/  APC 40 MK II - Orbit v1.xml (91 shortcuts, validated) +
                LAYOUT_CARD.md (printable, every control explained)
  docs/         fft-recipe-card.md    - the wiring convention and why it feels alive
                stability-protocol.md - how not to crash Avenue while an agent drives
                orbit-placards.md     - the science, scene by scene, read-aloud ready
  LICENSE       MIT
```

## Never coded? Start here (the from-zero path)

You do not need to program anything. You type sentences; the agent does the
clicking. Five installs-and-pastes:

1. **Resolume Avenue or Arena 7** - resolume.com (the trial works; it
   watermarks output but everything in this kit functions).
2. **Claude** - either the Claude desktop app (Cowork mode) or Claude Code
   (the terminal version) from claude.com. If a terminal scares you, use
   the desktop app - same brain.
3. **A Resolume MCP server** - this is the adapter that lets the agent see
   and drive Resolume. Search "Resolume MCP" on GitHub or the Resolume
   forum and follow its install steps; in Claude you then add it under
   Settings > Connectors (desktop) or `claude mcp add` (Code). One-time
   setup, roughly ten minutes.
4. Start Resolume with any composition open, even an empty one.
5. Open `prompts/01-first-contact.md` from this kit, copy everything below
   the line, paste it to Claude, and watch it read your rig out loud.
   That is the whole skill. Every other prompt works exactly the same way:
   open file, copy, paste. The agent will ask before it saves anything.

## Quickstart (10 minutes to first light, if you are already set up)

1. Connect your agent to a Resolume MCP; open any comp in Avenue/Arena 7.
2. Run `prompts/01-first-contact.md`. If the reads match your screen, go.
3. Run `prompts/07-orbit-gen-rebuild.md` (the full five-deck set) or
   `prompts/02-fft-starter-comp.md` (a simpler single-deck instrument).
4. Drop `controllers/APC 40 MK II - Orbit v1.xml` into Resolume's MIDI
   preset folder; Preferences > MIDI: enable the APC40 mkII as input AND
   output; select the preset. The grid lights in your column colors.
5. Set your audio input device (the set reacts to external FFT - the room,
   not the clips) and play.

## Who this is for

VJs who want a controller layout without hand-mapping 91 shortcuts. Agent
users who want a real-world rig project. Skeptics: the preset XML and the
manifests work with zero AI involved - the prompts just automate what they
document. This kit ships TOOLS, not output; the taste stays yours.

## Custom sources and what ships later

Three Pulse cells reference sources that are not stock Avenue: Fable Pulsar
(a custom FFGL source - CP1919 pulsar ridgelines, stateless, 7 scalar
params) and two Wire patches (Golden Flicker Reel, Geometry Pattern Maker).
Every such cell is marked `custom_source` with a native `fallback` - the set
plays complete without them. Roadmap: ready-to-load generative `.avc` comps
and the Fable Optics plugin pack land after license review of the Resolume
FFGL SDK terms (source-only if redistribution requires it). Prompt 06 builds
you the plugin either way.

## Make your OWN pack (the actual point)

Orbit is one theme: space, told in five physics regimes. The format is the
reusable part - a pack is just five things: themed deck manifests (steal the
JSON schema in `manifests/`, it is self-explanatory), an energy-contour
column order, placards that tell the truth, a matching controller preset,
and the discipline in `docs/`. `prompts/08-your-topic-pack.md` is the
one-paste version: fill in your topic ([deep sea, fungi, Detroit techno
history, the Roman aqueducts...]) and your agent designs, builds,
FFT-wires, and controller-maps the whole set - shaped to the APC40's 4x8
pad bank from the first design decision, placards cited, energy contour
enforced. Not an APC40 owner? `prompts/09-any-controller.md` has the agent
research YOUR hardware's actual banks, buttons, and color system, derive
the grid rule for it, and author the preset to match - plus your own
stated requirements.

Claude is what this kit was built and tested with, but the prompts are
plain text and the manifests are plain JSON - any agent that can drive a
Resolume MCP can play. If you make a pack, publish it the same way this
one shipped: manifests + prompts + preset + placards, no clip files, no
personal paths. That is the whole tradition. Send a link.

## Safety, support, license

The stability protocol in `docs/` is not optional reading - every rule in it
was paid for with a real crash. Saves always require the human's explicit
confirmation; the prompts are written that way on purpose.

As-is, PRs welcome, no support promised. Kit text, manifests, prompts:
MIT (see LICENSE). Placard facts carry their citations inline - corrections
are the most welcome PR of all.
