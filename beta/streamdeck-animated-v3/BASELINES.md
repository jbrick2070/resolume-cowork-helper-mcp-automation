# APC40MKII Electric Zentropa ScreenPulse v1

**ScreenPulse** is the music-driven, screen-first APC40 visual baseline preserved on 2026-07-21. It is designed to look its best on the composition monitor or a large display while music is playing.

## Matched shipping pair

- Composition: `compositions/APC40MKII_ELECTRIC_ZENTROPA_SCREENPULSE_v1.avc`
- MIDI preset: `controllers/APC40MKII_ELECTRIC_ZENTROPA_SCREENPULSE_v1.xml`
- Ship both files together. Their identical filename stem and internal names are intentional.
- Good for: music-driven on-screen APC40 visuals, with the bed and chassis background continuously visible.
- Known limitation: the physical APC40 button LEDs do not remain latched after release.
- The MIDI preset is an exact snapshot of the active 204-shortcut preset, apart from its new internal name.

The temporary loss of the background during testing was traced to Layer 1 being left in Solo. That was live runtime state and is not encoded in this saved baseline.
