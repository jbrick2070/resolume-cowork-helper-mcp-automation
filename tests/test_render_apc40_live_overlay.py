"""Focused offline tests for the APC40 live-overlay renderer."""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_apc40_live_overlay.py"
VALID_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "2026-07-18-apc40-animated-visual-qa"
    / "offline-preview"
    / "APC40_visual_qa_manifest.json"
)
SPEC = importlib.util.spec_from_file_location("apc40_renderer", SCRIPT)
assert SPEC and SPEC.loader
renderer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = renderer
SPEC.loader.exec_module(renderer)


class RendererTests(unittest.TestCase):
    def arguments(self, output: Path, measurement: Path | None = None) -> tuple:
        return (
            VALID_MANIFEST,
            renderer.DEFAULT_SVG,
            output,
            renderer.DEFAULT_LABEL_FONT,
            renderer.DEFAULT_GLYPH_FONT,
            renderer.DEFAULT_FALLBACK_GLYPH_FONT,
            measurement,
        )

    def publish_b0(self, output: Path) -> tuple[dict, dict]:
        artifacts, build_manifest = renderer.build_artifacts(*self.arguments(output))
        renderer.write_artifacts(artifacts, build_manifest, output)
        return artifacts, build_manifest

    @staticmethod
    def observed_parent_hashes(build_manifest: dict) -> dict:
        required = {
            renderer.ARTIFACT_NAMES["geometry"],
            renderer.ARTIFACT_NAMES["calibration"],
            renderer.ARTIFACT_NAMES["live_controls"],
            renderer.ARTIFACT_NAMES["overlay"],
        }
        return {
            key: value
            for key, value in build_manifest["artifacts"].items()
            if Path(key).name in required
        }

    def test_check_is_deterministic_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "not-created"
            artifacts, build_manifest = renderer.check_determinism(*self.arguments(output))
            self.assertFalse(output.exists())
            self.assertTrue(build_manifest["build_id"].startswith("B0-"))
            self.assertEqual(build_manifest["status"], "provisional")
            self.assertEqual(len(artifacts), 13)

    def test_fader_tags_and_calibration_are_directionally_truthful(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts, _ = renderer.build_artifacts(*self.arguments(Path(directory)))
            live_path = Path(directory) / renderer.ARTIFACT_NAMES["live_controls"]
            calibration_path = Path(directory) / renderer.ARTIFACT_NAMES["calibration"]
            live = json.loads(artifacts[live_path])
            calibration = json.loads(artifacts[calibration_path])
            self.assertEqual(live["layers"]["94"]["witness"]["text"], "\u25ac FADER1\nCC7/C1")
            self.assertEqual(live["layers"]["143"]["witness"]["text"], "\u25ac MASTER\nCC14/C1")
            self.assertEqual(live["layers"]["144"]["witness"]["text"], "\u2588 X-FADE\nCC15/C1")
            vertical = calibration["motion_ranges_by_layer"]["94"]
            self.assertGreater(vertical["value_at_cc0"], vertical["value_at_cc127"])
            self.assertGreater(vertical["geometry"]["travel_px"], 140)
            horizontal = calibration["motion_ranges_by_layer"]["144"]
            self.assertLess(horizontal["value_at_cc0"], horizontal["value_at_cc127"])
            self.assertGreater(horizontal["geometry"]["travel_px"], 100)
            self.assertNotIn(b"connect_continuous", artifacts[live_path])
            self.assertTrue(
                all(b"connect_continuous" not in payload for payload in artifacts.values())
            )

    def test_publication_hashes_every_artifact_and_manifest_is_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            artifacts, build_manifest = renderer.build_artifacts(*self.arguments(output))
            renderer.write_artifacts(artifacts, build_manifest, output)
            manifest_path = output / renderer.ARTIFACT_NAMES["build_manifest"]
            published = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertNotIn(manifest_path.name, {Path(key).name for key in published["artifacts"]})
            for key, metadata in published["artifacts"].items():
                path = output / Path(key).name
                self.assertEqual(renderer.sha256_file(path), metadata["sha256"])
                self.assertEqual(path.stat().st_size, metadata["bytes"])
            self.assertEqual((output / renderer.ARTIFACT_NAMES["overlay"]).read_bytes()[:8],
                             b"\x89PNG\r\n\x1a\n")

    def test_measurement_produces_lineage_bound_accepted_b1(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            artifacts, b0 = self.publish_b0(output)
            observed = self.observed_parent_hashes(b0)
            measurement = {
                "schema_version": 1,
                "build_id": b0["build_id"],
                "measurement_parent_artifact_hashes": observed,
                "selected_avenue_size": 2.125,
                "accepted_live_tag_metrics": {
                    "vertical": {"ink_box_px": [80, 30]},
                    "horizontal": {"ink_box_px": [70, 30]},
                },
            }
            measurement_path = output / "APC40_visual_qa_tag_measurement.json"
            measurement_path.write_text(
                json.dumps(measurement, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            b1_artifacts, b1 = renderer.check_determinism(
                *self.arguments(output, measurement_path)
            )
            self.assertTrue(b1["build_id"].startswith("B1-"))
            self.assertEqual(b1["status"], "accepted")
            self.assertEqual(b1["parent_build_id"], b0["build_id"])
            calibration_path = output / renderer.ARTIFACT_NAMES["calibration"]
            calibration = json.loads(b1_artifacts[calibration_path])
            self.assertEqual(calibration["status"], "accepted")
            self.assertEqual(calibration["parent_build_id"], b0["build_id"])
            self.assertEqual(calibration["measurement_sha256"], b1["measurement_sha256"])
            accepted = calibration["accepted_live_tag_metrics"]
            self.assertEqual(
                accepted["measurement_reference"]["ink_box_px"],
                [80, 30],
            )
            self.assertGreaterEqual(
                accepted["vertical"]["ink_box_px"][0],
                accepted["by_layer"]["143"]["ink_box_px"][0],
            )
            self.assertGreaterEqual(
                accepted["vertical"]["ink_box_px"][1],
                accepted["by_layer"]["143"]["ink_box_px"][1],
            )
            self.assertEqual(
                accepted["horizontal"]["ink_box_px"],
                accepted["by_layer"]["144"]["ink_box_px"],
            )
            self.assertNotEqual(
                accepted["horizontal"]["ink_box_px"],
                measurement["accepted_live_tag_metrics"]["horizontal"]["ink_box_px"],
            )
            report_path = output / renderer.ARTIFACT_NAMES["report"]
            report = json.loads(b1_artifacts[report_path])
            self.assertEqual(
                report["checks"]["moving_tag_metric_source"],
                "accepted_live_tag_metrics",
            )
            debug_path = output / renderer.ARTIFACT_NAMES["debug"]
            self.assertNotEqual(b1_artifacts[debug_path], artifacts[debug_path])
            live_path = output / renderer.ARTIFACT_NAMES["live_controls"]
            live = json.loads(b1_artifacts[live_path])
            size_field = next(
                field
                for field in live["layers"]["94"]["fields"]
                if field["parameter"] == "Size"
            )
            self.assertEqual(size_field["desired"], 2.125)

    def test_provisional_live_tag_size_uses_measured_safe_hint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            artifacts, _ = self.publish_b0(output)
            live_path = output / renderer.ARTIFACT_NAMES["live_controls"]
            live = json.loads(artifacts[live_path])
            self.assertEqual(
                live["glyph_font"]["provisional_moving_tag_size_hint"],
                renderer.PROVISIONAL_MOVING_TAG_SIZE_HINT,
            )
            for layer in (*renderer.VERTICAL_MOVING_TAG_LAYERS, 144):
                size_field = next(
                    field
                    for field in live["layers"][str(layer)]["fields"]
                    if field["parameter"] == "Size"
                )
                self.assertEqual(
                    size_field["desired"],
                    renderer.PROVISIONAL_MOVING_TAG_SIZE_HINT,
                )

    def test_live_fader_scale_expands_master_and_xfade_actual_tags(self) -> None:
        base_metric = {
            "text": "\u25ac FADER1\nCC7/C1",
            "ink_box_px": [40, 20],
        }
        tag_metrics = {
            str(layer): dict(base_metric)
            for layer in renderer.VERTICAL_MOVING_TAG_LAYERS
        }
        tag_metrics["143"] = {
            "text": "\u25ac MASTER\nCC14/C1",
            "ink_box_px": [60, 22],
        }
        tag_metrics["144"] = {
            "text": "\u2588 X-FADE\nCC15/C1",
            "ink_box_px": [58, 25],
        }
        glyph_font = renderer.FontChoice(
            Path("synthetic-glyph-font.ttf"),
            "Synthetic Glyph Font",
            18,
            -1,
            tag_metrics,
        )
        measured_fader = {
            "vertical": {"ink_box_px": [60, 24]},
            # The old implementation trusted this raw Fader 1-sized horizontal
            # envelope even though X-FADE is a different string and glyph.
            "horizontal": {"ink_box_px": [60, 24]},
        }

        derived = renderer.derive_accepted_live_tag_metrics(
            measured_fader,
            glyph_font,
            2.25,
        )

        self.assertEqual(
            derived["live_to_offline_scale"],
            {
                "width": {"numerator": 60, "denominator": 40},
                "height": {"numerator": 24, "denominator": 20},
            },
        )
        self.assertEqual(derived["by_layer"]["94"]["ink_box_px"], [60, 24])
        self.assertEqual(derived["by_layer"]["143"]["ink_box_px"], [90, 27])
        self.assertEqual(derived["vertical"]["ink_box_px"], [90, 27])
        self.assertEqual(derived["by_layer"]["144"]["ink_box_px"], [87, 30])
        self.assertEqual(derived["horizontal"]["ink_box_px"], [87, 30])
        self.assertGreater(
            derived["vertical"]["ink_box_px"][0],
            measured_fader["vertical"]["ink_box_px"][0],
        )
        self.assertGreater(
            derived["horizontal"]["ink_box_px"][0],
            measured_fader["horizontal"]["ink_box_px"][0],
        )

        oversized_metrics = dict(tag_metrics)
        oversized_metrics["143"] = {
            "text": "\u25ac MASTER\nCC14/C1",
            "ink_box_px": [70, 22],
        }
        with self.assertRaisesRegex(
            renderer.RenderError,
            r"layer 143 .*exceeding 92x42",
        ):
            renderer.derive_accepted_live_tag_metrics(
                measured_fader,
                renderer.FontChoice(
                    Path("synthetic-glyph-font.ttf"),
                    "Synthetic Glyph Font",
                    18,
                    -1,
                    oversized_metrics,
                ),
                2.25,
            )

    def test_measurement_rejects_malicious_size_and_ink_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            _, b0 = self.publish_b0(output)
            observed = self.observed_parent_hashes(b0)
            valid_metrics = {
                "vertical": {"ink_box_px": [80, 30]},
                "horizontal": {"ink_box_px": [70, 30]},
            }
            cases = (
                (
                    "schema",
                    {
                        "schema_version": 999,
                        "selected_avenue_size": 2.125,
                        "accepted_live_tag_metrics": valid_metrics,
                    },
                    "schema_version 1",
                ),
                (
                    "size99",
                    {
                        "schema_version": 1,
                        "selected_avenue_size": 99,
                        "accepted_live_tag_metrics": valid_metrics,
                    },
                    "within 0.5..4.0",
                ),
                (
                    "ink300",
                    {
                        "schema_version": 1,
                        "selected_avenue_size": 2.125,
                        "accepted_live_tag_metrics": {
                            "vertical": {"ink_box_px": [300, 300]},
                            "horizontal": {"ink_box_px": [300, 300]},
                        },
                    },
                    "exceeding 92x42",
                ),
            )
            for name, overrides, message in cases:
                with self.subTest(name=name):
                    measurement = {
                        "build_id": b0["build_id"],
                        "measurement_parent_artifact_hashes": observed,
                        **overrides,
                    }
                    measurement_path = output / f"{name}.json"
                    measurement_path.write_text(
                        json.dumps(measurement, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(renderer.RenderError, message):
                        renderer.build_artifacts(
                            *self.arguments(output, measurement_path)
                        )

    def test_numeric_raw_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = json.loads(VALID_MANIFEST.read_text(encoding="utf-8"))
            manifest[0]["raw_key"] = int(manifest[0]["raw_key"])
            path = Path(directory) / "numeric-raw-key.json"
            path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                renderer.RenderError, "raw_key must be a decimal string"
            ):
                renderer.load_manifest(path)

    def test_geometry_rejects_ring_body_and_swept_label_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts, _ = renderer.build_artifacts(*self.arguments(Path(directory)))
            geometry_path = Path(directory) / renderer.ARTIFACT_NAMES["geometry"]
            geometry = json.loads(artifacts[geometry_path])

            ring_body = copy.deepcopy(geometry)
            by_layer = {
                record["layer"]: record
                for record in ring_body["controls"].values()
            }
            by_layer[1]["body_box"] = [180, 120, 200, 140]
            with self.assertRaisesRegex(
                renderer.RenderError, "ring reaches layer 1 body"
            ):
                renderer.validate_geometry(ring_body)

            swept_label = copy.deepcopy(geometry)
            by_layer = {
                record["layer"]: record
                for record in swept_label["controls"].values()
            }
            by_layer[118]["label_box"] = [150, 785, 170, 795]
            with self.assertRaisesRegex(
                renderer.RenderError, "swept witness reaches layer 118 label"
            ):
                renderer.validate_geometry(swept_label)

    def test_bank_polygons_respect_half_open_body_boxes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts, _ = renderer.build_artifacts(*self.arguments(Path(directory)))
            geometry_path = Path(directory) / renderer.ARTIFACT_NAMES["geometry"]
            geometry = json.loads(artifacts[geometry_path])
            for record in geometry["controls"].values():
                if record["prototype"] != "bank_polygon":
                    continue
                left, top, right, bottom = record["body_box"]
                for x, y in record["body_polygon"]:
                    self.assertGreaterEqual(x, left)
                    self.assertGreaterEqual(y, top)
                    self.assertLess(x, right)
                    self.assertLess(y, bottom)
            overlay_path = Path(directory) / renderer.ARTIFACT_NAMES["overlay"]
            with renderer.Image.open(io.BytesIO(artifacts[overlay_path])) as overlay:
                overlay.load()
                for record in geometry["controls"].values():
                    ring = record.get("ring")
                    if not ring:
                        continue
                    left, top, right, bottom = ring["box"]
                    center_x, center_y = ring["center_px"]
                    self.assertEqual(overlay.getpixel((right, center_y)), (0, 0, 0))
                    self.assertEqual(overlay.getpixel((center_x, bottom)), (0, 0, 0))

    def test_calibration_rejects_nonpositive_measured_travel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifacts, _ = renderer.build_artifacts(*self.arguments(Path(directory)))
            geometry_path = Path(directory) / renderer.ARTIFACT_NAMES["geometry"]
            geometry = json.loads(artifacts[geometry_path])
            layer94 = next(
                record
                for record in geometry["controls"].values()
                if record["layer"] == 94
            )
            left, top, right, _ = layer94["lane_box"]
            layer94["lane_box"] = [left, top, right, top + 30]
            controls, _ = renderer.load_manifest(VALID_MANIFEST)
            glyph_font = renderer.choose_glyph_font(
                controls,
                renderer.DEFAULT_GLYPH_FONT,
                renderer.DEFAULT_FALLBACK_GLYPH_FONT,
            )
            metrics = {
                "vertical": {"ink_box_px": [80, 30]},
                "horizontal": {"ink_box_px": [70, 30]},
            }
            with self.assertRaisesRegex(
                renderer.RenderError, "non-positive vertical tag travel"
            ):
                renderer.build_calibration(
                    geometry,
                    glyph_font,
                    "test-build",
                    accepted_live_tag_metrics=metrics,
                )


if __name__ == "__main__":
    unittest.main()
