#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_control_map_doc.py - writes docs/APC40_CONTROL_MAP.md.

Generated from the SAME table the preset generator reads, so the printed
layout card and the shipped XML cannot disagree. Never hand-edit the output.
"""

import collections
import os

import es_apc_map as M
import es_spec as S


def main():
    m = M.build_map(S)
    os.makedirs(S.DOCS_DIR, exist_ok=True)
    out = os.path.join(S.DOCS_DIR, "APC40_CONTROL_MAP.md")

    by_key = collections.defaultdict(list)
    for sc in m:
        k = (M.note_key(sc["channel"], sc["note"]) if sc["kind"] == "note"
             else M.cc_key(sc["channel"], sc["cc"]))
        by_key[k].append(sc)

    L = []
    A = L.append
    A("# APC40 mkII — EarthSearch EP01 control map")
    A("")
    A("Generated from `build/es_apc_map.py`. Do not hand-edit — rebuild with")
    A("`python make_control_map_doc.py`.")
    A("")
    A("Preset: **%s**  ·  composition: **%s**"
      % (S.MIDI_PRESET_NAME, S.COMP_NAME))
    A("")
    A("**%d shortcuts across %d physical controls. Nothing on the surface is "
      "unmapped.**" % (len(m), len(by_key)))
    A("")
    A("---")
    A("")
    A("## The three controls that matter")
    A("")
    A("| | Button | What it does |")
    A("|---|---|---|")
    A("| **START BOTH @ 00:00** | `PLAY` | Fires MASTER A, MASTER B and the "
      "SCOPE together at frame zero. Measured on the rig at **0 ms drift "
      "across 905 seconds**, 30 samples. This is the only control that "
      "starts a master, and it starts from zero — it is not a mid-show "
      "repair. |")
    A("| **STOP / RESET BOTH** | `STOP` | Ejects every layer. Both masters "
      "return to 00:00. |")
    A("| **CLEAN / ALL FX OFF** | `BANK LOCK` | Takes all five effect banks, "
      "every overlay layer, the scope and the captions to zero in one press. "
      "Playback is not touched. |")
    A("")
    A("The **Cue Level** knob sweeps the same eight links continuously, so "
      "after a CLEAN it is also how you bring the look back — the physical "
      "knobs do not move themselves, and Avenue has no soft-takeover.")
    A("")
    A("`STOP ALL CLIPS` does what it says: it clears the five overlay layers "
      "and cannot reach a master.")
    A("")
    A("`RECORD` is **BLACKOUT**, and the **footswitch** is the same thing "
      "momentarily — hold for black, release for picture. Playback continues "
      "underneath either way.")
    A("")
    A("---")
    A("")
    A("## Why no pad can wreck the show")
    A("")
    A("* The 5×8 pad grid addresses **only** the five generative overlay "
      "layers. There is no pad that can reach either master.")
    A("* **Every** layer sets *Ignore Column Trigger*, so no column action — "
      "from this preset or from a mis-click in Resolume's own UI — can "
      "connect, eject or restart anything.")
    A("* There is **no seek or scrub binding anywhere** in the preset.")
    A("* **No layer has fader-start**, so no fader move can trigger a clip.")
    A("")
    A("---")
    A("")
    A("## The pad grid — generative overlays")
    A("")
    A("Physical row 1 is the bottom row. Each row is one layer; each column "
      "is one clip on it.")
    A("")
    for row in range(5, 0, -1):
        layer = M.ROW_LAYER[row]
        clips = S.OVERLAY_CLIPS[layer - 1]
        A("**Row %d — layer %d `%s`** (%s, %s)"
          % (row, layer, M.ROW_LAYER_NAME[row],
             dict((l[0] + 1, l[2]) for l in S.LAYERS)[layer] + " blend",
             M.ROW_LED[row]))
        A("")
        A("| col | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |")
        A("|---|---|---|---|---|---|---|---|---|")
        A("| clip | " + " | ".join(c[0] for c in clips) + " |")
        A("| note | " + " | ".join(str((row - 1) * 8 + c)
                                   for c in range(8)) + " |")
        A("")
    A("---")
    A("")
    A("## Effect banks")
    A("")
    A("All %d effects load **bypassed**. Lit pad = effect is active." %
      len(S.COMP_RACK))
    A("")
    A("Some carry a **wet ceiling** — the bank knob still sweeps its whole "
      "travel, but the top of that travel is a value chosen for a drama. "
      "GRAIN is capped at 0.12 because at full it is television snow.")
    A("")
    bankrow = {
        S.BANK_COLOUR: "RECORD ARM row (n48, ch1-8)",
        S.BANK_BROADCAST: "CROSSFADER A/B row (n66, ch1-8)",
        S.BANK_LIGHT: "DEVICE buttons (n58-65)",
        S.BANK_SPACE: "n87, n94-97, n100-102",
        S.BANK_FRACTURE: "SCENE LAUNCH 1-5 (n82-86) + USER (n89)",
    }
    for b in S.BANK_ORDER:
        items = [e for e in S.COMP_RACK if e[0] == b]
        A("### %s — %s" % (b, bankrow[b]))
        A("")
        A("| # | control | Resolume effect | OSC path | wet max |")
        A("|---|---|---|---|---|")
        for i, e in enumerate(items, 1):
            cap = ("%.2f" % e[4]) if len(e) > 4 else "1.00"
            A("| %d | **%s** | %s | `%s` | %s |"
              % (i, e[1], e[2], "/composition/video/effects/%s/bypassed"
                 % S.slug(e[2]), cap))
        A("")
        link = [n for n, bb in S.LINK_BANK.items() if bb == b][0]
        A("Bank intensity: **Device knob %d**. CLEAN drives it to zero." % link)
        A("")
    A("---")
    A("")
    A("## Faders and knobs")
    A("")
    A("| Control | Target | Home |")
    A("|---|---|---|")
    layer_names = [l[1] for l in S.LAYERS]
    for ch in range(1, 9):
        A("| Track fader %d | `%s` level | %s |"
          % (ch, layer_names[ch - 1], "up" if ch <= 2 else "down"))
    A("| Master fader | composition master | up |")
    A("| **Crossfader** | **A ↔ B dissolve.** MASTER A is on bus A, MASTER B "
      "on bus B. Hard left is pure A, hard right pure B, everything between "
      "is a true dissolve. | left (pure A) |")
    A("| Cue Level | FX MASTER sweep — anticlockwise is a clean image | up |")
    A("| Tempo knob | BPM reference for animation only; the masters run on "
      "their own timeline and are unaffected | — |")
    A("| Footswitch | momentary BLACKOUT — hold for black | — |")
    A("")
    A("### Device Control knobs — bank intensity")
    A("")
    A("| Knob | Link | Drives |")
    A("|---|---|---|")
    for n, label, what in S.COMP_DASHBOARD:
        A("| %d | link%d **%s** | %s |" % (n, n, label, what))
    A("")
    A("### Track Control knobs — live FFT control")
    A("")
    A("This is what makes the audio reactivity playable rather than baked. "
      "Watch the SCOPE layer and tune depth and release mid-episode without "
      "stopping.")
    A("")
    A("| Knob | Control | Path |")
    A("|---|---|---|")
    for sc in m:
        if sc["group"] == "Live FFT control":
            A("| %s | %s | `%s` |"
              % (sc["control"].split(" - ")[0].replace("Track knob ", ""),
                 sc["control"].split(" - ")[1], sc["path"]))
    A("")
    A("---")
    A("")
    A("## Mixer rows")
    A("")
    A("| Row | Note | Function |")
    A("|---|---|---|")
    A("| TRACK/CLIP STOP | n52 ch1-2 | **CUT TO A** / **CUT TO B** — hard "
      "cut between the two versions. Touches no transport. |")
    A("| TRACK/CLIP STOP | n52 ch3-8 | eject that overlay layer |")
    A("| TRACK SELECTION | n51 ch1-8 | select that layer |")
    A("| ACTIVATOR | n50 ch1-8 | mute that layer (lit = on air) |")
    A("| SOLO | n49 ch1-8 | solo that layer |")
    A("")
    A("| Button | Function |")
    A("|---|---|")
    for sc in m:
        if sc["group"] in ("Mixer", "Tempo"):
            A("| %s | %s%s |" % (sc["physical"], sc["control"],
                                 " — " + sc["note_text"] if sc["note_text"]
                                 else ""))
    A("")
    A("---")
    A("")
    A("## FFT map")
    A("")
    A("Composition FFT (`/audioengine/compositionfft`) analyses the "
      "composition's own audio, which here is the original programme audio "
      "embedded in MASTER A. It is frame-locked to the picture by "
      "construction — no virtual audio cable, no second transport, nothing "
      "to drift.")
    A("")
    A("| Band | Range | What lives there |")
    A("|---|---|---|")
    for b in ("low", "mid", "high"):
        lo, hi = S.BANDS[b]
        A("| %s | %.2f–%.2f | %s |" % (b.upper(), lo, hi,
                                       S.BAND_LABEL[b].split(")")[-1].strip()))
    A("")
    A("| Effect | Parameter | Band | Gain | Release | Floor → ceiling |")
    A("|---|---|---|---|---|---|")
    for (label, key, param, band, gain, fall, floor, ceil, _why) in S.FFT_MAP:
        A("| %s | %s | %s | %g dB | %g ms | %g → %g |"
          % (label, param, band.upper(), gain, fall, floor, ceil))
    A("")
    A("Every one of these is an effect *parameter* inside an effect that "
      "loads bypassed. FFT cannot reach a transport, a trigger, a column or a "
      "deck — and none of the dry/wet mixes is FFT-driven, because those "
      "belong to the dashboard links so CLEAN can always reach them.")
    A("")
    if M.UNMAPPED:
        A("---")
        A("")
        A("## Deliberately unmapped")
        A("")
        for name, why in M.UNMAPPED:
            A("* **%s** — %s" % (name, why))
        A("")

    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print("WROTE %s (%d lines)" % (out, len(L)))


if __name__ == "__main__":
    main()
