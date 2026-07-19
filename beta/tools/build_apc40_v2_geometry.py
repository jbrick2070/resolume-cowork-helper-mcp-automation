#!/usr/bin/env python3
"""Build deterministic, collision-checked APC40 V2 chassis geometry.

The protected envelopes come from the accepted historical R1 geometry blob.
Only label, witness, and motion boxes are protected.  V2 decoration is
represented twice:

* exact vector primitives for audit and collision QA;
* a native Text Block character grid for the live Resolume layer.

The character grid is clipped cell-by-cell against every protected envelope,
so its maximum possible cell ink bounds remain collision-free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SOURCE_COMMIT = "7711f49"
SOURCE_BLOB = "docs/APC40_visual_qa_geometry.json"
R1_COMPOSITION = Path("compositions/APC40_Visual_QA_148.avc")
R1_SHA256 = "91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99"
RUN_ID = "20260719T124750Z"
DEFAULT_OUTPUT = Path(f"beta/APC40_V2_GEOMETRY_{RUN_ID}.json")

CANVAS = (1920, 1080)
SAFE_BOX = (112.0, 66.0, 1808.0, 1022.0)
PADDING = 4.0
STROKE = 2.0
GRID_COLUMNS = 128
GRID_ROWS = 48


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_source_geometry(repo_root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_BLOB}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(proc.stdout)


def expand_box(box: Iterable[float], padding: float = PADDING) -> list[float]:
    x1, y1, x2, y2 = (float(value) for value in box)
    return [x1 - padding, y1 - padding, x2 + padding, y2 + padding]


def boxes_overlap(a: Iterable[float], b: Iterable[float]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)


def point_to_box_min_distance(cx: float, cy: float, box: Iterable[float]) -> float:
    x1, y1, x2, y2 = box
    dx = max(x1 - cx, 0.0, cx - x2)
    dy = max(y1 - cy, 0.0, cy - y2)
    return math.hypot(dx, dy)


def point_to_box_max_distance(cx: float, cy: float, box: Iterable[float]) -> float:
    x1, y1, x2, y2 = box
    return max(
        math.hypot(x - cx, y - cy)
        for x in (x1, x2)
        for y in (y1, y2)
    )


def line(
    primitive_id: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    family: str,
) -> dict[str, Any]:
    if x1 != x2 and y1 != y2:
        raise ValueError(f"{primitive_id}: only axis-aligned lines are supported")
    return {
        "id": primitive_id,
        "kind": "line",
        "family": family,
        "x1": float(x1),
        "y1": float(y1),
        "x2": float(x2),
        "y2": float(y2),
        "stroke_px": STROKE,
    }


def circle(
    primitive_id: str,
    cx: float,
    cy: float,
    radius: float,
    family: str,
) -> dict[str, Any]:
    return {
        "id": primitive_id,
        "kind": "circle",
        "family": family,
        "cx": float(cx),
        "cy": float(cy),
        "radius": float(radius),
        "stroke_px": STROKE,
    }


def build_primitives() -> list[dict[str, Any]]:
    primitives: list[dict[str, Any]] = [
        line("shell-top", 112, 66, 1808, 66, "shell"),
        line("shell-right", 1808, 66, 1808, 1022, "shell"),
        line("shell-bottom", 112, 1022, 1808, 1022, "shell"),
        line("shell-left", 112, 66, 112, 1022, "shell"),
        line("main-divider", 1272, 174, 1272, 1010, "section-divider"),
        line("grid-row-1", 122, 261, 1260, 261, "grid-divider"),
        line("grid-row-2", 122, 321, 1260, 321, "grid-divider"),
        line("grid-row-3", 122, 381, 1260, 381, "grid-divider"),
        line("grid-row-4", 122, 442, 1260, 442, "grid-divider"),
        line("clip-stop-divider", 122, 506, 1260, 506, "section-divider"),
        line("track-select-divider", 122, 576, 1260, 576, "section-divider"),
        line("track-mode-divider", 122, 640, 1260, 640, "section-divider"),
        line("fader-divider", 122, 760, 1158, 760, "section-divider"),
        line("right-top-divider", 1284, 392, 1796, 392, "section-divider"),
        line("right-knob-divider", 1284, 544, 1796, 544, "section-divider"),
        line("right-button-divider", 1284, 662, 1796, 662, "section-divider"),
        line("right-controls-divider", 1284, 729, 1796, 729, "section-divider"),
        line("right-navigation-divider", 1284, 800, 1796, 800, "section-divider"),
        line("right-mix-divider", 1284, 910, 1796, 910, "section-divider"),
        line("right-upper-row-1", 1284, 255, 1660, 255, "section-divider"),
        line("right-upper-row-2", 1284, 321, 1660, 321, "section-divider"),
        line("right-upper-column-1", 1397, 174, 1397, 380, "section-divider"),
        line("right-upper-column-2", 1534, 174, 1534, 380, "section-divider"),
        line("right-upper-column-3", 1660, 174, 1660, 380, "section-divider"),
        line("crossfader-guide", 1479, 930, 1715, 930, "crossfader-guide"),
        line("crossfader-cap-left", 1479, 920, 1479, 936, "crossfader-guide"),
        line("crossfader-cap-right", 1715, 920, 1715, 936, "crossfader-guide"),
        line("master-guide", 1278, 787, 1278, 1009, "master-guide"),
    ]

    # Eight channel-strip guides occupy the safe gaps immediately right of
    # the protected fader motion envelopes.
    for index, x in enumerate((256, 386, 516, 646, 775, 905, 1035, 1157), 1):
        primitives.append(
            line(f"track-fader-{index}", x, 787, x, 1009, "track-fader-guide")
        )

    # Conservative radii sit outside the protected center witness and stop
    # before the protected label below each rotary.
    track_centers = [(191, 130), (321, 130), (451, 130), (581, 130)]
    track_centers += [(711, 130), (840, 130), (970, 130), (1100, 130)]
    device_centers = [(1337, 452), (1467, 452), (1597, 452), (1727, 452)]
    device_centers += [(1337, 573), (1467, 573), (1597, 573), (1727, 573)]
    for index, (cx, cy) in enumerate(track_centers, 1):
        primitives.append(circle(f"track-knob-{index}", cx, cy, 32, "knob-surround"))
    for index, (cx, cy) in enumerate(device_centers, 1):
        primitives.append(circle(f"device-knob-{index}", cx, cy, 32, "knob-surround"))
    primitives.append(circle("cue-level", 1214, 696, 24, "knob-surround"))
    primitives.append(circle("tempo", 1727, 303, 24, "knob-surround"))
    return primitives


def protected_records(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    controls: list[dict[str, Any]] = []
    boxes: list[dict[str, Any]] = []
    for raw_key, control in sorted(
        source["controls"].items(), key=lambda item: int(item[1]["layer"])
    ):
        record = {
            "layer": int(control["layer"]),
            "raw_key": str(control["raw_key"]),
            "layer_name": str(control["layer_name"]),
            "prototype": str(control["prototype"]),
            "label_box": control.get("label_box"),
            "witness_box": control.get("witness_box"),
            "motion_box": control.get("motion_box"),
        }
        controls.append(record)
        seen: set[tuple[float, ...]] = set()
        for role in ("label_box", "witness_box", "motion_box"):
            value = control.get(role)
            if not value:
                continue
            expanded = expand_box(value)
            key = tuple(expanded)
            if key in seen:
                continue
            seen.add(key)
            boxes.append(
                {
                    "layer": int(control["layer"]),
                    "raw_key": str(control["raw_key"]),
                    "role": role,
                    "box": [float(number) for number in value],
                    "padded_box": expanded,
                }
            )
    return controls, boxes


def primitive_collisions(
    primitive: dict[str, Any], protected: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    half = float(primitive["stroke_px"]) / 2.0
    for record in protected:
        box = record["padded_box"]
        hit = False
        if primitive["kind"] == "line":
            ink_box = [
                min(primitive["x1"], primitive["x2"]) - half,
                min(primitive["y1"], primitive["y2"]) - half,
                max(primitive["x1"], primitive["x2"]) + half,
                max(primitive["y1"], primitive["y2"]) + half,
            ]
            hit = boxes_overlap(ink_box, box)
        elif primitive["kind"] == "circle":
            minimum = point_to_box_min_distance(primitive["cx"], primitive["cy"], box)
            maximum = point_to_box_max_distance(primitive["cx"], primitive["cy"], box)
            hit = (
                primitive["radius"] + half >= minimum
                and primitive["radius"] - half <= maximum
            )
        if hit:
            result.append(
                {
                    "primitive_id": primitive["id"],
                    "layer": record["layer"],
                    "raw_key": record["raw_key"],
                    "role": record["role"],
                }
            )
    return result


def coordinate_to_cell(
    x: float, y: float, columns: int = GRID_COLUMNS, rows: int = GRID_ROWS
) -> tuple[int, int]:
    x1, y1, x2, y2 = SAFE_BOX
    column = round((x - x1) * (columns - 1) / (x2 - x1))
    row = round((y - y1) * (rows - 1) / (y2 - y1))
    return (
        max(0, min(columns - 1, column)),
        max(0, min(rows - 1, row)),
    )


def cell_box(column: int, row: int) -> list[float]:
    x1, y1, x2, y2 = SAFE_BOX
    step_x = (x2 - x1) / (GRID_COLUMNS - 1)
    step_y = (y2 - y1) / (GRID_ROWS - 1)
    cx = x1 + column * step_x
    cy = y1 + row * step_y
    return [cx - step_x / 2, cy - step_y / 2, cx + step_x / 2, cy + step_y / 2]


def cells_for_primitive(primitive: dict[str, Any]) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    if primitive["kind"] == "line":
        c1, r1 = coordinate_to_cell(primitive["x1"], primitive["y1"])
        c2, r2 = coordinate_to_cell(primitive["x2"], primitive["y2"])
        if c1 == c2:
            for row in range(min(r1, r2), max(r1, r2) + 1):
                cells.add((c1, row))
        else:
            for column in range(min(c1, c2), max(c1, c2) + 1):
                cells.add((column, r1))
    else:
        circumference = 2.0 * math.pi * primitive["radius"]
        samples = max(24, int(circumference / 4.0))
        for index in range(samples):
            angle = 2.0 * math.pi * index / samples
            x = primitive["cx"] + math.cos(angle) * primitive["radius"]
            y = primitive["cy"] + math.sin(angle) * primitive["radius"]
            cells.add(coordinate_to_cell(x, y))
    return cells


def grid_text(
    primitives: list[dict[str, Any]], protected: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]], int]:
    desired: set[tuple[int, int]] = set()
    for primitive in primitives:
        desired.update(cells_for_primitive(primitive))

    occupied: set[tuple[int, int]] = set()
    clipped: list[dict[str, Any]] = []
    for column, row in sorted(desired, key=lambda item: (item[1], item[0])):
        box = cell_box(column, row)
        hits = [
            record
            for record in protected
            if boxes_overlap(box, record["padded_box"])
        ]
        if hits:
            clipped.append(
                {
                    "column": column,
                    "row": row,
                    "cell_box": [round(value, 3) for value in box],
                    "protected_layers": sorted({record["layer"] for record in hits}),
                }
            )
        else:
            occupied.add((column, row))

    # ASCII keeps the live source immune to Windows code-page differences.
    # Corners/intersections use '+', straight runs use '-'/'|', and isolated
    # samples from a clipped rotary surround use a quiet dot.
    glyphs = {
        0: ".",
        1: "-",
        2: "|",
        3: "+",
        4: "-",
        5: "-",
        6: "+",
        7: "+",
        8: "|",
        9: "+",
        10: "|",
        11: "+",
        12: "+",
        13: "+",
        14: "+",
        15: "+",
    }
    lines: list[str] = []
    for row in range(GRID_ROWS):
        chars: list[str] = []
        for column in range(GRID_COLUMNS):
            if (column, row) not in occupied:
                chars.append(" ")
                continue
            mask = 0
            if (column - 1, row) in occupied:
                mask |= 1
            if (column, row - 1) in occupied:
                mask |= 2
            if (column + 1, row) in occupied:
                mask |= 4
            if (column, row + 1) in occupied:
                mask |= 8
            chars.append(glyphs[mask])
        lines.append("".join(chars).rstrip())
    text = "\n".join(lines).rstrip() + "\n"

    # Recheck the surviving character cells as maximum ink rectangles.
    cell_collisions = 0
    for column, row in occupied:
        box = cell_box(column, row)
        cell_collisions += sum(
            1 for record in protected if boxes_overlap(box, record["padded_box"])
        )
    if cell_collisions:
        raise AssertionError(f"character cell collision count is {cell_collisions}")
    return text, clipped, len(occupied)


def build(repo_root: Path) -> dict[str, Any]:
    baseline_path = repo_root / R1_COMPOSITION
    baseline_sha = sha256_file(baseline_path)
    if baseline_sha != R1_SHA256:
        raise AssertionError(
            f"R1 hash mismatch: expected {R1_SHA256}, found {baseline_sha}"
        )

    source = load_source_geometry(repo_root)
    controls, protected = protected_records(source)
    if len(controls) != 148:
        raise AssertionError(f"expected 148 controls, found {len(controls)}")
    if [record["layer"] for record in controls] != list(range(1, 149)):
        raise AssertionError("protected layers are not exactly 1..148")

    primitives = build_primitives()
    collisions = [
        collision
        for primitive in primitives
        for collision in primitive_collisions(primitive, protected)
    ]
    if collisions:
        preview = json.dumps(collisions[:8], indent=2)
        raise AssertionError(f"vector collisions found:\n{preview}")

    text, clipped_cells, occupied_cells = grid_text(primitives, protected)
    text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    source_blob_sha = hashlib.sha256(
        json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "canvas": {"width": CANVAS[0], "height": CANVAS[1], "origin": "top-left"},
        "source": {
            "commit": SOURCE_COMMIT,
            "blob": SOURCE_BLOB,
            "canonical_json_sha256": source_blob_sha,
            "r1_composition": R1_COMPOSITION.as_posix(),
            "r1_sha256": baseline_sha,
        },
        "protection": {
            "padding_px": PADDING,
            "control_count": len(controls),
            "box_count": len(protected),
            "collision_count": 0,
            "controls": controls,
        },
        "decoration": {
            "primitive_count": len(primitives),
            "collision_count": 0,
            "primitives": primitives,
        },
        "native_text_block": {
            "font": "Cascadia Mono",
            "style": "Regular",
            "color_rgba": "#557f96ff",
            "size": 0.5,
            "line_width": 5000.0,
            "transform": {
                "position_x": -21.0,
                "position_y": 0.0,
                "scale": 50.0,
                "scale_w": 184.0,
                "scale_h": 181.0,
            },
            "grid_columns": GRID_COLUMNS,
            "grid_rows": GRID_ROWS,
            "intended_bounds": list(SAFE_BOX),
            "occupied_cells": occupied_cells,
            "clipped_cell_count": len(clipped_cells),
            "cell_collision_count": 0,
            "text_sha256": text_sha,
            "text": text,
        },
        "fft_contract": {
            "target": "clip video opacity",
            "phase_source": "composition_fft",
            "frequency_band": [0.0, 0.33],
            "output_range": [0.12, 0.28],
            "gain_db": 3.0,
            "fallback_ms": 1400,
            "geometry_modulated": False,
            "hue_modulated": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--print-text", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    document = build(repo_root)
    serialized = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    output = repo_root / args.output
    if args.check:
        if not output.is_file():
            raise SystemExit(f"missing geometry artifact: {output}")
        existing = output.read_text(encoding="utf-8")
        if existing != serialized:
            raise SystemExit(f"geometry artifact is stale: {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized, encoding="utf-8", newline="\n")
    if args.print_text:
        sys.stdout.write(document["native_text_block"]["text"])
    else:
        print(
            json.dumps(
                {
                    "output": str(output),
                    "controls": document["protection"]["control_count"],
                    "primitives": document["decoration"]["primitive_count"],
                    "collisions": document["decoration"]["collision_count"],
                    "occupied_cells": document["native_text_block"]["occupied_cells"],
                    "text_sha256": document["native_text_block"]["text_sha256"],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
