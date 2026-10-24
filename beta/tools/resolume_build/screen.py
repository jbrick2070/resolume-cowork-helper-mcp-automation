#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
screen.py - grab Avenue's window, or just its Composition Monitor, from the screen.

    from resolume_build import screen
    win = screen.grab_window()          # PIL image of the whole Avenue window
    out = screen.grab_monitor()         # just the 16:9 composition output

Windows only (ctypes + PIL.ImageGrab). The process is made DPI-aware so window
coordinates are physical pixels. Avenue is brought to the front first, so this is for
a rig the user has handed over: it takes the screen for a moment.
"""
import ctypes
import ctypes.wintypes as wt
import subprocess
import time

from PIL import ImageGrab

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()

# Where the Composition Monitor sits inside a maximised Avenue 7.28.1 window with the
# default layout, as fractions of the window's client area (measured on this rig).
MONITOR = {"x0": 0.0, "x1": 0.2485, "y_top": 0.351, "y_bottom": 0.631}


def avenue_hwnd():
    out = subprocess.check_output(["powershell", "-NoProfile", "-Command",
                                   "(Get-Process Avenue -ErrorAction Stop).MainWindowHandle"], text=True).strip()
    return int(out)


def bring_to_front(hwnd):
    # The ALT tap lets a background process take the foreground (Windows' focus rule).
    user32.keybd_event(0x12, 0, 0, 0)
    user32.keybd_event(0x12, 0, 2, 0)
    user32.ShowWindow(hwnd, 9 if user32.IsIconic(hwnd) else 5)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.6)


def client_rect(hwnd):
    r = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, pt.x + r.right, pt.y + r.bottom


def grab_window(hwnd=None, front=True):
    hwnd = hwnd or avenue_hwnd()
    if front:
        bring_to_front(hwnd)
    return ImageGrab.grab(bbox=client_rect(hwnd), all_screens=True)


def monitor_box(size):
    """The 16:9 output inside the Composition Monitor panel, in window-image pixels."""
    w, h = size
    x0, x1 = int(MONITOR["x0"] * w), int(MONITOR["x1"] * w)
    top, bottom = MONITOR["y_top"] * h, MONITOR["y_bottom"] * h
    mw = x1 - x0
    mh = int(round(mw * 9 / 16.0))
    if mh > bottom - top:                       # panel shorter than 16:9: fit by height
        mh = int(bottom - top)
        mw = int(round(mh * 16 / 9.0))
        x0 = x0 + ((x1 - x0) - mw) // 2
    y0 = int(top + ((bottom - top) - mh) / 2.0)
    return x0, y0, x0 + mw, y0 + mh


def grab_monitor(hwnd=None, front=True):
    win = grab_window(hwnd, front)
    return win.crop(monitor_box(win.size))


def pin(hwnd, on=True):
    """Keep Avenue above every other window while frames are captured (the capture reads the screen, so anything
    on top of the Composition Monitor ends up in the frames). Call pin(hwnd, False) when done."""
    HWND_TOPMOST, HWND_NOTOPMOST, SWP_NOMOVE, SWP_NOSIZE, SWP_SHOWWINDOW = -1, -2, 0x2, 0x1, 0x40
    user32.SetWindowPos(hwnd, HWND_TOPMOST if on else HWND_NOTOPMOST, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | (SWP_SHOWWINDOW if on else 0))
