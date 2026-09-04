#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_earthsearch.py - offline checks on the two shipped artefacts.

Runs without Resolume. It cannot prove that a path resolves - that needs the
rig, and `verify_paths_osc.py` / `verify_on_rig.ps1` do it - but it does prove
that the .avc and the preset agree with each other and with the design
contract, which is where silent damage usually comes from.

    python validate_earthsearch.py
"""

import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

import es_apc_map as M
import es_spec as S

FAIL = []
PASS = []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append((name, detail))
    print("  %-5s %-58s %s" % ("PASS" if cond else "FAIL", name, detail))


def main():
    comp_path = os.path.join(S.OUTPUT_DIR, S.COMP_FILE)
    preset_path = os.path.join(S.OUTPUT_DIR, S.MIDI_PRESET_NAME + ".xml")
    for p in (comp_path, preset_path):
        if not os.path.exists(p):
            sys.exit("missing artefact: %s\nRun the builders first." % p)

    comp_raw = open(comp_path, encoding="utf-8").read()
    comp = ET.parse(comp_path).getroot()
    preset_raw = open(preset_path, encoding="utf-8").read()
    preset = ET.parse(preset_path).getroot()

    print("=== composition ===")
    layers = comp.findall("Layer")
    check("8 layers", len(layers) == S.NUM_LAYERS, "%d" % len(layers))
    clips = [c for c in comp.iter("Clip")
             if c.find("Params/Param[@name='Name']") is not None]
    check("43 clips (2 masters + 41 generative)", len(clips) == 43,
          "%d" % len(clips))
    check("exactly 2 file-backed clips",
          comp_raw.count("<VideoFormatReaderSource") == 2,
          "%d" % comp_raw.count("<VideoFormatReaderSource"))
    check("both masters have an audio track",
          comp_raw.count("<AudioFileSource") == 2,
          "%d - without this the FFT is silent"
          % comp_raw.count("<AudioFileSource"))
    check("media is .mov (Avenue cannot open .mkv, and will not decode mp3)",
          ".mov" in comp_raw and ".mkv" not in comp_raw)
    check("no embedded thumbnails", comp_raw.count("EmbeddedThumbnail") == 0)

    print("\n=== safety contract ===")
    ign = comp_raw.count('name="Ignore Column Trigger"')
    check("every layer ignores column triggers", ign == S.NUM_LAYERS,
          "%d of %d" % (ign, S.NUM_LAYERS))
    check("no fader-start anywhere", "Fader Start" not in comp_raw
          and "faderstart" not in comp_raw.lower())
    check("nothing triggers a clip on load",
          'name="Trigger first clip on load" altName="Trigger First Clip On '
          'Play" T="BOOL" default="0" value="1"' not in comp_raw)
    for m in re.finditer(r'<Transport name="Transport">(.*?)</Transport>',
                         comp_raw, re.S):
        if "PhaseSourceFFT" in m.group(1):
            check("no FFT inside a Transport", False, "found one")
            break
    else:
        check("no FFT inside a Transport", True)
    check("crossfader buses assigned",
          comp_raw.count('name="CrossFaderGroup"') == 2)

    print("\n=== FFT ===")
    n_fft = comp_raw.count('linkId="/audioengine/compositionfft"')
    expected = len(S.FFT_MAP) + sum(len(f) for cl in S.OVERLAY_CLIPS.values()
                                    for (_n, _g, _v, f) in cl)
    check("composition FFT used, not external FFT",
          "externalfft" not in comp_raw)
    check("%d FFT-driven parameters" % expected, n_fft == expected,
          "%d" % n_fft)
    gains = [float(g) for g in re.findall(
        r'<ParamRange name="Gain" T="DOUBLE" default="0" value="([0-9.]+)"',
        comp_raw)]
    check("every FFT gain is calibrated, not a club default",
          all(g >= 20 for g in gains),
          "min %g dB, max %g dB" % (min(gains), max(gains)))
    # No effect's dry/wet may be FFT-driven, or CLEAN could not reach it.
    dw_fft = re.findall(
        r'<ParamRange name="Opacity"[^>]*>\s*<DurationSource', comp_raw)
    check("no effect dry/wet is FFT-driven (CLEAN must reach all of them)",
          not dw_fft, "%d" % len(dw_fft))

    print("\n=== dashboard / CLEAN ===")
    links = collections.Counter(
        re.findall(r'PhaseSourceDashboardLink[^>]*linkId="/link(\d+)"',
                   comp_raw))
    check("all five effect banks are on a link",
          all(str(n) in links for n in S.LINK_BANK))
    check("every rack effect is gated by a bank link",
          sum(links[str(n)] for n in S.LINK_BANK) == len(S.COMP_RACK),
          "%d of %d" % (sum(links[str(n)] for n in S.LINK_BANK),
                        len(S.COMP_RACK)))
    check("all five overlay layers are on link6", links["6"] == 5,
          "%s" % links["6"])
    check("the scope is on link7", links["7"] == 1)

    print("\n=== preset ===")
    shortcuts = list(preset.iter("Shortcut"))
    check("preset name matches the composition",
          preset.get("name") == S.MIDI_PRESET_NAME)
    check("shortcut count", len(shortcuts) > 0, "%d" % len(shortcuts))
    for bad in M.FORBIDDEN_PATHS:
        check("no %r path (would seek/retrigger a master)" % bad,
              bad not in preset_raw)
    paths = [sc.find("ShortcutPath[@name='InputPath']").get("path")
             for sc in shortcuts]
    check("no clip-connect on a master except START BOTH",
          sum(1 for p in paths
              if re.match(r"/composition/layers/[12]/clips/", p)) == 2,
          "2 = the two START BOTH shortcuts")
    keys = [sc.find("RawInputMessage").get("key") for sc in shortcuts]
    dup = {k: n for k, n in collections.Counter(keys).items() if n > 1}
    check("multi-shortcut keys are only the intended ones",
          len(dup) == 5, "%d controls carry more than one shortcut" % len(dup))

    print("\n=== coverage ===")
    m = M.build_map(S)
    covered = {(sc["kind"], sc["channel"],
                sc["note"] if sc["kind"] == "note" else sc["cc"])
               for sc in m}
    import gen_preset_earthsearch as G
    inv = G.physical_inventory()
    missing = [c for c in inv if c not in covered]
    check("every control on the surface has a job", not missing,
          "%d unmapped" % len(missing))

    print("\n=== cross-artefact agreement ===")
    fx_in_comp = {S.slug(e[2]) for e in S.COMP_RACK}
    fx_in_preset = {re.search(r"/effects/([^/]+)/bypassed", p).group(1)
                    for p in paths if "/effects/" in p and
                    p.endswith("/bypassed")}
    check("every rack effect has a button", fx_in_comp == fx_in_preset,
          "comp-only %s preset-only %s" % (fx_in_comp - fx_in_preset,
                                           fx_in_preset - fx_in_comp))

    print("\n=== %d passed, %d failed ===" % (len(PASS), len(FAIL)))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
