#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harvest_osc_paths.py - ask Resolume what its own OSC addresses are.

Guessing an effect's OSC slug is the single easiest way to ship a MIDI preset
full of buttons that do nothing: the preset loads, the path silently fails to
resolve, and the control is dead with no error anywhere. This tool removes the
guess entirely.

It listens on Resolume's OSC OUTPUT port while nudging each parameter through
the REST API, and prints the address Resolume itself emits for that parameter.

Requirements on the rig:
  Preferences > OSC       : OSC Output enabled, Outgoing 127.0.0.1 port 7001
  Preferences > Webserver : Enable Webserver & REST API, port 8080
  The EarthSearch composition open.

    python harvest_osc_paths.py
"""

import json
import socket
import struct
import sys
import threading
import time
import urllib.request

REST = "http://127.0.0.1:8080/api/v1"
OSC_LISTEN_PORT = 7001

_seen = []
_lock = threading.Lock()
_stop = threading.Event()


def osc_parse(data):
    """Return (address, args) from a minimal OSC packet. Bundles are walked."""
    out = []

    def one(buf):
        if buf.startswith(b"#bundle\x00"):
            i = 16
            while i < len(buf):
                (size,) = struct.unpack_from(">i", buf, i)
                i += 4
                one(buf[i:i + size])
                i += size
            return
        z = buf.find(b"\x00")
        if z < 0:
            return
        addr = buf[:z].decode("utf-8", "replace")
        i = (z // 4 + 1) * 4
        args = []
        if i < len(buf) and buf[i:i + 1] == b",":
            z2 = buf.find(b"\x00", i)
            tags = buf[i + 1:z2].decode("ascii", "replace")
            i = (z2 // 4 + 1) * 4
            for t in tags:
                if t == "f" and i + 4 <= len(buf):
                    args.append(struct.unpack_from(">f", buf, i)[0]); i += 4
                elif t == "i" and i + 4 <= len(buf):
                    args.append(struct.unpack_from(">i", buf, i)[0]); i += 4
                elif t in "sS":
                    z3 = buf.find(b"\x00", i)
                    args.append(buf[i:z3].decode("utf-8", "replace"))
                    i = (z3 // 4 + 1) * 4
                elif t in "TF":
                    args.append(t == "T")
        out.append((addr, args))

    one(data)
    return out


def listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("127.0.0.1", OSC_LISTEN_PORT))
    s.settimeout(0.3)
    while not _stop.is_set():
        try:
            data, _ = s.recvfrom(65535)
        except socket.timeout:
            continue
        for addr, args in osc_parse(data):
            with _lock:
                _seen.append((addr, args))
    s.close()


def rest_get(path):
    with urllib.request.urlopen(REST + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def rest_put(path, value):
    body = json.dumps({"value": value}).encode("utf-8")
    req = urllib.request.Request(REST + path, data=body, method="PUT",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status


def nudge(param_id, value):
    """Change a parameter and return every OSC address Resolume emitted."""
    with _lock:
        _seen.clear()
    rest_put("/parameter/by-id/%d" % param_id, value)
    time.sleep(0.6)
    with _lock:
        return list(_seen)


def main():
    t = threading.Thread(target=listener, daemon=True)
    t.start()
    time.sleep(0.5)

    comp = rest_get("/composition")
    print("composition: %s" % comp["name"]["value"])

    # Are we hearing anything at all?
    probe = nudge(comp["dashboard"]["Link 8"]["id"], 0.42)
    if not probe:
        sys.exit("No OSC received on port %d. Enable Preferences > OSC > "
                 "OSC Output (127.0.0.1, port %d)." % (OSC_LISTEN_PORT,
                                                       OSC_LISTEN_PORT))
    print("OSC output confirmed: %s\n" % probe[0][0])
    rest_put("/parameter/by-id/%d" % comp["dashboard"]["Link 8"]["id"], 1.0)

    print("=== effect bypass addresses ===")
    results = {}
    for e in comp["video"]["effects"]:
        name = e["name"]
        if name == "Transform":
            continue
        bid = e["bypassed"]["id"]
        cur = e["bypassed"]["value"]
        got = nudge(bid, not cur)
        addr = next((a for a, _ in got if a.endswith("/bypassed")), None)
        results[name] = addr
        print("  %-16s %s" % (name, addr or "(no address emitted)"))
        rest_put("/parameter/by-id/%d" % bid, cur)
        time.sleep(0.2)

    print("\n=== a few parameter addresses ===")
    interesting = [
        ("Bloom", "Amount"), ("Trails", "Feedback"),
        ("ShiftRGB", "Distance"), ("LoRezEffect", "Dither"),
        ("HueRotate", "Hue Rotate"), ("WaveWarp", "Height"),
        ("Ripples", "Amplitude Both"), ("Iterate", "StartOpacity"),
    ]
    for ename, pname in interesting:
        e = next((x for x in comp["video"]["effects"] if x["name"] == ename),
                 None)
        if not e or pname not in e.get("params", {}):
            print("  %-16s %-18s (not found)" % (ename, pname))
            continue
        p = e["params"][pname]
        got = nudge(p["id"], (p["value"] + 0.05) % 1.0)
        addr = next((a for a, _ in got if "/effects/" in a), None)
        print("  %-16s %-18s %s" % (ename, pname, addr or "(none)"))
        rest_put("/parameter/by-id/%d" % p["id"], p["value"])
        time.sleep(0.2)

    print("\n=== composition-level addresses ===")
    for label, pid, val in (
            ("master", comp["master"]["id"], 0.9),
            ("crossfader phase", comp["crossfader"]["phase"]["id"], 0.4),
            ("layer 1 master", comp["layers"][0]["master"]["id"], 0.9),
            ("layer 2 opacity", comp["layers"][1]["video"]["opacity"]["id"],
             0.4)):
        got = nudge(pid, val)
        addr = got[0][0] if got else None
        print("  %-18s %s" % (label, addr or "(none)"))

    _stop.set()
    time.sleep(0.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
