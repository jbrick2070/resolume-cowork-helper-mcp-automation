#!/usr/bin/env python3
"""Premultiplied re-render of the V3 chassis frame (append-only, new file).

The original APC40_MKII_Animated_Twin_V3_Chassis_Alpha.mov is straight-alpha;
Avenue's Add pipeline consumes raw RGB (premult convention), so its designed
59-86% breathing displayed at constant 100% - drowning the restrained tiles.
This renders the SAME chassis geometry/breath (imported from
render_apc40_animated_v3.py) premultiplied, honoring the authored levels.

Usage:
  python render_chassis_premult.py --frames A B    # render frame chunk
  python render_chassis_premult.py --encode        # encode the mov
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from render_apc40_animated_v3 import render_chassis, FRAMES, FPS  # noqa: E402

OUT_MOV = ROOT / "media" / "APC40_MKII_V3_Chassis_Premult_Alpha.mov"
SCRATCH = Path("/tmp/chassis_premult")


def premultiply(img):
    # premultiplied rgb, TRUE alpha kept - see render_apc40_spec_v3.premultiply
    # (opaque flatten made this full-frame layer occlude the whole wall)
    a = np.array(img, np.uint16)
    for c in range(3):
        a[..., c] = a[..., c] * a[..., 3] // 255
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", nargs=2, type=int)
    ap.add_argument("--encode", action="store_true")
    args = ap.parse_args()
    if args.frames:
        a, b = args.frames
        SCRATCH.mkdir(parents=True, exist_ok=True)
        for f in range(a, b):
            premultiply(render_chassis(f)).save(
                SCRATCH / f"f-{f:04d}.png", compress_level=1)
        print(f"frames [{a},{b}) rendered")
    if args.encode:
        n = len(list(SCRATCH.glob("f-*.png")))
        assert n == FRAMES, f"have {n}/{FRAMES} frames"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
             "-i", str(SCRATCH / "f-%04d.png"), "-c:v", "prores_ks",
             "-profile:v", "4", "-pix_fmt", "yuva444p10le", str(OUT_MOV)],
            check=True)
        print("chassis ->", OUT_MOV)


if __name__ == "__main__":
    main()
