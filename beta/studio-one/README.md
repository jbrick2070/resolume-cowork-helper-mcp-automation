# Studio One

*Everyone forgets. The record doesn't.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 711 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `Studio One - War Of The Worlds 1938.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - Studio One.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. Studio One** (studio) - CBS Studio One, fourth floor, 485 Madison Avenue, 8:00 pm, Sunday 30 October 1938: a windowless, double-height room of microphones, music stands and a foley table that looks like a machine shop. Silver-gelatin newsreel light - charcoal blacks, ivory highlights, soft halation round the practical lamps - and one amber, the glow of the board behind the glass. The RCA 44-BX is the hero object, a chrome diamond that hears front and back and nothing at its sides. Typed copy in Courier, the network's serif for the opening.

Scenes: 8 PM Air -> Roll It -> Facing Mics -> Foley Table -> Giant Cube -> Orchestra -> The Glass -> Dead Air

**2. Grovers Mill** (account) - The accounts, exactly as the soundtrack gives them: the observatory, the Wilmuth farm, the hum, the cap turning, the feelers in bad light, the heat ray from the mirror, the dead line, forty people. Every scene here is inside a reconstruction, so the optical soundtrack strip runs down the left edge. Night is charcoal-to-grey; the light is car headlights and one beam. The crowd is silhouettes; Phillips is never shown dead.

Scenes: Observatory -> The Farm -> The Hum -> The Cap -> Emergence -> Heat Ray -> Field Lost -> Forty Dead

**3. The Visitors** (takeover) - The r04 alternate history: the invasion is real, and two visitors with FCC credentials make the broadcasters call it theatre. They never speak, never hurry, never touch first; they knock while holding the keys. A black sedan at the curb, a brass revolving door, a card read with moving lips, a latch, a bare ridged hand on the board, and the red pencil. Red exists only on pencil marks: three clips in the whole composition.

Scenes: The Curb -> The Lobby -> The Card -> The Latch -> Gloves Off -> Red Line -> Station Break -> Clock Held

**4. New York** (account) - The second half's accounts: the battery in the Watchung Mountains, the bombers from Langham Field, the dive into the first machine, the roof of Broadcasting Building with smoke over the Hudson, fifty feet away, nineteen machines in Central Park with black birds wheeling, and the peaceful study. One column is not an account: The Window, the second proof - the avenue outside is wet, lit and untouched, so the strip gives way to the board's program line.

Scenes: The Battery -> Bombers -> The Dive -> The Roof -> Black Smoke -> The Window -> Nineteen -> Peaceful Study

**5. Morning After** (wildcard) - 9:00 pm and after: the heavy doors burst open on dark uniforms, the switchboard becomes a vast sea of light, flashbulbs at the morning press conference, and the front pages. Then the correction the century took to make: about two percent of the audience was listening, and the panic was printed, not broadcast. It ends on the disc in the rehearsal rack with a small circle on its sleeve, and next week's script already red-pencilled - the one other place red is allowed.

Scenes: 9 PM Doors -> Switchboard -> Flashbulbs -> Headlines -> Two Percent -> Hooper vs Myth -> The Disc -> Next Week

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

Sound is the whole subject, so the composition listens like the room did. The kick drives only physical size - the RCA 44-BX diamond, the cylinder's ribs, the heat ray's width, the headlights - so a hit reads as pressure on the ribbon. Mids drive the board's program line (SCOPE) and the cap turning; highs only shiver the ribbon and the crowd's edges. Nothing about colour ever reacts: charcoal, ivory, grey and one amber are fixed, and red appears only where a pencil drew it. Text never moves. Dead Air, the Silent Mic and the Clock Held are deliberately deaf: the stillness is the effect. Since the kinetic pass the room never stops: a texture on its own clock sits under every deck, the lows push the figures a little, the highs shiver the scope, and the captions stay put.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
