# Electric Zentropa baselines

These snapshots preserve the two useful states observed on 2026-07-21. They are baselines for continued work, not a finished controller release.

## Screen baseline v1

- Composition: `compositions/APC40_Electric_Zentropa_SCREEN_BASELINE_v1.avc`
- MIDI preset: `controllers/APC 40 MK II - Electric Zentropa SCREEN BASELINE v1.xml`
- Good for: the on-screen APC40 twin and playback, with the bed and chassis background continuously visible.
- Known limitation: the physical APC40 button LEDs do not remain latched after release.
- The MIDI preset is an exact snapshot of the active 204-shortcut preset, apart from its new internal name.

## LED latch L1 prototype

- MIDI preset: `controllers/APC 40 MK II - Electric Zentropa LED LATCH L1 PROTOTYPE.xml`
- Composition: use the screen baseline composition above.
- Good for: preserving the one-button Layer 1 feedback experiment, where the button color followed the active clip state.
- Known limitation: expected clip playback was not reliable in the live test. This preset changes only the Layer 1 feedback mapping and is not show-ready.

The temporary loss of the background during testing was traced to Layer 1 being left in Solo. That was live runtime state and is not encoded in either saved baseline.
