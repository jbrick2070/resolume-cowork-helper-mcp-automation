# The Manual

*Composition > Deck > Group > Layer > Clip. Click the cogwheel.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 786 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `The Manual - Avenue 7.28.1.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - The Manual.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. Vocabulary** (manual) - Basic Vocabulary, drawn: the composition framed in blue, the deck as a button under the grid, the layer strips with X B S and V A M, a group bracket, a clip's green thumbnail and its name handle, a column lit top to bottom, and the render order from source to output. Charcoal panels, grid lines, light-grey labels, Resolume blue for whatever is selected and green for whatever is playing.

Scenes: Composition -> Deck -> Layer -> Group -> Clip -> Column -> Source + FX -> Render Order

**2. The Clip** (manual) - The Clips chapter, one setting per scene: Trigger Style (Normal, Toggle, Piano), Beat Snap (1/4 Bar to 8 Bars), Clip Target (Own, Active, Free Layer), Resize (Fill, Fit, Stretch, Original), Fader Start, Ignore Column Trigger (the SCOPE layer in every pack uses it), Auto Pilot and the Transition (Layer Determined at the clip, Alpha at the layer). Every option name is the manual's.

Scenes: Trigger Style -> Beat Snap -> Clip Target -> Resize -> Fader Start -> Ignore Column -> Auto Pilot -> Transition

**3. Parameters** (manual) - Parameter Animation, the cogwheel's menu: Timeline with in and out points, BPM Sync in beats with Tap, Resync and Nudge, External FFT on this rig's CABLE Output with L M H bands, Gain and Fall, the Envelope's eight curves, the Dashboard's dials with In, Out, Invert and Dial Range, and Clip Position. This is the chapter every pack in this repo is built on.

Scenes: Cogwheel -> Timeline -> BPM Sync -> External FFT -> Gain + Fall -> Envelope -> Dashboard -> Clip Position

**4. Blend Modes** (manual) - Sixty-two blend modes harvested from this rig, grouped as the Blend Modes chapter groups them: General, Darken, Lighten, Contrast, Comparative, Composite and the Transitions, plus the ten '50' modes the harvest lists (the chapter documents only 50 Mask, under Composite). Each scene is two discs, A and B, overlapping, in the colours the mode would make of them. The pack itself uses Add on most layers, Screen on FIGURE, Alpha on TEXT and Overlay on AURA.

Scenes: Alpha -> Add + Screen -> Multiply + Burn -> Overlay -> Difference -> Luma Key -> 50 Mask -> Transitions

**5. This Rig** (wildcard) - The Nerds chapter as it is set on this machine: Audio input CABLE Output for the External FFT, the APC40 mkII as MIDI in and out so the pads light, the REST API on 8080 that read every clip of every pack back, OSC on 7000 and 7001, DMA Textures on Autodetect (the manual recommends Force ON), the Defaults (Add, Timeline, Loop), the harvest itself - 22 sources, 115 effects, 1,094 parameters, 62 blend modes off 7.28.1.26535 - and Shortcut mode, where the interface turns blue.

Scenes: Audio In -> MIDI -> Webserver -> OSC -> Video -> Defaults -> The Harvest -> Shortcut Mode

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

This pack is about the thing that makes it move, so the FFT is explicit. Deck 3 draws the spectrum, the L M H bands, Gain and Fall; Deck 5 draws the input device the whole repo depends on. Elsewhere the rule is the usual one: lows drive size and width (selection outlines, the playing cell, discs), mids drive playheads, dials and the spectrum, highs touch only the band in-point and dither. Colour never reacts: blue is selected, green is playing, amber is BPM, grey is everything else. Text never moves. Since the kinetic pass the room never stops: a texture on its own clock sits under every deck, the lows push the figures a little, the highs shiver the scope, and the captions stay put.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
