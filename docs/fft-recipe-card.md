# FFT Recipe Card (the house convention, generalized)

One page. This is how every reactive cell in the kit is wired, and why it
feels alive instead of flickery.

## The convention

- Split: bass 0.00-0.33, mids 0.33-0.66, highs 0.66-1.00. Narrow bands
  (e.g. bass 0-0.25 for a kick-gate) only when a cell must ignore melody.
- Target: the CLIP's video opacity for overlays; a source's single
  obvious driver param for plugins (one band per param - scalar law).
- Gain: +3 dB for cells that should whisper, +6 dB standard, +9 dB only
  for cells that must SNAP (finale strobes, terminal transits).
- Fallback (release): 100-400 ms = percussive cells (strobes, gates,
  fast lines); 500-800 ms = grooving mid cells; 1200-1800 ms = breathing
  beds and slow fields. Fallback is the feel knob - when in doubt, longer.
- Floor: 0.12 for everything except strobes (floor 0) - a cell that goes
  fully black reads as broken; a cell that never quite dies reads as alive.

## Assignment logic (the taste part)

- Bass drives things that PUMP: metaball blobs, tunnel rings, vertical
  streaks, anything with mass.
- Mids drive things that TRAVEL: spirals, orbits, pattern generators -
  melody and voice live here.
- Highs drive things that SPARKLE: thin lines, flicker reels, scapes.
- One strobe per deck, on a narrowed bass band, gain +3, fallback 100,
  floor 0. More than one strobe cell per deck is a mistake.
- Within one deck's reactive row, never repeat a source; across decks,
  reuse freely and re-dress.

## Live checklist

1. Audio input device set (external FFT reacts to the ROOM, not clips).
2. Play pink noise or a track: every reactive cell should visibly breathe
   at its own rate; nothing should sit at full brightness.
3. Kill the music: cells decay to their floors over their fallback times.
   Anything that snaps instantly to black has fallback too short.
