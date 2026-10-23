#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py - THE SURFACE, a stock-only Avenue 7.28.1 instrument about the
hardware it is played on: the Akai APC40 mkII, drawn as schematics the way the
SL-1210MKX deck was, and the MIDI wire between it and Resolume. The fifth deck
is an analog video mixer of the same family of knobs and T-bars, the Datavideo
SE-500 (four inputs, T-bar, wipes, PIP, and MIDI control of its own).

Every number is from the Akai APC40 Mk2 Communications Protocol v1.2 as decoded
in apc40mkii-kit/docs/APC40_native_addresses.md, the SysEx in
nisei/rafu-signal/build/apc_mode1_init.py, and the published spec sheet
(424 x 254 x 46 mm, 1.8 kg, USB bus powered).

Palette: matte black chassis, the silkscreen's warm white, pad-RGB green and
amber for the two LED families this repo uses, and one MIDI-DIN red.

    python packs/the-surface/design.py      -> bible.json + decks.json
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

CHASSIS = "#0f1012ff"
CHASSIS2 = "#1f2126ff"
SILK = "#e8e4d8ff"
SILK_DIM = "#e8e4d866"
PADGREEN = "#3ddc84ff"
PADGREEN_DIM = "#3ddc8466"
PADAMBER = "#ffae1aff"
PADAMBER_DIM = "#ffae1a66"
DINRED = "#e03a2fff"
CLEAR = "#00000000"

SILKFONT = "Bahnschrift"
MONO = "Consolas"


# ---------------------------------------------------------------- helpers
def chassis(col, why="Matte black chassis."):
    return clip(1, col, "Chassis", "Solid Color", {"Color": CHASSIS}, why)


def padgrid(col, nx=8, ny=5, c2=CHASSIS2, name="Pad Grid",
            why="The 5x8 clip-launch grid, 40 RGB pads, bottom-left is note 0."):
    return clip(1, col, name, "Checkered",
                {"Num X": nx, "Num Y": ny, "Color 1": CHASSIS, "Color 2": c2}, why)


def silk(col, amount=10, rot=0.0, color=CHASSIS2, layer=1, name="Silkscreen Rules", opacity=1.0,
         why="Silkscreen rules across the panel."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": 0.01, "Rotation": rot,
                 "Position": 0.5, "Color": color}, why, opacity=opacity)


def vrules(col, amount=8, color=CHASSIS2, opacity=1.0, name="Track Columns"):
    return clip(7, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": 0.01, "Rotation": 90.0,
                 "Position": 0.5, "Color": color}, "Eight track columns.", opacity=opacity)


def pad(layer, col, color=PADGREEN, x=-480, y=150, name="Lit Pad", opacity=0.9,
        why="One pad lit in its RGB velocity colour."):
    return clip(layer, col, name, "Shaper",
                {"Scale": 0.16, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                 "Color": color, "Outline": 0.0, "Outline Color": color}, why, opacity=opacity,
                effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 62.0,
                                                           "Position X": float(x), "Position Y": float(y)}}],
                fft=fft("Scale", "low", 0.16, 0.2, 8.0, 300))


def padrow(layer, col, color=PADGREEN, grid=8, y=0.0, name="Pad Row", opacity=0.85,
           why="A row of pads lit together."):
    return clip(layer, col, name, "Metaballs",
                {"Grid": grid, "Blend": "Minimal", "Size": 0.09, "Distance": 0.5, "Radius": 0.1,
                 "Fuzzyness": 0.02, "Speed": 0.0, "Position X": 0.0, "Position Y": y,
                 "Color": color, "BG Color": CLEAR}, why, opacity=opacity,
                fft=fft("Size", "low", 0.08, 0.13, 9.0, 300))


def knob(layer, col, color=SILK, size=0.3, name="Knob", effects=None, ring=False,
         why="A knob with its LED ring."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": 2 if ring else 1, "Size": size, "Spacing": 0.3,
                 "Line Width": 0.05 if ring else 0.03, "Style": "Stroke", "Gap": 90.0,
                 "Rotation": 135.0, "Rotation Step": 0.0, "Rotation Alternate": False,
                 "Color 1": color, "Color 2": PADAMBER if ring else color}, why, opacity=0.9,
                effects=effects, fft=fft("Gap", "mid", 20.0, 270.0, 10.0, 350))


def fader(layer, col, color=SILK, position=0.5, rot=90.0, width=0.03, name="Fader", fft_=None,
          why="A 45 mm fader: a slot and a cap."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": 1, "Width": width, "Rotation": rot,
                 "Position": position, "Color": color}, why,
                fft=fft_ if fft_ is not None else fft("Position", "low", position, min(1.0, position + 0.3), 9.0, 400))


def faders8(layer, col, color=SILK, name="Eight Faders", amount=8,
            why="Eight channel faders, CC7 on channels 1-8."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": 0.02, "Rotation": 90.0,
                 "Position": 0.5, "Color": color}, why, opacity=0.9,
                fft=fft("Width", "low", 0.02, 0.05, 8.0, 400))


def button(layer, col, color=SILK, x=0, y=0, name="Button", lit=False,
           why="A rubber button with a single-colour LED."):
    c = PADGREEN if lit else color
    return clip(layer, col, name, "Shaper",
                {"Scale": 0.08, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                 "Color": c, "Outline": 0.03, "Outline Color": SILK_DIM}, why, opacity=0.9,
                effects=[xform(x=x, y=y)], fft=fft("Scale", "mid", 0.08, 0.1, 7.0, 300))


def midi_wave(layer, col, color=DINRED, waves=8, amp=0.08, position=0.5, name="Serial Bits",
              why="31,250 baud serial: bytes on the wire."):
    return clip(layer, col, name, "Sine Wave",
                {"Waves": waves, "Mode": "Line", "Line Width": 0.015, "Fuzzyness": 0.0,
                 "Direction": "Horizontal", "Mirror": False, "Frequency": 0.0, "Main Speed": 6.0,
                 "Modulator": 0.0, "Modulation Depth": 0.0, "Modulator Speed": 1.0,
                 "Amplitude": amp, "Position": position, "Color": color, "BG Color": CLEAR}, why,
                opacity=0.9, fft=fft("Amplitude", "mid", amp, amp + 0.2, 10.0, 300))


def din(layer, col, color=SILK, name="DIN-5", why="A 5-pin DIN socket: pins 4 and 5 carry the current loop."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": 1, "Size": 0.4, "Spacing": 0.1, "Line Width": 0.03, "Style": "Stroke",
                 "Gap": 0.0, "Rotation": 0.0, "Rotation Step": 0.0, "Rotation Alternate": False,
                 "Color 1": color, "Color 2": color}, why, opacity=0.9,
                fft=fft("Line Width", "low", 0.03, 0.06, 8.0, 400))


def pins5(layer, col, color=DINRED, name="Five Pins",
          why="Five pins in a 180-degree arc."):
    return clip(layer, col, name, "Metaballs",
                {"Grid": 5, "Blend": "Minimal", "Size": 0.05, "Distance": 0.6, "Radius": 0.3,
                 "Fuzzyness": 0.0, "Speed": 0.0, "Position X": 0.0, "Position Y": 0.0,
                 "Color": color, "BG Color": CLEAR}, why, opacity=0.95,
                fft=fft("Size", "high", 0.05, 0.08, 9.0, 200))


def usb(layer, col, color=SILK, name="USB-B",
        why="USB type B: bus powered, no supply needed, class compliant."):
    return clip(layer, col, name, "Geometry Pattern Maker",
                {"Bloom": 0.05, "Bloom Mode": "Add", "Shape Types": "Square", "Shape Rounding": 0.1,
                 "Line Ammount": 8, "Innter Color 1": color, "Inner color 2": CHASSIS2,
                 "Outer Color 1": SILK_DIM, "Outer Color 2": CHASSIS2, "Inner Scale": 0.3,
                 "Outer Scale": 1.2, "Intersect Scale": 0.5}, why, opacity=0.85,
                fft=fft("Inner Scale", "low", 0.28, 0.4, 8.0, 400))


def glow(col, color=PADGREEN_DIM, opacity=0.14, layer=4, name="LED Glow",
         why="LED bleed through the pad's rubber."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": color, "Color 2": CLEAR, "Mode": "Smooth",
                 "Dither": 0.0, "Type": "Radial"}, why, opacity=opacity)


def pulse(col, freq=0.1, color=PADGREEN, opacity=0.14, layer=4, name="Note On",
          why="A note-on flash."):
    return clip(layer, col, name, "Stroboscope",
                {"Frequency": freq, "Fade": True, "Color 1": color, "Color 2": CLEAR}, why, opacity=opacity)


def wash(col, color, kind="Vertical", opacity=0.08, layer=6, name="Wash"):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": CLEAR, "Color 2": color, "Mode": "Smooth",
                 "Dither": 0.0, "Type": kind}, "A tone.", opacity=opacity)


def blank(layer, col, why="Nothing by design."):
    return clip(layer, col, "Blank", "Blank", {"Black BG": False}, why)


def tooth(col, opacity=0.04, name="Matte Tooth"):
    return clip(7, col, name, "Static", {"Mode": "Grayscale"}, "The chassis' matte texture.", opacity=opacity)


def label(col, s, color=SILK, size=0.9, font=MONO, align="Left", valign="Bottom", x=-860, y=460,
          name=None, layer=5, animated=False, why="Silkscreen caption and protocol value."):
    return L.text(col, s, color=color, size=size, font=font, align=align, valign=valign, x=x, y=y,
                  name=name, layer=layer, animated=animated, why=why)


def stamp(col, s, color=SILK, size=1.8, name=None, why="A silkscreen legend across the centre."):
    return label(col, s, color=color, size=size, font=SILKFONT, align="Center", valign="Center",
                 x=0, y=0, name=name, animated=True, why=why)


def vu(col, color=PADGREEN, amp=0.06, name="MIDI Activity"):
    return L.scope(col, color=color, position=0.9, amplitude=amp, name=name,
                   why="MIDI activity along the bottom: the monitor in Preferences > MIDI.")


# ================================================================ DECK 1
# THE GRID - 40 pads, notes 0-39, the RGB palette, the three modes
def deck1():
    C = []
    cols = ["Note Zero", "Row Of Eight", "Five Rows", "Velocity Palette",
            "Green 21", "Amber 9", "Scene Launch", "Mode 1"]
    C += [padgrid(1), pad(2, 1, color=PADGREEN, x=-840, y=-300, name="Pad n0",
                          why="Bottom-left pad: note 0. note = row_from_bottom x 8 + column."),
          blank(3, 1, "One pad."),
          glow(1, opacity=0.12),
          label(1, "NOTE 0 - CHANNEL 1\n0x90 0x00 vel\nBOTTOM-LEFT", why="Note-on status 0x90 on channel 1."),
          blank(6, 1), vrules(1), vu(1)]
    C += [padgrid(2), padrow(2, 2, color=PADGREEN, y=-0.62, name="Row 1: n0-n7"),
          blank(3, 2, "The row is the figure."),
          glow(2, opacity=0.1),
          label(2, "ROW 1 = BED LAYER\nn0 n1 n2 n3 n4 n5 n6 n7", why="The bottom row addresses layer 1's eight clips."),
          blank(6, 2), vrules(2), vu(2)]
    C += [padgrid(3), padrow(2, 3, color=PADGREEN, grid=8, y=-0.62, name="Row 1"),
          padrow(3, 3, color=PADAMBER, grid=8, y=0.62, name="Row 5: n32-n39",
                 why="Top row: n32-n39, the TEXT layer in every pack here."),
          glow(3, color=PADAMBER_DIM, opacity=0.1),
          label(3, "5 ROWS x 8 = 40 PADS\nn0 - n39\nROWS 1-5 = LAYERS 1-5"),
          blank(6, 3), vrules(3), vu(3)]
    C += [chassis(4), clip(2, 4, "128 Velocities", "Checkered",
                           {"Num X": 16, "Num Y": 8, "Color 1": CHASSIS2, "Color 2": PADGREEN_DIM},
                           "The 128-entry RGB velocity palette: 0-3 greys, then hues in fours.", opacity=0.6),
          pad(3, 4, color=PADAMBER, x=-620, y=260, name="Index 9",
              why="Index 9: amber on. 10 is its dim."),
          glow(4, color=PADAMBER_DIM, opacity=0.08),
          label(4, "VELOCITY = COLOUR\n0 OFF - 3 WHITE - 5 RED\n9 AMBER - 21 GREEN - 45 BLUE", size=0.8),
          blank(6, 4), tooth(4), vu(4)]
    C += [padgrid(5), pad(2, 5, color=PADGREEN, x=-480, y=150, name="Connected 21"),
          pad(3, 5, color=PADGREEN_DIM, x=-240, y=150, name="Disconnected 22",
              why="Resolume sends 21 for Connected and 22 for Disconnected on this family."),
          glow(5, opacity=0.14),
          label(5, "GREEN FAMILY\nON 21 - DIM 22\nCONNECTED / DISCONNECTED"),
          blank(6, 5), vrules(5), vu(5)]
    C += [padgrid(6), pad(2, 6, color=PADAMBER, x=-480, y=150, name="Connected 9"),
          pad(3, 6, color=PADAMBER_DIM, x=-240, y=150, name="Disconnected 10"),
          glow(6, color=PADAMBER_DIM, opacity=0.14),
          label(6, "AMBER FAMILY\nON 9 - DIM 10\nONLY PADS + SCENES ARE RGB"),
          blank(6, 6), vrules(6), vu(6)]
    C += [chassis(7), padrow(2, 7, color=PADGREEN, grid=5, y=0.0, name="Scene 1-5",
                             why="Scene Launch 1-5, notes 82-86, the right column."),
          button(3, 7, color=SILK, x=0, y=-400, name="Stop All n81",
                 why="STOP ALL CLIPS, note 81, below the scene pads."),
          glow(7, opacity=0.1),
          label(7, "SCENE LAUNCH n82-n86\nSTOP ALL CLIPS n81\nMASTER n80"),
          blank(6, 7), tooth(7), vu(7)]
    C += [chassis(8), midi_wave(2, 8, color=DINRED, waves=12, amp=0.06, name="SysEx Bytes",
                    why="Twelve bytes over class-compliant USB-MIDI: the Mode SysEx on the wire."),
          button(3, 8, color=SILK, x=0, y=0, name="Mode", lit=True,
                 why="Mode 1: every button a plain momentary note; Device knobs un-banked."),
          pulse(8, freq=0.05, color=DINRED, opacity=0.1, name="Power Cycle",
                why="Power-cycling resets to Mode 0: send the SysEx again."),
          label(8, "F0 47 7F 29 60 00 04\n41 00 00 00 F7\nMODE 1 = ABLETON LIVE", size=0.9,
                why="Akai APC40 Mk2 Communications Protocol v1.2: 0x40 generic, 0x41 Live, 0x42 alternate."),
          wash(8, DINRED, kind="Radial", opacity=0.05), tooth(8), vu(8, color=DINRED)]
    return {"name": "The Grid", "slug": "grid", "theme": "hardware",
            "world": ("The 5x8 pad grid drawn on a matte black chassis: note 0 bottom-left, rows of eight, "
                      "five rows for five layers, the 128-entry RGB velocity palette, the two LED families "
                      "every pack here speaks (green 21/22, amber 9/10), the Scene Launch column, and the "
                      "SysEx that puts the controller into Mode 1 - a show requirement, because a power "
                      "cycle forgets it."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Matte black chassis."},
                        {"role": "body", "hex": "#3ddc84", "why": "Pad green, velocity 21."},
                        {"role": "figure", "hex": "#ffae1a", "why": "Pad amber, velocity 9."},
                        {"role": "light", "hex": "#3ddc84", "why": "LED bleed."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Silkscreen white, protocol values in Consolas."},
                        {"role": "aura", "hex": "#e03a2f", "why": "MIDI red, only on the wire."}],
            "columns": cols,
            "text_corpus": ["NOTE 0", "n0 - n39", "5 x 8 = 40", "VELOCITY = COLOUR", "ON 21 - DIM 22",
                            "ON 9 - DIM 10", "SCENE LAUNCH n82-n86", "STOP ALL CLIPS n81",
                            "F0 47 7F 29 60 00 04 41", "MODE 1", "0x90", "CHANNEL 1"],
            "moments": [
                "Note zero: Scene Launch 1 and press the real bottom-left pad; the picture is the pad.",
                "Palette: column 4, tap the row-3 FIGURE pad on the beat so index 9 blinks amber over the "
                "128-cell table.",
                "Mode 1: UP to column 8 and let the SysEx bytes ride the mids; this is the message to send "
                "after every power-up."],
            "clips": C}


# ================================================================ DECK 2
# THE STRIPS - per-track buttons (note fixed, channel = track), faders, master, crossfader
def deck2():
    C = []
    cols = ["Channel = Track", "Clip Stop 52", "Select 51", "Activator 50",
            "Rec Arm 48", "A/B 66", "Faders CC7", "Crossfader CC15"]
    C += [silk(1, amount=8, rot=90.0, color=SILK_DIM, name="Track Columns", opacity=0.6),
          padrow(2, 1, color=SILK, grid=8, y=0.0, name="Eight Strips"),
          button(3, 1, color=SILK, x=-840, y=0, name="Track 1", lit=True,
                 why="Same note on every strip; only the MIDI channel differs, 1-8."),
          glow(1, opacity=0.08),
          label(1, "PER-TRACK BUTTONS\nNOTE FIXED - CHANNEL = TRACK\n0x90 + (ch - 1)"),
          blank(6, 1), tooth(1), vu(1)]
    C += [silk(2, amount=8, rot=90.0, color=SILK_DIM, name="Track Columns", opacity=0.4),
          padrow(2, 2, color=SILK, grid=8, y=0.3, name="Clip Stop Row"),
          button(3, 2, color=SILK, x=-600, y=200, name="n52 ch3", lit=True,
                 why="Clip Stop on strip 3: note 52, channel 3 - EJECT layer 3."),
          pulse(2, freq=0.2, color=PADGREEN, opacity=0.1),
          label(2, "CLIP STOP n52 ch1-8\n= EJECT LAYER 1-8\n(TRACK/CLIP STOP)"),
          blank(6, 2), tooth(2), vu(2)]
    C += [silk(3, amount=8, rot=90.0, color=SILK_DIM, name="Track Columns", opacity=0.4),
          padrow(2, 3, color=SILK, grid=8, y=0.1, name="Select Row"),
          button(3, 3, color=SILK, x=-360, y=70, name="n51 ch4", lit=True,
                 why="Track Select: note 51 - SELECT layer. In Mode 0 this re-banks the Device knobs instead."),
          glow(3, opacity=0.08),
          label(3, "TRACK SELECT n51\n= SELECT LAYER\nMODE 0 RE-BANKS THE KNOBS"),
          blank(6, 3), tooth(3), vu(3)]
    C += [silk(4, amount=8, rot=90.0, color=SILK_DIM, name="Track Columns", opacity=0.4),
          padrow(2, 4, color=PADGREEN, grid=8, y=-0.1, name="Activators Lit",
                 why="Activator LEDs lit = layer on air (bypass off)."),
          button(3, 4, color=SILK, x=120, y=-70, name="n50 ch6 Off",
                 why="One activator dark: layer 6 muted."),
          glow(4, opacity=0.1),
          label(4, "ACTIVATOR n50 = MUTE\nSOLO n49 = SOLO\nLIT = ON AIR"),
          blank(6, 4), tooth(4), vu(4)]
    C += [silk(5, amount=8, rot=90.0, color=SILK_DIM, name="Track Columns", opacity=0.4),
          padrow(2, 5, color=PADAMBER, grid=8, y=-0.3, name="Rec Arm Row",
                 why="Record Arm, note 48 on channels 1-8: FX bank 1, eight latching toggles."),
          button(3, 5, color=PADAMBER, x=-840, y=-210, name="FX1 TINT", lit=False,
                 why="The first seat of bank 1: TINT."),
          glow(5, color=PADAMBER_DIM, opacity=0.1),
          label(5, "RECORD ARM n48 ch1-8\n= FX BANK 1\nEIGHT LATCHING TOGGLES"),
          blank(6, 5), tooth(5), vu(5)]
    C += [silk(6, amount=8, rot=90.0, color=SILK_DIM, name="Track Columns", opacity=0.4),
          padrow(2, 6, color=PADAMBER, grid=8, y=-0.5, name="A/B Row",
                 why="Crossfade A/B, note 66: FX bank 2 here."),
          button(3, 6, color=SILK, x=360, y=-350, name="n66 ch6", lit=True),
          glow(6, color=PADAMBER_DIM, opacity=0.08),
          label(6, "CROSSFADE A/B n66 ch1-8\n= FX BANK 2\nDEVICE ROW n58-65 = BANK 3"),
          blank(6, 6), tooth(6), vu(6)]
    C += [chassis(7), faders8(2, 7), fader(3, 7, color=PADGREEN, position=0.1875, rot=90.0, width=0.04,
                                           name="Fader 2 Cap", fft_=fft("Width", "low", 0.04, 0.08, 8.0, 400),
                                           why="Fader 2: CC7 on channel 2, layer 2's master."),
          glow(7, opacity=0.06),
          label(7, "TRACK FADERS CC7 ch1-8\n= LAYER MASTER 1-8\nMASTER FADER CC14"),
          blank(6, 7), vrules(7, amount=8), vu(7)]
    C += [chassis(8), fader(2, 8, color=SILK, position=0.5, rot=0.0, width=0.03, name="Crossfader Slot",
                            fft_={}),
          fader(3, 8, color=PADGREEN, position=0.5, rot=90.0, width=0.06, name="Crossfader Cap",
                fft_=fft("Position", "low", 0.2, 0.8, 9.0, 700),
                why="CC15: environment <-> figures. Centre = everything, rig-measured."),
          glow(8, opacity=0.08),
          label(8, "CROSSFADER CC15\nA: BED BODY AURA\nB: FIGURE LIGHT TEXT"),
          blank(6, 8), tooth(8), vu(8)]
    return {"name": "The Strips", "slug": "strips", "theme": "hardware",
            "world": ("Eight track strips, each a copy of the last: the per-track buttons keep one note "
                      "and change only the MIDI channel. Clip Stop 52 ejects, Select 51 selects, Activator "
                      "50 is on-air, Solo 49, Record Arm 48 and Crossfade A/B 66 are the first two effect "
                      "banks in every pack here. Below them the eight faders on CC7, the master on CC14 "
                      "and the crossfader on CC15 whose centre is everything."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#e8e4d8", "why": "Silkscreen strips and fader slots."},
                        {"role": "figure", "hex": "#3ddc84", "why": "The one control lit."},
                        {"role": "light", "hex": "#ffae1a", "why": "Amber for the FX banks."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Note and CC numbers."},
                        {"role": "aura", "hex": "#1f2126", "why": "Grey."}],
            "columns": cols,
            "text_corpus": ["CHANNEL = TRACK", "CLIP STOP n52", "TRACK SELECT n51", "ACTIVATOR n50",
                            "SOLO n49", "RECORD ARM n48", "CROSSFADE A/B n66", "CC7 ch1-8",
                            "MASTER CC14", "CROSSFADER CC15", "0x90 + (ch - 1)", "CENTRE = EVERYTHING"],
            "moments": [
                "Channel = track: Scene Launch 1, then press Clip Stop on strip 3 - the one lit button (layer 3) "
                "vanishes, because note 52 on channel 3 ejects layer 3; Scene Launch 1 brings it back.",
                "Rec Arm: column 5, tap the real Record Arm buttons - they are FX bank 1, and the amber row "
                "is them.",
                "Crossfader: column 8, sweep the real crossfader; the scene's layers split A from B (the green "
                "cap sits on FIGURE, side B, and goes dark at hard A). The cap's own travel is the lows, not CC15."],
            "clips": C}


# ================================================================ DECK 3
# KNOBS + TRANSPORT - device knobs with rings, track knobs, cue, tempo encoder, transport
def deck3():
    C = []
    cols = ["Device CC16-23", "LED Rings", "Track CC48-55", "Cue Level CC47",
            "Tempo CC13", "Play Stop Rec", "Tap + Nudge", "Footswitch CC64"]
    C += [chassis(1), silk(1, amount=2, layer=2, color=SILK_DIM, name="Knob Rows", opacity=0.6),
          knob(3, 1, color=SILK, size=0.28, ring=True, name="Device Knob 1",
               why="Device Control knobs 1-8, CC16-23: dashboard links 1-8, the four bank wets and four macros."),
          glow(1, color=PADAMBER_DIM, opacity=0.1),
          label(1, "DEVICE KNOBS CC16-23\n= DASHBOARD LINK 1-8\nBANKS 1-4 - MACROS 5-8"),
          blank(6, 1), tooth(1), vu(1)]
    C += [chassis(2), knob(2, 2, color=SILK_DIM, size=0.5, ring=True, name="Ring Wide"),
          knob(3, 2, color=PADAMBER, size=0.5, ring=False, name="Ring Value",
               why="Ring LEDs follow the value CC in Mode 1; ring style is single, volume or pan."),
          glow(2, color=PADAMBER_DIM, opacity=0.12),
          label(2, "LED RINGS\nSINGLE - VOLUME - PAN STYLE\nFOLLOW THE VALUE CC"),
          blank(6, 2), tooth(2), vu(2)]
    C += [chassis(3), silk(3, amount=1, layer=2, color=SILK_DIM, name="Top Row", opacity=0.6),
          clip(3, 3, "Eight Track Knobs", "Metaballs",
               {"Grid": 8, "Blend": "Minimal", "Size": 0.07, "Distance": 0.5, "Radius": 0.1,
                "Fuzzyness": 0.02, "Speed": 0.0, "Position X": 0.0, "Position Y": 0.55,
                "Color": SILK, "BG Color": CLEAR},
               "Track Control knobs 1-8 along the top, CC48-55: LOW/MID/HIGH depth and release, SCOPE, TIME.",
               opacity=0.9, fft=fft("Size", "mid", 0.06, 0.11, 9.0, 300)),
          glow(3, opacity=0.08),
          label(3, "TRACK KNOBS CC48-55\nLOW MID HIGH: DEPTH + RELEASE\nSCOPE DEPTH - TIME", size=0.8),
          blank(6, 3), tooth(3), vu(3)]
    C += [chassis(4), knob(2, 4, color=SILK, size=0.34, name="Cue Level",
                           why="CUE LEVEL, CC47: the FX master sweep over the four bank links."),
          fader(3, 4, color=PADAMBER, position=0.5, rot=0.0, width=0.02, name="Sweep",
                fft_=fft("Position", "low", 0.2, 0.8, 8.0, 600)),
          glow(4, color=PADAMBER_DIM, opacity=0.08),
          label(4, "CUE LEVEL CC47\n= FX MASTER SWEEP\nANTICLOCKWISE = CLEAN"),
          blank(6, 4), tooth(4), vu(4)]
    C += [chassis(5), knob(2, 5, color=SILK, size=0.3, name="Tempo Encoder",
                           why="TEMPO, CC13, relative: 1-63 up, 127-64 down."),
          midi_wave(3, 5, color=DINRED, waves=4, amp=0.05, position=0.2, name="Relative Ticks"),
          pulse(5, freq=0.1, color=PADAMBER, opacity=0.1, name="Beat"),
          label(5, "TEMPO CC13 - RELATIVE\n1-63 = UP - 127-64 = DOWN\nBPM", size=0.9),
          blank(6, 5), tooth(5), vu(5)]
    C += [chassis(6), button(2, 6, color=SILK, x=-300, y=0, name="PLAY n91", lit=True,
                             why="PLAY: OPEN THE SHOW - column 1 + re-arm the SCOPE."),
          button(3, 6, color=SILK, x=0, y=0, name="STOP n92",
                 why="STOP: CLEAR THE GRID - eject layers 1-5. RECORD n93: BLACKOUT."),
          glow(6, opacity=0.08),
          label(6, "PLAY n91 - STOP n92\nRECORD n93 = BLACKOUT\nSESSION REC n102"),
          blank(6, 6), tooth(6), vu(6)]
    C += [chassis(7), button(2, 7, color=SILK, x=-200, y=0, name="TAP n99", lit=True),
          button(3, 7, color=SILK, x=200, y=0, name="NUDGE+ n101",
                 why="NUDGE - n100, NUDGE + n101; METRONOME n90 is resync."),
          pulse(7, freq=0.1, color=PADAMBER, opacity=0.14, name="Tap"),
          label(7, "TAP TEMPO n99\nNUDGE n100 / n101\nMETRONOME n90 = RESYNC"),
          blank(6, 7), tooth(7), vu(7)]
    C += [chassis(8), din(2, 8, color=SILK, name="1/4 Inch Jack",
                          why="The footswitch jack, rear panel."),
          fader(3, 8, color=DINRED, position=0.5, rot=0.0, width=0.04, name="CC64 Down",
                fft_=fft("Width", "low", 0.02, 0.1, 10.0, 200),
                why="CC64: 0x7F down, 0x00 up - momentary BLACKOUT."),
          pulse(8, freq=0.3, color=DINRED, opacity=0.1),
          label(8, "FOOTSWITCH CC64\n0x7F DOWN - 0x00 UP\n= MOMENTARY BLACKOUT"),
          blank(6, 8), tooth(8), vu(8, color=DINRED)]
    return {"name": "Knobs + Transport", "slug": "knobs", "theme": "hardware",
            "world": ("The right-hand block and the top row: eight Device knobs with LED rings on CC16-23 "
                      "(the dashboard links), eight Track knobs on CC48-55 (the live FFT), Cue Level on "
                      "CC47 (the effects master sweep), the relative Tempo encoder on CC13, PLAY STOP "
                      "RECORD on notes 91-93, Tap and Nudge, and the footswitch on CC64 that is a momentary "
                      "blackout in every pack here."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#e8e4d8", "why": "Knob bodies and buttons."},
                        {"role": "figure", "hex": "#ffae1a", "why": "LED rings."},
                        {"role": "light", "hex": "#ffae1a", "why": "Beat pulses."},
                        {"role": "text", "hex": "#e8e4d8", "why": "CC numbers."},
                        {"role": "aura", "hex": "#e03a2f", "why": "Red for relative ticks and the footswitch."}],
            "columns": cols,
            "text_corpus": ["DEVICE KNOBS CC16-23", "LED RINGS", "TRACK KNOBS CC48-55", "CUE LEVEL CC47",
                            "TEMPO CC13", "RELATIVE", "PLAY n91", "STOP n92", "RECORD n93", "TAP n99",
                            "NUDGE n100 / n101", "FOOTSWITCH CC64"],
            "moments": [
                "Rings: column 2, turn Device knob 1 slowly; the amber ring on screen is the ring under your "
                "hand.",
                "Cue level: column 4, sweep CUE LEVEL anticlockwise to CLEAN and back; the amber line is the "
                "four bank links moving together.",
                "Footswitch: column 8, stamp the pedal on the one; the red bar is CC64 going 0x7F."],
            "clips": C}


# ================================================================ DECK 4
# THE WIRE - MIDI itself: DIN-5, 31,250 baud, status bytes, the USB, the key encoding
def deck4():
    C = []
    cols = ["DIN-5", "31,250 Baud", "Status Byte", "Note On / Off",
            "Control Change", "USB-B", "Resolume Key", "Monitor"]
    C += [chassis(1), din(2, 1), pins5(3, 1),
          glow(1, color=DINRED, opacity=0.06),
          label(1, "DIN-5 - 180 DEGREES\nPINS 4 + 5: 5 mA LOOP\nOPTO-ISOLATED IN", why="The 1983 MIDI 1.0 spec."),
          blank(6, 1), tooth(1), vu(1, color=DINRED)]
    C += [chassis(2), midi_wave(2, 2, color=DINRED, waves=10, amp=0.1, name="Bit Stream"),
          clip(3, 2, "Start Stop Bits", "Lines",
               {"Fuzzyness": 0.0, "Amount": 10, "Width": 0.02, "Rotation": 90.0, "Position": 0.5,
                "Color": SILK_DIM}, "Ten bits per byte: start, eight data, stop.", opacity=0.6,
               fft=fft("Fuzzyness", "high", 0.0, 0.3, 8.0, 250)),
          glow(2, color=DINRED, opacity=0.05),
          label(2, "31,250 BAUD\n1 START - 8 DATA - 1 STOP\n320 us PER BYTE", why="Asynchronous serial, no parity."),
          blank(6, 2), tooth(2), vu(2, color=DINRED)]
    C += [chassis(3), clip(2, 3, "Eight Bits", "Checkered",
                           {"Num X": 8, "Num Y": 1, "Color 1": CHASSIS2, "Color 2": DINRED},
                           "A status byte: high bit set, 1001 nnnn.", opacity=0.8,
                           effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 24.0}}]),
          button(3, 3, color=DINRED, x=-770, y=0, name="MSB = 1", why="Bit 7 set: this is a status byte."),
          glow(3, color=DINRED, opacity=0.06),
          label(3, "STATUS 1001 nnnn = 0x9n\n1011 nnnn = 0xBn\nnnnn = CHANNEL - 1", font=MONO),
          blank(6, 3), tooth(3), vu(3, color=DINRED)]
    C += [padgrid(4), pad(2, 4, color=PADGREEN, x=-480, y=150, name="Note On"),
          pulse(4, freq=0.3, color=PADGREEN, opacity=0.3, layer=3, name="Note Off",
                why="Note off: 0x80, or 0x90 with velocity 0. The pad goes dark."),
          glow(4, opacity=0.1),
          label(4, "NOTE ON 0x90 nn vv\nNOTE OFF 0x80 nn 00\nPIANO = HOLD", why="Trigger style Piano listens to the note off."),
          blank(6, 4), vrules(4), vu(4)]
    C += [chassis(5), fader(2, 5, color=SILK, position=0.5, rot=90.0, name="Fader",
                            fft_=fft("Position", "low", 0.1, 0.9, 9.0, 500)),
          clip(3, 5, "0-127", "Lines",
               {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.01, "Rotation": 0.0, "Position": 0.5,
                "Color": SILK_DIM}, "7 bits of value: 0 to 127, 128 steps.", opacity=0.8),
          glow(5, opacity=0.06),
          label(5, "CONTROL CHANGE 0xBn cc vv\n7 BITS = 128 STEPS\nCC7 - CC14 - CC15 - CC16-23", size=0.8),
          blank(6, 5), tooth(5), vu(5)]
    C += [chassis(6), usb(2, 6), midi_wave(3, 6, color=SILK, waves=16, amp=0.03, position=0.75,
                                           name="USB Packets", why="Class-compliant USB MIDI: no driver, bus powered."),
          glow(6, opacity=0.06),
          label(6, "USB-B - BUS POWERED\nCLASS COMPLIANT\n424 x 254 x 46 MM - 1.8 KG", size=0.8),
          blank(6, 6), tooth(6), vu(6)]
    C += [chassis(7), silk(7, amount=4, layer=2, color=SILK_DIM, name="Key Rows", opacity=0.6),
          clip(3, 7, "Marker Bit", "Shaper",
               {"Scale": 0.1, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                "Color": PADGREEN, "Outline": 0.0, "Outline Color": PADGREEN},
               "2^56: the note marker; 2^57 for CC. How Resolume files a raw MIDI message.", opacity=0.9,
               effects=[xform(x=-700, y=120)], fft=fft("Scale", "mid", 0.1, 0.14, 8.0, 300)),
          glow(7, opacity=0.06),
          label(7, "KEY = MARKER\n+ (data1<<8) + status\nNOTE 2^56 - CC 2^57", font=MONO, size=0.8,
                why="Rig-proven across every preset in this workspace."),
          blank(6, 7), tooth(7), vu(7)]
    C += [chassis(8), silk(8, amount=12, layer=2, color=CHASSIS2, name="Monitor Rows"),
          midi_wave(3, 8, color=PADGREEN, waves=6, amp=0.06, position=0.5, name="Messages Scrolling",
                    why="USB-MIDI packets arriving: what the monitor in Preferences > MIDI shows."),
          pulse(8, freq=0.2, color=PADGREEN, opacity=0.08),
          label(8, "PREFERENCES > MIDI\nMIDI MONITOR\nAPC40 MKII: IN + OUT", why="The output drives the LEDs."),
          blank(6, 8), tooth(8), vu(8)]
    return {"name": "The Wire", "slug": "wire", "theme": "protocol",
            "world": ("MIDI itself, from the 1983 spec to tonight's preset: the DIN-5 with its 5 mA current "
                      "loop, 31,250 baud and ten bits a byte, the status byte with its high bit set, note on "
                      "and note off (Piano listens for the off), control change with 128 steps, the "
                      "class-compliant USB that powers the whole surface, and the 2^56 (note) and 2^57 (CC) markers Resolume "
                      "files a raw message under. Red is the wire; green is a message arriving."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#e03a2f", "why": "The wire."},
                        {"role": "figure", "hex": "#3ddc84", "why": "A message."},
                        {"role": "light", "hex": "#3ddc84", "why": "Note-on flashes."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Bytes in Consolas."},
                        {"role": "aura", "hex": "#e03a2f", "why": "Red."}],
            "columns": cols,
            "text_corpus": ["DIN-5", "5 mA CURRENT LOOP", "31,250 BAUD", "1 START - 8 DATA - 1 STOP",
                            "0x90", "0xB0", "NOTE ON / OFF", "0 - 127", "USB-B - BUS POWERED",
                            "2^56 + (data1 << 8) + status", "RAW INPUT MESSAGE", "MIDI MONITOR"],
            "moments": [
                "Baud: Scene Launch 2 and the bit stream rides the mids; on the five-pin wire every byte is ten "
                "bits (the APC rides USB, which packs them four bytes at a time).",
                "Note on/off: column 4, hold a pad - the green pad lives while you hold it, the flash is the "
                "note off.",
                "Monitor: column 8 with Preferences > MIDI open on the second screen; the scrolling line is "
                "what the monitor shows."],
            "clips": C}


# ================================================================ DECK 5
# SE-500 - the wildcard: a four-input analog video mixer with a T-bar and MIDI control
def deck5():
    C = []
    cols = ["Four Inputs", "Main / Sub", "T-Bar", "Wipe",
            "PIP", "Split Screen", "Colour Proc", "MIDI + RS-232"]
    C += [chassis(1, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), clip(2, 1, "Four BNCs", "Metaballs",
                           {"Grid": 4, "Blend": "Minimal", "Size": 0.1, "Distance": 0.5, "Radius": 0.1,
                            "Fuzzyness": 0.02, "Speed": 0.0, "Position X": 0.0, "Position Y": 0.3,
                            "Color": SILK, "BG Color": CLEAR},
                           "Four composite inputs on BNC; S-Video on mini-DIN beside each.", opacity=0.9,
                           fft=fft("Size", "low", 0.09, 0.14, 8.0, 300)),
          button(3, 1, color=SILK, x=-420, y=-180, name="Input 1", lit=True,
                 why="Illuminated selection buttons, one per input (red on the SE-500; green is the pack's lit colour)."),
          glow(1, opacity=0.08),
          label(1, "DATAVIDEO SE-500\n4 x COMPOSITE BNC\n4 x S-VIDEO MINI-DIN"),
          blank(6, 1), tooth(1), vu(1, name="Program")]
    C += [chassis(2, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), padrow(2, 2, color=SILK_DIM, grid=4, y=0.2, name="Sub Source", why="Sub source: the input the next transition, split or PIP will use."),
          padrow(3, 2, color=PADGREEN, grid=4, y=-0.2, name="Main Source",
                 why="Main source selected: what is on the output (the SE-500 lights it red; green is the pack's lit colour). Two composite program outs plus S-Video, component via the breakout cable, and a separate quad-preview out."),
          glow(2, opacity=0.1),
          label(2, "MAIN / SUB SOURCE\nOUT: 2 x COMPOSITE\nS-VIDEO - QUAD PREVIEW"),
          blank(6, 2), tooth(2), vu(2, name="Program")]
    C += [chassis(3, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), fader(2, 3, color=SILK, position=0.5, rot=0.0, width=0.03, name="T-Bar Slot", fft_={}),
          fader(3, 3, color=PADAMBER, position=0.5, rot=90.0, width=0.08, name="T-Bar",
                fft_=fft("Position", "low", 0.05, 0.95, 9.0, 800),
                why="The T-bar: pull it through and the transition happens at your speed."),
          glow(3, color=PADAMBER_DIM, opacity=0.1),
          label(3, "T-BAR\nDISSOLVE - FADE\nAT YOUR OWN SPEED"),
          blank(6, 3), tooth(3), vu(3, name="Program")]
    C += [chassis(4, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), clip(2, 4, "Source A", "Solid Color", {"Color": SILK_DIM}, "Input A, full frame.",
                           opacity=0.6),
          fader(3, 4, color=PADGREEN, position=0.4, rot=90.0, width=0.5, name="Wipe Edge",
                fft_=fft("Position", "mid", 0.0, 1.0, 8.0, 900),
                why="A vertical wipe revealing input B."),
          glow(4, opacity=0.06),
          label(4, "WIPE\n11 PATTERNS\nDIRECTION - BORDER"),
          blank(6, 4), tooth(4), vu(4, name="Program")]
    C += [chassis(5, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), clip(2, 5, "Background", "Solid Color", {"Color": CHASSIS2}, "Input A as background.",
                           opacity=1.0),
          clip(3, 5, "PIP Window", "Shaper",
               {"Scale": 0.3, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                "Color": PADGREEN, "Outline": 0.02, "Outline Color": SILK},
               "Picture-in-picture: input B in a window, top-right.", opacity=0.9,
               effects=[{"effect": "Transform", "params": {"Scale W": 160.0, "Scale H": 90.0,
                                                           "Position X": 520.0, "Position Y": -280.0}}],
               fft=fft("Scale", "low", 0.3, 0.36, 8.0, 400)),
          glow(5, opacity=0.06),
          label(5, "PIP\nPOSITION - SIZE - BORDER"),
          blank(6, 5), tooth(5), vu(5, name="Program")]
    C += [chassis(6, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), fader(2, 6, color=SILK, position=0.5, rot=90.0, width=0.01, name="Split Line", fft_={}),
          clip(3, 6, "Right Half", "Solid Color", {"Color": PADGREEN_DIM}, "Input B on the right half.",
               opacity=0.7, effects=[{"effect": "Transform", "params": {"Scale W": 50.0, "Scale H": 100.0,
                                                                           "Position X": 480.0}}]),
          glow(6, opacity=0.06),
          label(6, "SPLIT SCREEN\nA LEFT - B RIGHT"),
          blank(6, 6), tooth(6), vu(6, name="Program")]
    C += [chassis(7, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), clip(2, 7, "Colour Bars", "Checkered",
                           {"Num X": 8, "Num Y": 1, "Color 1": SILK, "Color 2": PADAMBER},
                           "Colour processing: bars to set levels by.", opacity=0.8),
          knob(3, 7, color=SILK, size=0.26, name="Chroma", effects=[xform(y=-320)],
               why="Colour processing, per input, from the on-screen menu (hold Background, steer with the arrows and +/-): brightness, contrast, colour, tint. The knob is the pack's glyph, not the SE-500's control."),
          glow(7, color=PADAMBER_DIM, opacity=0.08),
          label(7, "COLOUR PROCESSING\nBRIGHTNESS - CONTRAST\nCOLOUR - TINT (MENU)"),
          blank(6, 7), tooth(7), vu(7, name="Program")]
    C += [chassis(8, why="The SE-500\'s slate-blue body, drawn in the pack\'s black."), din(2, 8, color=SILK, name="DE-9 RS-232",
                          why="RS-232 on a 9-pin D-sub, tally on a 15-pin D-sub, and MIDI control on a 5-pin DIN."),
          pins5(3, 8, color=DINRED),
          pulse(8, freq=0.2, color=DINRED, opacity=0.08, name="Command"),
          label(8, "RS-232 D-SUB 9\nMIDI CONTROL 5-PIN DIN\nTHE APC'S LANGUAGE,\nON A REAL WIRE"),
          wash(8, DINRED, kind="Radial", opacity=0.05), tooth(8), vu(8, color=DINRED, name="MIDI In")]
    return {"name": "SE-500 Mixer", "slug": "se500", "theme": "wildcard",
            "world": ("A four-input analog SD video mixer drawn in the same chassis grammar: BNC composite "
                      "and S-Video inputs with illuminated select buttons, a main and a sub source bus, "
                      "the T-bar you pull at your own speed, wipes, picture-in-picture, split screen, "
                      "colour processing, and - the reason it belongs in this pack - RS-232 on a 9-pin D-sub "
                      "and MIDI control on a five-pin DIN: the APC40's language on the older wire (the APC itself is USB-only)."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#e8e4d8", "why": "Inputs, slots, split lines."},
                        {"role": "figure", "hex": "#3ddc84", "why": "The pack's lit green (the SE-500's own on-air colour is red)."},
                        {"role": "light", "hex": "#ffae1a", "why": "The T-bar's amber."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Panel legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "The control wire."}],
            "columns": cols,
            "text_corpus": ["DATAVIDEO SE-500", "4 x COMPOSITE BNC", "S-VIDEO MINI-DIN", "MAIN / SUB SOURCE",
                            "T-BAR", "WIPE", "PIP", "SPLIT SCREEN", "COLOUR PROCESSING", "RS-232 D-SUB 9",
                            "MIDI CONTROL 5-PIN DIN", "THE APC'S LANGUAGE"],
            "moments": [
                "T-bar: Scene Launch 3 and ride the real crossfader slowly end to end; the amber T-bar is "
                "your hand.",
                "Wipe to PIP: UP from Wipe to PIP on a downbeat with Device knob 3 (SPACE) at a quarter and MIRROR QUAD lit "
                "so the window tiles.",
                "The older wire: column 8, tap any APC button on the beat; the red pins flash - the same note-on, on five pins instead of USB."],
            "clips": C}


def main():
    decks = [deck1(), deck2(), deck3(), deck4(), deck5()]
    bible = {
        "pack_name": "The Surface",
        "comp_name": "The Surface - APC40 mkII + MIDI",
        "tagline": "Note 0 is bottom-left. Channel is track. Centre is everything.",
        "decks": [{k: v for k, v in d.items() if k != "clips"} for d in decks],
        "effect_wishlist": [
            {"effect": "Bloom", "role": "Bank A: LED bleed through the rubber."},
            {"effect": "Trails", "role": "Bank A: the T-bar's travel and the bit stream."},
            {"effect": "Mirror Quad", "role": "Bank D: the PIP window tiles."},
            {"effect": "CRT", "role": "Bank C: the mixer's program monitor."},
            {"effect": "Grid Cloner", "role": "Bank D: the pad grid of grids."}],
        "fft_philosophy": (
            "The controller is the subject and the music is what it controls, so the reactivity stays "
            "mechanical: lows swell pads and widen fader caps, mids turn knob gaps and move playheads and "
            "T-bars, highs only jitter the serial bits and the DIN pins. Colour never reacts: green is a "
            "lit pad or a message arriving, amber is the second LED family and the T-bar, red is the wire "
            "and nothing else. Text never moves. Every note, CC and byte on screen is the real one."),
        "wildcard_rationale": (
            "Four decks are the APC40 mkII and its wire: the grid, the strips, the knobs and transport, "
            "and MIDI itself. The fifth is a video mixer of the same era of hands-on control, the "
            "Datavideo SE-500, chosen because it speaks the APC's MIDI over the older five-pin wire and because "
            "its T-bar is the crossfader's older sibling.")}
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
