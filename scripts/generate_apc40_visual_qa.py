"""Build and safely install APC40 MkII Visual QA MIDI preset candidates.

The control manifest is deterministic, but the Avenue preset is never
regenerated from scratch.  Pilot and full candidates are derived from the
canonical active preset, preserve protected shortcut elements, and replace
only the allowlisted continuous-control mappings.  Candidate generation is
offline; installation and rollback are separate, explicit, hash-gated steps.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPO_PRESET = (
    PROJECT_ROOT
    / "react-kit/controllers/APC 40 MK II - Visual QA - Pristine 148.xml"
)
MANIFEST_PATH = PROJECT_ROOT / "react-kit/docs/APC40_visual_qa_manifest.json"
CALIBRATION_PATH = PROJECT_ROOT / "react-kit/docs/APC40_visual_qa_calibration.json"
BUILD_MANIFEST_PATH = PROJECT_ROOT / "react-kit/docs/APC40_visual_qa_build_manifest.json"
DEFAULT_CAMPAIGN_DIR = (
    PROJECT_ROOT / "react-kit/docs/2026-07-18-apc40-animated-visual-qa/artifacts"
)
ACTIVE_PRESET = (
    Path.home()
    / "OneDrive/Documents/Resolume Avenue/Shortcuts/MIDI"
    / "APC 40 MK II - Visual QA.xml"
)

PANEL_WIDTH = 4240
PANEL_HEIGHT = 2520
SAFE_WIDTH = 1720
SAFE_HEIGHT = 980
NOTE_BASE = 1 << 56
CC_BASE = 1 << 57
TEMPO_RELATIVE_STEP = "-0.0020833333333333333044"
VERTICAL_FADER_LAYERS = frozenset((*range(94, 102), 143))
CROSSFADER_LAYER = 144
ROTARY_LAYERS = frozenset((*range(102, 118), 145, 148))
PILOT_LAYERS = frozenset((94, 102, 148))
PRESET_DISPLAY_NAME = "APC 40 MK II - Visual QA"
MIDI_DEVICE_NAME = "APC40 mkII"
SHORTCUT_MANAGER_NAME = "MIDIShortcutManagerShortcuts"
COMPOSITION_NAME = "APC40_Visual_QA_148"
PREFLIGHT_MAX_AGE_SECONDS = 10 * 60
PREFLIGHT_FUTURE_TOLERANCE_SECONDS = 60
ROLLBACK_STAGES = frozenset(("rollback-prepilot", "rollback-full-to-pilot"))
REQUIRED_ARTIFACT_BASENAMES = frozenset(
    (
        "APC40_visual_qa_geometry.json",
        "APC40_visual_qa_calibration.json",
        "APC40_visual_qa_live_controls.json",
        "APC40_visual_qa_live_overlay.png",
        "APC40_visual_qa_live_overlay_debug.png",
        "APC40_visual_qa_renderer_report.json",
        "APC40_visual_qa_crop_grid.png",
        "APC40_visual_qa_crop_track_cluster.png",
        "APC40_visual_qa_crop_transport.png",
        "APC40_visual_qa_crop_fader.png",
        "APC40_visual_qa_crop_rotary.png",
        "APC40_visual_qa_crop_navigation.png",
        "APC40_visual_qa_crop_crossfader.png",
    )
)
JSON_BUILD_ARTIFACT_BASENAMES = frozenset(
    (
        "APC40_visual_qa_geometry.json",
        "APC40_visual_qa_calibration.json",
        "APC40_visual_qa_live_controls.json",
        "APC40_visual_qa_renderer_report.json",
    )
)
ACCEPTED_PARENT_HASH_BASENAMES = frozenset(
    (
        "APC40_visual_qa_geometry.json",
        "APC40_visual_qa_calibration.json",
        "APC40_visual_qa_live_controls.json",
        "APC40_visual_qa_live_overlay.png",
    )
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ROLE_NAMES = frozenset(
    (
        "button_connect",
        "legacy_cc",
        "wake",
        "opacity",
        "absolute_motion",
        "tempo_motion",
    )
)
LAYER_IN_PATH_RE = re.compile(r"^/composition/layers/(\d+)(?:/|$)")


@dataclass(frozen=True)
class Control:
    layer: int
    label: str
    layer_name: str
    category: str
    midi_type: str
    data1: int
    channel: int
    panel_x: int
    panel_y: int
    scale: int
    color: str
    led_velocity: int = 0
    single_line: bool = False

    @property
    def x(self) -> int:
        return round((self.panel_x / PANEL_WIDTH - 0.5) * SAFE_WIDTH)

    @property
    def y(self) -> int:
        return round((self.panel_y / PANEL_HEIGHT - 0.5) * SAFE_HEIGHT)

    @property
    def raw_key(self) -> int:
        status = (0x90 if self.midi_type == "note" else 0xB0) + self.channel - 1
        base = NOTE_BASE if self.midi_type == "note" else CC_BASE
        return base + (self.data1 << 8) + status

    @property
    def is_button(self) -> bool:
        return self.midi_type == "note"

    @property
    def midi_label(self) -> str:
        prefix = "N" if self.is_button else "CC"
        return f"{prefix}{self.data1}/C{self.channel}"

    @property
    def display_text(self) -> str:
        separator = " " if self.single_line else "\n"
        return f"{self.label}{separator}{self.midi_label}"


# APC40 mkII palette. Grid velocities are rig-confirmed by
# apc40_led_test.py; the RGB values match the existing Grid Map Test art.
WHITE = "#e6e6e6ff"    # velocity 3
RED = "#e23b3bff"      # velocity 5
ORANGE = "#f08a24ff"   # velocity 9
YELLOW = "#ffd43bff"   # velocity 13
GREEN = "#23c552ff"    # velocity 21
CYAN = "#17c8e8ff"     # velocity 37
BLUE = "#2b5bffff"     # velocity 45
VIOLET = "#7a3fc0ff"   # velocity 49
PINK = "#c81e9aff"     # velocity 53
GRID_LED_VELOCITIES = (45, 37, 21, 5, 9, 49, 53, 3)
GRID_COLORS = (BLUE, CYAN, GREEN, RED, ORANGE, VIOLET, PINK, WHITE)
def build_controls() -> list[Control]:
    controls: list[Control] = []

    def add(
        label: str,
        layer_name: str,
        category: str,
        midi_type: str,
        data1: int,
        channel: int,
        panel_x: int,
        panel_y: int,
        scale: int,
        color: str,
        led_velocity: int = 0,
        single_line: bool = False,
    ) -> None:
        controls.append(
            Control(
                layer=len(controls) + 1,
                label=label,
                layer_name=layer_name,
                category=category,
                midi_type=midi_type,
                data1=data1,
                channel=channel,
                panel_x=panel_x,
                panel_y=panel_y,
                scale=scale,
                color=color,
                led_velocity=led_velocity,
                single_line=single_line,
            )
        )

    track_x = [225 + 320 * i for i in range(8)]

    # Grid: MIDI note 0 is the physical bottom-left pad.
    for note in range(40):
        row_from_bottom, col = divmod(note, 8)
        row_from_top = 5 - row_from_bottom
        add(
            f"G{col + 1}-{row_from_top}",
            f"Grid {row_from_top} Track {col + 1}",
            "grid",
            "note",
            note,
            1,
            track_x[col],
            1085 - 155 * row_from_bottom,
            50,
            GRID_COLORS[col],
            GRID_LED_VELOCITIES[col],
        )

    # Scene launch: n82 is top; n86 is bottom.
    for index, note in enumerate(range(82, 87), start=1):
        add(
            f"SCENE{index}",
            f"Scene Launch {index}",
            "scene",
            "note",
            note,
            1,
            2745,
            465 + 155 * (index - 1),
            35,
            GREEN,
            21,
        )

    for track, x in enumerate(track_x, start=1):
        add(f"STOP{track}", f"Clip Stop {track}", "clip_stop", "note", 52, track, x, 1261, 35, ORANGE, 5)
    for track, x in enumerate(track_x, start=1):
        add(f"SEL{track}", f"Track Select {track}", "track_select", "note", 51, track, x, 1436, 35, ORANGE, 45)

    # Physical 2 x 2 cluster per channel strip:
    #   [ track number ] [ A/B ]
    #   [       S      ] [  ●  ]
    for track, x in enumerate(track_x, start=1):
        # The adjacent Record Arm dot is the red fixed-color button; only the
        # Solo button beside it uses the blue family.
        add("●", f"Record Arm {track}", "record_arm", "note", 48, track, x + 61, 1722, 27, RED, 5)
    for track, x in enumerate(track_x, start=1):
        # SOLO has a fixed blue LED, not an RGB LED. Use full-on feedback so
        # Avenue reliably lights the physical button on the APC40.
        add("S", f"Solo {track}", "solo", "note", 49, track, x - 61, 1722, 27, BLUE, 127)
    for track, x in enumerate(track_x, start=1):
        add(str(track), f"Activator {track}", "activator", "note", 50, track, x - 61, 1602, 27, ORANGE, 21)
    for track, x in enumerate(track_x, start=1):
        add("A/B", f"Crossfade A B {track}", "crossfade_assign", "note", 66, track, x + 61, 1602, 27, ORANGE, 9)

    # Continuous controls do not have colored button LEDs. Keep their visual
    # witnesses neutral white; Tempo is the one dedicated red exception.
    for track, x in enumerate(track_x, start=1):
        add(f"FADER{track}", f"Track Fader {track}", "track_fader", "cc", 7, track, x, 2180, 40, WHITE)
    for index, (cc, x) in enumerate(zip(range(48, 56), track_x), start=1):
        add(f"TRACK{index}", f"Track Knob {index}", "track_knob", "cc", cc, 1, x, 207, 40, WHITE)

    device_x = [3050, 3370, 3690, 4010]
    for index, cc in enumerate(range(16, 24), start=1):
        row, col = divmod(index - 1, 4)
        add(
            f"DEV{index}",
            f"Device Knob {index}",
            "device_knob",
            "cc",
            cc,
            1,
            device_x[col],
            1035 + 310 * row,
            40,
            WHITE,
        )

    # Preserve the useful original ordering where possible.  Bogus n67/n68-71
    # slots are reassigned to real controls; three missing endpoints are appended.
    right_controls = [
        ("PLAY", "Play", "transport", 91, 3370, 395, 35, ORANGE, 21, False),
        ("STOP", "Stop", "transport", 92, 3370, 485, 22, WHITE, 3, True),
        ("RECORD", "Record", "transport", 93, 3690, 395, 32, ORANGE, 5, False),
        ("TAP", "Tap Tempo", "transport", 99, 3690, 585, 28, WHITE, 9, False),
        ("NUDGE-", "Nudge Minus", "transport", 100, 3370, 775, 28, WHITE, 13, False),
        ("NUDGE+", "Nudge Plus", "transport", 101, 3690, 775, 28, WHITE, 13, False),
        ("PAN", "Pan Mode", "mode", 87, 3025, 395, 32, ORANGE, 49, False),
        ("STOPALL", "Stop All Clips", "right_column", 81, 2745, 1261, 30, WHITE, 5, False),
        ("U", "Bank Up", "navigation", 94, 3160, 2025, 24, WHITE, 49, True),
        ("D", "Bank Down", "navigation", 95, 3160, 2125, 24, WHITE, 49, True),
        ("R", "Bank Right", "navigation", 96, 3270, 2075, 24, WHITE, 49, True),
        ("L", "Bank Left", "navigation", 97, 3050, 2075, 24, WHITE, 49, True),
        ("SHIFT", "Shift", "navigation", 98, 3690, 2075, 28, WHITE, 49, False),
        ("DEVICE<", "Device Left", "device_button", 58, 3050, 1660, 28, ORANGE, 49, False),
        ("DEVICE>", "Device Right", "device_button", 59, 3370, 1660, 28, ORANGE, 49, False),
        ("BANK<", "Bank Left Button", "device_button", 60, 3690, 1660, 28, ORANGE, 49, False),
        ("BANK>", "Bank Right Button", "device_button", 61, 4010, 1660, 28, ORANGE, 49, False),
        ("ON/OFF", "Device On Off", "device_button", 62, 3050, 1830, 28, ORANGE, 21, False),
        ("LOCK", "Device Lock", "device_button", 63, 3370, 1830, 28, ORANGE, 49, False),
        ("CLIP/DEV", "Clip Device View", "device_button", 64, 3690, 1830, 26, ORANGE, 49, False),
        ("DETAIL", "Detail View", "device_button", 65, 4010, 1830, 28, ORANGE, 49, False),
        ("SENDS", "Sends Mode", "mode", 88, 3025, 585, 30, ORANGE, 49, False),
        ("USER", "User Mode", "mode", 89, 3025, 775, 30, ORANGE, 49, False),
        ("METRO", "Metronome", "transport", 90, 3370, 585, 30, ORANGE, 13, False),
        ("SESSION", "Session Record", "transport", 102, 4010, 395, 28, ORANGE, 53, False),
    ]
    for label, name, category, note, x, y, scale, color, led_velocity, single_line in right_controls:
        add(label, name, category, "note", note, 1, x, y, scale, color, led_velocity, single_line)

    add("MASTER", "Master Fader", "special_cc", "cc", 14, 1, 2745, 2180, 36, WHITE)
    add("X-FADE", "Crossfader", "special_cc", "cc", 15, 1, 3690, 2380, 34, WHITE)
    add("CUE", "Cue Level", "special_cc", "cc", 47, 1, 2745, 1662, 32, WHITE)

    add("MASTER", "Master Select", "right_column", "note", 80, 1, 2745, 1436, 30, ORANGE, 45)
    add("BANKLCK", "Bank Lock", "navigation", "note", 103, 1, 4010, 2075, 26, ORANGE, 49)
    add("TEMPO", "Tempo Knob", "tempo", "cc", 13, 1, 4010, 650, 28, RED)

    validate_controls(controls)
    return controls


def validate_controls(controls: list[Control]) -> None:
    assert len(controls) == 148
    assert [control.layer for control in controls] == list(range(1, 149))
    assert sum(control.is_button for control in controls) == 120
    assert sum(not control.is_button for control in controls) == 28
    assert len({control.raw_key for control in controls}) == 148
    assert not ({67, 68, 69, 70, 71} & {c.data1 for c in controls if c.is_button})

    expected_missing_repairs = {
        ("note", 80),
        ("note", 87),
        ("note", 88),
        ("note", 89),
        ("note", 90),
        ("note", 102),
        ("note", 103),
        ("cc", 13),
    }
    actual = {(control.midi_type, control.data1) for control in controls}
    assert expected_missing_repairs <= actual
    assert all(1 <= control.led_velocity <= 127 for control in controls if control.is_button)

    # TAP and TEMPO deliberately share one physical knob area, but have separate
    # non-overlapping label lanes so both MIDI messages can be swept at once.
    centers = [(control.x, control.y) for control in controls if control.label not in {"TAP", "TEMPO"}]
    assert len(centers) == len(set(centers))
    assert all(control.midi_label in control.display_text for control in controls)
    assert all(max(map(len, control.display_text.splitlines())) <= 11 for control in controls)


class GeneratorError(RuntimeError):
    """Base class for fail-closed generator errors."""


class ValidationError(GeneratorError):
    """An input or generated artifact violates the locked contract."""


class HashMismatch(GeneratorError):
    """A byte-level precondition changed."""


class UnsafeInstallError(GeneratorError):
    """An install or rollback request is not safe to execute."""


@dataclass(frozen=True)
class ShortcutSemantic:
    unique_id: int
    raw_key: int
    raw_value: str
    num_steps: int
    param_node_name: str
    behaviour: int
    input_device: str
    output_device_or_none: str | None
    ordered_paths: tuple[tuple[str, str, str, str], ...]
    subtarget_or_none: tuple[tuple[str, str], ...] | None
    value_range_or_none: tuple[tuple[str, str], ...] | None
    named_values: tuple[tuple[str, str], ...]
    role: str
    input_path: str

    @property
    def identity(self) -> tuple[int, str, str]:
        return (self.raw_key, self.role, self.input_path)

    def as_json(self) -> dict[str, object]:
        return {
            "unique_id": self.unique_id,
            "raw_key": str(self.raw_key),
            "raw_value": self.raw_value,
            "num_steps": self.num_steps,
            "param_node_name": self.param_node_name,
            "behaviour": self.behaviour,
            "input_device": self.input_device,
            "output_device_or_none": self.output_device_or_none,
            "ordered_paths": [list(item) for item in self.ordered_paths],
            "subtarget_or_none": (
                [list(item) for item in self.subtarget_or_none]
                if self.subtarget_or_none is not None
                else None
            ),
            "value_range_or_none": (
                [list(item) for item in self.value_range_or_none]
                if self.value_range_or_none is not None
                else None
            ),
            "named_values": [list(item) for item in self.named_values],
            "role": self.role,
            "input_path": self.input_path,
        }


@dataclass(frozen=True)
class PresetDocument:
    source: str
    raw_bytes: bytes
    root: ET.Element
    manager: ET.Element
    shortcuts: tuple[ET.Element, ...]
    semantics: tuple[ShortcutSemantic, ...]

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.raw_bytes)


@dataclass(frozen=True)
class CalibrationContract:
    path: Path
    raw_bytes: bytes
    data: Mapping[str, object]
    build_manifest_path: Path | None
    build_manifest_sha256: str | None
    test_only: bool

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.raw_bytes)

    @property
    def build_id(self) -> str:
        return str(self.data["build_id"])

    @property
    def status(self) -> str:
        return str(self.data["status"])


@dataclass(frozen=True)
class SemanticDiff:
    allowed_raw_keys: tuple[int, ...]
    changed_raw_keys: tuple[int, ...]
    added: tuple[ShortcutSemantic, ...]
    removed: tuple[ShortcutSemantic, ...]
    changed: tuple[tuple[ShortcutSemantic, ShortcutSemantic], ...]

    def as_json(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "allowed_raw_keys": [str(key) for key in self.allowed_raw_keys],
            "changed_raw_keys": [str(key) for key in self.changed_raw_keys],
            "added": [record.as_json() for record in self.added],
            "removed": [record.as_json() for record in self.removed],
            "changed": [
                {"before": before.as_json(), "after": after.as_json()}
                for before, after in self.changed
            ],
        }


@dataclass(frozen=True)
class CandidateResult:
    mode: str
    baseline_path: Path
    baseline_sha256: str
    repo_reference_path: Path
    repo_reference_sha256: str
    candidate_bytes: bytes
    candidate_sha256: str
    calibration: CalibrationContract
    diff: SemanticDiff
    shortcut_count: int
    installable: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise GeneratorError(f"cannot read {path}: {exc}") from exc


def _required_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise GeneratorError(f"{label} is unavailable at {path}: {exc}") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _only_child(element: ET.Element, tag: str, context: str) -> ET.Element:
    children = element.findall(tag)
    _require(len(children) == 1, f"{context} must contain exactly one {tag}")
    return children[0]


def _optional_child(element: ET.Element, tag: str, context: str) -> ET.Element | None:
    children = element.findall(tag)
    _require(len(children) <= 1, f"{context} may contain at most one {tag}")
    return children[0] if children else None


def _normalized_output_device(element: ET.Element) -> str | None:
    value = element.attrib.get("outputDeviceName")
    return value if value else None


def _shortcut_role(raw_key: int, input_path: str, behaviour: int) -> str:
    lower = input_path.lower()
    if lower.endswith("/connect"):
        return "button_connect" if raw_key < CC_BASE else "wake"
    if lower.endswith("/video/source/delay"):
        return "legacy_cc"
    if lower.endswith("/opacity"):
        return "opacity"
    if lower.endswith(("/positionx", "/positiony", "/rotationz")):
        return "tempo_motion" if behaviour == 16392 else "absolute_motion"
    raise ValidationError(
        f"unsupported shortcut target for raw key {raw_key}: {input_path}"
    )


def shortcut_semantic(element: ET.Element) -> ShortcutSemantic:
    context = f"Shortcut uniqueId={element.attrib.get('uniqueId', '<missing>')}"
    _require(element.tag == "Shortcut", f"{context} has tag {element.tag!r}")
    raw = _only_child(element, "RawInputMessage", context)
    paths = tuple(
        (
            path.attrib.get("name", ""),
            path.attrib.get("path", ""),
            path.attrib.get("translationType", ""),
            path.attrib.get("allowedTranslationTypes", ""),
        )
        for path in element.findall("ShortcutPath")
    )
    input_paths = [path for name, path, _, _ in paths if name == "InputPath"]
    _require(len(input_paths) == 1, f"{context} must have exactly one InputPath")
    try:
        unique_id = int(element.attrib["uniqueId"])
        raw_key = int(raw.attrib["key"])
        num_steps = int(raw.attrib["numSteps"])
        behaviour = int(element.attrib["behaviour"])
    except (KeyError, ValueError) as exc:
        raise ValidationError(f"{context} contains a missing/non-numeric field") from exc

    subtarget = _optional_child(element, "Subtarget", context)
    value_range = _optional_child(element, "ValueRange", context)
    named_parent = _optional_child(element, "NamedValues", context)
    named_values = ()
    if named_parent is not None:
        named_values = tuple(
            (value.attrib.get("first", ""), value.attrib.get("second", ""))
            for value in named_parent.findall("Value")
        )

    role = _shortcut_role(raw_key, input_paths[0], behaviour)
    semantic = ShortcutSemantic(
        unique_id=unique_id,
        raw_key=raw_key,
        raw_value=raw.attrib.get("value", ""),
        num_steps=num_steps,
        param_node_name=element.attrib.get("paramNodeName", ""),
        behaviour=behaviour,
        input_device=element.attrib.get("inputDeviceName", ""),
        output_device_or_none=_normalized_output_device(element),
        ordered_paths=paths,
        subtarget_or_none=(
            tuple(sorted(subtarget.attrib.items())) if subtarget is not None else None
        ),
        value_range_or_none=(
            tuple(sorted(value_range.attrib.items())) if value_range is not None else None
        ),
        named_values=named_values,
        role=role,
        input_path=input_paths[0],
    )
    _require(semantic.role in ROLE_NAMES, f"{context} has unknown role {semantic.role}")
    return semantic


def parse_preset_bytes(
    raw_bytes: bytes,
    *,
    source: str = "<memory>",
    controls: Sequence[Control] | None = None,
) -> PresetDocument:
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as exc:
        raise ValidationError(f"invalid preset XML from {source}: {exc}") from exc
    _require(root.tag == "MidiShortcutPreset", f"{source}: unexpected root {root.tag!r}")
    managers = root.findall("ShortcutManager")
    _require(len(managers) == 1, f"{source}: expected one ShortcutManager")
    manager = managers[0]
    _require(
        manager.attrib.get("name") == SHORTCUT_MANAGER_NAME,
        f"{source}: unexpected shortcut manager name",
    )
    shortcuts = tuple(child for child in list(manager) if child.tag == "Shortcut")
    _require(
        len(shortcuts) == len(list(manager)),
        f"{source}: non-Shortcut child found in ShortcutManager",
    )
    semantics = tuple(shortcut_semantic(element) for element in shortcuts)
    document = PresetDocument(
        source=source,
        raw_bytes=raw_bytes,
        root=root,
        manager=manager,
        shortcuts=shortcuts,
        semantics=semantics,
    )
    validate_preset_document(document, controls or build_controls())
    return document


def parse_preset_file(
    path: Path, *, controls: Sequence[Control] | None = None
) -> PresetDocument:
    return parse_preset_bytes(
        _required_bytes(path, "preset"),
        source=str(path),
        controls=controls,
    )


def validate_preset_document(
    document: PresetDocument, controls: Sequence[Control]
) -> None:
    try:
        validate_controls(list(controls))
    except AssertionError as exc:
        raise ValidationError("control manifest invariants failed") from exc
    _require(
        document.root.attrib.get("name") == PRESET_DISPLAY_NAME,
        f"{document.source}: preset display name changed",
    )
    ids = [record.unique_id for record in document.semantics]
    _require(len(ids) == len(set(ids)), f"{document.source}: duplicate shortcut uniqueId")
    identities = [record.identity for record in document.semantics]
    _require(
        len(identities) == len(set(identities)),
        f"{document.source}: duplicate (raw_key, role, input_path)",
    )

    by_raw = {control.raw_key: control for control in controls}
    actual_raw = {record.raw_key for record in document.semantics}
    _require(
        actual_raw == set(by_raw),
        f"{document.source}: shortcut raw-key set does not match 148 controls",
    )
    for record in document.semantics:
        control = by_raw[record.raw_key]
        for _, path, _, _ in record.ordered_paths:
            match = LAYER_IN_PATH_RE.match(path)
            _require(match is not None, f"{document.source}: invalid path {path!r}")
            _require(
                int(match.group(1)) == control.layer,
                f"{document.source}: path layer mismatch for {control.midi_label}",
            )
        if control.is_button:
            _require(
                record.role == "button_connect",
                f"{document.source}: note {control.midi_label} is not button_connect",
            )
            connect = f"/composition/layers/{control.layer}/clips/1/connect"
            connected = f"/composition/layers/{control.layer}/clips/1/connected"
            _require(
                record.param_node_name == ""
                and record.behaviour == 1028
                and record.input_device == MIDI_DEVICE_NAME
                and record.output_device_or_none == MIDI_DEVICE_NAME
                and record.raw_value == "0"
                and record.num_steps == 128,
                f"{document.source}: button schema changed for {control.midi_label}",
            )
            _require(
                record.ordered_paths
                == (
                    ("InputPath", connect, "1", "11"),
                    ("OutputPath", connect, "1", "11"),
                    ("InputSiblingPath", connected, "1", "-1"),
                    ("OutputSiblingPath", connected, "1", "-1"),
                ),
                f"{document.source}: button paths changed for {control.midi_label}",
            )
            _require(
                tuple(name for name, _ in record.named_values)
                == (
                    "Connected",
                    "Connected & previewing",
                    "Disconnected",
                    "Empty",
                    "Off",
                    "Previewing",
                ),
                f"{document.source}: button feedback values changed for {control.midi_label}",
            )
        else:
            _require(
                record.role != "button_connect",
                f"{document.source}: CC {control.midi_label} classified as a button",
            )
    for control in controls:
        records = [r for r in document.semantics if r.raw_key == control.raw_key]
        _require(records, f"{document.source}: missing {control.midi_label}")
        if control.is_button:
            _require(
                len(records) == 1,
                f"{document.source}: button {control.midi_label} has {len(records)} mappings",
            )


def _strip_layout_whitespace(element: ET.Element) -> None:
    if element.text is not None and not element.text.strip():
        element.text = None
    if element.tail is not None and not element.tail.strip():
        element.tail = None
    for child in list(element):
        _strip_layout_whitespace(child)


def _canonical_element_bytes(element: ET.Element) -> bytes:
    clone = copy.deepcopy(element)
    _strip_layout_whitespace(clone)
    return ET.tostring(clone, encoding="utf-8", short_empty_elements=True)


def _strict_element_signature(element: ET.Element) -> tuple[object, ...]:
    text = element.text if element.text is not None and element.text.strip() else None
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        text,
        tuple(_strict_element_signature(child) for child in list(element)),
    )


def _binary64_decimal_token(value: str) -> tuple[str, str]:
    """Return an exact token for a finite decimal's IEEE-754 binary64 value.

    Avenue parses ValueRange bounds as doubles and writes the exact decimal
    expansion of those doubles when it persists a loaded preset.  Invalid,
    non-finite, and overflowing values deliberately remain literal so this
    helper never turns malformed XML into an accepted numeric value.
    """

    try:
        decimal_value = Decimal(value)
        binary_value = float(decimal_value)
    except (InvalidOperation, OverflowError, ValueError):
        return ("literal", value)
    if not decimal_value.is_finite() or not math.isfinite(binary_value):
        return ("literal", value)
    return ("binary64", binary_value.hex())


def _loaded_generated_element_signature(element: ET.Element) -> tuple[object, ...]:
    """Strict XML signature with Avenue's ValueRange double rewrite normalized.

    Only ValueRange ``min`` and ``max`` receive numeric treatment.  Every tag,
    child position, text node, other attribute, and non-equivalent bound stays
    exact.  This signature is used solely for allowlisted generated CC records;
    protected records continue through ``_strict_element_signature`` and
    ``_canonical_element_bytes`` unchanged.
    """

    text = element.text if element.text is not None and element.text.strip() else None
    attributes: list[tuple[str, object]] = []
    for name, value in sorted(element.attrib.items()):
        normalized: object = value
        if element.tag == "ValueRange" and name in {"min", "max"}:
            normalized = _binary64_decimal_token(value)
        attributes.append((name, normalized))
    return (
        element.tag,
        tuple(attributes),
        text,
        tuple(
            _loaded_generated_element_signature(child) for child in list(element)
        ),
    )


def _loaded_generated_shape_signature(element: ET.Element) -> tuple[object, ...]:
    """Return the generated-record signature with only range bounds masked.

    This is used when promoting an installed pilot to an accepted full build.
    A live measurement can legitimately refine a pilot's calibrated bounds,
    but it must not change any other XML structure or shortcut field.
    """

    clone = copy.deepcopy(element)
    value_ranges = clone.findall("ValueRange")
    _require(
        len(value_ranges) <= 1,
        "generated shortcut contains multiple ValueRange elements",
    )
    if value_ranges:
        value_range = value_ranges[0]
        _require(
            set(value_range.attrib) == {"min", "max"},
            "generated shortcut ValueRange attributes changed",
        )
        value_range.attrib["min"] = "__CALIBRATION_MIN__"
        value_range.attrib["max"] = "__CALIBRATION_MAX__"
    return _loaded_generated_element_signature(clone)


def serialize_preset_root(root: ET.Element) -> bytes:
    clone = copy.deepcopy(root)
    _strip_layout_whitespace(clone)
    ET.indent(clone, space="  ")
    payload = ET.tostring(
        clone,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )
    return payload + (b"" if payload.endswith(b"\n") else b"\n")


def control_record(control: Control) -> dict[str, object]:
    record = asdict(control)
    record.update(
        x=control.x,
        y=control.y,
        raw_key=str(control.raw_key),
        midi_label=control.midi_label,
        display_text=control.display_text,
    )
    return record


def build_manifest_bytes(controls: Sequence[Control] | None = None) -> bytes:
    selected = list(controls or build_controls())
    try:
        validate_controls(selected)
    except AssertionError as exc:
        raise ValidationError("control manifest invariants failed") from exc
    return (
        json.dumps(
            [control_record(control) for control in selected],
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _contains_placeholder(value: object) -> bool:
    if isinstance(value, str):
        lowered = value.strip().lower()
        return "placeholder" in lowered or lowered.startswith("generated")
    if isinstance(value, Mapping):
        return any(_contains_placeholder(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_placeholder(item) for item in value)
    return False


def _decimal(value: object, context: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{context} must be numeric, got {value!r}") from exc
    _require(parsed.is_finite(), f"{context} must be finite")
    return parsed


def _decimal_xml(value: object, context: str) -> str:
    parsed = _decimal(value, context)
    rendered = format(parsed, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _manifest_artifact_candidates(key: str, manifest_path: Path) -> tuple[Path, ...]:
    artifact_path = Path(key)
    if artifact_path.is_absolute():
        return (artifact_path.resolve(),)
    candidates = (
        (PROJECT_ROOT / artifact_path).resolve(),
        (manifest_path.parent / artifact_path).resolve(),
        (manifest_path.parent / artifact_path.name).resolve(),
    )
    return tuple(dict.fromkeys(candidates))


def _validated_manifest_artifacts(
    manifest: Mapping[str, object],
    manifest_path: Path,
) -> dict[str, tuple[Path, Mapping[str, object], bytes]]:
    artifacts = manifest.get("artifacts")
    _require(isinstance(artifacts, Mapping), "build manifest artifacts must be an object")
    by_basename: dict[str, tuple[Path, Mapping[str, object], bytes]] = {}
    for key, value in artifacts.items():
        _require(
            isinstance(key, str) and bool(key),
            "build manifest artifact keys must be nonempty strings",
        )
        _require(
            isinstance(value, Mapping),
            f"build manifest metadata must be an object for {key!r}",
        )
        expected_sha = value.get("sha256")
        expected_bytes = value.get("bytes")
        _require(_valid_sha256(expected_sha), f"artifact {key!r} has invalid SHA-256")
        _require(
            isinstance(expected_bytes, int)
            and not isinstance(expected_bytes, bool)
            and expected_bytes >= 0,
            f"artifact {key!r} has invalid byte count",
        )
        matching: list[tuple[Path, bytes]] = []
        for candidate in _manifest_artifact_candidates(key, manifest_path):
            if not candidate.is_file():
                continue
            payload = _required_bytes(candidate, f"build artifact {key}")
            if len(payload) == expected_bytes and sha256_bytes(payload) == str(expected_sha).lower():
                matching.append((candidate, payload))
        _require(
            len(matching) == 1,
            f"artifact {key!r} is missing, ambiguous, or differs from its manifest hash",
        )
        basename = Path(key).name
        _require(
            basename not in by_basename,
            f"build manifest contains duplicate artifact basename {basename!r}",
        )
        by_basename[basename] = (matching[0][0], value, matching[0][1])

    missing = REQUIRED_ARTIFACT_BASENAMES - set(by_basename)
    _require(
        not missing,
        "build manifest is incomplete; missing artifacts: " + ", ".join(sorted(missing)),
    )
    return by_basename


def _validate_json_build_artifacts(
    by_basename: Mapping[str, tuple[Path, Mapping[str, object], bytes]],
    *,
    build_id: str,
    status: str,
) -> dict[str, Mapping[str, object]]:
    parsed: dict[str, Mapping[str, object]] = {}
    for basename in sorted(JSON_BUILD_ARTIFACT_BASENAMES):
        path, _, payload = by_basename[basename]
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON artifact at {path}: {exc}") from exc
        _require(isinstance(value, Mapping), f"JSON artifact {basename} must be an object")
        _require(value.get("schema_version") == 1, f"{basename} schema_version must be 1")
        _require(value.get("build_id") == build_id, f"{basename} build_id mismatch")
        if "status" in value:
            _require(value.get("status") == status, f"{basename} status mismatch")
        if basename == "APC40_visual_qa_live_controls.json":
            _require(
                value.get("artifact_role") == "typed_live_controls",
                "live-controls artifact_role must be typed_live_controls",
            )
        parsed[basename] = value
    for basename, (_, _, payload) in by_basename.items():
        if basename.lower().endswith(".png"):
            _require(
                payload.startswith(b"\x89PNG\r\n\x1a\n"),
                f"{basename} does not have a PNG signature",
            )
        _require(
            b"connect_continuous" not in payload,
            f"{basename} contains the retired generic dispatcher marker",
        )
    return parsed


def _validate_accepted_metrics(metrics: object) -> None:
    _require(isinstance(metrics, Mapping) and bool(metrics), "accepted live tag metrics missing")
    for layer in (*range(94, 102), 143, 144):
        candidate = metrics.get(str(layer))
        if candidate is None:
            candidate = metrics.get("horizontal" if layer == 144 else "vertical")
        if isinstance(candidate, Mapping):
            candidate = candidate.get("ink_box_px")
        _require(
            isinstance(candidate, (list, tuple)) and len(candidate) == 2,
            f"accepted live tag metrics lack layer {layer} ink_box_px",
        )
        _require(
            all(
                isinstance(item, int)
                and not isinstance(item, bool)
                and 0 < item <= maximum
                for item, maximum in zip(candidate, (92, 42))
            ),
            f"accepted live tag metrics are invalid for layer {layer}",
        )


def _validate_parent_artifact_hashes(value: object) -> None:
    _require(
        isinstance(value, Mapping) and bool(value),
        "accepted calibration must bind measurement parent artifact hashes",
    )
    normalized: dict[str, Mapping[str, object]] = {}
    for key, metadata in value.items():
        _require(isinstance(key, str) and bool(key), "parent artifact key is invalid")
        _require(isinstance(metadata, Mapping), f"parent artifact {key!r} must be an object")
        _require(_valid_sha256(metadata.get("sha256")), f"parent artifact {key!r} hash is invalid")
        byte_count = metadata.get("bytes")
        _require(
            isinstance(byte_count, int)
            and not isinstance(byte_count, bool)
            and byte_count >= 0,
            f"parent artifact {key!r} byte count is invalid",
        )
        basename = Path(key).name
        _require(basename not in normalized, f"duplicate parent artifact basename {basename!r}")
        normalized[basename] = metadata
    missing = ACCEPTED_PARENT_HASH_BASENAMES - set(normalized)
    _require(
        not missing,
        "accepted lineage misses parent artifacts: " + ", ".join(sorted(missing)),
    )


def load_calibration(
    path: Path,
    *,
    mode: str,
    build_manifest_path: Path | None,
    test_only: bool = False,
) -> CalibrationContract:
    _require(mode in {"pilot", "full"}, f"unsupported candidate mode {mode!r}")
    raw_bytes = _required_bytes(path, "calibration")
    try:
        data = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid calibration JSON at {path}: {exc}") from exc
    _require(isinstance(data, Mapping), "calibration root must be an object")
    _require(data.get("schema_version") == 1, "calibration schema_version must be 1")
    _require(isinstance(data.get("build_id"), str) and data["build_id"], "missing build_id")
    status = data.get("status")
    _require(
        status in {"provisional", "accepted"},
        "calibration status must be provisional or accepted",
    )
    if status == "provisional":
        _require(data.get("parent_build_id") is None, "provisional parent_build_id must be null")
        _require(data.get("measurement_sha256") is None, "provisional measurement hash must be null")
        _require(
            data.get("measurement_parent_artifact_hashes") is None,
            "provisional measurement parent hashes must be null",
        )
        _require(
            data.get("accepted_live_tag_metrics") is None,
            "provisional accepted-live metrics must be null",
        )
    else:
        _require(
            isinstance(data.get("parent_build_id"), str)
            and bool(data["parent_build_id"])
            and data["parent_build_id"] != data["build_id"],
            "accepted calibration must name a distinct provisional parent build",
        )
        measurement_hash = data.get("measurement_sha256")
        _require(
            _valid_sha256(measurement_hash),
            "accepted calibration must contain a SHA-256 measurement hash",
        )
        _validate_parent_artifact_hashes(data.get("measurement_parent_artifact_hashes"))
        _validate_accepted_metrics(data.get("accepted_live_tag_metrics"))
    if mode == "full":
        _require(status == "accepted", "full candidate requires accepted calibration")
        _require(
            not _contains_placeholder(data),
            "full candidate rejects placeholder calibration values",
        )

    domain = data.get("position_domain")
    _require(
        isinstance(domain, list)
        and len(domain) == 2
        and [_decimal(item, "position_domain") for item in domain]
        == [Decimal("-32768"), Decimal("32768")],
        "position_domain must be [-32768, 32768]",
    )
    rotation_domain = data.get("rotation_domain_deg")
    _require(
        isinstance(rotation_domain, list)
        and len(rotation_domain) == 2
        and [_decimal(item, "rotation_domain_deg") for item in rotation_domain]
        == [Decimal("-180"), Decimal("180")],
        "rotation_domain_deg must be [-180, 180]",
    )
    knob_rest = data.get("knob_rest_degrees")
    _require(
        isinstance(knob_rest, list)
        and len(knob_rest) == 2
        and [_decimal(item, "knob_rest_degrees") for item in knob_rest]
        == [Decimal("-135"), Decimal("135")],
        "knob_rest_degrees must be [-135, 135]",
    )
    tempo_relative = data.get("tempo_relative")
    _require(isinstance(tempo_relative, Mapping), "missing tempo_relative")
    _require(
        str(tempo_relative.get("step")) == TEMPO_RELATIVE_STEP
        and tempo_relative.get("num_steps") == 480,
        "tempo_relative schema does not match the proven mapping",
    )
    _require(
        data.get("position_y_visual_direction") == "positive_down",
        "position_y_visual_direction must be positive_down",
    )
    opacity = data.get("opacity_ranges_by_category")
    _require(isinstance(opacity, Mapping), "missing opacity_ranges_by_category")
    expected_opacity = {
        "fader": (Decimal("0.65"), Decimal("1")),
        "crossfader": (Decimal("0.65"), Decimal("1")),
        "rotary": (Decimal("0.35"), Decimal("1")),
    }
    for category, expected in expected_opacity.items():
        values = opacity.get(category)
        _require(
            isinstance(values, list) and len(values) == 2,
            f"missing {category} opacity range",
        )
        actual = tuple(_decimal(item, f"{category} opacity") for item in values)
        _require(actual == expected, f"unexpected {category} opacity range {actual}")

    motion = data.get("motion_ranges_by_layer")
    _require(isinstance(motion, Mapping), "missing motion_ranges_by_layer")
    required_layers = (
        frozenset((94, 102))
        if mode == "pilot"
        else (VERTICAL_FADER_LAYERS | {CROSSFADER_LAYER} | (ROTARY_LAYERS - {148}))
    )
    for layer in sorted(required_layers):
        entry = motion.get(str(layer))
        _require(isinstance(entry, Mapping), f"missing motion calibration for layer {layer}")
        value_range = entry.get("xml_value_range")
        _require(
            isinstance(value_range, list) and len(value_range) == 2,
            f"layer {layer} xml_value_range must contain two endpoints",
        )
        endpoints = tuple(
            _decimal(item, f"layer {layer} motion endpoint") for item in value_range
        )
        _require(
            _decimal(entry.get("value_at_cc0"), f"layer {layer} value_at_cc0")
            == endpoints[0]
            and _decimal(entry.get("value_at_cc127"), f"layer {layer} value_at_cc127")
            == endpoints[1],
            f"layer {layer} named CC endpoints disagree with xml_value_range",
        )
        _require(
            all(Decimal("0") <= item <= Decimal("1") for item in endpoints),
            f"layer {layer} endpoints are outside normalized range",
        )
        axis = str(entry.get("axis", "")).lower()
        if layer in VERTICAL_FADER_LAYERS:
            _require(axis == "y", f"layer {layer} must use y motion")
            _require(
                endpoints[0] > endpoints[1],
                f"layer {layer} must map CC0 bottom to CC127 top (descending)",
            )
        elif layer == CROSSFADER_LAYER:
            _require(axis == "x", "crossfader must use x motion")
            _require(
                endpoints[0] < endpoints[1],
                "crossfader must map CC0 left to CC127 right",
            )
        else:
            _require(
                axis in {"rotation_z", "rotationz", "z"},
                f"layer {layer} must use Rotation Z motion",
            )
            _require(
                endpoints == (Decimal("0.125"), Decimal("0.875")),
                f"layer {layer} rotary range must be 0.125..0.875",
            )

    manifest_sha: str | None = None
    if build_manifest_path is None:
        _require(test_only, "build manifest is required for non-test candidates")
    else:
        manifest_bytes = _required_bytes(build_manifest_path, "build manifest")
        manifest_sha = sha256_bytes(manifest_bytes)
        try:
            manifest = json.loads(manifest_bytes)
        except json.JSONDecodeError as exc:
            raise ValidationError(
                f"invalid build manifest JSON at {build_manifest_path}: {exc}"
            ) from exc
        _require(isinstance(manifest, Mapping), "build manifest root must be an object")
        _require(manifest.get("schema_version") == 1, "build manifest schema must be 1")
        manifest_test_only = manifest.get("test_only", False)
        _require(
            isinstance(manifest_test_only, bool),
            "build manifest test_only must be a boolean when present",
        )
        _require(
            manifest_test_only is test_only,
            "build manifest test_only status does not match candidate mode",
        )
        _require(
            manifest.get("build_id") == data["build_id"],
            "calibration/build-manifest build_id mismatch",
        )
        _require(
            manifest.get("status") == data["status"],
            "calibration/build-manifest status mismatch",
        )
        if status == "accepted":
            _require(
                manifest.get("parent_build_id") == data["parent_build_id"],
                "accepted build-manifest parent_build_id mismatch",
            )
            _require(
                manifest.get("measurement_sha256") == data["measurement_sha256"],
                "accepted build-manifest measurement_sha256 mismatch",
            )
        else:
            _require(
                manifest.get("parent_build_id") is None,
                "provisional build-manifest parent_build_id must be null",
            )
            _require(
                manifest.get("measurement_sha256") is None,
                "provisional build-manifest measurement_sha256 must be null",
            )
        artifacts = _validated_manifest_artifacts(manifest, build_manifest_path)
        parsed_artifacts = _validate_json_build_artifacts(
            artifacts,
            build_id=str(data["build_id"]),
            status=str(status),
        )
        calibration_artifact_path, entry, calibration_artifact_bytes = artifacts[
            "APC40_visual_qa_calibration.json"
        ]
        _require(
            calibration_artifact_path == path.resolve(),
            "build manifest calibration path does not match the consumed calibration",
        )
        _require(
            calibration_artifact_bytes == raw_bytes
            and entry.get("sha256") == sha256_bytes(raw_bytes),
            "build manifest calibration SHA-256 mismatch",
        )
        _require(
            entry.get("bytes") == len(raw_bytes),
            "build manifest calibration byte count mismatch",
        )
        _require(
            parsed_artifacts["APC40_visual_qa_calibration.json"] == data,
            "parsed calibration artifact differs from consumed calibration",
        )
        report = parsed_artifacts["APC40_visual_qa_renderer_report.json"]
        report_inputs = report.get("inputs")
        _require(isinstance(report_inputs, Mapping), "renderer report inputs are missing")
        if status == "accepted":
            _require(
                report_inputs.get("measurement_sha256") == data["measurement_sha256"],
                "renderer report measurement hash disagrees with accepted calibration",
            )
            measurement_value = report_inputs.get("measurement")
            _require(
                isinstance(measurement_value, str) and bool(measurement_value),
                "renderer report does not name the accepted measurement artifact",
            )
            measurement_path = Path(measurement_value)
            if not measurement_path.is_absolute():
                measurement_path = (
                    artifacts["APC40_visual_qa_renderer_report.json"][0].parent
                    / measurement_path
                )
            measurement_bytes = _required_bytes(
                measurement_path.resolve(), "accepted live tag measurement"
            )
            _require(
                sha256_bytes(measurement_bytes) == data["measurement_sha256"],
                "accepted live tag measurement hash mismatch",
            )
        else:
            _require(
                report_inputs.get("measurement") is None
                and report_inputs.get("measurement_sha256") is None,
                "provisional renderer report must not reference a live measurement",
            )

    return CalibrationContract(
        path=path.resolve(),
        raw_bytes=raw_bytes,
        data=data,
        build_manifest_path=build_manifest_path.resolve() if build_manifest_path else None,
        build_manifest_sha256=manifest_sha,
        test_only=test_only,
    )


def _motion_range(calibration: CalibrationContract, layer: int) -> tuple[str, str]:
    motion = calibration.data["motion_ranges_by_layer"]
    assert isinstance(motion, Mapping)
    entry = motion[str(layer)]
    assert isinstance(entry, Mapping)
    values = entry["xml_value_range"]
    assert isinstance(values, list)
    return (
        _decimal_xml(values[0], f"layer {layer} motion min"),
        _decimal_xml(values[1], f"layer {layer} motion max"),
    )


def _opacity_range(calibration: CalibrationContract, control: Control) -> tuple[str, str]:
    category = (
        "fader"
        if control.layer in VERTICAL_FADER_LAYERS
        else "crossfader"
        if control.layer == CROSSFADER_LAYER
        else "rotary"
    )
    opacity = calibration.data["opacity_ranges_by_category"]
    assert isinstance(opacity, Mapping)
    values = opacity[category]
    assert isinstance(values, list)
    return (
        _decimal_xml(values[0], f"{category} opacity min"),
        _decimal_xml(values[1], f"{category} opacity max"),
    )


def _wake_shortcut(control: Control, unique_id: int) -> ET.Element:
    shortcut = ET.Element(
        "Shortcut",
        name="Shortcut",
        uniqueId=str(unique_id),
        paramNodeName="ParamEvent",
        behaviour="1028",
        inputDeviceName=MIDI_DEVICE_NAME,
    )
    path = f"/composition/layers/{control.layer}/clips/1/connect"
    for name in ("InputPath", "OutputPath"):
        ET.SubElement(
            shortcut,
            "ShortcutPath",
            name=name,
            path=path,
            translationType="1",
            allowedTranslationTypes="11",
        )
    ET.SubElement(
        shortcut,
        "RawInputMessage",
        key=str(control.raw_key),
        value="1",
        numSteps="128",
    )
    named = ET.SubElement(shortcut, "NamedValues")
    ET.SubElement(named, "Value", first="Disconnected", second="1")
    return shortcut


def _absolute_shortcut(
    control: Control,
    unique_id: int,
    path: str,
    minimum: str,
    maximum: str,
) -> ET.Element:
    shortcut = ET.Element(
        "Shortcut",
        name="Shortcut",
        uniqueId=str(unique_id),
        paramNodeName="ParamRange",
        behaviour="8",
        inputDeviceName=MIDI_DEVICE_NAME,
    )
    for name in ("InputPath", "OutputPath"):
        ET.SubElement(
            shortcut,
            "ShortcutPath",
            name=name,
            path=path,
            translationType="1",
            allowedTranslationTypes="11",
        )
    ET.SubElement(shortcut, "Subtarget", type="5", optionIndex="-1")
    ET.SubElement(shortcut, "ValueRange", min=minimum, max=maximum)
    ET.SubElement(
        shortcut,
        "RawInputMessage",
        key=str(control.raw_key),
        value="1",
        numSteps="128",
    )
    return shortcut


def _tempo_shortcut(control: Control, unique_id: int) -> ET.Element:
    path = f"/composition/layers/{control.layer}/clips/1/video/effects/transform/rotationz"
    shortcut = ET.Element(
        "Shortcut",
        name="Shortcut",
        uniqueId=str(unique_id),
        paramNodeName="ParamRange",
        behaviour="16392",
        inputDeviceName=MIDI_DEVICE_NAME,
    )
    for name in ("InputPath", "OutputPath"):
        ET.SubElement(
            shortcut,
            "ShortcutPath",
            name=name,
            path=path,
            translationType="1",
            allowedTranslationTypes="1",
        )
    ET.SubElement(shortcut, "Subtarget", type="5", optionIndex="-1")
    ET.SubElement(
        shortcut,
        "RawInputMessage",
        key=str(control.raw_key),
        value=TEMPO_RELATIVE_STEP,
        numSteps="480",
    )
    return shortcut


def _desired_shortcuts(
    control: Control,
    base_id: int,
    calibration: CalibrationContract,
) -> list[ET.Element]:
    wake = _wake_shortcut(control, base_id + 1000)
    if control.layer == 148:
        return [wake, _tempo_shortcut(control, base_id)]

    clip_video = f"/composition/layers/{control.layer}/clips/1/video"
    opacity_min, opacity_max = _opacity_range(calibration, control)
    opacity = _absolute_shortcut(
        control,
        base_id,
        f"{clip_video}/opacity",
        opacity_min,
        opacity_max,
    )
    motion_min, motion_max = _motion_range(calibration, control.layer)
    if control.layer in VERTICAL_FADER_LAYERS:
        target = "positiony"
    elif control.layer == CROSSFADER_LAYER:
        target = "positionx"
    elif control.layer in ROTARY_LAYERS:
        target = "rotationz"
    else:
        raise ValidationError(f"unclassified continuous layer {control.layer}")
    motion = _absolute_shortcut(
        control,
        base_id + 2000,
        f"{clip_video}/effects/transform/{target}",
        motion_min,
        motion_max,
    )
    return [wake, opacity, motion]


def _base_record(records: Sequence[ShortcutSemantic], control: Control) -> ShortcutSemantic:
    priorities = (
        ("tempo_motion", "legacy_cc")
        if control.layer == 148
        else ("opacity", "legacy_cc")
    )
    for role in priorities:
        matches = [record for record in records if record.role == role]
        if matches:
            _require(
                len(matches) == 1,
                f"{control.midi_label} has multiple candidate base records for {role}",
            )
            return matches[0]
    raise ValidationError(f"{control.midi_label} has no existing value record")


def _raw_key_from_element(element: ET.Element) -> int:
    return int(_only_child(element, "RawInputMessage", "Shortcut").attrib["key"])


def _protected_elements_by_raw(
    document: PresetDocument, raw_key: int
) -> tuple[bytes, ...]:
    return tuple(
        _canonical_element_bytes(element)
        for element in document.shortcuts
        if _raw_key_from_element(element) == raw_key
    )


def _replace_cc_records(
    baseline: PresetDocument,
    controls: Sequence[Control],
    selected_layers: frozenset[int],
    calibration: CalibrationContract,
) -> ET.Element:
    by_layer = {control.layer: control for control in controls}
    selected = [by_layer[layer] for layer in sorted(selected_layers)]
    selected_raw = {control.raw_key for control in selected}
    records_by_raw: dict[int, list[ShortcutSemantic]] = {
        control.raw_key: [
            record for record in baseline.semantics if record.raw_key == control.raw_key
        ]
        for control in selected
    }
    all_by_id = {record.unique_id: record for record in baseline.semantics}
    elements_by_id = {
        shortcut_semantic(element).unique_id: element for element in baseline.shortcuts
    }
    replacements: dict[int, list[ET.Element]] = {}
    derived_ids: set[int] = set()
    for control in selected:
        base = _base_record(records_by_raw[control.raw_key], control)
        desired = _desired_shortcuts(control, base.unique_id, calibration)
        emitted: list[ET.Element] = []
        for generated in desired:
            semantic = shortcut_semantic(generated)
            _require(
                semantic.unique_id not in derived_ids,
                f"derived ID {semantic.unique_id} is duplicated",
            )
            derived_ids.add(semantic.unique_id)
            owner = all_by_id.get(semantic.unique_id)
            if owner is not None and owner.raw_key != control.raw_key:
                raise ValidationError(
                    f"derived ID {semantic.unique_id} collides with protected/different "
                    f"mapping for raw key {owner.raw_key}"
                )
            if owner is None:
                emitted.append(generated)
                continue
            owner_element = elements_by_id[semantic.unique_id]
            if _loaded_generated_element_signature(
                owner_element
            ) == _loaded_generated_element_signature(generated):
                emitted.append(copy.deepcopy(owner_element))
                continue
            if (
                owner.raw_key == control.raw_key
                and owner.role == semantic.role
                and _loaded_generated_shape_signature(owner_element)
                == _loaded_generated_shape_signature(generated)
            ):
                # An installed pilot may carry a prior, provisional calibrated
                # range. Full promotion deliberately rewrites that allowlisted
                # generated record to the accepted B1 range while preserving
                # its ID, raw key, role, and exact XML shape.
                emitted.append(generated)
                continue
            if owner.unique_id == base.unique_id and owner == base:
                # The existing value record deliberately donates its base ID to
                # opacity (or Tempo motion). It is the sole sanctioned
                # semantic rewrite of an occupied derived ID.
                emitted.append(generated)
                continue
            raise ValidationError(
                f"derived ID {semantic.unique_id} collides with a different mapping "
                f"for raw key {control.raw_key}"
            )
        replacements[control.raw_key] = emitted

    new_root = copy.deepcopy(baseline.root)
    new_managers = new_root.findall("ShortcutManager")
    _require(len(new_managers) == 1, "copied preset lost ShortcutManager")
    new_manager = new_managers[0]
    for child in list(new_manager):
        new_manager.remove(child)
    inserted: set[int] = set()
    for child in list(baseline.manager):
        if child.tag == "Shortcut":
            raw_key = _raw_key_from_element(child)
            if raw_key in selected_raw:
                if raw_key not in inserted:
                    for replacement in replacements[raw_key]:
                        new_manager.append(copy.deepcopy(replacement))
                    inserted.add(raw_key)
                continue
        new_manager.append(copy.deepcopy(child))
    _require(inserted == selected_raw, "not every selected CC was replaced")
    return new_root


def _records_by_raw(
    document: PresetDocument,
) -> dict[int, list[ShortcutSemantic]]:
    grouped: dict[int, list[ShortcutSemantic]] = {}
    for record in document.semantics:
        grouped.setdefault(record.raw_key, []).append(record)
    return grouped


def semantic_diff(
    before: PresetDocument,
    after: PresetDocument,
    allowed_raw_keys: Iterable[int],
) -> SemanticDiff:
    before_by_identity = {record.identity: record for record in before.semantics}
    after_by_identity = {record.identity: record for record in after.semantics}
    added: list[ShortcutSemantic] = []
    removed: list[ShortcutSemantic] = []
    changed: list[tuple[ShortcutSemantic, ShortcutSemantic]] = []
    all_identities = sorted(set(before_by_identity) | set(after_by_identity))
    for identity in all_identities:
        old = before_by_identity.get(identity)
        new = after_by_identity.get(identity)
        if old is None:
            assert new is not None
            added.append(new)
        elif new is None:
            removed.append(old)
        elif old != new:
            changed.append((old, new))
    changed_raw = sorted(
        {record.raw_key for record in added}
        | {record.raw_key for record in removed}
        | {old.raw_key for old, _ in changed}
    )
    allowed = tuple(sorted(set(allowed_raw_keys)))
    unexpected = set(changed_raw) - set(allowed)
    _require(
        not unexpected,
        f"semantic diff changed protected raw keys: {sorted(unexpected)}",
    )
    return SemanticDiff(
        allowed_raw_keys=allowed,
        changed_raw_keys=tuple(changed_raw),
        added=tuple(added),
        removed=tuple(removed),
        changed=tuple(changed),
    )


def _path_histogram(document: PresetDocument) -> Counter[str]:
    histogram: Counter[str] = Counter()
    for record in document.semantics:
        lower = record.input_path.lower()
        if lower.endswith("/connect"):
            histogram["connect"] += 1
        elif lower.endswith("/video/source/delay"):
            histogram["delay"] += 1
        elif lower.endswith("/opacity"):
            histogram["opacity"] += 1
        elif lower.endswith("/positiony"):
            histogram["positiony"] += 1
        elif lower.endswith("/positionx"):
            histogram["positionx"] += 1
        elif lower.endswith("/rotationz"):
            histogram["rotationz"] += 1
        else:
            raise ValidationError(f"uncounted path {record.input_path}")
    return histogram


def _assert_wake(record: ShortcutSemantic, control: Control) -> None:
    path = f"/composition/layers/{control.layer}/clips/1/connect"
    _require(record.role == "wake", f"{control.midi_label}: wake role missing")
    _require(record.param_node_name == "ParamEvent", "wake must use ParamEvent")
    _require(record.behaviour == 1028, "wake behaviour must be 1028")
    _require(record.input_device == MIDI_DEVICE_NAME, "wake MIDI input changed")
    _require(record.output_device_or_none is None, "wake must omit output device")
    _require(record.raw_value == "1" and record.num_steps == 128, "wake raw schema changed")
    _require(
        record.ordered_paths
        == (
            ("InputPath", path, "1", "11"),
            ("OutputPath", path, "1", "11"),
        ),
        "wake paths do not match proven schema",
    )
    _require(record.subtarget_or_none is None, "wake must not contain Subtarget")
    _require(record.value_range_or_none is None, "wake must not contain ValueRange")
    _require(
        record.named_values == (("Disconnected", "1"),),
        "wake NamedValues must contain only Disconnected=1",
    )


def _assert_selected_schema(
    document: PresetDocument,
    control: Control,
    calibration: CalibrationContract,
) -> None:
    records = [record for record in document.semantics if record.raw_key == control.raw_key]
    expected_roles = (
        ["wake", "tempo_motion"]
        if control.layer == 148
        else ["wake", "opacity", "absolute_motion"]
    )
    _require(
        Counter(record.role for record in records) == Counter(expected_roles),
        f"{control.midi_label}: role set mismatch",
    )
    base_id = (
        next(record.unique_id for record in records if record.role == "tempo_motion")
        if control.layer == 148
        else next(record.unique_id for record in records if record.role == "opacity")
    )
    elements_by_id = {
        shortcut_semantic(element).unique_id: element for element in document.shortcuts
    }
    expected_elements = _desired_shortcuts(control, base_id, calibration)
    for expected_element in expected_elements:
        expected_record = shortcut_semantic(expected_element)
        actual_element = elements_by_id.get(expected_record.unique_id)
        _require(
            actual_element is not None
            and _loaded_generated_element_signature(actual_element)
            == _loaded_generated_element_signature(expected_element),
            f"{control.midi_label}: generated shortcut schema/range mismatch",
        )
    for record in records:
        _require(
            "outputDeviceName" not in elements_by_id[record.unique_id].attrib,
            f"{control.midi_label}: generated {record.role} must physically omit "
            "outputDeviceName",
        )
    _assert_wake(next(record for record in records if record.role == "wake"), control)


def _assert_upgradeable_selected_schema(
    document: PresetDocument,
    control: Control,
    calibration: CalibrationContract,
) -> None:
    """Validate an installed pilot while allowing bounded range refinement."""

    records = [record for record in document.semantics if record.raw_key == control.raw_key]
    expected_roles = (
        ["wake", "tempo_motion"]
        if control.layer == 148
        else ["wake", "opacity", "absolute_motion"]
    )
    _require(
        Counter(record.role for record in records) == Counter(expected_roles),
        f"{control.midi_label}: role set mismatch",
    )
    base_id = (
        next(record.unique_id for record in records if record.role == "tempo_motion")
        if control.layer == 148
        else next(record.unique_id for record in records if record.role == "opacity")
    )
    elements_by_id = {
        shortcut_semantic(element).unique_id: element for element in document.shortcuts
    }
    expected_elements = _desired_shortcuts(control, base_id, calibration)
    for expected_element in expected_elements:
        expected_record = shortcut_semantic(expected_element)
        actual_element = elements_by_id.get(expected_record.unique_id)
        _require(
            actual_element is not None,
            f"{control.midi_label}: generated shortcut ID is missing",
        )
        assert actual_element is not None
        actual_record = shortcut_semantic(actual_element)
        if (
            expected_record.value_range_or_none is None
            or expected_record.role != "absolute_motion"
        ):
            _require(
                _loaded_generated_element_signature(actual_element)
                == _loaded_generated_element_signature(expected_element),
                f"{control.midi_label}: generated shortcut schema/range mismatch",
            )
            continue

        _require(
            _loaded_generated_shape_signature(actual_element)
            == _loaded_generated_shape_signature(expected_element),
            f"{control.midi_label}: generated shortcut shape mismatch",
        )
        actual_range = dict(actual_record.value_range_or_none or ())
        expected_range = dict(expected_record.value_range_or_none or ())
        actual_min = _decimal(actual_range.get("min"), "installed pilot range min")
        actual_max = _decimal(actual_range.get("max"), "installed pilot range max")
        expected_min = _decimal(expected_range.get("min"), "accepted range min")
        expected_max = _decimal(expected_range.get("max"), "accepted range max")
        _require(
            all(
                Decimal("0") <= endpoint <= Decimal("1")
                for endpoint in (actual_min, actual_max)
            ),
            f"{control.midi_label}: installed pilot range is outside 0..1",
        )
        actual_delta = actual_max - actual_min
        expected_delta = expected_max - expected_min
        _require(
            actual_delta != 0
            and expected_delta != 0
            and (actual_delta > 0) == (expected_delta > 0),
            f"{control.midi_label}: installed pilot range direction changed",
        )
        actual_span = abs(actual_delta)
        expected_span = abs(expected_delta)
        _require(
            expected_span * Decimal("0.75")
            <= actual_span
            <= expected_span * Decimal("1.25"),
            f"{control.midi_label}: installed pilot range span is not a bounded "
            "prior calibration",
        )
        actual_midpoint = (actual_min + actual_max) / Decimal("2")
        expected_midpoint = (expected_min + expected_max) / Decimal("2")
        _require(
            abs(actual_midpoint - expected_midpoint)
            <= expected_span * Decimal("0.25"),
            f"{control.midi_label}: installed pilot range center changed",
        )

    for record in records:
        _require(
            "outputDeviceName" not in elements_by_id[record.unique_id].attrib,
            f"{control.midi_label}: generated {record.role} must physically omit "
            "outputDeviceName",
        )
    _assert_wake(next(record for record in records if record.role == "wake"), control)


def _assert_headers_preserved(before: PresetDocument, after: PresetDocument) -> None:
    _require(before.root.tag == after.root.tag, "preset root tag changed")
    _require(before.root.attrib == after.root.attrib, "preset root/header attributes changed")
    before_non_manager = [
        _canonical_element_bytes(child)
        for child in list(before.root)
        if child.tag != "ShortcutManager"
    ]
    after_non_manager = [
        _canonical_element_bytes(child)
        for child in list(after.root)
        if child.tag != "ShortcutManager"
    ]
    _require(before_non_manager == after_non_manager, "preset non-shortcut header changed")
    _require(before.manager.attrib == after.manager.attrib, "ShortcutManager attributes changed")


def assert_pilot_document(
    document: PresetDocument,
    controls: Sequence[Control],
    calibration: CalibrationContract,
    *,
    allow_prior_calibration: bool = False,
) -> None:
    _require(len(document.semantics) == 153, "pilot must contain 153 shortcuts")
    by_layer = {control.layer: control for control in controls}
    for layer in PILOT_LAYERS:
        if allow_prior_calibration:
            _assert_upgradeable_selected_schema(
                document, by_layer[layer], calibration
            )
        else:
            _assert_selected_schema(document, by_layer[layer], calibration)
    for control in controls:
        records = [record for record in document.semantics if record.raw_key == control.raw_key]
        if control.is_button:
            _require(len(records) == 1 and records[0].role == "button_connect", "bad button")
        elif control.layer not in PILOT_LAYERS:
            _require(
                len(records) == 1 and records[0].role == "legacy_cc",
                f"pilot must preserve legacy mapping for {control.midi_label}",
            )
    _require(
        Counter(record.behaviour for record in document.semantics)
        == Counter({1028: 123, 8: 29, 16392: 1}),
        "pilot behaviour histogram mismatch",
    )
    _require(
        _path_histogram(document)
        == Counter(
            {
                "connect": 123,
                "delay": 25,
                "opacity": 2,
                "positiony": 1,
                "rotationz": 2,
            }
        ),
        "pilot path histogram mismatch",
    )
    for record in document.semantics:
        if record.raw_key >= CC_BASE and record.role != "legacy_cc":
            _require(
                record.output_device_or_none is None,
                "generated pilot records must omit outputDeviceName",
            )


def assert_full_document(
    document: PresetDocument,
    controls: Sequence[Control],
    calibration: CalibrationContract,
) -> None:
    _require(calibration.status == "accepted", "full assertions need accepted calibration")
    _require(len(document.semantics) == 203, "full preset must contain 203 shortcuts")
    for control in controls:
        if control.is_button:
            records = [r for r in document.semantics if r.raw_key == control.raw_key]
            _require(len(records) == 1 and records[0].role == "button_connect", "bad button")
        else:
            _assert_selected_schema(document, control, calibration)
    _require(
        Counter(record.behaviour for record in document.semantics)
        == Counter({1028: 148, 8: 54, 16392: 1}),
        "full behaviour histogram mismatch",
    )
    _require(
        _path_histogram(document)
        == Counter(
            {
                "connect": 148,
                "opacity": 27,
                "positiony": 9,
                "positionx": 1,
                "rotationz": 18,
            }
        ),
        "full path histogram mismatch",
    )
    for record in document.semantics:
        lower = record.input_path.lower()
        _require("/video/source/delay" not in lower, "full preset contains legacy delay")
        _require("/video/source/opacity" not in lower, "full preset contains source opacity")
        if record.raw_key >= CC_BASE:
            _require(
                record.input_device == MIDI_DEVICE_NAME,
                "continuous MIDI input device changed",
            )
            _require(
                record.output_device_or_none is None,
                "full continuous records must omit outputDeviceName",
            )


def _assert_protected_exact(
    before: PresetDocument,
    after: PresetDocument,
    allowed_raw_keys: set[int],
) -> None:
    before_sequence = [
        _canonical_element_bytes(element)
        for element in before.shortcuts
        if _raw_key_from_element(element) not in allowed_raw_keys
    ]
    after_sequence = [
        _canonical_element_bytes(element)
        for element in after.shortcuts
        if _raw_key_from_element(element) not in allowed_raw_keys
    ]
    _require(
        before_sequence == after_sequence,
        "protected shortcut element order/content changed",
    )
    before_keys = {record.raw_key for record in before.semantics}
    for raw_key in sorted(before_keys - allowed_raw_keys):
        _require(
            _protected_elements_by_raw(before, raw_key)
            == _protected_elements_by_raw(after, raw_key),
            f"protected XML element changed for raw key {raw_key}",
        )


def _load_repo_reference(
    path: Path,
    controls: Sequence[Control],
) -> PresetDocument:
    reference = parse_preset_file(path, controls=controls)
    _require(
        len(reference.semantics) == 148,
        "repo reference must contain exactly 148 pristine shortcuts",
    )
    for control in controls:
        records = [
            record for record in reference.semantics if record.raw_key == control.raw_key
        ]
        expected_role = "button_connect" if control.is_button else "legacy_cc"
        _require(
            len(records) == 1 and records[0].role == expected_role,
            f"repo reference is not pristine for {control.midi_label}",
        )
    _require(
        Counter(record.behaviour for record in reference.semantics)
        == Counter({1028: 120, 8: 28}),
        "repo reference behaviour histogram is not pristine",
    )
    return reference


def _reference_shape(record: ShortcutSemantic) -> tuple[object, ...]:
    return (
        record.unique_id,
        record.raw_key,
        record.num_steps,
        record.param_node_name,
        record.behaviour,
        record.input_device,
        record.output_device_or_none,
        record.ordered_paths,
        record.subtarget_or_none,
        record.value_range_or_none,
        tuple(name for name, _ in record.named_values),
        record.role,
        record.input_path,
    )


def _assert_reference_compatible(
    reference: PresetDocument,
    baseline: PresetDocument,
    allowed_raw_keys: set[int],
) -> None:
    for raw_key in sorted(
        {record.raw_key for record in reference.semantics} - allowed_raw_keys
    ):
        expected = [
            _reference_shape(record)
            for record in reference.semantics
            if record.raw_key == raw_key
        ]
        observed = [
            _reference_shape(record)
            for record in baseline.semantics
            if record.raw_key == raw_key
        ]
        _require(
            observed == expected,
            f"canonical preset shape differs from repo reference for raw key {raw_key}",
        )


def build_candidate(
    *,
    mode: str,
    baseline_bytes: bytes,
    baseline_path: Path,
    calibration: CalibrationContract,
    controls: Sequence[Control] | None = None,
    repo_reference_path: Path = REPO_PRESET,
) -> CandidateResult:
    _require(mode in {"pilot", "full"}, f"unsupported mode {mode!r}")
    selected_controls = list(controls or build_controls())
    baseline = parse_preset_bytes(
        baseline_bytes,
        source=str(baseline_path),
        controls=selected_controls,
    )
    reference = _load_repo_reference(repo_reference_path, selected_controls)
    if mode == "full":
        _require(
            calibration.status == "accepted",
            "full candidate requires accepted calibration",
        )
        assert_pilot_document(
            baseline,
            selected_controls,
            calibration,
            allow_prior_calibration=True,
        )

    selected_layers = PILOT_LAYERS if mode == "pilot" else frozenset(
        control.layer for control in selected_controls if not control.is_button
    )
    selected_raw = {
        control.raw_key for control in selected_controls if control.layer in selected_layers
    }
    _assert_reference_compatible(reference, baseline, selected_raw)
    candidate_root = _replace_cc_records(
        baseline, selected_controls, selected_layers, calibration
    )
    candidate_bytes = serialize_preset_root(candidate_root)
    candidate = parse_preset_bytes(
        candidate_bytes,
        source=f"{mode}-candidate",
        controls=selected_controls,
    )
    _assert_headers_preserved(baseline, candidate)
    _assert_protected_exact(baseline, candidate, selected_raw)
    diff = semantic_diff(baseline, candidate, selected_raw)
    if mode == "pilot":
        assert_pilot_document(candidate, selected_controls, calibration)
    else:
        assert_full_document(candidate, selected_controls, calibration)

    # The serialized form is authoritative. Reparse and rerun all assertions.
    reparsed = parse_preset_bytes(
        candidate_bytes,
        source=f"{mode}-candidate-reparse",
        controls=selected_controls,
    )
    if mode == "pilot":
        assert_pilot_document(reparsed, selected_controls, calibration)
    else:
        assert_full_document(reparsed, selected_controls, calibration)
    _require(
        serialize_preset_root(reparsed.root) == candidate_bytes,
        "candidate serialization is not byte-deterministic",
    )
    return CandidateResult(
        mode=mode,
        baseline_path=baseline_path.resolve(),
        baseline_sha256=sha256_bytes(baseline_bytes),
        repo_reference_path=repo_reference_path.resolve(),
        repo_reference_sha256=reference.sha256,
        candidate_bytes=candidate_bytes,
        candidate_sha256=sha256_bytes(candidate_bytes),
        calibration=calibration,
        diff=diff,
        shortcut_count=len(candidate.semantics),
        installable=not calibration.test_only,
    )


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _semantic_diff_markdown(result: CandidateResult) -> bytes:
    lines = [
        f"# APC40 {result.mode.title()} Preset Semantic Diff",
        "",
        f"- Baseline SHA-256: `{result.baseline_sha256}`",
        f"- Candidate SHA-256: `{result.candidate_sha256}`",
        f"- Changed raw keys: {', '.join(str(key) for key in result.diff.changed_raw_keys)}",
        f"- Added mappings: {len(result.diff.added)}",
        f"- Removed mappings: {len(result.diff.removed)}",
        f"- Changed-in-place mappings: {len(result.diff.changed)}",
        "",
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _ensure_manifest_output_path(path: Path) -> None:
    resolved = path.resolve()
    _require(path.suffix.lower() != ".xml", "control manifest output may not be an XML path")
    _require(
        resolved not in {ACTIVE_PRESET.resolve(), REPO_PRESET.resolve()},
        "control manifest may not overwrite the active or repo preset",
    )


def write_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    _ensure_manifest_output_path(path)
    payload = build_manifest_bytes()
    _atomic_write_bytes(path, payload)
    _require(path.read_bytes() == payload, "manifest readback mismatch")
    return {"path": str(path.resolve()), "sha256": sha256_bytes(payload), "bytes": len(payload)}


def _ensure_campaign_output_path(path: Path, campaign_dir: Path) -> None:
    resolved = path.resolve()
    campaign = campaign_dir.resolve()
    _require(
        resolved == campaign or campaign in resolved.parents,
        f"candidate artifact must stay under campaign directory {campaign}",
    )
    forbidden = {ACTIVE_PRESET.parent.resolve(), REPO_PRESET.parent.resolve()}
    _require(
        not any(parent == resolved.parent or parent in resolved.parents for parent in forbidden),
        "candidate artifacts may not be written in active/repo preset directories",
    )


def write_candidate_artifacts(
    result: CandidateResult,
    campaign_dir: Path,
) -> dict[str, Path]:
    campaign_dir = campaign_dir.resolve()
    candidate_path = campaign_dir / f"APC40_visual_qa_{result.mode}_candidate.xml"
    diff_json_path = campaign_dir / f"APC40_visual_qa_{result.mode}_semantic_diff.json"
    diff_md_path = campaign_dir / f"APC40_visual_qa_{result.mode}_semantic_diff.md"
    metadata_path = campaign_dir / f"APC40_visual_qa_{result.mode}_candidate_metadata.json"
    for path in (candidate_path, diff_json_path, diff_md_path, metadata_path):
        _ensure_campaign_output_path(path, campaign_dir)

    diff_json = _json_bytes(result.diff.as_json())
    diff_md = _semantic_diff_markdown(result)
    _atomic_write_bytes(candidate_path, result.candidate_bytes)
    parsed = parse_preset_file(candidate_path)
    _require(parsed.sha256 == result.candidate_sha256, "candidate write/readback mismatch")
    _atomic_write_bytes(diff_json_path, diff_json)
    _atomic_write_bytes(diff_md_path, diff_md)
    metadata = {
        "schema_version": 1,
        "kind": "apc40_visual_qa_preset_candidate",
        "mode": result.mode,
        "preset_display_name": PRESET_DISPLAY_NAME,
        "baseline_path": str(result.baseline_path),
        "baseline_sha256": result.baseline_sha256,
        "repo_reference_sha256": result.repo_reference_sha256,
        "repo_reference_path": str(result.repo_reference_path),
        "repo_reference_sha256": result.repo_reference_sha256,
        "candidate_path": str(candidate_path),
        "candidate_sha256": result.candidate_sha256,
        "candidate_bytes": len(result.candidate_bytes),
        "shortcut_count": result.shortcut_count,
        "allowed_raw_keys": [str(key) for key in result.diff.allowed_raw_keys],
        "calibration_path": str(result.calibration.path),
        "calibration_sha256": result.calibration.sha256,
        "calibration_build_id": result.calibration.build_id,
        "calibration_status": result.calibration.status,
        "build_manifest_path": (
            str(result.calibration.build_manifest_path)
            if result.calibration.build_manifest_path
            else None
        ),
        "build_manifest_sha256": result.calibration.build_manifest_sha256,
        "semantic_diff_json_path": str(diff_json_path),
        "semantic_diff_json_sha256": sha256_bytes(diff_json),
        "semantic_diff_markdown_path": str(diff_md_path),
        "semantic_diff_markdown_sha256": sha256_bytes(diff_md),
        "installable": result.installable,
        "test_only": result.calibration.test_only,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    _atomic_write_bytes(metadata_path, _json_bytes(metadata))
    return {
        "candidate": candidate_path,
        "diff_json": diff_json_path,
        "diff_markdown": diff_md_path,
        "metadata": metadata_path,
    }


def _load_metadata(path: Path) -> Mapping[str, object]:
    raw = _required_bytes(path, "candidate metadata")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid candidate metadata at {path}: {exc}") from exc
    _require(isinstance(data, Mapping), "candidate metadata root must be an object")
    _require(data.get("schema_version") == 1, "candidate metadata schema must be 1")
    _require(
        data.get("kind") == "apc40_visual_qa_preset_candidate",
        "unexpected candidate metadata kind",
    )
    return data


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def validate_mutation_preflight(
    path: Path,
    *,
    expected_sha256: str,
    expected_stage: str,
    expected_active_sha256: str,
    now: datetime | None = None,
) -> Mapping[str, object]:
    _require(_valid_sha256(expected_sha256), "preflight SHA-256 is invalid")
    raw = _required_bytes(path, "mutation preflight")
    observed_sha = sha256_bytes(raw)
    if observed_sha != expected_sha256.lower():
        raise HashMismatch(
            f"preflight hash mismatch: expected {expected_sha256}, found {observed_sha}"
        )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid mutation preflight JSON at {path}: {exc}") from exc
    _require(isinstance(value, Mapping), "mutation preflight must be a JSON object")
    _require(value.get("schema_version") == 1, "mutation preflight schema_version must be 1")
    _require(value.get("stage") == expected_stage, "mutation preflight stage mismatch")
    _require(
        value.get("expected_layer_count") == 148,
        "mutation preflight must explicitly require 148 layers",
    )
    _require(
        value.get("actual_layer_count") == 148,
        "mutation preflight must report exactly 148 live layers",
    )

    timestamp = value.get("timestamp")
    _require(isinstance(timestamp, str) and bool(timestamp), "mutation preflight timestamp missing")
    try:
        captured = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError("mutation preflight timestamp is invalid") from exc
    _require(captured.tzinfo is not None, "mutation preflight timestamp must include timezone")
    current = now or datetime.now(timezone.utc)
    _require(current.tzinfo is not None, "preflight validation clock must include timezone")
    age = (current.astimezone(timezone.utc) - captured.astimezone(timezone.utc)).total_seconds()
    _require(
        age <= PREFLIGHT_MAX_AGE_SECONDS,
        "mutation preflight is older than 10 minutes",
    )
    _require(
        age >= -PREFLIGHT_FUTURE_TOLERANCE_SECONDS,
        "mutation preflight timestamp is unacceptably in the future",
    )

    processes = value.get("processes")
    _require(isinstance(processes, Mapping), "mutation preflight process inventory missing")
    avenue_pids = processes.get("avenue_pids")
    bridge_pids = processes.get("bridge_pids")
    watcher_pids = processes.get("watcher_pids")
    _require(
        isinstance(avenue_pids, list)
        and len(avenue_pids) == 1
        and all(isinstance(pid, int) and not isinstance(pid, bool) and pid > 0 for pid in avenue_pids),
        "mutation preflight must report exactly one Avenue PID",
    )
    _require(
        isinstance(bridge_pids, list)
        and len(bridge_pids) == 1
        and all(isinstance(pid, int) and not isinstance(pid, bool) and pid > 0 for pid in bridge_pids),
        "mutation preflight must report exactly one bridge PID",
    )
    _require(
        isinstance(watcher_pids, list) and not watcher_pids,
        "mutation preflight must report zero pulse watcher PIDs",
    )
    for product_field in ("native_product", "bridge_product"):
        product = value.get(product_field)
        _require(
            isinstance(product, Mapping)
            and str(product.get("name", "")).casefold() == "avenue",
            f"mutation preflight {product_field} did not identify Avenue",
        )

    fingerprint = value.get("composition_fingerprint")
    _require(isinstance(fingerprint, Mapping), "composition fingerprint missing")
    _require(
        fingerprint.get("name") == COMPOSITION_NAME,
        "mutation preflight composition name mismatch",
    )
    _require(
        fingerprint.get("width") == 1920 and fingerprint.get("height") == 1080,
        "mutation preflight composition must be 1920x1080",
    )
    column_ids = fingerprint.get("column_ids")
    layer_ids = fingerprint.get("layer_ids")
    clip_ids = fingerprint.get("clip_ids")
    _require(
        isinstance(column_ids, list) and len(column_ids) == 1,
        "mutation preflight composition must have one column",
    )
    _require(
        isinstance(layer_ids, list) and len(layer_ids) == 148,
        "mutation preflight composition must have 148 layer IDs",
    )
    _require(
        isinstance(clip_ids, list) and len(clip_ids) == 148,
        "mutation preflight composition must have 148 clip IDs",
    )
    identity = {
        "name": fingerprint["name"],
        "width": fingerprint["width"],
        "height": fingerprint["height"],
        "column_ids": column_ids,
        "layer_ids": layer_ids,
        "clip_ids": clip_ids,
    }
    _require(
        _valid_sha256(fingerprint.get("sha256"))
        and str(fingerprint["sha256"]).lower()
        == sha256_bytes(_canonical_json_bytes(identity)),
        "mutation preflight composition fingerprint hash mismatch",
    )
    validation = value.get("control_validation")
    _require(
        isinstance(validation, Mapping)
        and validation.get("layers") == 148
        and validation.get("names") == "exact"
        and validation.get("trigger_styles") == "exact",
        "mutation preflight control validation is incomplete",
    )
    active_hash = value.get("active_preset_sha256")
    if active_hash is not None:
        _require(
            _valid_sha256(active_hash)
            and str(active_hash).lower() == expected_active_sha256.lower(),
            "mutation preflight active preset hash mismatch",
        )
    return value


def _ensure_campaign_input_path(path: Path, campaign_dir: Path, label: str) -> Path:
    resolved = path.resolve()
    campaign = campaign_dir.resolve()
    _require(
        campaign in resolved.parents,
        f"{label} must stay under campaign directory {campaign}",
    )
    _require(
        resolved not in {ACTIVE_PRESET.resolve(), REPO_PRESET.resolve()},
        f"{label} may not use the active or repo preset",
    )
    _require(resolved.is_file(), f"{label} is missing: {resolved}")
    return resolved


def _load_hashed_json(
    path: Path,
    expected_sha256: str,
    label: str,
) -> Mapping[str, object]:
    _require(_valid_sha256(expected_sha256), f"{label} SHA-256 is invalid")
    raw = _required_bytes(path, label)
    observed = sha256_bytes(raw)
    if observed != expected_sha256.lower():
        raise HashMismatch(
            f"{label} hash mismatch: expected {expected_sha256}, found {observed}"
        )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid {label} JSON at {path}: {exc}") from exc
    _require(isinstance(value, Mapping), f"{label} must be a JSON object")
    return value


def _replace_active_bytes(
    *,
    target: Path,
    replacement_bytes: bytes,
    expected_before_sha256: str,
    expected_after_sha256: str,
    sleep_seconds: float = 0.5,
) -> None:
    _require(target.exists(), f"active preset is missing: {target}")
    current = sha256_file(target)
    if current != expected_before_sha256:
        raise HashMismatch(
            f"active hash changed: expected {expected_before_sha256}, found {current}"
        )
    temp = target.with_name(f".{target.name}.{uuid.uuid4().hex}.replace-tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(replacement_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        parse_preset_file(temp)
        _require(
            sha256_file(temp) == expected_after_sha256,
            "replacement temp-file hash mismatch",
        )
        _require(
            sha256_file(target) == expected_before_sha256,
            "active hash changed immediately before replacement",
        )
        for attempt in range(1, 4):
            try:
                os.replace(temp, target)
                break
            except PermissionError:
                observed = sha256_file(target)
                if observed == expected_after_sha256:
                    break
                if observed != expected_before_sha256:
                    raise HashMismatch(
                        "active preset changed during PermissionError retry"
                    )
                if attempt == 3:
                    raise
                time.sleep(sleep_seconds)
        final = sha256_file(target)
        if final != expected_after_sha256:
            raise HashMismatch(
                f"replacement verification failed: expected {expected_after_sha256}, "
                f"found {final}"
            )
    finally:
        if temp.exists():
            temp.unlink()


def install_candidate(
    *,
    candidate_path: Path,
    metadata_path: Path,
    active_path: Path,
    campaign_dir: Path,
    preflight_path: Path,
    preflight_sha256: str,
    sleep_seconds: float = 0.5,
) -> Mapping[str, object]:
    campaign_dir = campaign_dir.resolve()
    _ensure_campaign_input_path(candidate_path, campaign_dir, "candidate")
    _ensure_campaign_input_path(metadata_path, campaign_dir, "candidate metadata")
    metadata = _load_metadata(metadata_path)
    _require(metadata.get("installable") is True, "candidate is marked non-installable")
    _require(metadata.get("test_only") is False, "test-only candidate cannot be installed")
    mode = str(metadata.get("mode"))
    _require(mode in {"pilot", "full"}, "candidate metadata mode is invalid")
    candidate_bytes = _required_bytes(candidate_path, "candidate")
    candidate_hash = sha256_bytes(candidate_bytes)
    _require(
        candidate_hash == metadata.get("candidate_sha256"),
        "candidate SHA-256 does not match metadata",
    )
    _require(
        len(candidate_bytes) == metadata.get("candidate_bytes"),
        "candidate byte count does not match metadata",
    )
    expected_baseline = str(metadata.get("baseline_sha256"))
    _require(_valid_sha256(expected_baseline), "candidate baseline SHA-256 is invalid")
    active_bytes = _required_bytes(active_path, "active preset")
    if sha256_bytes(active_bytes) != expected_baseline:
        raise HashMismatch("active preset no longer matches candidate baseline")
    validate_mutation_preflight(
        preflight_path,
        expected_sha256=preflight_sha256,
        expected_stage=f"install-{mode}",
        expected_active_sha256=expected_baseline,
    )

    repo_reference_value = metadata.get("repo_reference_path")
    _require(
        isinstance(repo_reference_value, str) and bool(repo_reference_value),
        "candidate metadata lacks repo_reference_path",
    )
    repo_reference_path = Path(repo_reference_value)
    _require(
        repo_reference_path.resolve() == REPO_PRESET.resolve(),
        "candidate metadata does not name the canonical repo reference",
    )
    repo_reference = _load_repo_reference(REPO_PRESET, build_controls())
    _require(
        repo_reference.sha256 == metadata.get("repo_reference_sha256"),
        "repo reference changed since candidate generation",
    )

    calibration_path = Path(str(metadata["calibration_path"]))
    build_manifest_value = metadata.get("build_manifest_path")
    calibration = load_calibration(
        calibration_path,
        mode=mode,
        build_manifest_path=Path(str(build_manifest_value)) if build_manifest_value else None,
        test_only=False,
    )
    _require(
        calibration.sha256 == metadata.get("calibration_sha256"),
        "calibration hash differs from candidate metadata",
    )
    _require(
        calibration.build_manifest_sha256 == metadata.get("build_manifest_sha256"),
        "build manifest hash differs from candidate metadata",
    )
    rebuilt = build_candidate(
        mode=mode,
        baseline_bytes=active_bytes,
        baseline_path=active_path,
        calibration=calibration,
        repo_reference_path=REPO_PRESET,
    )
    _require(
        rebuilt.candidate_bytes == candidate_bytes,
        "candidate does not match deterministic rebuild from current baseline",
    )
    diff_json_path = Path(str(metadata["semantic_diff_json_path"]))
    _ensure_campaign_input_path(diff_json_path, campaign_dir, "semantic diff JSON")
    diff_json_bytes = _required_bytes(diff_json_path, "semantic diff JSON")
    _require(
        sha256_bytes(diff_json_bytes) == metadata.get("semantic_diff_json_sha256"),
        "semantic diff JSON hash differs from candidate metadata",
    )
    try:
        observed_diff = json.loads(diff_json_bytes)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid semantic diff JSON at {diff_json_path}: {exc}") from exc
    _require(
        observed_diff == rebuilt.diff.as_json(),
        "semantic diff JSON does not match deterministic candidate diff",
    )
    diff_md_path = Path(str(metadata["semantic_diff_markdown_path"]))
    _ensure_campaign_input_path(diff_md_path, campaign_dir, "semantic diff Markdown")
    diff_md_bytes = _required_bytes(diff_md_path, "semantic diff Markdown")
    _require(
        sha256_bytes(diff_md_bytes) == metadata.get("semantic_diff_markdown_sha256"),
        "semantic diff Markdown hash differs from candidate metadata",
    )
    _require(
        diff_md_bytes == _semantic_diff_markdown(rebuilt),
        "semantic diff Markdown does not match deterministic candidate diff",
    )

    stamp = _timestamp_slug()
    backup_path = campaign_dir / (
        f"APC40_visual_qa_pre_{mode}_{stamp}.xml"
    )
    receipt_path = campaign_dir / f"APC40_visual_qa_install_{mode}_{stamp}.json"
    _ensure_campaign_output_path(backup_path, campaign_dir)
    _ensure_campaign_output_path(receipt_path, campaign_dir)
    _require(not backup_path.exists(), f"fresh backup path already exists: {backup_path}")
    _require(not receipt_path.exists(), f"fresh receipt path already exists: {receipt_path}")
    campaign_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_bytes(backup_path, active_bytes)
    backup = parse_preset_file(backup_path)
    _require(backup.sha256 == expected_baseline, "backup hash mismatch")
    _replace_active_bytes(
        target=active_path,
        replacement_bytes=candidate_bytes,
        expected_before_sha256=expected_baseline,
        expected_after_sha256=candidate_hash,
        sleep_seconds=sleep_seconds,
    )
    receipt = {
        "schema_version": 1,
        "kind": "apc40_visual_qa_install_receipt",
        "action": f"install-{mode}",
        "active_path": str(active_path.resolve()),
        "expected_current_hash": expected_baseline,
        "installed_hash": candidate_hash,
        "candidate_path": str(candidate_path.resolve()),
        "backup_path": str(backup_path),
        "backup_hash": backup.sha256,
        "preflight_path": str(preflight_path.resolve()),
        "preflight_sha256": preflight_sha256.lower(),
        "build_manifest_sha256": calibration.build_manifest_sha256,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt_bytes = _json_bytes(receipt)
    _atomic_write_bytes(receipt_path, receipt_bytes)
    return {
        **receipt,
        "receipt_path": str(receipt_path),
        "receipt_sha256": sha256_bytes(receipt_bytes),
    }


def rollback_preset(
    *,
    active_path: Path,
    backup_path: Path,
    expected_current_hash: str,
    target_backup_hash: str,
    campaign_dir: Path,
    backup_receipt_path: Path,
    backup_receipt_sha256: str,
    preflight_path: Path,
    preflight_sha256: str,
    preflight_stage: str,
    sleep_seconds: float = 0.5,
) -> Mapping[str, object]:
    _require(_valid_sha256(expected_current_hash), "expected_current_hash is invalid")
    _require(_valid_sha256(target_backup_hash), "target_backup_hash is invalid")
    _require(
        preflight_stage in ROLLBACK_STAGES,
        f"invalid rollback preflight stage {preflight_stage!r}",
    )
    campaign_dir = campaign_dir.resolve()
    backup_path = _ensure_campaign_input_path(
        backup_path, campaign_dir, "rollback backup"
    )
    backup_receipt_path = _ensure_campaign_input_path(
        backup_receipt_path, campaign_dir, "install receipt"
    )
    install_receipt = _load_hashed_json(
        backup_receipt_path,
        backup_receipt_sha256,
        "install receipt",
    )
    _require(
        install_receipt.get("schema_version") == 1
        and install_receipt.get("kind") == "apc40_visual_qa_install_receipt",
        "rollback backup is not backed by a generator install receipt",
    )
    expected_install_action = (
        "install-pilot"
        if preflight_stage == "rollback-prepilot"
        else "install-full"
    )
    _require(
        install_receipt.get("action") == expected_install_action,
        "install receipt action does not match rollback stage",
    )
    _require(
        Path(str(install_receipt.get("active_path"))).resolve() == active_path.resolve(),
        "install receipt active path mismatch",
    )
    _require(
        Path(str(install_receipt.get("backup_path"))).resolve() == backup_path,
        "install receipt backup path mismatch",
    )
    _require(
        install_receipt.get("backup_hash") == target_backup_hash,
        "install receipt backup hash mismatch",
    )
    _require(
        install_receipt.get("installed_hash") == expected_current_hash,
        "install receipt installed hash mismatch",
    )
    current = sha256_file(active_path)
    if current != expected_current_hash:
        raise HashMismatch(
            f"rollback current hash mismatch: expected {expected_current_hash}, found {current}"
        )
    validate_mutation_preflight(
        preflight_path,
        expected_sha256=preflight_sha256,
        expected_stage=preflight_stage,
        expected_active_sha256=expected_current_hash,
    )
    backup_bytes = _required_bytes(backup_path, "rollback backup")
    observed_backup_hash = sha256_bytes(backup_bytes)
    if observed_backup_hash != target_backup_hash:
        raise HashMismatch(
            f"rollback target hash mismatch: expected {target_backup_hash}, "
            f"found {observed_backup_hash}"
        )
    try:
        backup_root = ET.fromstring(backup_bytes)
    except ET.ParseError as exc:
        raise ValidationError(f"invalid rollback XML at {backup_path}: {exc}") from exc
    shortcut_count = len(backup_root.findall("./ShortcutManager/Shortcut"))
    _require(
        backup_path.name.casefold() != "apc 40 mk ii - visual qa.pre148.xml",
        "the named .pre148 backup is explicitly untrusted",
    )
    _require(
        shortcut_count != 145,
        "145-shortcut .pre148 backup is explicitly untrusted",
    )
    backup = parse_preset_bytes(backup_bytes, source=str(backup_path))
    stamp = _timestamp_slug()
    receipt_path = campaign_dir / f"APC40_visual_qa_rollback_{stamp}.json"
    _ensure_campaign_output_path(receipt_path, campaign_dir)
    _require(not receipt_path.exists(), f"fresh receipt path already exists: {receipt_path}")
    _replace_active_bytes(
        target=active_path,
        replacement_bytes=backup_bytes,
        expected_before_sha256=expected_current_hash,
        expected_after_sha256=target_backup_hash,
        sleep_seconds=sleep_seconds,
    )
    receipt = {
        "schema_version": 1,
        "kind": "apc40_visual_qa_rollback_receipt",
        "action": "rollback-preset",
        "active_path": str(active_path.resolve()),
        "backup_path": str(backup_path.resolve()),
        "expected_current_hash": expected_current_hash,
        "target_backup_hash": target_backup_hash,
        "install_receipt_path": str(backup_receipt_path),
        "install_receipt_sha256": backup_receipt_sha256.lower(),
        "preflight_stage": preflight_stage,
        "preflight_path": str(preflight_path.resolve()),
        "preflight_sha256": preflight_sha256.lower(),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt_bytes = _json_bytes(receipt)
    _atomic_write_bytes(receipt_path, receipt_bytes)
    return {
        **receipt,
        "receipt_path": str(receipt_path),
        "receipt_sha256": sha256_bytes(receipt_bytes),
    }


def _candidate_summary(result: CandidateResult, *, wrote: bool) -> dict[str, object]:
    return {
        "mode": result.mode,
        "baseline_sha256": result.baseline_sha256,
        "candidate_sha256": result.candidate_sha256,
        "shortcuts": result.shortcut_count,
        "changed_raw_keys": [str(key) for key in result.diff.changed_raw_keys],
        "calibration_build_id": result.calibration.build_id,
        "calibration_status": result.calibration.status,
        "installable": result.installable,
        "wrote_files": wrote,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    artifacts = subparsers.add_parser(
        "artifacts", help="validate controls and optionally write only the manifest"
    )
    artifacts.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    artifacts.add_argument("--check", action="store_true", help="write nothing")

    candidate = subparsers.add_parser(
        "candidate", help="build a deterministic pilot or full candidate"
    )
    candidate.add_argument("--mode", choices=("pilot", "full"), required=True)
    candidate.add_argument("--baseline", type=Path, default=ACTIVE_PRESET)
    candidate.add_argument("--calibration", type=Path, default=CALIBRATION_PATH)
    candidate.add_argument("--build-manifest", type=Path, default=BUILD_MANIFEST_PATH)
    candidate.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    candidate.add_argument("--check", action="store_true", help="write nothing")
    candidate.add_argument(
        "--test-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    install = subparsers.add_parser(
        "install", help="hash-gated installation of an already-built candidate"
    )
    install.add_argument("--candidate", type=Path, required=True)
    install.add_argument("--metadata", type=Path, required=True)
    install.add_argument("--active", type=Path, default=ACTIVE_PRESET)
    install.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    install.add_argument("--preflight", type=Path, required=True)
    install.add_argument("--preflight-sha256", required=True)

    rollback = subparsers.add_parser(
        "rollback", help="hash-gated rollback to an exact campaign backup"
    )
    rollback.add_argument("--active", type=Path, default=ACTIVE_PRESET)
    rollback.add_argument("--backup", type=Path, required=True)
    rollback.add_argument("--expected-current-hash", required=True)
    rollback.add_argument("--target-backup-hash", required=True)
    rollback.add_argument("--campaign-dir", type=Path, default=DEFAULT_CAMPAIGN_DIR)
    rollback.add_argument("--backup-receipt", type=Path, required=True)
    rollback.add_argument("--backup-receipt-sha256", required=True)
    rollback.add_argument("--preflight", type=Path, required=True)
    rollback.add_argument("--preflight-sha256", required=True)
    rollback.add_argument("--stage", choices=sorted(ROLLBACK_STAGES), required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    # A bare invocation and the historical `--check` form are both read-only.
    if not arguments:
        arguments.extend(("artifacts", "--check"))
    elif arguments == ["--check"]:
        arguments.insert(0, "artifacts")
    parser = _build_parser()
    args = parser.parse_args(arguments)
    try:
        if args.command == "artifacts":
            payload = build_manifest_bytes()
            result: dict[str, object] = {
                "controls": 148,
                "buttons": 120,
                "continuous": 28,
                "manifest_sha256": sha256_bytes(payload),
                "manifest_bytes": len(payload),
                "wrote_files": not args.check,
            }
            if not args.check:
                result["manifest"] = write_manifest(args.manifest)
        elif args.command == "candidate":
            if not args.test_only and args.baseline.resolve() != ACTIVE_PRESET.resolve():
                raise UnsafeInstallError(
                    "non-test candidates must be derived from the canonical active preset"
                )
            calibration = load_calibration(
                args.calibration,
                mode=args.mode,
                build_manifest_path=(
                    args.build_manifest if args.build_manifest.exists() else None
                ),
                test_only=args.test_only,
            )
            baseline_bytes = _required_bytes(args.baseline, "canonical active preset")
            candidate_result = build_candidate(
                mode=args.mode,
                baseline_bytes=baseline_bytes,
                baseline_path=args.baseline,
                calibration=calibration,
            )
            if args.check:
                result = _candidate_summary(candidate_result, wrote=False)
            else:
                paths = write_candidate_artifacts(candidate_result, args.campaign_dir)
                result = {
                    **_candidate_summary(candidate_result, wrote=True),
                    "artifacts": {key: str(path) for key, path in paths.items()},
                }
        elif args.command == "install":
            if args.active.resolve() != ACTIVE_PRESET.resolve():
                raise UnsafeInstallError(
                    "CLI install may target only the canonical active preset"
                )
            result = dict(
                install_candidate(
                    candidate_path=args.candidate,
                    metadata_path=args.metadata,
                    active_path=args.active,
                    campaign_dir=args.campaign_dir,
                    preflight_path=args.preflight,
                    preflight_sha256=args.preflight_sha256,
                )
            )
        else:
            if args.active.resolve() != ACTIVE_PRESET.resolve():
                raise UnsafeInstallError(
                    "CLI rollback may target only the canonical active preset"
                )
            result = dict(
                rollback_preset(
                    active_path=args.active,
                    backup_path=args.backup,
                    expected_current_hash=args.expected_current_hash,
                    target_backup_hash=args.target_backup_hash,
                    campaign_dir=args.campaign_dir,
                    backup_receipt_path=args.backup_receipt,
                    backup_receipt_sha256=args.backup_receipt_sha256,
                    preflight_path=args.preflight,
                    preflight_sha256=args.preflight_sha256,
                    preflight_stage=args.stage,
                )
            )
    except GeneratorError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
