#!/usr/bin/env python3
"""Build the Electric Zentropa AUTOTEST preset with latched APC40 LED feedback.

The live AUTOTEST preset uses ``connectnextclip`` so each press alternates the
per-control idle and active clips.  That event has no persistent state of its
own, so this builder keeps the input action but restores MIDI output feedback
from the active clip's ``connected`` sibling path.

The source files are never modified.  The output receives a new preset name
and deterministic preset ID so it can be drag-loaded into a running Avenue.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PRESET_NAME = "APC 40 MK II - Visual QA V3 Animated AUTOTEST LATCHED"
NEXT_RE = re.compile(r"^/composition/layers/(\d+)/connectnextclip$")
DIRECT_ACTIVE_RE = re.compile(r"^/composition/layers/(\d+)/clips/2/connect$")


def fail(message: str) -> "NoReturn":
    raise ValueError(message)


def parse(path: Path) -> ET.ElementTree:
    try:
        return ET.parse(path)
    except (OSError, ET.ParseError) as exc:
        fail(f"Could not parse {path}: {exc}")


def input_path(shortcut: ET.Element) -> str:
    for node in shortcut.findall("ShortcutPath"):
        if node.get("name") == "InputPath":
            return node.get("path", "")
    return ""


def raw_key(shortcut: ET.Element) -> str:
    node = shortcut.find("RawInputMessage")
    return "" if node is None else node.get("key", "")


def preset_id_for(name: str) -> str:
    raw = int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:4], "little")
    if raw >= 2**31:
        raw -= 2**32
    return str(raw or 1)


def named_values_by_name(shortcut: ET.Element) -> dict[str, float]:
    result: dict[str, float] = {}
    named = shortcut.find("NamedValues")
    if named is None:
        return result
    for value in named.findall("Value"):
        result[value.get("first", "")] = float(value.get("second", "nan"))
    return result


def insert_feedback_siblings(shortcut: ET.Element, layer: int) -> None:
    for node in list(shortcut.findall("ShortcutPath")):
        if node.get("name") in {"InputSiblingPath", "OutputSiblingPath"}:
            shortcut.remove(node)

    children = list(shortcut)
    output_index = next(
        (
            index
            for index, node in enumerate(children)
            if node.tag == "ShortcutPath" and node.get("name") == "OutputPath"
        ),
        None,
    )
    if output_index is None:
        fail(f"Layer {layer}: connect-next shortcut has no OutputPath")

    connected_path = f"/composition/layers/{layer}/clips/2/connected"
    attributes = {
        "path": connected_path,
        "translationType": "1",
        "allowedTranslationTypes": "-1",
    }
    input_sibling = ET.Element(
        "ShortcutPath", {"name": "InputSiblingPath", **attributes}
    )
    output_sibling = ET.Element(
        "ShortcutPath", {"name": "OutputSiblingPath", **attributes}
    )
    shortcut.insert(output_index + 1, input_sibling)
    shortcut.insert(output_index + 2, output_sibling)


def replace_named_values(shortcut: ET.Element, donor: ET.Element, layer: int) -> None:
    donor_values = donor.find("NamedValues")
    if donor_values is None:
        fail(f"Layer {layer}: donor shortcut has no NamedValues")

    old = shortcut.find("NamedValues")
    if old is None:
        shortcut.append(copy.deepcopy(donor_values))
        return

    index = list(shortcut).index(old)
    shortcut.remove(old)
    shortcut.insert(index, copy.deepcopy(donor_values))


def build(live_path: Path, donor_path: Path, output_path: Path, overwrite: bool) -> dict:
    if output_path.exists() and not overwrite:
        fail(f"Refusing to overwrite existing output: {output_path}")

    live_tree = parse(live_path)
    donor_tree = parse(donor_path)
    live_root = live_tree.getroot()
    donor_root = donor_tree.getroot()
    if live_root.tag != "MidiShortcutPreset" or donor_root.tag != "MidiShortcutPreset":
        fail("Both inputs must be Resolume MidiShortcutPreset XML files")

    live_manager = live_root.find("ShortcutManager")
    donor_manager = donor_root.find("ShortcutManager")
    if live_manager is None or donor_manager is None:
        fail("ShortcutManager missing from an input preset")

    live_shortcuts = list(live_manager.findall("Shortcut"))
    donor_shortcuts = list(donor_manager.findall("Shortcut"))

    next_by_layer: dict[int, ET.Element] = {}
    for shortcut in live_shortcuts:
        match = NEXT_RE.fullmatch(input_path(shortcut))
        if match:
            layer = int(match.group(1))
            if layer in next_by_layer:
                fail(f"Duplicate connect-next shortcut for layer {layer}")
            next_by_layer[layer] = shortcut

    donor_by_layer: dict[int, ET.Element] = {}
    for shortcut in donor_shortcuts:
        match = DIRECT_ACTIVE_RE.fullmatch(input_path(shortcut))
        if match:
            layer = int(match.group(1))
            if layer in donor_by_layer:
                fail(f"Duplicate direct active donor for layer {layer}")
            donor_by_layer[layer] = shortcut

    if len(next_by_layer) != 120:
        fail(f"Expected exactly 120 connect-next shortcuts; found {len(next_by_layer)}")
    if set(next_by_layer) != set(donor_by_layer):
        missing = sorted(set(next_by_layer) - set(donor_by_layer))
        extra = sorted(set(donor_by_layer) - set(next_by_layer))
        fail(f"Donor layer mismatch; missing={missing}, extra={extra}")

    duplicate_direct: list[ET.Element] = []
    for shortcut in live_shortcuts:
        match = DIRECT_ACTIVE_RE.fullmatch(input_path(shortcut))
        if not match:
            continue
        layer = int(match.group(1))
        next_shortcut = next_by_layer.get(layer)
        if next_shortcut is not None and raw_key(shortcut) == raw_key(next_shortcut):
            duplicate_direct.append(shortcut)

    if len(duplicate_direct) != 1:
        fail(
            "Expected exactly one duplicate direct active shortcut sharing a "
            f"connect-next raw key; found {len(duplicate_direct)}"
        )
    duplicate_layer = int(DIRECT_ACTIVE_RE.fullmatch(input_path(duplicate_direct[0])).group(1))
    if duplicate_layer != 33:
        fail(f"Expected duplicate on layer 33; found layer {duplicate_layer}")
    live_manager.remove(duplicate_direct[0])

    for layer, shortcut in sorted(next_by_layer.items()):
        donor = donor_by_layer[layer]
        insert_feedback_siblings(shortcut, layer)
        replace_named_values(shortcut, donor, layer)
        shortcut.set("paramNodeName", "ParamEvent")
        shortcut.set("outputDeviceName", "APC40 mkII")

    live_root.set("name", PRESET_NAME)
    new_preset_id = preset_id_for(PRESET_NAME)
    if new_preset_id in {live_root.get("presetId"), donor_root.get("presetId")}:
        fail("Generated preset ID unexpectedly collides with an input preset")
    live_root.set("presetId", new_preset_id)

    final_shortcuts = list(live_manager.findall("Shortcut"))
    if len(final_shortcuts) != 203:
        fail(f"Expected 203 shortcuts after duplicate removal; found {len(final_shortcuts)}")

    event_keys: set[str] = set()
    for layer, shortcut in sorted(next_by_layer.items()):
        paths = {node.get("name"): node.get("path") for node in shortcut.findall("ShortcutPath")}
        expected = f"/composition/layers/{layer}/clips/2/connected"
        if paths.get("InputSiblingPath") != expected or paths.get("OutputSiblingPath") != expected:
            fail(f"Layer {layer}: connected-state feedback paths were not installed")
        values = named_values_by_name(shortcut)
        if values.get("Connected", 0.0) <= 0.0:
            fail(f"Layer {layer}: Connected feedback is not lit")
        if values.get("Disconnected") != 0.0:
            fail(f"Layer {layer}: Disconnected feedback is not off")
        key = raw_key(shortcut)
        if not key or key in event_keys:
            fail(f"Layer {layer}: missing or duplicate connect-next raw MIDI key {key!r}")
        event_keys.add(key)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(live_tree, space="\t")
    live_tree.write(output_path, encoding="utf-8", xml_declaration=True)

    reparsed = parse(output_path)
    if reparsed.getroot().get("name") != PRESET_NAME:
        fail("Output verification failed after serialization")

    return {
        "output": str(output_path.resolve()),
        "preset_name": PRESET_NAME,
        "preset_id": new_preset_id,
        "shortcut_count": len(final_shortcuts),
        "latched_button_shortcuts": len(next_by_layer),
        "removed_duplicate_layer": duplicate_layer,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("live", type=Path, help="Current connect-next AUTOTEST XML")
    parser.add_argument("donor", type=Path, help="Direct clip-2 AUTOTEST donor XML")
    parser.add_argument("output", type=Path, help="New staged LATCHED preset XML")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output")
    args = parser.parse_args()
    try:
        result = build(args.live, args.donor, args.output, args.overwrite)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
