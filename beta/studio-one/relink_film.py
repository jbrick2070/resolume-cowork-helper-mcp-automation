#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relink_film.py - point the Studio One FILM composition at wherever you put the clips.

The composition was built with the clips in  C:\\Resolume Clips\\studio_one.  If yours are
somewhere else (another drive, a Mac, a shared folder), run this once:

    python relink_film.py "D:\\VJ\\studio_one"
    python relink_film.py /Users/me/Movies/studio_one

It writes  "Studio One - War Of The Worlds 1938 FILM (relinked).avc"  next to the original,
leaving the original untouched, and tells you if any of the 40 clips is missing from the folder.
Standard library only; works on Windows, macOS and Linux (Avenue and Arena are Windows/macOS).
"""
import os
import re
import sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Studio One - War Of The Worlds 1938 FILM.avc")
DST = os.path.join(HERE, "Studio One - War Of The Worlds 1938 FILM (relinked).avc")
OLD = re.compile(r'C:\\Resolume Clips\\studio_one\\([^"]+?\.mov)')


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 1)
    folder = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if not os.path.isdir(folder):
        sys.exit("not a folder: %s" % folder)
    xml = open(SRC, encoding="utf-8").read()
    names = sorted(set(OLD.findall(xml)))
    if not names:
        sys.exit("no clip paths found in %s (already relinked?)" % os.path.basename(SRC))
    missing = [n for n in names if not os.path.exists(os.path.join(folder, n))]
    # clips may sit one level down if the zip was extracted into the chosen folder
    if len(missing) == len(names) and os.path.isdir(os.path.join(folder, "studio_one")):
        folder = os.path.join(folder, "studio_one")
        missing = [n for n in names if not os.path.exists(os.path.join(folder, n))]
    out = OLD.sub(lambda m: escape(os.path.join(folder, m.group(1)), {'"': "&quot;"}), xml)
    with open(DST, "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print("clips referenced: %d | found in %s: %d | missing: %d" % (
        len(names), folder, len(names) - len(missing), len(missing)))
    for n in missing[:10]:
        print("  missing:", n)
    print("wrote", DST)
    print("Open that file in Resolume, and copy 'APC 40 MK II - Studio One FILM.xml' to "
          "Documents/Resolume Avenue/Shortcuts/MIDI to use the APC40 layout.")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
