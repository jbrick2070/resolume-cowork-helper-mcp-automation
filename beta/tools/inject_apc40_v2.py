#!/usr/bin/env python3
"""Inject APC40 V2 chassis geometry into a candidate composition (offline).

Reads the native Text Block raster produced by ``build_apc40_v2_geometry.py``
and surgically replaces ONLY the chassis Text Block ``value="..."`` inside a
source ``.avc``, writing a new candidate.  Every other byte -- including the
protected R1 layers 1..148 and the V2 crossfader Solid Color -- is preserved
exactly.  No Resolume runtime is required, so the build is deterministic and
cannot disturb a live session.

Usage:
    python beta/tools/inject_apc40_v2.py \
        --source  beta/compositions/<verified candidate>.avc \
        --geometry beta/APC40_V2_GEOMETRY_<run>.json \
        --output  beta/compositions/<compare candidate>.avc
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

BRAILLE = re.compile("[⠀-⣿]")
OPEN_MARKER = 'value="'


def find_braille_value_span(text: str) -> tuple[int, int]:
    """Return the (start, end) character span of the chassis Text Block value.

    The chassis is the only Text Block whose value contains Unicode Braille.
    Braille glyphs and newlines contain no double-quote, so the closing quote
    is unambiguous.
    """
    match = BRAILLE.search(text)
    if not match:
        raise SystemExit("no braille chassis text found in source composition")
    braille_at = match.start()
    open_at = text.rfind(OPEN_MARKER, 0, braille_at)
    if open_at < 0:
        raise SystemExit('could not locate opening value=" for chassis text')
    start = open_at + len(OPEN_MARKER)
    end = text.index('"', braille_at)
    span = text[start:end]
    for char in span:
        if char not in ("\n", "\r") and not (0x2800 <= ord(char) <= 0x28FF):
            raise SystemExit(
                "chassis text span contains an unexpected character; refusing"
            )
    return start, end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--geometry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--name",
        default=None,
        help="Internal composition name (Avenue title). Defaults to output stem.",
    )
    args = parser.parse_args()

    geometry = json.loads(args.geometry.read_text(encoding="utf-8"))
    block = geometry["native_text_block"]
    new_text = block["text"]
    rows = new_text.split("\n")
    if len(rows) != block["grid_rows"] or any(
        len(row) != block["grid_columns"] for row in rows
    ):
        raise SystemExit("geometry text grid shape mismatch")
    if hashlib.sha256(new_text.encode("utf-8")).hexdigest() != block["text_sha256"]:
        raise SystemExit("geometry text_sha256 does not match its own text")

    raw = args.source.read_bytes()
    text = raw.decode("utf-8")

    # Rename the composition so the Avenue title bar matches the file name.
    # The identity lives in <CompositionInfo name="..."> and the composition
    # level <Param name="Name" ... value="...">. Copying the source verbatim
    # leaves both reading the old candidate name, which makes it impossible to
    # tell which composition is loaded from the title alone.
    name_match = re.search(r'<CompositionInfo name="([^"]*)"', text)
    if not name_match:
        raise SystemExit("could not locate CompositionInfo name for rename")
    old_name = name_match.group(1)
    new_name = args.name or args.output.stem
    name_occurrences = text.count(old_name)
    if name_occurrences == 0:
        raise SystemExit("composition name string not found for rename")
    text = text.replace(old_name, new_name)

    start, end = find_braille_value_span(text)
    old_span = text[start:end]

    # Preserve the source composition's newline convention inside the value
    # (Resolume saves CRLF). The geometry text is LF-joined; re-join to match so
    # only braille glyphs differ and the raster byte length is unchanged.
    newline = "\r\n" if "\r\n" in old_span else "\n"
    new_span = newline.join(new_text.split("\n"))
    if new_span.count("\n") != old_span.count("\n"):
        raise SystemExit("raster row count changed; refusing")
    out_text = text[:start] + new_span + text[end:]
    out_bytes = out_text.encode("utf-8")

    # The only edits are the composition name and the raster span; confirm the
    # renamed name is present and the old one is fully gone.
    if old_name in out_text or new_name not in out_text:
        raise SystemExit("composition rename verification failed")

    args.output.write_bytes(out_bytes)

    print(
        json.dumps(
            {
                "source": str(args.source),
                "output": str(args.output),
                "old_composition_name": old_name,
                "new_composition_name": new_name,
                "name_occurrences_replaced": name_occurrences,
                "old_raster_sha256": hashlib.sha256(
                    old_span.encode("utf-8")
                ).hexdigest(),
                "new_raster_sha256": hashlib.sha256(
                    new_span.encode("utf-8")
                ).hexdigest(),
                "geometry_text_sha256": block["text_sha256"],
                "bytes_before": len(raw),
                "bytes_after": len(out_bytes),
                "output_sha256": hashlib.sha256(out_bytes).hexdigest(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
