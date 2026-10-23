#!/usr/bin/env python3
"""Inline the palette, themes, engine.js, app.js and style.css into one
self-contained apc40_colour_lab.html (no network, no dependencies)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return f.read()


def main():
    pal = json.loads(read("apc_lab", "palette.json"))["colours"]
    th = json.loads(read("apc_lab", "themes.json"))
    data = "const PALETTE = %s;\nconst THEMES = %s;\nconst THEME_ORDER = %s;" % (
        json.dumps(pal), json.dumps(th["themes"]), json.dumps(th["order"]))
    html = read("demo", "page.html")
    for token, body in (("/*STYLE*/", read("demo", "style.css")), ("/*DATA*/", data),
                        ("/*ENGINE*/", read("demo", "engine.js")), ("/*APP*/", read("demo", "app.js"))):
        assert token in html, token
        html = html.replace(token, body)
    out = os.path.join(ROOT, "apc40_colour_lab.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote", out, len(html), "bytes")


if __name__ == "__main__":
    main()
