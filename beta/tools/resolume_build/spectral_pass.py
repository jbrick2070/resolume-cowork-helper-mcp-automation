# -*- coding: utf-8 -*-
"""
spectral_pass.py - fill empty AURA slots with Avenue 7.29's audio-reactive Spectral generators.

    from resolume_build import spectral_pass as SP
    SP.apply(decks, bible, report=print)

Why: the Spectral sources analyse the audio themselves (Input = Composition, so Avenue's global
FFT gain - the TEMPO knob - drives them) and carry their own idle motion (Fallback), so one clip
replaces a whole FFT link set. Rules, same spirit as kinetic_pass:
  * only a Blank or missing AURA clip is ever replaced - a designed wash is never touched;
  * a column where no clip has an FFT link was made deliberately still by the designer
    (Dead Air, a held beat): it is left empty;
  * colour comes from the deck's own palette (a non-red 'light' / 'body' entry); Hue is fixed,
    Spread kept small, so nothing about colour reacts;
  * Fallback stays above zero so the room never goes dead without a signal; opacity is low.
"""
import colorsys
import collections

AURA_LAYER = 6
KINDS = ("Spectral Bloom", "Spectral Eclipse", "Spectral Drops", "Spectral Shape")
OPACITY = 0.4


def _rgb(h):
    h = h.lstrip("#")[:6]
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _hls(h):
    return colorsys.rgb_to_hls(*_rgb(h))


def pick_colours(deck_bible):
    """(main, soft, dim) hex colours from a deck palette; reds are avoided, darkest is dropped."""
    cols = []
    for p in (deck_bible or {}).get("palette", []):
        try:
            hh, ll, ss = _hls(p["hex"])
        except Exception:
            continue
        red = (hh < 0.04 or hh > 0.95) and ss > 0.5
        if red or ll < 0.12:
            continue
        cols.append((p["hex"][:7], hh, ll, ss, p.get("role", "")))
    if not cols:
        return "#e9e1cf", "#8a857a", "#4a4742"
    cols.sort(key=lambda c: -(c[3] * 0.6 + c[2] * 0.4))
    main = cols[0][0]
    soft = cols[1][0] if len(cols) > 1 else main
    dim = cols[-1][0]
    return main, soft, dim


def clip_for(kind, column, deck_bible, deck_index):
    main, soft, dim = pick_colours(deck_bible)
    hue = round(_hls(main)[0], 3)
    if kind == "Spectral Bloom":
        params = {"Amount": 0.35, "Trail": 0.55, "Hue": hue, "Spread": 0.05, "Glow": 0.6,
                  "Sectors": 0.3, "Balance": 0.45}
    elif kind == "Spectral Eclipse":
        params = {"Reach": 0.45, "Eclipse": 0.3, "Trail": 0.5, "Glow": 0.3, "Hue": hue, "Spread": 0.05,
                  "Fallback": 0.3, "Balance": 0.4}
    elif kind == "Spectral Drops":
        params = {"Speed": 0.6, "Stillness": 0.75, "Detail": 0.25, "Size": 0.5, "Force": 0.5,
                  "Low": main + "ff", "Mid": soft + "ff", "High": dim + "ff", "Range": 0.4,
                  "Balance": 0.4}
    else:  # Spectral Shape
        params = {"Amount": 12.0, "Thickness": 0.2, "Glow": 0.2, "Animation": 0.2,
                  "Speed": 0.12, "Color 1": main + "ff", "Color 2": soft + "ff",
                  "Fallback": 0.3}
    return {"layer": AURA_LAYER, "column": column, "name": kind[9:] + " Aura", "source": kind,
            "params": params, "fft": {}, "effects": [], "opacity": OPACITY,
            "why": "Spectral pass: audio-reactive aura in the deck's own colour; FFT via Avenue's global input."}


def apply(decks, bible, report=lambda m: None):
    """Mutates decks in place. Returns the number of clips added."""
    added = 0
    for di, deck in enumerate(decks):
        dbible = (bible.get("decks") or [{}] * (di + 1))[di] if di < len(bible.get("decks") or []) else {}
        cols = collections.defaultdict(list)
        for c in deck["clips"]:
            cols[c["column"]].append(c)
        k = 0
        for col in sorted(cols):
            cs = cols[col]
            aura = next((c for c in cs if c.get("layer") == AURA_LAYER), None)
            if aura is not None and str(aura.get("why", "")).startswith("Spectral pass"):
                aura = dict(aura, source="Blank")        # re-run: replace our own earlier clip
                cs[:] = [aura if c.get("layer") == AURA_LAYER else c for c in cs]
                deck["clips"][:] = [aura if (c.get("layer") == AURA_LAYER and c.get("column") == col) else c for c in deck["clips"]]
            if aura is not None and aura.get("source") != "Blank":
                continue
            if not any(c.get("fft") or any(e.get("fft") for e in (c.get("effects") or [])) for c in cs):
                continue                     # deliberately still
            kind = KINDS[(di + k) % len(KINDS)]
            k += 1
            new = clip_for(kind, col, dbible, di)
            if aura is not None:
                deck["clips"][deck["clips"].index(aura)] = new
            else:
                deck["clips"].append(new)
            added += 1
        report("  deck %d %s: %d spectral clips" % (di + 1, deck.get("deck", ""),
                                                  sum(1 for c in deck["clips"] if str(c.get("source", "")).startswith("Spectral"))))
    return added
