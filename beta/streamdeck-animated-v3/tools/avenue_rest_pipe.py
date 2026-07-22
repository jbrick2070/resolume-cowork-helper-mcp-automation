"""HTTP-over-named-pipe client for Resolume Avenue's local REST API.

Avenue exposes REST on `\\.\pipe\Resolume Avenue\rest-api` (HTTP/1.1 over a
named pipe, no TCP). One request per pipe connection, serialized - the same
constraint the avenue_pipe_bridge honours. 100% local, pywin32 only.
"""
import json

import win32file

PIPE = r"\\.\pipe\Resolume Avenue\rest-api"
BUFFER = 65536


def _read_response(handle):
    buf = b""
    # headers
    while b"\r\n\r\n" not in buf:
        _, data = win32file.ReadFile(handle, BUFFER)
        if not data:
            break
        buf += data
    head, _, rest = buf.partition(b"\r\n\r\n")
    headers = head.decode("latin1").lower()
    body = rest
    if "transfer-encoding: chunked" in headers:
        # read until terminating chunk
        while not body.endswith(b"0\r\n\r\n"):
            _, data = win32file.ReadFile(handle, BUFFER)
            if not data:
                break
            body += data
        # de-chunk
        out = b""
        i = 0
        while i < len(body):
            j = body.index(b"\r\n", i)
            size = int(body[i:j], 16)
            if size == 0:
                break
            out += body[j + 2:j + 2 + size]
            i = j + 2 + size + 2
        body = out
    else:
        length = 0
        for line in headers.split("\r\n"):
            if line.startswith("content-length:"):
                length = int(line.split(":")[1])
        while len(body) < length:
            _, data = win32file.ReadFile(handle, BUFFER)
            if not data:
                break
            body += data
    status = int(head.split(b" ")[1])
    return status, body


def request(method, path, body=None, content_type=None):
    handle = win32file.CreateFile(
        PIPE, win32file.GENERIC_READ | win32file.GENERIC_WRITE,
        0, None, win32file.OPEN_EXISTING, 0, None)
    try:
        payload = b""
        headers = [f"{method} {path} HTTP/1.1", "Host: localhost",
                   "Connection: close"]
        if body is not None:
            if isinstance(body, bytes):
                payload = body
                content_type = content_type or "application/octet-stream"
            elif isinstance(body, str):
                payload = body.encode("utf-8")
                content_type = content_type or "text/plain; charset=utf-8"
            else:
                payload = json.dumps(body).encode("utf-8")
                content_type = content_type or "application/json"
            headers += [f"Content-Type: {content_type}",
                        f"Content-Length: {len(payload)}"]
        raw = ("\r\n".join(headers) + "\r\n\r\n").encode() + payload
        win32file.WriteFile(handle, raw)
        status, resp = _read_response(handle)
        return status, (json.loads(resp) if resp.strip().startswith(b"{") or
                        resp.strip().startswith(b"[") else resp)
    finally:
        handle.Close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method")
    parser.add_argument("path")
    parser.add_argument("body", nargs="?")
    parser.add_argument("--content-type")
    args = parser.parse_args()

    status, response = request(
        args.method.upper(),
        args.path,
        args.body,
        content_type=args.content_type,
    )
    print(status)
    if isinstance(response, (dict, list)):
        print(json.dumps(response, indent=2))
    else:
        print(response.decode("utf-8", errors="replace"))
