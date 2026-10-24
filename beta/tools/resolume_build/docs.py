#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs.py - README and run sheet for a standard-instrument pack, written from
the bible and the build manifest so they cannot drift from the files.
"""
import json
import os


def write_docs(out_dir, bible, manifest, extra_notes=None):
    pack = bible["pack_name"]
    comp = bible["comp_name"]
    preset = "APC 40 MK II - %s" % pack
    decks = bible["decks"]
    counts = manifest["counts"]
    nd = len(decks)
    nword = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight"}.get(nd, str(nd))
    readme = []
    A = readme.append
    A("# %s" % pack)
    A("")
    A("*%s*" % bible.get("tagline", ""))
    A("")
    A("A procedural live instrument for **Resolume Avenue 7.28.1** and an "
      "**Akai APC40 mkII**. Every one of its %d clips is a stock Resolume "
      "generator with hand-set parameters - no media files, no third-party "
      "plugins - and %d of its parameters listen to the music through "
      "Resolume's external FFT." % (counts["clips"], counts["fft_nodes"]))
    A("")
    A("| | |")
    A("|---|---|")
    A("| `%s.avc` | the composition: %d decks x 8 layers x 8 scenes |" % (comp.replace(":", " -"), nd))
    A("| `%s.xml` | the APC40 mkII preset - every control has a job |" % preset)
    A("| `docs/RUN_SHEET.md` | plug in, set the audio input, press PLAY |")
    A("| `docs/CONTROL_MAP.md` | every button, pad, knob and fader |")
    A("| `docs/DECKS.md` | the %s worlds, scene by scene |" % nword)
    A("| `BUILD_REPORT.txt` | what the builder repaired, if anything |")
    A("")
    A("## The %s worlds" % nword)
    A("")
    for i, d in enumerate(decks, start=1):
        A("**%d. %s** (%s) - %s" % (i, d["name"], d.get("theme", ""),
                                    d.get("world", "")))
        A("")
        A("Scenes: " + " -> ".join(d["columns"]))
        A("")
    A("## How it plays")
    A("")
    A("* **Decks are worlds.** LEFT / RIGHT walk the %s deck tabs." % nword)
    A("* **Columns are scenes.** Scene Launch 1-5 fire scenes 1-5; UP / "
      "DOWN walk all eight. A scene fires all eight layers at once, "
      "composed as one picture.")
    A("* **Pads are the five playable layers.** Bottom row = BED, then BODY, "
      "FIGURE, LIGHT, TEXT. Mix any pad with any other; the three "
      "non-pad layers (AURA, GRAIN, SCOPE) only change with a scene.")
    A("* **The crossfader** is environment <-> figures: hard left shows only "
      "BED, BODY and AURA; hard right only FIGURE, LIGHT and TEXT; centre "
      "is everything. Rig-measured, not assumed.")
    A("* **The rack** is 30 stock effects in four banks on the button rows "
      "(RECORD ARM, CROSSFADE A/B, the DEVICE row, and PAN/SENDS/USER/"
      "NUDGE/SESSION REC), each bank's wetness on Device knobs 1-4, plus "
      "four always-armed macros on knobs 5-8: GLOW, ECHO, FRINGE and the "
      "fourth (VOID or SILK). BANK LOCK is CLEAN - every link to zero.")
    A("* **FFT** lives on the Track Control knobs: depth and release for the "
      "low, mid and high anchors, SCOPE depth, and TIME (composition speed "
      "0-2x) on knob 8.")
    A("")
    A("## FFT philosophy")
    A("")
    A(bible.get("fft_philosophy", ""))
    A("")
    A("## Built from the running application")
    A("")
    A("Every source, effect, parameter name, range, choice and blend-mode id "
      "in this pack was harvested from Avenue 7.28.1 itself through its REST "
      "API (`harvest/`), and the composition was opened on the rig and every "
      "parameter read back before it shipped. Shape Shifter 3D is excluded: "
      "it crashed Avenue on save, twice.")
    if extra_notes:
        A("")
        A("## Notes")
        A("")
        for n in extra_notes:
            A("* " + n)
    A("")
    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(readme))

    rs = []
    B = rs.append
    B("# %s - run sheet" % pack)
    B("")
    B("## Before the first frame")
    B("")
    B("1. Install: `%s.xml` -> `Documents\\Resolume Avenue\\Shortcuts\\MIDI\\`; "
      "`%s.avc` -> `Documents\\Resolume Avenue\\Compositions\\` (this rig's "
      "Documents is under OneDrive)." % (preset, comp))
    B("2. **Audio in.** Preferences -> Audio -> Input device: `CABLE Output "
      "(VB-Audio Virtual Cable)`. Play your music into `CABLE Input`. The "
      "composition uses External FFT; with no input device every reactive "
      "parameter sits at its floor and the picture looks static.")
    B("3. Preferences -> MIDI: `APC40 mkII` as input AND output (output "
      "drives the pad colours).")
    B("4. Open the composition. It selects its own MIDI preset.")
    B("5. Park the CROSSFADER in the centre and all eight faders up.")
    B("")
    B("## Opening")
    B("")
    B("* **PLAY** fires scene 1 of the current deck and arms the SCOPE.")
    B("* Watch the SCOPE (layer 8, fader 8): if it is flat, the audio input "
      "is not set.")
    B("* Track knobs 1-6 are depth / release for the three bands; turn depth "
      "up until the SCOPE breathes with the music, not with every hi-hat.")
    B("* **FFT GAIN is the TEMPO knob**, on every composition: Avenue's "
      "global audio gain. Turn it up when the picture is too calm for the "
      "room, down when it slams. METRONOME puts it back to the middle.")
    B("* **TIME is Track knob 8**: composition speed, 0 to 2x with 1x at "
      "the centre. TAP TEMPO puts it back to exactly 1x.")
    B("")
    B("## Playing")
    B("")
    B("* Scenes with Scene Launch 1-5 and UP/DOWN; worlds with LEFT/RIGHT.")
    B("* Pads mash the five playable layers across any scene.")
    B("* Effects: lit button = active. Device knobs 1-4 are the four banks' "
      "wetness, 5-8 the macros. CUE LEVEL nudges all four banks together "
      "(anticlockwise toward the clean picture).")
    B("* **STOP** clears the pad layers only (beds and scope survive). "
      "**STOP ALL CLIPS** ejects everything. **RECORD** is blackout "
      "(press again to return). The footswitch is a momentary blackout.")
    B("* **BANK LOCK = CLEAN.** Every effect dry, every macro off, picture "
      "untouched. Avenue has no soft-takeover: after CLEAN the physical "
      "knobs are where you left them, so the next knob you touch jumps. "
      "Sweep CUE LEVEL to come back smoothly.")
    B("")
    B("## Signature moments, deck by deck")
    B("")
    for d in decks:
        B("**%s**" % d["name"])
        for m in d.get("moments", []):
            B("- " + m)
        B("")
    with open(os.path.join(out_dir, "docs", "RUN_SHEET.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(rs))


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    bible = json.load(open(os.path.join(out, "bible.json"), encoding="utf-8"))
    manifest = json.load(open(os.path.join(out, "manifest.json"),
                              encoding="utf-8"))
    write_docs(out, bible, manifest)
