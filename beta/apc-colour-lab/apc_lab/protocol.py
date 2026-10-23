#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
protocol.py - the APC40 mkII message vocabulary the colour lab speaks.

Sources: Akai APC40 Mk2 Communications Protocol v1.2, as decoded in
apc40mkii-kit/docs/APC40_native_addresses.md and transcribed in the
APC40-MkII-Chataigne-Module's MIDI_Messages.md (cunabula27, GPL-3.0).

The one idea everything here rests on: on the RGB pads (clip grid notes 0-39,
Scene Launch notes 82-86) the NOTE-ON VELOCITY picks the colour from a fixed
128-entry palette and the MIDI CHANNEL picks the animation:

    channel  1      primary colour (static)
    channel  2-6    secondary colour, one-shot   1/24 1/16 1/8 1/4 1/2
    channel  7-11   secondary colour, pulsing    1/24 1/16 1/8 1/4 1/2
    channel 12-16   secondary colour, blinking   1/24 1/16 1/8 1/4 1/2

so two messages per pad make the controller animate a pad by itself.

ASSUMPTIONS, not yet verified on this rig's hardware (the controller's ports
are held by Avenue): (a) the rates are note values at the host tempo, so
1/4 = one beat; (b) a note-on on an animation channel animates between the pad's
primary colour and the colour in that message; (c) resending the primary on
channel 1 cancels an animation (the module's "Reset Mode" does exactly this).
"""

NOTE_ON, NOTE_OFF, CC = "on", "off", "cc"

SCENE_NOTES = (82, 83, 84, 85, 86)        # 82 = top row, 86 = bottom row
PAD_NOTES = tuple(range(40))              # 0 = bottom-left, 39 = top-right
ALL_PADS = PAD_NOTES + SCENE_NOTES

KINDS = ("primary", "oneshot", "pulsing", "blinking")
DIVS = ("1/24", "1/16", "1/8", "1/4", "1/2")
# Length of each division in beats (a quarter note is one beat).
DIV_BEATS = {"1/24": 4.0 / 24, "1/16": 0.25, "1/8": 0.5, "1/4": 1.0, "1/2": 2.0}

RING_STYLES = {"off": 0, "single": 1, "volume": 2, "pan": 3}
DEVICE_RING_STYLE_CC = tuple(range(24, 32))     # style for device knobs 1-8
DEVICE_RING_VALUE_CC = tuple(range(16, 24))
TRACK_RING_STYLE_CC = tuple(range(56, 64))      # style for track knobs 1-8
TRACK_RING_VALUE_CC = tuple(range(48, 56))

# Single-colour LED buttons: velocity 0 = off, anything else = on, except
# these two which take a palette of their own.
CLIP_STOP_NOTE = 52                              # 0 off, 1 on, 2 blink
CROSSFADE_AB_NOTE = 66                           # 0 off, 1 yellow (A), 2 orange (B)
TRACK_BUTTON_NOTES = {"record_arm": 48, "solo": 49, "activator": 50,
                      "track_select": 51, "clip_stop": 52, "crossfade_ab": 66}
BUTTON_NOTES = {"pan": 87, "sends": 88, "user": 89, "metronome": 90, "play": 91,
                "record": 93, "session": 102, "bank_lock": 103,
                "device_left": 58, "device_right": 59, "bank_left": 60,
                "bank_right": 61, "device_on_off": 62, "device_lock": 63,
                "clip_device_view": 64, "detail_view": 65, "master": 80}


def pad_col_row(note):
    """(column 0-7, row 0-4) with row 0 at the bottom, for notes 0-39 and 82-86."""
    if note in SCENE_NOTES:
        return (8, 86 - note)                    # a ninth column, n82 on the top row
    return (note % 8, note // 8)


def pad_note(col, row):
    return row * 8 + col


def mode_to_channel(kind, div=None):
    """('pulsing', '1/4') -> channel 10. ('primary', None) -> channel 1."""
    if kind == "primary":
        return 1
    base = {"oneshot": 2, "pulsing": 7, "blinking": 12}[kind]
    return base + DIVS.index(div)


def channel_to_mode(ch):
    """Inverse of mode_to_channel: 1-16 -> (kind, div)."""
    if not 1 <= ch <= 16:
        raise ValueError("MIDI channel out of range: %r" % ch)
    if ch == 1:
        return ("primary", None)
    if ch <= 6:
        return ("oneshot", DIVS[ch - 2])
    if ch <= 11:
        return ("pulsing", DIVS[ch - 7])
    return ("blinking", DIVS[ch - 12])


MODE_BYTE = {0: 0x40, 1: 0x41, 2: 0x42}           # Generic, Ableton Live, Alternate


def mode_sysex(mode=2):
    """F0 47 7F 29 60 00 04 <mode> 00 00 00 F7. Mode 2 hands every LED to the host."""
    return bytes([0xF0, 0x47, 0x7F, 0x29, 0x60, 0x00, 0x04,
                  MODE_BYTE[mode], 0x00, 0x00, 0x00, 0xF7])


def on(ch, note, vel):
    return (NOTE_ON, ch, note, vel)


def off(ch, note):
    return (NOTE_OFF, ch, note, 0)


def cc(ch, ctrl, val):
    return (CC, ch, ctrl, val)


def status_bytes(msg):
    """(kind, ch, a, b) -> the three raw MIDI bytes."""
    kind, ch, a, b = msg
    base = {NOTE_ON: 0x90, NOTE_OFF: 0x80, CC: 0xB0}[kind]
    return bytes([base | (ch - 1), a & 0x7F, b & 0x7F])
