# Prompt 09 - Any Controller (bring your own hardware)

This prompt builds a **performance mapping**. To mirror every physical control
as an on-screen diagnostic instrument, start with
`docs/CONTROLLER_VISUAL_TWIN_PLAYBOOK.md` and then use
`docs/ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md`.

The flexible version of the controller step: you name YOUR MIDI controller
and YOUR requirements; the agent researches the hardware's actual banks,
buttons, and color system, derives the grid rule for it, and shapes the
set + preset around what you own. Works standalone after prompt 02/07/08,
or replaces prompt 03 entirely.

Throughout, follow the kit's control law in `docs/CONTROL_LOGIC.md` - its
safety rails, two-tier knob design, serializer law, and debunk list apply to
EVERY controller, not just the APC40 (there is no "connected clip dashboard"
address - never invent one).

---

My controller is: [MAKE + EXACT MODEL - e.g. Akai APC mini mk2, Novation
Launchpad X, Launch Control XL, Behringer X-Touch, Akai MPD226]

My requirements: [YOUR RULES - e.g. "left hand launches, right hand mixes",
"I need a dedicated blackout button", "faders must never touch audio",
"I play seated with two controllers", "strobes need a hold-to-fire, not
a toggle" - anything. If unsure, write "propose defaults".]

PHASE 1 - RESEARCH THE HARDWARE FIRST (no guessing):
1. Look up my exact controller's layout - web search and MIDI implementation
   docs, not memory: the clip/pad GRID dimensions (rows x columns) and how
   it banks (does it shift/page? dedicated bank buttons?), every non-grid
   control (buttons, faders, encoders, endless vs absolute), and the pad
   COLOR system (velocity table? channel-based modes? sysex? none?).
   Also check how Resolume's controller feedback interacts with it.
2. Report back a one-page hardware map: what the surface truly offers,
   what banks exist, and what the color feedback can and cannot show.
   Flag anything you could not verify - do not invent MIDI details.

PHASE 2 - DERIVE THE GRID RULE FOR THIS SURFACE:
3. The kit's APC40 layout follows a "4x8 bank rule": the comp is SHAPED to
   the controller's native grid so one pad = one cell with zero scrolling,
   and deck switches re-skin the same pads. Derive the equivalent for MY
   hardware: an 8x8 grid fits 4 layers x 8 columns twice (propose what the
   upper half does); a 4x4 wants fewer performance columns or explicit
   banking; a no-grid surface (faders/knobs only) becomes a mixing wing
   and clip launch stays elsewhere. State MY controller's rule in one
   sentence and what comp shape it implies.
4. Reconcile with my requirements above; where they conflict with the
   hardware, say so plainly and propose the compromise. STOP for my OK.

PHASE 3 - MAP AND SHIP:
5. If the comp shape needs adjusting (column count, layer count, FX rack
   size), list the exact changes and make them only after I confirm -
   per the stability protocol, structural ops one at a time.
6. Author the Resolume preset XML for my controller: grid = clip launch
   positionally, color feedback per the researched color system (if the
   hardware needs a helper script for colors - like channel/velocity
   painting - write it, python-rtmidi, and explain how it coexists with
   Resolume's feedback), remaining controls per my requirements, transit
   and deck-next on whatever this surface's best equivalent of scene
   launch is. For any knobs/encoders, use the two-tier dashboard design from
   CONTROL_LOGIC.md (selected-clip dashboard + the always-correct layer-rack
   tier), the canonical 8-slot scheme, and ALL its safety rails - Trails
   feedback capped 0.95, strobe off knobs, enum/boolean params to BUTTONS not
   dials, Video Router never self-inputs. Reuse rig-proven shortcut blocks and
   diff+clone any new species per the serializer law; never emit a debunked
   path or fabricated schema. Every performance action: unique ID and unique
   raw MIDI key except a serializer-required feedback sibling or another
   explicitly documented grouping; validate the declared groups and counts
   before finishing. UTF-8 no BOM, CRLF.
7. Deliver: preset XML (+ helper script if needed), a layout card naming
   every control's job, and the activation steps (Preferences > MIDI,
   input AND output, which preset to pick).

VERIFY (me): plug in, load, play. Every pad launches what its position
says, colors mean something, and nothing in my requirements list got
silently dropped. Turn on General Preferences > "Update clip panels on external
triggers" so knob banks follow what you launch, and pin any Trails dial to max
to confirm the image still decays (no freeze). If a control does the wrong
thing, tell the agent WHICH one - it is a two-minute remap, not a redesign.
