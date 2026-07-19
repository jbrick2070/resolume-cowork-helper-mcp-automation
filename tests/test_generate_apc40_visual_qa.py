from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/generate_apc40_visual_qa.py"
SPEC = importlib.util.spec_from_file_location("generate_apc40_visual_qa", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


def _motion_entry(layer: int) -> dict[str, object]:
    if layer in generator.VERTICAL_FADER_LAYERS:
        if layer == 94:
            return {
                "axis": "y",
                "geometry": {"top": 100, "bottom": 300},
                "value_at_cc0": 0.50666809082,
                "value_at_cc127": 0.504257202148,
                "xml_value_range": [0.50666809082, 0.504257202148],
            }
        return {
            "axis": "y",
            "geometry": {"top": 100, "bottom": 300},
            "value_at_cc0": 0.51,
            "value_at_cc127": 0.49,
            "xml_value_range": [0.51, 0.49],
        }
    if layer == generator.CROSSFADER_LAYER:
        return {
            "axis": "x",
            "geometry": {"left": 100, "right": 300},
            "value_at_cc0": 0.49,
            "value_at_cc127": 0.51,
            "xml_value_range": [0.49, 0.51],
        }
    return {
        "axis": "rotation_z",
        "geometry": {"center": [100, 100], "radius": 42},
        "value_at_cc0": 0.125,
        "value_at_cc127": 0.875,
        "xml_value_range": [0.125, 0.875],
    }


def _calibration_data(
    status: str,
    *,
    measurement_sha256: str | None = None,
) -> dict[str, object]:
    motion_layers = (
        generator.VERTICAL_FADER_LAYERS
        | {generator.CROSSFADER_LAYER}
        | (generator.ROTARY_LAYERS - {148})
    )
    accepted = status == "accepted"
    parent_hashes = (
        {
            basename: {"sha256": "b" * 64, "bytes": 1}
            for basename in generator.ACCEPTED_PARENT_HASH_BASENAMES
        }
        if accepted
        else None
    )
    accepted_metrics = (
        {
            str(layer): {"ink_box_px": [88, 39]}
            for layer in (*range(94, 102), 143, 144)
        }
        if accepted
        else None
    )
    return {
        "schema_version": 1,
        "build_id": "fixture-B1" if accepted else "fixture-B0",
        "parent_build_id": "fixture-B0" if accepted else None,
        "measurement_sha256": measurement_sha256 if accepted else None,
        "measurement_parent_artifact_hashes": parent_hashes,
        "status": status,
        "position_domain": [-32768, 32768],
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
            "font": "Segoe UI Symbol",
            "ink_box_px": [86, 35],
        },
        "accepted_live_tag_metrics": accepted_metrics,
        "motion_ranges_by_layer": {
            str(layer): _motion_entry(layer) for layer in sorted(motion_layers)
        },
        "knob_rest_degrees": [-135, 135],
        "tempo_relative": {
            "step": generator.TEMPO_RELATIVE_STEP,
            "num_steps": 480,
        },
        "position_y_visual_direction": "positive_down",
    }


def _write_calibration_fixture(
    directory: Path, status: str, *, test_only: bool
) -> tuple[Path, Path]:
    artifact_dir = directory / status
    artifact_dir.mkdir(parents=True, exist_ok=True)
    measurement_path = artifact_dir / "APC40_visual_qa_tag_measurement.json"
    measurement_sha256 = None
    if status == "accepted":
        measurement_bytes = (
            json.dumps(
                {"schema_version": 1, "artifact_role": "live_tag_measurement"},
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        measurement_path.write_bytes(measurement_bytes)
        measurement_sha256 = hashlib.sha256(measurement_bytes).hexdigest()
    calibration_path = artifact_dir / "APC40_visual_qa_calibration.json"
    calibration_data = _calibration_data(
        status, measurement_sha256=measurement_sha256
    )
    calibration_bytes = (
        json.dumps(calibration_data, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    calibration_path.write_bytes(calibration_bytes)
    build_id = str(calibration_data["build_id"])
    json_artifacts = {
        "APC40_visual_qa_geometry.json": {
            "schema_version": 1,
            "build_id": build_id,
        },
        "APC40_visual_qa_live_controls.json": {
            "schema_version": 1,
            "build_id": build_id,
            "status": status,
            "artifact_role": "typed_live_controls",
        },
        "APC40_visual_qa_renderer_report.json": {
            "schema_version": 1,
            "build_id": build_id,
            "status": status,
            "inputs": {
                "measurement": str(measurement_path.resolve())
                if status == "accepted"
                else None,
                "measurement_sha256": measurement_sha256,
            },
        },
    }
    for name, value in json_artifacts.items():
        (artifact_dir / name).write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    for name in generator.REQUIRED_ARTIFACT_BASENAMES:
        path = artifact_dir / name
        if path.exists():
            continue
        if path.suffix.lower() == ".png":
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + name.encode("ascii"))
    manifest_path = artifact_dir / "APC40_visual_qa_build_manifest.json"
    artifact_paths = [
        artifact_dir / name for name in generator.REQUIRED_ARTIFACT_BASENAMES
    ]
    manifest = {
        "schema_version": 1,
        "build_id": calibration_data["build_id"],
        "status": status,
        "parent_build_id": calibration_data["parent_build_id"],
        "measurement_sha256": calibration_data["measurement_sha256"],
        "artifacts": {
            str(path.resolve()): {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": len(path.read_bytes()),
            }
            for path in artifact_paths
        },
        "test_only": test_only,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return calibration_path, manifest_path


def _write_preflight(
    directory: Path,
    stage: str,
    *,
    active_sha256: str | None,
    timestamp: datetime | None = None,
    expected_layer_count: int = 148,
    bridge_pids: list[int] | None = None,
    watcher_pids: list[int] | None = None,
) -> tuple[Path, str]:
    directory.mkdir(parents=True, exist_ok=True)
    layer_ids = list(range(1, 149))
    clip_ids = list(range(1001, 1149))
    identity = {
        "name": generator.COMPOSITION_NAME,
        "width": 1920,
        "height": 1080,
        "column_ids": [1],
        "layer_ids": layer_ids,
        "clip_ids": clip_ids,
    }
    fingerprint = {
        "sha256": hashlib.sha256(
            generator._canonical_json_bytes(identity)
        ).hexdigest(),
        **identity,
    }
    value = {
        "schema_version": 1,
        "stage": stage,
        "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
        "expected_layer_count": expected_layer_count,
        "actual_layer_count": 148,
        "processes": {
            "avenue_pids": [65000],
            "bridge_pids": [66752] if bridge_pids is None else bridge_pids,
            "watcher_pids": [] if watcher_pids is None else watcher_pids,
        },
        "native_product": {"name": "Avenue"},
        "bridge_product": {"name": "Avenue"},
        "composition_fingerprint": fingerprint,
        "control_validation": {
            "layers": 148,
            "names": "exact",
            "trigger_styles": "exact",
        },
    }
    if active_sha256 is not None:
        value["active_preset_sha256"] = active_sha256
    path = directory / f"preflight-{stage}.json"
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return path, hashlib.sha256(payload).hexdigest()


def _avenue_rewrite_pilot_bytes(pilot_bytes: bytes) -> bytes:
    """Model the observed Avenue load/save rewrite without using Avenue."""

    root = ET.fromstring(pilot_bytes)
    manager = root.find("ShortcutManager")
    assert manager is not None
    replacements = {
        "/composition/layers/94/clips/1/video/opacity": {
            "min": "0.6500000000000000222",
        },
        "/composition/layers/94/clips/1/video/effects/transform/positiony": {
            "min": "0.50666809081999997222",
            "max": "0.50425720214799996111",
        },
        "/composition/layers/102/clips/1/video/opacity": {
            "min": "0.3499999999999999778",
        },
    }
    observed: set[str] = set()
    for shortcut in manager.findall("Shortcut"):
        input_path = next(
            (
                path.attrib["path"]
                for path in shortcut.findall("ShortcutPath")
                if path.attrib.get("name") == "InputPath"
            ),
            None,
        )
        if input_path not in replacements:
            continue
        value_range = shortcut.find("ValueRange")
        assert value_range is not None
        value_range.attrib.update(replacements[input_path])
        observed.add(input_path)
    assert observed == set(replacements)

    # Avenue also assigns its own preset id and globally reorders records.
    # Reversal is a deterministic stand-in that exercises both behaviours.
    root.attrib["presetId"] = "2027461064"
    children = list(manager)
    for child in children:
        manager.remove(child)
    for child in reversed(children):
        manager.append(child)
    return generator.serialize_preset_root(root)


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_baseline = generator.REPO_PRESET.read_bytes()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.baseline_path = self.root / "active.xml"
        self.baseline_path.write_bytes(self.repo_baseline)
        provisional_path, provisional_manifest = _write_calibration_fixture(
            self.root, "provisional", test_only=False
        )
        self.provisional = generator.load_calibration(
            provisional_path,
            mode="pilot",
            build_manifest_path=provisional_manifest,
            test_only=False,
        )
        accepted_path, accepted_manifest = _write_calibration_fixture(
            self.root, "accepted", test_only=True
        )
        self.accepted = generator.load_calibration(
            accepted_path,
            mode="full",
            build_manifest_path=accepted_manifest,
            test_only=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build_pilot(self) -> generator.CandidateResult:
        return generator.build_candidate(
            mode="pilot",
            baseline_bytes=self.baseline_path.read_bytes(),
            baseline_path=self.baseline_path,
            calibration=self.provisional,
        )

    def test_manifest_is_deterministic_and_has_decimal_string_raw_keys(self) -> None:
        first = generator.build_manifest_bytes()
        second = generator.build_manifest_bytes()
        self.assertEqual(first, second)
        records = json.loads(first)
        self.assertEqual(len(records), 148)
        self.assertEqual([row["layer"] for row in records], list(range(1, 149)))
        self.assertTrue(all(isinstance(row["raw_key"], str) for row in records))
        self.assertNotIn(b"connect_continuous", first)

    def test_literal_continuous_control_contract_and_full_targets(self) -> None:
        # This is deliberately independent of build_controls(): it is the
        # audited APC40 mkII address/target contract, not another rendering of
        # the generator's own mapping table.
        expected = (
            (94, 1, "FADER1", "Track Fader 1", 7, 1, "CC7/C1", ("wake", "opacity", "absolute_motion"), "positiony"),
            (95, 1, "FADER2", "Track Fader 2", 7, 2, "CC7/C2", ("wake", "opacity", "absolute_motion"), "positiony"),
            (96, 1, "FADER3", "Track Fader 3", 7, 3, "CC7/C3", ("wake", "opacity", "absolute_motion"), "positiony"),
            (97, 1, "FADER4", "Track Fader 4", 7, 4, "CC7/C4", ("wake", "opacity", "absolute_motion"), "positiony"),
            (98, 1, "FADER5", "Track Fader 5", 7, 5, "CC7/C5", ("wake", "opacity", "absolute_motion"), "positiony"),
            (99, 1, "FADER6", "Track Fader 6", 7, 6, "CC7/C6", ("wake", "opacity", "absolute_motion"), "positiony"),
            (100, 1, "FADER7", "Track Fader 7", 7, 7, "CC7/C7", ("wake", "opacity", "absolute_motion"), "positiony"),
            (101, 1, "FADER8", "Track Fader 8", 7, 8, "CC7/C8", ("wake", "opacity", "absolute_motion"), "positiony"),
            (102, 1, "TRACK1", "Track Knob 1", 48, 1, "CC48/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (103, 1, "TRACK2", "Track Knob 2", 49, 1, "CC49/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (104, 1, "TRACK3", "Track Knob 3", 50, 1, "CC50/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (105, 1, "TRACK4", "Track Knob 4", 51, 1, "CC51/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (106, 1, "TRACK5", "Track Knob 5", 52, 1, "CC52/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (107, 1, "TRACK6", "Track Knob 6", 53, 1, "CC53/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (108, 1, "TRACK7", "Track Knob 7", 54, 1, "CC54/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (109, 1, "TRACK8", "Track Knob 8", 55, 1, "CC55/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (110, 1, "DEV1", "Device Knob 1", 16, 1, "CC16/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (111, 1, "DEV2", "Device Knob 2", 17, 1, "CC17/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (112, 1, "DEV3", "Device Knob 3", 18, 1, "CC18/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (113, 1, "DEV4", "Device Knob 4", 19, 1, "CC19/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (114, 1, "DEV5", "Device Knob 5", 20, 1, "CC20/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (115, 1, "DEV6", "Device Knob 6", 21, 1, "CC21/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (116, 1, "DEV7", "Device Knob 7", 22, 1, "CC22/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (117, 1, "DEV8", "Device Knob 8", 23, 1, "CC23/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (143, 1, "MASTER", "Master Fader", 14, 1, "CC14/C1", ("wake", "opacity", "absolute_motion"), "positiony"),
            (144, 1, "X-FADE", "Crossfader", 15, 1, "CC15/C1", ("wake", "opacity", "absolute_motion"), "positionx"),
            (145, 1, "CUE", "Cue Level", 47, 1, "CC47/C1", ("wake", "opacity", "absolute_motion"), "rotationz"),
            (148, 1, "TEMPO", "Tempo Knob", 13, 1, "CC13/C1", ("wake", "tempo_motion"), "rotationz"),
        )
        self.assertEqual(len(expected), 28)

        controls = {
            control.layer: control
            for control in generator.build_controls()
            if not control.is_button
        }
        self.assertEqual(set(controls), {row[0] for row in expected})

        pilot = self.build_pilot()
        pilot_path = self.root / "literal-contract-pilot.xml"
        pilot_path.write_bytes(pilot.candidate_bytes)
        full = generator.build_candidate(
            mode="full",
            baseline_bytes=pilot.candidate_bytes,
            baseline_path=pilot_path,
            calibration=self.accepted,
        )
        self.assertEqual(full.shortcut_count, 203)
        document = generator.parse_preset_bytes(full.candidate_bytes)
        self.assertFalse(
            any(record.role == "legacy_cc" for record in document.semantics)
        )
        self.assertFalse(
            any(
                record.input_path.endswith("/video/source/delay")
                for record in document.semantics
            )
        )

        for (
            layer,
            clip,
            label,
            layer_name,
            cc,
            channel,
            midi_label,
            expected_roles,
            motion_axis,
        ) in expected:
            with self.subTest(layer=layer, midi=midi_label):
                control = controls[layer]
                self.assertEqual(
                    (
                        control.layer,
                        control.label,
                        control.layer_name,
                        control.data1,
                        control.channel,
                        control.midi_label,
                    ),
                    (layer, label, layer_name, cc, channel, midi_label),
                )

                records = [
                    record
                    for record in document.semantics
                    if record.raw_key == control.raw_key
                ]
                by_role = {record.role: record.input_path for record in records}
                self.assertEqual(set(by_role), set(expected_roles))
                self.assertEqual(len(records), len(expected_roles))

                clip_root = f"/composition/layers/{layer}/clips/{clip}"
                expected_paths = {
                    "wake": f"{clip_root}/connect",
                    (
                        "tempo_motion"
                        if "tempo_motion" in expected_roles
                        else "absolute_motion"
                    ): f"{clip_root}/video/effects/transform/{motion_axis}",
                }
                if "opacity" in expected_roles:
                    expected_paths["opacity"] = f"{clip_root}/video/opacity"
                self.assertEqual(by_role, expected_paths)

    def test_bottom_row_solo_is_blue_and_record_arm_dot_is_red(self) -> None:
        controls = generator.build_controls()
        solos = [control for control in controls if control.category == "solo"]
        record_arms = [
            control for control in controls if control.category == "record_arm"
        ]
        self.assertEqual(len(solos), 8)
        self.assertEqual(len(record_arms), 8)
        self.assertTrue(
            all(
                control.data1 == 49
                and control.color == generator.BLUE
                and control.led_velocity == 127
                for control in solos
            )
        )
        self.assertTrue(
            all(
                control.data1 == 48
                and control.color == generator.RED
                and control.led_velocity == 5
                for control in record_arms
            )
        )

    def test_continuous_controls_are_white_except_red_tempo(self) -> None:
        controls = generator.build_controls()
        continuous = [control for control in controls if not control.is_button]
        tempo = [control for control in continuous if control.category == "tempo"]
        neutral = [control for control in continuous if control.category != "tempo"]
        self.assertEqual(len(continuous), 28)
        self.assertEqual(len(tempo), 1)
        self.assertEqual(tempo[0].color, generator.RED)
        self.assertTrue(all(control.color == generator.WHITE for control in neutral))

    def test_pilot_candidate_is_deterministic_and_schema_exact(self) -> None:
        first = self.build_pilot()
        second = self.build_pilot()
        self.assertEqual(first.candidate_bytes, second.candidate_bytes)
        self.assertEqual(first.shortcut_count, 153)
        self.assertEqual(
            set(first.diff.changed_raw_keys),
            {
                generator.build_controls()[layer - 1].raw_key
                for layer in generator.PILOT_LAYERS
            },
        )
        document = generator.parse_preset_bytes(first.candidate_bytes)
        generator.assert_pilot_document(
            document, generator.build_controls(), self.provisional
        )
        fader = generator.build_controls()[93]
        records = [row for row in document.semantics if row.raw_key == fader.raw_key]
        wake = records[0]
        self.assertIsNone(wake.output_device_or_none)
        self.assertIsNone(wake.subtarget_or_none)
        self.assertIsNone(wake.value_range_or_none)
        self.assertEqual(wake.named_values, (("Disconnected", "1"),))
        motion = records[2]
        value_range = dict(motion.value_range_or_none or ())
        self.assertGreater(
            generator.Decimal(value_range["min"]),
            generator.Decimal(value_range["max"]),
        )

    def test_full_candidate_from_generated_pilot(self) -> None:
        pilot = self.build_pilot()
        pilot_path = self.root / "accepted-pilot.xml"
        pilot_path.write_bytes(pilot.candidate_bytes)
        full = generator.build_candidate(
            mode="full",
            baseline_bytes=pilot.candidate_bytes,
            baseline_path=pilot_path,
            calibration=self.accepted,
        )
        self.assertEqual(full.shortcut_count, 203)
        document = generator.parse_preset_bytes(full.candidate_bytes)
        generator.assert_full_document(
            document, generator.build_controls(), self.accepted
        )
        self.assertFalse(
            any("/video/source/" in row.input_path for row in document.semantics)
        )
        self.assertTrue(
            all(
                row.output_device_or_none is None
                for row in document.semantics
                if row.raw_key >= generator.CC_BASE
            )
        )

        before = generator.parse_preset_bytes(pilot.candidate_bytes)
        button_keys = {
            control.raw_key for control in generator.build_controls() if control.is_button
        }
        for raw_key in button_keys:
            self.assertEqual(
                generator._protected_elements_by_raw(before, raw_key),
                generator._protected_elements_by_raw(document, raw_key),
            )

    def test_full_candidate_recalibrates_an_installed_prior_pilot(self) -> None:
        pilot = self.build_pilot()
        accepted_data = copy.deepcopy(dict(self.accepted.data))
        accepted_fader = accepted_data["motion_ranges_by_layer"]["94"]
        accepted_fader["value_at_cc0"] = 0.506629943848
        accepted_fader["value_at_cc127"] = 0.504295349121
        accepted_fader["xml_value_range"] = [0.506629943848, 0.504295349121]
        recalibrated = generator.CalibrationContract(
            path=self.accepted.path,
            raw_bytes=self.accepted.raw_bytes,
            data=accepted_data,
            build_manifest_path=self.accepted.build_manifest_path,
            build_manifest_sha256=self.accepted.build_manifest_sha256,
            test_only=True,
        )
        full = generator.build_candidate(
            mode="full",
            baseline_bytes=pilot.candidate_bytes,
            baseline_path=self.root / "installed-prior-pilot.xml",
            calibration=recalibrated,
        )
        document = generator.parse_preset_bytes(full.candidate_bytes)
        generator.assert_full_document(
            document, generator.build_controls(), recalibrated
        )
        fader = generator.build_controls()[93]
        fader_motion = next(
            record
            for record in document.semantics
            if record.raw_key == fader.raw_key and record.role == "absolute_motion"
        )
        self.assertEqual(
            dict(fader_motion.value_range_or_none or ()),
            {
                "max": "0.504295349121",
                "min": "0.506629943848",
            },
        )
        self.assertIn(fader.raw_key, full.diff.changed_raw_keys)

    def test_full_candidate_rejects_unbounded_prior_pilot_range(self) -> None:
        pilot = self.build_pilot()
        root = ET.fromstring(pilot.candidate_bytes)
        manager = root.find("ShortcutManager")
        self.assertIsNotNone(manager)
        assert manager is not None
        target_path = "/composition/layers/94/clips/1/video/effects/transform/positiony"
        for shortcut in manager.findall("Shortcut"):
            input_path = next(
                (
                    path.attrib.get("path")
                    for path in shortcut.findall("ShortcutPath")
                    if path.attrib.get("name") == "InputPath"
                ),
                None,
            )
            if input_path == target_path:
                value_range = shortcut.find("ValueRange")
                self.assertIsNotNone(value_range)
                assert value_range is not None
                value_range.attrib.update(min="1", max="0")
                break
        else:
            self.fail("pilot Fader 1 motion mapping was not found")
        hostile = generator.serialize_preset_root(root)
        with self.assertRaisesRegex(
            generator.ValidationError, "bounded prior calibration"
        ):
            generator.build_candidate(
                mode="full",
                baseline_bytes=hostile,
                baseline_path=self.root / "hostile-prior-pilot.xml",
                calibration=self.accepted,
            )

    def test_full_candidate_accepts_observed_avenue_pilot_rewrite(self) -> None:
        pilot = self.build_pilot()
        loaded_bytes = _avenue_rewrite_pilot_bytes(pilot.candidate_bytes)
        loaded_path = self.root / "avenue-loaded-pilot.xml"
        loaded_path.write_bytes(loaded_bytes)
        loaded = generator.parse_preset_bytes(loaded_bytes)

        # Loaded-pilot acceptance is semantic for generated records: Avenue may
        # reorder them and expand a decimal to the exact same binary64 value.
        generator.assert_pilot_document(
            loaded, generator.build_controls(), self.accepted
        )
        full = generator.build_candidate(
            mode="full",
            baseline_bytes=loaded_bytes,
            baseline_path=loaded_path,
            calibration=self.accepted,
        )
        self.assertEqual(
            full.baseline_sha256,
            hashlib.sha256(loaded_bytes).hexdigest(),
        )
        document = generator.parse_preset_bytes(full.candidate_bytes)
        generator.assert_full_document(
            document, generator.build_controls(), self.accepted
        )

        pilot_raw_keys = {
            generator.build_controls()[layer - 1].raw_key
            for layer in generator.PILOT_LAYERS
        }
        self.assertTrue(pilot_raw_keys.isdisjoint(full.diff.changed_raw_keys))
        fader = generator.build_controls()[93]
        fader_ranges = {
            row.role: dict(row.value_range_or_none or ())
            for row in document.semantics
            if row.raw_key == fader.raw_key
        }
        self.assertEqual(
            fader_ranges["opacity"]["min"], "0.6500000000000000222"
        )
        self.assertEqual(
            fader_ranges["absolute_motion"],
            {
                "max": "0.50425720214799996111",
                "min": "0.50666809081999997222",
            },
        )

        button_keys = {
            control.raw_key
            for control in generator.build_controls()
            if control.is_button
        }
        for raw_key in button_keys:
            self.assertEqual(
                generator._protected_elements_by_raw(loaded, raw_key),
                generator._protected_elements_by_raw(document, raw_key),
            )

    def test_avenue_numeric_acceptance_is_exact_and_not_used_for_protected_xml(
        self,
    ) -> None:
        equivalent_pairs = (
            ("0.65", "0.6500000000000000222"),
            ("0.504257202148", "0.50425720214799996111"),
            ("0.50666809082", "0.50666809081999997222"),
            ("0.35", "0.3499999999999999778"),
        )
        for short, expanded in equivalent_pairs:
            with self.subTest(short=short):
                self.assertEqual(
                    generator._binary64_decimal_token(short),
                    generator._binary64_decimal_token(expanded),
                )
        self.assertNotEqual(
            generator._binary64_decimal_token("0.65"),
            generator._binary64_decimal_token("0.6500000000000001"),
        )

        loaded_bytes = _avenue_rewrite_pilot_bytes(self.build_pilot().candidate_bytes)
        bad_root = ET.fromstring(loaded_bytes)
        bad_manager = bad_root.find("ShortcutManager")
        assert bad_manager is not None
        for shortcut in bad_manager.findall("Shortcut"):
            input_path = next(
                (
                    path.attrib["path"]
                    for path in shortcut.findall("ShortcutPath")
                    if path.attrib.get("name") == "InputPath"
                ),
                None,
            )
            if input_path == "/composition/layers/94/clips/1/video/opacity":
                value_range = shortcut.find("ValueRange")
                assert value_range is not None
                value_range.attrib["min"] = "0.6500000000000001"
                break
        bad_bytes = generator.serialize_preset_root(bad_root)
        with self.assertRaisesRegex(
            generator.ValidationError, "schema/range mismatch"
        ):
            generator.build_candidate(
                mode="full",
                baseline_bytes=bad_bytes,
                baseline_path=self.root / "bad-loaded-pilot.xml",
                calibration=self.accepted,
            )

        before = generator.parse_preset_bytes(loaded_bytes)
        protected_root = ET.fromstring(loaded_bytes)
        protected_manager = protected_root.find("ShortcutManager")
        assert protected_manager is not None
        protected = next(
            shortcut
            for shortcut in protected_manager.findall("Shortcut")
            if int(shortcut.find("RawInputMessage").attrib["key"])
            < generator.CC_BASE
        )
        zero_value = next(
            value
            for value in protected.findall("./NamedValues/Value")
            if value.attrib.get("second") == "0"
        )
        zero_value.attrib["second"] = "0.0"
        after = generator.parse_preset_bytes(
            generator.serialize_preset_root(protected_root)
        )
        all_cc_raw_keys = {
            control.raw_key
            for control in generator.build_controls()
            if not control.is_button
        }
        with self.assertRaisesRegex(
            generator.ValidationError, "protected shortcut element"
        ):
            generator._assert_protected_exact(before, after, all_cc_raw_keys)

    def test_full_rejects_provisional_calibration(self) -> None:
        with self.assertRaises(generator.ValidationError):
            generator.load_calibration(
                self.provisional.path,
                mode="full",
                build_manifest_path=self.provisional.build_manifest_path,
                test_only=False,
            )

    def test_derived_id_collision_fails_closed(self) -> None:
        root = ET.fromstring(self.repo_baseline)
        manager = root.find("ShortcutManager")
        self.assertIsNotNone(manager)
        assert manager is not None
        fader = generator.build_controls()[93]
        knob = generator.build_controls()[101]
        baseline = generator.parse_preset_bytes(self.repo_baseline)
        fader_base = next(
            record.unique_id
            for record in baseline.semantics
            if record.raw_key == fader.raw_key and record.role == "legacy_cc"
        )
        knob_element = next(
            element
            for element in manager.findall("Shortcut")
            if int(element.find("RawInputMessage").attrib["key"]) == knob.raw_key
        )
        knob_element.attrib["uniqueId"] = str(fader_base + 1000)
        collision_bytes = generator.serialize_preset_root(root)
        with self.assertRaisesRegex(generator.ValidationError, "collides"):
            generator.build_candidate(
                mode="pilot",
                baseline_bytes=collision_bytes,
                baseline_path=self.baseline_path,
                calibration=self.provisional,
            )

    def test_candidate_check_cli_writes_nothing(self) -> None:
        output_dir = self.root / "must-not-exist"
        test_calibration, test_manifest = _write_calibration_fixture(
            self.root / "cli-test-only",
            "provisional",
            test_only=True,
        )
        command = [
            sys.executable,
            str(SCRIPT),
            "candidate",
            "--mode",
            "pilot",
            "--baseline",
            str(self.baseline_path),
            "--calibration",
            str(test_calibration),
            "--build-manifest",
            str(test_manifest),
            "--campaign-dir",
            str(output_dir),
            "--check",
            "--test-only",
        ]
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["wrote_files"])
        self.assertFalse(output_dir.exists())

    def test_bare_cli_invocation_is_read_only(self) -> None:
        manifest_before = (
            generator.MANIFEST_PATH.read_bytes()
            if generator.MANIFEST_PATH.exists()
            else None
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            check=True,
            capture_output=True,
            text=True,
            cwd=self.root,
        )
        result = json.loads(completed.stdout)
        self.assertFalse(result["wrote_files"])
        manifest_after = (
            generator.MANIFEST_PATH.read_bytes()
            if generator.MANIFEST_PATH.exists()
            else None
        )
        self.assertEqual(manifest_before, manifest_after)

    def test_hash_gated_install_and_exact_rollback_in_temp_directory(self) -> None:
        pilot = self.build_pilot()
        artifact_dir = self.root / "campaign"
        artifacts = generator.write_candidate_artifacts(pilot, artifact_dir)
        original_hash = hashlib.sha256(self.repo_baseline).hexdigest()
        install_preflight, install_preflight_hash = _write_preflight(
            self.root,
            "install-pilot",
            active_sha256=original_hash,
        )
        receipt = generator.install_candidate(
            candidate_path=artifacts["candidate"],
            metadata_path=artifacts["metadata"],
            active_path=self.baseline_path,
            campaign_dir=artifact_dir,
            preflight_path=install_preflight,
            preflight_sha256=install_preflight_hash,
            sleep_seconds=0,
        )
        self.assertEqual(
            hashlib.sha256(self.baseline_path.read_bytes()).hexdigest(),
            pilot.candidate_sha256,
        )
        backup_path = Path(str(receipt["backup_path"]))
        rollback_preflight, rollback_preflight_hash = _write_preflight(
            self.root,
            "rollback-prepilot",
            active_sha256=pilot.candidate_sha256,
        )
        rollback = generator.rollback_preset(
            active_path=self.baseline_path,
            backup_path=backup_path,
            expected_current_hash=pilot.candidate_sha256,
            target_backup_hash=original_hash,
            campaign_dir=artifact_dir,
            backup_receipt_path=Path(str(receipt["receipt_path"])),
            backup_receipt_sha256=str(receipt["receipt_sha256"]),
            preflight_path=rollback_preflight,
            preflight_sha256=rollback_preflight_hash,
            preflight_stage="rollback-prepilot",
            sleep_seconds=0,
        )
        self.assertEqual(rollback["target_backup_hash"], original_hash)
        self.assertEqual(self.baseline_path.read_bytes(), self.repo_baseline)

    def test_install_rejects_baseline_drift(self) -> None:
        pilot = self.build_pilot()
        artifact_dir = self.root / "campaign"
        artifacts = generator.write_candidate_artifacts(pilot, artifact_dir)
        original_hash = hashlib.sha256(self.repo_baseline).hexdigest()
        preflight, preflight_hash = _write_preflight(
            self.root,
            "install-pilot",
            active_sha256=original_hash,
        )
        self.baseline_path.write_bytes(self.repo_baseline + b"\n")
        with self.assertRaises(generator.HashMismatch):
            generator.install_candidate(
                candidate_path=artifacts["candidate"],
                metadata_path=artifacts["metadata"],
                active_path=self.baseline_path,
                campaign_dir=artifact_dir,
                preflight_path=preflight,
                preflight_sha256=preflight_hash,
                sleep_seconds=0,
            )

    def test_manifest_writer_rejects_xml_and_preset_paths(self) -> None:
        for path in (
            self.root / "not-a-manifest.xml",
            generator.ACTIVE_PRESET,
            generator.REPO_PRESET,
        ):
            with self.subTest(path=path):
                with self.assertRaisesRegex(generator.ValidationError, "XML|preset"):
                    generator.write_manifest(path)

    def test_test_only_manifest_cannot_be_relabelled_for_install(self) -> None:
        with self.assertRaisesRegex(generator.ValidationError, "test_only"):
            generator.load_calibration(
                self.accepted.path,
                mode="full",
                build_manifest_path=self.accepted.build_manifest_path,
                test_only=False,
            )

    def test_incomplete_build_manifest_fails_closed(self) -> None:
        calibration_path, manifest_path = _write_calibration_fixture(
            self.root / "incomplete",
            "provisional",
            test_only=False,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifact_key = next(
            key
            for key in manifest["artifacts"]
            if Path(key).name == "APC40_visual_qa_live_overlay.png"
        )
        del manifest["artifacts"][artifact_key]
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(generator.ValidationError, "incomplete"):
            generator.load_calibration(
                calibration_path,
                mode="pilot",
                build_manifest_path=manifest_path,
                test_only=False,
            )

    def test_install_rejects_build_manifest_drift_before_mutation(self) -> None:
        pilot = self.build_pilot()
        artifact_dir = self.root / "campaign"
        artifacts = generator.write_candidate_artifacts(pilot, artifact_dir)
        original_hash = hashlib.sha256(self.repo_baseline).hexdigest()
        preflight, preflight_hash = _write_preflight(
            self.root,
            "install-pilot",
            active_sha256=original_hash,
        )
        manifest_path = self.provisional.build_manifest_path
        assert manifest_path is not None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["drift_after_candidate"] = True
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(generator.ValidationError, "manifest hash differs"):
            generator.install_candidate(
                candidate_path=artifacts["candidate"],
                metadata_path=artifacts["metadata"],
                active_path=self.baseline_path,
                campaign_dir=artifact_dir,
                preflight_path=preflight,
                preflight_sha256=preflight_hash,
                sleep_seconds=0,
            )
        self.assertEqual(self.baseline_path.read_bytes(), self.repo_baseline)

    def test_mutation_preflight_rejects_stale_or_wrong_runtime_state(self) -> None:
        active_hash = hashlib.sha256(self.repo_baseline).hexdigest()
        valid_path, valid_hash = _write_preflight(
            self.root / "valid-preflight",
            "install-pilot",
            active_sha256=active_hash,
        )
        generator.validate_mutation_preflight(
            valid_path,
            expected_sha256=valid_hash,
            expected_stage="install-pilot",
            expected_active_sha256=active_hash,
        )

        cases = (
            {
                "name": "stale",
                "kwargs": {
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=11)
                },
                "expected": "older than 10 minutes",
            },
            {
                "name": "wrong-layer-count",
                "kwargs": {"expected_layer_count": 149},
                "expected": "148 layers",
            },
            {
                "name": "duplicate-bridge",
                "kwargs": {"bridge_pids": [1, 2]},
                "expected": "one bridge",
            },
            {
                "name": "watcher",
                "kwargs": {"watcher_pids": [123]},
                "expected": "zero pulse watcher",
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                path, digest = _write_preflight(
                    self.root / str(case["name"]),
                    "install-pilot",
                    active_sha256=active_hash,
                    **case["kwargs"],
                )
                with self.assertRaisesRegex(
                    generator.ValidationError, str(case["expected"])
                ):
                    generator.validate_mutation_preflight(
                        path,
                        expected_sha256=digest,
                        expected_stage="install-pilot",
                        expected_active_sha256=active_hash,
                    )
        with self.assertRaisesRegex(generator.ValidationError, "stage mismatch"):
            generator.validate_mutation_preflight(
                valid_path,
                expected_sha256=valid_hash,
                expected_stage="install-full",
                expected_active_sha256=active_hash,
            )

    def test_rollback_rejects_repo_or_noncampaign_backup_before_mutation(self) -> None:
        original_hash = hashlib.sha256(self.repo_baseline).hexdigest()
        campaign = self.root / "campaign"
        campaign.mkdir()
        fake_receipt = campaign / "receipt.json"
        fake_receipt.write_text("{}\n", encoding="utf-8")
        preflight, preflight_hash = _write_preflight(
            self.root,
            "rollback-prepilot",
            active_sha256=original_hash,
        )
        with self.assertRaisesRegex(generator.ValidationError, "campaign directory"):
            generator.rollback_preset(
                active_path=self.baseline_path,
                backup_path=generator.REPO_PRESET,
                expected_current_hash=original_hash,
                target_backup_hash=hashlib.sha256(
                    generator.REPO_PRESET.read_bytes()
                ).hexdigest(),
                campaign_dir=campaign,
                backup_receipt_path=fake_receipt,
                backup_receipt_sha256=hashlib.sha256(
                    fake_receipt.read_bytes()
                ).hexdigest(),
                preflight_path=preflight,
                preflight_sha256=preflight_hash,
                preflight_stage="rollback-prepilot",
                sleep_seconds=0,
            )
        self.assertEqual(self.baseline_path.read_bytes(), self.repo_baseline)

    def test_build_requires_readable_pristine_repo_reference(self) -> None:
        with self.assertRaises(generator.GeneratorError):
            generator.build_candidate(
                mode="pilot",
                baseline_bytes=self.repo_baseline,
                baseline_path=self.baseline_path,
                calibration=self.provisional,
                repo_reference_path=self.root / "missing-reference.xml",
            )
        invalid_reference = self.root / "invalid-reference.xml"
        invalid_reference.write_text("<not-a-preset />", encoding="utf-8")
        with self.assertRaises(generator.ValidationError):
            generator.build_candidate(
                mode="pilot",
                baseline_bytes=self.repo_baseline,
                baseline_path=self.baseline_path,
                calibration=self.provisional,
                repo_reference_path=invalid_reference,
            )

    def test_same_raw_derived_id_semantic_collision_fails_closed(self) -> None:
        for mutation in ("wrong-value", "empty-output-attribute"):
            with self.subTest(mutation=mutation):
                root = ET.fromstring(self.repo_baseline)
                manager = root.find("ShortcutManager")
                assert manager is not None
                baseline = generator.parse_preset_bytes(self.repo_baseline)
                fader = generator.build_controls()[93]
                base_id = next(
                    record.unique_id
                    for record in baseline.semantics
                    if record.raw_key == fader.raw_key
                )
                wake = generator._wake_shortcut(fader, base_id + 1000)
                if mutation == "wrong-value":
                    raw = wake.find("RawInputMessage")
                    assert raw is not None
                    raw.attrib["value"] = "0"
                else:
                    wake.attrib["outputDeviceName"] = ""
                manager.append(wake)
                collision_bytes = generator.serialize_preset_root(root)
                with self.assertRaisesRegex(generator.ValidationError, "collides"):
                    generator.build_candidate(
                        mode="pilot",
                        baseline_bytes=collision_bytes,
                        baseline_path=self.baseline_path,
                        calibration=self.provisional,
                    )


if __name__ == "__main__":
    unittest.main()
