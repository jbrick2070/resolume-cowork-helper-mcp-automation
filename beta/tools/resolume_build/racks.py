#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
racks.py - the composition effect rack for the standard instrument: four
banks of latching toggles (30 seats on the APC40's button rows) plus four
always-armed MACRO effects on dashboard links 5-8.

All values are inside the ranges harvested from Avenue 7.28.1. Wet caps
(`wet_max`) stop a bank knob from ever reaching television snow. FFT
bindings sit on inner parameters, never on an effect's dry/wet, so CLEAN
can always reach everything.

rack_for(palette) returns the rack with the pack's own colours poured into
the colour-bearing effects. palette: {role: "#rrggbb"} with at least
"deep", "accent", "accent2", "paper".
"""


def rack_for(palette, theme="nightfield"):
    deep = palette.get("deep", "#05070c")
    accent = palette.get("accent", "#ffb03a")
    accent2 = palette.get("accent2", "#4fe3ff")
    paper = palette.get("paper", "#e8eef2")
    alert = palette.get("alert", "#ff3b2f")

    banks = [
        {"label": "COLOUR", "effects": [
            {"label": "TINT", "effect": "Tint",
             "params": {"Black To": deep, "White To": accent}, "wet_max": 0.6},
            {"label": "COLORIZE", "effect": "Colorize",
             "params": {"Color": accent2, "Contrast": 0.45,
                        "GreysTolerance": 0.3}, "wet_max": 0.6},
            {"label": "DRIFT", "effect": "Hue Rotate",
             "params": {"Hue Scale": 1.0, "Sat. Scale": 0.5},
             "fft": {"Hue Rotate": {"band": "low", "gain": 9.0,
                                    "release": 1200, "floor": 0.0,
                                    "ceiling": 0.08}}},
            {"label": "VIBRANCE", "effect": "Vibrance",
             "params": {"Vibrance": 0.6}},
            {"label": "POSTERIZE", "effect": "Posterize",
             "params": {"Posterize": 0.35}, "wet_max": 0.7},
            {"label": "NEGATIVE", "effect": "Invert RGB", "params": {}},
            {"label": "LEVELS", "effect": "Levels",
             "params": {"Base": 0.56, "Midpoint": 0.5, "Ratio": 0.5}},
            {"label": "THRESHOLD", "effect": "Threshold",
             "params": {"Threshold": 0.45, "Smoothness": 0.08,
                        "Color 1": accent, "Color 2": deep,
                        "Alpha": "Original"}, "wet_max": 0.8},
        ]},
        {"label": "TEXTURE", "effects": [
            {"label": "CRT", "effect": "CRT",
             "params": {"Columns": 640.0, "Rows": 240.0, "Shift": 100.0,
                        "Vignette": 24.0, "Fisheye": 6.0, "Spread": 55.0,
                        "Brightness": 52.0, "Bloom Amount": 40.0}},
            {"label": "GRAIN", "effect": "Static", "params": {"Mode": "Grayscale"},
             "wet_max": 0.15},
            {"label": "DITHER", "effect": "Dither", "params": {"Mode": "4x"},
             "wet_max": 0.6},
            {"label": "DOT SCREEN", "effect": "Dot Screen",
             "params": {"Saturation": 0.5, "Scale": 0.5}, "wet_max": 0.4},
            {"label": "HATCHED", "effect": "Hatched",
             "params": {"Density": 5.0, "Levels": 5.0, "Color1": paper,
                        "Color2": deep}, "wet_max": 0.5},
            {"label": "ACUARELA", "effect": "Acuarela",
             "params": {"Strength": 0.35, "Detail": 4.0}, "wet_max": 0.6},
            {"label": "GOUACHE", "effect": "Kuwahara", "params": {"Radius": 6.0},
             "wet_max": 0.6},
            {"label": "RASTER", "effect": "Raster",
             "params": {"Modulo X": 2.0, "Modulo Y": 2.0}, "wet_max": 0.5},
        ]},
        {"label": "SPACE", "effects": [
            {"label": "KALEIDO", "effect": "Kaleidoscope",
             "params": {"Angles": 0.33, "Zoom": 0.5}},
            {"label": "MIRROR QUAD", "effect": "Mirror Quad", "params": {}},
            {"label": "TUNNEL", "effect": "Tunnel",
             "params": {"Speed": 0.5, "Twist": 0.5, "Rotation": 0.5}},
            {"label": "ZOOM", "effect": "Infinite Zoom",
             "params": {"Zoom": 0.05, "Range": 3.0, "Num Slices": 10.0,
                        "Alpha": 0.5}, "wet_max": 0.7},
            {"label": "RADIAL CLONE", "effect": "Radial Cloner",
             "params": {"Clones": 8.0, "Start Radius": 0.3,
                        "Start Scale": 30.0, "End Radius": 0.9,
                        "End Scale": 60.0, "End Rotation": 360.0}},
            {"label": "GRID CLONE", "effect": "Grid Cloner",
             "params": {"Columns": 3.0, "Rows": 3.0, "Input Scale": 30.0,
                        "Width": 1.2, "Height": 0.7, "Background": "#00000000"}},
            {"label": "WARPSPEED", "effect": "WarpSpeed",
             "params": {"Vignette": 0.2, "Fade": 0.5, "Scale": 0.5}},
            {"label": "SPHERE", "effect": "Sphere",
             "params": {"Size": 0.4, "Resolution": 0.6, "Extrusion": 0.1,
                        "ColorMode": "Multiply", "ColorValue": paper},
             "wet_max": 0.8},
        ]},
        {"label": "FRACTURE", "effects": [
            {"label": "TEAR", "effect": "Shift Glitch",
             "params": {"Frequency": 0.15, "Vertical": 0.1,
                        "Horizontal": 0.3, "Size": 0.06}},
            {"label": "TWITCH", "effect": "Twitch",
             "params": {"Global Twitch": 0.32, "Max Pos Y": 0.05,
                        "Pos Frequency": 0.2, "Max RGB Shift": 0.1,
                        "RGB Frequency": 0.2}},
            {"label": "EDGE", "effect": "Edge Detection",
             "params": {"Use Color": True, "Color": accent2,
                        "Multiplier": 0.25}, "wet_max": 0.75},
            {"label": "FACET", "effect": "Triangulate",
             "params": {"Scale": 0.125, "Levels": 4.0}, "wet_max": 0.55},
            {"label": "STROBE", "effect": "Strobe",
             "params": {"Frequency": 0.3, "Fade": True, "Color": paper},
             "wet_max": 0.6},
            {"label": "STUTTER", "effect": "Stop Motion",
             "params": {"Frequency": 0.5}},
        ]},
    ]

    macros = [
        {"label": "GLOW", "effect": "Bloom",
         "params": {"Threshold": 0.62, "Size": 0.3, "Iterations": 2.0},
         "fft": {"Amount": {"band": "mid", "gain": 9.0, "release": 700,
                            "floor": 0.3, "ceiling": 0.75}}},
        {"label": "ECHO", "effect": "Trails",
         "params": {"Mode": "Lighten"},
         "fft": {"Feedback": {"band": "low", "gain": 9.0, "release": 900,
                              "floor": 0.4, "ceiling": 0.78}}},
        {"label": "FRINGE", "effect": "Shift RGB",
         "params": {"Mode": "Shift X", "R": 0.3, "B": -0.3},
         "fft": {"Distance": {"band": "high", "gain": 10.0, "release": 400,
                              "floor": 0.01, "ceiling": 0.08}}},
        {"label": "VOID", "effect": "Vignette",
         "params": {"Roundness": 0.4, "Size": 0.5, "Softness": 0.8}},
    ]
    if theme == "arachne":
        banks[2]["effects"][5] = {
            "label": "SILK CLONE", "effect": "Linear Cloner",
            "params": {"Clones": 12.0, "Tails": 3.0, "Start Scale": 40.0,
                       "End Scale": 10.0, "Distortion": 30.0}}
        banks[3]["effects"][3] = {
            "label": "WEB MASK", "effect": "Shape Mask",
            "params": {"Shape": "Octagon", "Feather": 40.0, "Scale": 80.0},
            "wet_max": 0.8}
        macros[3] = {"label": "SILK", "effect": "Strokes",
                     "params": {"Amount": 1400.0, "Size": 0.12,
                                "Variation": 0.3, "Swirl": 0.2, "Flow": 0.2,
                                "Feedback": 0.6},
                     "fft": {"Size": {"band": "high", "gain": 9.0,
                                      "release": 400, "floor": 0.08,
                                      "ceiling": 0.22}}}
    return {"banks": banks, "macros": macros,
            "fft_anchor": {"low": ("Trails", "Feedback"),
                           "mid": ("Bloom", "Amount"),
                           "high": ("ShiftRGB", "Distance")}}
