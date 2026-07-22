# APC40 Animated Twin V3 - SPEC refinement build report (2026-07-20)

> **FINAL EVENING STATE (rig-verified with Jeffrey, 2026-07-20): SHIPPED &
> WORKING.** After the live debugging arc below, the twin runs on the rig:
> full wall composites (tiles + bed + chassis), hardware presses TOGGLE
> controls on/off with visible active art + legends, knob/fader caps ride
> live CC, LEDs mirror connected state. Final architecture:
>
> - **Column 1 "Pressed"** (MIDI-wired via the 148 clip/1 connects) = the
>   ACTIVE / FIRE clips. Trigger style = R1's TOGGLE: press lights the
>   control, press again returns it to idle.
> - **Column 2 "APC40 Live"** = the animated idle wall (+ Tier B statics,
>   bed, chassis). Trigger it to light or reset the whole wall.
> - **Bed** additionally carries a static idle GHOST of every Tier A control
>   at breath-mean, so a toggled-off control shows a calm empty button, never
>   a hole. Idle Tier A art carries NO legend (empty buttons); the name +
>   MIDI address appear on the pressed art only.
> - **Brightness**: authored contract levels x3 gain on pressed/active/static
>   art, x1.5 on idle (press "pops"); chassis at its own designed level.
>   Encoding: premultiplied rgb + TRUE alpha (see serializer law 5, revised).
> - **Media plays from `C:\Resolume Clips\APC40_V3\`** (robocopy mirror of
>   the append-only `media/` tree; refresh with Avenue parked on the Base
>   comp - it LOCKS loaded files).
> - The full 203-shortcut preset copy is installed as
>   `APC 40 MK II - Visual QA V3 Animated` in
>   `OneDrive\Documents\Resolume Avenue\Shortcuts\MIDI\` (the live
>   `Visual QA` preset already carries all 203; MIDI Output must be enabled
>   in Preferences > MIDI for hardware LEDs).
>
> **Punch list for the next session (Jeffrey's review):**
> 1. TEMPO + CUE show no visible response to turning - read the preset's
>    CC13/CC47 mappings and match the art/param they actually drive.
> 2. The "Stop" secondary bar under PLAY reads as an anonymous grey pill in
>    idle - restyle to match its transport siblings.
> 3. Active-state button legends: bigger / higher contrast.
> 4. MIDI value monitor (corner readout of last CC/note + values) - V4 Wire
>    deliverable, alongside per-control live readouts (the reference HTML
>    look) and the note-off -> auto-unlatch preset species.

> **2026-07-20 rig update: cold-open VERIFIED on Avenue 7.27.1.** The first
> candidate cold-opened wrong (giant stretched tiles, both appended layers and
> the States column silently dropped). Root causes were found by live probing
> and fixed offline; the current candidate has been cold-opened on the rig by
> API, idle wall + States wall + native-pixel inspects all verified. See
> "Serializer laws learned" below - three new hard rules for every future
> comp injector in this repo.

Refines the V3 candidate's clip content to the approved design contract
(`react-kit/docs/APC40_SURFACE_ANIMATION_CONCEPTS.md`, restrained set +
`APC40_SURFACE_ANIMATION_REFERENCE.html`). Append-only: every prior file in
this folder is byte-untouched (hash-verified); the blessed kit and R1 are
byte-untouched (sha-pinned).

## What shipped

| Artifact | Path |
|---|---|
| 268 per-control clips (Tier A pairs + Tier B statics) | `media/clips_spec/<family>/L###_<Name>__<state>.mov` |
| Tier B bed (static arcs, slots, ticks, detent, ALL Tier B legends) | `media/APC40_MKII_V3_TierB_Bed_Alpha.mov` |
| Candidate comp (150 layers, 2 columns, 270 wired clips) | `compositions/APC40_Visual_Twin_V3_Spec_Candidate.avc` |
| Renderer / injector / QA | `tools/render_apc40_spec_v3.py`, `tools/inject_apc40_v3_spec.py`, `tools/qa_spec_v3.py` |
| Manifest (tile rects, Position X/Y, states, seam proofs) | `build/spec_manifest_v3.json` |
| QA verdict + detail | `docs/APC40_V3_SPEC_QA.md` / `.json` |
| Evidence (per-family stills, bounds overlays, idle wall) | `screenshots/spec/` |

Tier A picks, at the stated loop lengths (all full-sine, per-layer phase
offsets): 1A Ember Bed (6 s / 2 s), 2A Soft Core (5 s), 3A Quiet Rim (7 s),
4A Solid Latch (3 s), 5A LED Dome (4 s), 10B Directional Nudge (5 s),
11A Standby Rim (6 s / 2 s), 12A Pin LED witness dots (on 85% steady in idle
clips, 70-100% sine in active clips). Pad colors from each clip's original
ColorId. Tier B: value-agnostic caps only - knob cap with 12-o'clock detent
index, fader thumb-cap, centre-detent puck; zero numerals, zero tip segments,
zero lit tick counts, zero text.

Geometry contract preserved for V4: 15 arc segments on 270 deg (bed), 11
uniform fader ticks (bed), 0.04u silhouette insets, u = control short edge.

## Candidate comp wiring

* Layers 1-148 keep indices, names, Add blend, and every MIDI path - the
  203-shortcut preset works unchanged (`clips/1` = column 0).
* Column 1 "APC40 Live" = idle / static clips (TextBlock sources swapped to
  VideoFormatReaderSource, clip video-track canvas = tile dims, Transform
  pixel-true: Position = tile centre - (960, 540), Scale/W/H = 100). Clip
  `Param name="Name"` set per deck-label law; comp renamed in BOTH name
  fields. Stale R1 per-layer opacity/master values normalized to 1.
* Column 2 "States" = a full wall: 120 Tier A active/fire clips + the 28
  Tier B statics + bed + chassis cloned in, so triggering the column previews
  every state without ejecting the frame (empty cells eject their layers).
  300 clips total.
* Layer 149 `V3 Tier B Bed` (static, never MIDI-driven -> Tier B legends can
  never move), layer 150 `V3 Chassis Frame` (reused, previously QA-passed
  chassis MOV). Both Add blend, both present in both columns.
* CRLF preserved throughout (R1 is uniformly CRLF); UTF-8, no BOM.

## Serializer laws learned (rig-proven 2026-07-20, apply to ALL injectors)

1. **Registration counts gate parsing.** `<Composition ... numLayers numColumns>`
   and `<Deck ... numLayers numColumns numLayersWithContent
   numColumnsWithContent>` are trusted at load; any layer/column nodes beyond
   the counts are SILENTLY dropped (this is why the first candidate lost
   layers 149/150 and the States column). Patch the counts with the nodes.
2. **The clip video-track canvas is the render quad.** Avenue draws the
   clip's `VideoTrack Params Width/Height` 1:1 in composition space and
   stretches the source into it. R1's text clips inherited 1920x1080, which
   blew 106x44 tiles up to giant blurs. Canvas = file dims -> native, crisp,
   no resampling. (Avenue-saved video clips carry canvas == file dims;
   specimen: `build_gen_src.avc`.)
3. **Never resize a clip canvas mid-session.** A live width/height write +
   retrigger renders BLACK (same family as the FFGL cold-open law). Canvas
   dims are load-time facts - change them offline, reopen.
4. Avenue omits `ParamRange` nodes whose value equals the default (the stop
   clips carry no Position Y), and the CC-fanned clips serialize Opacity
   before Width - injector regexes must not assume presence or order.
5. **Alpha semantics (REVISED after the full saga): ship PREMULTIPLIED rgb
   with TRUE alpha.** Three encodings were rig-tested: straight alpha
   displays translucent elements at full rgb (wrong levels); flattened
   opaque-black makes full-frame layers OCCLUDE everything beneath (the
   bed/chassis hid the whole wall - Avenue's mixer honors opacity as
   coverage even on Add); premultiplied rgb + original alpha gives correct
   levels AND correct transparency. `premultiply()` in the renderer is the
   reference implementation (plus display gain).
6. Avenue LOCKS loaded media files (Windows share locks) - deleting or
   safely replacing a mov needs the comp switched away first. And the MCP
   monitor snapshot/inspect attenuates dim content heavily: spec-level
   (20-35%) elements read near-black in probes while being correct on a real
   display - judge restrained art on the actual output, not the API monitor.

Because Tier B legends live in the static bed, the live CC fan-out
(posy/rotz/opacity, inherited from R1) now moves ONLY the caps - a moving
thumb-cap / rotating knob cap is live truth from the hardware, and text never
moves. This closes the old V3's text-law breach without touching the preset.

## Deviations from the contract (with reasons)

1. **ProRes 4444 alpha, not DXV3 HQ.** The local ffmpeg dxv encoder is
   DXT1-only, no alpha. ProRes is the in-repo precedent and Avenue reads it;
   transcode in Alley later if playback perf asks for DXV.
2. **One-shots (scene fire, stop fire, bank nudge) bake as a loop:** one
   attack/decay envelope + settled tail, period = the stated loop length
   (repeat cadence 0.14-0.2 Hz, far below the 2 Hz law). A true
   play-once-and-hold needs a clip playmode XML species with no rig specimen
   yet - capture one, then flip these clips.
3. **Pad legend plate is text-sized**, not 0.14u (0.14u = 6 px at these 44 px
   pads; the reference HTML's own plate is text-sized at 40% black - matched).
4. **Active states are wired but not MIDI-switched.** Note-on -> `clips/2`
   connect + note-off -> `clips/1` is a PROPOSED shortcut species
   (CONTROL_LOGIC section 6: make one in the UI, save, diff, clone). Until
   then: trigger column 2 by mouse/column for demos.
5. **Witness active sine** = integer cycles fitted to the parent loop
   (seamlessness law outranks the exact 2 s witness cycle).
6. **Legend contrast floors documented:** combined-glyph min 3.2:1 on pads
   (the 60%-alpha address line is contract-fixed; label line alone > 4.5:1);
   track-button OFF state is spec-dim (unlit LED, glyph 40% over 6% wash).

## QA - all gates PASS (`docs/APC40_V3_SPEC_QA.md`)

Bounds on shipped movs (silhouette-inset masks, witness cells): 0 violations.
Ink overlaps: 0 (8 benign rect abutments from the V2 re-centred rings).
Loop seams: 0 failures (wrap frame bit-exact pre-encode, decoded wrap step
verified). Durations: 0 mismatches. Chassis red inside controls: 0. Legend
moved: 0. Idle-wall red share: 12.8% (< 30%). Bed ink inside Tier A rects: 0.
Pre-existing files changed: 0. R1 sha pinned OK. Candidate parses, BOM-free.

## Cold-open - VERIFIED on the rig (API-driven, 2026-07-20)

Machine-checked over the live API: 150 layers / 2 columns register, column 1
lights the full idle wall (all 150 clips playing, tiles at native size,
verified with native-pixel inspects on pad / knob / fader zones), column 2
shows the complete States wall with the frame intact, diagnose reports
healthy playback (300/300 slots). Remaining HUMAN gates for the bless:

1. Play the APC40: pads/faders/knobs land on the right controls (preset
   unchanged); knob caps rotate / thumb caps ride with live CC.
2. Judge the restrained aesthetic at full size + over time (loop seams,
   breath rates, legibility from performance distance).
3. If anything misbehaves: the prior candidates and R1 are untouched -
   `APC40_Visual_Twin_V3_Animated_Candidate.avc`, `..._V3_Base.avc`, or
   `APC40_Visual_QA_148.avc`. Deleting `media/clips_spec/`, the bed MOV, the
   spec comp, and the three `*_spec_v3.py` tools removes this build wholly.
   Note the old `..._V3_Animated_Candidate.avc` carries the same latent
   registration-count bug (its 2 appended layers will drop at load).

## Punch-list session 2 - items 1-3 fixed, item 4 specced (2026-07-20 pm)

All four review items addressed. **No comp change** - only clip ART changed, at
identical tile dims/positions, so the shipped candidate plays the new movs once
the mirror is refreshed; the comp, R1, the kit and the preset are byte-untouched.

1. **TEMPO / CUE now read on turn.** Read the preset: CC13 (Tempo) drives
   `L148/.../transform/rotationz` (relative encoder, endless), CC47 (Cue) drives
   `L145/.../transform/rotationz` (0.125..0.875) **and** `.../opacity`
   (0.35..1). Both caps are Tier B `small_rotary`. Their thin centred detent
   read as no motion when turned. `render_knob_cap` now gives the two DRIVEN
   caps a bold single-sided needle + bright rim + a tip witness dot + hub:
   the tip dot travelling the rim is the clearest turn cue, the asymmetry makes
   direction unambiguous, and the brighter body lets Cue's opacity swing read.
   Jeffrey's call: the SAME needle now also goes on the 16 grid `rotary` knobs
   (they ride the same rotationz CCs) for one consistent reads-on-turn knob
   family - the 16 rotary statics were re-rendered too.
2. **Stop secondary bar de-anonymised.** Root cause: its `witness_box` equals
   its `label_box`, so `draw_witness` no-oped and it had no LED while its
   transport siblings (Play/Record) show a corner LED. `render_transport` now
   draws a right-centre status LED for the degenerate-witness (secondary_text)
   case, inset well inside the silhouette (bounds-safe).
3. **Pressed legends bigger + higher contrast.** `draw_legend2` (only ever
   called for lit states) now uses larger glyphs, a dark contrast stroke under
   light labels, and a lifted address line; track-button legends get the stroke
   without enlarging (their address hugs the corner witness cell). Idle art is
   untouched (still legend-free empty buttons).
4. **MIDI monitor = V4 Wire.** Confirmed not feasible on a pre-rendered
   Avenue twin; full build spec in `docs/APC40_V4_MIDI_MONITOR_SPEC.md`
   (corner last-event ticker + per-control readouts + note-off auto-unlatch).

Re-rendered only the changed states (139 movs: all active/fire + the 2 small
caps + the 16 grid rotary statics + Stop idle) via a new
`render_apc40_spec_v3.py --states` filter that preserves untouched states
byte-identical. Originals backed up under
`backups/spec_v3_punchlist_bak_20260720/`. QA harness (movs/legend/composite/
regress) all gates **PASS**: 0 bounds/seam/duration/chassis-red, legend contrast
min 3.31 (floor 3.0), 0 ink overlaps, red share 0.198, 0 protected files
changed, R1 sha pinned, candidate parses, BOM-free. The regress snapshot moved
off the environment-specific `/tmp` path to `build/preexisting_snapshot.json`
(override with `SPEC_V3_SNAPSHOT`).

## Rig verification (refresh mirror with Avenue parked on Base, then reopen)

```powershell
cd "C:\Art Projects\Res_Fable\react-kit-apc40-v2-overnight\beta\streamdeck-animated-v3"
# 1. In Avenue: open APC40_Visual_Twin_V3_Base.avc (parks off the candidate so
#    Windows releases the loaded movs), THEN run:
robocopy ".\media\clips_spec" "C:\Resolume Clips\APC40_V3\clips_spec" /MIR /NFL /NDL /NJH /NJS
# 2. Reopen APC40_Visual_Twin_V3_Spec_Candidate.avc, trigger column 2 to preview
#    the states wall, turn TEMPO + CUE and watch the needle/tip-dot sweep.
```

## Re-run / verify on Windows (PowerShell)

```powershell
cd "C:\Art Projects\Res_Fable\react-kit-apc40-v2-overnight\beta\streamdeck-animated-v3"
python tools\qa_spec_v3.py --part movs --layers 1 148
python tools\qa_spec_v3.py --part legend --layers 1 148
python tools\qa_spec_v3.py --part composite
python tools\qa_spec_v3.py --part regress
python tools\qa_spec_v3.py --part report
```

(The injector needs `lxml`; the full QA parts `movs` / `legend` /
`composite` additionally need numpy, Pillow, and ffmpeg on PATH. The comp in
`compositions/` is already built and validated - the block above only
re-verifies it.)
