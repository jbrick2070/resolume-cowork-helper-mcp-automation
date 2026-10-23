import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest

from apc_lab import engine as E
from apc_lab import protocol as P


def test_palette_is_128_and_matches_akai_anchors():
    assert len(E.PALETTE) == 128
    anchors = {0: (0, 0, 0), 3: (255, 255, 255), 5: (255, 0, 0), 9: (255, 84, 0), 13: (255, 255, 0),
               21: (0, 255, 0), 45: (0, 0, 255), 119: (224, 255, 255)}
    for v, rgb in anchors.items():
        assert tuple(E.PALETTE[v]) == rgb


def _velocities(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("colour", "secondary") and isinstance(v, int):
                yield v
            else:
                for x in _velocities(v):
                    yield x
    elif isinstance(o, list):
        for x in o:
            if isinstance(x, int):
                yield x
            else:
                for y in _velocities(x):
                    yield y


def test_every_theme_velocity_exists_in_the_palette():
    for key, th in E.THEMES.items():
        for k in ("pairs", "greys"):
            for v in _velocities(th.get(k, [])):
                assert 0 <= v < 128, (key, k, v)
        rest = {k: th[k] for k in th if k in ("playing", "ambient", "touch", "scene")}
        for v in _velocities(rest):
            assert 0 <= v < 128, (key, v)
    assert set(E.THEME_ORDER) == set(E.THEMES)


# ---- the surface emulation ---------------------------------------------------
def test_surface_primary_and_off():
    s = E.Surface()
    s.apply(P.on(1, 5, 21), 0.0)
    assert s.rgb(5, 1.0) == [0, 255, 0]
    s.apply(P.off(1, 5), 1.0)
    assert s.rgb(5, 1.0) == [0, 0, 0]


def test_surface_pulsing_breathes_between_primary_and_secondary():
    s = E.Surface()
    s.apply(P.on(1, 3, 22), 0.0)                                       # dim green primary
    s.apply(P.on(P.mode_to_channel("pulsing", "1/4"), 3, 21), 0.0)     # pulse to bright green
    bpm = 120.0                                                        # 1/4 = one beat = 0.5 s
    assert s.rgb(3, 0.0, bpm) == pytest.approx([0, 89, 0])
    assert s.rgb(3, 0.25, bpm) == pytest.approx([0, 255, 0])           # half a period: fully secondary
    assert s.rgb(3, 0.5, bpm) == pytest.approx([0, 89, 0], abs=1e-6)
    assert s.rgb(3, 0.25, 240.0) == pytest.approx([0, 89, 0], abs=1e-6)   # twice the tempo: one full period


def test_surface_blinking_and_oneshot():
    s = E.Surface()
    s.apply(P.on(1, 0, 5), 0.0)
    s.apply(P.on(P.mode_to_channel("blinking", "1/4"), 0, 3), 0.0)
    assert s.rgb(0, 0.1, 120) == [255, 255, 255] and s.rgb(0, 0.3, 120) == [255, 0, 0]
    o = E.Surface()
    o.apply(P.on(1, 0, 5), 0.0)
    o.apply(P.on(P.mode_to_channel("oneshot", "1/4"), 0, 3), 1.0)
    assert o.rgb(0, 1.2, 120) == [255, 255, 255]                       # the flash
    assert o.rgb(0, 1.6, 120) == [255, 0, 0]                           # back to primary


def test_primary_on_channel_one_cancels_an_animation():
    s = E.Surface()
    s.apply(P.on(1, 0, 5), 0.0)
    s.apply(P.on(P.mode_to_channel("blinking", "1/8"), 0, 3), 0.0)
    s.apply(P.on(1, 0, 5), 0.2)
    assert s.rgb(0, 0.2, 120) == s.rgb(0, 0.7, 120) == [255, 0, 0]


# ---- the router --------------------------------------------------------------
def test_press_is_forwarded_untouched():
    r = E.Router("halloween")
    to_res, _ = r.from_apc(P.on(1, 12, 100), 0.0)
    assert to_res == [P.on(1, 12, 100)]


def test_identity_theme_passes_feedback_through():
    r = E.Router("pack")
    assert r.from_resolume(P.on(1, 8, 21), 0.0) == [P.on(1, 8, 21)]
    assert r.from_resolume(P.on(1, 9, 22), 0.0) == [P.on(1, 9, 22)]


def test_halloween_remaps_playing_and_loaded_green():
    r = E.Router("halloween")
    play = r.from_resolume(P.on(1, 8, 21), 0.0)
    assert play[0] == P.on(1, 8, 94) and play[1][1] == P.mode_to_channel("pulsing", "1/4")
    assert play[1][3] == 96                                            # breathes to pumpkin
    assert r.from_resolume(P.on(1, 9, 22), 0.0) == [P.on(1, 9, 51)]    # loaded = dim violet


def test_unknown_velocities_pass_through():
    r = E.Router("halloween")
    assert r.from_resolume(P.on(1, 8, 127), 0.0) == [P.on(1, 8, 127)]


def test_diffing_sends_nothing_when_nothing_changed():
    r = E.Router("halloween")
    r.tick(0.0)
    assert r.tick(0.0) == []
    assert E.Router("pack").tick(5.0) == []                            # identity + no ambient: silence


def test_dark_pad_returns_to_ambient_when_resolume_clears_it():
    r = E.Router("christmas")
    r.tick(0.0)
    r.from_resolume(P.on(1, 4, 21), 0.0)
    msgs = r.from_resolume(P.off(1, 4), 0.0)                           # Resolume says: dark now
    assert all(m[2] == 4 for m in msgs)


def test_ripple_is_a_ring_ordered_by_distance():
    r = E.Router("halloween")
    r.tick(0.0)
    _, immediate = r.from_apc(P.on(1, 20, 100), 1.0)                   # pad (4, 2)
    assert immediate == [P.on(P.mode_to_channel("oneshot", "1/8"), 20, 94)]
    ch = P.mode_to_channel("oneshot", "1/8")
    got = []
    t = 1.0
    while r.queue and t < 3.0:
        t = round(t + 0.01, 3)
        got += [(t, m) for m in r.tick(t) if m[1] == ch]

    def dist(n):
        c, row = P.pad_col_row(n)
        return max(abs(c - 4), abs(row - 2))
    times = {m[2]: tt for tt, m in got}
    assert len(times) == 39                                            # every other pad, once
    for n, tt in times.items():
        assert tt == pytest.approx(1.0 + dist(n) * 0.065, abs=0.02)


def test_invert_flips_lit_and_dark_pads():
    r = E.Router("inverse")
    r.from_resolume(P.on(1, 0, 21), 0.0)                               # pad 0 lit
    _, out = r.from_apc(P.on(1, 5, 100), 0.0)
    by_note = {m[2]: m[3] for m in out}
    assert by_note[0] == 1 and by_note[1] == 3                         # lit goes dark, dark goes white


def test_ambient_is_deterministic():
    a, b = E.Router("halloween"), E.Router("halloween")
    assert a.tick(3.3) == b.tick(3.3)
    assert a.tick(3.9) == b.tick(3.9)


def test_every_theme_runs_a_press_and_ten_seconds_without_error():
    for key in E.THEME_ORDER:
        r = E.Router(key)
        for n in (0, 12, 39):
            r.from_resolume(P.on(1, n, 21 if n % 2 else 22), 0.0)
        r.from_apc(P.on(1, 12, 90), 0.5)
        total = 0
        for k in range(0, 1000):
            out = r.tick(k * 0.01)
            total += len(out)
            for m in out:
                assert 1 <= m[1] <= 16 and 0 <= m[2] < 128 and 0 <= m[3] < 128
        assert total > 0 or key == "pack"


def test_hash_is_stable_and_in_range():
    vals = [E.hash01(a, b) for a in range(5) for b in range(5)]
    assert all(0 <= v < 1 for v in vals) and len(set(vals)) == len(vals)
    assert E.hash01(7, 11) == E.hash01(7, 11)


# ---- rings and clock -----------------------------------------------------------
def test_ring_meter_only_sends_changes():
    m = E.RingMeter()
    assert m.set(0, 0.5) == [P.cc(1, 56, 2), P.cc(1, 48, 64)]          # style first, then value
    assert m.set(0, 0.5) == []
    assert m.set(0, 1.0) == [P.cc(1, 48, 127)]
    assert m.set(8, 0.0, "pan") == [P.cc(1, 24, 3), P.cc(1, 16, 0)]


def test_clock_is_24_per_quarter_note():
    assert E.clock_ticks(0.0, 0.5, 120.0) == 24                        # one beat at 120 bpm
    assert E.clock_ticks(0.0, 1.0, 60.0) == 24
    pieces = sum(E.clock_ticks(i / 10.0, (i + 1) / 10.0, 133.0) for i in range(100))
    assert pieces == E.clock_ticks(0.0, 10.0, 133.0)
