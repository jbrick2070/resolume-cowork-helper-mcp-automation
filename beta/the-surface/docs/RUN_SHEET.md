# The Surface - run sheet

## Before the first frame

1. Install: `APC 40 MK II - The Surface.xml` -> `Documents\Resolume Avenue\Shortcuts\MIDI\`; `The Surface - APC40 mkII + MIDI.avc` -> `Documents\Resolume Avenue\Compositions\` (this rig's Documents is under OneDrive).
2. **Audio in.** Preferences -> Audio -> Input device: `CABLE Output (VB-Audio Virtual Cable)`. Play your music into `CABLE Input`. The composition uses External FFT; with no input device every reactive parameter sits at its floor and the picture looks static.
3. Preferences -> MIDI: `APC40 mkII` as input AND output (output drives the pad colours).
4. Open the composition. It selects its own MIDI preset.
5. Park the CROSSFADER in the centre and all eight faders up.

## Opening

* **PLAY** fires scene 1 of the current deck and arms the SCOPE.
* Watch the SCOPE (layer 8, fader 8): if it is flat, the audio input is not set.
* Track knobs 1-6 are depth / release for the three bands; turn depth up until the SCOPE breathes with the music, not with every hi-hat.
* **FFT GAIN is the TEMPO knob**, on every composition: Avenue's global audio gain. Turn it up when the picture is too calm for the room, down when it slams. METRONOME puts it back to the middle.
* **TIME is Track knob 8**: composition speed, 0 to 2x with 1x at the centre. TAP TEMPO puts it back to exactly 1x.

## Playing

* Scenes with Scene Launch 1-5 and UP/DOWN; worlds with LEFT/RIGHT.
* Pads mash the five playable layers across any scene.
* Effects: lit button = active. Device knobs 1-4 are the four banks' wetness, 5-8 the macros. CUE LEVEL nudges all four banks together (anticlockwise toward the clean picture).
* **STOP** clears the pad layers only (beds and scope survive). **STOP ALL CLIPS** ejects everything. **RECORD** is blackout (press again to return). The footswitch is a momentary blackout.
* **BANK LOCK = CLEAN.** Every effect dry, every macro off, picture untouched. Avenue has no soft-takeover: after CLEAN the physical knobs are where you left them, so the next knob you touch jumps. Sweep CUE LEVEL to come back smoothly.

## Signature moments, deck by deck

**The Grid**
- Note zero: Scene Launch 1 and press the real bottom-left pad; the picture is the pad.
- Palette: column 4, tap the row-3 FIGURE pad on the beat so index 9 blinks amber over the 128-cell table.
- Mode 1: UP to column 8 and let the SysEx bytes ride the mids; this is the message to send after every power-up.

**The Strips**
- Channel = track: Scene Launch 1, then press Clip Stop on strip 3 - the one lit button (layer 3) vanishes, because note 52 on channel 3 ejects layer 3; Scene Launch 1 brings it back.
- Rec Arm: column 5, tap the real Record Arm buttons - they are FX bank 1, and the amber row is them.
- Crossfader: column 8, sweep the real crossfader; the scene's layers split A from B (the green cap sits on FIGURE, side B, and goes dark at hard A). The cap's own travel is the lows, not CC15.

**Knobs + Transport**
- Rings: column 2, turn Device knob 1 slowly; the amber ring on screen is the ring under your hand.
- Cue level: column 4, sweep CUE LEVEL anticlockwise to CLEAN and back; the amber line is the four bank links moving together.
- Gain: column 5, turn the TEMPO encoder; the red ticks are CC13 and the FFT gain moves with them.
- Footswitch: column 8, stamp the pedal on the one; the red bar is CC64 going 0x7F.

**The Wire**
- Baud: Scene Launch 2 and the bit stream rides the mids; on the five-pin wire every byte is ten bits (the APC rides USB, which packs them four bytes at a time).
- Note on/off: column 4, hold a pad - the green pad lives while you hold it, the flash is the note off.
- Monitor: column 8 with Preferences > MIDI open on the second screen; the scrolling line is what the monitor shows.

**SE-500 Mixer**
- T-bar: Scene Launch 3 and ride the real crossfader slowly end to end; the amber T-bar is your hand.
- Wipe to PIP: UP from Wipe to PIP on a downbeat with Device knob 3 (SPACE) at a quarter and MIRROR QUAD lit so the window tiles.
- The older wire: column 8, tap any APC button on the beat; the red pins flash - the same note-on, on five pins instead of USB.
