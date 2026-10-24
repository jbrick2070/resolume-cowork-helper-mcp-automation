# One APC40 mkII, every composition

If you play more than one composition from this kit, the controls below do the same thing in
all of them. Learn them once.

Two kinds of composition are exempt on purpose: the controller twins and simulators (Visual QA,
Electric Zentropa, 145 Layers, AUTOTEST), which show the hardware button for button, and the
one-off live show EarthSearch EP01, whose arrow buttons are effect toggles.

## The standard

| control | does |
|---|---|
| **TEMPO knob** (CC13) | **FFT INPUT GAIN.** Avenue's global audio gain, the same knob in every composition. Turn it up when the picture is too calm for the room, down when it slams. Relative, so it never jumps. |
| **Track knob 8** | **TIME.** Composition speed, 0 to 2x with 1x at the centre (instrument packs). In the Lexicon family it is the selected clip's own Speed. |
| **CUE LEVEL knob** (CC47) | Instrument packs: **FX MASTER**, nudges all four effect banks together, anticlockwise toward the clean picture. Older packs: **TIME** (composition speed). Relative, so it never jumps. |
| **METRONOME** | FFT gain home: puts the gain back to the middle (instrument packs). |
| **TAP TEMPO** | TIME home: puts composition speed back to exactly 1x (instrument packs). |
| **UP / DOWN** | Next / previous scene (column). UP walks forward. |
| **RIGHT / LEFT** | Next / previous deck. |
| **PLAY** | Open the show: scene 1. Instrument packs also re-arm the scope. |
| **STOP** | Stop. Instrument packs clear the five pad layers and leave beds, grain and scope. |
| **STOP ALL CLIPS** | Eject everything. |
| **RECORD** | Blackout toggle. Press again to return. |
| **FOOTSWITCH** | Momentary blackout. |
| **MASTER fader** | Composition master level. |
| **CROSSFADER** | Instrument packs: environment (BED BODY AURA) against figures (FIGURE LIGHT TEXT), centre is everything. |

The audio-reactive motion needs Avenue's External FFT pointed at a real input (Preferences, Audio).
Without one every reactive parameter sits at its floor and the picture looks still.

## Who follows it

`python -m resolume_build.preset_patch --check` prints this table from the preset files.
Thirteen rules, a dot is a pass.

| preset | rules passed |
|---|---|
| Signal Lost, Studio One, The Library And The Hand, The Manual, The Surface, The Mixers | 13 of 13 |
| Dead Air, Dew Line | 13 of 13 |
| Lexicon v1, Lexicon v2, Nisei v1, TestCard v1, Orbit v1, React v4.4, SPECIMEN | 13 of 13 |
| EarthSearch EP01 | 7 of 13 (live show; arrows, PLAY and STOP ALL stay as designed) |

The instrument packs get there by construction: they are all generated from one control table.
Dead Air, Dew Line and the older React family were made by earlier generators, so they were
brought up to the standard in place with `python -m resolume_build.preset_patch`, which edits
only the controls named above and writes a change log beside each file.

## What changed in the older presets

| preset family | changed |
|---|---|
| React family (Lexicon, Nisei, TestCard, Orbit, React, SPECIMEN) | Free controls filled: TEMPO, UP, DOWN, STOP, RECORD, FOOTSWITCH. PLAY now opens scene 1 (tempo resync moved to METRONOME). CUE LEVEL was an absolute scrub on a relative knob and is now TIME. Nisei and TestCard had RIGHT and LEFT reversed. Orbit, React and SPECIMEN moved RIGHT and LEFT from scenes to decks, because UP and DOWN now walk the scenes. |
| Dead Air, Dew Line | UP and DOWN were the old direction. TEMPO, METRONOME, TAP and CUE LEVEL as above. |
| EarthSearch EP01 | TEMPO is FFT gain. CUE LEVEL is relative. METRONOME is FFT gain home. |

## What differs on purpose

- Which layer each pad row plays, and what the five scene buttons do, in the React family.
  Those presets were built around a five-layer composition, not the eight-layer instrument.
- Which effects sit on the four FX banks, and the LED colours. Those are the look of a pack.
- Dead Air and Dew Line keep an Overlay GRAIN layer where the newer packs use Add. Dew Line's eighth macro is
  SILK, not VOID, because that pack's rack puts a stroke effect there.
- EarthSearch EP01 and SPECIMEN take their FFT from the composition's own audio, not from the input device.
  The FFT gain knob is Avenue's input-device gain, so it does nothing in those two. Everything else listens
  to the External FFT.

## Not yet confirmed on the hardware

The standard was assembled from the performer's own saved presets, which is where the FFT gain
path and the relative reading of CUE LEVEL come from. Two things have not been seen working on
the APC40 itself: the lamp behaviour of METRONOME and TAP after they became reset buttons, and
the feel of the relative step sizes (FFT gain 128 steps, FX master 64, TIME on CUE LEVEL 256).

## Five-minute hardware check

Restart Avenue so it reads the new presets, open any instrument pack (The Manual is a good one) with music playing
into the input, and try these in order.

1. Turn the TEMPO knob slowly clockwise: the audio-driven motion gets livelier. Anticlockwise: calmer.
   Press METRONOME: the gain returns to the middle.
2. Turn CUE LEVEL anticlockwise: the four effect banks fall away together. Clockwise: they come back, smoothly,
   with no jump. If it jumps instead, CUE LEVEL is sending positions, not steps; say so and it is a one-line flip.
3. Track knob 8 at its centre is 1x speed. Turn it, then press TAP TEMPO: speed returns to exactly 1x.
4. UP then DOWN walk the scenes, RIGHT then LEFT walk the decks, RECORD blacks out and returns, the footswitch
   blacks out while held.
5. Look at the METRONOME and TAP lamps after pressing them. They were tempo buttons and are now reset buttons,
   so the lamp behaviour is the one thing nobody has seen yet.
