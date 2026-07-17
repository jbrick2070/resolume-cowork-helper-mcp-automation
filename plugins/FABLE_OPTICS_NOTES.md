# Fable Optics — A Little Museum of Moving-Image Machines

Four custom FFGL plugins for Resolume Avenue, each an homage to a real machine that
changed how pictures move. Built from the official Resolume FFGL SDK (x64 Release,
static CRT, GLSL 410 core). Install folder:
`Documents\Resolume Avenue\Extra Effects\`

FFT convention used throughout (the reference rig): Composition FFT, frequency ranges
**bass 0–0.33 / mids 0.33–0.66 / highs 0.66–1.0**, gain **+3 to +9 dB**, fallback
**100–1800 ms** (fast for percussive links, slow for breathing links).

---

## Placard 1 — Fable Gate (1895) — EFFECT, id FGTE

> "1895 - the film gate: weave, judder, dust and flicker of mechanical cinema."

**The machine.** On 28 December 1895, the Lumiere brothers ran their hand-cranked
Cinematographe before a paying audience in the Salon Indien du Grand Cafe, Paris —
projected cinema was born. A claw mechanism yanked nitrate film through a metal
gate sixteen times a second, and every imperfection of that mechanism ended up on
the screen: the frame drifted in the loose gate (weave), slipped a sprocket hole
(judder), and projected every speck of dust and gate hair forty feet wide. The
spinning shutter gave early movies their nickname: the flickers.

**Parameters (all 0–1):**

| Param | Default | On the real machine |
|---|---|---|
| Weave | 0.3 | Frame drifting in the gate — claw/sprocket registration tolerance (two slow incommensurate LFOs, up to ~1.5% of frame) |
| Judder | 0.25 | Vertical frame slips when the claw misses a perforation (random per ~0.4 s, up to 4% jumps) |
| Dust | 0.35 | Dust, lint and hairs caught in the aperture, projected huge (2–4 specks + occasional edge hair) |
| Flicker | 0.4 | Shutter blade + uneven hand-crank + arc-lamp wobble (global luma ±25% at max, pulsing vignette) |
| Era | 0.0 | The film stock itself — 0–0.33 nitrate (sepia, heavy vignette), 0.33–0.66 silver B&W (cool lift), 0.66–1 Super 8 (warm, corner blur, extra grain) |
| Grain | 0.3 | Silver-halide grain, luminance-weighted, animated per frame |
| Mix | 1.0 | Dry/wet |

Frame lines: faint black bars just inside top/bottom tremble with Judder — the
neighbouring frame peeking through the gate.

**Suggested FFT links:** Flicker ← bass 0–0.33, gain +6, fallback 300 ms (shutter
beats with the kick). Grain ← highs 0.66–1.0, gain +3, fallback 200 ms. Judder is
strong seasoning — link to mids 0.33–0.66 at gain +3, fallback 600 ms, or ride it
by hand. Weave and Era: leave static, set per scene.

---

## Placard 2 — Fable Anamorphic (1953) — EFFECT, id FANA

> "1953 - CinemaScope anamorphic glass: streak flares, oval bokeh, fringed edges."

**The machine.** In September 1953, 20th Century-Fox premiered The Robe in
CinemaScope, built on Henri Chretien's 1926 Hypergonar: a cylindrical lens that
squeezes a wide image onto normal 35mm film, then un-squeezes it in projection to
a wall-filling 2.55:1. The cylinder elements bent light differently in x and y,
and the side effects became a look Hollywood never stopped chasing: point lights
smear into horizontal blue streaks, out-of-focus highlights go oval, edges fringe
with color, and the image visibly "breathes" as the focus puller racks.

**Parameters (all 0–1):**

| Param | Default | On the real machine |
|---|---|---|
| Streak | 0.5 | Horizontal flare from the cylindrical elements — thresholded highlights box-blurred sideways (24-tap), tinted cool blue #66AAFF, screen-blended |
| Threshold | 0.7 | Which highlights are bright enough to flare (lens coating quality) |
| Squeeze | 0.3 | The de-squeeze stretch (toward 1.33x at max) plus vertical-oval vignette shaping |
| Fringe | 0.35 | Lateral chromatic aberration of early adapter glass — R/B split grows radially, up to ~1.2% at edges |
| Breathe | 0.2 | Focus breathing — slow ~0.15 Hz zoom oscillation, up to 0.5% ("anamorphic mumps" era) |
| Mix | 1.0 | Dry/wet |

**Suggested FFT links:** Streak ← highs 0.66–1.0, gain +6, fallback 300 ms (flares
bloom on hats and leads). Breathe ← bass 0–0.33, gain +3, fallback 1200–1800 ms
(the lens inhales with the low end). Fringe ← mids 0.33–0.66, gain +3, fallback
800 ms, optional. Threshold: set once per clip brightness, do not automate.

---

## Placard 3 — Fable Scanline (1972) — EFFECT, id FSCN

> "Rutt-Etra style scanline displacement."

**The machine.** In 1972, Steve Rutt and Bill Etra built the Rutt/Etra Video
Synthesizer in New York: a modified CRT whose deflection coils were wired to the
video signal itself, so brightness physically pushed the scanlines around the
tube. The image stopped being a picture and became a glowing topography — bright
areas rise as ridges of light on black. Nam June Paik, Gary Hill and a generation
of video artists made it the sound of analog video made visible.

**Parameters (all 0–1):**

| Param | Default | On the real machine |
|---|---|---|
| Lines | 0.25 | Raster density of the display (maps 16–480 scanlines) |
| Displace | 0.35 | Deflection amplifier gain — luminance pushes lines upward (to 35% of screen) |
| Thickness | 0.5 | Electron beam focus — line core width |
| Glow | 0.4 | Phosphor bloom around each line |
| Mix | 1.0 | Dry/wet |

**Suggested FFT links:** Displace ← bass 0–0.33, gain +6, fallback 100–300 ms —
the money link. Glow ← highs 0.66–1.0, gain +3 to +6, fallback 300–600 ms. Lines ←
mids 0.33–0.66 subtly (keep the range narrow, roughly 0.15–0.4), fallback 800 ms.

---

## Placard 4 — Fable Video Music (1977) — SOURCE, id FAVM

> "1977 - Atari Video Music: the first consumer music visualizer, diamonds on your hi-fi."

**The machine.** The Atari Video Music (model C240), designed by Robert Brown,
plugged into the space between your hi-fi and your television: RCA audio in,
antenna out. Raw TTL-era logic turned the music's level into hard-edged diamonds,
bars and rectangles that pumped in pure saturated color — no software, no pixels
as we know them, just a signal chain reacting to loudness. It sold poorly, was
gone within a year, and became the ancestor of every visualizer since. This is a
SOURCE plugin: drop it in a clip slot like footage; it generates on black.

**Parameters (all 0–1):**

| Param | Default | On the real machine |
|---|---|---|
| Level | 0.5 | The audio level from the hi-fi input — THE driver; shapes grow/rise/pulse with it. FFT-link this. |
| Pattern | 0.0 | The front-panel pattern buttons: 0–0.25 nested diamonds / 0.25–0.5 vertical bars / 0.5–0.75 concentric rectangles / 0.75–1 split mirror diamonds |
| Chunk | 0.4 | The coarse raster of the video circuit — quantizes to an 8–40 cell grid |
| Cycle | 0.3 | Automatic color cycling through the fixed 8-color palette (orange, magenta, cyan, green, yellow, red, blue, white), hard steps |
| Solid | 0.5 | The Solid/Hollow buttons — fill vs outline balance per ring/bar |

**Suggested FFT links:** Level ← bass 0–0.33, gain +6 to +9, fallback 100–300 ms —
this is the whole act; the diamonds must hit with the kick. Cycle ← mids
0.33–0.66, gain +3, fallback 1800 ms for palette drift that follows the song, or
leave static. Pattern/Chunk/Solid: switch per scene like the real buttons.

---

## Rebuild and deploy (any of the four)

```
& "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe" "C:\Art Projects\Res_Fable\ffgl\build\windows\<Name>.vcxproj" /p:Configuration=Release /p:Platform=x64
```

Batch helpers: `C:\Art Projects\Res_Fable\ffgl\build_fable_optics.ps1` builds
Gate + Anamorphic + Video Music; `deploy_fable_optics.ps1` verifies x64 and copies
them to Extra Effects with display names. Scanline keeps its own
`deploy_fable_scanline.ps1`. Plugin ids registry:
`C:\Art Projects\Res_Fable\ffgl\build\PluginIds.txt` (FSCN, FGTE, FANA, FAVM).
Avenue only rescans Extra Effects at startup — restart it to pick up new DLLs.
