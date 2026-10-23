/* engine.js - the colour lab's engine in JavaScript, a line-for-line port of
 * apc_lab/engine.py so the HTML demo and the Python router produce the same
 * messages. tools/parity.py runs one scenario through both and diffs them.
 *
 * It expects PALETTE (128 [r,g,b]) and THEMES / THEME_ORDER to be supplied by
 * the host (the demo inlines them; node loads the same JSON files).
 */
(function (root) {
  "use strict";

  const DIVS = ["1/24", "1/16", "1/8", "1/4", "1/2"];
  const DIV_BEATS = { "1/24": 4 / 24, "1/16": 0.25, "1/8": 0.5, "1/4": 1.0, "1/2": 2.0 };
  const SCENE_NOTES = [82, 83, 84, 85, 86];
  const PAD_NOTES = Array.from({ length: 40 }, (_, i) => i);
  const ALL_PADS = PAD_NOTES.concat(SCENE_NOTES);
  const NOTE_ON = "on", NOTE_OFF = "off", CC = "cc";

  function padColRow(note) {
    if (note >= 82 && note <= 86) return [8, 86 - note];
    return [note % 8, Math.floor(note / 8)];
  }
  function modeToChannel(kind, div) {
    if (kind === "primary") return 1;
    return { oneshot: 2, pulsing: 7, blinking: 12 }[kind] + DIVS.indexOf(div);
  }
  function channelToMode(ch) {
    if (ch < 1 || ch > 16) throw new Error("MIDI channel out of range: " + ch);
    if (ch === 1) return ["primary", null];
    if (ch <= 6) return ["oneshot", DIVS[ch - 2]];
    if (ch <= 11) return ["pulsing", DIVS[ch - 7]];
    return ["blinking", DIVS[ch - 12]];
  }
  const on = (ch, note, vel) => [NOTE_ON, ch, note, vel];
  const off = (ch, note) => [NOTE_OFF, ch, note, 0];
  const cc = (ch, ctrl, val) => [CC, ch, ctrl, val];

  // Deterministic 0..1 hash, bit-identical to engine.py's hash01.
  function hash01(a, b) {
    let h = (Math.imul(a, 374761393) + Math.imul(b, 668265263)) >>> 0;
    h = Math.imul((h ^ (h >>> 13)) >>> 0, 1274126177) >>> 0;
    h = (h ^ (h >>> 16)) >>> 0;
    return (h & 0xFFFFFF) / 0x1000000;
  }
  const lerp = (a, b, w) => [a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w, a[2] + (b[2] - a[2]) * w];
  const luma = (c) => (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255.0;

  // The (on, dim) velocity pairs the packs send, in hue order (see engine.py).
  const FAMILIES = [[5, 6], [9, 10], [13, 14], [17, 18], [21, 22], [25, 26],
                    [37, 38], [41, 42], [45, 46], [49, 50], [53, 54], [57, 58]];
  const FEEDBACK = {};
  FAMILIES.forEach((p, i) => { FEEDBACK[p[0]] = [i, "on"]; FEEDBACK[p[1]] = [i, "dim"]; });
  FEEDBACK[3] = [null, "on"];
  FEEDBACK[2] = [null, "dim"];

  function create(PALETTE, THEMES, THEME_ORDER) {
    // ---- the surface ----------------------------------------------------------
    class Surface {
      constructor() {
        this.pads = {};
        ALL_PADS.forEach((n) => { this.pads[n] = { p: 0, s: 0, kind: "primary", div: null, t: 0 }; });
      }
      apply(msg, t) {
        const [kind, ch, note, vel] = msg;
        const pad = this.pads[note];
        if (pad === undefined || kind === CC) return;
        const [mode, div] = channelToMode(ch);
        if (kind === NOTE_OFF || (kind === NOTE_ON && vel === 0)) {
          if (mode === "primary") { pad.p = 0; pad.s = 0; pad.kind = "primary"; pad.div = null; }
          else { pad.s = 0; pad.kind = "primary"; pad.div = null; }
          return;
        }
        if (mode === "primary") { pad.p = vel; pad.s = 0; pad.kind = "primary"; pad.div = null; pad.t = t; }
        else { pad.s = vel; pad.kind = mode; pad.div = div; pad.t = t; }
      }
      rgb(note, t, bpm) {
        const pad = this.pads[note];
        const prim = PALETTE[pad.p], sec = PALETTE[pad.s];
        if (pad.kind === "primary") return prim.slice();
        const period = DIV_BEATS[pad.div] * 60.0 / bpm;
        const phase = (t - pad.t) / period;
        if (pad.kind === "oneshot") return (phase >= 0 && phase < 1) ? sec.slice() : prim.slice();
        if (pad.kind === "pulsing") return lerp(prim, sec, 0.5 - 0.5 * Math.cos(2 * Math.PI * phase));
        const f = phase - Math.floor(phase);
        return f < 0.5 ? sec.slice() : prim.slice();
      }
    }

    const secEq = (a, b) => (a === null || b === null) ? a === b : (a[0] === b[0] && a[1] === b[1] && a[2] === b[2]);

    // ---- the router -------------------------------------------------------------
    class Router {
      constructor(theme, bpm) {
        this.bpm = bpm || 120.0;
        this.themeKey = theme || "pack";
        this.base = {}; this.sent = {};
        ALL_PADS.forEach((n) => { this.base[n] = 0; this.sent[n] = [0, null]; });
        this.queue = [];
        this.seq = 0;
        this.presses = 0;
      }
      get theme() { return THEMES[this.themeKey]; }
      setTheme(key, t) { this.themeKey = key; return this.tick(t); }

      fromApc(msg, t) {
        let out = [];
        const [kind, ch, note, vel] = msg;
        if (kind === NOTE_ON && vel > 0 && note < 40 && ch === 1) {
          this.presses += 1;
          out = this._touch(note, t);
        }
        return [[msg], out];
      }
      fromResolume(msg, t) {
        const [kind, ch, note, vel] = msg;
        if (Object.prototype.hasOwnProperty.call(this.base, note) && kind !== CC) {
          const isOn = kind === NOTE_ON && vel > 0;
          this.base[note] = isOn ? vel : 0;
          return this._refresh(note, t);
        }
        return [msg];
      }
      tick(t) {
        const out = [];
        this.queue.sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
        while (this.queue.length && this.queue[0][0] <= t) out.push(this.queue.shift()[2]);
        ALL_PADS.forEach((n) => { this._refresh(n, t).forEach((m) => out.push(m)); });
        return out;
      }

      desired(note, t) {
        const v = this.base[note];
        const th = this.theme;
        if (v) return this._remap(note, v, th);
        if (note >= 82) return [0, null];
        return this._ambient(note, t, th);
      }
      _remap(note, v, th) {
        const mode = th.remap;
        const fb = FEEDBACK[v];
        const fam = fb ? fb[0] : null, state = fb ? fb[1] : null;
        if (mode === "identity" || state === null) return [v, null];
        const playing = th.playing;
        let sec = (playing && state === "on") ? [playing.colour, playing.kind, playing.div] : null;
        if (note >= 82 && state === "on" && th.scene) {
          const s = th.scene;
          return [s.colour, [s.secondary, s.kind, s.div]];
        }
        if (mode === "pairs") {
          const pairs = th.pairs;
          const pair = pairs[(fam !== null ? fam : 0) % pairs.length];
          if (fam === null) {
            sec = (sec && playing) ? [pairs[0][0], playing.kind, playing.div] : null;
            return [state === "on" ? 3 : 2, sec];
          }
          if (state !== "on") return [pair[1], null];
          if (playing) sec = [pair[2], playing.kind, playing.div];
          return [pair[0], sec];
        }
        const greys = th.greys;
        const lum = luma(PALETTE[v]);
        let idx = lum < 0.12 ? 0 : lum < 0.30 ? 1 : lum < 0.50 ? 2 : lum < 0.75 ? 3 : 4;
        if (state === "on") idx = 4; else idx = Math.min(idx, 2);
        if (mode === "luma-invert") idx = greys.length - 1 - idx;
        return [greys[idx], sec];
      }
      _ambient(note, t, th) {
        const a = th.ambient, kind = a.kind;
        const [col, row] = padColRow(note);
        if (kind === "none") return [0, null];
        if (kind === "fill") return [a.colour, null];
        const cs = a.colours;
        if (kind === "pulse") return [cs[0], [cs[1], "pulsing", a.div]];
        if (kind === "stripes") return [cs[row % cs.length], null];
        const k = Math.floor(t * a.rate);
        if (kind === "flicker") {
          if (hash01(note, k) < a.density) return [cs[Math.floor(hash01(note + 101, k) * cs.length)], null];
          return [0, null];
        }
        if (kind === "chase") {
          const i = row * 8 + (row % 2 === 0 ? col : 7 - col);
          return [cs[(((i - k) % cs.length) + cs.length) % cs.length], null];
        }
        if (kind === "rain") {
          const rel = (row + k + col * 3) % 10;
          return rel < cs.length ? [cs[rel], null] : [0, null];
        }
        if (kind === "scan") {
          const d = Math.abs(row - (k % 5));
          return d < cs.length ? [cs[d], null] : [0, null];
        }
        return [0, null];
      }
      _refresh(note, t) {
        const want = this.desired(note, t);
        const have = this.sent[note];
        if (want[0] === have[0] && secEq(want[1], have[1])) return [];
        const out = [];
        const p = want[0], sec = want[1];
        if (p !== have[0] || (sec === null && have[1] !== null) || !secEq(sec, have[1])) {
          out.push(p ? on(1, note, p) : off(1, note));
        }
        if (sec !== null) out.push(on(modeToChannel(sec[1], sec[2]), note, sec[0]));
        this.sent[note] = want;
        return out;
      }
      _touch(note, t) {
        const tc = this.theme.touch, kind = tc.kind;
        if (kind === "none") return [];
        const ch = modeToChannel("oneshot", tc.div);
        const cs = tc.colours;
        const [c0, r0] = padColRow(note);
        const plan = [];
        PAD_NOTES.forEach((m) => {
          const [c, r] = padColRow(m);
          const dc = Math.abs(c - c0), dr = Math.abs(r - r0);
          if (kind === "ripple") {
            const d = Math.max(dc, dr);
            plan.push([d * tc.step, m, cs[d % cs.length]]);
          } else if (kind === "cross" && (dc === 0 || dr === 0)) {
            const d = dc + dr;
            plan.push([d * tc.step, m, cs[d % cs.length]]);
          } else if (kind === "invert") {
            plan.push([0.0, m, this.base[m] ? cs[0] : cs[1]]);
          }
        });
        if (kind === "sparkle") {
          for (let j = 0; j < tc.count; j++) {
            const m = Math.floor(hash01(j + 1, this.presses) * 40);
            plan.push([hash01(j + 50, this.presses) * 0.35, m, cs[Math.floor(hash01(j + 90, this.presses) * cs.length)]]);
          }
        }
        plan.sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]));
        const out = [];
        plan.forEach(([delay, m, colour]) => {
          const msg = on(ch, m, colour);
          if (delay <= 0) out.push(msg);
          else { this.seq += 1; this.queue.push([t + delay, this.seq, msg]); }
        });
        return out;
      }
    }

    // ---- rings and clock -----------------------------------------------------------
    const RING_STYLES = { off: 0, single: 1, volume: 2, pan: 3 };
    class RingMeter {
      constructor() { this.style = new Array(16).fill(null); this.value = new Array(16).fill(null); }
      static ccs(i) { return i < 8 ? [48 + i, 56 + i] : [16 + (i - 8), 24 + (i - 8)]; }
      set(i, level, style) {
        const out = [];
        const [valueCc, styleCc] = RingMeter.ccs(i);
        const s = RING_STYLES[style || "volume"];
        if (this.style[i] !== s) { out.push(cc(1, styleCc, s)); this.style[i] = s; }
        const v = Math.max(0, Math.min(127, Math.round(level * 127)));
        if (this.value[i] !== v) { out.push(cc(1, valueCc, v)); this.value[i] = v; }
        return out;
      }
    }
    const clockTicks = (t0, t1, bpm) => Math.floor(t1 * bpm * 24 / 60.0) - Math.floor(t0 * bpm * 24 / 60.0);

    return { Surface, Router, RingMeter, clockTicks };
  }

  const api = {
    create, DIVS, DIV_BEATS, SCENE_NOTES, PAD_NOTES, ALL_PADS, padColRow, modeToChannel, channelToMode,
    on, off, cc, hash01, FAMILIES, FEEDBACK,
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.APCLab = api;
})(typeof self !== "undefined" ? self : this);
