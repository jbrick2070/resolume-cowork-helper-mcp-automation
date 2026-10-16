#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_to_kit.py - mirror a built pack into the public kit repo checkout
(react-kit/ -> github.com/jbrick2070/resolume-cowork-helper-mcp-automation)
in the same folder shape as beta/earthsearch, beta/nisei, beta/lexicon-ii.

    python -m resolume_build.sync_to_kit packs/dead-air dead-air

Copies:  <pack>/*.avc *.xml README.md BUILD_REPORT.txt manifest.json
         bible.json decks.json docs/   -> react-kit/beta/<slug>/
         resolume_build/*.py            -> react-kit/beta/tools/resolume_build/
         harvest/harvest_7281.py + out/*.json -> react-kit/beta/tools/harvest/
Never copies the harvest .avc scratch files or anything under _dryrun.
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, "react-kit", "beta")


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def main():
    pack_dir, slug = sys.argv[1], sys.argv[2]
    pack_dir = os.path.abspath(pack_dir)
    dst = os.path.join(KIT, slug)
    n = 0
    for name in os.listdir(pack_dir):
        p = os.path.join(pack_dir, name)
        if name.startswith("_") or name.startswith("."):
            continue
        if os.path.isdir(p):
            if name == "docs":
                for f in os.listdir(p):
                    copy(os.path.join(p, f), os.path.join(dst, "docs", f))
                    n += 1
            continue
        if name.endswith((".avc", ".xml", ".md", ".txt", ".json")):
            copy(p, os.path.join(dst, name))
            n += 1
    tools = os.path.join(KIT, "tools")
    for f in os.listdir(os.path.join(ROOT, "resolume_build")):
        if f.endswith((".py", ".js")) and not f.startswith("_"):
            copy(os.path.join(ROOT, "resolume_build", f),
                 os.path.join(tools, "resolume_build", f))
            n += 1
    copy(os.path.join(ROOT, "harvest", "harvest_7281.py"),
         os.path.join(tools, "harvest", "harvest_7281.py"))
    for f in os.listdir(os.path.join(ROOT, "harvest", "out")):
        if f.endswith(".json") and not f.startswith("_"):
            copy(os.path.join(ROOT, "harvest", "out", f),
                 os.path.join(tools, "harvest", "out", f))
            n += 1
    print("mirrored %d files into %s" % (n, dst))


if __name__ == "__main__":
    main()
