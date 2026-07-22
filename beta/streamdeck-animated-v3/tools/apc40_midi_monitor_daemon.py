#!/usr/bin/env python3
"""APC40 V3 twin - live MIDI + spectrum + BPM monitor daemon (no Wire).

Feeds the L151 "Monitor" TextGenerator clips in
APC40_Visual_Twin_V3_Spec_Candidate over Avenue's LOCAL named-pipe REST API
(via avenue_rest_pipe.py) - the same mechanism R1's readouts used.
100% local, open-source deps only.

Readout (bottom-left corner, 4 lines, Consolas):
    CC 47  093  CUE LEVEL        <- last continuous move
    N  91  ON   PLAY             <- last note event
    L067 M045 H012 |bar|         <- audio-loopback FFT lows/mids/highs 0-127
    BPM 120.0                    <- Avenue transport BPM (live)

Deps (install once):
    pip install mido python-rtmidi pywin32
Run (with Avenue open on the Spec_Candidate comp):
    cd "C:\\Art Projects\\Res_Fable\\react-kit-apc40-v2-overnight\\beta\\streamdeck-animated-v3\\tools"
    python apc40_midi_monitor_daemon.py
Stop: Ctrl+C.

Graceful degradation: if the APC40 port is busy/absent the MIDI lines stay
dashed; if audio loopback is unavailable the FFT line stays dashed; the BPM
line only needs Avenue.
"""
import json
import os
import threading
import time

import avenue_rest_pipe as rest

MIDI_LAYER = 151       # top-right strip: CC | note (single line)
WAVE_LAYER = 152       # top-centre: scrolling block wave (single line)
BAND_LAYER = 153       # bottom-right box: L/M/H numbers + BPM (two lines)
FPS = 12.0
BLOCKS = " ▁▄█"   # Consolas-safe ramp (▂▃▅▆▇ render as tofu)


def find_text_ids(layer):
    ids = []
    for col in (1, 2):
        st, clip = rest.request("GET", f"/api/v1/composition/layers/{layer}/clips/{col}")
        if st == 200:
            try:
                ids.append(clip["video"]["sourceparams"]["Text"]["id"])
            except (KeyError, TypeError):
                pass
    return ids


def set_text(ids, text):
    for pid in ids:
        try:
            rest.request("PUT", f"/api/v1/parameter/by-id/{pid}", {"value": text})
        except Exception:
            pass


def get_bpm():
    try:
        st, comp = rest.request("GET", "/api/v1/composition")
        return float(comp["tempocontroller"]["tempo"]["value"])
    except Exception:
        return None


def load_names():
    names = {}
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "build", "build_input_v3.json")
    try:
        for r in json.load(open(path, encoding="utf-8")):
            key = int(r["raw_key"])
            status, num = key & 0xFF, (key >> 8) & 0xFF
            kind = "CC" if (status & 0xF0) == 0xB0 else "N"
            names[(kind, num)] = r["name"].upper()
    except Exception as e:
        print("name table unavailable:", e)
    return names


class State:
    def __init__(self):
        self.cc = "CC --  ---"
        self.note = "N  --  ---"
        self.fft = "L--- M--- H---"
        self.bar = ""
        self.bpm = "BPM ---.-"
        self.dirty = True
        self.lock = threading.Lock()

    def midi_text(self):
        # single line for the top-right chassis strip
        return "  |  ".join([self.cc, self.note])

    def wave_text(self):
        # the glyph wave alone, top-centre
        return self.bar or " "

    def band_text(self):
        # bottom-right box: band numbers + BPM
        return self.fft + "\n" + self.bpm


def midi_thread(st, names):
    try:
        import mido
    except ImportError:
        print("mido not installed - MIDI lines disabled")
        return
    port_name = next((n for n in mido.get_input_names()
                      if "APC40" in n.upper().replace(" ", "")), None)
    if not port_name:
        print("APC40 input port not found - MIDI lines disabled")
        return
    try:
        inp = mido.open_input(port_name)
    except Exception as e:
        print("could not open APC40 port (busy?):", e)
        return
    print("MIDI: listening on", port_name)
    for msg in inp:
        with st.lock:
            if msg.type == "control_change":
                nm = names.get(("CC", msg.control), "")
                st.cc = f"CC {msg.control:2d}  {msg.value:03d}  {nm[:14]}"
                st.dirty = True
            elif msg.type in ("note_on", "note_off"):
                on = msg.type == "note_on" and msg.velocity > 0
                nm = names.get(("N", msg.note), "")
                st.note = f"N {msg.note:3d}  {'ON ' if on else 'OFF'}  {nm[:14]}"
                st.dirty = True


def fft_thread(st):
    """L/M/H straight from Avenue's own FFT - no audio capture, no loopback.

    The spectrometer wall already animates clip opacities from Avenue's
    external FFT; polling three of them (a low-row, mid-row and high-row pad)
    over the pipe REST gives real band levels. 0.5..1.0 -> 0..127."""
    probes = {}
    for label, layer in (("L", 4), ("M", 20), ("H", 36)):
        try:
            _, clip = rest.request("GET",
                                   f"/api/v1/composition/layers/{layer}/clips/2")
            probes[label] = clip["video"]["opacity"]["id"]
        except Exception as e:
            print("fft probe", label, "unavailable:", e)
    if len(probes) < 3:
        print("fft probes incomplete - spectrum lines disabled")
        return
    print("fft probes:", probes)
    history = []
    while True:
        vals = {}
        for label, pid in probes.items():
            try:
                stt, pr = rest.request("GET", f"/api/v1/parameter/by-id/{pid}")
                v = float(pr["value"])
                vals[label] = max(0, min(127, int((v - 0.5) / 0.5 * 127)))
            except Exception:
                vals[label] = 0
        overall = max(vals.values())
        history.append(overall)
        if len(history) > 24:
            history.pop(0)
        wave = "".join(BLOCKS[min(3, v * 4 // 128)] for v in history)
        with st.lock:
            st.fft = "L{L:03d} M{M:03d} H{H:03d}".format(**vals)
            st.bar = wave
            st.dirty = True
        time.sleep(0.12)


def main():
    midi_ids = find_text_ids(MIDI_LAYER)
    wave_ids = find_text_ids(WAVE_LAYER)
    band_ids = find_text_ids(BAND_LAYER)
    if not midi_ids:
        raise SystemExit("Monitor clip not found - is the Spec_Candidate comp "
                         "open in Avenue (layers 151-153)?")
    print("midi ids:", midi_ids, "wave ids:", wave_ids, "band ids:", band_ids)
    st = State()
    threading.Thread(target=midi_thread, args=(st, load_names()), daemon=True).start()
    threading.Thread(target=fft_thread, args=(st,), daemon=True).start()
    last_bpm = 0.0
    last_midi = last_wave = last_band = None
    while True:
        now = time.time()
        if now - last_bpm > 1.0:
            bpm = get_bpm()
            if bpm is not None:
                with st.lock:
                    if f"BPM {bpm:5.1f}" != st.bpm:
                        st.bpm = f"BPM {bpm:5.1f}"
                        st.dirty = True
            last_bpm = now
        mt = wt = bt = None
        with st.lock:
            if st.dirty:
                mt, wt, bt = st.midi_text(), st.wave_text(), st.band_text()
                st.dirty = False
        if mt and mt != last_midi:
            set_text(midi_ids, mt)
            last_midi = mt
        if wt and wt != last_wave and wave_ids:
            set_text(wave_ids, wt)
            last_wave = wt
        if bt and bt != last_band and band_ids:
            set_text(band_ids, bt)
            last_band = bt
        time.sleep(1 / FPS)


if __name__ == "__main__":
    main()
