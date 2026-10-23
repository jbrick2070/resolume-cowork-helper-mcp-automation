#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gallery.py - photograph every composition in the kit on the running Avenue and lay each one
out as a card: a large output frame, the part of Avenue's clip grid it uses, and a strip of
its most interesting frames. Writes <kit>/gallery/<slug>/{card,hero}.jpg and manifest.json.

    python -m resolume_build.gallery                     # every composition in COMPS
    python -m resolume_build.gallery --only the-manual,dead-air
    python -m resolume_build.gallery --readme-only       # rebuild gallery/README.md from the manifest

Opening a composition REPLACES whatever is open in Avenue; run it only when the user has
handed the rig over. Nothing is ever saved to Avenue. To show each composition fully, the
LIVE state is changed after it opens (not saved): solo and bypass are cleared, and layers
are taken off the crossfader so both sides show at once. Dashboard knobs stay as saved.
The frames are real output from Avenue's Composition Monitor; the card shows the most
interesting of the frames sampled (near-black and duplicate frames are dropped).
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resolume_build import rig, screen               # noqa: E402

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat   # noqa: E402

KIT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "react-kit")

# (slug, title, .avc relative to the kit, folder to link, one line)
COMPS = [
    ("visual-qa-148", "APC40 Visual QA 148", "compositions/APC40_Visual_QA_148.avc", "compositions",
     "The stable release: every physical control of the APC40 mkII mirrored on screen by 148 native Text Animator witnesses."),
    ("electric-zentropa", "Electric Zentropa", "compositions/APC40MKII_Electric_Zentropa_Lost_Buttons.avc", "compositions",
     "The performance interface, built only from native Resolume sources (Lost Buttons edition; True Button Toggles shares the interface)."),
    ("res-react-live-gen", "Res React Live Gen", "beta/compositions/Res React Live Gen.avc", "beta/compositions",
     "An audio-reactive generative instrument: FFT-driven stock generators across six decks."),
    ("res-react-orbit-gen", "Res React Orbit Gen", "beta/compositions/Res React Orbit Gen.avc", "beta/compositions",
     "Orbit: five FFT-reactive decks specified cell by cell in the manifests."),
    ("lexicon", "Res React Lexicon", "beta/lexicon/compositions/Res React Lexicon.avc", "beta/lexicon",
     "The controller as a sentence machine: five pad rows are the five slots of a sentence, 512 grammatical sentences."),
    ("lexicon-ii", "Res React Lexicon II - Eighties-ism", "beta/lexicon-ii/compositions/Res React Lexicon II.avc", "beta/lexicon-ii",
     "The sequel: 200 pads of found broadcast-age text across five decks."),
    ("testcard", "Res React Test Card", "beta/testcard/compositions/Res React Test Card.avc", "beta/testcard",
     "Pure signal: every pad a typographic test pattern, all of them moving under live WaveWarp."),
    ("nisei", "Res React Nisei", "beta/nisei/compositions/Res React Nisei.avc", "beta/nisei",
     "Archival testimony, poetry, documents and places from the Japanese American experience, for Nisei Week."),
    ("earthsearch", "EarthSearch EP01 Live Mix", "beta/earthsearch/compositions/EarthSearch_EP01_Live_Mix.avc", "beta/earthsearch",
     "Not a clip launcher: two 27-minute masters that never stop, and a surface that shapes them."),
    ("dead-air", "Dead Air - Listening Posts", "beta/dead-air/Dead Air Listening Posts.avc", "beta/dead-air",
     "Five rooms where someone is listening to the dark, and the dark, occasionally, replies."),
    ("dew-line", "Dew Line - The Spinningwork", "beta/dew-line/Dew Line - The Spinningwork.avc", "beta/dew-line",
     "A spider builds an early-warning station out of silk and casts her shadow on every star the net catches."),
    ("library-hand", "The Library And The Hand - GUSTO", "beta/library-hand/The Library And The Hand - GUSTO.avc", "beta/library-hand",
     "GUSTO, a proposed robot that fetches, flips, mixes and scratches real vinyl; stylus-cyan is documented, cue-orange proposed."),
    ("studio-one", "Studio One - War Of The Worlds 1938", "beta/studio-one/Studio One - War Of The Worlds 1938.avc", "beta/studio-one",
     "For the broadcast's 88th anniversary: CBS Studio One, Grovers Mill, the Visitors, New York, the Morning After."),
    ("signal-lost", "Signal Lost - Transmission From Tomorrow", "beta/signal-lost/Signal Lost - Transmission From Tomorrow.avc", "beta/signal-lost",
     "The OldTimeRadio pipeline as a show, including a VJ journey through the workflow one node per scene."),
    ("the-manual", "The Manual - Avenue 7.28.1", "beta/the-manual/The Manual - Avenue 7.28.1.avc", "beta/the-manual",
     "A composition about Resolume itself: the vocabulary, the clip, parameter animation, the 62 blend modes, this rig."),
    ("the-surface", "The Surface - APC40 mkII + MIDI", "beta/the-surface/The Surface - APC40 mkII + MIDI.avc", "beta/the-surface",
     "The controller every pack here is played on, drawn as schematics, every number from Akai's protocol document."),
    ("the-mixers", "The Mixers - V-4, MXPro, MX-1 + JVC", "beta/the-mixers/The Mixers - V-4, MXPro, MX-1 + JVC.avc", "beta/the-mixers",
     "Three video mixers (Edirol V-4, Videonics MXPro, MX-1), a JVC S-VHS deck beside a pro edit controller, and the APC40 itself; LEFT and RIGHT walk the six decks."),
]

# The clip grid, as fractions of a maximised Avenue 7.28.1 window (default layout, this rig).
GRID = {"y0": 0.0189, "y1": 0.2943, "head": 0.1975, "col": 0.0410}
BG, INK, DIM, LINE = (16, 17, 21), (236, 236, 242), (140, 142, 152), (40, 42, 50)
MAX_DECKS, MAX_COLS, SETTLE = 6, 4, 2.2


def font(size, bold=False):
    names = ("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")
    for name in names + ("DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def avc_counts(path):
    with open(path, "rb") as f:
        head = f.read(4000).decode("utf-8", "replace")
    m = re.search(r'<Composition name="([^"]*)"[^>]*numDecks="(\d+)"[^>]*numLayers="(\d+)"[^>]*numColumns="(\d+)"', head)
    if not m:
        raise ValueError("no <Composition> header in %s" % path)
    return m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))


def signature(c):
    return (c["name"]["value"], len(c["decks"]), len(c["layers"]), len(c["columns"]),
            c["layers"][0]["name"]["value"] if c["layers"] else "")


def open_and_wait(path, timeout=240):
    name, nd, nl, nc = avc_counts(path)
    try:
        before = signature(rig.composition())
    except Exception:
        before = None
    try:
        rig.post("/composition/open", rig.file_url(path), timeout=timeout)
    except Exception as exc:
        print("  open call:", exc)
    # Avenue names an open composition after its file, not the header's name attribute
    stem = os.path.splitext(os.path.basename(path))[0]
    same_as_before = before is not None and before[0] in (name, stem) and before[1:4] == (nd, nl, nc)
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1.5)
        if not rig.alive():
            continue
        try:
            c = rig.composition()
        except Exception:
            continue
        sig = signature(c)
        counts_ok = (len(c["decks"]), len(c["layers"]), len(c["columns"])) == (nd, nl, nc)
        # the target may already have been open (reopened in place): accept it after a pause
        if counts_ok and (sig != before or (same_as_before and time.time() - t0 > 8)):
            time.sleep(4)
            return rig.composition()
    return None


def reveal(c):
    """Live-only changes so the whole composition shows: no solo, no bypass, no crossfader sides."""
    changed = 0
    for i, L in enumerate(c["layers"], start=1):
        body = {}
        if L.get("solo", {}).get("value"):
            body["solo"] = {"value": False}
        if L.get("bypassed", {}).get("value"):
            body["bypassed"] = {"value": False}
        if L.get("crossfadergroup", {}).get("value") in ("A", "B"):
            body["crossfadergroup"] = {"value": "None"}
        if body:
            rig.put("/composition/layers/%d" % i, body)
            changed += 1
    return changed


def spread(n, k):
    if n <= k:
        return list(range(1, n + 1))
    return sorted({1 + round(i * (n - 1) / float(k - 1)) for i in range(k)})


def score(im):
    small = im.resize((160, 90))
    g = ImageStat.Stat(small.convert("L"))
    s = ImageStat.Stat(small.convert("HSV"))
    mean, std, sat = g.mean[0], g.stddev[0], s.mean[1]
    if mean < 7 and std < 6:
        return -1.0                                   # near-black: not a sample
    return std + 0.35 * mean + 0.25 * sat


def too_similar(a, b):
    x, y = a.resize((64, 36)).convert("L"), b.resize((64, 36)).convert("L")
    return ImageStat.Stat(ImageChops.difference(x, y)).mean[0] < 7


def pick(frames, k=9):
    good = sorted([f for f in frames if f["score"] > 0], key=lambda f: -f["score"])
    chosen, decks = [], set()
    for f in good:                                    # first the best frame of each deck
        if f["deck"] not in decks and not any(too_similar(f["img"], c["img"]) for c in chosen):
            chosen.append(f)
            decks.add(f["deck"])
    for f in good:                                    # then fill by score
        if len(chosen) >= k:
            break
        if f not in chosen and not any(too_similar(f["img"], c["img"]) for c in chosen):
            chosen.append(f)
    return sorted(chosen[:k], key=lambda f: -f["score"])


def grid_crop(win, n_cols):
    w, h = win.size
    x1 = min(w, int((GRID["head"] + GRID["col"] * min(n_cols, 20) + 0.004) * w))
    return win.crop((0, int(GRID["y0"] * h), x1, int(GRID["y1"] * h)))


def fit(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def caption(d, xy, text, width, f):
    while text and d.textlength(text, font=f) > width:
        text = text[:-2]
    d.text(xy, text, font=f, fill=DIM)


def card(entry, hero, grid, rest, path):
    """Title; a big frame on the left; on the right the clip grid at full column width with up
    to four frames under it; then a full-width strip if three or more frames are left.
    The right column's WIDTH is solved so that it ends level with the big frame, and the card
    is as wide as its content, so there are no empty panels whatever the frame count."""
    M, G, cap = 24, 14, 20
    big_w, big_h = 960, 540
    side = rest[:4]
    if len(side) == 3:                                # keep the right column in whole rows
        side = side[:2]
    left = rest[len(side):]
    strip = left[:4] if len(left) >= 3 else []
    per_row = 1 if len(side) == 1 else 2
    rows = (len(side) + per_row - 1) // per_row
    k = grid.height / float(grid.width)
    target = big_h + cap

    def side_dims(rw):
        sw_ = rw if per_row == 1 else (rw - G) // 2
        return sw_, sw_ * 9 // 16

    def content(rw):
        return int(k * rw) + cap + rows * (G + side_dims(rw)[1] + cap)

    lo, hi = 280.0, 1100.0                            # content() grows with the width: bisect
    for _ in range(40):
        mid = (lo + hi) / 2.0
        if content(int(mid)) <= target:
            lo = mid
        else:
            hi = mid
    rw = int(lo)
    gh, gw = int(k * rw), rw
    small_w, small_h = side_dims(rw)
    rx = M + big_w + 20
    W = rx + rw + M
    n = max(1, len(strip))
    sw = (W - 2 * M - (n - 1) * G) // n                # the strip always spans the full width
    sh = sw * 9 // 16
    H = 96 + big_h + cap + (G + sh + cap if strip else 0) + M
    f_cap = font(13)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((M, 18), entry["title"], font=font(34, True), fill=INK)
    sub = "%d deck%s  ·  %d layers  ·  %d column%s  ·  %s" % (
        entry["decks"], "" if entry["decks"] == 1 else "s", entry["layers"], entry["columns"],
        "" if entry["columns"] == 1 else "s", entry["folder"] + "/")
    d.text((M, 62), sub, font=font(17), fill=DIM)
    y = 96
    im.paste(fit(hero["img"], big_w, big_h), (M, y))
    caption(d, (M, y + big_h + 2), "%s  ·  %s" % (hero["deck_name"], hero["col_name"]), big_w, f_cap)
    im.paste(fit(grid, gw, gh), (rx, y))
    d.rectangle((rx - 1, y - 1, rx + gw, y + gh), outline=LINE)
    caption(d, (rx, y + gh + 2), "the clip grid in Avenue", rw, f_cap)
    for i, f in enumerate(side):
        x = rx + (i % per_row) * (small_w + G)
        yy = y + gh + cap + G + (i // per_row) * (small_h + cap + G)
        im.paste(fit(f["img"], small_w, small_h), (x, yy))
        caption(d, (x, yy + small_h + 2), "%s  ·  %s" % (f["deck_name"], f["col_name"]), small_w, f_cap)
    if strip:
        y2 = y + big_h + cap + G
        for i, f in enumerate(strip):
            x = M + i * (sw + G)
            im.paste(fit(f["img"], sw, sh), (x, y2))
            caption(d, (x, y2 + sh + 2), "%s  ·  %s" % (f["deck_name"], f["col_name"]), sw, f_cap)
    im.save(path, quality=86, optimize=True, progressive=True)


def shoot(slug, title, rel, folder, blurb, out_root):
    # Open a temporary copy, never the kit file itself: Avenue may save the open composition
    # (with the live changes reveal() makes) when it quits, and that once overwrote a kit file.
    src = os.path.join(KIT, rel)
    tmp_dir = os.path.join(tempfile.gettempdir(), "resolume_gallery")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, os.path.basename(src))
    shutil.copy2(src, path)
    entry = {"slug": slug, "title": title, "avc": rel, "folder": folder, "blurb": blurb}
    if not rig.ensure_running():
        entry["error"] = "Avenue not reachable"
        return entry
    c = open_and_wait(path)
    if c is None:
        entry["error"] = "did not open within the timeout"
        return entry
    entry.update(decks=len(c["decks"]), layers=len(c["layers"]), columns=len(c["columns"]),
                 rest_name=c["name"]["value"], revealed_layers=reveal(c))
    time.sleep(1)
    frames = []
    for di in range(1, min(len(c["decks"]), MAX_DECKS) + 1):
        rig.post("/composition/decks/%d/select" % di)
        time.sleep(2.0)
        cd = rig.composition()
        dname = cd["decks"][di - 1]["name"]["value"]
        for ci in spread(len(cd["columns"]), MAX_COLS):
            try:
                rig.post("/composition/columns/%d/connect" % ci)
            except Exception as exc:                  # a deck can have fewer columns than the composition
                print("  deck %d column %d: %s" % (di, ci, exc))
                continue
            time.sleep(SETTLE)
            img = screen.grab_monitor()
            frames.append({"deck": di, "deck_name": dname, "col": ci,
                           "col_name": cd["columns"][ci - 1]["name"]["value"], "img": img, "score": score(img)})
    entry["sampled"] = len(frames)
    chosen = pick(frames)
    entry["rendered"] = bool(chosen)
    if not chosen:
        entry["error"] = "every sampled frame was black"
        return entry
    hero = chosen[0]
    # come back to the hero frame for the window grab, so the grid and the big frame agree
    rig.post("/composition/decks/%d/select" % hero["deck"])
    time.sleep(2.0)
    rig.post("/composition/columns/%d/connect" % hero["col"])
    time.sleep(SETTLE)
    win = screen.grab_window()
    fresh = win.crop(screen.monitor_box(win.size))
    if score(fresh) > 0:
        hero = dict(hero, img=fresh)
    grid = grid_crop(win, entry["columns"])
    out = os.path.join(out_root, slug)
    os.makedirs(out, exist_ok=True)
    card(entry, hero, grid, chosen[1:], os.path.join(out, "card.jpg"))
    fit(hero["img"], 640, 360).save(os.path.join(out, "hero.jpg"), quality=86, optimize=True, progressive=True)
    entry["frames"] = [{"deck": f["deck_name"], "column": f["col_name"]} for f in [hero] + chosen[1:]]
    return entry


def write_readme(manifest, out_root):
    lines = ["# Gallery", "",
             "Every composition in this kit, opened on Resolume Avenue 7.28.1 and photographed from its own Composition Monitor.",
             "Each card shows the most interesting of the frames sampled (up to %d decks x %d columns), the part of Avenue's"
             % (MAX_DECKS, MAX_COLS),
             "clip grid it uses, and where it lives. To show each composition whole, layers were taken off the crossfader and",
             "solo/bypass cleared for the photographs (live state only, nothing saved); dashboard knobs are as saved.",
             "Regenerate with `python -m resolume_build.gallery` from the build repo.", ""]
    for e in manifest:
        lines.append("## %s" % e["title"])
        lines.append("")
        lines.append("%s  [`%s/`](../%s)" % (e["blurb"], e["folder"], e["folder"].replace(" ", "%20")))
        lines.append("")
        if e.get("rendered"):
            lines.append("![%s](%s/card.jpg)" % (e["title"], e["slug"]))
        else:
            lines.append("*No frame captured: %s.*" % e.get("error", "unknown"))
        lines.append("")
    with open(os.path.join(out_root, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


START, END = "<!-- gallery:start -->", "<!-- gallery:end -->"


def anchor(title):
    return re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")


def main_readme_section(manifest):
    shot = [e for e in manifest if e.get("rendered")]
    lines = [START, "## The compositions", "",
             "%d compositions; %d of them photographed from Avenue's own output. Click a frame for its full card, or see"
             % (len(manifest), len(shot)),
             "the [whole gallery](gallery/README.md).", "",
             "| | |", "|---|---|"]
    for e in manifest:
        tag = "stable" if not e["folder"].startswith("beta") else "beta"
        link = "[`%s/`](%s)" % (e["folder"], e["folder"].replace(" ", "%20"))
        text = "**%s** · %s<br>%s<br>%s" % (e["title"], tag, e["blurb"], link)
        if e.get("rendered"):
            img = '<a href="gallery/README.md#%s"><img src="gallery/%s/hero.jpg" alt="%s" width="320"></a>' % (
                anchor(e["title"]), e["slug"], e["title"])
        else:
            img = "*no frame: %s*" % e.get("error", "not captured")
        lines.append("| %s | %s |" % (img, text))
    lines += ["", END]
    return "\n".join(lines)


def update_main_readme(manifest, readme):
    with open(readme, encoding="utf-8") as f:
        text = f.read()
    section = main_readme_section(manifest)
    if START in text and END in text:
        text = text[:text.index(START)] + section + text[text.index(END) + len(END):]
    else:                                             # first time: right before "## What this is"
        marker = "## What this is"
        i = text.index(marker)
        text = text[:i] + section + "\n\n" + text[i:]
    with open(readme, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="comma list of slugs")
    ap.add_argument("--out", default=os.path.join(KIT, "gallery"))
    ap.add_argument("--readme-only", action="store_true")
    ap.add_argument("--main-readme", action="store_true", help="also write the list into the kit's README.md")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    mpath = os.path.join(a.out, "manifest.json")
    old = {}
    if os.path.exists(mpath):
        old = {e["slug"]: e for e in json.load(open(mpath, encoding="utf-8"))}
    if not a.readme_only:
        want = set(a.only.split(",")) if a.only else None
        for slug, title, rel, folder, blurb in COMPS:
            if want and slug not in want:
                continue
            t0 = time.time()
            try:
                e = shoot(slug, title, rel, folder, blurb, a.out)
            except Exception as exc:
                e = {"slug": slug, "title": title, "avc": rel, "folder": folder, "blurb": blurb,
                     "error": "%s: %s" % (type(exc).__name__, exc)}
            print("%-20s %-6s %5.0fs  %s" % (slug, "ok" if e.get("rendered") else "FAIL", time.time() - t0,
                                             e.get("error", "%s sampled, %d used" % (e.get("sampled"), len(e.get("frames", []))))),
                  flush=True)
            old[slug] = e
            json.dump([old[s[0]] for s in COMPS if s[0] in old], open(mpath, "w", encoding="utf-8"), indent=2)
    manifest = [old[s[0]] for s in COMPS if s[0] in old]
    write_readme(manifest, a.out)
    print("wrote", os.path.join(a.out, "README.md"))
    if a.main_readme:
        update_main_readme(manifest, os.path.join(KIT, "README.md"))
        print("updated", os.path.join(KIT, "README.md"))


if __name__ == "__main__":
    main()
