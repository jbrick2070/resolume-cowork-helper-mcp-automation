# Installing the APC 40 MK II preset (manual, no AI involved)

Two ways to get the layout: install the shipped XML (2 minutes), or map it
yourself by hand using the layout card as the spec (~45 minutes, and you
will learn Resolume's MIDI system doing it). Both below.

## A. Install a shipped preset XML

1. Close Resolume.
2. Use the stable verified pair:

   | Composition | MIDI preset |
   |---|---|
   | `APC40_Visual_QA_148.avc` | `APC 40 MK II - Visual QA.xml` |

3. Copy the selected XML into Resolume's MIDI shortcuts
   folder:
   - Windows: `Documents\Resolume Avenue\Shortcuts\MIDI\`
     (Arena: `Documents\Resolume Arena\Shortcuts\MIDI\`. If your Documents
     folder is OneDrive-managed, it lives under OneDrive's Documents.)
   - macOS: `~/Documents/Resolume Avenue/Shortcuts/MIDI/`
   If the `Shortcuts\MIDI` folder does not exist yet, open Resolume once,
   create any MIDI shortcut, and it appears. Official folder map:
   https://resolume.com/support/en/directory-list
4. Plug in the APC40 mkII, start Resolume, and open
   `compositions/APC40_Visual_QA_148.avc`.
5. Preferences > MIDI: enable "APC40 mkII" as INPUT **and** OUTPUT.
   Output is not optional - it is what drives the pad color feedback.
6. In the same MIDI preferences, select the matching preset for the device.
7. Trigger column 1 once if the labels are initially dark, then touch the
   physical controls.

VERIFY: a grid pad toggles its matching label and every fader/knob wakes and
moves its own witness.

The older React Live and Orbit composition/preset pairs are retained under
`beta/`. They are experimental and are not claimed as controller-verified.

## B. Map a beta performance layout yourself

This section describes the older Live/Orbit 4x9 performance design, not the
stable 148-control visual twin.

Resolume's MIDI mapping is point-and-click - no XML editing needed.
Official guide (read this first):
https://resolume.com/support/en/midi-shortcuts

The short version: Shortcuts menu > Edit MIDI Map. Resolume dims into
mapping mode; click any interface element, then touch the physical control
you want bound to it; repeat. Done > Save. Use
[`beta/controllers/LAYOUT_CARD.md`](../beta/controllers/LAYOUT_CARD.md) as
your beta spec sheet:

- THE 4x8 / 4x9 RULE: the composition is 9 columns wide, but the APC's
  clip pads cover columns 1-8 ONLY (4 layers x 8 columns = the main pad
  bank, one pad per cell, no sideways banking). Column 9 - the TRANSIT -
  deliberately lives OFF the grid, on the TOP scene-launch button. Do not
  try to fit 9 columns onto 8 pads.
- Map the pad grid accordingly: rows = layers 1-4 bottom-up across
  columns 1-8; pad row 5 = composition effect bypass toggles in rack
  order.
- Map faders 1-4 to layer video opacity, master fader to composition
  master, crossfader to crossfader.
- Map the TOP scene-launch button to "trigger column 9" and the BOTTOM
  scene-launch to Composition > Select Next Deck.
- Color feedback: with the APC enabled as an output device, Resolume
  sends clip states automatically; per-pad idle colors follow the velocity
  you assign in the shortcut's "Button feedback" settings (each shortcut
  row in mapping mode exposes it).

Related official pages:
- Parameters and what can be mapped:
  https://resolume.com/support/en/parameters
- Preferences overview: https://resolume.com/support/en/preferences

## Troubleshooting

- Grid launches the WRONG cells / flipped: your APC is in a different
  mode. Power-cycle it (Resolume puts it in the right mode when it is
  enabled as output), and make sure no other app (Ableton) grabbed it
  first.
- No pad colors: the APC is enabled as input only - enable it as OUTPUT
  in Preferences > MIDI as well.
- Controller not listed at all on Windows 11: recent Windows MIDI 2.0
  updates broke some class-compliant devices; Resolume's note:
  https://resolume.com/support/en/midi-troubles-on-windows-with-midi-2-0-update
- Preset not in the dropdown: the XML is in the wrong folder - check the
  directory list link in section A, and note the Avenue vs Arena folder
  difference.

## Building for another controller

To build a complete on-screen diagnostic twin rather than only a performance
mapping, start with
[`docs/CONTROLLER_VISUAL_TWIN_PLAYBOOK.md`](../docs/CONTROLLER_VISUAL_TWIN_PLAYBOOK.md).
It covers hardware inventory, one-layer-per-control geometry, target-version
XML specimens, continuous-control fan-out, physical QA, and rollback. The
companion
[`docs/ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md`](../docs/ANY_CONTROLLER_VISUAL_TWIN_PROMPT.md)
is the copy-paste execution prompt.
