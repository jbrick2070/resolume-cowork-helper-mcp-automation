import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mido

from apc_lab import live
from apc_lab import protocol as P


def test_mido_roundtrip_keeps_one_based_channels():
    for msg in (P.on(1, 0, 21), P.on(10, 8, 22), P.off(1, 5), P.cc(1, 56, 2), P.on(16, 39, 127)):
        m = live.to_mido(msg)
        assert m.channel == msg[1] - 1
        back = live.from_mido(m)
        assert back[0] in (P.NOTE_ON, P.NOTE_OFF, P.CC) and back[1] == msg[1] and back[2] == msg[2]


def test_raw_bytes_match_protocol_status_bytes():
    for msg in (P.on(10, 8, 22), P.off(1, 5), P.cc(1, 24, 3)):
        assert bytes(live.to_mido(msg).bytes()) == P.status_bytes(msg)


def test_sysex_payload_is_framed_by_mido():
    data = list(P.mode_sysex(2)[1:-1])
    assert bytes(mido.Message("sysex", data=data).bytes()) == P.mode_sysex(2)


def test_startup_is_mode_then_all_pads_off():
    s = live.startup_messages(2)
    assert s[0] == ("sysex", P.mode_sysex(2))
    assert len(s) == 1 + len(P.ALL_PADS) and all(m[0] == P.NOTE_OFF for m in s[1:])


def test_dry_run_and_list_open_no_ports(capsys):
    assert live.main(["--dry-run", "--seconds", "1.5", "--theme", "christmas"]) == 0
    out = capsys.readouterr().out
    assert "startup: mode SysEx F0 47 7F 29 60 00 04 42 00 00 00 F7" in out
    assert "90 " in out or "99 " in out
