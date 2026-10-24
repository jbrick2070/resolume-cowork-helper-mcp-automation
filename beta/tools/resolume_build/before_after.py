#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
before_after.py - record the same columns from two builds of a composition on the running Avenue
and write one side-by-side looping GIF (before on the left, after on the right), plus the rig
read-back of the "after" build.

    python -m resolume_build.before_after \
        --still react-kit/beta/signal-lost/"Signal Lost - Transmission From Tomorrow.avc" \
        --kinetic packs/signal-lost/"Signal Lost - Transmission From Tomorrow.avc" \
        --bible packs/signal-lost/bible.json --decks packs/signal-lost/decks.json \
        --shots 1:2,2:7,4:5,5:6 --out clip.gif

Per build it opens a TEMPORARY copy (never the original: Avenue may re-save an open file when it
quits), and for the "after" build it runs verify_pack on the freshly opened composition BEFORE any
live change, so the layer settings are read back clean. Then it lifts solo / bypass / crossfader
sides in the live state only (nothing is saved) and records each shot from Avenue's Composition
Monitor.

Opening replaces what is open in Avenue and the recording brings Avenue to the front, so run it
only when the rig has been handed over. The audio-driven parts only move if music is playing into
Avenue's audio input while it records: play a track first.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import gallery, rig, screen          # noqa: E402

from PIL import Image, ImageDraw, ImageFont               # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG, INK, DIM, GOOD = (16, 17, 21), (236, 236, 242), (140, 142, 152), (61, 220, 132)


def font(size):
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def temp_copy(src, tag):
    """A temporary copy whose FILE NAME carries the tag. Avenue names an open composition after its
    file, so the two builds get different names and a slow load can never be mistaken for the
    new one."""
    d = os.path.join(tempfile.gettempdir(), "resolume_gallery", tag)
    os.makedirs(d, exist_ok=True)
    stem, ext = os.path.splitext(os.path.basename(src))
    dst = os.path.join(d, "%s [%s]%s" % (stem, tag, ext))
    shutil.copy2(src, dst)
    return dst


def parse_shots(text):
    return [tuple(int(x) for x in part.split(":")) for part in text.split(",")]


def expected_captions(decks_path):
    """{(deck, column): caption text} from a decks.json, to prove each shot landed on the cell it was meant to."""
    import json
    if not decks_path:
        return {}
    d = json.load(open(decks_path, encoding="utf-8"))
    decks = d["decks"] if isinstance(d, dict) and "decks" in d else d
    out = {}
    for di, dk in enumerate(decks):
        for c in dk.get("clips", []):
            if c.get("layer") == 5 and c.get("params", {}).get("Text"):
                out[(di + 1, int(c["column"]))] = " ".join(str(c["params"]["Text"]).split())
    return out


def land(deck, col, expected, tries=4):
    """Select the deck, connect the column and PROVE it took: the TEXT layer's clip in that column must be connected
    and carry the expected caption. Avenue is sometimes slow to switch deck; retry by going to another deck and back."""
    nd = len(rig.composition()["decks"])
    for attempt in range(tries):
        if attempt and nd > 1:
            rig.post("/composition/decks/%d/select" % (deck % nd + 1))
            time.sleep(2.0)
        rig.post("/composition/decks/%d/select" % deck)
        t0 = time.time()
        while time.time() - t0 < 8:
            c = rig.composition()
            if c["decks"][deck - 1].get("selected", {}).get("value"):
                break
            time.sleep(0.5)
        time.sleep(1.5)
        rig.post("/composition/columns/%d/connect" % col)
        time.sleep(2.0)
        try:
            clip = rig.get("/composition/layers/5/clips/%d" % col)
            live = " ".join(str(clip["video"]["sourceparams"].get("Text", {}).get("value", "")).split())
            connected = str(clip.get("connected", {}).get("value", "")).lower().startswith("connected")
        except Exception:
            live, connected = "", False
        if (connected or expected) and (not expected or live == expected):     # the caption text proves the cell
            return True
        print("  shot deck %d col %d landed on %r (connected=%s), retrying" % (deck, col, live[:30], connected), flush=True)
    return False


def record(avc, tag, shots, fps, seconds, size, verify=None, expected=None):
    path = temp_copy(avc, tag)
    t0 = time.time()
    print("%s: opening %s" % (tag, os.path.basename(path)), flush=True)
    c = gallery.open_and_wait(path, timeout=900)
    if not c:
        raise SystemExit("did not open %s" % tag)
    print("%s: open returned after %.0f s" % (tag, time.time() - t0), flush=True)
    verdict = None
    if verify:                                    # read the fresh composition back before any live change
        import json
        print("%s: reading the composition back" % tag, flush=True)
        with open(verify["bible"], encoding="utf-8") as f:
            bible = json.load(f)
        bible["comp_name"] = c["name"]["value"]    # what Avenue calls it (the header's Name, not the temp file's)
        bible_tmp = os.path.join(os.path.dirname(path), "bible_tmp.json")
        with open(bible_tmp, "w", encoding="utf-8") as f:
            json.dump(bible, f)
        r = subprocess.run([sys.executable, "-W", "ignore", "-m", "resolume_build.verify_pack", "--avc", path,
                            "--no-open", "--bible", bible_tmp, "--decks", verify["decks"], "--connect",
                            "--layer-blends", verify["blends"]], cwd=ROOT, capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        with open(verify["out"], "w", encoding="utf-8") as f:
            f.write(out)
        lines = out.splitlines()
        verdict = next((l.strip() for l in reversed(lines) if "checks," in l), "no summary line")
        print("%s read-back: %s" % (tag, verdict), flush=True)
        c = rig.composition()
    gallery.reveal(c)
    # The read-back connects clips, and the SCOPE layer ignores column triggers, so a clip it connected
    # would stay on screen in the "after" recording only. Both builds start from nothing connected.
    rig.post("/composition/disconnect-all")
    time.sleep(2.5)
    print("%s: composition revealed, nothing connected, recording" % tag, flush=True)
    hwnd = screen.avenue_hwnd()
    screen.pin(hwnd)
    clips = []
    for deck, col in shots:
        if not land(deck, col, (expected or {}).get((deck, col))):
            raise SystemExit("%s: deck %d column %d never landed on the expected cell" % (tag, deck, col))
        cd = rig.composition()
        label = "%s - %s" % (cd["decks"][deck - 1]["name"]["value"], cd["columns"][col - 1]["name"]["value"])
        screen.bring_to_front(hwnd)
        frames = []
        for _ in range(int(fps * seconds)):
            t = time.time()
            frames.append(screen.grab_monitor(hwnd, front=False).resize(size, Image.LANCZOS))
            time.sleep(max(0.0, 1.0 / fps - (time.time() - t)))
        clips.append((label, frames))
        print("%s  %s  %d frames" % (tag, label, len(frames)), flush=True)
    screen.pin(hwnd, False)
    return clips, verdict


def write_gif(still, kinetic, out, fps, size, name_before="before", name_after="after"):
    W, H = size
    f, fs = font(18), font(14)
    frames = []
    for (label, a), (_, b) in zip(still, kinetic):
        for fa, fb in zip(a, b):
            im = Image.new("RGB", (W * 2 + 12, H + 30), BG)
            d = ImageDraw.Draw(im)
            d.text((8, 5), label, font=f, fill=INK)
            d.text((W - 70, 8), name_before, font=fs, fill=DIM)
            d.text((W * 2 - 55, 8), name_after, font=fs, fill=GOOD)
            im.paste(fa, (0, 30))
            im.paste(fb, (W + 12, 30))
            frames.append(im)
    step = max(1, len(frames) // 6)
    strip = Image.new("RGB", (W * 2 + 12, (H + 30) * 6))
    for i, fr in enumerate(frames[::step][:6]):
        strip.paste(fr, (0, i * (H + 30)))
    master = strip.quantize(colors=96, dither=Image.Dither.NONE)
    q = [fr.quantize(palette=master, dither=Image.Dither.NONE) for fr in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0)
    return len(frames)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--still", required=True, help="the published build (before)")
    ap.add_argument("--kinetic", required=True, help="the new build (after)")
    ap.add_argument("--shots", required=True, help="deck:column pairs, 1-based, e.g. 1:2,2:7,4:5,5:6")
    ap.add_argument("--out", required=True, help="the .gif to write")
    ap.add_argument("--bible", help="bible.json of the new build: enables the read-back")
    ap.add_argument("--decks", help="decks.json of the new build")
    ap.add_argument("--layer-blends", default="7:Add")
    ap.add_argument("--verify-out", help="where to write the read-back text (default: next to --out)")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--width", type=int, default=420)
    a = ap.parse_args()
    size = (a.width, a.width * 9 // 16)
    shots = parse_shots(a.shots)
    verify = None
    if a.bible and a.decks:
        verify = {"bible": a.bible, "decks": a.decks, "blends": a.layer_blends,
                  "out": a.verify_out or os.path.splitext(a.out)[0] + "_readback.txt"}
    expected = expected_captions(a.decks)
    still, _ = record(a.still, "still", shots, a.fps, a.seconds, size, expected=expected)
    kinetic, verdict = record(a.kinetic, "kinetic", shots, a.fps, a.seconds, size, verify, expected=expected)
    n = write_gif(still, kinetic, a.out, a.fps, size)
    print("wrote %s  %d frames  %.1f MB%s" % (a.out, n, os.path.getsize(a.out) / 1048576.0,
                                              "  | read-back: " + verdict if verdict else ""), flush=True)


if __name__ == "__main__":
    main()
