# INSTALL - zero to playing in ~10 minutes, no AI, no coding

Four copy-paste steps. Windows paths shown; on macOS replace `Documents\`
with `~/Documents/`. Using Arena instead of Avenue? Its folders say
"Resolume Arena". If your Documents folder is OneDrive-managed, everything
lives under OneDrive's Documents.

## 1. The composition

Copy a comp from this repo's `compositions/` into:

    Documents\Resolume Avenue\Compositions\

- `Res Fable Live Gen.avc` - 6 decks of scene banks, the simpler start
- `Res Fable Orbit Gen.avc` - the five-regime space journey

Open Resolume > Composition menu > Open, pick the file. First open takes a
moment while thumbnails generate. Both comps are 100% generative - no
media files needed, nothing else to download.

## 2. The plugins (optional but recommended)

Copy everything from this repo's `plugins/dll/` into:

    Documents\Resolume Avenue\Extra Effects\

(create the folder if it does not exist), then RESTART Resolume - it only
scans that folder at startup. You get five new toys: sources "Fable
Pulsar" and "Fable Video Musi[c]" under Sources, and three effects under
Video Effects. Try Fable Pulsar in Orbit's O3 deck, column 5 - that cell
was designed for it. Details and build-from-source: `plugins/README.md`.

## 3. The controller (APC40 mkII)

Copy the preset XML from this repo's `controllers/` into:

    Documents\Resolume Avenue\Shortcuts\MIDI\

- `APC 40 MK II - Orbit v1.xml` pairs with the Orbit comp
- `APC 40 MK II - Fable v4.2.xml` pairs with the Live comp

Then in Resolume: Preferences > MIDI > enable "APC40 mkII" as INPUT **and**
OUTPUT (output = pad colors), and select the preset for the device. The
grid lights up within a couple of seconds. What every button does:
`controllers/LAYOUT_CARD.md`. No APC40? `prompts/09-any-controller.md`
maps YOUR hardware. Prefer to map by hand? `controllers/INSTALL.md` has
the manual road with official Resolume doc links.

## 4. The audio

Preferences > Audio > set your audio INPUT device (line-in, loopback, or
a virtual cable carrying the DJ feed). The reactive cells listen to
external FFT - the room, not the clips. Play music; the Pulse row
breathes. No music = cells sit at their calm floor levels, by design.

## It's not working

- Pads launch wrong cells: power-cycle the APC; make sure Ableton or
  another app didn't grab it first.
- No pad colors: the APC is input-only - enable it as OUTPUT too.
- Plugins missing: you didn't restart Resolume after copying the DLLs.
- Preset not in the dropdown: wrong folder - note Shortcuts\MIDI, not
  Presets. Full folder map: https://resolume.com/support/en/directory-list
- More: `controllers/INSTALL.md` troubleshooting section.
