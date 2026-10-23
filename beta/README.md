# Beta

These files are useful experiments, not the verified stable release.

| Composition | Matching controller preset |
|---|---|
| `compositions/Res React Live Gen.avc` | `controllers/APC 40 MK II - React v4.4.xml` |
| `compositions/Res React Orbit Gen.avc` | `controllers/APC 40 MK II - Orbit v1.xml` |
| `lexicon/compositions/Res React Lexicon.avc` | `lexicon/controllers/APC 40 MK II - Lexicon v1.xml` |
| `lexicon-ii/compositions/Res React Lexicon II.avc` | `lexicon-ii/controllers/APC 40 MK II - Lexicon v2.xml` |

Both generative compositions remain useful as references for the FFT prompts,
manifests, and FFGL plugins. Their APC40 controller pairings have not been
accepted as end-to-end verified builds. Use them for experimentation, not as
the stable install path.

`lexicon/` is a self-contained wordplay instrument — 40 pads, 40 words, a
sentence machine built entirely from native Text Block sources. Played on the
rig but **never yet touched by the hardware**; see `lexicon/README.md` for the
first-test checklist.

`lexicon-ii/` is the sequel — "Eighties-ism". Same five-row sentence machine,
but 200 pads across five decks of found broadcast-age text, and the bank arrows
become a channel dial. **Opened once, never played:** on 2026-10-23 it loaded in
Avenue 7.28.1 and all five decks rendered for the [gallery](../gallery/README.md), but no
shortcut, pad or knob has been tested. It is here for the curious, not for a show; see
`lexicon-ii/README.md`.

`library-hand/` is **The Library And The Hand**, a procedural pack cut from a
feasibility script about GUSTO, a proposed robot that fetches, flips, mixes and
scratches real vinyl. Five decks: The Plinths (machines that already exist), The
Hand (the proposed scratch head), The Catalog (identity and permission), The
Ledger (budgets and test gates), and SL-1210MKX (the newest Technics deck drawn
as schematics). Its colours follow the script's rule: stylus-cyan is documented,
cue-orange is proposed. It uses 320 stock generators, no media files and no
plugins. It was opened on Avenue 7.28.1 and every clip was read back: 18/18
checks, 0/320 mismatches. See `library-hand/README.md`.

`studio-one/` is **Studio One - War Of The Worlds 1938**, made for the
broadcast's 88th anniversary (30 October 2026). Its five decks are the room
(CBS Studio One, the RCA 44-BX, the foley table), Grovers Mill, The Visitors
(an alternate history in which the invasion is real), New York, and the
Morning After (the panic was printed, not broadcast). It uses a
silver-gelatin palette, and red appears only where a red pencil drew it. It
uses 320 stock generators, no media files and no plugins. It was opened on
Avenue 7.28.1 and every clip was read back: 18/18 checks, 0/320 mismatches.

`signal-lost/` is **Signal Lost - Transmission From Tomorrow**, drawn from the
ComfyUI-OldTimeRadio pipeline: the set signing on, the writers' room, the cast,
a VJ journey through the canonical workflow one node per scene with its real
input and output sockets, and The Shivering Gauge, the episode the pack's README
opens on. It uses 320 stock generators, no media files and no plugins. It was
opened on Avenue 7.28.1 and every clip was read back: 18/18 checks, 0/320
mismatches.

`the-manual/` is **The Manual - Avenue 7.28.1**: a composition about Resolume
itself. Its five decks are the Basic Vocabulary (Composition, Deck, Layer,
Group, Clip, Column, the render order), the Clips chapter (Trigger Style, Beat
Snap, Clip Target, Resize, Fader Start, Ignore Column Trigger, Auto Pilot,
Transition), Parameter Animation (the cogwheel, Timeline, BPM Sync, External
FFT, Gain and Fall, Envelopes, the Dashboard, Clip Position), the 62 blend
modes grouped as the manual groups them, and this rig's own Preferences. Every
term is the manual's, and the visual grammar is the interface's own: charcoal
panels, blue selection, green playing clips. It uses 320 stock generators, no
media files and no plugins, and was read back on Avenue 7.28.1: 18/18 checks,
0/320 mismatches.

`the-surface/` is **The Surface - APC40 mkII + MIDI**: the controller every
pack here is played on, drawn as schematics. The grid (notes 0-39, the RGB
velocity palette, the Mode 1 SysEx), the strips (note fixed, channel = track;
CC7, CC14, CC15), the knobs and transport (CC16-23 with LED rings, CC48-55,
Cue Level, the relative tempo encoder, PLAY STOP RECORD, the footswitch), MIDI
itself (DIN-5, 31,250 baud, status bytes, the 2^56 key Resolume files a raw
message under), and a Datavideo SE-500 video mixer as the wildcard, because it
is controlled over the same five-pin wire. Every number is from the Akai
APC40 Mk2 Communications Protocol v1.2. 320 stock generators, no media, no
plugins; see its README for the rig read-back result.

`apc-colour-lab/` is a MIDI router proof of concept for the APC40 mkII. A pad's note-on
velocity picks its colour from a 128-entry palette and its MIDI channel picks an animation
(static, one-shot, pulsing, blinking) that the controller runs by itself, so a router on the
LED path can re-theme any pack's feedback, fill dark pads with an ambient show and answer
every press. It has thirteen themes (Halloween, Christmas, Valentine's, Stars & Stripes,
Dia de Muertos, Synthwave, two black-and-white ones, and four record-sleeve ones: a prism,
a plotted pulsar, one blue, one purple), a Python engine and a JavaScript port checked
against each other on 117 scenarios (70,884 messages, 0 differences), 58 unit tests, a
one-file interactive demo, `apc40_colour_lab.html`, looping GIFs of every theme in
`docs/media/`, and a tool that turns any picture (an album sleeve, say) into a theme by
mapping its dominant colours to the nearest of the APC's 128 LED colours. Animation rates
default to a slow 60 bpm after a first look at a real controller found the first ones too
fast. The palette and pulsing were watched on a real APC40 mkII; the other animations are
emulated from Akai's protocol document and Ableton's skin and are not yet confirmed.

`the-mixers/` is **The Mixers - V-4, MXPro, MX-1 + JVC**: six decks of hands-on video
hardware drawn as schematics, walked with the APC40 mkII's own LEFT and RIGHT buttons
(previous / next deck). The APC40 mkII as an object; the Edirol V-4 (2002: TAP and BPM SYNC
from MIDI clock, input select on MIDI notes 36-48, no audio at all); the Videonics MXPro
(1997: 501 transitions, a CURRENT and a NEXT row instead of A/B buses); the Videonics MX-1
(1994: the Take-bar, 210 numbered effects, the manual's own nightclub); a JVC deck pairing the
1999 HR-S7600U S-VHS VCR with the RM-G850E, which turned out to be a professional U-matic
edit controller rather than its remote, so the deck says they never met; and a patch bay of
the words they all share. Every caption is sourced in `the-mixers/docs/SOURCES_*.md`.
384 stock generators, no media, no plugins.
