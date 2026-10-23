// Runs a scenario (JSON on stdin) through the JavaScript engine and prints the
// messages it emits as JSON. Used by tools/parity.py.
"use strict";
const fs = require("fs");
const path = require("path");
const lab = require("./engine.js");

const root = path.join(__dirname, "..", "apc_lab");
const PALETTE = JSON.parse(fs.readFileSync(path.join(root, "palette.json"), "utf8")).colours;
const T = JSON.parse(fs.readFileSync(path.join(root, "themes.json"), "utf8"));
const E = lab.create(PALETTE, T.themes, T.order);

const scenario = JSON.parse(fs.readFileSync(0, "utf8"));
const router = new E.Router(scenario.theme, scenario.bpm);
const surface = new E.Surface();
const log = [];
for (const ev of scenario.events) {
  let msgs = [];
  if (ev.kind === "resolume") msgs = router.fromResolume(ev.msg, ev.t);
  else if (ev.kind === "apc") msgs = router.fromApc(ev.msg, ev.t)[1];
  else if (ev.kind === "theme") msgs = router.setTheme(ev.theme, ev.t);
  else if (ev.kind === "tick") msgs = router.tick(ev.t);
  msgs.forEach((m) => surface.apply(m, ev.t));
  log.push(msgs);
}
const samples = scenario.samples.map((s) => lab.ALL_PADS.map((n) => surface.rgb(n, s, scenario.bpm).map((x) => Math.round(x * 1000) / 1000)));
process.stdout.write(JSON.stringify({ log, samples }));
