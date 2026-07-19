from __future__ import annotations

import contextlib
import dataclasses
import importlib.util
import io
import json
import struct
import sys
import tempfile
import time
import types
import unittest
import zlib
from pathlib import Path
from typing import Any

from PIL import Image


SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "apc40_visual_qa_live.py"
)
SPEC = importlib.util.spec_from_file_location("apc40_visual_qa_live", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
live = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = live
SPEC.loader.exec_module(live)


def response_bytes(
    body: bytes = b"",
    *,
    status: int = 200,
    reason: str = "OK",
    headers: list[tuple[str, str]] | None = None,
) -> bytes:
    actual_headers = list(headers or [])
    if not any(key.casefold() == "content-length" for key, _ in actual_headers):
        actual_headers.append(("Content-Length", str(len(body))))
    head = [f"HTTP/1.1 {status} {reason}"]
    head.extend(f"{key}: {value}" for key, value in actual_headers)
    return ("\r\n".join(head) + "\r\n\r\n").encode("ascii") + body


def chunked_response(
    chunks: list[bytes], trailers: list[tuple[str, str]] | None = None
) -> bytes:
    head = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: application/json\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"X-Repeat: one\r\n"
        b"X-Repeat: two\r\n\r\n"
    )
    encoded = bytearray(head)
    for chunk in chunks:
        encoded.extend(f"{len(chunk):X}\r\n".encode("ascii"))
        encoded.extend(chunk)
        encoded.extend(b"\r\n")
    encoded.extend(b"0\r\n")
    for key, value in trailers or []:
        encoded.extend(f"{key}: {value}\r\n".encode("ascii"))
    encoded.extend(b"\r\n")
    return bytes(encoded)


class FakeConnection:
    def __init__(self, chunks: list[bytes], *, fail_write: bool = False) -> None:
        self.chunks = list(chunks)
        self.fail_write = fail_write
        self.writes: list[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        if self.fail_write:
            raise OSError("injected write failure")
        return len(data)

    def read(self, size: int) -> bytes:
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk

    def close(self) -> None:
        self.closed = True


class SlowConnection(FakeConnection):
    def __init__(self, delay: float, chunks: list[bytes]) -> None:
        super().__init__(chunks)
        self.delay = delay

    def read(self, size: int) -> bytes:
        time.sleep(self.delay)
        return super().read(size)


class Factory:
    def __init__(self, connections: list[FakeConnection]) -> None:
        self.connections = list(connections)
        self.created: list[FakeConnection] = []

    def __call__(self, _: str) -> FakeConnection:
        if not self.connections:
            raise OSError("no scripted connection")
        connection = self.connections.pop(0)
        self.created.append(connection)
        return connection


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", crc)
    )


def make_png(width: int = 1920, height: int = 1080, color_type: int = 6) -> bytes:
    mode = "RGBA" if color_type == 6 else "RGB"
    image = Image.new(mode, (width, height), (0, 0, 0, 255) if mode == "RGBA" else (0, 0, 0))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def make_tag_png(
    bounds: tuple[int, int, int, int] | None,
    *,
    color: tuple[int, int, int, int] = (23, 200, 232, 255),
    noise_pixels: list[tuple[int, int]] | None = None,
) -> bytes:
    image = Image.new("RGBA", (1920, 1080), (0, 0, 0, 255))
    if bounds is not None:
        left, top, right, bottom = bounds
        for y in range(top, bottom):
            for x in range(left, right):
                image.putpixel((x, y), color)
    for point in noise_pixels or []:
        image.putpixel(point, (255, 255, 255, 255))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def make_structurally_valid_but_undecodable_png(
    width: int = 1920, height: int = 1080
) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        live.PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(b"\x00"))
        + png_chunk(b"IEND", b"")
    )


def valid_processes(*, avenue_count: int = 1, mcp_count: int = 1) -> list:
    rows = [
        live.ProcessRecord(
            100 + index,
            "Avenue.exe",
            r"C:\Program Files\Resolume Avenue\Avenue.exe",
            "",
        )
        for index in range(avenue_count)
    ]
    rows.append(
        live.ProcessRecord(
            200,
            "python.exe",
            "",
            r"python C:\Art Projects\Res_Fable\avenue_pipe_bridge.py",
        )
    )
    rows.extend(
        live.ProcessRecord(
            300 + index,
            "node.exe",
            "",
            "node resolume-mcp server",
        )
        for index in range(mcp_count)
    )
    return rows


def write_active_preset(root: Path, payload: bytes = b"<preset />") -> Path:
    path = root / "active.xml"
    path.write_bytes(payload)
    return path


def publish_snapshot(
    runner: Any, path: Path, snapshot: dict[str, Any]
) -> None:
    live.atomic_write_json(path, snapshot)
    runner.journal.append(
        {
            "kind": "campaign_snapshot_published",
            "snapshot": str(path.resolve()),
            "snapshot_sha256": live.sha256_file(path),
            "artifact_id": snapshot["artifact_id"],
            "build_id": snapshot["build_id"],
            "restart_stage": snapshot["restart_stage"],
            "active_preset_path": snapshot["active_preset_path"],
            "active_preset_sha256": snapshot["active_preset_sha256"],
            "expected_layer_count": snapshot["expected_layer_count"],
            "composition_fingerprint": snapshot["composition_fingerprint"]["sha256"],
        }
    )


def write_live_bundle(
    root: Path,
    manifest: list[dict[str, Any]],
    *,
    build_id: str,
    status: str,
) -> tuple[Path, Path, Path]:
    def fields_for_layer(layer: int) -> list[dict[str, Any]]:
        fields = [
            {
                "target": "text_animator_source",
                "parameter": "Text",
                "valuetype": "ParamText",
                "desired": f"L{layer}",
                "purpose": "test",
            }
        ]
        if layer == 94:
            fields.extend(
                [
                    {
                        "target": "text_animator_source",
                        "parameter": "Font",
                        "valuetype": "ParamChoice",
                        "desired": "Segoe UI Symbol",
                        "purpose": "test glyph coverage",
                    },
                    {
                        "target": "text_animator_source",
                        "parameter": "Size",
                        "valuetype": "ParamRange",
                        "desired": 2.25,
                        "purpose": "test raster size",
                    },
                    {
                        "target": "text_animator_source",
                        "parameter": "Position X",
                        "valuetype": "ParamRange",
                        "desired": 0.0,
                        "purpose": "test source position",
                    },
                    {
                        "target": "text_animator_source",
                        "parameter": "Position Y",
                        "valuetype": "ParamRange",
                        "desired": 0.0,
                        "purpose": "test source position",
                    },
                    {
                        "target": "text_animator_source",
                        "parameter": "Spacing Y",
                        "valuetype": "ParamRange",
                        "desired": -10.0,
                        "purpose": "test line spacing",
                    },
                ]
            )
        return fields

    controls = root / f"{build_id}-controls.json"
    overlay = root / f"{build_id}-overlay.png"
    geometry = root / "APC40_visual_qa_geometry.json"
    calibration = root / "APC40_visual_qa_calibration.json"
    controls.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "build_id": build_id,
                "status": status,
                "artifact_role": "typed_live_controls",
                "wave_size": 24,
                "glyph_font": {
                    "offline_path": "font.ttf",
                    "live_family": "Segoe UI Symbol",
                    "offline_size_px": 18,
                    "live_size_value": 18,
                    "measurement_status": status,
                },
                "layers": {
                    str(layer): {
                        "layer": layer,
                        "raw_key": str(1_000_000 + layer),
                        "midi_label": manifest[layer - 1]["midi_label"],
                        "category": "test",
                        "witness": {
                            "kind": "test",
                            "text": "x",
                            "color": "#ffffffff",
                            "box": [143, 783, 239, 1013]
                            if layer == 94
                            else None,
                        },
                        "fields": fields_for_layer(layer),
                    }
                    for layer in range(1, 149)
                },
            }
        ),
        encoding="utf-8",
    )
    overlay.write_bytes(make_png())
    geometry.write_text(
        json.dumps({"schema_version": 1, "build_id": build_id}),
        encoding="utf-8",
    )
    calibration.write_text(
        json.dumps({"schema_version": 1, "build_id": build_id}),
        encoding="utf-8",
    )
    artifacts = {
        path.relative_to(root).as_posix(): {
            "sha256": live.sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in (controls, overlay, geometry, calibration)
    }
    build_manifest = root / f"{build_id}-build.json"
    build_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "build_id": build_id,
                "status": status,
                "parent_build_id": "B0-parent" if status == "accepted" else None,
                "measurement_sha256": "3" * 64 if status == "accepted" else None,
                "artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )
    return controls, overlay, build_manifest


def param(value: Any, valuetype: str = "ParamString", identifier: int = 1) -> dict:
    result = {"id": identifier, "valuetype": valuetype, "value": value}
    if valuetype in ("ParamChoice", "ParamState"):
        result.update({"index": 1 if str(value).startswith("Connected") else 0})
    return result


def make_clip(
    layer: int,
    *,
    name: str | None = None,
    connected: bool = False,
    cc: bool = False,
) -> dict:
    clip = {
        "id": 20_000 + layer,
        "name": param(name or f"N{layer}/C1"),
        "connected": param(
            "Connected" if connected else "Disconnected", "ParamChoice", 30_000 + layer
        ),
        "triggerstyle": param(
            "Normal" if cc else "Toggle", "ParamChoice", 40_000 + layer
        ),
        "video": {
            "description": "Text Animator",
            "sourceparams": {
                "Text": param(f"L{layer}", "ParamText", 50_000 + layer),
                "Font": param(
                    "Barlow Condensed",
                    "ParamChoice",
                    110_000 + layer,
                ),
                "Size": param(1.5, "ParamRange", 120_000 + layer),
                "Position X": param(1.0, "ParamRange", 130_000 + layer),
                "Position Y": param(2.0, "ParamRange", 140_000 + layer),
                "Spacing Y": param(0.0, "ParamRange", 150_000 + layer),
                "Color": param("#17c8e8ff", "ParamColor", 160_000 + layer),
                "Opacity": param(1.0, "ParamRange", 170_000 + layer),
            },
            "effects": [],
        },
    }
    if cc:
        clip["video"]["opacity"] = param(1.0, "ParamRange", 60_000 + layer)
        clip["video"]["effects"] = [
            {
                "id": 70_000 + layer,
                "name": "Transform",
                "display_name": "Transform",
                "is_user_removable": False,
                "params": {
                    "Position X": param(0.0, "ParamRange", 80_000 + layer),
                    "Position Y": param(0.0, "ParamRange", 90_000 + layer),
                    "Rotation Z": param(0.0, "ParamRange", 100_000 + layer),
                },
            }
        ]
    return clip


def make_composition(
    *,
    connected_layers: set[int] | None = None,
    manifest: list[dict] | None = None,
) -> tuple[dict, dict[int, dict]]:
    connected_layers = connected_layers or set()
    clips: dict[int, dict] = {}
    layers = []
    generated_manifest: list[dict] = []
    for layer in range(1, 149):
        cc = layer in live.CC_LAYERS
        if manifest is None:
            record = {
                "layer": layer,
                "layer_name": f"Layer {layer}",
                "midi_label": f"{'CC' if cc else 'N'}{layer}/C1",
                "midi_type": "cc" if cc else "note",
            }
            generated_manifest.append(record)
        else:
            record = manifest[layer - 1]
        clip = make_clip(
            layer,
            name=record["midi_label"],
            connected=layer in connected_layers,
            cc=cc,
        )
        clips[layer] = clip
        layers.append(
            {
                "id": 10_000 + layer,
                "name": param(record["layer_name"]),
                "clips": [clip],
            }
        )
    composition = {
        "name": param(live.DEFAULT_COMPOSITION_NAME),
        "video": {
            "width": param(1920, "ParamRange"),
            "height": param(1080, "ParamRange"),
        },
        "columns": [{"id": 9001}],
        "layers": layers,
    }
    return composition, clips


def json_response(value: Any) -> live.HttpResponse:
    data = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return live.HttpResponse(
        200, "OK", (("Content-Type", "application/json"),), data
    )


class FakeApiClient:
    def __init__(self, composition: dict, clips: dict[int, dict]) -> None:
        self.composition = composition
        self.clips = clips
        self.calls: list[tuple[str, str, Any]] = []
        self.fail_after_put_number: int | None = None
        self.put_count = 0
        self.tag_bounds: tuple[int, int, int, int] = (150, 880, 220, 910)
        self.tag_noise_pixels: list[tuple[int, int]] = []
        self.text_render_delay_polls = 0
        self.monitor_snapshot_count = 0
        self._rendered_text = str(
            clips[94]["video"]["sourceparams"]["Text"]["value"]
        )
        self._pending_rendered_text: str | None = None
        self._render_delay_remaining = 0

    def monitor_png(self) -> bytes:
        self.monitor_snapshot_count += 1
        if self._pending_rendered_text is not None:
            if self._render_delay_remaining > 0:
                self._render_delay_remaining -= 1
            else:
                self._rendered_text = self._pending_rendered_text
                self._pending_rendered_text = None
        clip = self.clips[94]
        video = clip["video"]
        source = video["sourceparams"]
        visible = (
            live.clip_is_connected(clip)
            and bool(self._rendered_text.strip())
            and float(video["opacity"]["value"]) > 0.0
            and float(source["Opacity"]["value"]) > 0.0
            and int(str(source["Color"]["value"])[-2:], 16) > 0
        )
        return make_tag_png(
            self.tag_bounds if visible else None,
            noise_pixels=self.tag_noise_pixels if visible else None,
        )

    def parameter(self, identifier: int) -> dict[str, Any]:
        def visit(value: Any) -> dict[str, Any] | None:
            if isinstance(value, dict):
                if value.get("id") == identifier and "valuetype" in value:
                    return value
                for child in value.values():
                    found = visit(child)
                    if found is not None:
                        return found
            elif isinstance(value, list):
                for child in value:
                    found = visit(child)
                    if found is not None:
                        return found
            return None

        for clip in self.clips.values():
            found = visit(clip)
            if found is not None:
                return found
        raise AssertionError(f"unknown parameter ID {identifier}")

    def get(self, path: str) -> live.HttpResponse:
        self.calls.append(("GET", path, None))
        if path == "/api/v1/product":
            return json_response(
                {"name": "Avenue", "major": 7, "minor": 27, "micro": 1, "revision": 0}
            )
        if path == "/api/v1/composition":
            return json_response(self.composition)
        match = live.re.fullmatch(
            r"/api/v1/composition/layers/([1-9]\d*)/clips/1", path
        )
        if match:
            return json_response(self.clips[int(match.group(1))])
        match = live.re.fullmatch(r"/api/v1/parameter/by-id/([1-9]\d*)", path)
        if match:
            return json_response(self.parameter(int(match.group(1))))
        if path == "/api/v1/composition/monitors":
            return json_response([{"id": 77, "name": "Composition"}])
        if path == "/api/v1/composition/monitors/77/snapshot.png":
            return live.HttpResponse(
                200,
                "OK",
                (("Content-Type", "image/png"),),
                self.monitor_png(),
            )
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path: str, *, json_body: Any = None) -> live.HttpResponse:
        self.calls.append(("POST", path, json_body))
        raise AssertionError("test must not issue POST")

    def put(self, path: str, *, json_body: Any) -> live.HttpResponse:
        self.calls.append(("PUT", path, json_body))
        match = live.re.fullmatch(r"/api/v1/parameter/by-id/([1-9]\d*)", path)
        if not match:
            raise AssertionError(f"unexpected PUT {path}")
        if not isinstance(json_body, dict) or set(json_body) != {"value"}:
            raise AssertionError(f"unexpected PUT body {json_body!r}")
        parameter = self.parameter(int(match.group(1)))
        parameter["value"] = json_body["value"]
        if parameter is self.clips[94]["video"]["sourceparams"]["Text"]:
            self._pending_rendered_text = str(json_body["value"])
            self._render_delay_remaining = int(self.text_render_delay_polls)
        self.put_count += 1
        if self.fail_after_put_number == self.put_count:
            self.fail_after_put_number = None
            raise live.PipeTransportError(
                "injected ambiguous PUT failure",
                ambiguous=True,
            )
        return live.HttpResponse(204, "No Content", (), b"")

    def close(self) -> None:
        pass


class TransportTests(unittest.TestCase):
    def test_binary_chunked_response_preserves_headers_and_trailers(self) -> None:
        connection = FakeConnection(
            [
                chunked_response(
                    [b'{"name":', b'"Avenue"}'], [("Digest", "good")]
                )
            ]
        )
        client = live.PipeHttpClient("fake", connection_factory=Factory([connection]))
        response = client.get("/api/v1/product")
        self.assertEqual(response.json(), {"name": "Avenue"})
        self.assertEqual(response.header_values("X-Repeat"), ("one", "two"))
        self.assertEqual(response.trailers, (("Digest", "good"),))

    def test_png_body_remains_binary_and_204_needs_no_length(self) -> None:
        image = make_png()
        first = FakeConnection(
            [
                response_bytes(
                    image,
                    headers=[("Content-Type", "image/png")],
                ),
                b"HTTP/1.1 204 No Content\r\nConnection: keep-alive\r\n\r\n",
            ]
        )
        client = live.PipeHttpClient("fake", connection_factory=Factory([first]))
        response = client.get("/api/v1/composition/monitors/1/snapshot.png")
        self.assertEqual(response.body, image)
        self.assertEqual(live.validate_png(response.body).mode, "RGBA")
        result = client.post(
            "/api/v1/composition/grow-to",
            json_body={"layer_count": 149, "column_count": 1},
        )
        self.assertEqual(result.status, 204)

    def test_only_get_retries_transport_failure(self) -> None:
        failed_get = FakeConnection([])
        successful_get = FakeConnection(
            [
                response_bytes(
                    b'{"name":"Avenue"}',
                    headers=[("Content-Type", "application/json")],
                )
            ]
        )
        factory = Factory([failed_get, successful_get])
        client = live.PipeHttpClient("fake", connection_factory=factory)
        self.assertEqual(client.get("/api/v1/product").json()["name"], "Avenue")
        self.assertEqual(len(factory.created), 2)

        failed_post = FakeConnection([])
        unused = FakeConnection([response_bytes(status=204)])
        post_factory = Factory([failed_post, unused])
        post_client = live.PipeHttpClient("fake", connection_factory=post_factory)
        with self.assertRaises(live.PipeTransportError) as context:
            post_client.post(
                "/api/v1/composition/grow-to",
                json_body={"layer_count": 149},
            )
        self.assertTrue(context.exception.ambiguous)
        self.assertEqual(len(post_factory.created), 1)

    def test_http_error_is_not_retried(self) -> None:
        error = FakeConnection(
            [
                response_bytes(
                    b'{"error":"no"}',
                    status=500,
                    reason="Bad",
                    headers=[("Content-Type", "application/json")],
                )
            ]
        )
        unused = FakeConnection([response_bytes()])
        factory = Factory([error, unused])
        client = live.PipeHttpClient("fake", connection_factory=factory)
        with self.assertRaises(live.HttpStatusError):
            client.get("/api/v1/product")
        self.assertEqual(len(factory.created), 1)

    def test_missing_content_type_accepts_valid_json_only(self) -> None:
        response = live.HttpResponse(
            status=200,
            reason="OK",
            headers=(),
            body=b'{"value": 0.5}',
        )
        self.assertEqual(response.json(), {"value": 0.5})
        with self.assertRaises(live.RunnerError):
            dataclasses.replace(response, body=b"not-json").json()

    def test_request_deadline_and_full_rgba_png_decode_are_enforced(self) -> None:
        slow = SlowConnection(
            0.02,
            [
                response_bytes(
                    b'{"name":"Avenue"}',
                    headers=[("Content-Type", "application/json")],
                )
            ],
        )
        client = live.PipeHttpClient(
            "fake",
            connection_factory=Factory([slow, SlowConnection(0.02, [])]),
            request_timeout_seconds=0.001,
        )
        with self.assertRaises(live.PipeTransportError):
            client.get("/api/v1/product")

        with self.assertRaises(live.RunnerError):
            live.validate_png(make_structurally_valid_but_undecodable_png())
        with self.assertRaises(live.RunnerError):
            live.validate_png(make_png(color_type=2))
        self.assertEqual(
            live.validate_png(
                make_png(color_type=2),
                allowed_modes=("RGB", "RGBA"),
            ).mode,
            "RGB",
        )

    def test_route_policy_rejects_every_unlisted_route_before_io(self) -> None:
        factory = Factory([FakeConnection([response_bytes()])])
        client = live.PipeHttpClient("fake", connection_factory=factory)
        rejected = [
            ("POST", "/api/v1/composition/save"),
            ("POST", "/api/v1/composition/new"),
            ("POST", "/api/v1/composition/open"),
            ("POST", "/api/v1/composition/" + "dis" + "connect-all"),
            ("DELETE", "/api/v1/composition/layers/1"),
            ("PUT", "/api/v1/composition/layers/1"),
            ("GET", "/api/v1/composition?expanded=true"),
        ]
        for method, path in rejected:
            with self.subTest(method=method, path=path):
                with self.assertRaises(live.RouteRejected):
                    client.request(method, path)
        self.assertEqual(factory.created, [])


class ArtifactAndJournalTests(unittest.TestCase):
    def test_artifact_bundle_verifies_hash_size_build_and_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            docs = root / "react-kit" / "docs"
            docs.mkdir(parents=True)
            controls = docs / "controls.json"
            overlay = docs / "overlay.png"
            controls.write_text(
                json.dumps({"schema_version": 1, "build_id": "B1"}),
                encoding="utf-8",
            )
            overlay.write_bytes(make_png())
            manifest = docs / "build.json"
            artifact_map = {}
            for path in (controls, overlay):
                key = path.relative_to(root).as_posix()
                artifact_map[key] = {
                    "sha256": live.sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "build_id": "B1",
                        "status": "accepted",
                        "parent_build_id": "B0",
                        "measurement_sha256": "1" * 64,
                        "artifacts": artifact_map,
                    }
                ),
                encoding="utf-8",
            )
            bundle = live.ArtifactBundle.verify(manifest, root)
            self.assertEqual(bundle.build_id, "B1")
            bundle.require_path(controls)
            key, metadata = bundle.require(Path("controls.json"))
            self.assertEqual(key, controls.relative_to(root).as_posix())
            self.assertEqual(metadata["bytes"], controls.stat().st_size)
            controls.write_text("tampered", encoding="utf-8")
            with self.assertRaises(live.ArtifactError):
                bundle.require_path(controls)
            with self.assertRaises(live.ArtifactError):
                live.ArtifactBundle.verify(manifest, root)

    def test_artifact_status_lineage_and_live_controls_status_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = root / "child.json"
            child.write_text(
                json.dumps({"schema_version": 1, "build_id": "B0"}),
                encoding="utf-8",
            )
            manifest = root / "build.json"
            entry = {
                "sha256": live.sha256_file(child),
                "bytes": child.stat().st_size,
            }
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "build_id": "B0",
                        "status": "provisional",
                        "parent_build_id": "wrong",
                        "measurement_sha256": None,
                        "artifacts": {"child.json": entry},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(live.ArtifactError):
                live.ArtifactBundle.verify(manifest, root)

            value = json.loads(manifest.read_text(encoding="utf-8"))
            value.update(
                {
                    "status": "accepted",
                    "parent_build_id": "B0",
                    "measurement_sha256": "not-a-sha",
                }
            )
            manifest.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(live.ArtifactError):
                live.ArtifactBundle.verify(manifest, root)

    def test_lock_is_exclusive_and_journal_is_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock_path = root / "campaign.lock"
            journal = live.CampaignJournal(root / "campaign.jsonl")
            with live.CampaignLock(lock_path):
                self.assertTrue(lock_path.exists())
                with self.assertRaises(live.RunnerError):
                    with live.CampaignLock(lock_path):
                        pass
                journal.append({"kind": "one"})
                journal.append({"kind": "two"})
            self.assertFalse(lock_path.exists())
            self.assertEqual(
                [record["kind"] for record in journal.records()], ["one", "two"]
            )

    def test_process_hygiene_requires_one_avenue_and_keeps_mcp_report_only(self) -> None:
        result = live.validate_process_hygiene(valid_processes(mcp_count=2))
        self.assertEqual(result["mcp_pids_report_only"], [300, 301])
        with self.assertRaises(live.RunnerError):
            live.validate_process_hygiene(valid_processes(avenue_count=0))
        with self.assertRaises(live.RunnerError):
            live.validate_process_hygiene(valid_processes(avenue_count=2))
        parser = live.build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(
                    ["preflight", "--stage", "offline", "--skip-process-check"]
                )


class SnapshotAndDryRunTests(unittest.TestCase):
    def make_runner(
        self, root: Path, *, connected_layers: set[int] | None = None
    ) -> tuple[live.LiveRunner, FakeApiClient, list[dict]]:
        composition, clips = make_composition(connected_layers=connected_layers)
        manifest = [
            {
                "layer": layer,
                "layer_name": f"Layer {layer}",
                "midi_label": f"{'CC' if layer in live.CC_LAYERS else 'N'}{layer}/C1",
                "midi_type": "cc" if layer in live.CC_LAYERS else "note",
            }
            for layer in range(1, 149)
        ]
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        api = FakeApiClient(composition, clips)
        runner = live.LiveRunner(
            bridge=api,
            native=api,
            manifest_path=manifest_path,
            journal_path=root / "journal.jsonl",
            lock_path=root / "campaign.lock",
            process_provider=types.SimpleNamespace(
                list_processes=lambda: valid_processes()
            ),
        )
        return runner, api, manifest

    def prepare_calibration(
        self,
        root: Path,
        *,
        connected: bool = True,
        render_delay_polls: int = 0,
        tag_bounds: tuple[int, int, int, int] | None = None,
        noise_pixels: list[tuple[int, int]] | None = None,
    ) -> tuple[
        live.LiveRunner,
        FakeApiClient,
        Path,
        Path,
        live.ArtifactBundle,
        live.TypedLiveControls,
    ]:
        runner, api, manifest = self.make_runner(
            root,
            connected_layers={94} if connected else set(),
        )
        active_preset = write_active_preset(root)
        snapshot_path = root / "pilot-baseline.json"
        runner.snapshot_controls(
            out=snapshot_path,
            restart_stage="restart-a",
            build_id="B0",
            active_preset_path=active_preset,
            active_preset_sha256=live.sha256_file(active_preset),
            dry_run=False,
        )
        controls, _, build_manifest = write_live_bundle(
            root,
            manifest,
            build_id="B0",
            status="provisional",
        )
        bundle = live.ArtifactBundle.verify(build_manifest, root)
        typed_controls = live.TypedLiveControls.verify(controls, bundle)
        api.calls.clear()
        api.text_render_delay_polls = render_delay_polls
        if tag_bounds is not None:
            api.tag_bounds = tag_bounds
        api.tag_noise_pixels = list(noise_pixels or [])
        return (
            runner,
            api,
            active_preset,
            snapshot_path,
            bundle,
            typed_controls,
        )

    def begin_interrupted_calibration(
        self,
        *,
        runner: live.LiveRunner,
        active_preset: Path,
        snapshot_path: Path,
        bundle: live.ArtifactBundle,
        out: Path,
    ) -> tuple[
        str,
        dict[str, dict[str, Any]],
        dict[str, dict[str, Any]],
    ]:
        snapshot, snapshot_hash = runner._load_snapshot(snapshot_path)
        composition = runner.composition()
        fingerprint = live.composition_fingerprint(composition)
        expected_clip = snapshot["clips"][93]
        clip = runner.clip(94)
        runner._require_calibration_clip_identity(clip, expected_clip)
        parameters = runner._calibration_source_parameters(clip)
        original_states = {
            name: runner._read_parameter_state(
                int(parameters[name]["id"]),
                valuetype=valuetype,
                label=f"test interrupted calibration {name}",
            )
            for name, valuetype in live.CALIBRATION_SOURCE_FIELD_TYPES.items()
        }
        parent_hashes = live.measurement_parent_artifact_hashes(bundle)
        transaction_id = runner.begin_calibration_recovery(
            layer=94,
            out=out,
            original_states=original_states,
            expected_clip=expected_clip,
            current_fingerprint=fingerprint,
            active_preset=active_preset,
            active_preset_sha256=live.sha256_file(active_preset),
            snapshot_path=snapshot_path,
            snapshot_sha256=snapshot_hash,
            snapshot=snapshot,
            bundle=bundle,
            parent_manifest_sha256=live.sha256_file(bundle.manifest_path),
            parent_artifact_hashes=parent_hashes,
        )
        return transaction_id, parameters, original_states

    @staticmethod
    def restarted_runner(
        runner: live.LiveRunner,
        api: FakeApiClient,
    ) -> live.LiveRunner:
        return live.LiveRunner(
            bridge=api,
            native=api,
            manifest_path=runner.manifest_path,
            journal_path=runner.journal.path,
            lock_path=runner.lock_path,
            calibration_recovery_path=runner.calibration_recovery.path,
            process_provider=types.SimpleNamespace(
                list_processes=lambda: valid_processes()
            ),
        )

    def test_snapshot_dry_run_publishes_nothing_and_never_writes_api(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, api, _ = self.make_runner(root)
            out = root / "snapshot.json"
            active_preset = write_active_preset(root)
            result = runner.snapshot_controls(
                out=out,
                restart_stage="restart-a",
                build_id="B0",
                active_preset_path=active_preset,
                active_preset_sha256=live.sha256_file(active_preset),
                dry_run=True,
            )
            self.assertIsNone(result["artifact_id"])
            self.assertFalse(out.exists())
            self.assertFalse(runner.journal.path.exists())
            self.assertTrue(api.calls)
            self.assertEqual({method for method, _, _ in api.calls}, {"GET"})

    def test_explicit_gate_binds_snapshot_fingerprint_and_exact_layers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, api, _ = self.make_runner(root, connected_layers={1})
            snapshot_path = root / "baseline.json"
            active_preset = write_active_preset(root)
            api.clips[1]["connected"] = param(
                "Disconnected", "ParamChoice", 30_001
            )
            runner.snapshot_controls(
                out=snapshot_path,
                restart_stage="restart-a",
                build_id="B0",
                active_preset_path=active_preset,
                active_preset_sha256=live.sha256_file(active_preset),
                dry_run=False,
            )
            api.clips[1]["connected"] = param(
                "Connected", "ParamChoice", 30_001
            )
            with self.assertRaises(live.ManualActionRequired) as context:
                runner.restore_snapshot_gate(
                    snapshot_path=snapshot_path,
                    supplied_gate=None,
                    active_preset=active_preset,
                    dry_run=False,
                )
            gate = context.exception.gate_id
            self.assertEqual(context.exception.layers, (1,))
            self.assertEqual(
                [record["kind"] for record in runner.journal.records()],
                ["campaign_snapshot_published", "manual_gate_created"],
            )

            api.clips[1]["connected"] = param(
                "Disconnected", "ParamChoice", 30_001
            )
            with self.assertRaises(live.RunnerError):
                runner.manual_eject_check(
                    snapshot_path=snapshot_path,
                    gate_id=gate,
                    layers=[2],
                    evidence_out=root / "wrong.png",
                    active_preset=active_preset,
                    dry_run=False,
                )
            evidence = root / "gate.png"
            verified = runner.manual_eject_check(
                snapshot_path=snapshot_path,
                gate_id=gate,
                layers=[1],
                evidence_out=evidence,
                active_preset=active_preset,
                dry_run=False,
            )
            self.assertEqual(verified["layers"], [1])
            self.assertTrue(evidence.exists())
            self.assertTrue(evidence.with_suffix(".png.json").exists())
            with self.assertRaises(live.RunnerError):
                runner.restore_snapshot_gate(
                    snapshot_path=snapshot_path,
                    supplied_gate=None,
                    active_preset=active_preset,
                    dry_run=True,
                )
            plan = runner.restore_snapshot_gate(
                snapshot_path=snapshot_path,
                supplied_gate=gate,
                active_preset=active_preset,
                dry_run=True,
            )
            self.assertEqual(plan["manual_eject_layers"], [])
            self.assertEqual({method for method, _, _ in api.calls}, {"GET"})
            evidence.write_bytes(make_png(width=1, height=1))
            with self.assertRaises(live.RunnerError):
                runner.restore_snapshot_gate(
                    snapshot_path=snapshot_path,
                    supplied_gate=gate,
                    active_preset=active_preset,
                    dry_run=True,
                )

    def test_monitor_dry_run_validates_but_does_not_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, api, _ = self.make_runner(root)
            out = root / "frame.png"
            result = runner.capture_monitor(
                monitor_name="Composition", out=out, dry_run=True
            )
            self.assertEqual((result["width"], result["height"]), (1920, 1080))
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix(".png.json").exists())
            self.assertEqual({method for method, _, _ in api.calls}, {"GET"})

    def test_149_snapshot_requires_exact_overlay_claim_and_build(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, api, _ = self.make_runner(root)
            active_preset = write_active_preset(root)
            clip = make_clip(149, name="OVERLAY/C1")
            api.clips[149] = clip
            api.composition["layers"].append(
                {"id": 10_149, "name": param("Overlay"), "clips": [clip]}
            )
            kwargs = {
                "out": root / "snapshot.json",
                "restart_stage": "visual-controls",
                "build_id": "B1",
                "active_preset_path": active_preset,
                "active_preset_sha256": live.sha256_file(active_preset),
                "dry_run": True,
            }
            with self.assertRaises(live.RunnerError):
                runner.snapshot_controls(**kwargs)
            fingerprint = live.composition_fingerprint(api.composition)
            runner.journal.append(
                {
                    "kind": "overlay_claimed",
                    "build_id": "wrong-build",
                    "composition_fingerprint": fingerprint["sha256"],
                    "expected_layer_count": 149,
                    "original_layer_ids": fingerprint["layer_ids"][:148],
                    "overlay_layer_id": fingerprint["layer_ids"][148],
                }
            )
            with self.assertRaises(live.RunnerError):
                runner.snapshot_controls(**kwargs)
            runner.journal.append(
                {
                    "kind": "overlay_claimed",
                    "build_id": "B1",
                    "composition_fingerprint": fingerprint["sha256"],
                    "expected_layer_count": 149,
                    "original_layer_ids": fingerprint["layer_ids"][:148],
                    "overlay_layer_id": fingerprint["layer_ids"][148],
                }
            )
            result = runner.snapshot_controls(**kwargs)
            self.assertEqual(result["expected_layer_count"], 149)

    def test_snapshot_schema_rejects_duplicate_layers_and_string_booleans(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, _, _ = self.make_runner(root)
            active_preset = write_active_preset(root)
            snapshot = runner.snapshot_controls(
                out=root / "baseline.json",
                restart_stage="restart-a",
                build_id="B0",
                active_preset_path=active_preset,
                active_preset_sha256=live.sha256_file(active_preset),
                dry_run=False,
            )
            duplicate = json.loads(json.dumps(snapshot))
            duplicate["clips"][1] = duplicate["clips"][0]
            with self.assertRaises(live.RunnerError):
                live.validate_runtime_snapshot(duplicate, root / "duplicate.json")
            wrong_boolean = json.loads(json.dumps(snapshot))
            wrong_boolean["clips"][0]["connected"] = "false"
            with self.assertRaises(live.RunnerError):
                live.validate_runtime_snapshot(wrong_boolean, root / "boolean.json")

    def test_calibration_dry_run_uses_provisional_build_at_148(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, _, manifest = self.make_runner(root)
            active_preset = write_active_preset(root)
            snapshot_path = root / "pilot-baseline.json"
            runner.snapshot_controls(
                out=snapshot_path,
                restart_stage="restart-a",
                build_id="B0",
                active_preset_path=active_preset,
                active_preset_sha256=live.sha256_file(active_preset),
                dry_run=False,
            )
            controls, overlay, build_manifest = write_live_bundle(
                root, manifest, build_id="B0", status="provisional"
            )
            args = types.SimpleNamespace(
                command="calibrate-moving-tag",
                dry_run=True,
                build_manifest=build_manifest,
                repo_root=root,
                live_controls=controls,
                overlay=overlay,
                layers=[],
                layer=94,
                snapshot=snapshot_path,
                out=root / "measurement.json",
                active_preset=active_preset,
            )
            plan = live._disabled_mutation_plan(args, runner)
            self.assertEqual(plan["preflight"]["expected_layer_count"], 148)
            self.assertEqual(plan["live_controls_status"], "provisional")
            self.assertEqual(plan["layers"], [94])
            self.assertEqual(plan["request_count"], 7)
            self.assertEqual(
                [request["parameter"] for request in plan["requests"]],
                [
                    "Text",
                    "Text",
                    "Font",
                    "Size",
                    "Position X",
                    "Position Y",
                    "Spacing Y",
                ],
            )
            self.assertEqual(
                plan["requests"][0]["phase"],
                "blank-text-off-baseline",
            )
            self.assertFalse(
                plan["capture_semantics"]["endpoint_sweep_verified"]
            )

    def test_calibration_executes_b0_source_wave_measures_and_restores(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                typed_controls,
            ) = self.prepare_calibration(root)
            source = api.clips[94]["video"]["sourceparams"]
            original = {
                name: json.loads(json.dumps(source[name]))
                for name in live.CALIBRATION_SOURCE_FIELD_TYPES
            }
            out = root / "APC40_visual_qa_tag_measurement.json"

            result = runner.calibrate_moving_tag(
                layer=94,
                snapshot_path=snapshot_path,
                active_preset=active_preset,
                bundle=bundle,
                live_controls=typed_controls,
                out=out,
            )

            self.assertTrue(out.is_file())
            measurement = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(measurement["build_id"], "B0")
            self.assertEqual(
                measurement["calibration_transaction_id"],
                result["calibration_transaction_id"],
            )
            self.assertFalse(runner.calibration_recovery.path.exists())
            self.assertEqual(measurement["selected_avenue_size"], 2.25)
            self.assertEqual(
                measurement["accepted_live_tag_metrics"],
                {
                    "vertical": {"ink_box_px": [70, 30]},
                    "horizontal": {"ink_box_px": [70, 30]},
                },
            )
            self.assertEqual(
                measurement["measurement_parent_artifact_hashes"],
                {
                    key: {
                        "sha256": metadata["sha256"],
                        "bytes": metadata["bytes"],
                    }
                    for key, metadata in sorted(bundle.artifacts.items())
                },
            )
            self.assertEqual(result["apply_count"], 7)
            self.assertEqual(result["restore_count"], 7)
            self.assertFalse(result["endpoint_sweep_verified"])
            self.assertFalse(
                measurement["capture_semantics"]["endpoint_sweep_verified"]
            )
            self.assertEqual(
                result["restore_order"],
                [
                    "Spacing Y",
                    "Position Y",
                    "Position X",
                    "Size",
                    "Font",
                    "Text",
                    "Text",
                ],
            )
            for state in live.CALIBRATION_CAPTURE_STATES:
                image = live.calibration_capture_path(out, state)
                self.assertTrue(image.is_file())
                self.assertTrue(image.with_suffix(".png.json").is_file())
            put_calls = [
                (path, body)
                for method, path, body in api.calls
                if method == "PUT"
            ]
            self.assertEqual(len(put_calls), 14)
            apply_ids = [
                source[name]["id"] for name in live.CALIBRATION_SOURCE_FIELD_TYPES
            ]
            restore_ids = list(reversed(apply_ids))
            self.assertEqual(
                [int(path.rsplit("/", 1)[1]) for path, _ in put_calls],
                [source["Text"]["id"]]
                + apply_ids
                + restore_ids
                + [source["Text"]["id"]],
            )
            for name, state in original.items():
                self.assertEqual(source[name], state)
            self.assertTrue(
                all(
                    path.startswith("/api/v1/parameter/by-id/")
                    for path, _ in put_calls
                )
            )
            self.assertIn(
                "calibration_recovery_committed",
                [record["kind"] for record in runner.journal.records()],
            )

    def test_calibration_rejects_disconnected_layer_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                typed_controls,
            ) = self.prepare_calibration(root, connected=False)
            out = root / "APC40_visual_qa_tag_measurement.json"

            with self.assertRaisesRegex(
                live.RunnerError,
                "must be connected",
            ):
                runner.calibrate_moving_tag(
                    layer=94,
                    snapshot_path=snapshot_path,
                    active_preset=active_preset,
                    bundle=bundle,
                    live_controls=typed_controls,
                    out=out,
                )

            self.assertFalse(out.exists())
            self.assertFalse(any(method == "PUT" for method, _, _ in api.calls))
            self.assertEqual(api.monitor_snapshot_count, 0)

    def test_calibration_waits_for_two_stable_frames_after_delayed_render(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                typed_controls,
            ) = self.prepare_calibration(root, render_delay_polls=2)
            out = root / "APC40_visual_qa_tag_measurement.json"

            runner.calibrate_moving_tag(
                layer=94,
                snapshot_path=snapshot_path,
                active_preset=active_preset,
                bundle=bundle,
                live_controls=typed_controls,
                out=out,
            )

            measurement = json.loads(out.read_text(encoding="utf-8"))
            blank_settle = measurement["captures"]["off"]["render_settle"]
            final_settle = measurement["captures"]["minimum"]["render_settle"]
            self.assertEqual(blank_settle["poll_count"], 4)
            self.assertEqual(final_settle["poll_count"], 4)
            self.assertEqual(blank_settle["stable_frames_required"], 2)
            self.assertEqual(final_settle["stable_frames_required"], 2)
            self.assertTrue(
                all(
                    record["rejected_as_previous_render"]
                    for record in blank_settle["polls"][:2]
                )
            )
            self.assertTrue(
                all(
                    record["rejected_as_previous_render"]
                    for record in final_settle["polls"][:2]
                )
            )
            self.assertEqual(api.monitor_snapshot_count, 11)

    def test_calibration_rejects_roi_clipping_and_restores_without_outputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                typed_controls,
            ) = self.prepare_calibration(
                root,
                tag_bounds=(111, 880, 181, 910),
            )
            out = root / "APC40_visual_qa_tag_measurement.json"

            with self.assertRaisesRegex(
                live.RunnerError,
                "touches the witness ROI edge",
            ):
                runner.calibrate_moving_tag(
                    layer=94,
                    snapshot_path=snapshot_path,
                    active_preset=active_preset,
                    bundle=bundle,
                    live_controls=typed_controls,
                    out=out,
                )

            self.assertFalse(out.exists())
            self.assertEqual(
                sum(method == "PUT" for method, _, _ in api.calls),
                14,
            )
            for state in live.CALIBRATION_CAPTURE_STATES:
                image = live.calibration_capture_path(out, state)
                self.assertFalse(image.exists())
                self.assertFalse(image.with_suffix(".png.json").exists())
            self.assertEqual(list(root.glob(".*.captures.*")), [])

    def test_measurement_rejects_noise_only_and_unstable_centroid_masks(
        self,
    ) -> None:
        witness = [143, 783, 239, 1013]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            off = root / "off.png"
            off.write_bytes(make_tag_png(None))

            noise = [(150, 880), (161, 880), (150, 887), (161, 887)]
            noise_paths: dict[str, Path] = {}
            for state in ("minimum", "midpoint", "maximum"):
                path = root / f"noise-{state}.png"
                path.write_bytes(make_tag_png(None, noise_pixels=noise))
                noise_paths[state] = path
            with self.assertRaisesRegex(
                live.RunnerError,
                "changed only 4 pixels",
            ):
                live.measure_calibration_ink(
                    off_path=off,
                    state_paths=noise_paths,
                    witness_box=witness,
                )

            drift_bounds = (
                (150, 880, 220, 910),
                (152, 880, 222, 910),
                (150, 880, 220, 910),
            )
            drift_paths: dict[str, Path] = {}
            for state, bounds in zip(
                ("minimum", "midpoint", "maximum"),
                drift_bounds,
                strict=True,
            ):
                path = root / f"drift-{state}.png"
                path.write_bytes(make_tag_png(bounds))
                drift_paths[state] = path
            with self.assertRaisesRegex(
                live.RunnerError,
                "mask centroids drift",
            ):
                live.measure_calibration_ink(
                    off_path=off,
                    state_paths=drift_paths,
                    witness_box=witness,
                )

    def test_interrupted_calibration_fails_closed_then_recovers_exact_states(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                _,
            ) = self.prepare_calibration(root)
            out = root / "APC40_visual_qa_tag_measurement.json"
            transaction_id, parameters, original_states = (
                self.begin_interrupted_calibration(
                    runner=runner,
                    active_preset=active_preset,
                    snapshot_path=snapshot_path,
                    bundle=bundle,
                    out=out,
                )
            )

            runner._calibration_transaction_put(
                transaction_id,
                parameters["Text"],
                value="",
                expected_state=None,
                label="test blank text before simulated process death",
                phase="blank-baseline",
                parameter_name="Text",
            )
            size_intent = runner.calibration_recovery.append(
                transaction_id,
                {
                    "kind": "parameter_write_intent",
                    "phase": "apply",
                    "parameter": "Size",
                    "parameter_id": parameters["Size"]["id"],
                    "valuetype": "ParamRange",
                    "value": 2.25,
                },
            )
            api.put(
                f"/api/v1/parameter/by-id/{parameters['Size']['id']}",
                json_body={"value": 2.25},
            )
            self.assertIsInstance(size_intent["sequence"], int)
            self.assertTrue(runner.calibration_recovery.path.is_file())

            restarted = self.restarted_runner(runner, api)
            with self.assertRaisesRegex(
                live.RunnerError,
                "requires `recover-calibration`",
            ):
                restarted.preflight(
                    stage="restart-a",
                    expected_layer_count=148,
                    active_preset=active_preset,
                )

            put_count_before_preview = api.put_count
            preview = restarted.recover_calibration(
                active_preset=active_preset,
                dry_run=True,
            )
            self.assertTrue(preview["dry_run"])
            self.assertEqual(preview["transaction_id"], transaction_id)
            self.assertEqual(
                preview["would_restore_parameters"],
                ["Size", "Text"],
            )
            self.assertEqual(preview["write_count"], 2)
            self.assertEqual(api.put_count, put_count_before_preview)
            self.assertTrue(restarted.calibration_recovery.path.is_file())

            result = restarted.recover_calibration(
                active_preset=active_preset,
            )
            self.assertEqual(result["transaction_id"], transaction_id)
            self.assertEqual(result["restored_parameters"], ["Size", "Text"])
            self.assertEqual(result["restore_count"], 2)
            self.assertFalse(restarted.calibration_recovery.path.exists())
            for name, original in original_states.items():
                self.assertTrue(
                    live.parameter_states_equal(
                        live.parameter_state(api.parameter(parameters[name]["id"])),
                        original,
                    ),
                    name,
                )
            restarted.preflight(
                stage="restart-a",
                expected_layer_count=148,
                active_preset=active_preset,
            )
            journal_kinds = [
                record["kind"] for record in restarted.journal.records()
            ]
            self.assertIn("calibration_recovery_started", journal_kinds)
            self.assertIn("calibration_recovery_progress", journal_kinds)
            self.assertIn("calibration_recovery_committed", journal_kinds)

    def test_interrupted_calibration_recovery_rejects_identity_drift_without_put(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                _,
            ) = self.prepare_calibration(root)
            out = root / "APC40_visual_qa_tag_measurement.json"
            transaction_id, parameters, _ = self.begin_interrupted_calibration(
                runner=runner,
                active_preset=active_preset,
                snapshot_path=snapshot_path,
                bundle=bundle,
                out=out,
            )
            runner._calibration_transaction_put(
                transaction_id,
                parameters["Text"],
                value="",
                expected_state=None,
                label="test mutation before identity drift",
                phase="blank-baseline",
                parameter_name="Text",
            )
            put_count = api.put_count
            api.composition["layers"][0]["id"] += 1

            restarted = self.restarted_runner(runner, api)
            with self.assertRaisesRegex(
                live.RunnerError,
                "composition fingerprint does not match",
            ):
                restarted.recover_calibration(
                    active_preset=active_preset,
                )
            self.assertEqual(api.put_count, put_count)
            self.assertTrue(restarted.calibration_recovery.path.is_file())

    def test_calibration_ambiguous_partial_wave_restores_reverse_and_publishes_nothing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                typed_controls,
            ) = self.prepare_calibration(root)
            source = api.clips[94]["video"]["sourceparams"]
            original = {
                name: json.loads(json.dumps(source[name]))
                for name in live.CALIBRATION_SOURCE_FIELD_TYPES
            }
            api.fail_after_put_number = 4
            out = root / "APC40_visual_qa_tag_measurement.json"

            with self.assertRaisesRegex(
                live.PipeTransportError,
                "injected ambiguous PUT failure",
            ):
                runner.calibrate_moving_tag(
                    layer=94,
                    snapshot_path=snapshot_path,
                    active_preset=active_preset,
                    bundle=bundle,
                    live_controls=typed_controls,
                    out=out,
            )

            self.assertFalse(out.exists())
            self.assertFalse(runner.calibration_recovery.path.exists())
            for state in live.CALIBRATION_CAPTURE_STATES:
                image = live.calibration_capture_path(out, state)
                self.assertFalse(image.exists())
                self.assertFalse(image.with_suffix(".png.json").exists())
            put_paths = [
                path for method, path, _ in api.calls if method == "PUT"
            ]
            apply_ids = [
                source[name]["id"]
                for name in ("Text", "Font", "Size")
            ]
            self.assertEqual(
                [int(path.rsplit("/", 1)[1]) for path in put_paths],
                [source["Text"]["id"]]
                + apply_ids
                + list(reversed(apply_ids))
                + [source["Text"]["id"]],
            )
            for name, state in original.items():
                self.assertEqual(source[name], state)

    def test_calibration_rejects_composition_drift_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (
                runner,
                api,
                active_preset,
                snapshot_path,
                bundle,
                typed_controls,
            ) = self.prepare_calibration(root)
            api.composition["layers"][0]["id"] += 1
            out = root / "APC40_visual_qa_tag_measurement.json"

            with self.assertRaisesRegex(
                live.RunnerError,
                "fingerprint does not match",
            ):
                runner.calibrate_moving_tag(
                    layer=94,
                    snapshot_path=snapshot_path,
                    active_preset=active_preset,
                    bundle=bundle,
                    live_controls=typed_controls,
                    out=out,
                )
            self.assertFalse(out.exists())
            self.assertFalse(any(method == "PUT" for method, _, _ in api.calls))

    def test_disabled_live_command_dry_run_is_read_only_request_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner, api, manifest = self.make_runner(root)
            # The generated manifest and composition are already exact.
            controls = root / "controls.json"
            overlay = root / "overlay.png"
            controls.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "build_id": "B1",
                        "status": "accepted",
                        "artifact_role": "typed_live_controls",
                        "wave_size": 24,
                        "glyph_font": {
                            "offline_path": "font.ttf",
                            "live_family": "Segoe UI Symbol",
                            "offline_size_px": 18,
                            "live_size_value": 18,
                            "measurement_status": "accepted",
                        },
                        "layers": {
                            str(layer): {
                                "layer": layer,
                                "raw_key": str(1_000_000 + layer),
                                "midi_label": manifest[layer - 1]["midi_label"],
                                "category": "test",
                                "witness": {
                                    "kind": "test",
                                    "text": "x",
                                    "color": "#ffffffff",
                                },
                                "fields": [
                                    {
                                        "target": "text_animator_source",
                                        "parameter": "Text",
                                        "valuetype": "ParamText",
                                        "desired": f"L{layer}",
                                        "purpose": "test",
                                    }
                                ],
                            }
                            for layer in range(1, 149)
                        },
                    }
                ),
                encoding="utf-8",
            )
            overlay.write_bytes(make_png())
            artifacts = {}
            for path in (controls, overlay):
                artifacts[path.relative_to(root).as_posix()] = {
                    "sha256": live.sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            build_manifest = root / "build.json"
            build_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "build_id": "B1",
                        "status": "accepted",
                        "parent_build_id": "B0",
                        "measurement_sha256": "2" * 64,
                        "artifacts": artifacts,
                    }
                ),
                encoding="utf-8",
            )
            args = types.SimpleNamespace(
                command="append-overlay",
                dry_run=True,
                build_manifest=build_manifest,
                repo_root=root,
                live_controls=controls,
                overlay=overlay,
                layers=[],
                active_preset=write_active_preset(root),
            )
            plan = live._disabled_mutation_plan(args, runner)
            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["request_count"], 5)
            self.assertEqual(
                [request["method"] for request in plan["requests"]],
                ["POST", "POST", "PUT", "PUT", "POST"],
            )
            self.assertEqual({method for method, _, _ in api.calls}, {"GET"})
            self.assertFalse(runner.journal.path.exists())
            self.assertFalse(runner.lock_path.exists())

    def test_source_has_no_midi_watcher_or_broad_inverse_route(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8").casefold()
        self.assertNotIn("rt" + "midi", source)
        self.assertNotIn("dis" + "connect-all", source)
        mapped = [
            (layer, target, parameter)
            for layer in sorted(live.CC_LAYERS)
            for target, parameter in live.mapped_cc_fields(layer)
        ]
        self.assertEqual(len(mapped), 55)
        self.assertEqual(
            sum(parameter == "Position Y" for _, _, parameter in mapped), 9
        )
        self.assertEqual(
            sum(parameter == "Position X" for _, _, parameter in mapped), 1
        )
        self.assertEqual(
            sum(parameter == "Rotation Z" for _, _, parameter in mapped), 18
        )


if __name__ == "__main__":
    unittest.main()
