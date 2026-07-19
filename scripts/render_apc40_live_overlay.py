"""Build the deterministic, Add-ready APC40 MkII live-overlay artifact set.

This is an offline renderer.  It never opens or talks to Resolume.  The static
PNG supplies controller structure and labels while the existing Text Animator
clips supply active witnesses.  In particular, every fader's cap, name, and
MIDI address are one two-line moving tag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("Pillow is required: install it before rendering APC40 artifacts") from exc


SCHEMA_VERSION = 1
RENDERER_VERSION = "b0-core-3"
CANVAS = (1920, 1080)
SAFE_BOX = (100, 50, 1820, 1030)
POSITION_DOMAIN = (-32768, 32768)
WAVE_SIZE = 24
MOVING_TAG_TARGET_PX = (92, 42)
# The first Avenue live probe rendered Size 2.25 at 155x70. Size 1.25 projects
# the Fader tag to roughly 86x39 and leaves width/height headroom for the
# slightly longer MASTER and X-FADE labels before accepted B1 measurement.
PROVISIONAL_MOVING_TAG_SIZE_HINT = 1.25
LIVE_SIZE_RANGE = (0.5, 4.0)
VERTICAL_MOVING_TAG_LAYERS = (*range(94, 102), 143)
HORIZONTAL_MOVING_TAG_LAYERS = (144,)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS = PROJECT_ROOT / "react-kit" / "docs"
DEFAULT_MANIFEST = DOCS / "APC40_visual_qa_manifest.json"
DEFAULT_SVG = DOCS / "APC40_native_addresses.svg"
DEFAULT_LABEL_FONT = Path(r"C:\Windows\Fonts\BarlowCondensed-Bold.ttf")
DEFAULT_GLYPH_FONT = Path(r"C:\Windows\Fonts\seguisym.ttf")
DEFAULT_FALLBACK_GLYPH_FONT = Path(r"C:\Windows\Fonts\NotoSans-Bold.ttf")
DEFAULT_MEASUREMENT = DOCS / "APC40_visual_qa_tag_measurement.json"

ARTIFACT_NAMES = {
    "geometry": "APC40_visual_qa_geometry.json",
    "calibration": "APC40_visual_qa_calibration.json",
    "live_controls": "APC40_visual_qa_live_controls.json",
    "overlay": "APC40_visual_qa_live_overlay.png",
    "debug": "APC40_visual_qa_live_overlay_debug.png",
    "report": "APC40_visual_qa_renderer_report.json",
    "build_manifest": "APC40_visual_qa_build_manifest.json",
}
CROP_NAMES = (
    "grid",
    "track_cluster",
    "transport",
    "fader",
    "rotary",
    "navigation",
    "crossfader",
)


class RenderError(RuntimeError):
    """An input or generated artifact violated the renderer contract."""


@dataclass(frozen=True)
class Box:
    """Right/bottom-exclusive integer rectangle."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def center(self) -> tuple[int, int]:
        return ((self.left + self.right) // 2, (self.top + self.bottom) // 2)

    def inset(self, x: int, y: int | None = None) -> "Box":
        y = x if y is None else y
        return Box(self.left + x, self.top + y, self.right - x, self.bottom - y)

    def expand(self, amount: int) -> "Box":
        return Box(
            self.left - amount,
            self.top - amount,
            self.right + amount,
            self.bottom + amount,
        )

    def as_list(self) -> list[int]:
        return [self.left, self.top, self.right, self.bottom]


@dataclass(frozen=True)
class FontChoice:
    path: Path
    live_family: str
    size_px: int
    spacing_px: int
    tag_metrics: Mapping[str, Mapping[str, Any]]


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def parse_hex(value: str) -> tuple[int, int, int]:
    text = value.removeprefix("#")
    if len(text) not in (6, 8):
        raise RenderError(f"expected #rrggbb or #rrggbbaa, got {value!r}")
    return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))


def rgb_hex(rgb: Sequence[int]) -> str:
    return "#" + "".join(f"{max(0, min(255, int(channel))):02x}" for channel in rgb)


def scale_rgb(rgb: Sequence[int], factor: float) -> tuple[int, int, int]:
    return tuple(round(channel * factor) for channel in rgb)


def srgb_channel(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: Sequence[int]) -> float:
    red, green, blue = (srgb_channel(int(channel)) for channel in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_on_black(rgb: Sequence[int]) -> float:
    return (relative_luminance(rgb) + 0.05) / 0.05


def readable_rgb(rgb: Sequence[int], minimum: float = 3.2) -> tuple[int, int, int]:
    result = tuple(min(254, int(channel)) for channel in rgb)
    for _ in range(256):
        if contrast_on_black(result) >= minimum:
            return result
        result = tuple(min(254, round(channel + (254 - channel) * 0.04)) for channel in result)
    raise RenderError(f"could not produce readable color from {rgb!r}")


def box_at(center: tuple[int, int], width: int, height: int) -> Box:
    left = center[0] - width // 2
    top = center[1] - height // 2
    return Box(left, top, left + width, top + height)


def box_union(boxes: Iterable[Box]) -> Box:
    materialized = list(boxes)
    if not materialized:
        raise RenderError("cannot union an empty box sequence")
    return Box(
        min(box.left for box in materialized),
        min(box.top for box in materialized),
        max(box.right for box in materialized),
        max(box.bottom for box in materialized),
    )


def boxes_overlap(first: Box, second: Box, gutter: int = 0) -> bool:
    return not (
        first.right + gutter <= second.left
        or second.right + gutter <= first.left
        or first.bottom + gutter <= second.top
        or second.bottom + gutter <= first.top
    )


def contains(outer: Box, inner: Box) -> bool:
    return (
        outer.left <= inner.left
        and outer.top <= inner.top
        and inner.right <= outer.right
        and inner.bottom <= outer.bottom
    )


def circle_reaches_box(
    center: Sequence[int], radius: float, box: Box, gutter: float = 0
) -> bool:
    nearest_x = min(max(float(center[0]), box.left), box.right)
    nearest_y = min(max(float(center[1]), box.top), box.bottom)
    distance = math.hypot(float(center[0]) - nearest_x, float(center[1]) - nearest_y)
    return distance < radius + gutter


def panel_to_canvas(panel_x: int, panel_y: int) -> tuple[int, int]:
    return (round(100 + panel_x * 43 / 106), round(50 + panel_y * 7 / 18))


def normalized_position(rest_value: float) -> float:
    minimum, maximum = POSITION_DOMAIN
    return round((rest_value - minimum) / (maximum - minimum), 12)


def require_file(path: Path, role: str) -> bytes:
    if not path.is_file():
        if role == "manifest":
            raise RenderError(
                f"manifest is absent: {path}; run generate_apc40_visual_qa.py manifest first"
            )
        raise RenderError(f"{role} file is absent: {path}")
    return path.read_bytes()


def load_manifest(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    raw = require_file(path, "manifest")
    try:
        controls = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderError(f"manifest is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(controls, list):
        raise RenderError("manifest root must be an array")
    layers = [control.get("layer") for control in controls]
    if len(controls) != 148 or layers != list(range(1, 149)):
        raise RenderError("manifest must contain layers 1..148 exactly once")
    if sum(control.get("midi_type") == "note" for control in controls) != 120:
        raise RenderError("manifest must contain exactly 120 note controls")
    if sum(control.get("midi_type") == "cc" for control in controls) != 28:
        raise RenderError("manifest must contain exactly 28 CC controls")
    required = {
        "layer",
        "label",
        "layer_name",
        "category",
        "midi_type",
        "data1",
        "channel",
        "panel_x",
        "panel_y",
        "x",
        "y",
        "raw_key",
        "midi_label",
        "color",
    }
    for control in controls:
        missing = sorted(required - set(control))
        if missing:
            raise RenderError(f"layer {control.get('layer')} lacks fields: {missing}")
        raw_key = control["raw_key"]
        if (
            not isinstance(raw_key, str)
            or not raw_key.isascii()
            or not raw_key.isdecimal()
        ):
            raise RenderError(
                f"layer {control['layer']} raw_key must be a decimal string"
            )
        center = panel_to_canvas(int(control["panel_x"]), int(control["panel_y"]))
        if int(control["x"]) != center[0] - 960 or int(control["y"]) != center[1] - 540:
            raise RenderError(f"layer {control['layer']} applies the panel transform incorrectly")
        expected_midi = (
            ("N" if control["midi_type"] == "note" else "CC")
            + str(control["data1"])
            + "/C"
            + str(control["channel"])
        )
        if control["midi_label"] != expected_midi:
            raise RenderError(f"layer {control['layer']} has a stale MIDI label")
    raw_keys = [control["raw_key"] for control in controls]
    if len(set(raw_keys)) != 148:
        raise RenderError("manifest raw_key values must be unique")
    return controls, raw


def text_ink(font_path: Path, size: int, text: str, spacing: int = 0) -> dict[str, Any]:
    font = ImageFont.truetype(str(font_path), size)
    scratch = Image.new("L", (512, 256), 0)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing, align="center")
    width = int(math.ceil(bbox[2] - bbox[0]))
    height = int(math.ceil(bbox[3] - bbox[1]))
    return {"ink_box_px": [width, height], "bbox": [int(value) for value in bbox]}


def moving_tag_text(control: Mapping[str, Any]) -> str:
    layer = int(control["layer"])
    if 94 <= layer <= 101:
        name = f"FADER{layer - 93}"
        cap = "\u25ac"
    elif layer == 143:
        name = "MASTER"
        cap = "\u25ac"
    elif layer == 144:
        name = "X-FADE"
        cap = "\u2588"
    else:
        raise RenderError(f"layer {layer} is not a moving-tag control")
    return f"{cap} {name}\n{control['midi_label']}"


def choose_glyph_font(
    controls: Sequence[Mapping[str, Any]], primary: Path, fallback: Path
) -> FontChoice:
    if primary.is_file():
        path = primary
        live_family = "Segoe UI Symbol"
        target_size = 18
    elif fallback.is_file():
        path = fallback
        live_family = "Noto Sans"
        target_size = 18
    else:
        raise RenderError(f"neither glyph font exists: {primary} or {fallback}")
    tag_controls = [control for control in controls if int(control["layer"]) in (*range(94, 102), 143, 144)]
    chosen_size = target_size
    spacing = -1
    while chosen_size >= 12:
        metrics = {
            str(control["layer"]): {
                "text": moving_tag_text(control),
                **text_ink(path, chosen_size, moving_tag_text(control), spacing),
            }
            for control in tag_controls
        }
        if all(
            value["ink_box_px"][0] <= 92 and value["ink_box_px"][1] <= 42
            for value in metrics.values()
        ):
            return FontChoice(path, live_family, chosen_size, spacing, metrics)
        chosen_size -= 1
    raise RenderError("moving tags cannot fit the required 92x42 raster target")


def prototype_for(control: Mapping[str, Any]) -> str:
    layer = int(control["layer"])
    category = str(control["category"])
    if category == "grid":
        return "grid_pad"
    if category == "scene":
        return "scene_pad"
    if category == "clip_stop":
        return "clip_stop"
    if category == "track_select":
        return "track_select"
    if category in {"record_arm", "solo", "activator", "crossfade_assign"}:
        return "track_button"
    if category in {"track_knob", "device_knob"}:
        return "rotary"
    if category == "track_fader" or layer == 143:
        return "vertical_fader"
    if layer == 144:
        return "crossfader"
    if layer in {145, 148}:
        return "small_rotary"
    if layer == 119:
        return "secondary_text"
    if layer == 125:
        return "stop_all"
    if layer == 146:
        return "master_select"
    if layer in {126, 127, 128, 129}:
        return "bank_polygon"
    return "small_button"


PROTOTYPES: dict[str, dict[str, Any]] = {
    "grid_pad": {"body_size": [112, 48]},
    "scene_pad": {"body_size": [72, 48]},
    "clip_stop": {"body_size": [96, 48]},
    "track_select": {"body_size": [112, 40]},
    "track_button": {"body_size": [44, 40]},
    "small_button": {"body_size": [72, 36]},
    "secondary_text": {"body_size": None},
    "stop_all": {"body_size": [72, 48]},
    "master_select": {"body_size": [72, 40]},
    "bank_polygon": {"body_size": [44, 36]},
    "rotary": {"ring_diameter": 84, "outer_radius": 42, "inner_radius": 22},
    "small_rotary": {"ring_diameter": 64, "outer_radius": 32, "inner_radius": 18},
    "vertical_fader": {"lane_size": [12, 192], "motion_size": [96, 230]},
    "crossfader": {"lane_size": [202, 12], "motion_size": [236, 60]},
}


def led_family(control: Mapping[str, Any]) -> str:
    if control["midi_type"] == "cc":
        return "continuous_no_led"
    if control["category"] in {"grid", "scene"}:
        return "rgb"
    if control["category"] == "solo":
        return "fixed_blue"
    if parse_hex(str(control["color"])) == (230, 230, 230):
        return "no_led"
    return "fixed_amber"


def section_for(control: Mapping[str, Any]) -> str:
    category = str(control["category"])
    if category in {"grid", "scene"}:
        return "clip_launch"
    if category in {
        "clip_stop",
        "track_select",
        "record_arm",
        "solo",
        "activator",
        "crossfade_assign",
        "track_fader",
    }:
        return "channel_strips"
    if category in {"track_knob"}:
        return "track_control"
    if category in {"device_knob", "device_button"}:
        return "device_control"
    if category == "navigation":
        return "navigation"
    if category in {"transport", "mode", "tempo"}:
        return "transport"
    return "master"


def bank_polygon(layer: int, body: Box) -> list[list[int]]:
    cx, cy = body.center
    right = body.right - 1
    bottom = body.bottom - 1
    if layer == 126:
        return [[cx, body.top], [right, bottom], [body.left, bottom]]
    if layer == 127:
        return [[body.left, body.top], [right, body.top], [cx, bottom]]
    if layer == 128:
        return [[body.left, body.top], [right, cy], [body.left, bottom]]
    return [[right, body.top], [body.left, cy], [right, bottom]]


def build_geometry(
    controls: Sequence[Mapping[str, Any]],
    label_font: Path,
    glyph_font: FontChoice,
    build_id: str,
) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for control in controls:
        layer = int(control["layer"])
        center = panel_to_canvas(int(control["panel_x"]), int(control["panel_y"]))
        prototype = prototype_for(control)
        spec = PROTOTYPES[prototype]
        body: Box | None = None
        lane: Box | None = None
        motion: Box | None = None
        ring: dict[str, Any] | None = None
        if spec.get("body_size"):
            body = box_at(center, *spec["body_size"])
            label = body.inset(3, 2)
        elif prototype == "secondary_text":
            label = box_at(center, 76, 18)
        elif prototype in {"rotary", "small_rotary"}:
            diameter = int(spec["ring_diameter"])
            ring_box = box_at(center, diameter, diameter)
            label = Box(
                ring_box.left - 2,
                ring_box.bottom + 2,
                ring_box.right + 2,
                ring_box.bottom + 31,
            )
            ring = {
                "center_px": list(center),
                "outer_radius": spec["outer_radius"],
                "inner_radius": spec["inner_radius"],
                "box": ring_box.as_list(),
            }
        elif prototype == "vertical_fader":
            lane = box_at(center, *spec["lane_size"])
            motion = box_at(center, *spec["motion_size"])
            label = Box(motion.left + 3, motion.top + 94, motion.left + 45, motion.top + 132)
        elif prototype == "crossfader":
            lane = box_at(center, *spec["lane_size"])
            motion = box_at(center, *spec["motion_size"])
            label = Box(motion.left + 4, motion.top + 3, motion.left + 48, motion.bottom - 3)
        else:  # pragma: no cover - prototype table guards this
            raise RenderError(f"unsupported prototype {prototype}")

        active_rgb = readable_rgb(parse_hex(str(control["color"])))
        family = led_family(control)
        if family == "fixed_blue":
            active_rgb = readable_rgb((43, 91, 255))
        elif family == "fixed_amber":
            active_rgb = readable_rgb((240, 138, 36))
        elif family == "no_led":
            active_rgb = (230, 230, 230)
        off_rgb = scale_rgb(active_rgb, 0.15 if category_is_structure(control) else 0.10)

        witness_box: Box
        if motion is not None:
            witness_box = motion
        elif ring is not None:
            witness_box = box_at(center, 22, 22)
        elif body is not None:
            if control["category"] == "record_arm":
                witness_box = Box(body.right - 13, body.bottom - 13, body.right - 3, body.bottom - 3)
            else:
                witness_box = Box(body.right - 13, body.top + 3, body.right - 3, body.top + 13)
        else:
            witness_box = label

        key = f"{layer}:{control['raw_key']}"
        records[key] = {
            "layer": layer,
            "raw_key": str(control["raw_key"]),
            "midi_label": control["midi_label"],
            "label": control["label"],
            "layer_name": control["layer_name"],
            "category": control["category"],
            "section": section_for(control),
            "center_px": list(center),
            "prototype": prototype,
            "body_box": body.as_list() if body else None,
            "body_polygon": bank_polygon(layer, body) if prototype == "bank_polygon" and body else None,
            "label_box": label.as_list(),
            "name_box": [label.left, label.top, label.right - 12, (label.top + label.bottom) // 2]
            if body
            else label.as_list(),
            "address_box": [label.left, (label.top + label.bottom) // 2, label.right, label.bottom]
            if body
            else label.as_list(),
            "lane_box": lane.as_list() if lane else None,
            "motion_box": motion.as_list() if motion else None,
            "ring": ring,
            "witness_box": witness_box.as_list(),
            "collision_group": "bank_nav" if prototype == "bank_polygon" else None,
            "led_family": family,
            "off_rgb": list(off_rgb),
            "active_rgb": list(active_rgb),
            "witness_metrics": glyph_font.tag_metrics.get(str(layer)),
        }

    geometry = {
        "schema_version": SCHEMA_VERSION,
        "build_id": build_id,
        "canvas": {"width": CANVAS[0], "height": CANVAS[1], "origin": "top-left"},
        "safe_box": list(SAFE_BOX),
        "panel_transform": {
            "x": "round(100 + panel_x * 43/106)",
            "y": "round(50 + panel_y * 7/18)",
        },
        "fonts": {
            "label": str(label_font.resolve()),
            "glyph": str(glyph_font.path.resolve()),
            "glyph_live_family": glyph_font.live_family,
            "moving_tag_size_px": glyph_font.size_px,
        },
        "prototypes": PROTOTYPES,
        "controls": records,
    }
    validate_geometry(geometry)
    return geometry


def category_is_structure(control: Mapping[str, Any]) -> bool:
    return control["category"] != "grid"


def record_box(record: Mapping[str, Any], field: str) -> Box | None:
    value = record.get(field)
    return Box(*value) if value else None


def validate_geometry(geometry: Mapping[str, Any]) -> None:
    records = sorted(
        geometry["controls"].values(), key=lambda record: int(record["layer"])
    )
    if len(records) != 148:
        raise RenderError("geometry must contain 148 records")
    if [record["layer"] for record in records] != list(range(1, 149)):
        raise RenderError("geometry layer order is not 1..148")
    safe = Box(*geometry["safe_box"])
    for record in records:
        for field in ("body_box", "label_box", "lane_box", "motion_box", "witness_box"):
            box = record_box(record, field)
            if box and not contains(safe, box):
                raise RenderError(f"layer {record['layer']} {field} escapes the safe box")
        ring = record.get("ring")
        if ring and not contains(safe, Box(*ring["box"])):
            raise RenderError(f"layer {record['layer']} ring escapes the safe box")

    # Independent physical bodies must keep the two-pixel gutter.  Labels are
    # inside their own bodies or purposefully close to their own ring/lane.
    for index, first in enumerate(records):
        first_body = record_box(first, "body_box")
        for second in records[index + 1 :]:
            second_body = record_box(second, "body_box")
            same_collision_group = bool(
                first.get("collision_group")
                and first.get("collision_group") == second.get("collision_group")
            )
            if (
                first_body
                and second_body
                and not same_collision_group
                and boxes_overlap(first_body, second_body, gutter=2)
            ):
                raise RenderError(
                    f"body collision: layers {first['layer']} and {second['layer']}"
                )
            first_label = record_box(first, "label_box")
            second_label = record_box(second, "label_box")
            assert first_label and second_label
            if boxes_overlap(first_label, second_label, gutter=2):
                raise RenderError(
                    f"label collision: layers {first['layer']} and {second['layer']}"
                )
            if second_body and boxes_overlap(first_label, second_body, gutter=2):
                raise RenderError(
                    f"layer {first['layer']} label reaches layer {second['layer']} body"
                )
            if first_body and boxes_overlap(second_label, first_body, gutter=2):
                raise RenderError(
                    f"layer {second['layer']} label reaches layer {first['layer']} body"
                )
            first_ring = first.get("ring")
            second_ring = second.get("ring")
            if first_ring and circle_reaches_box(
                first_ring["center_px"], float(first_ring["outer_radius"]), second_label, 2
            ):
                raise RenderError(
                    f"layer {first['layer']} ring reaches layer {second['layer']} label"
                )
            if second_ring and circle_reaches_box(
                second_ring["center_px"], float(second_ring["outer_radius"]), first_label, 2
            ):
                raise RenderError(
                    f"layer {second['layer']} ring reaches layer {first['layer']} label"
                )
            if first_ring and second_ring:
                distance = math.dist(first_ring["center_px"], second_ring["center_px"])
                if distance < first_ring["outer_radius"] + second_ring["outer_radius"] + 2:
                    raise RenderError(
                        f"rotary collision: layers {first['layer']} and {second['layer']}"
                    )
            if first_ring and second_body and circle_reaches_box(
                first_ring["center_px"],
                float(first_ring["outer_radius"]),
                second_body,
                2,
            ):
                raise RenderError(
                    f"layer {first['layer']} ring reaches layer {second['layer']} body"
                )
            if second_ring and first_body and circle_reaches_box(
                second_ring["center_px"],
                float(second_ring["outer_radius"]),
                first_body,
                2,
            ):
                raise RenderError(
                    f"layer {second['layer']} ring reaches layer {first['layer']} body"
                )

    moving = [record for record in records if record.get("motion_box")]
    for index, first in enumerate(moving):
        first_motion = record_box(first, "motion_box")
        assert first_motion
        for second in moving[index + 1 :]:
            second_motion = record_box(second, "motion_box")
            assert second_motion
            if boxes_overlap(first_motion, second_motion, gutter=2):
                raise RenderError(
                    f"swept witness collision: layers {first['layer']} and {second['layer']}"
                )
        for second in records:
            if second["layer"] == first["layer"]:
                continue
            body = record_box(second, "body_box")
            label = record_box(second, "label_box")
            ring = Box(*second["ring"]["box"]) if second.get("ring") else None
            if (body and boxes_overlap(first_motion, body, gutter=2)) or (
                ring and boxes_overlap(first_motion, ring, gutter=2)
            ):
                raise RenderError(
                    f"layer {first['layer']} swept witness reaches layer {second['layer']}"
                )
            if label and boxes_overlap(first_motion, label, gutter=2):
                raise RenderError(
                    f"layer {first['layer']} swept witness reaches "
                    f"layer {second['layer']} label"
                )


def accepted_metric_dimensions(
    layer: int, accepted_metrics: Mapping[str, Any]
) -> tuple[int, int]:
    candidate = accepted_metrics.get(str(layer)) or accepted_metrics.get(
        "horizontal" if layer == 144 else "vertical"
    )
    if isinstance(candidate, Mapping):
        candidate = candidate.get("ink_box_px")
    if not isinstance(candidate, (list, tuple)) or len(candidate) != 2:
        raise RenderError(f"accepted live tag metrics lack layer {layer} ink_box_px")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in candidate
    ):
        raise RenderError(
            f"accepted live tag metrics for layer {layer} must be positive integer pixels"
        )
    width, height = int(candidate[0]), int(candidate[1])
    target_width, target_height = MOVING_TAG_TARGET_PX
    if width > target_width or height > target_height:
        raise RenderError(
            f"accepted live tag metrics for layer {layer} are {width}x{height}, "
            f"exceeding {target_width}x{target_height}"
        )
    return width, height


def validate_accepted_live_tag_metrics(metrics: Mapping[str, Any]) -> None:
    for layer in (*VERTICAL_MOVING_TAG_LAYERS, *HORIZONTAL_MOVING_TAG_LAYERS):
        accepted_metric_dimensions(layer, metrics)


def derive_accepted_live_tag_metrics(
    measured_metrics: Mapping[str, Any],
    glyph_font: FontChoice,
    selected_avenue_size: float,
) -> dict[str, Any]:
    """Expand a live Fader 1 measurement to truthful tag-family envelopes.

    Avenue Size is not a pixel size, so the live Fader 1 raster is the scale
    reference.  Width and height are scaled independently because Avenue's
    multiline layout can add vertical spacing without widening the glyphs.
    Applying the larger ratio to both axes falsely widens every tag when that
    happens. Integer rational arithmetic plus ceiling avoids float-rounding
    and under-sizing on either axis.
    """

    measured_width, measured_height = accepted_metric_dimensions(
        94, measured_metrics
    )
    reference = glyph_font.tag_metrics.get("94")
    if not isinstance(reference, Mapping):
        raise RenderError("offline moving-tag metrics lack Fader 1 layer 94")
    offline_reference = reference.get("ink_box_px")
    if (
        not isinstance(offline_reference, (list, tuple))
        or len(offline_reference) != 2
        or any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
            for value in offline_reference
        )
    ):
        raise RenderError("offline Fader 1 ink_box_px is invalid")
    offline_width, offline_height = (
        int(offline_reference[0]),
        int(offline_reference[1]),
    )

    def scaled_dimension(value: int, numerator: int, denominator: int) -> int:
        return (
            value * numerator + denominator - 1
        ) // denominator

    by_layer: dict[str, Any] = {}
    for layer in (*VERTICAL_MOVING_TAG_LAYERS, *HORIZONTAL_MOVING_TAG_LAYERS):
        metric = glyph_font.tag_metrics.get(str(layer))
        if not isinstance(metric, Mapping):
            raise RenderError(f"offline moving-tag metrics lack layer {layer}")
        offline_box = metric.get("ink_box_px")
        text = metric.get("text")
        if (
            not isinstance(offline_box, (list, tuple))
            or len(offline_box) != 2
            or any(
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
                for value in offline_box
            )
            or not isinstance(text, str)
            or not text
        ):
            raise RenderError(f"offline moving-tag metric for layer {layer} is invalid")
        scaled_box = [
            scaled_dimension(int(offline_box[0]), measured_width, offline_width),
            scaled_dimension(int(offline_box[1]), measured_height, offline_height),
        ]
        if any(
            value > maximum
            for value, maximum in zip(scaled_box, MOVING_TAG_TARGET_PX)
        ):
            raise RenderError(
                f"derived live tag metrics for layer {layer} are "
                f"{scaled_box[0]}x{scaled_box[1]}, exceeding "
                f"{MOVING_TAG_TARGET_PX[0]}x{MOVING_TAG_TARGET_PX[1]}"
            )
        by_layer[str(layer)] = {
            "text": text,
            "offline_ink_box_px": [int(offline_box[0]), int(offline_box[1])],
            "ink_box_px": scaled_box,
        }

    vertical_box = [
        max(by_layer[str(layer)]["ink_box_px"][dimension] for layer in VERTICAL_MOVING_TAG_LAYERS)
        for dimension in range(2)
    ]
    horizontal_box = [
        max(by_layer[str(layer)]["ink_box_px"][dimension] for layer in HORIZONTAL_MOVING_TAG_LAYERS)
        for dimension in range(2)
    ]
    derived = {
        "measurement_reference": {
            "layer": 94,
            "ink_box_px": [measured_width, measured_height],
            "selected_avenue_size": selected_avenue_size,
        },
        "offline_reference": {
            "layer": 94,
            "ink_box_px": [offline_width, offline_height],
            "font": glyph_font.live_family,
            "size_px": glyph_font.size_px,
        },
        "live_to_offline_scale": {
            "width": {
                "numerator": measured_width,
                "denominator": offline_width,
            },
            "height": {
                "numerator": measured_height,
                "denominator": offline_height,
            },
        },
        "by_layer": by_layer,
        "vertical": {
            "layers": list(VERTICAL_MOVING_TAG_LAYERS),
            "ink_box_px": vertical_box,
        },
        "horizontal": {
            "layers": list(HORIZONTAL_MOVING_TAG_LAYERS),
            "ink_box_px": horizontal_box,
        },
    }
    validate_accepted_live_tag_metrics(derived)
    return derived


def motion_ink_size(
    layer: int, glyph_font: FontChoice, accepted_metrics: Mapping[str, Any] | None
) -> tuple[int, int]:
    if accepted_metrics is not None:
        return accepted_metric_dimensions(layer, accepted_metrics)
    metric = glyph_font.tag_metrics[str(layer)]["ink_box_px"]
    return int(metric[0]), int(metric[1])


def build_calibration(
    geometry: Mapping[str, Any],
    glyph_font: FontChoice,
    build_id: str,
    *,
    status: str = "provisional",
    parent_build_id: str | None = None,
    measurement_sha256: str | None = None,
    measurement_parent_artifact_hashes: Mapping[str, Any] | None = None,
    accepted_live_tag_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    by_layer = {record["layer"]: record for record in geometry["controls"].values()}
    ranges: dict[str, Any] = {}
    for layer in (*range(94, 102), 143):
        record = by_layer[layer]
        lane = Box(*record["lane_box"])
        motion = Box(*record["motion_box"])
        ink_width, ink_height = motion_ink_size(
            layer, glyph_font, accepted_live_tag_metrics
        )
        top_center = lane.top + ink_height / 2
        bottom_center = lane.bottom - ink_height / 2
        if top_center >= bottom_center:
            raise RenderError(f"layer {layer} has non-positive vertical tag travel")
        if (
            lane.center[0] - ink_width / 2 < motion.left
            or lane.center[0] + ink_width / 2 > motion.right
            or top_center - ink_height / 2 < motion.top
            or bottom_center + ink_height / 2 > motion.bottom
        ):
            raise RenderError(f"layer {layer} moving tag escapes its motion box")
        top_rest = top_center - 540
        bottom_rest = bottom_center - 540
        ranges[str(layer)] = {
            "axis": "y",
            "geometry": {
                "lane": lane.as_list(),
                "motion_box": record["motion_box"],
                "top_center_px": round(top_center, 3),
                "bottom_center_px": round(bottom_center, 3),
                "travel_px": round(bottom_center - top_center, 3),
            },
            "value_at_cc0": normalized_position(bottom_rest),
            "value_at_cc127": normalized_position(top_rest),
            "xml_value_range": [
                normalized_position(bottom_rest),
                normalized_position(top_rest),
            ],
        }
    layer = 144
    record = by_layer[layer]
    lane = Box(*record["lane_box"])
    motion = Box(*record["motion_box"])
    ink_width, ink_height = motion_ink_size(
        layer, glyph_font, accepted_live_tag_metrics
    )
    left_center = lane.left + ink_width / 2
    right_center = lane.right - ink_width / 2
    if left_center >= right_center:
        raise RenderError("layer 144 has non-positive horizontal tag travel")
    if (
        left_center - ink_width / 2 < motion.left
        or right_center + ink_width / 2 > motion.right
        or lane.center[1] - ink_height / 2 < motion.top
        or lane.center[1] + ink_height / 2 > motion.bottom
    ):
        raise RenderError("layer 144 moving tag escapes its motion box")
    ranges[str(layer)] = {
        "axis": "x",
        "geometry": {
            "lane": lane.as_list(),
            "motion_box": record["motion_box"],
            "left_center_px": round(left_center, 3),
            "right_center_px": round(right_center, 3),
            "travel_px": round(right_center - left_center, 3),
        },
        "value_at_cc0": normalized_position(left_center - 960),
        "value_at_cc127": normalized_position(right_center - 960),
        "xml_value_range": [
            normalized_position(left_center - 960),
            normalized_position(right_center - 960),
        ],
    }
    for rotary_layer in (*range(102, 118), 145):
        record = by_layer[rotary_layer]
        ranges[str(rotary_layer)] = {
            "axis": "rotation_z",
            "geometry": record["ring"],
            "value_at_cc0": 0.125,
            "value_at_cc127": 0.875,
            "xml_value_range": [0.125, 0.875],
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "build_id": build_id,
        "parent_build_id": parent_build_id,
        "measurement_sha256": measurement_sha256,
        "measurement_parent_artifact_hashes": measurement_parent_artifact_hashes,
        "status": status,
        "position_domain": list(POSITION_DOMAIN),
        "rotation_domain_deg": [-180, 180],
        "opacity_ranges_by_category": {
            "fader": [0.65, 1.0],
            "crossfader": [0.65, 1.0],
            "rotary": [0.35, 1.0],
        },
        "moving_tag_raster_targets_px": {
            "vertical": [92, 42],
            "horizontal": [92, 42],
        },
        "offline_tag_metrics": {
            "font": str(glyph_font.path.resolve()),
            "live_family": glyph_font.live_family,
            "size_px": glyph_font.size_px,
            "spacing_px": glyph_font.spacing_px,
            "by_layer": glyph_font.tag_metrics,
        },
        "accepted_live_tag_metrics": accepted_live_tag_metrics,
        "motion_ranges_by_layer": ranges,
        "knob_rest_degrees": [-135, 135],
        "tempo_relative": {
            "step": "-0.0020833333333333333044",
            "num_steps": 480,
        },
        "position_y_visual_direction": "positive_down",
    }


def source_field(parameter: str, valuetype: str, desired: Any, purpose: str) -> dict[str, Any]:
    return {
        "target": "text_animator_source",
        "parameter": parameter,
        "valuetype": valuetype,
        "desired": desired,
        "purpose": purpose,
    }


def build_live_controls(
    controls: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    glyph_font: FontChoice,
    build_id: str,
    status: str = "provisional",
    accepted_size: float | None = None,
) -> dict[str, Any]:
    by_layer = {record["layer"]: record for record in geometry["controls"].values()}
    layers: dict[str, Any] = {}
    for control in controls:
        layer = int(control["layer"])
        record = by_layer[layer]
        if control["midi_type"] == "note":
            witness_text = "\u25cf" if control["category"] == "record_arm" else "\u25a0"
            witness_kind = "button_circle" if control["category"] == "record_arm" else "button_square"
            live_size = 1.5
        elif layer in (*range(94, 102), 143, 144):
            witness_text = moving_tag_text(control)
            witness_kind = "horizontal_moving_tag" if layer == 144 else "vertical_moving_tag"
            live_size = (
                accepted_size
                if accepted_size is not None
                else PROVISIONAL_MOVING_TAG_SIZE_HINT
            )
        else:
            witness_text = "\u25b2"
            witness_kind = "rotary_pointer"
            live_size = 1.5

        color = rgb_hex(record["active_rgb"]) + "ff"
        source_x = 0.0
        source_y = 0.0
        if control["midi_type"] == "note":
            witness_center = Box(*record["witness_box"]).center
            control_center = tuple(record["center_px"])
            permanent_scale = float(control.get("scale", 100)) / 100.0
            if permanent_scale <= 0:
                raise RenderError(f"layer {layer} has a non-positive permanent scale")
            source_x = round((witness_center[0] - control_center[0]) / permanent_scale, 6)
            source_y = round((witness_center[1] - control_center[1]) / permanent_scale, 6)
        fields = [
            source_field("Text", "ParamText", witness_text, "active witness"),
            source_field("Font", "ParamChoice", glyph_font.live_family, "glyph coverage"),
            source_field("Size", "ParamRange", live_size, "raster-sized witness"),
            source_field("Color", "ParamColor", color, "LED-family witness color"),
            source_field(
                "Position X",
                "ParamRange",
                source_x,
                "corner witness offset in source pixels before permanent scale",
            ),
            source_field(
                "Position Y",
                "ParamRange",
                source_y,
                "corner witness offset in source pixels before permanent scale",
            ),
        ]
        if "\n" in witness_text:
            fields.append(source_field("Spacing Y", "ParamRange", -10.0, "compact two-line tag"))
        if control["midi_type"] == "cc":
            fields.append(
                {
                    "target": "clip_video",
                    "parameter": "opacity",
                    "valuetype": "ParamRange",
                    "desired": 1.0,
                    "purpose": "visible continuous witness",
                }
            )
            if layer in (*range(94, 102), 143):
                axis, desired = "Position Y", float(control["y"])
            elif layer == 144:
                axis, desired = "Position X", float(control["x"])
            else:
                axis, desired = "Rotation Z", 0.0
            fields.append(
                {
                    "target": "permanent_transform",
                    "parameter": axis,
                    "valuetype": "ParamRange",
                    "desired": desired,
                    "purpose": "MIDI motion axis",
                }
            )
        layers[str(layer)] = {
            "layer": layer,
            "raw_key": str(control["raw_key"]),
            "midi_label": control["midi_label"],
            "category": control["category"],
            "prototype": layer in {1, 46, 94, 102},
            "witness": {
                "kind": witness_kind,
                "text": witness_text,
                "color": color,
                "box": record["witness_box"],
            },
            "fields": fields,
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "build_id": build_id,
        "status": status,
        "artifact_role": "typed_live_controls",
        "wave_size": WAVE_SIZE,
        "glyph_font": {
            "offline_path": str(glyph_font.path.resolve()),
            "live_family": glyph_font.live_family,
            "offline_size_px": glyph_font.size_px,
            "live_size_value": accepted_size,
            "measurement_status": status,
            "provisional_moving_tag_size_hint": PROVISIONAL_MOVING_TAG_SIZE_HINT,
            "calibration_sweep": [0.5, 4.0],
        },
        "layers": layers,
    }
    encoded = canonical_json(result)
    if b"connect_continuous" in encoded:
        raise RenderError("typed live controls contain a forbidden generic operation")
    return result


def draw_fitted_text(
    image: Image.Image,
    box: Box,
    text: str,
    font_path: Path,
    size: int,
    fill: tuple[int, int, int],
) -> dict[str, Any]:
    font = ImageFont.truetype(str(font_path), size)
    scratch = Image.new("L", (512, 128), 0)
    scratch_draw = ImageDraw.Draw(scratch)
    bbox = scratch_draw.textbbox((0, 0), text, font=font)
    width = max(1, int(math.ceil(bbox[2] - bbox[0])))
    height = max(1, int(math.ceil(bbox[3] - bbox[1])))
    scratch_draw.text((-bbox[0], -bbox[1]), text, font=font, fill=255)
    mask = scratch.crop((0, 0, width, height))
    source_size = mask.size
    if mask.width > box.width:
        mask = mask.resize((box.width, mask.height), Image.Resampling.LANCZOS)
    if mask.height > box.height:
        scale = box.height / mask.height
        mask = mask.resize((max(1, round(mask.width * scale)), box.height), Image.Resampling.LANCZOS)
    left = box.left + (box.width - mask.width) // 2
    top = box.top + (box.height - mask.height) // 2
    color = Image.new("RGB", mask.size, fill)
    image.paste(color, (left, top), mask)
    return {
        "text": text,
        "box": box.as_list(),
        "ink_box": [left, top, left + mask.width, top + mask.height],
        "source_ink_px": list(source_size),
        "rendered_ink_px": [mask.width, mask.height],
        "font_size": size,
    }


def draw_overlay(
    controls: Sequence[Mapping[str, Any]],
    geometry: Mapping[str, Any],
    label_font: Path,
) -> tuple[Image.Image, list[dict[str, Any]]]:
    image = Image.new("RGB", CANVAS, (0, 0, 0))
    draw = ImageDraw.Draw(image)
    by_layer = {record["layer"]: record for record in geometry["controls"].values()}
    metrics: list[dict[str, Any]] = []
    for control in controls:
        record = by_layer[int(control["layer"])]
        active = tuple(record["active_rgb"])
        structural = tuple(record["off_rgb"])
        body = record_box(record, "body_box")
        if body:
            coordinates = (body.left, body.top, body.right - 1, body.bottom - 1)
            fill = scale_rgb(active, 0.025)
            if record["body_polygon"]:
                polygon = [tuple(point) for point in record["body_polygon"]]
                draw.polygon(polygon, fill=fill, outline=structural)
            else:
                radius = min(8, body.height // 5)
                draw.rounded_rectangle(coordinates, radius=radius, fill=fill, outline=structural, width=2)
            name_box = Box(*record["name_box"])
            address_box = Box(*record["address_box"])
            if control["category"] == "record_arm":
                witness = Box(*record["witness_box"])
                radius = max(2, min(witness.width, witness.height) // 2 - 1)
                draw.ellipse(
                    (witness.left, witness.top, witness.right - 1, witness.bottom - 1),
                    fill=structural,
                    outline=scale_rgb(active, 0.22),
                    width=1,
                )
            else:
                metrics.append(
                    {
                        "layer": control["layer"],
                        "role": "name",
                        **draw_fitted_text(image, name_box, str(control["label"]), label_font, 17, active),
                    }
                )
            metrics.append(
                {
                    "layer": control["layer"],
                    "role": "address",
                    **draw_fitted_text(
                        image, address_box, str(control["midi_label"]), label_font, 13, active
                    ),
                }
            )
        elif record["prototype"] == "secondary_text":
            metrics.append(
                {
                    "layer": control["layer"],
                    "role": "secondary",
                    **draw_fitted_text(
                        image,
                        Box(*record["label_box"]),
                        f"{control['label']} {control['midi_label']}",
                        label_font,
                        13,
                        active,
                    ),
                }
            )
        elif record["ring"]:
            ring = record["ring"]
            cx, cy = ring["center_px"]
            outer = int(ring["outer_radius"])
            inner = int(ring["inner_radius"])
            ring_box = Box(*ring["box"])
            draw.ellipse(
                (
                    ring_box.left,
                    ring_box.top,
                    ring_box.right - 1,
                    ring_box.bottom - 1,
                ),
                outline=structural,
                width=2,
            )
            draw.ellipse(
                (cx - inner, cy - inner, cx + inner - 1, cy + inner - 1),
                outline=scale_rgb(active, 0.22),
                width=2,
            )
            for degrees in range(-135, 136, 45):
                radians = math.radians(degrees - 90)
                inner_tick = outer - 6
                outer_tick = outer - 1
                draw.line(
                    (
                        round(cx + inner_tick * math.cos(radians)),
                        round(cy + inner_tick * math.sin(radians)),
                        round(cx + outer_tick * math.cos(radians)),
                        round(cy + outer_tick * math.sin(radians)),
                    ),
                    fill=structural,
                    width=1,
                )
            label = Box(*record["label_box"])
            midpoint = (label.top + label.bottom) // 2
            metrics.append(
                {
                    "layer": control["layer"],
                    "role": "name",
                    **draw_fitted_text(
                        image,
                        Box(label.left, label.top, label.right, midpoint),
                        str(control["label"]),
                        label_font,
                        17,
                        active,
                    ),
                }
            )
            metrics.append(
                {
                    "layer": control["layer"],
                    "role": "address",
                    **draw_fitted_text(
                        image,
                        Box(label.left, midpoint, label.right, label.bottom),
                        str(control["midi_label"]),
                        label_font,
                        13,
                        active,
                    ),
                }
            )
        elif record["lane_box"]:
            lane = Box(*record["lane_box"])
            if record["prototype"] == "vertical_fader":
                draw.rounded_rectangle(
                    (lane.left, lane.top, lane.right - 1, lane.bottom - 1),
                    radius=4,
                    outline=structural,
                    width=2,
                )
                for y in (lane.top, (lane.top + lane.bottom) // 2, lane.bottom - 1):
                    draw.line((lane.left - 10, y, lane.left - 3, y), fill=structural, width=2)
                anchor = (
                    f"F{int(control['layer']) - 93}" if int(control["layer"]) <= 101 else "MF"
                )
            else:
                draw.rounded_rectangle(
                    (lane.left, lane.top, lane.right - 1, lane.bottom - 1),
                    radius=4,
                    outline=structural,
                    width=2,
                )
                for x in (lane.left, (lane.left + lane.right) // 2, lane.right - 1):
                    draw.line((x, lane.top - 8, x, lane.top - 3), fill=structural, width=2)
                anchor = "XF"
            label = Box(*record["label_box"])
            midpoint = (label.top + label.bottom) // 2
            dim_label = readable_rgb(scale_rgb(active, 0.55), 3.0)
            metrics.append(
                {
                    "layer": control["layer"],
                    "role": "anchor",
                    **draw_fitted_text(
                        image,
                        Box(label.left, label.top, label.right, midpoint),
                        anchor,
                        label_font,
                        13,
                        dim_label,
                    ),
                }
            )
            metrics.append(
                {
                    "layer": control["layer"],
                    "role": "midi_reference",
                    **draw_fitted_text(
                        image,
                        Box(label.left, midpoint, label.right, label.bottom),
                        str(control["midi_label"]),
                        label_font,
                        11,
                        dim_label,
                    ),
                }
            )
    return image, metrics


def paste_debug_tag(
    image: Image.Image,
    center: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    spacing: int,
    target_size: tuple[int, int],
) -> None:
    scratch = Image.new("L", (512, 256), 0)
    scratch_draw = ImageDraw.Draw(scratch)
    bbox = scratch_draw.multiline_textbbox(
        (0, 0), text, font=font, spacing=spacing, align="center"
    )
    width = max(1, int(math.ceil(bbox[2] - bbox[0])))
    height = max(1, int(math.ceil(bbox[3] - bbox[1])))
    scratch_draw.multiline_text(
        (-bbox[0], -bbox[1]),
        text,
        font=font,
        fill=255,
        align="center",
        spacing=spacing,
    )
    mask = scratch.crop((0, 0, width, height))
    if mask.size != target_size:
        mask = mask.resize(target_size, Image.Resampling.LANCZOS)
    left = round(center[0] - mask.width / 2)
    top = round(center[1] - mask.height / 2)
    color = Image.new("RGB", mask.size, (85, 85, 85))
    image.paste(color, (left, top), mask)


def draw_debug(
    overlay: Image.Image,
    geometry: Mapping[str, Any],
    glyph_font: FontChoice,
    accepted_metrics: Mapping[str, Any] | None = None,
) -> Image.Image:
    image = overlay.copy()
    draw = ImageDraw.Draw(image)
    safe = Box(*geometry["safe_box"])
    draw.rectangle((safe.left, safe.top, safe.right - 1, safe.bottom - 1), outline=(45, 45, 45))
    font = ImageFont.truetype(str(glyph_font.path), glyph_font.size_px)
    for record in geometry["controls"].values():
        body = record_box(record, "body_box")
        if body:
            draw.rectangle((body.left, body.top, body.right - 1, body.bottom - 1), outline=(20, 60, 80))
        motion = record_box(record, "motion_box")
        if not motion:
            continue
        draw.rectangle(
            (motion.left, motion.top, motion.right - 1, motion.bottom - 1),
            outline=(100, 50, 100),
        )
        metric = record.get("witness_metrics")
        if not metric:
            continue
        text = metric["text"]
        width, height = motion_ink_size(
            int(record["layer"]), glyph_font, accepted_metrics
        )
        lane = record_box(record, "lane_box")
        assert lane
        if record["layer"] == 144:
            centers = (
                (round(lane.left + width / 2), lane.center[1]),
                (round(lane.right - width / 2), lane.center[1]),
            )
        else:
            centers = (
                (lane.center[0], round(lane.top + height / 2)),
                (lane.center[0], round(lane.bottom - height / 2)),
            )
        for center in centers:
            paste_debug_tag(
                image,
                center,
                text,
                font,
                glyph_font.spacing_px,
                (width, height),
            )
    return image


def png_bytes(image: Image.Image) -> bytes:
    buffer = tempfile.SpooledTemporaryFile()
    image.save(buffer, format="PNG", compress_level=9, optimize=False)
    buffer.seek(0)
    data = buffer.read()
    buffer.close()
    return data


def checked_png(data: bytes, expected_size: tuple[int, int]) -> None:
    import io

    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RenderError("generated image lacks the PNG signature")
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        if image.size != expected_size or image.mode != "RGB":
            raise RenderError(
                f"generated PNG is {image.mode} {image.size}, expected RGB {expected_size}"
            )


def crop_box_for(name: str, geometry: Mapping[str, Any]) -> Box:
    layer_sets = {
        "grid": set(range(1, 46)),
        "track_cluster": set(range(46, 94)),
        "transport": set(range(118, 143)) | {148},
        "fader": set(range(94, 102)) | {143},
        "rotary": set(range(102, 118)) | {145, 148},
        "navigation": set(range(126, 141)) | {147},
        "crossfader": {144},
    }
    boxes: list[Box] = []
    for record in geometry["controls"].values():
        if record["layer"] not in layer_sets[name]:
            continue
        for field in ("body_box", "label_box", "motion_box"):
            box = record_box(record, field)
            if box:
                boxes.append(box)
        if record.get("ring"):
            boxes.append(Box(*record["ring"]["box"]))
    union = box_union(boxes).expand(12)
    return Box(
        max(0, union.left),
        max(0, union.top),
        min(CANVAS[0], union.right),
        min(CANVAS[1], union.bottom),
    )


def add_simulation(overlay: Image.Image) -> dict[str, Any]:
    patches = {
        "black": (0, 0, 0),
        "gray18": (46, 46, 46),
        "saturated_red": (220, 18, 18),
        "saturated_green": (18, 220, 18),
        "saturated_blue": (18, 18, 220),
    }
    extrema = overlay.getextrema()
    peak = [channel[1] for channel in extrema]
    results: dict[str, Any] = {}
    for name, patch in patches.items():
        result = [min(255, patch[index] + peak[index]) for index in range(3)]
        results[name] = {
            "background_rgb": list(patch),
            "overlay_peak_rgb": peak,
            "expected_peak_rgb": result,
            "clipped_channels": [
                index for index in range(3) if patch[index] + peak[index] > 255
            ],
        }
    return results


def verify_text_metrics(metrics: Sequence[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    for metric in metrics:
        outer = Box(*metric["box"])
        ink = Box(*metric["ink_box"])
        if not contains(outer, ink):
            failures.append(f"layer {metric['layer']} {metric['role']} ink escapes its box")
        if metric["role"] == "name" and metric["rendered_ink_px"][1] < 12:
            failures.append(f"layer {metric['layer']} name raster is under 12 px high")
        if metric["role"] == "address" and metric["rendered_ink_px"][1] < 9:
            failures.append(f"layer {metric['layer']} address raster is under 9 px high")
    return failures


def artifact_key(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def load_accepted_measurement(
    measurement_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Validate a live measurement against the currently published B0 set."""

    measurement_bytes = require_file(measurement_path, "live tag measurement")
    try:
        measurement = json.loads(measurement_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderError(f"measurement is not valid UTF-8 JSON: {measurement_path}") from exc
    if not isinstance(measurement, Mapping) or measurement.get("schema_version") != 1:
        raise RenderError("measurement must be a schema_version 1 JSON object")
    parent_manifest_path = output_dir / ARTIFACT_NAMES["build_manifest"]
    parent_bytes = require_file(parent_manifest_path, "provisional build manifest")
    try:
        parent_manifest = json.loads(parent_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderError("published provisional build manifest is invalid") from exc
    if parent_manifest.get("status") != "provisional":
        raise RenderError("measurement parent must be a published provisional B0 build")
    parent_build_id = str(parent_manifest.get("build_id", ""))
    observed_build_id = measurement.get("build_id")
    if not isinstance(observed_build_id, str) or not observed_build_id:
        raise RenderError("measurement must name its observed B0 build_id")
    if observed_build_id != parent_build_id:
        raise RenderError(
            f"measurement observes {observed_build_id!r}, not current parent {parent_build_id!r}"
        )
    observed_hashes = measurement.get("measurement_parent_artifact_hashes")
    if not isinstance(observed_hashes, Mapping):
        raise RenderError("measurement must contain its observed B0 artifact hashes")
    parent_artifacts = parent_manifest.get("artifacts")
    if not isinstance(parent_artifacts, Mapping):
        raise RenderError("provisional build manifest lacks its artifact hash table")
    parent_by_basename = {Path(key).name: (key, value) for key, value in parent_artifacts.items()}
    required = {
        ARTIFACT_NAMES["geometry"],
        ARTIFACT_NAMES["calibration"],
        ARTIFACT_NAMES["live_controls"],
        ARTIFACT_NAMES["overlay"],
    }
    observed_basenames = {Path(str(key)).name for key in observed_hashes}
    if not required <= observed_basenames:
        raise RenderError(
            "measurement must bind geometry, calibration, live-controls, and overlay B0 hashes"
        )
    normalized_hashes: dict[str, dict[str, Any]] = {}
    for observed_key, observed_value in observed_hashes.items():
        basename = Path(str(observed_key)).name
        if basename not in parent_by_basename:
            raise RenderError(f"measurement names unknown B0 artifact {observed_key!r}")
        parent_key, parent_value = parent_by_basename[basename]
        observed_sha = (
            observed_value.get("sha256")
            if isinstance(observed_value, Mapping)
            else observed_value
        )
        if observed_sha != parent_value.get("sha256"):
            raise RenderError(f"measurement hash mismatch for {basename}")
        live_path = output_dir / basename
        if not live_path.is_file() or sha256_file(live_path) != observed_sha:
            raise RenderError(f"published B0 artifact drifted before acceptance: {basename}")
        normalized_hashes[parent_key] = {
            "sha256": observed_sha,
            "bytes": int(parent_value["bytes"]),
        }
    metrics = measurement.get("accepted_live_tag_metrics")
    if not isinstance(metrics, Mapping) or not metrics:
        raise RenderError("measurement lacks accepted live tag metrics")
    validate_accepted_live_tag_metrics(metrics)
    selected_size = measurement.get("selected_avenue_size")
    if (
        not isinstance(selected_size, (int, float))
        or isinstance(selected_size, bool)
        or not math.isfinite(float(selected_size))
    ):
        raise RenderError("measurement lacks a finite selected Avenue Size")
    minimum_size, maximum_size = LIVE_SIZE_RANGE
    if not minimum_size <= float(selected_size) <= maximum_size:
        raise RenderError(
            f"selected Avenue Size must be within {minimum_size}..{maximum_size}"
        )
    return {
        "bytes": measurement_bytes,
        "sha256": sha256_bytes(measurement_bytes),
        "parent_build_id": parent_build_id,
        "parent_artifact_hashes": normalized_hashes,
        "metrics": metrics,
        "selected_size": float(selected_size),
        "path": measurement_path,
    }


def atomic_write(path: Path, data: bytes, validator: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        validator(data)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def validate_json_bytes(data: bytes) -> None:
    json.loads(data.decode("utf-8"))


def build_artifacts(
    manifest_path: Path,
    svg_path: Path,
    output_dir: Path,
    label_font_path: Path,
    glyph_font_path: Path,
    fallback_glyph_font_path: Path,
    measurement_path: Path | None = None,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    controls, manifest_bytes = load_manifest(manifest_path)
    svg_bytes = require_file(svg_path, "physical SVG")
    if b"<svg" not in svg_bytes[:1024]:
        raise RenderError(f"physical SVG does not look like SVG: {svg_path}")
    require_file(label_font_path, "label font")
    glyph_font = choose_glyph_font(controls, glyph_font_path, fallback_glyph_font_path)
    measurement = (
        load_accepted_measurement(measurement_path, output_dir)
        if measurement_path is not None
        else None
    )
    accepted_metrics = (
        derive_accepted_live_tag_metrics(
            measurement["metrics"],
            glyph_font,
            measurement["selected_size"],
        )
        if measurement
        else None
    )
    seed = canonical_json(
        {
            "renderer_version": RENDERER_VERSION,
            "manifest_sha256": sha256_bytes(manifest_bytes),
            "svg_sha256": sha256_bytes(svg_bytes),
            "label_font_sha256": sha256_file(label_font_path),
            "glyph_font_sha256": sha256_file(glyph_font.path),
            "glyph_family": glyph_font.live_family,
            "glyph_size": glyph_font.size_px,
            "parent_build_id": measurement["parent_build_id"] if measurement else None,
            "measurement_sha256": measurement["sha256"] if measurement else None,
        }
    )
    build_id = ("B1-" if measurement else "B0-") + sha256_bytes(seed)[:16]
    geometry = build_geometry(controls, label_font_path, glyph_font, build_id)
    calibration = build_calibration(
        geometry,
        glyph_font,
        build_id,
        status="accepted" if measurement else "provisional",
        parent_build_id=measurement["parent_build_id"] if measurement else None,
        measurement_sha256=measurement["sha256"] if measurement else None,
        measurement_parent_artifact_hashes=measurement["parent_artifact_hashes"]
        if measurement
        else None,
        accepted_live_tag_metrics=accepted_metrics,
    )
    live_controls = build_live_controls(
        controls,
        geometry,
        glyph_font,
        build_id,
        status="accepted" if measurement else "provisional",
        accepted_size=measurement["selected_size"] if measurement else None,
    )
    overlay, text_metrics = draw_overlay(controls, geometry, label_font_path)
    debug = draw_debug(
        overlay,
        geometry,
        glyph_font,
        accepted_metrics,
    )
    text_failures = verify_text_metrics(text_metrics)
    corners = [overlay.getpixel(point) for point in ((0, 0), (1919, 0), (0, 1079), (1919, 1079))]
    if any(pixel != (0, 0, 0) for pixel in corners):
        raise RenderError("overlay corners are not true black")
    if text_failures:
        raise RenderError("; ".join(text_failures[:8]))
    if max(channel[1] for channel in overlay.getextrema()) == 255:
        raise RenderError("overlay has a clipped 255-valued channel")

    artifacts: dict[Path, bytes] = {
        output_dir / ARTIFACT_NAMES["geometry"]: canonical_json(geometry),
        output_dir / ARTIFACT_NAMES["calibration"]: canonical_json(calibration),
        output_dir / ARTIFACT_NAMES["live_controls"]: canonical_json(live_controls),
        output_dir / ARTIFACT_NAMES["overlay"]: png_bytes(overlay),
        output_dir / ARTIFACT_NAMES["debug"]: png_bytes(debug),
    }
    crop_records: dict[str, Any] = {}
    for crop_name in CROP_NAMES:
        crop_box = crop_box_for(crop_name, geometry)
        crop = overlay.crop(crop_box.as_list())
        crop_path = output_dir / f"APC40_visual_qa_crop_{crop_name}.png"
        artifacts[crop_path] = png_bytes(crop)
        crop_records[crop_name] = {
            "path": artifact_key(crop_path),
            "box": crop_box.as_list(),
            "size": [crop_box.width, crop_box.height],
        }
    report = {
        "schema_version": SCHEMA_VERSION,
        "build_id": build_id,
        "status": "accepted" if measurement else "provisional",
        "renderer_version": RENDERER_VERSION,
        "inputs": {
            "manifest": str(manifest_path.resolve()),
            "manifest_sha256": sha256_bytes(manifest_bytes),
            "physical_svg": str(svg_path.resolve()),
            "physical_svg_sha256": sha256_bytes(svg_bytes),
            "measurement": str(measurement["path"].resolve()) if measurement else None,
            "measurement_sha256": measurement["sha256"] if measurement else None,
        },
        "counts": {"controls": 148, "notes": 120, "cc": 28},
        "fonts": geometry["fonts"],
        "checks": {
            "geometry": "pass",
            "true_black_corners": "pass",
            "text_ink_containment": "pass",
            "contrast_minimum": 3.0,
            "minimum_active_contrast": round(
                min(contrast_on_black(record["active_rgb"]) for record in geometry["controls"].values()),
                4,
            ),
            "structural_peak_below_255": "pass",
            "moving_tags_fit_92x42": "pass",
            "moving_tag_metric_source": (
                "accepted_live_tag_metrics" if measurement else "offline_tag_metrics"
            ),
            "legacy_generic_dispatch_absent": "pass",
        },
        "moving_tag_travel": {
            layer: calibration["motion_ranges_by_layer"][layer]["geometry"]["travel_px"]
            for layer in [*(str(value) for value in range(94, 102)), "143", "144"]
        },
        "add_simulation": add_simulation(overlay),
        "text_metrics": text_metrics,
        "crops": crop_records,
    }
    report_path = output_dir / ARTIFACT_NAMES["report"]
    artifacts[report_path] = canonical_json(report)
    forbidden_dispatch_marker = b"connect_" + b"continuous"
    contaminated = [
        path.name
        for path, data in artifacts.items()
        if forbidden_dispatch_marker in data
    ]
    if contaminated:
        raise RenderError(
            "generated artifacts contain the retired generic dispatcher marker: "
            + ", ".join(sorted(contaminated))
        )

    for path, data in artifacts.items():
        if path.suffix.lower() == ".png":
            expected = CANVAS if path.name in {
                ARTIFACT_NAMES["overlay"],
                ARTIFACT_NAMES["debug"],
            } else tuple(next(
                record["size"] for record in crop_records.values() if Path(record["path"]).name == path.name
            ))
            checked_png(data, expected)  # type: ignore[arg-type]
        else:
            validate_json_bytes(data)
    build_manifest = {
        "schema_version": SCHEMA_VERSION,
        "build_id": build_id,
        "status": "accepted" if measurement else "provisional",
        "parent_build_id": measurement["parent_build_id"] if measurement else None,
        "measurement_sha256": measurement["sha256"] if measurement else None,
        "artifacts": {
            artifact_key(path): {"sha256": sha256_bytes(data), "bytes": len(data)}
            for path, data in sorted(artifacts.items(), key=lambda item: artifact_key(item[0]))
        },
    }
    return artifacts, build_manifest


def write_artifacts(artifacts: Mapping[Path, bytes], build_manifest: Mapping[str, Any], output_dir: Path) -> None:
    for path, data in sorted(artifacts.items(), key=lambda item: artifact_key(item[0])):
        if path.suffix.lower() == ".png":
            import io

            def validator(payload: bytes) -> None:
                with Image.open(io.BytesIO(payload)) as image:
                    image.load()
                    if image.mode != "RGB":
                        raise RenderError(f"{path.name} is not RGB")

            atomic_write(path, data, validator)
        else:
            atomic_write(path, data, validate_json_bytes)
    # The checksum/build-ID manifest is deliberately the final publication.
    manifest_path = output_dir / ARTIFACT_NAMES["build_manifest"]
    atomic_write(manifest_path, canonical_json(build_manifest), validate_json_bytes)


def check_determinism(
    manifest_path: Path,
    svg_path: Path,
    output_dir: Path,
    label_font_path: Path,
    glyph_font_path: Path,
    fallback_glyph_font_path: Path,
    measurement_path: Path | None = None,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    arguments = (
        manifest_path,
        svg_path,
        output_dir,
        label_font_path,
        glyph_font_path,
        fallback_glyph_font_path,
        measurement_path,
    )
    first_artifacts, first_manifest = build_artifacts(*arguments)
    second_artifacts, second_manifest = build_artifacts(*arguments)
    if first_manifest != second_manifest or first_artifacts != second_artifacts:
        raise RenderError("identical inputs did not produce byte-identical artifacts")
    return first_artifacts, first_manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--physical-svg", type=Path, default=DEFAULT_SVG)
    parser.add_argument("--output-dir", type=Path, default=DOCS)
    parser.add_argument("--label-font", type=Path, default=DEFAULT_LABEL_FONT)
    parser.add_argument("--glyph-font", type=Path, default=DEFAULT_GLYPH_FONT)
    parser.add_argument("--fallback-glyph-font", type=Path, default=DEFAULT_FALLBACK_GLYPH_FONT)
    parser.add_argument(
        "--measurement",
        type=Path,
        help=(
            "accepted live tag measurement; validates the currently published B0 "
            "artifact hashes and emits a lineage-bound B1 set"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="build twice in memory, validate, and write nothing",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts, build_manifest = check_determinism(
        args.manifest.resolve(),
        args.physical_svg.resolve(),
        args.output_dir.resolve(),
        args.label_font.resolve(),
        args.glyph_font.resolve(),
        args.fallback_glyph_font.resolve(),
        args.measurement.resolve() if args.measurement else None,
    )
    if args.check:
        print(
            f"CHECK PASS {build_manifest['build_id']} "
            f"({len(artifacts)} staged artifacts; no files written)"
        )
        return 0
    write_artifacts(artifacts, build_manifest, args.output_dir.resolve())
    print(
        f"WROTE {build_manifest['build_id']} "
        f"({len(artifacts) + 1} artifacts; build manifest published last)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
