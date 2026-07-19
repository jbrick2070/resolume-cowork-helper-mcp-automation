# APC40 mkII — Native MIDI Address Reference (every surface)

Complete decode of every control on the APC40 mkII. **Rig-confirmed** entries were decoded
from `beta/controllers/APC 40 MK II - React v4.4.xml` (86 mapped controls);
the rest are filled from the official
**Akai APC40 Mk2 Communications Protocol v1.2**. Companion diagram: `APC40_native_addresses.svg`.

Encoding: note-on status = `0x90 + (channel-1)`; CC status = `0xB0 + (channel-1)`.
Resolume RawInputMessage `key = 2^56 + (data1 << 8) + status`.

## Clip grid — 5×8, notes 0-39, channel 1
Bottom-left pad = note 0. `note = row_from_bottom x 8 + column_index`.

| pad row (physical) | notes (col1-8) |
|---|---|
| row 5 (top)    | n32 n33 n34 n35 n36 n37 n38 n39 |
| row 4          | n24 n25 n26 n27 n28 n29 n30 n31 |
| row 3          | n16 n17 n18 n19 n20 n21 n22 n23 |
| row 2          | n8  n9  n10 n11 n12 n13 n14 n15 |
| row 1 (bottom) | n0  n1  n2  n3  n4  n5  n6  n7  |

## Right column (channel 1)
| control | note | Akai name |
|---|---|---|
| Scene launch 1-5 | n82 n83 n84 n85 n86 | SCENE LAUNCH 1-5 |
| Stop All Clips   | n81 | STOP ALL CLIPS |
| Master select    | n80 | MASTER |

## Per-track buttons — note is FIXED, the **MIDI channel = track (1-8)**
Eight physical copies of each, one per track column; only the channel differs.

| control | note | channel | Akai name |
|---|---|---|---|
| Clip Stop     | n52 | ch1-8 | TRACK/CLIP STOP |
| Track Select  | n51 | ch1-8 | TRACK SELECTION |
| Activator     | n50 | ch1-8 | ACTIVATOR |
| Solo          | n49 | ch1-8 | SOLO |
| Record Arm    | n48 | ch1-8 | RECORD ARM |
| Crossfade A/B | n66 | ch1-8 | CROSSFADER A/B |

## Global mode + transport + device (channel 1, Akai standard notes)
| control | note | | control | note |
|---|---|---|---|---|
| Pan            | n87 | | Play          | n91 |
| Sends          | n88 | | Stop          | n92 |
| User           | n89 | | Record        | n93 |
| Metronome      | n90 | | Session Rec   | n102 |
| Tap Tempo      | n99 | | Nudge -       | n100 |
| Up             | n94 | | Nudge +       | n101 |
| Down           | n95 | | Shift         | n98 |
| Right          | n96 | | Bank Lock     | n103 |
| Left           | n97 | |               |     |
| Device <       | n58 | | Device >      | n59 |
| Bank <         | n60 | | Bank >        | n61 |
| Device On/Off  | n62 | | Device Lock   | n63 |
| Clip/Dev View  | n64 | | Detail View   | n65 |

## Knobs & faders (Control Change)
| control | CC | channel | notes |
|---|---|---|---|
| Track Control knobs 1-8 (top) | CC48-55 | ch1 | absolute |
| Device Control knobs 1-8 (right) | CC16-23 | ch1 (ch=track in Mode 0) | absolute |
| Cue Level | CC47 | ch1 | absolute |
| Tempo knob | CC13 | ch1 | **relative** (1-63 = +, 127-64 = -) |
| Track faders 1-8 | CC7 | ch1-8 | one per track, channel = track |
| Master fader | CC14 | ch1 | absolute |
| Crossfader | CC15 | ch1 | absolute |
| Footswitch | CC64 | ch1 | 0x7F down / 0x00 up |

## Your preset's re-mappings (rig-confirmed, for reference)
- Grid n8-39 -> clip connect (layers 1-4 x cols 1-8); n1-5 -> comp FX bypass; n7 -> comp bypass (blackout).
- n48 ch1-4 -> layer bypass; n49 ch1-4 -> layer solo; n51 ch1-8 -> column connect; n52 ch1-4 -> layer clear.
- n81 -> disconnect all; n86 -> select next deck; n91 -> resync; n96/n97 -> next/prev column; n99 -> tap tempo.
- CC7 ch1-4 -> layer opacity; CC14 -> master; CC15 -> crossfader; CC47 -> selected-clip position;
  CC48-55 -> selected-clip dashboard link 1-8; CC16-23 (17-22 used) -> effect params.

Source: Akai APC40 Mk2 Communications Protocol v1.2 (2015-01-19) + decoded React v4.4 preset.
