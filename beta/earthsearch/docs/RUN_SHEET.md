# EarthSearch EP01 — run sheet

One page. Everything between plugging in and the first frame.

---

## Before the show

1. **Plug in the APC40 mkII**, then start Resolume Avenue.
2. Open `EarthSearch_EP01_Live_Mix`. It selects its own MIDI preset — check the
   Shortcuts menu says *APC 40 MK II - EarthSearch EP01*.
3. **Preferences → MIDI**: `APC40 mkII` enabled as **input AND output**.
   Output is not optional — it is what lights the pads.
4. **Preferences → Audio**: any working output device. The FFT analyses the
   composition's own audio, so the audio engine has to be running, but it does
   not matter *which* device. No virtual cable, no routing.
5. **Push the crossfader hard LEFT.** It is a physical fader and Resolume
   cannot see where it sits until it moves. The composition opens on pure
   MASTER A; if the fader is elsewhere, your first move will jump.
6. **Preferences → Recording → Record Audio OFF.** The take must be video-only;
   the untouched original soundtrack goes back underneath it in Resolve. One
   missed preference bakes the audio into the capture.

If the pads are dark, trigger anything once — Resolume sends LED state on the
first change.

---

## Starting

**Press PLAY.** That is the whole procedure.

Both masters and the FFT scope start together at frame zero. Measured on this
rig at **0 ms drift across 905 seconds** — more than half the episode — and
they stay locked because nothing on the surface can retrigger them.

The image you get is **MASTER A, untreated**: every effect bypassed, every
overlay down, crossfader hard left.

> **PLAY is start-from-zero, not a repair.** Pressing it mid-show restarts the
> episode. If one version drops out, use **CUT TO A** or **CUT TO B** — they
> change what you see without touching a transport.

At the end of 27:10.708 both masters **loop** together and stay locked.

---

## The safety controls

| | |
|---|---|
| **PLAY** | START BOTH @ 00:00 |
| **STOP** | STOP / RESET BOTH — ejects everything, both masters back to zero |
| **BANK LOCK** | **CLEAN / ALL FX OFF** — five effect banks, every overlay, the scope and the captions, all to zero. Playback untouched. |
| **STOP ALL CLIPS** | clears the five overlay layers. Cannot reach a master. |
| **RECORD** | BLACKOUT — reversible black, playback continues underneath |
| **Footswitch** | momentary blackout — hold for black, release for picture |

**CLEAN mutes; it does not disarm.** Every effect pad stays lit and every
overlay stays connected — the eight links are simply at zero. So bring things
back *deliberately*, one **Device knob** at a time, and un-light anything you
did not want. **Cue Level is the safe way back after a CLEAN**: it is a
relative encoder, so turning it clockwise raises all eight links together from
zero with no jump. The Device knobs are positions, and Avenue has no
soft-takeover, so their first touch sends whatever position they sit in.

---

## If something goes wrong

| Symptom | Do this |
|---|---|
| The image is a mess and you need out | **BANK LOCK** — instant silence. Then **STOP ALL CLIPS** to drop the overlays, un-light the effect pads you do not want, and bring back one bank at a time on the Device knobs. |
| You need black right now | **RECORD**, or hold the footswitch. Playback keeps running. |
| One version has dropped out | **CUT TO A** or **CUT TO B**. Do not press PLAY — that restarts the episode. |
| Both masters stopped | **PLAY** restarts both together from zero. |
| Nothing reacts to the audio | Check a master is playing and that Preferences → Audio has a working output device. The FFT reads the composition's own audio. |
| The pads are dark | The APC40 must be enabled as a MIDI **output** as well as an input. |
| A knob jumped when you touched it | Expected — Avenue has no soft-takeover, and after a CLEAN the software is at zero while your knobs are not. Come back with Cue Level, which is relative and never jumps. |
| The crossfader does nothing | The masters must be on crossfader buses A and B. The composition ships that way. |

---

## Playing it

**The A ↔ B mix is the crossfader.** Hard left is pure V2, hard right pure V3,
everything between is a true dissolve. The two versions are frame-locked to the
same cut grid, so a mid-position is a genuine double exposure of the same
moment — not two films fighting. **CUT TO A**, **CENTRE** and **CUT TO B**
(above the two master strips) are instant snaps to those three positions.

**Track faders 1 and 2 are pre-crossfader trims.** They set each version's
level *within* its own bus. If the crossfader is hard left, pushing fader 2
does nothing visible — that is correct, not a fault. Move the crossfader first.

**Faders 3–7** bring in the five generative overlay layers; **fader 8** is the
FFT scope.

**The pad grid launches overlay content and cannot touch the masters.** There
is no pad on the surface that can. Fire freely.

**The effect banks** are five rows of latching toggles. Lit means active. Some
effects carry a wet ceiling, so the bank knob's full travel is already a value
chosen for a drama.

**Device knobs 1–5** are the five bank intensities; 6 the overlays, 7 the
scope, 8 the captions. Pull one down and that family goes dry without changing
which buttons are lit.

**Track knobs** are live FFT depth and release, each named after the one
parameter it actually moves. Watch the SCOPE layer and tune while the show runs.

### Handle with care

These are all safe for playback but can bury a face mid-line. Use them between
scenes, not under dialogue:

* **RADAR** masks half the frame for half a sweep — it is a face-hider by design.
* **HOLD** (Freeze) stops the picture while the film keeps running underneath.
  Rig-tested: both masters stay in sync at 0.00 ms while it is held.
* **NEGATIVE**, **TWITCH** and **TEAR** are the loudest effects here.
* **BONE WASH** and **RED ALERT** are radial — clear in the centre, colour at
  the edge — so light arrives from outside the frame rather than covering a
  face. Nothing in this pack strobes, but a bright wash under a quiet line
  still reads as a mistake.

---

## After the show

The capture is video-only by design. Bring it into Resolve and lay the
untouched original audio back underneath — the soundtrack was never altered,
mixed or rendered by Resolume.
