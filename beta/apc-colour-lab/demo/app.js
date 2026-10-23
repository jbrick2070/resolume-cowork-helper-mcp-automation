/* app.js - the colour lab demo. PALETTE, THEMES, THEME_ORDER and APCLab are
 * defined above it by build_demo.py. Everything here is presentation: the
 * messages come from the same engine the Python router uses. */
(function () {
  "use strict";
  const E = APCLab.create(PALETTE, THEMES, THEME_ORDER);
  const { Router, Surface, RingMeter, clockTicks } = E;
  const L = APCLab;

  const el = (tag, cls, parent) => { const e = document.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; };
  const hex = (c) => "#" + c.map((x) => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2, "0")).join("");
  const $ = (id) => document.getElementById(id);

  // ---------------------------------------------------------------- state ----
  const ROW_FAMILIES = [[49, 50], [37, 38], [21, 22], [9, 10], [3, 2]];     // what a pack sends per layer row
  const EMPTY = { 4: [6, 7] };                                            // row 5 has two empty slots
  const state = { playing: [0, 3, 5, 1, 6], column: -1 };
  let router = new Router("pack", 120);
  const apc = new Surface();          // what the controller shows
  const raw = new Surface();          // what Resolume sends, untouched
  const rings = new RingMeter();
  let bpm = 120, paused = false, auto = false, lastAuto = 0, nextPress = 1.2, t0 = performance.now(), tPaused = 0;
  const logEl = $("log");
  const MAXLOG = 22;
  let sentWindow = [];                // timestamps of messages to the APC, for msgs/s

  // ---------------------------------------------------------------- build ----
  const padEls = {}, rawEls = {}, ringEls = [];
  const padwrap = $("padwrap");
  for (let r = 4; r >= 0; r--) {
    for (let c = 0; c < 8; c++) {
      const n = r * 8 + c;
      const b = el("button", "pad", padwrap);
      b.type = "button"; b.dataset.note = n; b.setAttribute("aria-label", "Pad row " + (r + 1) + " column " + (c + 1));
      padEls[n] = b;
    }
    el("span", "gap", padwrap);
    const sn = 86 - r;
    const s = el("button", "pad scene", padwrap);
    s.type = "button"; s.dataset.note = sn; s.setAttribute("aria-label", "Scene launch " + (87 - sn));
    padEls[sn] = s;
  }
  const cmp = $("compare");
  for (let r = 4; r >= 0; r--) {
    for (let c = 0; c < 8; c++) rawEls[r * 8 + c] = el("i", "", cmp);
    el("span", "", cmp);
    rawEls[86 - r] = el("i", "", cmp);
  }
  function makeRings(parent) {
    for (let i = 0; i < 8; i++) {
      const w = el("div", "ring", parent);
      const dots = [];
      for (let k = 0; k < 15; k++) {
        const d = el("i", "", w);
        const a = (-135 + k * (270 / 14)) * Math.PI / 180;
        d.style.left = (50 + 44 * Math.sin(a)) + "%";
        d.style.top = (50 - 44 * Math.cos(a)) + "%";
        dots.push(d);
      }
      el("b", "", w);
      ringEls.push(dots);
    }
  }
  makeRings($("rings-top"));
  makeRings($("rings-bottom"));
  const ledStop = $("led-stop"), ledAB = $("led-ab");
  const stopEls = [], abEls = [];
  for (let i = 0; i < 8; i++) { stopEls.push(el("i", "led", ledStop)); abEls.push(el("i", "led", ledAB)); }
  el("span", "", ledStop); el("span", "lbl", ledStop).textContent = "CLIP STOP";
  el("span", "", ledAB); el("span", "lbl", ledAB).textContent = "CROSSFADE A/B";

  // theme cards
  const themesEl = $("themes");
  const velocities = (o, out) => {
    if (Array.isArray(o)) o.forEach((x) => (typeof x === "number" ? out.push(x) : velocities(x, out)));
    else if (o && typeof o === "object") Object.keys(o).forEach((k) => {
      if ((k === "colour" || k === "secondary") && typeof o[k] === "number") out.push(o[k]); else velocities(o[k], out);
    });
    return out;
  };
  const cards = {};
  THEME_ORDER.forEach((key) => {
    const th = THEMES[key];
    const b = el("button", "theme", themesEl);
    b.type = "button"; b.setAttribute("aria-pressed", key === "pack" ? "true" : "false");
    el("span", "nm", b).textContent = th.name;
    const chips = el("div", "chips", b);
    const seen = [];
    velocities({ p: th.pairs, g: th.greys, a: th.ambient, t: th.touch, s: th.playing }, []).concat(
      key === "pack" ? [49, 37, 21, 9, 3] : []).forEach((v) => { if (v && seen.indexOf(v) < 0 && seen.length < 6) seen.push(v); });
    seen.forEach((v) => { el("span", "", chips).style.background = hex(PALETTE[v]); });
    b.addEventListener("click", () => setTheme(key));
    cards[key] = b;
  });

  // ------------------------------------------------------------- the loop ----
  function now() { return ((paused ? tPaused : performance.now()) - t0) / 1000; }

  function describe(m) {
    const [kind, ch, a, b] = m;
    if (kind === "cc") return "CC " + a + " = " + b;
    const [mode, div] = L.channelToMode(ch);
    const what = kind === "off" ? "note off" : "note on";
    const col = kind === "off" ? "" : "  colour " + b;
    return what + " n" + a + col + (mode === "primary" ? "  primary" : "  " + mode + " " + div);
  }
  function hexOf(m) {
    const base = { on: 0x90, off: 0x80, cc: 0xB0 }[m[0]];
    return [base | (m[1] - 1), m[2], m[3]].map((x) => x.toString(16).toUpperCase().padStart(2, "0")).join(" ");
  }
  function logMsg(dir, m, t) {
    const li = el("li", "");
    el("span", "dir", li).textContent = dir;
    el("span", "hex", li).textContent = hexOf(m);
    el("span", "", li).textContent = describe(m);
    const sw = el("span", "sw", li);
    sw.style.background = m[0] === "on" ? hex(PALETTE[m[3]]) : "transparent";
    logEl.insertBefore(li, logEl.firstChild);
    while (logEl.children.length > MAXLOG) logEl.removeChild(logEl.lastChild);
  }

  function emitToApc(msgs, t, quiet) {
    msgs.forEach((m) => { apc.apply(m, t); if (!quiet) logMsg("→ APC", m, t); });
    sentWindow.push([t, msgs.length]);
  }
  function fromResolume(msg, t) {
    raw.apply(msg, t);
    emitToApc(router.fromResolume(msg, t), t);
  }
  function resolumeFeedback(t) {
    // The fake Resolume: one playing clip per row, the rest loaded (dim), a couple empty.
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 8; c++) {
        const n = r * 8 + c, [on, dim] = ROW_FAMILIES[r];
        let m;
        if ((EMPTY[r] || []).indexOf(c) >= 0) m = L.off(1, n);
        else m = L.on(1, n, state.playing[r] === c ? on : dim);
        fromResolume(m, t);
      }
    }
    for (let i = 0; i < 5; i++) {
      const sn = 82 + i;
      fromResolume(L.on(1, sn, state.column === i ? 3 : 2), t);
    }
    // crossfade A/B and clip stop LEDs are single-colour buttons: Resolume drives them directly.
    renderButtons();
  }
  function renderButtons() {
    for (let i = 0; i < 8; i++) {
      abEls[i].className = "led " + (i < 4 ? "on-y" : "on-o");           // vel 1 = yellow (A), 2 = orange (B)
    }
  }

  function press(note, t) {
    const [toRes, toApc] = router.fromApc(L.on(1, note, 127), t);
    logMsg("← APC", L.on(1, note, 127), t);
    toRes.forEach((m) => logMsg("→ Res", m, t));
    emitToApc(toApc, t);
    // the fake Resolume answers: connect the clip (or the whole column) and send new feedback
    if (note >= 82) state.column = note - 82, state.playing = state.playing.map(() => note - 82);
    else { state.playing[Math.floor(note / 8)] = note % 8; state.column = -1; }
    resolumeFeedback(t);
  }

  function setTheme(key, t) {
    t = t === undefined ? now() : t;
    router = new Router(key, bpm);
    ALL_RESET(t);
    resolumeFeedback(t);
    emitToApc(router.tick(t), t);
    Object.keys(cards).forEach((k) => cards[k].setAttribute("aria-pressed", k === key ? "true" : "false"));
    $("blurb").textContent = THEMES[key].blurb;
  }
  function ALL_RESET(t) {
    L.ALL_PADS.forEach((n) => apc.apply(L.off(1, n), t));
  }

  let ringStyle = "volume";
  function driveRings(t) {
    for (let i = 0; i < 16; i++) {
      const lvl = 0.5 + 0.5 * Math.sin(t * (0.7 + i * 0.23) + i);
      const style = ringStyle;
      const msgs = rings.set(i, ringStyle === "pan" ? lvl : lvl, style);
      // light the dots the way the ring styles do
      const dots = ringEls[i];
      const v = Math.round(lvl * 127);
      dots.forEach((d, k) => {
        let lit;
        if (style === "volume") lit = v === 0 ? false : k < Math.ceil((v / 127) * 15);
        else if (style === "single") lit = k === Math.min(14, Math.floor(v / 8.5));
        else { const c = 7, p = Math.min(14, Math.floor(v / 8.5)); lit = (p >= c) ? (k >= c && k <= p) : (k <= c && k >= p); }
        d.classList.toggle("lit", lit);
      });
      msgs.forEach((m) => sentWindow.push([t, 1]));
    }
  }

  function frame() {
    const t = now();
    if (!paused) {
      if (auto && t >= nextPress) { press(Math.floor(Math.random() * 40), t); nextPress = t + 0.9 + Math.random() * 1.6; }
      emitToApc(router.tick(t), t);
      driveRings(t);
      clockSent += clockTicks(lastT, t, bpm);
      lastT = t;
    }
    for (const k in padEls) {
      const c = apc.rgb(+k, t, bpm), r = raw.rgb(+k, t, bpm);
      const bright = Math.max(c[0], c[1], c[2]);
      padEls[k].style.background = hex(c);
      padEls[k].style.boxShadow = bright > 90 ? "0 0 " + Math.round(bright / 14) + "px " + hex(c) + "88, inset 0 0 0 1px rgba(255,255,255,.1)" : "inset 0 0 0 1px rgba(255,255,255,.06)";
      rawEls[k].style.background = hex(r);
    }
    // stop-clip LEDs blink at 1/8 note (documented), driven by the same clock
    const blinkOn = (t / (L.DIV_BEATS["1/8"] * 60 / bpm)) % 1 < 0.5;
    stopEls.forEach((e, i) => { e.className = "led" + (state.playing[0] >= 0 && i % 3 === 0 && blinkOn ? " on-o" : ""); });
    // stats
    sentWindow = sentWindow.filter((x) => x[0] > t - 2);
    $("st-rate").textContent = (sentWindow.reduce((a, x) => a + x[1], 0) / 2).toFixed(0);
    let anim = 0;
    L.PAD_NOTES.forEach((n) => { if (apc.pads[n].kind !== "primary") anim++; });
    $("st-anim").textContent = anim;
    $("st-clock").textContent = clockSent;
    requestAnimationFrame(frame);
  }
  let lastT = 0, clockSent = 0;

  // ------------------------------------------------------------- controls ----
  padwrap.addEventListener("pointerdown", (e) => {
    const b = e.target.closest(".pad");
    if (b) { press(+b.dataset.note, now()); }
  });
  $("bpm").addEventListener("input", (e) => { bpm = +e.target.value; $("bpm-out").textContent = bpm + " bpm"; });
  $("auto").addEventListener("click", (e) => { auto = !auto; e.target.setAttribute("aria-pressed", auto); });
  $("pause").addEventListener("click", (e) => {
    paused = !paused; e.target.setAttribute("aria-pressed", paused); e.target.textContent = paused ? "Resume" : "Pause";
    if (paused) tPaused = performance.now(); else { t0 += performance.now() - tPaused; }
  });
  $("ringstyle").addEventListener("change", (e) => { ringStyle = e.target.value; });
  $("reset").addEventListener("click", () => { state.playing = [0, 3, 5, 1, 6]; state.column = -1; setTheme(router.themeKey); });

  // start: calm if the visitor prefers reduced motion
  setTheme("pack", 0);
  if (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches) {
    paused = true; tPaused = performance.now(); $("pause").setAttribute("aria-pressed", "true"); $("pause").textContent = "Resume";
  }
  requestAnimationFrame(frame);
  window.__lab = { setTheme, press, router: () => router, apc, state, now };
})();
