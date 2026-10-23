# The Surface

*Note 0 is bottom-left. Channel is track. Centre is everything.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 441 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `The Surface - APC40 mkII + MIDI.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - The Surface.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. The Grid** (hardware) - The 5x8 pad grid drawn on a matte black chassis: note 0 bottom-left, rows of eight, five rows for five layers, the 128-entry RGB velocity palette, the two LED families every pack here speaks (green 21/22, amber 9/10), the Scene Launch column, and the SysEx that puts the controller into Mode 1 - a show requirement, because a power cycle forgets it.

Scenes: Note Zero -> Row Of Eight -> Five Rows -> Velocity Palette -> Green 21 -> Amber 9 -> Scene Launch -> Mode 1

**2. The Strips** (hardware) - Eight track strips, each a copy of the last: the per-track buttons keep one note and change only the MIDI channel. Clip Stop 52 ejects, Select 51 selects, Activator 50 is on-air, Solo 49, Record Arm 48 and Crossfade A/B 66 are the first two effect banks in every pack here. Below them the eight faders on CC7, the master on CC14 and the crossfader on CC15 whose centre is everything.

Scenes: Channel = Track -> Clip Stop 52 -> Select 51 -> Activator 50 -> Rec Arm 48 -> A/B 66 -> Faders CC7 -> Crossfader CC15

**3. Knobs + Transport** (hardware) - The right-hand block and the top row: eight Device knobs with LED rings on CC16-23 (the dashboard links), eight Track knobs on CC48-55 (the live FFT), Cue Level on CC47 (the effects master sweep), the relative Tempo encoder on CC13, PLAY STOP RECORD on notes 91-93, Tap and Nudge, and the footswitch on CC64 that is a momentary blackout in every pack here.

Scenes: Device CC16-23 -> LED Rings -> Track CC48-55 -> Cue Level CC47 -> Tempo CC13 -> Play Stop Rec -> Tap + Nudge -> Footswitch CC64

**4. The Wire** (protocol) - MIDI itself, from the 1983 spec to tonight's preset: the DIN-5 with its 5 mA current loop, 31,250 baud and ten bits a byte, the status byte with its high bit set, note on and note off (Piano listens for the off), control change with 128 steps, the class-compliant USB that powers the whole surface, and the 2^56 (note) and 2^57 (CC) markers Resolume files a raw message under. Red is the wire; green is a message arriving.

Scenes: DIN-5 -> 31,250 Baud -> Status Byte -> Note On / Off -> Control Change -> USB-B -> Resolume Key -> Monitor

**5. SE-500 Mixer** (wildcard) - A four-input analog SD video mixer drawn in the same chassis grammar: BNC composite and S-Video inputs with illuminated select buttons, a main and a sub source bus, the T-bar you pull at your own speed, wipes, picture-in-picture, split screen, colour processing, and - the reason it belongs in this pack - RS-232 on a 9-pin D-sub and MIDI control on a five-pin DIN: the APC40's language on the older wire (the APC itself is USB-only).

Scenes: Four Inputs -> Main / Sub -> T-Bar -> Wipe -> PIP -> Split Screen -> Colour Proc -> MIDI + RS-232

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

The controller is the subject and the music is what it controls, so the reactivity stays mechanical: lows swell pads and widen fader caps, mids turn knob gaps and move playheads and T-bars, highs only jitter the serial bits and the DIN pins. Colour never reacts: green is a lit pad or a message arriving, amber is the second LED family and the T-bar, red is the wire and nothing else. Text never moves. Every note, CC and byte on screen is the real one.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
