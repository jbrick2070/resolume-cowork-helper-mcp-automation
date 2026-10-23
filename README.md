# apc40mkii-kit

**An AI agent can build your Resolume compositions and customized controller
shortcut layouts.** The stable release is a complete APC40 mkII visual twin:
148 native Text Animator witnesses driven by a verified 203-shortcut MIDI
preset. The repository also includes reusable prompts, control maps, and
experimental FFT-reactive compositions under `beta/`.

> Tested on Resolume Avenue 7.27 + Resolume MCP 7.26, Windows 11.
> Version drift is real; pin your expectations here.

<!-- gallery:start -->
## The compositions

17 compositions; 16 of them photographed from Avenue's own output. Click a frame for its full card, or see
the [whole gallery](gallery/README.md).

| | |
|---|---|
| <a href="gallery/README.md#apc40-visual-qa-148"><img src="gallery/visual-qa-148/hero.jpg" alt="APC40 Visual QA 148" width="320"></a> | **APC40 Visual QA 148** · stable<br>The stable release: every physical control of the APC40 mkII mirrored on screen by 148 native Text Animator witnesses.<br>[`compositions/`](compositions) |
| <a href="gallery/README.md#electric-zentropa"><img src="gallery/electric-zentropa/hero.jpg" alt="Electric Zentropa" width="320"></a> | **Electric Zentropa** · stable<br>The performance interface, built only from native Resolume sources (Lost Buttons edition; True Button Toggles shares the interface).<br>[`compositions/`](compositions) |
| <a href="gallery/README.md#res-react-live-gen"><img src="gallery/res-react-live-gen/hero.jpg" alt="Res React Live Gen" width="320"></a> | **Res React Live Gen** · beta<br>An audio-reactive generative instrument: FFT-driven stock generators across six decks.<br>[`beta/compositions/`](beta/compositions) |
| <a href="gallery/README.md#res-react-orbit-gen"><img src="gallery/res-react-orbit-gen/hero.jpg" alt="Res React Orbit Gen" width="320"></a> | **Res React Orbit Gen** · beta<br>Orbit: five FFT-reactive decks specified cell by cell in the manifests.<br>[`beta/compositions/`](beta/compositions) |
| <a href="gallery/README.md#res-react-lexicon"><img src="gallery/lexicon/hero.jpg" alt="Res React Lexicon" width="320"></a> | **Res React Lexicon** · beta<br>The controller as a sentence machine: five pad rows are the five slots of a sentence, 512 grammatical sentences.<br>[`beta/lexicon/`](beta/lexicon) |
| <a href="gallery/README.md#res-react-lexicon-ii---eighties-ism"><img src="gallery/lexicon-ii/hero.jpg" alt="Res React Lexicon II - Eighties-ism" width="320"></a> | **Res React Lexicon II - Eighties-ism** · beta<br>The sequel: 200 pads of found broadcast-age text across five decks.<br>[`beta/lexicon-ii/`](beta/lexicon-ii) |
| <a href="gallery/README.md#res-react-test-card"><img src="gallery/testcard/hero.jpg" alt="Res React Test Card" width="320"></a> | **Res React Test Card** · beta<br>Pure signal: every pad a typographic test pattern, all of them moving under live WaveWarp.<br>[`beta/testcard/`](beta/testcard) |
| <a href="gallery/README.md#res-react-nisei"><img src="gallery/nisei/hero.jpg" alt="Res React Nisei" width="320"></a> | **Res React Nisei** · beta<br>Archival testimony, poetry, documents and places from the Japanese American experience, for Nisei Week.<br>[`beta/nisei/`](beta/nisei) |
| *no frame: its two 27-minute video masters live outside the repo and were not on this machine, so Avenue showed black* | **EarthSearch EP01 Live Mix** · beta<br>Not a clip launcher: two 27-minute masters that never stop, and a surface that shapes them.<br>[`beta/earthsearch/`](beta/earthsearch) |
| <a href="gallery/README.md#dead-air---listening-posts"><img src="gallery/dead-air/hero.jpg" alt="Dead Air - Listening Posts" width="320"></a> | **Dead Air - Listening Posts** · beta<br>Five rooms where someone is listening to the dark, and the dark, occasionally, replies.<br>[`beta/dead-air/`](beta/dead-air) |
| <a href="gallery/README.md#dew-line---the-spinningwork"><img src="gallery/dew-line/hero.jpg" alt="Dew Line - The Spinningwork" width="320"></a> | **Dew Line - The Spinningwork** · beta<br>A spider builds an early-warning station out of silk and casts her shadow on every star the net catches.<br>[`beta/dew-line/`](beta/dew-line) |
| <a href="gallery/README.md#the-library-and-the-hand---gusto"><img src="gallery/library-hand/hero.jpg" alt="The Library And The Hand - GUSTO" width="320"></a> | **The Library And The Hand - GUSTO** · beta<br>GUSTO, a proposed robot that fetches, flips, mixes and scratches real vinyl; stylus-cyan is documented, cue-orange proposed.<br>[`beta/library-hand/`](beta/library-hand) |
| <a href="gallery/README.md#studio-one---war-of-the-worlds-1938"><img src="gallery/studio-one/hero.jpg" alt="Studio One - War Of The Worlds 1938" width="320"></a> | **Studio One - War Of The Worlds 1938** · beta<br>For the broadcast's 88th anniversary: CBS Studio One, Grovers Mill, the Visitors, New York, the Morning After.<br>[`beta/studio-one/`](beta/studio-one) |
| <a href="gallery/README.md#signal-lost---transmission-from-tomorrow"><img src="gallery/signal-lost/hero.jpg" alt="Signal Lost - Transmission From Tomorrow" width="320"></a> | **Signal Lost - Transmission From Tomorrow** · beta<br>The OldTimeRadio pipeline as a show, including a VJ journey through the workflow one node per scene.<br>[`beta/signal-lost/`](beta/signal-lost) |
| <a href="gallery/README.md#the-manual---avenue-7281"><img src="gallery/the-manual/hero.jpg" alt="The Manual - Avenue 7.28.1" width="320"></a> | **The Manual - Avenue 7.28.1** · beta<br>A composition about Resolume itself: the vocabulary, the clip, parameter animation, the 62 blend modes, this rig.<br>[`beta/the-manual/`](beta/the-manual) |
| <a href="gallery/README.md#the-surface---apc40-mkii--midi"><img src="gallery/the-surface/hero.jpg" alt="The Surface - APC40 mkII + MIDI" width="320"></a> | **The Surface - APC40 mkII + MIDI** · beta<br>The controller every pack here is played on, drawn as schematics, every number from Akai's protocol document.<br>[`beta/the-surface/`](beta/the-surface) |
| <a href="gallery/README.md#the-mixers---v-4-mxpro-mx-1--jvc"><img src="gallery/the-mixers/hero.jpg" alt="The Mixers - V-4, MXPro, MX-1 + JVC" width="320"></a> | **The Mixers - V-4, MXPro, MX-1 + JVC** · beta<br>Three video mixers (Edirol V-4, Videonics MXPro, MX-1), a JVC S-VHS deck beside a pro edit controller, and the APC40 itself; LEFT and RIGHT walk the six decks.<br>[`beta/the-mixers/`](beta/the-mixers) |

<!-- gallery:end -->

## What this is

Four things, in Resolume's own terms:

1. **A verified controller visual twin.** `APC40_Visual_QA_148.avc` mirrors
   every physical control without external media. Its matching preset makes
   buttons toggle, faders travel, knobs rotate, and hardware LEDs follow the
   APC40 mkII's actual color capabilities.
2. **The Electric Zentropa performance suites.** A gorgeous, ready-to-play interface built entirely from native Resolume sources. Choose between **Lost Buttons** for bulletproof on-screen UI reliability, or **True Button Toggles** to bring the controller's physical grid to life with full RGB LED colors.
3. **Experimental performance instruments.** The earlier audio-reactive and
   Orbit compositions, their controller presets, FFT manifests, and custom
   FFGL plugins remain available under `beta/` and the supporting folders.
   They are useful building material, but their controller pairings are not
   part of the verified stable release.
4. **The prompts and protocols that made both.** Nine copy-paste prompts
   so an agent does the same against YOUR composition and YOUR hardware,
   plus the crash-tested rules for letting an agent drive Avenue at all.

No external clip files are required by the stable visual twin.

## Repo tree

```
apc40mkii-kit/
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
  compositions/ APC40_Visual_QA_148.avc - verified 148-control APC40 twin
  controllers/  APC 40 MK II - Visual QA.xml - verified 203-shortcut preset
  beta/         older audio-reactive + Orbit compositions and controller presets
                lexicon/ - the wordplay instrument: 40 pads = 40 words (untested)
  docs/         CONTROL_LOGIC.md          - THE control law: safety rails + knob design
                CONTROLLER_VISUAL_TWIN_PLAYBOOK.md - reusable build guide + lessons learned
                APC40_Standard_Layout.md  - beta performance-layout design
                APC40_Control_Map.xlsx    - beta performance map + provenance
                APC40_Standard_Layout.png - one-page readable layout picture
                fft-recipe-card.md        - the wiring convention and why it feels alive
                stability-protocol.md     - how not to crash Avenue while an agent drives
                orbit-placards.md         - the science, scene by scene, read-aloud ready
  LICENSE       MIT
```

## Just want to play? -> [INSTALL.md](INSTALL.md)

One page, four copy-paste steps: composition, plugins, controller preset,
audio. No AI, no coding, ~10 minutes to a lit grid.

## Installing the APC40 mkII shortcuts (never done this before? read this)

The preset is just an XML file you copy into one folder, then pick from a
menu. Step by step:

1. Download `controllers/APC 40 MK II - Visual QA.xml`.
2. Close Resolume if it is running.
3. Open File Explorer (Finder on Mac) and go to your Documents folder,
   then into `Resolume Avenue` > `Shortcuts` > `MIDI`. Notes: if you run
   Arena the folder says `Resolume Arena`; if Windows keeps your Documents
   in OneDrive, it is OneDrive's Documents folder; if `Shortcuts\MIDI`
   does not exist yet, start Resolume once, press Ctrl+M then Escape, and
   the folder appears.
4. Copy the XML file into that `MIDI` folder. That is the whole install.
5. Plug in the APC40 mkII BEFORE starting Resolume, then start Resolume
   and open `compositions/APC40_Visual_QA_148.avc`.
6. In Resolume: Avenue (or Arena) menu > Preferences > MIDI. You will see
   "APC40 mkII" listed as a device. Turn it ON as an input AND as an
   output - both checkboxes. Output is what makes the pads light up.
7. Still in that MIDI preferences panel, choose
   `APC 40 MK II - Visual QA`.
8. Close Preferences and trigger column 1 once if the labels are dark.
   Buttons toggle their matching witnesses; faders move vertically; knobs
   rotate; the crossfader moves horizontally.

If something misbehaves: no lights means output was not enabled (step 6);
wrong clips launching means another app (like Ableton) grabbed the
controller first - close it and power-cycle the APC; the preset missing
from the dropdown means the XML landed in the wrong folder (step 3).
Full troubleshooting: `controllers/INSTALL.md`. The stable control inventory
is in `docs/APC40_Visual_QA_Control_Map.xlsx` and
`docs/APC40_native_addresses.md`.

## Never coded? Start here (the from-zero path)

You do not need to program anything. You type sentences; the agent does the
clicking. Five installs-and-pastes:

1. **Resolume Avenue or Arena 7** - resolume.com (the trial works; it
   watermarks output but everything in this kit functions).
2. **Claude** - either the Claude desktop app (Cowork mode) or Claude Code
   (the terminal version) from claude.com. If a terminal scares you, use
   the desktop app - same brain.
3. **The official Resolume Arena/Avenue and Wire MCP servers** - these
   adapters ship with Resolume 7.26+ and let Claude see and drive Resolume.
   In Claude Desktop, open Settings > Extensions > Advanced settings >
   Install Extension, then choose the bundled
   `resolume_arena_mcp_server.mcpb` (Arena/Avenue) and, if you use Wire,
   `resolume_wire_mcp_server.mcpb` from the program's `mcp` folder. On
   macOS, you can double-click the same `.mcpb` bundles. Follow
   [Resolume's official MCP setup guide](https://resolume.com/support/en/mcp-servers)
   for the exact file locations. One-time setup, roughly ten minutes.
4. Start Resolume with any composition open, even an empty one.
5. Open `prompts/01-first-contact.md` from this kit, copy everything below
   the line, paste it to Claude, and watch it read your rig out loud.
   That is the whole skill. Every other prompt works exactly the same way:
   open file, copy, paste. The agent will ask before it saves anything.

## Quickstart (10 minutes to first light, if you are already set up)

1. Connect your agent to a Resolume MCP; open any comp in Avenue/Arena 7.
2. Run `prompts/01-first-contact.md`. If the reads match your screen, go.
3. Or skip the agent entirely: open
   `compositions/APC40_Visual_QA_148.avc`.
4. Install `controllers/APC 40 MK II - Visual QA.xml`; enable the APC40
   mkII as input AND output; select that preset.
5. Trigger column 1 if needed, then touch the hardware and watch the twin.

## Who this is for

VJs and tinkerers who want a controller twin without hand-building 148
layers and 203 shortcuts. The verified composition and preset work with
zero AI involved; the prompts document how to repeat the method.

## Beta performance experiments

Three Pulse cells reference sources that are not stock Avenue: Fable Pulsar
(a custom FFGL source - CP1919 pulsar ridgelines, stateless, 7 scalar
params) and two Wire patches (Golden Flicker Reel, Geometry Pattern Maker).
Every such cell is marked `custom_source` with a native `fallback` - the set
plays without them. The audio-reactive and Orbit `.avc` files and their controller
presets are retained under `beta/`; they are not claimed as end-to-end
controller-verified builds. Prompt 06 documents the plugin build path.

### Coming next: Res React Lexicon — the controller as a sentence machine

What if every pad were a word?

`beta/lexicon/` turns the whole APC40 mkII into a typographic instrument. The five pad
rows are the five slots of a sentence, stacked in the same order they appear on screen,
so the grid reads like the output:

```
THE ARCHIVE          <- top pad row     Subject
MISREADS             <-                 Verb
A BORROWED NAME      <-                 Object
::                   <-                 Mark
— — — — — — — —      <- bottom pad row  Field
```

8 subjects x 8 verbs x 8 objects = **512 grammatical sentences**, x 8 marks, over 8
typographic grounds. Every combination parses. Track Select fires a whole sentence; the
scene buttons drop a single grammar slot out of it; the faders are how present each slot
is. Every one of the 40 pads carries its own eight dials, and dial 1 runs Text Block Size
across 0.5-10 — a small turn takes one word from a line of text to the entire screen.
Field rides the bass and Mark rides the highs, while the three word rows stay deliberately
static, because the sentence has to stay readable.

It is **100% native Text Block**. Zero video files, zero FFGL, zero Wire, nothing to
install — 5 layers, 8 columns, 40 clips, 98 shortcuts, one composition that opens anywhere.

**Not verified yet.** It was built and played through the API on Avenue 7.27.1, but the
hardware has not been in the loop — no pad physically pressed, no LED colour confirmed on
the unit. The first-test checklist is in
[`beta/lexicon/README.md`](beta/lexicon/README.md). It stays in `beta/` until it survives
a real set.

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

## Build a controller visual twin

Start with the
[controller visual-twin playbook](docs/CONTROLLER_VISUAL_TWIN_PLAYBOOK.md).
It turns the APC40 build's failures and fixes into a reusable workflow for any
controller: inventory, manifests, specimen-first XML, a small hardware pilot,
live calibration, extreme-state QA, process hygiene, and rollback. Then give
the [any-controller execution prompt](docs/ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md)
to an agent.

Choose the product deliberately: the beta 91-shortcut performance design
launches and controls a show; the stable 148-control, 203-shortcut Visual QA
preset mirrors the physical surface for diagnosis. A visual twin may
intentionally fan one raw CC into wake, opacity, and motion records. That is
not a duplicate mapping bug, and it does not replace the stricter
performance-preset rules in [Control Logic](docs/CONTROL_LOGIC.md).

The APC40 mkII reference set is the
[ready-to-open composition](compositions/APC40_Visual_QA_148.avc), the
[accepted MIDI preset](controllers/APC%2040%20MK%20II%20-%20Visual%20QA.xml),
the [control-map workbook](docs/APC40_Visual_QA_Control_Map.xlsx), and the
[native address map](docs/APC40_native_addresses.md).

![APC40 mkII visual twin](docs/APC40_Visual_Twin.png)

Open the `.avc`, install the matching XML, enable the APC40 mkII as both MIDI
input and output, and select `APC 40 MK II - Visual QA`. The composition has
148 native Text Animator clips, one per physical control, and no external
media dependencies.

## Safety, support, license

The stability protocol in `docs/` is not optional reading - every rule in it
was paid for with a real crash. Saves always require the human's explicit
confirmation; the prompts are written that way on purpose.

As-is, PRs welcome, no support promised. Kit text, manifests, prompts:
MIT (see LICENSE). Placard facts carry their citations inline - corrections
are the most welcome PR of all.


## Electric Zentropa

In the stable release folders (`compositions/` and `controllers/`), you will find two matched editions of the Electric Zentropa UI:

1. **Lost Buttons** (`APC40MKII_Electric_Zentropa_Lost_Buttons`)
   This edition maps all physical Note buttons to `connectnextclip` for rock-solid on-screen UI reliability, intentionally sacrificing physical button LED toggle states in exchange for bulletproof performance. 

2. **True Button Toggles** (`APC40MKII_Electric_Zentropa_True_Button_Toggles`)
   This edition retains Resolume's native toggle mapping. It features the fully engineered LED feedback with precise colors matching the on-screen grid, at the cost of potential desyncs with the on-screen UI during heavy usage.

In both editions, all Continuous Controllers (Faders and Knobs) retain their pristine absolute/relative behaviors.

![Electric Zentropa performance interface](docs/Electric_Zentropa_Interface.png)
![Electric Zentropa animated controller mapping](docs/Electric_Zentropa_Animated_Mapping.jpg)

### Electric Zentropa in Motion

These compressed 720p H.264 demos retain their AAC stereo audio, so you can
see and hear the controller surface react in performance.

**Demo 1 - Performance interface**

https://github.com/user-attachments/assets/ee7890c9-cb91-4c9e-bf00-fe257dc55bb1

**Demo 2 - Animated mapping**

https://github.com/user-attachments/assets/a11cd356-343e-4407-bb1f-489c4fece759

**Demo 3 - Full controller response**

https://github.com/user-attachments/assets/cd932d0e-1d80-4dd5-ad71-44f53244eb99

### Installing the Presets

Each edition is an identically named `.avc` + `.xml` pair. Copy the XML from `controllers/` into the Resolume Avenue `Shortcuts/MIDI` folder, restart Avenue so it registers the preset, and then open the matching `.avc` composition. Enable the APC40 mkII as both MIDI input and output, and select the corresponding preset from the shortcuts dropdown.

## Dedication

Electric Zentropa was finished on 20 July 2026 - **Nam June Paik's birthday** -
and is dedicated to his memory. Paik taught the machine to sing; this project
tries, in a small way, to let the controller listen back.
백남준 선생님을 기리며 (In memory of Nam June Paik).
