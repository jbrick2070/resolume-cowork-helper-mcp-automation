# EarthSearch EP01 — run sheet

One page. Everything you need between plugging in and the first frame.

---

## Before the show

1. **Plug in the APC40 mkII**, then start Resolume Avenue.
2. Open `EarthSearch_EP01_Live_Mix`.
   It selects its own MIDI preset — check the Shortcuts menu says
   *APC 40 MK II - EarthSearch EP01*.
3. **Preferences → MIDI**: `APC40 mkII` enabled as **input AND output**.
   Output is not optional — it is what lights the pads.
4. **Preferences → Audio**: any working output device. The FFT analyses the
   composition's own audio, so the audio engine has to be running, but it does
   not matter *which* device — no virtual cable, no routing.
5. **Preferences → Recording**: if you are capturing, turn **Record Audio OFF**.
   The take must be video-only; the untouched original soundtrack goes back
   underneath it in Resolve.

If the pads are dark, trigger anything once — Resolume sends the LED state on
the first change.

---

## Starting

**Press PLAY.** That is the whole procedure.

Both masters and the FFT scope start together at frame zero. Measured on this
rig at 0.00 ms drift over 20 seconds, and they stay locked because nothing on
the surface can retrigger them.

The image you get is **MASTER A, untreated**. Every effect loads bypassed,
every overlay layer is down, the crossfader is hard left.

---

## The three safety controls

| | |
|---|---|
| **PLAY** | START BOTH @ 00:00 |
| **STOP** | STOP / RESET BOTH — ejects everything, both masters back to zero |
| **STOP ALL CLIPS** or **BANK LOCK** | CLEAN / ALL FX OFF — every bank, every overlay, the scope, all to zero. Playback is not touched. |
| **RECORD** | BLACKOUT — reversible black, playback continues underneath |

Two more routes to a clean image: the **Cue Level** knob sweeps it
continuously, and the **footswitch** is a momentary — hold for clean, release
to bring it all back.

---

## Playing it

**The A ↔ B mix is the crossfader.** Hard left is pure V2, hard right is pure
V3, everything between is a true dissolve. The two versions are frame-locked
to the same cut grid, so a mid-position is a genuine double exposure of the
same moment, not two films fighting.

**Track faders 1 and 2** trim each master's level independently — use them to
dip one version without moving the crossfade.

**Track faders 3–7** bring in the five generative overlay layers. **Fader 8**
is the FFT scope.

**The pad grid launches overlay content.** It cannot touch the masters — there
is no pad on the surface that can. Fire freely.

**The effect banks** are five rows of latching toggles. Lit means active.

**Device knobs 1–5** are the five bank intensities. Pull one down and that
whole family goes dry without changing which buttons are lit.

**Track knobs** are live FFT control — depth and release per band. Watch the
SCOPE layer and tune while the show runs.

---

## If something goes wrong

| Symptom | Do this |
|---|---|
| The image is a mess and you need out | **CLEAN** (STOP ALL CLIPS or BANK LOCK). One press. |
| You need black right now | **RECORD**. Reversible; playback keeps running. |
| A master stopped | **PLAY** restarts *both* together. Never restart one alone — that is what breaks sync. |
| Nothing is reacting to the audio | Check a master is actually playing, and that Preferences → Audio has a working output device. The FFT reads the composition's own audio. |
| The pads are dark | APC40 must be enabled as a MIDI **output** as well as an input. |
| The crossfader does nothing | The two masters must be on crossfader buses A and B. The composition ships that way; check the layer headers if it was edited. |

---

## After the show

The capture is video-only by design. Bring it into Resolve and lay the
untouched original audio back underneath — the soundtrack was never altered,
mixed or rendered by Resolume.
