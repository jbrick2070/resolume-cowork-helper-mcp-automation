# Session Handoff -- APC40 mkII Animated Twin V3 (rig tuning) -- 2026-07-20 late

## Core goal
Tune the visual twin (`APC40_Visual_Twin_V3_Spec_Candidate.avc`) against Jeffrey's
live rig. Work dir: `C:\Art Projects\Res_Fable\react-kit-apc40-v2-overnight\beta\streamdeck-animated-v3\`.
Append-only: R1 / kit / MIDI preset byte-untouched. NEVER save the comp.

## Shipped this session (all QA PASS, live on rig, awaiting Jeffrey's bless)
1. **ABGR COLOR LAW**: .avc ParamColor uint32 is ABGR. rgb = (v&255,(v>>8)&255,(v>>16)&255).
   Old COLOR_BY_ID was a backwards decode. Per-layer true colors from R1 in
   `build/r1_layer_colors.json`; renderer uses `row_color(row)`.
   Grid columns: T1 blue / T2 cyan / T3 green / T4 red / T5 amber / T6 purple /
   T7 magenta / T8 white. STOP/SEL/Activator/A-B/transport amber, Solo blue,
   arm red, scenes green, Tempo red, Cue white.
2. **Grid knobs (16 rotary) + their bed arcs = hardware AMBER (240,138,36)**;
   Tempo red / Cue white keep R1 colors.
3. **Transport LEDs**: circular, floating a smidge ABOVE the key with a gap,
   specular dome. PLAY = PURE GREEN (44,230,44) -- (35,197,82) was rejected as
   aquamarine. RECORD + SESSION = red. Lit on press only.
   `TRANSPORT_LED_EXT=20` px tile growth for layers 118/120/142 -> comp was
   RE-INJECTED (injector already targets col1 "Pressed"/col2 "APC40 Live") and
   cold-open verified 150 layers/2 cols. qa allowed_mask sanctions the top-20px
   LED zone on those layers.
4. **L119 truly empty at idle**; idle = STATIC faint outline everywhere except
   the 40 grid pads (subtle 12-18% baked glow); pressed-label contrast pass.
5. **FFT (unattended, per Jeffrey's yoga note)**: all 40 grid-pad LAYER
   `video/opacity` on **external_fft**, startStop 0.55-1 (visible when quiet),
   Gain +6 dB, Fallback 1200 ms. Applied live via API AND hand-baked into the
   candidate .avc (PhaseSourceFFT species copied from Res Fable Signal.avc).
   TRAP: L1's layer Opacity ParamRange was omitted at default -- inserted.
   Cold-open verified. Pre-FFT backup: `backups/Spec_Candidate_preFFT_20260720.avc`.
   WARNING: re-running `inject_apc40_v3_spec.py` DISCARDS the FFT patch --
   re-apply it (or fold into the injector) after any re-inject.

## NOT done (Jeffrey's remaining asks)
- **Corner MIDI value ticker + corner audio waveform** = V4 Wire deliverables
  A + C in `docs/APC40_V4_MIDI_MONITOR_SPEC.md` (C added this session).
  Wire was NOT running, so nothing was built. Plan: launch Wire, confirm node
  classes, one patch -> Texture Out(s), offline-author overlay layers 151/152
  (FFGL cold-open law + registration counts).

## Reload shorthand (art-only changes)
Park on `..._V3_Base.avc` (composition:open times out then late-lands ~25 s --
poll status, never re-fire) -> robocopy `media\clips_spec` (+ bed mov) to
`C:\Resolume Clips\APC40_V3` -> reopen candidate -> `column trigger 2` ->
`clip trigger` L148 col1 + L145 col1 -> monitor inspect (API crushes dim art --
judge on the real display).

## Renderer facts
`tools/render_apc40_spec_v3.py`: ~1 s/control on device_bash; chunk
`--layers A B` in ~30s WITH `--families <all>` (--layers alone renders nothing);
`--states` filter keeps untouched states byte-identical. QA:
`tools/qa_spec_v3.py` parts movs/legend/composite/regress/report; refresh
`build/preexisting_snapshot.json` hashes after intentional changes.

## Do-not-redo
- Knob-feel MIDI mapping fix (TEMPO/CUE relative encoders) -- blessed "perfect".
- ACTIVE preset = "APC 40 MK II - Visual QA V3 Animated"; session holds live
  mappings (disk edits inert; "reset MIDI settings" loads them).

---
## Resume instructions
Fresh window: read this file + the `apc40-v3-spec-build` memory, verify rig
state matches, state the current step, wait for go.
