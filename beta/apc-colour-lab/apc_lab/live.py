#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live.py - run the router against real MIDI ports (mido + python-rtmidi).

NOTHING here runs unless you ask: --list only names the ports, --dry-run opens
none, and a real run opens exactly the ports you name.

The router sits ON THE LED PATH. Two topologies:

  A. The router owns the controller (works on any Windows):

       APC40 mkII  -- presses -->  router  -- forwarded -->  [loopMIDI "to-res"]   -> Resolume MIDI in
       APC40 mkII  <-- LEDs ----   router  <-- feedback ---  [loopMIDI "from-res"] <- Resolume MIDI out

     Resolume's MIDI input AND output are then the two virtual ports, not the APC.
     (loopMIDI by Tobias Erichsen is not installed on this rig; Windows MIDI
     Services' own loopback endpoints can stand in.)

  B. Windows MIDI Services multi-client: Resolume keeps the APC and the router
     opens it too, sending only LED messages. Verified for the OUTPUT port on this rig
     (a second process drove the APC's LEDs while Avenue was running, 2026-10-23); the
     input port was not tried. The router can then only ADD to what Resolume sends: its
     own feedback still reaches the controller directly, so re-colouring needs topology A.

Usage:
    python -m apc_lab.live --list
    python -m apc_lab.live --dry-run --theme halloween
    python -m apc_lab.live --dry-run --theme-file cover.json --theme cover     # a theme made from a picture
    python -m apc_lab.live --apc "APC40 mkII" --to-res "to-res" --from-res "from-res" --theme halloween

Keys while running: n / p = next / previous theme, q = quit.
"""
import argparse
import json
import os
import sys
import time

from . import engine as E
from . import protocol as P


def to_mido(msg):
    """(kind, ch, a, b) -> mido.Message (channel is 0-based in mido)."""
    import mido
    kind, ch, a, b = msg
    if kind == P.NOTE_ON:
        return mido.Message("note_on", channel=ch - 1, note=a, velocity=b)
    if kind == P.NOTE_OFF:
        return mido.Message("note_off", channel=ch - 1, note=a, velocity=b)
    return mido.Message("control_change", channel=ch - 1, control=a, value=b)


def from_mido(m):
    """mido.Message -> (kind, ch, a, b), or None for messages the router ignores."""
    if m.type == "note_on":
        return (P.NOTE_ON, m.channel + 1, m.note, m.velocity)
    if m.type == "note_off":
        return (P.NOTE_OFF, m.channel + 1, m.note, m.velocity)
    if m.type == "control_change":
        return (P.CC, m.channel + 1, m.control, m.value)
    return None


def startup_messages(mode):
    """What to send first: the mode SysEx, then every pad off."""
    return [("sysex", P.mode_sysex(mode))] + [P.off(1, n) for n in P.ALL_PADS]


def dry_run(theme, seconds, bpm):
    r = E.Router(theme, bpm)
    s = E.Surface()
    print("startup: mode SysEx", P.mode_sysex(2).hex(" ").upper(), "+ %d pad-off messages" % len(P.ALL_PADS))
    shown = 0

    def show(t, m):
        nonlocal shown
        s.apply(m, t)
        if shown < 24:
            print("t=%.2f  %s  %s" % (t, P.status_bytes(m).hex(" ").upper(), m))
            shown += 1

    # a pack-like grid arrives from Resolume (one playing clip per row), already re-coloured
    print("-- Resolume feedback, themed:")
    for row, (on, dim) in enumerate([(49, 50), (37, 38), (21, 22), (9, 10), (3, 2)]):
        for col in range(8):
            for m in r.from_resolume(P.on(1, row * 8 + col, on if col == 0 else dim), 0.0):
                show(0.0, m)
    print("-- then a press of pad 20 at t=1.0:")
    pressed = False
    t = 0.0
    while t < seconds:
        out = r.tick(t)
        if t >= 1.0 and not pressed:
            pressed = True
            out += r.from_apc(P.on(1, 20, 100), t)[1]
        for m in out:
            show(t, m)
        t = round(t + 1 / 60.0, 6)
    print("... first %d messages shown; MIDI clock bytes over %.1fs at %g bpm: %d"
          % (shown, seconds, bpm, E.clock_ticks(0.0, seconds, bpm)))


def run(args):
    import mido
    apc_in = mido.open_input(args.apc_in or args.apc)
    apc_out = mido.open_output(args.apc_out or args.apc)
    to_res = mido.open_output(args.to_res)
    from_res = mido.open_input(args.from_res)
    r = E.Router(args.theme, args.bpm)
    themes = E.THEME_ORDER
    t0 = time.perf_counter()
    last_clock_t = 0.0

    def send(msgs):
        for m in msgs:
            apc_out.send(to_mido(m) if m[0] != "sysex" else mido.Message("sysex", data=list(m[1][1:-1])))

    send(startup_messages(args.mode))
    send(r.tick(0.0))
    print("running; theme %s; n/p to change, q to quit" % args.theme)
    try:
        while True:
            t = time.perf_counter() - t0
            for m in apc_in.iter_pending():
                msg = from_mido(m)
                if msg is None:
                    continue
                forward, led = r.from_apc(msg, t)
                for f in forward:
                    to_res.send(to_mido(f))
                send(led)
            for m in from_res.iter_pending():
                msg = from_mido(m)
                if msg is not None:
                    send(r.from_resolume(msg, t))
            send(r.tick(t))
            for _ in range(E.clock_ticks(last_clock_t, t, args.bpm)):
                apc_out.send(mido.Message("clock"))
            last_clock_t = t
            if os.name == "nt":
                import msvcrt
                while msvcrt.kbhit():
                    k = msvcrt.getwch().lower()
                    if k == "q":
                        return
                    if k in "np":
                        i = (themes.index(r.theme_key) + (1 if k == "n" else -1)) % len(themes)
                        send(r.set_theme(themes[i], t))
                        print("theme:", themes[i])
            time.sleep(1 / 120.0)
    finally:
        send([P.off(1, n) for n in P.ALL_PADS])
        for port in (apc_in, apc_out, to_res, from_res):
            port.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print MIDI port names and exit (opens nothing)")
    ap.add_argument("--dry-run", action="store_true", help="simulate a short session and print the bytes (opens nothing)")
    ap.add_argument("--theme", default="halloween", help="one of: " + ", ".join(E.THEME_ORDER) + ", or the key in --theme-file")
    ap.add_argument("--theme-file", help="a theme .json made by tools/theme_from_image.py; adds it before --theme is looked up")
    ap.add_argument("--bpm", type=float, default=P.DEFAULT_BPM, help="MIDI clock tempo the pad animations follow (slower = calmer)")
    ap.add_argument("--mode", type=int, default=2, choices=(0, 1, 2), help="APC mode SysEx to send first")
    ap.add_argument("--seconds", type=float, default=3.0, help="dry-run length")
    ap.add_argument("--apc", help="APC port name (substring) for both directions")
    ap.add_argument("--apc-in"), ap.add_argument("--apc-out")
    ap.add_argument("--to-res", help="virtual port that Resolume reads presses from")
    ap.add_argument("--from-res", help="virtual port that Resolume writes LED feedback to")
    a = ap.parse_args(argv)
    if a.theme_file:
        with open(a.theme_file, encoding="utf-8") as f:
            doc = json.load(f)
        E.add_theme(doc["key"], doc["theme"])
    if a.theme not in E.THEMES:
        ap.error("unknown theme %r (known: %s)" % (a.theme, ", ".join(E.THEME_ORDER)))
    if a.list:
        import mido
        print("inputs :", mido.get_input_names())
        print("outputs:", mido.get_output_names())
        return 0
    if a.dry_run:
        dry_run(a.theme, a.seconds, a.bpm)
        return 0
    if not (a.apc or (a.apc_in and a.apc_out)) or not a.to_res or not a.from_res:
        ap.error("a real run needs --apc (or --apc-in/--apc-out), --to-res and --from-res")
    run(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
