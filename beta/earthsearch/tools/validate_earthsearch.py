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

    # ---- the fixes that came out of the review round -------------------
    # Each of these guards a bug that shipped in an earlier draft and was
    # caught either by a reviewer or by asking the running application.
    print("\n=== regressions guarded ===")
    check("colours are ABGR-packed, which is Resolume's real layout",
          S.PALETTE["phosphor"] == 0xFFA8FF38,
          "phosphor 0x%X -> loads as #38FFA8" % S.PALETTE["phosphor"])
    check("no blend-mode cycling anywhere",
          "blendmode" not in preset_raw,
          "a 50-option ParamChoice, walked blind, passes 'to White'")
    check("no control can clear a master",
          "/composition/layers/1/clear" not in preset_raw
          and "/composition/layers/2/clear" not in preset_raw)
    check("GRAIN carries a wet ceiling",
          '<ValueRange name="startStop" min="0" max="0.12"' in comp_raw,
          "at full it is television snow")
    check("crossfader opens hard on A, not at centre",
          '<ParamRange name="Phase" T="DOUBLE" default="0" value="-1">'
          in comp_raw,
          "Phase runs -1..1; a home of 0 is a 50/50 double exposure")
    check("the crossfader snaps are normalised 0 / 0.5 / 1",
          preset_raw.count('<ValueRange min="0.5" max="0.5" />') == 1)
    check("the FLARE washes are radial, not half-frame ramps",
          comp_raw.count('<ParamChoice name="Type" T="INT32" default="0" '
                         'value="2" storeChoices="0" />') == 5)
    # The captions carry the crew and the ship at the performer's explicit
    # request. What is guarded now is not the absence of story text - that
    # decision is theirs - but that the geometry stays legible: roughly 25
    # characters fit across the frame at Size 1, so nothing may be written
    # wider than the frame, and Text Animator clamps below Size 0.5.
    caps = S.OVERLAY_CLIPS[5]
    too_wide = [c[0] for c in caps
                if c[1] == "TextGenerator"
                and len(c[2]["Text"]) / 25.0 * 1920 * c[2]["Size"] > 1860]
    check("no caption is written wider than the frame", not too_wide,
          ", ".join(too_wide) if too_wide else "widest is EARTHSEARCH at ~1690 px")
    check("no caption is below Text Animator's minimum size",
          all(c[2].get("Size", 1) >= 0.5 for c in caps))
    check("no dead effect: every rack entry loads a real value or a ceiling",
          all(e[3] or len(e) > 4 or e[2] in ("HueRotate", "InvertRGB",
                                             "ShiftRGB", "Trails", "Blur",
                                             "Freeze", "MirrorQuad",
                                             "Displace", "StopMotion",
                                             "PolarKaleido", "WarpSpeed")
              for e in S.COMP_RACK))

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
    for link_no in sorted(set(S.LAYER_LINK.values())):
        want = sum(1 for v in S.LAYER_LINK.values() if v == link_no)
        check("link%d carries %d layer opacit%s" % (link_no, want,
                                                    "y" if want == 1 else "ies"),
              links[str(link_no)] == want, "%s" % links[str(link_no)])
    check("CLEAN reaches every link that puts something on screen",
          set(S.CLEAN_LINKS) >= set(S.LINK_BANK) | set(S.LAYER_LINK.values()))

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
    m = M.build_map(S)
    # Several shortcuts sharing one MIDI key is the mechanism behind one-button
    # START BOTH and one-button CLEAN, so the check is not "are there
    # duplicates" but "are the duplicates exactly the four controls that are
    # supposed to have them".
    dup_keys = {k for k, n in collections.Counter(keys).items() if n > 1}
    dup_controls = set()
    for sc in shortcuts:
        if sc.find("RawInputMessage").get("key") in dup_keys:
            dup_controls.add(sc.find(
                "ShortcutPath[@name='InputPath']").get("path").rsplit(
                    "/", 1)[0])
    by_phys = collections.Counter(
        s2["physical"] for s2 in m
        if (M.note_key(s2["channel"], s2["note"]) if s2["kind"] == "note"
            else M.cc_key(s2["channel"], s2["cc"])) in
        {int(k) for k in dup_keys})
    expected = {"PLAY n91", "STOP ALL CLIPS n81", "BANK LOCK n103",
                "CUE LEVEL CC47"}
    check("multi-shortcut controls are exactly the intended four",
          set(by_phys) == expected,
          "%s" % sorted(by_phys))

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
