# APC 40 MK II - Orbit v1 - Layout Card (print me)

Preset: `APC 40 MK II - Orbit v1.xml`
Activation: Resolume Preferences > MIDI > enable "APC40 mkII" as INPUT and
OUTPUT (output = pad color feedback), then select the preset. Grid lights
within ~2 seconds of a comp with clips.

## Clip grid (5x8 pads)

- Rows 1-4 (bottom-up) = layers: Bed / Structure / Body / Pulse.
- Columns 1-8 = scene columns 1-8 of the ACTIVE deck. Pads launch cells;
  column colors are per-deck feedback.
- Row 5 = FX PUNCH ROW (composition effect bypass toggles, in rack order):
  Trails, Hue Rotate, Shift RGB, LoRez, Invert RGB, Mirror Quad, Freeze,
  comp Blackout. Punch in, punch out - they are toggles.

## Scene launch column (right edge, 5 buttons)

- TOP = trigger column 9: the TRANSIT. Fire it, let it establish for a
  phrase while your clips keep playing, then...
- BOTTOM = next deck (cycles all deck tabs, wraps). That is the jump:
  transit establishes, bottom button lands you in the next regime.
- Middle three: dark by design (documented hand-map slots for direct
  deck jumps if you want them - Resolume Ctrl+M, ~30 s each).

## Faders and knobs

- Faders 1-8: layer opacities (5-8 unmapped on a 4-layer comp).
- Master fader: composition master. Crossfader: crossfader.
- Device knobs 1 and 4: Trails feedback / Hue Rotate amount rides.
- Clip-stop row: buttons 1-4 eject layers 1-4; 5-8 unmapped.

## Performance notes

- Column order IS the energy arc on every deck: 1-2 open, 3 build,
  4-5 peak, 6-7 comedown, 8 null/art, 9 transit. Muscle memory transfers
  across all five decks.
- Tap tempo on the Resolume side; nothing in the set assumes a numeric
  BPM. Audio reactivity is FFT on external input - set your audio device
  before doors.
- Validation state of this XML: 91 shortcuts, 91 unique ids, 91 unique
  MIDI keys, transit note present exactly once.
