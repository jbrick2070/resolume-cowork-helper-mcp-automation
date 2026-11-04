# Studio One - Sume clip prompts (math + motion edition)

*Everyone forgets. The record doesn't.*

Forty clips, one per scene, as a photographic floor under the generators. Every prompt has two
parts: a **construction** (the curve, lattice, symmetry or field the picture is built on) and a
**motion law** (what moves, at what rate, with what easing, over what period). Periods divide
the clip length, so every clip closes on itself: 5 s clips use periods of 5, 2.5 or 1.25 s;
10 s clips use 10 or 5 s. The scene's generator is in brackets so clip and generator share one
construction.

## Settings

| | |
|---|---|
| Model | Gemini Omni Flash 1.1 (4K). Fallback Wan 3.0. Seedance 2.0 for 2.2 and 5.3 if Omni Flash invents faces. |
| Length | 5 s. 10 s for clips marked *long*. |
| Aspect | 16:9, highest resolution offered |
| Loop | Periods are chosen to close at the clip end, so a straight loop should land. If it does not, Resolume Ping Pong. For one-way motions, Sume Create Video with the same still as Start and End frame. |
| Tempo | In Resolume set the clip to BPM Sync and the stated period becomes beats: a 2.5 s period at 120 BPM is 5 beats, at 96 BPM it is 4. |
| Red | only in 3.3, 3.6, 3.7 and 5.8. Every other prompt carries "no colour". |

**Suffix on every prompt:** `Silver-gelatin 1938 newsreel, black and white, no colour, heavy
film grain, halation on lamps, charcoal blacks, ivory highlights. Locked camera. No text, no
captions, no lettering, no logos, no recognisable faces.`

**Test set, one per deck, about $2:** 1.3 Facing Mics, 2.4 The Cap, 3.2 The Lobby, 4.4 The Roof,
5.3 Flashbulbs. Judge whether the engine honours the construction and the period before the rest.

## Deck 1 - Studio One (CBS, 8:00 pm, 30 October 1938)

1. **8 PM Air** (spiral) - Construction: studio clock from directly below, dial centred, numerals as a 12-fold ring, the bulb above throwing Airy rings whose radii grow as the square roots of 1, 2, 3. Motion: second hand rotates at 6 degrees per second, constant, 30 degrees over the clip; the Airy rings breathe in radius by 3 percent on a 2.5 s sine.
2. **Roll It** (rings) - Construction: transcription lathe from straight above, 16-inch disc, groove an Archimedean spiral r = a + b·theta of constant pitch, cutting head on a radial line. Motion: disc at 33 1/3 rpm, exactly 2.78 turns in 5 s; acetate curl grows as a helix at one turn per second, shed at the end.
3. **Facing Mics** (figure-8 grille) - Construction: RCA 44-BX through its own grille from behind, two hexagonal meshes rotated 7 degrees, moiré fringes with spacing of about 8 mesh cells, the lamp beyond as a Gaussian bloom through the diamond. Motion: the rear mesh rotates 1 degree over 5 s so the fringes roll one full fringe-width, linear, no easing.
4. **Foley Table** (rings) - Construction: straight down into a cast-iron pot, a jam-jar lid on the rim, capillary rings with wavelengths in ratio 2:1 interfering as a standing pattern. Motion: lid scrapes a quarter of the rim per 1.25 s with sinusoidal speed, rings launch on each scrape and decay in 2.5 s.
5. **Giant Cube** (metaballs, strobe) - Construction: nine motors in a 3x3 lattice on a bench, shot from the bench end so the lattice collapses to one-point perspective, shafts as nine discs. Motion: shafts spin at 1, 2, 3 ... 9 Hz so the aliasing differs on each; a flashgun fires once at 2.5 s and freezes them for one frame.
6. **Orchestra** (lines) - Construction: 27 music stands from the catwalk straight down, three concentric arcs of nine at radii in ratio 1 : 1.6 : 2.6, pages as white rectangles at the golden angle of 137.5 degrees. Motion: a page-turn ripple propagates outward from the centre at one arc per 1.25 s with ease-out, repeating every 5 s.
7. **The Glass** (lines, rings) - Construction: control-booth window at a 20-degree dutch tilt, two VU needles reflected in the glass, the reflection doubled by the pane into two images offset by 2 percent, amber booth glow behind. Motion: needles trace a 3:2 Lissajous (x = sin 3t, y = sin 2t) with period 2.5 s; the double image drifts apart 1 percent and back on a 5 s sine.
8. **Dead Air** *(long)* - Construction: one microphone on a stand in an empty studio from floor level, linoleum seams converging to one vanishing point behind the stand, the lamp cone a triangle enclosing the stand. Motion: dust falls through the cone at constant velocity, 1 frame-height per 10 s, Brownian jitter of 2 percent; nothing else moves.

## Deck 2 - Grovers Mill (the accounts)

1. **Observatory** (dome rings, Mars disc) - Construction: inside the dome looking up the tube to the slit, dome ribs as meridians converging at the zenith, the slit a 10-degree sector, a bright disc of radius 1/40 frame. Motion: dome rotates 10 degrees over 5 s with ease-in-out; the disc crosses the slit on a straight line at constant speed, entering at 1 s and leaving at 4 s.
2. **The Farm** (headlight metaballs, crowd lines) - Construction: two headlight discs at a farm gate at night, each a Gaussian blob, beams as two cones crossing at the lens; crowd silhouettes as a picket of verticals at Poisson spacing; camera at waist height. Motion: headlight blobs merge and separate as metaballs on a 5 s sine (cars rocking); breath plumes rise at 0.1 frame per second and dissolve in 2.5 s.
3. **The Hum** (tunnelines) - Construction: the cylinder end-on from the pit floor, ribs as rings receding to a vanishing point just above centre, each ring 0.85 the radius of the one before. Motion: a standing wave of 3 nodes along the tube, amplitude 2 percent of radius, period 1.25 s; the vanishing point does not move.
4. **The Cap** (rings turning) - Construction: the cylinder cap from directly above, a screw thread of ten concentric turns, one work lamp from the left so each turn is half lit. Motion: cap rotates 90 degrees clockwise over 4 s with ease-in, cubic, then stops dead for 1 s; flakes shed along the tangent at the stop.
5. **Emergence** (spiral feelers, strobe) - Construction: from under the pit rim, a wet ribbed tentacle as a logarithmic spiral r = e^(0.3·theta), each turn 1.6 times the last, never fully in frame. Motion: the spiral unrolls by one full turn over 5 s with ease-out; the flashlight stutters at 4 Hz with a 50 percent duty cycle.
6. **Heat Ray** (lines, wash) - Construction: a single beam from a parabolic mirror, a horizontal line through the exact frame centre, shot from a ditch so the field is a plane below the line, headlights along it at geometric spacing. Motion: beam sweeps 40 degrees over 5 s at constant angular rate; headlights extinguish in order of distance, one per 0.5 s.
7. **Field Lost** - Construction: black field, one microphone cable as a catenary y = cosh(x) across wet grass in the foreground, a dropped flashlight as the only source. Motion: flashlight rolls in a damped arc, three oscillations decaying by half each, settling at 4 s; then 1 s of nothing.
8. **Forty Dead** (stone wall lines, black smoke) - Construction: a dry-stone wall shot along its length at ground level, courses as parallels to a vanishing point at frame right, embers behind, smoke as a turbulent sheet. Motion: smoke advects left to right at 0.2 frame-widths per second with Kelvin-Helmholtz curls; embers flicker at 8 Hz with 1/f intensity.

## Deck 3 - The Visitors (the alternate history)

1. **The Curb** (sedan shaper, two homburgs) - Construction: a black 1938 sedan at a wet curb from the gutter, looking up: the body one dark ellipse, its reflection the mirror ellipse below the waterline, two hat brims as two arcs above the lens, rain as verticals in a lamp cone. Motion: rain at constant 1 frame-height per 0.5 s; the reflection ellipse shimmers with a 2 percent ripple at 2 Hz; the brims pass left to right over 5 s at walking pace.
2. **The Lobby** (revolving door spiral, lift dial rings) - Construction: brass revolving door from directly above the hub, four leaves at 90 degrees, floor as radial marble sectors, a lift floor-dial arc of 180 degrees reflected in the brass; 4-fold symmetry. Motion: the door turns 90 degrees over 5 s with ease-in-out so the frame ends as it began; the dial needle sweeps 30 degrees and back on the same 5 s.
3. **The Card** (red line on card) - Construction: a white credential card on a desk, macro, a 3:2 rectangle filling the frame, one red pencil line on the diagonal. Motion: the line is drawn corner to corner over 5 s at constant speed with a slight hand tremor of 1 percent at 3 Hz; red is the only colour.
4. **The Latch** (porthole rings, keys) - Construction: a round porthole from the corridor, a circle centred in frame, the console glow a second concentric circle inside it, a ring of keys hanging as a pendulum across the chord. Motion: keys swing as a simple pendulum with period 2.5 s and amplitude 15 degrees, undamped, two full swings per clip.
5. **Gloves Off** (patch cords, bare hand) - Construction: a patch bay from six inches, a 12x8 grid of jacks, cords hanging as catenaries, one bare ridged hand resting on the grid, fingers as five parallels. Motion: the hand enters from the right over 2 s with ease-out, rests for 3 s; the catenaries sway at 0.5 Hz with 1 percent amplitude from the touch.
6. **Red Line** (red pencil) - Construction: typed script page, macro, type lines as a ruled grid at constant leading, one red pencil line through one sentence. Motion: the line is drawn left to right over 4 s at constant speed, then holds for 1 s; red only on the graphite.
7. **Station Break** (mic grille, red line at eye) - Construction: an RCA mic from the announcer's chair tilted up 30 degrees, the grille a rhombus centred in frame, one thin red horizontal line floating in the lamp glass at the rhombus's horizontal diagonal. Motion: the red line pulses in brightness on a 2.5 s sine between 40 and 100 percent; the lamp halo breathes in antiphase.
8. **Clock Held** (spiral stopped) - Construction: studio clock reflected in a dark window, the second hand frozen at 41 past, the reflection doubled into two circles 2 percent apart in scale. Motion: the hands do not move; the two reflections drift 0.5 percent apart and back on a 5 s sine; grain is the only other motion.

## Deck 4 - New York (the second half)

1. **The Battery** (gun lines, distant tripod, muzzle strobe) - Construction: artillery on a ridge at night from behind the crew at knee height, five barrels as parallels at 15 degrees elevation, a three-legged shape on the horizon as an isosceles triangle. Motion: muzzle flashes fire left to right at 1 per 0.5 s with a 1-frame flash and a 0.5 s smoke decay; the triangle takes one step toward the camera at 4 s.
2. **Bombers** *(long)* (bomber rings, black smoke) - Construction: nine bombers in a V from directly below through low cloud, each prop a disc with a 3-blade stroboscopic ghost, smoke rising past them in laminar sheets. Motion: formation crosses the frame bottom to top over 10 s at constant speed; props show the wagon-wheel effect reversing direction once at 5 s; smoke rises at half the formation's speed.
3. **The Dive** (tunnelines, nose glazing) - Construction: inside a bomber's glazed nose, the glazing a lattice of ribs converging on one vanishing point dead ahead, the dark machine at that point. Motion: the machine grows exponentially by a factor of 4 over 5 s (r = r0 · 4^(t/5)), the ribs rush outward at the matching rate, no roll, no yaw.
4. **The Roof** *(long)* (skyline line scape, smoke) - Construction: Manhattan skyline from a rooftop over the parapet edge, the skyline as a jagged line scape in three parallax layers, the smoke front as a turbulent sheet lit from below. Motion: layers drift right at 1, 2 and 3 percent of frame per 10 s; the smoke front advances toward the camera at 0.1 frame-heights per second with eddies at 0.5 Hz.
5. **Black Smoke** (abstract field) - Construction: inside black smoke, the whole frame a 1/f noise field, one street lamp a Gaussian halo at the exact centre. Motion: the field churns as curl noise with a 2.5 s period, the halo radius pulses 10 percent on a 5 s sine, nothing resolves.
6. **The Window** (tall window lines, avenue metaballs, rain) - Construction: a tall studio window at night from the sill looking down, mullions a 2x6 grid, rain tracks as curved paths on the glass, the avenue below a receding column of shop-window blobs at diminishing intervals. Motion: rain tracks descend at 1 pane-height per 2.5 s with random lateral walk; the avenue blobs flicker independently at 0.2 to 1 Hz.
7. **Nineteen** (machine lines, bird metaballs) - Construction: nineteen tall three-legged machines in Central Park at dawn seen from the ground through bare trees, on a hexagonal lattice to the horizon, birds as a flock in a torus above. Motion: the machines are still; the torus of birds rotates once per 5 s about a vertical axis, birds as metaballs merging at the near side of the ring.
8. **Peaceful Study** (shelves lines, pen) - Construction: a desk lamp over books, a fountain pen writing, shot from inside the bookshelf between two volumes so the frame is a narrow vertical slot, spines as horizontal bands top and bottom. Motion: the pen writes one line left to right over 4 s with a 5 Hz tremor of 1 percent, lifts and returns over 1 s.

## Deck 5 - Morning After (9:00 pm and after)

1. **9 PM Doors** (uniform lines, spiral, flashbulb) - Construction: heavy double doors opening toward the lens from floor level, each door edge sweeping a 90-degree arc, dark uniforms as a row of equal verticals behind, one flashbulb at frame centre. Motion: doors open over 2 s with ease-out and hold; the flashbulb fires at 2 s for one frame and its smoke rises for the remaining 3 s.
2. **Switchboard** (checkered sea of light, jacks) - Construction: a telephone switchboard from straight above, a 20x12 grid of lamps, cords as catenaries, operators as hands only. Motion: lamps light along a diagonal wavefront from top-left to bottom-right over 5 s, one diagonal per 0.16 s, so the last lamp lights as the clip ends.
3. **Flashbulbs** (mic battery, press metaballs, strobe) - Construction: eleven press microphones on a table shot from the table surface, a comb of verticals at equal spacing, flashbulb sources at random positions. Motion: flashbulbs fire as a Poisson process at 2 per second, each one frame bright then 0.5 s of smoke; microphone shadows swing with each flash.
4. **Headlines** (column rules, front page) - Construction: a front page through the press rollers, eight columns as parallel verticals, halftone dots as a 45-degree lattice visible in macro, no words readable. Motion: the page moves upward at exactly one page-height per 5 s, constant, so the loop is seamless by construction.
5. **Two Percent** (audience bar) - Construction: a rooftop of one hundred radio aerials at night in a staggered grid, only two lit at the base, rain. Motion: the two lit bases flicker independently at 1 and 1.5 Hz; rain falls at constant speed; nothing else moves.
6. **Hooper vs Myth** (the record lines) - Construction: a stack of newspapers under a lamp from the desk end at paper height, the stack as horizontal lines, a ruler across them as one diagonal. Motion: dust settles through the lamp cone at constant speed; the lamp filament breathes 5 percent on a 2.5 s sine.
7. **The Disc** (rings, small circle) - Construction: a transcription disc in a rehearsal rack through the rack slats, slats as vertical bars at equal spacing, the disc an arc behind them, a small paper circle on its sleeve as the one bright point. Motion: the disc rotates 1/4 turn over 5 s with ease-in-out so the paper circle passes behind exactly two slats and back.
8. **Next Week** (script, already red) - Construction: a fresh script cover on a desk, macro, the page a rectangle filling the frame, one red pencil mark as a short diagonal in the upper-left quadrant. Motion: the lamp dims to black over the last 2 s on an ease-in curve; red only on the mark.

## Built in (2026-11-03)

All forty scenes are rendered, 1920x1080, 24 fps, 5.17 s, picture only (The Lobby desaturated),
and converted to DXV 3 (Normal Quality, No Alpha). Twenty came from Sume (HeyGen Video 1, free
tickets, native 1080p) and twenty from MiniMax H3 run locally in ComfyUI on a 16 GB card
(`render/`: text-to-video, native 1920x1088 cropped to 1080, the official 8-step turbo LoRA at
6 steps, int8 video VAE, about 16 minutes a clip). `add_film_layer.py` splices them under the
instrument:

| | |
|---|---|
| `Studio One - War Of The Worlds 1938 FILM.avc` | the composition with a ninth layer, **FILM**, at the bottom (layer 1, Alpha, crossfader A); BED and everything above composite over it with their existing blends |
| `APC 40 MK II - Studio One FILM.xml` | the same preset with every layer path moved up one, so the pads, faders and scene buttons do exactly what they did |
| Play Mode | every film clip is **Bounce** (ping-pong), so it loops without a cut; the layer has no pad row and changes with the scene |

Sume: 1.2 1.3 1.6 1.8, 2.2 2.4 2.5 2.6, 3.1 3.2 3.4 3.6, 4.2 4.3 4.4 4.7, 5.1 5.2 5.3 5.4.
Local H3: the other twenty, from the prompts in `render/make_prompts.py` (the same constructions
as this sheet, reworded to avoid period dates, which make some video models pillarbox to 4:3).

**The clips are not stored in the repository** (about 2.4 GB). Download them from the
[release](https://github.com/jbrick2070/resolume-cowork-helper-mcp-automation/releases/tag/studio-one-film-clips-v1) and extract both zips into `C:\Resolume Clips\`, or into any folder and
run `relink_film.py` on it. To rebuild them yourself, render each scene from the prompts here (or
`render/`), put the files in `media/` as `S1_<deck>_<scene>_<slug>.mov` or `.mp4`, and run
`python packs/studio-one/add_film_layer.py`: it copies them to the library folder and rewrites the
composition. `verify_pack.py` asserts 8 layers, so run it against the original composition, not
the FILM one.

## Delivery

Name each clip `S1_<deck>_<scene>_<slug>.mp4` (for example `S1_2_4_the_cap.mp4`) and put it in
`packs/studio-one/media/`. Placing them as a layer under BED is a separate build step.

Dead Air has its own sheet at `packs/dead-air/docs/SUME_CLIP_PROMPTS.md` for a second pack later.
