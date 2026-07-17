# Prompt 03 - APC40 mkII Layout Builder (the party trick)

Prereq: a comp you like (prompt 02 or your own). Your agent will WRITE A
CUSTOM CONTROLLER PRESET for it - grid colors and all. This is the "I did
not know an agent could do that" moment.

---

Generate a complete "APC 40 MK II" MIDI preset XML for my current Resolume
composition, and do not touch Resolume while you do it - this is a file job.

First READ my comp via the MCP: layer count and names, column count and
names, composition effects. Then author the preset:

- Grid: pads mirror the clip grid positionally - rows bottom-up = layers
  1-4, columns 1-8 = my scene columns. Clip-launch shortcuts per pad.
- COLOR FEEDBACK: assign each column a distinct pad color via the APC40
  mkII velocity color table (it is a 128-entry palette; pick saturated,
  distinguishable hues; playing/queued states come free from Resolume).
- Row 5 of the grid: bypass-toggle punch buttons for my composition
  effects, one per effect, in rack order.
- Scene launch column: top button triggers column 9 if I have one (my
  transit/finale column); bottom button = composition select-next-deck.
  Middle three: leave dark and say so.
- Faders 1-8 = layer opacities (extras unmapped), master = comp master,
  crossfader = crossfader. Device knobs 1 and 4: map to my first two
  comp-effect wet/amount params and TELL ME which.
- Every shortcut needs a unique id and a unique MIDI key. Note-number
  collisions are the classic failure - validate before you finish:
  count shortcuts, count unique ids, count unique MIDI keys, all equal.

Write the XML as UTF-8 without BOM, CRLF line endings, into a file I can
drop into Resolume's MIDI preset folder. Then print: total shortcut count,
the validation counts, and a 10-line "layout card" of what every control
does.

VERIFY (me): Preferences > MIDI: enable APC40 mkII as input AND output,
select the preset. The grid should light in my column colors within two
seconds. Pads launch clips; if a pad launches the WRONG clip, the grid
orientation is flipped - tell your agent, it is a 5-minute fix.
