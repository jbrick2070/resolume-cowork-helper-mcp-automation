#!/usr/bin/env python3
"""Build the Electric Zentropa pressed-button FFT variant offline.

The ButtonGlow baseline remains immutable. This builder clones only the
authored clip-level Opacity FFT parameter from the matching active/fire clip
in APC40_Electric_Zentropa_FLIP.avc. It never adds layer-level FFT and never
touches fader, knob, master, or tempo layers.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import xml.etree.ElementTree as etree
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSITIONS = ROOT / "compositions"
CONTROLLERS = ROOT / "controllers"

BASE_STEM = "APC40MKII_ELECTRIC_ZENTROPA_BUTTONGLOW_BASELINE_v1"
OUT_STEM = "APC40MKII_ELECTRIC_ZENTROPA_BUTTONPULSE_FFT_v1"
OUT_PRESET_ID = "-2036841787"

BASE_COMP = COMPOSITIONS / f"{BASE_STEM}.avc"
BASE_PRESET = CONTROLLERS / f"{BASE_STEM}.xml"
DONOR_COMP = COMPOSITIONS / "APC40_Electric_Zentropa_FLIP.avc"
GEOMETRY = ROOT / "build" / "build_input_v3.json"
OUT_COMP = COMPOSITIONS / f"{OUT_STEM}.avc"
OUT_PRESET = CONTROLLERS / f"{OUT_STEM}.xml"

# Resolume layers are 1-based in its REST API and user-facing documentation;
# .avc Clip layerIndex values are zero-based.
BUTTON_LAYERS = tuple(
    list(range(0, 93)) + list(range(117, 142)) + [145, 146]
)


def parse(path: Path) -> etree.ElementTree:
    return etree.parse(path)


def deck_zero(root: etree.Element) -> etree.Element:
    decks = [deck for deck in root.findall("Deck") if deck.get("deckIndex") == "0"]
    if len(decks) != 1:
        raise AssertionError(f"expected one deckIndex=0, found {len(decks)}")
    return decks[0]


def clip_name(clip: etree.Element) -> str:
    nodes = clip.findall("./Params/Param[@name='Name']")
    if len(nodes) != 1:
        raise AssertionError("clip must have exactly one Name parameter")
    return nodes[0].get("value", "")


def media_path(clip: etree.Element) -> str:
    nodes = clip.findall("./PreloadData/VideoFile")
    if len(nodes) != 1:
        raise AssertionError(f"{clip_name(clip)} must have one VideoFile")
    return nodes[0].get("value", "")


def pressed_by_layer(deck: etree.Element) -> dict[int, etree.Element]:
    result: dict[int, etree.Element] = {}
    for clip in deck.findall("Clip"):
        name_nodes = clip.findall("./Params/Param[@name='Name']")
        if not name_nodes:
            # Resolume serializes empty cells as Clip elements without Params.
            continue
        if len(name_nodes) != 1:
            raise AssertionError("clip must have at most one Name parameter")
        name = name_nodes[0].get("value", "")
        if name.endswith(" - active") or name.endswith(" - fire"):
            layer = int(clip.get("layerIndex"))
            if layer in result:
                raise AssertionError(f"duplicate pressed clip at layer {layer + 1}")
            result[layer] = clip
    return result


def set_comp_names(root: etree.Element) -> None:
    info = root.find("CompositionInfo")
    if info is None:
        raise AssertionError("CompositionInfo missing")
    info.set("name", OUT_STEM)

    params = root.find("Params")
    if params is None:
        raise AssertionError("composition Params missing")
    values = {p.get("name"): p for p in params.findall("Param")}
    values["Name"].set("value", OUT_STEM)
    values["MidiShortcutPreset"].set("value", OUT_STEM)


def insert_opacity_fft(target: etree.Element, donor: etree.Element) -> None:
    target_params = target.find("./VideoTrack/Params")
    if target_params is None:
        raise AssertionError(f"target VideoTrack Params missing: {clip_name(target)}")

    existing = target_params.findall("./ParamRange[@name='Opacity']")
    if existing:
        raise AssertionError(
            f"pressed target unexpectedly already has Opacity: {clip_name(target)}"
        )

    donor_opacity = [
        node
        for node in donor.findall("./VideoTrack/Params/ParamRange[@name='Opacity']")
        if node.find("PhaseSourceFFT") is not None
    ]
    if len(donor_opacity) != 1:
        raise AssertionError(
            f"donor must have exactly one FFT Opacity: {clip_name(donor)}"
        )

    cloned = copy.deepcopy(donor_opacity[0])
    width = target_params.findall("./ParamRange[@name='Width']")
    insert_at = list(target_params).index(width[0]) if width else 0
    target_params.insert(insert_at, cloned)


def frequency_center(layer: int, geometry: dict[int, dict]) -> float:
    """Map the pressed controls into one chassis-wide spectrum field.

    The 5x8 grid rises from bass on its bottom row to highs on its top row,
    with a smaller left-to-right rise inside each row. The lower track strip
    runs lows-left to highs-right. The right control quadrant rises from bass
    at the bottom to highs at the top, with a smaller rightward lift.
    """
    if 0 <= layer <= 39:
        vertical = (layer // 8) / 4.0
        horizontal = (layer % 8) / 7.0
        field = 0.78 * vertical + 0.22 * horizontal
    elif 40 <= layer <= 44:
        vertical = 1.0 - ((layer - 40) / 4.0)
        field = 0.78 * vertical + 0.22
    elif 45 <= layer <= 92:
        field = ((layer - 45) % 8) / 7.0
    else:
        box = geometry[layer]["label_box"]
        x = (box[0] + box[2]) / 2.0
        y = (box[1] + box[3]) / 2.0
        vertical = max(0.0, min(1.0, (857.0 - y) / (857.0 - 204.0)))
        horizontal = max(0.0, min(1.0, (x - 1214.0) / (1727.0 - 1214.0)))
        field = 0.70 * vertical + 0.30 * horizontal
    return 0.05 + 0.90 * field


def remap_fft_band(opacity: etree.Element, layer: int, geometry: dict[int, dict]) -> None:
    frequency = opacity.find(
        "./PhaseSourceFFT/Params/ParamRange[@name='FrequencyRange']"
    )
    value_range = None if frequency is None else frequency.find(
        "./ValueRange[@name='startStop']"
    )
    if frequency is None or value_range is None:
        raise AssertionError(f"FFT frequency range missing at layer {layer + 1}")

    desired = frequency_center(layer, geometry)
    width = 0.18 if layer <= 44 else 0.20
    low = max(0.0, desired - width / 2.0)
    high = min(1.0, desired + width / 2.0)
    center = (low + high) / 2.0
    frequency.set("value", f"{center:.6g}")
    value_range.set("min", f"{low:.6g}")
    value_range.set("max", f"{high:.6g}")


def serialize(tree: etree.ElementTree) -> bytes:
    raw = etree.tostring(
        tree.getroot(),
        encoding="utf-8",
        xml_declaration=True,
    )
    # Resolume's source compositions are CRLF. lxml normalizes parsed line
    # endings to LF, so restore the native convention deterministically.
    return raw.replace(b"\n", b"\r\n") + b"\r\n"


def build(force: bool) -> None:
    for path in (BASE_COMP, BASE_PRESET, DONOR_COMP, GEOMETRY):
        if not path.is_file():
            raise FileNotFoundError(path)
    if not force:
        for path in (OUT_COMP, OUT_PRESET):
            if path.exists():
                raise FileExistsError(f"refusing to overwrite {path}; pass --force")

    tree = parse(BASE_COMP)
    donor_tree = parse(DONOR_COMP)
    root = tree.getroot()
    donor_root = donor_tree.getroot()
    set_comp_names(root)

    targets = pressed_by_layer(deck_zero(root))
    donors = pressed_by_layer(deck_zero(donor_root))
    geometry = {
        int(item["layer"]) - 1: item
        for item in json.loads(GEOMETRY.read_text(encoding="utf-8"))
        if item.get("layer") is not None
    }
    if set(targets) != set(BUTTON_LAYERS):
        raise AssertionError(
            f"baseline pressed layer set mismatch: {len(targets)} vs 120"
        )
    if set(donors) != set(BUTTON_LAYERS):
        raise AssertionError(
            f"donor pressed layer set mismatch: {len(donors)} vs 120"
        )

    for layer in BUTTON_LAYERS:
        target = targets[layer]
        donor = donors[layer]
        if clip_name(target) != clip_name(donor):
            raise AssertionError(
                f"name mismatch L{layer + 1}: {clip_name(target)} != {clip_name(donor)}"
            )
        if media_path(target) != media_path(donor):
            raise AssertionError(f"media mismatch L{layer + 1}")
        insert_opacity_fft(target, donor)
        opacity = target.find(
            "./VideoTrack/Params/ParamRange[@name='Opacity'][PhaseSourceFFT]"
        )
        if opacity is None:
            raise AssertionError(f"inserted FFT opacity missing at layer {layer + 1}")
        remap_fft_band(opacity, layer, geometry)

    OUT_COMP.write_bytes(serialize(tree))

    preset = BASE_PRESET.read_text(encoding="utf-8")
    preset, count = re.subn(
        r'(<MidiShortcutPreset\s+presetId=")[^"]+("\s+name=")[^"]+("\s*>)',
        rf"\g<1>{OUT_PRESET_ID}\g<2>{OUT_STEM}\g<3>",
        preset,
        count=1,
    )
    if count != 1:
        raise AssertionError("failed to rename the derived MIDI preset")
    OUT_PRESET.write_text(preset, encoding="utf-8", newline="")

    # Post-build invariants.
    built = parse(OUT_COMP).getroot()
    built_deck = deck_zero(built)
    built_pressed = pressed_by_layer(built_deck)
    pressed_fft = sum(
        built_pressed[layer].find(
            "./VideoTrack/Params/ParamRange[@name='Opacity']/PhaseSourceFFT"
        )
        is not None
        for layer in BUTTON_LAYERS
    )
    total_fft = sum(1 for _ in built.iter("PhaseSourceFFT"))
    layer_fft = sum(
        1 for layer in built.findall("Layer") for _ in layer.iter("PhaseSourceFFT")
    )
    if pressed_fft != 120 or total_fft != 300 or layer_fft != 0:
        raise AssertionError(
            f"FFT invariant failed: pressed={pressed_fft}, total={total_fft}, layer={layer_fft}"
        )

    def built_center(layer: int) -> float:
        node = built_pressed[layer].find(
            "./VideoTrack/Params/ParamRange[@name='Opacity']"
            "/PhaseSourceFFT/Params/ParamRange[@name='FrequencyRange']"
        )
        if node is None:
            raise AssertionError(f"built FFT center missing at layer {layer + 1}")
        return float(node.get("value"))

    if not (
        built_center(0) < built_center(16) < built_center(32)
        and built_center(45) < built_center(48) < built_center(52)
        and built_center(125) < built_center(117)
    ):
        raise AssertionError("spatial spectrum ordering invariant failed")

    preset_root = etree.parse(OUT_PRESET).getroot()
    shortcuts = sum(1 for _ in preset_root.iter("Shortcut"))
    if preset_root.get("name") != OUT_STEM or shortcuts != 203:
        raise AssertionError(
            f"preset invariant failed: name={preset_root.get('name')}, shortcuts={shortcuts}"
        )

    print(f"built {OUT_COMP}")
    print(f"built {OUT_PRESET}")
    print(
        f"verified: 120 pressed FFT opacities, {total_fft} total FFT nodes, "
        f"0 layer FFT nodes, {shortcuts} MIDI shortcuts; spatial bass-to-high map"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    build(args.force)


if __name__ == "__main__":
    main()
