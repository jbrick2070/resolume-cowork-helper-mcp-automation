#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apc_map_html.py - a self-contained, read-only HTML cheat sheet of an APC40
mkII MIDI preset, drawn as the physical board and labelled from the
composition it drives.

Generic: it reads ANY Resolume MIDI shortcut preset (.xml) and, optionally,
the .avc it belongs to, so it works for every pack in this repo, not only the
ones resolume_build made. Nothing is triggered; the page needs no server.

    python -m resolume_build.apc_map_html PRESET.xml [--avc COMP.avc] [--out X.html]
    python -m resolume_build.apc_map_html --all react-kit/beta

--all pairs every .avc with the preset named in its MidiShortcutPreset
parameter and writes an index page linking every map.

Idea and board-as-grid presentation credit: Rieger Gergo's ROGGER
(github.com/riegergogi2001/resolume-rogger, MIT), docs/apc40-mapping.html.
"""
import argparse
import glob
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

NOTE_MARKER = 1 << 56
CC_MARKER = 1 << 57

# APC40 mkII RGB velocity palette (same family as Ableton's 128-colour pad
# palette). Indices 0-3 are black/greys; from 4 on, groups of four step
# through hues: bright tint, full, dim, dark. Approximate, for display only.
_HUES = ["#ff4a4a", "#ff8a1a", "#ffe11a", "#a6ff1a", "#3dff3d", "#1aff8a",
         "#1affc4", "#1ae6ff", "#1aa8ff", "#1a5cff", "#5c1aff", "#a61aff",
         "#ff1ae6", "#ff1a8a", "#ff5c1a", "#c4a61a"]


def led_rgb(v):
    if v is None:
        return None
    v = int(round(v))
    if v <= 0:
        return None
    if v < 4:
        return ["#000000", "#3a3a3a", "#8a8a8a", "#ffffff"][v]
    g, k = divmod(v - 4, 4)
    base = _HUES[g % len(_HUES)]
    r, gg, b = (int(base[i:i + 2], 16) for i in (1, 3, 5))
    f = [1.0, 1.0, 0.45, 0.22][k]
    if k == 0:
        r, gg, b = (int(c + (255 - c) * 0.35) for c in (r, gg, b))
    return "#%02x%02x%02x" % tuple(int(c * f) for c in (r, gg, b))


def slug(name):
    return "".join(ch.lower() for ch in name if ch.isalnum())


# ----------------------------------------------------------------- preset --
def decode_key(key):
    status = key & 0xFF
    data1 = (key >> 8) & 0xFF
    kind = "cc" if key & CC_MARKER else "note"
    return kind, (status & 0x0F) + 1, data1


def read_preset(path):
    root = ET.parse(path).getroot()
    out = []
    for sc in root.iter("Shortcut"):
        raw = sc.find("RawInputMessage")
        ip = sc.find("ShortcutPath[@name='InputPath']")
        if raw is None or ip is None:
            continue
        kind, ch, d1 = decode_key(int(raw.get("key")))
        leds = {}
        nv = sc.find("NamedValues")
        if nv is not None:
            for v in nv.findall("Value"):
                try:
                    leds[v.get("first")] = float(v.get("second")) * 127.0
                except (TypeError, ValueError):
                    pass
        vr = sc.find("ValueRange")
        out.append({"kind": kind, "ch": ch, "n": d1, "path": ip.get("path"),
                    "behaviour": sc.get("behaviour"),
                    "range": [vr.get("min"), vr.get("max")] if vr is not None
                    else None, "leds": leds})
    return root.get("name") or os.path.basename(path), out


# ------------------------------------------------------------ composition --
def _pname(el):
    p = el.find("./Params/Param[@name='Name']")
    return p.get("value") if p is not None else None


def read_avc(path):
    root = ET.parse(path).getroot()
    info = {"name": None, "layers": [], "decks": [], "effects": {},
            "layer_effects": {}, "links": {}, "preset": None}
    info["name"] = _pname(root)
    mp = root.find("./Params/Param[@name='MidiShortcutPreset']")
    info["preset"] = mp.get("value") if mp is not None else None
    for p in root.findall("./Params[@name='Dashboard']/ParamRange"):
        m = re.match(r"Link (\d+)", p.get("name", ""))
        if m:
            info["links"][int(m.group(1))] = p.get("altName") or p.get("name")
    chain = root.find("./VideoTrack/RenderPass[@name='RenderPassChain']")
    if chain is not None:
        for rp in chain.findall("RenderPass"):
            nm = rp.get("name")
            if nm and nm != "Transform":
                info["effects"].setdefault(slug(nm), nm)
    for L in root.findall("Layer"):
        info["layers"].append(_pname(L) or "Layer %d"
                              % (int(L.get("layerIndex")) + 1))
        ch = L.find("./VideoTrack/RenderPass[@name='RenderPassChain']")
        fx = {}
        if ch is not None:
            for rp in ch.findall("RenderPass"):
                nm = rp.get("name")
                if nm and nm != "Transform":
                    fx[slug(nm)] = nm
        info["layer_effects"][len(info["layers"])] = fx
    for d in root.findall("Deck"):
        deck = {"name": _pname(d) or "Deck %d" % (int(d.get("deckIndex")) + 1),
                "columns": {}, "clips": {}}
        for c in d.findall("Column"):
            deck["columns"][int(c.get("columnIndex")) + 1] = _pname(c) or ""
        for c in d.findall("Clip"):
            nm = _pname(c) or ""
            src = ""
            rp = c.find("./VideoTrack/PrimarySource/VideoSource/RenderPass")
            if rp is not None:
                src = rp.get("name") or ""
            else:
                f = c.find(".//VideoFormatReaderSource")
                if f is not None:
                    src = os.path.basename(f.get("fileName") or "")
            deck["clips"]["%d,%d" % (int(c.get("layerIndex")) + 1,
                                     int(c.get("columnIndex")) + 1)] = [nm, src]
        if deck["clips"] or deck["columns"]:
            info["decks"].append(deck)
    return info


# ---------------------------------------------------------------- labels --
def describe(path, comp, rng):
    """Plain-words label for a shortcut path, resolved against the comp."""
    p = path or ""
    lay = (comp or {}).get("layers", [])

    def lname(n):
        n = int(n)
        return lay[n - 1] if 0 < n <= len(lay) else "layer %d" % n

    m = re.match(r"/composition/layers/(\d+)/clips/(\d+)/connect$", p)
    if m:
        return {"t": "clip", "layer": int(m.group(1)), "col": int(m.group(2)),
                "label": "%s clip %s" % (lname(m.group(1)), m.group(2))}
    m = re.match(r"/composition/columns/(\d+)/connect$", p)
    if m:
        return {"t": "column", "col": int(m.group(1)),
                "label": "Scene %s" % m.group(1)}
    m = re.match(r"/composition/video/effects/([^/]+)/(.*)$", p)
    if m:
        eff = (comp or {}).get("effects", {}).get(m.group(1), m.group(1))
        rest = m.group(2)
        if rest == "bypassed":
            return {"t": "fx", "label": "%s on/off" % eff}
        rest = rest.replace("effect/", "").replace("behaviour/", "FFT ")
        return {"t": "fxparam", "label": "%s %s" % (eff, rest.replace("/", " "))}
    m = re.match(r"/composition/layers/(\d+)/video/effects/([^/]+)/(.*)$", p)
    if m:
        fx = (comp or {}).get("layer_effects", {}).get(int(m.group(1)), {})
        eff = fx.get(m.group(2), m.group(2))
        return {"t": "fx", "label": "%s: %s %s" % (lname(m.group(1)), eff,
                                                    m.group(3).replace("/", " "))}
    m = re.match(r"/composition/dashboard/link(\d+)$", p)
    if m:
        nm = (comp or {}).get("links", {}).get(int(m.group(1)),
                                                "link %s" % m.group(1))
        if rng and rng[0] == rng[1]:
            return {"t": "dash", "label": "%s -> %s" % (nm, rng[0])}
        return {"t": "dash", "label": "Macro %s" % nm}
    m = re.match(r"/composition/selectedclip/dashboard/link(\d+)$", p)
    if m:
        return {"t": "dash", "label": "Selected clip dial %s" % m.group(1)}
    m = re.match(r"/composition/layers/(\d+)/(.*)$", p)
    if m:
        what = {"clear": "eject", "select": "select", "bypassed": "mute",
                "solo": "solo", "master": "level", "video/opacity": "opacity",
                "connectnextclip": "next clip",
                "connectprevclip": "previous clip"}.get(m.group(2),
                                                       m.group(2).replace("/", " "))
        return {"t": "layer", "label": "%s %s" % (lname(m.group(1)), what)}
    simple = {
        "/composition/bypassed": "BLACKOUT",
        "/composition/disconnectall": "Eject everything",
        "/composition/master": "Master level",
        "/composition/crossfader/phase": "Crossfader",
        "/composition/speed": "Composition speed",
        "/composition/selectnextdeck": "Next deck",
        "/composition/selectprevdeck": "Previous deck",
        "/composition/connectnextcolumn": "Next scene",
        "/composition/connectprevcolumn": "Previous scene",
        "/composition/tempocontroller/tempotap": "Tap tempo",
        "/composition/tempocontroller/resync": "Tempo resync",
        "/composition/tempocontroller/tempo": "Tempo",
        "/composition/select": "Select composition",
        "/audiodevicemanager/params/fftinputgain": "FFT input gain",
    }
    if p in simple:
        lab = simple[p]
        if p == "/composition/speed" and rng and rng[0] == rng[1]:
            lab = "Composition speed -> 1x" if rng[0] == "0.1" else lab
        if p == "/audiodevicemanager/params/fftinputgain" and rng and rng[0] == rng[1]:
            lab = "FFT input gain -> home"
        if p == "/composition/crossfader/phase" and rng and rng[0] == rng[1]:
            lab = "Crossfader -> %s" % {"0": "A", "1": "B", "0.5": "centre"}.get(
                rng[0], rng[0])
        return {"t": "global", "label": lab}
    return {"t": "other", "label": p.replace("/composition/", "")
            .replace("/", " ")}


# ------------------------------------------------------------------ board --
def build_model(preset_path, avc_path=None):
    pname, shortcuts = read_preset(preset_path)
    comp = read_avc(avc_path) if avc_path else None
    controls = {}
    for sc in shortcuts:
        k = "%s:%d:%d" % (sc["kind"], sc["ch"], sc["n"])
        d = describe(sc["path"], comp, sc["range"])
        led = None
        for st in ("Connected", "On", "Off", "Disconnected"):
            if st in sc["leds"]:
                led = led_rgb(sc["leds"][st])
                if led:
                    break
        controls.setdefault(k, []).append({
            "path": sc["path"], "label": d["label"], "t": d["t"],
            "layer": d.get("layer"), "col": d.get("col"), "led": led,
            "range": sc["range"]})
    return {"preset": pname, "preset_file": os.path.basename(preset_path),
            "comp": comp, "controls": controls,
            "count": len(shortcuts)}


PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#0b0c0e;--p1:#14161a;--p2:#1b1e23;--line:#2a2e35;--t:#e9edf3;--d:#8d939c;--a:#ffb03a}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f4f2ee;--p1:#ffffff;--p2:#ece9e3;--line:#d3cfc7;--t:#16181b;--d:#5d636b;--a:#b4570a}}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--t);font:13px/1.4 "Segoe UI",system-ui,sans-serif;padding:20px 16px;max-width:1320px;margin:0 auto}
h1{font-size:20px;letter-spacing:.08em}h1 b{color:var(--a)}
.meta{color:var(--d);font-size:12px;margin:4px 0 14px}
.bar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
select,input{background:var(--p1);color:var(--t);border:1px solid var(--line);border-radius:6px;padding:6px 8px;font:inherit}
.wrap{overflow-x:auto}
.board{display:grid;grid-template-columns:92px repeat(8,minmax(62px,1fr)) 86px 16px repeat(4,minmax(58px,1fr));gap:4px;min-width:1080px}
.z{font-size:9px;font-weight:700;letter-spacing:.06em;color:var(--d);text-transform:uppercase;display:flex;align-items:center}
.c{border:1px solid var(--line);border-radius:6px;background:var(--p2);min-height:40px;padding:3px 4px;font-size:10px;font-weight:600;overflow:hidden;cursor:pointer;position:relative;word-break:break-word}
.c small{display:block;font-weight:400;color:var(--d);font-size:9px}
.c.knob{border-radius:18px;text-align:center}
.c.none{opacity:.25;cursor:default}
.c.sel{outline:2px solid var(--a)}
.c i{position:absolute;left:0;top:0;bottom:0;width:5px}
.c.multi::after{content:attr(data-n);position:absolute;right:3px;top:2px;font-size:9px;color:var(--a)}
.gap{grid-column:span 1}
#info{margin:14px 0;padding:12px;border:1px solid var(--line);border-radius:8px;background:var(--p1);min-height:64px}
#info code{color:var(--d);font-size:11px}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:12px}
th,td{text-align:left;padding:5px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--d);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
td code{color:var(--d);font-size:11px}
.foot{color:var(--d);font-size:11px;margin-top:18px}
</style></head><body>
<h1><b>APC40 mkII</b> &middot; __H1__</h1>
<div class="meta" id="meta"></div>
<div class="bar"><label>Deck <select id="deck"></select></label>
<input id="q" placeholder="Search controls, paths, clips..." size="34"></div>
<div class="wrap"><div class="board" id="board"></div></div>
<div id="info">Click any control.</div>
<h2 style="font-size:12px;letter-spacing:.12em;color:var(--d);margin:14px 0 6px">COMPOSITION &middot; <span id="dname"></span></h2>
<div class="wrap"><table id="grid"></table></div>
<table><thead><tr><th>Control</th><th>Does</th><th>Path</th></tr></thead><tbody id="rows"></tbody></table>
<div class="foot">Read-only cheat sheet generated from the preset and composition files; nothing here talks to Resolume.
Pad colours approximate the APC40's LED palette. Board-as-grid idea after Rieger Gerg&#337;'s ROGGER (MIT).</div>
<script>
const M=__DATA__;
const comp=M.comp||{decks:[],layers:[]};
const decks=comp.decks.length?comp.decks:[{name:"(no composition)",columns:{},clips:{}}];
let D=0,SEL=null;
const NOTE={pad:(r,c)=>`note:1:${(r-1)*8+(c-1)}`};
function k(kind,ch,n){return `${kind}:${ch}:${n}`}
const names={
 "note:1:80":"MASTER","note:1:81":"STOP ALL","note:1:82":"SCENE 1","note:1:83":"SCENE 2","note:1:84":"SCENE 3","note:1:85":"SCENE 4","note:1:86":"SCENE 5",
 "note:1:58":"DEV &lt;","note:1:59":"DEV &gt;","note:1:60":"BANK &lt;","note:1:61":"BANK &gt;","note:1:62":"DEV ON","note:1:63":"DEV LOCK","note:1:64":"CLIP/DEV","note:1:65":"DETAIL",
 "note:1:87":"PAN","note:1:88":"SENDS","note:1:89":"USER","note:1:90":"METRO","note:1:91":"PLAY","note:1:92":"STOP","note:1:93":"RECORD","note:1:94":"UP","note:1:95":"DOWN","note:1:96":"RIGHT","note:1:97":"LEFT","note:1:98":"SHIFT","note:1:99":"TAP","note:1:100":"NUDGE -","note:1:101":"NUDGE +","note:1:102":"SESSION","note:1:103":"BANK LOCK",
 "cc:1:13":"TEMPO","cc:1:14":"MASTER FADER","cc:1:15":"CROSSFADER","cc:1:47":"CUE LEVEL","cc:1:64":"FOOTSWITCH"};
function nm(key){if(names[key])return names[key];const [kd,ch,n]=key.split(":");
 if(kd==="note"&&+n<40)return `PAD r${Math.floor(n/8)+1} c${n%8+1}`;
 const rows={48:"REC ARM",49:"SOLO",50:"ACTIVATOR",51:"SELECT",52:"CLIP STOP",66:"X-FADE A/B"};
 if(kd==="note"&&rows[n])return `${rows[n]} ${ch}`;
 if(kd==="cc"&&n==7)return `FADER ${ch}`;
 if(kd==="cc"&&n>=16&&n<=23)return `DEVICE KNOB ${n-15}`;
 if(kd==="cc"&&n>=48&&n<=55)return `TRACK KNOB ${n-47}`;
 return key}
function lab(s){const dk=decks[D];
 if(s.t==="clip"){const c=dk.clips[`${s.layer},${s.col}`];return c?c[0]||c[1]:"(empty)"}
 if(s.t==="column"){const n=dk.columns[s.col];return n?`Scene ${s.col}: ${n}`:s.label}
 return s.label}
function short(key){const L=M.controls[key];if(!L)return "";return L.map(lab).join(" + ")}
function cell(key,cls=""){const L=M.controls[key];const d=document.createElement("div");
 d.className="c "+cls+(L?"":" none");d.dataset.k=key;
 const led=L&&L.find(s=>s.led);if(led)d.innerHTML=`<i style="background:${led.led}"></i>`;
 d.innerHTML+=`<span style="padding-left:6px;display:block">${L?esc(short(key)):""}<small>${nm(key)}</small></span>`;
 if(L&&L.length>1){d.classList.add("multi");d.dataset.n="x"+L.length}
 if(L)d.onclick=()=>pick(key);return d}
function esc(s){return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
function z(t){const d=document.createElement("div");d.className="z";d.textContent=t;return d}
function blank(){const d=document.createElement("div");return d}
function draw(){const b=document.getElementById("board");b.innerHTML="";
 const add=e=>b.appendChild(e);
 // row: track knobs | device knobs
 add(z("Track knobs"));for(let i=0;i<8;i++)add(cell(k("cc",1,48+i),"knob"));add(cell(k("cc",1,13),"knob"));add(blank());
 for(let i=0;i<4;i++)add(cell(k("cc",1,16+i),"knob"));
 for(let r=5;r>=1;r--){add(z(r===5?"Pads (top)":(r===1?"Pads (bottom)":"Pads")));
  for(let c=1;c<=8;c++)add(cell(NOTE.pad(r,c)));add(cell(k("note",1,87-r)));add(blank());
  if(r===5)for(let i=0;i<4;i++)add(cell(k("cc",1,20+i),"knob"));
  else if(r===4)[58,59,60,61].forEach(n=>add(cell(k("note",1,n))));
  else if(r===3)[62,63,64,65].forEach(n=>add(cell(k("note",1,n))));
  else if(r===2)[87,88,89,90].forEach(n=>add(cell(k("note",1,n))));
  else [91,92,93,102].forEach(n=>add(cell(k("note",1,n))));}
 const rows=[[52,"Clip stop"],[51,"Track select"],[66,"X-fade A/B"],[50,"Activator"],[49,"Solo"],[48,"Rec arm"]];
 const right=[[81,80,103,98],[94,95,97,96],[99,100,101,null],["cc47","cc64",null,null],[null,null,null,null],[null,null,null,null]];
 rows.forEach(([n,t],i)=>{add(z(t));for(let ch=1;ch<=8;ch++)add(cell(k("note",ch,n),"small"));
  add(i===0?cell(k("note",1,81)):blank());add(blank());
  right[i].forEach(x=>{if(x===null)add(blank());else if(typeof x==="string")add(cell(k("cc",1,+x.slice(2)),"knob"));else add(cell(k("note",1,x)))});});
 add(z("Faders"));for(let ch=1;ch<=8;ch++)add(cell(k("cc",ch,7)));add(cell(k("cc",1,14)));add(blank());
 add(cell(k("cc",1,15)));add(blank());add(blank());add(blank());
 if(SEL)hl(SEL);table()}
function hl(key){document.querySelectorAll(".c.sel").forEach(e=>e.classList.remove("sel"));
 const e=document.querySelector(`.c[data-k="${key}"]`);if(e)e.classList.add("sel")}
function pick(key){SEL=key;hl(key);const L=M.controls[key]||[];
 document.getElementById("info").innerHTML=`<b>${nm(key)}</b> <code>${key}</code><br>`+L.map(s=>`&bull; ${esc(lab(s))} <code>${esc(s.path)}${s.range?" ["+s.range.join("..")+"]":""}</code>`).join("<br>")}
function grid(){const dk=decks[D];const g=document.getElementById("grid");document.getElementById("dname").textContent=dk.name;
 const cols=Math.max(0,...Object.keys(dk.columns).map(Number),...Object.keys(dk.clips).map(k=>+k.split(",")[1]));
 const lays=(comp.layers||[]).length;if(!cols||!lays){g.innerHTML="<tr><td>(no clips)</td></tr>";return}
 let h="<tr><th></th>"+Array.from({length:cols},(_,i)=>`<th>${i+1} ${esc(dk.columns[i+1]||"")}</th>`).join("")+"</tr>";
 for(let l=lays;l>=1;l--){h+=`<tr><th>${l} ${esc(comp.layers[l-1]||"")}</th>`;for(let c=1;c<=cols;c++){const x=dk.clips[`${l},${c}`];h+=`<td>${x?esc(x[0]||x[1])+(x[1]&&x[0]!==x[1]?`<br><code>${esc(x[1])}</code>`:""):""}</td>`}h+="</tr>"}
 g.innerHTML=h}
function table(){grid();const q=document.getElementById("q").value.toLowerCase();const tb=document.getElementById("rows");tb.innerHTML="";
 Object.keys(M.controls).sort((a,b)=>nm(a).localeCompare(nm(b),undefined,{numeric:true})).forEach(key=>{
  M.controls[key].forEach(s=>{const row=[nm(key),lab(s),s.path].join(" ").toLowerCase();if(q&&!row.includes(q))return;
   const tr=document.createElement("tr");tr.innerHTML=`<td>${nm(key)}</td><td>${esc(lab(s))}</td><td><code>${esc(s.path)}</code></td>`;
   tr.onclick=()=>pick(key);tb.appendChild(tr)})})}
const sel=document.getElementById("deck");decks.forEach((d,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`${i+1}. ${d.name}`;sel.appendChild(o)});
sel.onchange=()=>{D=+sel.value;draw();if(SEL)pick(SEL)};
document.getElementById("q").oninput=table;
document.getElementById("meta").textContent=`Preset "${M.preset}" (${M.count} shortcuts on ${Object.keys(M.controls).length} controls)`+(M.comp?` · composition "${M.comp.name}" · ${decks.length} deck(s), ${(M.comp.layers||[]).length} layers`:"");
draw();
</script></body></html>
"""


def write_html(model, out, title=None):
    comp_name = (model["comp"] or {}).get("name") or model["preset"]
    t = title or comp_name
    page = (PAGE.replace("__TITLE__", html.escape("APC40 map - %s" % t))
            .replace("__H1__", html.escape(t))
            .replace("__DATA__", json.dumps(model, ensure_ascii=False)
                     .replace("</", "<\\/")))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(page)
    return out


def run_all(root):
    presets = {}
    for p in glob.glob(os.path.join(root, "**", "*.xml"), recursive=True):
        try:
            r = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        if r.tag == "MidiShortcutPreset":
            presets[r.get("name")] = p
    made = []
    used = set()
    for avc in sorted(glob.glob(os.path.join(root, "**", "*.avc"),
                                recursive=True)):
        try:
            info = read_avc(avc)
        except ET.ParseError:
            continue
        pp = presets.get(info["preset"])
        if not pp and info["preset"]:
            # "React v4" in the comp, "React v4.4" on disk: take the single
            # preset whose name extends the one the composition asks for.
            cands = [p for n, p in presets.items()
                     if n and n.startswith(info["preset"])]
            pp = cands[0] if len(cands) == 1 else None
        if not pp:
            continue
        used.add(pp)
        pack_dir = os.path.dirname(avc)
        if os.path.basename(pack_dir) in ("compositions", "controllers"):
            pack_dir = os.path.dirname(pack_dir)
        out = os.path.join(pack_dir, "docs", "APC40_MAP_%s.html"
                           % re.sub(r"[^A-Za-z0-9]+", "_", os.path.splitext(
                               os.path.basename(avc))[0]).strip("_"))
        write_html(build_model(pp, avc), out)
        made.append((info["name"], info["preset"], out))
    for name, pp in presets.items():
        if pp in used:
            continue
        out = os.path.join(os.path.dirname(pp), "APC40_MAP_%s.html"
                           % re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_"))
        write_html(build_model(pp), out, title=name)
        made.append((None, name, out))
    idx = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
           "<meta name='viewport' content='width=device-width,initial-scale=1'>"
           "<title>APC40 maps</title><style>body{font:14px system-ui;"
           "background:#0b0c0e;color:#e9edf3;padding:24px 16px;max-width:900px;"
           "margin:auto}a{color:#ffb03a}li{margin:6px 0}small{color:#8d939c}"
           "@media (prefers-color-scheme: light){body{background:#f4f2ee;"
           "color:#16181b}a{color:#b4570a}}</style></head><body>"
           "<h1>APC40 mkII maps</h1><ul>"]
    for name, pre, out in sorted(made, key=lambda x: x[2]):
        rel = os.path.relpath(out, root).replace("\\", "/")
        idx.append("<li><a href='%s'>%s</a> <small>%s</small></li>"
                   % (html.escape(rel), html.escape(name or pre),
                      html.escape(pre if name else "preset only")))
    idx.append("</ul></body></html>")
    with open(os.path.join(root, "APC40_MAPS.html"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(idx))
    return made


def run_dirs(avc_dir, preset_dir, out_dir):
    """Every .avc in avc_dir -> one page in out_dir, paired with its preset
    from preset_dir (exact name, else the single name that extends it).
    Comps whose preset is missing still get a page: board empty, grid full."""
    presets = {}
    pdirs = preset_dir if isinstance(preset_dir, list) else [preset_dir]
    adirs = avc_dir if isinstance(avc_dir, list) else [avc_dir]
    for p in [x for d in pdirs for x in glob.glob(os.path.join(d, "**", "*.xml"),
                                                  recursive=True)]:
        try:
            r = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        if r.tag == "MidiShortcutPreset":
            presets[r.get("name")] = p
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    skip = ("harvest", "backups", "__pycache__", ".git", "_dryrun", "_partial")
    found = []
    for d in adirs:
        for x in glob.glob(os.path.join(d, "**", "*.avc"), recursive=True):
            if not any(("%s%s" % (os.sep, k)) in x or ("/%s" % k) in x
                       for k in skip):
                found.append((d, x))
    seen = set()
    for base, avc in sorted(found, key=lambda t: t[1].lower()):
        try:
            info = read_avc(avc)
        except ET.ParseError as exc:
            rows.append((os.path.basename(avc), None, None, "unreadable"))
            continue
        want = info["preset"] or ""
        pp = presets.get(want)
        if not pp and want:
            c = [p for n, p in presets.items() if n and n.startswith(want)]
            pp = c[0] if len(c) == 1 else None
        stem = os.path.splitext(os.path.basename(avc))[0]
        rel = os.path.relpath(os.path.dirname(avc), base)
        where = os.path.basename(os.path.normpath(base)) + (
            "" if rel == "." else "/" + rel.replace(os.sep, "/"))
        fn = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_")
        if fn.lower() in seen:
            fn = re.sub(r"[^A-Za-z0-9]+", "_", where + "_" + stem).strip("_")
        seen.add(fn.lower())
        out = os.path.join(out_dir, fn + ".html")
        if pp:
            model = build_model(pp, avc)
        else:
            model = {"preset": want or "(none)", "preset_file": None,
                     "comp": info, "controls": {}, "count": 0}
        write_html(model, out, title=stem)
        nd = len(info["decks"])
        nc = sum(len(d["clips"]) for d in info["decks"])
        rows.append((stem, want, os.path.basename(out),
                     "%s - %d decks, %d clips%s" % (where, nd, nc, "" if pp
                                                    else " - preset not found")))
    idx = ["<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
           "<meta name='viewport' content='width=device-width,initial-scale=1'>"
           "<title>Composition maps</title><style>body{font:14px system-ui;"
           "background:#0b0c0e;color:#e9edf3;padding:24px 16px;max-width:1000px;"
           "margin:auto}a{color:#ffb03a}td{padding:4px 8px;border-bottom:1px "
           "solid #2a2e35}small,.d{color:#8d939c}table{border-collapse:collapse;"
           "width:100%}@media (prefers-color-scheme: light){body{background:"
           "#f4f2ee;color:#16181b}a{color:#b4570a}td{border-color:#d3cfc7}}"
           "</style></head><body><h1>Composition maps</h1><p class='d'>%d "
           "compositions. Generated from the files; nothing talks to Resolume."
           "</p><table>"]
    idx[0] = idx[0].replace("%d ", str(len(rows)) + " ", 1)
    for stem, want, out, note in rows:
        idx.append("<tr><td>%s</td><td class='d'>%s</td><td class='d'>%s</td>"
                   "</tr>" % ("<a href='%s'>%s</a>" % (html.escape(out),
                                                        html.escape(stem))
                              if out else html.escape(stem),
                              html.escape(want or ""), html.escape(note)))
    idx.append("</table></body></html>")
    with open(os.path.join(out_dir, "index.html"), "w",
              encoding="utf-8") as f:
        f.write(chr(10).join(idx))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preset", nargs="?")
    ap.add_argument("--avc")
    ap.add_argument("--out")
    ap.add_argument("--all")
    ap.add_argument("--avc-dir", action="append")
    ap.add_argument("--preset-dir", action="append")
    ap.add_argument("--out-dir")
    a = ap.parse_args()
    if a.avc_dir:
        for r in run_dirs(a.avc_dir, a.preset_dir, a.out_dir):
            print("%-40s %-44s %s" % (r[0][:40], (r[1] or "")[:44], r[3]))
        return
    if a.all:
        for name, pre, out in run_all(a.all):
            print("%-34s %-40s %s" % (name, pre, out))
        return
    if not a.preset:
        sys.exit(__doc__)
    out = a.out or os.path.splitext(a.preset)[0] + ".html"
    print(write_html(build_model(a.preset, a.avc), out))


if __name__ == "__main__":
    main()
