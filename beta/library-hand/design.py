#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py - the creative bible and all 320 clip recipes for THE LIBRARY AND
THE HAND, a stock-only Avenue 7.28.1 instrument cut from the GUSTO feasibility
script ("The Library And The Hand", 21 scenes) and its locked palette:

    lacquer #17171C   paper-white #F2EFE8   stylus-cyan #3CC6D0   cue-orange #F2792B

The script's data convention is the pack's whole visual grammar: SOLID
stylus-cyan = documented fact, DASHED cue-orange = proposal / target /
estimate, dimmed paper-white = everything else. No other colours exist.

    python packs/library-hand/design.py      -> bible.json + decks.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

LACQ = "#17171cff"
LACQ2 = "#24242bff"      # lacquer lifted one step: the grid ruling
PAPER = "#f2efe8ff"
PAPER_DIM = "#f2efe866"
CYAN = "#3cc6d0ff"
CYAN_DIM = "#3cc6d066"
ORANGE = "#f2792bff"
ORANGE_DIM = "#f2792b66"
CLEAR = "#00000000"

MONO = "Cascadia Mono"
MONO2 = "Consolas"
HEAD = "Bahnschrift"

# The locked-groove click: one tick per revolution. Stroboscope Frequency
# 0.3 measured near a 1.34 s period on this rig (Dead Air), so 33 1/3 rpm
# (1.8 s) sits near 0.22 and 45 rpm (1.33 s) near 0.3.
CLICK_33 = 0.22
CLICK_45 = 0.3


# ---------------------------------------------------------------- helpers
def fft(param, band, floor, ceiling, gain=9.0, release=500):
    return {param: {"band": band, "gain": gain, "release": release,
                    "floor": floor, "ceiling": ceiling}}


def clip(layer, column, name, source, params, why, opacity=1.0, fft=None,
         effects=None):
    return {"layer": layer, "column": column, "name": name[:18],
            "source": source, "params": params, "fft": fft or {},
            "effects": effects or [], "opacity": opacity, "why": why}


def xform(x=0, y=0, scale=100, rot=0):
    return {"effect": "Transform", "params": {"Position X": x, "Position Y": y,
                                             "Scale": scale, "Rotation Z": rot}}


# --- BED: the lacquer grid (horizontal ruling; GRAIN adds the vertical)
def ruling(col, amount=18, width=0.012, color=LACQ2, rotation=0, opacity=1.0,
           name="Lacquer Grid", why="The isometric lacquer grid every scene stands on."):
    return clip(1, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": width,
                 "Rotation": rotation, "Position": 0.5, "Color": color},
                why, opacity=opacity)


def floor_iso(col, color=LACQ2, height=4.0, speed=0.15, opacity=0.9,
              name="Iso Floor", why="A tilted wireframe floor: the booth seen from the isometric camera."):
    return clip(1, col, name, "Line Scape",
                {"Tilt": 62.0, "Direction": 0.0, "Position Y": 6.0,
                 "Speed": speed, "Height": height, "Jagginess": 0.0,
                 "Wobble": 0.0, "Attenuation": 140.0, "Line Width": 0.25,
                 "Fuzzyness": 0.0, "Color": color, "Show Knots": False},
                why, opacity=opacity)


def black(col, name="Lacquer", why="Black lacquer; nothing is drawn yet."):
    return clip(1, col, name, "Solid Color", {"Color": LACQ}, why)


# --- the 12-inch disc in wireframe
def disc(layer, col, color=PAPER, rings=9, size=0.55, width=0.012, spacing=0.12,
         rotation=0.0, name="12-Inch Disc", opacity=1.0, fft_=None,
         why="The twelve-inch record as concentric wireframe grooves, turning flat at frame centre.",
         effects=None):
    return clip(layer, col, name, "Rings",
                {"Num Rings": rings, "Size": size, "Spacing": spacing,
                 "Line Width": width, "Style": "Stroke", "Gap": 0.0,
                 "Rotation": rotation, "Rotation Step": 0.0,
                 "Rotation Alternate": False, "Color 1": color,
                 "Color 2": color}, why, opacity=opacity,
                fft=fft_ if fft_ is not None else fft("Line Width", "low", width, width * 3.0, 9.0, 400),
                effects=effects)


def groove(layer, col, color=PAPER, speed=0.18, zoom=1.0, leafs=1, name="Locked Groove",
           opacity=0.8, direction="Clockwise",
           why="One spiral groove at 33 1/3: the locked run-out that the click rides."):
    return clip(layer, col, name, "Spiral",
                {"Direction": direction, "Control Mode": "Even",
                 "Spread Even": 1.2, "Detail": 1.0, "Speed": speed,
                 "Zoom": zoom, "Leafs": leafs, "Distortion": 0.0,
                 "Fuzzyness": 0.0, "Ramification": 0.0, "Button": True,
                 "Button Size": 0.12, "Button Fuzzyness": 0.0, "Color": color,
                 "BG Color": CLEAR}, why, opacity=opacity,
                fft=fft("Spread Even", "low", 1.0, 1.6, 8.0, 500))


# --- the hall of plinths / corridors
def hall(layer, col, c1=PAPER_DIM, c2=CYAN_DIM, zoom=1.6, freq=0.06, width=0.008,
         name="Hall Of Plinths", opacity=0.7,
         why="A long wireframe hall receding to a point: the plinths stand along it."):
    return clip(layer, col, name, "Tunnelines",
                {"Color 1": c1, "Color 2": c2, "Line Width": width,
                 "Zoom": zoom, "Vertical": 0.06, "Frequency": freq,
                 "Horizontal": 0.09}, why, opacity=opacity,
                fft=fft("Frequency", "mid", freq, freq + 0.12, 8.0, 900))


# --- rails, racks, bars
def rail(layer, col, color=ORANGE, amount=3, width=0.02, rotation=0, position=0.5,
         name="Rail", opacity=1.0, fft_=None,
         why="The one-metre rail as a dashed orange line across the floor."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": width,
                 "Rotation": rotation, "Position": position, "Color": color},
                why, opacity=opacity, fft=fft_ or {})


def rack(layer, col, color=CYAN, amount=24, width=0.03, name="Record Rack",
         opacity=0.9, why="Bare discs on edge in a slotted rack: vertical ruling in cyan."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.05, "Amount": amount, "Width": width,
                 "Rotation": 90.0, "Position": 0.5, "Color": color}, why,
                opacity=opacity, fft=fft("Fuzzyness", "high", 0.02, 0.25, 7.0, 300))


# --- the hand / grip / callouts
def dot(layer, col, color=ORANGE, scale=0.08, outline=0.0, name="Scratch Head",
        opacity=1.0, effects=None, fft_=None,
        why="The proposed scratch head hovering above the label, clear of the grooves."):
    return clip(layer, col, name, "Shaper",
                {"Scale": scale, "Noise Type": "Grain", "Noise Amount": 0.0,
                 "Noise Speed": 0.0, "Color": color, "Outline": outline,
                 "Outline Color": color}, why, opacity=opacity,
                effects=effects, fft=fft_ if fft_ is not None else fft("Scale", "low", scale, scale * 1.6, 9.0, 350))


def cups(layer, col, color=CYAN, grid=3, size=0.22, speed=0.4, name="Suction Cups",
         opacity=0.9, why="Soft suction cups and grip pads breathing as metaballs."):
    return clip(layer, col, name, "Metaballs",
                {"Grid": grid, "Blend": "Minimal", "Size": size,
                 "Distance": 0.5, "Radius": 0.5, "Fuzzyness": 0.15,
                 "Speed": speed, "Position X": 0.0, "Position Y": 0.0,
                 "Color": color, "BG Color": CLEAR}, why, opacity=opacity,
                fft=fft("Size", "low", size, min(0.95, size + 0.25), 9.0, 400))


def marker(layer, col, nx=6, ny=6, c1=LACQ, c2=PAPER, name="ArUco Marker",
           opacity=1.0, effects=None,
           why="A black-and-white marker square: a dictionary ID, not catalog text."):
    return clip(layer, col, name, "Checkered",
                {"Num X": nx, "Num Y": ny, "Color 1": c1, "Color 2": c2}, why,
                opacity=opacity, effects=effects)


def geo(layer, col, shape="Hexagon", c1=CYAN, c2=CYAN, name="Pattern",
        opacity=0.9, lines=12, why="A geometry pattern as a machined part."):
    return clip(layer, col, name, "Geometry Pattern Maker",
                {"Bloom": 0.1, "Bloom Mode": "Add", "Shape Types": shape,
                 "Shape Rounding": 0.1, "Line Ammount": lines,
                 "Innter Color 1": c1, "Inner color 2": c2,
                 "Outer Color 1": c1, "Outer Color 2": c2,
                 "Inner Scale": 0.35, "Outer Scale": 1.4,
                 "Intersect Scale": 0.6}, why, opacity=opacity,
                fft=fft("Inner Scale", "mid", 0.3, 0.5, 8.0, 500))


# --- light: the click, the work lamp, washes
def click(col, rpm=33, color=PAPER, opacity=0.18, name="Locked Groove Click",
          why="The one sampled stylus click per revolution, as a one-frame paper flash."):
    return clip(4, col, name, "Stroboscope",
                {"Frequency": CLICK_33 if rpm == 33 else CLICK_45,
                 "Fade": False, "Color 1": color, "Color 2": CLEAR}, why,
                opacity=opacity)


def lamp(col, color=PAPER, opacity=0.28, name="Work Lamp", layer=4,
         why="One work lamp: a radial paper-white pool with lacquer at the edges."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": color, "Color 2": CLEAR,
                 "Mode": "Smooth", "Dither": 0.0, "Type": "Radial"}, why,
                opacity=opacity)


def wash(col, color, kind="Vertical", opacity=0.12, name="Wash", layer=6,
         why="An edge wash in the scene's evidence colour."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": CLEAR, "Color 2": color,
                 "Mode": "Smooth", "Dither": 0.0, "Type": kind}, why,
                opacity=opacity)


def flat(col, color, opacity=0.08, name="Gel", layer=6,
         why="A flat colour gel over the whole frame."):
    return clip(layer, col, name, "Solid Color", {"Color": color}, why,
                opacity=opacity)


def blank(layer, col, why="Nothing here by design."):
    return clip(layer, col, "Blank", "Blank", {"Black BG": False}, why)


# --- text
NL = chr(10)

def wrap(s, n=22):
    """Every caption line <= n chars (the builder's legibility limit)."""
    out = []
    for line in s.split(NL):
        cur = ""
        for w in line.split(" "):
            if cur and len(cur) + 1 + len(w) > n:
                out.append(cur)
                cur = w
            else:
                cur = (cur + " " + w) if cur else w
        out.append(cur)
    return NL.join(out)


# How Avenue 7.28.1 places a Text Block, measured on the rig (2026-10-23):
#   * Position X is the CENTRE of the Line Width box; Alignment only justifies lines inside it.
#   * AlignmentVertically picks the FRAME EDGE the block is aligned to (Top / Center / Bottom),
#     and Position Y is an offset downward from that edge, not from the frame centre.
# text()'s x/y keep their natural meaning (where the text's align/valign corner sits, in pixels
# from the frame centre, y down) and are translated here. Before this, a bottom caption at
# y=460 was pushed 460 px BELOW the bottom edge, and left-aligned text started off the left edge.
TEXT_LINE_W = 1400.0
HALF_H = 540.0


def text_block_place(align, valign, x, y, line_w=TEXT_LINE_W):
    """(Position X, Position Y, AlignmentVertically) that put a Text Block's (align, valign)
    corner at (x, y), in composition pixels from the centre, y down."""
    bx = x + line_w / 2.0 if align == "Left" else x - line_w / 2.0 if align == "Right" else x
    by = y - HALF_H if valign == "Bottom" else y + HALF_H if valign == "Top" else y
    return bx, by, valign


def text(col, s, color=CYAN, size=0.9, font=MONO, align="Left", valign="Bottom",
         x=-860, y=460, animated=False, delay=90, name=None, layer=5,
         why="On-screen text in the script's monospace, cyan for documented, orange for proposed."):
    """Multi-line captions are Text Block (rig-proven with newlines in Dead
    Air); a single animated line is Text Animator so the pad can retype it.
    (x, y) is where the text's (align, valign) corner sits. Text Animator placement was not
    re-measured; every Text Animator these packs build is centred at (0, 0)."""
    s = wrap(s)
    if animated and NL not in s:
        # measured: a centred stamp is about 0.04 of the frame width per character per unit of Size, so keep it
        # inside 88% of the frame ("ROLL IT" at 2.0 spans 0.55; "CTRL - SHIFT - K" at 2.0 overflowed)
        size = min(size, round(0.88 / (0.0395 * max(1, len(s))), 2))
        p = {"Text": s, "Font": font, "Style": "Regular", "Color": color,
             "Size": size, "Alignment": align, "AlignmentVertically": valign,
             "Position X": x, "Position Y": y, "Animated": True,
             "Glow In": 0.0, "Glow Out": 0.0, "Outline Width": 0.0,
             "Range": "Characters", "Order": "Front to back",
             "Delay": delay, "Opacity": 1.0, "Scale": 1.0}      # 0.0 / 0.9 never revealed on the rig (probed 2026-10-23)
        src = "Text Animator"
    else:
        bx, by, bvalign = text_block_place(align, valign, x, y)
        p = {"Text": s, "Font": font, "Style": "Regular", "Color": color,
             "Size": size, "Alignment": align, "AlignmentVertically": bvalign,
             "Line Width": TEXT_LINE_W, "Position X": bx, "Position Y": by,
             "Spacing Y": 12.0, "Outline Width": 0.0, "Glow In": 0.0,
             "Glow Out": 0.0}
        src = "Text Block"
    return clip(layer, col, name or s.split(NL)[0], src, p, why)


def stamp(col, s, color=PAPER, size=2.2, font=HEAD, layer=5, animated=True,
          why="A stamp across the centre of the frame."):
    return text(col, s, color=color, size=size, font=font, align="Center",
                valign="Center", x=0, y=0, animated=animated, delay=60,
                layer=layer, why=why)


# --- grain: vertical ruling completes the grid; or hatching
def vruling(col, amount=32, width=0.012, color=LACQ2, opacity=1.0,
            name="Grid Columns", why="The vertical half of the lacquer grid."):
    return clip(7, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": width,
                 "Rotation": 90.0, "Position": 0.5, "Color": color}, why,
                opacity=opacity)


def hatch(col, color=PAPER, opacity=0.08, rotation=45.0, amount=60,
          name="Hatching", why="Hatched vector fill: heavy platter hatching, never a texture."):
    return clip(7, col, name, "Lines",
                {"Fuzzyness": 0.1, "Amount": amount, "Width": 0.01,
                 "Rotation": rotation, "Position": 0.5, "Color": color}, why,
                opacity=opacity, fft=fft("Fuzzyness", "high", 0.05, 0.4, 7.0, 300))


# --- scope: requested vs actual record motion
def scope(col, color=ORANGE, position=0.86, amplitude=0.05, waves=1, width=0.03,
          name="Record Motion", opacity=1.0, speed=2.0,
          why="ACTUAL RECORD ANGLE: a dashed-orange trace that follows the music 1:1."):
    return clip(8, col, name, "Sine Wave",
                {"Waves": waves, "Mode": "Line", "Line Width": width,
                 "Fuzzyness": 0.05, "Direction": "Horizontal", "Mirror": False,
                 "Frequency": 3.0, "Main Speed": speed, "Modulator": 2.0,
                 "Modulation Depth": 0.4, "Modulator Speed": 1.0,
                 "Amplitude": amplitude, "Position": position, "Color": color,
                 "BG Color": CLEAR}, why, opacity=opacity,
                fft={**fft("Amplitude", "mid", amplitude, 0.32, 10.0, 300),
                     **fft("Line Width", "low", width, width * 3, 8.0, 400)})


def swing(layer, col, color=PAPER, waves=2, amp=0.25, position=0.5, width=0.02,
          speed=3.0, name="Reversal Trace", opacity=0.9,
          why="The scratch stroke as a sine: backward and forward in time."):
    return clip(layer, col, name, "Sine Wave",
                {"Waves": waves, "Mode": "Line", "Line Width": width,
                 "Fuzzyness": 0.0, "Direction": "Horizontal", "Mirror": False,
                 "Frequency": 0.0, "Main Speed": speed, "Modulator": 0.0,
                 "Modulation Depth": 0.0, "Modulator Speed": 1.0,
                 "Amplitude": amp, "Position": position, "Color": color,
                 "BG Color": CLEAR}, why, opacity=opacity,
                fft=fft("Amplitude", "low", amp, min(1.0, amp + 0.4), 9.0, 350))


# ================================================================ DECK 1
# THE PLINTHS - scenes 01-07, 33 1/3 rpm, the documented precedents
def deck1():
    C = []
    cols = ["Cold Open", "Six Jobs", "Glenton 150", "Rocket LP",
            "Maker Rail", "Juke Bots", "Scripted Shows", "DJ I Robot"]
    # 1 Cold Open: one disc on black, the hand stops before contact
    C += [black(1, why="Black. A single disc turns at frame centre."),
          disc(2, 1, rings=10, size=0.6),
          dot(3, 1, color=ORANGE, scale=0.07, outline=0.08,
              effects=[xform(y=180, scale=100)],
              why="The dashed proposed hand enters above and stops just before contact."),
          click(1, 33),
          text(1, "GUSTO\nFEASIBILITY STUDY", color=PAPER, size=1.0, font=HEAD,
               why="Cold-open title, paper-white, bottom-left."),
          blank(6, 1, "No colour claim yet: nothing is documented, nothing is proposed."),
          blank(7, 1, "No grid in the cold open; the grid arrives with the specification."),
          scope(1)]
    # 2 Six Jobs: the empty booth, six requirement tags drop in, all orange
    C += [ruling(2), hall(2, 2, c1=LACQ2, c2=PAPER_DIM, zoom=1.2, opacity=0.5,
                         name="Empty Booth", why="Isometric plan of an empty booth on the lacquer grid."),
          rail(3, 2, color=ORANGE, amount=6, width=0.05, rotation=90.0,
               name="Six Tags", why="Six requirement tags in a row, dashed orange: specified, not built.",
               fft_=fft("Width", "low", 0.04, 0.12, 9.0, 350)),
          click(2, 33),
          text(2, "RANDOM ACCESS - FLIP\nDUAL DECK - BEATMATCH\nSCRATCH - CUT",
               color=ORANGE, size=0.8, animated=True, delay=70,
               why="The six jobs typed on, one tag at a time, in proposal orange."),
          wash(2, ORANGE_DIM, opacity=0.08),
          vruling(2),
          scope(2)]
    # 3 Glenton 150: the cabinet under a dome; 150 discs on edge; two stone platters
    C += [ruling(3), rack(2, 3, color=CYAN, amount=30, width=0.025,
                          name="150 LPs On Edge",
                          why="One hundred fifty bare discs standing on edge in an illuminated rack."),
          disc(3, 3, color=CYAN, rings=5, size=0.3, width=0.015, name="Stone Platters",
               effects=[xform(x=-380, y=-120, scale=70)],
               why="Two stone turntables, documented, so the disc is cyan; left platter."),
          lamp(3, color=CYAN_DIM, opacity=0.2, name="Glass Dome",
               why="The glass-outline dome as a soft cyan radial over the cabinet."),
          text(3, "GLENTON 150\n150 LPs - 2 STONE DECKS\n169 x 215 x 104 CM",
               color=CYAN, size=0.8, why="Dimension lines in solid cyan, from the manufacturer's page."),
          wash(3, CYAN_DIM, opacity=0.08, kind="Radial"),
          vruling(3),
          scope(3, color=CYAN, why="The platter's rotation, documented: cyan.")]
    # 4 Rocket LP: the chrome jukebox, 1950s silhouette, a magazine of LPs
    C += [ruling(4), geo(2, 4, shape="Circle", c1=PAPER_DIM, c2=CYAN, lines=10,
                         name="Chrome Rocket",
                         why="The Anniversary Rocket's chrome silhouette as round wireframe geometry."),
          rack(3, 4, color=CYAN, amount=10, width=0.05, name="Ten LP Magazine",
               why="Ten LPs in the magazine; the VLP-20 holds twenty on a separate outline."),
          click(4, 33),
          text(4, "SOUND LEISURE LP\nCONCEPT 1968 - LAUNCHED\n13 OCT 2018", color=CYAN,
               size=0.8, why="Two date stamps drop in solid cyan."),
          wash(4, CYAN_DIM, opacity=0.1, kind="Horizontal"),
          vruling(4),
          scope(4, color=CYAN)]
    # 5 Maker Rail: Robot DJ v1 -> v2, the 1 m rail, five CANopen nodes
    C += [floor_iso(5, color=LACQ2),
          rail(2, 5, color=CYAN, amount=1, width=0.03, position=0.5,
               name="One Metre Rail", why="The one-metre linear stage, a physical mechanism: cyan."),
          cups(3, 5, color=CYAN, grid=2, size=0.2, name="Silicone Cups",
               why="v1's two custom silicone suction cups; v2's edge gripper replaces them."),
          click(5, 33),
          text(5, "ROBOT DJ v1 -> v2\n1 M RAIL - 5-NODE CANopen\nPHYSICAL BUILD INCOMPLETE",
               color=CYAN, size=0.8, why="Published design details in cyan; the unfinished route stays dashed."),
          wash(5, ORANGE_DIM, opacity=0.1, kind="Horizontal",
               why="The simulated full workflow as an orange wash: it does not turn the machine cyan."),
          hatch(5, color=PAPER, opacity=0.06),
          scope(5, color=ORANGE,
                why="The simulation window's motion, dashed orange.")]
    # 6 Juke Bots: two KUKA arms in a ring of 22 records, disc held at centre
    C += [ruling(6), disc(2, 6, color=CYAN, rings=22, size=0.9, width=0.01, spacing=0.1,
                          name="22 Records Ring",
                          why="Twenty-two records in racks, ringed around both arms; the safety perimeter."),
          dot(3, 6, color=CYAN, scale=0.26, outline=0.05, name="Held Disc",
              fft_=fft("Scale", "low", 0.22, 0.34, 10.0, 300),
              why="One arm holds a disc at its centre and rotates it against a stylus: forward, back, fast, slow."),
          click(6, 33),
          text(6, "robotlab - juke_bots\n2001-2007 - 22 RECORDS\nNO PLAYBACK PLATTER", color=CYAN,
               size=0.8, why="Exhibition labels tick past in cyan."),
          wash(6, CYAN_DIM, opacity=0.1, kind="Radial"),
          vruling(6),
          scope(6, color=CYAN, amplitude=0.08,
                why="The held disc against the stylus: documented scratching, cyan.")]
    # 7 Scripted Shows: three film-strip bands, YuMi / Automatica / DJ Kuka
    C += [ruling(7), rail(2, 7, color=PAPER_DIM, amount=3, width=0.18, rotation=0.0,
                          name="Film Strip Bands",
                          why="Three translucent wireframe film-strip bands, one per show."),
          rail(3, 7, color=CYAN, amount=14, width=0.02, rotation=90.0,
               name="Sprocket Holes", why="Sprocket ruling across the bands: edited video, time adjustment, compositing.",
               fft_=fft("Width", "high", 0.015, 0.05, 8.0, 250)),
          click(7, 33),
          text(7, "YuMi - AUTOMATICA - DJ KUKA\nPERFORMANCE != COMPLETE\nAUTONOMY", color=CYAN, size=0.8,
               why="Documented productions in cyan; no blanket NO FEEDBACK label."),
          blank(6, 7, "No wash: three different demonstrations, not interchangeable proofs."),
          vruling(7),
          scope(7, color=CYAN)]
    # 8 DJ I Robot: three servo icons, a dashed reconstruction of records and mixer
    C += [ruling(8), cups(2, 8, color=CYAN, grid=3, size=0.18, speed=0.3,
                          name="Three Servos", why="Three solid cyan servo icons."),
          disc(3, 8, color=ORANGE, rings=6, size=0.4, width=0.01, name="Deck Schematic",
               why="A dashed reconstruction of records and a mixer: SCHEMATIC - DECK LAYOUT NOT VERIFIED."),
          click(8, 33),
          text(8, "DJ I, ROBOT - MIT\n1998 / 1999 / 2001\nEARLIER SCRATCH / CUT / MIX", color=CYAN,
               size=0.8, why="Three separate milestones kept distinct."),
          wash(8, ORANGE_DIM, opacity=0.08, kind="Vertical"),
          vruling(8),
          scope(8, color=ORANGE)]
    return {"name": "The Plinths", "slug": "plinths", "theme": "documented",
            "world": ("A long wireframe hall of glass-outline plinths, each holding a small machine that "
                      "already exists: a domed cabinet, a chrome jukebox, an aluminium rail, two industrial "
                      "arms, a servo on a fader. The camera dollies past them at 33 1/3 rpm with one stylus "
                      "click per revolution. Everything documented is SOLID stylus-cyan; the one thing that "
                      "does not exist, the whole machine, is a dashed orange booth that stops drawing itself "
                      "halfway. Register: feasibility-study captions in Cascadia Mono, bottom-left."),
            "palette": [{"role": "bed", "hex": "#17171c", "why": "Lacquer. The locked black every scene stands on."},
                        {"role": "body", "hex": "#f2efe8", "why": "Paper-white wireframe for the disc and the hall; dimmed to 40% when it is context."},
                        {"role": "figure", "hex": "#3cc6d0", "why": "Stylus-cyan: a documented machine, a published spec, an attributed claim."},
                        {"role": "light", "hex": "#f2efe8", "why": "The click is paper-white and one frame long."},
                        {"role": "text", "hex": "#3cc6d0", "why": "Captions take the evidence colour of what they describe."},
                        {"role": "aura", "hex": "#f2792b", "why": "Cue-orange: proposal, reconstruction, estimate. Only ever a wash here."}],
            "columns": cols,
            "text_corpus": ["GUSTO", "RETRIEVE - FLIP - TWO PLAYERS", "SCRATCH - CUT",
                            "GLENTON 150", "150 LPs", "~EUR 100,000 REPORTED",
                            "SOUND LEISURE LP", "ROBOT DJ v1 -> v2", "juke_bots",
                            "PERFORMANCE != AUTONOMY", "DJ I, ROBOT", "NOT DOCUMENTED"],
            "moments": [
                "Cold open: fire Scene Launch 1 with every effect off and the crossfader hard right, so only the "
                "disc, the orange hand and the title exist; let the click run for a full phrase before anything moves.",
                "The hall: walk UP through Glenton, Rocket and Maker Rail with Device knob 2 (TEXTURE) at a third and CRT lit "
                "so the plinths read as a console; tap the row-5 TEXT pad on each downbeat so the dimension lines retype.",
                "juke_bots: Scene Launch 6, then hold the row-3 FIGURE pad and turn Device knob 6 (ECHO) up "
                "so the held disc leaves a cyan afterimage against the stylus; drop it to zero on the breakdown."],
            "clips": C}


# ================================================================ DECK 2
# THE HAND - scenes 08-13, the click shifts to 45 rpm
def deck2():
    C = []
    cols = ["Scratchbot", "Five Hour Clock", "Seven vs Twelve",
            "Inertia Gap", "Two Separations", "Circle Trap", "Millimetres", "Swing-In Hand"]
    # 1 Scratchbot: a student desk, a hobby servo crank on the fader
    C += [floor_iso(1, color=LACQ2, height=3.0),
          swing(2, 1, color=CYAN, waves=1, amp=0.18, speed=4.0, name="Servo Sweep",
                why="A two-servo arm pivots over the spindle: one presses the pad, one sweeps it."),
          dot(3, 1, color=CYAN, scale=0.06, outline=0.1, name="Crank On Fader",
              effects=[xform(x=520, y=-300, scale=100)],
              why="A hobby servo with a 3D-printed crank moving the crossfader stem, bottom right."),
          click(1, 45),
          text(1, "SCRATCHBOT - 2015\nARDUINO MEGA 2560\nHEEL CUSHION - GRIP-MAT", color=CYAN,
               size=0.8, why="Pad materials: tried and struck through, then the two that worked."),
          lamp(1, color=PAPER_DIM, opacity=0.18, layer=6, name="Desk Lamp",
               why="A single work lamp over a desk-sized plinth."),
          vruling(1, amount=48, width=0.008),
          scope(1, color=CYAN, amplitude=0.08, speed=3.0,
                why="The pad's sweep around the spindle, documented.")]
    # 2 Five Hour Clock: MIDI clock ticks count and reset; the laptop glows; thermal
    C += [ruling(2, amount=32, width=0.006),
          rail(2, 2, color=CYAN, amount=24, width=0.012, rotation=90.0, name="Clock Ticks",
               fft_=fft("Fuzzyness", "high", 0.0, 0.5, 9.0, 200),
               why="Clock ticks counting against beat-phase messages; hi-hats smear them into jitter."),
          geo(3, 2, shape="Square", c1=CYAN, c2=ORANGE, lines=8, name="Laptop Heat",
              why="The laptop glows: timing becomes unstable at 5:00:00. REPORTED THERMAL THROTTLING."),
          click(2, 45),
          text(2, "5:00:00 - MIDI SYNC TEST\nTRAKTOR > loopMIDI >\nHAIRLESS > MEGA 2560", color=CYAN,
               size=0.8, why="The signal line from the laptop, in cyan: a documented chain."),
          wash(2, ORANGE_DIM, opacity=0.14, kind="Radial",
               why="Heat as an orange radial that grows with the mids: reported, not measured."),
          vruling(2, amount=64, width=0.004),
          scope(2, color=CYAN, amplitude=0.04, waves=4, speed=6.0, name="Beat Phase",
                why="Beat-phase error trace: steady until the throttle.")]
    # 3 Seven vs Twelve: the record-size comparison, same scale, two clicks hold
    C += [ruling(3),
          disc(2, 3, color=PAPER, rings=12, size=0.62, width=0.01, name="12-Inch 180 g",
               effects=[xform(x=260, scale=100)],
               why="The twelve-inch LP at fixed camera scale, right of centre."),
          disc(3, 3, color=PAPER_DIM, rings=6, size=0.36, width=0.01, name="7-Inch 40 g",
               effects=[xform(x=-420, scale=100)],
               why="The seven-inch single, same scale, so the larger radius is immediately apparent."),
          click(3, 45),
          text(3, "7-INCH: WORKED OKAY\n12-INCH: POOR\nPERFORMANCE", color=CYAN, size=0.9,
               why="The builder's own words."),
          blank(6, 3, "Two outlines, two clicks, nothing else."),
          vruling(3),
          scope(3, color=ORANGE, amplitude=0.03,
                why="A dashed reconstruction of inadequate motion and possible slip: hypothetical.")]
    # 4 Inertia Gap: exploded side elevation, platter hatching, formula, ratio bars
    C += [ruling(4, amount=6, width=0.02, color=PAPER_DIM, opacity=0.5, name="Exploded Layers",
                 why="Three stacked layers in side elevation: platter, slipmat, record."),
          rail(2, 4, color=ORANGE, amount=2, width=0.14, rotation=90.0, position=0.62,
               name="Ratio Bars", fft_=fft("Width", "low", 0.1, 0.3, 10.0, 400),
               why="Illustrative ratio bars, dashed: 13.2 x inertia for the same angular acceleration."),
          swing(3, 4, color=PAPER, waves=3, amp=0.2, speed=5.0, name="Requested vs Actual",
                why="A paper-white requested trajectory; the dashed record response diverges under SIMULATED LIMIT."),
          click(4, 45),
          text(4, "I ~ 1/2 m r^2\n180 g LP ~ 13.2 x 40 g SINGLE\n8-15 REVERSALS/s", color=ORANGE,
               size=0.9, font=MONO2, why="The formula and the reversal-rate target, orange: a model, not a measurement."),
          wash(4, ORANGE_DIM, opacity=0.1, kind="Horizontal"),
          hatch(4, color=PAPER, opacity=0.16, rotation=45.0, amount=80, name="Platter Hatch",
                why="Heavy hatching on the aluminium platter."),
          scope(4, color=ORANGE, amplitude=0.1, waves=2, speed=5.0,
                why="Record angle diverging from motor angle.")]
    # 5 Two Separations: wall drops between library and hand; sleeve to drawer
    C += [floor_iso(5, color=LACQ2),
          rail(2, 5, color=ORANGE, amount=1, width=0.03, rotation=90.0, position=0.5,
               name="The Wall", why="A dashed orange wall drops between back (library) and front (hand)."),
          swing(3, 5, color=ORANGE, waves=6, amp=0.12, speed=8.0, position=0.42,
                name="Hand Oscillates", why="In front, a local scratch head oscillates 8-15 reversals/s: DESIGN INTENT."),
          click(5, 45),
          text(5, "LIBRARY != PERFORMANCE\n~20 s TRANSFER\nNO LOOSE SLEEVES", color=ORANGE, size=0.8,
               why="Two separations, both proposed."),
          wash(5, CYAN_DIM, opacity=0.06, kind="Vertical"),
          hatch(5, color=PAPER, opacity=0.05, rotation=0.0, amount=40, name="Static Lines",
                why="Paper collapses and static lines crackle: sleeves out of the cell."),
          scope(5, color=ORANGE, amplitude=0.06, speed=1.0, name="Loader Path",
                why="The loader's slow pick / flip / place path, 0.05 cycles per second.")]
    # 6 Circle Trap: four layouts A-D overhead, B brightens
    C += [ruling(6),
          disc(2, 6, color=ORANGE_DIM, rings=4, size=0.8, width=0.01, spacing=0.2, name="Ring Layout A",
               why="A: a compact ring of records around a central arm; clearance approaches the arm base."),
          rail(3, 6, color=ORANGE, amount=1, width=0.05, rotation=0.0, position=0.5, name="Rail Layout B",
               fft_=fft("Width", "low", 0.04, 0.09, 8.0, 400),
               why="B: the straight rack beside a 1-1.5 m rail, brightened, still dashed."),
          click(6, 45),
          text(6, "A RING - B RAIL (PROPOSED)\nC CAROUSEL - D CABINET\nREAR / MIDDLE / FRONT", color=ORANGE,
               size=0.8, why="Four candidates; A, C, D dim without being stamped impossible."),
          wash(6, CYAN_DIM, opacity=0.08, kind="Radial",
               why="The Glenton 150 footprint ghosts in beside it, cyan, for scale."),
          vruling(6),
          scope(6, color=ORANGE)]
    # 7 Millimetres: four callout cubes; comb slots; three-point caliper; spindle pilot
    C += [ruling(7, amount=40, width=0.004),
          rack(2, 7, color=ORANGE, amount=40, width=0.012, name="Comb Slots",
               why="Machined acetal comb slots with flared chamfers, one disc per slot: MECHANISM PREVIEW."),
          cups(3, 7, color=ORANGE, grid=3, size=0.14, speed=0.5, name="Edge Caliper",
               why="A three-point edge caliper; a suction cup spanning the centre hole leaks."),
          click(7, 45),
          text(7, "COMB SLOTS - VERIFIED GRIP\nSPINDLE GUIDE - LIFT /\nPOSITION / LOWER", color=ORANGE,
               size=0.8, why="Four callouts, all dashed, all previews."),
          lamp(7, color=PAPER_DIM, opacity=0.14, layer=6, name="Ring Light",
               why="The waiting disc under a ring light at the verification station."),
          vruling(7, amount=72, width=0.004),
          scope(7, color=ORANGE, amplitude=0.02, name="Vibration Trace",
                why="A vibration trace from the moving loader stays visible for testing.")]
    # 8 Swing-In Hand: pillar, coaxial head over the spindle; $247; 8 kHz ring
    C += [floor_iso(8, color=LACQ2),
          disc(2, 8, color=PAPER, rings=9, size=0.5, width=0.01, name="Deck A",
               why="Deck A in close isometric, the record seated."),
          dot(3, 8, color=ORANGE, scale=0.12, outline=0.12, name="Coaxial Head",
              fft_=fft("Scale", "low", 0.1, 0.2, 10.0, 300),
              why="The hollow elastomer-lined ring lowers onto the label, clear of the grooves: dashed."),
          click(8, 45),
          text(8, "S1 + D5312s + OA1 = $247\nTHREE COMPONENTS ONLY\n8 kHz INTERNAL CONTROL", color=CYAN,
               size=0.8, why="Checked arithmetic in cyan; mechanics, power and heat stay dashed."),
          wash(8, ORANGE_DIM, opacity=0.12, kind="Radial",
               why="Torque and temperature window, open, orange: no animation awards a pass."),
          hatch(8, color=PAPER, opacity=0.05, rotation=90.0, amount=30, name="Pillar",
                why="The pillar rising behind the deck."),
          scope(8, color=ORANGE, amplitude=0.12, waves=2, speed=6.0,
                why="Motor angle can follow its command while the pad slips over the vinyl.")]
    return {"name": "The Hand", "slug": "hand", "theme": "proposal",
            "world": ("The pressure is physical and the click runs at 45. One desk, one lamp, a hobby servo on "
                      "a fader; then the seven-inch beside the twelve-inch at the same scale, the platter "
                      "hatched heavy, I = 1/2 m r^2 in orange because it is a model. The proposed hand swings in "
                      "over Deck A and hovers. Nothing in this deck has been measured: almost every figure is "
                      "DASHED cue-orange, and the few cyan lines are a $247 subtotal and a builder's own words."),
            "palette": [{"role": "bed", "hex": "#17171c", "why": "Lacquer."},
                        {"role": "body", "hex": "#f2efe8", "why": "Paper-white for the discs and the requested trajectory."},
                        {"role": "figure", "hex": "#f2792b", "why": "Cue-orange: the hand, the head, the wall, the layouts. Proposed."},
                        {"role": "light", "hex": "#f2efe8", "why": "The click, now one tick every 1 1/3 s."},
                        {"role": "text", "hex": "#f2792b", "why": "Targets and models read orange; the few documented facts read cyan."},
                        {"role": "aura", "hex": "#f2792b", "why": "Heat, torque windows, simulated limits: orange radials."}],
            "columns": cols,
            "text_corpus": ["SCRATCHBOT 2015", "7-INCH OKAY - 12-INCH POOR", "I ~ 1/2 m r^2",
                            "13.2 x", "8-15 REVERSALS/s", "LIBRARY != PERFORMANCE",
                            "NO LOOSE SLEEVES", "B RAIL (PROPOSED)", "MECHANISM PREVIEW",
                            "$247 BASE COMPONENTS", "STROKE / GRIP / HEAT", "DESIGN INTENT"],
            "moments": [
                "Seven vs twelve: Scene Launch 3, then hold for two clicks with nothing lit; on the third click tap "
                "the row-3 FIGURE pad off so only the twelve-inch remains, and let the SCOPE show the slip.",
                "Inertia gap: Scene Launch 4 with Device knob 4 (FRACTURE) at a quarter and STUTTER lit so the ratio bars step like a "
                "chart recorder; push the row-2 BODY fader on the drop so the bars fill the frame.",
                "Swing-in: walk UP to column 8, hold the row-3 FIGURE pad (the coaxial head) and turn Device knob 5 "
                "(GLOW) up until the ring whites out over the label, then pull it back: no pass is awarded."],
            "clips": C}


# ================================================================ DECK 3
# THE CATALOG - scenes 14-17, back to 33 1/3: identity, permission, clock, interlocks
def deck3():
    C = []
    cols = ["What Record", "NFC Tier", "Camera Tier", "ArUco Tier",
            "Who May Touch", "Refused", "Three Layers", "Interlocks"]
    # 1 What Record: the middle verification zone, three tiers stacked like shelves
    C += [ruling(1, amount=3, width=0.02, color=ORANGE_DIM, opacity=0.6, name="Three Shelves",
                 why="Three tiers stack like shelves, all dashed orange."),
          disc(2, 1, color=PAPER, rings=8, size=0.45, width=0.01, name="COPY_PENDING",
               why="The main-story disc waiting at the verification station, marked COPY_PENDING."),
          dot(3, 1, color=ORANGE, scale=0.05, outline=0.14, name="Confidence Dot",
              fft_=fft("Scale", "mid", 0.04, 0.1, 9.0, 400),
              why="Candidate matches with confidence indicators."),
          click(1, 33),
          text(1, "TIER 1 NFC - TIER 2 CAMERA\nTIER 3 OPTIONAL ArUco\nVERIFIED COPY + SIDE", color=ORANGE,
               size=0.8, why="The three tiers, sequential, then together."),
          lamp(1, color=PAPER_DIM, opacity=0.14, layer=6, name="Ring Light"),
          vruling(1),
          scope(1, color=ORANGE, amplitude=0.03, name="Recognition")]
    # 2 NFC Tier: a hand taps a jacket, the expected slot lights
    C += [ruling(2),
          rack(2, 2, color=ORANGE_DIM, amount=20, width=0.03, name="Slot Dividers",
               why="NFC tags on sleeves and slot dividers; the expected slot lights."),
          disc(3, 2, color=CYAN, rings=3, size=0.2, width=0.02, spacing=0.3, name="Tag Field",
               fft_=fft("Size", "mid", 0.15, 0.4, 9.0, 300),
               why="The near-field as three cyan rings that swell when the jacket is tapped."),
          click(2, 33),
          text(2, "TIER 1 - NFC\nEXPECTED SLOT\nNOT PROOF OF THE DISC", color=ORANGE, size=0.8,
               why="A tag identifies the expected item or location, not the physical disc."),
          wash(2, CYAN_DIM, opacity=0.06, kind="Radial"),
          vruling(2),
          scope(2, color=ORANGE, amplitude=0.02)]
    # 3 Camera Tier: polarised lighting, both labels imaged before every load
    C += [ruling(3, amount=24, width=0.006),
          disc(2, 3, color=PAPER, rings=4, size=0.42, width=0.02, spacing=0.25, name="Label Under Lamp",
               why="Both labels imaged under controlled, polarised lighting."),
          rail(3, 3, color=CYAN, amount=16, width=0.01, rotation=0.0, name="Scan Lines",
               fft_=fft("Fuzzyness", "high", 0.0, 0.3, 8.0, 250),
               why="OCR scan lines over the label; an ambiguous reading goes to inspection."),
          lamp(3, color=CYAN_DIM, opacity=0.3, name="Polarised Light"),
          text(3, "TIER 2 - CAMERA\nBOTH LABELS BEFORE LOAD\nAMBIGUOUS -> INSPECTION", color=ORANGE, size=0.8),
          blank(6, 3, "The lamp is the only light."),
          vruling(3, amount=64, width=0.004),
          scope(3, color=CYAN, amplitude=0.03, name="Image Features")]
    # 4 ArUco Tier: the marker square, black and white cells
    C += [black(4, why="Black: the marker fills the frame."),
          marker(2, 4, nx=6, ny=6, name="ArUco 6x6", effects=[xform(scale=42)],
                 why="An optional ArUco marker on an approved Side A label, kept outside the grooves."),
          disc(3, 4, color=CYAN, rings=1, size=0.46, width=0.015, name="Marker Frame",
               fft_=fft("Size", "low", 0.44, 0.5, 8.0, 400),
               why="The marker's quiet-zone border."),
          click(4, 33),
          text(4, "MARKER ID -> LOCAL LOOKUP\n-> COPY_1 - SIDE A", color=CYAN, size=0.9,
               align="Center", valign="Bottom", x=0, y=460,
               why="A dictionary ID resolved by local lookup; the marker holds no permission."),
          blank(6, 4, "No wash over a marker: contrast is the point."),
          blank(7, 4, "No grid behind the marker."),
          scope(4, color=CYAN, amplitude=0.02)]
    # 5 Who May Touch: the switch grid becomes a permission table, lock badges
    C += [ruling(5, amount=9, width=0.01, color=PAPER_DIM, opacity=0.6, name="Table Rows",
                 why="The permission table: one row per physical copy."),
          marker(2, 5, nx=12, ny=7, c1=LACQ, c2=LACQ2, name="Switch Grid", opacity=1.0,
                 why="The marker's cells become a grid of switches."),
          geo(3, 5, shape="Square", c1=ORANGE, c2=CYAN, lines=9, name="Lock Badges",
              why="PLAY_ONLY, SCRATCH_APPROVED, ARCHIVAL_LOCKED badges."),
          click(5, 33),
          text(5, "PLAY_ONLY\nSCRATCH_APPROVED\nARCHIVAL_LOCKED", color=ORANGE, size=1.0,
               why="Three protection levels per copy."),
          wash(5, ORANGE_DIM, opacity=0.06, kind="Vertical"),
          vruling(5, amount=12, width=0.01, color=PAPER_DIM, opacity=0.5, name="Table Columns"),
          scope(5, color=ORANGE, amplitude=0.02)]
    # 6 Refused: the AI assistant's perform_routine hits the wall; stamp REFUSED
    C += [ruling(6),
          disc(2, 6, color=PAPER, rings=8, size=0.45, width=0.01, name="COPY_1 PLAY_ONLY",
               why="COPY_1 seated for ordinary playback beneath the raised scratch head."),
          dot(3, 6, color=ORANGE, scale=0.1, outline=0.1, name="Hand Stays Up",
              effects=[xform(y=260)], fft_={},
              why="The scratch arm stays retracted. It does not react to the music; the rule holds."),
          click(6, 33),
          stamp(6, "REFUSED AT THE\nCONTROLLER", color=PAPER, size=2.0,
                why="Paper-white stamp, held for one full click. Caller role from trusted session, never from prompt text."),
          wash(6, ORANGE, opacity=0.12, kind="Horizontal", name="Policy Wall",
               why="The wall at the local operation controller."),
          vruling(6),
          scope(6, color=PAPER, amplitude=0.0, name="Flat Line",
                why="Requested motion is flat: nothing moves.")]
    # 7 Three Layers One Clock: cross-section beneath the floor; laptop / Pi / Teensy
    C += [ruling(7, amount=3, width=0.03, color=CYAN_DIM, opacity=0.7, name="Three Layers",
                 why="Cross-section beneath the floor: AI host, Pi 5 supervision, Teensy execution."),
          rail(2, 7, color=CYAN, amount=8, width=0.01, rotation=90.0, name="Tool Names",
               fft_=fft("Fuzzyness", "high", 0.0, 0.3, 8.0, 250),
               why="find_record, load_record, cue_record, play_record, crossfade, perform_routine, return_record, get_status."),
          swing(3, 7, color=ORANGE, waves=8, amp=0.08, speed=10.0, name="1 kHz Trajectory",
                why="1,000 trajectory updates per second; each S1 closes its own 8 kHz loop."),
          click(7, 33),
          text(7, "REQUEST / SUPERVISE / EXECUTE\nTEENSY 1 kHz - S1 8 kHz\nHOST-DISCONNECT TEST", color=CYAN,
               size=0.8, why="Published hardware specs cyan; the architecture stays dashed."),
          wash(7, ORANGE_DIM, opacity=0.06, kind="Radial",
               why="A ghost of Scratchbot's overheated laptop flickers above."),
          vruling(7, amount=48, width=0.006),
          scope(7, color=CYAN, amplitude=0.05, waves=3, speed=8.0, name="Timestamped Queue")]
    # 8 Interlocks: mushroom stop, light curtain, exclusion cylinders over each deck
    C += [ruling(8),
          disc(2, 8, color=ORANGE, rings=3, size=0.5, width=0.03, spacing=0.3, name="Exclusion Zone",
               fft_=fft("Size", "low", 0.46, 0.6, 9.0, 500),
               why="A cylindrical exclusion volume glows over each deck."),
          dot(3, 8, color=PAPER, scale=0.14, outline=0.0, name="Mushroom Stop",
              fft_={},
              why="A paper-white mushroom button rises out of the floor. It is pressed."),
          click(8, 33),
          text(8, "TORQUE OFF != INSTANT STOP\nTONEARM HOME - HEAD RETRACTED\nPLATTER STOPPED", color=ORANGE,
               size=0.8, why="Three independently confirmed lamps before the loader moves."),
          wash(8, CYAN_DIM, opacity=0.1, kind="Vertical", name="Light Curtain",
               why="A light curtain standing far enough from the hazard for the measured stopping time."),
          vruling(8),
          scope(8, color=ORANGE, amplitude=0.08, speed=1.0, name="Deceleration",
                why="Controlled deceleration, then torque removal; the brake holds the disc.")]
    return {"name": "The Catalog", "slug": "catalog", "theme": "policy",
            "world": ("The middle zone, where a record waits under a ring light to be told what it is. "
                      "Tags, cameras, an optional black-and-white marker; then the marker's cells become a "
                      "grid of switches and the switches become a permission table. An AI assistant asks to "
                      "scratch a play-only copy and the local controller refuses: a paper-white stamp held for "
                      "one full click while the hand stays up. Beneath the floor, three layers and one clock; "
                      "at the front, a mushroom stop. The click is back at 33 1/3."),
            "palette": [{"role": "bed", "hex": "#17171c", "why": "Lacquer."},
                        {"role": "body", "hex": "#f2efe8", "why": "The disc, the marker's white cells, the stamp."},
                        {"role": "figure", "hex": "#f2792b", "why": "Every tier and lock is a proposed enforcement design: orange."},
                        {"role": "light", "hex": "#f2efe8", "why": "The click; a polarised cyan lamp for the camera tier."},
                        {"role": "text", "hex": "#f2792b", "why": "Policy is proposed; published hardware specs are cyan."},
                        {"role": "aura", "hex": "#3cc6d0", "why": "Cyan for the near-field and the light curtain."}],
            "columns": cols,
            "text_corpus": ["WHAT IS THIS RECORD", "COPY_PENDING", "TIER 1 NFC", "TIER 2 CAMERA",
                            "TIER 3 ArUco", "COPY_1 - SIDE A", "PLAY_ONLY", "SCRATCH_APPROVED",
                            "ARCHIVAL_LOCKED", "REFUSED AT THE CONTROLLER",
                            "IDENTIFICATION != AUTHORIZATION", "RECOVERY_AUDIT"],
            "moments": [
                "Refused: Scene Launch 5 then walk UP to Refused on a downbeat; tap the row-5 TEXT pad so the stamp "
                "retypes, hold it for one full click with nothing else lit, and only then press the row-3 FIGURE "
                "pad on the next scene so the hand lowers onto COPY_2 instead.",
                "ArUco: Scene Launch 4 with Device knob 3 (SPACE) at a third and MIRROR QUAD lit so the marker tiles into a grid; "
                "tap NEGATIVE on the one of each bar so the cells invert with the click.",
                "Interlocks: column 8, hold the row-2 BODY pad and turn Device knob 8 (VOID) up so the "
                "exclusion rings close around the mushroom stop; on the drop tap RECORD for one bar of blackout."],
            "clips": C}


# ================================================================ DECK 4
# THE LEDGER - scenes 18-21: ladder, ledger, gates, coda
def deck4():
    C = []
    cols = ["The Ladder", "The Ledger", "Gate 1A", "Gate 1B",
            "Stage Two", "Stage Three", "Coda", "End Card"]
    # 1 The Ladder: six rungs, cyan plate left, orange plate right
    C += [ruling(1, amount=6, width=0.03, color=PAPER_DIM, opacity=0.7, name="Six Rungs",
                 why="A vertical ladder of six rungs."),
          rail(2, 1, color=CYAN, amount=1, width=0.4, rotation=90.0, position=0.3, name="Precedent Plates",
               why="Solid cyan plates on the left: documented precedents."),
          rail(3, 1, color=ORANGE, amount=1, width=0.4, rotation=90.0, position=0.7, name="Target Plates",
               fft_=fft("Width", "low", 0.36, 0.46, 8.0, 400),
               why="Dashed orange plates on the right: GUSTO's integration targets, no completed-stage stamp."),
          click(1, 33),
          text(1, "1 PLAYBACK - 2 BEATMATCH\n3 BABY SCRATCH - 4 CHIRP\n5 FLARE / ORBIT - 6 JUGGLE", color=PAPER,
               size=0.8, why="The six rungs, revealed one at a time."),
          blank(6, 1, "The ladder ranks integration stages; no wash, no claim."),
          vruling(1, amount=2, width=0.02, color=PAPER_DIM, opacity=0.6, name="Rails"),
          scope(1, color=ORANGE, amplitude=0.03)]
    # 2 The Ledger: three columns topped by three booths at different scales
    C += [ruling(2, amount=12, width=0.006),
          rail(2, 2, color=PAPER_DIM, amount=3, width=0.02, rotation=90.0, name="Three Columns",
               why="Proof of concept, home prototype, exhibition."),
          rail(3, 2, color=ORANGE, amount=3, width=0.08, rotation=90.0, position=0.55, name="Totals",
               fft_=fft("Width", "low", 0.06, 0.2, 9.0, 450),
               why="~$3,373 - ~$15,178 - ~$39,777: inherited planning estimates, dashed."),
          click(2, 33),
          text(2, "~$3.4K - 180-260 H\n~$15.2K - 500-750 H\n~$39.8K - 1,200-1,800 H", color=ORANGE,
               size=0.8, why="Totals and hours; not verified build quotes."),
          wash(2, CYAN_DIM, opacity=0.06, kind="Vertical",
               why="A ghost Glenton tag, ~EUR 100,000, not a like-for-like quote."),
          vruling(2, amount=6, width=0.01, color=PAPER_DIM, opacity=0.5, name="Ledger Lines"),
          scope(2, color=ORANGE, amplitude=0.02)]
    # 3 Gate 1A: handling bench; counter 50 cycles / 0 drops / NOT RUN
    C += [floor_iso(3, color=LACQ2, height=3.0),
          rail(2, 3, color=ORANGE, amount=1, width=0.03, position=0.5, name="Linear Actuator",
               why="A linear actuator, candidate edge grip, and a thrift-store turntable."),
          disc(3, 3, color=PAPER, rings=7, size=0.36, width=0.01, name="Thrift Turntable",
               effects=[xform(x=380, y=-60, scale=90)],
               why="The clearance-checked loading guide over a cheap deck."),
          click(3, 33),
          text(3, "STAGE 1A - HANDLING\nTARGET: 50 CYCLES - 0 DROPS\nRESULT: NOT RUN", color=ORANGE,
               size=0.8, why="Counters at their unstarted states; result fields unfilled."),
          lamp(3, color=PAPER_DIM, opacity=0.16, layer=6, name="Bench Lamp"),
          hatch(3, color=PAPER, opacity=0.05, rotation=0.0, amount=30),
          scope(3, color=ORANGE, amplitude=0.04, speed=1.0, name="Pick Flip Return")]
    # 4 Gate 1B: performance bench; 15:00 required / 00:00 elapsed
    C += [floor_iso(4, color=LACQ2, height=3.0),
          disc(2, 4, color=PAPER, rings=10, size=0.55, width=0.012, name="Direct Drive Deck",
               why="A direct-drive deck, scratch cartridge, used contactless-fader mixer."),
          dot(3, 4, color=ORANGE, scale=0.11, outline=0.12, name="Candidate Drive",
              fft_=fft("Scale", "low", 0.1, 0.18, 10.0, 300),
              why="The candidate brushless drive and Teensy over the label."),
          click(4, 33),
          text(4, "STAGE 1B - PERFORMANCE\nREQUIRED 15:00 - ELAPSED 00:00\nTARGET: 0 SKIPS - NOT RUN", color=ORANGE,
               size=0.8, why="The first gate's timer, unstarted."),
          wash(4, ORANGE_DIM, opacity=0.1, kind="Radial", name="Temperature Window"),
          hatch(4, color=PAPER, opacity=0.06, rotation=45.0, amount=50),
          scope(4, color=ORANGE, amplitude=0.1, waves=2, speed=6.0, name="Record vs Motor",
                why="BEAT ERROR - RECORD VS MOTOR ANGLE - CURRENT / TEMPERATURE.")]
    # 5 Stage Two: one autonomous deck; misfiled disc; forbidden scratch; host disconnect
    C += [ruling(5),
          disc(2, 5, color=PAPER, rings=8, size=0.45, width=0.01, name="One Deck",
               why="One autonomous deck."),
          marker(3, 5, nx=6, ny=6, c1=LACQ, c2=ORANGE, name="Misfiled Disc", effects=[xform(x=-520, y=200, scale=18)],
                 why="A deliberately misfiled disc the deck must detect: SLOT_INVENTORY_MISMATCH."),
          click(5, 33),
          text(5, "STAGE 2 - SINGLE-DECK AUTONOMY\nDETECT MISFILE - REFUSE\nSURVIVE HOST DISCONNECT", color=ORANGE,
               size=0.8, why="Proposed tests; later integration, separately costed."),
          wash(5, ORANGE_DIM, opacity=0.06, kind="Horizontal"),
          vruling(5),
          scope(5, color=ORANGE, amplitude=0.04, name="Local Timing Plan",
                why="The queued routine continues only if the design passes.")]
    # 6 Stage Three: two decks, fifty records, a sixty-minute set
    C += [ruling(6),
          disc(2, 6, color=PAPER, rings=8, size=0.4, width=0.01, name="Deck A",
               effects=[xform(x=-400)], why="Two decks, left."),
          disc(3, 6, color=PAPER, rings=8, size=0.4, width=0.01, name="Deck B",
               effects=[xform(x=400)], fft_=fft("Line Width", "mid", 0.01, 0.03, 9.0, 400),
               why="Two decks, right: measured tempo / phase error between them."),
          click(6, 33),
          text(6, "STAGE 3 - TWO-DECK SET\n50 RECORDS - 60 MINUTES\nCONTINUE / REDESIGN / STOP", color=ORANGE,
               size=0.8, why="Each gate has three exits."),
          wash(6, CYAN_DIM, opacity=0.05, kind="Vertical"),
          rack(7, 6, color=PAPER_DIM, amount=50, width=0.01, name="Fifty Records", opacity=0.35,
               why="Fifty records in the rack behind the decks."),
          scope(6, color=ORANGE, amplitude=0.05, waves=2, name="Phase Error")]
    # 7 Coda: the Scene 01 composition returns; the hand lowers; freeze before contact
    C += [black(7, why="Lacquer black; the full booth stands in faint dashed outline, unlit."),
          disc(2, 7, rings=10, size=0.6, why="The same disc, same scale, same camera as the cold open."),
          dot(3, 7, color=ORANGE, scale=0.07, outline=0.08, effects=[xform(y=60)],
              fft_=fft("Scale", "low", 0.07, 0.09, 6.0, 500), name="Hand Lowers",
              why="The hand lowers toward the label; freeze one frame before contact."),
          click(7, 33),
          text(7, "NEXT ACTION: STAGE 1B\n12-INCH SCRATCH + CUT BENCH\n~$1,616 - UNDER 4 WEEKS", color=ORANGE,
               size=0.8, why="A static planning estimate; the timer unstarted; the result blank."),
          wash(7, ORANGE_DIM, opacity=0.05, kind="Radial", name="Faint Booth"),
          blank(7, 7, "No grid: the booth is unlit."),
          scope(7, color=PAPER, amplitude=0.0, name="Result Blank",
                why="Actual measurement fields stay blank.")]
    # 8 End Card: black; citations scroll in cyan monospace; click stops
    C += [black(8, why="Black. The needle lifts and the click stops."),
          blank(2, 8, "Nothing but the sources."),
          blank(3, 8, "Nothing but the sources."),
          blank(4, 8, "No click: the end card plays in silence."),
          text(8, "SOURCES\nGLENTON JKB - SOUND LEISURE\nIVAN BUILDS - robotlab\nDJ TECHTOOLS - MIT MEDIA LAB\nODRIVE - TECHNICS - RANE",
               color=CYAN, size=0.7, align="Center", valign="Center", x=0, y=0, animated=True, delay=40,
               name="Sources", why="The citation list in stylus-cyan monospace."),
          blank(6, 8, "Silence."),
          blank(7, 8, "Silence."),
          scope(8, color=CYAN, amplitude=0.0, name="Needle Lifted")]
    return {"name": "The Ledger", "slug": "ledger", "theme": "estimate",
            "world": ("What GUSTO must earn, in the order it must spend. A six-rung ladder with precedents on "
                      "the cyan left and targets on the orange right; a ledger with three booths at three "
                      "scales; a road of gates whose counters all read NOT RUN. Then the cold open comes "
                      "back exactly, disc and hand and camera, and the viewer sees what was missing: the "
                      "test. The hand lowers, freezes one frame before contact, the needle lifts, and the "
                      "sources scroll in silence."),
            "palette": [{"role": "bed", "hex": "#17171c", "why": "Lacquer."},
                        {"role": "body", "hex": "#f2efe8", "why": "Ladder, ledger lines, the returning disc."},
                        {"role": "figure", "hex": "#f2792b", "why": "Every total, target and timer is dashed orange."},
                        {"role": "light", "hex": "#f2efe8", "why": "The click, until the needle lifts."},
                        {"role": "text", "hex": "#f2792b", "why": "Estimates orange; the end card's sources cyan."},
                        {"role": "aura", "hex": "#3cc6d0", "why": "Only the ghost Glenton tag and the rack glow cyan."}],
            "columns": cols,
            "text_corpus": ["1 PLAYBACK", "2 BEATMATCH", "3 BABY SCRATCH", "6 JUGGLE",
                            "~$3,373", "~$15,178", "~$39,777", "RESULT: NOT RUN",
                            "15:00 REQUIRED - 00:00 ELAPSED", "CONTINUE / REDESIGN / STOP",
                            "~$1,616 - UNDER 4 WEEKS", "THE HAND STILL NEEDS A TEST"],
            "moments": [
                "Gates: walk UP from Gate 1A through Stage Three one column per phrase, tapping the row-5 TEXT "
                "pad on each downbeat so the counters retype at NOT RUN; never let a bank knob pass a third.",
                "Coda: Scene Launch 7 with every effect off, crossfader hard right, SCOPE fader at zero; "
                "hold the row-3 FIGURE pad as the hand lowers and release it one click before the drop.",
                "End card: walk UP to column 8 on the last beat, pull faders 1-4 to zero, and let the sources "
                "type out over silence; RECORD for blackout when the room is done."],
            "clips": C}


# ================================================================ DECK 5
# SL-1210MKX - the wildcard: the Technics manual's schematics as a deck of their own
def deck5():
    C = []
    cols = ["33 1/3", "DIP Switches", "Pitch Fader", "S-Tonearm",
            "Slipmat", "45", "Reverse", "Lock Groove"]
    # 1 33 1/3: the platter from above, 1.8 s per rev
    C += [ruling(1),
          disc(2, 1, color=PAPER, rings=14, size=0.7, width=0.01, spacing=0.1, name="Platter 33",
               why="The 332 mm platter from above, a uniform-disc model, turning at 33 1/3."),
          groove(3, 1, color=CYAN, speed=0.18, name="Groove 33",
                 why="The groove spiral at 33 1/3, documented: cyan."),
          click(1, 33),
          text(1, "SL-1210MKX\n33 1/3 RPM - 1.8 s / REV\n0.7 s START - 11.9 kg", color=CYAN, size=0.8,
               font=MONO2, why="MKX launch specs (ADE 2026): 0.7 s to speed, 11.9 kg with the cast balance weight."),
          wash(1, CYAN_DIM, opacity=0.06, kind="Radial"),
          vruling(1),
          scope(1, color=CYAN, amplitude=0.03, speed=1.0, name="Platter Speed")]
    # 2 DIP Switches: the under-platter 8-pin matrix SW1-SW8 (MK7 platform)
    C += [black(2, why="Black lacquer under the platter."),
          disc(2, 2, color=PAPER_DIM, rings=4, size=0.82, width=0.02, spacing=0.14, name="Platter Underside",
               why="The aluminium die-cast platter lifted away, seen from below."),
          marker(3, 2, nx=8, ny=1, c1=LACQ2, c2=CYAN, name="SW1-SW8", opacity=0.9,
                 effects=[xform(y=-120, scale=40)],
                 why="The eight DIP switches as an 8x1 row: LED, reserved, REV, 78, TQ1/TQ2, BK1/BK2."),
          click(2, 33, color=CYAN, opacity=0.2, name="Switch Tick"),
          text(2, "DIP SW1 LED - SW3 REV - SW4 78\nSW5-6 TORQUE - SW7-8 BRAKE\nMK7 PLATFORM", color=CYAN,
               size=0.8, font=MONO2, why="Under-platter matrix from the MK7 operating instructions, shared by the MKX."),
          blank(6, 2, "Only the switches."),
          blank(7, 2, "Only the switches."),
          scope(2, color=CYAN, amplitude=0.02, name="Torque Ramp")]
    # 3 Pitch Fader: +-8 / +-16 %, the fader travel as a vertical rail
    C += [ruling(3),
          rail(2, 3, color=PAPER, amount=1, width=0.02, rotation=90.0, position=0.78, name="Pitch Slot",
               why="The pitch fader's slot, right of the platter."),
          dot(3, 3, color=CYAN, scale=0.05, outline=0.06, name="Fader Knob",
              effects=[xform(x=540, y=0)], fft_=fft("Scale", "mid", 0.05, 0.08, 8.0, 400),
              why="The fader knob at centre detent: 0 %."),
          click(3, 33),
          text(3, "PITCH +-4 / 8 / 16 / 50 %\n+-4 %: 2x FINER PER MM\nDIGITAL SLIDER - NO TRACK", color=CYAN,
               size=0.8, font=MONO2, why="The MKX's new +-4 % fine and +-50 % wide ranges; the tempo half of beatmatching."),
          wash(3, CYAN_DIM, opacity=0.05, kind="Horizontal"),
          vruling(3),
          scope(3, color=CYAN, amplitude=0.04, name="Speed Reference")]
    # 4 Cue Lever: lift, position, withdraw the fork, lower
    C += [ruling(4),
          disc(2, 4, color=PAPER, rings=10, size=0.55, width=0.01, name="Record Seated",
               effects=[xform(x=-200)], why="The record seated, left; the tonearm reaches from the right."),
          rail(3, 4, color=CYAN, amount=1, width=0.015, rotation=22.0, position=0.5, name="S-Tonearm",
               fft_=fft("Width", "low", 0.012, 0.03, 8.0, 400),
               why="The polished silver S-tonearm, 22 degree offset, floating free during play."),
          lamp(4, color=PAPER_DIM, opacity=0.14, name="Stylus Light"),
          text(4, "S-TONEARM 230 mm - 22 DEG\nOVERHANG 15 mm\nLIFT - POSITION - LOWER", color=CYAN, size=0.8,
               font=MONO2, why="Tonearm geometry from the MK7-platform service manual; cueing order from the script."),
          blank(6, 4, "No wash: a gap stays visible between stylus and record."),
          vruling(4),
          scope(4, color=CYAN, amplitude=0.02, name="Cue Lever")]
    # 5 Slipmat: the record reverses above the forward-turning platter
    C += [ruling(5),
          disc(2, 5, color=PAPER_DIM, rings=14, size=0.7, width=0.01, spacing=0.1, name="Platter Forward",
               why="The platter keeps turning forward."),
          groove(3, 5, color=ORANGE, speed=0.6, direction="Anti-clockwise", name="Record Reverses",
                 why="The record alone reverses above the slipmat: the scratch, dashed orange because it is GUSTO's job."),
          click(5, 45),
          text(5, "SLIPMAT: RECORD OVER\nFORWARD PLATTER\nGRIP > REQUIRED TORQUE", color=ORANGE, size=0.8,
               font=MONO2, why="Extra grip pressure also increases slipmat drag."),
          wash(5, ORANGE_DIM, opacity=0.08, kind="Radial"),
          hatch(5, color=PAPER, opacity=0.08, rotation=45.0, amount=60, name="Felt"),
          scope(5, color=ORANGE, amplitude=0.12, waves=3, speed=7.0, name="Reversals")]
    # 6 45: the click shifts; everything 1.35x faster
    C += [ruling(6),
          disc(2, 6, color=PAPER, rings=14, size=0.7, width=0.01, spacing=0.1, name="Platter 45",
               fft_=fft("Line Width", "low", 0.01, 0.03, 10.0, 300),
               why="The same platter at 45: 1 1/3 s per revolution."),
          groove(3, 6, color=CYAN, speed=0.25, name="Groove 45"),
          click(6, 45),
          text(6, "45 RPM - 1.33 s / REV\n78 RPM VIA DIP SW4", color=CYAN, size=1.0, font=MONO2),
          wash(6, CYAN_DIM, opacity=0.06, kind="Radial"),
          vruling(6),
          scope(6, color=CYAN, amplitude=0.04, speed=1.4, name="Platter Speed 45")]
    # 7 Reverse: reverse playback per the manual; the spiral unwinds
    C += [ruling(7),
          disc(2, 7, color=PAPER, rings=14, size=0.7, width=0.01, spacing=0.1, name="Platter Reverse"),
          groove(3, 7, color=CYAN, speed=0.18, direction="Anti-clockwise", name="Groove Unwinds",
                 why="Reverse playback is a documented deck function: cyan, anti-clockwise."),
          click(7, 33),
          text(7, "REVERSE PLAYBACK\nDIP SW3 - CORELESS\nDIRECT DRIVE", color=CYAN, size=0.8,
               font=MONO2),
          wash(7, CYAN_DIM, opacity=0.05, kind="Horizontal"),
          vruling(7),
          scope(7, color=CYAN, amplitude=0.04, speed=1.0, name="Reverse")]
    # 8 Lock Groove: the run-out; the click motif; the needle lifts
    C += [black(8, why="Black: one spiral and one click."),
          groove(2, 8, color=PAPER, speed=0.18, zoom=1.6, name="Run-Out Groove",
                 why="The locked run-out groove, one blemish per revolution."),
          dot(3, 8, color=PAPER, scale=0.02, outline=0.0, name="The Blemish",
              effects=[xform(x=300, y=0)], fft_=fft("Scale", "high", 0.02, 0.05, 9.0, 150),
              why="The single blemish the needle passes once per revolution."),
          click(8, 33),
          text(8, "ONE TICK EVERY 1.8 s\nNEVER MELODIC - NEVER DOUBLED\nNO REVERB - NO SWING", color=PAPER,
               size=0.8, font=MONO2, why="The audio system's rules for the click."),
          blank(6, 8, "Nothing but the groove."),
          blank(7, 8, "Nothing but the groove."),
          scope(8, color=PAPER, amplitude=0.02, waves=1, name="Stylus")]
    return {"name": "SL-1210MKX", "slug": "sl1210", "theme": "wildcard",
            "world": ("The Technics SL-1210MKX (ADE, October 2026) drawn as schematics: the die-cast platter "
                      "from above, the under-platter DIP switches, the new +-4 / +-50 % pitch slot, the "
                      "silver S-tonearm at 22 degrees, the slipmat letting the record reverse above a forward "
                      "platter. Internals not yet published for the MKX are labelled MK7 PLATFORM. Everything the manual documents is cyan; the one orange column is the "
                      "scratch, because that is the job GUSTO has not yet earned. It ends in the run-out "
                      "groove with the blemish the whole film's click was built from."),
            "palette": [{"role": "bed", "hex": "#17171c", "why": "Lacquer."},
                        {"role": "body", "hex": "#f2efe8", "why": "The platter and the strobe rows, paper-white."},
                        {"role": "figure", "hex": "#3cc6d0", "why": "Cyan: groove, tonearm, pitch knob, documented deck functions."},
                        {"role": "light", "hex": "#3cc6d0", "why": "The strobe lamp is the deck's one cyan light."},
                        {"role": "text", "hex": "#3cc6d0", "why": "Operating-instruction captions in Consolas."},
                        {"role": "aura", "hex": "#f2792b", "why": "Orange exists only in the Slipmat column."}],
            "columns": cols,
            "text_corpus": ["SL-1210MKX", "33 1/3 RPM - 1.8 s / REV", "45 RPM - 1.33 s / REV",
                            "DIP SW1-SW8", "PITCH +-4 / +-50 %", "LIFT - POSITION - LOWER",
                            "SLIPMAT", "REVERSE PLAYBACK", "11.9 kg - 0.7 s START", "LOCKED GROOVE",
                            "ONE TICK EVERY 1.8 s", "NEVER MELODIC"],
            "moments": [
                "33 to 45: Scene Launch 1, then fire Scene Launch 6 on a downbeat with Track knob 8 (TIME) "
                "pushed from centre to three-quarters so every generator speeds up with the click.",
                "Slipmat: column 5, hold the row-3 FIGURE pad and push Device knob 3 (SPACE) with TUNNEL lit so the "
                "reversing orange groove pulls the platter inward; release on the breakdown.",
                "Lock groove: walk UP to column 8, pull every fader but 2, 3 and 4, and let the blemish tick "
                "on the highs until the room is quiet; then STOP ALL CLIPS as the needle lifts."],
            "clips": C}


# The kinetic pass (2026-10-23): the shared pass in resolume_build/kinetic_pass.py gives the room a
# moving texture on its own clock, unfreezes generators, lets the lows punch a little and keeps
# captions still. KINETIC = False rebuilds the still version.
KINETIC = True
STILL_COLUMNS = set()                 # (deck from 0, column from 1) held still on purpose
KINETIC_NOTE = (" Since the kinetic pass the room never stops: a texture on its own clock sits under every "
                "deck, the lows push the figures a little, the highs shiver the scope, and the captions stay put.")


def main():
    decks = [deck1(), deck2(), deck3(), deck4(), deck5()]
    extra = {}
    if KINETIC:
        import sys
        sys.path.insert(0, os.path.join(HERE, "..", ".."))
        from resolume_build import kinetic_pass as KP
        fired = []
        KP.pass_decks(decks, KP.default_motion(PAPER), fired.append, still=STILL_COLUMNS)
        extra = KP.BIBLE_EXTRA
        print("kinetic clamps fired: %d" % len(fired))
        for line in fired[:12]:
            print("  " + line)
    bible = {
        "pack_name": "The Library And The Hand",
        "comp_name": "The Library And The Hand - GUSTO",
        "tagline": "The library has precedents. The hand still needs a test.",
        "decks": [{k: v for k, v in d.items() if k != "clips"} for d in decks],
        "effect_wishlist": [
            {"effect": "Trails", "role": "Bank A persistence: the held disc's afterimage, the loader path, the hand lowering frame by frame."},
            {"effect": "Bloom", "role": "Bank A glow for the strobe lamp, the ring light and the white-out over the label; kept under a third."},
            {"effect": "Vignette", "role": "Bank A, the work lamp's throw and the exclusion zone closing."},
            {"effect": "CRT", "role": "Bank C period: the plinths and the cross-section read as a console."},
            {"effect": "Stop Motion", "role": "Bank C: the chart-recorder step for ratio bars and counters."},
            {"effect": "Mirror Quad", "role": "Bank D: the ArUco marker tiles into the switch grid."},
            {"effect": "Tunnel", "role": "Bank B: the reversing groove pulls the platter inward in Slipmat."},
            {"effect": "Invert RGB", "role": "Bank A: the marker's cells invert with the click."},
            {"effect": "Edge Detection", "role": "Bank D: any fill becomes wireframe again; the pack's safety net against solid shapes."}],
        "fft_philosophy": (
            "The film has one sound, a stylus click once per revolution, so the composition's reactivity is "
            "built to read as rotation and never as a light show. Sub and low (kick) drive only width and "
            "size: the disc's line width, the ratio bars, the exclusion rings, the hand's scale, on a 300-500 "
            "ms release, so a kick is a push on the record. Mids drive the SCOPE 1:1 as ACTUAL RECORD ANGLE, "
            "the one honest readout, and breathe the hall's frequency and the confidence dot. Highs touch "
            "only ruling fuzz and hatching: hi-hats become jitter on clock ticks and scan lines. Nothing "
            "about colour ever reacts: cyan means documented and orange means proposed, and the music does "
            "not get to change what is true. Text never moves. The click itself is a Stroboscope held on "
            "the LIGHT layer at 33 1/3 or 45; it is a motif, not the beat."),
        "wildcard_rationale": (
            "Four decks walk the script: the plinths that already exist, the hand that is only proposed, "
            "the catalog that decides who may touch which copy, and the ledger of what it would cost to "
            "find out. The fifth deck is the Technics SL-1210MKX manual drawn as schematics, because every "
            "number in the film - 1.8 seconds per revolution, 1.8 kg, 332 mm, lift-position-lower - comes "
            "from that deck, and because the click the whole film rides is a locked groove on it.")}
    bible.update(extra)
    if KINETIC:
        bible["fft_philosophy"] += KINETIC_NOTE
    with open(os.path.join(HERE, "bible.json"), "w", encoding="utf-8") as f:
        json.dump(bible, f, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "decks.json"), "w", encoding="utf-8") as f:
        json.dump({"decks": [{"deck": d["name"], "clips": d["clips"]} for d in decks]},
                  f, indent=1, ensure_ascii=False)
    n = sum(len(d["clips"]) for d in decks)
    print("bible: 5 decks; clips:", n)
    for d in decks:
        cells = {(c["layer"], c["column"]) for c in d["clips"]}
        missing = [(l, c) for l in range(1, 9) for c in range(1, 9) if (l, c) not in cells]
        if missing or len(d["clips"]) != 64:
            print("  %s: %d clips, missing %s" % (d["name"], len(d["clips"]), missing))


if __name__ == "__main__":
    main()
