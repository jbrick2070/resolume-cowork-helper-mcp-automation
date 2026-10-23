import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import pytest

pytest.importorskip("PIL")
pytest.importorskip("numpy")
from PIL import Image

from apc_lab import engine as E
from apc_lab import live
from apc_lab import protocol as P
import theme_from_image as T


def solid(rgb, size=(24, 24)):
    return Image.new("RGB", size, rgb)


def bands(colours, size=(60, 60)):
    im = Image.new("RGB", size)
    w = size[0] // len(colours)
    for i, c in enumerate(colours):
        im.paste(c, (i * w, 0, (i + 1) * w if i < len(colours) - 1 else size[0], size[1]))
    return im


def test_nearest_apc_finds_the_obvious_matches():
    assert T.nearest_apc((255, 0, 0)) in (5, 72)                       # both are #FF0000
    assert T.nearest_apc((0, 255, 0)) in (21, 87)
    assert T.nearest_apc((255, 255, 255)) == 3
    assert T.apc_luma(T.nearest_apc((0, 0, 0))) < 0.06                 # black maps to a near-black LED (0 itself is skipped)
    assert tuple(E.PALETTE[T.nearest_apc((30, 60, 200))])[2] > 150     # a strong blue stays blue


def test_dim_keeps_the_hue_and_is_darker():
    for idx in (5, 21, 45, 53, 96):
        d = T.dim_of(idx)
        assert T.apc_luma(d) < T.apc_luma(idx)
        r, g, b = E.PALETTE[d]
        r0, g0, b0 = E.PALETTE[idx]
        assert (r > 0) == (r0 > 0) or (g > 0) == (g0 > 0) or (b > 0) == (b0 > 0)


def test_dominant_colours_of_a_two_colour_picture_are_those_colours():
    mapped = T.apc_colours_of(bands([(255, 0, 0), (0, 0, 255)]))
    got = {i for _, _, i in mapped}
    assert got & {5, 72} and got & {45, 67}
    assert sum(s for s, _, _ in mapped) == pytest.approx(1.0)


def test_theme_is_valid_and_runs_on_the_router():
    im = bands([(255, 120, 0), (120, 0, 200), (20, 200, 220), (240, 240, 240)])
    theme = T.theme_from_colours(T.apc_colours_of(im), "Test Cover", "cover.png", "rain")
    E.add_theme("testcover", theme)
    try:
        r = E.Router("testcover")
        for n in (0, 9, 20):
            r.from_resolume(P.on(1, n, 21 if n % 2 else 22), 0.0)
        r.from_apc(P.on(1, 9, 100), 0.5)
        for k in range(400):
            for m in r.tick(k * 0.02):
                assert 1 <= m[1] <= 16 and 0 <= m[2] < 128 and 0 <= m[3] < 128
    finally:
        E.THEMES.pop("testcover", None)
        E.THEME_ORDER.remove("testcover")


def test_same_picture_gives_the_same_theme():
    im = bands([(200, 30, 30), (30, 200, 30), (30, 30, 200)])
    a = T.theme_from_colours(T.apc_colours_of(im), "x", "x.png")
    b = T.theme_from_colours(T.apc_colours_of(im.copy()), "x", "x.png")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


@pytest.mark.parametrize("ambient", T.AMBIENTS)
def test_every_ambient_choice_makes_a_runnable_theme(ambient):
    th = T.theme_from_colours(T.apc_colours_of(bands([(250, 20, 20), (250, 250, 20), (20, 20, 250)])), "t", "t.png", ambient)
    assert th["ambient"]["kind"] == ambient
    for key in ("pairs",):
        for triple in th[key]:
            assert len(triple) == 3 and all(0 <= v < 128 for v in triple)
    E.add_theme("amb_" + ambient, th)
    try:
        r = E.Router("amb_" + ambient)
        assert len(r.tick(1.0)) > 0
    finally:
        E.THEMES.pop("amb_" + ambient)
        E.THEME_ORDER.remove("amb_" + ambient)


def test_one_colour_picture_still_makes_a_theme_of_three_families():
    th = T.theme_from_colours(T.apc_colours_of(solid((255, 80, 0))), "mono", "mono.png")
    assert len(th["pairs"]) == 3
    assert len({p[0] for p in th["pairs"]}) == 3                       # three distinct 'on' colours


def test_add_theme_rejects_a_theme_with_missing_fields():
    with pytest.raises(ValueError):
        E.add_theme("broken", {"name": "x", "remap": "pairs"})
    with pytest.raises(ValueError):
        E.add_theme("broken", {"name": "x", "remap": "sparkly", "ambient": {"kind": "none"}, "touch": {"kind": "none"}})
    assert "broken" not in E.THEMES


def test_live_dry_run_loads_a_theme_file(tmp_path, capsys):
    th = T.theme_from_colours(T.apc_colours_of(bands([(250, 20, 20), (20, 250, 20), (20, 20, 250)])), "File Theme", "f.png")
    path = tmp_path / "t.json"
    path.write_text(json.dumps({"key": "filetheme", "theme": th}), encoding="utf-8")
    try:
        assert live.main(["--dry-run", "--theme-file", str(path), "--theme", "filetheme", "--seconds", "1"]) == 0
        assert "startup: mode SysEx" in capsys.readouterr().out
    finally:
        E.THEMES.pop("filetheme", None)
        if "filetheme" in E.THEME_ORDER:
            E.THEME_ORDER.remove("filetheme")
