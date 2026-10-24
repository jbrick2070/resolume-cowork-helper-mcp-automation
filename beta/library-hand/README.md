# The Library And The Hand

*The library has precedents. The hand still needs a test.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 747 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `The Library And The Hand - GUSTO.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - The Library And The Hand.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. The Plinths** (documented) - A long wireframe hall of glass-outline plinths, each holding a small machine that already exists: a domed cabinet, a chrome jukebox, an aluminium rail, two industrial arms, a servo on a fader. The camera dollies past them at 33 1/3 rpm with one stylus click per revolution. Everything documented is SOLID stylus-cyan; the one thing that does not exist, the whole machine, is a dashed orange booth that stops drawing itself halfway. Register: feasibility-study captions in Cascadia Mono, bottom-left.

Scenes: Cold Open -> Six Jobs -> Glenton 150 -> Rocket LP -> Maker Rail -> Juke Bots -> Scripted Shows -> DJ I Robot

**2. The Hand** (proposal) - The pressure is physical and the click runs at 45. One desk, one lamp, a hobby servo on a fader; then the seven-inch beside the twelve-inch at the same scale, the platter hatched heavy, I = 1/2 m r^2 in orange because it is a model. The proposed hand swings in over Deck A and hovers. Nothing in this deck has been measured: almost every figure is DASHED cue-orange, and the few cyan lines are a $247 subtotal and a builder's own words.

Scenes: Scratchbot -> Five Hour Clock -> Seven vs Twelve -> Inertia Gap -> Two Separations -> Circle Trap -> Millimetres -> Swing-In Hand

**3. The Catalog** (policy) - The middle zone, where a record waits under a ring light to be told what it is. Tags, cameras, an optional black-and-white marker; then the marker's cells become a grid of switches and the switches become a permission table. An AI assistant asks to scratch a play-only copy and the local controller refuses: a paper-white stamp held for one full click while the hand stays up. Beneath the floor, three layers and one clock; at the front, a mushroom stop. The click is back at 33 1/3.

Scenes: What Record -> NFC Tier -> Camera Tier -> ArUco Tier -> Who May Touch -> Refused -> Three Layers -> Interlocks

**4. The Ledger** (estimate) - What GUSTO must earn, in the order it must spend. A six-rung ladder with precedents on the cyan left and targets on the orange right; a ledger with three booths at three scales; a road of gates whose counters all read NOT RUN. Then the cold open comes back exactly, disc and hand and camera, and the viewer sees what was missing: the test. The hand lowers, freezes one frame before contact, the needle lifts, and the sources scroll in silence.

Scenes: The Ladder -> The Ledger -> Gate 1A -> Gate 1B -> Stage Two -> Stage Three -> Coda -> End Card

**5. SL-1210MKX** (wildcard) - The Technics SL-1210MKX (ADE, October 2026) drawn as schematics: the die-cast platter from above, the under-platter DIP switches, the new +-4 / +-50 % pitch slot, the silver S-tonearm at 22 degrees, the slipmat letting the record reverse above a forward platter. Internals not yet published for the MKX are labelled MK7 PLATFORM. Everything the manual documents is cyan; the one orange column is the scratch, because that is the job GUSTO has not yet earned. It ends in the run-out groove with the blemish the whole film's click was built from.

Scenes: 33 1/3 -> DIP Switches -> Pitch Fader -> S-Tonearm -> Slipmat -> 45 -> Reverse -> Lock Groove

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

The film has one sound, a stylus click once per revolution, so the composition's reactivity is built to read as rotation and never as a light show. Sub and low (kick) drive only width and size: the disc's line width, the ratio bars, the exclusion rings, the hand's scale, on a 300-500 ms release, so a kick is a push on the record. Mids drive the SCOPE 1:1 as ACTUAL RECORD ANGLE, the one honest readout, and breathe the hall's frequency and the confidence dot. Highs touch only ruling fuzz and hatching: hi-hats become jitter on clock ticks and scan lines. Nothing about colour ever reacts: cyan means documented and orange means proposed, and the music does not get to change what is true. Text never moves. The click itself is a Stroboscope held on the LIGHT layer at 33 1/3 or 45; it is a motif, not the beat. Since the kinetic pass the room never stops: a texture on its own clock sits under every deck, the lows push the figures a little, the highs shiver the scope, and the captions stay put.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
