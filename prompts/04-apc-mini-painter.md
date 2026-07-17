# Prompt 04 - APC mini mk2 Grid Painter (dual-surface rig)

Prereq: prompt 03. Adds an APC mini mk2 as a second surface: the mini
LAUNCHES, the 40 MIXES. Needs Python on your machine.

---

Set up my APC mini mk2 as a clip-launch surface next to the APC40 mkII.

1. Author a second Resolume MIDI preset for the mini: 8x8 grid of
   clip-launch shortcuts (layers 1-4 on the bottom four rows, columns 1-8;
   upper rows spare), unique ids and keys, same validation discipline as
   the APC40 preset (counts must match).
2. The mini mk2 does color via MIDI velocity + channel (channel selects
   solid/blink/pulse; velocity indexes the 128-color palette). Resolume's
   shortcut feedback only sends a few states, so write me a small Python
   script (python-rtmidi) - "grid painter" - that paints my column colors
   onto the mini's pads directly, and explain how it coexists with
   Resolume's own feedback (painter sets the base colors; Resolume's
   playing/queued feedback rides on top).
3. Division of labor doc, 10 lines: mini = launching scenes and cells,
   APC40 = faders, knobs, FX punches, transit button. No duplicated
   controls between surfaces.
4. Tell me how to autostart the painter script when I plug the mini in
   (a shortcut or a tiny watcher - your call, simplest wins).

Guardrails: this is a file + script job; do not touch my composition.
If python-rtmidi is not installed, give me the one-line install and wait.

VERIFY (me): plug both in, run the painter - the mini shows my column
colors; pressing a mini pad launches the same cell as the matching APC40
pad; nothing double-fires.
