"""Safety-focused live QA runner for the APC40 MkII Avenue composition.

This module deliberately has no MIDI input support.  It offers a small HTTP
surface over a configurable Windows named pipe, validates renderer artifacts,
captures restorable state, and enforces explicit operator gates where Avenue
has no narrow REST inverse.

The high-level mutation commands remain fail-closed until their exact live
schemas have passed the staged pilot.  ``--dry-run`` still performs read-only
discovery and emits the request plan without publishing artifacts.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import io
import json
import math
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import uuid
import zlib
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Protocol, Sequence


SCRIPT_PATH = Path(__file__).resolve()
REACT_KIT_ROOT = SCRIPT_PATH.parents[1]
DEFAULT_MANIFEST = REACT_KIT_ROOT / "docs" / "APC40_visual_qa_manifest.json"
DEFAULT_LIVE_CONTROLS = (
    REACT_KIT_ROOT / "docs" / "APC40_visual_qa_live_controls.json"
)
DEFAULT_BUILD_MANIFEST = (
    REACT_KIT_ROOT / "docs" / "APC40_visual_qa_build_manifest.json"
)
DEFAULT_OVERLAY = REACT_KIT_ROOT / "docs" / "APC40_visual_qa_live_overlay.png"
DEFAULT_CAMPAIGN_DIR = (
    REACT_KIT_ROOT / "docs" / "2026-07-18-apc40-animated-visual-qa" / "runtime"
)
DEFAULT_JOURNAL = DEFAULT_CAMPAIGN_DIR / "apc40_visual_qa_live.jsonl"
DEFAULT_LOCK = DEFAULT_CAMPAIGN_DIR / "apc40_visual_qa_live.lock"
DEFAULT_CALIBRATION_RECOVERY = (
    DEFAULT_CAMPAIGN_DIR / "apc40_visual_qa_calibration_recovery.json"
)
DEFAULT_COMPOSITION_NAME = "APC40_Visual_QA_148"
NATIVE_PIPE = r"\\.\pipe\Resolume Avenue\rest-api"
BRIDGE_PIPE = r"\\.\pipe\Resolume Arena\rest-api"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_WRITES_PER_WAVE = 24
DEFAULT_CONNECT_TIMEOUT_SECONDS = 5.0
DEFAULT_READ_TIMEOUT_SECONDS = 5.0
DEFAULT_REQUEST_TIMEOUT_SECONDS = 15.0
CALIBRATION_SOURCE_FIELD_TYPES: Mapping[str, str] = {
    "Text": "ParamText",
    "Font": "ParamChoice",
    "Size": "ParamRange",
    "Position X": "ParamRange",
    "Position Y": "ParamRange",
    "Spacing Y": "ParamRange",
}
CALIBRATION_CAPTURE_STATES = ("off", "minimum", "midpoint", "maximum")
LIVE_SIZE_RANGE = (0.5, 4.0)
MOVING_TAG_TARGET_PX = (92, 42)
MIN_MOVING_TAG_INK_PX = (12, 8)
MIN_MOVING_TAG_CHANGED_PIXELS = 64
MAX_MOVING_TAG_CENTROID_DRIFT_PX = 1.0
CALIBRATION_ROI_PADDING_PX = 32
CALIBRATION_SETTLE_MAX_POLLS = 8
CALIBRATION_SETTLE_STABLE_FRAMES = 2
CALIBRATION_SETTLE_POLL_INTERVAL_SECONDS = 0.02
CC_LAYERS = frozenset((*range(94, 118), 143, 144, 145, 148))
STAGES = frozenset(
    {
        "offline",
        "install-pilot",
        "restart-a",
        "restart-a1r",
        "rollback-prepilot",
        "install-full",
        "restart-a2",
        "rollback-full-to-pilot",
        "append-overlay",
        "visual-controls",
        "authorized-save",
        "restart-b",
    }
)


JsonObject = dict[str, Any]


def mapped_cc_fields(layer: int) -> tuple[tuple[str, str], ...]:
    fields: list[tuple[str, str]] = []
    if layer != 148:
        fields.append(("clip_opacity", "opacity"))
    if 94 <= layer <= 101 or layer == 143:
        fields.append(("permanent_transform", "Position Y"))
    elif layer == 144:
        fields.append(("permanent_transform", "Position X"))
    else:
        fields.append(("permanent_transform", "Rotation Z"))
    return tuple(fields)


class RunnerError(RuntimeError):
    """Base class for a fail-closed runner error."""


class RouteRejected(RunnerError):
    """Raised before any I/O when a route is outside the narrow policy."""


class PipeTransportError(RunnerError):
    """A named-pipe failure with explicit request-delivery ambiguity."""

    def __init__(self, message: str, *, ambiguous: bool) -> None:
        super().__init__(message)
        self.ambiguous = bool(ambiguous)


class HttpStatusError(RunnerError):
    """An HTTP error response.  These are never retried."""

    def __init__(self, method: str, path: str, response: "HttpResponse") -> None:
        preview = response.body[:300].decode("utf-8", errors="replace")
        super().__init__(
            f"{method} {path} returned HTTP {response.status}: {preview}"
        )
        self.method = method
        self.path = path
        self.response = response


class ArtifactError(RunnerError):
    """Renderer artifact set is missing, stale, or inconsistent."""


class ManualActionRequired(RunnerError):
    """A targeted UI eject is needed before exact restoration can continue."""

    def __init__(
        self,
        *,
        gate_id: str,
        snapshot: Path,
        layers: Sequence[int],
    ) -> None:
        self.gate_id = gate_id
        self.snapshot = snapshot
        self.layers = tuple(sorted(int(layer) for layer in layers))
        super().__init__(
            "targeted Avenue UI eject required: "
            f"gate={gate_id}, snapshot={snapshot}, layers="
            + ",".join(str(layer) for layer in self.layers)
        )


class LiveMutationNotValidated(RunnerError):
    """A live write path is intentionally disabled pending its staged pilot."""


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        .encode("utf-8")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None


def json_from_bytes(data: bytes, path: Path) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"cannot read valid JSON from {path}: {exc}") from exc


def load_json(path: Path) -> Any:
    try:
        return json_from_bytes(path.read_bytes(), path)
    except OSError as exc:
        raise ArtifactError(f"cannot read valid JSON from {path}: {exc}") from exc


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write, fsync, validate visibility, and atomically replace one artifact."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, canonical_json(value) + b"\n")


@dataclasses.dataclass(frozen=True)
class HttpResponse:
    status: int
    reason: str
    headers: tuple[tuple[str, str], ...]
    body: bytes
    trailers: tuple[tuple[str, str], ...] = ()

    def header_values(self, name: str) -> tuple[str, ...]:
        wanted = name.casefold()
        return tuple(value for key, value in self.headers if key.casefold() == wanted)

    def header(self, name: str) -> str | None:
        values = self.header_values(name)
        return values[-1] if values else None

    def json(self) -> Any:
        content_type = (self.header("content-type") or "").casefold()
        if content_type and "json" not in content_type and self.body:
            raise RunnerError(f"response is not JSON (content-type={content_type!r})")
        try:
            return json.loads(self.body.decode("utf-8")) if self.body else None
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RunnerError(f"invalid JSON response: {exc}") from exc


class ByteConnection(Protocol):
    def write(self, data: bytes) -> int:
        ...

    def read(self, size: int) -> bytes:
        ...

    def close(self) -> None:
        ...


class NamedPipeConnection:
    """Unbuffered byte-mode pipe access with bounded availability polling.

    Python's regular file wrapper does not expose cancellable overlapped pipe
    reads.  WaitNamedPipe bounds instance acquisition and PeekNamedPipe keeps
    reads from entering the kernel until at least one byte is available.  A
    narrow race remains between WaitNamedPipe and ``open``; it fails closed
    rather than starting or replacing a bridge process.
    """

    def __init__(
        self,
        pipe_path: str,
        *,
        connect_timeout_seconds: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        read_timeout_seconds: float = DEFAULT_READ_TIMEOUT_SECONDS,
    ) -> None:
        if os.name != "nt":
            raise OSError("Windows named pipes are available only on Windows")
        if connect_timeout_seconds <= 0 or read_timeout_seconds <= 0:
            raise ValueError("named-pipe timeouts must be positive")
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.WaitNamedPipeW.argtypes = (ctypes.c_wchar_p, ctypes.c_uint32)
        kernel32.WaitNamedPipeW.restype = ctypes.c_int
        timeout_ms = max(1, min(int(connect_timeout_seconds * 1000), 0xFFFFFFFE))
        if not kernel32.WaitNamedPipeW(pipe_path, timeout_ms):
            error = ctypes.get_last_error()
            raise TimeoutError(
                f"named pipe was unavailable after {connect_timeout_seconds:.3f}s "
                f"(winerror={error}): {pipe_path}"
            )
        self._handle = open(pipe_path, "r+b", buffering=0)
        self._kernel32 = kernel32
        self._read_timeout_seconds = float(read_timeout_seconds)

    def write(self, data: bytes) -> int:
        written = self._handle.write(data)
        return 0 if written is None else int(written)

    def read(self, size: int) -> bytes:
        import ctypes
        import msvcrt

        if size <= 0:
            return b""
        deadline = time.monotonic() + self._read_timeout_seconds
        os_handle = msvcrt.get_osfhandle(self._handle.fileno())
        while True:
            available = ctypes.c_uint32()
            ok = self._kernel32.PeekNamedPipe(
                ctypes.c_void_p(os_handle),
                None,
                0,
                None,
                ctypes.byref(available),
                None,
            )
            if not ok:
                error = ctypes.get_last_error()
                raise OSError(error, f"PeekNamedPipe failed for {self._handle.name}")
            if available.value:
                return self._handle.read(min(size, int(available.value)))
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"named-pipe read timed out after "
                    f"{self._read_timeout_seconds:.3f}s"
                )
            time.sleep(0.01)

    def close(self) -> None:
        self._handle.close()


class RoutePolicy:
    """Exact allowlist for the runner's read and write API surface."""

    _RULES: Mapping[str, tuple[re.Pattern[str], ...]] = {
        "GET": (
            re.compile(r"^/api/v1/product$"),
            re.compile(r"^/api/v1/composition$"),
            re.compile(r"^/api/v1/composition/layers/[1-9]\d*$"),
            re.compile(r"^/api/v1/composition/layers/[1-9]\d*/clips/1$"),
            re.compile(r"^/api/v1/parameter/by-id/[1-9]\d*$"),
            re.compile(r"^/api/v1/parameter/by-id/[1-9]\d*/phase-source$"),
            re.compile(r"^/api/v1/composition/monitors$"),
            re.compile(r"^/api/v1/composition/monitors/[1-9]\d*/snapshot\.png$"),
        ),
        "PUT": (re.compile(r"^/api/v1/parameter/by-id/[1-9]\d*$"),),
        "POST": (
            re.compile(r"^/api/v1/composition/grow-to$"),
            re.compile(r"^/api/v1/composition/clips/open$"),
            re.compile(
                r"^/api/v1/composition/layers/[1-9]\d*/clips/1/connect$"
            ),
        ),
    }

    @classmethod
    def validate(cls, method: str, path: str) -> None:
        normalized_method = method.upper()
        if not path.startswith("/") or "?" in path or "#" in path:
            raise RouteRejected(f"route must be an absolute query-free API path: {path}")
        rules = cls._RULES.get(normalized_method, ())
        if not any(rule.fullmatch(path) for rule in rules):
            raise RouteRejected(f"route rejected by narrow policy: {method} {path}")


ConnectionFactory = Callable[[str], ByteConnection]


class PipeHttpClient:
    """Binary-safe HTTP/1.1 client over one configurable named pipe.

    Transport failures on GET are retried once using a fresh connection.  HTTP
    errors and every write request are returned/raised exactly once.
    """

    def __init__(
        self,
        pipe_path: str,
        *,
        connection_factory: ConnectionFactory | None = None,
        route_policy: type[RoutePolicy] = RoutePolicy,
        connect_timeout_seconds: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        read_timeout_seconds: float = DEFAULT_READ_TIMEOUT_SECONDS,
        request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        if request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        self.pipe_path = pipe_path
        self._factory = connection_factory or (
            lambda path: NamedPipeConnection(
                path,
                connect_timeout_seconds=connect_timeout_seconds,
                read_timeout_seconds=read_timeout_seconds,
            )
        )
        self._policy = route_policy
        self._request_timeout_seconds = float(request_timeout_seconds)
        self._request_deadline: float | None = None
        self._connection: ByteConnection | None = None
        self._buffer = bytearray()

    def close(self) -> None:
        if self._connection is not None:
            with contextlib.suppress(Exception):
                self._connection.close()
        self._connection = None
        self._buffer.clear()

    def __enter__(self) -> "PipeHttpClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _connect(self) -> None:
        self.close()
        try:
            self._connection = self._factory(self.pipe_path)
        except Exception as exc:
            raise PipeTransportError(
                f"cannot connect to named pipe {self.pipe_path}: {exc}",
                ambiguous=False,
            ) from exc

    def _read_more(self) -> None:
        if self._connection is None:
            raise PipeTransportError("named pipe is not connected", ambiguous=False)
        if (
            self._request_deadline is not None
            and time.monotonic() >= self._request_deadline
        ):
            raise PipeTransportError("named-pipe request deadline expired", ambiguous=True)
        try:
            chunk = self._connection.read(65536)
        except Exception as exc:
            raise PipeTransportError(
                f"named pipe read failed: {exc}", ambiguous=True
            ) from exc
        if (
            self._request_deadline is not None
            and time.monotonic() >= self._request_deadline
        ):
            raise PipeTransportError("named-pipe request deadline expired", ambiguous=True)
        if not chunk:
            raise PipeTransportError("named pipe closed during response", ambiguous=True)
        self._buffer.extend(chunk)

    def _read_until(self, marker: bytes, *, limit: int = 1024 * 1024) -> bytes:
        while True:
            index = self._buffer.find(marker)
            if index >= 0:
                end = index + len(marker)
                result = bytes(self._buffer[:end])
                del self._buffer[:end]
                return result
            if len(self._buffer) > limit:
                raise PipeTransportError("HTTP header/line exceeds limit", ambiguous=True)
            self._read_more()

    def _read_exactly(self, size: int) -> bytes:
        while len(self._buffer) < size:
            self._read_more()
        result = bytes(self._buffer[:size])
        del self._buffer[:size]
        return result

    @staticmethod
    def _parse_header_lines(data: bytes) -> tuple[tuple[str, str], ...]:
        headers: list[tuple[str, str]] = []
        for raw_line in data.split(b"\r\n"):
            if not raw_line:
                continue
            if raw_line[:1] in (b" ", b"\t") or b":" not in raw_line:
                raise PipeTransportError("malformed HTTP header", ambiguous=True)
            raw_name, raw_value = raw_line.split(b":", 1)
            try:
                name = raw_name.decode("ascii")
                value = raw_value.strip().decode("latin-1")
            except UnicodeError as exc:
                raise PipeTransportError(
                    f"invalid HTTP header encoding: {exc}", ambiguous=True
                ) from exc
            headers.append((name, value))
        return tuple(headers)

    def _read_response(self, request_method: str) -> HttpResponse:
        while True:
            head = self._read_until(b"\r\n\r\n")
            first_line, separator, raw_headers = head[:-4].partition(b"\r\n")
            if not separator:
                raise PipeTransportError("malformed HTTP response", ambiguous=True)
            try:
                version, raw_status, raw_reason = first_line.split(b" ", 2)
                if not version.startswith(b"HTTP/"):
                    raise ValueError("bad HTTP version")
                status = int(raw_status)
                reason = raw_reason.decode("latin-1")
            except (ValueError, UnicodeError) as exc:
                raise PipeTransportError(
                    f"malformed HTTP status line: {first_line!r}", ambiguous=True
                ) from exc
            headers = self._parse_header_lines(raw_headers)
            if 100 <= status < 200 and status != 101:
                continue
            break

        lookup: dict[str, list[str]] = {}
        for key, value in headers:
            lookup.setdefault(key.casefold(), []).append(value)

        trailers: tuple[tuple[str, str], ...] = ()
        no_body = request_method == "HEAD" or status in (204, 304)
        transfer_values = ",".join(lookup.get("transfer-encoding", ())).casefold()
        if no_body:
            body = b""
        elif "chunked" in transfer_values:
            chunks: list[bytes] = []
            while True:
                raw_size = self._read_until(b"\r\n", limit=8192)[:-2]
                try:
                    size = int(raw_size.split(b";", 1)[0].strip(), 16)
                except ValueError as exc:
                    raise PipeTransportError(
                        f"invalid chunk size: {raw_size!r}", ambiguous=True
                    ) from exc
                if size == 0:
                    trailer_lines: list[bytes] = []
                    while True:
                        trailer_line = self._read_until(b"\r\n", limit=8192)[:-2]
                        if not trailer_line:
                            break
                        trailer_lines.append(trailer_line)
                    trailers = self._parse_header_lines(b"\r\n".join(trailer_lines))
                    break
                chunks.append(self._read_exactly(size))
                if self._read_exactly(2) != b"\r\n":
                    raise PipeTransportError("malformed chunk delimiter", ambiguous=True)
            body = b"".join(chunks)
        else:
            content_lengths = lookup.get("content-length", ())
            if not content_lengths:
                raise PipeTransportError(
                    "response has neither Content-Length nor chunked encoding",
                    ambiguous=True,
                )
            if len(set(content_lengths)) != 1:
                raise PipeTransportError(
                    "conflicting Content-Length headers", ambiguous=True
                )
            try:
                length = int(content_lengths[0])
            except ValueError as exc:
                raise PipeTransportError(
                    "invalid Content-Length header", ambiguous=True
                ) from exc
            if length < 0:
                raise PipeTransportError("negative Content-Length", ambiguous=True)
            body = self._read_exactly(length)

        response = HttpResponse(status, reason, headers, body, trailers)
        if "close" in (response.header("connection") or "").casefold():
            self.close()
        return response

    def _request_once(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = dataclasses.MISSING,
    ) -> HttpResponse:
        self._policy.validate(method, path)
        body = (
            b""
            if json_body is dataclasses.MISSING
            else json.dumps(
                json_body, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
        )
        lines = [
            f"{method} {path} HTTP/1.1",
            "Host: localhost",
            "Accept: application/json, image/png",
            "Connection: keep-alive",
        ]
        if json_body is not dataclasses.MISSING:
            lines.extend(
                ("Content-Type: application/json", f"Content-Length: {len(body)}")
            )
        request_bytes = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii") + body

        if self._connection is None:
            self._connect()
        assert self._connection is not None
        started_write = False
        self._request_deadline = time.monotonic() + self._request_timeout_seconds
        try:
            view = memoryview(request_bytes)
            while view:
                if time.monotonic() >= self._request_deadline:
                    raise TimeoutError("named-pipe request deadline expired during write")
                started_write = True
                count = self._connection.write(bytes(view))
                if count <= 0:
                    raise OSError("zero-byte named-pipe write")
                view = view[count:]
            response = self._read_response(method)
        except PipeTransportError as exc:
            self.close()
            raise PipeTransportError(
                str(exc), ambiguous=started_write or exc.ambiguous
            ) from exc
        except Exception as exc:
            self.close()
            raise PipeTransportError(
                f"named pipe request failed: {exc}", ambiguous=started_write
            ) from exc
        finally:
            self._request_deadline = None
        if response.status >= 400:
            raise HttpStatusError(method, path, response)
        return response

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = dataclasses.MISSING,
    ) -> HttpResponse:
        normalized_method = method.upper()
        attempts = 2 if normalized_method == "GET" else 1
        last_error: PipeTransportError | None = None
        for _ in range(attempts):
            try:
                return self._request_once(
                    normalized_method, path, json_body=json_body
                )
            except PipeTransportError as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    def get(self, path: str) -> HttpResponse:
        return self.request("GET", path)

    def post(
        self, path: str, *, json_body: Any = dataclasses.MISSING
    ) -> HttpResponse:
        return self.request("POST", path, json_body=json_body)

    def put(self, path: str, *, json_body: Any) -> HttpResponse:
        return self.request("PUT", path, json_body=json_body)


class CampaignLock:
    """One-process campaign lock.  Stale locks require manual inspection."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self._held = False

    def __enter__(self) -> "CampaignLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = canonical_json(
            {"pid": os.getpid(), "created_at": utc_timestamp(), "path": str(self.path)}
        )
        try:
            descriptor = os.open(
                self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except FileExistsError as exc:
            raise RunnerError(
                f"campaign lock already exists; inspect it before removal: {self.path}"
            ) from exc
        try:
            os.write(descriptor, payload + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        _fsync_directory(self.path.parent)
        self._held = True
        return self

    def __exit__(self, *_: object) -> None:
        if self._held:
            self.path.unlink()
            _fsync_directory(self.path.parent)
            self._held = False


class CampaignJournal:
    """Append-only JSONL operation journal with fsync on every event."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def append(self, event: Mapping[str, Any]) -> JsonObject:
        record: JsonObject = {
            "event_id": str(uuid.uuid4()),
            "timestamp": utc_timestamp(),
            **dict(event),
        }
        data = canonical_json(record) + b"\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab", buffering=0) as handle:
            handle.write(data)
            os.fsync(handle.fileno())
        _fsync_directory(self.path.parent)
        return record

    def records(self) -> list[JsonObject]:
        if not self.path.exists():
            return []
        records: list[JsonObject] = []
        with self.path.open("rb") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RunnerError(
                        f"invalid journal line {line_number} in {self.path}: {exc}"
                    ) from exc
                if not isinstance(value, dict):
                    raise RunnerError(
                        f"journal line {line_number} is not an object"
                    )
                records.append(value)
        return records

    def gate(self, gate_id: str) -> tuple[JsonObject, JsonObject | None]:
        created_records: list[tuple[int, JsonObject]] = []
        verified_records: list[tuple[int, JsonObject]] = []
        for index, record in enumerate(self.records()):
            if record.get("gate_id") != gate_id:
                continue
            if record.get("kind") == "manual_gate_created":
                created_records.append((index, record))
            elif record.get("kind") == "manual_gate_verified":
                verified_records.append((index, record))
        if not created_records:
            raise RunnerError(f"unknown manual gate ID: {gate_id}")
        if len(created_records) != 1 or len(verified_records) > 1:
            raise RunnerError(f"manual gate {gate_id} has duplicate journal records")
        created_index, created = created_records[0]
        if verified_records:
            verified_index, verified = verified_records[0]
            if verified_index <= created_index:
                raise RunnerError(
                    f"manual gate {gate_id} was verified before it was created"
                )
            return created, verified
        return created, None


def validate_calibration_recovery_marker(value: Any, path: Path) -> JsonObject:
    """Validate the durable, authoritative recovery state for one live calibration."""

    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RunnerError(f"invalid calibration recovery marker schema: {path}")
    if value.get("artifact_role") != "live_calibration_recovery":
        raise RunnerError(f"invalid calibration recovery marker role: {path}")
    if value.get("status") != "active":
        raise RunnerError(f"calibration recovery marker is not active: {path}")
    transaction_id = value.get("transaction_id")
    try:
        uuid.UUID(str(transaction_id))
    except (ValueError, AttributeError) as exc:
        raise RunnerError("calibration recovery transaction_id is not a UUID") from exc
    if value.get("layer") != 94:
        raise RunnerError("calibration recovery marker must target exactly layer 94")
    if not isinstance(value.get("created_at"), str) or not value["created_at"]:
        raise RunnerError("calibration recovery marker has no created_at timestamp")
    if not isinstance(value.get("build_id"), str) or not value["build_id"]:
        raise RunnerError("calibration recovery marker has no build_id")
    if (
        not isinstance(value.get("measurement_out"), str)
        or not Path(value["measurement_out"]).is_absolute()
    ):
        raise RunnerError("calibration recovery measurement output is invalid")

    original_states = value.get("original_states")
    if not isinstance(original_states, dict) or set(original_states) != set(
        CALIBRATION_SOURCE_FIELD_TYPES
    ):
        raise RunnerError("calibration recovery marker has incomplete original states")
    for name, valuetype in CALIBRATION_SOURCE_FIELD_TYPES.items():
        state = original_states[name]
        if not isinstance(state, dict) or state.get("valuetype") != valuetype:
            raise RunnerError(
                f"calibration recovery original {name} has the wrong valuetype"
            )
        if "value" not in state:
            raise RunnerError(f"calibration recovery original {name} has no value")
        parameter_id = state.get("parameter_id_hint")
        if (
            not isinstance(parameter_id, int)
            or isinstance(parameter_id, bool)
            or parameter_id <= 0
        ):
            raise RunnerError(
                f"calibration recovery original {name} has no parameter ID"
            )
        if valuetype == "ParamRange" and (
            not isinstance(state["value"], (int, float))
            or isinstance(state["value"], bool)
            or not math.isfinite(float(state["value"]))
        ):
            raise RunnerError(
                f"calibration recovery original {name} has a non-finite value"
            )
        if valuetype in {"ParamChoice", "ParamState"}:
            index = state.get("index")
            if not isinstance(index, int) or isinstance(index, bool) or index < 0:
                raise RunnerError(
                    f"calibration recovery original {name} has an invalid index"
                )

    clip_identity = value.get("clip_identity")
    if not isinstance(clip_identity, dict):
        raise RunnerError("calibration recovery marker has no clip identity")
    if (
        not isinstance(clip_identity.get("clip_id_hint"), int)
        or isinstance(clip_identity.get("clip_id_hint"), bool)
        or clip_identity["clip_id_hint"] <= 0
        or not isinstance(clip_identity.get("name"), str)
        or not clip_identity["name"]
        or clip_identity.get("trigger_style") not in {"Normal", "Toggle"}
        or not isinstance(clip_identity.get("source_identity"), dict)
    ):
        raise RunnerError("calibration recovery clip identity is invalid")

    fingerprint = value.get("composition_fingerprint")
    if not isinstance(fingerprint, dict) or not is_sha256(fingerprint.get("sha256")):
        raise RunnerError("calibration recovery composition fingerprint is invalid")
    active_preset = value.get("active_preset")
    if (
        not isinstance(active_preset, dict)
        or not isinstance(active_preset.get("path"), str)
        or not Path(active_preset["path"]).is_absolute()
        or not is_sha256(active_preset.get("sha256"))
    ):
        raise RunnerError("calibration recovery active preset lineage is invalid")
    snapshot = value.get("snapshot")
    if (
        not isinstance(snapshot, dict)
        or not isinstance(snapshot.get("path"), str)
        or not Path(snapshot["path"]).is_absolute()
        or not is_sha256(snapshot.get("sha256"))
        or not isinstance(snapshot.get("artifact_id"), str)
        or snapshot.get("restart_stage") != "restart-a"
    ):
        raise RunnerError("calibration recovery snapshot lineage is invalid")
    try:
        uuid.UUID(snapshot["artifact_id"])
    except (ValueError, AttributeError) as exc:
        raise RunnerError(
            "calibration recovery snapshot artifact_id is not a UUID"
        ) from exc

    artifacts = value.get("artifact_lineage")
    if (
        not isinstance(artifacts, dict)
        or not isinstance(artifacts.get("repo_root"), str)
        or not Path(artifacts["repo_root"]).is_absolute()
        or not isinstance(artifacts.get("manifest_path"), str)
        or not Path(artifacts["manifest_path"]).is_absolute()
        or not is_sha256(artifacts.get("manifest_sha256"))
        or not isinstance(artifacts.get("parent_artifact_hashes"), dict)
        or not artifacts["parent_artifact_hashes"]
    ):
        raise RunnerError("calibration recovery artifact lineage is invalid")
    for key, metadata in artifacts["parent_artifact_hashes"].items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(metadata, dict)
            or not is_sha256(metadata.get("sha256"))
            or not isinstance(metadata.get("bytes"), int)
            or isinstance(metadata.get("bytes"), bool)
            or metadata["bytes"] < 0
        ):
            raise RunnerError(
                f"calibration recovery parent artifact entry is invalid: {key!r}"
            )

    events = value.get("events")
    if not isinstance(events, list):
        raise RunnerError("calibration recovery marker events are not an array")
    for sequence, event in enumerate(events, 1):
        if (
            not isinstance(event, dict)
            or event.get("sequence") != sequence
            or not isinstance(event.get("timestamp"), str)
            or not event["timestamp"]
            or not isinstance(event.get("kind"), str)
            or not event["kind"]
        ):
            raise RunnerError(
                f"calibration recovery marker event {sequence} is invalid"
            )
    return value


class CalibrationRecoveryStore:
    """Atomic recovery marker updated before and after every calibration write."""

    def __init__(self, path: Path, journal: CampaignJournal) -> None:
        self.path = path.resolve()
        self.journal = journal

    def load(self, *, required: bool = True) -> JsonObject | None:
        if not self.path.exists():
            if required:
                raise RunnerError(
                    f"no incomplete calibration recovery marker exists: {self.path}"
                )
            return None
        try:
            payload = self.path.read_bytes()
        except OSError as exc:
            raise RunnerError(
                f"cannot read calibration recovery marker {self.path}: {exc}"
            ) from exc
        value = json_from_bytes(payload, self.path)
        return validate_calibration_recovery_marker(value, self.path)

    def begin(self, marker: Mapping[str, Any]) -> JsonObject:
        if self.path.exists():
            existing = self.load()
            assert existing is not None
            raise RunnerError(
                "incomplete calibration transaction "
                f"{existing['transaction_id']} already requires recovery at {self.path}"
            )
        value = validate_calibration_recovery_marker(dict(marker), self.path)
        atomic_write_json(self.path, value)
        self.journal.append(
            {
                "kind": "calibration_recovery_started",
                "transaction_id": value["transaction_id"],
                "recovery_marker": str(self.path),
                "build_id": value["build_id"],
                "layer": value["layer"],
            }
        )
        return value

    def append(self, transaction_id: str, event: Mapping[str, Any]) -> JsonObject:
        marker = self.load()
        assert marker is not None
        if marker["transaction_id"] != transaction_id:
            raise RunnerError(
                "calibration recovery transaction changed while it was active"
            )
        record: JsonObject = {
            **dict(event),
            "sequence": len(marker["events"]) + 1,
            "timestamp": utc_timestamp(),
        }
        marker["events"].append(record)
        validate_calibration_recovery_marker(marker, self.path)
        atomic_write_json(self.path, marker)
        self.journal.append(
            {
                "kind": "calibration_recovery_progress",
                "transaction_id": transaction_id,
                "recovery_marker": str(self.path),
                "progress": record,
            }
        )
        return record

    def commit(self, transaction_id: str, result: Mapping[str, Any]) -> None:
        marker = self.load()
        assert marker is not None
        if marker["transaction_id"] != transaction_id:
            raise RunnerError(
                "calibration recovery transaction changed before commit"
            )
        self.append(
            transaction_id,
            {
                "kind": "final_restore_verified",
                "result": dict(result),
            },
        )
        self.journal.append(
            {
                "kind": "calibration_recovery_committed",
                "transaction_id": transaction_id,
                "recovery_marker": str(self.path),
                **dict(result),
            }
        )
        try:
            self.path.unlink()
            _fsync_directory(self.path.parent)
        except OSError as exc:
            raise RunnerError(
                f"cannot remove committed calibration recovery marker {self.path}: {exc}"
            ) from exc


@dataclasses.dataclass(frozen=True)
class ArtifactBundle:
    build_id: str
    status: str
    parent_build_id: str | None
    measurement_sha256: str | None
    manifest_path: Path
    repo_root: Path
    artifacts: Mapping[str, Mapping[str, Any]]

    @classmethod
    def verify(cls, manifest_path: Path, repo_root: Path) -> "ArtifactBundle":
        manifest_path = manifest_path.resolve()
        repo_root = repo_root.resolve()
        value = load_json(manifest_path)
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ArtifactError("build manifest must use schema_version 1")
        build_id = value.get("build_id")
        status = value.get("status")
        parent_build_id = value.get("parent_build_id")
        measurement_sha256 = value.get("measurement_sha256")
        artifacts = value.get("artifacts")
        if not isinstance(build_id, str) or not build_id:
            raise ArtifactError("build manifest has no nonempty build_id")
        if status not in {"provisional", "accepted"}:
            raise ArtifactError("build manifest status must be provisional or accepted")
        if status == "provisional":
            if parent_build_id is not None or measurement_sha256 is not None:
                raise ArtifactError(
                    "provisional build must have null parent and measurement lineage"
                )
        else:
            if (
                not isinstance(parent_build_id, str)
                or not parent_build_id
                or parent_build_id == build_id
            ):
                raise ArtifactError(
                    "accepted build must name a distinct provisional parent build"
                )
            if not is_sha256(measurement_sha256):
                raise ArtifactError(
                    "accepted build must contain a SHA-256 measurement hash"
                )
        if not isinstance(artifacts, dict) or not artifacts:
            raise ArtifactError("build manifest has no artifacts")

        manifest_resolved = manifest_path.resolve()
        for key, metadata in artifacts.items():
            if not isinstance(key, str) or "\\" in key or key.startswith("/"):
                raise ArtifactError(f"artifact key is not normalized POSIX: {key!r}")
            candidate = (repo_root / Path(*key.split("/"))).resolve()
            try:
                candidate.relative_to(repo_root)
            except ValueError as exc:
                raise ArtifactError(f"artifact escapes repo root: {key}") from exc
            if candidate == manifest_resolved:
                raise ArtifactError("build manifest cannot hash itself")
            if not isinstance(metadata, dict):
                raise ArtifactError(f"artifact metadata is not an object: {key}")
            expected_hash = metadata.get("sha256")
            expected_bytes = metadata.get("bytes")
            if not candidate.is_file():
                raise ArtifactError(f"artifact is missing: {candidate}")
            try:
                payload = candidate.read_bytes()
            except OSError as exc:
                raise ArtifactError(f"cannot read artifact: {candidate}: {exc}") from exc
            actual_bytes = len(payload)
            actual_hash = sha256_bytes(payload)
            if (
                not is_sha256(expected_hash)
                or not isinstance(expected_bytes, int)
                or isinstance(expected_bytes, bool)
                or expected_bytes < 0
                or actual_hash != expected_hash
                or actual_bytes != expected_bytes
            ):
                raise ArtifactError(
                    f"artifact hash/size mismatch: {candidate} "
                    f"(expected {expected_hash}/{expected_bytes}, "
                    f"got {actual_hash}/{actual_bytes})"
                )
            if candidate.suffix.casefold() == ".json":
                child = json_from_bytes(payload, candidate)
                if (
                    isinstance(child, dict)
                    and "build_id" in child
                    and child["build_id"] != build_id
                ):
                    raise ArtifactError(
                        f"artifact build_id mismatch in {candidate}: "
                        f"{child['build_id']} != {build_id}"
                    )
        return cls(
            build_id,
            status,
            parent_build_id,
            measurement_sha256,
            manifest_path,
            repo_root,
            artifacts,
        )

    def _path_key_and_metadata(
        self, path: Path
    ) -> tuple[Path, str, Mapping[str, Any]]:
        resolved = path.resolve()
        try:
            key = resolved.relative_to(self.repo_root).as_posix()
        except ValueError as exc:
            raise ArtifactError(f"artifact is outside repo root: {resolved}") from exc
        metadata = self.artifacts.get(key)
        if not isinstance(metadata, dict):
            raise ArtifactError(f"artifact is not declared by build manifest: {key}")
        return resolved, key, metadata

    def read_verified_bytes(self, path: Path) -> bytes:
        """Read once and bind the exact returned payload to manifest metadata."""

        resolved, _, metadata = self._path_key_and_metadata(path)
        try:
            payload = resolved.read_bytes()
        except OSError as exc:
            raise ArtifactError(f"cannot read artifact: {resolved}: {exc}") from exc
        if (
            len(payload) != metadata.get("bytes")
            or sha256_bytes(payload) != metadata.get("sha256")
        ):
            raise ArtifactError(f"artifact changed after manifest verification: {resolved}")
        return payload

    def require_path(self, path: Path) -> Mapping[str, Any]:
        _, _, metadata = self._path_key_and_metadata(path)
        self.read_verified_bytes(path)
        return metadata

    def require(self, requested: Path) -> tuple[str, Mapping[str, Any]]:
        """Require an exact artifact path or one unique manifest basename."""

        text = requested.as_posix()
        if requested.is_absolute() or "/" in text:
            resolved, key, metadata = self._path_key_and_metadata(requested)
            self.read_verified_bytes(resolved)
            return key, metadata
        matches = [
            (key, metadata)
            for key, metadata in self.artifacts.items()
            if Path(key).name == requested.name
        ]
        if not matches:
            raise ArtifactError(
                f"artifact basename is not declared by build manifest: {requested.name}"
            )
        if len(matches) != 1:
            raise ArtifactError(
                f"artifact basename is ambiguous in build manifest: {requested.name}"
            )
        key, metadata = matches[0]
        self.read_verified_bytes(self.repo_root / Path(*key.split("/")))
        return key, metadata


@dataclasses.dataclass(frozen=True)
class TypedLiveControls:
    """Validated, non-executable desired-state allowlist from the renderer."""

    build_id: str
    status: str
    layers: Mapping[str, Mapping[str, Any]]
    path: Path

    _FIELD_TYPES: Mapping[tuple[str, str], str] = dataclasses.field(
        default_factory=lambda: {
            ("text_animator_source", "Text"): "ParamText",
            ("text_animator_source", "Font"): "ParamChoice",
            ("text_animator_source", "Size"): "ParamRange",
            ("text_animator_source", "Color"): "ParamColor",
            ("text_animator_source", "Spacing Y"): "ParamRange",
            ("text_animator_source", "Position X"): "ParamRange",
            ("text_animator_source", "Position Y"): "ParamRange",
            ("clip_video", "opacity"): "ParamRange",
            ("permanent_transform", "Position X"): "ParamRange",
            ("permanent_transform", "Position Y"): "ParamRange",
            ("permanent_transform", "Rotation Z"): "ParamRange",
        },
        init=False,
        repr=False,
        compare=False,
    )

    @classmethod
    def verify(
        cls, path: Path, bundle: ArtifactBundle
    ) -> "TypedLiveControls":
        path = path.resolve()
        value = json_from_bytes(bundle.read_verified_bytes(path), path)
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise ArtifactError("live-controls must use schema_version 1")
        if value.get("artifact_role") != "typed_live_controls":
            raise ArtifactError("live-controls has the wrong artifact_role")
        if value.get("build_id") != bundle.build_id:
            raise ArtifactError("live-controls build_id does not match build manifest")
        if value.get("wave_size") != MAX_WRITES_PER_WAVE:
            raise ArtifactError(
                f"live-controls wave_size must be {MAX_WRITES_PER_WAVE}"
            )
        status = value.get("status")
        if status != bundle.status:
            raise ArtifactError(
                "live-controls status does not match the build manifest"
            )
        glyph_font = value.get("glyph_font")
        if not isinstance(glyph_font, dict):
            raise ArtifactError("live-controls has no glyph_font contract")
        layers = value.get("layers")
        if not isinstance(layers, dict) or set(layers) != {
            str(index) for index in range(1, 149)
        }:
            raise ArtifactError("live-controls must contain exact layers 1..148")

        allowed_types = cls.__dataclass_fields__["_FIELD_TYPES"].default_factory()
        for layer_number in range(1, 149):
            record = layers[str(layer_number)]
            if not isinstance(record, dict) or record.get("layer") != layer_number:
                raise ArtifactError(
                    f"live-controls layer record mismatch at {layer_number}"
                )
            raw_key = record.get("raw_key")
            if not isinstance(raw_key, str) or not raw_key.isdecimal():
                raise ArtifactError(
                    f"live-controls raw_key must be decimal text at layer {layer_number}"
                )
            fields = record.get("fields")
            if not isinstance(fields, list) or not fields:
                raise ArtifactError(
                    f"live-controls has no fields at layer {layer_number}"
                )
            seen: set[tuple[str, str]] = set()
            for field in fields:
                if not isinstance(field, dict):
                    raise ArtifactError(
                        f"live-controls field is not an object at layer {layer_number}"
                    )
                key = (field.get("target"), field.get("parameter"))
                expected_type = allowed_types.get(key)
                if expected_type is None:
                    raise ArtifactError(
                        f"unallowlisted live-controls field at layer "
                        f"{layer_number}: {key}"
                    )
                if field.get("valuetype") != expected_type:
                    raise ArtifactError(
                        f"wrong valuetype for layer {layer_number} {key}: "
                        f"{field.get('valuetype')} != {expected_type}"
                    )
                if key in seen:
                    raise ArtifactError(
                        f"duplicate live-controls field at layer {layer_number}: {key}"
                    )
                seen.add(key)
                desired = field.get("desired")
                if expected_type in ("ParamText", "ParamChoice", "ParamColor"):
                    if not isinstance(desired, str):
                        raise ArtifactError(
                            f"non-string desired value at layer {layer_number}: {key}"
                        )
                elif not isinstance(desired, (int, float)) or isinstance(
                    desired, bool
                ) or not math.isfinite(float(desired)):
                    raise ArtifactError(
                        f"nonnumeric desired value at layer {layer_number}: {key}"
                    )
                purpose = field.get("purpose")
                if not isinstance(purpose, str) or not purpose:
                    raise ArtifactError(
                        f"field purpose is missing at layer {layer_number}: {key}"
                    )
        return cls(bundle.build_id, status, layers, path)


@dataclasses.dataclass(frozen=True)
class PngInfo:
    width: int
    height: int
    mode: str


def validate_png(
    data: bytes,
    expected_size: tuple[int, int] | None = None,
    *,
    allowed_modes: Sequence[str] = ("RGBA",),
) -> PngInfo:
    allowed = tuple(allowed_modes)
    if not allowed or any(mode not in {"RGB", "RGBA"} for mode in allowed):
        raise RunnerError(f"invalid allowed PNG modes: {allowed!r}")
    if not data.startswith(PNG_SIGNATURE):
        raise RunnerError("monitor response is not a PNG")
    offset = len(PNG_SIGNATURE)
    width = height = color_type = bit_depth = None
    saw_end = False
    saw_image_data = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise RunnerError("truncated PNG chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise RunnerError("truncated PNG payload")
        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(kind)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise RunnerError(f"PNG CRC mismatch for chunk {kind!r}")
        if kind == b"IHDR":
            if length != 13 or width is not None:
                raise RunnerError("invalid PNG IHDR")
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB", payload
            )
        elif kind == b"IDAT":
            saw_image_data = True
        elif kind == b"IEND":
            saw_end = True
            if length != 0 or crc_end != len(data):
                raise RunnerError("invalid trailing PNG data")
            break
        offset = crc_end
    if not saw_end or not saw_image_data or width is None or height is None:
        raise RunnerError("incomplete PNG")
    ihdr_mode = {2: "RGB", 6: "RGBA"}.get(color_type)
    if bit_depth != 8 or ihdr_mode not in allowed:
        raise RunnerError(
            "unexpected PNG pixel format: "
            f"bit_depth={bit_depth}, color_type={color_type}, "
            f"allowed_modes={allowed!r}"
        )
    if expected_size is not None and (width, height) != expected_size:
        raise RunnerError(
            f"unexpected PNG dimensions {(width, height)} != {expected_size}"
        )
    try:
        from PIL import Image
    except ImportError as exc:
        raise RunnerError("Pillow is required for full PNG validation") from exc
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            decoded_format = image.format
            decoded_mode = image.mode
            decoded_size = image.size
    except (OSError, ValueError) as exc:
        raise RunnerError(f"PNG cannot be fully decoded: {exc}") from exc
    if decoded_format != "PNG" or decoded_mode != ihdr_mode:
        raise RunnerError(
            "decoded image mode disagrees with the PNG header: "
            f"{decoded_format}/{decoded_mode}, expected PNG/{ihdr_mode}"
        )
    if decoded_size != (width, height):
        raise RunnerError(
            f"decoded PNG dimensions {decoded_size} disagree with IHDR {(width, height)}"
        )
    return PngInfo(width, height, ihdr_mode)


def parameter_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def parameter_state(parameter: Mapping[str, Any]) -> JsonObject:
    valuetype = parameter.get("valuetype")
    result: JsonObject = {"valuetype": valuetype, "value": parameter.get("value")}
    if valuetype in ("ParamChoice", "ParamState"):
        result["index"] = parameter.get("index")
    if "id" in parameter:
        result["parameter_id_hint"] = parameter["id"]
    return result


def parameter_values_equal(valuetype: str, left: Any, right: Any) -> bool:
    if valuetype == "ParamRange":
        if (
            not isinstance(left, (int, float))
            or isinstance(left, bool)
            or not math.isfinite(float(left))
            or not isinstance(right, (int, float))
            or isinstance(right, bool)
            or not math.isfinite(float(right))
        ):
            return False
        return float(left) == float(right)
    return type(left) is type(right) and left == right


def parameter_states_equal(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    include_choice_index: bool = True,
) -> bool:
    valuetype = left.get("valuetype")
    if not isinstance(valuetype, str) or right.get("valuetype") != valuetype:
        return False
    if not parameter_values_equal(valuetype, left.get("value"), right.get("value")):
        return False
    if valuetype in {"ParamChoice", "ParamState"} and include_choice_index:
        return left.get("index") == right.get("index")
    return True


def measurement_parent_artifact_hashes(
    bundle: ArtifactBundle,
) -> dict[str, dict[str, Any]]:
    """Re-read and bind every exact provisional artifact before calibration."""

    observed: dict[str, dict[str, Any]] = {}
    for key in sorted(bundle.artifacts):
        metadata = bundle.artifacts[key]
        candidate = bundle.repo_root / Path(*key.split("/"))
        payload = bundle.read_verified_bytes(candidate)
        observed[key] = {
            "sha256": sha256_bytes(payload),
            "bytes": len(payload),
        }
        if observed[key] != {
            "sha256": metadata.get("sha256"),
            "bytes": metadata.get("bytes"),
        }:
            raise ArtifactError(f"artifact metadata drifted during calibration: {key}")
    return observed


def calibration_capture_path(measurement_path: Path, state: str) -> Path:
    if state not in CALIBRATION_CAPTURE_STATES:
        raise RunnerError(f"unknown calibration capture state: {state}")
    return measurement_path.resolve().with_name(
        f"{measurement_path.stem}_{state}.png"
    )


def calibration_witness_roi(
    witness_box: Sequence[Any] | None,
) -> tuple[int, int, int, int]:
    if (
        not isinstance(witness_box, (list, tuple))
        or len(witness_box) != 4
        or any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in witness_box
        )
    ):
        raise RunnerError("layer 94 witness box is not four integer pixels")
    left, top, right, bottom = (int(value) for value in witness_box)
    if not (0 <= left < right <= 1920 and 0 <= top < bottom <= 1080):
        raise RunnerError("layer 94 witness box escapes the 1920x1080 frame")
    return left, top, right, bottom


def calibration_capture_roi(
    witness_box: Sequence[Any] | None,
) -> tuple[int, int, int, int]:
    """Pad the travel envelope so endpoint ink is measured, not crop-clipped."""

    left, top, right, bottom = calibration_witness_roi(witness_box)
    padding = CALIBRATION_ROI_PADDING_PX
    return (
        max(0, left - padding),
        max(0, top - padding),
        min(1920, right + padding),
        min(1080, bottom + padding),
    )


def calibration_roi_observation(
    path: Path,
    roi: tuple[int, int, int, int],
) -> JsonObject:
    """Return an exact ROI hash and a conservative visible-activity count."""

    try:
        from PIL import Image
    except ImportError as exc:
        raise RunnerError("Pillow is required for live tag measurement") from exc
    try:
        payload = path.resolve().read_bytes()
    except OSError as exc:
        raise RunnerError(f"cannot read monitor capture {path}: {exc}") from exc
    validate_png(payload, (1920, 1080))
    try:
        with Image.open(io.BytesIO(payload)) as source:
            crop = source.convert("RGBA").crop(roi)
            pixels = list(
                crop.get_flattened_data()
                if hasattr(crop, "get_flattened_data")
                else crop.getdata()
            )
            crop_bytes = crop.tobytes()
    except (OSError, ValueError) as exc:
        raise RunnerError(f"cannot decode monitor capture {path}: {exc}") from exc
    counts: dict[tuple[int, int, int, int], int] = {}
    for pixel in pixels:
        counts[pixel] = counts.get(pixel, 0) + 1
    dominant_count = max(counts.values(), default=0)
    return {
        "roi": list(roi),
        "roi_sha256": sha256_bytes(crop_bytes),
        "non_dominant_pixel_count": len(pixels) - dominant_count,
    }


def measure_calibration_ink(
    *,
    off_path: Path,
    state_paths: Mapping[str, Path],
    witness_box: Sequence[Any] | None,
) -> tuple[JsonObject, JsonObject]:
    """Measure per-state changed RGB ink against the off-state monitor frame."""

    try:
        from PIL import Image, ImageChops
    except ImportError as exc:
        raise RunnerError("Pillow is required for live tag measurement") from exc

    roi = calibration_capture_roi(witness_box)

    try:
        off_bytes = off_path.resolve().read_bytes()
    except OSError as exc:
        raise RunnerError(f"cannot read off-state capture {off_path}: {exc}") from exc
    validate_png(off_bytes, (1920, 1080))
    try:
        with Image.open(io.BytesIO(off_bytes)) as source:
            off_image = source.convert("RGB")
    except (OSError, ValueError) as exc:
        raise RunnerError(f"cannot decode off-state capture {off_path}: {exc}") from exc

    state_measurements: JsonObject = {}
    widths: list[int] = []
    heights: list[int] = []
    centroids_x: list[float] = []
    centroids_y: list[float] = []
    for state in ("minimum", "midpoint", "maximum"):
        path = state_paths.get(state)
        if path is None:
            raise RunnerError(f"missing calibration capture path for {state}")
        try:
            payload = path.resolve().read_bytes()
        except OSError as exc:
            raise RunnerError(f"cannot read {state} capture {path}: {exc}") from exc
        validate_png(payload, (1920, 1080))
        try:
            with Image.open(io.BytesIO(payload)) as source:
                current = source.convert("RGB")
        except (OSError, ValueError) as exc:
            raise RunnerError(f"cannot decode {state} capture {path}: {exc}") from exc
        baseline = off_image.crop(roi)
        current = current.crop(roi)
        difference = ImageChops.difference(current, baseline)
        changed: list[tuple[int, int]] = []
        width_px, height_px = difference.size
        difference_pixels = (
            difference.get_flattened_data()
            if hasattr(difference, "get_flattened_data")
            else difference.getdata()
        )
        for index, pixel in enumerate(difference_pixels):
            if any(int(channel) != 0 for channel in pixel):
                changed.append((index % width_px, index // width_px))
        changed_pixel_count = len(changed)
        if not changed:
            raise RunnerError(
                f"{state} monitor capture has no measurable ink change from off"
            )
        left = min(point[0] for point in changed)
        top = min(point[1] for point in changed)
        right = max(point[0] for point in changed) + 1
        bottom = max(point[1] for point in changed) + 1
        if left == 0 or top == 0 or right == width_px or bottom == height_px:
            raise RunnerError(f"{state} live tag ink touches the witness ROI edge")
        absolute = [
            left + roi[0],
            top + roi[1],
            right + roi[0],
            bottom + roi[1],
        ]
        width = int(right - left)
        height = int(bottom - top)
        minimum_width, minimum_height = MIN_MOVING_TAG_INK_PX
        if width < minimum_width or height < minimum_height:
            raise RunnerError(
                f"{state} live tag ink is only {width}x{height}; minimum readable "
                f"ink is {minimum_width}x{minimum_height}"
            )
        if changed_pixel_count < MIN_MOVING_TAG_CHANGED_PIXELS:
            raise RunnerError(
                f"{state} live tag changed only {changed_pixel_count} pixels; "
                f"minimum is {MIN_MOVING_TAG_CHANGED_PIXELS}"
            )
        target_width, target_height = MOVING_TAG_TARGET_PX
        if width > target_width or height > target_height:
            raise RunnerError(
                f"{state} live tag ink is {width}x{height}, exceeding "
                f"{target_width}x{target_height}"
            )
        centroid_x = roi[0] + sum(point[0] for point in changed) / changed_pixel_count
        centroid_y = roi[1] + sum(point[1] for point in changed) / changed_pixel_count
        widths.append(width)
        heights.append(height)
        centroids_x.append(centroid_x)
        centroids_y.append(centroid_y)
        state_measurements[state] = {
            "ink_bounds_px": absolute,
            "ink_box_px": [width, height],
            "changed_pixel_count": changed_pixel_count,
            "ink_centroid_px": [
                round(centroid_x, 3),
                round(centroid_y, 3),
            ],
        }

    if max(widths) - min(widths) > 1 or max(heights) - min(heights) > 1:
        raise RunnerError(
            "repeated live-tag stability captures disagree by more than one pixel"
        )
    if (
        max(centroids_x) - min(centroids_x)
        > MAX_MOVING_TAG_CENTROID_DRIFT_PX
        or max(centroids_y) - min(centroids_y)
        > MAX_MOVING_TAG_CENTROID_DRIFT_PX
    ):
        raise RunnerError(
            "repeated live-tag mask centroids drift by more than "
            f"{MAX_MOVING_TAG_CENTROID_DRIFT_PX:g} pixel"
        )
    envelope = [max(widths), max(heights)]
    metrics: JsonObject = {
        "vertical": {"ink_box_px": list(envelope)},
        # The prototype uses the same two-line Text Animator raster for the
        # horizontal tag; retaining the larger observed envelope is conservative.
        "horizontal": {"ink_box_px": list(envelope)},
    }
    return state_measurements, metrics


def text_value(parameter: Any) -> str:
    value = parameter_value(parameter)
    return "" if value is None else str(value)


def clip_is_connected(clip: Mapping[str, Any]) -> bool:
    return text_value(clip.get("connected")).casefold().startswith("connected")


def clip_trigger_style(clip: Mapping[str, Any]) -> str:
    return text_value(clip.get("triggerstyle"))


def composition_dimensions(composition: Mapping[str, Any]) -> tuple[int, int]:
    video = composition.get("video")
    if not isinstance(video, dict):
        raise RunnerError("composition has no video object")
    try:
        return (
            int(float(parameter_value(video["width"]))),
            int(float(parameter_value(video["height"]))),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RunnerError("composition dimensions are unavailable") from exc


def composition_fingerprint(composition: Mapping[str, Any]) -> JsonObject:
    layers = composition.get("layers")
    columns = composition.get("columns")
    if not isinstance(layers, list) or not isinstance(columns, list):
        raise RunnerError("composition has no layer/column arrays")
    width, height = composition_dimensions(composition)
    identity = {
        "name": text_value(composition.get("name")),
        "width": width,
        "height": height,
        "column_ids": [column.get("id") for column in columns],
        "layer_ids": [layer.get("id") for layer in layers],
        "clip_ids": [
            (layer.get("clips") or [{}])[0].get("id")
            if isinstance(layer.get("clips"), list)
            else None
            for layer in layers
        ],
    }
    return {"sha256": sha256_bytes(canonical_json(identity)), **identity}


def source_identity(clip: Mapping[str, Any]) -> JsonObject:
    video = clip.get("video")
    if not isinstance(video, dict):
        return {"present": False}
    sourceparams = video.get("sourceparams")
    effects = video.get("effects")
    fileinfo = video.get("fileinfo")
    path = fileinfo.get("path") if isinstance(fileinfo, dict) else None
    return {
        "present": True,
        "description": video.get("description"),
        "path": path,
        "source_parameters": sorted(
            (
                str(name),
                str(param.get("valuetype")),
            )
            for name, param in (sourceparams or {}).items()
            if isinstance(param, dict)
        ),
        "effects": [
            {
                "name": effect.get("name"),
                "display_name": effect.get("display_name"),
                "is_user_removable": effect.get("is_user_removable"),
                "parameters": sorted(
                    (str(name), str(param.get("valuetype")))
                    for name, param in (effect.get("params") or {}).items()
                    if isinstance(param, dict)
                ),
            }
            for effect in (effects or [])
            if isinstance(effect, dict)
        ],
    }


def _find_transform(clip: Mapping[str, Any]) -> Mapping[str, Any]:
    video = clip.get("video")
    effects = video.get("effects") if isinstance(video, dict) else None
    matches = [
        effect
        for effect in (effects or [])
        if isinstance(effect, dict)
        and (
            str(effect.get("name", "")).casefold() == "transform"
            or str(effect.get("display_name", "")).casefold() == "transform"
        )
        and effect.get("is_user_removable") is not True
    ]
    if len(matches) != 1:
        raise RunnerError(
            f"expected exactly one permanent Transform, found {len(matches)}"
        )
    return matches[0]


def capture_cc_detail(clip: Mapping[str, Any]) -> JsonObject:
    video = clip.get("video")
    if not isinstance(video, dict):
        raise RunnerError("continuous-control clip has no video track")
    sourceparams = video.get("sourceparams")
    if not isinstance(sourceparams, dict):
        raise RunnerError("continuous-control clip has no source parameters")
    transform = _find_transform(clip)
    transform_params = transform.get("params")
    if not isinstance(transform_params, dict):
        raise RunnerError("permanent Transform has no parameters")
    motion: JsonObject = {}
    for name in ("Position X", "Position Y", "Rotation Z"):
        parameter = transform_params.get(name)
        if not isinstance(parameter, dict) or parameter.get("valuetype") != "ParamRange":
            raise RunnerError(
                f"permanent Transform is missing ParamRange {name}"
            )
        motion[name] = parameter_state(parameter)
    opacity = video.get("opacity")
    if not isinstance(opacity, dict):
        raise RunnerError("continuous-control clip has no clip opacity")
    return {
        "identity": source_identity(clip),
        "clip_opacity": parameter_state(opacity),
        "source_parameter_evidence": {
            str(name): parameter_state(parameter)
            for name, parameter in sourceparams.items()
            if isinstance(parameter, dict) and "value" in parameter
        },
        "permanent_transform": {
            "name": transform.get("name"),
            "display_name": transform.get("display_name"),
            "effect_id_hint": transform.get("id"),
            "motion": motion,
        },
    }


def _require_snapshot_parameter_state(
    value: Any, *, label: str, valuetype: str | None = None
) -> None:
    if not isinstance(value, dict):
        raise RunnerError(f"snapshot {label} is not a parameter state")
    actual_type = value.get("valuetype")
    if not isinstance(actual_type, str) or not actual_type:
        raise RunnerError(f"snapshot {label} has no valuetype")
    if valuetype is not None and actual_type != valuetype:
        raise RunnerError(
            f"snapshot {label} valuetype is {actual_type}, expected {valuetype}"
        )
    if "value" not in value:
        raise RunnerError(f"snapshot {label} has no value")
    parameter_value_data = value["value"]
    if actual_type == "ParamRange" and (
        not isinstance(parameter_value_data, (int, float))
        or isinstance(parameter_value_data, bool)
        or not math.isfinite(float(parameter_value_data))
    ):
        raise RunnerError(f"snapshot {label} has a non-finite range value")
    if actual_type in {"ParamChoice", "ParamState"}:
        index = value.get("index")
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            raise RunnerError(f"snapshot {label} has an invalid choice index")
    hint = value.get("parameter_id_hint")
    if hint is not None and (
        not isinstance(hint, int) or isinstance(hint, bool) or hint <= 0
    ):
        raise RunnerError(f"snapshot {label} has an invalid parameter ID hint")


def _validate_snapshot_fingerprint(value: Any, expected_count: int) -> JsonObject:
    if not isinstance(value, dict):
        raise RunnerError("snapshot has no composition fingerprint")
    identity_keys = (
        "name",
        "width",
        "height",
        "column_ids",
        "layer_ids",
        "clip_ids",
    )
    identity = {key: value.get(key) for key in identity_keys}
    if not isinstance(identity["name"], str) or not identity["name"]:
        raise RunnerError("snapshot fingerprint has no composition name")
    if identity["width"] != 1920 or identity["height"] != 1080:
        raise RunnerError("snapshot fingerprint dimensions are not 1920x1080")
    if not isinstance(identity["column_ids"], list) or len(identity["column_ids"]) != 1:
        raise RunnerError("snapshot fingerprint must contain exactly one column")
    if (
        not isinstance(identity["layer_ids"], list)
        or len(identity["layer_ids"]) != expected_count
        or any(
            not isinstance(item, int) or isinstance(item, bool) or item <= 0
            for item in identity["layer_ids"]
        )
        or len(set(identity["layer_ids"])) != expected_count
    ):
        raise RunnerError("snapshot fingerprint layer IDs are incomplete or duplicate")
    if (
        not isinstance(identity["clip_ids"], list)
        or len(identity["clip_ids"]) != expected_count
        or any(
            not isinstance(item, int) or isinstance(item, bool) or item <= 0
            for item in identity["clip_ids"]
        )
        or len(set(identity["clip_ids"])) != expected_count
    ):
        raise RunnerError("snapshot fingerprint clip IDs are incomplete or duplicate")
    expected_hash = sha256_bytes(canonical_json(identity))
    if value.get("sha256") != expected_hash:
        raise RunnerError("snapshot composition fingerprint hash is invalid")
    return value


def _validate_snapshot_cc_detail(value: Any, layer: int) -> None:
    if not isinstance(value, dict):
        raise RunnerError(f"snapshot layer {layer} has no CC detail")
    if not isinstance(value.get("identity"), dict):
        raise RunnerError(f"snapshot layer {layer} has no source identity")
    _require_snapshot_parameter_state(
        value.get("clip_opacity"),
        label=f"layer {layer} clip opacity",
        valuetype="ParamRange",
    )
    source_evidence = value.get("source_parameter_evidence")
    if not isinstance(source_evidence, dict) or not source_evidence:
        raise RunnerError(f"snapshot layer {layer} has no source parameter evidence")
    for name, state in source_evidence.items():
        if not isinstance(name, str) or not name:
            raise RunnerError(f"snapshot layer {layer} has an invalid source parameter")
        _require_snapshot_parameter_state(
            state, label=f"layer {layer} source parameter {name}"
        )
    transform = value.get("permanent_transform")
    if not isinstance(transform, dict):
        raise RunnerError(f"snapshot layer {layer} has no permanent Transform")
    motion = transform.get("motion")
    if not isinstance(motion, dict) or set(motion) != {
        "Position X",
        "Position Y",
        "Rotation Z",
    }:
        raise RunnerError(f"snapshot layer {layer} has incomplete Transform motion")
    for name, state in motion.items():
        _require_snapshot_parameter_state(
            state,
            label=f"layer {layer} Transform {name}",
            valuetype="ParamRange",
        )


def validate_runtime_snapshot(value: Any, path: Path) -> JsonObject:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RunnerError(f"not a schema-version 1 runtime snapshot: {path}")
    if value.get("artifact_role") != "campaign_runtime_snapshot":
        raise RunnerError(f"not a campaign runtime snapshot: {path}")
    artifact_id = value.get("artifact_id")
    if not isinstance(artifact_id, str):
        raise RunnerError("snapshot has no artifact_id")
    try:
        uuid.UUID(artifact_id)
    except (ValueError, AttributeError) as exc:
        raise RunnerError("snapshot artifact_id is not a UUID") from exc
    if not isinstance(value.get("captured_at"), str) or not value["captured_at"]:
        raise RunnerError("snapshot has no captured_at timestamp")
    if not isinstance(value.get("build_id"), str) or not value["build_id"]:
        raise RunnerError("snapshot has no build_id")
    if value.get("restart_stage") not in STAGES:
        raise RunnerError("snapshot has an invalid restart_stage")
    active_path = value.get("active_preset_path")
    if (
        not isinstance(active_path, str)
        or not active_path
        or not Path(active_path).is_absolute()
    ):
        raise RunnerError("snapshot has no absolute active_preset_path")
    if not is_sha256(value.get("active_preset_sha256")):
        raise RunnerError("snapshot has no valid active_preset_sha256")
    expected_count = value.get("expected_layer_count")
    if expected_count not in (148, 149):
        raise RunnerError("snapshot expected_layer_count must be 148 or 149")
    _validate_snapshot_fingerprint(value.get("composition_fingerprint"), expected_count)
    clips = value.get("clips")
    if not isinstance(clips, list) or len(clips) != expected_count:
        raise RunnerError("snapshot clip count is internally inconsistent")
    for expected_layer, clip in enumerate(clips, 1):
        if not isinstance(clip, dict) or clip.get("layer") != expected_layer:
            raise RunnerError(
                f"snapshot clip sequence is invalid at layer {expected_layer}"
            )
        if not isinstance(clip.get("name"), str) or not clip["name"]:
            raise RunnerError(f"snapshot layer {expected_layer} has no clip name")
        if clip.get("trigger_style") not in {"Toggle", "Normal"}:
            raise RunnerError(
                f"snapshot layer {expected_layer} has invalid trigger style"
            )
        if not isinstance(clip.get("connected"), bool):
            raise RunnerError(
                f"snapshot layer {expected_layer} connected state is not boolean"
            )
        if not isinstance(clip.get("source_identity"), dict):
            raise RunnerError(
                f"snapshot layer {expected_layer} has no source identity"
            )
        if expected_layer in CC_LAYERS:
            _validate_snapshot_cc_detail(clip.get("cc_detail"), expected_layer)
        elif "cc_detail" in clip:
            raise RunnerError(
                f"snapshot non-CC layer {expected_layer} unexpectedly has CC detail"
            )
    return value


@dataclasses.dataclass(frozen=True)
class ProcessRecord:
    pid: int
    name: str
    executable_path: str
    command_line: str


class ProcessProvider(Protocol):
    def list_processes(self) -> list[ProcessRecord]:
        ...


class CimProcessProvider:
    """Read-only Win32_Process inventory through PowerShell CIM."""

    def list_processes(self) -> list[ProcessRecord]:
        command = (
            "Get-CimInstance Win32_Process | "
            "Select-Object ProcessId,Name,ExecutablePath,CommandLine | "
            "ConvertTo-Json -Compress"
        )
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
                creationflags=creation_flags,
            )
            raw = json.loads(completed.stdout or "[]")
        except (
            OSError,
            subprocess.SubprocessError,
            json.JSONDecodeError,
        ) as exc:
            raise RunnerError(f"cannot inventory runtime processes safely: {exc}") from exc
        rows = [raw] if isinstance(raw, dict) else raw
        result: list[ProcessRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            result.append(
                ProcessRecord(
                    pid=int(row.get("ProcessId") or 0),
                    name=str(row.get("Name") or ""),
                    executable_path=str(row.get("ExecutablePath") or ""),
                    command_line=str(row.get("CommandLine") or ""),
                )
            )
        return result


def validate_process_hygiene(processes: Sequence[ProcessRecord]) -> JsonObject:
    avenues = [
        process
        for process in processes
        if "avenue" in process.name.casefold()
        and "resolume" in (process.executable_path + process.command_line).casefold()
    ]
    bridges = [
        process
        for process in processes
        if "avenue_pipe_bridge.py" in process.command_line.casefold()
    ]
    watchers = [
        process
        for process in processes
        if "apc40_visual_qa_pulse.py" in process.command_line.casefold()
    ]
    mcp = [
        process
        for process in processes
        if "resolume" in process.command_line.casefold()
        and "mcp" in process.command_line.casefold()
    ]
    if len(avenues) != 1:
        raise RunnerError(
            f"expected exactly one Resolume Avenue process, found {len(avenues)}"
        )
    if len(bridges) != 1:
        raise RunnerError(f"expected exactly one Avenue bridge, found {len(bridges)}")
    if watchers:
        raise RunnerError(
            "pulse watcher must not run; found PIDs "
            + ",".join(str(process.pid) for process in watchers)
        )
    return {
        "avenue_pids": [process.pid for process in avenues],
        "bridge_pids": [process.pid for process in bridges],
        "watcher_pids": [],
        "mcp_pids_report_only": [process.pid for process in mcp],
    }


class LiveRunner:
    """Readback, evidence, and explicit restoration-gate coordinator."""

    def __init__(
        self,
        *,
        bridge: PipeHttpClient,
        native: PipeHttpClient | None,
        manifest_path: Path,
        journal_path: Path,
        lock_path: Path,
        calibration_recovery_path: Path | None = None,
        composition_name: str = DEFAULT_COMPOSITION_NAME,
        process_provider: ProcessProvider | None = None,
    ) -> None:
        self.bridge = bridge
        self.native = native
        self.manifest_path = manifest_path.resolve()
        self.journal = CampaignJournal(journal_path)
        self.lock_path = lock_path.resolve()
        recovery_path = (
            calibration_recovery_path
            if calibration_recovery_path is not None
            else Path(journal_path).with_name(
                "apc40_visual_qa_calibration_recovery.json"
            )
        )
        self.calibration_recovery = CalibrationRecoveryStore(
            recovery_path,
            self.journal,
        )
        self.composition_name = composition_name
        self.process_provider = process_provider or CimProcessProvider()

    def _json_get(
        self, path: str, *, client: PipeHttpClient | None = None
    ) -> Any:
        response = (client or self.bridge).get(path)
        return response.json()

    def composition(self) -> JsonObject:
        value = self._json_get("/api/v1/composition")
        if not isinstance(value, dict):
            raise RunnerError("composition response is not an object")
        return value

    def clip(self, layer: int) -> JsonObject:
        value = self._json_get(f"/api/v1/composition/layers/{int(layer)}/clips/1")
        if not isinstance(value, dict):
            raise RunnerError(f"layer {layer} clip response is not an object")
        return value

    def begin_calibration_recovery(
        self,
        *,
        layer: int,
        out: Path,
        original_states: Mapping[str, Mapping[str, Any]],
        expected_clip: Mapping[str, Any],
        current_fingerprint: Mapping[str, Any],
        active_preset: Path,
        active_preset_sha256: str,
        snapshot_path: Path,
        snapshot_sha256: str,
        snapshot: Mapping[str, Any],
        bundle: ArtifactBundle,
        parent_manifest_sha256: str,
        parent_artifact_hashes: Mapping[str, Mapping[str, Any]],
    ) -> str:
        """Persist exact recovery lineage before the first calibration PUT."""

        if layer != 94:
            raise RunnerError("calibration recovery may target only layer 94")
        transaction_id = str(uuid.uuid4())
        marker: JsonObject = {
            "schema_version": 1,
            "artifact_role": "live_calibration_recovery",
            "status": "active",
            "transaction_id": transaction_id,
            "created_at": utc_timestamp(),
            "build_id": bundle.build_id,
            "layer": layer,
            "measurement_out": str(out.resolve()),
            "original_states": {
                name: dict(original_states[name])
                for name in CALIBRATION_SOURCE_FIELD_TYPES
            },
            "clip_identity": {
                "clip_id_hint": expected_clip.get("clip_id_hint"),
                "name": expected_clip.get("name"),
                "trigger_style": expected_clip.get("trigger_style"),
                "source_identity": expected_clip.get("source_identity"),
            },
            "composition_fingerprint": dict(current_fingerprint),
            "active_preset": {
                "path": str(active_preset.resolve()),
                "sha256": active_preset_sha256,
            },
            "snapshot": {
                "path": str(snapshot_path.resolve()),
                "sha256": snapshot_sha256,
                "artifact_id": snapshot.get("artifact_id"),
                "restart_stage": snapshot.get("restart_stage"),
            },
            "artifact_lineage": {
                "repo_root": str(bundle.repo_root),
                "manifest_path": str(bundle.manifest_path),
                "manifest_sha256": parent_manifest_sha256,
                "parent_artifact_hashes": {
                    key: dict(metadata)
                    for key, metadata in parent_artifact_hashes.items()
                },
            },
            "events": [],
        }
        self.calibration_recovery.begin(marker)
        return transaction_id

    def _calibration_transaction_put(
        self,
        transaction_id: str,
        parameter: Mapping[str, Any],
        *,
        value: Any,
        expected_state: Mapping[str, Any] | None,
        label: str,
        phase: str,
        parameter_name: str,
    ) -> JsonObject:
        """Journal intent before one PUT and verified readback immediately after it."""

        parameter_id = int(parameter["id"])
        intent_error: BaseException | None = None
        try:
            intent = self.calibration_recovery.append(
                transaction_id,
                {
                    "kind": "parameter_write_intent",
                    "phase": phase,
                    "parameter": parameter_name,
                    "parameter_id": parameter_id,
                    "valuetype": str(parameter["valuetype"]),
                    "value": value,
                },
            )
        except BaseException as exc:
            if phase not in {"rollback", "recovery"}:
                raise
            # Once any apply PUT may have landed, restoration takes precedence
            # over progress publication. The still-active marker remains the
            # fail-closed recovery authority.
            intent_error = exc
            intent = {"sequence": None}
        try:
            actual = self._put_parameter_value(
                parameter,
                value=value,
                expected_state=expected_state,
                label=label,
            )
        except BaseException as exc:
            with contextlib.suppress(BaseException):
                self.calibration_recovery.append(
                    transaction_id,
                    {
                        "kind": "parameter_write_error",
                        "phase": phase,
                        "parameter": parameter_name,
                        "parameter_id": parameter_id,
                        "intent_sequence": intent["sequence"],
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "ambiguous": (
                            exc.ambiguous
                            if isinstance(exc, PipeTransportError)
                            else None
                        ),
                    },
                )
            raise
        try:
            self.calibration_recovery.append(
                transaction_id,
                {
                    "kind": "parameter_write_verified",
                    "phase": phase,
                    "parameter": parameter_name,
                    "parameter_id": parameter_id,
                    "intent_sequence": intent["sequence"],
                    "readback": actual,
                },
            )
        except BaseException:
            if intent_error is None:
                raise
        if intent_error is not None:
            raise RunnerError(
                f"{label} was restored, but its recovery intent could not be "
                f"persisted: {intent_error}"
            ) from intent_error
        return actual

    def recover_calibration(
        self,
        *,
        active_preset: Path,
        dry_run: bool = False,
    ) -> JsonObject:
        """Exactly restore one interrupted layer-94 calibration after all gates pass."""

        marker = self.calibration_recovery.load()
        assert marker is not None
        transaction_id = str(marker["transaction_id"])
        if marker["layer"] != 94:
            raise RunnerError("calibration recovery marker targets the wrong layer")

        expected_active = marker["active_preset"]
        active_preset = active_preset.resolve()
        if str(active_preset) != expected_active["path"]:
            raise RunnerError("calibration recovery active preset path does not match")
        if sha256_file(active_preset) != expected_active["sha256"]:
            raise RunnerError("calibration recovery active preset hash does not match")

        composition = self.composition()
        layers = composition.get("layers")
        if not isinstance(layers, list) or len(layers) != 148:
            raise RunnerError("calibration recovery requires exactly 148 live layers")
        fingerprint = composition_fingerprint(composition)
        if canonical_json(fingerprint) != canonical_json(
            marker["composition_fingerprint"]
        ):
            raise RunnerError(
                "calibration recovery composition fingerprint does not match"
            )

        snapshot_lineage = marker["snapshot"]
        snapshot_path = Path(snapshot_lineage["path"]).resolve()
        snapshot, snapshot_sha256 = self._load_snapshot(snapshot_path)
        if (
            snapshot_sha256 != snapshot_lineage["sha256"]
            or snapshot["artifact_id"] != snapshot_lineage["artifact_id"]
            or snapshot["restart_stage"] != snapshot_lineage["restart_stage"]
            or snapshot["build_id"] != marker["build_id"]
            or snapshot["active_preset_path"] != expected_active["path"]
            or snapshot["active_preset_sha256"] != expected_active["sha256"]
            or snapshot["composition_fingerprint"]["sha256"]
            != fingerprint["sha256"]
        ):
            raise RunnerError("calibration recovery snapshot lineage does not match")

        artifact_lineage = marker["artifact_lineage"]
        bundle = ArtifactBundle.verify(
            Path(artifact_lineage["manifest_path"]),
            Path(artifact_lineage["repo_root"]),
        )
        if (
            bundle.build_id != marker["build_id"]
            or bundle.status != "provisional"
            or sha256_file(bundle.manifest_path)
            != artifact_lineage["manifest_sha256"]
            or measurement_parent_artifact_hashes(bundle)
            != artifact_lineage["parent_artifact_hashes"]
        ):
            raise ArtifactError(
                "calibration recovery provisional artifact lineage does not match"
            )

        clip = self.clip(94)
        self._require_calibration_clip_identity(clip, marker["clip_identity"])
        parameters = self._calibration_source_parameters(clip)
        original_states = marker["original_states"]
        current_states: dict[str, JsonObject] = {}
        for name, valuetype in CALIBRATION_SOURCE_FIELD_TYPES.items():
            parameter_id = int(parameters[name]["id"])
            if parameter_id != original_states[name]["parameter_id_hint"]:
                raise RunnerError(
                    f"calibration recovery parameter ID changed for {name}"
                )
            current_states[name] = self._read_parameter_state(
                parameter_id,
                valuetype=valuetype,
                label=f"layer 94 recovery {name}",
            )

        pending_restore = [
            name
            for name in reversed(tuple(CALIBRATION_SOURCE_FIELD_TYPES))
            if not parameter_states_equal(
                current_states[name],
                original_states[name],
            )
        ]
        if dry_run:
            return {
                "transaction_id": transaction_id,
                "layer": 94,
                "build_id": marker["build_id"],
                "dry_run": True,
                "recovery_marker": str(self.calibration_recovery.path),
                "would_restore_parameters": pending_restore,
                "write_count": len(pending_restore),
                "composition_fingerprint": fingerprint["sha256"],
            }

        restored: list[str] = []
        for name in pending_restore:
            original = original_states[name]
            self._calibration_transaction_put(
                transaction_id,
                parameters[name],
                value=original["value"],
                expected_state=original,
                label=f"layer 94 interrupted calibration recovery {name}",
                phase="recovery",
                parameter_name=name,
            )
            restored.append(name)

        final_clip = self.clip(94)
        self._require_calibration_clip_identity(
            final_clip,
            marker["clip_identity"],
        )
        final_parameters = self._calibration_source_parameters(final_clip)
        for name, valuetype in CALIBRATION_SOURCE_FIELD_TYPES.items():
            if int(final_parameters[name]["id"]) != original_states[name][
                "parameter_id_hint"
            ]:
                raise RunnerError(
                    f"calibration recovery final parameter ID changed for {name}"
                )
            final_state = self._read_parameter_state(
                int(final_parameters[name]["id"]),
                valuetype=valuetype,
                label=f"layer 94 recovery final {name}",
            )
            if not parameter_states_equal(final_state, original_states[name]):
                raise RunnerError(
                    f"calibration recovery did not restore {name}"
                )

        final_fingerprint = composition_fingerprint(self.composition())
        if canonical_json(final_fingerprint) != canonical_json(fingerprint):
            raise RunnerError(
                "calibration recovery composition changed during restoration"
            )
        if (
            sha256_file(active_preset) != expected_active["sha256"]
            or sha256_file(snapshot_path) != snapshot_lineage["sha256"]
            or sha256_file(bundle.manifest_path)
            != artifact_lineage["manifest_sha256"]
            or measurement_parent_artifact_hashes(bundle)
            != artifact_lineage["parent_artifact_hashes"]
        ):
            raise RunnerError(
                "calibration recovery lineage changed during restoration"
            )

        result: JsonObject = {
            "transaction_id": transaction_id,
            "layer": 94,
            "build_id": marker["build_id"],
            "dry_run": False,
            "restored_parameters": restored,
            "restore_count": len(restored),
            "final_composition_fingerprint": final_fingerprint["sha256"],
        }
        self.calibration_recovery.commit(transaction_id, result)
        return result

    def preflight(
        self,
        *,
        stage: str,
        expected_layer_count: int | None = None,
        active_preset: Path | None = None,
        validate_controls: bool = True,
        allow_calibration_recovery: bool = False,
    ) -> JsonObject:
        if stage not in STAGES:
            raise RunnerError(f"unknown preflight stage: {stage}")
        if not allow_calibration_recovery:
            recovery = self.calibration_recovery.load(required=False)
            if recovery is not None:
                raise RunnerError(
                    "incomplete calibration transaction "
                    f"{recovery['transaction_id']} requires `recover-calibration` "
                    f"before any other live operation: "
                    f"{self.calibration_recovery.path}"
                )
        process_info = validate_process_hygiene(
            self.process_provider.list_processes()
        )

        active_preset_path: str | None = None
        active_preset_sha256: str | None = None
        if active_preset is not None:
            resolved_preset = active_preset.resolve()
            try:
                preset_bytes = resolved_preset.read_bytes()
            except OSError as exc:
                raise RunnerError(
                    f"active preset is unreadable: {resolved_preset}: {exc}"
                ) from exc
            active_preset_path = str(resolved_preset)
            active_preset_sha256 = sha256_bytes(preset_bytes)

        if self.native is None:
            raise RunnerError("native Avenue pipe client is required for preflight")
        native_product = self._json_get("/api/v1/product", client=self.native)
        if not isinstance(native_product, dict) or str(
            native_product.get("name", "")
        ).casefold() != "avenue":
            raise RunnerError("native pipe did not identify Resolume Avenue")
        bridge_product = self._json_get("/api/v1/product")
        if not isinstance(bridge_product, dict) or str(
            bridge_product.get("name", "")
        ).casefold() != "avenue":
            raise RunnerError("bridge pipe did not identify Resolume Avenue")

        composition = self.composition()
        layers = composition.get("layers")
        columns = composition.get("columns")
        if not isinstance(layers, list) or not isinstance(columns, list):
            raise RunnerError("composition lacks layer/column arrays")
        if text_value(composition.get("name")) != self.composition_name:
            raise RunnerError(
                f"wrong composition: {text_value(composition.get('name'))!r}"
            )
        if composition_dimensions(composition) != (1920, 1080):
            raise RunnerError("composition must be 1920x1080")
        if len(columns) != 1:
            raise RunnerError(f"composition must have one column, found {len(columns)}")
        if expected_layer_count is not None and len(layers) != expected_layer_count:
            raise RunnerError(
                f"expected {expected_layer_count} layers, found {len(layers)}"
            )

        validation = {"skipped": True}
        if validate_controls:
            validation = self._validate_manifest_controls(composition)
        return {
            "schema_version": 1,
            "stage": stage,
            "timestamp": utc_timestamp(),
            "processes": process_info,
            "native_product": native_product,
            "bridge_product": bridge_product,
            "expected_layer_count": expected_layer_count,
            "actual_layer_count": len(layers),
            "active_preset_path": active_preset_path,
            "active_preset_sha256": active_preset_sha256,
            "composition_fingerprint": composition_fingerprint(composition),
            "control_validation": validation,
        }

    def _validate_manifest_controls(
        self, composition: Mapping[str, Any]
    ) -> JsonObject:
        manifest = load_json(self.manifest_path)
        if not isinstance(manifest, list) or len(manifest) != 148:
            raise RunnerError("manifest must contain exactly 148 controls")
        layers = composition.get("layers")
        if not isinstance(layers, list) or len(layers) < 148:
            raise RunnerError("composition has fewer than 148 control layers")
        for index, record in enumerate(manifest, 1):
            if not isinstance(record, dict) or int(record.get("layer", 0)) != index:
                raise RunnerError(f"manifest layer sequence breaks at {index}")
            layer = layers[index - 1]
            if text_value(layer.get("name")) != record.get("layer_name"):
                raise RunnerError(f"layer {index} name does not match manifest")
            clips = layer.get("clips")
            if not isinstance(clips, list) or len(clips) != 1:
                raise RunnerError(f"layer {index} must contain exactly one clip")
            clip = clips[0]
            if text_value(clip.get("name")) != record.get("midi_label"):
                raise RunnerError(f"layer {index} clip name does not match manifest")
            expected_style = "Toggle" if record.get("midi_type") == "note" else "Normal"
            if clip_trigger_style(clip).casefold() != expected_style.casefold():
                raise RunnerError(
                    f"layer {index} trigger style is not {expected_style}"
                )
        return {"layers": 148, "names": "exact", "trigger_styles": "exact"}

    def _require_overlay_claim(
        self, composition: Mapping[str, Any], build_id: str
    ) -> JsonObject:
        layers = composition.get("layers")
        if not isinstance(layers, list) or len(layers) != 149:
            raise RunnerError("overlay claim requires exactly 149 live layers")
        fingerprint = composition_fingerprint(composition)
        expected = {
            "kind": "overlay_claimed",
            "build_id": build_id,
            "composition_fingerprint": fingerprint["sha256"],
            "expected_layer_count": 149,
            "original_layer_ids": [layer.get("id") for layer in layers[:148]],
            "overlay_layer_id": layers[148].get("id"),
        }
        matches = [
            record
            for record in self.journal.records()
            if all(record.get(key) == item for key, item in expected.items())
        ]
        if len(matches) != 1:
            raise RunnerError(
                "149-layer composition lacks one exact journal-owned overlay claim "
                f"for build {build_id!r}"
            )
        return matches[0]

    def _require_snapshot_publication(
        self,
        snapshot_path: Path,
        snapshot_hash: str,
        snapshot: Mapping[str, Any],
    ) -> JsonObject:
        expected = {
            "kind": "campaign_snapshot_published",
            "snapshot": str(snapshot_path.resolve()),
            "snapshot_sha256": snapshot_hash,
            "artifact_id": snapshot["artifact_id"],
            "build_id": snapshot["build_id"],
            "restart_stage": snapshot["restart_stage"],
            "active_preset_path": snapshot["active_preset_path"],
            "active_preset_sha256": snapshot["active_preset_sha256"],
            "expected_layer_count": snapshot["expected_layer_count"],
            "composition_fingerprint": snapshot["composition_fingerprint"]["sha256"],
        }
        matches = [
            record
            for record in self.journal.records()
            if all(record.get(key) == item for key, item in expected.items())
        ]
        if len(matches) != 1:
            raise RunnerError(
                "snapshot lacks one exact publication record in the campaign journal"
            )
        return matches[0]

    def snapshot_controls(
        self,
        *,
        out: Path,
        restart_stage: str,
        build_id: str,
        active_preset_path: Path,
        active_preset_sha256: str,
        dry_run: bool,
    ) -> JsonObject:
        if restart_stage not in STAGES:
            raise RunnerError(f"invalid snapshot restart stage: {restart_stage}")
        if not isinstance(build_id, str) or not build_id:
            raise RunnerError("campaign snapshot requires a nonempty build_id")
        if not is_sha256(active_preset_sha256):
            raise RunnerError(
                "campaign snapshot requires the verified active preset SHA-256"
            )
        normalized_active_preset_sha256 = active_preset_sha256.lower()
        try:
            current_preset_hash = sha256_bytes(active_preset_path.resolve().read_bytes())
        except OSError as exc:
            raise RunnerError(
                f"campaign snapshot active preset is unreadable: {exc}"
            ) from exc
        if current_preset_hash != normalized_active_preset_sha256:
            raise RunnerError("active preset changed between preflight and snapshot")
        composition = self.composition()
        layers = composition.get("layers")
        if not isinstance(layers, list) or len(layers) not in (148, 149):
            raise RunnerError("campaign snapshot requires exactly 148 or 149 layers")
        if len(layers) == 149:
            self._require_overlay_claim(composition, build_id)
        clips: list[JsonObject] = []
        for index in range(1, len(layers) + 1):
            clip = self.clip(index)
            item: JsonObject = {
                "layer": index,
                "clip_id_hint": clip.get("id"),
                "name": text_value(clip.get("name")),
                "trigger_style": clip_trigger_style(clip),
                "connected": clip_is_connected(clip),
                "source_identity": source_identity(clip),
            }
            if index in CC_LAYERS:
                item["cc_detail"] = capture_cc_detail(clip)
            clips.append(item)
        result: JsonObject = {
            "schema_version": 1,
            "artifact_role": "campaign_runtime_snapshot",
            "artifact_id": None if dry_run else str(uuid.uuid4()),
            "captured_at": utc_timestamp(),
            "build_id": build_id,
            "restart_stage": restart_stage,
            "active_preset_path": str(active_preset_path.resolve()),
            "active_preset_sha256": normalized_active_preset_sha256,
            "expected_layer_count": len(layers),
            "composition_fingerprint": composition_fingerprint(composition),
            "clips": clips,
        }
        if not dry_run:
            atomic_write_json(out, result)
            self.journal.append(
                {
                    "kind": "campaign_snapshot_published",
                    "snapshot": str(out.resolve()),
                    "snapshot_sha256": sha256_file(out.resolve()),
                    "artifact_id": result["artifact_id"],
                    "build_id": result["build_id"],
                    "restart_stage": result["restart_stage"],
                    "active_preset_path": result["active_preset_path"],
                    "active_preset_sha256": result["active_preset_sha256"],
                    "expected_layer_count": result["expected_layer_count"],
                    "composition_fingerprint": result["composition_fingerprint"][
                        "sha256"
                    ],
                }
            )
        return result

    def _load_snapshot(self, snapshot_path: Path) -> tuple[JsonObject, str]:
        snapshot_path = snapshot_path.resolve()
        try:
            payload = snapshot_path.read_bytes()
        except OSError as exc:
            raise RunnerError(f"cannot read snapshot {snapshot_path}: {exc}") from exc
        value = json_from_bytes(payload, snapshot_path)
        snapshot = validate_runtime_snapshot(value, snapshot_path)
        snapshot_hash = sha256_bytes(payload)
        self._require_snapshot_publication(snapshot_path, snapshot_hash, snapshot)
        return snapshot, snapshot_hash

    def restore_snapshot_gate(
        self,
        *,
        snapshot_path: Path,
        supplied_gate: str | None,
        active_preset: Path,
        dry_run: bool,
    ) -> JsonObject:
        """Validate exact restore identity and establish/consume an eject gate.

        Parameter restoration is deliberately not performed here until its
        staged live pilot validates the complete API shape.  This method still
        prevents unsafe broad inverses and handles the exact manual gate.
        """

        snapshot_path = snapshot_path.resolve()
        snapshot, snapshot_hash = self._load_snapshot(snapshot_path)
        if str(active_preset.resolve()) != snapshot["active_preset_path"]:
            raise RunnerError("snapshot active preset path does not match the live preset")
        try:
            current_preset_hash = sha256_bytes(active_preset.resolve().read_bytes())
        except OSError as exc:
            raise RunnerError(f"active preset is unreadable: {active_preset}: {exc}") from exc
        if current_preset_hash != snapshot["active_preset_sha256"]:
            raise RunnerError("snapshot active preset hash does not match the live preset")
        composition = self.composition()
        current_fingerprint = composition_fingerprint(composition)
        expected_fingerprint = snapshot.get("composition_fingerprint")
        if not isinstance(expected_fingerprint, dict):
            raise RunnerError("snapshot has no composition fingerprint")
        if current_fingerprint["sha256"] != expected_fingerprint.get("sha256"):
            raise RunnerError("snapshot composition fingerprint does not match live state")
        if snapshot["expected_layer_count"] == 149:
            self._require_overlay_claim(composition, snapshot["build_id"])

        expected_clips = snapshot["clips"]
        needs_eject: list[int] = []
        reconnect: list[int] = []
        current_cc_details: dict[int, JsonObject] = {}
        for expected in expected_clips:
            layer = int(expected["layer"])
            current = self.clip(layer)
            if expected.get("name") != text_value(current.get("name")):
                raise RunnerError(f"layer {layer} clip identity drifted")
            if expected["trigger_style"] != clip_trigger_style(current):
                raise RunnerError(f"layer {layer} trigger style drifted")
            if canonical_json(expected["source_identity"]) != canonical_json(
                source_identity(current)
            ):
                raise RunnerError(f"layer {layer} source/effect identity drifted")
            expected_connected = expected["connected"]
            current_connected = clip_is_connected(current)
            if not expected_connected and current_connected:
                needs_eject.append(layer)
            elif expected_connected and not current_connected:
                reconnect.append(layer)
            if layer in CC_LAYERS:
                current_cc_details[layer] = capture_cc_detail(current)

        parameter_requests: list[JsonObject] = []
        for layer in sorted(CC_LAYERS):
            expected_detail = expected_clips[layer - 1]["cc_detail"]
            current_detail = current_cc_details[layer]
            for target, parameter_name in mapped_cc_fields(layer):
                if target == "clip_opacity":
                    expected_state = expected_detail["clip_opacity"]
                    current_state = current_detail["clip_opacity"]
                else:
                    expected_state = expected_detail["permanent_transform"]["motion"][
                        parameter_name
                    ]
                    current_state = current_detail["permanent_transform"]["motion"][
                        parameter_name
                    ]
                if canonical_json(expected_state["value"]) == canonical_json(
                    current_state["value"]
                ):
                    continue
                parameter_requests.append(
                    {
                        "method": "PUT",
                        "path_template": (
                            "/api/v1/parameter/by-id/"
                            "{rediscovered_parameter_id}"
                        ),
                        "layer": layer,
                        "target": target,
                        "parameter": parameter_name,
                        "valuetype": expected_state["valuetype"],
                        "json": {"value": expected_state["value"]},
                    }
                )

        plan = {
            "snapshot": str(snapshot_path),
            "snapshot_sha256": snapshot_hash,
            "composition_fingerprint": current_fingerprint["sha256"],
            "manual_eject_layers": sorted(needs_eject),
            "connect_layers": sorted(reconnect),
            "cc_parameter_layers": sorted(CC_LAYERS),
            "cc_parameter_restore_layers": sorted(
                {int(request["layer"]) for request in parameter_requests}
            ),
            "write_limit_per_wave": MAX_WRITES_PER_WAVE,
            "requests": [
                {
                    "method": "POST",
                    "path": (
                        f"/api/v1/composition/layers/{layer}/clips/1/connect"
                    ),
                    "reason": "restore connected snapshot state",
                }
                for layer in sorted(reconnect)
            ]
            + parameter_requests,
            "request_count": len(reconnect) + len(parameter_requests),
            "dry_run": dry_run,
        }

        matching_created = [
            record
            for record in self.journal.records()
            if record.get("kind") == "manual_gate_created"
            and record.get("snapshot") == str(snapshot_path)
            and record.get("snapshot_sha256") == snapshot_hash
            and record.get("composition_fingerprint") == current_fingerprint["sha256"]
        ]
        if supplied_gate is None and matching_created:
            gate_ids = sorted(str(record.get("gate_id")) for record in matching_created)
            raise RunnerError(
                "an explicit --gate is required for this snapshot; matching gates: "
                + ",".join(gate_ids)
            )

        if supplied_gate is not None:
            created, verified = self.journal.gate(supplied_gate)
            created_layers = created.get("layers")
            if not isinstance(created_layers, list) or any(
                not isinstance(layer, int) or isinstance(layer, bool)
                for layer in created_layers
            ):
                raise RunnerError(f"manual gate {supplied_gate} has invalid layers")
            if (
                created_layers != sorted(set(created_layers))
                or any(
                    layer < 1 or layer > snapshot["expected_layer_count"]
                    for layer in created_layers
                )
                or not created_layers
            ):
                raise RunnerError(
                    f"manual gate {supplied_gate} layer set is not exact"
                )
            self._validate_gate_record(
                created,
                supplied_gate,
                snapshot_path,
                snapshot_hash,
                current_fingerprint["sha256"],
                created_layers,
            )
            if verified is None:
                raise ManualActionRequired(
                    gate_id=supplied_gate,
                    snapshot=snapshot_path,
                    layers=created_layers,
                )
            self._validate_gate_record(
                verified,
                supplied_gate,
                snapshot_path,
                snapshot_hash,
                current_fingerprint["sha256"],
                created_layers,
            )
            if verified.get("dry_run") is not False or not isinstance(
                verified.get("evidence"), dict
            ):
                raise RunnerError(
                    f"manual gate {supplied_gate} lacks published visual evidence"
                )
            evidence = verified["evidence"]
            evidence_path = Path(str(evidence.get("path", ""))).resolve()
            try:
                evidence_bytes = evidence_path.read_bytes()
            except OSError as exc:
                raise RunnerError(
                    f"manual gate evidence is unreadable: {evidence_path}: {exc}"
                ) from exc
            if sha256_bytes(evidence_bytes) != evidence.get("png_sha256"):
                raise RunnerError(
                    f"manual gate evidence hash drifted: {evidence_path}"
                )
            validate_png(evidence_bytes, (1920, 1080))
            still_connected = [
                layer for layer in created_layers if clip_is_connected(self.clip(layer))
            ]
            if still_connected:
                raise RunnerError(
                    "verified gate no longer matches live state; connected layers: "
                    + ",".join(map(str, still_connected))
                )
            if needs_eject:
                raise RunnerError(
                    "verified gate does not cover current connected layers: "
                    + ",".join(map(str, sorted(needs_eject)))
                )
            plan["manual_gate"] = supplied_gate
            plan["manual_eject_layers"] = []
        elif needs_eject:
            if dry_run:
                plan["manual_gate_required"] = True
                return plan
            gate_id = str(uuid.uuid4())
            self.journal.append(
                {
                    "kind": "manual_gate_created",
                    "gate_id": gate_id,
                    "snapshot": str(snapshot_path),
                    "snapshot_sha256": snapshot_hash,
                    "composition_fingerprint": current_fingerprint["sha256"],
                    "layers": sorted(needs_eject),
                }
            )
            raise ManualActionRequired(
                gate_id=gate_id, snapshot=snapshot_path, layers=needs_eject
            )

        if not dry_run:
            raise LiveMutationNotValidated(
                "snapshot identity and any manual gate passed, but live "
                "parameter/connect restoration remains disabled until staged writes "
                "are validated"
            )
        return plan

    @staticmethod
    def _validate_gate_record(
        record: Mapping[str, Any],
        gate_id: str,
        snapshot: Path,
        snapshot_hash: str,
        fingerprint: str,
        layers: Sequence[int],
    ) -> None:
        expected = {
            "gate_id": gate_id,
            "snapshot": str(snapshot.resolve()),
            "snapshot_sha256": snapshot_hash,
            "composition_fingerprint": fingerprint,
            "layers": sorted(int(layer) for layer in layers),
        }
        for key, value in expected.items():
            if record.get(key) != value:
                raise RunnerError(f"manual gate {gate_id} does not match {key}")

    def manual_eject_check(
        self,
        *,
        snapshot_path: Path,
        gate_id: str,
        layers: Sequence[int],
        evidence_out: Path,
        active_preset: Path,
        dry_run: bool,
    ) -> JsonObject:
        snapshot_path = snapshot_path.resolve()
        snapshot, snapshot_hash = self._load_snapshot(snapshot_path)
        if str(active_preset.resolve()) != snapshot["active_preset_path"]:
            raise RunnerError("manual gate active preset path does not match snapshot")
        try:
            active_hash = sha256_bytes(active_preset.resolve().read_bytes())
        except OSError as exc:
            raise RunnerError(f"active preset is unreadable: {active_preset}: {exc}") from exc
        if active_hash != snapshot["active_preset_sha256"]:
            raise RunnerError("manual gate active preset does not match snapshot")
        created, verified = self.journal.gate(gate_id)
        requested_layers = sorted(set(int(layer) for layer in layers))
        composition = self.composition()
        fingerprint = composition_fingerprint(composition)
        if fingerprint["sha256"] != snapshot["composition_fingerprint"]["sha256"]:
            raise RunnerError("manual gate composition does not match snapshot")
        if snapshot["expected_layer_count"] == 149:
            self._require_overlay_claim(composition, snapshot["build_id"])
        self._validate_gate_record(
            created,
            gate_id,
            snapshot_path,
            snapshot_hash,
            fingerprint["sha256"],
            requested_layers,
        )
        if verified is not None:
            raise RunnerError(f"manual gate is already verified: {gate_id}")
        connected = [
            layer for layer in requested_layers if clip_is_connected(self.clip(layer))
        ]
        if connected:
            raise RunnerError(
                "targeted eject is not complete; still connected: "
                + ",".join(map(str, connected))
            )
        capture = self.capture_monitor(
            monitor_name="Composition", out=evidence_out, dry_run=dry_run
        )
        result = {
            "gate_id": gate_id,
            "snapshot": str(snapshot_path),
            "snapshot_sha256": snapshot_hash,
            "composition_fingerprint": fingerprint["sha256"],
            "layers": requested_layers,
            "evidence": capture,
            "dry_run": dry_run,
        }
        if not dry_run:
            self.journal.append({"kind": "manual_gate_verified", **result})
        return result

    def _read_parameter_state(
        self,
        parameter_id: int,
        *,
        valuetype: str,
        label: str,
    ) -> JsonObject:
        value = self._json_get(f"/api/v1/parameter/by-id/{parameter_id}")
        if not isinstance(value, dict):
            raise RunnerError(f"{label} parameter readback is not an object")
        returned_id = value.get("id")
        if returned_id is not None and returned_id != parameter_id:
            raise RunnerError(
                f"{label} parameter readback ID {returned_id!r} != {parameter_id}"
            )
        state = parameter_state(value)
        _require_snapshot_parameter_state(
            state,
            label=f"{label} readback",
            valuetype=valuetype,
        )
        return state

    @staticmethod
    def _calibration_source_parameters(
        clip: Mapping[str, Any],
    ) -> dict[str, Mapping[str, Any]]:
        video = clip.get("video")
        if not isinstance(video, dict) or video.get("description") != "Text Animator":
            raise RunnerError("layer 94 must contain exactly one Text Animator source")
        # Even though calibration never writes it, requiring the unique permanent
        # Transform preserves the compound prototype identity from the snapshot.
        _find_transform(clip)
        sourceparams = video.get("sourceparams")
        if not isinstance(sourceparams, dict):
            raise RunnerError("layer 94 Text Animator has no source parameters")
        result: dict[str, Mapping[str, Any]] = {}
        for name, valuetype in CALIBRATION_SOURCE_FIELD_TYPES.items():
            parameter = sourceparams.get(name)
            if not isinstance(parameter, dict):
                raise RunnerError(f"layer 94 source is missing exact parameter {name}")
            if parameter.get("valuetype") != valuetype:
                raise RunnerError(
                    f"layer 94 source {name} is {parameter.get('valuetype')}, "
                    f"expected {valuetype}"
                )
            parameter_id = parameter.get("id")
            if (
                not isinstance(parameter_id, int)
                or isinstance(parameter_id, bool)
                or parameter_id <= 0
            ):
                raise RunnerError(f"layer 94 source {name} has no live parameter ID")
            result[name] = parameter
        return result

    def _put_parameter_value(
        self,
        parameter: Mapping[str, Any],
        *,
        value: Any,
        expected_state: Mapping[str, Any] | None,
        label: str,
    ) -> JsonObject:
        parameter_id = int(parameter["id"])
        valuetype = str(parameter["valuetype"])
        self.bridge.put(
            f"/api/v1/parameter/by-id/{parameter_id}",
            json_body={"value": value},
        )
        actual = self._read_parameter_state(
            parameter_id,
            valuetype=valuetype,
            label=label,
        )
        if expected_state is None:
            if not parameter_values_equal(valuetype, actual.get("value"), value):
                raise RunnerError(
                    f"{label} readback {actual.get('value')!r} != {value!r}"
                )
        elif not parameter_states_equal(actual, expected_state):
            raise RunnerError(
                f"{label} restoration readback does not match captured state"
            )
        return actual

    @staticmethod
    def _require_calibration_clip_identity(
        current: Mapping[str, Any],
        expected: Mapping[str, Any],
    ) -> None:
        if current.get("id") != expected.get("clip_id_hint"):
            raise RunnerError("layer 94 clip ID does not match the same-session snapshot")
        if text_value(current.get("name")) != expected.get("name"):
            raise RunnerError("layer 94 clip name drifted from the snapshot")
        if clip_trigger_style(current) != expected.get("trigger_style"):
            raise RunnerError("layer 94 trigger style drifted from the snapshot")
        if canonical_json(source_identity(current)) != canonical_json(
            expected.get("source_identity")
        ):
            raise RunnerError("layer 94 source/effect identity drifted from the snapshot")

    def _require_calibration_visible_eligibility(
        self,
        *,
        current: Mapping[str, Any],
        expected: Mapping[str, Any],
        original_text: Mapping[str, Any],
        desired_text: Any,
    ) -> JsonObject:
        if expected.get("connected") is not True or not clip_is_connected(current):
            raise RunnerError(
                "layer 94 must be connected in both the snapshot and live state "
                "before calibration"
            )
        if not isinstance(original_text.get("value"), str) or not str(
            original_text["value"]
        ).strip():
            raise RunnerError("layer 94 original Text is blank and not visibly eligible")
        if not isinstance(desired_text, str) or not desired_text.strip():
            raise ArtifactError("layer 94 desired Text must be nonempty")

        video = current.get("video")
        if not isinstance(video, dict):
            raise RunnerError("layer 94 has no video track")
        clip_opacity = video.get("opacity")
        if (
            not isinstance(clip_opacity, dict)
            or clip_opacity.get("valuetype") != "ParamRange"
            or not isinstance(clip_opacity.get("id"), int)
        ):
            raise RunnerError("layer 94 has no readable clip opacity")
        clip_opacity_state = self._read_parameter_state(
            int(clip_opacity["id"]),
            valuetype="ParamRange",
            label="layer 94 clip opacity eligibility",
        )
        expected_clip_opacity = expected["cc_detail"]["clip_opacity"]
        if not parameter_states_equal(clip_opacity_state, expected_clip_opacity):
            raise RunnerError("layer 94 clip opacity drifted from the snapshot")

        sourceparams = video.get("sourceparams")
        if not isinstance(sourceparams, dict):
            raise RunnerError("layer 94 has no Text Animator source parameters")
        source_opacity = sourceparams.get("Opacity")
        if (
            not isinstance(source_opacity, dict)
            or source_opacity.get("valuetype") != "ParamRange"
            or not isinstance(source_opacity.get("id"), int)
        ):
            raise RunnerError("layer 94 has no readable source Opacity")
        source_opacity_state = self._read_parameter_state(
            int(source_opacity["id"]),
            valuetype="ParamRange",
            label="layer 94 source Opacity eligibility",
        )
        expected_source_opacity = expected["cc_detail"][
            "source_parameter_evidence"
        ].get("Opacity")
        _require_snapshot_parameter_state(
            expected_source_opacity,
            label="layer 94 source parameter Opacity",
            valuetype="ParamRange",
        )
        if not parameter_states_equal(source_opacity_state, expected_source_opacity):
            raise RunnerError("layer 94 source Opacity drifted from the snapshot")

        clip_value = float(clip_opacity_state["value"])
        source_value = float(source_opacity_state["value"])
        if clip_value <= 0.0 or source_value <= 0.0:
            raise RunnerError(
                "layer 94 clip/source opacity is zero and not visibly eligible"
            )

        color = sourceparams.get("Color")
        if not isinstance(color, dict) or color.get("valuetype") != "ParamColor":
            raise RunnerError("layer 94 has no source Color visibility evidence")
        color_value = color.get("value")
        if (
            not isinstance(color_value, str)
            or re.fullmatch(r"#[0-9a-fA-F]{8}", color_value) is None
            or int(color_value[-2:], 16) == 0
        ):
            raise RunnerError("layer 94 source Color is transparent or invalid")
        return {
            "snapshot_connected": True,
            "live_connected": True,
            "clip_opacity": clip_value,
            "source_opacity": source_value,
            "source_color": color_value,
            "original_text_nonempty": True,
            "desired_text_nonempty": True,
        }

    def _capture_settled_calibration_roi(
        self,
        *,
        monitor_name: str,
        out: Path,
        witness_box: Sequence[Any] | None,
        reject_roi_sha256: str,
        phase: str,
    ) -> JsonObject:
        """Poll until a non-stale ROI is byte-stable for two consecutive frames."""

        roi = calibration_capture_roi(witness_box)
        previous_hash: str | None = None
        stable_frames = 0
        poll_records: list[JsonObject] = []
        for poll_index in range(1, CALIBRATION_SETTLE_MAX_POLLS + 1):
            poll_path = out.parent / (
                f".{out.stem}.{phase}.poll-{poll_index:02d}.png"
            )
            metadata = self.capture_monitor(
                monitor_name=monitor_name,
                out=poll_path,
                dry_run=False,
            )
            observation = calibration_roi_observation(poll_path, roi)
            roi_hash = str(observation["roi_sha256"])
            stale = roi_hash == reject_roi_sha256
            if stale:
                previous_hash = None
                stable_frames = 0
            elif roi_hash == previous_hash:
                stable_frames += 1
            else:
                previous_hash = roi_hash
                stable_frames = 1
            poll_records.append(
                {
                    "poll": poll_index,
                    "roi_sha256": roi_hash,
                    "rejected_as_previous_render": stale,
                    "consecutive_stable_frames": stable_frames,
                }
            )
            if stable_frames >= CALIBRATION_SETTLE_STABLE_FRAMES:
                payload = poll_path.read_bytes()
                settled = {
                    **metadata,
                    "path": str(out.resolve()),
                    "render_settle": {
                        "phase": phase,
                        "max_polls": CALIBRATION_SETTLE_MAX_POLLS,
                        "poll_count": poll_index,
                        "stable_frames_required": CALIBRATION_SETTLE_STABLE_FRAMES,
                        "stable_roi_sha256": roi_hash,
                        "polls": poll_records,
                    },
                }
                atomic_write_bytes(out, payload)
                atomic_write_json(
                    out.with_suffix(out.suffix + ".json"),
                    settled,
                )
                return settled
            if poll_index < CALIBRATION_SETTLE_MAX_POLLS:
                time.sleep(CALIBRATION_SETTLE_POLL_INTERVAL_SECONDS)
        raise RunnerError(
            f"{phase} render did not converge to "
            f"{CALIBRATION_SETTLE_STABLE_FRAMES} consecutive stable ROI frames "
            f"within {CALIBRATION_SETTLE_MAX_POLLS} polls"
        )

    def calibrate_moving_tag(
        self,
        *,
        layer: int,
        snapshot_path: Path,
        active_preset: Path,
        bundle: ArtifactBundle,
        live_controls: TypedLiveControls,
        out: Path,
    ) -> JsonObject:
        """Measure the B0 layer-94 tag and restore every source write.

        This is intentionally the only executable pre-overlay visual mutation.
        It never writes clip opacity, permanent Transform, source Color, source
        identity, trigger state, or composition structure.
        """

        if layer != 94:
            raise RunnerError("calibrate-moving-tag requires exactly layer 94")
        if bundle.status != "provisional" or live_controls.status != "provisional":
            raise ArtifactError("moving-tag calibration requires provisional artifacts")
        if re.fullmatch(r"B0(?:-.*)?", bundle.build_id) is None:
            raise ArtifactError(
                f"moving-tag calibration requires a provisional B0 build, "
                f"got {bundle.build_id!r}"
            )
        if live_controls.build_id != bundle.build_id:
            raise ArtifactError("live-controls build does not match provisional B0")

        out = out.resolve()
        snapshot_path = snapshot_path.resolve()
        active_preset = active_preset.resolve()
        protected_paths = {
            bundle.manifest_path.resolve(),
            snapshot_path,
            active_preset,
            *(
                (
                    bundle.repo_root / Path(*key.split("/"))
                ).resolve()
                for key in bundle.artifacts
            ),
        }
        final_capture_paths = {
            state: calibration_capture_path(out, state)
            for state in CALIBRATION_CAPTURE_STATES
        }
        publication_paths = {
            out,
            *final_capture_paths.values(),
            *(
                path.with_suffix(path.suffix + ".json")
                for path in final_capture_paths.values()
            ),
        }
        overlap = protected_paths & publication_paths
        if overlap:
            raise ArtifactError(
                "calibration output would overwrite protected input: "
                + ", ".join(str(path) for path in sorted(overlap, key=str))
            )
        preexisting = sorted(
            (path for path in publication_paths if path.exists()),
            key=str,
        )
        if preexisting:
            raise RunnerError(
                "calibration outputs already exist; refusing to overwrite: "
                + ", ".join(str(path) for path in preexisting)
            )

        snapshot, snapshot_hash = self._load_snapshot(snapshot_path)
        if snapshot["build_id"] != bundle.build_id:
            raise RunnerError("calibration snapshot build_id does not match B0")
        if snapshot["restart_stage"] != "restart-a":
            raise RunnerError("calibration requires the canonical restart-a snapshot")
        if snapshot["expected_layer_count"] != 148:
            raise RunnerError("calibration snapshot must contain exactly 148 layers")
        if snapshot["active_preset_path"] != str(active_preset):
            raise RunnerError("calibration snapshot active preset path does not match")
        try:
            active_preset_hash = sha256_bytes(active_preset.read_bytes())
        except OSError as exc:
            raise RunnerError(
                f"calibration active preset is unreadable: {active_preset}: {exc}"
            ) from exc
        if active_preset_hash != snapshot["active_preset_sha256"]:
            raise RunnerError("calibration active preset hash does not match snapshot")

        composition = self.composition()
        layers = composition.get("layers")
        if not isinstance(layers, list) or len(layers) != 148:
            raise RunnerError("moving-tag calibration requires exactly 148 live layers")
        current_fingerprint = composition_fingerprint(composition)
        if current_fingerprint["sha256"] != snapshot["composition_fingerprint"]["sha256"]:
            raise RunnerError(
                "calibration snapshot composition fingerprint does not match live state"
            )

        expected_clip = snapshot["clips"][layer - 1]
        current_clip = self.clip(layer)
        self._require_calibration_clip_identity(current_clip, expected_clip)
        source_parameters = self._calibration_source_parameters(current_clip)
        snapshot_source = expected_clip["cc_detail"]["source_parameter_evidence"]

        layer_fields = live_controls.layers[str(layer)].get("fields")
        if not isinstance(layer_fields, list):
            raise ArtifactError("layer 94 live-controls fields are unavailable")
        desired_fields: dict[str, Mapping[str, Any]] = {}
        for field in layer_fields:
            if (
                isinstance(field, dict)
                and field.get("target") == "text_animator_source"
                and field.get("parameter") in CALIBRATION_SOURCE_FIELD_TYPES
            ):
                name = str(field["parameter"])
                if name in desired_fields:
                    raise ArtifactError(
                        f"duplicate layer 94 calibration field in live-controls: {name}"
                    )
                desired_fields[name] = field
        missing_fields = set(CALIBRATION_SOURCE_FIELD_TYPES) - set(desired_fields)
        if missing_fields:
            raise ArtifactError(
                "layer 94 live-controls lack calibration fields: "
                + ", ".join(sorted(missing_fields))
            )
        if len(desired_fields) + 1 > MAX_WRITES_PER_WAVE:
            raise RunnerError(
                f"calibration apply wave exceeds {MAX_WRITES_PER_WAVE} writes"
            )
        selected_size = desired_fields["Size"]["desired"]
        if (
            not isinstance(selected_size, (int, float))
            or isinstance(selected_size, bool)
            or not math.isfinite(float(selected_size))
            or not LIVE_SIZE_RANGE[0] <= float(selected_size) <= LIVE_SIZE_RANGE[1]
        ):
            raise ArtifactError(
                f"layer 94 Size must be within {LIVE_SIZE_RANGE[0]}.."
                f"{LIVE_SIZE_RANGE[1]}"
            )

        original_states: dict[str, JsonObject] = {}
        for name, valuetype in CALIBRATION_SOURCE_FIELD_TYPES.items():
            expected_state = snapshot_source.get(name)
            _require_snapshot_parameter_state(
                expected_state,
                label=f"layer 94 source parameter {name}",
                valuetype=valuetype,
            )
            state = self._read_parameter_state(
                int(source_parameters[name]["id"]),
                valuetype=valuetype,
                label=f"layer 94 source {name}",
            )
            if not parameter_states_equal(state, expected_state):
                raise RunnerError(
                    f"layer 94 source {name} drifted from the campaign snapshot"
                )
            original_states[name] = state
        witness_box = live_controls.layers[str(layer)].get("witness", {}).get("box")
        calibration_witness_roi(witness_box)
        visibility_eligibility = self._require_calibration_visible_eligibility(
            current=current_clip,
            expected=expected_clip,
            original_text=original_states["Text"],
            desired_text=desired_fields["Text"]["desired"],
        )

        parent_hashes = measurement_parent_artifact_hashes(bundle)
        try:
            parent_manifest_bytes = bundle.manifest_path.read_bytes()
        except OSError as exc:
            raise ArtifactError(
                f"cannot bind provisional build manifest: {bundle.manifest_path}: {exc}"
            ) from exc
        parent_manifest_hash = sha256_bytes(parent_manifest_bytes)
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            capture_staging = tempfile.TemporaryDirectory(
                prefix=f".{out.stem}.captures.",
                dir=str(out.parent),
            )
        except OSError as exc:
            raise RunnerError(
                f"cannot create calibration capture staging directory: {exc}"
            ) from exc
        staging_root = Path(capture_staging.name)
        capture_paths = {
            state: staging_root / f"{state}.png"
            for state in CALIBRATION_CAPTURE_STATES
        }
        try:
            calibration_transaction_id = self.begin_calibration_recovery(
                layer=layer,
                out=out,
                original_states=original_states,
                expected_clip=expected_clip,
                current_fingerprint=current_fingerprint,
                active_preset=active_preset,
                active_preset_sha256=active_preset_hash,
                snapshot_path=snapshot_path,
                snapshot_sha256=snapshot_hash,
                snapshot=snapshot,
                bundle=bundle,
                parent_manifest_sha256=parent_manifest_hash,
                parent_artifact_hashes=parent_hashes,
            )
        except BaseException:
            capture_staging.cleanup()
            raise

        rollback_stack: list[tuple[str, JsonObject]] = []
        applied_states: dict[str, JsonObject] = {}
        restored_states: dict[str, JsonObject] = {}
        capture_records: dict[str, JsonObject] = {}
        state_ink: JsonObject | None = None
        accepted_metrics: JsonObject | None = None
        primary_error: BaseException | None = None
        off_text_readback: JsonObject | None = None
        apply_write_count = 0
        eligibility_capture: JsonObject | None = None

        try:
            eligibility_path = staging_root / "eligible-before-mutation.png"
            eligibility_metadata = self.capture_monitor(
                monitor_name="Composition",
                out=eligibility_path,
                dry_run=False,
            )
            eligibility_observation = calibration_roi_observation(
                eligibility_path,
                calibration_capture_roi(witness_box),
            )
            if (
                eligibility_observation["non_dominant_pixel_count"]
                < MIN_MOVING_TAG_CHANGED_PIXELS
            ):
                raise RunnerError(
                    "layer 94 monitor ROI has insufficient visible activity "
                    "before calibration"
                )
            eligibility_capture = {
                "png_sha256": eligibility_metadata["png_sha256"],
                **eligibility_observation,
            }
            # A true raster baseline cannot come from the preexisting visible
            # glyphs. Blank only the already captured, allowlisted Text field,
            # verify it, and retain Text in the reverse rollback set.
            rollback_stack.append(("Text", original_states["Text"]))
            apply_write_count += 1
            off_text_readback = self._calibration_transaction_put(
                calibration_transaction_id,
                source_parameters["Text"],
                value="",
                expected_state=None,
                label="layer 94 source Text off baseline",
                phase="blank-baseline",
                parameter_name="Text",
            )
            capture_records["off"] = self._capture_settled_calibration_roi(
                monitor_name="Composition",
                out=capture_paths["off"],
                witness_box=witness_box,
                reject_roi_sha256=str(eligibility_observation["roi_sha256"]),
                phase="blank-baseline",
            )
            capture_records["off"].update(
                {
                    "capture_semantics": "blank_text_raster_baseline",
                    "source_text_blank_verified": True,
                }
            )
            for name in CALIBRATION_SOURCE_FIELD_TYPES:
                field = desired_fields[name]
                rollback_stack.append(
                    (
                        name,
                        off_text_readback
                        if name == "Text"
                        else original_states[name],
                    )
                )
                apply_write_count += 1
                applied_states[name] = self._calibration_transaction_put(
                    calibration_transaction_id,
                    source_parameters[name],
                    value=field["desired"],
                    expected_state=None,
                    label=f"layer 94 source {name} apply",
                    phase="apply",
                    parameter_name=name,
                )
            capture_records["minimum"] = self._capture_settled_calibration_roi(
                monitor_name="Composition",
                out=capture_paths["minimum"],
                witness_box=witness_box,
                reject_roi_sha256=str(
                    capture_records["off"]["render_settle"][
                        "stable_roi_sha256"
                    ]
                ),
                phase="final-tag",
            )
            capture_records["minimum"].update(
                {
                    "capture_semantics": (
                        "settled_live_tag_raster_stability_sample"
                    ),
                    "endpoint_position_verified": False,
                }
            )
            for state in ("midpoint", "maximum"):
                capture_records[state] = self.capture_monitor(
                    monitor_name="Composition",
                    out=capture_paths[state],
                    dry_run=False,
                )
                capture_records[state].update(
                    {
                        "capture_semantics": (
                            "sequential_live_tag_raster_stability_sample"
                        ),
                        "endpoint_position_verified": False,
                    }
                )
            state_ink, accepted_metrics = measure_calibration_ink(
                off_path=capture_paths["off"],
                state_paths=capture_paths,
                witness_box=witness_box,
            )
            for state, ink in state_ink.items():
                capture_records[state].update(ink)
        except BaseException as exc:
            primary_error = exc

        restoration_errors: list[BaseException] = []
        restore_order: list[str] = []
        for name, rollback_state in reversed(rollback_stack):
            restore_order.append(name)
            try:
                restore_clip = self.clip(layer)
                self._require_calibration_clip_identity(restore_clip, expected_clip)
                restore_parameters = self._calibration_source_parameters(restore_clip)
                restored_states[name] = self._calibration_transaction_put(
                    calibration_transaction_id,
                    restore_parameters[name],
                    value=rollback_state["value"],
                    expected_state=rollback_state,
                    label=f"layer 94 source {name} restore",
                    phase="rollback",
                    parameter_name=name,
                )
            except BaseException as exc:
                restoration_errors.append(exc)

        # Verify the complete narrow rollback, its composition lineage, the active
        # preset, snapshot bytes, and all B0 parent artifacts even after failure.
        try:
            verified_clip = self.clip(layer)
            self._require_calibration_clip_identity(verified_clip, expected_clip)
            verified_parameters = self._calibration_source_parameters(verified_clip)
            for name, valuetype in CALIBRATION_SOURCE_FIELD_TYPES.items():
                verified_state = self._read_parameter_state(
                    int(verified_parameters[name]["id"]),
                    valuetype=valuetype,
                    label=f"layer 94 source {name} final restore",
                )
                if not parameter_states_equal(verified_state, original_states[name]):
                    raise RunnerError(
                        f"layer 94 source {name} final state was not restored"
                    )
                restored_states[name] = verified_state
            final_composition = self.composition()
            final_fingerprint = composition_fingerprint(final_composition)
            if final_fingerprint["sha256"] != current_fingerprint["sha256"]:
                raise RunnerError("composition fingerprint changed during calibration")
            if sha256_file(active_preset) != active_preset_hash:
                raise RunnerError("active preset changed during calibration")
            if sha256_file(snapshot_path) != snapshot_hash:
                raise RunnerError("campaign snapshot changed during calibration")
            if sha256_file(bundle.manifest_path) != parent_manifest_hash:
                raise ArtifactError("provisional build manifest changed during calibration")
            if measurement_parent_artifact_hashes(bundle) != parent_hashes:
                raise ArtifactError("provisional B0 artifacts changed during calibration")
            self.calibration_recovery.commit(
                calibration_transaction_id,
                {
                    "build_id": bundle.build_id,
                    "layer": layer,
                    "apply_count": apply_write_count,
                    "restore_count": len(rollback_stack),
                    "primary_error": (
                        None
                        if primary_error is None
                        else {
                            "type": type(primary_error).__name__,
                            "message": str(primary_error),
                        }
                    ),
                },
            )
        except BaseException as exc:
            restoration_errors.append(exc)

        if restoration_errors:
            detail = "; ".join(str(error) for error in restoration_errors)
            capture_staging.cleanup()
            if primary_error is not None:
                raise RunnerError(
                    f"moving-tag calibration failed ({primary_error}); "
                    f"rollback verification also failed: {detail}"
                ) from restoration_errors[0]
            raise RunnerError(
                f"moving-tag calibration rollback verification failed: {detail}"
            ) from restoration_errors[0]
        if primary_error is not None:
            capture_staging.cleanup()
            if isinstance(primary_error, RunnerError):
                raise primary_error
            raise RunnerError(
                f"moving-tag calibration failed: {primary_error}"
            ) from primary_error
        if (
            state_ink is None
            or accepted_metrics is None
            or eligibility_capture is None
        ):
            capture_staging.cleanup()
            raise RunnerError("moving-tag calibration produced no accepted metrics")

        for state, final_path in final_capture_paths.items():
            capture_records[state]["path"] = str(final_path)

        measurement: JsonObject = {
            "schema_version": 1,
            "artifact_role": "live_tag_measurement",
            "artifact_id": str(uuid.uuid4()),
            "captured_at": utc_timestamp(),
            "build_id": bundle.build_id,
            "calibration_transaction_id": calibration_transaction_id,
            "measurement_parent_artifact_hashes": parent_hashes,
            "measurement_parent_build_manifest": {
                "path": str(bundle.manifest_path),
                "sha256": parent_manifest_hash,
                "bytes": len(parent_manifest_bytes),
            },
            "snapshot": {
                "path": str(snapshot_path),
                "sha256": snapshot_hash,
                "artifact_id": snapshot["artifact_id"],
                "restart_stage": snapshot["restart_stage"],
                "composition_fingerprint": current_fingerprint["sha256"],
                "active_preset_path": str(active_preset),
                "active_preset_sha256": active_preset_hash,
            },
            "layer": layer,
            "visibility_eligibility": {
                **visibility_eligibility,
                "monitor": eligibility_capture,
            },
            "selected_avenue_size": float(selected_size),
            "accepted_live_tag_metrics": accepted_metrics,
            "capture_semantics": {
                "off": "Text was blanked and GET-verified before capture.",
                "minimum_midpoint_maximum": (
                    "Contract state names are retained for evidence compatibility; "
                    "these are sequential raster-stability samples at the current "
                    "controller position, not verified physical endpoints."
                ),
                "endpoint_sweep_verified": False,
                "later_acceptance_gate": (
                    "Verify every fader and the crossfader physically at minimum, "
                    "midpoint, and maximum after the accepted full preset is loaded."
                ),
            },
            "captures": capture_records,
            "off_text_readback": off_text_readback,
            "source_fields": {
                name: {
                    "valuetype": CALIBRATION_SOURCE_FIELD_TYPES[name],
                    "desired": desired_fields[name]["desired"],
                    "original": original_states[name],
                    "applied_readback": applied_states[name],
                    "restored_readback": restored_states[name],
                }
                for name in CALIBRATION_SOURCE_FIELD_TYPES
            },
            "write_waves": {
                "maximum_writes": MAX_WRITES_PER_WAVE,
                "apply_count": apply_write_count,
                "restore_count": len(rollback_stack),
                "restore_order": restore_order,
            },
        }
        created_outputs: list[Path] = []
        try:
            for state, final_path in final_capture_paths.items():
                staged_path = capture_paths[state]
                atomic_write_bytes(final_path, staged_path.read_bytes())
                created_outputs.append(final_path)
                sidecar = final_path.with_suffix(final_path.suffix + ".json")
                atomic_write_json(sidecar, capture_records[state])
                created_outputs.append(sidecar)
            atomic_write_json(out, measurement)
            created_outputs.append(out)
            published_bytes = out.read_bytes()
        except BaseException as exc:
            cleanup_errors: list[str] = []
            for created in reversed(created_outputs):
                try:
                    created.unlink()
                except OSError as cleanup_exc:
                    cleanup_errors.append(f"{created}: {cleanup_exc}")
            message = f"cannot publish live tag measurement set {out}: {exc}"
            if cleanup_errors:
                message += "; cleanup failed: " + "; ".join(cleanup_errors)
            raise RunnerError(message) from exc
        finally:
            capture_staging.cleanup()
        return {
            "path": str(out),
            "sha256": sha256_bytes(published_bytes),
            "bytes": len(published_bytes),
            "build_id": bundle.build_id,
            "calibration_transaction_id": calibration_transaction_id,
            "layer": layer,
            "selected_avenue_size": float(selected_size),
            "accepted_live_tag_metrics": accepted_metrics,
            "endpoint_sweep_verified": False,
            "captures": capture_records,
            "apply_count": apply_write_count,
            "restore_count": len(rollback_stack),
            "restore_order": restore_order,
        }

    def capture_monitor(
        self, *, monitor_name: str, out: Path, dry_run: bool
    ) -> JsonObject:
        monitors = self._json_get("/api/v1/composition/monitors")
        if not isinstance(monitors, list):
            raise RunnerError("monitor list is not an array")
        matches = [
            monitor
            for monitor in monitors
            if isinstance(monitor, dict) and monitor.get("name") == monitor_name
        ]
        if len(matches) != 1:
            raise RunnerError(
                f"expected one monitor named {monitor_name!r}, found {len(matches)}"
            )
        monitor = matches[0]
        monitor_id = int(monitor["id"])
        endpoint = f"/api/v1/composition/monitors/{monitor_id}/snapshot.png"
        response = self.bridge.get(endpoint)
        content_type = (response.header("content-type") or "").split(";", 1)[0]
        if content_type.casefold() != "image/png":
            raise RunnerError(
                f"monitor snapshot content type is not image/png: {content_type!r}"
            )
        info = validate_png(response.body, (1920, 1080))
        metadata: JsonObject = {
            "schema_version": 1,
            "captured_at": utc_timestamp(),
            "monitor": monitor,
            "endpoint": endpoint,
            "content_type": content_type,
            "mode": info.mode,
            "width": info.width,
            "height": info.height,
            "png_sha256": sha256_bytes(response.body),
            "png_bytes": len(response.body),
            "path": str(out.resolve()),
            "dry_run": dry_run,
        }
        if not dry_run:
            atomic_write_bytes(out, response.body)
            atomic_write_json(out.with_suffix(out.suffix + ".json"), metadata)
        return metadata


def parse_layers(values: Sequence[str]) -> list[int]:
    layers: list[int] = []
    for value in values:
        for token in value.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                layer = int(token)
            except ValueError as exc:
                raise argparse.ArgumentTypeError(f"invalid layer: {token}") from exc
            if not 1 <= layer <= 149:
                raise argparse.ArgumentTypeError(f"layer out of range: {layer}")
            layers.append(layer)
    unique = sorted(set(layers))
    if not unique:
        raise argparse.ArgumentTypeError("at least one layer is required")
    return unique


def _add_runtime_options(
    parser: argparse.ArgumentParser, *, active_preset_required: bool = False
) -> None:
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--native-pipe", default=NATIVE_PIPE)
    parser.add_argument("--bridge-pipe", default=BRIDGE_PIPE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--journal", type=Path, default=DEFAULT_JOURNAL)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--calibration-recovery",
        type=Path,
        default=DEFAULT_CALIBRATION_RECOVERY,
    )
    parser.add_argument("--composition-name", default=DEFAULT_COMPOSITION_NAME)
    parser.add_argument(
        "--active-preset",
        type=Path,
        required=active_preset_required,
        help="canonical active MIDI preset whose exact bytes bind this stage",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight")
    _add_runtime_options(preflight)
    preflight.add_argument("--stage", required=True, choices=sorted(STAGES))
    preflight.add_argument("--expected-layer-count", type=int)
    preflight.add_argument("--out", type=Path)

    snapshot = subparsers.add_parser("snapshot-controls")
    _add_runtime_options(snapshot, active_preset_required=True)
    snapshot.add_argument("--scope", choices=("campaign",), required=True)
    snapshot.add_argument("--out", type=Path, required=True)
    snapshot.add_argument("--restart-stage", required=True, choices=sorted(STAGES))
    snapshot.add_argument("--build-id", required=True)

    restore = subparsers.add_parser("restore-snapshot")
    _add_runtime_options(restore, active_preset_required=True)
    restore.add_argument("--snapshot", type=Path, required=True)
    restore.add_argument("--gate")

    manual = subparsers.add_parser("manual-eject-check")
    _add_runtime_options(manual, active_preset_required=True)
    manual.add_argument("--snapshot", type=Path, required=True)
    manual.add_argument("--gate", required=True)
    manual.add_argument("--layers", nargs="+", required=True)
    manual.add_argument("--evidence-out", type=Path, required=True)

    capture = subparsers.add_parser("capture-snapshot")
    _add_runtime_options(capture)
    capture.add_argument("--monitor", default="Composition")
    capture.add_argument("--out", type=Path, required=True)
    capture.add_argument("--stage", choices=sorted(STAGES), default="offline")
    capture.add_argument("--expected-layer-count", type=int)

    recovery = subparsers.add_parser("recover-calibration")
    _add_runtime_options(recovery, active_preset_required=True)

    verify_artifacts = subparsers.add_parser("verify-artifacts")
    verify_artifacts.add_argument(
        "--build-manifest", type=Path, default=DEFAULT_BUILD_MANIFEST
    )
    verify_artifacts.add_argument("--repo-root", type=Path, default=REACT_KIT_ROOT.parent)
    verify_artifacts.add_argument(
        "--require",
        type=Path,
        action="append",
        default=[],
    )

    for name in (
        "append-overlay",
        "capture-controls",
        "apply-controls",
        "restore-controls",
        "verify-controls",
        "calibrate-moving-tag",
    ):
        command = subparsers.add_parser(name)
        _add_runtime_options(command, active_preset_required=True)
        command.add_argument("--layers", nargs="*", default=[])
        command.add_argument("--layer", type=int)
        command.add_argument("--snapshot", type=Path)
        command.add_argument("--state", type=Path)
        command.add_argument("--out", type=Path)
        command.add_argument(
            "--build-manifest", type=Path, default=DEFAULT_BUILD_MANIFEST
        )
        command.add_argument(
            "--live-controls", type=Path, default=DEFAULT_LIVE_CONTROLS
        )
        command.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
        command.add_argument("--repo-root", type=Path, default=REACT_KIT_ROOT.parent)

    return parser


def make_runner(args: argparse.Namespace) -> LiveRunner:
    return LiveRunner(
        bridge=PipeHttpClient(args.bridge_pipe),
        native=PipeHttpClient(args.native_pipe),
        manifest_path=args.manifest,
        journal_path=args.journal,
        lock_path=args.lock,
        calibration_recovery_path=args.calibration_recovery,
        composition_name=args.composition_name,
    )


def _disabled_mutation_plan(
    args: argparse.Namespace,
    runner: LiveRunner,
    *,
    allow_calibration_execution: bool = False,
) -> JsonObject:
    is_calibration = args.command == "calibrate-moving-tag"
    stage = (
        "restart-a"
        if is_calibration
        else "append-overlay"
        if args.command == "append-overlay"
        else "visual-controls"
    )
    expected_count = 148 if is_calibration else (
        None if args.command == "append-overlay" else 149
    )
    preflight = runner.preflight(
        stage=stage,
        expected_layer_count=expected_count,
        active_preset=args.active_preset,
    )
    bundle = ArtifactBundle.verify(args.build_manifest, args.repo_root)
    expected_status = "provisional" if is_calibration else "accepted"
    if bundle.status != expected_status:
        raise ArtifactError(
            f"{args.command} requires a {expected_status} artifact build, "
            f"got {bundle.status}"
        )
    live_controls = TypedLiveControls.verify(args.live_controls, bundle)
    overlay_bytes = bundle.read_verified_bytes(args.overlay)
    overlay_info = validate_png(
        overlay_bytes,
        (1920, 1080),
        allowed_modes=("RGB", "RGBA"),
    )
    composition = runner.composition()
    live_layer_count = len(composition.get("layers") or [])
    if args.command == "append-overlay":
        if live_layer_count not in (148, 149):
            raise RunnerError(
                f"append-overlay requires 148 layers or a claimed 149, found "
                f"{live_layer_count}"
            )
        if live_layer_count == 149:
            runner._require_overlay_claim(composition, bundle.build_id)
    elif live_layer_count == 149:
        runner._require_overlay_claim(composition, bundle.build_id)

    if is_calibration:
        if args.layer != 94:
            raise RunnerError("calibrate-moving-tag requires exactly --layer 94")
        if args.snapshot is None:
            raise RunnerError("calibrate-moving-tag requires --snapshot")
        if getattr(args, "out", None) is None:
            raise RunnerError("calibrate-moving-tag requires --out")
        snapshot, _ = runner._load_snapshot(args.snapshot)
        if snapshot["build_id"] != bundle.build_id:
            raise RunnerError("calibration snapshot build_id does not match B0")
        if snapshot["expected_layer_count"] != 148:
            raise RunnerError("calibration snapshot must contain 148 layers")
        if snapshot["active_preset_sha256"] != preflight["active_preset_sha256"]:
            raise RunnerError("calibration snapshot active preset does not match")
        if snapshot["active_preset_path"] != preflight["active_preset_path"]:
            raise RunnerError("calibration snapshot active preset path does not match")
        if (
            snapshot["composition_fingerprint"]["sha256"]
            != preflight["composition_fingerprint"]["sha256"]
        ):
            raise RunnerError("calibration snapshot is not from this live session")
        layers = [94]
    elif args.command == "append-overlay":
        layers = []
    else:
        layers = (
            parse_layers(args.layers)
            if args.layers
            else [1, 46, 94, 102]
        )
        if 149 in layers:
            raise RunnerError("visual control targets are restricted to layers 1..148")
    if args.command == "capture-controls" and getattr(args, "out", None) is None:
        raise RunnerError("capture-controls requires --out")
    if args.command == "restore-controls":
        state_path = getattr(args, "state", None)
        if state_path is None or not state_path.resolve().is_file():
            raise RunnerError("restore-controls requires a readable --state artifact")

    requests: list[JsonObject] = []
    if args.command == "append-overlay" and live_layer_count == 148:
        requests = [
            {
                "method": "POST",
                "path": "/api/v1/composition/grow-to",
                "json": {"layer_count": 149, "column_count": 1},
            },
            {
                "method": "POST",
                "path": "/api/v1/composition/clips/open",
                "json": [
                    {
                        "target": "/composition/layers/149/clips/1",
                        "source": args.overlay.resolve().as_uri(),
                    }
                ],
            },
            {
                "method": "PUT",
                "path_template": "/api/v1/parameter/by-id/{rediscovered_layer149_opacity}",
                "json": {"value": 1.0},
            },
            {
                "method": "PUT",
                "path_template": "/api/v1/parameter/by-id/{rediscovered_layer149_blend}",
                "json": {"index": 10},
            },
            {
                "method": "POST",
                "path": "/api/v1/composition/layers/149/clips/1/connect",
            },
        ]
    elif args.command in {
        "apply-controls",
        "restore-controls",
        "calibrate-moving-tag",
    }:
        if is_calibration:
            requests.append(
                {
                    "method": "PUT",
                    "path_template": (
                        "/api/v1/parameter/by-id/"
                        "{rediscovered_parameter_id}"
                    ),
                    "layer": 94,
                    "target": "text_animator_source",
                    "parameter": "Text",
                    "valuetype": "ParamText",
                    "json": {"value": ""},
                    "phase": "blank-text-off-baseline",
                }
            )
        for layer in layers:
            for field in live_controls.layers[str(layer)]["fields"]:
                if is_calibration and (
                    field["target"] != "text_animator_source"
                    or field["parameter"]
                    not in {
                        "Text",
                        "Font",
                        "Size",
                        "Position X",
                        "Position Y",
                        "Spacing Y",
                    }
                ):
                    continue
                requests.append(
                    {
                        "method": "PUT",
                        "path_template": (
                            "/api/v1/parameter/by-id/"
                            "{rediscovered_parameter_id}"
                        ),
                        "layer": layer,
                        "target": field["target"],
                        "parameter": field["parameter"],
                        "valuetype": field["valuetype"],
                        "json": {"value": field["desired"]}
                        if is_calibration
                        else None,
                        "phase": "apply-final-live-controls"
                        if is_calibration
                        else None,
                    }
                )
        if is_calibration and len(requests) > MAX_WRITES_PER_WAVE:
            raise RunnerError(
                f"calibration apply wave exceeds {MAX_WRITES_PER_WAVE} writes"
            )
    plan = {
        "command": args.command,
        "dry_run": args.dry_run,
        "preflight": preflight,
        "build_id": bundle.build_id,
        "live_controls_status": live_controls.status,
        "overlay": {
            "path": str(args.overlay.resolve()),
            "sha256": sha256_bytes(overlay_bytes),
            "mode": overlay_info.mode,
            "width": overlay_info.width,
            "height": overlay_info.height,
        },
        "layers": layers,
        "max_writes_per_wave": MAX_WRITES_PER_WAVE,
        "request_count": len(requests),
        "requests": requests,
        "capture_semantics": (
            {
                "off": "blank Text then capture",
                "named_samples": (
                    "sequential raster-stability samples; physical endpoint "
                    "positions are not asserted"
                ),
                "endpoint_sweep_verified": False,
            }
            if is_calibration
            else None
        ),
        "publication": (
            str(args.out.resolve())
            if args.command in {"capture-controls", "calibrate-moving-tag"}
            and getattr(args, "out", None) is not None
            else None
        ),
    }
    if args.dry_run or (is_calibration and allow_calibration_execution):
        return plan
    raise LiveMutationNotValidated(
        f"{args.command} is fail-closed until its exact Avenue write schema "
        "passes the staged live pilot; no write was attempted"
    )


def dispatch(args: argparse.Namespace) -> JsonObject:
    if args.command == "verify-artifacts":
        bundle = ArtifactBundle.verify(args.build_manifest, args.repo_root)
        for path in args.require:
            bundle.require(path)
        return {
            "build_id": bundle.build_id,
            "status": bundle.status,
            "artifact_count": len(bundle.artifacts),
        }

    runner = make_runner(args)
    try:
        if args.command == "recover-calibration":
            if args.dry_run:
                runner.preflight(
                    stage="restart-a",
                    expected_layer_count=148,
                    active_preset=args.active_preset,
                    allow_calibration_recovery=True,
                )
                return runner.recover_calibration(
                    active_preset=args.active_preset,
                    dry_run=True,
                )
            with CampaignLock(args.lock):
                runner.preflight(
                    stage="restart-a",
                    expected_layer_count=148,
                    active_preset=args.active_preset,
                    allow_calibration_recovery=True,
                )
                return runner.recover_calibration(
                    active_preset=args.active_preset,
                )
        if args.command == "preflight":
            result = runner.preflight(
                stage=args.stage,
                expected_layer_count=args.expected_layer_count,
                active_preset=args.active_preset,
            )
            if args.out is not None and not args.dry_run:
                atomic_write_json(args.out, result)
            return result
        if args.command == "snapshot-controls":
            if args.dry_run:
                preflight = runner.preflight(
                    stage=args.restart_stage,
                    active_preset=args.active_preset,
                )
                return runner.snapshot_controls(
                    out=args.out,
                    restart_stage=args.restart_stage,
                    build_id=args.build_id,
                    active_preset_path=args.active_preset,
                    active_preset_sha256=preflight["active_preset_sha256"],
                    dry_run=True,
                )
            with CampaignLock(args.lock):
                preflight = runner.preflight(
                    stage=args.restart_stage,
                    active_preset=args.active_preset,
                )
                return runner.snapshot_controls(
                    out=args.out,
                    restart_stage=args.restart_stage,
                    build_id=args.build_id,
                    active_preset_path=args.active_preset,
                    active_preset_sha256=preflight["active_preset_sha256"],
                    dry_run=False,
                )
        if args.command == "restore-snapshot":
            snapshot, _ = runner._load_snapshot(args.snapshot)
            if args.dry_run:
                runner.preflight(
                    stage=snapshot["restart_stage"],
                    expected_layer_count=snapshot["expected_layer_count"],
                    active_preset=args.active_preset,
                )
                return runner.restore_snapshot_gate(
                    snapshot_path=args.snapshot,
                    supplied_gate=args.gate,
                    active_preset=args.active_preset,
                    dry_run=True,
                )
            with CampaignLock(args.lock):
                runner.preflight(
                    stage=snapshot["restart_stage"],
                    expected_layer_count=snapshot["expected_layer_count"],
                    active_preset=args.active_preset,
                )
                return runner.restore_snapshot_gate(
                    snapshot_path=args.snapshot,
                    supplied_gate=args.gate,
                    active_preset=args.active_preset,
                    dry_run=False,
                )
        if args.command == "manual-eject-check":
            parsed_layers = parse_layers(args.layers)
            snapshot, _ = runner._load_snapshot(args.snapshot)
            if args.dry_run:
                runner.preflight(
                    stage=snapshot["restart_stage"],
                    expected_layer_count=snapshot["expected_layer_count"],
                    active_preset=args.active_preset,
                )
                return runner.manual_eject_check(
                    snapshot_path=args.snapshot,
                    gate_id=args.gate,
                    layers=parsed_layers,
                    evidence_out=args.evidence_out,
                    active_preset=args.active_preset,
                    dry_run=True,
                )
            with CampaignLock(args.lock):
                runner.preflight(
                    stage=snapshot["restart_stage"],
                    expected_layer_count=snapshot["expected_layer_count"],
                    active_preset=args.active_preset,
                )
                return runner.manual_eject_check(
                    snapshot_path=args.snapshot,
                    gate_id=args.gate,
                    layers=parsed_layers,
                    evidence_out=args.evidence_out,
                    active_preset=args.active_preset,
                    dry_run=False,
                )
        if args.command == "capture-snapshot":
            if args.dry_run:
                runner.preflight(
                    stage=args.stage,
                    expected_layer_count=args.expected_layer_count,
                    active_preset=args.active_preset,
                )
                return runner.capture_monitor(
                    monitor_name=args.monitor, out=args.out, dry_run=True
                )
            with CampaignLock(args.lock):
                runner.preflight(
                    stage=args.stage,
                    expected_layer_count=args.expected_layer_count,
                    active_preset=args.active_preset,
                )
                return runner.capture_monitor(
                    monitor_name=args.monitor, out=args.out, dry_run=False
                )
        if args.command == "calibrate-moving-tag" and not args.dry_run:
            with CampaignLock(args.lock):
                _disabled_mutation_plan(
                    args,
                    runner,
                    allow_calibration_execution=True,
                )
                bundle = ArtifactBundle.verify(
                    args.build_manifest,
                    args.repo_root,
                )
                live_controls = TypedLiveControls.verify(
                    args.live_controls,
                    bundle,
                )
                return runner.calibrate_moving_tag(
                    layer=args.layer,
                    snapshot_path=args.snapshot,
                    active_preset=args.active_preset,
                    bundle=bundle,
                    live_controls=live_controls,
                    out=args.out,
                )
        return _disabled_mutation_plan(args, runner)
    finally:
        runner.bridge.close()
        if runner.native is not None:
            runner.native.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = dispatch(args)
    except ManualActionRequired as exc:
        print(
            json.dumps(
                {
                    "status": "manual_action_required",
                    "gate_id": exc.gate_id,
                    "snapshot": str(exc.snapshot),
                    "layers": list(exc.layers),
                    "message": str(exc),
                },
                indent=2,
            )
        )
        return 3
    except RunnerError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 2
    print(json.dumps({"status": "ok", "result": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
