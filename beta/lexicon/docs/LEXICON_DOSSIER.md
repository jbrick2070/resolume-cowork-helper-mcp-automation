# Res React Lexicon — Complete Dossier

**A live-performance instrument that turns a music controller into a sentence machine.**

Built 31 July 2026 by Jeffrey A. Brick with an AI agent, on Resolume Avenue 7.27.1,
Windows 11, an Akai APC40 mkII, and an RTX 5080 laptop.

---

## 0. What this document is

This is a single self-contained record of one project: what it is, why it exists, how it
works, how it was made, what had to be reverse-engineered to make it, what has been proven
and what has not. It assumes no prior knowledge of video performance software, MIDI
controllers, or the person who built it. Everything needed to understand and discuss the
project is inside this file. A glossary sits at the end (section 14); readers unfamiliar
with the vocabulary may want to read that first.

---

## 1. The world this lives in

**VJing** is live visual performance. A VJ stands beside or behind a DJ or band and plays
images the way a musician plays notes — triggering, layering, and distorting video in time
with the music, in front of an audience, without a net. There is no undo in front of a
crowd.

**Resolume** is the software most VJs use. Its central metaphor is a grid: rows are called
*layers*, columns are called *columns* or *scenes*, and each cell in the grid is a *clip* —
a piece of content. Layers stack like sheets of glass: layer 1 is the bottom, and each layer
above composites onto the ones below according to a *blend mode*. Only one clip plays per
layer at a time, so firing a new clip on a layer replaces whatever was there. Fire a whole
column and every layer changes at once — that is a scene change.

The **Akai APC40 mkII** is the hardware most commonly used to play Resolume. It is a MIDI
controller: a grid of 40 backlit rubber pads arranged 5 rows by 8 columns, plus nine faders,
sixteen knobs, a crossfader, and several rows of buttons. It sends no sound and no image; it
sends MIDI messages, and the software decides what those messages mean. That mapping — which
physical control does what — is stored in an XML file Resolume calls a *shortcut preset*.
The pads' colours are not decorative either; the software sends colour instructions *back*
to the controller, so a well-designed preset makes the hardware light up as a live diagram
of what the software is doing.

The person who built this project has spent months building compositions and controller
mappings in this environment, including a "visual twin" — a Resolume composition that draws
a working picture of the APC40 itself on screen. The Lexicon is a deliberate departure from
that line of work.

---

## 2. The idea, in one sentence

**Every one of the 40 pads is a word, and the five rows of pads are the five slots of a
sentence, so playing the grid writes language on the screen in real time.**

The five rows map to grammatical roles, stacked in the same order they appear on the output:

| Pad row (top to bottom) | Role | What it holds |
|---|---|---|
| Row 1 (top) | **Subject** | who or what |
| Row 2 | **Verb** | what it does |
| Row 3 | **Object** | to what |
| Row 4 | **Mark** | punctuation |
| Row 5 (bottom) | **Field** | a typographic ground, behind everything |

Pressing one pad in each of the top three rows assembles a sentence:

```
THE ARCHIVE          <- Subject   (top pad row)
MISREADS             <- Verb
A BORROWED NAME      <- Object
::                   <- Mark
— — — — — — — —      <- Field     (bottom pad row, the ground)
```

Eight choices in each of three grammatical slots gives **8 × 8 × 8 = 512 grammatical
sentences**. Multiply by the eight punctuation marks and the eight typographic grounds and
the instrument holds **4,096 distinct lines over 8 backgrounds** — from forty buttons.

The vocabulary was chosen so that *every* combination parses. There is no wrong chord. A
performer can play the grid at speed, without reading, and the output will always be a
sentence — sometimes banal, sometimes uncanny, occasionally very good. That is the design
goal: an instrument where the constraint guarantees coherence and the player supplies the
timing and the taste.

---

## 3. The complete vocabulary

This is the entire content of the instrument. Each entry shows the label printed on the pad
and, where different, the text that appears on screen in capitals.

**Subject — 8 words, warm white, upper third of the screen**

The Signal · Every Machine · The Chorus · A Slow Comet · The Archive · Nobody ·
The Blue Hour · This Circuit

**Verb — 8 words, amber, centre**

Remembers · Dissolves · Rehearses · Forgives · Broadcasts · Misreads · Orbits · Answers

**Object — 8 phrases, cyan, lower third**

The Static · A Borrowed Name · Every Exit · The Long Night · Its Own Echo ·
The First Tape · Nothing At All · The Next Room

**Mark — 8 glyphs, magenta, bottom**

Period `.` · Question `?` · Bang `!` · Dash `—` · Ellipsis `…` · Parens `( )` ·
Therefore `::` · Slashes `///`

**Field — 8 typographic textures, slate grey, centre, oversized**

Carrier Line `— — — — — — — —` · Dot Drift `· · · · · · · ·` ·
Plus Grid `+ + + + + + + +` · Paren Chorus `( ( ( ( ) ) ) )` ·
Block Static `▓▒░▓▒░▓▒░▓` · Backslash Dusk `\ \ \ \ \ \ \ \` ·
Hash Lattice `# # # # # # # #` · Zero Null `0 0 0 0 0 0 0 0`

The register is deliberate: broadcast-era and science-fictional, machine-poetic,
non-violent. Sample outputs, all reachable by pressing three pads:

- THE ARCHIVE / MISREADS / A BORROWED NAME
- NOBODY / REHEARSES / THE LONG NIGHT
- EVERY MACHINE / FORGIVES / ITS OWN ECHO
- A SLOW COMET / BROADCASTS / NOTHING AT ALL
- THE BLUE HOUR / ANSWERS / THE FIRST TAPE

The eight columns are named for moods rather than content — **Carrier, Drift, Grid, Chorus,
Static, Dusk, Lattice, Null** — because a column can also be fired as a whole, which throws
a complete pre-composed sentence on screen in one press.

---

## 4. It is made of nothing

The single most unusual technical fact about this composition: **it contains no media at
all.**

Most VJ compositions are containers for video files — gigabytes of rendered loops, each one
a dependency. Move the file, rename a folder, or open it on another machine and the clips
come up empty. This one contains **zero video files, zero images, zero third-party plugins,
zero external references.** Every one of the forty cells is a *Text Block*, a text generator
built into Resolume itself. Even the background layer is text: rows of repeating typographic
characters used as texture.

The consequences are practical. The whole instrument is a single file of roughly 755 KB —
smaller than one second of video — most of which is the forty embedded pad thumbnails. It
opens on any machine with Resolume installed. Nothing to relink, nothing to transcode,
nothing to forget in the van. And because the content is text rather than pixels, the words
can be changed by editing a list and re-running a script.

---

## 5. Anatomy of the composition

Five layers, eight columns, forty clips, one deck.

| # | Layer | Blend mode | Vertical position | Colour | Role |
|---|---|---|---|---|---|
| 1 | Field | Alpha | centre, size 2.2 | slate `#7C8A9C` | typographic ground |
| 2 | Subject | Screen | 270 px above centre | warm white `#FFF4E0` | who |
| 3 | Verb | Screen | 50 px above centre | amber `#FFB020` | does what |
| 4 | Object | Screen | 140 px below centre | cyan `#46E0FF` | to what |
| 5 | Mark | Add | 330 px below centre | magenta `#FF3CC8` | punctuation |

The colour assignment does double duty. On screen it separates the grammatical roles so the
sentence reads as a structured object rather than a paragraph. On the controller, each row
of pads lights in *the same colour as its row on screen* — so the hardware becomes a legend
for the output. A performer glancing down sees amber and knows that is the verb row without
reading anything.

Every clip carries two effects of its own: a **Bloom** (a soft light spill around bright
edges) and a **WaveWarp** (a rippling distortion), the latter set to zero amplitude so it is
silent until deliberately dialled up. Each of the four text layers additionally carries its
own Bloom at zero, assigned to a knob, so a whole grammatical role can be made to glow.

The composition also carries a rack of five global effects — Hue Rotate, Shift RGB, LoRez,
Invert RGB and Mirror Quad — all bypassed when the file opens, each on a button.

**One notable omission.** Two common effects, Trails and Freeze, were deliberately excluded
from the composition-level rack. In an earlier project on this rig, a Trails effect with its
feedback parameter mapped to a fader was pushed to maximum during a session and produced an
infinite feedback loop: the output froze and would not clear. That pairing is now treated as
a known hazard and is simply not present here. This is what a safety decision looks like in
a performance instrument — not a warning label, an absence.

---

## 6. The controller

Ninety-eight shortcuts. Every physical control on the APC40 mkII is assigned; nothing on the
surface is dead.

### The grid

| Pad row | MIDI notes | Drives | LED colour |
|---|---|---|---|
| top | 32–39, ch 1 | layer 2 — Subject | white |
| second | 24–31, ch 1 | layer 3 — Verb | amber |
| third | 16–23, ch 1 | layer 4 — Object | sky |
| fourth | 8–15, ch 1 | layer 5 — Mark | pink |
| bottom | 0–7, ch 1 | layer 1 — Field | violet |

Bright means playing; dim means loaded but silent.

This row ordering deliberately corrects a problem in the builder's earlier work. A previous
mapping put the main visible content on the third row down, with unrelated functions above
it — an arrangement he had flagged as counterintuitive. Here **row order is layer order is
reading order**: the top row of pads is the top line of the sentence.

### Everything else

| Control | MIDI | Function |
|---|---|---|
| Track Select 1–8 | note 51, ch 1–8 | fire an entire pre-composed sentence (column 1–8) |
| Scene Launch 1–5 | notes 82–86 | drop one grammar slot out of the sentence, aligned row-for-row |
| Clip Stop 1–6 | note 52, ch 1–6 | global effect toggles: Hue, Shift RGB, LoRez, Invert, Mirror, All-off |
| Activator 1–5 | note 48, ch 1–5 | mute a grammar slot |
| Solo 1–5 | note 49, ch 1–5 | isolate a grammar slot |
| Faders 1–5 | CC 7, ch 1–5 | how present each slot is |
| Master fader | CC 14 | overall output level |
| Crossfader | CC 15 | crossfader phase |
| Device knobs 1–4 | CC 16–19 | hue · colour-channel shift · pixel size · bit reduction |
| Device knobs 5–8 | CC 20–23 | glow on Subject · Verb · Object · Mark |
| Track knobs 1–8 | CC 48–55 | the selected clip's own eight dials (see section 7) |
| Big encoder | CC 47 | playback position of the selected clip |
| Tap / Resync | notes 99 / 91 | tempo |
| Stop All | note 81 | clear everything |
| Bank ‹ › | notes 96 / 97 | previous / next column |

The design principle behind the surface is that every control should mean something in the
instrument's own terms. The faders are not "layer opacity" — they are *how present each part
of speech is*. Push the verb fader down and the sentence loses its action while the nouns
remain. The scene launch buttons are not "layer clear" — they *drop a grammar slot out*, and
they sit physically beside the row they empty.

---

## 7. Eight dials on every pad

The eight rotary knobs on the right of the APC40 are wired to the *selected clip's* own
dashboard — Resolume's term for a small bank of eight assignable dials that belongs to an
individual clip. Combined with a Resolume preference called *"Update clip panels on external
triggers,"* the selection follows the last pad pressed. The practical result: **every pad
brings its own eight knobs with it.** Press a word, and the knobs are now that word's knobs.

The same eight functions sit in the same eight positions on all forty pads, so muscle memory
carries across the whole grid:

| Dial | Controls | Range |
|---|---|---|
| 1 SIZE | text size | 0.5 – 10 |
| 2 GLOW | glow around the letterforms | 0 – 1 |
| 3 BLOOM | bloom intensity | 0 – 1 |
| 4 HALO | bloom radius | 0 – 1 |
| 5 THRESH | bloom threshold | 0 – 1 |
| 6 WARP | ripple depth, vertical | 0 – 1 |
| 7 RIPPLE | ripple depth, horizontal | 0 – 1 |
| 8 DRIFT | ripple speed | 0 – 1 |

Dial 1 is the dramatic one and its behaviour is a deliberate choice rather than an accident.
Text size runs from 0.5 to 10, and the resting value of 1.0 sits at roughly five percent of
the knob's travel. The knob is therefore extremely sensitive near the bottom of its throw —
a small turn takes a single word from one line of text to something that fills the entire
screen. Verified live: dial 1 at about a third of its travel, with a little WARP and BLOOM,
turned the word MISREADS into a full-frame ribbon field of amber while the other three rows
stayed crisp and readable underneath.

**One parameter was deliberately left off the knobs.** Vertical position would seem an
obvious candidate for a dial, but its underlying range in Resolume is ±32,768 — meaning the
entire useful travel, roughly ±500 pixels, occupies less than two percent of the knob's
rotation. It would be unplayable. The vertical band therefore stays a fixed design constant,
and that dial was spent on bloom threshold instead. This is a small decision but a
representative one: the range was measured before the dial was assigned, rather than after.

---

## 8. It listens

Two of the five rows are driven by audio. Resolume can perform an FFT — a frequency
analysis — on an incoming audio signal and use the energy in a chosen frequency band to
drive any parameter.

| Row | Frequency band | Gain | Fallback | Floor |
|---|---|---|---|---|
| Field | bass, 0 – 0.33 | +6 dB | 800 ms (a slow breath) | 0.55 |
| Mark | highs, 0.66 – 1.0 | +6 dB | 200 ms (a snap) | 0.45 |

The background texture breathes with the kick drum; the punctuation flickers on hi-hats.

**The three word rows are deliberately excluded.** They never move with the music. This is
the central aesthetic decision of the audio design: an instrument whose whole subject is
language must keep the language legible. Making the words pulse would look impressive for
ten seconds and become unreadable for the rest of the set. The motion is pushed to the two
elements that carry no meaning — the ground and the punctuation — where it adds life without
costing comprehension.

The "fallback" figures are decay times: how long a parameter takes to fall back after a
transient. 800 ms on the bass reads as breathing; 200 ms on the highs reads as snapping.
The "floor" values are the resting level with no signal, and they are set high on purpose so
that the composition still reads correctly when no audio is connected at all. Nothing
disappears if the audio routing is not set up.

---

## 9. How it was built — the offline method

The conventional way to build a Resolume composition with an AI agent is through Resolume's
own API: create the composition, add layers, load each clip, set each parameter — hundreds of
individual network calls into a running application. On this rig that path has a documented
history of trouble. The "create new composition" call times out and can leave the
application in a half-broken state; rapid batches of clip loads have crashed it outright;
and a cache layer sometimes serves stale answers that look convincing and are wrong.

This project used a different method, and it is arguably the most reusable thing to come out
of it.

A Resolume composition file — the `.avc` extension — is **XML**. So instead of driving the
running application, the agent:

1. **Harvested donors.** Read existing composition files as plain text and extracted
   verbatim XML fragments for each thing needed — a text source, a bloom effect, a wave
   distortion, a blend mode, an audio-reactive parameter. Real fragments written by
   Resolume itself, never invented markup.
2. **Generated the whole file offline** with a Python script — five layers, eight columns,
   forty clips, every parameter, in about four seconds.
3. **Validated before writing.** XML parses, unique identifiers are unique, clip and layer
   and column counts are exactly what was intended.
4. **Opened the finished file** in Resolume, once, and looked at it.

The advantages compound. It is deterministic. It cannot crash the host application because
the host application is not involved. It cannot damage existing work because it only ever
writes new files. It is fast enough to iterate — change a word list, re-run, reopen. And it
produces a *generator*, not just an artifact: the composition can be rebuilt from scratch at
any time, so the words are editable by anyone who can edit a list in a text file.

The rule that made it safe was strict: **never invent XML.** Every structure written into
the file was first observed in a file that Resolume had saved. Where a needed structure could
not be found in any existing file, it was not guessed — it was extracted by making Resolume
produce one (see section 10).

---

## 10. Three things that had to be reverse-engineered

The project ran into three undocumented file-format problems. Each was solved by
observation rather than assumption, and each result is reusable.

### The vertical axis is upside down

The first build rendered the sentence inverted — subject at the bottom, punctuation at the
top. The vertical position parameter turned out to be measured in pixels from the centre of
the frame with **positive values pointing down**, which is the opposite of the mathematical
convention. A one-line fix, but only findable by rendering it and looking.

### The pad images

Resolume draws a small preview image on each pad in the grid. Left to generate these
automatically, six of the forty came out **completely blank** — specifically the ones whose
content is thin or small: a period, a question mark, an exclamation mark, backslashes,
hashes. Those clips render perfectly on the main output; only their previews were empty. And
because blank images are byte-identical to one another, the grid showed six duplicate pads.

The obvious fix — an "upload a custom thumbnail" function in the API — turned out to be a
trap. It *displayed* correctly and never *persisted*: it wrote nothing into the composition
file, left no sidecar file anywhere on disk, and reverted on restart. Worse, after the first
save, neither uploading nor regenerating changed a single one of the forty stored images.
The application was serving a frozen cache.

So the format itself was decoded. Each preview is stored inside the composition file as
**base64-encoded, LZF-compressed raw BGRA pixels, 320 × 240, 307,200 bytes uncompressed,
compressing to about two to three percent.** A compressor and decompressor were written from
scratch, every image round-trip asserted before writing, and forty custom word cards were
injected directly into the file — where they travel with it and survive restarts.

There is a caveat worth knowing: saving the composition from inside Resolume overwrites the
injected images with the application's own auto-generated set, blanks included. The injector
must be re-run after any in-application save.

### The per-pad dials

The eight-dials-per-pad system needed an XML structure that appeared in **no file on disk**.
Rather than fabricate it — a failure mode that has cost this project time before — the agent
made Resolume produce one: it created a single dial through the API, saved to a throwaway
probe file, and read the result.

The probe corrected two beliefs that had been recorded as fact from earlier work. First, the
XML element carries an attribute that the previously documented version omitted. Second, and
more consequentially, creating a dial through the API attaches it to the *parent layer*, not
to the clip — which would have put the knobs on the wrong object entirely. Knowing that, the
generator writes the dials onto the clips, matching the shape found in files Resolume itself
had saved, so that the "selected clip" knob mapping actually reaches them. Forty clips × eight
dials = **320 parameter links**, all written offline in one pass.

The general lesson, and the reason this section exists: **three separate pieces of
"documented" knowledge turned out to be wrong, and all three were caught by looking at real
output instead of trusting the note.**

---

## 11. What is proven and what is not

**Proven, on the rig, on 31 July 2026.** The composition opens in Resolume Avenue 7.27.1.
The sentence assembles and reads correctly top to bottom. The colour palette renders as
specified. The global effect rack loads bypassed — no freeze, no black frame. The per-pad
dials load, all eight per pad, and demonstrably drive pixels. All forty pad images are
distinct and embedded in the file. The composition shares zero content with any earlier work
on this rig — checked by comparison against every other composition in the library: no shared
clip names, no shared media, no shared plugins.

**Not proven.** **The APC40 mkII has not been in the loop.** No pad has been physically
pressed. No LED colour has been confirmed on the hardware. No knob throw has been felt by a
human hand. The entire controller mapping — all ninety-eight shortcuts — is *designed and
serialized*, not *controller-verified*. It is a strong design based on a working preset from
the same rig, but the distinction matters and is stated plainly wherever the project is
documented.

For that reason the instrument ships in a folder named `beta/` inside its repository, and
does not join the stable release until it survives a real set.

**A caveat about glyphs.** The character `∴` (the mathematical "therefore" symbol) was in
the original design for one of the punctuation pads. It renders as a missing-glyph box in
Resolume's text font, and was replaced with a double colon `::`. Everything else in the
vocabulary was confirmed as rendering.

**One side effect, disclosed.** Launching Resolume caused it to rewrite whichever MIDI
preset was active at the time — the application flushes the active preset roughly twenty
seconds after startup. One unrelated preset file therefore differs, byte for byte, from
before the session, though it remains valid and complete. Every other file in the library
was verified byte-identical to its pre-session cryptographic hash: sixty-five compositions
and thirty-one presets, unchanged. The verification method — hash everything before touching
anything, re-verify at the end — is what caught it.

---

## 12. The design decisions, and why

A list of the choices that shaped the instrument, each with its reasoning, because the
reasoning is more transferable than the choices.

**Constraint as a feature.** The vocabulary is built so every combination parses. The player
never has to think about grammar, only about timing and meaning. A wrong note is impossible;
this frees the performer to play fast.

**The controller is a legend.** Pad colour matches screen colour, and row order matches
reading order. The hardware explains the software at a glance, in the dark, under time
pressure.

**Motion where meaning is not.** The audio drives the ground and the punctuation. The words
stay still. Legibility beats spectacle in an instrument whose subject is language.

**Ranges measured, not assumed.** Every parameter's range was read from the running
application before a knob was assigned to it. One candidate was rejected outright because
its range made it unplayable.

**Hazards removed rather than labelled.** The effect pairing that once locked up the output
is simply not in the composition. A performance instrument should not contain a control that
can ruin a set, however well documented.

**Nothing to install.** No video files, no plugins, no dependencies. The whole instrument is
one small file, so it cannot break by being moved.

**Editable by design.** The words live in a plain list inside a generator script. Changing
the vocabulary is editing a list and running one command — not rebuilding a composition by
hand.

**Honest labelling.** The gap between "played through software" and "played on hardware" is
stated in the repository README, the project README, and the commit message. Three places,
same words, so nobody discovers it the hard way.

---

## 13. Changing it

The instrument regenerates from two commands. The word lists live at the top of the build
script as five lists of eight entries; edit them, then:

```
python build_lexicon.py
python inject_thumbs.py "Res React Lexicon.avc" "Res React Lexicon.avc" BGRA
```

The first rebuilds the composition — layers, columns, all forty clips, all 320 parameter
links, the audio routing. The second writes the forty pad images back into it. Both validate
before writing and neither touches any other file. A third script regenerates the controller
preset independently, so the mapping can be revised without rebuilding the composition.

This is the real deliverable in the long run. The Lexicon as shipped is one vocabulary; the
machine that produces it will make any vocabulary — a different language, a specific show, a
commissioned text, someone else's poem.

---

## 14. Glossary

**APC40 mkII** — Akai's MIDI controller for VJ software: 40 backlit pads in a 5 × 8 grid,
nine faders, sixteen knobs, a crossfader, and several button rows.

**Bloom** — a visual effect that spills soft light outward from bright areas, the way an
overexposed light source blooms on film.

**Blend mode** — the rule for compositing one layer onto the ones beneath. *Alpha* replaces,
*Screen* lightens, *Add* sums brightness.

**Clip** — one cell in the Resolume grid: a piece of content plus its own effects and
settings.

**Column / scene** — a vertical slice of the grid. Firing a column changes every layer at
once.

**Composition (`.avc`)** — a Resolume project file. Internally it is XML, which is what made
the offline build method possible.

**Dashboard** — a bank of eight assignable dials belonging to a clip, layer, or composition.
Mapping knobs to the *selected clip's* dashboard is what gives every pad its own knobs.

**FFT** — Fast Fourier Transform, a frequency analysis of an audio signal. It separates bass
from mid-range from treble, so a parameter can be driven by one part of the sound.

**FFGL** — Resolume's plugin format for custom effects and sources. Notable here by its
absence: the Lexicon uses none.

**Layer** — a horizontal row of the grid, and a plane in the visual stack. Layer 1 is the
bottom.

**LZF** — a fast, simple compression algorithm, used by Resolume to store pad preview images
inside the composition file.

**MIDI** — the messaging standard hardware controllers use. A MIDI controller sends numbers,
not sound or images; the software assigns meaning to them.

**Shortcut preset** — the XML file mapping each physical control to a software function.
Applied for input *and* output, output being what lights the pads.

**Text Block** — Resolume's built-in text generator. Every one of the forty clips in this
composition is one.

**Trails / Freeze** — two effects that, combined at high feedback, can lock a composition's
output into an unclearable loop. Deliberately absent here.

**VJ** — visual jockey; a live visual performer.

---

## 15. Facts at a glance

| | |
|---|---|
| Name | Res React Lexicon |
| Type | Live visual performance instrument — a typographic sentence machine |
| Built | 31 July 2026 |
| Author | Jeffrey A. Brick, with an AI agent |
| Platform | Resolume Avenue 7.27.1, Windows 11, RTX 5080 laptop |
| Controller | Akai APC40 mkII |
| Composition | 5 layers × 8 columns = 40 clips, one deck |
| File size | ~755 KB, most of it the 40 embedded pad images |
| Content | 100% native text — 0 video files, 0 plugins, 0 external dependencies |
| Vocabulary | 8 subjects, 8 verbs, 8 objects, 8 punctuation marks, 8 typographic grounds |
| Combinations | 512 grammatical sentences; 4,096 lines; over 8 grounds |
| Controller map | 98 shortcuts — every physical control assigned |
| Per-pad dials | 8 dials on each of 40 pads = 320 parameter links |
| Audio | External FFT on 2 of 5 rows: Field on bass, Mark on highs |
| Build method | Offline XML generation from harvested donor fragments, validated before writing |
| Formats decoded | Pad-image storage (LZF/BGRA), per-clip dial links, vertical axis direction |
| Status | **Beta — played through software, never touched by the hardware** |
| Location | `react-kit/beta/lexicon/`, commit `0c9978a` |

---

*End of dossier.*
