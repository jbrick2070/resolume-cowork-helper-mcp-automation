# Dew Line

*A spider builds an early-warning station out of silk, takes her own scaffold down before dawn, and casts her shadow on every star the net catches.*

A procedural live instrument for **Resolume Avenue 7.28.1** and an **Akai APC40 mkII**. Every one of its 320 clips is a stock Resolume generator with hand-set parameters - no media files, no third-party plugins - and 684 of its parameters listen to the music through Resolume's external FFT.

| | |
|---|---|
| `Dew Line - The Spinningwork.avc` | the composition: 5 decks x 8 layers x 8 scenes |
| `APC 40 MK II - Dew Line.xml` | the APC40 mkII preset - every control has a job |
| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |
| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |
| `docs/DECKS.md` | the five worlds, scene by scene |
| `BUILD_REPORT.txt` | what the builder repaired, if anything |

## The five worlds

**1. Orb Plate 1889** (the web as geometry) - An orb web built from nothing between two hedge stems before sunrise, drawn the way Henry McCook engraved it in 1889 and stamped the way a 1962 drawing office would stamp it: bone thread on slate, every radius numbered, a title block bottom-left that says DO NOT SCALE. The light is the grey half-hour before the sun finds the dew. The wonder is procedural: one animal, one line, forty minutes, a structure whose scaffold she eats as she lays the capture spiral and whose finished work she eats at dawn so the protein can be spun again. Register: Victorian plate engraving, drafting-office revision letters, specimen not taken.

Scenes: Bridge Line -> Y Frame -> Thirty Radii -> The Hub -> Dry Spiral -> Capture Spiral -> Dew Load -> Eaten at Dawn

**2. Sit and Wait** (the hunt, read by vibration) - A funnel web in long grass at three in the morning, seen from inside the funnel: the silk sheet is a drumskin and the spider is downstairs in the retreat, reading it through slits in her legs. A sodium streetlamp on a timer is the only light from above; nothing moves until something lands, and then bearing, amplitude, decision, rush. The dread is that stillness is the trap and she can wait twelve days; the wonder is that she tells wind from rain from prey by frequency alone. Register: 1970s nocturnal field biology, a seismograph pen on a paper drum, the darkest deck of the five.

Scenes: Funnel Mouth -> Twelve Days -> First Tremor -> Triangulate -> Pluck the Line -> The Rush -> Swathe -> The Husk

**3. Arachne's Loom** (the weavers' myth) - Two weavers who became the stories they told, shown at closing time in a museum: Arachne, Idmon's daughter of Lydia, who wove the gods' crimes without a flaw and was struck with the shuttle, hanged, and told to live; and Kwaku Ananse, who paid the sky god Nyame four captures for every story in the world and keeps them in his web. The light is gallery halogen on bronze and gilt thread on wine-dark warp, with the title card of a BBC Schools 'Myth and Legend' broadcast on 16mm. The dread is the verdict, one madder strobe and a torn cloth; the wonder is the cosmogram, a Rings web whose nodes are stories and whose sweep lights them one at a time. Everything is weave: Checkered is warp and weft, the Pattern Maker is the tapestry, the spider is the shape left when the woman is subtracted, and the tab switch into this deck is a change of century.

Scenes: Warp and Weft -> Gods' Crimes -> Shuttle Thrown -> The Verdict -> Hang Forever -> Nyame's Price -> Story Nodes -> Ananse Web

**4. Goose Summer** (the nursery and the ballooning) - Inside the egg sac is the quietest room in the world: three hundred eggs in wound silk, lit through from outside like a lamp through linen, with the mother on the outside not eating and not leaving, and in some species the first meal. Then the moult, where a spider leaves an exact ghost of herself and walks out soft; then the spiderlings on tiptoe at the top of a fence post, abdomens to the wind, throwing a line into the sky's electric field and letting go. Darwin found the Beagle's rigging coated in their silk sixty miles from land, and Middle English called the stuff gossamer, goose summer. The light is milk and amber on the only light ground in the instrument, 16mm natural history circa 1979, microscope-close and heavy with grain; the register is a naturalist's tenderness in lower case, and this is the deck you switch to when the room needs to breathe.

Scenes: Egg Sac -> Three Hundred -> The Gift -> Moult -> Ecdysis -> Tiptoe -> Balloon -> Beagle Rigging

**5. Dew Line Station** (silk as signal) - A Cold War early-warning radar station whose antenna sweep leaves an orb web as its trace: the DEW Line of 1957 and dew on a web at dawn are the same picture, a net strung across the dark that catches light so you can see what is coming. The dome is a telescope too, and every telescope already contains a spider: the four vanes that hold the secondary mirror cast a cross on every bright star, and surveyors once strung their reticles with a single strand of silk. Louise Bourgeois' Maman stands over the dance floor, nine metres of steel seen from underneath with marble eggs held in the sac; Arabella spun in Skylab in 1973; CP1919 ticks every 1.337 seconds and was not a signal, it was a clock. The light is P7 phosphor, signal white and tape-reel amber on blue-black, 1981 regional continuity with no warmth at all, and the deck ends in a legitimate black, a test card, and a stop.

Scenes: Carrier -> Sweep -> Silk Crosshair -> Maman -> Eight O'Clock -> Net of Light -> Blackout -> Sign Off

## How it plays

* **Decks are worlds.** LEFT / RIGHT walk the five deck tabs.
* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / DOWN walk all eight. A scene fires all eight layers at once, composed as one picture.
* **Pads are the five playable layers.** Bottom row = BED, then BODY, FIGURE, LIGHT, TEXT. Mix any pad with any other; the three non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.
* **The crossfader** is environment <-> figures: hard left shows only BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre is everything. Rig-measured, not assumed.
* **The rack** is 30 stock effects in four banks on the button rows (RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.
* **FFT** lives on the Track Control knobs: depth and release for the low, mid and high anchors, SCOPE depth, and TIME (composition speed 0-2x) on knob 8.

## FFT philosophy

Lows (kick, 40-120 Hz) drive structural tension only - Suckr strength, Rings Size and Spacing contracting a few percent, Trails length, Sine Wave Modulation Depth - through an envelope follower with fast attack and a 300-600 ms release, so the web tightens on the kick and relaxes between hits like a load on a structure rather than a flash. Mids (200 Hz-2 kHz) drive the slow motion rates (Spiral Speed, Line Scape Wobble, Abstract Field drift, Metaballs Speed) so a busy mix makes the world breathe faster but never flicker, and highs (6 kHz up) drive the silk alone - Fuzzyness, Displace amount, Bloom and dew brightness - in ranges small enough that silk shivers and never tears. Nothing ever reacts on TEXT (words must be readable on a wall at 2am), nothing moves the FIGURE's position (the spider decides where she is), hue never reacts anywhere, nothing on AURA reacts, column transitions never react, the rotation of any orb never reacts (a web does not spin to a beat), the Radar sweep period never reacts because it is the clock, and strobe frequency is not a signal path at all - every flash is a Stroboscope pad under a finger. The SCOPE layer alone takes the raw unsmoothed spectrum, precisely so that everything else can afford to be slow. Reactivity is a musician's hand on a fader, not a VU meter: smoothed, thresholded, and deliberately missing the obvious beat half the time.

## Built from the running application

Every source, effect, parameter name, range, choice and blend-mode id in this pack was harvested from Avenue 7.28.1 itself through its REST API (`harvest/`), and the composition was opened on the rig and every parameter read back before it shipped. Shape Shifter 3D is excluded: it crashed Avenue on save, twice.
