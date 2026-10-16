#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rig.py - talk to the running Resolume Avenue over its REST API (port 8080).

    from resolume_build import rig
    rig.alive()
    rig.open_composition(path)        # file:/// URL, polls until loaded
    rig.save_composition(path)        # NEVER call without the user's say-so
    comp = rig.composition()
    rig.ensure_running()              # restart Avenue after a crash
"""
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8080/api/v1"
AVENUE_EXE = r"C:\Program Files\Resolume Avenue\Avenue.exe"


def req(method, path, body=None, timeout=60):
    data = None
    headers = {}
    if body is not None:
        if isinstance(body, str):
            data = body.encode("utf-8")
            headers["Content-Type"] = "text/plain"
        else:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers=headers)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        raw = resp.read()
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError:
            return raw.decode("utf-8", "replace")


def get(path, timeout=60):
    return req("GET", path, timeout=timeout)


def put(path, body, timeout=60):
    return req("PUT", path, body, timeout=timeout)


def post(path, body=None, timeout=60):
    return req("POST", path, body, timeout=timeout)


def alive():
    try:
        return get("/product", timeout=5) is not None
    except Exception:
        return False


def product():
    return get("/product")


def file_url(path):
    return "file:///" + urllib.parse.quote(os.path.abspath(path)
                                          .replace("\\", "/"))


def composition():
    return get("/composition", timeout=120)


def composition_name():
    try:
        return composition()["name"]["value"]
    except Exception:
        return None


def open_composition(path, expect_name=None, timeout=180):
    """POST /composition/open and poll until the named composition is up."""
    try:
        post("/composition/open", file_url(path), timeout=timeout)
    except Exception as exc:
        print("  open call: %s" % exc)
    want = expect_name
    for _ in range(timeout):
        time.sleep(1)
        if not alive():
            continue
        name = composition_name()
        if name and (want is None or name == want):
            return True
    return False


def save_composition(path, timeout=240):
    """Save the open composition to `path`. Caller must have user consent."""
    if os.path.exists(path):
        os.remove(path)
    try:
        post("/composition/save", file_url(path), timeout=timeout)
    except Exception as exc:
        print("  save call: %s" % exc)
    for _ in range(timeout):
        if os.path.exists(path) and os.path.getsize(path) > 2000:
            time.sleep(1)
            return True
        time.sleep(1)
    return False


def new_composition():
    return post("/composition/new")


def pid():
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Process Avenue -ErrorAction SilentlyContinue).Id"],
            text=True).strip()
        return int(out) if out else None
    except Exception:
        return None


def ensure_running(wait=120):
    """If Avenue is gone, start it and wait for the REST API."""
    if alive():
        return True
    if pid() is None:
        print("  Avenue is not running - starting it")
        subprocess.Popen([AVENUE_EXE], close_fds=True)
    for _ in range(wait):
        time.sleep(1)
        if alive():
            time.sleep(3)
            return True
    return False


def kill():
    subprocess.call(["powershell", "-NoProfile", "-Command",
                     "Stop-Process -Name Avenue -Force -ErrorAction "
                     "SilentlyContinue"])


# ---- read-back helpers ------------------------------------------------------
def layer_json(n):
    return get("/composition/layers/%d" % n)


def clip_json(layer, column):
    return get("/composition/layers/%d/clips/%d" % (layer, column))


def deck_select(n):
    return post("/composition/decks/%d/select" % n)


def source_params(layer, column):
    c = clip_json(layer, column)
    v = c.get("video") or {}
    return (v.get("sourceparams") or {}), c


def param_value(p):
    """Collapse a REST parameter object to a plain comparable value."""
    if p is None:
        return None
    vt = p.get("valuetype")
    if vt == "ParamChoice":
        return p.get("value")
    return p.get("value")
