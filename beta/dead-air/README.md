# Dead Air

*Five rooms where someone is listening to the dark, and the dark, occasionally, replies.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 645 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `Dead Air Listening Posts.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - Dead Air.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. Hydrogen Line** (space) - The night shift at a listening post, 1967 to 1995 but always three in the morning: a hut, a chart recorder drawing ninety-six feet of paper a day, a P1 phosphor tube, and a sky that is pure hiss at 2.725 kelvin until it is not. The light is sensor-bias grey, buff paper and one pen lamp; chart-paper white is the only thing allowed to glow, and hydrogen-alpha red arrives once, for seventy-two seconds. The wonder is clerical: a quarter-inch of scruff that repeats every 1.337 seconds, WOW! in a margin, three thousand galaxies developing on a plate; the dread is that the pulse is too regular to be natural. Register: teletype telemetry in OCR A Extended, bottom-left and never centred, right ascension and declination, LISTENING, NOT SENDING.

Scenes: Dark Run -> Scruff -> Chart Recorder -> CP 1919 -> Wow Signal -> Deep Field -> No Carrier -> Dawn Chorus

**2. Loss Of Signal** (fusion) - Mission Control's voice loop at the moment the spacecraft goes behind the Moon: LOS, forty-five minutes of dead air, and the whistling the Apollo 10 crew heard on the far side and nearly did not report. The room is console grey, P39 phosphor green and one amber tally lamp; everything else is the dark the carrier left behind, and in this room the scope is the picture, full width along the lower third. The dread is that the loop keeps counting into silence and the voice that eventually answers may not be on the roster; the wonder is AOS, the sunrise that comes back on schedule as one long white flash. Period register is 1969 Houston in Consolas: teletype paper, capcom cadence, left-justified, hiss at 2.2 kHz.

Scenes: Go For TLI -> The Loop -> LOS In Ten -> Dead Air -> Whistling -> Alarm 1202 -> Acquisition -> Splashdown

**3. The Sitters** (halloween) - A Victorian parlour seance by one candle, run to a strict protocol: lamp down, hands joined, knock once for yes, never break the circle. The light is a single flame that a moth keeps crossing, and everything it does not reach is the brown of a daguerreotype; one cold blue opens in the north-west corner when something answers. The dread is procedural: the table tilts at 11:47, the trumpet lifts, the glass spells L-E-A-V-E, and the wax cylinder plays back a name nobody gave it. Period register is 1872 Hackney in Baskerville Old Face with a 1971 overdub in Lucida Sans Typewriter: Raudive's Class A voices under the hiss, Ouija letters spaced across the board.

Scenes: Lights Down -> Join Hands -> Knock Once -> The Table -> Moth To Lamp -> Trumpet Lifts -> Class A -> Break Circle

**4. Hour Of Saturn** (halloween) - A grimoire read under Giallo light in a Rome print lab, 1977: the circle drawn in chalk, the planetary hour struck, the lamp swapped for a red gel and then a blue one, the way a corridor in Suspiria or a Hammer crypt is lit from the wrong side. The body of the world is geometry, the three-by-three square of Saturn in verdigris and rings that contract, which assembles and then breaks; the gels cut, they never crossfade. The dread is formal: the ritual is a recipe and the recipe is working. Period register is the Key of Solomon in Engravers MT with Italian intertitles in Bodoni MT caps tracked wide (PRIMO TEMPO, NON APRIRE, FINE) and a Carpenter pulse underneath.

Scenes: Chalk Circle -> Hour Struck -> First Seal -> Red Gel -> Blue Gel -> Conjuration -> The Lamp Goes -> Licence To Go

**5. German Bight** (wildcard) - The 0048 shipping forecast after Sailing By: a voice reading sea areas into the dark on 198 kHz long wave for people who may or may not be out there. It is the North Sea at night as a wireframe swell under a lighthouse with a published character, Fl(2) W 10s, two flashes every ten seconds, and a grey that is almost blue with port red and starboard green at the edges. The wonder is liturgical: Viking, North Utsire, Forties, a low losing its identity, and the gale warnings carry real dread without a single horror cue. Period register is BBC Radio 4 in Gill Sans MT, a Met Office card and a light list read in a flat voice, with the bridge radar the only green on board.

Scenes: Sailing By -> Gale Warnings -> Viking Utsire -> Dogger Fisher -> German Bight -> Lundy Fastnet -> Rockall Malin -> Fair Isle

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

Sub and low (20 to 120 Hz) through a fast-attack, 400 ms release envelope drive only amplitude-type parameters (Line Scape Height, React Pulsar Level, Metaballs Size, Sine Wave Amplitude, the BED gradient's breath) so a kick reads as a push or a tide and never as a flash; low-mids (120 to 500 Hz) through a 2-second envelope drive density and rotation (Abstract Field Density, Lines Fuzzyness, Rings and Spiral rotation), the slow structural breathing of the room; highs (6 to 16 kHz) touch GRAIN opacity and the Golden Flicker Reel's ember dots only, so hi-hats become hiss and moth dust and nothing else. One long RMS envelope over several seconds drives AURA opacity and the Vignette size so builds open the room and breakdowns close it; that is the only macro the music gets. Onsets are triggers, not levels: one Stroboscope flash, one candle gutter, one glitch frame, quantised to the beat and rate-limited to once per bar, and most of them are fired by hand on a pad rather than by a threshold, because the performer is the medium and a knock that answers must be answered. These never react at all: TEXT position, scale, opacity or content (words are read, not shaken, and the mids-gate on text proposed by one runner-up is rejected); hue, blend mode, gel or AURA colour (colour is a decision the performer makes with a scene, the music only changes how much light is in the room, never what colour the room is); the BED's scale and position (the environment does not dance); the SCOPE's own gain (it is the honest readout and the one element allowed to follow the signal 1:1); and scene changes.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
