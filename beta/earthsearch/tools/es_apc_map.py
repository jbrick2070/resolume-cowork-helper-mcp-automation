#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
es_apc_map.py - the complete APC40 mkII control map for EarthSearch EP01.

One table, consumed by the preset generator AND the control-map document, so
the shipped XML and the printed layout card can never disagree.

Physical addresses come from apc40mkii-kit/docs/APC40_native_addresses.md
(decoded from the Akai APC40 Mk2 Communications Protocol v1.2 and confirmed
against working presets on this rig).

Every shortcut SHAPE below - behaviour code, paramNodeName, translationType,
allowedTranslationTypes - was harvested from presets that have actually run on
this rig. A shape is only used here if it appears in at least one of them.

THE SAFETY ARCHITECTURE, in one place:

  * The 5x8 pad grid addresses ONLY the five generative overlay layers (3-7).
    There is no pad anywhere on this surface that can reach either master.
  * Every layer in the composition sets "Ignore Column Trigger", so no column
    action - not from this preset, not from a mis-click in Resolume's own UI -
    can connect, eject or restart anything.
  * There is no seek/scrub binding. /composition/selectedclip/transport/position
    is deliberately absent from this file.
  * There is no fader-start anywhere, so no fader move can trigger a clip.
  * START BOTH is the ONLY control that starts the masters, and it starts them
    as one gesture: three clip-connect shortcuts sharing a single MIDI key.
    Measured on this rig at 0.0 ms drift.
"""

# --------------------------------------------------------------------------
# MIDI key encoding. Resolume packs the input message into one 64-bit int:
#     key = marker + (data1 << 8) + statusByte
# --------------------------------------------------------------------------
NOTE_MARKER = 72057594037927936        # 2**56
CC_MARKER = 144115188075855872         # 2**57


def note_key(channel, note):
    return NOTE_MARKER + (note << 8) + (0x90 + channel - 1)


def cc_key(channel, cc):
    return CC_MARKER + (cc << 8) + (0xB0 + channel - 1)


# --------------------------------------------------------------------------
# APC40 mkII LED velocities.
#
# Only the 40 clip pads and the 5 Scene Launch pads speak the RGB palette.
# Every other button LED is BINARY - 0 is off, any 1-127 is on - so state on
# those has to be expressed as lit/unlit, and an "Off" value that was a palette
# index would just read as "on". (Prior rig research, apc_map.py 2026-08-08.)
# --------------------------------------------------------------------------
LED_OFF = 0
LED = {
    "phosphor":  {"on": 21, "dim": 22},   # SIGNAL     - terminal green
    "signal":    {"on": 37, "dim": 38},   # STARFIELD  - telemetry cyan
    "amber":     {"on": 9,  "dim": 10},   # GRID       - CRT amber
    "bone":      {"on": 3,  "dim": 2},    # CAPTION    - bone white
    "alert":     {"on": 5,  "dim": 6},    # FLARE      - distress red
}
# Pad row 1 is the BOTTOM row and addresses layer 3.
ROW_LED = {1: "phosphor", 2: "signal", 3: "amber", 4: "bone", 5: "alert"}
ROW_LAYER = {1: 3, 2: 4, 3: 5, 4: 6, 5: 7}
ROW_LAYER_NAME = {1: "SIGNAL", 2: "STARFIELD", 3: "GRID", 4: "CAPTION",
                  5: "FLARE"}


def vel(v):
    """Resolume stores LED velocity as velocity/127 at full double precision."""
    return repr(v / 127.0)


# --------------------------------------------------------------------------
# Shortcut shapes, each verified against a working preset in this workspace.
#   behaviour 1028   note button with output feedback
#   behaviour 4      bool toggle
#   behaviour 8      absolute CC
#   behaviour 16392  relative encoder
#   behaviour 131082 cycle a ParamChoice
# --------------------------------------------------------------------------
SHAPES = {
    "clip":      dict(behaviour="1028", param_node="", tt="1", att_in="11",
                      att_out="11", devices=True, sibling="connected"),
    "action11":  dict(behaviour="1028", param_node="", tt="1", att_in="11",
                      att_out="11", devices=True, sibling=None),
    "action1":   dict(behaviour="1028", param_node="", tt="1", att_in="1",
                      att_out="1", devices=True, sibling=None),
    "select":    dict(behaviour="1028", param_node="", tt="1", att_in="3",
                      att_out="3", devices=True, sibling="selected"),
    "selectcomp": dict(behaviour="1028", param_node="", tt="1", att_in="1",
                       att_out="1", devices=True, sibling=None),
    "bypass11":  dict(behaviour="4", param_node="", tt="1", att_in="11",
                      att_out="11", devices=False, sibling=None),
    "solo":      dict(behaviour="4", param_node="", tt="1", att_in="3",
                      att_out="3", devices=False, sibling="soloed"),
    "boolparam": dict(behaviour="4", param_node="RangedParam[bool]", tt="1",
                      att_in="1", att_out="1", devices=False, sibling=None),
    "cycle":     dict(behaviour="131082",
                      param_node="ParamChoice[unsigned long long]", tt="1",
                      att_in="11", att_out="11", devices=True, sibling=None),
    "cc11":      dict(behaviour="8", param_node="", tt="1", att_in="11",
                      att_out="11", devices=True, sibling=None,
                      subtarget=True),
    "cc1":       dict(behaviour="8", param_node="", tt="1", att_in="1",
                      att_out="1", devices=True, sibling=None,
                      subtarget=True),
    "ccrange":   dict(behaviour="8", param_node="ParamRange", tt="1",
                      att_in="1", att_out="1", devices=True, sibling=None,
                      subtarget=True),
    "relative":  dict(behaviour="16392", param_node="", tt="1", att_in="1",
                      att_out="1", devices=True, sibling=None),
}


def _sc(control, physical, kind, path, shape, led=None, note=None,
        channel=1, cc=None, group="", note_text="", value_range=None,
        init=None):
    return dict(control=control, physical=physical, kind=kind, path=path,
                shape=shape, led=led or {}, note=note, channel=channel,
                cc=cc, group=group, note_text=note_text,
                value_range=value_range, init=init)


def build_map(spec):
    """Return the full ordered list of shortcut definitions.

    `spec` is the es_spec module, so the effect banks and layer names here can
    never drift from the composition.
    """
    S = spec
    m = []

    # ------------------------------------------------------------ pad grid --
    # 40 clip pads -> the five generative overlay layers, 8 columns each.
    # note = (row-1)*8 + (col-1), all channel 1, row 1 = bottom = layer 3.
    #
    # This is the whole reason the masters live on layers 1-2: the pad grid
    # physically cannot address them, so "no pad may restart a master" needs no
    # discipline from the performer.
    for row in range(1, 6):
        fam = ROW_LED[row]
        layer = ROW_LAYER[row]
        lname = ROW_LAYER_NAME[row]
        clips = S.OVERLAY_CLIPS[layer - 1]
        for col in range(1, 9):
            n = (row - 1) * 8 + (col - 1)
            cname = clips[col - 1][0] if col - 1 < len(clips) else "(empty)"
            m.append(_sc(
                "Pad R%dC%d - %s" % (row, col, cname),
                "Clip Launch grid, physical row %d col %d" % (row, col),
                "note", "/composition/layers/%d/clips/%d/connect"
                % (layer, col), "clip", note=n, group="Overlay grid",
                note_text="%s layer, %s" % (lname, cname),
                led={"Connected": LED[fam]["on"],
                     "Connected & previewing": LED[fam]["on"],
                     "Disconnected": LED[fam]["dim"],
                     "Previewing": LED[fam]["dim"],
                     "Empty": LED_OFF, "Off": LED_OFF}))

    # ------------------------------------------------------ per-track rows --
    layer_names = [l[1] for l in S.LAYERS]

    # Clip Stop row. Channels 1 and 2 sit above the two master strips, and an
    # earlier draft mapped them to /composition/layers/{1,2}/clear - which
    # ejects a master mid-show and can only be recovered by restarting the
    # whole episode. Three independent reviewers flagged it; they were right,
    # and it is gone. Those two seats now do what a hand above the master
    # strips actually wants: a HARD CUT to one version or the other. Nothing
    # on this row touches a transport any more.
    # These three write NORMALISED positions: a shortcut ValueRange is 0..1
    # over the parameter's own range, so on a -1..1 crossfader 0 is hard A,
    # 0.5 is centre and 1 is hard B. Writing -1 here would work only by
    # clamping, which is the kind of accident that survives until it doesn't.
    m.append(_sc(
        "CUT TO A", "TRACK/CLIP STOP n52 ch1", "note",
        "/composition/crossfader/phase", "ccrange", note=52, channel=1,
        group="A / B", value_range=("0", "0"), init="0",
        note_text="hard cut to MASTER A. Touches no transport.",
        led={"Off": LED_OFF, "On": 127}))
    m.append(_sc(
        "CUT TO B", "TRACK/CLIP STOP n52 ch2", "note",
        "/composition/crossfader/phase", "ccrange", note=52, channel=2,
        group="A / B", value_range=("1", "1"), init="0",
        note_text="hard cut to MASTER B. Touches no transport.",
        led={"Off": LED_OFF, "On": 127}))
    for ch in range(3, 9):
        m.append(_sc(
            "Eject %s" % layer_names[ch - 1], "TRACK/CLIP STOP n52 ch%d" % ch,
            "note", "/composition/layers/%d/clear" % ch, "action11",
            note=52, channel=ch, group="Eject overlay",
            note_text="drops whatever %s is showing" % layer_names[ch - 1],
            led={"Off": LED_OFF, "On": 1}))

    # Track Select: put a layer under the Track knobs / layer dashboard.
    for ch in range(1, 9):
        m.append(_sc(
            "Select %s" % layer_names[ch - 1], "TRACK SELECTION n51 ch%d" % ch,
            "note", "/composition/layers/%d/select" % ch, "select",
            note=51, channel=ch, group="Select layer",
            led={"Off": 0, "On": 1}))

    # Activator: mute. Lit = layer is LIVE, dark = muted, so the row reads as a
    # channel-strip "on air" row.
    for ch in range(1, 9):
        m.append(_sc(
            "Mute %s" % layer_names[ch - 1], "ACTIVATOR n50 ch%d" % ch,
            "note", "/composition/layers/%d/bypassed" % ch, "bypass11",
            note=50, channel=ch, group="Mute layer",
            led={"Off": 1, "On": LED_OFF}))

    # Solo.
    for ch in range(1, 9):
        m.append(_sc(
            "Solo %s" % layer_names[ch - 1], "SOLO n49 ch%d" % ch,
            "note", "/composition/layers/%d/solo" % ch, "solo",
            note=49, channel=ch, group="Solo layer",
            led={"Off": LED_OFF, "On": 1}))

    # --------------------------------------------------------- effect banks --
    # Five banks of composition effects, one per physical row, all latching
    # bypass toggles. LIT = effect is ACTIVE (bypassed = false -> the "Off"
    # state of the Bypassed parameter).
    def bank(bank_name):
        return [e for e in S.COMP_RACK if e[0] == bank_name]

    def fx_rows(bank_name, physical, note=None, channel_range=None,
                notes=None, group=None):
        out = []
        items = bank(bank_name)
        for i, (_b, label, key, _v) in enumerate([e[:4] for e in items]):
            if notes is not None:
                nn, cc_ = notes[i], 1
            else:
                nn, cc_ = note, channel_range[i]
            out.append(_sc(
                "%s / %s" % (bank_name, label),
                physical % (cc_ if notes is None else nn),
                "note", "/composition/video/effects/%s/bypassed"
                % S.slug(key), "boolparam", note=nn, channel=cc_,
                group=group or ("FX bank %s" % bank_name),
                note_text="composition effect %s" % key,
                led={"Off": 1, "On": 0}))
        return out

    m += fx_rows(S.BANK_COLOUR, "RECORD ARM n48 ch%d", note=48,
                 channel_range=list(range(1, 9)))
    m += fx_rows(S.BANK_BROADCAST, "CROSSFADER A/B n66 ch%d", note=66,
                 channel_range=list(range(1, 9)))
    m += fx_rows(S.BANK_LIGHT, "DEVICE button n%d",
                 notes=[58, 59, 60, 61, 62, 63, 64, 65])
    m += fx_rows(S.BANK_SPACE, "n%d",
                 notes=[87, 94, 95, 96, 97, 100, 101, 102])
    # FRACTURE is six: five on the Scene Launch rail beside the grid, and the
    # sixth on USER, the seat the blend-mode cycle used to occupy.
    m += fx_rows(S.BANK_FRACTURE, "SCENE LAUNCH n%d",
                 notes=[82, 83, 84, 85, 86, 89])

    # -------------------------------------------------------------- safety --
    # THE THREE SEPARATED CONTROLS. Physically apart from each other and from
    # every expressive control.
    #
    # START BOTH is three shortcuts sharing one MIDI key. Both halves are
    # rig-verified: 57 working presets in this workspace already share a key
    # across up to three shortcuts including .../connect paths, and connecting
    # the two masters as separate events measured 0.0 ms drift over 20 s on
    # this rig.
    for layer_n, what in ((1, "MASTER A"), (2, "MASTER B"), (8, "SCOPE")):
        m.append(_sc(
            "START BOTH @ 00:00 (%s)" % what, "PLAY n91",
            "note", "/composition/layers/%d/clips/1/connect" % layer_n,
            "clip", note=91, group="SAFETY - start",
            note_text="one press fires all three at frame zero",
            led={"Connected": 127, "Connected & previewing": 127,
                 "Disconnected": 1, "Previewing": 1,
                 "Empty": LED_OFF, "Off": LED_OFF}))

    m.append(_sc(
        "STOP / RESET BOTH", "STOP n92",
        "note", "/composition/disconnectall", "action1", note=92,
        group="SAFETY - stop",
        note_text="ejects every layer and resets both masters to 00:00",
        led={"Off": LED_OFF, "On": 127}))

    # STOP ALL CLIPS is silk-screened on the hardware, so it has to do
    # something a performer reading that label would expect. It clears the five
    # overlay layers - which is exactly what "stop all clips" means here - and
    # cannot reach a master. An earlier draft put CLEAN on this button, which
    # made the most panic-reachable control in the room lie about its job.
    for layer_n in (3, 4, 5, 6, 7):
        m.append(_sc(
            "CLEAR OVERLAYS (%s)" % layer_names[layer_n - 1],
            "STOP ALL CLIPS n81", "note",
            "/composition/layers/%d/clear" % layer_n, "action11", note=81,
            group="SAFETY - clear overlays",
            note_text="drops all overlay content. The masters keep running.",
            led={"Off": LED_OFF, "On": 127}))

    m.append(_sc(
        "BLACKOUT", "RECORD n93 (red)",
        "note", "/composition/bypassed", "boolparam", note=93,
        group="SAFETY - blackout",
        note_text="reversible black. Playback continues underneath.",
        led={"Off": 0, "On": 127}))

    # CLEAN / ALL FX OFF - seven shortcuts on one key, one per composition
    # dashboard link, each with a degenerate ValueRange so any press writes 0.
    # Links 1-5 gate the five effect banks' dry/wet; 6 gates every overlay
    # layer's opacity; 7 gates the scope. One press takes the whole
    # experimental chain off without touching playback, bypass state, or
    # either master's transport.
    for link in S.CLEAN_LINKS:
        m.append(_sc(
            "CLEAN / ALL FX OFF (link %d)" % link, "BANK LOCK n103",
            "note", "/composition/dashboard/link%d" % link, "ccrange",
            note=103, group="SAFETY - clean", value_range=("0", "0"),
            init="0",
            note_text="drives %s to zero" % S.COMP_DASHBOARD[link - 1][1],
            led={"Off": LED_OFF, "On": 127}))

    # ------------------------------------------------------- mixer / misc ---
    m.append(_sc("Select composition", "MASTER n80", "note",
                 "/composition/select", "selectcomp", note=80,
                 group="Mixer", led={"Off": 0, "On": 1}))
    # NO BLEND-MODE CYCLING ANYWHERE. An earlier draft put a cycle shortcut on
    # each master's Blend Mode. The live rig says that ParamChoice carries
    # FIFTY options in alphabetical order: Alpha sits at index 11, and stepping
    # forward from it walks through B&W, Burn, Cube, Cut and Darken, and passes
    # "to White" before it ever reaches Screen. On a controller with no display
    # that is a blind walk through destructive modes on a live full-frame
    # output. Both masters are pinned to Alpha; additive and light composites
    # come from the overlay layers, which is where they belong.
    # A shortcut ValueRange is NORMALISED 0..1 over the parameter's own range,
    # not expressed in its units - Resolume's own SPECIMEN preset maps this
    # -1..1 crossfader with min="0" max="1". So 0.5 is the centre. Written as
    # ("0","0") this button was a second CUT TO A, which is exactly the kind of
    # control that is worse than no control.
    m.append(_sc("CENTRE (50 / 50)", "SENDS n88", "note",
                 "/composition/crossfader/phase", "ccrange", note=88,
                 group="A / B", value_range=("0.5", "0.5"), init="0",
                 note_text="park the crossfade dead centre - a true double "
                           "exposure of the same moment in two renders",
                 led={"Off": LED_OFF, "On": 127}))
    m.append(_sc("Tempo resync", "METRONOME n90", "note",
                 "/composition/tempocontroller/resync", "action1", note=90,
                 group="Tempo", led={"Off": LED_OFF, "On": 127}))
    m.append(_sc("Tap tempo", "TAP TEMPO n99", "note",
                 "/composition/tempocontroller/tempotap", "action1", note=99,
                 group="Tempo",
                 note_text="the masters are timeline-locked, so tempo only "
                           "affects BPM-synced animation - never playback",
                 led={"Off": LED_OFF, "On": 127}))
    m.append(_sc("Re-arm SCOPE", "SHIFT n98", "note",
                 "/composition/layers/8/clips/1/connect", "clip", note=98,
                 group="Mixer",
                 note_text="brings the FFT readout back if it was ejected. "
                           "Touches nothing else.",
                 led={"Connected": 1, "Connected & previewing": 1,
                      "Disconnected": 0, "Previewing": 0,
                      "Empty": LED_OFF, "Off": LED_OFF}))
    # CLEAN lives on BANK LOCK alone. An earlier draft duplicated it onto STOP
    # ALL CLIPS for reachability, but that button is silk-screened with a
    # promise it would not have kept, and a panic control that lies is worse
    # than one you have to reach for. The continuous equivalent is always
    # under the other hand: Cue Level sweeps the same eight links.

    # -------------------------------------------------------------- faders --
    # Layer MASTER, not layer opacity: opacity on the overlay and scope layers
    # is owned by dashboard links 6 and 7 so CLEAN can reach it, and on the two
    # masters it is owned by the crossfader. Master is the free, per-layer
    # level control, and it is what the physical fader should feel like.
    for ch in range(1, 9):
        m.append(_sc("Fader %d - %s" % (ch, layer_names[ch - 1]),
                     "TRACK FADER CC7 ch%d" % ch, "cc",
                     "/composition/layers/%d/master" % ch, "cc11",
                     cc=7, channel=ch, group="Layer level",
                     init="1" if ch <= 2 else "0"))
    m.append(_sc("Master fader", "MASTER FADER CC14", "cc",
                 "/composition/master", "cc1", cc=14, group="Master",
                 init="1"))
    m.append(_sc("A / B CROSSFADE", "CROSSFADER CC15", "cc",
                 "/composition/crossfader/phase", "cc1", cc=15,
                 group="Master", init="0",
                 note_text="MASTER A is on bus A, MASTER B on bus B. Hard "
                           "left is pure A, hard right is pure B, and every "
                           "point between is a true dissolve."))

    # --------------------------------------------------------------- knobs --
    # Device Control knobs -> the composition dashboard. Global; never
    # retargets when something is launched.
    for i in range(1, 9):
        m.append(_sc("Device knob %d - %s" % (i, S.COMP_DASHBOARD[i - 1][1]),
                     "DEVICE CONTROL knob %d CC%d" % (i, 15 + i), "cc",
                     "/composition/dashboard/link%d" % i, "cc1", cc=15 + i,
                     group="Bank intensity",
                     note_text=S.COMP_DASHBOARD[i - 1][2], init="1"))

    # Track Control knobs -> LIVE FFT CONTROL.
    # .../behaviour/gain is the band's depth in dB; .../behaviour/fallback is
    # its release in ms. Both paths are rig-verified. This is what makes the
    # audio reactivity playable rather than baked: the performer watches the
    # SCOPE layer and tunes depth and release mid-episode without stopping.
    fft_knobs = []
    for band in ("low", "mid", "high"):
        label, key, param = S.FFT_BAND_ANCHOR[band]
        base = ("/composition/video/effects/%s/effect/%s"
                % (S.slug(key), S.param_slug(key, param)))
        # Named after the parameter each knob actually moves, not after the
        # band. A knob labelled "LOW DEPTH" implies it governs everything on
        # the low band; it does not - it governs one anchor parameter, and
        # saying so is the difference between a control map and a promise.
        fft_knobs.append(("%s DEPTH (%s band)" % (label, band),
                          base + "/behaviour/gain",
                          "how hard the %s band drives %s, and only %s"
                          % (band, label, label)))
        fft_knobs.append(("%s RELEASE (%s band)" % (label, band),
                          base + "/behaviour/fallback",
                          "how slowly %s falls back after a peak" % label))
    for key, param, why in (("HueRotate", "Hue Rotate", "colour-drift depth"),
                            ("WaveWarp", "Height", "warp depth")):
        fft_knobs.append(("%s DEPTH" % S.slug(key).upper(),
                          "/composition/video/effects/%s/effect/%s"
                          "/behaviour/gain"
                          % (S.slug(key), S.param_slug(key, param)), why))
    for i, (label, path, why) in enumerate(fft_knobs[:8]):
        m.append(_sc("Track knob %d - %s" % (i + 1, label),
                     "TRACK CONTROL knob %d CC%d" % (i + 1, 48 + i), "cc",
                     path, "ccrange", cc=48 + i, group="Live FFT control",
                     note_text=why, init="0.5"))

    # Cue Level -> the FX MASTER sweep. Same seven links as the CLEAN buttons,
    # but continuous, so the whole chain can be ridden in and out by hand.
    for link in S.CLEAN_LINKS:
        m.append(_sc("FX MASTER sweep (link %d)" % link, "CUE LEVEL CC47",
                     "cc", "/composition/dashboard/link%d" % link, "ccrange",
                     cc=47, group="FX master", value_range=("0", "1"),
                     init="1",
                     note_text="fully anticlockwise is the same clean image "
                               "the CLEAN buttons give you"))

    # Footswitch -> MOMENTARY BLACKOUT.
    #
    # An earlier draft made this a momentary CLEAN across the dashboard links.
    # Three reviewers independently caught the same bug, and they were right: a
    # MIDI shortcut has no memory, so releasing the switch could not restore
    # the performer's mix - it would slam every bank, every overlay and the
    # scope to FULL. Mid-show that is a full-stack flash, which is the one
    # thing the brief explicitly forbids.
    #
    # Blackout has no such problem. It is a bool, so press-on / release-off is
    # the whole of its state, and hands-free black for a scene change is what a
    # foot actually wants.
    m.append(_sc("Footswitch momentary BLACKOUT", "FOOTSWITCH CC64", "cc",
                 "/composition/bypassed", "ccrange", cc=64,
                 value_range=("0", "1"), init="0", group="SAFETY - blackout",
                 note_text="hold for black, release for picture. Playback "
                           "continues underneath either way."))

    # Tempo knob is a RELATIVE encoder - behaviour 16392. Binding it as an
    # absolute CC would make the value jump on the first touch.
    m.append(_sc("Tempo knob", "TEMPO CC13 (relative encoder)", "cc",
                 "/composition/tempocontroller/tempo", "relative", cc=13,
                 group="Tempo",
                 note_text="BPM reference for animation only. The masters run "
                           "on their own timeline and are not affected."))

    return m


# --------------------------------------------------------------------------
# Controls deliberately NOT mapped, and why. Shipped in the control-map doc so
# nothing on the surface is silently dead.
# --------------------------------------------------------------------------
UNMAPPED = [
    ("Knob LED ring CCs (CC24-31, CC56-63)",
     "Output-only ring value/style messages, not inputs. In APC Mode 1 the "
     "rings follow their value CCs automatically."),
]

# Paths that must NEVER appear in the preset. The generator asserts this.
FORBIDDEN_PATHS = [
    "transport/position",      # seeking a master would break sync
    "columns/",                # no column control anywhere
    "connectnextcolumn",
    "connectprevcolumn",
    "selectnextdeck",
    "selectprevdeck",
    "composition/speed",       # would change playback rate
    "connectnextclip",         # would retrigger a master
    "connectprevclip",
]
