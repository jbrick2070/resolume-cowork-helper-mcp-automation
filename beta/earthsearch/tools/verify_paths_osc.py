#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_paths_osc.py - prove that every path in the MIDI preset resolves.

A Resolume MIDI shortcut whose path does not resolve is silently inert: the
preset loads, the button does nothing, and you find out on stage. This script
removes that risk by exercising the SAME address space over OSC and reading the
result back over REST.

Requirements on the rig:
  Preferences > OSC   : OSC Input enabled, Incoming Port 7000
  Preferences > Webserver : Enable Webserver & REST API, port 8080
  The EarthSearch composition open.

    python verify_paths_osc.py
    python verify_paths_osc.py --all      # every path, not just a sample
"""

import argparse
import socket
import struct
import sys
import time
import json
import urllib.request

import es_apc_map as M
import es_spec as S

OSC_HOST, OSC_PORT = "127.0.0.1", 7000
REST = "http://127.0.0.1:8080/api/v1"


def osc_pad(b):
    return b + b"\x00" * (4 - len(b) % 4)


def osc_message(address, value):
    """Minimal OSC 1.0 encoder: one float argument."""
    out = osc_pad(address.encode("utf-8") + b"\x00")
    out += osc_pad(b",f\x00")
    out += struct.pack(">f", float(value))
    return out


def send(sock, address, value):
    sock.sendto(osc_message(address, value), (OSC_HOST, OSC_PORT))


def rest(path):
    with urllib.request.urlopen(REST + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def composition():
    return rest("/composition")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    comp = composition()
    if comp["name"]["value"] != S.COMP_NAME:
        sys.exit("The EarthSearch composition is not open (found %r)."
                 % comp["name"]["value"])

    fx = {e["name"]: e for e in comp["video"]["effects"]}
    ok = bad = 0

    print("=== effect bypass paths (one per composition-rack effect) ===")
    for (_bank, label, key, _v) in S.COMP_RACK:
        name = key
        path = "/composition/video/effects/%s/bypassed" % S.slug(key)
        before = fx[name]["bypassed"]["value"]
        send(sock, path, 0.0 if before else 1.0)
        time.sleep(0.35)
        after = {e["name"]: e for e in composition()["video"]["effects"]
                 }[name]["bypassed"]["value"]
        good = after != before
        print("  %-6s %-46s %s -> %s" % ("OK" if good else "DEAD", path,
                                         before, after))
        if good:
            ok += 1
            send(sock, path, 1.0 if before else 0.0)   # put it back
            time.sleep(0.2)
        else:
            bad += 1

    print("\n=== FFT behaviour paths (the live depth / release knobs) ===")
    for band in ("low", "mid", "high"):
        label, key, param = S.FFT_BAND_ANCHOR[band]
        base = ("/composition/video/effects/%s/effect/%s"
                % (S.slug(key), S.param_slug(key, param)))
        for leaf, probe in (("behaviour/gain", 20.0),
                            ("behaviour/fallback", 800.0)):
            path = "%s/%s" % (base, leaf)
            pid = fx[key]["params"][param]["id"]
            ps = rest("/parameter/by-id/%d/phase-source" % pid)
            pname = "Gain" if leaf.endswith("gain") else "Fallback"
            before = ps["parameters"][pname]["value"]
            send(sock, path, probe)
            time.sleep(0.4)
            after = rest("/parameter/by-id/%d/phase-source"
                         % pid)["parameters"][pname]["value"]
            good = abs(after - before) > 1e-6
            print("  %-6s %-62s %.2f -> %.2f" % ("OK" if good else "DEAD",
                                                 path, before, after))
            ok += good
            bad += not good
            send(sock, path, before)
            time.sleep(0.2)

    print("\n=== composition dashboard links (CLEAN / bank intensity) ===")
    for n in S.CLEAN_LINKS:
        path = "/composition/dashboard/link%d" % n
        before = composition()["dashboard"]["Link %d" % n]["value"]
        send(sock, path, 0.25)
        time.sleep(0.35)
        after = composition()["dashboard"]["Link %d" % n]["value"]
        good = abs(after - 0.25) < 0.02
        print("  %-6s %-40s %.3f -> %.3f" % ("OK" if good else "DEAD", path,
                                             before, after))
        ok += good
        bad += not good
        send(sock, path, before)
        time.sleep(0.15)

    print("\n=== layer paths ===")
    layer_paths = []
    for i in range(1, S.NUM_LAYERS + 1):
        layer_paths.append(("/composition/layers/%d/master" % i, 0.5,
                            lambda c, i=i: c["layers"][i - 1]["master"]["value"]))
    for path, probe, getter in layer_paths:
        before = getter(composition())
        send(sock, path, probe)
        time.sleep(0.3)
        after = getter(composition())
        good = abs(after - probe) < 0.02
        print("  %-6s %-40s %.3f -> %.3f" % ("OK" if good else "DEAD", path,
                                             before, after))
        ok += good
        bad += not good
        send(sock, path, before)
        time.sleep(0.15)

    print("\n=== crossfader ===")
    for path, probe in (("/composition/crossfader/phase", 0.5),
                        ("/composition/master", 0.8)):
        c = composition()
        before = (c["crossfader"]["phase"]["value"] if "crossfader" in path
                  else c["master"]["value"])
        send(sock, path, probe)
        time.sleep(0.3)
        c = composition()
        after = (c["crossfader"]["phase"]["value"] if "crossfader" in path
                 else c["master"]["value"])
        good = abs(after - probe) < 0.02
        print("  %-6s %-40s %.3f -> %.3f" % ("OK" if good else "DEAD", path,
                                             before, after))
        ok += good
        bad += not good
        send(sock, path, before)
        time.sleep(0.15)

    print("\n=== %d paths resolved, %d dead ===" % (ok, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
