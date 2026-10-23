# The Surface - deck sheets

Note 0 is bottom-left. Channel is track. Centre is everything.


## Deck 1 - The Grid

The 5x8 pad grid drawn on a matte black chassis: note 0 bottom-left, rows of eight, five rows for five layers, the 128-entry RGB velocity palette, the two LED families every pack here speaks (green 21/22, amber 9/10), the Scene Launch column, and the SysEx that puts the controller into Mode 1 - a show requirement, because a power cycle forgets it.

Palette: bed #0f1012, body #3ddc84, figure #ffae1a, light #3ddc84, text #e8e4d8, aura #e03a2f

| layer | 1 Note Zero | 2 Row Of Eight | 3 Five Rows | 4 Velocity Palette | 5 Green 21 | 6 Amber 9 | 7 Scene Launch | 8 Mode 1 |
|---|---|---|---|---|---|---|---|---|
| 8 SCOPE | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> |
| 7 GRAIN | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Matte Tooth<br><small>Static</small> | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> |
| 6 AURA | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Wash<br><small>Gradient</small> |
| 5 TEXT | NOTE 0 - CHANNEL 1<br><small>Text Block</small> | ROW 1 = BED LAYER<br><small>Text Block</small> | 5 ROWS x 8 = 40 PA<br><small>Text Block</small> | VELOCITY = COLOUR<br><small>Text Block</small> | GREEN FAMILY<br><small>Text Block</small> | AMBER FAMILY<br><small>Text Block</small> | SCENE LAUNCH n82-n<br><small>Text Block</small> | F0 47 7F 29 60 00 <br><small>Text Block</small> |
| 4 LIGHT | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | Power Cycle<br><small>Stroboscope</small> |
| 3 FIGURE | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Row 5: n32-n39<br><small>Metaballs</small> | Index 9<br><small>Shaper / Transform</small> | Disconnected 22<br><small>Shaper / Transform</small> | Disconnected 10<br><small>Shaper / Transform</small> | Stop All n81<br><small>Shaper / Transform</small> | Mode<br><small>Shaper / Transform</small> |
| 2 BODY | Pad n0<br><small>Shaper / Transform</small> | Row 1: n0-n7<br><small>Metaballs</small> | Row 1<br><small>Metaballs</small> | 128 Velocities<br><small>Checkered</small> | Connected 21<br><small>Shaper / Transform</small> | Connected 9<br><small>Shaper / Transform</small> | Scene 1-5<br><small>Metaballs</small> | SysEx Bytes<br><small>Sine Wave</small> |
| 1 BED | Pad Grid<br><small>Checkered</small> | Pad Grid<br><small>Checkered</small> | Pad Grid<br><small>Checkered</small> | Chassis<br><small>Solid Color</small> | Pad Grid<br><small>Checkered</small> | Pad Grid<br><small>Checkered</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> |

Text corpus: NOTE 0 · n0 - n39 · 5 x 8 = 40 · VELOCITY = COLOUR · ON 21 - DIM 22 · ON 9 - DIM 10 · SCENE LAUNCH n82-n86 · STOP ALL CLIPS n81 · F0 47 7F 29 60 00 04 41 · MODE 1 · 0x90 · CHANNEL 1

- Note zero: Scene Launch 1 and press the real bottom-left pad; the picture is the pad.
- Palette: column 4, tap the row-3 FIGURE pad on the beat so index 9 blinks amber over the 128-cell table.
- Mode 1: UP to column 8 and let the SysEx bytes ride the mids; this is the message to send after every power-up.

## Deck 2 - The Strips

Eight track strips, each a copy of the last: the per-track buttons keep one note and change only the MIDI channel. Clip Stop 52 ejects, Select 51 selects, Activator 50 is on-air, Solo 49, Record Arm 48 and Crossfade A/B 66 are the first two effect banks in every pack here. Below them the eight faders on CC7, the master on CC14 and the crossfader on CC15 whose centre is everything.

Palette: bed #0f1012, body #e8e4d8, figure #3ddc84, light #ffae1a, text #e8e4d8, aura #1f2126

| layer | 1 Channel = Track | 2 Clip Stop 52 | 3 Select 51 | 4 Activator 50 | 5 Rec Arm 48 | 6 A/B 66 | 7 Faders CC7 | 8 Crossfader CC15 |
|---|---|---|---|---|---|---|---|---|
| 8 SCOPE | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> |
| 7 GRAIN | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Track Columns<br><small>Lines</small> | Matte Tooth<br><small>Static</small> |
| 6 AURA | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> |
| 5 TEXT | PER-TRACK BUTTONS<br><small>Text Block</small> | CLIP STOP n52 ch1-<br><small>Text Block</small> | TRACK SELECT n51<br><small>Text Block</small> | ACTIVATOR n50 = MU<br><small>Text Block</small> | RECORD ARM n48 ch1<br><small>Text Block</small> | CROSSFADE A/B n66<br><small>Text Block</small> | TRACK FADERS CC7 c<br><small>Text Block</small> | CROSSFADER CC15<br><small>Text Block</small> |
| 4 LIGHT | LED Glow<br><small>Gradient</small> | Note On<br><small>Stroboscope</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> |
| 3 FIGURE | Track 1<br><small>Shaper / Transform</small> | n52 ch3<br><small>Shaper / Transform</small> | n51 ch4<br><small>Shaper / Transform</small> | n50 ch6 Off<br><small>Shaper / Transform</small> | FX1 TINT<br><small>Shaper / Transform</small> | n66 ch6<br><small>Shaper / Transform</small> | Fader 2 Cap<br><small>Lines</small> | Crossfader Cap<br><small>Lines</small> |
| 2 BODY | Eight Strips<br><small>Metaballs</small> | Clip Stop Row<br><small>Metaballs</small> | Select Row<br><small>Metaballs</small> | Activators Lit<br><small>Metaballs</small> | Rec Arm Row<br><small>Metaballs</small> | A/B Row<br><small>Metaballs</small> | Eight Faders<br><small>Lines</small> | Crossfader Slot<br><small>Lines</small> |
| 1 BED | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Track Columns<br><small>Lines</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> |

Text corpus: CHANNEL = TRACK · CLIP STOP n52 · TRACK SELECT n51 · ACTIVATOR n50 · SOLO n49 · RECORD ARM n48 · CROSSFADE A/B n66 · CC7 ch1-8 · MASTER CC14 · CROSSFADER CC15 · 0x90 + (ch - 1) · CENTRE = EVERYTHING

- Channel = track: Scene Launch 1, then press Clip Stop on strip 3 - the one lit button (layer 3) vanishes, because note 52 on channel 3 ejects layer 3; Scene Launch 1 brings it back.
- Rec Arm: column 5, tap the real Record Arm buttons - they are FX bank 1, and the amber row is them.
- Crossfader: column 8, sweep the real crossfader; the scene's layers split A from B (the green cap sits on FIGURE, side B, and goes dark at hard A). The cap's own travel is the lows, not CC15.

## Deck 3 - Knobs + Transport

The right-hand block and the top row: eight Device knobs with LED rings on CC16-23 (the dashboard links), eight Track knobs on CC48-55 (the live FFT), Cue Level on CC47 (the effects master sweep), the relative Tempo encoder on CC13, PLAY STOP RECORD on notes 91-93, Tap and Nudge, and the footswitch on CC64 that is a momentary blackout in every pack here.

Palette: bed #0f1012, body #e8e4d8, figure #ffae1a, light #ffae1a, text #e8e4d8, aura #e03a2f

| layer | 1 Device CC16-23 | 2 LED Rings | 3 Track CC48-55 | 4 Cue Level CC47 | 5 Tempo CC13 | 6 Play Stop Rec | 7 Tap + Nudge | 8 Footswitch CC64 |
|---|---|---|---|---|---|---|---|---|
| 8 SCOPE | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> |
| 7 GRAIN | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> |
| 6 AURA | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> |
| 5 TEXT | DEVICE KNOBS CC16-<br><small>Text Block</small> | LED RINGS<br><small>Text Block</small> | TRACK KNOBS CC48-5<br><small>Text Block</small> | CUE LEVEL CC47<br><small>Text Block</small> | TEMPO CC13 - RELAT<br><small>Text Block</small> | PLAY n91 - STOP n9<br><small>Text Block</small> | TAP TEMPO n99<br><small>Text Block</small> | FOOTSWITCH CC64<br><small>Text Block</small> |
| 4 LIGHT | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | Beat<br><small>Stroboscope</small> | LED Glow<br><small>Gradient</small> | Tap<br><small>Stroboscope</small> | Note On<br><small>Stroboscope</small> |
| 3 FIGURE | Device Knob 1<br><small>Rings</small> | Ring Value<br><small>Rings</small> | Eight Track Knobs<br><small>Metaballs</small> | Sweep<br><small>Lines</small> | Relative Ticks<br><small>Sine Wave</small> | STOP n92<br><small>Shaper / Transform</small> | NUDGE+ n101<br><small>Shaper / Transform</small> | CC64 Down<br><small>Lines</small> |
| 2 BODY | Knob Rows<br><small>Lines</small> | Ring Wide<br><small>Rings</small> | Top Row<br><small>Lines</small> | Cue Level<br><small>Rings</small> | Tempo Encoder<br><small>Rings</small> | PLAY n91<br><small>Shaper / Transform</small> | TAP n99<br><small>Shaper / Transform</small> | 1/4 Inch Jack<br><small>Rings</small> |
| 1 BED | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> |

Text corpus: DEVICE KNOBS CC16-23 · LED RINGS · TRACK KNOBS CC48-55 · CUE LEVEL CC47 · TEMPO CC13 · RELATIVE · PLAY n91 · STOP n92 · RECORD n93 · TAP n99 · NUDGE n100 / n101 · FOOTSWITCH CC64

- Rings: column 2, turn Device knob 1 slowly; the amber ring on screen is the ring under your hand.
- Cue level: column 4, sweep CUE LEVEL anticlockwise to CLEAN and back; the amber line is the four bank links moving together.
- Footswitch: column 8, stamp the pedal on the one; the red bar is CC64 going 0x7F.

## Deck 4 - The Wire

MIDI itself, from the 1983 spec to tonight's preset: the DIN-5 with its 5 mA current loop, 31,250 baud and ten bits a byte, the status byte with its high bit set, note on and note off (Piano listens for the off), control change with 128 steps, the class-compliant USB that powers the whole surface, and the 2^56 (note) and 2^57 (CC) markers Resolume files a raw message under. Red is the wire; green is a message arriving.

Palette: bed #0f1012, body #e03a2f, figure #3ddc84, light #3ddc84, text #e8e4d8, aura #e03a2f

| layer | 1 DIN-5 | 2 31,250 Baud | 3 Status Byte | 4 Note On / Off | 5 Control Change | 6 USB-B | 7 Resolume Key | 8 Monitor |
|---|---|---|---|---|---|---|---|---|
| 8 SCOPE | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> | MIDI Activity<br><small>Sine Wave</small> |
| 7 GRAIN | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Track Columns<br><small>Lines</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> |
| 6 AURA | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> |
| 5 TEXT | DIN-5 - 180 DEGREE<br><small>Text Block</small> | 31,250 BAUD<br><small>Text Block</small> | STATUS 1001 nnnn =<br><small>Text Block</small> | NOTE ON 0x90 nn vv<br><small>Text Block</small> | CONTROL CHANGE 0xB<br><small>Text Block</small> | USB-B - BUS POWERE<br><small>Text Block</small> | KEY = MARKER<br><small>Text Block</small> | PREFERENCES > MIDI<br><small>Text Block</small> |
| 4 LIGHT | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | Note On<br><small>Stroboscope</small> |
| 3 FIGURE | Five Pins<br><small>Metaballs</small> | Start Stop Bits<br><small>Lines</small> | MSB = 1<br><small>Shaper / Transform</small> | Note Off<br><small>Stroboscope</small> | 0-127<br><small>Lines</small> | USB Packets<br><small>Sine Wave</small> | Marker Bit<br><small>Shaper / Transform</small> | Messages Scrolling<br><small>Sine Wave</small> |
| 2 BODY | DIN-5<br><small>Rings</small> | Bit Stream<br><small>Sine Wave</small> | Eight Bits<br><small>Checkered / Transform</small> | Note On<br><small>Shaper / Transform</small> | Fader<br><small>Lines</small> | USB-B<br><small>Geometry Pattern Maker</small> | Key Rows<br><small>Lines</small> | Monitor Rows<br><small>Lines</small> |
| 1 BED | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Pad Grid<br><small>Checkered</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> |

Text corpus: DIN-5 · 5 mA CURRENT LOOP · 31,250 BAUD · 1 START - 8 DATA - 1 STOP · 0x90 · 0xB0 · NOTE ON / OFF · 0 - 127 · USB-B - BUS POWERED · 2^56 + (data1 << 8) + status · RAW INPUT MESSAGE · MIDI MONITOR

- Baud: Scene Launch 2 and the bit stream rides the mids; on the five-pin wire every byte is ten bits (the APC rides USB, which packs them four bytes at a time).
- Note on/off: column 4, hold a pad - the green pad lives while you hold it, the flash is the note off.
- Monitor: column 8 with Preferences > MIDI open on the second screen; the scrolling line is what the monitor shows.

## Deck 5 - SE-500 Mixer

A four-input analog SD video mixer drawn in the same chassis grammar: BNC composite and S-Video inputs with illuminated select buttons, a main and a sub source bus, the T-bar you pull at your own speed, wipes, picture-in-picture, split screen, colour processing, and - the reason it belongs in this pack - RS-232 on a 9-pin D-sub and MIDI control on a five-pin DIN: the APC40's language on the older wire (the APC itself is USB-only).

Palette: bed #0f1012, body #e8e4d8, figure #3ddc84, light #ffae1a, text #e8e4d8, aura #e03a2f

| layer | 1 Four Inputs | 2 Main / Sub | 3 T-Bar | 4 Wipe | 5 PIP | 6 Split Screen | 7 Colour Proc | 8 MIDI + RS-232 |
|---|---|---|---|---|---|---|---|---|
| 8 SCOPE | Program<br><small>Sine Wave</small> | Program<br><small>Sine Wave</small> | Program<br><small>Sine Wave</small> | Program<br><small>Sine Wave</small> | Program<br><small>Sine Wave</small> | Program<br><small>Sine Wave</small> | Program<br><small>Sine Wave</small> | MIDI In<br><small>Sine Wave</small> |
| 7 GRAIN | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> | Matte Tooth<br><small>Static</small> |
| 6 AURA | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Blank<br><small>Blank</small> | Wash<br><small>Gradient</small> |
| 5 TEXT | DATAVIDEO SE-500<br><small>Text Block</small> | MAIN / SUB SOURCE<br><small>Text Block</small> | T-BAR<br><small>Text Block</small> | WIPE<br><small>Text Block</small> | PIP<br><small>Text Block</small> | SPLIT SCREEN<br><small>Text Block</small> | COLOUR PROCESSING<br><small>Text Block</small> | RS-232 D-SUB 9<br><small>Text Block</small> |
| 4 LIGHT | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | LED Glow<br><small>Gradient</small> | Command<br><small>Stroboscope</small> |
| 3 FIGURE | Input 1<br><small>Shaper / Transform</small> | Main Source<br><small>Metaballs</small> | T-Bar<br><small>Lines</small> | Wipe Edge<br><small>Lines</small> | PIP Window<br><small>Shaper / Transform</small> | Right Half<br><small>Solid Color / Transform</small> | Chroma<br><small>Rings / Transform</small> | Five Pins<br><small>Metaballs</small> |
| 2 BODY | Four BNCs<br><small>Metaballs</small> | Sub Source<br><small>Metaballs</small> | T-Bar Slot<br><small>Lines</small> | Source A<br><small>Solid Color</small> | Background<br><small>Solid Color</small> | Split Line<br><small>Lines</small> | Colour Bars<br><small>Checkered</small> | DE-9 RS-232<br><small>Rings</small> |
| 1 BED | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> | Chassis<br><small>Solid Color</small> |

Text corpus: DATAVIDEO SE-500 · 4 x COMPOSITE BNC · S-VIDEO MINI-DIN · MAIN / SUB SOURCE · T-BAR · WIPE · PIP · SPLIT SCREEN · COLOUR PROCESSING · RS-232 D-SUB 9 · MIDI CONTROL 5-PIN DIN · THE APC'S LANGUAGE

- T-bar: Scene Launch 3 and ride the real crossfader slowly end to end; the amber T-bar is your hand.
- Wipe to PIP: UP from Wipe to PIP on a downbeat with Device knob 3 (SPACE) at a quarter and MIRROR QUAD lit so the window tiles.
- The older wire: column 8, tap any APC button on the beat; the red pins flash - the same note-on, on five pins instead of USB.
