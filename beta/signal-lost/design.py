#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py - SIGNAL LOST, a stock-only Avenue 7.28.1 instrument drawn from the
performer's own ComfyUI-OldTimeRadio pipeline: a radio drama written from
tonight's news, cast in neural voices, scored, filtered to a 1940s bandpass,
drawn in storybook engravings and cut to an .mp4 with burned captions and a
credit roll. "Good evening. This is SIGNAL LOST."

Palette: midnight bakelite, dial amber, cream paper, magic-eye green, one
ON AIR red. Register: Rockwell for the station, Courier for the script's cue
markup ([SFX:] [MUSIC:] [BEAT] [PAUSE] [ACT]), Bahnschrift for burned captions.

    python packs/signal-lost/design.py      -> bible.json + decks.json
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

NIGHT = "#0b0a14ff"
NIGHT2 = "#1c1826ff"
AMBER = "#ffb347ff"
AMBER_DIM = "#ffb34766"
CREAM = "#f4e9c8ff"
CREAM_DIM = "#f4e9c866"
GREEN = "#7fd37fff"
GREEN_DIM = "#7fd37f66"
RED = "#e0432aff"
CLEAR = "#00000000"

STATION = "Rockwell"
SCRIPT = "Courier New"
CAPTION = "Bahnschrift"


# ---------------------------------------------------------------- helpers
def bakelite(col, why="Midnight bakelite: the set's cabinet."):
    return clip(1, col, "Bakelite", "Solid Color", {"Color": NIGHT}, why)


def ruling(col, amount=18, rot=0.0, color=NIGHT2, opacity=1.0, name="Script Ruling",
           why="Ruled script paper, barely lifted from the night."):
    return clip(1, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": amount, "Width": 0.012, "Rotation": rot,
                 "Position": 0.5, "Color": color}, why, opacity=opacity)


def glow(col, color=AMBER_DIM, opacity=0.3, name="Dial Glow", layer=4,
         why="The dial lamp's radial glow."):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": color, "Color 2": CLEAR,
                 "Mode": "Smooth", "Dither": 0.0, "Type": "Radial"}, why, opacity=opacity)


def wash(col, color, kind="Vertical", opacity=0.1, name="Wash", layer=6):
    return clip(layer, col, name, "Gradient",
                {"Method": "2 Colors", "Color 1": CLEAR, "Color 2": color,
                 "Mode": "Smooth", "Dither": 0.0, "Type": kind},
                "A tone across the frame.", opacity=opacity)


def dial(layer, col, color=CREAM, rings=1, size=0.8, width=0.015, name="Tuning Dial",
         opacity=0.9, effects=None, fft_=None,
         why="The round tuning dial of a cathedral radio."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": rings, "Size": size, "Spacing": 0.12, "Line Width": width,
                 "Style": "Stroke", "Gap": 0.0, "Rotation": 0.0, "Rotation Step": 0.0,
                 "Rotation Alternate": False, "Color 1": color, "Color 2": color},
                why, opacity=opacity, effects=effects,
                fft=fft_ if fft_ is not None else fft("Line Width", "low", width, width * 2.5, 8.0, 450))


def needle(layer, col, color=AMBER, rot=72.0, name="Dial Needle",
           why="The station needle across the band."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.01, "Rotation": rot,
                 "Position": 0.5, "Color": color}, why,
                fft=fft("Rotation", "mid", rot - 6, rot + 6, 7.0, 900))


def band(layer, col, color=CREAM_DIM, amount=30, name="Station Band", opacity=0.8,
         why="The tuning band: kilocycle ticks along the glass."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.05, "Amount": amount, "Width": 0.02, "Rotation": 90.0,
                 "Position": 0.5, "Color": color}, why, opacity=opacity,
                fft=fft("Fuzzyness", "high", 0.02, 0.3, 8.0, 250))


def carrier(layer, col, color=GREEN, waves=6, amp=0.1, position=0.5, speed=3.0, width=0.015,
            name="Carrier", opacity=0.9, why="The carrier wave: a steady sine until a voice rides it."):
    return clip(layer, col, name, "Sine Wave",
                {"Waves": waves, "Mode": "Line", "Line Width": width, "Fuzzyness": 0.05,
                 "Direction": "Horizontal", "Mirror": True, "Frequency": 2.0, "Main Speed": speed,
                 "Modulator": 1.0, "Modulation Depth": 0.4, "Modulator Speed": 1.0,
                 "Amplitude": amp, "Position": position, "Color": color, "BG Color": CLEAR},
                why, opacity=opacity, fft=fft("Amplitude", "mid", amp, min(1.0, amp + 0.3), 10.0, 300))


def magic_eye(layer, col, color=GREEN, size=0.22, name="Magic Eye",
              why="The 6E5 tuning-eye tube: a green fan that closes on a strong signal."):
    return clip(layer, col, name, "Rings",
                {"Num Rings": 1, "Size": size, "Spacing": 0.1, "Line Width": 0.2,
                 "Style": "Fill", "Gap": 60.0, "Rotation": 90.0, "Rotation Step": 0.0,
                 "Rotation Alternate": False, "Color 1": color, "Color 2": color},
                why, opacity=0.9, fft=fft("Gap", "mid", 10.0, 120.0, 10.0, 300))


def on_air(col, opacity=0.9, name="ON AIR", layer=4,
           why="The ON AIR lamp: the one red in the pack."):
    return clip(layer, col, name, "Stroboscope",
                {"Frequency": 0.02, "Fade": True, "Color 1": RED, "Color 2": CLEAR},
                why, opacity=opacity)


def crackle(col, opacity=0.08, name="Shellac Crackle",
            why="Surface noise: the vintage filter's crackle bed."):
    return clip(7, col, name, "Static", {"Mode": "Grayscale"}, why, opacity=opacity)


def blank(layer, col, why="Nothing by design."):
    return clip(layer, col, "Blank", "Blank", {"Black BG": False}, why)


def text(col, s, color=CREAM, size=0.9, font=SCRIPT, align="Left", valign="Bottom",
         x=-860, y=460, name=None, layer=5, animated=False,
         why="Typed cue markup from the script, Courier, bottom-left."):
    return L.text(col, s, color=color, size=size, font=font, align=align, valign=valign,
                  x=x, y=y, name=name, layer=layer, animated=animated, why=why)


def caption(col, s, color=CREAM, size=1.0, name=None,
            why="A burned caption, centred at the bottom, speaker-labelled."):
    return text(col, s, color=color, size=size, font=CAPTION, align="Center", valign="Bottom",
                x=0, y=460, name=name, why=why)


def vu(col, color=AMBER, amp=0.06, name="VU Line",
       why="The program line: the honest readout of whatever is on air."):
    return L.scope(col, color=color, position=0.88, amplitude=amp, name=name, why=why)


def waveform(col, color=GREEN, amp=0.12, name="Waveform",
             why="The 48 kHz master's waveform along the bottom."):
    return L.scope(col, color=color, position=0.86, amplitude=amp, waves=3, speed=4.0, name=name, why=why)


def tube(layer, col, color=AMBER, grid=4, size=0.1, name="Tube Filaments",
         why="Valve filaments glowing in the chassis."):
    return clip(layer, col, name, "Metaballs",
                {"Grid": grid, "Blend": "Minimal", "Size": size, "Distance": 0.6, "Radius": 0.3,
                 "Fuzzyness": 0.5, "Speed": 0.15, "Position X": 0.0, "Position Y": 0.0,
                 "Color": color, "BG Color": CLEAR}, why, opacity=0.8,
                fft=fft("Size", "low", size, size + 0.1, 8.0, 500))


def engraving(layer, col, color=CREAM, opacity=0.5, name="Engraving Hatch", rot=35.0,
              why="Storybook-engraving hatching: the stills are drawn, not photographed."):
    return clip(layer, col, name, "Lines",
                {"Fuzzyness": 0.15, "Amount": 70, "Width": 0.008, "Rotation": rot,
                 "Position": 0.5, "Color": color}, why, opacity=opacity,
                fft=fft("Fuzzyness", "high", 0.1, 0.4, 7.0, 300))


def node_box(layer, col, color=AMBER, name="Node", lines=8, shape="Square", opacity=0.85,
             why="A ComfyUI node: a rounded box with sockets."):
    return clip(layer, col, name, "Geometry Pattern Maker",
                {"Bloom": 0.08, "Bloom Mode": "Add", "Shape Types": shape, "Shape Rounding": 0.3,
                 "Line Ammount": lines, "Innter Color 1": color, "Inner color 2": NIGHT2,
                 "Outer Color 1": CREAM_DIM, "Outer Color 2": NIGHT2, "Inner Scale": 0.3,
                 "Outer Scale": 1.3, "Intersect Scale": 0.5}, why, opacity=opacity,
                fft=fft("Inner Scale", "low", 0.28, 0.4, 8.0, 400))


def wires(layer, col, color=AMBER_DIM, name="Graph Wires", opacity=0.7,
          why="The workflow's wires, bezier-ish, from node to node."):
    return clip(layer, col, name, "Line Scape",
                {"Tilt": 0.0, "Direction": 0.0, "Position Y": 2.0, "Speed": 0.3, "Height": 6.0,
                 "Jagginess": 0.0, "Wobble": 0.3, "Attenuation": 80.0, "Line Width": 0.25,
                 "Fuzzyness": 0.0, "Color": color, "Show Knots": True}, why, opacity=opacity,
                fft=fft("Wobble", "mid", 0.2, 0.6, 7.0, 700))


def ticker(layer, col, s, color=CREAM, name=None,
           why="Tonight's headline on the RSS ticker, typed on."):
    return L.text(col, s, color=color, size=0.8, font=SCRIPT, align="Left", valign="Top",
                  x=-860, y=-460, animated=True, delay=50, layer=layer, name=name, why=why)


# ================================================================ DECK 1
# SIGN-ON - the set warms up; tonight's news; "Good evening. This is SIGNAL LOST."
def deck1():
    C = []
    cols = ["Warm Up", "Tuning", "Lock", "Tonight's News",
            "Theme", "Good Evening", "Act One", "Station Break"]
    C += [bakelite(1), tube(2, 1, size=0.06, name="Cold Filaments"),
          dial(3, 1, color=CREAM_DIM, size=0.8, width=0.01, fft_={}, name="Dark Dial"),
          glow(1, opacity=0.08, name="Filament Glow"),
          text(1, "[WARM UP]", size=1.0),
          blank(6, 1), crackle(1, opacity=0.1), vu(1, amp=0.02)]
    C += [bakelite(2), dial(2, 2, size=0.8), band(3, 2),
          glow(2, opacity=0.3),
          text(2, "[TUNING]\n540 - 1600 KC", size=0.9),
          blank(6, 2), crackle(2, opacity=0.12),
          carrier(8, 2, color=GREEN_DIM, waves=12, amp=0.04, position=0.86, speed=6.0,
                  name="Between Stations", why="Hiss between stations.")]
    C += [bakelite(3), dial(2, 3, size=0.8), needle(3, 3),
          glow(3, opacity=0.34),
          text(3, "SIGNAL LOST\n1230 KC", font=STATION, size=1.1, color=AMBER,
               why="The station found on the dial."),
          wash(3, AMBER_DIM, kind="Radial", opacity=0.08), crackle(3, opacity=0.06),
          carrier(8, 3, position=0.86, amp=0.06, name="Carrier Locked")]
    C += [ruling(4, amount=24), wires(2, 4, color=CREAM_DIM, opacity=0.4, name="Feed Lines"),
          node_box(3, 4, color=AMBER, name="RSS Reader", shape="Square"),
          glow(4, opacity=0.2),
          ticker(5, 4, "SCIENCE DAILY: TONIGHT'S\nHEADLINE SEEDS THE SCRIPT", name="News Ticker"),
          blank(6, 4), crackle(4, opacity=0.05), vu(4, amp=0.04)]
    C += [bakelite(5), magic_eye(2, 5, size=0.3, name="Magic Eye Wide"),
          carrier(3, 5, color=AMBER, waves=4, amp=0.18, position=0.5, speed=2.0, name="Theme Swell",
                  why="The theme, composed in the musical style of wherever the story came from."),
          glow(5, color=GREEN_DIM, opacity=0.26, name="Eye Glow"),
          text(5, "[MUSIC: THEME]", size=1.0),
          wash(5, GREEN_DIM, kind="Radial", opacity=0.08), crackle(5, opacity=0.06),
          waveform(5)]
    C += [bakelite(6), dial(2, 6, size=0.8, opacity=0.5), magic_eye(3, 6, size=0.22),
          on_air(6),
          caption(6, "ANNOUNCER: GOOD EVENING.\nTHIS IS SIGNAL LOST.", size=1.1,
                  why="The line every episode opens with, burned in and speaker-labelled."),
          wash(6, AMBER_DIM, kind="Vertical", opacity=0.1), crackle(6, opacity=0.06),
          vu(6, amp=0.1)]
    C += [ruling(7), engraving(2, 7, opacity=0.3, name="Act Card Hatch"),
          node_box(3, 7, color=CREAM, name="Act Card", shape="Square", lines=6),
          glow(7, opacity=0.18),
          text(7, "[ACT 1]", font=STATION, size=2.0, align="Center", valign="Center", x=0, y=0,
               animated=True, why="The act card."),
          blank(6, 7), crackle(7, opacity=0.08), vu(7, amp=0.05)]
    C += [bakelite(8), dial(2, 8, size=0.8, opacity=0.6), needle(3, 8, rot=72.0),
          glow(8, opacity=0.24),
          caption(8, "ANNOUNCER: WE PAUSE FOR\nSTATION IDENTIFICATION", size=0.9),
          blank(6, 8), crackle(8, opacity=0.1),
          carrier(8, 8, color=GREEN_DIM, waves=12, amp=0.03, position=0.86, speed=6.0, name="Idle Carrier")]
    return {"name": "Sign-On", "slug": "sign-on", "theme": "radio",
            "world": ("A cathedral radio warming up in a dark room: cold filaments, then the dial lamp, "
                      "the band of kilocycle ticks, the needle hunting and locking on 1230, the magic-eye "
                      "tube closing on a strong signal. Tonight's headline comes off the RSS feed and seeds "
                      "the script; the theme swells; the ON AIR lamp lights; and the announcer says the only "
                      "line every episode shares. Midnight bakelite, dial amber, cream paper, magic-eye "
                      "green, one red lamp."),
            "palette": [{"role": "bed", "hex": "#0b0a14", "why": "Midnight bakelite."},
                        {"role": "body", "hex": "#f4e9c8", "why": "Cream dial glass and script paper."},
                        {"role": "figure", "hex": "#ffb347", "why": "Dial amber: needle, filaments, nodes."},
                        {"role": "light", "hex": "#7fd37f", "why": "Magic-eye green for signal; the ON AIR lamp is the one red."},
                        {"role": "text", "hex": "#f4e9c8", "why": "Cue markup in Courier; captions in Bahnschrift."},
                        {"role": "aura", "hex": "#ffb347", "why": "Amber radials only."}],
            "columns": cols,
            "text_corpus": ["GOOD EVENING. THIS IS SIGNAL LOST.", "[WARM UP]", "[TUNING]", "1230 KC",
                            "[MUSIC: THEME]", "[ACT 1]", "STATION IDENTIFICATION", "TONIGHT'S HEADLINE",
                            "TRANSMISSION FROM TOMORROW", "ANNOUNCER", "ON AIR", "[PAUSE]"],
            "moments": [
                "Warm up to lock: Scene Launch 1 with every fader low, walk UP one column per bar while raising "
                "fader 4 (LIGHT) so the dial lamp comes up with the filaments; the needle locks on column 3.",
                "Good evening: Scene Launch 6 on the downbeat, tap the row-5 TEXT pad so the caption retypes, "
                "and leave the ON AIR lamp on its own slow pulse. Do not touch an effect for a phrase.",
                "Act one: UP to column 7, bank-C knob to a third with CRT lit so the act card reads as a title "
                "card on a print; drop it to zero on the first line of dialogue."],
            "clips": C}


# ================================================================ DECK 2
# THE WRITERS' ROOM - LedgerScriptWriter -> FreezeCascade: premise, cast, cues, freeze
def deck2():
    C = []
    cols = ["Premise", "Characters", "Plot", "Setting",
            "Cue Markup", "Beat", "Freeze Cascade", "Ledger Locked"]
    C += [ruling(1), node_box(2, 1, color=AMBER, name="ScriptWriter", lines=10),
          wires(3, 1, opacity=0.5),
          glow(1, opacity=0.14),
          text(1, "OTR_LedgerScriptWriter\nsource_bank: my_story\ncustom_premise:", size=0.8,
               why="The node and its three widgets, as typed in the workflow."),
          blank(6, 1), crackle(1, opacity=0.05), vu(1, amp=0.03)]
    C += [ruling(2), tube(2, 2, color=CREAM, grid=3, size=0.12, name="Three Voices",
                          why="story_characters: three silhouettes as soft discs."),
          engraving(3, 2, opacity=0.25),
          glow(2, opacity=0.14),
          text(2, "story_characters:\nTHE ARCHIVIST\nTHE APPRENTICE", size=0.8),
          blank(6, 2), crackle(2, opacity=0.05), vu(2, amp=0.03)]
    C += [ruling(3, amount=12),
          clip(2, 3, "Plot Line", "Line Scape",
               {"Tilt": 20.0, "Direction": 0.0, "Position Y": 4.0, "Speed": 0.4, "Height": 10.0,
                "Jagginess": 0.4, "Wobble": 0.1, "Attenuation": 60.0, "Line Width": 0.3,
                "Fuzzyness": 0.0, "Color": AMBER, "Show Knots": True},
               "story_plot: a rising line with knots at the turns.", opacity=0.8,
               fft=fft("Jagginess", "low", 0.3, 0.8, 8.0, 500)),
          blank(3, 3, "The plot line is the figure."),
          glow(3, opacity=0.12),
          text(3, "story_plot:\nONE NIGHT IN THE LAB\nRACING VINEGAR SYNDROME", size=0.8),
          blank(6, 3), crackle(3, opacity=0.05), vu(3, amp=0.03)]
    C += [ruling(4, amount=30, rot=90.0, name="Shelving"),
          engraving(2, 4, opacity=0.4, rot=0.0, name="Lab Shelves"),
          node_box(3, 4, color=CREAM_DIM, name="Setting Card", lines=6, opacity=0.6),
          glow(4, opacity=0.16),
          text(4, "story_setting:\nA FILM LAB, AFTER HOURS\nDEVELOPING TANKS", size=0.8),
          blank(6, 4), crackle(4, opacity=0.06), vu(4, amp=0.03)]
    C += [ruling(5), blank(2, 5, "The markup is the picture."),
          blank(3, 5, "The markup is the picture."),
          glow(5, opacity=0.1),
          text(5, "[SFX: TANK LID]\n[MUSIC: STING]\n[BEAT] [PAUSE] [ACT]", size=1.0, color=AMBER,
               why="The five cue tags the parser reads out of the script."),
          blank(6, 5), crackle(5, opacity=0.05), vu(5, amp=0.04)]
    C += [bakelite(6), blank(2, 6, "Nothing moves in a beat."),
          blank(3, 6, "Nothing moves in a beat."),
          blank(4, 6, "No glow."),
          text(6, "[BEAT]", font=STATION, size=2.4, align="Center", valign="Center", x=0, y=0,
               why="A beat: the script's held breath."),
          blank(6, 6), crackle(6, opacity=0.1),
          L.scope(6, color=AMBER, position=0.88, amplitude=0.0, name="Held", why="Flat for the beat.")]
    C += [ruling(7, amount=8),
          clip(2, 7, "Cascade", "Line Scape",
               {"Tilt": 60.0, "Direction": 0.0, "Position Y": 8.0, "Speed": 0.6, "Height": 14.0,
                "Jagginess": 0.0, "Wobble": 0.0, "Attenuation": 120.0, "Line Width": 0.2,
                "Fuzzyness": 0.0, "Color": CREAM_DIM, "Show Knots": False},
               "The freeze cascade: lines falling into place, phase by phase.", opacity=0.7,
               fft=fft("Height", "low", 10.0, 20.0, 8.0, 400)),
          node_box(3, 7, color=GREEN, name="FreezeCascade", lines=12, shape="Hexagon"),
          glow(7, color=GREEN_DIM, opacity=0.18),
          text(7, "OTR_LedgerFreezeCascade\nPHASE 7: NORMALIZE\nPHASE 8: COVERAGE AUDIT", size=0.8),
          blank(6, 7), crackle(7, opacity=0.05), vu(7, amp=0.05)]
    C += [ruling(8, amount=24), node_box(2, 8, color=GREEN, name="Ledger", lines=8),
          clip(3, 8, "Padlock Ring", "Rings",
               {"Num Rings": 2, "Size": 0.2, "Spacing": 0.4, "Line Width": 0.04, "Style": "Stroke",
                "Gap": 0.0, "Rotation": 0.0, "Rotation Step": 0.0, "Rotation Alternate": False,
                "Color 1": GREEN, "Color 2": CREAM}, "The ledger locked: two rings, a shackle.",
               opacity=0.9, effects=[xform(y=-180)], fft={}),
          glow(8, color=GREEN_DIM, opacity=0.2),
          text(8, "LEDGER LOCKED\nSCRIPT IS SOURCE OF TRUTH", size=0.9, color=GREEN),
          blank(6, 8), crackle(8, opacity=0.05), vu(8, amp=0.03)]
    return {"name": "Writers Room", "slug": "writers-room", "theme": "pipeline",
            "world": ("The script's birth, node by node: OTR_LedgerScriptWriter takes a premise, characters, "
                      "a plot and a setting and writes the play; the parser pulls [SFX:] [MUSIC:] [BEAT] "
                      "[PAUSE] [ACT] out of the text; OTR_LedgerFreezeCascade normalizes it for speech and "
                      "audits visual coverage; then the ledger locks and the script becomes the source of "
                      "truth for every later node. Nodes are amber boxes on ruled cream paper, wired; the "
                      "locked ledger turns magic-eye green."),
            "palette": [{"role": "bed", "hex": "#0b0a14", "why": "Midnight."},
                        {"role": "body", "hex": "#ffb347", "why": "Amber nodes and plot lines."},
                        {"role": "figure", "hex": "#f4e9c8", "why": "Cream cards and hatching."},
                        {"role": "light", "hex": "#7fd37f", "why": "Green when a phase freezes."},
                        {"role": "text", "hex": "#f4e9c8", "why": "Widget names in Courier, exactly as the node shows them."},
                        {"role": "aura", "hex": "#7fd37f", "why": "Green only at the lock."}],
            "columns": cols,
            "text_corpus": ["OTR_LedgerScriptWriter", "source_bank: my_story", "custom_premise",
                            "story_characters", "story_plot", "story_setting", "[SFX:]", "[MUSIC:]",
                            "[BEAT]", "[PAUSE]", "[ACT]", "LEDGER LOCKED"],
            "moments": [
                "Premise to setting: walk UP through columns 1-4 one per phrase; the wires on row 3 wobble on "
                "the mids. Keep every effect off so the node boxes read.",
                "Beat: fire Scene Launch 6 exactly on a dropped beat in the music and let the room hold - "
                "the SCOPE goes flat on purpose.",
                "Freeze to lock: UP to column 7 with bank-A at a quarter and TRAILS lit so the cascade's lines "
                "stack; UP again to Ledger Locked on the downbeat and tap BANK LOCK (CLEAN)."],
            "clips": C}


# ================================================================ DECK 3
# THE CAST - CastLock, Kokoro voices, eight languages, the waveform
def deck3():
    C = []
    cols = ["Cast Lock", "Kokoro", "Announcer", "Eight Languages",
            "Voice Pool", "Dialogue", "Captions", "Credit Roll"]
    C += [ruling(1), node_box(2, 1, color=AMBER, name="CastLock", lines=9),
          tube(3, 1, color=CREAM, grid=3, size=0.1, name="Bound Voices"),
          glow(1, opacity=0.14),
          text(1, "OTR_CastLock\nBINDS A VOICE TO A NAME\nFOR THE WHOLE EPISODE", size=0.8),
          blank(6, 1), crackle(1, opacity=0.05), waveform(1, amp=0.06)]
    C += [bakelite(2), carrier(2, 2, color=GREEN, waves=8, amp=0.2, position=0.5, speed=4.0,
                               name="Kokoro Voice", why="A Kokoro ONNX voice as a dense sine."),
          carrier(3, 2, color=AMBER, waves=3, amp=0.1, position=0.5, speed=2.0, width=0.01,
                  name="Phoneme Line", why="The phoneme stream under the voice."),
          glow(2, color=GREEN_DIM, opacity=0.2),
          text(2, "kokoro-onnx\naf_heart - am_michael\n24 KHZ", size=0.8),
          blank(6, 2), crackle(2, opacity=0.04), waveform(2)]
    C += [bakelite(3), dial(2, 3, size=0.5, color=CREAM, name="Announcer Mic Ring"),
          magic_eye(3, 3, size=0.18),
          on_air(3, opacity=0.6),
          caption(3, "ANNOUNCER: FROM OUR STUDIOS\nTRANSMISSION FROM TOMORROW", size=0.9),
          wash(3, AMBER_DIM, kind="Vertical", opacity=0.08), crackle(3, opacity=0.06), vu(3, amp=0.08)]
    C += [ruling(4, amount=8),
          clip(2, 4, "Eight Bands", "Lines",
               {"Fuzzyness": 0.0, "Amount": 8, "Width": 0.06, "Rotation": 0.0, "Position": 0.5,
                "Color": AMBER_DIM}, "Eight horizontal bands, one per language.", opacity=0.9,
               fft=fft("Width", "low", 0.05, 0.12, 8.0, 400)),
          blank(3, 4, "The bands are the figure."),
          glow(4, opacity=0.12),
          text(4, "EN ES PT IT FR HI JA ZH\nONE episode_language\nSWITCH", size=0.9, color=AMBER),
          blank(6, 4), crackle(4, opacity=0.05), waveform(4, amp=0.08)]
    C += [bakelite(5), tube(2, 5, color=CREAM, grid=6, size=0.07, name="Voice Pool",
                            why="The voice pool: many small discs, a few lit."),
          tube(3, 5, color=GREEN, grid=2, size=0.1, name="Chosen Two"),
          glow(5, color=GREEN_DIM, opacity=0.14),
          text(5, "VOICE POOL\nGENDER - AGE - ACCENT\nCOVERAGE REPAIR", size=0.8),
          blank(6, 5), crackle(5, opacity=0.04), waveform(5, amp=0.06)]
    C += [bakelite(6), carrier(2, 6, color=GREEN, waves=5, amp=0.16, position=0.42, speed=3.0,
                               name="Voice A"),
          carrier(3, 6, color=AMBER, waves=7, amp=0.12, position=0.58, speed=5.0, name="Voice B",
                  why="Two voices in exchange, never overlapping lines."),
          glow(6, opacity=0.1),
          caption(6, "ARCHIVIST: THE GAUGE\nIS SHIVERING AGAIN.", size=1.0),
          blank(6, 6), crackle(6, opacity=0.05), waveform(6)]
    C += [bakelite(7), engraving(2, 7, opacity=0.35, name="Still Hatch"),
          clip(3, 7, "Caption Bar", "Lines",
               {"Fuzzyness": 0.0, "Amount": 1, "Width": 0.1, "Rotation": 0.0, "Position": 0.86,
                "Color": NIGHT2}, "The burned caption's dark bar along the bottom.", opacity=1.0),
          blank(4, 7, "No lamp over a still."),
          caption(7, "APPRENTICE: HOW LONG\nDO WE HAVE?", size=1.0,
                  why="Captions mirror the written line rather than translating it."),
          blank(6, 7), crackle(7, opacity=0.06), vu(7, amp=0.04)]
    C += [bakelite(8), blank(2, 8, "Credits only."), blank(3, 8, "Credits only."),
          glow(8, opacity=0.08),
          L.text(8, "WRITTEN - CAST - PERFORMED\nSCORED - DRAWN - CUT\nON ONE MACHINE",
                 color=CREAM, size=0.9, font=STATION, align="Center", valign="Center", x=0, y=0,
                 animated=True, delay=40, name="Credit Roll", layer=5,
                 why="The credit roll, typed on line by line."),
          blank(6, 8), crackle(8, opacity=0.08), vu(8, amp=0.02)]
    return {"name": "The Cast", "slug": "cast", "theme": "voices",
            "world": ("Who speaks, and in what tongue. OTR_CastLock binds a Kokoro voice to each name for "
                      "the whole episode; the announcer gets the ring and the ON AIR lamp; eight languages "
                      "are eight bands under one switch; the voice pool is a field of soft discs with two "
                      "lit. Dialogue is two sines in exchange, green and amber, never overlapping. Captions "
                      "are burned in Bahnschrift over a dark bar and mirror the written line. It ends on the "
                      "credit roll: written, cast, performed, scored, drawn, cut, on one machine."),
            "palette": [{"role": "bed", "hex": "#0b0a14", "why": "Midnight."},
                        {"role": "body", "hex": "#7fd37f", "why": "Voice A, the Kokoro sine, green."},
                        {"role": "figure", "hex": "#ffb347", "why": "Voice B and the phoneme line, amber."},
                        {"role": "light", "hex": "#7fd37f", "why": "The magic eye for the announcer."},
                        {"role": "text", "hex": "#f4e9c8", "why": "Captions, speaker-labelled."},
                        {"role": "aura", "hex": "#ffb347", "why": "Amber."}],
            "columns": cols,
            "text_corpus": ["OTR_CastLock", "kokoro-onnx", "af_heart", "am_michael", "ANNOUNCER",
                            "EN ES PT IT FR HI JA ZH", "episode_language", "VOICE POOL",
                            "ARCHIVIST", "APPRENTICE", "CAPTIONS MIRROR THE LINE", "ON ONE MACHINE"],
            "moments": [
                "Dialogue: Scene Launch 6 and ride faders 2 and 3 against each other as the voices trade lines; "
                "the SCOPE waveform is the master.",
                "Eight languages: Scene Launch 4 with bank-D at a quarter and GRID CLONE lit so the eight "
                "bands tile; tap NEGATIVE once per language if the track has eight hits.",
                "Credit roll: UP to column 8 on the last chorus, pull every fader but 5 and 7, and let the "
                "credits type over crackle; BLACKOUT on the final beat."],
            "clips": C}


# ================================================================ DECK 4
# THE GRAPH - a VJ journey through the canonical workflow, one node per column:
# input sockets stacked on the left (green), outputs on the right (amber), the
# wire between them. Socket names are the real ones from otr_canonical.json.
NODES = [
    ("ScriptWriter", "OTR_LedgerScriptWriter", ["gate_in"],
     ["script_text", "script_json", "news_used"]),
    ("FreezeCascade", "OTR_LedgerFreezeCascade", ["script_text", "script_json", "news_used"],
     ["script_json", "v2_ledger_json"]),
    ("CastLock", "OTR_CastLock", ["script_json"], ["ledger_json"]),
    ("Voices", "OTR_BatchCharacterVoices", ["script_json", "ledger_json", "gate_in"],
     ["character_audio", "done"]),
    ("SceneSequencer", "OTR_SceneSequencer", ["tts_audio_clips", "announcer_audio_clips", "script_json"],
     ["scene_audio"]),
    ("Assembler", "OTR_EpisodeAssembler", ["scene_audio", "music_cue_audio", "video_policy_json"],
     ["episode_audio", "output_path", "audio_done"]),
    ("RenderBatch", "OTR_VideoRenderBatch", ["patched_ledger_json", "master_audio_path", "image_done"],
     ["clip_manifest_json"]),
    ("MasterAudioMux", "OTR_MasterAudioMux", ["silent_video_path", "master_audio_path", "audio_done"],
     ["EPISODE.MP4"]),
]


def sockets(layer, col, names, side, color, name,
            why="Socket dots stacked down one edge of the node."):
    n = max(1, len(names))
    return clip(layer, col, name, "Metaballs",
                {"Grid": n, "Blend": "Minimal", "Size": 0.06, "Distance": 0.35, "Radius": 0.1,
                 "Fuzzyness": 0.05, "Speed": 0.0, "Position X": side, "Position Y": 0.0,
                 "Color": color, "BG Color": CLEAR}, why, opacity=0.95,
                fft=fft("Size", "low", 0.05, 0.1, 9.0, 350))


def deck4():
    C = []
    cols = [n[0] for n in NODES]
    for i, (short, full, ins, outs) in enumerate(NODES, start=1):
        last = (i == len(NODES))
        C += [ruling(i, amount=22, color=NIGHT2, name="Canvas Grid",
                     why="The ComfyUI canvas grid."),
              node_box(2, i, color=GREEN if last else AMBER, name=short, lines=8 + len(ins),
                       shape="Square", opacity=0.85,
                       why="%s as a rounded box; its wire runs on to the next node." % full),
              sockets(3, i, ins, -0.62, GREEN, "Inputs",
                      why="Input sockets on the left: " + ", ".join(ins)),
              sockets(4, i, outs, 0.62, AMBER, "Outputs",
                      why="Output sockets on the right: " + ", ".join(outs)),
              text(i, full.replace("OTR_Ledger", "OTR_Ledger" + chr(10)).replace("OTR_BatchCharacter", "OTR_Batch" + chr(10) + "Character") + chr(10) + "IN: " + " ".join(ins[:2]) + chr(10) + "OUT: " + " ".join(outs[:2]),
                   size=0.75, color=GREEN if last else CREAM,
                   why="The node's class name and its wired sockets, as typed in the workflow."),
              wires(6, i, color=AMBER_DIM, opacity=0.5, name="Wire On",
                    why="The wire leaving the right edge toward the next node."),
              crackle(i, opacity=0.04),
              (waveform(i, amp=0.08, name="Audio On The Wire") if i >= 4 else
               vu(i, amp=0.03, name="JSON On The Wire",
                  why="Before the voices there is only text on the wire: a thin line."))]
    return {"name": "The Graph", "slug": "graph", "theme": "pipeline",
            "world": ("A VJ journey through otr_canonical.json, one node per scene in signal order: "
                      "ScriptWriter, FreezeCascade, CastLock, Voices, SceneSequencer, Assembler, "
                      "RenderBatch, MasterAudioMux. Each column is one rounded node on the canvas grid "
                      "with its real input sockets stacked green down the left edge and its outputs "
                      "amber down the right, and a wire leaving right toward the next. Until the voices "
                      "node the wire carries only JSON, a thin line; from there it carries audio and the "
                      "SCOPE becomes a waveform. The last node is green: the .mp4."),
            "palette": [{"role": "bed", "hex": "#0b0a14", "why": "The canvas."},
                        {"role": "body", "hex": "#ffb347", "why": "Node boxes, amber."},
                        {"role": "figure", "hex": "#7fd37f", "why": "Input sockets, green."},
                        {"role": "light", "hex": "#ffb347", "why": "Output sockets, amber."},
                        {"role": "text", "hex": "#f4e9c8", "why": "Class names and socket names, exact."},
                        {"role": "aura", "hex": "#ffb347", "why": "The wire."}],
            "columns": cols,
            "text_corpus": [n[1] for n in NODES] + ["script_json", "ledger_json", "master_audio_path",
                                                     "EPISODE.MP4"],
            "moments": [
                "The journey: Scene Launch 1 then UP once per bar through all eight nodes; keep bank-A at a "
                "quarter with only TRAILS lit so each wire leaves a trace into the next column.",
                "Sockets: on any node, tap the row-3 FIGURE pad and row-4 LIGHT pad alternately on the beat "
                "so inputs and outputs blink in turn; the kick swells the dots.",
                "Mux: at column 8 pull faders 1 and 6, leave the green node and the waveform, and tap "
                "NEGATIVE for one bar as the file lands."],
            "clips": C}


# ================================================================ DECK 5
# THE SHIVERING GAUGE - the wildcard: the episode itself, as engravings
def deck5():
    C = []
    cols = ["Lab After Hours", "Developing Tanks", "The Gauge", "Vinegar",
            "Reel By Reel", "Shivering", "Dawn", "Sign-Off"]
    C += [bakelite(1), engraving(2, 1, opacity=0.4, rot=0.0, name="Lab Shelves"),
          tube(3, 1, color=AMBER, grid=2, size=0.08, name="Two Lamps"),
          glow(1, opacity=0.2, name="Safelight"),
          caption(1, "NARRATOR: A FILM LAB,\nAFTER HOURS.", size=0.9),
          blank(6, 1), crackle(1, opacity=0.08), vu(1, amp=0.04)]
    C += [bakelite(2), clip(2, 2, "Tanks", "Checkered",
                            {"Num X": 4, "Num Y": 1, "Color 1": NIGHT2, "Color 2": CREAM_DIM},
                            "Four developing tanks in a row.", opacity=0.7,
                            effects=[{"effect": "Transform", "params": {"Scale W": 100.0, "Scale H": 40.0}}]),
          engraving(3, 2, opacity=0.35, rot=90.0, name="Tank Hatch"),
          glow(2, opacity=0.16, name="Safelight"),
          caption(2, "ARCHIVIST: KEEP THE LIDS\nON. DON'T BREATHE IT.", size=0.9),
          blank(6, 2), crackle(2, opacity=0.08), vu(2, amp=0.05)]
    C += [bakelite(3), dial(2, 3, size=0.6, color=CREAM, rings=12, width=0.01, name="Gauge Face"),
          needle(3, 3, color=RED, rot=110.0, name="Gauge Needle",
                 why="The gauge needle, red: the second place red is allowed."),
          glow(3, opacity=0.18),
          caption(3, "APPRENTICE: IT'S PAST\nTHE RED LINE.", size=0.9),
          blank(6, 3), crackle(3, opacity=0.06), vu(3, amp=0.08)]
    C += [bakelite(4), clip(2, 4, "Acetate Haze", "Abstract Field",
                            {"Octaves": 3, "Amplitude": 0.4, "Density": 0.5},
                            "Vinegar syndrome: the acetate base hazing and warping.", opacity=0.5,
                            effects=[{"effect": "Tint", "params": {"Black To": NIGHT, "White To": AMBER_DIM}}],
                            fft=fft("Density", "low", 0.4, 0.8, 8.0, 1200)),
          engraving(3, 4, opacity=0.3, rot=20.0, name="Warped Hatch"),
          glow(4, opacity=0.1),
          caption(4, "NARRATOR: THE SMELL\nOF VINEGAR.", size=0.9),
          wash(4, AMBER_DIM, kind="Radial", opacity=0.08), crackle(4, opacity=0.12), vu(4, amp=0.04)]
    C += [bakelite(5), dial(2, 5, size=0.5, color=CREAM, rings=20, width=0.01, name="Reel",
                            effects=[xform(x=-320)]),
          dial(3, 5, size=0.5, color=CREAM_DIM, rings=20, width=0.01, name="Take-Up Reel",
               effects=[xform(x=320)]),
          glow(5, opacity=0.14),
          caption(5, "ARCHIVIST: REEL BY REEL.\nTHAT'S THE ONLY WAY.", size=0.9),
          blank(6, 5), crackle(5, opacity=0.08), vu(5, amp=0.06)]
    C += [bakelite(6), dial(2, 6, size=0.6, color=CREAM, rings=12, width=0.01, name="Gauge Face",
                            fft_=fft("Size", "high", 0.58, 0.64, 10.0, 150),
                            why="The gauge face shivering on the highs."),
          needle(3, 6, color=RED, rot=110.0, name="Shivering Needle"),
          clip(4, 6, "Flicker", "Stroboscope", {"Frequency": 0.6, "Fade": True, "Color 1": CREAM_DIM,
                                                "Color 2": CLEAR},
               "The safelight flickering with the shiver.", opacity=0.14),
          caption(6, "APPRENTICE: IT'S\nSHIVERING AGAIN.", size=1.0),
          blank(6, 6), crackle(6, opacity=0.1), vu(6, amp=0.1)]
    C += [clip(1, 7, "Dawn", "Gradient", {"Method": "2 Colors", "Color 1": NIGHT, "Color 2": NIGHT2,
                                          "Mode": "Smooth", "Dither": 0.0, "Type": "Vertical"},
               "First light under the door."),
          engraving(2, 7, opacity=0.3, rot=0.0, name="Lab Shelves"),
          tube(3, 7, color=CREAM, grid=1, size=0.06, name="Last Lamp"),
          glow(7, color=CREAM_DIM, opacity=0.16, name="Door Light"),
          caption(7, "NARRATOR: BY DAWN, THE\nREELS WERE SAFE.", size=0.9),
          wash(7, CREAM_DIM, kind="Vertical", opacity=0.08), crackle(7, opacity=0.06), vu(7, amp=0.03)]
    C += [bakelite(8), dial(2, 8, size=0.8, opacity=0.5, color=CREAM_DIM, fft_={}, name="Dial Fading"),
          needle(3, 8, color=AMBER, rot=72.0),
          on_air(8, opacity=0.3),
          caption(8, "ANNOUNCER: THIS HAS BEEN\nSIGNAL LOST. GOOD NIGHT.", size=1.0),
          blank(6, 8), crackle(8, opacity=0.1),
          carrier(8, 8, color=GREEN_DIM, waves=12, amp=0.03, position=0.86, speed=6.0,
                  name="Carrier Drops", why="The carrier fading to hiss.")]
    return {"name": "Shivering Gauge", "slug": "shivering-gauge", "theme": "wildcard",
            "world": ("The episode itself, drawn as the pack draws everything: a film archivist and an "
                      "apprentice racing vinegar syndrome through one night in the lab. Storybook-engraving "
                      "hatching, four developing tanks, two reels, and a gauge whose red needle sits past "
                      "the line and shivers on the highs. Safelight amber, acetate haze, first light under "
                      "the door, and the sign-off: this has been SIGNAL LOST. Good night."),
            "palette": [{"role": "bed", "hex": "#0b0a14", "why": "The lab after hours."},
                        {"role": "body", "hex": "#f4e9c8", "why": "Engraving cream."},
                        {"role": "figure", "hex": "#e0432a", "why": "The gauge needle: red, past the line."},
                        {"role": "light", "hex": "#ffb347", "why": "Safelight amber."},
                        {"role": "text", "hex": "#f4e9c8", "why": "Burned captions."},
                        {"role": "aura", "hex": "#ffb347", "why": "Amber haze."}],
            "columns": cols,
            "text_corpus": ["A FILM LAB, AFTER HOURS", "KEEP THE LIDS ON", "PAST THE RED LINE",
                            "THE SMELL OF VINEGAR", "REEL BY REEL", "IT'S SHIVERING AGAIN",
                            "BY DAWN", "THIS HAS BEEN SIGNAL LOST", "GOOD NIGHT", "ARCHIVIST",
                            "APPRENTICE", "NARRATOR"],
            "moments": [
                "The gauge: Scene Launch 3, hold the row-3 FIGURE pad so the red needle shows only while held; "
                "UP to Shivering on the hi-hat run and let the face shake.",
                "Vinegar: column 4, bank-B knob to a third with WAVE WARP lit so the acetate haze warps the "
                "hatching; pull it to zero on the next caption.",
                "Sign-off: UP to column 8 on the last phrase, fade every fader but 2, 3, 5 and 8, let the "
                "carrier drop to hiss, then STOP ALL CLIPS."],
            "clips": C}


def main():
    decks = [deck1(), deck2(), deck3(), deck4(), deck5()]
    bible = {
        "pack_name": "Signal Lost",
        "comp_name": "Signal Lost - Transmission From Tomorrow",
        "tagline": "Good evening. This is SIGNAL LOST.",
        "decks": [{k: v for k, v in d.items() if k != "clips"} for d in decks],
        "effect_wishlist": [
            {"effect": "Trails", "role": "Bank A: the freeze cascade stacking, the carrier's afterglow."},
            {"effect": "Vignette", "role": "Bank A: the bandpass window closing on the full band."},
            {"effect": "CRT", "role": "Bank C: engravings and act cards as a print."},
            {"effect": "Stop Motion", "role": "Bank C: the sequencer's scene changes."},
            {"effect": "Wave Warp", "role": "Bank B: acetate warping in Vinegar."},
            {"effect": "Grid Cloner", "role": "Bank D: eight languages tiled."}],
        "fft_philosophy": (
            "Radio is sound made visible, so the composition's reactivity is the program line and the "
            "voices. Mids drive the SCOPE (VU line or waveform) 1:1 and the magic eye's fan; lows drive "
            "only size and width - dial lines, node boxes, timeline blocks, filament size - so a kick is "
            "pressure on the chassis; highs shiver the band ticks, the hatching and, once, the gauge face. "
            "Colour never reacts: amber is work, green is signal and master, cream is paper, red is the "
            "ON AIR lamp and the gauge needle and nothing else. Text never moves. [BEAT] and the 48 kHz "
            "Master are deliberately still: the picture holds while the sound does the work."),
        "wildcard_rationale": (
            "Four decks are the machine: the set signing on, the writers' room, the cast, the filter. The "
            "fifth is what the machine made - The Shivering Gauge, the episode the pack's README opens on - "
            "drawn the way the pipeline draws its own stills, so the instrument ends by performing its own "
            "output.")}
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
    print("clips carrying red:", sum(1 for d in decks for c in d["clips"]
                                     if RED.lower() in json.dumps(c).lower()))


if __name__ == "__main__":
    main()
