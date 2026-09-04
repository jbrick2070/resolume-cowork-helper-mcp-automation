#!/usr/bin/env bash
# sync_to_kit.sh - copy the built pack into the Resolume MCP repo's house layout.
#
# The MCP repo is react-kit/ ->
#   github.com/jbrick2070/resolume-cowork-helper-mcp-automation
# where the earlier instruments live under beta/. This mirrors the pack into
# beta/earthsearch/ using the same folder shape as beta/nisei and
# beta/lexicon-ii, so the repo stays internally consistent.
#
# It copies and stages. It does NOT commit and does NOT push - publishing is a
# decision, not a build step.
set -euo pipefail

SRC="C:/Art Projects/Res_Fable/earthsearch"
DST="C:/Art Projects/Res_Fable/react-kit/beta/earthsearch"

mkdir -p "$DST/compositions" "$DST/controllers" "$DST/docs" "$DST/tools" \
         "$DST/reference"

cp "$SRC/output/EarthSearch_EP01_Live_Mix.avc"          "$DST/compositions/"
cp "$SRC/output/APC 40 MK II - EarthSearch EP01.xml"    "$DST/controllers/"
cp "$SRC"/docs/*.md                                      "$DST/docs/"
cp "$SRC/HANDOFF.md"                                     "$DST/docs/BUILD_LOG.md"
cp "$SRC"/build/*.py "$SRC"/build/*.ps1 "$SRC"/build/*.sh "$DST/tools/"
cp "$SRC"/reference/*.json                               "$DST/reference/"

echo "synced $(find "$DST" -type f | wc -l) files into beta/earthsearch/"
cd "C:/Art Projects/Res_Fable/react-kit"
git add beta/earthsearch
git status --short beta/earthsearch | sed 's/^/  /'
echo
echo "staged, not committed. To publish:"
echo "  cd 'C:/Art Projects/Res_Fable/react-kit' && git commit && git push"
