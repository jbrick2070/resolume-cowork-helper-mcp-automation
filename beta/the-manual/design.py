#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py - THE MANUAL, a stock-only Avenue 7.28.1 instrument about Avenue
itself: its vocabulary, its clip menus, its parameter animation, its 62 blend
modes and this rig's own Preferences. Every term is a real one, taken from
resolume.com/support (Clips, Layers, Composition, Parameter Animation,
Envelopes, Dashboard, BPM, Autopilot, Blend Modes, Preferences) or from the
rig harvest (22 sources, 115 effects, 1,094 parameters, 62 blend modes).

The visual grammar is the interface's: charcoal panels, grid lines, light-grey
labels, Resolume blue for selection, green for a playing clip, one amber for
BPM and warnings. Segoe UI for labels, Consolas for values.

    python packs/the-manual/design.py      -> bible.json + decks.json
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "lh", os.path.join(HERE, "..", "library-hand", "design.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
clip, fft, xform = L.clip, L.fft, L.xform

PANEL = "#1e1f24ff"
PANEL2 = "#2a2b33ff"
LABEL = "#cfd0d6ff"
LABEL_DIM = "#cfd0d666"
BLUE = "#4a8fe7ff"
BLUE_DIM = "#4a8fe766"
GREEN = "#6fcf6fff"
GREEN_DIM = "#6fcf6f66"
AMBER = "#f0a030ff"
CLEAR = "#00000000"

UI = "Segoe UI"
VAL = "Consolas"
BIG = "Bahnschrift"


# ---------------------------------------------------------------- helpers
def panel(col, why="The interface's charcoal panel."):
    return clip(1, col, "Panel", "Solid Color", {"Color": PANEL}, why)


def grid(col, nx=8, ny=5, name="Clip Grid",
         why="The deck's clip grid: columns across, layers down."):
    return clip(1, col, name, "Checkered",
                {"Num X": nx, "Num Y": ny, "Color 1": PANEL, "Color 2": PANEL2}, why)


def ruling(col, amount=12, rot=0.0, color=PANEL2, layer=1, name="Panel Rows", opacity=1.0,
           why="Rows of a panel: one parameter per line."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": 0.012, "Rotation": rot,
                 "Position": 0.5, "Color": color}, why, opacity=opacity)


def vgrid(col, amount=16, color=PANEL2, opacity=1.0, name="Grid Columns"):
    return clip(7, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": 0.01, "Rotation": 90.0,
                 "Position": 0.5, "Color": color}, "The grid's columns.", opacity=opacity)


def selection(layer, col, color=BLUE, size=0.5, name="Selection", opacity=0.9, effects=None,
              fft_=None, why="The blue selection outline around the chosen thing."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": 1, "Size": size, "Spacing": 0.1, "Line Width": 0.02,
                 "Style": "Stroke", "Gap": 0.0, "Rotation": 0.0, "Rotation Step": 0.0,
                 "Rotation Alternate": False, "Color 1": color, "Color 2": color},
                why, opacity=opacity, effects=effects,
                fft=fft_ if fft_ is not None else fft("Line Width", "low", 0.02, 0.05, 8.0, 400))


def knob(layer, col, color=LABEL, size=0.3, name="Dial", rings=1, effects=None,
         why="A dashboard dial."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": rings, "Size": size, "Spacing": 0.15, "Line Width": 0.04,
                 "Style": "Stroke", "Gap": 90.0, "Rotation": 135.0, "Rotation Step": 0.0,
                 "Rotation Alternate": False, "Color 1": color, "Color 2": color},
                why, opacity=0.9, effects=effects,
                fft=fft("Gap", "mid", 20.0, 270.0, 10.0, 350))


def slider(layer, col, color=BLUE, position=0.5, rot=90.0, width=0.03, name="Slider",
           fft_=None, why="A fader: one line whose position is the value."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": 1, "Width": width, "Rotation": rot,
                 "Position": position, "Color": color}, why,
                fft=fft_ if fft_ is not None else fft("Position", "low", position, min(1.0, position + 0.25), 9.0, 400))


def playhead(layer, col, color=GREEN, name="Playhead",
             why="A green sweep along the timeline (Resolume's own pointer is blue)."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.012, "Rotation": 90.0,
                 "Position": 0.3, "Color": color}, why,
                fft=fft("Position", "mid", 0.1, 0.9, 7.0, 900))


def playing(layer, col, color=GREEN, name="Playing Clip", nx=8, ny=5,
            why="One cell lit green: the clip that is playing."):
    return clip(layer, col, name, "Shaper",
                {"Scale": 0.16, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                 "Color": color, "Outline": 0.0, "Outline Color": color}, why, opacity=0.85,
                effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 62.0,
                                                           "Position X": -480.0, "Position Y": 150.0}}],
                fft=fft("Scale", "low", 0.16, 0.2, 8.0, 300))


def cog(layer, col, color=LABEL_DIM, name="Cogwheel", size=0.22,
        why="The grey cogwheel beside a parameter name: the animation menu."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": 2, "Size": size, "Spacing": 0.5, "Line Width": 0.06,
                 "Style": "Stroke", "Gap": 20.0, "Rotation": 0.0, "Rotation Step": 22.5,
                 "Rotation Alternate": True, "Color 1": color, "Color 2": color}, why,
                opacity=0.9, fft=fft("Rotation", "low", 0.0, 45.0, 8.0, 500))


def spectrum(layer, col, color=BLUE, name="FFT Spectrum",
             why="The spectrum display under an FFT-driven parameter."):
    return clip(layer, col, name, "Line Scape",
                {"Tilt": 0.0, "Direction": 0.0, "Position Y": 2.0, "Speed": 0.5, "Height": 8.0,
                 "Jagginess": 0.8, "Wobble": 0.2, "Attenuation": 40.0, "Line Width": 0.4,
                 "Fuzzyness": 0.0, "Color": color, "Show Knots": False}, why, opacity=0.85,
                fft=fft("Height", "mid", 4.0, 20.0, 10.0, 250))


def envelope(layer, col, color=BLUE, waves=1, name="Envelope Curve", amp=0.3,
             why="An envelope curve between keyframes."):
    return clip(layer, col, name, "Sine Wave",
                {"Waves": waves, "Mode": "Line", "Line Width": 0.02, "Fuzzyness": 0.0,
                 "Direction": "Horizontal", "Mirror": False, "Frequency": 0.0, "Main Speed": 1.0,
                 "Modulator": 0.0, "Modulation Depth": 0.0, "Modulator Speed": 1.0,
                 "Amplitude": amp, "Position": 0.5, "Color": color, "BG Color": CLEAR}, why,
                opacity=0.9, fft=fft("Amplitude", "low", amp, min(1.0, amp + 0.3), 9.0, 400))


def glow(col, color=BLUE_DIM, opacity=0.14, layer=4, name="Highlight",
         why="A soft highlight on the selected panel."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": color, "Color 2": CLEAR,
                 "Mode": "Smooth", "Dither": 0.0, "Type": "Radial"}, why, opacity=opacity)


def wash(col, color, kind="Vertical", opacity=0.08, layer=6, name="Wash"):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": CLEAR, "Color 2": color,
                 "Mode": "Smooth", "Dither": 0.0, "Type": kind}, "A tone.", opacity=opacity)


def pulse(col, freq=0.1, color=GREEN, opacity=0.15, layer=4, name="Beat Pulse",
          why="The BPM panel's beat indicator: a blue square stepping round a square, one corner per beat, outlined every 16 beats."):
    return clip(layer, col, name, "Stroboscope",
                {"Frequency": freq, "Fade": True, "Color 1": color, "Color 2": CLEAR}, why,
                opacity=opacity)


def blank(layer, col, why="Nothing by design."):
    return clip(layer, col, "Blank", "Blank", {"Black BG": False}, why)


def noise(col, opacity=0.03, name="Dither"):
    return clip(7, col, name, "Static", {"Mode": "Grayscale"}, "A whisper of dither.", opacity=opacity)


def label(col, s, color=LABEL, size=0.9, font=UI, align="Left", valign="Bottom", x=-860, y=460,
          name=None, layer=5, animated=False, why="A panel label, exactly as the manual names it."):
    return L.text(col, s, color=color, size=size, font=font, align=align, valign=valign, x=x, y=y,
                  name=name, layer=layer, animated=animated, why=why)


def title(col, s, color=LABEL, size=1.8, name=None, why="A chapter title across the centre."):
    return label(col, s, color=color, size=size, font=BIG, align="Center", valign="Center", x=0, y=0,
                 name=name, animated=True, why=why)


def vu(col, color=GREEN, amp=0.06, name="Output Level"):
    return L.scope(col, color=color, position=0.9, amplitude=amp, name=name,
                   why="The composition's output level along the bottom.")


def tl(col, color=BLUE, amp=0.08, name="Timeline"):
    return L.scope(col, color=color, position=0.9, amplitude=amp, waves=2, speed=3.0, name=name,
                   why="A timeline's animated value along the bottom.")


# ================================================================ DECK 1
# VOCABULARY - Composition > Deck > Group > Layer > Clip > Column; the render order
def deck1():
    C = []
    cols = ["Composition", "Deck", "Layer", "Group", "Clip", "Column", "Source + FX", "Render Order"]
    C += [panel(1), selection(2, 1, size=1.1, name="Comp Frame",
                              why="The whole output framed in blue: the Composition."),
          blank(3, 1, "Nothing inside yet."),
          glow(1, opacity=0.1),
          label(1, "COMPOSITION\n1920 x 1080 - 60 FPS\n8-BIT", font=VAL,
                why="Composition > Settings: Name, Size, FrameRate, Bit Depth."),
          blank(6, 1), noise(1), vu(1)]
    C += [grid(2), selection(2, 2, size=0.9, name="Deck Tab", opacity=0.6,
                             effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 12.0,
                                                                         "Position Y": 470.0}}],
                             why="A deck button along the bottom, under the clip layers: a DJ's record bag."),
          playing(3, 2),
          glow(2, opacity=0.08),
          label(2, "DECK\nA COLLECTION OF CLIPS\nONE ACTIVE AT A TIME"),
          blank(6, 2), vgrid(2, amount=8), vu(2)]
    C += [grid(3), ruling(3, amount=8, color=BLUE_DIM, layer=2, name="Layer Strips", opacity=0.6,
                          why="Eight layer strips: X, B, S and the V / A / M faders."),
          slider(3, 3, color=LABEL, position=0.14, rot=0.0, name="Layer Row",
                 fft_=fft("Width", "low", 0.03, 0.08, 8.0, 400),
                 why="One layer row lit: layer 1, the bottom."),
          glow(3, opacity=0.08),
          label(3, "LAYER\nX - B - S - V - A - M\nBLEND: ADD (DEFAULT)"),
          blank(6, 3), vgrid(3, amount=8), vu(3)]
    C += [grid(4), selection(2, 4, size=0.8, name="Group Bracket",
                             effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 44.0}}],
                             why="A bracket round three layers: a Group (Arena only), with its own blend, opacity and effects."),
          blank(3, 4, "The bracket is the figure."),
          glow(4, opacity=0.1),
          label(4, "GROUP (ARENA ONLY)\nLAYERS IN A CONTAINER\nOWN BLEND - OWN FX"),
          blank(6, 4), vgrid(4, amount=8), vu(4)]
    C += [grid(5), playing(2, 5, name="Clip Thumbnail"),
          selection(3, 5, size=0.3, name="Clip Selected",
                    effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 62.0,
                                                                "Position X": -480.0, "Position Y": 150.0}}],
                    why="Click the thumbnail to trigger; click the name handle to select without triggering."),
          glow(5, color=GREEN_DIM, opacity=0.1),
          label(5, "CLIP\nTHE NUTS AND BOLTS\nTHUMBNAIL + NAME HANDLE"),
          blank(6, 5), vgrid(5, amount=8), vu(5)]
    C += [grid(6), slider(2, 6, color=BLUE, position=0.3, rot=90.0, width=0.12, name="Column Lit",
                          fft_={}, why="One column highlighted top to bottom: triggers every layer's clip at once."),
          blank(3, 6, "The column is the figure."),
          pulse(6, freq=0.1, color=BLUE, opacity=0.12, name="Column Flash", why="The column lighting as it triggers."),
          label(6, "COLUMN\nTRIGGERS EVERY LAYER\nBEAT SNAP: 1 BAR"),
          blank(6, 6), vgrid(6, amount=8), vu(6)]
    C += [panel(7), knob(2, 7, color=LABEL, size=0.26, name="Source", effects=[xform(x=-500)],
                         why="Source: the content generator."),
          knob(3, 7, color=BLUE, size=0.26, name="Effects", effects=[xform(x=500)],
               why="Effects: pixel processors, after the permanent Transform."),
          glow(7, opacity=0.1),
          label(7, "CLIP = SOURCE\n+ TRANSFORM\n+ EFFECTS"),
          blank(6, 7), noise(7), vu(7)]
    C += [panel(8), ruling(8, amount=7, color=LABEL_DIM, layer=2, name="Pipeline Rows", opacity=0.7),
          playhead(3, 8, color=GREEN, name="Render Pass"),
          glow(8, opacity=0.08),
          label(8, "SOURCE > CLIP FX > LAYER\n> GROUP > COMP FX\n> OUTPUT", font=VAL, size=0.8),
          blank(6, 8), noise(8), vu(8)]
    return {"name": "Vocabulary", "slug": "vocabulary", "theme": "manual",
            "world": ("Basic Vocabulary, drawn: the composition framed in blue, the deck as a button under the grid, the "
                      "layer strips with X B S and V A M, a group bracket, a clip's green thumbnail and "
                      "its name handle, a column lit top to bottom, and the render order from source to "
                      "output. Charcoal panels, grid lines, light-grey labels, Resolume blue for whatever "
                      "is selected and green for whatever is playing."),
            "palette": [{"role": "bed", "hex": "#1e1f24", "why": "The panel charcoal."},
                        {"role": "body", "hex": "#4a8fe7", "why": "Selection blue."},
                        {"role": "figure", "hex": "#6fcf6f", "why": "Playing green."},
                        {"role": "light", "hex": "#4a8fe7", "why": "Blue highlights."},
                        {"role": "text", "hex": "#cfd0d6", "why": "Labels in Segoe UI, values in Consolas."},
                        {"role": "aura", "hex": "#2a2b33", "why": "Grid grey."}],
            "columns": cols,
            "text_corpus": ["COMPOSITION", "DECK", "LAYER", "GROUP", "CLIP", "COLUMN",
                            "SOURCE + TRANSFORM + EFFECTS", "1920 x 1080 - 60 FPS", "X - B - S",
                            "V - A - M", "NAME HANDLE", "RENDER ORDER"],
            "moments": [
                "Hierarchy: walk UP from Composition to Column one per bar with nothing lit; the blue frame "
                "shrinks to a tab, a strip, a bracket, a cell, a column.",
                "Clip: on column 5 tap the row-2 BODY pad on the beat so the green thumbnail retriggers.",
                "Render order: column 8, Device knob 6 (ECHO) at a third so the green pass leaves a "
                "trace down the pipeline rows."],
            "clips": C}


# ================================================================ DECK 2
# THE CLIP - trigger style, beat snap, target, resize, fader start, autopilot, transition
def deck2():
    C = []
    cols = ["Trigger Style", "Beat Snap", "Clip Target", "Resize",
            "Fader Start", "Ignore Column", "Auto Pilot", "Transition"]
    C += [panel(1), playing(2, 1), selection(3, 1, size=0.3,
                                             effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 62.0,
                                                                                         "Position X": -480.0, "Position Y": 150.0}}]),
          pulse(1, freq=0.3, color=GREEN, opacity=0.18, name="Piano Press",
                why="Piano: the clip plays while the key is held."),
          label(1, "TRIGGER STYLE\nNORMAL - TOGGLE - PIANO", why="Right-click a clip > Trigger style."),
          blank(6, 1), vgrid(1, amount=8), vu(1)]
    C += [grid(2, nx=4, ny=1, name="Four Bars"), slider(2, 2, color=BLUE, position=0.25, width=0.02,
                                                       name="1 Bar", fft_={}),
          playhead(3, 2, color=GREEN, name="Waiting"),
          pulse(2, freq=0.1, color=AMBER, opacity=0.12, name="Metronome"),
          label(2, "BEAT SNAP\n1/4 BAR - 1 BAR\n2 BARS - 4 BARS - 8 BARS"),
          blank(6, 2), vgrid(2, amount=16, opacity=0.6), vu(2)]
    C += [grid(3), ruling(3, amount=8, color=BLUE_DIM, layer=2, name="Layer Strips", opacity=0.5),
          slider(3, 3, color=GREEN, position=0.5, rot=0.0, name="Free Layer",
                 fft_=fft("Position", "mid", 0.2, 0.8, 7.0, 800),
                 why="Free Layer: the clip lands on whichever layer is empty."),
          glow(3, color=GREEN_DIM, opacity=0.08),
          label(3, "CLIP TARGET\nOWN - ACTIVE - FREE\nCOMPOSITION DETERMINED"),
          blank(6, 3), vgrid(3, amount=8), vu(3)]
    C += [panel(4), selection(2, 4, size=0.9, color=LABEL_DIM, name="Comp Bounds", fft_={}),
          selection(3, 4, size=0.6, color=BLUE, name="Clip Bounds",
                    effects=[{"effect": "Transform", "params": {"Scale W": 130.0, "Scale H": 100.0}}],
                    fft_=fft("Size", "low", 0.5, 0.95, 9.0, 500),
                    why="Fill crops, Fit letterboxes, Stretch distorts, Original is pixel size."),
          glow(4, opacity=0.08),
          label(4, "RESIZE\nFILL - FIT - STRETCH\nORIGINAL"),
          blank(6, 4), noise(4), vu(4)]
    C += [panel(5), slider(2, 5, color=BLUE, position=0.2, rot=0.0, width=0.04, name="Opacity Fader",
                           fft_=fft("Position", "low", 0.1, 0.9, 10.0, 600),
                           why="The layer's V fader rising..."),
          playhead(3, 5, color=GREEN, name="Restart",
                   why="...and the clip restarting from the beginning each time."),
          glow(5, color=GREEN_DIM, opacity=0.08),
          label(5, "FADER START\nRESTART ON FADE UP\nCLIP OR LAYER"),
          blank(6, 5), noise(5), vu(5)]
    C += [grid(6), slider(2, 6, color=BLUE_DIM, position=0.3, rot=90.0, width=0.12, name="Column Trigger",
                          fft_={}),
          playing(3, 6, name="Keeps Playing", why="The layer with Ignore Column Trigger keeps its clip."),
          blank(4, 6, "No flash: this layer ignores the column."),
          label(6, "IGNORE COLUMN TRIGGER\nCLIP - LAYER - GROUP\nSCOPE LAYER USES THIS"),
          blank(6, 6), vgrid(6, amount=8), vu(6)]
    C += [grid(7), playing(2, 7), playhead(3, 7, color=BLUE, name="Next Clip",
                                           why="Auto Pilot: next, previous, random (Any / Other / Bag), first, last, specific."),
          glow(7, opacity=0.08),
          label(7, "AUTO PILOT\nNEXT - PREVIOUS - RANDOM\nLOOPS: 1 - DURATION: BEATS"),
          blank(6, 7), vgrid(7, amount=8), vu(7)]
    C += [panel(8), envelope(2, 8, color=BLUE, waves=1, amp=0.25, name="Crossfade",
                             why="Transition mode Alpha: a crossfade over the transition time."),
          slider(3, 8, color=LABEL, position=0.5, rot=90.0, name="Transition Time",
                 fft_=fft("Position", "mid", 0.1, 0.9, 6.0, 1200),
                 why="0 to 10 seconds, millisecond precision in the Layer panel."),
          glow(8, opacity=0.08),
          label(8, "TRANSITION\nCLIP: LAYER DETERMINED\nLAYER: ALPHA - 0-10 S"),
          blank(6, 8), noise(8), tl(8)]
    return {"name": "The Clip", "slug": "the-clip", "theme": "manual",
            "world": ("The Clips chapter, one setting per scene: Trigger Style (Normal, Toggle, Piano), "
                      "Beat Snap (1/4 Bar to 8 Bars), Clip Target (Own, Active, Free "
                      "Layer), Resize (Fill, Fit, Stretch, Original), Fader Start, Ignore Column Trigger "
                      "(the SCOPE layer in every pack uses it), Auto Pilot and the Transition (Layer Determined at the clip, Alpha at the layer). "
                      "Every option name is the manual's."),
            "palette": [{"role": "bed", "hex": "#1e1f24", "why": "Panel."},
                        {"role": "body", "hex": "#6fcf6f", "why": "The playing clip."},
                        {"role": "figure", "hex": "#4a8fe7", "why": "The control being explained."},
                        {"role": "light", "hex": "#f0a030", "why": "The metronome's amber."},
                        {"role": "text", "hex": "#cfd0d6", "why": "Option names, exact."},
                        {"role": "aura", "hex": "#2a2b33", "why": "Grid grey."}],
            "columns": cols,
            "text_corpus": ["NORMAL - TOGGLE - PIANO", "BEAT SNAP", "1 BAR", "OWN LAYER", "FREE LAYER",
                            "FILL - FIT - STRETCH", "FADER START", "IGNORE COLUMN TRIGGER", "AUTO PILOT",
                            "LAYER DETERMINED", "TRANSITION", "ALPHA"],
            "moments": [
                "Piano: Scene Launch 1, right-click the row-2 BODY clip > Trigger style > Piano, then play the pad "
                "like a key - the green cell exists only while you hold it. That is Piano.",
                "Beat snap: Composition > Beat Snap > 1 Bar, then Scene Launch 2 and tap Scene Launch 3 off the "
                "beat; Avenue waits for the bar. Watch the amber metronome.",
                "Fader start: column 5, turn Layer > Fader Start on for layer 3, then ride fader 3 down and up on "
                "the phrase; the green restart line jumps each time."],
            "clips": C}


# ================================================================ DECK 3
# PARAMETERS - the cogwheel menu: Timeline, BPM Sync, FFT L/M/H, Envelope, Dashboard, Clip Position
def deck3():
    C = []
    cols = ["Cogwheel", "Timeline", "BPM Sync", "External FFT",
            "Gain + Fall", "Envelope", "Dashboard", "Clip Position"]
    C += [panel(1), ruling(1, amount=10, color=PANEL2, layer=2, name="Parameter Rows"),
          cog(3, 1),
          glow(1, opacity=0.1),
          label(1, "THE COGWHEEL\nTIMELINE - BPM SYNC\nFFT - ENVELOPE - DASHBOARD",
                why="Click the grey cogwheel next to a parameter name."),
          blank(6, 1), noise(1), vu(1)]
    C += [panel(2), ruling(2, amount=1, color=LABEL_DIM, layer=2, name="Timeline Bar", opacity=0.8),
          playhead(3, 2),
          glow(2, opacity=0.08),
          label(2, "TIMELINE\nIN - OUT - SPEED - DURATION\nLOOP - PING-PONG - ONE-SHOT"),
          blank(6, 2), vgrid(2, amount=16, opacity=0.5), tl(2)]
    C += [grid(3, nx=16, ny=1, name="Sixteen Beats"), slider(2, 3, color=AMBER, position=0.0625, width=0.02,
                                                            name="Beat One", fft_={}),
          playhead(3, 3, color=GREEN, name="Beat Head"),
          pulse(3, freq=0.1, color=AMBER, opacity=0.14, name="Sync Indicator",
                why="The blue square circles a larger square and hits top-left on every first beat."),
          label(3, "BPM SYNC\nTIME IN BEATS - 4 - 8 - 16\nTAP - RESYNC - NUDGE", font=VAL, size=0.8),
          blank(6, 3), vgrid(3, amount=16, opacity=0.5), tl(3, color=AMBER)]
    C += [panel(4), spectrum(2, 4),
          slider(3, 4, color=GREEN, position=0.3, rot=90.0, width=0.015, name="Band In Point",
                 fft_=fft("Position", "high", 0.25, 0.4, 6.0, 400),
                 why="In/out points under the spectrum fine-tune the frequency range."),
          glow(4, color=GREEN_DIM, opacity=0.1),
          label(4, "EXTERNAL FFT\nINPUT: CABLE OUTPUT\nL - M - H", font=VAL, size=0.8,
                why="The audio input device chosen in Preferences > Audio: this rig's VB-Cable."),
          blank(6, 4), noise(4), vu(4, name="FFT Signal")]
    C += [panel(5), knob(2, 5, color=BLUE, size=0.3, name="Gain", effects=[xform(x=-400)]),
          knob(3, 5, color=LABEL, size=0.3, name="Fall", effects=[xform(x=400)],
               why="Fall: how quickly the value drops back from a peak."),
          glow(5, opacity=0.08),
          label(5, "GAIN - FALL\n> LOW TO HIGH  < HIGH TO LOW\n- / + DRIVE SPEED", font=VAL, size=0.8),
          blank(6, 5), noise(5), vu(5, name="Driven Value")]
    C += [panel(6), envelope(2, 6, color=BLUE, waves=2, amp=0.3, name="Elastic Curve"),
          selection(3, 6, size=0.06, color=LABEL, name="Keyframe", effects=[xform(x=-300, y=-120)],
                    fft_={}, why="A keyframe: double-click to add, drag to move, type phase and value."),
          glow(6, opacity=0.08),
          label(6, "ENVELOPE\nQUADRATIC - SINE - CIRCULAR\nEXPONENTIAL - ELASTIC - BOUNCE", size=0.8),
          blank(6, 6), noise(6), tl(6)]
    C += [panel(7), knob(2, 7, color=BLUE, size=0.2, rings=1, name="Dial 1", effects=[xform(x=-600)]),
          knob(3, 7, color=LABEL_DIM, size=0.2, rings=1, name="Dial 2", effects=[xform(x=-200)]),
          glow(7, opacity=0.1),
          label(7, "DASHBOARD\nDRAG A PARAMETER ONTO A DIAL\nIN - OUT - INVERT - DIAL RANGE", size=0.8),
          blank(6, 7), noise(7), vu(7)]
    C += [panel(8), playhead(2, 8, color=GREEN, name="Clip Playhead"),
          envelope(3, 8, color=BLUE, waves=1, amp=0.2, name="Follows Playhead",
                   why="Clip Position: the parameter follows scrubbing, speed, direction and beatloop."),
          glow(8, color=GREEN_DIM, opacity=0.08),
          label(8, "CLIP POSITION\nSYNCED TO THE PLAYHEAD\nCLIPS ONLY"),
          blank(6, 8), noise(8), tl(8, color=GREEN)]
    return {"name": "Parameters", "slug": "parameters", "theme": "manual",
            "world": ("Parameter Animation, the cogwheel's menu: Timeline with in and out points, BPM "
                      "Sync in beats with Tap, Resync and Nudge, External FFT on this rig's CABLE Output "
                      "with L M H bands, Gain and Fall, the Envelope's eight curves, the Dashboard's dials "
                      "with In, Out, Invert and Dial Range, and Clip Position. This is the chapter every "
                      "pack in this repo is built on."),
            "palette": [{"role": "bed", "hex": "#1e1f24", "why": "Panel."},
                        {"role": "body", "hex": "#4a8fe7", "why": "Curves, spectrum, dials."},
                        {"role": "figure", "hex": "#6fcf6f", "why": "Playheads."},
                        {"role": "light", "hex": "#f0a030", "why": "BPM amber."},
                        {"role": "text", "hex": "#cfd0d6", "why": "Menu items, exact."},
                        {"role": "aura", "hex": "#2a2b33", "why": "Grid grey."}],
            "columns": cols,
            "text_corpus": ["TIMELINE", "BPM SYNC", "EXTERNAL FFT", "COMPOSITION FFT", "L - M - H",
                            "GAIN - FALL", "ENVELOPE", "ELASTIC", "BOUNCE", "DASHBOARD", "CLIP POSITION",
                            "CROSSFADER PHASE"],
            "moments": [
                "FFT: Scene Launch 4 and turn Track knob 3 (MID DEPTH) up until the whole picture blooms on the "
                "mids; the spectrum in column 4 already rides the signal on its own. This scene is the pack "
                "explaining its own reactivity.",
                "Envelope: column 6, Device knob 2 (TEXTURE) at a quarter with GOUACHE lit so the elastic curve smears as it overshoots.",
                "Dashboard: column 7, turn Device knobs 1-4 and watch the dials - they are the real links."],
            "clips": C}


# ================================================================ DECK 4
# BLEND MODES - 62 on this rig, grouped as the manual groups them
def deck4():
    C = []
    cols = ["Alpha", "Add + Screen", "Multiply + Burn", "Overlay",
            "Difference", "Luma Key", "50 Mask", "Transitions"]

    def two(col, c1, c2, name_a="Layer A", name_b="Layer B", why_b="Layer B over A."):
        return [clip(2, col, name_a, "Shaper",
                     {"Scale": 0.5, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                      "Color": c1, "Outline": 0.0, "Outline Color": c1}, "Layer A: a disc, left.",
                     opacity=0.9, effects=[xform(x=-180)], fft=fft("Scale", "low", 0.5, 0.6, 8.0, 400)),
                clip(3, col, name_b, "Shaper",
                     {"Scale": 0.5, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                      "Color": c2, "Outline": 0.0, "Outline Color": c2}, why_b,
                     opacity=0.9, effects=[xform(x=180)], fft=fft("Scale", "mid", 0.5, 0.6, 8.0, 400))]

    C += [panel(1)] + two(1, LABEL, BLUE, why_b="Alpha: mixed by opacity; transparent pixels show what is below.") + [
          glow(1, opacity=0.08),
          label(1, "ALPHA (DEFAULT TRANSITION)\nCUT: HARD SWITCH"),
          blank(6, 1), noise(1), vu(1)]
    C += [panel(2)] + two(2, BLUE, GREEN, why_b="Add sums the channels; Screen is softer and glows.") + [
          glow(2, color=GREEN_DIM, opacity=0.12),
          label(2, "LIGHTEN MODES\nLIGHTEN - SCREEN - DODGE\n(ADD IS COMPARATIVE)"),
          wash(2, GREEN_DIM, kind="Radial", opacity=0.06), noise(2), vu(2)]
    C += [panel(3)] + two(3, LABEL, PANEL2, why_b="Multiply darkens; Burn darkens hard and raises contrast.") + [
          blank(4, 3, "No highlight: darken modes."),
          label(3, "DARKEN MODES\nDARKEN - MULTIPLY - BURN"),
          blank(6, 3), noise(3), vu(3)]
    C += [panel(4)] + two(4, BLUE, LABEL, why_b="Overlay: Multiply below 50% grey, Screen above.") + [
          glow(4, opacity=0.08),
          label(4, "CONTRAST MODES\nOVERLAY - SOFT LIGHT\nHARD LIGHT"),
          blank(6, 4), noise(4), vu(4)]
    C += [panel(5)] + two(5, BLUE, BLUE, why_b="Difference: identical pixels turn black.") + [
          glow(5, opacity=0.06),
          label(5, "COMPARATIVE MODES\nADD (LAYER DEFAULT)\nSUBTRACT - DIFFERENCE\nDIFFERENCE I - EXCLUSION", size=0.75),
          blank(6, 5), noise(5), vu(5)]
    C += [grid(6, nx=6, ny=4, name="Luma Checker")] + two(6, LABEL, PANEL, why_b="Luma Key: bright stays, dark goes transparent.") + [
          glow(6, opacity=0.06),
          label(6, "COMPOSITE MODES\nLUMA KEY - LUMA KEY I\nLUMA IS ALPHA - DISPLACE", size=0.8),
          blank(6, 6), noise(6), vu(6)]
    C += [panel(7), clip(2, 7, "Grey Ramp", "Gradient",
                         {"Method": "2 Colors", "Color 1": PANEL, "Color 2": LABEL, "Mode": "Smooth",
                          "Dither": 0.0, "Type": "Horizontal"}, "A grey ramp: the mask source."),
          clip(3, 7, "Masked Disc", "Shaper",
               {"Scale": 0.5, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                "Color": BLUE, "Outline": 0.0, "Outline Color": BLUE},
               "50 Mask: white fully visible, black transparent, grey partial.", opacity=0.9,
               fft=fft("Scale", "low", 0.5, 0.62, 8.0, 400)),
          glow(7, opacity=0.06),
          label(7, "50 BLENDS\n50 MASK - 50 ADD - 50 MULTIPLY\n...TEN OF THEM", size=0.8),
          blank(6, 7), noise(7), vu(7)]
    C += [panel(8), selection(2, 8, size=0.9, color=BLUE, name="Wipe Ellipse",
                              fft_=fft("Size", "mid", 0.2, 1.2, 9.0, 600),
                              why="Wipe Ellipse: an elliptical wipe revealing the next layer."),
          slider(3, 8, color=LABEL, position=0.5, rot=0.0, width=0.5, name="Push Up",
                 fft_=fft("Position", "low", 0.0, 1.0, 8.0, 900),
                 why="Push Up / Down / Left / Right."),
          glow(8, opacity=0.08),
          label(8, "TRANSITION MODES\nWIPE ELLIPSE - DISSOLVE\nPUSH - ZOOM - TO BLACK", size=0.8),
          blank(6, 8), noise(8), tl(8)]
    return {"name": "Blend Modes", "slug": "blend-modes", "theme": "manual",
            "world": ("Sixty-two blend modes harvested from this rig, grouped as the Blend Modes chapter "
                      "groups them: General, Darken, Lighten, Contrast, Comparative, Composite and the "
                      "Transitions, plus the ten '50' modes the harvest lists (the chapter documents only 50 Mask, under Composite). Each scene is two discs, A and B, overlapping, in "
                      "the colours the mode would make of them. The pack itself uses Add on most layers, "
                      "Screen on FIGURE, Alpha on TEXT and Overlay on AURA."),
            "palette": [{"role": "bed", "hex": "#1e1f24", "why": "Panel."},
                        {"role": "body", "hex": "#cfd0d6", "why": "Layer A."},
                        {"role": "figure", "hex": "#4a8fe7", "why": "Layer B."},
                        {"role": "light", "hex": "#6fcf6f", "why": "Lighten modes glow green."},
                        {"role": "text", "hex": "#cfd0d6", "why": "Mode names, exact."},
                        {"role": "aura", "hex": "#2a2b33", "why": "Grid grey."}],
            "columns": cols,
            "text_corpus": ["ALPHA", "ADD", "SCREEN", "MULTIPLY", "OVERLAY", "DIFFERENCE", "LUMA KEY",
                            "LUMA IS ALPHA", "50 MASK", "WIPE ELLIPSE", "PUSH UP", "62 BLEND MODES"],
            "moments": [
                "A over B: on any column, ride faders 2 and 3 against each other; the discs overlap at centre.",
                "Lighten: Scene Launch 2 with Device knob 5 (GLOW) up so Screen actually screens.",
                "Transitions: column 8, Track knob 8 (TIME) past three-quarters so the wipe and push race."],
            "clips": C}


# ================================================================ DECK 5
# THIS RIG - Preferences and Nerds as they are set on this machine (wildcard)
def deck5():
    C = []
    cols = ["Audio In", "MIDI", "Webserver", "OSC",
            "Video", "Defaults", "The Harvest", "Shortcut Mode"]
    C += [panel(1), spectrum(2, 1, color=GREEN, name="Input Meter"),
          selection(3, 1, size=0.4, color=GREEN, name="Device Row",
                    effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 18.0, "Position Y": 60.0}}],
                    fft_={}, why="Preferences > Audio > Audio Input Device: CABLE Output (VB-Audio Virtual Cable)."),
          glow(1, color=GREEN_DIM, opacity=0.1),
          label(1, "PREFERENCES > AUDIO\nINPUT: CABLE OUTPUT\n(VB-AUDIO) - FFT GAIN", font=VAL, size=0.8),
          blank(6, 1), noise(1), vu(1, name="External FFT")]
    C += [grid(2, nx=8, ny=5, name="APC Pads"), playing(2, 2, color=BLUE, name="Pad Lit"),
          selection(3, 2, size=0.9, color=LABEL_DIM, name="Controller",
                    effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 70.0}}], fft_={}),
          pulse(2, freq=0.2, color=BLUE, opacity=0.1, name="MIDI In"),
          label(2, "PREFERENCES > MIDI\nAPC40 MKII: IN + OUT\nOUTPUT DRIVES THE LEDS", font=VAL, size=0.8),
          blank(6, 2), vgrid(2, amount=8), vu(2)]
    C += [panel(3), ruling(3, amount=14, color=PANEL2, layer=2, name="JSON Rows"),
          playhead(3, 3, color=GREEN, name="Request",
                   why="GET /api/v1/composition: how every pack here was read back."),
          glow(3, opacity=0.08),
          label(3, "PREFERENCES > WEBSERVER\nREST API: ON - PORT 8080\n/api/v1/composition", font=VAL, size=0.8),
          blank(6, 3), noise(3), vu(3)]
    C += [panel(4), slider(2, 4, color=BLUE, position=0.4, rot=0.0, name="OSC In 7000", fft_={}),
          slider(3, 4, color=LABEL, position=0.6, rot=0.0, name="OSC Out 7001", fft_={}),
          pulse(4, freq=0.5, color=BLUE, opacity=0.08, name="Message"),
          label(4, "PREFERENCES > OSC\nIN 7000 - OUT 7001\n/composition/layers/1\n/clips/1/connect", font=VAL, size=0.7),
          blank(6, 4), noise(4), vu(4)]
    C += [panel(5), selection(2, 5, size=0.8, color=LABEL_DIM, name="Texture", fft_={}),
          clip(3, 5, "DMA On", "Checkered", {"Num X": 24, "Num Y": 14, "Color 1": PANEL, "Color 2": BLUE_DIM},
               "DMA Textures: this rig sits on Autodetect; the manual recommends Force ON.", opacity=0.6),
          glow(5, opacity=0.06),
          label(5, "PREFERENCES > VIDEO\nDMA: AUTODETECT\n(MANUAL: FORCE ON)", font=VAL, size=0.8),
          blank(6, 5), noise(5), vu(5)]
    C += [panel(6), ruling(6, amount=6, color=PANEL2, layer=2, name="Default Rows"),
          slider(3, 6, color=AMBER, position=0.5, rot=90.0, name="Tempo Nudge Range", fft_={}),
          glow(6, opacity=0.06),
          label(6, "PREFERENCES > DEFAULTS\nBLEND: ADD - TRANSPORT:\nTIMELINE - PLAY MODE: LOOP", font=VAL, size=0.8),
          blank(6, 6), noise(6), vu(6)]
    C += [grid(7, nx=22, ny=5, name="Source Grid"), playing(2, 7, color=BLUE, name="Harvest Cell"),
          selection(3, 7, size=0.9, color=GREEN, name="Library",
                    effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 70.0}}],
                    fft_=fft("Line Width", "low", 0.02, 0.05, 8.0, 400)),
          glow(7, color=GREEN_DIM, opacity=0.08),
          label(7, "THE HARVEST - 7.28.1.26535\n22 SOURCES - 115 EFFECTS\n1,094 PARAMS - 62 BLENDS", font=VAL, size=0.8,
                why="What harvest_7281.py read off this running application through REST."),
          blank(6, 7), vgrid(7, amount=22, opacity=0.5), vu(7)]
    C += [clip(1, 8, "Blue Interface", "Solid Color", {"Color": "#1a2a44ff"},
               "Shortcut mode: the interface turns partially blue."),
          selection(2, 8, size=0.5, color=BLUE, name="Mapped Control"),
          cog(3, 8, color=BLUE, name="Shortcut Options",
              why="Toggle, Piano, Range, Value, Mouse: the Shortcuts tab, bottom-right."),
          pulse(8, freq=0.15, color=BLUE, opacity=0.14, name="Learn Flash"),
          title(8, "CTRL - SHIFT - K", color=LABEL, size=2.0,
                why="Shortcuts > Edit Keyboard, or CTRL-SHIFT-K; Escape leaves."),
          wash(8, BLUE_DIM, kind="Radial", opacity=0.1), noise(8), vu(8)]
    return {"name": "This Rig", "slug": "this-rig", "theme": "wildcard",
            "world": ("The Nerds chapter as it is set on this machine: Audio input CABLE Output for the "
                      "External FFT, the APC40 mkII as MIDI in and out so the pads light, the REST API on "
                      "8080 that read every clip of every pack back, OSC on 7000 and 7001, DMA Textures "
                      "on Autodetect (the manual recommends Force ON), the Defaults (Add, Timeline, Loop), "
                      "the harvest itself - 22 sources, 115 "
                      "effects, 1,094 parameters, 62 blend modes off 7.28.1.26535 - and Shortcut mode, "
                      "where the interface turns blue."),
            "palette": [{"role": "bed", "hex": "#1e1f24", "why": "Panel; the last scene turns Shortcut-mode blue."},
                        {"role": "body", "hex": "#4a8fe7", "why": "Blue."},
                        {"role": "figure", "hex": "#6fcf6f", "why": "Green for live signal and the library."},
                        {"role": "light", "hex": "#4a8fe7", "why": "MIDI and OSC message flashes."},
                        {"role": "text", "hex": "#cfd0d6", "why": "Preference names and this rig's values."},
                        {"role": "aura", "hex": "#4a8fe7", "why": "Shortcut-mode blue."}],
            "columns": cols,
            "text_corpus": ["CABLE OUTPUT (VB-AUDIO)", "APC40 MKII: IN + OUT", "REST API: PORT 8080",
                            "OSC 7000 / 7001", "DMA TEXTURES: AUTODETECT", "DEFAULT BLEND: ADD",
                            "22 SOURCES", "115 EFFECTS", "1,094 PARAMETERS", "62 BLEND MODES",
                            "7.28.1.26535", "CTRL-SHIFT-K"],
            "moments": [
                "Audio in: Scene Launch 1 - if the input meter is flat, Preferences > Audio is not set to "
                "CABLE Output. The composition explains its own silence.",
                "MIDI: column 2, press any pad; the pack's LED feedback is what Preferences > MIDI output "
                "is for.",
                "Shortcut mode: UP to column 8 on the last bar, every fader up, and let the interface go "
                "blue; BLACKOUT to leave."],
            "clips": C}


def main():
    decks = [deck1(), deck2(), deck3(), deck4(), deck5()]
    bible = {
        "pack_name": "The Manual",
        "comp_name": "The Manual - Avenue 7.28.1",
        "tagline": "Composition > Deck > Group > Layer > Clip. Click the cogwheel.",
        "decks": [{k: v for k, v in d.items() if k != "clips"} for d in decks],
        "effect_wishlist": [
            {"effect": "Trails", "role": "Bank A: the render pass leaving a trace down the pipeline."},
            {"effect": "Bloom", "role": "Bank A: Screen and Add actually glowing."},
            {"effect": "Wave Warp", "role": "Bank B: the envelope's elastic overshoot."},
            {"effect": "CRT", "role": "Bank C: the manual as a screen."},
            {"effect": "Grid Cloner", "role": "Bank D: a deck's grid of grids."}],
        "fft_philosophy": (
            "This pack is about the thing that makes it move, so the FFT is explicit. Deck 3 draws the "
            "spectrum, the L M H bands, Gain and Fall; Deck 5 draws the input device the whole repo "
            "depends on. Elsewhere the rule is the usual one: lows drive size and width (selection "
            "outlines, the playing cell, discs), mids drive playheads, dials and the spectrum, highs touch "
            "only the band in-point and dither. Colour never reacts: blue is selected, green is playing, "
            "amber is BPM, grey is everything else. Text never moves."),
        "wildcard_rationale": (
            "Four decks are the manual: vocabulary, the clip, parameters, blend modes. The fifth is this "
            "rig's own Preferences as they are set tonight - the audio input, the controller, the REST "
            "port, the harvest counts - so the composition documents the machine that played it.")}
    with open(os.path.join(HERE, "bible.json"), "w", encoding="utf-8") as f:
        json.dump(bible, f, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "decks.json"), "w", encoding="utf-8") as f:
        json.dump({"decks": [{"deck": d["name"], "clips": d["clips"]} for d in decks]},
                  f, indent=1, ensure_ascii=False)
    print("bible: 5 decks; clips:", sum(len(d["clips"]) for d in decks))
    for d in decks:
        cells = [(c["layer"], c["column"]) for c in d["clips"]]
        missing = [(l, c) for l in range(1, 9) for c in range(1, 9) if (l, c) not in cells]
        dup = sorted({x for x in cells if cells.count(x) > 1})
        if missing or dup:
            print("  %s: missing %s dup %s" % (d["name"], missing, dup))


if __name__ == "__main__":
    main()
