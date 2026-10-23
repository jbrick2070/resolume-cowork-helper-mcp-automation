#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py - THE MIXERS, a stock-only Avenue 7.28.1 instrument about four pieces of
hands-on video hardware drawn as schematics, one deck each, switched from the APC40
mkII's own LEFT / RIGHT buttons (notes 97 / 96: previous / next deck):

  deck 1  APC40 mkII        the controller as an object: chassis, pads, faders, USB
  deck 2  Edirol V-4        Roland's 4-channel mixer with MIDI and beat sync (2002)
  deck 3  Videonics MXPro   the 1998 digital mixer with the effect keypad
  deck 4  Videonics MX-1    the 1994 original: four inputs, a T-bar, a numeric keypad
  deck 5  Patch Bay         how the four talk: T-bar vs crossfader, inputs vs layers,
                            composite vs USB, and the words they share

Drawing helpers come from packs/the-surface/design.py (chassis, pads, knobs, faders,
DIN sockets); captions from packs/library-hand/design.py. Every number on screen is
from the sources listed in README.md; a caption that could not be sourced says so or
was cut.

    python packs/the-mixers/design.py      -> bible.json + decks.json
"""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "..", rel, "design.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = _load("lh", "library-hand")
S = _load("surf", "the-surface")
clip, fft, xform = L.clip, L.fft, L.xform
(chassis, padgrid, silk, vrules, pad, padrow, knob, fader, faders8, button, midi_wave, din, pins5,
 usb, glow, pulse, wash, blank, tooth, label, stamp, vu) = (
    S.chassis, S.padgrid, S.silk, S.vrules, S.pad, S.padrow, S.knob, S.fader, S.faders8, S.button,
    S.midi_wave, S.din, S.pins5, S.usb, S.glow, S.pulse, S.wash, S.blank, S.tooth, S.label, S.stamp, S.vu)

CHASSIS, CHASSIS2, SILK, SILK_DIM = S.CHASSIS, S.CHASSIS2, S.SILK, S.SILK_DIM
GREEN, GREEN_DIM, AMBER, AMBER_DIM, RED, CLEAR = (S.PADGREEN, S.PADGREEN_DIM, S.PADAMBER,
                                                 S.PADAMBER_DIM, S.DINRED, S.CLEAR)
# the two mixers' own colours: Edirol's blue-grey and the Videonics beige, both kept dim
EDIROL = "#5b7a99ff"
EDIROL_DIM = "#5b7a9966"
VIDEONICS = "#d8cfb8ff"
VIDEONICS_DIM = "#d8cfb866"


# ---------------------------------------------------------------- shared drawings
def inputs(layer, col, n=4, color=SILK, y=0.3, name="Inputs", why="The video inputs, one dot each."):
    return clip(layer, col, name, "Metaballs",
                {"Grid": n, "Blend": "Minimal", "Size": 0.1, "Distance": 0.5, "Radius": 0.1,
                 "Fuzzyness": 0.02, "Speed": 0.0, "Position X": 0.0, "Position Y": y,
                 "Color": color, "BG Color": CLEAR}, why, opacity=0.9,
                fft=fft("Size", "low", 0.09, 0.14, 8.0, 300))


def tbar(col, color=AMBER, layer=3, name="T-Bar", why="The T-bar: the transition at your own speed."):
    return fader(layer, col, color=color, position=0.5, rot=90.0, width=0.08, name=name,
                 fft_=fft("Position", "low", 0.05, 0.95, 9.0, 800), why=why)


def slot(col, layer=2, rot=0.0, name="T-Bar Slot"):
    return fader(layer, col, color=SILK, position=0.5, rot=rot, width=0.03, name=name, fft_={},
                 why="The slot the bar travels in.")


def wipe(col, color=GREEN, layer=3, position=0.4, name="Wipe Edge", why="A wipe revealing the other bus."):
    return fader(layer, col, color=color, position=position, rot=90.0, width=0.5, name=name,
                 fft_=fft("Position", "mid", 0.0, 1.0, 8.0, 900), why=why)


def window(col, color=GREEN, layer=3, w=160.0, h=90.0, x=520.0, y=-280.0, name="PIP Window",
           why="Picture-in-picture: the other source in a window."):
    return clip(layer, col, name, "Shaper",
                {"Scale": 0.3, "Noise Type": "Grain", "Noise Amount": 0.0, "Noise Speed": 0.0,
                 "Color": color, "Outline": 0.02, "Outline Color": SILK}, why, opacity=0.9,
                effects=[{"effect": "Transform", "params": {"Scale W": w, "Scale H": h,
                                                           "Position X": x, "Position Y": y}}],
                fft=fft("Scale", "low", 0.3, 0.36, 8.0, 400))


def keypad(layer, col, nx=3, ny=4, color=SILK_DIM, name="Keypad", why="A numeric keypad: type the effect number."):
    return clip(layer, col, name, "Checkered",
                {"Num X": nx, "Num Y": ny, "Color 1": CLEAR, "Color 2": color}, why, opacity=0.7,
                effects=[{"effect": "Transform", "params": {"Scale W": 24.0, "Scale H": 40.0,
                                                           "Position X": 560.0, "Position Y": 80.0}}])


def bars(col, layer=2, name="Colour Bars", why="Colour bars: the test signal every mixer starts from."):
    return clip(layer, col, name, "Checkered",
                {"Num X": 8, "Num Y": 1, "Color 1": SILK, "Color 2": AMBER}, why, opacity=0.8)


def half(col, color=GREEN_DIM, layer=3, x=480.0, name="Right Half", why="The other source on the right half."):
    return clip(layer, col, name, "Solid Color", {"Color": color}, why, opacity=0.7,
                effects=[{"effect": "Transform", "params": {"Scale W": 50.0, "Scale H": 100.0, "Position X": x}}])


def field(col, color=SILK_DIM, layer=2, opacity=0.6, name="Source A", why="Input A, full frame."):
    return clip(layer, col, name, "Solid Color", {"Color": color}, why, opacity=opacity)


def freeze(col, layer=3, color=SILK, name="Freeze Frame", why="A frozen field: one picture held."):
    return clip(layer, col, name, "Static", {"Mode": "Grayscale"}, why, opacity=0.35)


def strobe(col, freq=0.5, color=SILK, layer=4, opacity=0.2, name="Strobe", why="A strobe: the frame held and dropped."):
    return pulse(col, freq=freq, color=color, opacity=opacity, layer=layer, name=name, why=why)


def legend(col, s, size=1.8, name=None, why="A silkscreen legend across the centre (layer 3, so the caption keeps layer 5)."):
    return label(col, s, color=SILK, size=size, font=S.SILKFONT, align="Center", valign="Center",
                 x=0, y=0, name=name, layer=3, animated=True, why=why)


def column(col, body, figure, text, light=None, aura=None, scope_name="Program", scope_color=GREEN,
           bed=None, grain=None):
    """One column with every layer filled: bed, body, figure, light, text, aura, grain, scope."""
    return [bed or chassis(col), body, figure, light or glow(col, opacity=0.08), text,
            aura or blank(6, col), grain or tooth(col), vu(col, color=scope_color, name=scope_name)]


# ================================================================ DECK 1
# APC40 mkII - the controller as hardware
def deck1():
    C = []
    cols = ["The Object", "40 Pads", "9 Faders", "16 Knobs",
            "Crossfader", "USB-B", "Three Modes", "On The Desk"]
    C += column(1, padrow(2, 1, color=SILK_DIM, grid=8, y=0.3, name="Pad Row (Dim)", why="A row of unlit pads."),
                padrow(3, 1, color=GREEN, grid=8, y=-0.1, name="Pad Row"),
                label(1, "AKAI APC40 MKII\n424 x 254 x 46 MM\n1.8 KG - BUS POWERED"),
                bed=padgrid(1, name="Pad Grid"))
    C += column(2, silk(2, amount=5, rot=0.0, layer=2, name="Five Rows"), pad(3, 2, color=GREEN, x=-480, y=150, name="Note 0"),
                label(2, "40 RGB PADS\nNOTE 0 = BOTTOM-LEFT\n128-COLOUR PALETTE"),
                bed=padgrid(2, name="5 x 8 Grid"), light=glow(2, opacity=0.12))
    C += column(3, silk(3, amount=9, rot=90.0, layer=2, name="Nine Slots"), faders8(3, 3, color=SILK, amount=9, name="Nine Faders",
                                                                           why="Eight channel faders and a master, 45 mm travel."),
                label(3, "9 x 45 MM FADERS\nCC7 CH1-8, MASTER CC14\nABSOLUTE, 0-127"))
    C += column(4, knob(2, 4, color=SILK, size=0.26, name="Track Knob", effects=[xform(x=-300, y=120)], ring=True,
                        why="Eight track knobs with LED rings, CC48-55."),
                knob(3, 4, color=SILK, size=0.26, name="Device Knob", effects=[xform(x=300, y=120)], ring=True,
                     why="Eight device knobs with LED rings, CC16-23."),
                label(4, "16 KNOBS, LED RINGS\nTRACK CC48-55\nDEVICE CC16-23"),
                light=glow(4, color=AMBER_DIM, opacity=0.1))
    C += column(5, slot(5, rot=0.0, name="Crossfader Slot"), fader(3, 5, color=AMBER, position=0.5, rot=90.0, width=0.08,
                                                                 name="Crossfader", fft_=fft("Position", "low", 0.05, 0.95, 9.0, 800),
                                                                 why="The crossfader, CC15: A left, B right, centre is both."),
                label(5, "CROSSFADER CC15\nA LEFT - B RIGHT\nCENTRE = EVERYTHING"),
                light=glow(5, color=AMBER_DIM, opacity=0.1))
    C += column(6, usb(2, 6, color=SILK), pulse(6, freq=0.3, color=GREEN, opacity=0.1, layer=3, name="Bus Power",
                                                 why="Bus powered: the cable is the supply."),
                label(6, "USB TYPE B\nBUS POWERED\nCLASS COMPLIANT"),
                scope_name="USB")
    C += column(7, keypad(2, 7, nx=3, ny=1, color=SILK_DIM, name="Three Modes",
                          why="Mode 0 generic, Mode 1 Ableton Live, Mode 2 alternate: set by SysEx."),
                pulse(7, freq=0.15, color=GREEN, opacity=0.12, layer=3, name="SysEx",
                      why="F0 47 7F 29 60 00 04 <40|41|42> 00 00 00 F7."),
                label(7, "F0 47 7F 29 60 00 04\n40 | 41 | 42 ... F7\nMODE 0 - 1 - 2"),
                scope_name="SysEx")
    C += column(8, silk(8, amount=4, rot=0.0, layer=2, name="Desk Rules"),
                legend(8, "THE CONTROLLER", size=1.6, name="The Controller",
                       why="What the other decks are played from."),
                label(8, "LEFT = PREVIOUS DECK\nRIGHT = NEXT DECK\nNOTES 97 + 96"),
                light=glow(8, opacity=0.1))
    return {"name": "APC40 mkII", "slug": "apc40", "theme": "the controller",
            "world": ("The controller as an object before it is a protocol: the 424 x 254 x 46 mm chassis, "
                      "40 RGB pads with note 0 bottom-left, nine 45 mm faders, sixteen knobs with LED rings, the "
                      "crossfader, the USB-B socket that also powers it, the three modes set by SysEx, and the two "
                      "buttons this pack is walked with: LEFT and RIGHT, previous and next deck."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#e8e4d8", "why": "Silkscreen, slots, sockets."},
                        {"role": "figure", "hex": "#3ddc84", "why": "A lit pad."},
                        {"role": "light", "hex": "#ffae1a", "why": "Rings and the crossfader."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Panel legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "Unused here; the wire is deck 5's."}],
            "columns": cols,
            "text_corpus": ["AKAI APC40 MKII", "424 x 254 x 46 MM", "40 RGB PADS", "9 x 45 MM FADERS",
                            "16 KNOBS WITH LED RINGS", "CROSSFADER CC15", "USB TYPE B", "MODE 0 - 1 - 2",
                            "LEFT / RIGHT = PREVIOUS / NEXT DECK"],
            "moments": [
                "Column 8 first: read the legend, then press RIGHT once; the V-4 appears. RIGHT again, the MXPro. "
                "LEFT walks back. That is the whole navigation.",
                "Column 5 with the real crossfader: the amber bar on screen follows the lows, your hand follows it.",
                "Column 2, any pad: note 0 lights bottom-left on screen and on the desk at once."],
            "clips": C}


# ================================================================ DECK 2
# EDIROL V-4 - Roland's four-channel mixer with MIDI and beat sync (docs/SOURCES_V-4.md)
def deck2():
    C = []
    cols = ["The Box", "Four Inputs", "A / B Buses", "T-Bar", "Effects", "BPM Sync", "MIDI", "Output Fade"]
    C += column(1, inputs(2, 1, n=4, color=EDIROL, y=0.25, name="Four Inputs (Panel)", why="The four input columns of the panel."),
                legend(1, "EDIROL V-4", size=1.8, name="Edirol V-4", why="The badge."),
                label(1, "EDIROL V-4 - 2002\n225 x 295 x 105 MM\n2.3 KG - NO AUDIO"),
                light=glow(1, color=EDIROL_DIM, opacity=0.1))
    C += column(2, inputs(2, 2, n=4, color=SILK, y=0.3, name="Composite 1-4", why="Four composite inputs on RCA."),
                inputs(3, 2, n=2, color=EDIROL, y=-0.1, name="S-Video 1-2", why="S-Video on inputs 1 and 2, which takes priority."),
                label(2, "4 x COMPOSITE IN\nS-VIDEO ON 1 + 2\n2 FRAME SYNCHRONIZERS"))
    C += column(3, padrow(2, 3, color=SILK_DIM, grid=4, y=0.2, name="Channel A", why="Channel A: input select buttons 1-4."),
                padrow(3, 3, color=GREEN, grid=4, y=-0.2, name="Channel B", why="Channel B: input select buttons 1-4."),
                label(3, "CHANNEL A: 1 2 3 4\nCHANNEL B: 1 2 3 4\nTRANSFORMER = CUT"))
    C += column(4, slot(4, name="T-Bar Slot"), tbar(4, color=AMBER, why="A T-bar of over 100 steps; it mounts horizontal or vertical."),
                label(4, "T-BAR, 100+ STEPS\nMIX - WIPE - EFX\n200+ WIPE PATTERNS"),
                light=glow(4, color=AMBER_DIM, opacity=0.1))
    C += column(5, field(5, color=EDIROL_DIM, opacity=0.5, name="Channel A"),
                strobe(5, freq=0.4, color=SILK, layer=3, opacity=0.2, name="Strobe",
                       why="Channel A's first effect button: Strobe."),
                label(5, "A: STROBE NEGATIVE\nCOLORIZE MULTI\nB: MIRROR - KEYS - PIP"))
    C += column(6, padrow(2, 6, color=SILK_DIM, grid=4, y=0.0, name="Beat Grid", why="Four beats to the bar."),
                pulse(6, freq=0.25, color=GREEN, opacity=0.16, layer=3, name="BPM Sync",
                      why="BPM SYNC switches A and B on the beat without touching the fader."),
                label(6, "TAP - BPM SYNC\nCUTS A/B ON THE BEAT\nF8 CLOCK DRIVES IT"))
    C += column(7, din(2, 7, color=SILK, name="MIDI IN", why="MIDI IN and MIDI OUT on 5-pin DIN; THRU is a soft option."),
                pins5(3, 7, color=RED),
                label(7, "A: NOTES 36 38 40 41\nB: NOTES 43 45 47 48\nCC7 = TRANSITION TIME"),
                aura=wash(7, RED, kind="Radial", opacity=0.05), scope_name="MIDI In", scope_color=RED)
    C += column(8, clip(2, 8, "Fade Ramp", "Gradient",
                        {"Method": "2 Colors", "Color 1": "#000000ff", "Color 2": "#ffffffff", "Mode": "Smooth",
                         "Dither": 0.0, "Type": "Horizontal"}, "Black on the left, white on the right.", opacity=0.6),
                knob(3, 8, color=SILK, size=0.24, name="Output Fade", why="OUTPUT FADE: left to black, right to white."),
                label(8, "OUTPUT FADE\nLEFT: TO BLACK\nRIGHT: TO WHITE"))
    return {"name": "Edirol V-4", "slug": "v4", "theme": "beat sync",
            "world": ("Roland's 2002 four-channel mixer that VJs carried for a decade: four composite inputs, two "
                      "frame synchronizers, an A and a B bus, a T-bar of over 100 steps, more than 200 wipes, eight "
                      "effects, a TAP button and BPM SYNC that cut on the beat from MIDI clock, input select on MIDI "
                      "notes, and no audio at all."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#5b7a99", "why": "Edirol's blue-grey."},
                        {"role": "figure", "hex": "#3ddc84", "why": "The lit bus."},
                        {"role": "light", "hex": "#ffae1a", "why": "The T-bar."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Panel legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "The MIDI wire."}],
            "columns": cols,
            "text_corpus": ["EDIROL V-4", "4 x COMPOSITE IN", "CHANNEL A", "CHANNEL B", "T-BAR", "MIX - WIPE - EFX",
                            "TAP - BPM SYNC", "OUTPUT FADE"],
            "moments": [
                "BPM Sync on the downbeat: tap TAP TEMPO on the APC with the music; the green pulse is the V-4 cutting for you.",
                "T-Bar with the real crossfader, slowly end to end.",
                "MIDI then Output Fade: two columns UP - the wire, then the fade to white."],
            "clips": C}


# ================================================================ DECK 3
# VIDEONICS MXPRO - the 1997 desktop mixer with 501 transitions (docs/SOURCES_MXPRO.md)
def deck3():
    C = []
    cols = ["The Box", "Current / Next", "501", "Shapes", "Keypad + Play", "Input F/X", "Multi-PIP", "Learn"]
    C += column(1, field(1, color=VIDEONICS_DIM, opacity=0.35, name="Beige Case", why="The Videonics beige."),
                legend(1, "MXPRO", size=2.0, name="MXPro", why="The badge."),
                label(1, "VIDEONICS MXPRO 1997\n$1,799 - MODEL MX-3000\nCAMPBELL, CALIFORNIA"),
                light=glow(1, color=VIDEONICS_DIM, opacity=0.08))
    C += column(2, padrow(2, 2, color=SILK_DIM, grid=5, y=0.2, name="Current Row", why="CURRENT: A B C D COLOR."),
                padrow(3, 2, color=GREEN, grid=5, y=-0.2, name="Next Row", why="NEXT: A B C D COLOR; they swap after each transition."),
                label(2, "CURRENT: A B C D COLOR\nNEXT: A B C D COLOR\nTHEY SWAP EACH TAKE"))
    C += column(3, keypad(2, 3, nx=5, ny=1, color=VIDEONICS_DIM, name="Five Categories",
                          why="USER, BASIC, EDGES, TRAILING, SHAPES."),
                legend(3, "501", size=2.4, name="501", why="501 transitions, up from the MX-1's 210."),
                label(3, "501 TRANSITIONS\nUSER BASIC EDGES\nTRAILING SHAPES"))
    C += column(4, field(4, color=SILK_DIM, opacity=0.5, name="Current"),
                window(4, color=GREEN, w=70.0, h=100.0, x=0.0, y=0.0, name="Keyhole",
                       why="A shape wipe: the next source grows inside a shape."),
                label(4, "HEART STAR DIAMOND\nKEYHOLE BINOCULAR\nANTI-ALIASED EDGES"))
    C += column(5, keypad(2, 5, nx=3, ny=4, color=SILK_DIM, name="Keypad", why="Type the transition number."),
                button(3, 5, color=SILK, x=-300, y=0, name="PLAY", lit=True,
                       why="PLAY performs the transition; press it again to wipe back."),
                label(5, "TYPE THE NUMBER\nPRESS PLAY\nSPEED 0-9 - REVERSE"))
    C += column(6, field(6, color=VIDEONICS_DIM, opacity=0.4, name="Source"),
                strobe(6, freq=0.5, color=SILK, layer=3, opacity=0.2, name="Strobe",
                       why="STROBE 0-9, switched off during transitions."),
                label(6, "STROBE 0-9 - MOSAIC\nPOSTERIZE - B&W\nCOLOR NEG - FLIP"))
    C += column(7, clip(2, 7, "Sixteen Tiles", "Checkered",
                        {"Num X": 4, "Num Y": 4, "Color 1": CLEAR, "Color 2": SILK_DIM},
                        "Up to 16 images on one screen.", opacity=0.6),
                window(7, color=GREEN, w=25.0, h=25.0, x=-360.0, y=-200.0, name="Joystick PIP",
                       why="The joystick places a PIP; new since the MX-1."),
                label(7, "UP TO 16 IMAGES\n9 MULTI-PIP LAYOUTS\nJOYSTICK PLACES THEM"))
    C += column(8, padrow(2, 8, color=SILK_DIM, grid=8, y=0.0, name="Eight Memories",
                          why="8 learned environments survive power-off."),
                pulse(8, freq=0.15, color=GREEN, opacity=0.12, layer=3, name="GPI Pulse",
                      why="A GPI pulse on the mini-jack acts exactly as PLAY."),
                label(8, "LEARN: 250 STEPS\nGPI PULSE = PLAY\n8 MEMORIES SURVIVE"))
    return {"name": "Videonics MXPro", "slug": "mxpro", "theme": "the keypad",
            "world": ("The 1997 upgrade to the MX-1, built in Campbell, California: four inputs with audio, a CURRENT "
                      "row and a NEXT row instead of A/B buses, 501 transitions in five categories including hearts, "
                      "stars and keyholes, a keypad to type them by number, PLAY instead of the slack T-bar, input "
                      "effects, a 16-image multi-PIP placed by joystick, and LEARN scripts of 250 steps."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#d8cfb8", "why": "The Videonics beige."},
                        {"role": "figure", "hex": "#3ddc84", "why": "The NEXT source."},
                        {"role": "light", "hex": "#ffae1a", "why": "Unused but for the glow."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Panel legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "Unused."}],
            "columns": cols,
            "text_corpus": ["VIDEONICS MXPRO", "CURRENT", "NEXT", "501 TRANSITIONS", "SHAPES", "PLAY", "STROBE",
                            "MULTI-PIP", "LEARN"],
            "moments": [
                "501 then Shapes on consecutive downbeats: the number, then the keyhole.",
                "Keypad + Play: press the APC's PLAY as the MXPro's PLAY.",
                "Learn last, then RIGHT: from the MXPro back to where it started, the MX-1."],
            "clips": C}


# ================================================================ DECK 4
# VIDEONICS MX-1 - the 1994 original (docs/SOURCES_MX-1.md)
def deck4():
    C = []
    cols = ["The Original", "Take-Bar", "Numbered", "Quad Preview", "Film Look", "Chroma Key", "Freeze", "The Club"]
    C += column(1, field(1, color=VIDEONICS_DIM, opacity=0.3, name="Beige Case", why="The Videonics beige."),
                legend(1, "MX-1", size=2.4, name="MX-1", why="The badge."),
                label(1, "VIDEONICS MX-1 1994\n4 INPUTS - DUAL TBC\n300 x 165 x 99 MM"),
                light=glow(1, color=VIDEONICS_DIM, opacity=0.08))
    C += column(2, slot(2, name="Take-Bar Slot"), tbar(2, color=AMBER, name="Take-Bar",
                                                       why="'T-bar' is short for 'Take-bar'; start it from either end."),
                label(2, "T-BAR = TAKE-BAR\nSTART FROM EITHER END\n10 SPEEDS: 0-9"),
                light=glow(2, color=AMBER_DIM, opacity=0.1))
    C += column(3, keypad(2, 3, nx=3, ny=4, color=SILK_DIM, name="Keypad", why="Every effect has a number."),
                legend(3, "0-239", size=2.0, name="0-239", why="210 effects, numbered 0 to 239."),
                label(3, "EFFECT 0 = CUT\n1 = DISSOLVE\n212 = BUTTERFLY"))
    C += column(4, clip(2, 4, "Four Thumbnails", "Checkered",
                        {"Num X": 2, "Num Y": 2, "Color 1": SILK_DIM, "Color 2": VIDEONICS_DIM},
                        "Preview: all four inputs live at once.", opacity=0.5),
                window(4, color=GREEN, w=50.0, h=50.0, x=-480.0, y=-270.0, name="Input A",
                       why="Input A's live thumbnail, lit."),
                label(4, "PREVIEW: ALL FOUR\nINPUTS LIVE AT ONCE\nPLUS THE EFFECT LIST"))
    C += column(5, field(5, color=VIDEONICS_DIM, opacity=0.4, name="Source"),
                strobe(5, freq=0.12, color=SILK, layer=3, opacity=0.18, name="Film Look",
                       why="Strobe setting 1 is the 'film look'."),
                label(5, "STROBE 0-7\n1 = FILM LOOK\n2 = OLD MOVIE"))
    C += column(6, field(6, color=GREEN_DIM, opacity=0.5, name="Background"),
                window(6, color=SILK, w=90.0, h=90.0, x=0.0, y=0.0, name="Keyed Source",
                       why="Chroma key: pick the colour with an on-screen cursor."),
                label(6, "CHROMA KEY: PICK THE\nCOLOUR WITH A CURSOR\nLUMA KEY: 237 + 238"))
    C += column(7, freeze(7, layer=2), button(3, 7, color=SILK, x=300, y=0, name="FREEZE", lit=True,
                                               why="FREEZE captures a field."),
                label(7, "FREEZE ONE FIELD\nSHIFT+FREEZE =\nSTOP-MOTION SNAPSHOTS"))
    C += column(8, half(8, color=VIDEONICS_DIM, layer=2, x=-480.0, name="Music Video", why="Source A: a music video."),
                half(8, color=GREEN_DIM, layer=3, x=480.0, name="Dance Floor Camera",
                     why="Source B: 'a camera aimed at the dance floor' - the manual's own example."),
                label(8, "A: THE MUSIC VIDEO\nB: A CAMERA ON\nTHE DANCE FLOOR"))
    return {"name": "Videonics MX-1", "slug": "mx1", "theme": "the original",
            "world": ("The 1994 four-input mixer from Campbell, California that put a frame synchronizer, dual TBC, "
                      "210 numbered effects and a Take-bar on a desk for about a thousand dollars; the manual's own "
                      "example is a nightclub, a music video on one input and a camera on the dance floor on the other."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#d8cfb8", "why": "The Videonics beige."},
                        {"role": "figure", "hex": "#3ddc84", "why": "The lit source."},
                        {"role": "light", "hex": "#ffae1a", "why": "The Take-bar."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Panel legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "Unused."}],
            "columns": cols,
            "text_corpus": ["VIDEONICS MX-1", "TAKE-BAR", "EFFECT 0 = CUT", "PREVIEW", "FILM LOOK", "CHROMA KEY",
                            "FREEZE", "THE DANCE FLOOR"],
            "moments": [
                "Take-Bar with the real crossfader: the gesture the whole pack is built on, from 1994.",
                "Film Look under a slow track: the strobe at setting 1.",
                "The Club last: the manual's own nightclub, on the APC that replaced it."],
            "clips": C}


# ================================================================ DECK 6
# JVC - an S-VHS deck with jog/shuttle on its face, and a pro edit controller it never met
# (docs/SOURCES_JVC.md)
VIDEO_BLUE = "#3a6fd8ff"


def deck5():
    C = []
    cols = ["The Deck", "Jog", "Shuttle", "Heads", "TBC + 3-DNR", "S-VHS ET", "RM-G850E", "Perform"]
    C += column(1, silk(1, amount=3, rot=0.0, layer=2, name="Tape Path", why="The tray and the transport."),
                legend(1, "S-VHS", size=2.2, name="S-VHS", why="The format badge on the tray door."),
                label(1, "JVC HR-S7600U - 1999\nS-VHS HI-FI - $449.95\n437 x 97 x 347 MM"))
    C += column(2, knob(2, 2, color=SILK, size=0.34, name="Jog Dial", why="The JOG dial, on the front panel."),
                pulse(2, freq=0.3, color=GREEN, opacity=0.12, layer=3, name="Frame Step",
                      why="One click, one frame: right forward, left back."),
                label(2, "JOG DIAL\nRIGHT: FRAME FORWARD\nLEFT: FRAME BACK"))
    C += column(3, knob(2, 3, color=SILK, size=0.4, name="Shuttle Ring", ring=True,
                        why="The TIME SCAN SHUTTLE ring around the jog dial."),
                fader(3, 3, color=AMBER, position=0.5, rot=0.0, width=0.02, name="Scan Lines",
                      fft_=fft("Position", "mid", 0.1, 0.9, 9.0, 500), why="The picture scanning at speed."),
                label(3, "SHUTTLE RING\nTIME SCAN TO 7x\nIT STAYS WHERE IT SITS"),
                light=glow(3, color=AMBER_DIM, opacity=0.1))
    C += column(4, clip(2, 4, "Head Drum", "Rings",
                        {"Num Rings": 3, "Size": 0.35, "Spacing": 0.25, "Line Width": 0.02, "Style": "Stroke",
                         "Gap": 30.0, "Rotation": 0.0, "Rotation Step": 120.0, "Rotation Alternate": False,
                         "Color 1": SILK, "Color 2": SILK_DIM},
                        "The spinning head drum.", opacity=0.85, fft=fft("Rotation", "low", 0.0, 180.0, 6.0, 900)),
                inputs(3, 4, n=6, color=GREEN, y=0.0, name="Six Heads", why="4 video heads and 2 hi-fi audio heads."),
                label(4, "DA-4 HEAD SYSTEM\n4 VIDEO + 2 HI-FI\n400 LINES IN S-VHS"))
    C += column(5, clip(2, 5, "Jitter", "Lines",
                        {"Fuzzyness": 0.4, "Amount": 30, "Width": 0.01, "Rotation": 0.0, "Position": 0.5,
                         "Color": SILK_DIM}, "Unstable tape lines before correction.", opacity=0.4,
                        fft=fft("Fuzzyness", "high", 0.2, 0.8, 9.0, 300)),
                silk(5, amount=30, rot=0.0, layer=3, color=SILK, name="Corrected Lines", opacity=0.5,
                     why="The same lines after the time base corrector."),
                label(5, "DIGITAL TBC + 3-DNR\n2 MB FRAME MEMORY\nUSE IT TO EDIT"))
    C += column(6, field(6, color=SILK_DIM, opacity=0.4, name="VHS Tape", why="A plain VHS cassette."),
                legend(6, "ET", size=2.6, name="ET", why="The S-VHS ET button, lit."),
                label(6, "S-VHS ET\nS-VHS PICTURE ON\nPLAIN VHS TAPE"))
    C += column(7, knob(2, 7, color=SILK, size=0.24, name="Player Dial", effects=[xform(x=-420, y=0)],
                        why="RM-G850E: the PLAYER search dial."),
                knob(3, 7, color=SILK, size=0.24, name="Recorder Dial", effects=[xform(x=420, y=0)],
                     why="RM-G850E: the RECORDER search dial."),
                label(7, "JVC RM-G850E\nPRO EDIT CONTROLLER\nPLAYER + RECORDER"))
    C += column(8, clip(2, 8, "Edit Keys", "Checkered",
                        {"Num X": 4, "Num Y": 1, "Color 1": AMBER, "Color 2": VIDEO_BLUE},
                        "Colour-coded edit keys: ASSEM orange, AUDIO green, VIDEO blue.", opacity=0.5),
                button(3, 8, color=RED, x=0, y=-200, name="PERFORM",
                       why="The red PERFORM key between PREVIEW and REVIEW."),
                label(8, "PREVIEW - PERFORM\nREVIEW - GO TO\nIT DROVE U-MATIC"),
                aura=wash(8, RED, kind="Radial", opacity=0.05))
    return {"name": "JVC S-VHS + Edit", "slug": "jvc", "theme": "the tape",
            "world": ("Two JVC machines that never worked together: the 1999 HR-S7600U S-VHS deck, with its jog dial "
                      "and shuttle ring on the front panel, DA-4 heads, digital TBC with 3-DNR and S-VHS ET; and the "
                      "RM-G850E, a wired professional edit controller with a player dial, a recorder dial and a red "
                      "PERFORM key, built to drive JVC's U-matic editing decks."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "The black deck."},
                        {"role": "body", "hex": "#e8e4d8", "why": "Dials, heads, tape lines."},
                        {"role": "figure", "hex": "#3ddc84", "why": "A frame stepped."},
                        {"role": "light", "hex": "#ffae1a", "why": "TIME SCAN and the ASSEM key."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "PERFORM."}],
            "columns": cols,
            "text_corpus": ["JVC HR-S7600U", "S-VHS", "JOG DIAL", "SHUTTLE RING", "DA-4", "DIGITAL TBC", "S-VHS ET",
                            "JVC RM-G850E", "PREVIEW - PERFORM"],
            "moments": [
                "Jog then Shuttle under a breakdown: one frame, then seven times speed.",
                "Heads on a heavy kick: the drum turns with the lows.",
                "Perform last: the red key, then RIGHT to the Patch Bay."],
            "clips": C}


# ================================================================ DECK 6
# PATCH BAY - how the other decks talk to each other
def deck6():
    C = []
    cols = ["Four Into Eight", "T-Bar / Crossfader", "Composite / USB", "Dissolve",
            "Wipe", "Key", "Freeze", "The Shared Words"]
    C += column(1, inputs(2, 1, n=4, color=SILK, y=0.3, name="Four Inputs", why="A mixer has four inputs."),
                padrow(3, 1, color=GREEN, grid=8, y=-0.2, name="Eight Layers", why="Resolume has eight layers here."),
                label(1, "MIXER: 4 IN, 1 OUT\nTHIS PACK: 8 LAYERS\nSAME IDEA, MORE BUSES"))
    C += column(2, slot(2, rot=0.0, name="Slot"), tbar(2, color=AMBER, name="T-Bar = Crossfader",
                                                       why="The mixer's T-bar and the APC's crossfader are the same gesture."),
                label(2, "MIXER: THE T-BAR\nAPC: CROSSFADER CC15\nONE HAND, ONE MOVE"),
                light=glow(2, color=AMBER_DIM, opacity=0.1))
    C += column(3, din(2, 3, color=SILK, name="BNC / RCA", why="Composite video on a coax: one wire, one picture."),
                usb(3, 3, color=SILK, why="USB: one wire, every message."),
                label(3, "COMPOSITE: 1 PICTURE\nUSB: EVERY MESSAGE\nMIDI DIN: 31,250 BAUD"),
                aura=wash(3, RED, kind="Radial", opacity=0.05), scope_name="Wire", scope_color=RED)
    C += column(4, field(4, color=SILK_DIM, opacity=0.5, name="Source A"),
                clip(3, 4, "Source B", "Solid Color", {"Color": GREEN_DIM}, "Input B dissolving in.", opacity=0.5),
                label(4, "DISSOLVE\nA OUT AS B COMES IN\nTHE FIRST MOVE"))
    C += column(5, field(5, color=SILK_DIM, opacity=0.6), wipe(5, color=GREEN, name="Wipe Edge"),
                label(5, "WIPE\nAN EDGE CROSSES\nB REVEALED BEHIND A"))
    C += column(6, field(6, color=GREEN_DIM, opacity=0.6, name="Background"), window(6, color=SILK, name="Keyed Window",
                                                                                  why="A luma or chroma key: one picture cut into another."),
                label(6, "KEY\nLUMA: BY BRIGHTNESS\nCHROMA: BY COLOUR"))
    C += column(7, freeze(7, layer=2), strobe(7, freq=0.5, color=SILK, layer=3, opacity=0.18),
                label(7, "FREEZE - STROBE\nONE FIELD HELD\nDROPPED ON THE BEAT"),
                light=glow(7, opacity=0.06))
    C += column(8, silk(8, amount=6, rot=0.0, layer=2, name="Rules"),
                legend(8, "MIX", size=2.0, name="Mix", why="The one verb every box here shares."),
                label(8, "MIX WIPE KEY FREEZE\nTHE SAME FOUR WORDS\nEVERY BOX SPEAKS IT"),
                light=glow(8, opacity=0.1))
    return {"name": "Patch Bay", "slug": "patchbay", "theme": "how they talk",
            "world": ("The deck that joins the others: a mixer's four inputs beside Resolume's eight layers, "
                      "the T-bar beside the crossfader, a composite wire beside a USB cable, and the four verbs every "
                      "box here shares: dissolve, wipe, key, freeze."),
            "palette": [{"role": "bed", "hex": "#0f1012", "why": "Chassis."},
                        {"role": "body", "hex": "#e8e4d8", "why": "Inputs, slots, sockets."},
                        {"role": "figure", "hex": "#3ddc84", "why": "The lit side of every comparison."},
                        {"role": "light", "hex": "#ffae1a", "why": "The T-bar / crossfader."},
                        {"role": "text", "hex": "#e8e4d8", "why": "Legends."},
                        {"role": "aura", "hex": "#e03a2f", "why": "The wire."}],
            "columns": cols,
            "text_corpus": ["4 INPUTS, 1 OUT", "8 LAYERS, 1 OUT", "T-BAR = CROSSFADER", "COMPOSITE", "USB",
                            "DISSOLVE", "WIPE", "KEY", "FREEZE", "MIX"],
            "moments": [
                "Column 2 and the real crossfader: the gesture every mixer here was built around.",
                "Walk columns 4 to 7 UP on consecutive downbeats: dissolve, wipe, key, freeze - the grammar.",
                "Column 8 last, then LEFT four times back to the APC40 deck: the loop closes."],
            "clips": C}


def write(decks, bible_extra):
    bible = {"pack_name": "The Mixers", "comp_name": "The Mixers - V-4, MXPro, MX-1 + JVC",
             "tagline": "Three mixers, a VCR, an edit controller and the APC40. LEFT and RIGHT walk between them.",
             "decks": [{k: v for k, v in d.items() if k != "clips"} for d in decks]}
    bible.update(bible_extra)
    with open(os.path.join(HERE, "bible.json"), "w", encoding="utf-8") as f:
        json.dump(bible, f, indent=1, ensure_ascii=False)
    with open(os.path.join(HERE, "decks.json"), "w", encoding="utf-8") as f:
        json.dump({"decks": [{"deck": d["name"], "clips": d["clips"]} for d in decks]},
                  f, indent=1, ensure_ascii=False)
    print("bible: %d decks; clips: %d" % (len(decks), sum(len(d["clips"]) for d in decks)))
    for d in decks:
        cells = [(c["layer"], c["column"]) for c in d["clips"]]
        missing = [(l, c) for l in range(1, 9) for c in range(1, 9) if (l, c) not in cells]
        dup = sorted({x for x in cells if cells.count(x) > 1})
        if missing or dup:
            print("  %s: missing %s dup %s" % (d["name"], missing, dup))


def main():
    decks = [deck1(), deck2(), deck3(), deck4(), deck5(), deck6()]
    write(decks, {
        "effect_wishlist": [
            {"effect": "Bloom", "role": "Bank A: LED bleed and phosphor glow."},
            {"effect": "Trails", "role": "Bank A: the T-bar's travel and the shuttle's scan."},
            {"effect": "Mirror Quad", "role": "Bank D: the multi-PIP tiles."},
            {"effect": "CRT", "role": "Bank C: the program monitor every mixer fed."},
            {"effect": "Grid Cloner", "role": "Bank D: the quad preview."}],
        "fft_philosophy": (
            "The hardware is the subject and the music is what it plays, so the reactivity stays mechanical: lows "
            "push T-bars and turn the head drum, mids move wipe edges and the shuttle's scan, highs only jitter "
            "uncorrected tape lines and the MIDI pins. Colour never reacts. Text never moves. Every number on screen "
            "is from the sources in docs/."),
        "wildcard_rationale": (
            "Six decks, walked with the APC40's LEFT and RIGHT buttons: the controller itself, three video mixers "
            "(Edirol V-4, Videonics MXPro, Videonics MX-1), a JVC S-VHS deck beside a JVC pro edit controller it "
            "never met, and a patch bay of the words they share.")})


if __name__ == "__main__":
    main()
