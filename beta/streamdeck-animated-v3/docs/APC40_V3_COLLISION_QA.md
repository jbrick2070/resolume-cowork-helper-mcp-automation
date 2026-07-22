# APC40 Animated Twin V3 -- Collision / Bounds QA

**Verdict: PASS**

- Controls: 148  |  geometry boxes: 306

## A. Territories disjoint (actual 0px overlap)
- Real cross-control box overlaps: **0** (PASS)
- Neighbours within the 4px design margin (informational, allowed): 13

## B. Structural containment
- Each element is rendered into a sub-tile of exactly its box and pasted at
  `box*SS`; ink cannot leave the box by construction.

## C. Empirical out-of-bounds ink (lit alpha outside all boxes, +/-2px)

| frame | lit px | outside-box px |
|---|---|---|
| 0 | 370219 | 0 |
| 20 | 363761 | 0 |
| 40 | 363462 | 0 |
| 60 | 369189 | 0 |
| 80 | 374936 | 0 |
| 100 | 376074 | 0 |
| 119 | 370361 | 0 |

- Worst: **0** (PASS)

## D. Rendered-ink intersection for at-risk neighbours (across loop)
- Pairs checked: 13  |  frames: [0, 30, 60, 90, 119]
- Worst shared pixels between any two controls: **0** (PASS)

  - Grid 1 Track 1 & Track Knob 1: 0px
  - Grid 1 Track 2 & Track Knob 2: 0px
  - Grid 1 Track 3 & Track Knob 3: 0px
  - Grid 1 Track 4 & Track Knob 4: 0px
  - Grid 1 Track 5 & Track Knob 5: 0px
  - Grid 1 Track 6 & Track Knob 6: 0px
  - Grid 1 Track 7 & Track Knob 7: 0px
  - Grid 1 Track 8 & Track Knob 8: 0px
  - Bank Up & Bank Down: 0px
  - Bank Up & Bank Right: 0px
  - Bank Up & Bank Left: 0px
  - Bank Down & Bank Right: 0px

A + B + C + D => the animated controls never exit their bounds or overlap, even during motion, pulses, or state changes.