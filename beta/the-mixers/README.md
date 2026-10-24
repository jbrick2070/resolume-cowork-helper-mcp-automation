# The Mixers

*Three mixers, a VCR, an edit controller and the APC40. LEFT and RIGHT walk between them.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 384 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 816 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `The Mixers - V-4, MXPro, MX-1 + JVC.avc` | the composition: 6 decks x 8 layers x 8 scenes |
| `APC 40 MK II - The Mixers.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the six worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The six worlds

**1. APC40 mkII** (the controller) - The controller as an object before it is a protocol: the 424 x 254 x 46 mm chassis, 40 RGB pads with note 0 bottom-left, nine 45 mm faders, sixteen knobs with LED rings, the crossfader, the USB-B socket that also powers it, the three modes set by SysEx, and the two buttons this pack is walked with: LEFT and RIGHT, previous and next deck.

Scenes: The Object -> 40 Pads -> 9 Faders -> 16 Knobs -> Crossfader -> USB-B -> Three Modes -> On The Desk

**2. Edirol V-4** (beat sync) - Roland's 2002 four-channel mixer that VJs carried for a decade: four composite inputs, two frame synchronizers, an A and a B bus, a T-bar of over 100 steps, more than 200 wipes, eight effects, a TAP button and BPM SYNC that cut on the beat from MIDI clock, input select on MIDI notes, and no audio at all.

Scenes: The Box -> Four Inputs -> A / B Buses -> T-Bar -> Effects -> BPM Sync -> MIDI -> Output Fade

**3. Videonics MXPro** (the keypad) - The 1997 upgrade to the MX-1, built in Campbell, California: four inputs with audio, a CURRENT row and a NEXT row instead of A/B buses, 501 transitions in five categories including hearts, stars and keyholes, a keypad to type them by number, PLAY instead of the slack T-bar, input effects, a 16-image multi-PIP placed by joystick, and LEARN scripts of 250 steps.

Scenes: The Box -> Current / Next -> 501 -> Shapes -> Keypad + Play -> Input F/X -> Multi-PIP -> Learn

**4. Videonics MX-1** (the original) - The 1994 four-input mixer from Campbell, California that put a frame synchronizer, dual TBC, 210 numbered effects and a Take-bar on a desk for about a thousand dollars; the manual's own example is a nightclub, a music video on one input and a camera on the dance floor on the other.

Scenes: The Original -> Take-Bar -> Numbered -> Quad Preview -> Film Look -> Chroma Key -> Freeze -> The Club

**5. JVC S-VHS + Edit** (the tape) - Two JVC machines that never worked together: the 1999 HR-S7600U S-VHS deck, with its jog dial and shuttle ring on the front panel, DA-4 heads, digital TBC with 3-DNR and S-VHS ET; and the RM-G850E, a wired professional edit controller with a player dial, a recorder dial and a red PERFORM key, built to drive JVC's U-matic editing decks.

Scenes: The Deck -> Jog -> Shuttle -> Heads -> TBC + 3-DNR -> S-VHS ET -> RM-G850E -> Perform

**6. Patch Bay** (how they talk) - The deck that joins the others: a mixer's four inputs beside Resolume's eight layers, the T-bar beside the crossfader, a composite wire beside a USB cable, and the four verbs every box here shares: dissolve, wipe, key, freeze.

Scenes: Four Into Eight -> T-Bar / Crossfader -> Composite / USB -> Dissolve -> Wipe -> Key -> Freeze -> The Shared Words

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the six deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

The hardware is the subject and the music is what it plays, so the reactivity stays mechanical: lows push T-bars and turn the head drum, mids move wipe edges and the shuttle's scan, highs only jitter uncorrected tape lines and the MIDI pins. Since the kinetic pass the room never stops: every deck has a moving texture under it, pads drift, knobs turn with the mids, figures punch on the kick and leave trails, and light blooms with the lows. Colour never reacts. Captions never move. Every number on screen is from the sources in docs/.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
