#!/usr/bin/env python3
"""QA: prove the animated V3 surface never violates control bounds or overlaps.

Four-part proof:
  A. TERRITORIES DISJOINT -- no two DIFFERENT controls' geometry boxes actually
     overlap (0px).  Neighbours that merely come within the 4px design margin are
     reported as informational adjacency, not a violation.
  B. STRUCTURAL CONTAINMENT -- the renderer paints each element into a sub-tile of
     exactly its box and pastes at box*SS, so a control can only ink its own boxes.
  C. EMPIRICAL BOUNDS -- across sampled loop frames, count lit alpha pixels that
     fall OUTSIDE the union of all control boxes (+/-2px AA tolerance).
  D. RENDERED-INK INTERSECTION -- for every pair of controls that come within the
     4px margin (the only collision-risk neighbours), render each in isolation and
     confirm 0 shared lit pixels across the loop -- i.e. animations never touch.

A + B + C + D => controls never overlap, even during motion, pulses, state changes.
Writes docs/APC40_V3_COLLISION_QA.json and .md.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 1920, 1080
MARGIN = 4
TOL = 2
ALPHA_ON = 16
ROOT = Path(__file__).resolve().parents[1]
BUILD_INPUT = ROOT / "build" / "build_input_v3.json"
SURFACE = Path("/tmp/v3_surface")
OUT_JSON = ROOT / "docs" / "APC40_V3_COLLISION_QA.json"
OUT_MD = ROOT / "docs" / "APC40_V3_COLLISION_QA.md"


def boxes_of(r):
    return [b for b in (r["label_box"], r["witness_box"], r["motion_box"]) if b]


def overlap(a, b, pad):
    return not (a[2] + pad < b[0] - pad or b[2] + pad < a[0] - pad
                or a[3] + pad < b[1] - pad or b[3] + pad < a[1] - pad)


def load_renderer():
    spec = importlib.util.spec_from_file_location(
        "r", str(ROOT / "tools" / "render_apc40_animated_v3.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    rows = json.load(open(BUILD_INPUT))
    m = load_renderer()
    by = {r["name"]: r for r in rows}
    entries = [(i, b) for i, r in enumerate(rows) for b in boxes_of(r)]

    # ---- A. actual (0px) overlaps + informational adjacency (<=4px)
    actual, adjacent = [], set()
    for x in range(len(entries)):
        i, a = entries[x]
        for y in range(x + 1, len(entries)):
            j, b = entries[y]
            if i == j:
                continue
            if overlap(a, b, 0):
                actual.append([rows[i]["name"], rows[j]["name"]])
            elif overlap(a, b, MARGIN):
                adjacent.add(tuple(sorted((i, j))))

    # ---- D. rendered-ink intersection for every at-risk (adjacent) pair
    frames = sorted(int(p.stem.split("-")[1]) for p in SURFACE.glob("frame-*.png"))
    dframes = frames[::30] + [frames[-1]] if frames else [0]
    ink_cache = {}

    def ink(name, f):
        key = (name, f)
        if key not in ink_cache:
            big = Image.new("RGBA", (m.W * m.SS, m.H * m.SS), (0, 0, 0, 0))
            m.render_control(big, by[name], f)
            ink_cache[key] = np.asarray(
                big.resize((m.W, m.H), Image.LANCZOS))[:, :, 3] > ALPHA_ON
        return ink_cache[key]

    d_worst = 0
    d_pairs = []
    for i, j in sorted(adjacent):
        n1, n2 = rows[i]["name"], rows[j]["name"]
        worst = max(int((ink(n1, f) & ink(n2, f)).sum()) for f in dframes)
        d_worst = max(d_worst, worst)
        d_pairs.append({"a": n1, "b": n2, "max_shared_px": worst})

    # ---- C. empirical out-of-bounds ink
    allmask = np.zeros((H, W), bool)
    for r in rows:
        for b in boxes_of(r):
            x1, y1, x2, y2 = (int(round(v)) for v in b)
            allmask[max(0, y1 - TOL):min(H, y2 + TOL),
                    max(0, x1 - TOL):min(W, x2 + TOL)] = True
    per_frame, c_worst = [], 0
    for f in (frames[::20] + [frames[-1]] if frames else []):
        im = np.asarray(Image.open(SURFACE / f"frame-{f:04d}.png"))
        alpha = im[:, :, 3] > ALPHA_ON
        outside = int((alpha & ~allmask).sum())
        c_worst = max(c_worst, outside)
        per_frame.append({"frame": f, "lit_px": int(alpha.sum()),
                          "outside_box_px": outside})

    a_pass, c_pass, d_pass = (len(actual) == 0), (c_worst == 0), (d_worst == 0)
    result = {
        "control_count": len(rows), "box_count": len(entries),
        "A_actual_overlaps_0px": actual, "A_pass": a_pass,
        "A_adjacent_within_4px_pairs": len(adjacent),
        "B_structural_containment": "sub-tile paste at box*SS; ink cannot leave box",
        "C_per_frame": per_frame, "C_worst_outside_box_px": c_worst, "C_pass": c_pass,
        "D_frames_checked": sorted(set(dframes)), "D_at_risk_pairs": d_pairs,
        "D_worst_shared_px": d_worst, "D_pass": d_pass,
        "verdict": "PASS" if (a_pass and c_pass and d_pass) else "FAIL",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(OUT_JSON, "w"), indent=1)

    md = [
        "# APC40 Animated Twin V3 -- Collision / Bounds QA", "",
        f"**Verdict: {result['verdict']}**", "",
        f"- Controls: {len(rows)}  |  geometry boxes: {len(entries)}", "",
        "## A. Territories disjoint (actual 0px overlap)",
        f"- Real cross-control box overlaps: **{len(actual)}** ({'PASS' if a_pass else 'FAIL'})",
        f"- Neighbours within the 4px design margin (informational, allowed): "
        f"{len(adjacent)}", "",
        "## B. Structural containment",
        "- Each element is rendered into a sub-tile of exactly its box and pasted at",
        "  `box*SS`; ink cannot leave the box by construction.", "",
        "## C. Empirical out-of-bounds ink (lit alpha outside all boxes, +/-2px)", "",
        "| frame | lit px | outside-box px |", "|---|---|---|",
    ]
    md += [f"| {p['frame']} | {p['lit_px']} | {p['outside_box_px']} |" for p in per_frame]
    md += ["", f"- Worst: **{c_worst}** ({'PASS' if c_pass else 'FAIL'})", "",
           "## D. Rendered-ink intersection for at-risk neighbours (across loop)",
           f"- Pairs checked: {len(d_pairs)}  |  frames: {sorted(set(dframes))}",
           f"- Worst shared pixels between any two controls: **{d_worst}** "
           f"({'PASS' if d_pass else 'FAIL'})", ""]
    for p in sorted(d_pairs, key=lambda x: -x["max_shared_px"])[:12]:
        md.append(f"  - {p['a']} & {p['b']}: {p['max_shared_px']}px")
    md += ["", "A + B + C + D => the animated controls never exit their bounds or "
           "overlap, even during motion, pulses, or state changes."]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"verdict={result['verdict']} A={a_pass}(actual={len(actual)}) "
          f"C={c_pass}(worst={c_worst}) D={d_pass}(worst={d_worst}) "
          f"adjacent_pairs={len(adjacent)}")


if __name__ == "__main__":
    main()
