# Beta

These files are useful experiments, not the verified stable release.

| Composition | Matching controller preset |
|---|---|
| `compositions/Res React Live Gen.avc` | `controllers/APC 40 MK II - React v4.4.xml` |
| `compositions/Res React Orbit Gen.avc` | `controllers/APC 40 MK II - Orbit v1.xml` |
| `lexicon/compositions/Res React Lexicon.avc` | `lexicon/controllers/APC 40 MK II - Lexicon v1.xml` |
| `lexicon-ii/compositions/Res React Lexicon II.avc` | `lexicon-ii/controllers/APC 40 MK II - Lexicon v2.xml` |
| `telemetry/compositions/Res React Telemetry.avc` | `telemetry/controllers/APC 40 MK II - Telemetry v1.xml` |

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
become a channel dial. **Completely untested: it has not been opened in Resolume
even once.** It is here for the curious, not for a show. Two files, ninety
seconds to find out; see `lexicon-ii/README.md`.

`telemetry/` is "The Measuring Room" — five fictional instruments (EKG,
seismograph, VU array, polygraph, Geiger counter) that all measure the room's
audio; the FFT is the subject, not the garnish. 200 native-generator pads drawn
in block-element raster typography, and the first performance preset in the kit
to map **all 149 physical controls** — footswitch and relative tempo encoder
included. **Completely untested, same weight of disclaimer as lexicon-ii**; see
`telemetry/README.md`.
