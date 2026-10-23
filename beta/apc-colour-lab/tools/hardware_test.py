#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hardware_test.py - a staged look at how a real APC40 mkII answers the LED messages the
colour lab depends on. Someone has to WATCH THE CONTROLLER; the controller does not
report its LEDs back, so nothing here can see the result.

  python tools/hardware_test.py --dry-run          # print the plan, open nothing
  python tools/hardware_test.py --port "APC40 mkII 1"

It opens ONE output port, sends only note-on / note-off (and MIDI clock for the
tempo stages), never sends the mode SysEx (so the controller's current mode is
left alone), and clears every pad and stops the clock when it ends or is interrupted.
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from apc_lab import protocol as P          # noqa: E402

PADS = list(P.PAD_NOTES)
SCENES = list(P.SCENE_NOTES)
RATE_ROWS = ["1/2", "1/4", "1/8", "1/16", "1/24"]      # row 1 (bottom) slowest ... row 5 fastest
TEST_BPM = int(P.DEFAULT_BPM)       # 120 was "a bit too fast" on the first hardware look (2026-10-23)


class Rig(object):
    """Sends messages, keeps time, and can run the MIDI clock in the background of sleeps."""

    def __init__(self, port, dry):
        self.dry, self.port, self.sent = dry, None, 0
        self.bpm = None
        self._tick_t = 0.0
        if not dry:
            import mido
            self.mido = mido
            self.port = mido.open_output(port)

    def send(self, msg):
        self.sent += 1
        if self.dry:
            return
        kind, ch, a, b = msg
        if kind == P.NOTE_ON:
            self.port.send(self.mido.Message("note_on", channel=ch - 1, note=a, velocity=b))
        elif kind == P.NOTE_OFF:
            self.port.send(self.mido.Message("note_off", channel=ch - 1, note=a, velocity=0))

    def raw(self, name):
        self.sent += 1
        if not self.dry:
            self.port.send(self.mido.Message(name))

    def sleep(self, seconds):
        """Sleep, sending MIDI clock (24 per quarter note) if a tempo is set."""
        end = time.perf_counter() + seconds
        if self.dry:
            return
        next_tick = time.perf_counter()
        while True:
            now = time.perf_counter()
            if now >= end:
                return
            if self.bpm and now >= next_tick:
                self.raw("clock")
                next_tick += 60.0 / (self.bpm * 24.0)
                continue
            time.sleep(0.0005)

    def clock(self, bpm):
        if bpm and not self.bpm:
            self.raw("start")
        if not bpm and self.bpm:
            self.raw("stop")
        self.bpm = bpm

    def close(self):
        if self.port:
            self.port.close()


def clear(rig):
    for n in PADS + SCENES:
        rig.send(P.off(1, n))


def prim(rig, n, v):
    rig.send(P.on(1, n, v))


def anim(rig, n, kind, div, v):
    rig.send(P.on(P.mode_to_channel(kind, div), n, v))


def say(msg):
    print("\n[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def stage_dark(rig):
    say("1. DARK - every pad off for 3 s. Expect: all 40 pads and 5 scene pads dark.")
    clear(rig)
    rig.sleep(3)


def stage_palette(rig):
    say("2. PALETTE - 8 hues across, brightness ladder down (bottom row full, then light, dim, very dim, greys on top). 7 s.")
    for row in range(4):
        for col in range(8):
            # hue families run in fours: +0 light, +1 full, +2 dim, +3 very dim (velocity 4..59)
            base = 4 + 4 * col
            prim(rig, P.pad_note(col, row), base + (1, 0, 2, 3)[row])
    for col, v in enumerate((0, 1, 117, 118, 2, 3, 3, 3)):
        if v:
            prim(rig, P.pad_note(col, 4), v)
    rig.sleep(7)


def stage_pulse(rig, title, bpm, seconds):
    say(title)
    clear(rig)
    rig.clock(bpm)
    for row, div in enumerate(RATE_ROWS):
        for col in range(8):
            n = P.pad_note(col, row)
            prim(rig, n, 46)                       # dark blue, the primary
            anim(rig, n, "pulsing", div, 45)       # pulsing to bright blue
    rig.sleep(seconds)


def stage_blink(rig):
    say("6. BLINK at %d bpm - red alternating with white, rows at five rates. 8 s." % TEST_BPM)
    clear(rig)
    rig.clock(TEST_BPM)
    for row, div in enumerate(RATE_ROWS):
        for col in range(8):
            n = P.pad_note(col, row)
            prim(rig, n, 5)
            anim(rig, n, "blinking", div, 3)
    rig.sleep(8)


def stage_oneshot(rig):
    say("7. ONE-SHOT WAVE - dim violet pads; every 2.2 s a white ring of one-shot flashes spreads out from the middle pad. 3 waves.")
    clear(rig)
    rig.clock(TEST_BPM)
    for n in PADS:
        prim(rig, n, 50)
    c0, r0 = 3, 2
    for wave in range(3):
        plan = sorted(((max(abs(P.pad_col_row(n)[0] - c0), abs(P.pad_col_row(n)[1] - r0)) * 0.07, n) for n in PADS))
        t0 = time.perf_counter()
        for delay, n in plan:
            while not rig.dry and time.perf_counter() - t0 < delay:
                rig.sleep(0.002)
            anim(rig, n, "oneshot", "1/4", 3)
        rig.sleep(1.5)


def stage_cancel(rig):
    say("8. CANCEL - all pads blink red/white for 4 s, then the LEFT half is re-sent its primary on channel 1 (should stop blinking), 4 s, then all off.")
    clear(rig)
    rig.clock(TEST_BPM)
    for n in PADS:
        prim(rig, n, 5)
        anim(rig, n, "blinking", "1/4", 3)
    rig.sleep(4)
    say("   ... left half re-sent as plain red")
    for n in PADS:
        if P.pad_col_row(n)[0] < 4:
            prim(rig, n, 5)
    rig.sleep(4)
    clear(rig)
    rig.sleep(1)


def stage_scene(rig):
    say("9. SCENE LAUNCH pads (the 5 on the right) - five colours for 3 s, then each blinks. 7 s.")
    clear(rig)
    rig.clock(TEST_BPM)
    for n, v in zip(SCENES, (5, 9, 13, 21, 45)):
        prim(rig, n, v)
    rig.sleep(3)
    for n in SCENES:
        anim(rig, n, "blinking", "1/2", 3)
    rig.sleep(4)


def run(rig, only):
    plan = [
        ("dark", lambda: stage_dark(rig)),
        ("palette", lambda: stage_palette(rig)),
        ("pulse0", lambda: stage_pulse(rig, "3. PULSE with NO clock - dark blue breathing to bright blue; bottom row slowest (1/2), top row fastest (1/24). 8 s.", None, 8)),
        ("pulse60", lambda: stage_pulse(rig, "4. PULSE with MIDI clock at %d bpm - same pads. 8 s." % TEST_BPM, TEST_BPM, 8)),
        ("pulse120", lambda: stage_pulse(rig, "5. PULSE with MIDI clock at %d bpm - should be twice as fast as stage 4 if the pads follow the clock (120 was the rate judged too fast). 8 s." % (TEST_BPM * 2), TEST_BPM * 2, 8)),
        ("blink", lambda: stage_blink(rig)),
        ("oneshot", lambda: stage_oneshot(rig)),
        ("cancel", lambda: stage_cancel(rig)),
        ("scene", lambda: stage_scene(rig)),
    ]
    for key, fn in plan:
        if only and key not in only:
            continue
        fn()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", default="APC40 mkII 1", help="MIDI OUTPUT port name")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma list of stages: dark,palette,pulse0,pulse60,pulse120,blink,oneshot,cancel,scene")
    ap.add_argument("--countdown", type=int, default=5)
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    rig = Rig(a.port, a.dry_run)
    try:
        if not a.dry_run and a.countdown:
            say("starting in %d s - watch the controller" % a.countdown)
            time.sleep(a.countdown)
        run(rig, only)
    finally:
        try:
            rig.clock(None)
            clear(rig)
        finally:
            rig.close()
        say("done; pads cleared and the clock stopped. %d messages sent." % rig.sent)


if __name__ == "__main__":
    main()
