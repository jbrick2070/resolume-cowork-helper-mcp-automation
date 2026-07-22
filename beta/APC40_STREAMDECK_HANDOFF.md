# APC40 MKII Stream Deck V2 source

`media/APC40_MKII_StreamDeck_Outlines_Alpha.mov` is a 10-second, 1920x1080,
30 fps ProRes 4444 clip with alpha.

It is the new V2 visual direction: an APC40 MKII-faithful set of animated
clips—not generic cards. It uses square pad cells, narrow Scene buttons,
circular track/device knobs, vertical fader strips, and a horizontal
crossfader. Each clip redraws the original control title and MIDI address in
red (`#b51d35` family), then animates only inside that control silhouette.

Render script: `tools/render_apc40_streamdeck.py`.

## Safe Avenue insertion

Create a new compare-only candidate from the saved V2 candidate. Replace the
existing V2 chassis clip source (layer 149) with this alpha MOV, retain layer
150's crossfader base only if it remains visually useful, and do not touch
layers 1–148, the R1 AVC, or the controller XML. The source has no external
audio or FFT dependency, so it does not move R1 witnesses.

The live Avenue composition was deliberately left unchanged because it reports
unsaved state and the shared Resolume gateway is not currently available.
