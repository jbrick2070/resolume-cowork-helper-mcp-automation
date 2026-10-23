# Hosting the colour lab in Chataigne

Status: a plan from research, not a built or tested project. Nothing here has been loaded into Chataigne yet.

Chataigne (Ben Kuper, GPL-3.0) is the free show-control hub the request was reaching for ("an open source Bitfocus"). **Version 1.10.3 is already installed on this PC**
(`C:\Program Files\Chataigne`, installed 2026-07-18). Stable is 1.10.4 and a beta, 1.10.5b7, adds a built-in MCP server; both would be explicit downloads from
`benjamin.kuperberg.fr/chataigne/user/data/`. The 1.10.4 installer was fetched during research (unsigned, 8,907,157 bytes) and not installed.

## What Chataigne gives the lab

| Need | Chataigne feature |
|---|---|
| Own the APC's ports | the built-in **MIDI** module (input + output), `sendNoteOn(channel, note, velocity)`, `sendCC`, `sendSysex`, channels start at 1 |
| Talk to Resolume | the **Resolume** module (OSC out, default `127.0.0.1:7000`, the `/composition/layers/{L}/clips/{C}/connect` scheme the packs already use) plus a generic **OSC input** module for feedback |
| Host clock | an **Ableton Link** module and MIDI clock out, so the pads can pulse at the show's tempo |
| Shift pages, modes | the **State Machine** (one state per theme) |
| LED light shows | **Sequences** driving custom variables |

## Do not use the community APC40 module for this

* Its README warns that using Chataigne's **Router** with it crashes.
* From reading its source (not run): its pad "mode" enum runs 0-15 and appears to be passed straight to `local.sendNoteOn(c, n, v)` as a channel, while Chataigne channels start at 1. If so,
  every animation lands one wire channel early (a 1/16 one-shot plays as 1/24; the first mode of each family crosses into the previous family), and mode 0 is clamped to channel 1, so static
  colours still work.

Use the plain MIDI module and put the engine in a script. Chataigne's script engine is believed to be a limited, ES5-like JavaScript (unverified here: classes, arrow functions and
`Math.imul` may be missing), so `demo/engine.js` would need a mechanical port before it can run there; `tools/parity.py` is the safety net for that port.

## Open decisions

1. **Port ownership.** Chataigne owns the APC and Resolume talks to loopback ports (topology A in the README), or Windows MIDI Services lets both open it (untested).
2. **Mode 1 or Mode 2.** The existing presets assume Mode 1. Mode 2 gives the router every LED.
3. **Resolume feedback source.** Resolume's MIDI shortcut feedback (what this lab remaps), or the REST/WebSocket API on port 8080, which reports full composition state. The REST API is
   the richer source and Chataigne has HTTP and WebSocket modules.
4. **Coexistence.** The router would run alongside `avenue_pipe_bridge.py` and the Resolume MCP servers. Per `AGENTS.md`, reuse the running instances and never start duplicates.
5. A hand-written `.noisette` (plain JSON) has never been loaded; the first step is to load a minimal one.
