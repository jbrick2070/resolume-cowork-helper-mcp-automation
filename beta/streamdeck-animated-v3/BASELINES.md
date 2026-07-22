# Electric Zentropa working editions

Every edition ships as a matched pair: one `.avc` composition and one `.xml`
MIDI preset with the same filename stem and internal preset name. Copy and keep
the pair together.

## ButtonGlow Baseline v1

The frozen controller-first rollback point. It preserves the good sine motion,
button lighting, continuously visible chassis/background, and the known-good
148-control Visual QA mappings without adding new pressed-state FFT behavior.

- Composition: `compositions/APC40MKII_ELECTRIC_ZENTROPA_BUTTONGLOW_BASELINE_v1.avc`
- MIDI preset: `controllers/APC40MKII_ELECTRIC_ZENTROPA_BUTTONGLOW_BASELINE_v1.xml`
- MIDI shortcuts: 203
- Best for: a dependable rollback, hardware-button work, and verifying mappings
  before trying the more reactive edition.

The eight A/B controls retain the known-good mapping: clip 1 in Toggle mode,
MIDI note 66 on channels 1-8, with connected-state LED feedback.

## ButtonPulse FFT v1

The performance edition. It is ButtonGlow plus audio FFT on the 120 visible
ON/pressed clips only. The always-on chassis/background and the continuous
faders/knobs remain unchanged, so music animates the lit controls without
making the board itself disappear.

- Composition: `compositions/APC40MKII_ELECTRIC_ZENTROPA_BUTTONPULSE_FFT_v1.avc`
- MIDI preset: `controllers/APC40MKII_ELECTRIC_ZENTROPA_BUTTONPULSE_FFT_v1.xml`
- MIDI shortcuts: 203
- Pressed FFT opacities: 120
- Best for: music playback, controller performance, and a full-board spectrum
  look.

The frequency field reads like a large spectrometer:

- bottom = bass, middle = low-mid/mid, top = highs;
- left = lower bands, center = mids, right = higher bands;
- the lower control strip rises from lows on the left to highs on the right;
- the right control quadrant rises from bass at the bottom to highs at the top.

ButtonPulse keeps ButtonGlow's controller shortcuts, including all eight A/B
toggle/feedback mappings. Layers 94-117, 143-145, and 148 are continuous
controls and intentionally receive no new pressed-state FFT.

## ScreenPulse v1

The screen-first edition preserved on 2026-07-21. It keeps the bed and chassis
background continuously visible and is designed to look strongest on the
composition monitor or a large display while music is playing.

- Composition: `compositions/APC40MKII_ELECTRIC_ZENTROPA_SCREENPULSE_v1.avc`
- MIDI preset: `controllers/APC40MKII_ELECTRIC_ZENTROPA_SCREENPULSE_v1.xml`
- MIDI shortcuts: 204
- Known limitation: physical APC40 button LEDs do not remain latched after
  release.

## Loading a matched pair

1. Copy the edition's XML into the Resolume Avenue `Shortcuts/MIDI` folder.
2. Start or restart Avenue so the new preset is registered. If Avenue was
   already open, select the exact edition name from the MIDI preset menu.
3. Open the identically named AVC and confirm the same preset name is active.

Use **ButtonGlow** as the rollback, **ButtonPulse FFT** for the strongest
music-reactive controller performance, and **ScreenPulse** for the screen-first
look.

The temporary loss of the background during earlier testing was live runtime
state caused by a soloed layer; it is not encoded in these saved editions.
