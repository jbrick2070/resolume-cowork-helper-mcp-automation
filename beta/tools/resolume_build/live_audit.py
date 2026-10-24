#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_audit.py - walk every deck and column of a composition on the running Avenue and measure what the
performer would actually see.

    python -u -m resolume_build.live_audit "packs/signal-lost/Signal Lost - Transmission From Tomorrow.avc" \
        --still 2:6,4:8 --out research/audit/signal-lost

Opens a TEMPORARY copy (never the original: Avenue may re-save an open file when it quits), lifts solo,
bypass and crossfader sides in the live state only, then for every deck and column: connects the column,
lets the clip crossfades settle, records the Composition Monitor for a couple of seconds and measures

  brightness   mean luminance, share of near-black and near-white pixels
  motion       frame-to-frame change (a column that moves in silence is a kinetic column)
  flashing     luminance swing and reversals per second (the three-flashes-a-second guideline)
  captions     layer 5 soloed: the bounding box of the text, inside the safe margins or not
  gpu          Avenue's 3D-engine utilisation during the capture (Windows GPU Engine counters)

and writes <out>.json and <out>.md. Columns named with --still are allowed to be nearly motionless.
It takes the screen for a few minutes (Avenue is brought to the front), so run it only when the rig
has been handed over. The audio-driven parts only move if music is playing into Avenue.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import gallery, rig, screen            # noqa: E402
from resolume_build.before_after import temp_copy          # noqa: E402

SIZE = (320, 180)
FPS = 8
SECONDS = 2.5
SETTLE = 1.3
SAFE = 0.03                      # captions must stay this far (fraction of the frame) from every edge
CAPTION_LAYER = 5


def avenue_pid():
    import psutil
    for p in psutil.process_iter(["name", "pid"]):
        if (p.info["name"] or "").lower() == "avenue.exe":
            return p.info["pid"]
    return None


def start_gpu(pid, samples=2):
    """A PowerShell Get-Counter running while the frames are captured; collect() returns the readings."""
    cmd = ("$s = Get-Counter '\\GPU Engine(*pid_%d*engtype_3D)\\Utilization Percentage' -SampleInterval 1 "
           "-MaxSamples %d -ErrorAction SilentlyContinue; ($s | ForEach-Object { "
           "($_.CounterSamples | Measure-Object CookedValue -Sum).Sum }) -join ','" % (pid, samples))
    return subprocess.Popen(["powershell", "-NoProfile", "-Command", cmd], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True)


def collect_gpu(proc):
    try:
        out, _ = proc.communicate(timeout=20)
        vals = [float(x) for x in out.strip().split(",") if x.strip()]
        return (max(vals) if vals else None)
    except Exception:
        return None


def lum(img):
    return np.asarray(img.convert("L").resize(SIZE), dtype=np.float32) / 255.0


def grab(hwnd, n, fps):
    frames, t_next = [], time.time()
    for _ in range(n):
        frames.append(lum(screen.grab_monitor(hwnd, front=False)))
        t_next += 1.0 / fps
        time.sleep(max(0.0, t_next - time.time()))
    return frames


def stats(frames, fps):
    means = np.array([f.mean() for f in frames])
    diffs = [float(np.abs(frames[i + 1] - frames[i]).mean()) for i in range(len(frames) - 1)]
    dm = np.diff(means)
    sig = dm[np.abs(dm) > 0.03]
    reversals = int(np.sum(np.sign(sig[1:]) != np.sign(sig[:-1]))) if len(sig) > 1 else 0
    dur = len(frames) / float(fps)
    moving = [float((np.abs(frames[i + 1] - frames[i]) > 0.03).mean()) for i in range(len(frames) - 1)]
    lag = max(1, int(fps))                                  # one second apart: slow drift shows up here
    drift = [float((np.abs(frames[i + lag] - frames[i]) > 0.03).mean()) for i in range(len(frames) - lag)]
    return dict(mean=float(means.mean()), black=float(np.mean([(f < 0.03).mean() for f in frames])),
                white=float(np.mean([(f > 0.95).mean() for f in frames])),
                motion=float(np.mean(diffs)) if diffs else 0.0, swing=float(means.max() - means.min()),
                moving_px=float(np.mean(moving)) if moving else 0.0,
                drift_px=float(np.mean(drift)) if drift else 0.0,
                flash_hz=round(reversals / 2.0 / dur, 2))


def caption_box(hwnd, layer, settle=1.2, dark=False):
    """Bounding box of the TEXT layer's visible text as fractions of the frame, or None.
    Light text is found by soloing the layer on black. Dark text on a light bed is found by comparing the bed
    alone (layer 1) with bed + text."""
    ref = None
    if dark:
        rig.put("/composition/layers/1", {"solo": {"value": True}})
        time.sleep(0.9)
        ref = grab(hwnd, 2, 4)[-1]
    rig.put("/composition/layers/%d" % layer, {"solo": {"value": True}})
    time.sleep(settle)
    f = grab(hwnd, 3, 6)
    mask = (lambda x: np.abs(x - ref) > 0.08) if dark else (lambda x: x > 0.12)
    if max(float(mask(x).sum()) for x in f) < 12:          # an animated caption may be between loops: look for 6 s
        f += grab(hwnd, 12, 2)
    rig.put("/composition/layers/%d" % layer, {"solo": {"value": False}})
    if dark:
        rig.put("/composition/layers/1", {"solo": {"value": False}})
    best = max(f, key=lambda x: float(mask(x).sum()))
    ys, xs = np.where(mask(best))
    if len(xs) < 12:
        return None
    h, w = best.shape
    return dict(x0=round(xs.min() / w, 3), x1=round((xs.max() + 1) / w, 3),
                y0=round(ys.min() / h, 3), y1=round((ys.max() + 1) / h, 3))


def caption_ok(b):
    if b is None:
        return True
    return b["x0"] >= SAFE and b["y0"] >= SAFE and b["x1"] <= 1 - SAFE and b["y1"] <= 1 - SAFE


def caption_info(col, layer=CAPTION_LAYER):
    """(has text, text luminance 0..1) of the TEXT layer's clip in this column."""
    try:
        c = rig.get("/composition/layers/%d/clips/%d" % (layer, col))
        sp = c["video"]["sourceparams"]
        text = str(sp.get("Text", {}).get("value", "")).strip()
        colr = str(sp.get("Color", {}).get("value", "#ffffffff")).lstrip("#")
        r, g, b = (int(colr[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        return bool(text), 0.299 * r + 0.587 * g + 0.114 * b
    except Exception:
        return False, 1.0


def parse_still(text):
    return {tuple(int(x) for x in p.split(":")) for p in text.split(",")} if text else set()


def run(avc, still, out, decks=None, captions=True):
    path = temp_copy(avc, "audit")
    print("opening %s" % os.path.basename(path), flush=True)
    t0 = time.time()
    c = gallery.open_and_wait(path, timeout=900)
    if not c:
        raise SystemExit("did not open")
    print("opened after %.0f s" % (time.time() - t0), flush=True)
    gallery.reveal(c)
    rig.post("/composition/disconnect-all")
    time.sleep(2.5)
    hwnd = screen.avenue_hwnd()
    screen.bring_to_front(hwnd)
    screen.pin(hwnd)
    pid = avenue_pid()
    ndecks = len(c["decks"])
    ncols = len(c["columns"])
    cells = []
    for deck in range(1, ndecks + 1):
        if decks and deck not in decks:
            continue
        rig.post("/composition/decks/%d/select" % deck)
        time.sleep(1.2)
        cd = rig.composition()
        dname = cd["decks"][deck - 1]["name"]["value"]
        for col in range(1, ncols + 1):
            rig.post("/composition/columns/%d/connect" % col)
            time.sleep(SETTLE)
            gpu = start_gpu(pid) if pid else None
            frames = grab(hwnd, int(FPS * SECONDS), FPS)
            s = stats(frames, FPS)
            try:
                from PIL import Image
                d_ = os.path.join(os.path.dirname(out) or ".", "frames", os.path.basename(out))
                os.makedirs(d_, exist_ok=True)
                Image.fromarray((frames[-1] * 255).astype("uint8")).save(os.path.join(d_, "d%dc%d.png" % (deck, col)))
            except Exception:
                pass
            s["gpu_max"] = collect_gpu(gpu) if gpu else None
            cn = cd["columns"][col - 1]["name"]["value"]
            exp, lumi = caption_info(col) if captions else (False, 1.0)
            cb = caption_box(hwnd, CAPTION_LAYER, dark=(lumi < 0.25)) if captions else None
            s.update(deck=deck, deck_name=dname, col=col, col_name=cn, caption=cb, caption_expected=exp,
                     still=((deck, col) in still))
            cells.append(s)
            print("deck %d col %d %-18s mean %.2f motion %.4f swing %.2f flash %.1f Hz gpu %s caption %s" % (
                deck, col, cn[:18], s["mean"], s["motion"], s["swing"], s["flash_hz"],
                "-" if s["gpu_max"] is None else "%.0f%%" % s["gpu_max"],
                "-" if cb is None else "%.2f..%.2f x %.2f..%.2f" % (cb["x0"], cb["x1"], cb["y0"], cb["y1"])), flush=True)
    rig.post("/composition/disconnect-all")
    screen.pin(hwnd, False)
    return cells


def findings(cells):
    f = {"black": [], "blown": [], "frozen": [], "flashy": [], "caption_missing": [], "caption_edge": [], "gpu_heavy": []}
    for s in cells:
        tag = "deck %d col %d %s" % (s["deck"], s["col"], s["col_name"])
        if s["mean"] < 0.025:
            f["black"].append(tag)
        if s["mean"] > 0.85 or s["white"] > 0.30:
            f["blown"].append("%s (mean %.2f, %.0f%% white)" % (tag, s["mean"], 100 * s["white"]))
        if (s["motion"] < 0.0015 and s["swing"] < 0.01 and s.get("moving_px", 0.0) < 0.003
                and s.get("drift_px", 0.0) < 0.01 and s["mean"] >= 0.025 and not s["still"]):
            f["frozen"].append("%s (%.2f%% of pixels change per frame, %.2f%% over a second)" % (
                tag, 100 * s.get("moving_px", 0.0), 100 * s.get("drift_px", 0.0)))
        if s["flash_hz"] >= 3.0 and s["swing"] >= 0.12:
            f["flashy"].append("%s (%.1f Hz, swing %.2f)" % (tag, s["flash_hz"], s["swing"]))
        if s.get("caption_expected") and s["caption"] is None:
            f["caption_missing"].append("%s (a caption is set but nothing is visible)" % tag)
        if not caption_ok(s["caption"]):
            b = s["caption"]
            f["caption_edge"].append("%s (box %.2f..%.2f x %.2f..%.2f)" % (tag, b["x0"], b["x1"], b["y0"], b["y1"]))
        if s["gpu_max"] is not None and s["gpu_max"] > 85:
            f["gpu_heavy"].append("%s (%.0f%%)" % (tag, s["gpu_max"]))
    return f


def write(out, name, cells):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    f = findings(cells)
    with open(out + ".json", "w", encoding="utf-8") as fh:
        json.dump(dict(composition=name, cells=cells, findings=f), fh, indent=1)
    gp = [s["gpu_max"] for s in cells if s["gpu_max"] is not None]
    lines = ["# Live audit - %s" % name, "",
             "%d columns walked. Motion in silence unless music was playing; flash rate is an estimate at %d fps." % (len(cells), FPS), ""]
    lines.append("| finding | count |")
    lines.append("|---|---|")
    for k, v in f.items():
        lines.append("| %s | %d |" % (k.replace("_", " "), len(v)))
    if gp:
        lines.append("| gpu max / mean of maxima | %.0f%% / %.0f%% |" % (max(gp), sum(gp) / len(gp)))
    lines.append("")
    for k, v in f.items():
        if v:
            lines += ["## %s" % k.replace("_", " "), ""] + ["- " + x for x in v] + [""]
    with open(out + ".md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("avc")
    ap.add_argument("--out", required=True, help="path stem for the .json and .md reports")
    ap.add_argument("--still", default="", help="deck:column pairs designed to be nearly motionless, e.g. 2:6,4:8")
    ap.add_argument("--decks", default="", help="only these decks, e.g. 1,3")
    ap.add_argument("--no-captions", action="store_true")
    a = ap.parse_args()
    decks = {int(x) for x in a.decks.split(",")} if a.decks else None
    cells = run(a.avc, parse_still(a.still), a.out, decks, not a.no_captions)
    f = write(a.out, os.path.basename(a.avc), cells)
    print("wrote %s.json / .md  |  %s" % (a.out, "  ".join("%s %d" % (k, len(v)) for k, v in f.items())), flush=True)


if __name__ == "__main__":
    main()
