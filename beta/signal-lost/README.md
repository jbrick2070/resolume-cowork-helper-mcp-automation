# Signal Lost

*Good evening. This is SIGNAL LOST.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 831 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `Signal Lost - Transmission From Tomorrow.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - Signal Lost.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. Sign-On** (radio) - A cathedral radio warming up in a dark room: cold filaments, then the dial lamp, the band of kilocycle ticks, the needle hunting and locking on 1230, the magic-eye tube closing on a strong signal. Tonight's headline comes off the RSS feed and seeds the script; the theme swells; the ON AIR lamp lights; and the announcer says the only line every episode shares. Midnight bakelite, dial amber, cream paper, magic-eye green, one red lamp.

Scenes: Warm Up -> Tuning -> Lock -> Tonight's News -> Theme -> Good Evening -> Act One -> Station Break

**2. Writers Room** (pipeline) - The script's birth, node by node: OTR_LedgerScriptWriter takes a premise, characters, a plot and a setting and writes the play; the parser pulls [SFX:] [MUSIC:] [BEAT] [PAUSE] [ACT] out of the text; OTR_LedgerFreezeCascade normalizes it for speech and audits visual coverage; then the ledger locks and the script becomes the source of truth for every later node. Nodes are amber boxes on ruled cream paper, wired; the locked ledger turns magic-eye green.

Scenes: Premise -> Characters -> Plot -> Setting -> Cue Markup -> Beat -> Freeze Cascade -> Ledger Locked

**3. The Cast** (voices) - Who speaks, and in what tongue. OTR_CastLock binds a Kokoro voice to each name for the whole episode; the announcer gets the ring and the ON AIR lamp; eight languages are eight bands under one switch; the voice pool is a field of soft discs with two lit. Dialogue is two sines in exchange, green and amber, never overlapping. Captions are burned in Bahnschrift over a dark bar and mirror the written line. It ends on the credit roll: written, cast, performed, scored, drawn, cut, on one machine.

Scenes: Cast Lock -> Kokoro -> Announcer -> Eight Languages -> Voice Pool -> Dialogue -> Captions -> Credit Roll

**4. The Graph** (pipeline) - A VJ journey through otr_canonical.json, one node per scene in signal order: ScriptWriter, FreezeCascade, CastLock, Voices, SceneSequencer, Assembler, RenderBatch, MasterAudioMux. Each column is one rounded node on the canvas grid with its real input sockets stacked green down the left edge and its outputs amber down the right, and a wire leaving right toward the next. Until the voices node the wire carries only JSON, a thin line; from there it carries audio and the SCOPE becomes a waveform. The last node is green: the .mp4.

Scenes: ScriptWriter -> FreezeCascade -> CastLock -> Voices -> SceneSequencer -> Assembler -> RenderBatch -> MasterAudioMux

**5. Shivering Gauge** (wildcard) - The episode itself, drawn as the pack draws everything: a film archivist and an apprentice racing vinegar syndrome through one night in the lab. Storybook-engraving hatching, four developing tanks, two reels, and a gauge whose red needle sits past the line and shivers on the highs. Safelight amber, acetate haze, first light under the door, and the sign-off: this has been SIGNAL LOST. Good night.

Scenes: Lab After Hours -> Developing Tanks -> The Gauge -> Vinegar -> Reel By Reel -> Shivering -> Dawn -> Sign-Off

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

Radio is sound made visible, so the composition's reactivity is the program line and the voices. Mids drive the SCOPE (VU line or waveform) 1:1 and the magic eye's fan; lows drive only size and width - dial lines, node boxes, timeline blocks, filament size - so a kick is pressure on the chassis; highs shiver the band ticks, the hatching and, once, the gauge face. Colour never reacts: amber is work, green is signal and master, cream is paper, red is the ON AIR lamp and the gauge needle and nothing else. Text never moves. [BEAT] and the 48 kHz Master are deliberately still: the picture holds while the sound does the work. Everywhere else the room never stops: a texture on its own clock under every deck, the lows push the figures a little, the highs shiver the scope, and the captions stay put.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
