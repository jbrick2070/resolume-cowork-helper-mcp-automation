"""Submit an API-format graph to local ComfyUI, wait, print a compact JSON summary.

usage: python -I run_api.py GRAPH.json [TIMEOUT_SECONDS]
"""
import json
import sys
import time
import urllib.request
import uuid

SERVER = "http://127.0.0.1:8000"
graph = json.load(open(sys.argv[1], encoding="utf-8"))
timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 1800


def post(path, body):
    req = urllib.request.Request(
        SERVER + path, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode("utf-8", "replace")[:3000]}


def get(path):
    return json.load(urllib.request.urlopen(SERVER + path, timeout=60))


t0 = time.time()
resp = post("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})
if "prompt_id" not in resp:
    print(json.dumps({"ok": False, "stage": "submit", "resp": resp})[:3500])
    sys.exit(2)
pid = resp["prompt_id"]

while True:
    time.sleep(3)
    h = get("/history/" + pid)
    if pid in h:
        rec = h[pid]
        st = rec.get("status", {})
        files = []
        for nid, o in (rec.get("outputs") or {}).items():
            for key in ("images", "videos", "gifs", "audio"):
                for f in o.get(key, []) or []:
                    files.append(f"{f.get('subfolder','')}/{f.get('filename')}")
        err = None
        if st.get("status_str") != "success":
            for m in st.get("messages", []):
                if m[0] == "execution_error":
                    d = m[1]
                    err = {"node": d.get("node_id"), "type": d.get("node_type"),
                           "msg": str(d.get("exception_message"))[:600]}
        print(json.dumps({"ok": st.get("status_str") == "success", "prompt_id": pid,
                          "seconds": round(time.time() - t0, 1), "files": files, "error": err}))
        sys.exit(0 if st.get("status_str") == "success" else 1)
    if time.time() - t0 > timeout:
        print(json.dumps({"ok": False, "stage": "timeout", "prompt_id": pid}))
        sys.exit(3)
