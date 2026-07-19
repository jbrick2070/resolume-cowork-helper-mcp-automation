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
RUN_ID = "20260719T204648Z"
DEFAULT_OUTPUT = Path(f"beta/APC40_V2_GEOMETRY_{RUN_ID}.json")

CANVAS = (1920, 1080)
SAFE_BOX = (112.0, 66.0, 1808.0, 1022.0)
PADDING = 4.0
STROKE = 2.0
GRID_COLUMNS = 160
GRID_ROWS = 60
DOT_COLUMNS = GRID_COLUMNS * 2
DOT_ROWS = GRID_ROWS * 4
BASE_OVERLAY_TRANSFORM = {
    "position_x": 637.0,
    "position_y": 480.0,
    "scale": 100.0,
    "scale_w": 13.9,
    "scale_h": 0.5,
}

# Unicode Braille stores a 2x4 dot tile in one fixed-width character.
BRAILLE_BITS = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (0, 3): 0x40,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (1, 3): 0x80,
}


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
        timeout=30,
    )
    if len(proc.stdout.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError(
            f"source geometry blob exceeds 2 MiB: {SOURCE_COMMIT}:{SOURCE_BLOB}"
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
    *,
    clip_to_protection: bool = False,
) -> dict[str, Any]:
    return {
        "id": primitive_id,
        "kind": "line",
        "family": family,
        "x1": float(x1),
        "y1": float(y1),
        "x2": float(x2),
        "y2": float(y2),
        "stroke_px": STROKE,
        "clip_to_protection": clip_to_protection,
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
        "clip_to_protection": False,
    }


def ellipse(
    primitive_id: str,
    cx: float,
    cy: float,
    radius_x: float,
    radius_y: float,
    family: str,
    *,
    clip_to_protection: bool = True,
) -> dict[str, Any]:
    return {
        "id": primitive_id,
        "kind": "ellipse",
        "family": family,
        "cx": float(cx),
        "cy": float(cy),
        "radius_x": float(radius_x),
        "radius_y": float(radius_y),
        "stroke_px": STROKE,
        "clip_to_protection": clip_to_protection,
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
        line("crossfader-guide", 1463, 1019, 1730, 1019, "crossfader-guide"),
        line("crossfader-cap-left", 1463, 945, 1463, 1019, "crossfader-guide"),
        line("crossfader-cap-right", 1730, 945, 1730, 1019, "crossfader-guide"),
        line("master-guide", 1278, 787, 1278, 1009, "master-guide"),
        # User-marked hardware accents. These intent paths are deliberately
        # raster-clipped around every padded R1 witness cell below.
        line(
            "marked-pad-top",
            130,
            194,
            1166,
            194,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-pad-row-1-lower",
            122,
            227,
            1167,
            227,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-matrix-scene-separator",
            1167,
            194,
            1167,
            505,
            "marked-scene-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-scene-1-underline",
            1178,
            257,
            1257,
            257,
            "marked-scene-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-left-row-2-tick",
            124,
            290,
            231,
            290,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-scene-2-underline",
            1180,
            319,
            1274,
            319,
            "marked-scene-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-left-row-3-tick",
            124,
            348,
            231,
            348,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-scene-3-underline",
            1182,
            381,
            1275,
            381,
            "marked-scene-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-left-row-4-tick",
            122,
            409,
            240,
            409,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-scene-4-underline",
            1181,
            439,
            1283,
            439,
            "marked-scene-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-left-row-5-tick",
            120,
            473,
            222,
            473,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-scene-5-underline",
            1180,
            497,
            1281,
            497,
            "marked-scene-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-left-grid-bottom",
            122,
            503,
            225,
            503,
            "marked-pad-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-track-mode-tick",
            124,
            643,
            245,
            643,
            "marked-track-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-fader-section-tick",
            130,
            700,
            247,
            700,
            "marked-track-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-track-mode-vertical",
            193,
            652,
            193,
            746,
            "marked-track-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-navigation-left",
            1306,
            810,
            1306,
            904,
            "marked-navigation-guide",
            clip_to_protection=True,
        ),
        line(
            "marked-navigation-right",
            1458,
            810,
            1458,
            904,
            "marked-navigation-guide",
            clip_to_protection=True,
        ),
    ]

    # Eight channel-strip guides occupy the safe gaps immediately right of
    # the protected fader motion envelopes.
    for index, x in enumerate((256, 386, 516, 646, 775, 905, 1035, 1157), 1):
        primitives.append(
            line(f"track-fader-{index}", x, 787, x, 1009, "track-fader-guide")
        )

    # The green user markup is a placement trace only. Compare-attempt
    # re-centering: each contour is anchored on the measured green ring so it
    # encircles the knob witness AND its rotated label group (cx from the
    # protected witness/label boxes; cy/radii measured per-knob from the green
    # markup). Deliberate breaks where the ring crosses the knob or a grid label
    # are produced by protection clipping and are acceptable.
    track_contours = [
        (191, 174, 56, 50),
        (321, 174, 56, 50),
        (451, 174, 56, 50),
        (581, 174, 56, 50),
        (711, 174, 56, 50),
        (840, 174, 56, 50),
        (970, 174, 56, 50),
        (1100, 174, 56, 50),
    ]
    device_contours = [
        (1337, 483, 50, 42),
        (1467, 483, 50, 42),
        (1597, 483, 50, 42),
        (1727, 483, 50, 42),
        (1337, 605, 50, 43),
        (1467, 605, 50, 43),
        (1597, 605, 50, 43),
        (1727, 605, 50, 43),
    ]
    for index, (cx, cy, radius_x, radius_y) in enumerate(track_contours, 1):
        primitives.append(
            ellipse(
                f"track-knob-{index}",
                cx,
                cy,
                radius_x,
                radius_y,
                "knob-surround",
            )
        )
    for index, (cx, cy, radius_x, radius_y) in enumerate(device_contours, 1):
        primitives.append(
            ellipse(
                f"device-knob-{index}",
                cx,
                cy,
                radius_x,
                radius_y,
                "knob-surround",
            )
        )
    primitives.append(
        ellipse("cue-level", 1216, 732, 48, 50, "knob-surround")
    )
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
        elif primitive["kind"] == "ellipse":
            cx = primitive["cx"]
            cy = primitive["cy"]
            radius_x = primitive["radius_x"]
            radius_y = primitive["radius_y"]
            x1, y1, x2, y2 = box
            nearest_x = min(max(cx, x1), x2)
            nearest_y = min(max(cy, y1), y2)
            minimum = math.sqrt(
                ((nearest_x - cx) / radius_x) ** 2
                + ((nearest_y - cy) / radius_y) ** 2
            )
            maximum = max(
                math.sqrt(
                    ((x - cx) / radius_x) ** 2
                    + ((y - cy) / radius_y) ** 2
                )
                for x in (x1, x2)
                for y in (y1, y2)
            )
            normalized_half = half / min(radius_x, radius_y)
            hit = 1.0 + normalized_half >= minimum and 1.0 - normalized_half <= maximum
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


def coordinate_to_dot(x: float, y: float) -> tuple[int, int]:
    x1, y1, x2, y2 = SAFE_BOX
    step_x = (x2 - x1) / DOT_COLUMNS
    step_y = (y2 - y1) / DOT_ROWS
    column = math.floor((x - x1) / step_x)
    row = math.floor((y - y1) / step_y)
    return (
        max(0, min(DOT_COLUMNS - 1, column)),
        max(0, min(DOT_ROWS - 1, row)),
    )


def dot_box(column: int, row: int) -> list[float]:
    x1, y1, x2, y2 = SAFE_BOX
    step_x = (x2 - x1) / DOT_COLUMNS
    step_y = (y2 - y1) / DOT_ROWS
    return [
        x1 + column * step_x,
        y1 + row * step_y,
        x1 + (column + 1) * step_x,
        y1 + (row + 1) * step_y,
    ]


def dots_for_primitive(primitive: dict[str, Any]) -> set[tuple[int, int]]:
    dots: set[tuple[int, int]] = set()
    if primitive["kind"] == "line":
        c1, r1 = coordinate_to_dot(primitive["x1"], primitive["y1"])
        c2, r2 = coordinate_to_dot(primitive["x2"], primitive["y2"])
        if c1 == c2:
            for row in range(min(r1, r2), max(r1, r2) + 1):
                dots.add((c1, row))
        elif r1 == r2:
            for column in range(min(c1, c2), max(c1, c2) + 1):
                dots.add((column, r1))
        else:
            samples = max(abs(c2 - c1), abs(r2 - r1)) * 4 + 1
            for index in range(samples):
                fraction = index / max(samples - 1, 1)
                x = primitive["x1"] + (
                    primitive["x2"] - primitive["x1"]
                ) * fraction
                y = primitive["y1"] + (
                    primitive["y2"] - primitive["y1"]
                ) * fraction
                dots.add(coordinate_to_dot(x, y))
    elif primitive["kind"] == "circle":
        circumference = 2.0 * math.pi * primitive["radius"]
        x1, y1, x2, y2 = SAFE_BOX
        step_x = (x2 - x1) / DOT_COLUMNS
        step_y = (y2 - y1) / DOT_ROWS
        samples = max(
            96,
            math.ceil(circumference / min(step_x, step_y) * 4.0),
        )
        for index in range(samples):
            angle = 2.0 * math.pi * index / samples
            x = primitive["cx"] + math.cos(angle) * primitive["radius"]
            y = primitive["cy"] + math.sin(angle) * primitive["radius"]
            dots.add(coordinate_to_dot(x, y))
    elif primitive["kind"] == "ellipse":
        radius_x = primitive["radius_x"]
        radius_y = primitive["radius_y"]
        circumference = math.pi * (
            3.0 * (radius_x + radius_y)
            - math.sqrt(
                (3.0 * radius_x + radius_y)
                * (radius_x + 3.0 * radius_y)
            )
        )
        x1, y1, x2, y2 = SAFE_BOX
        step_x = (x2 - x1) / DOT_COLUMNS
        step_y = (y2 - y1) / DOT_ROWS
        samples = max(
            96,
            math.ceil(circumference / min(step_x, step_y) * 4.0),
        )
        for index in range(samples):
            angle = 2.0 * math.pi * index / samples
            x = primitive["cx"] + math.cos(angle) * radius_x
            y = primitive["cy"] + math.sin(angle) * radius_y
            dots.add(coordinate_to_dot(x, y))
    else:
        raise ValueError(f"unsupported primitive kind: {primitive['kind']}")
    return dots


def grid_text(
    primitives: list[dict[str, Any]], protected: list[dict[str, Any]]
) -> tuple[str, dict[str, Any]]:
    desired: set[tuple[int, int]] = set()
    primitive_dots: dict[str, set[tuple[int, int]]] = {}
    for primitive in primitives:
        dots = dots_for_primitive(primitive)
        primitive_dots[primitive["id"]] = dots
        desired.update(dots)

    occupied: set[tuple[int, int]] = set()
    clipped: list[dict[str, Any]] = []
    for column, row in sorted(desired, key=lambda item: (item[1], item[0])):
        box = dot_box(column, row)
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
                    "dot_box": [round(value, 6) for value in box],
                    "protected_layers": sorted({record["layer"] for record in hits}),
                }
            )
        else:
            occupied.add((column, row))

    empty_primitives = sorted(
        primitive_id
        for primitive_id, dots in primitive_dots.items()
        if not (dots & occupied)
    )
    if empty_primitives:
        raise AssertionError(
            "native Braille raster lost complete primitives: "
            + ", ".join(empty_primitives)
        )

    # U+2800 is a non-collapsing blank glyph in Cascadia Mono. Keeping every
    # row at exactly 160 characters prevents Text Block from re-aligning short
    # rows, while each visible glyph packs a 2x4 dot tile.
    lines: list[str] = []
    for row in range(GRID_ROWS):
        chars: list[str] = []
        for column in range(GRID_COLUMNS):
            mask = 0
            for local_x in range(2):
                for local_y in range(4):
                    if (
                        column * 2 + local_x,
                        row * 4 + local_y,
                    ) in occupied:
                        mask |= BRAILLE_BITS[(local_x, local_y)]
            chars.append(chr(0x2800 + mask))
        lines.append("".join(chars))
    text = "\n".join(lines)

    # Recheck each surviving logical dot as a maximum ink rectangle.
    dot_collisions = 0
    for column, row in occupied:
        box = dot_box(column, row)
        dot_collisions += sum(
            1 for record in protected if boxes_overlap(box, record["padded_box"])
        )
    if dot_collisions:
        raise AssertionError(f"Braille dot collision count is {dot_collisions}")

    nonblank_glyph_count = sum(
        1 for line_text in lines for glyph in line_text if ord(glyph) != 0x2800
    )
    return text, {
        "desired_dot_count": len(desired),
        "occupied_dot_count": len(occupied),
        "clipped_dot_count": len(clipped),
        "dot_collision_count": dot_collisions,
        "nonblank_glyph_count": nonblank_glyph_count,
        "represented_primitive_count": len(primitives) - len(empty_primitives),
        "empty_primitive_count": len(empty_primitives),
    }


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
    clip_enabled_ids = {
        primitive["id"]
        for primitive in primitives
        if primitive.get("clip_to_protection")
    }
    unexpected_collisions = [
        collision
        for collision in collisions
        if collision["primitive_id"] not in clip_enabled_ids
    ]
    if unexpected_collisions:
        preview = json.dumps(unexpected_collisions[:8], indent=2)
        raise AssertionError(f"unexpected vector collisions found:\n{preview}")

    text, text_metrics = grid_text(primitives, protected)
    text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    overlay_center = [
        CANVAS[0] / 2.0 + BASE_OVERLAY_TRANSFORM["position_x"],
        CANVAS[1] / 2.0 + BASE_OVERLAY_TRANSFORM["position_y"],
    ]
    overlay_size = [
        CANVAS[0] * BASE_OVERLAY_TRANSFORM["scale_w"] / 100.0,
        CANVAS[1] * BASE_OVERLAY_TRANSFORM["scale_h"] / 100.0,
    ]
    overlay_bounds = [
        overlay_center[0] - overlay_size[0] / 2.0,
        overlay_center[1] - overlay_size[1] / 2.0,
        overlay_center[0] + overlay_size[0] / 2.0,
        overlay_center[1] + overlay_size[1] / 2.0,
    ]
    overlay_collisions = [
        {
            "layer": record["layer"],
            "raw_key": record["raw_key"],
            "role": record["role"],
        }
        for record in protected
        if boxes_overlap(overlay_bounds, record["padded_box"])
    ]
    if overlay_collisions:
        preview = json.dumps(overlay_collisions[:8], indent=2)
        raise AssertionError(f"solid overlay collisions found:\n{preview}")
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
            "collision_count": len(unexpected_collisions),
            "clipped_intent_collision_count": len(collisions),
            "clip_enabled_primitive_count": len(clip_enabled_ids),
            "rendered_collision_count": text_metrics["dot_collision_count"],
            "primitives": primitives,
        },
        "native_text_block": {
            "font": "Cascadia Mono",
            "style": "Regular",
            "color_rgba": "#b51d35ff",
            "outline_color_rgba": "#b51d35ff",
            "outline_width": 0.32,
            "outline_geometry_contract": {
                "bounded_by": "protected maximum dot-cell geometry",
                "enlarges_protected_geometry_footprint": False,
                "dot_collision_count": text_metrics["dot_collision_count"],
            },
            "size": 0.5,
            "source_scale": 0.28,
            "line_width": 5000.0,
            "transform": {
                "position_x": 13.0,
                "position_y": 0.0,
                "scale": 50.0,
                "scale_w": 204.0,
                "scale_h": 170.0,
            },
            "encoding": "unicode_braille_2x4",
            "grid_columns": GRID_COLUMNS,
            "grid_rows": GRID_ROWS,
            "effective_dot_columns": DOT_COLUMNS,
            "effective_dot_rows": DOT_ROWS,
            "intended_bounds": list(SAFE_BOX),
            "desired_dot_count": text_metrics["desired_dot_count"],
            "occupied_dot_count": text_metrics["occupied_dot_count"],
            "nonblank_glyph_count": text_metrics["nonblank_glyph_count"],
            "clipped_dot_count": text_metrics["clipped_dot_count"],
            "dot_collision_count": text_metrics["dot_collision_count"],
            "represented_primitive_count": text_metrics[
                "represented_primitive_count"
            ],
            "empty_primitive_count": text_metrics["empty_primitive_count"],
            # Compatibility aliases retained for the current QA validator.
            "occupied_cells": text_metrics["occupied_dot_count"],
            "clipped_cell_count": text_metrics["clipped_dot_count"],
            "cell_collision_count": text_metrics["dot_collision_count"],
            "text_sha256": text_sha,
            "text": text,
        },
        "solid_overlay": {
            "layer": 150,
            "name": "V2 Crossfader Base",
            "source": "Solid Color",
            "color_rgba": "#b51d35ff",
            "abgr_decimal": "4281671093",
            "blend_mode": "Add",
            "layer_opacity": 1.0,
            "shape": "rectangle",
            "center": overlay_center,
            "size": overlay_size,
            "bounds": overlay_bounds,
            "collision_count": len(overlay_collisions),
            "transform": BASE_OVERLAY_TRANSFORM,
            "fft_contract": {
                "target": "clip video opacity",
                "phase_source": "composition_fft",
                "frequency_band": [0.0, 0.33],
                "output_range": [0.65, 0.95],
                "gain_db": 3.0,
                "fallback_ms": 1400,
                "geometry_modulated": False,
                "hue_modulated": False,
            },
        },
        "fft_contract": {
            "target": "clip video opacity",
            "phase_source": "composition_fft",
            "frequency_band": [0.0, 0.33],
            "output_range": [0.65, 0.95],
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
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(document["native_text_block"]["text"])
    else:
        print(
            json.dumps(
                {
                    "output": str(output),
                    "controls": document["protection"]["control_count"],
                    "primitives": document["decoration"]["primitive_count"],
                    "collisions": document["decoration"]["collision_count"],
                    "occupied_dots": document["native_text_block"][
                        "occupied_dot_count"
                    ],
                    "nonblank_glyphs": document["native_text_block"][
                        "nonblank_glyph_count"
                    ],
                    "clipped_dots": document["native_text_block"][
                        "clipped_dot_count"
                    ],
                    "dot_collisions": document["native_text_block"][
                        "dot_collision_count"
                    ],
                    "text_sha256": document["native_text_block"]["text_sha256"],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
