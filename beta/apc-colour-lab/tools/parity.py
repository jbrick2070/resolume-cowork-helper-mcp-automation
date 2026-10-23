#!/usr/bin/env python3
"""Run identical scenarios through engine.py and demo/engine.js and diff every
message they emit and every pad colour the emulated surface shows.

    python tools/parity.py          # exits non-zero on any difference
"""
import json
import os
import random
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from apc_lab import engine as E          # noqa: E402
from apc_lab import protocol as P        # noqa: E402


def scenario(theme, seed):
    rnd = random.Random(seed)
    ev = []
    t = 0.0
    # Resolume loads a pack-like grid: dim clips everywhere, one playing per row.
    fams = [(49, 50), (41, 42), (21, 22), (9, 10), (3, 2)]
    for row in range(5):
        for col in range(8):
            on, dim = fams[row]
            ev.append({"kind": "resolume", "t": 0.0, "msg": ["on", 1, row * 8 + col, on if col == row else dim]})
    ev.append({"kind": "resolume", "t": 0.0, "msg": ["on", 1, 82, 45]})
    ev.append({"kind": "resolume", "t": 0.0, "msg": ["on", 1, 86, 46]})
    for _ in range(60):
        t = round(t + rnd.choice([0.01, 0.02, 0.05, 0.11, 0.25]), 3)
        r = rnd.random()
        if r < 0.55:
            ev.append({"kind": "tick", "t": t})
        elif r < 0.8:
            ev.append({"kind": "apc", "t": t, "msg": ["on", 1, rnd.randrange(40), rnd.randrange(1, 128)]})
        elif r < 0.93:
            n = rnd.randrange(40)
            if rnd.random() < 0.3:
                ev.append({"kind": "resolume", "t": t, "msg": ["off", 1, n, 0]})
            else:
                ev.append({"kind": "resolume", "t": t, "msg": ["on", 1, n, rnd.choice([21, 22, 5, 6, 9, 3, 127, 45, 57])]})
        else:
            ev.append({"kind": "theme", "t": t, "theme": rnd.choice(E.THEME_ORDER)})
    ev.append({"kind": "tick", "t": round(t + 2.0, 3)})
    return {"theme": theme, "bpm": 128.0, "events": ev, "samples": [0.0, 0.7, 1.9, 4.2, round(t + 2.0, 3)]}


def run_python(sc):
    r = E.Router(sc["theme"], sc["bpm"])
    s = E.Surface()
    log = []
    for e in sc["events"]:
        if e["kind"] == "resolume":
            out = r.from_resolume(tuple(e["msg"]), e["t"])
        elif e["kind"] == "apc":
            out = r.from_apc(tuple(e["msg"]), e["t"])[1]
        elif e["kind"] == "theme":
            out = r.set_theme(e["theme"], e["t"])
        else:
            out = r.tick(e["t"])
        for m in out:
            s.apply(m, e["t"])
        log.append([list(m) for m in out])
    samples = [[[round(x, 3) for x in s.rgb(n, tt, sc["bpm"])] for n in P.ALL_PADS] for tt in sc["samples"]]
    return {"log": log, "samples": samples}


def main():
    bad = 0
    total_msgs = 0
    for theme in E.THEME_ORDER:
        for seed in range(6):
            sc = scenario(theme, seed)
            py = run_python(sc)
            node = subprocess.run(["node", os.path.join(ROOT, "demo", "run_scenario.js")],
                                  input=json.dumps(sc), capture_output=True, text=True, check=True)
            js = json.loads(node.stdout)
            total_msgs += sum(len(x) for x in py["log"])
            if py["log"] != js["log"]:
                bad += 1
                for i, (a, b) in enumerate(zip(py["log"], js["log"])):
                    if a != b:
                        print("MESSAGE DIFF theme=%s seed=%d event=%d\n  py %s\n  js %s" % (theme, seed, i, a[:4], b[:4]))
                        break
            else:
                a = json.dumps(py["samples"])
                b = json.dumps(js["samples"])
                if a != b:
                    bad += 1
                    print("COLOUR DIFF theme=%s seed=%d" % (theme, seed))
    print("parity: %d scenarios, %d messages compared, %d differ" % (len(E.THEME_ORDER) * 6, total_msgs, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
