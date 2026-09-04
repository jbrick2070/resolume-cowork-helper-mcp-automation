# FFT and audio routing

## The short version

**There is no routing.** No virtual audio cable, no second player, no Stereo
Mix, nothing to configure beyond having a working audio output device.

The composition uses **Composition FFT** (`/audioengine/compositionfft`), which
analyses the composition's own audio. The composition's own audio *is* the
original programme audio, because it is embedded in MASTER A and decoded by the
same clip that draws the picture. The analysis is therefore frame-locked to the
image by construction — there is no second transport that could drift.

That is the whole design, and it is why the obvious alternative was rejected.

---

## Why not External FFT

External FFT (`/audioengine/externalfft`) reads Resolume's audio **input**
device. To make it follow the programme you would have to either:

* loop Resolume's own output back into its own input through VB-CABLE, which
  adds a full WASAPI round trip of latency and costs you speaker monitoring,
  because Resolume has exactly one audio device; or
* play the standalone `EarthSearch 01of10.mp3` in a separate player into a
  virtual cable — two independent transports, which means guaranteed drift
  against the picture over 27 minutes.

Composition FFT has neither problem. It also survives the operator changing
audio devices, which an input-side loop does not.

---

## What had to be true for this to work

Two things were found the hard way on the rig, and both are load-bearing.

**1. Resolume Avenue 7.27.1 will not decode an MP3 audio stream in any
container.** Tested three ways against the same source:

| Container + audio codec | Clip loads with an audio track? |
|---|---|
| `.mov` + mp3 (stream copy) | **No** |
| `.mov` + `pcm_s16le` | Yes |
| `.mp4` + AAC | Yes |

The masters are mono MP3 inside Matroska, so a straight remux — however
lossless — produces a clip with **no audio track at all**, and Composition FFT
then has nothing to analyse. Every reactive parameter sits pinned at its floor
and the composition looks broken in a way that produces no error anywhere.

The performance copies are therefore `.mov` with the video **stream-copied
bit-for-bit** and the audio decoded to **PCM**. PCM rather than AAC because PCM
is the exact decode of the original MP3 — no second lossy generation, nothing
added, nothing processed.

**2. A clip needs both halves of the audio wiring in its XML.** An
`<AudioFile>` entry in `PreloadData` *and* an `<AudioTrack>` containing an
`<AudioFileSource>`. Miss either and Resolume builds a video-only clip.

---

## The audio is still protected

* The `.mkv` archive masters are untouched.
* `D:\earthsearch\EarthSearch09of10\EarthSearch 01of10.mp3` is untouched and is
  not loaded into Resolume at all.
* Resolume only ever **decodes**. It does not mix, process or render the
  soundtrack.
* Set **Preferences → Recording → Record Audio OFF**. The take is video-only
  and the untouched original goes back underneath it in Resolve.
* MASTER B's clip audio is muted (−192 dB). A and B carry the *same* programme
  audio; two coherent copies of one mono track can comb-filter at sample level,
  and the FFT would then be analysing an artefact rather than the score.

---

## The bands, and why they are not the house defaults

The house FFT recipe card is written for club material. This is a band-limited,
dialogue-dominated 1981 BBC radio drama at 40 kbps mono, and it behaves
completely differently. Every number below was **measured on this rig against
this episode's soundtrack** with `build/calibrate_fft.ps1`.

| Band | Range | Gain | Span of output range actually used |
|---|---|---|---|
| LOW | 0.00–0.30 | 27 dB | ~23 % |
| MID | 0.32–0.62 | 30 dB | ~70 % |
| HIGH | 0.58–0.82 | 30–36 dB | ~86 % |

Three things the measurements changed:

* **3–6 dB is far too quiet here.** At the recipe card's standard gains, every
  parameter moved less than 6 % of its range. Invisible. This source needs
  roughly 30 dB.
* **A 0.66–1.00 high band is dead on this material.** It moved 9 % of its range
  even at 42 dB — the top tenth of the spectrum is genuinely empty in a 40 kbps
  mono broadcast. Pulled down to 0.58–0.82 the same band moves 86 % at 36 dB.
* **Resolume's spectrum axis is perceptual, not linear.** The mid band responds
  strongly even though the source is lowpassed well below the linear midpoint,
  which is why speech lands in "mid" as you would expect musically rather than
  where a linear FFT would put it.

Speech is the working band of this episode. Low carries the Radiophonic stings
and room tone; high carries consonants and tape brightness.

---

## What the FFT drives

Eight composition-rack parameters, eleven on the generative overlays, and three
on the SCOPE readout.

| Effect | Parameter | Band | Why |
|---|---|---|---|
| BLOOM | Amount | MID | Speech lifts the analogue glow. Floor 0.14 keeps it alive in silence so it reads as a lamp, not a gate. |
| ECHO | Feedback | LOW | The score's low end lengthens the feedback tail. Ceiling 0.66 — above ~0.75 Trails smears the faces the story depends on. |
| DRIFT | Hue Rotate | MID | Voice drifts the palette by at most ~16° of hue. Felt, never seen as a rainbow. |
| WAVE | Height | MID | Mid energy breathes the frame, under the point where faces distort. |
| FRINGE | Distance | HIGH | Consonants put a broadcast fringe on edges. |
| RIPPLE | Amplitude Both | HIGH | Surface shimmer, kept tiny so text stays readable. |
| ITERATE | StartOpacity | MID | How strongly the recursive copies register — the holographic element, held well below full. |
| BIT CRUSH | Dither | HIGH | The closest thing in the chain to analogue signal texture. |

---

## Why the FFT can never break the show

* Resolume can only attach a phase source to a `ParamRange`. Clip, column and
  deck triggering live in a completely separate subsystem that has no
  phase-source concept at all.
* The two `ParamRange`s that *could* disturb playback — a clip's Transport
  Position and the composition Speed — are deliberately left on
  `PhaseSourceStatic`, and the builder **asserts** that no FFT node appears
  inside a `<Transport>` block or in the composition header.
* Every FFT target sits inside an effect that loads **bypassed**, so the
  reactivity is armed but silent until the performer opens that effect.
* No effect's dry/wet mix is FFT-driven. Those belong to the dashboard links,
  so CLEAN can always reach them.

---

## Live control

The eight Track Control knobs are per-band **DEPTH**
(`.../behaviour/gain`, dB) and **RELEASE** (`.../behaviour/fallback`, ms).
The SCOPE layer is the readout: a phosphor oscilloscope trace whose height
follows speech, weight follows the low end and frequency follows the highs.
Bring it up on fader 8, watch what the audio is doing, then decide how hard to
drive the picture.
