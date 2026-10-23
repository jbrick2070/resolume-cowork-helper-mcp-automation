import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest

from apc_lab import protocol as P


def test_channel_mode_roundtrip_all_sixteen():
    seen = set()
    for ch in range(1, 17):
        kind, div = P.channel_to_mode(ch)
        assert P.mode_to_channel(kind, div) == ch
        seen.add((kind, div))
    assert len(seen) == 16


@pytest.mark.parametrize("kind,div,ch", [
    ("primary", None, 1), ("oneshot", "1/24", 2), ("oneshot", "1/2", 6),
    ("pulsing", "1/24", 7), ("pulsing", "1/4", 10), ("pulsing", "1/2", 11),
    ("blinking", "1/24", 12), ("blinking", "1/8", 14), ("blinking", "1/2", 16)])
def test_documented_channels(kind, div, ch):
    # Akai protocol v1.2 p.18 and Ableton's Pulse/Blink decode, 0-based 0 | 1-5 | 6-10 | 11-15
    assert P.mode_to_channel(kind, div) == ch


def test_ableton_playing_example():
    # Ableton ClipStarted = Pulse(GREEN.shade(1), GREEN, 48): velocity 22 on channel 0, then
    # 21 on channel 10 (0-based), which is MIDI channel 11 and a 1/2 pulse.
    assert P.mode_to_channel("pulsing", "1/2") - 1 == 10


def test_division_lengths_are_midi_clock_ticks():
    ticks = {"1/24": 4, "1/16": 6, "1/8": 12, "1/4": 24, "1/2": 48}     # Ableton, 24 per quarter note
    for d, t in ticks.items():
        assert P.DIV_BEATS[d] == pytest.approx(t / 24.0)


def test_pad_geometry():
    assert P.pad_col_row(0) == (0, 0) and P.pad_col_row(39) == (7, 4) and P.pad_col_row(8) == (0, 1)
    assert P.pad_col_row(82) == (8, 4) and P.pad_col_row(86) == (8, 0)    # scene 1 is the TOP row
    assert P.pad_note(7, 4) == 39


def test_sysex_bytes():
    assert P.mode_sysex(1) == bytes.fromhex("F0477F296000044100000" + "0F7")
    assert P.mode_sysex(2)[7] == 0x42 and P.mode_sysex(0)[7] == 0x40
    assert P.mode_sysex(2)[0] == 0xF0 and P.mode_sysex(2)[-1] == 0xF7 and len(P.mode_sysex(2)) == 12


def test_status_bytes():
    assert P.status_bytes(P.on(1, 0, 21)) == bytes([0x90, 0, 21])
    assert P.status_bytes(P.on(10, 8, 22)) == bytes([0x99, 8, 22])
    assert P.status_bytes(P.off(1, 5)) == bytes([0x80, 5, 0])
    assert P.status_bytes(P.cc(1, 56, 2)) == bytes([0xB0, 56, 2])


def test_channel_range_checked():
    with pytest.raises(ValueError):
        P.channel_to_mode(0)
    with pytest.raises(ValueError):
        P.channel_to_mode(17)
