# Electric Zentropa screen baseline

This snapshot preserves the screen-safe state observed on 2026-07-21. It is a baseline for continued work, not a finished controller release.

## Screen baseline v1

- Composition: `compositions/APC40_Electric_Zentropa_SCREEN_BASELINE_v1.avc`
- MIDI preset: `controllers/APC 40 MK II - Electric Zentropa SCREEN BASELINE v1.xml`
- Good for: the on-screen APC40 twin and playback, with the bed and chassis background continuously visible.
- Known limitation: the physical APC40 button LEDs do not remain latched after release.
- The MIDI preset is an exact snapshot of the active 204-shortcut preset, apart from its new internal name.

The temporary loss of the background during testing was traced to Layer 1 being left in Solo. That was live runtime state and is not encoded in this saved baseline.
