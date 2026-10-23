#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py - STUDIO ONE, a stock-only Avenue 7.28.1 instrument for the 1938
Mercury War of the Worlds broadcast, from two of the performer's docs:
"The Architecture of an Illusion" (CBS Studio One, 485 Madison Avenue,
reconstructed) and the r04 "Studio Takeover Brief" (the visitors, the red
pencil, the disc that survives).

Rules carried from the brief, enforced here:
  * silver-gelatin palette - charcoal, ivory, warm grey, one lamp amber;
  * RED APPEARS ONLY ON RED-PENCIL MARKS (deck 3, a handful of clips);
  * the studio clock shows real time, 8:00-9:00 pm, never the play's times;
  * the optical soundtrack strip (SCOPE, vertical, left edge) appears only
    inside accounts the soundtrack is giving - decks 2 and 4;
  * the visitors never speak: their clips carry no text.

The clip helpers are the Library And The Hand's; every colour is passed.

    python packs/studio-one/design.py      -> bible.json + decks.json
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "lh", os.path.join(HERE, "..", "library-hand", "design.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
clip, fft, xform, wrap = L.clip, L.fft, L.xform, L.wrap

CHAR = "#121212ff"       # charcoal black
CHAR2 = "#262420ff"      # charcoal lifted: rulings, linoleum
IVORY = "#e9e1cfff"
IVORY_DIM = "#e9e1cf55"
GREY = "#8a857aff"
GREY_DIM = "#8a857a66"
AMBER = "#d9a441ff"      # practical lamps: desk lamp, jack lamp, VU glow
AMBER_DIM = "#d9a44155"
RED = "#c41e1eff"        # red pencil only
CLEAR = "#00000000"

TYPE = "Courier New"     # typed scripts and wires
HEAD = "Bodoni MT"       # newspaper headlines, the Mercury card
GOTH = "Franklin Gothic Heavy"


# ---------------------------------------------------------------- helpers
def floor(col, color=CHAR2, amount=14, rot=0.0, opacity=1.0, name="Linoleum",
          why="Studio linoleum ruling, charcoal on charcoal."):
    return clip(1, col, name, "Lines",
                {"Fuzzyness": 0.05, "Amount": amount, "Width": 0.01,
                 "Rotation": rot, "Position": 0.5, "Color": color}, why,
                opacity=opacity)


def black(col, why="Black: the windowless room before a lamp."):
    return clip(1, col, "Charcoal", "Solid Color", {"Color": CHAR}, why)


def night(col, why="New Jersey night: a charcoal-to-grey sky gradient."):
    return clip(1, col, "Night Field", "Gradient",
                {"Method": "2 Colors", "Color 1": CHAR, "Color 2": CHAR2,
                 "Mode": "Smooth", "Dither": 0.0, "Type": "Vertical"}, why)


def mic(layer, col, color=IVORY, scale=0.9, opacity=0.9, name="RCA 44-BX", fft_=None,
        why="The RCA 44-BX: a diamond of satin chrome, figure-8, 8.5 lb on its yoke."):
    """The ribbon microphone as Geometry Pattern Maker diamonds (Square, rotated)."""
    return clip(layer, col, name, "Geometry Pattern Maker",
                {"Bloom": 0.15, "Bloom Mode": "Add", "Shape Types": "Square",
                 "Shape Rounding": 0.2, "Line Ammount": 18,
                 "Innter Color 1": color, "Inner color 2": GREY,
                 "Outer Color 1": GREY, "Outer Color 2": CHAR2,
                 "Inner Scale": 0.3, "Outer Scale": 1.2, "Intersect Scale": 0.5,
                 "Gloabal rot": 0.25}, why, opacity=opacity,
                effects=[xform(scale=scale * 100)],
                fft=fft_ if fft_ is not None else fft("Inner Scale", "low", 0.28, 0.42, 9.0, 400))


def ribbon(layer, col, color=IVORY, amount=40, opacity=0.8, name="Ribbon",
           why="The corrugated aluminium ribbon, 2.5 microns, inside the grille."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.1, "Amount": amount, "Width": 0.2,
                 "Rotation": 90.0, "Position": 0.5, "Color": color}, why,
                opacity=opacity, fft=fft("Fuzzyness", "high", 0.05, 0.45, 9.0, 250))


def clock(layer, col, color=IVORY, name="Studio Clock", opacity=0.9, speed=0.12,
          why="The big studio clock with a sweep second hand above the glass."):
    return clip(layer, col, name, "Spiral",
                {"Direction": "Clockwise", "Control Mode": "Even",
                 "Spread Even": 0.0, "Detail": 1.0, "Speed": speed, "Zoom": 0.8,
                 "Leafs": 1, "Distortion": 0.0, "Fuzzyness": 0.0,
                 "Ramification": 0.0, "Button": True, "Button Size": 0.05,
                 "Button Fuzzyness": 0.0, "Color": color, "BG Color": CLEAR},
                why, opacity=opacity)


def dial(layer, col, color=GREY, rings=12, size=0.7, width=0.02, name="Dial",
         opacity=0.8, fft_=None, effects=None,
         why="A round face: clock dial, lift dial, VU meter, or record."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": rings, "Size": size, "Spacing": 0.12,
                 "Line Width": width, "Style": "Stroke", "Gap": 0.0,
                 "Rotation": 0.0, "Rotation Step": 0.0,
                 "Rotation Alternate": False, "Color 1": color, "Color 2": color},
                why, opacity=opacity, effects=effects,
                fft=fft_ if fft_ is not None else fft("Line Width", "low", width, width * 2.5, 8.0, 450))


def lamp(col, color=AMBER_DIM, opacity=0.3, name="Practical Lamp", layer=4,
         why="One practical lamp: soft halation, a radial pool."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": color, "Color 2": CLEAR,
                 "Mode": "Smooth", "Dither": 0.0, "Type": "Radial"}, why,
                opacity=opacity)


def strobe(col, freq=0.12, color=IVORY, opacity=0.2, name="Flashbulb", layer=4,
           why="A flashbulb or a lamp failing."):
    return clip(layer, col, name, "Stroboscope",
                {"Frequency": freq, "Fade": True, "Color 1": color, "Color 2": CLEAR},
                why, opacity=opacity)


def wash(col, color, kind="Vertical", opacity=0.12, name="Wash", layer=6,
         why="A silver-gelatin tone over the frame."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": CLEAR, "Color 2": color,
                 "Mode": "Smooth", "Dither": 0.0, "Type": kind}, why,
                opacity=opacity)


def grain(col, opacity=0.07, name="Film Grain",
          why="Fine silver-gelatin grain over everything."):
    return clip(7, col, name, "Static", {"Mode": "Grayscale"}, why, opacity=opacity)


def blank(layer, col, why="Nothing here by design."):
    return clip(layer, col, "Blank", "Blank", {"Black BG": False}, why)


def text(col, s, color=IVORY, size=0.9, font=TYPE, align="Left", valign="Bottom",
         x=-860, y=460, name=None, layer=5, animated=False,
         why="Typed script copy, Courier, bottom-left."):
    return L.text(col, s, color=color, size=size, font=font, align=align,
                  valign=valign, x=x, y=y, name=name, layer=layer,
                  animated=animated, why=why)


def vu(col, color=AMBER, amp=0.06, name="VU Line",
       why="The program line on the board's VU meters: the one honest readout."):
    """Studio decks: SCOPE as a horizontal program line along the bottom."""
    return L.scope(col, color=color, position=0.88, amplitude=amp, name=name, why=why)


def strip(col, color=IVORY, amp=0.08, name="Soundtrack Strip",
          why="The optical soundtrack strip down the left edge: we are inside an account."):
    """Account decks: SCOPE turned vertical, hugging the left edge."""
    c = L.scope(col, color=color, position=0.04, amplitude=amp, name=name, why=why)
    c["params"]["Direction"] = "Vertical"
    c["params"]["Waves"] = 2
    return c


def cylinder(layer, col, color=IVORY_DIM, opacity=0.8, name="The Cylinder",
             why="The cylinder half buried in the pit, its end shedding flakes."):
    return clip(layer, col, name, "Tunnelines",
                {"Color 1": color, "Color 2": GREY_DIM, "Line Width": 0.01,
                 "Zoom": 2.4, "Vertical": 0.02, "Frequency": 0.04,
                 "Horizontal": 0.02}, why, opacity=opacity,
                fft=fft("Frequency", "low", 0.04, 0.2, 9.0, 700))


def headlights(layer, col, color=IVORY, grid=6, size=0.12, opacity=0.8,
               name="Headlights", why="A row of car headlights behind the crowd."):
    return clip(layer, col, name, "Metaballs",
                {"Grid": grid, "Blend": "Minimal", "Size": size, "Distance": 0.6,
                 "Radius": 0.2, "Fuzzyness": 0.6, "Speed": 0.2,
                 "Position X": 0.0, "Position Y": -0.4, "Color": color,
                 "BG Color": CLEAR}, why, opacity=opacity,
                fft=fft("Size", "low", size, size + 0.12, 8.0, 500))


def ray(layer, col, color=IVORY, opacity=0.9, name="Heat Ray",
        why="The heat ray: one beam of light from the mirror."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.4, "Amount": 1, "Width": 0.06, "Rotation": 18.0,
                 "Position": 0.5, "Color": color}, why, opacity=opacity,
                fft=fft("Width", "low", 0.03, 0.4, 12.0, 300))


def machine(layer, col, color=GREY, opacity=0.8, name="Fighting Machine", lines=9,
            why="A towering three-legged machine: tripod geometry rising from smoke."):
    return clip(layer, col, name, "Geometry Pattern Maker",
                {"Bloom": 0.05, "Bloom Mode": "Add", "Shape Types": "Triangle",
                 "Shape Rounding": 0.0, "Line Ammount": lines,
                 "Innter Color 1": color, "Inner color 2": CHAR2,
                 "Outer Color 1": color, "Outer Color 2": CHAR2,
                 "Inner Scale": 0.25, "Outer Scale": 1.6, "Intersect Scale": 0.4},
                why, opacity=opacity, fft=fft("Inner Scale", "mid", 0.22, 0.36, 8.0, 600))


def smoke(layer, col, color=GREY_DIM, opacity=0.6, name="Black Smoke",
          why="Drifting black smoke over the marshes."):
    return clip(layer, col, name, "Abstract Field",
                {"Octaves": 4, "Amplitude": 0.5, "Density": 0.45}, why,
                opacity=opacity,
                effects=[{"effect": "Tint", "params": {"Black To": CHAR, "White To": color}}],
                fft=fft("Density", "low", 0.4, 0.7, 7.0, 1500))


def underline(layer, col, y=0.62, name="Red Pencil Line", opacity=1.0,
              why="One red pencil line beneath the text. Red exists only here."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.012, "Rotation": 0.0,
                 "Position": y, "Color": RED}, why, opacity=opacity)


def page(layer, col, color=IVORY, opacity=0.85, name="Script Page",
         why="A typed script page, paper-clipped, ivory on charcoal."):
    return clip(layer, col, name, "Solid Color", {"Color": color}, why,
                opacity=opacity, effects=[xform(scale=36), {"effect": "Transform", "params": {"Scale W": 72.0, "Scale H": 100.0}}][:1])


# ================================================================ DECK 1
# STUDIO ONE - the room, 8:00 pm: microphone, foley, orchestra, glass, clock
def deck1():
    C = []
    cols = ["8 PM Air", "Roll It", "Facing Mics", "Foley Table",
            "Giant Cube", "Orchestra", "The Glass", "Dead Air"]
    # 1 Air time: the empty curb, the network announcement
    C += [black(1), mic(2, 1, scale=0.7, opacity=0.6, name="Network Mic",
                        why="Doyle's network microphone at left, the first thing lit."),
          clock(3, 1, why="The studio clock: 8:00 pm. Studio time is real time."),
          lamp(1, opacity=0.22),
          text(1, "COLUMBIA BROADCASTING\nSYSTEM - 8:00 PM\nSUNDAY 30 OCT 1938", font=HEAD, size=0.9,
               why="The network opening, in the building's own serif."),
          blank(6, 1), grain(1), vu(1)]
    # 2 Roll It: Welles at the microphone draws the circle; the lathe starts
    C += [floor(2), mic(2, 2, scale=1.0, name="Center Mic"),
          dial(3, 2, color=IVORY, rings=24, size=0.55, width=0.01, name="Lathe A",
               why="Nora lowers the cutting arm onto a turning black disc: lathe A."),
          lamp(2, opacity=0.18),
          text(2, "ROLL IT", font=TYPE, size=2.0, align="Center", valign="Center", x=0, y=0,
               animated=True, why="The roll-it signal: a small circle drawn in the air."),
          wash(2, GREY_DIM, kind="Radial", opacity=0.1), grain(2), vu(2)]
    # 3 Facing Mics: figure-8, actors clustered across the chrome grille
    C += [floor(3), mic(2, 3, scale=0.8, name="Figure-8 Grille"),
          ribbon(3, 3, why="The ribbon's figure-8: live front and back, dead at the sides."),
          lamp(3, opacity=0.2),
          text(3, "RCA 44-BX\n12 x 4.75 x 3.375 IN\n8.5 LB - FIGURE-8", size=0.8,
               why="The microphone's specification from its manual."),
          wash(3, IVORY_DIM, kind="Horizontal", opacity=0.08), grain(3), vu(3)]
    # 4 Foley Table: jar, thunder sheet, sandbox, cornstarch
    C += [floor(4, amount=28, rot=90.0, name="Sandbox Boards"),
          dial(2, 4, color=GREY, rings=6, size=0.35, width=0.03, name="Iron Pot",
               effects=[xform(x=-300)], why="The cast-iron vessel whose rim the jar scrapes."),
          dial(3, 4, color=IVORY, rings=3, size=0.18, width=0.02, name="Jam Jar Lid",
               effects=[xform(x=-300)], fft_=fft("Size", "high", 0.16, 0.24, 9.0, 200),
               why="The glass jam jar turning in the pot: the cylinder unscrewing."),
          lamp(4, color=AMBER_DIM, opacity=0.24, name="Foley Lamp"),
          text(4, "JAR + IRON POT\nSANDBOX - CORNSTARCH\nROLLER SKATES", size=0.8,
               why="Ora Nichols's metaphors: mundane objects, unearthly sounds."),
          blank(6, 4), grain(4), vu(4, name="Foley Mic")]
    # 5 Giant Cube: nine motors, pumps and whistles
    C += [floor(5), geo_cube(2, 5),
          clip(3, 5, "Nine Motors", "Metaballs",
               {"Grid": 3, "Blend": "Minimal", "Size": 0.16, "Distance": 0.5,
                "Radius": 0.5, "Fuzzyness": 0.1, "Speed": 1.2, "Position X": 0.0,
                "Position Y": 0.0, "Color": GREY, "BG Color": CLEAR},
               "Nine independent electric motors behind switches and levers.", opacity=0.8,
               fft=fft("Size", "low", 0.14, 0.3, 9.0, 300)),
          strobe(5, freq=0.5, color=AMBER, opacity=0.12, name="Machine Gun",
                 why="The cube's rapid-fire machine-gun bursts."),
          text(5, "GIANT-CUBE MACHINE\n5 FT x 2 FT\n9 MOTORS - PUMPS - WHISTLES", size=0.8),
          blank(6, 5), grain(5), vu(5, amp=0.1)]
    # 6 Orchestra: Herrmann and 27 musicians through the side window
    C += [floor(6),
          clip(2, 6, "Music Stands", "Lines",
               {"Fuzzyness": 0.0, "Amount": 27, "Width": 0.02, "Rotation": 90.0,
                "Position": 0.5, "Color": GREY}, "Twenty-seven music stands in a clustered arc.",
               opacity=0.6, fft=fft("Width", "mid", 0.015, 0.05, 8.0, 500)),
          clip(3, 6, "Piano Filler", "Sine Wave",
               {"Waves": 3, "Mode": "Line", "Line Width": 0.02, "Fuzzyness": 0.1,
                "Direction": "Horizontal", "Mirror": True, "Frequency": 2.0,
                "Main Speed": 1.0, "Modulator": 1.0, "Modulation Depth": 0.3,
                "Modulator Speed": 1.0, "Amplitude": 0.12, "Position": 0.5,
                "Color": IVORY, "BG Color": CLEAR},
               "The solo piano filler, played for unbearably long stretches.", opacity=0.8,
               fft=fft("Amplitude", "mid", 0.1, 0.3, 9.0, 600)),
          lamp(6, opacity=0.2),
          text(6, "BERNARD HERRMANN\n27 MUSICIANS\nDEBUSSY - CHOPIN FILLER", size=0.8),
          wash(6, AMBER_DIM, kind="Horizontal", opacity=0.08), grain(6), vu(6)]
    # 7 The Glass: the control booth behind double-paned glass, VU glow
    C += [floor(7),
          clip(2, 7, "Booth Glass", "Lines",
               {"Fuzzyness": 0.0, "Amount": 2, "Width": 0.6, "Rotation": 0.0,
                "Position": 0.35, "Color": CHAR2}, "The double-paned soundproof window.",
               opacity=1.0),
          dial(3, 7, color=AMBER, rings=4, size=0.12, width=0.03, name="VU Meters",
               effects=[xform(y=-200)], fft_=fft("Size", "mid", 0.1, 0.2, 10.0, 250),
               why="The board's round VU meters glowing behind the glass."),
          lamp(7, color=AMBER_DIM, opacity=0.26, name="Console Glow"),
          text(7, "CONTROL BOOTH\nHOUSEMAN - TAYLOR\nACOUSTICALLY SEVERED", size=0.8),
          wash(7, AMBER_DIM, kind="Vertical", opacity=0.1), grain(7), vu(7)]
    # 8 Dead Air: Welles raises his hands; everyone freezes
    C += [black(8, why="Dead air: the room freezes under Welles's raised hands."),
          mic(2, 8, scale=0.9, opacity=0.35, fft_={}, name="Silent Mic",
              why="The microphone with nothing in front of it. It does not react."),
          blank(3, 8, "Nobody moves."),
          blank(4, 8, "No lamp change in the silence."),
          text(8, "... ", font=TYPE, size=1.4, name="Dead Air",
               why="Dead air. Nothing typed."),
          blank(6, 8), grain(8, opacity=0.1),
          clip(8, 8, "Flat Line", "Sine Wave",
               {"Waves": 1, "Mode": "Line", "Line Width": 0.02, "Fuzzyness": 0.0,
                "Direction": "Horizontal", "Mirror": False, "Frequency": 0.0,
                "Main Speed": 1.0, "Modulator": 0.0, "Modulation Depth": 0.0,
                "Modulator Speed": 1.0, "Amplitude": 0.0, "Position": 0.88,
                "Color": AMBER, "BG Color": CLEAR},
               "The program line flat: the pause stretched for an agonizing length.")]
    return {"name": "Studio One", "slug": "studio", "theme": "studio",
            "world": ("CBS Studio One, fourth floor, 485 Madison Avenue, 8:00 pm, Sunday 30 October 1938: "
                      "a windowless, double-height room of microphones, music stands and a foley table "
                      "that looks like a machine shop. Silver-gelatin newsreel light - charcoal blacks, "
                      "ivory highlights, soft halation round the practical lamps - and one amber, the "
                      "glow of the board behind the glass. The RCA 44-BX is the hero object, a chrome "
                      "diamond that hears front and back and nothing at its sides. Typed copy in "
                      "Courier, the network's serif for the opening."),
            "palette": [{"role": "bed", "hex": "#121212", "why": "Charcoal: no daylight reaches this room."},
                        {"role": "body", "hex": "#e9e1cf", "why": "Ivory highlights on chrome and paper."},
                        {"role": "figure", "hex": "#8a857a", "why": "Warm grey for iron, wood and wool."},
                        {"role": "light", "hex": "#d9a441", "why": "Practical-lamp amber: the board, the desk lamp, the VU glow."},
                        {"role": "text", "hex": "#e9e1cf", "why": "Typed ivory."},
                        {"role": "aura", "hex": "#8a857a", "why": "Grey tone; no colour enters the studio."}],
            "columns": cols,
            "text_corpus": ["COLUMBIA BROADCASTING SYSTEM", "8:00 PM", "ROLL IT", "RCA 44-BX",
                            "FIGURE-8", "JAR + IRON POT", "GIANT-CUBE MACHINE", "27 MUSICIANS",
                            "CONTROL BOOTH", "DEAD AIR", "MERCURY THEATRE", "STUDIO ONE"],
            "moments": [
                "Roll it: Scene Launch 2 on the downbeat, tap the row-5 TEXT pad so ROLL IT retypes, and hold the "
                "row-3 FIGURE pad so the lathe disc turns under Nora's arm.",
                "Foley: Scene Launch 4 and roll the bank-A knob with ECHO lit so the jar lid leaves rings in the "
                "iron pot; tap STUTTER on each scrape.",
                "Dead air: walk UP to column 8 on the loudest moment of the track, let the room freeze for a full "
                "phrase, then fire Scene Launch 1 to come back on air."],
            "clips": C}


def geo_cube(layer, col):
    return clip(layer, col, "Giant Cube", "Geometry Pattern Maker",
                {"Bloom": 0.05, "Bloom Mode": "Add", "Shape Types": "Square",
                 "Shape Rounding": 0.0, "Line Ammount": 12, "Innter Color 1": GREY,
                 "Inner color 2": CHAR2, "Outer Color 1": IVORY_DIM,
                 "Outer Color 2": CHAR2, "Inner Scale": 0.4, "Outer Scale": 1.3,
                 "Intersect Scale": 0.6},
                "Arthur Nichols's five-foot sound machine as a nest of squares.",
                opacity=0.85, fft=fft("Inner Scale", "low", 0.36, 0.5, 9.0, 300))


# ================================================================ DECK 2
# GROVERS MILL - the accounts, with the soundtrack strip down the left edge
def deck2():
    C = []
    cols = ["Observatory", "The Farm", "The Hum", "The Cap",
            "Emergence", "Heat Ray", "Field Lost", "Forty Dead"]
    # 1 Observatory: Princeton, the telescope clockwork
    C += [night(1), dial(2, 1, color=IVORY_DIM, rings=16, size=0.8, width=0.01, name="Telescope Dome",
                         why="The observatory dome's ribs."),
          clip(3, 1, "Mars Disc", "Shaper",
               {"Scale": 0.06, "Noise Type": "Grain", "Noise Amount": 0.2, "Noise Speed": 0.1,
                "Color": IVORY, "Outline": 0.0, "Outline Color": IVORY},
               "Mars in the eyepiece: a small grainy disc. No red: red is the pencil's.",
               fft=fft("Scale", "low", 0.06, 0.09, 8.0, 500)),
          lamp(1, color=IVORY_DIM, opacity=0.14, name="Eyepiece Glow"),
          text(1, "PRINCETON OBSERVATORY\nPIERSON - PHILLIPS", size=0.8),
          blank(6, 1), grain(1), strip(1)]
    # 2 The Farm: Wilmuth farm, headlights, crowd silhouettes
    C += [night(2), headlights(2, 2),
          clip(3, 2, "Crowd", "Lines",
               {"Fuzzyness": 0.3, "Amount": 40, "Width": 0.5, "Rotation": 90.0,
                "Position": 0.5, "Color": CHAR}, "A crowd of silhouettes against the headlights.",
               opacity=0.9, fft=fft("Fuzzyness", "mid", 0.25, 0.5, 7.0, 600)),
          lamp(2, color=IVORY_DIM, opacity=0.18, name="Headlamp Pool"),
          text(2, "WILMUTH FARM\nGROVERS MILL, N.J.", size=0.8),
          blank(6, 2), grain(2), strip(2)]
    # 3 The Hum: the cylinder hums; nobody in the room is making it
    C += [night(3), cylinder(2, 3),
          clip(3, 3, "The Hum", "Sine Wave",
               {"Waves": 8, "Mode": "Line", "Line Width": 0.01, "Fuzzyness": 0.2,
                "Direction": "Horizontal", "Mirror": True, "Frequency": 12.0,
                "Main Speed": 4.0, "Modulator": 0.0, "Modulation Depth": 0.0,
                "Modulator Speed": 1.0, "Amplitude": 0.04, "Position": 0.5,
                "Color": IVORY, "BG Color": CLEAR},
               "The hum: a dense, even vibration in the air above the pit.", opacity=0.7,
               fft=fft("Amplitude", "low", 0.03, 0.2, 10.0, 400)),
          lamp(3, color=AMBER_DIM, opacity=0.14, name="Sealed Jack Lamp",
               why="The only lit jack in the field is the sealed one."),
          text(3, "THE HUM", size=1.2),
          blank(6, 3), grain(3), strip(3)]
    # 4 The Cap: the top begins to turn
    C += [night(4), cylinder(2, 4, opacity=0.9, name="Cylinder End"),
          dial(3, 4, color=IVORY, rings=5, size=0.3, width=0.02, name="The Cap Turns",
               fft_=fft("Size", "mid", 0.28, 0.4, 9.0, 300),
               why="The circular top beginning to turn - matched to the jam jar lid in Studio One."),
          lamp(4, color=IVORY_DIM, opacity=0.22, name="Pit Light"),
          text(4, "THE TOP IS\nBEGINNING TO TURN", size=0.8),
          blank(6, 4), grain(4), strip(4)]
    # 5 Emergence: ribbed feelers in bad light
    C += [night(5), cylinder(2, 5, opacity=0.6),
          clip(3, 5, "Ribbed Feelers", "Spiral",
               {"Direction": "Anti-clockwise", "Control Mode": "Detailed", "Spread Even": 2.0,
                "Detail": 3.0, "Speed": 0.4, "Zoom": 1.4, "Leafs": 3, "Distortion": 30.0,
                "Fuzzyness": 0.3, "Ramification": 0.6, "Button": False, "Button Size": 0.0,
                "Button Fuzzyness": 0.0, "Color": GREY, "BG Color": CLEAR},
               "The hatch's ribbed feelers - the tentacles - in bad light.", opacity=0.7,
               fft=fft("Distortion", "low", 20.0, 60.0, 8.0, 500)),
          strobe(5, freq=0.08, color=IVORY_DIM, opacity=0.18, name="Bad Light"),
          text(5, "SOMETHING'S WRIGGLING\nOUT OF THE SHADOW", size=0.8),
          blank(6, 5), grain(5, opacity=0.1), strip(5)]
    # 6 Heat Ray: the mirror, the beam
    C += [night(6), headlights(2, 6, opacity=0.5),
          ray(3, 6),
          strobe(6, freq=0.3, color=IVORY, opacity=0.25, name="Ray Flash"),
          text(6, "A JET OF FLAME\nSPRINGS FROM THE MIRROR", size=0.8),
          wash(6, IVORY_DIM, kind="Radial", opacity=0.14), grain(6), strip(6, amp=0.2)]
    # 7 Field Lost: the line goes dead, the broadcast from the farm is lost
    C += [black(7, why="The broadcast from the farm is lost."),
          blank(2, 7, "Nothing from the field."),
          blank(3, 7, "Nothing from the field."),
          blank(4, 7, "The sealed lamp dies."),
          text(7, "WE ARE UNABLE TO\nCONTINUE THE BROADCAST", size=0.8),
          blank(6, 7), grain(7, opacity=0.12),
          strip(7, amp=0.0, name="Strip Silent", why="The strip runs on, carrying nothing.")]
    # 8 Forty Dead: the field in smoke, martial law
    C += [night(8), smoke(2, 8),
          clip(3, 8, "Stone Wall", "Lines",
               {"Fuzzyness": 0.2, "Amount": 6, "Width": 0.3, "Rotation": 0.0,
                "Position": 0.7, "Color": GREY_DIM},
               "The stone wall Phillips was last seen behind. He is never shown dead.", opacity=0.7),
          lamp(8, color=IVORY_DIM, opacity=0.1, name="Embers"),
          text(8, "FORTY PEOPLE\nMARTIAL LAW", size=0.8),
          blank(6, 8), grain(8), strip(8)]
    return {"name": "Grovers Mill", "slug": "grovers-mill", "theme": "account",
            "world": ("The accounts, exactly as the soundtrack gives them: the observatory, the Wilmuth farm, "
                      "the hum, the cap turning, the feelers in bad light, the heat ray from the mirror, the "
                      "dead line, forty people. Every scene here is inside a reconstruction, so the optical "
                      "soundtrack strip runs down the left edge. Night is charcoal-to-grey; the light is car "
                      "headlights and one beam. The crowd is silhouettes; Phillips is never shown dead."),
            "palette": [{"role": "bed", "hex": "#121212", "why": "New Jersey night."},
                        {"role": "body", "hex": "#e9e1cf", "why": "Headlights, the cylinder's pale ribs, the beam."},
                        {"role": "figure", "hex": "#8a857a", "why": "Feelers and smoke in warm grey."},
                        {"role": "light", "hex": "#e9e1cf", "why": "Ivory flashes; amber only for the sealed jack."},
                        {"role": "text", "hex": "#e9e1cf", "why": "The reporter's words, typed."},
                        {"role": "aura", "hex": "#e9e1cf", "why": "An ivory radial when the ray fires."}],
            "columns": cols,
            "text_corpus": ["GROVERS MILL, N.J.", "WILMUTH FARM", "THE HUM", "THE TOP IS TURNING",
                            "SOMETHING'S WRIGGLING", "A JET OF FLAME", "UNABLE TO CONTINUE",
                            "FORTY PEOPLE", "MARTIAL LAW", "PRINCETON", "PIERSON", "PHILLIPS"],
            "moments": [
                "The cap: Scene Launch 4, hold the row-3 FIGURE pad so the cap turns on the mids, and ride the "
                "bank-B knob with TUNNEL lit to pull the cylinder's ribs inward.",
                "Heat ray: Scene Launch 5 then UP to Heat Ray on the drop; the beam's width follows the kick. "
                "Tap STROBE on the hit only, never twice in a bar.",
                "Field lost: UP to column 7 mid-phrase so the picture cuts to black under the strip, hold a full "
                "bar of nothing, then Scene Launch 1 of deck 1 to return to the studio."],
            "clips": C}


# ================================================================ DECK 3
# THE VISITORS - the red pencil. Red exists only in this deck, only on pencil marks.
def deck3():
    C = []
    cols = ["The Curb", "The Lobby", "The Card", "The Latch",
            "Gloves Off", "Red Line", "Station Break", "Clock Held"]
    # 1 The Curb: a black sedan, two motionless homburgs
    C += [floor(1, color=CHAR2, amount=6, name="Wet Pavement"),
          clip(2, 1, "Black Sedan", "Shaper",
               {"Scale": 0.5, "Noise Type": "Hatched", "Noise Amount": 0.1, "Noise Speed": 0.0,
                "Color": CHAR2, "Outline": 0.02, "Outline Color": GREY},
               "A black sedan at the curb, its outline catching the street light.",
               opacity=0.9, effects=[xform(y=180, scale=100)], fft={}),
          clip(3, 1, "Two Homburgs", "Metaballs",
               {"Grid": 2, "Blend": "Minimal", "Size": 0.1, "Distance": 0.3, "Radius": 0.1,
                "Fuzzyness": 0.05, "Speed": 0.0, "Position X": 0.0, "Position Y": 0.0,
                "Color": CHAR, "BG Color": CLEAR},
               "Two motionless homburgs inside. They never hurry.", opacity=1.0),
          lamp(1, color=IVORY_DIM, opacity=0.14, name="Street Lamp"),
          blank(5, 1, "The visitors never speak: no text."),
          blank(6, 1), grain(1), vu(1, amp=0.03)]
    # 2 The Lobby: brass revolving door, the guard's desk, the switchboard
    C += [floor(2, amount=20, rot=45.0, name="Marble"),
          dial(2, 2, color=GREY, rings=1, size=0.6, width=0.02, name="Lift Dial",
               effects=[xform(y=-240, scale=60)],
               why="The semicircular lift dial above the closed gate."),
          clip(3, 2, "Revolving Door", "Spiral",
               {"Direction": "Clockwise", "Control Mode": "Even", "Spread Even": 0.0, "Detail": 1.0,
                "Speed": 0.3, "Zoom": 1.0, "Leafs": 4, "Distortion": 0.0, "Fuzzyness": 0.0,
                "Ramification": 0.0, "Button": False, "Button Size": 0.0, "Button Fuzzyness": 0.0,
                "Color": AMBER_DIM, "BG Color": CLEAR},
               "The brass revolving door still turning as they step onto the marble.", opacity=0.6),
          lamp(2, color=AMBER_DIM, opacity=0.3, name="Desk Lamp"),
          blank(5, 2, "The visitors never speak."),
          blank(6, 2), grain(2), vu(2, amp=0.03)]
    # 3 The Card: the network's own sentence, one red line
    C += [black(3),
          page(2, 3, name="Visitors' Card", why="A small card in a grey kid glove."),
          underline(3, 3, y=0.52, name="Red Line On Card"),
          lamp(3, color=AMBER_DIM, opacity=0.24, name="Desk Lamp"),
          blank(5, 3, "Amos reads it with moving lips; nobody in frame speaks."),
          blank(6, 3), grain(3), vu(3, amp=0.03)]
    # 4 The Latch: credentials pressed to the glass; Nora opens
    C += [floor(4, amount=8, rot=90.0, name="Door Panels"),
          dial(2, 4, color=IVORY_DIM, rings=1, size=0.3, width=0.03, name="Porthole",
               why="The small window in the control-room door."),
          clip(3, 4, "Ring Of Keys", "Rings",
               {"Num Rings": 3, "Size": 0.1, "Spacing": 0.3, "Line Width": 0.03, "Style": "Stroke",
                "Gap": 30.0, "Rotation": 0.0, "Rotation Step": 40.0, "Rotation Alternate": True,
                "Color 1": GREY, "Color 2": GREY},
               "They knock while holding the keys.", opacity=0.8,
               effects=[xform(x=260, y=-80)], fft={}),
          lamp(4, color=AMBER_DIM, opacity=0.2, name="Console Glow"),
          text(4, "FEDERAL SUPERVISION\nDO NOT ENTER", size=0.8,
               why="The notice on the studio door; written by the network, not spoken by them."),
          blank(6, 4), grain(4), vu(4, amp=0.04)]
    # 5 Gloves Off: Carver patches the artillery wire himself
    C += [floor(5, amount=24, rot=90.0, name="Jack Field"),
          clip(2, 5, "Patch Cords", "Sine Wave",
               {"Waves": 5, "Mode": "Line", "Line Width": 0.012, "Fuzzyness": 0.0,
                "Direction": "Vertical", "Mirror": False, "Frequency": 1.0, "Main Speed": 1.0,
                "Modulator": 0.5, "Modulation Depth": 0.4, "Modulator Speed": 1.0,
                "Amplitude": 0.2, "Position": 0.6, "Color": GREY, "BG Color": CLEAR},
               "Patch cords hanging across the jack field.", opacity=0.8,
               fft=fft("Amplitude", "mid", 0.18, 0.3, 7.0, 600)),
          clip(3, 5, "Bare Hand", "Shaper",
               {"Scale": 0.12, "Noise Type": "Hatched", "Noise Amount": 0.3, "Noise Speed": 0.2,
                "Color": GREY, "Outline": 0.0, "Outline Color": GREY},
               "Carver's bare hand on the board, creased and ridged.", opacity=0.9,
               fft=fft("Noise Amount", "low", 0.2, 0.6, 8.0, 500)),
          lamp(5, color=AMBER_DIM, opacity=0.26, name="Jack Lamps"),
          blank(5, 5, "The visitors never speak."),
          blank(6, 5), grain(5), vu(5, amp=0.08)]
    # 6 Red Line: Small red-pencils the closing pages
    C += [black(6),
          page(2, 6, why="The station-break page, typed."),
          underline(3, 6, y=0.48, name="Red Pencil",
                    why="Small's nickel-ferruled red pencil draws one line. The only red on screen."),
          lamp(6, color=IVORY_DIM, opacity=0.2, name="Page Light"),
          text(6, "THIS IS A\nDRAMATIZATION", font=TYPE, size=1.1, color=CHAR, align="Center",
               valign="Center", x=0, y=-20, why="The line under the red pencil, typed on the page."),
          blank(6, 6), grain(6), vu(6, amp=0.03)]
    # 7 Station Break: Doyle reads the red line and goes calm
    C += [floor(7),
          mic(2, 7, scale=0.7, name="Doyle's Mic"),
          underline(3, 7, y=0.7, name="Red Line At Eye", opacity=0.9,
                    why="The page clipped at Doyle's eye level, one red line beneath the text."),
          lamp(7, color=AMBER_DIM, opacity=0.2),
          text(7, "YOU ARE LISTENING\nTO A CBS PRESENTATION", size=0.8,
               why="The station identification, read calm."),
          wash(7, GREY_DIM, kind="Radial", opacity=0.1), grain(7), vu(7, amp=0.05)]
    # 8 Clock Held: Small pins the sweep hand; Welles reads from memory
    C += [floor(8),
          clock(2, 8, speed=0.0, name="Clock Held",
                why="A ridged finger pins the sweep hand. The clock reads 8:41 pm."),
          mic(3, 8, scale=0.5, opacity=0.6, name="Welles Eyes Closed"),
          lamp(8, color=AMBER_DIM, opacity=0.16),
          text(8, "8:41 PM", font=TYPE, size=1.4,
               why="Real time, never the play's time."),
          blank(6, 8), grain(8), vu(8, amp=0.07)]
    return {"name": "The Visitors", "slug": "visitors", "theme": "takeover",
            "world": ("The r04 alternate history: the invasion is real, and two visitors with FCC credentials "
                      "make the broadcasters call it theatre. They never speak, never hurry, never touch first; "
                      "they knock while holding the keys. A black sedan at the curb, a brass revolving door, a "
                      "card read with moving lips, a latch, a bare ridged hand on the board, and the red pencil. "
                      "Red exists only on pencil marks: three clips in the whole composition."),
            "palette": [{"role": "bed", "hex": "#121212", "why": "Charcoal."},
                        {"role": "body", "hex": "#e9e1cf", "why": "Paper: cards, pages, the porthole."},
                        {"role": "figure", "hex": "#c41e1e", "why": "RED PENCIL ONLY. Three lines, nothing else."},
                        {"role": "light", "hex": "#d9a441", "why": "Desk lamp, jack lamps, console glow."},
                        {"role": "text", "hex": "#e9e1cf", "why": "Notices and typed pages; the visitors themselves never get a caption."},
                        {"role": "aura", "hex": "#8a857a", "why": "Grey only."}],
            "columns": cols,
            "text_corpus": ["FEDERAL SUPERVISION", "DO NOT ENTER", "THIS IS A DRAMATIZATION",
                            "YOU ARE LISTENING", "8:41 PM", "JOHN", "JOHN", "VISITORS' BOOK",
                            "FCC FIELD DIVISION", "CUSTODY", "REHEARSAL RACK", "NEXT WEEK"],
            "moments": [
                "Red line: Scene Launch 6 with every effect off; hold the row-3 FIGURE pad so the red pencil "
                "line appears only while you hold it, and let it go on the downbeat.",
                "Station break: UP to column 7, pull fader 3 down to a third so the red line sits under "
                "Doyle's microphone like a thought he cannot finish.",
                "Clock held: column 8, push Track knob 8 (TIME) fully anticlockwise so every generator in "
                "the room stops with the sweep hand; bring it back to centre to release."],
            "clips": C}


# ================================================================ DECK 4
# NEW YORK - the roof, the bombers, the window, nineteen machines (accounts)
def deck4():
    C = []
    cols = ["The Battery", "Bombers", "The Dive", "The Roof",
            "Black Smoke", "The Window", "Nineteen", "Peaceful Study"]
    C += [night(1), machine(2, 1, opacity=0.5, name="Distant Tripod"),
          clip(3, 1, "Gun Battery", "Lines",
               {"Fuzzyness": 0.1, "Amount": 4, "Width": 0.03, "Rotation": 30.0, "Position": 0.4,
                "Color": GREY}, "Four gun barrels raised at 30 degrees.", opacity=0.9,
               fft=fft("Width", "low", 0.02, 0.08, 10.0, 250)),
          strobe(1, freq=0.4, color=IVORY, opacity=0.2, name="Muzzle Flash"),
          text(1, "THE BATTERY\nWATCHUNG MOUNTAINS", size=0.8),
          blank(6, 1), grain(1), strip(1)]
    C += [night(2), smoke(2, 2, opacity=0.4),
          clip(3, 2, "Bomber Formation", "Rings",
               {"Num Rings": 3, "Size": 0.05, "Spacing": 2.0, "Line Width": 0.04, "Style": "Fill",
                "Gap": 0.0, "Rotation": 0.0, "Rotation Step": 0.0, "Rotation Alternate": False,
                "Color 1": GREY, "Color 2": GREY},
               "Bombers close together, ready to attack.", opacity=0.9,
               effects=[xform(y=-200)], fft=fft("Spacing", "mid", 1.6, 2.4, 7.0, 600)),
          lamp(2, color=IVORY_DIM, opacity=0.1, name="Low Cloud"),
          text(2, "LANGHAM FIELD\nBOMBERS IN FORMATION", size=0.8),
          blank(6, 2), grain(2), strip(2)]
    C += [night(3), machine(2, 3, opacity=0.8, name="Cowl Fills Glass"),
          clip(3, 3, "Nose Glazing", "Tunnelines",
               {"Color 1": GREY, "Color 2": CHAR2, "Line Width": 0.02, "Zoom": 3.5, "Vertical": 0.2,
                "Frequency": 0.4, "Horizontal": 0.0},
               "The glazed nose rushing toward the cowl: very large, fast.", opacity=0.7,
               fft=fft("Frequency", "low", 0.4, 1.4, 10.0, 300)),
          strobe(3, freq=0.6, color=IVORY_DIM, opacity=0.14, name="Engine Failing"),
          text(3, "DIVING ON THE\nFIRST MACHINE", size=0.8),
          blank(6, 3), grain(3), strip(3, amp=0.18)]
    C += [night(4), clip(2, 4, "Skyline", "Line Scape",
                         {"Tilt": 0.0, "Direction": 0.0, "Position Y": 4.0, "Speed": 0.0, "Height": 8.0,
                          "Jagginess": 1.0, "Wobble": 0.0, "Attenuation": 30.0, "Line Width": 0.3,
                          "Fuzzyness": 0.0, "Color": GREY, "Show Knots": False},
                         "Manhattan's skyline from the roof of Broadcasting Building.", opacity=0.8),
          smoke(3, 4, opacity=0.5, name="Smoke Over Hudson"),
          lamp(4, color=IVORY_DIM, opacity=0.12, name="Bells"),
          text(4, "ROOF OF\nBROADCASTING BUILDING", size=0.8),
          blank(6, 4), grain(4), strip(4)]
    C += [night(5), smoke(2, 5, opacity=0.8),
          smoke(3, 5, color=IVORY_DIM, opacity=0.3, name="Fifty Feet"),
          blank(4, 5, "The smoke takes the light."),
          text(5, "FIFTY FEET\nAWAY", size=1.0),
          blank(6, 5), grain(5, opacity=0.12), strip(5, amp=0.04)]
    # The Window: the second proof - the avenue untouched (studio, so VU not strip)
    C += [floor(6, color=CHAR2, amount=4, rot=90.0, name="Tall Window"),
          headlights(2, 6, color=AMBER_DIM, grid=8, size=0.06, opacity=0.6, name="Avenue Lights"),
          clip(3, 6, "Rain On Glass", "Static", {"Mode": "Grayscale"},
               "Wet pavement and rain on the glass: the avenue untouched.", opacity=0.08),
          lamp(6, color=AMBER_DIM, opacity=0.2, name="Shop Windows"),
          text(6, "THE AVENUE\nUNTOUCHED", size=0.9,
               why="The page has outrun the world."),
          blank(6, 6), grain(6), vu(6)]
    C += [night(7), clip(2, 7, "Nineteen Machines", "Lines",
                         {"Fuzzyness": 0.1, "Amount": 19, "Width": 0.02, "Rotation": 90.0,
                          "Position": 0.5, "Color": GREY}, "A long row of towering machines, cowls open and empty.",
                         opacity=0.7),
          machine(3, 7, opacity=0.6, name="Empty Cowl", lines=6),
          clip(4, 7, "Black Birds", "Metaballs",
               {"Grid": 5, "Blend": "Minimal", "Size": 0.04, "Distance": 0.9, "Radius": 0.9,
                "Fuzzyness": 0.0, "Speed": 2.0, "Position X": 0.0, "Position Y": 0.5,
                "Color": CHAR, "BG Color": CLEAR}, "Black birds wheeling above.", opacity=1.0),
          text(7, "NINETEEN MACHINES\nCENTRAL PARK", size=0.8),
          blank(6, 7), grain(7), strip(7)]
    C += [floor(8, color=CHAR2, amount=10, name="Study Shelves"),
          lamp(8, color=AMBER_DIM, opacity=0.34, name="Study Lamp", layer=2),
          clip(3, 8, "Pierson's Pen", "Sine Wave",
               {"Waves": 1, "Mode": "Line", "Line Width": 0.01, "Fuzzyness": 0.0,
                "Direction": "Horizontal", "Mirror": False, "Frequency": 2.0, "Main Speed": 1.0,
                "Modulator": 1.0, "Modulation Depth": 0.3, "Modulator Speed": 1.0,
                "Amplitude": 0.04, "Position": 0.6, "Color": IVORY, "BG Color": CLEAR},
               "Pierson's journal pen in the peaceful study.", opacity=0.8,
               fft=fft("Amplitude", "mid", 0.03, 0.1, 7.0, 800)),
          blank(4, 8, "The lamp is on layer 2 here."),
          text(8, "PEACEFUL STUDY\nAT PRINCETON", size=0.8),
          blank(6, 8), grain(8), strip(8, amp=0.05)]
    return {"name": "New York", "slug": "new-york", "theme": "account",
            "world": ("The second half's accounts: the battery in the Watchung Mountains, the bombers from "
                      "Langham Field, the dive into the first machine, the roof of Broadcasting Building with "
                      "smoke over the Hudson, fifty feet away, nineteen machines in Central Park with black "
                      "birds wheeling, and the peaceful study. One column is not an account: The Window, the "
                      "second proof - the avenue outside is wet, lit and untouched, so the strip gives way to "
                      "the board's program line."),
            "palette": [{"role": "bed", "hex": "#121212", "why": "Night over the city."},
                        {"role": "body", "hex": "#8a857a", "why": "Machines, guns, skyline: grey."},
                        {"role": "figure", "hex": "#8a857a", "why": "Smoke and cowls."},
                        {"role": "light", "hex": "#e9e1cf", "why": "Muzzle flashes; amber only for the untouched avenue."},
                        {"role": "text", "hex": "#e9e1cf", "why": "Place names, typed."},
                        {"role": "aura", "hex": "#8a857a", "why": "Grey."}],
            "columns": cols,
            "text_corpus": ["THE BATTERY", "LANGHAM FIELD", "DIVING ON THE FIRST MACHINE",
                            "ROOF OF BROADCASTING BUILDING", "FIFTY FEET AWAY", "THE AVENUE UNTOUCHED",
                            "NINETEEN MACHINES", "CENTRAL PARK", "PEACEFUL STUDY", "PRINCETON",
                            "THE HUDSON", "BAYONNE"],
            "moments": [
                "The dive: Scene Launch 3 on the build and push Track knob 8 (TIME) past three-quarters so the "
                "nose glazing rushes; drop it to centre on the impact.",
                "The window: UP from The Roof to The Window on the drop - smoke cuts to a wet, lit, untouched "
                "avenue. Hold it; that is the proof.",
                "Nineteen: column 7, bank-D knob at a third with MIRROR QUAD lit so the row of machines "
                "multiplies; release on the line about the birds."],
            "clips": C}


# ================================================================ DECK 5
# THE MORNING AFTER - the wildcard: blue uniforms, flashbulbs, headlines, the myth
def deck5():
    C = []
    cols = ["9 PM Doors", "Switchboard", "Flashbulbs", "Headlines",
            "Two Percent", "Hooper vs Myth", "The Disc", "Next Week"]
    C += [black(1), clip(2, 1, "Blue Uniforms", "Lines",
                         {"Fuzzyness": 0.2, "Amount": 9, "Width": 0.5, "Rotation": 90.0, "Position": 0.5,
                          "Color": CHAR2}, "The doors burst open: a wall of dark uniforms.", opacity=1.0,
                         fft=fft("Fuzzyness", "mid", 0.15, 0.4, 8.0, 400)),
          clock(3, 1, name="9:00 PM", speed=0.0, why="The studio clock at 9:00 pm."),
          strobe(1, freq=0.2, color=IVORY, opacity=0.2),
          text(1, "9:00 PM\nTHE DOORS OPEN", size=0.9),
          blank(6, 1), grain(1), vu(1, amp=0.02)]
    C += [floor(2, amount=30, rot=90.0, name="Switchboard Jacks"),
          clip(2, 2, "Sea Of Light", "Checkered",
               {"Num X": 40, "Num Y": 12, "Color 1": CHAR, "Color 2": AMBER_DIM},
               "The switchboard as a vast sea of light.", opacity=0.6),
          clip(3, 2, "Lamps Ringing", "Stroboscope",
               {"Frequency": 0.7, "Fade": True, "Color 1": AMBER, "Color 2": CLEAR},
               "Every line lit, flickering with calls.", opacity=0.14),
          lamp(2, color=AMBER_DIM, opacity=0.2),
          text(2, "A VAST SEA\nOF LIGHT", size=1.0),
          blank(6, 2), grain(2), vu(2, amp=0.1)]
    C += [black(3), mic(2, 3, scale=0.5, opacity=0.8, name="Battery Of Mics",
                        why="Welles before a battery of microphones, unshaven."),
          clip(3, 3, "Press Corps", "Metaballs",
               {"Grid": 4, "Blend": "Minimal", "Size": 0.2, "Distance": 0.6, "Radius": 0.4,
                "Fuzzyness": 0.2, "Speed": 0.6, "Position X": 0.0, "Position Y": -0.5,
                "Color": CHAR2, "BG Color": CLEAR}, "Reporters crowding the table.", opacity=0.9),
          strobe(3, freq=0.35, color=IVORY, opacity=0.35, name="Flashbulbs"),
          text(3, "DEFINITELY NOT", size=1.2, why="Welles at the press conference, 31 October."),
          blank(6, 3), grain(3, opacity=0.1), vu(3, amp=0.04)]
    C += [floor(4, color=CHAR2, amount=5, name="Column Rules"),
          page(2, 4, color=IVORY, opacity=0.9, name="Front Page"),
          blank(3, 4, "The headline is the picture."),
          lamp(4, color=IVORY_DIM, opacity=0.1),
          text(4, "RADIO WAR\nTERRORIZES U.S.", font=GOTH, size=2.0, color=CHAR, align="Center",
               valign="Center", x=0, y=0, why="A front-page headline style, black on newsprint."),
          blank(6, 4), grain(4, opacity=0.12), vu(4, amp=0.02)]
    C += [black(5), clip(2, 5, "Audience Bar", "Lines",
                         {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.02, "Rotation": 90.0,
                          "Position": 0.2, "Color": IVORY},
                         "A single thin bar: about 2% of the radio audience.", opacity=1.0),
          clip(3, 5, "Bergen On NBC", "Lines",
               {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.7, "Rotation": 90.0, "Position": 0.65,
                "Color": GREY_DIM}, "Everyone else was listening to Edgar Bergen on NBC.", opacity=0.8),
          blank(4, 5, "No lamp."),
          text(5, "C.E. HOOPER: ~2%\nOF THE AUDIENCE", size=0.9),
          blank(6, 5), grain(5), vu(5, amp=0.03)]
    C += [black(6), page(2, 6, color=IVORY_DIM, opacity=0.6, name="The Myth"),
          clip(3, 6, "The Record", "Lines",
               {"Fuzzyness": 0.0, "Amount": 12, "Width": 0.01, "Rotation": 0.0, "Position": 0.5,
                "Color": IVORY}, "Ruled columns: what was actually documented.", opacity=0.6),
          blank(4, 6, "No lamp."),
          text(6, "THE PANIC WAS\nPRINTED, NOT\nBROADCAST", size=0.9,
               why="Newspapers manufactured the mass-panic myth to wound radio."),
          blank(6, 6), grain(6), vu(6, amp=0.03)]
    C += [floor(7, amount=40, rot=90.0, name="Rehearsal Rack"),
          dial(2, 7, color=IVORY, rings=30, size=0.6, width=0.01, name="Disc A",
               why="Disc A, filed as next week's rehearsal, with the hum in its grooves."),
          clip(3, 7, "Small Circle", "Rings",
               {"Num Rings": 1, "Size": 0.08, "Spacing": 0.1, "Line Width": 0.03, "Style": "Stroke",
                "Gap": 20.0, "Rotation": 0.0, "Rotation Step": 0.0, "Rotation Alternate": False,
                "Color 1": IVORY, "Color 2": IVORY},
               "Nora draws a small circle on the sleeve without knowing why.", opacity=1.0,
               effects=[xform(x=420, y=-260)], fft={}),
          lamp(7, color=AMBER_DIM, opacity=0.2),
          text(7, "EVERYONE FORGETS\nTHE RECORD DOESN'T", size=0.9),
          blank(6, 7), grain(7), strip(7, why="The grooves become the optical soundtrack strip carrying the theme out.")]
    C += [black(8), page(2, 8, color=IVORY_DIM, opacity=0.5, name="Next Week's Script"),
          underline(3, 8, y=0.5, name="Already Red",
                    why="Next week's script in the briefcase, already red-pencilled."),
          blank(4, 8, "No lamp: the schedule repeats."),
          text(8, "NEXT WEEK", font=HEAD, size=1.6, align="Center", valign="Bottom", x=0, y=460),
          blank(6, 8), grain(8), vu(8, amp=0.02)]
    return {"name": "Morning After", "slug": "morning-after", "theme": "wildcard",
            "world": ("9:00 pm and after: the heavy doors burst open on dark uniforms, the switchboard becomes "
                      "a vast sea of light, flashbulbs at the morning press conference, and the front pages. "
                      "Then the correction the century took to make: about two percent of the audience was "
                      "listening, and the panic was printed, not broadcast. It ends on the disc in the "
                      "rehearsal rack with a small circle on its sleeve, and next week's script already "
                      "red-pencilled - the one other place red is allowed."),
            "palette": [{"role": "bed", "hex": "#121212", "why": "Charcoal."},
                        {"role": "body", "hex": "#e9e1cf", "why": "Newsprint and flashbulbs."},
                        {"role": "figure", "hex": "#262420", "why": "Dark uniforms, the press crowd."},
                        {"role": "light", "hex": "#d9a441", "why": "The switchboard's sea of amber lamps."},
                        {"role": "text", "hex": "#e9e1cf", "why": "Typed; headlines black on ivory."},
                        {"role": "aura", "hex": "#c41e1e", "why": "Red once, on next week's script."}],
            "columns": cols,
            "text_corpus": ["9:00 PM", "THE DOORS OPEN", "A VAST SEA OF LIGHT", "DEFINITELY NOT",
                            "RADIO WAR TERRORIZES U.S.", "~2% OF THE AUDIENCE",
                            "PRINTED, NOT BROADCAST", "EVERYONE FORGETS", "THE RECORD DOESN'T",
                            "NEXT WEEK", "CHASE AND SANBORN HOUR", "OCTOBER 31, 1938"],
            "moments": [
                "Doors: Scene Launch 1 on the last hit of a track; the uniforms' edges shiver on the mids. "
                "Tap STROBE once for the doors.",
                "Headlines to two percent: Scene Launch 4, hold it for a phrase, then UP to Two Percent so the "
                "front page collapses to one thin bar.",
                "The disc: walk UP to column 7, pull every fader but 2, 3 and 8, and let the strip carry the "
                "music out; then UP to Next Week and BLACKOUT on the last beat."],
            "clips": C}


def main():
    decks = [deck1(), deck2(), deck3(), deck4(), deck5()]
    bible = {
        "pack_name": "Studio One",
        "comp_name": "Studio One - War Of The Worlds 1938",
        "tagline": "Everyone forgets. The record doesn't.",
        "decks": [{k: v for k, v in d.items() if k != "clips"} for d in decks],
        "effect_wishlist": [
            {"effect": "Trails", "role": "Bank A: the jar lid's rings, the switchboard's sea of light."},
            {"effect": "Bloom", "role": "Bank A: halation around practical lamps and the heat ray."},
            {"effect": "CRT", "role": "Bank C: a newsreel print."},
            {"effect": "Stop Motion", "role": "Bank C: the foley scrape and the station break."},
            {"effect": "Tunnel", "role": "Bank B: the cylinder's ribs pulled inward."},
            {"effect": "Mirror Quad", "role": "Bank D: nineteen machines multiplied."}],
        "fft_philosophy": (
            "Sound is the whole subject, so the composition listens like the room did. The kick drives only "
            "physical size - the RCA 44-BX diamond, the cylinder's ribs, the heat ray's width, the headlights - "
            "so a hit reads as pressure on the ribbon. Mids drive the board's program line (SCOPE) and the cap "
            "turning; highs only shiver the ribbon and the crowd's edges. Nothing about colour ever reacts: "
            "charcoal, ivory, grey and one amber are fixed, and red appears only where a pencil drew it. Text "
            "never moves. Dead Air, the Silent Mic and the Clock Held are deliberately deaf: the stillness is "
            "the effect."),
        "wildcard_rationale": (
            "Four decks walk the night: the room, the accounts it gave, the visitors who took it, and the city "
            "it described. The fifth is what happened after 9 pm - the doors, the switchboard, the flashbulbs "
            "and the headlines - and the correction: the panic was printed, not broadcast. The broadcast's "
            "88th anniversary is Thursday 30 October 2026.")}
    with open(os.path.join(HERE, "bible.json"), "w", encoding="utf-8") as f:
        json.dump(bible, f, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "decks.json"), "w", encoding="utf-8") as f:
        json.dump({"decks": [{"deck": d["name"], "clips": d["clips"]} for d in decks]},
                  f, indent=1, ensure_ascii=False)
    print("bible: 5 decks; clips:", sum(len(d["clips"]) for d in decks))
    reds = 0
    for d in decks:
        cells = [(c["layer"], c["column"]) for c in d["clips"]]
        missing = [(l, c) for l in range(1, 9) for c in range(1, 9) if (l, c) not in cells]
        dup = sorted({x for x in cells if cells.count(x) > 1})
        if missing or dup:
            print("  %s: missing %s dup %s" % (d["name"], missing, dup))
        reds += sum(1 for c in d["clips"] if RED.lower() in json.dumps(c).lower())
    print("clips carrying red:", reds)


if __name__ == "__main__":
    main()
