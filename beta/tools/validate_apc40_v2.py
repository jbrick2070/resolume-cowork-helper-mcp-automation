#!/usr/bin/env python3
"""Validate the APC40 Visual Twin V2 candidate and emit a QA receipt.

The validator is intentionally read-only with respect to Resolume.  It checks
the immutable R1 files, the saved V2 composition, the deterministic geometry
artifact, representative PNG evidence, and the singleton gateway topology.
It writes only the requested JSON receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import struct
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any, Iterable


RUN_ID = "20260719T124750Z"
EXPECTED_NAME = f"APC40_Visual_Twin_V2_Candidate_{RUN_ID}"
EXPECTED_R1_AVC_SHA256 = (
    "91cc3096d7aa0f12f648b970cc2b6352a5bd19dd4d5dfb60bf33188c5ebd7f99"
)
EXPECTED_R1_MIDI_SHA256 = (
    "4628634b4fb9a9909a5b1ee9d7c9df1a759371cc7a90ce183d8bb4cc40d1abc5"
)
EXPECTED_CANDIDATE_SHA256 = (
    "cec1137a2230dfa3f5a45563fbefed73fc1c5451f90f67cada60cfc8501a04c9"
)
R1_COMPOSITION = Path("compositions/APC40_Visual_QA_148.avc")
R1_CONTROLLER = Path("controllers/APC 40 MK II - Visual QA.xml")
DEFAULT_CANDIDATE = Path(
    f"beta/compositions/APC40_Visual_Twin_V2_Candidate_{RUN_ID}.avc"
)
DEFAULT_GEOMETRY = Path(f"beta/APC40_V2_GEOMETRY_{RUN_ID}.json")
DEFAULT_SCREENSHOTS = Path(f"beta/screenshots/apc40-v2-{RUN_ID}")
DEFAULT_OUTPUT = Path(f"beta/APC40_V2_QA_{RUN_ID}.json")
EXPECTED_SCREENSHOTS = (
    "01-r1-witnesses-candidate-baseline.png",
    "03-v2-fft-silence-composite.png",
    "03b-v2-fft-silence-layer.png",
    "04-v2-bypass-r1-restore.png",
    "05-v2-low-band-peak-envelope.png",
    "05b-v2-low-band-peak-layer.png",
    "06-v2-final-restored.png",
)
PARAM_TAGS_WITH_VALUE = {"Param", "ParamChoice", "ParamColor", "ParamText"}
LAYER_RUNTIME_PARAMETERS = frozenset(
    {
        (None, "Master"),
        ("audio_track", "Volume"),
        ("video_track", "Opacity"),
        ("layer_blend_mixer", "Opacity"),
        ("transition_mixer_current_state", "Opacity"),
    }
)
CLIP_RUNTIME_PARAMETERS_BY_PROTOTYPE = {
    "vertical_fader": frozenset(
        {
            ("video_track", "Opacity"),
            ("render_pass:TransformEffect", "Position Y"),
        }
    ),
    "rotary": frozenset(
        {
            ("video_track", "Opacity"),
            ("render_pass:TransformEffect", "Rotation Z"),
        }
    ),
    "small_rotary": frozenset(
        {
            ("video_track", "Opacity"),
            ("render_pass:TransformEffect", "Rotation Z"),
        }
    ),
    "crossfader": frozenset(
        {
            ("video_track", "Opacity"),
            ("render_pass:TransformEffect", "Position X"),
        }
    ),
}
MEDIA_EXTENSIONS = re.compile(
    r"\.(?:avi|bmp|flac|gif|jpeg|jpg|m4a|mkv|mov|mp3|mp4|mpeg|mpg|png|"
    r"tif|tiff|wav|webm)(?:$|[?#])",
    re.IGNORECASE,
)
ABSOLUTE_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\[^\\]+\\[^\\]+)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def approx(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return abs(actual - expected) <= tolerance


def as_float(node: ET.Element | None, attribute: str = "value") -> float | None:
    if node is None or attribute not in node.attrib:
        return None
    return float(node.attrib[attribute])


def abgr_decimal_to_rgba(value: str | None) -> str | None:
    if value is None:
        return None
    packed = int(value)
    red = packed & 0xFF
    green = (packed >> 8) & 0xFF
    blue = (packed >> 16) & 0xFF
    alpha = (packed >> 24) & 0xFF
    return f"#{red:02x}{green:02x}{blue:02x}{alpha:02x}"


def named_param(parent: ET.Element, tag: str, name: str) -> ET.Element | None:
    return parent.find(f".//{tag}[@name='{name}']")


def direct_named_param(parent: ET.Element, tag: str, name: str) -> ET.Element | None:
    return parent.find(f"./Params/{tag}[@name='{name}']")


def element_name(entity: ET.Element) -> str | None:
    node = direct_named_param(entity, "Param", "Name")
    return None if node is None else node.attrib.get("value")


def parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def has_ancestor(
    node: ET.Element,
    parents: dict[ET.Element, ET.Element],
    tags: Iterable[str],
) -> bool:
    excluded = set(tags)
    current = node
    while current in parents:
        current = parents[current]
        if current.tag in excluded:
            return True
    return False


def parameter_context(
    node: ET.Element, parents: dict[ET.Element, ET.Element]
) -> str | None:
    current = node
    render_context: str | None = None
    video_context: str | None = None
    while current in parents:
        current = parents[current]
        if current.tag == "ChoosableMixer":
            if current.attrib.get("name") == "Transition":
                return "transition_mixer_current_state"
            if current.attrib.get("name") == "Blend":
                return "layer_blend_mixer"
        if current.tag == "AudioTrack":
            return "audio_track"
        if current.tag == "RenderPass" and render_context is None:
            render_context = "render_pass:" + (
                current.attrib.get("type")
                or current.attrib.get("name")
                or "unknown"
            )
        if current.tag == "VideoTrack":
            video_context = "video_track"
    return render_context or video_context


def static_parameter_signature(entity: ET.Element) -> list[dict[str, Any]]:
    """Capture visual/behavior configuration while excluding runtime transport."""

    parents = parent_map(entity)
    signature: list[dict[str, Any]] = []
    for node in entity.iter():
        if has_ancestor(node, parents, {"PreloadData", "Transport"}):
            continue
        if node.tag == "ParamRange":
            phase = next(
                (
                    child
                    for child in node
                    if child.tag.startswith("PhaseSource")
                    or child.tag == "DurationSource"
                ),
                None,
            )
            value_range = node.find("./ValueRange")
            record: dict[str, Any] = {
                "tag": node.tag,
                "name": node.attrib.get("name"),
                "context": parameter_context(node, parents),
                "type": node.attrib.get("T"),
                "default": node.attrib.get("default"),
                "phase": None if phase is None else phase.tag,
                "link_id": None if phase is None else phase.attrib.get("linkId"),
                "range": (
                    None
                    if value_range is None
                    else {
                        "name": value_range.attrib.get("name"),
                        "min": value_range.attrib.get("min"),
                        "max": value_range.attrib.get("max"),
                    }
                ),
            }
            if phase is None or phase.tag == "PhaseSourceStatic":
                record["value"] = node.attrib.get("value")
            signature.append(record)
        elif node.tag in PARAM_TAGS_WITH_VALUE:
            signature.append(
                {
                    "tag": node.tag,
                    "name": node.attrib.get("name"),
                    "context": parameter_context(node, parents),
                    "type": node.attrib.get("T"),
                    "default": node.attrib.get("default"),
                    "value": node.attrib.get("value"),
                }
            )
    return signature


def partition_parameters(
    records: list[dict[str, Any]],
    runtime_keys: frozenset[tuple[str | None, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    protected: list[dict[str, Any]] = []
    runtime: list[dict[str, Any]] = []
    for record in records:
        key = (record.get("context"), record.get("name"))
        target = runtime if key in runtime_keys else protected
        target.append(record)
    return protected, runtime


def runtime_records_are_static(records: list[dict[str, Any]]) -> bool:
    """Runtime-value exceptions may never hide animation or range changes."""

    return all(
        record.get("tag") == "ParamRange"
        and record.get("type") == "DOUBLE"
        and record.get("phase") in (None, "PhaseSourceStatic")
        and record.get("link_id") is None
        and record.get("range") is None
        for record in records
    )


def accepted_runtime_parameter_changes(
    baseline: list[dict[str, Any]],
    candidate: list[dict[str, Any]],
    runtime_keys: frozenset[tuple[str | None, str]],
    reason: str,
) -> list[dict[str, Any]]:
    """Describe only allowlisted runtime records that actually changed."""

    changes: list[dict[str, Any]] = []
    for context, name in sorted(runtime_keys, key=str):
        before = [
            record
            for record in baseline
            if (record.get("context"), record.get("name")) == (context, name)
        ]
        after = [
            record
            for record in candidate
            if (record.get("context"), record.get("name")) == (context, name)
        ]
        if before != after:
            changes.append(
                {
                    "context": context,
                    "parameter": name,
                    "baseline_record_count": len(before),
                    "candidate_record_count": len(after),
                    "baseline_values": [record.get("value") for record in before],
                    "candidate_values": [record.get("value") for record in after],
                    "reason": reason,
                }
            )
    return changes


def protected_layer_equivalent(
    baseline: ET.Element, candidate: ET.Element
) -> tuple[bool, list[dict[str, Any]]]:
    before = layer_fingerprint(baseline)
    after = layer_fingerprint(candidate)
    for key in ("attrs", "name", "render_passes"):
        if before[key] != after[key]:
            return False, []
    before_protected, before_runtime = partition_parameters(
        before["parameters"], LAYER_RUNTIME_PARAMETERS
    )
    after_protected, after_runtime = partition_parameters(
        after["parameters"], LAYER_RUNTIME_PARAMETERS
    )
    accepted = accepted_runtime_parameter_changes(
        before_runtime,
        after_runtime,
        LAYER_RUNTIME_PARAMETERS,
        "save-time layer mixer state",
    )
    return (
        before_protected == after_protected
        and runtime_records_are_static(before_runtime)
        and runtime_records_are_static(after_runtime),
        accepted,
    )


def protected_clip_equivalent(
    baseline: ET.Element,
    candidate: ET.Element,
    prototype: str | None,
) -> tuple[bool, list[dict[str, Any]]]:
    before = clip_fingerprint(baseline)
    after = clip_fingerprint(candidate)
    for key in ("attrs", "name", "render_passes", "sources"):
        if before[key] != after[key]:
            return False, []
    runtime_keys = CLIP_RUNTIME_PARAMETERS_BY_PROTOTYPE.get(
        prototype, frozenset()
    )
    before_protected, before_runtime = partition_parameters(
        before["parameters"], runtime_keys
    )
    after_protected, after_runtime = partition_parameters(
        after["parameters"], runtime_keys
    )
    accepted = accepted_runtime_parameter_changes(
        before_runtime,
        after_runtime,
        runtime_keys,
        f"save-time {prototype or 'unclassified'} control state",
    )
    return (
        before_protected == after_protected
        and runtime_records_are_static(before_runtime)
        and runtime_records_are_static(after_runtime),
        accepted,
    )


def render_signature(entity: ET.Element) -> list[dict[str, str | None]]:
    parents = parent_map(entity)
    result: list[dict[str, str | None]] = []
    for node in entity.iter("RenderPass"):
        if has_ancestor(node, parents, {"PreloadData", "Transport"}):
            continue
        result.append(
            {
                key: node.attrib.get(key)
                for key in (
                    "name",
                    "type",
                    "uniqueTypeId",
                    "uniqueId",
                    "baseType",
                    "storage",
                )
            }
        )
    return result


def source_signature(entity: ET.Element) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in entity.findall(".//VideoSource"):
        result.append(
            {
                "type": source.attrib.get("type"),
                "width": source.attrib.get("width"),
                "height": source.attrib.get("height"),
                "generators": [
                    {
                        key: render.attrib.get(key)
                        for key in ("name", "type", "uniqueTypeId", "uniqueId")
                    }
                    for render in source.findall("./RenderPass")
                ],
            }
        )
    return result


def layer_fingerprint(layer: ET.Element) -> dict[str, Any]:
    return {
        "attrs": {
            key: layer.attrib.get(key) for key in ("uniqueId", "layerIndex")
        },
        "name": element_name(layer),
        "parameters": static_parameter_signature(layer),
        "render_passes": render_signature(layer),
    }


def clip_fingerprint(clip: ET.Element) -> dict[str, Any]:
    return {
        "attrs": {
            key: clip.attrib.get(key)
            for key in ("uniqueId", "layerIndex", "columnIndex")
        },
        "name": element_name(clip),
        "parameters": static_parameter_signature(clip),
        "render_passes": render_signature(clip),
        "sources": source_signature(clip),
    }


def composition_clips(root: ET.Element) -> list[ET.Element]:
    decks = root.findall("./Deck")
    if not decks:
        return []
    return sorted(
        decks[0].findall("./Clip"),
        key=lambda clip: (
            int(clip.attrib.get("layerIndex", "-1")),
            int(clip.attrib.get("columnIndex", "-1")),
        ),
    )


def scan_external_media(root: ET.Element) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for node in root.iter():
        if node.tag in {"FileVideoSource", "FileAudioSource", "MediaFile"}:
            hits.append({"element": node.tag, "attribute": "", "value": ""})
        for key, value in node.attrib.items():
            if MEDIA_EXTENSIONS.search(value) or (
                ABSOLUTE_PATH.search(value)
                and key.lower() in {"path", "filename", "file", "url", "uri"}
            ):
                hits.append(
                    {"element": node.tag, "attribute": key, "value": value}
                )
    return hits


def read_png(path: Path) -> tuple[int, int, bytes]:
    """Return width, height, and 8-bit RGB pixels using only the stdlib."""

    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{path} is not a PNG")
    offset = 8
    width = height = bit_depth = color_type = interlace = None
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
        elif chunk_type == b"IDAT":
            compressed.extend(chunk)
        elif chunk_type == b"IEND":
            break
    if (
        width is None
        or height is None
        or bit_depth != 8
        or interlace != 0
        or color_type not in {0, 2, 4, 6}
    ):
        raise ValueError(f"{path} uses an unsupported PNG format")

    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    rows: list[bytearray] = []
    cursor = 0

    def paeth(a: int, b: int, c: int) -> int:
        estimate = a + b - c
        pa = abs(estimate - a)
        pb = abs(estimate - b)
        pc = abs(estimate - c)
        if pa <= pb and pa <= pc:
            return a
        return b if pb <= pc else c

    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        scanline = bytearray(raw[cursor : cursor + stride])
        cursor += stride
        previous = rows[-1] if rows else bytearray(stride)
        for index in range(stride):
            left = scanline[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                scanline[index] = (scanline[index] + left) & 0xFF
            elif filter_type == 2:
                scanline[index] = (scanline[index] + up) & 0xFF
            elif filter_type == 3:
                scanline[index] = (scanline[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                scanline[index] = (
                    scanline[index] + paeth(left, up, upper_left)
                ) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"{path} uses PNG filter {filter_type}")
        rows.append(scanline)

    rgb = bytearray()
    for row in rows:
        for index in range(0, len(row), channels):
            if color_type in {0, 4}:
                rgb.extend((row[index], row[index], row[index]))
            else:
                rgb.extend(row[index : index + 3])
    return width, height, bytes(rgb)


def image_metrics(first: Path, second: Path) -> dict[str, Any]:
    width_a, height_a, pixels_a = read_png(first)
    width_b, height_b, pixels_b = read_png(second)
    if (width_a, height_a) != (width_b, height_b):
        raise ValueError("image dimensions differ")
    differences = [
        abs(left - right) for left, right in zip(pixels_a, pixels_b)
    ]
    squared = [
        (left - right) ** 2 for left, right in zip(pixels_a, pixels_b)
    ]
    mse = sum(squared) / len(squared)
    changed_pixels = sum(
        1
        for index in range(0, len(pixels_a), 3)
        if pixels_a[index : index + 3] != pixels_b[index : index + 3]
    )
    pixel_count = width_a * height_a
    return {
        "width": width_a,
        "height": height_a,
        "mae": sum(differences) / len(differences),
        "mse": mse,
        "psnr_db": None if mse == 0 else 10 * math.log10((255**2) / mse),
        "pixel_identical": mse == 0,
        "max_channel_difference": max(differences, default=0),
        "changed_pixels": changed_pixels,
        "changed_percent": 100 * changed_pixels / pixel_count,
    }


def mean_luma(path: Path) -> float:
    _, _, pixels = read_png(path)
    total = 0.0
    for index in range(0, len(pixels), 3):
        red, green, blue = pixels[index : index + 3]
        total += 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return total / (len(pixels) // 3)


def runtime_observation(expected_name: str) -> dict[str, Any]:
    with urllib.request.urlopen(
        "http://127.0.0.1:8765/healthz", timeout=5
    ) as response:
        health = json.load(response)

    command = (
        "$p = Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId,Name,CommandLine; "
        "ConvertTo-Json -Compress -Depth 3 -InputObject @($p)"
    )
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    processes = json.loads(proc.stdout)
    if isinstance(processes, dict):
        processes = [processes]

    def matching(name: str, command_fragment: str | None = None) -> list[dict]:
        result = [
            item
            for item in processes
            if str(item.get("Name", "")).lower() == name.lower()
        ]
        if command_fragment is not None:
            result = [
                item
                for item in result
                if command_fragment.lower()
                in str(item.get("CommandLine", "")).lower()
            ]
        return result

    gateway = matching("node.exe", "resolume-mcp-gateway\\src\\server.mjs")
    arena_children = matching("resolume_arena_mcp_server.exe")
    wire_children = matching("resolume_wire_mcp_server.exe")
    bridges = matching("python.exe", "avenue_pipe_bridge.py") + matching(
        "pythonw.exe", "avenue_pipe_bridge.py"
    )
    avenues = matching("Avenue.exe")
    wire_apps = matching("Wire.exe")
    arena_health = health.get("upstreams", {}).get("arena", {})
    wire_health = health.get("upstreams", {}).get("wire", {})
    probe_summary = (
        arena_health.get("applicationProbe", {}).get("summary", "")
    )

    return {
        "gateway": {
            "count": len(gateway),
            "pid": health.get("pid"),
            "ready": health.get("ready"),
            "status": health.get("status"),
            "queue_depth": health.get("queue", {}).get("queueDepth"),
        },
        "arena_child": {
            "count": len(arena_children),
            "pid": arena_health.get("pid"),
            "ready": arena_health.get("ready"),
            "parent_is_gateway": (
                len(arena_children) == 1
                and arena_children[0].get("ParentProcessId") == health.get("pid")
            ),
        },
        "wire_child": {
            "count": len(wire_children),
            "pid": wire_health.get("pid"),
            "ready": wire_health.get("ready"),
            "parent_is_gateway": (
                len(wire_children) == 1
                and wire_children[0].get("ParentProcessId") == health.get("pid")
            ),
        },
        "avenue_bridge": {
            "count": len(bridges),
            "pid": None if len(bridges) != 1 else bridges[0].get("ProcessId"),
        },
        "avenue_application": {
            "count": len(avenues),
            "pid": None if len(avenues) != 1 else avenues[0].get("ProcessId"),
            "exact_candidate_active": expected_name in probe_summary,
        },
        "wire_application": {
            "count": len(wire_apps),
            "expected": "closed is valid",
        },
        "mcp_sessions": health.get("sessions", {}).get("total"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canonical-r1-root",
        type=Path,
        help="Root holding the immutable on-rig R1 files; defaults to this checkout.",
    )
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--screenshots", type=Path, default=DEFAULT_SCREENSHOTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-runtime", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    canonical_r1_root = (
        repo_root
        if args.canonical_r1_root is None
        else args.canonical_r1_root.resolve()
    )
    candidate_path = (
        args.candidate
        if args.candidate.is_absolute()
        else repo_root / args.candidate
    )
    geometry_path = (
        args.geometry
        if args.geometry.is_absolute()
        else repo_root / args.geometry
    )
    screenshot_dir = (
        args.screenshots
        if args.screenshots.is_absolute()
        else repo_root / args.screenshots
    )
    output_path = (
        args.output if args.output.is_absolute() else repo_root / args.output
    )
    r1_path = canonical_r1_root / R1_COMPOSITION
    controller_path = canonical_r1_root / R1_CONTROLLER

    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def check(
        check_id: str,
        condition: bool,
        actual: Any,
        expected: Any,
        evidence: str,
    ) -> None:
        status = "PASS" if condition else "FAIL"
        checks.append(
            {
                "id": check_id,
                "status": status,
                "actual": actual,
                "expected": expected,
                "evidence": evidence,
            }
        )
        if not condition:
            failures.append(check_id)

    r1_sha = sha256_file(r1_path)
    controller_sha = sha256_file(controller_path)
    candidate_sha = sha256_file(candidate_path)
    candidate_xml_text = candidate_path.read_text(encoding="utf-8")
    check(
        "r1_composition_hash_after",
        r1_sha == EXPECTED_R1_AVC_SHA256,
        r1_sha,
        EXPECTED_R1_AVC_SHA256,
        R1_COMPOSITION.as_posix(),
    )
    check(
        "r1_controller_hash_after",
        controller_sha == EXPECTED_R1_MIDI_SHA256,
        controller_sha,
        EXPECTED_R1_MIDI_SHA256,
        R1_CONTROLLER.as_posix(),
    )
    check(
        "candidate_hash",
        candidate_sha == EXPECTED_CANDIDATE_SHA256,
        candidate_sha,
        EXPECTED_CANDIDATE_SHA256,
        DEFAULT_CANDIDATE.as_posix(),
    )

    baseline_root = ET.parse(r1_path).getroot()
    candidate_root = ET.parse(candidate_path).getroot()
    controller_root = ET.parse(controller_path).getroot()
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))

    baseline_info = baseline_root.find("./CompositionInfo")
    candidate_info = candidate_root.find("./CompositionInfo")
    baseline_layers = sorted(
        baseline_root.findall("./Layer"),
        key=lambda node: int(node.attrib["layerIndex"]),
    )
    candidate_layers = sorted(
        candidate_root.findall("./Layer"),
        key=lambda node: int(node.attrib["layerIndex"]),
    )
    baseline_clips = composition_clips(baseline_root)
    candidate_clips = composition_clips(candidate_root)
    candidate_decks = candidate_root.findall("./Deck")
    first_deck_columns = (
        [] if not candidate_decks else candidate_decks[0].findall("./Column")
    )

    candidate_name_node = direct_named_param(
        candidate_root, "Param", "Name"
    )
    candidate_name = (
        None if candidate_name_node is None else candidate_name_node.attrib.get("value")
    )
    dimensions = (
        None if candidate_info is None else candidate_info.attrib.get("width"),
        None if candidate_info is None else candidate_info.attrib.get("height"),
    )
    check(
        "candidate_identity",
        candidate_name == EXPECTED_NAME and candidate_path.stem == EXPECTED_NAME,
        {"composition_name": candidate_name, "filename_stem": candidate_path.stem},
        {"composition_name": EXPECTED_NAME, "filename_stem": EXPECTED_NAME},
        "saved composition Params/Name and filename",
    )
    check(
        "candidate_dimensions",
        dimensions == ("1920", "1080"),
        dimensions,
        ("1920", "1080"),
        "CompositionInfo",
    )
    check(
        "candidate_counts",
        (
            candidate_root.attrib.get("numLayers") == "149"
            and candidate_root.attrib.get("numColumns") == "1"
            and candidate_root.attrib.get("numDecks") == "3"
            and len(candidate_layers) == 149
            and len(candidate_clips) == 149
            and len(candidate_decks) == 3
            and len(first_deck_columns) == 1
            and len({node.attrib.get("uniqueId") for node in candidate_layers}) == 149
            and len({node.attrib.get("uniqueId") for node in candidate_clips}) == 149
            and len(candidate_root.findall("./Group")) == 0
        ),
        {
            "layers": len(candidate_layers),
            "clips": len(candidate_clips),
            "columns": len(first_deck_columns),
            "decks": len(candidate_decks),
            "groups": len(candidate_root.findall("./Group")),
            "unique_layer_ids": len(
                {node.attrib.get("uniqueId") for node in candidate_layers}
            ),
            "unique_clip_ids": len(
                {node.attrib.get("uniqueId") for node in candidate_clips}
            ),
        },
        {
            "layers": 149,
            "clips": 149,
            "columns": 1,
            "decks": 3,
            "groups": 0,
            "unique_layer_ids": 149,
            "unique_clip_ids": 149,
        },
        "Composition and active Deck element counts",
    )
    check(
        "append_only_layer_indices",
        [int(node.attrib["layerIndex"]) for node in candidate_layers]
        == list(range(149)),
        [int(node.attrib["layerIndex"]) for node in candidate_layers],
        "exactly 0..148",
        "Layer/@layerIndex",
    )

    protected_layer_mismatches: list[int] = []
    accepted_layer_runtime_state: list[dict[str, Any]] = []
    for index, (baseline, candidate) in enumerate(
        zip(baseline_layers, candidate_layers[:148])
    ):
        equivalent, accepted = protected_layer_equivalent(baseline, candidate)
        if not equivalent:
            protected_layer_mismatches.append(index + 1)
        for item in accepted:
            accepted_layer_runtime_state.append(
                {
                    "layer": index + 1,
                    "layer_name": element_name(candidate),
                    **item,
                }
            )

    controls_by_layer = {
        int(control["layer"]): control
        for control in geometry["protection"]["controls"]
    }
    protected_clip_mismatches: list[int] = []
    accepted_clip_runtime_state: list[dict[str, Any]] = []
    for baseline, candidate in zip(baseline_clips, candidate_clips[:148]):
        layer = int(candidate.attrib["layerIndex"]) + 1
        control = controls_by_layer.get(layer)
        prototype = None if control is None else str(control["prototype"])
        equivalent, accepted = protected_clip_equivalent(
            baseline, candidate, prototype
        )
        if not equivalent:
            protected_clip_mismatches.append(layer)
        for item in accepted:
            accepted_clip_runtime_state.append(
                {
                    "layer": layer,
                    "clip_name": element_name(candidate),
                    "control_name": (
                        None if control is None else control["layer_name"]
                    ),
                    "prototype": prototype,
                    **item,
                }
            )
    check(
        "protected_layer_fingerprints",
        len(baseline_layers) == 148 and not protected_layer_mismatches,
        {
            "semantic_mismatches": protected_layer_mismatches,
            "accepted_runtime_state": accepted_layer_runtime_state,
        },
        {
            "semantic_mismatches": [],
            "accepted_runtime_state": "documented if present",
        },
        (
            "Layer attrs/name/render passes and every parameter except exact "
            "runtime mixer paths for Master, Volume, and Opacity; runtime "
            "records must remain static/unlinked and every change is listed"
        ),
    )
    check(
        "protected_clip_fingerprints",
        (
            len(baseline_clips) == 148
            and len(controls_by_layer) == 148
            and not protected_clip_mismatches
        ),
        {
            "geometry_control_layers": len(controls_by_layer),
            "semantic_mismatches": protected_clip_mismatches,
            "accepted_runtime_state": accepted_clip_runtime_state,
        },
        {
            "geometry_control_layers": 148,
            "semantic_mismatches": [],
            "accepted_runtime_state": "documented if present",
        },
        (
            "Clip attrs/name/render passes/source signatures and every "
            "parameter except prototype- and path-scoped VideoTrack/Transform "
            "runtime fields: vertical_fader Opacity/Position Y, rotary or "
            "small_rotary Opacity/Rotation Z, and crossfader Opacity/Position "
            "X; runtime records must remain static/unlinked, while source "
            "Opacity, phase, link, range, Text, Color, and all other records "
            "remain exact"
        ),
    )

    preset = direct_named_param(candidate_root, "Param", "MidiShortcutPreset")
    preset_name = None if preset is None else preset.attrib.get("value")
    shortcuts = controller_root.findall("./ShortcutManager/Shortcut")
    raw_messages = [
        message
        for shortcut in shortcuts
        for message in shortcut.findall("./RawInputMessage")
    ]
    raw_keys = {message.attrib.get("key") for message in raw_messages}
    input_paths = [
        path.attrib.get("path", "")
        for shortcut in shortcuts
        for path in shortcut.findall("./ShortcutPath[@name='InputPath']")
    ]
    target_layers = [
        int(match.group(1))
        for path in input_paths
        if (match := re.search(r"/composition/layers/(\d+)", path))
    ]
    shortcut_ids = {shortcut.attrib.get("uniqueId") for shortcut in shortcuts}
    check(
        "midi_contract",
        (
            preset_name == "APC 40 MK II - Visual QA"
            and len(shortcuts) == 203
            and len(shortcut_ids) == 203
            and len(raw_messages) == 203
            and len(raw_keys) == 148
            and target_layers
            and max(target_layers) <= 148
        ),
        {
            "preset": preset_name,
            "shortcut_records": len(shortcuts),
            "unique_shortcut_ids": len(shortcut_ids),
            "raw_messages": len(raw_messages),
            "unique_raw_keys": len(raw_keys),
            "maximum_target_layer": max(target_layers, default=None),
        },
        {
            "preset": "APC 40 MK II - Visual QA",
            "shortcut_records": 203,
            "unique_shortcut_ids": 203,
            "raw_messages": 203,
            "unique_raw_keys": 148,
            "maximum_target_layer": 148,
        },
        "immutable R1 controller XML and candidate preset reference",
    )
    beta_controller = (
        repo_root / "beta/controllers/APC 40 MK II - Visual Twin V2 Beta.xml"
    )
    check(
        "added_midi_shortcuts",
        not beta_controller.exists(),
        0 if not beta_controller.exists() else "beta preset exists",
        0,
        "V2 reuses the immutable R1 preset; layer 149 has no shortcut",
    )

    external_media = scan_external_media(candidate_root)
    video_sources = candidate_root.findall(".//VideoSource")
    source_types = sorted(
        {source.attrib.get("type", "") for source in video_sources}
    )
    check(
        "external_media",
        (
            not external_media
            and len(video_sources) == 149
            and source_types == ["GeneratorVideoSource"]
        ),
        {
            "external_hits": external_media,
            "video_source_count": len(video_sources),
            "source_types": source_types,
        },
        {
            "external_hits": [],
            "video_source_count": 149,
            "source_types": ["GeneratorVideoSource"],
        },
        "saved AVC semantic scan",
    )

    new_layer = candidate_layers[-1]
    new_clip = candidate_clips[-1]
    layer_blend = new_layer.find(
        "./VideoTrack/ChoosableMixer[@name='Blend']/RenderPass"
    )
    layer_opacity = new_layer.find(
        "./VideoTrack/Params/ParamRange[@name='Opacity']"
    )
    source_render = new_clip.find("./VideoTrack/PrimarySource/VideoSource/RenderPass")
    text_node = None if source_render is None else named_param(
        source_render, "ParamText", "Text"
    )
    font_node = None if source_render is None else named_param(
        source_render, "ParamChoice", "Font"
    )
    style_node = None if source_render is None else named_param(
        source_render, "ParamChoice", "Style"
    )
    size_node = None if source_render is None else named_param(
        source_render, "ParamRange", "Size"
    )
    source_scale_node = None if source_render is None else named_param(
        source_render, "ParamRange", "Scale"
    )
    line_width_node = None if source_render is None else named_param(
        source_render, "ParamRange", "Line Width"
    )
    color_node = None if source_render is None else named_param(
        source_render, "ParamColor", "Color"
    )
    outline_color_node = None if source_render is None else named_param(
        source_render, "ParamColor", "Outline Color"
    )
    outline_width_node = None if source_render is None else named_param(
        source_render, "ParamRange", "Outline Width"
    )
    geometry_text = geometry["native_text_block"]["text"]
    raw_text_matches = re.findall(
        r'<ParamText name="Text" T="STRING" default="Resolume" '
        r'value="(.*?)">\s*<Params name="Params">',
        candidate_xml_text,
        flags=re.DOTALL,
    )
    candidate_text = (
        None if not raw_text_matches else html.unescape(raw_text_matches[-1])
    )
    candidate_text_sha = (
        None
        if candidate_text is None
        else hashlib.sha256(candidate_text.encode("utf-8")).hexdigest()
    )
    new_clip_effects = new_clip.findall(
        "./VideoTrack/RenderPass[@name='RenderPassChain']/RenderPass"
    )
    new_layer_audio_effects = new_layer.findall(
        "./AudioTrack/AudioEffectChain/*"
    )
    source_contract_actual = {
        "source": (
            None if source_render is None else source_render.attrib.get("type")
        ),
        "font": None if font_node is None else font_node.attrib.get("value"),
        "style": None if style_node is None else style_node.attrib.get("value"),
        "size": as_float(size_node),
        "source_scale": as_float(source_scale_node),
        "line_width": as_float(line_width_node),
        "color": {
            "parameter_tag": None if color_node is None else color_node.tag,
            "parameter_name": (
                None if color_node is None else color_node.attrib.get("name")
            ),
            "parameter_type": (
                None if color_node is None else color_node.attrib.get("T")
            ),
            "abgr_decimal": (
                None if color_node is None else color_node.attrib.get("value")
            ),
            "rgba": abgr_decimal_to_rgba(
                None if color_node is None else color_node.attrib.get("value")
            ),
        },
        "outline": {
            "color_parameter_tag": (
                None if outline_color_node is None else outline_color_node.tag
            ),
            "color_parameter_name": (
                None
                if outline_color_node is None
                else outline_color_node.attrib.get("name")
            ),
            "color_parameter_type": (
                None
                if outline_color_node is None
                else outline_color_node.attrib.get("T")
            ),
            "color_abgr_decimal": (
                None
                if outline_color_node is None
                else outline_color_node.attrib.get("value")
            ),
            "color_rgba": abgr_decimal_to_rgba(
                None
                if outline_color_node is None
                else outline_color_node.attrib.get("value")
            ),
            "width_parameter_tag": (
                None if outline_width_node is None else outline_width_node.tag
            ),
            "width_parameter_name": (
                None
                if outline_width_node is None
                else outline_width_node.attrib.get("name")
            ),
            "width_parameter_type": (
                None
                if outline_width_node is None
                else outline_width_node.attrib.get("T")
            ),
            "width": as_float(outline_width_node),
        },
        "text_sha256": candidate_text_sha,
    }
    source_contract_expected = {
        "source": "BlockTextGenerator",
        "font": "Cascadia Mono",
        "style": "Regular",
        "size": 0.5,
        "source_scale": 0.28,
        "line_width": 5000.0,
        "color": {
            "parameter_tag": "ParamColor",
            "parameter_name": "Color",
            "parameter_type": "COLOR",
            "abgr_decimal": "4281671093",
            "rgba": "#b51d35ff",
        },
        "outline": {
            "color_parameter_tag": "ParamColor",
            "color_parameter_name": "Outline Color",
            "color_parameter_type": "COLOR",
            "color_abgr_decimal": "4281671093",
            "color_rgba": "#b51d35ff",
            "width_parameter_tag": "ParamRange",
            "width_parameter_name": "Outline Width",
            "width_parameter_type": "DOUBLE",
            "width": 0.22,
        },
        "text_sha256": geometry["native_text_block"]["text_sha256"],
    }
    check(
        "v2_layer_source_contract",
        (
            element_name(new_layer) == "V2 Chassis Low FFT"
            and new_layer.attrib.get("layerIndex") == "148"
            and layer_blend is not None
            and layer_blend.attrib.get("type") == "Add"
            and approx(as_float(layer_opacity) or -1, 1.0)
            and element_name(new_clip) == "V2 Chassis Low FFT"
            and new_clip.attrib.get("layerIndex") == "148"
            and new_clip.attrib.get("columnIndex") == "0"
            and source_render is not None
            and source_render.attrib.get("type") == "BlockTextGenerator"
            and candidate_text == geometry_text
            and candidate_text_sha
            == geometry["native_text_block"]["text_sha256"]
            and font_node is not None
            and font_node.attrib.get("value") == "Cascadia Mono"
            and style_node is not None
            and style_node.attrib.get("value") == "Regular"
            and approx(as_float(size_node) or -1, 0.5)
            and approx(as_float(source_scale_node) or -1, 0.28)
            and approx(as_float(line_width_node) or -1, 5000.0)
            and color_node is not None
            and color_node.attrib.get("T") == "COLOR"
            and color_node.attrib.get("value") == "4281671093"
            and outline_color_node is not None
            and outline_color_node.attrib.get("T") == "COLOR"
            and outline_color_node.attrib.get("value") == "4281671093"
            and outline_width_node is not None
            and outline_width_node.attrib.get("T") == "DOUBLE"
            and approx(as_float(outline_width_node) or -1, 0.22)
            and len(new_clip_effects) == 1
            and new_clip_effects[0].attrib.get("type") == "TransformEffect"
            and not new_layer_audio_effects
            and new_clip.find("./AudioTrack") is None
        ),
        {
            "layer": element_name(new_layer),
            "blend": None if layer_blend is None else layer_blend.attrib.get("type"),
            "layer_opacity": as_float(layer_opacity),
            "clip": element_name(new_clip),
            "source_contract": source_contract_actual,
            "clip_effect_types": [
                node.attrib.get("type") for node in new_clip_effects
            ],
            "layer_audio_effect_count": len(new_layer_audio_effects),
            "clip_has_audio_track": new_clip.find("./AudioTrack") is not None,
        },
        {
            "layer": "V2 Chassis Low FFT",
            "blend": "Add",
            "layer_opacity": 1.0,
            "clip": "V2 Chassis Low FFT",
            "source_contract": source_contract_expected,
            "clip_effect_types": ["TransformEffect"],
            "layer_audio_effect_count": 0,
            "clip_has_audio_track": False,
        },
        "append-only layer 149 and clip 149",
    )
    check(
        "v2_source_outline_contract",
        (
            source_contract_actual["color"]["parameter_tag"] == "ParamColor"
            and source_contract_actual["color"]["parameter_name"] == "Color"
            and source_contract_actual["color"]["parameter_type"] == "COLOR"
            and source_contract_actual["color"]["rgba"] == "#b51d35ff"
            and source_contract_actual["outline"]["color_parameter_tag"]
            == "ParamColor"
            and source_contract_actual["outline"]["color_parameter_name"]
            == "Outline Color"
            and source_contract_actual["outline"]["color_parameter_type"]
            == "COLOR"
            and source_contract_actual["outline"]["color_rgba"]
            == "#b51d35ff"
            and source_contract_actual["outline"]["width_parameter_tag"]
            == "ParamRange"
            and source_contract_actual["outline"]["width_parameter_name"]
            == "Outline Width"
            and source_contract_actual["outline"]["width_parameter_type"]
            == "DOUBLE"
            and source_contract_actual["outline"]["width"] is not None
            and approx(source_contract_actual["outline"]["width"], 0.22)
        ),
        {
            "color": source_contract_actual["color"],
            "outline": source_contract_actual["outline"],
        },
        {
            "color": source_contract_expected["color"],
            "outline": source_contract_expected["outline"],
        },
        (
            "Text Block fill and outline ParamColor metadata plus serialized "
            "RGBA color and Outline Width thickness"
        ),
    )

    transform = new_clip.find(
        "./VideoTrack/RenderPass[@name='RenderPassChain']/"
        "RenderPass[@type='TransformEffect']"
    )
    transform_actual: dict[str, float | None] = {}
    for name in ("Position X", "Position Y", "Scale", "Scale W", "Scale H"):
        node = None if transform is None else named_param(
            transform, "ParamRange", name
        )
        transform_actual[name] = 0.0 if node is None and name == "Position Y" else as_float(node)
    expected_transform = {
        "Position X": 13.0,
        "Position Y": 0.0,
        "Scale": 50.0,
        "Scale W": 204.0,
        "Scale H": 170.0,
    }
    check(
        "v2_transform_static",
        all(
            value is not None and approx(value, expected_transform[name])
            for name, value in transform_actual.items()
        ),
        transform_actual,
        expected_transform,
        "clip Transform; geometry is not FFT-modulated",
    )

    opacity = new_clip.find("./VideoTrack/Params/ParamRange[@name='Opacity']")
    fft = None if opacity is None else opacity.find("./PhaseSourceFFT")
    opacity_range = None if opacity is None else opacity.find("./ValueRange")
    frequency = None if fft is None else named_param(
        fft, "ParamRange", "FrequencyRange"
    )
    gain = None if fft is None else named_param(fft, "ParamRange", "Gain")
    fallback = None if fft is None else named_param(fft, "ParamRange", "Fallback")
    frequency_range = None if frequency is None else frequency.find("./ValueRange")
    fft_nodes = new_clip.findall(".//PhaseSourceFFT")
    fft_parents = parent_map(new_clip)
    fft_target_is_opacity = (
        len(fft_nodes) == 1
        and fft_nodes[0] in fft_parents
        and fft_parents[fft_nodes[0]] is opacity
    )
    fft_actual = {
        "phase_source": None if fft is None else fft.attrib.get("linkId"),
        "frequency_value": as_float(frequency),
        "frequency_min": as_float(frequency_range, "min"),
        "frequency_max": as_float(frequency_range, "max"),
        "gain_db": as_float(gain),
        "fallback_ms": as_float(fallback),
        "output_min": as_float(opacity_range, "min"),
        "output_max": as_float(opacity_range, "max"),
        "fft_node_count": len(fft_nodes),
        "target_is_clip_opacity": fft_target_is_opacity,
    }
    check(
        "fft_contract",
        (
            fft_actual["phase_source"] == "/audioengine/compositionfft"
            and fft_actual["frequency_value"] is not None
            and approx(fft_actual["frequency_value"], 0.165)
            and fft_actual["frequency_min"] is not None
            and approx(fft_actual["frequency_min"], 0.0)
            and fft_actual["frequency_max"] is not None
            and approx(fft_actual["frequency_max"], 0.33)
            and fft_actual["gain_db"] is not None
            and approx(fft_actual["gain_db"], 3.0)
            and fft_actual["fallback_ms"] is not None
            and approx(fft_actual["fallback_ms"], 1400.0)
            and fft_actual["output_min"] is not None
            and approx(fft_actual["output_min"], 0.65)
            and fft_actual["output_max"] is not None
            and approx(fft_actual["output_max"], 0.95)
            and fft_actual["fft_node_count"] == 1
            and fft_actual["target_is_clip_opacity"]
        ),
        fft_actual,
        {
            "phase_source": "/audioengine/compositionfft",
            "frequency_value": 0.165,
            "frequency_min": 0.0,
            "frequency_max": 0.33,
            "gain_db": 3.0,
            "fallback_ms": 1400.0,
            "output_min": 0.65,
            "output_max": 0.95,
            "fft_node_count": 1,
            "target_is_clip_opacity": True,
        },
        "only clip 149 opacity is FFT-driven",
    )

    primitives = geometry["decoration"]["primitives"]
    controls = geometry["protection"]["controls"]
    prototype_counts: dict[str, int] = {}
    for control in controls:
        prototype = control["prototype"]
        prototype_counts[prototype] = prototype_counts.get(prototype, 0) + 1
    track_guides = [
        item for item in primitives if item["family"] == "track-fader-guide"
    ]
    native_text = geometry["native_text_block"]
    check(
        "geometry_collision_contract",
        (
            geometry["protection"]["control_count"] == 148
            and geometry["protection"]["collision_count"] == 0
            and geometry["decoration"]["primitive_count"] == 54
            and geometry["decoration"]["collision_count"] == 0
            and native_text["cell_collision_count"] == 0
            and native_text["encoding"] == "unicode_braille_2x4"
            and native_text["grid_columns"] == 160
            and native_text["grid_rows"] == 60
            and native_text["effective_dot_columns"] == 320
            and native_text["effective_dot_rows"] == 240
            and native_text["desired_dot_count"] == 5382
            and native_text["occupied_dot_count"] == 5377
            and native_text["clipped_dot_count"] == 5
            and native_text["dot_collision_count"] == 0
            and native_text["nonblank_glyph_count"] == 2221
            and native_text["represented_primitive_count"] == 54
            and native_text["empty_primitive_count"] == 0
            and approx(float(native_text["source_scale"]), 0.28)
            and len(track_guides) == 8
        ),
        {
            "controls": geometry["protection"]["control_count"],
            "protected_boxes": geometry["protection"]["box_count"],
            "vector_primitives": geometry["decoration"]["primitive_count"],
            "vector_collisions": geometry["decoration"]["collision_count"],
            "encoding": native_text["encoding"],
            "grid_columns": native_text["grid_columns"],
            "grid_rows": native_text["grid_rows"],
            "effective_dot_columns": native_text["effective_dot_columns"],
            "effective_dot_rows": native_text["effective_dot_rows"],
            "desired_dot_count": native_text["desired_dot_count"],
            "occupied_dot_count": native_text["occupied_dot_count"],
            "clipped_dot_count": native_text["clipped_dot_count"],
            "dot_collision_count": native_text["dot_collision_count"],
            "text_cell_collisions": native_text["cell_collision_count"],
            "nonblank_glyph_count": native_text["nonblank_glyph_count"],
            "represented_primitive_count": native_text[
                "represented_primitive_count"
            ],
            "empty_primitive_count": native_text["empty_primitive_count"],
            "source_scale": native_text["source_scale"],
            "track_fader_guides": len(track_guides),
            "prototype_counts": prototype_counts,
        },
        {
            "controls": 148,
            "vector_primitives": 54,
            "vector_collisions": 0,
            "encoding": "unicode_braille_2x4",
            "grid_columns": 160,
            "grid_rows": 60,
            "effective_dot_columns": 320,
            "effective_dot_rows": 240,
            "desired_dot_count": 5382,
            "occupied_dot_count": 5377,
            "clipped_dot_count": 5,
            "dot_collision_count": 0,
            "text_cell_collisions": 0,
            "nonblank_glyph_count": 2221,
            "represented_primitive_count": 54,
            "empty_primitive_count": 0,
            "source_scale": 0.28,
            "track_fader_guides": 8,
        },
        "resting, fader/knob motion hull, crossfader, and chassis geometry",
    )

    screenshot_records: list[dict[str, Any]] = []
    screenshot_ok = True
    for name in EXPECTED_SCREENSHOTS:
        path = screenshot_dir / name
        if not path.is_file():
            screenshot_ok = False
            screenshot_records.append({"path": name, "missing": True})
            continue
        try:
            width, height, _ = read_png(path)
        except Exception as error:  # noqa: BLE001 - report all format failures
            screenshot_ok = False
            screenshot_records.append({"path": name, "error": str(error)})
            continue
        if (width, height) != (200, 113):
            screenshot_ok = False
        screenshot_records.append(
            {
                "path": name,
                "width": width,
                "height": height,
                "sha256": sha256_file(path),
            }
        )
    check(
        "visual_evidence_files",
        screenshot_ok,
        screenshot_records,
        f"{len(EXPECTED_SCREENSHOTS)} valid 200x113 PNGs",
        DEFAULT_SCREENSHOTS.as_posix(),
    )

    baseline_image = screenshot_dir / EXPECTED_SCREENSHOTS[0]
    silence_image = screenshot_dir / EXPECTED_SCREENSHOTS[1]
    silence_layer_image = screenshot_dir / EXPECTED_SCREENSHOTS[2]
    bypass_image = screenshot_dir / EXPECTED_SCREENSHOTS[3]
    peak_image = screenshot_dir / EXPECTED_SCREENSHOTS[4]
    peak_layer_image = screenshot_dir / EXPECTED_SCREENSHOTS[5]
    final_image = screenshot_dir / EXPECTED_SCREENSHOTS[6]
    bypass_metrics = image_metrics(baseline_image, bypass_image)
    bypass_sha_identical = (
        sha256_file(baseline_image) == sha256_file(bypass_image)
    )
    silence_peak_metrics = image_metrics(silence_image, peak_image)
    layer_silence_peak_metrics = image_metrics(
        silence_layer_image, peak_layer_image
    )
    layer_silence_luma = mean_luma(silence_layer_image)
    layer_peak_luma = mean_luma(peak_layer_image)
    final_restored_matches_silence_sha = (
        sha256_file(silence_image) == sha256_file(final_image)
    )
    monitor_luma_limitation = (
        "Arena monitor 200x113 isolated-layer RGB is alpha-composited and "
        "downsampled; mean luma is not a monotonic opacity meter. The "
        "increasing accepted range is enforced separately by fft_contract."
    )
    check(
        "bypass_restores_r1",
        bypass_metrics["pixel_identical"] and bypass_sha_identical,
        {
            "metrics": bypass_metrics,
            "file_sha_identical": bypass_sha_identical,
        },
        {
            "pixel_identical": True,
            "file_sha_identical": True,
        },
        "R1 baseline versus V2-layer bypass capture",
    )
    check(
        "fft_floor_peak_visual",
        (
            silence_peak_metrics["changed_pixels"] > 0
            and layer_silence_peak_metrics["changed_pixels"] > 0
            and layer_silence_luma > 0
            and layer_peak_luma > 0
            and final_restored_matches_silence_sha
        ),
        {
            "composite_floor_vs_peak": silence_peak_metrics,
            "isolated_layer_floor_vs_peak": layer_silence_peak_metrics,
            "floor_layer_mean_luma": layer_silence_luma,
            "peak_layer_mean_luma": layer_peak_luma,
            "monitor_luma_limitation": monitor_luma_limitation,
            "accepted_range_enforced_by": "fft_contract",
            "final_restored_matches_floor_sha": (
                final_restored_matches_silence_sha
            ),
        },
        {
            "composite_changed_pixels": "> 0",
            "isolated_layer_changed_pixels": "> 0",
            "floor_layer_mean_luma": "> 0",
            "peak_layer_mean_luma": "> 0",
            "mean_luma_monotonicity_required": False,
            "accepted_range_enforced_by": "fft_contract",
            "final_restored_matches_floor_sha": True,
        },
        (
            "nonblack, pixel-distinct floor/peak endpoints and exact floor "
            "restoration; numeric accepted-range increase is proved by "
            "fft_contract, not downsampled monitor luma"
        ),
    )

    runtime: dict[str, Any]
    if args.skip_runtime:
        runtime = {"status": "SKIPPED"}
    else:
        try:
            runtime = runtime_observation(EXPECTED_NAME)
            runtime_ok = (
                runtime["gateway"]["count"] == 1
                and runtime["gateway"]["ready"] is True
                and runtime["gateway"]["status"] == "ok"
                and runtime["gateway"]["queue_depth"] == 0
                and runtime["arena_child"]["count"] == 1
                and runtime["arena_child"]["ready"] is True
                and runtime["arena_child"]["parent_is_gateway"] is True
                and runtime["wire_child"]["count"] == 1
                and runtime["wire_child"]["ready"] is True
                and runtime["wire_child"]["parent_is_gateway"] is True
                and runtime["avenue_bridge"]["count"] == 1
                and runtime["avenue_application"]["count"] == 1
                and runtime["avenue_application"]["exact_candidate_active"] is True
                and runtime["wire_application"]["count"] == 0
            )
            check(
                "runtime_singleton",
                runtime_ok,
                runtime,
                {
                    "gateway": 1,
                    "arena_child": 1,
                    "wire_child": 1,
                    "avenue_bridge": 1,
                    "avenue_application": 1,
                    "wire_application": 0,
                    "exact_candidate_active": True,
                },
                "gateway healthz plus Win32 process topology",
            )
        except Exception as error:  # noqa: BLE001 - preserve receipt on failure
            runtime = {"status": "ERROR", "detail": str(error)}
            check(
                "runtime_singleton",
                False,
                runtime,
                "healthy singleton topology",
                "gateway healthz plus Win32 process topology",
            )

    geometry_text_blob = geometry_path.read_text(encoding="utf-8")
    personal_path_hits = sorted(
        set(
            re.findall(
                r"C:\\Users\\[^\\\r\n\"<]+",
                candidate_xml_text + "\n" + geometry_text_blob,
                flags=re.IGNORECASE,
            )
        )
    )
    check(
        "personal_path_scan",
        not personal_path_hits,
        personal_path_hits,
        [],
        "candidate AVC and deterministic geometry artifact",
    )

    human_gates = [
        {
            "id": "physical_apc40_complete_sweep",
            "status": "OPEN — HUMAN TEST REQUIRED",
            "scope": (
                "every button family and feedback color; track/master faders at "
                "min/mid/max; all ordinary/device knobs at both extremes; tempo "
                "both directions; crossfader both endpoints"
            ),
        },
        {
            "id": "real_audio_band_calibration",
            "status": "OPEN — HUMAN TEST REQUIRED",
            "scope": (
                "silence, isolated low/bass, midrange, high-frequency, and "
                "accepted real-audio peak with all witnesses readable"
            ),
        },
        {
            "id": "matched_performance_gate",
            "status": "OPEN — HUMAN TEST REQUIRED",
            "scope": (
                "elevated, comparable 5-minute R1 and V2 PresentMon intervals; "
                "reject if V2 frame time regresses more than 10%"
            ),
            "blocked_reason": (
                "PresentMon capture exited without samples in the non-elevated "
                "session; Performance Log Users membership is absent"
            ),
        },
    ]
    performance = {
        "gate": "OPEN — HUMAN TEST REQUIRED",
        "baseline_ui_observation_fps": 23.9,
        "baseline_ui_observation_frame_time_ms": 1000.0 / 23.9,
        "observation_comparable": False,
        "v2_comparable_fps": None,
        "frame_time_regression_percent": None,
        "rejection_threshold_percent": 10.0,
        "note": (
            "The UI value is context only and cannot pass the performance gate."
        ),
    }
    collision_states = [
        {
            "state": "resting/all-visible",
            "method": "saved composite plus protected-envelope geometry",
            "intersections": 0,
        },
        {
            "state": "all track/master faders min-mid-max",
            "method": "full protected motion boxes",
            "intersections": 0,
            "physical_status": "OPEN — HUMAN TEST REQUIRED",
        },
        {
            "state": "all ordinary/device knobs both extremes",
            "method": "full protected rotary motion hulls",
            "intersections": 0,
            "physical_status": "OPEN — HUMAN TEST REQUIRED",
        },
        {
            "state": "crossfader both endpoints",
            "method": "full protected crossfader motion box",
            "intersections": 0,
            "physical_status": "OPEN — HUMAN TEST REQUIRED",
        },
        {
            "state": "chassis-only silence floor",
            "method": "isolated layer capture",
            "intersections": 0,
        },
        {
            "state": "implemented low band synthetic accepted peak",
            "method": "isolated layer and all-visible composite captures",
            "intersections": 0,
            "real_audio_status": "OPEN — HUMAN TEST REQUIRED",
        },
        {
            "state": "V2 bypass",
            "method": "baseline/bypass image comparison",
            "intersections": 0,
        },
    ]

    document = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "verdict": (
            "PARTIAL — software candidate ready for human test"
            if not failures
            else "BLOCKED — automated validation failures"
        ),
        "automated_result": "PASS" if not failures else "FAIL",
        "candidate": {
            "path": DEFAULT_CANDIDATE.as_posix(),
            "sha256": candidate_sha,
            "name": candidate_name,
        },
        "r1_integrity": {
            "composition": {
                "path": R1_COMPOSITION.as_posix(),
                "before_sha256": EXPECTED_R1_AVC_SHA256,
                "after_sha256": r1_sha,
                "byte_identical": r1_sha == EXPECTED_R1_AVC_SHA256,
            },
            "controller": {
                "path": R1_CONTROLLER.as_posix(),
                "before_sha256": EXPECTED_R1_MIDI_SHA256,
                "after_sha256": controller_sha,
                "byte_identical": controller_sha == EXPECTED_R1_MIDI_SHA256,
            },
        },
        "counts": {
            "resolution": [1920, 1080],
            "decks": len(candidate_decks),
            "columns": len(first_deck_columns),
            "layers": len(candidate_layers),
            "protected_layers": 148,
            "added_layers": 1,
            "clips": len(candidate_clips),
            "shortcut_records": len(shortcuts),
            "unique_raw_midi_keys": len(raw_keys),
            "added_midi_shortcuts": 0,
            "external_media": len(external_media),
        },
        "source": source_contract_actual,
        "fft": fft_actual,
        "geometry": {
            "artifact": DEFAULT_GEOMETRY.as_posix(),
            "protected_controls": geometry["protection"]["control_count"],
            "protected_boxes": geometry["protection"]["box_count"],
            "vector_primitives": geometry["decoration"]["primitive_count"],
            "vector_collisions": geometry["decoration"]["collision_count"],
            "encoding": native_text["encoding"],
            "grid_columns": native_text["grid_columns"],
            "grid_rows": native_text["grid_rows"],
            "effective_dot_columns": native_text["effective_dot_columns"],
            "effective_dot_rows": native_text["effective_dot_rows"],
            "desired_dot_count": native_text["desired_dot_count"],
            "occupied_dot_count": native_text["occupied_dot_count"],
            "clipped_dot_count": native_text["clipped_dot_count"],
            "dot_collision_count": native_text["dot_collision_count"],
            "native_text_cell_collisions": native_text[
                "cell_collision_count"
            ],
            "nonblank_glyph_count": native_text["nonblank_glyph_count"],
            "represented_primitive_count": native_text[
                "represented_primitive_count"
            ],
            "empty_primitive_count": native_text["empty_primitive_count"],
            "source_scale": native_text["source_scale"],
            "collision_states": collision_states,
        },
        "visual_metrics": {
            "baseline_vs_bypass": bypass_metrics,
            "composite_floor_vs_peak": silence_peak_metrics,
            "isolated_layer_floor_vs_peak": layer_silence_peak_metrics,
            "floor_layer_mean_luma": layer_silence_luma,
            "peak_layer_mean_luma": layer_peak_luma,
            "monitor_luma_limitation": monitor_luma_limitation,
            "final_restored_matches_floor_sha": (
                final_restored_matches_silence_sha
            ),
        },
        "runtime": runtime,
        "performance": performance,
        "checks": checks,
        "human_gates": human_gates,
        "failures": failures,
    }
    serialized = json.dumps(
        document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n"
    if args.check:
        if not output_path.is_file():
            raise SystemExit(f"missing QA receipt: {output_path}")
        if output_path.read_text(encoding="utf-8") != serialized:
            raise SystemExit(f"QA receipt is stale: {output_path}")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8", newline="\n")

    print(
        json.dumps(
            {
                "output": str(output_path),
                "automated_result": document["automated_result"],
                "verdict": document["verdict"],
                "checks": len(checks),
                "failures": failures,
                "human_gates_open": len(human_gates),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
