# APC40 mkII Animated Surface Concepts

Purpose: Stream Deck-grade animated "lit surface" treatments for the on-screen APC40 mkII twin, rendered as seamless looping vector clips in Resolume (1920x1080, black background). 3 concepts per control-surface type, idle + triggered/active states.

Companion file: `APC40_SURFACE_ANIMATION_REFERENCE.html` (same folder) - a live, clickable browser demo of the 12 recommended picks (restrained set) showing the exact geometry, colors, and timing to match. Value readouts in the demo are V4-only; see the roadmap section.

## Global build rules (apply to every concept)

- **Units.** `u` = the control's short edge. All radii, insets, and travel are fractions of `u`, so concepts scale from pads to faders without rework.
- **Bounds law.** Every lit element is clipped to the control's silhouette path, inset >= 0.04u. Blooms and glows are *inner* radial gradients rendered inside that mask - a "brighter" moment raises opacity/luminance only, never geometry. Nothing can spill at peak by construction.
- **Text law.** The legend (label + MIDI address) is a separate topmost layer, static, never scaled, scrolled, or warped. Default legend: #e6e6e6 at 90% (label), 60% (address). When a concept fills the surface above ~55% luminance, the legend flips to dark knockout #0c0c0c (a state swap, not an animation of the text). Where a fill animates, the legend sits on a fixed darkened plate so contrast never drops below ~4.5:1.
- **Palette discipline.** Unlit surface base #101010, rims #1a1a1a-#242424. State colors only: red #e83c2e, green #3cd05a, amber #f5aa22, cyan #28c8dc, blue #5a78ff. Chassis red #b51d35 never appears inside a control. Red-family controls (stops, arms) keep steady-state red small (rims, chips, dots); bright red exists only in trigger moments, so the wall never reads all-red.
- **Motion discipline.** All idle cycles are full sine periods (seamless by construction), ease in-out. Trigger events are single attack/decay envelopes (>= 120 ms attack visible, no repeats faster than 2 Hz) - never strobes. No scanning bars, wipes, marquees, or sweeps anywhere; level-fills below are meter reads (value-driven), not traveling bars.
- **Value-driven vs looped.** Fader thumbs, crossfader puck, knob arcs are positioned by MIDI value (dashboard-driven), not by the loop. The loop animates the surface around them; stated loop lengths are the idle breathing cycle.

---

## 1. Clip pad - rounded square - "G1-5 N0/C1" - color varies per pad (ColorId)

**1A. Ember Bed**
- Idle: centered radial gradient (radius 0.75u, clipped, inset 0.04u) breathing 22% -> 30% -> 22% opacity, 6 s sine. Constant 1 px rim at 35%.
- Triggered (clip playing): 90 ms ease-out attack to 85% center, 500 ms release into a sustained playing-breath 55-70% at 2 s cycle. On stop, 700 ms decay to idle.
- Text: two-line legend centered on a 0.14u-tall darkened plate (40% multiply); the gradient passes under it.
- Color: the pad's own ColorId state color. Loop: 6 s idle / 2 s active.

**1B. Inset Keyline**
- Idle: 1.5 px stroke inset 0.08u following the rounded-square silhouette, 40% -> 60% over 4 s; interior flat 8% fill.
- Triggered: stroke to 100%; a ghost stroke expands inward 0.04u once (200 ms) and dies; interior holds 20% while playing.
- Text: centered on the near-dark interior - always readable, no plate needed.
- Color: pad ColorId. Loop: 4 s.

**1C. Quad Corners**
- Idle: four corner glows (radial, radius 0.3u) fading to zero by 0.35u from center; opposing pairs crossfade 25% <-> 45% over 8 s (a slow seesaw, no rotational read).
- Triggered: all four corners to 80% plus one 120 ms center bloom, settling to 50% while playing.
- Text: centered in the guaranteed-clean center zone.
- Color: pad ColorId. Loop: 8 s.

**Pick: 1A Ember Bed** - closest to a real backlit silicone pad, and the only one of the three that stays visually quiet when 40 pads run at once.
Bounds: all gradients are clipped inner fills, inset 0.04u; peak states change opacity only. In bounds at peak.

---

## 2. Scene launch - short rounded bar - "SCENE1 N82/C1" - green

**2A. Soft Core**
- Idle: horizontal linear gradient, brightest at center, reaching zero at 90% of half-width; 18% -> 28% over 5 s.
- Triggered: 100 ms attack to 75% while the bright core widens from 0.5 to 0.8 of bar width; 600 ms release. Legend flips to knockout above 55%.
- Text: centered; core is behind it.
- Color: green. Loop: 5 s.

**2B. Launch Ledge**
- Idle: a 2 px "ledge" along the inner bottom edge (full width minus 0.08u end insets) at 45%, drifting +/-10% over 6 s.
- Triggered: ledge thickens upward into a 0.18u-tall level (LED-bar read) for 250 ms, decays 700 ms back to 2 px.
- Text: occupies the upper 2/3 of the bar, never touched by the ledge zone.
- Color: green. Loop: 6 s.

**2C. Rim + Hub**
- Idle: 1 px silhouette rim at 35% plus a faint elliptical underglow (0.5u wide) behind the legend at 12%.
- Triggered: rim to 100%, underglow to 60%, both sustained while the scene is active; 400 ms decay on release.
- Text: sits on the underglow; knockout flip not needed (peaks below 55%).
- Color: green. Loop: 4 s.

**Pick: 2A Soft Core** - reads as one lit rubber key, and center emphasis matches the single centered legend.
Bounds: gradient and ledge are clipped fills inside 0.04u inset; ledge peak height 0.18u is interior. In bounds at peak.

---

## 3. Clip stop - rounded bar - "STOP1 N52/C1" - red (restrained)

**3A. Quiet Rim**
- Idle: 1 px red rim at 30% (+/-8% over 7 s); interior a flat 4% red tint.
- Triggered (stop fired): rim to 100% and interior to 22% in 150 ms, then a 900 ms decay back to idle. One envelope per press.
- Text: white legend on near-dark interior; untouched.
- Color: red. Loop: 7 s.

**3B. Stop Chip**
- Idle: a small square chip (0.18u) at the left end of the bar at 45%; interior dark.
- Triggered: chip blooms to 100% (140 ms), interior lifts 12%, both decay 800 ms.
- Text: right of the chip, fixed; chip never overlaps the legend block.
- Color: red. Loop: 5 s.

**3C. Undertow**
- Idle: a faint red floor along the bottom inner edge, 0.06u tall at 12%.
- Triggered: floor rises to 0.1u tall at 30% (level read, 200 ms), decays 700 ms.
- Text: upper zone, clear of the floor at its peak height.
- Color: red. Loop: 6 s.

**Pick: 3A Quiet Rim** - across a row of eight stops it keeps the steady-state red footprint smallest, honoring the never-all-red rule.
Bounds: rim is stroked inside the silhouette inset; interior lifts are clipped fills. In bounds at peak.

---

## 4. Track select - rounded bar - "SEL1 N51/C1" - cyan (latching)

**4A. Solid Latch**
- Idle (unselected): dark interior, cyan legend, 1 px rim at 25%.
- Active (selected, sustained): interior fills cyan to 85%, rim 100%, legend flips to #0c0c0c knockout; sustained micro-breath 80-88% at 3 s. 120 ms crossfade in/out of selection.
- Text: same position both states; only the color state swaps.
- Color: cyan. Loop: 3 s.

**4B. Baseline**
- Idle: 2 px cyan underline directly under the legend baseline at 60%, 5 s +/-8% breath.
- Active: underline 100%, interior lifts to 30%, rim to 70%; all sustained.
- Text: white throughout (30% fill keeps contrast).
- Color: cyan. Loop: 5 s.

**4C. End Brackets**
- Idle: two vertical end caps (0.06u wide, full bar height minus insets) at 40%.
- Active: caps to 100% while a gradient from each cap meets mid-bar at 25% interior; sustained.
- Text: centered between caps, above the low interior fill.
- Color: cyan. Loop: 5 s.

**Pick: 4A Solid Latch** - matches the hardware (SEL lights solid when selected); the selected track is unambiguous from across the room.
Bounds: fills clipped to silhouette inset; caps and underline interior. In bounds at peak.

---

## 5. Track button - small square - "● N48/C1" - red/green (arm / activator)

**5A. LED Dome**
- Idle (off): whole square at 6%; the ● glyph at 40%.
- Active (on, latched): centered radial dome (radius 0.4u) behind the glyph at 90% with soft falloff, square base at 18%; 80 ms attack. Sustained micro-breath +/-5% at 4 s.
- Text/glyph: the ● doubles as the LED hotspot; the N48/C1 address sits below on the dark base.
- Color: red (arm) / green (activator). Loop: 4 s.

**5B. Full Key**
- Idle: 8% flat fill. Active: whole square at 75%, glyph and address knockout dark; 100 ms crossfade; +/-4% breath.
- Text: knockout when lit.
- Color: red/green. Loop: 4 s.

**5C. Ring Pip**
- Idle: thin ring (radius 0.35u) around the glyph at 25%.
- Active: ring scales once 0.25u -> 0.35u (250 ms, inside bounds the whole way) then holds at 90% with glyph lit.
- Text: address below ring, fixed.
- Color: red/green. Loop: 5 s.

**Pick: 5A LED Dome** - an LED under a square diffuser is exactly what the real button is; the glyph-as-hotspot makes state read at tiny sizes.
Bounds: dome radius 0.4u from center of a 1u square stays inside the 0.04u inset; ring max radius 0.35u likewise. In bounds at peak.

---

## 6. Vertical fader - tall slot + travelling thumb - "FADER1 CC7/C1 █ 127" - amber

**6A. LED Ladder**
- Geometry: 11 fixed ticks (0.25u wide, hairline tall) along the right inner edge of the slot; flat thumb cap 0.9u wide with a 1 px amber top edge. Thumb position is value-driven.
- Idle: ticks at/below value lit at 70%; the topmost lit tick breathes +/-10% at 3 s.
- Active (touched/moving): lit ticks to 100%; the top tick gets a 150 ms bloom per value step; thumb edge to 100%.
- Text: label + address on a fixed plate below the slot; value numerals fixed at top-right. Nothing travels with the thumb.
- Color: amber. Loop: 3 s.

**6B. Column Fill**
- Idle: below-thumb region filled amber at 26% with a 0.05u soft upper edge under the thumb; +/-3% shimmer over 6 s.
- Active: fill to 45%, thumb top edge to 100%; 250 ms decay after release.
- Text: fixed plate below slot; numerals fixed top-right.
- Color: amber. Loop: 6 s.

**6C. Focus Halo**
- Idle: slot dark with 1 px rails at 20%; radial halo (0.5u) around the thumb breathing 30-40% over 5 s.
- Active: halo tightens to 0.35u at 70% (focus read); after motion stops, a 250 ms residual fade.
- Text: fixed plate below slot.
- Color: amber. Loop: 5 s.

**Pick: 6A LED Ladder** - mixer-authentic and the only one that reads the value at a distance without looking at the numerals.
Bounds: ticks, fill, and halo are clipped to the slot silhouette inset 0.04u; thumb cap width 0.9u never reaches the slot edge, at any travel position including extremes. In bounds at peak.

---

## 7. Crossfader - horizontal slot + sliding puck - "X-FADE CC15/C1 █ 127" - blue

**7A. Detent Beacon**
- Geometry: a center detent tick (0.04u wide, full inner slot height) at 45%; puck with a soft blue halo (0.4u). Puck position value-driven.
- Idle: detent breathes +/-10% over 5 s; puck halo steady 40%.
- Active: puck halo to 80%; the slot half the puck is entering gains a 12% gradient lean (A/B read); 300 ms settle after release.
- Text: label + address fixed above the slot; numerals fixed right. Static.
- Color: blue. Loop: 5 s.

**7B. Dual Shores**
- Idle: 0.1u-wide end caps at both slot ends; brightness inverse to puck distance (near cap ~70%, far ~25%), easing as the puck moves; at rest both drift +/-5% over 6 s.
- Active: response sharpens; the puck leaves a 200 ms fading wake (single decaying trail, not a repeating sweep).
- Text: fixed above slot.
- Color: blue. Loop: 6 s.

**7C. Rail Bed**
- Idle: hairline top/bottom rails at 20%, groove interior 6%.
- Active: rails to 60%; puck gains a bright desaturated-blue core (#dfe6ff at 90%) inside its halo.
- Text: fixed above slot.
- Color: blue. Loop: 4 s.

**Pick: 7A Detent Beacon** - the center detent is the landmark a performer feels for; lighting it makes puck position *meaningful*, not just visible.
Bounds: detent, halo, caps, and wake all clipped to slot silhouette inset; puck travel limits keep halo inside end insets. In bounds at peak.

---

## 8. Rotary knob - circle + swept indicator - "TRACK1 CC48/C1 → 107" - amber

**8A. LED Arc**
- Geometry: 15 discrete segments on a 270° arc (start 225°, end -45°, gap at bottom), 12° segments with 6° gaps, radius just inside the knob's enclosure ring. Center hub: dark disc 0.55u.
- Idle: segments lit up to value at 75%; the tip segment breathes +/-8% at 3 s.
- Active (turning): lit segments to 100%; the tip segment blooms 120 ms per step.
- Text: value ("→ 107") on the dark hub; label + address in the bottom 90° gap. Both fixed.
- Color: amber. Loop: 3 s.

**8B. Needle + Fill Arc**
- Idle: continuous 2 px arc track at 25%; filled arc from min to value at 65%; a needle line from hub edge to rim at the value angle, glowing 70-90% over 4 s.
- Active: fill to 85%, needle 100%.
- Text: hub + bottom gap as 8A.
- Color: amber. Loop: 4 s.

**8C. Tick Halo**
- Idle: hairline ticks every 10° around the 270° range at 15%; the value tick at 100% with +/-1 neighbors at 60%/30%.
- Active: the lit window widens to +/-3 ticks, then relaxes 300 ms after the turn stops.
- Text: hub + bottom gap.
- Color: amber. Loop: 5 s.

**Pick: 8A LED Arc** - it is literally what the APC40's device knobs do (LED ring); zero learning curve and the segment quantization hides small MIDI jitter.
Bounds: arc radius sits inside the enclosure ring (per the V2 re-centered rings that enclose knob + label); blooms are per-segment opacity only. In bounds at peak.

---

## 9. Small rotary - small circle - "CUE CC47/C1 ↙ 001" - blue/red

**9A. Position Pip**
- Idle: a single pip (0.08u dot) on the perimeter at the value angle, 80%, breathing +/-10% over 4 s; 1 px rim at 20%.
- Active (turning): pip 100% with a 25°, 200 ms comet fade trailing it - one decaying trail while moving, gone at rest.
- Text: label above or on the hub, address below; fixed.
- Color: blue; pip crossfades to red over 250 ms only while cue is engaged.
- Loop: 4 s.

**9B. Hub Ring**
- Idle: dark hub (0.4u), thin blue ring at 35%.
- Active: ring to 90% plus 20% hub underglow; blue -> red crossfade (250 ms) for cue-engaged.
- Text: on/under hub, fixed.
- Loop: 5 s.

**9C. Quadrant Shade**
- Idle: interior radial gradient oriented toward the value angle (bright side = pointer side) at 20%.
- Active: 45%, reorienting smoothly with the value.
- Text: hub, fixed.
- Loop: 6 s.

**Pick: 9A Position Pip** - at this size a single pip is the only read that stays clean; the trail gives turn feedback without clutter.
Bounds: pip and trail ride the perimeter *inside* the 0.04u inset circle; trail is opacity decay, not geometry. In bounds at peak.

---

## 10. Bank arrow - directional triangle - "U N94/C1" - blue

**10A. Chevron Breath**
- Idle: triangle outline 1.5 px, inset 0.08u; apex-weighted interior gradient 10% -> 0%; outline 40 -> 60% over 4 s.
- Pressed: one fill bloom to 70% (120 ms attack, 400 ms decay).
- Text: "U N94/C1" at the triangle's visual centroid, fixed.
- Color: blue. Loop: 4 s.

**10B. Directional Nudge**
- Geometry: all lit geometry inset 0.12u from the silhouette.
- Idle: outline at 45%, +/-8% over 5 s, static position.
- Pressed: the lit geometry translates 0.05u in the pointing direction and returns (ease-out then ease-in, 300 ms total) with an accompanying 60% fill bloom. Margin math: 0.12u inset - 0.05u travel = 0.07u clearance at peak.
- Text: fixed at centroid; the text layer does NOT translate (surface moves under it).
- Color: blue. Loop: 5 s.

**10C. Apex Charge**
- Idle: a small pip at the apex at 60%, breathing over 4 s.
- Pressed: a single luminance pulse runs base -> apex in 150 ms (one event per press, trigger-only - never an idle loop), apex pip blooms and decays 400 ms.
- Text: centroid, fixed.
- Color: blue. Loop: 4 s.

**Pick: 10B Directional Nudge** - the 0.05u nudge encodes *which way the bank moves*, which is the whole job of this button, and the margin arithmetic is proven above.
Bounds: 10A/10C fully interior; 10B clearance 0.07u at peak travel by construction. In bounds at peak.

---

## 11. Transport / device - rounded bar - "PLAY N91/C1" - green/white

**11A. Standby Rim**
- Idle: 1 px white rim at 20%, white legend.
- Active (latched, e.g., playing): rim crossfades to green at 90%, interior fills green 25% with a sustained 22-28% breath at 2 s; legend stays white (contrast holds over a 25% fill).
- Text: fixed, color unchanged.
- Color: white idle / green active. Loop: 6 s idle / 2 s active.

**11B. Legend Glow**
- Idle: legend white at 70%, surface near-dark.
- Active: legend to 100% with a 0.04u green backlight halo behind the glyphs (a static glow layer under the text - the text itself never moves or changes shape), interior 12%.
- Color: white/green. Loop: 4 s.

**11C. Floor Bar**
- Idle: a bottom floor strip (0.15u tall) at 8% white.
- Active: floor turns green at 30% with a slow level breath.
- Text: upper zone, clear of the floor.
- Color: white/green. Loop: 5 s.

**Pick: 11A Standby Rim** - latch state reads across the whole transport row without lighting entire bars; white->green is the cleanest "armed vs running" grammar.
Bounds: rim stroked inside silhouette inset; fills clipped. In bounds at peak.

---

## 12. LED / witness - tiny corner dot - on / off / active

**12A. Pin LED**
- Off: 8% neutral grey. On: 85% steady state color with a 1 px soft halo. Active: 70 <-> 100% sine at 2 s.
- Text: none (the dot is the message); any adjacent label belongs to the parent control.
- Color: inherits its function's state color. Loop: 2 s.

**12B. Halo Ring**
- Off: 8% core. On: core 85%. Active: a separate 1 px ring appears at 60% around the core.
- Loop: 3 s (+/-5% core drift).

**12C. Event Bloom**
- Steady core per 12A; on each discrete event, one 150 ms bloom to a 2x-radius halo (clipped inside the dot's cell), then rest. Idle drift +/-5% over 4 s.
- Loop: 4 s idle; blooms are event-driven.

**Pick: 12A Pin LED** - a witness LED must be glanceable and boring; three brightness states do the whole job.
Bounds: halo radius capped at the dot's cell inset; blooms clipped. In bounds at peak.

---

## Constraint self-check (all 36 concepts)

| Constraint | Status |
|---|---|
| Silhouette match + strict bounds | All lit elements are masked inner fills/strokes with >= 0.04u inset; the two concepts with travel (10B nudge, thumb/puck) have explicit margin arithmetic. |
| Text rendered in, legible, static | Legend layer topmost, fixed position in every concept; knockout swaps are state changes, never motion. |
| State palette only; #b51d35 never a fill | Verified - chassis red absent from all 36; unlit surfaces are neutral greys. |
| Never everything red | Red types (3, 5-arm, 9-cue) idle as rims/chips/pips; bright red is trigger-envelope only. |
| Seamless loop, length stated | Every concept states a full-sine idle cycle (2-8 s); triggers are one-shot envelopes layered on top. |
| Banned motion | No scanning bars, barcode wipes, strobes, marquee text, or idle sweeps. 10C's base->apex pulse is a single per-press event, flagged as trigger-only. |

---

## Implementation tier split: baked DXV loops vs Wire patches

Continuous controls cannot be pre-rendered - the lit geometry (arc sweep, ladder count, thumb/puck position, value numerals) must track live CC. Those go to Wire. Binary/latching controls bake cleanly as clip pairs.

**Tier A - baked DXV loops (state = which clip plays, or dashboard-switched):**

| Type | States needed |
|---|---|
| 1 Clip pad | idle loop + playing loop (per ColorId variant) |
| 2 Scene launch | idle loop + trigger one-shot |
| 3 Clip stop | idle loop + fire one-shot |
| 4 Track select | unselected loop + selected loop |
| 5 Track button | off loop + on loop (red arm / green activator variants) |
| 10 Bank arrow | idle loop + press one-shot (per direction) |
| 11 Transport | standby loop + latched loop |
| 12 LED witness | off / on / active loops |

**Tier B - Wire patches (value-driven, dashboard-linked Float In receives the CC):**

| Type | Wire patch sketch |
|---|---|
| 6 Vertical fader | Float In (0-127) -> normalize -> thumb Y transform + instanced 11-tick compare (tick index < value -> lit opacity); internal LFO drives the top-tick breath; value readout from the same Float In |
| 7 Crossfader | Float In -> puck X transform + side-lean gradient weight; detent breath from internal LFO |
| 8 Rotary knob | Float In -> lit-segment count over 15 instanced segments on the 270 deg arc; tip = highest lit index, breath via LFO; hub value readout |
| 9 Small rotary | Float In -> pip angle (135 deg + value/127 * 270 deg); turn detection (value delta != 0) gates the comet-trail fade |

Notes:
- Feed each patch through the existing dashboard-link route (v4.4 preset / clip .avc dashboard-link XML), same as the selected-clip dial wiring.
- Wire/FFGL cold-open law applies: patches must be present at composition load - instances added mid-session render black.
- Touched/active state for Tier B = value-delta gate (moving) rather than a separate MIDI note, so no extra mapping is needed.

---

## Decided roadmap: V3 (baked, no Wire) then V4 (Wire live)

**Aesthetic: restrained set (decided).** Idle = breath only; flash budget spent on one-shot trigger envelopes.

**V3 - all baked clips, no Wire:**
- Tier A types (1-5, 10-12) ship as the recommended-pick animated clip pairs above.
- Continuous controls (6-9) get improved static art only - and must be value-agnostic so a baked frame never reads as a stale live value:
  - Knob 8: full 270 deg arc at uniform dim lit, no tip segment, no numeral; hub carries label + CC address only.
  - Small rotary 9: rim + hub art, no pip; label + address only.
  - Fader 6: slot, rails, and plate art; thumb drawn at detent or omitted; no value numerals, no lit tick count.
  - Crossfader 7: slot + detent art; puck at center or omitted; no numerals.
- Rule: anything that looks like a readout waits for V4.

**V4 - Wire implementation for 6-9 per Tier B sketches.**
- V3 static art and V4 Wire patches share geometry constants (15 segments, 11 ticks, insets, palette, type sizes) so V4 is a source swap, not a redesign.

**V3 shipped 2026-07-20.** Built to this contract in
`react-kit-apc40-v2-overnight/beta/streamdeck-animated-v3/`: 268 clips (Tier A
idle+active/fire pairs per the recommended picks at the stated loop lengths,
Tier B value-agnostic caps), a static Tier B bed layer carrying the 15-segment
arcs / 11 uniform ticks / slots / detent / all Tier B legends (so live CC
motion can never move text), and the wired candidate comp
`APC40_Visual_Twin_V3_Spec_Candidate.avc` (columns: 1 = idle, 2 = states;
203-shortcut preset unchanged). All automated gates PASS; deviations (ProRes
4444 instead of DXV3-alpha, one-shots as envelope+settled-tail loops, active
column not yet MIDI-switched pending a note-off shortcut specimen) are
reasoned in `docs/APC40_V3_SPEC_BUILD_REPORT.md` there. Cold-open VERIFIED
on the rig 2026-07-20 (150 layers / 2 columns register, idle + states walls
native-pixel checked over the API); three new serializer laws recorded in the
build report (registration counts, clip canvas = render quad, no mid-session
canvas resize). Awaiting Jeffrey's hardware pass + bless.
