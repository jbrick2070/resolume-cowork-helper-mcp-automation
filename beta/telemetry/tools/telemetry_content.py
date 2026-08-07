# telemetry_content.py - THE CELLS for "Res React Telemetry" (The Measuring Room).
# Edit here, then `python build_telemetry.py` to regenerate the composition.
#
# Five decks = five fictional instruments, all wired to measure the same thing:
# the room's audio. Five layers, bottom to top:
#
#   L1 PAPER    the chart bed (graph paper, rulers, scatter fields)
#   L2 TRACE    the main line the instrument draws
#   L3 NEEDLE   secondary channel - numbers, gauges, sub-traces
#   L4 STAMP    the verdict, Add-blended and hot
#   L5 READOUT  station captions across the top
#
# Cell spec: a dict per cell.
#   kind   'text' (default) | 'static' | 'strobe' | 'shaper'
#   label  clip name in Avenue (defaults to first line of text)
#   lines  explicit list of lines (VERBATIM, no wrapping), or
#   text   a single string, greedy-wrapped by the build
#   posY   per-cell Position Y override (px from centre, +Y down)
#   posX   clip TRANSFORM Position X (the VU column trick), default None
#   cap    per-cell size cap override
#   fft    'row' (deck/layer table, default) | 'none' | 'strobe'
#
# Glyph note: traces and paper use Unicode block elements (U+2580-259F),
# blocks-and-bars (U+2581-2587) and box drawing (U+2500-257F). These are
# first-time glyphs for the rig font, exactly like Lexicon II's French accents.
# If they render as boxes, flip ASCII_FALLBACK = True in build_telemetry.py
# and rebuild - every glyph has a plain-ASCII stand-in.

DECKS = ['THE EKG', 'THE RICHTER', 'THE VU', 'THE POLYGRAPH', 'THE GEIGER']

COLUMNS = {
    'THE EKG':       ['RESTING', 'ELEVATED', 'TACHY', 'ARREST', 'DEFIB',
                      'CAL', 'UTILITY', 'SNOW'],
    'THE RICHTER':   ['CALM', 'TREMOR', 'SWARM', 'MAJOR', 'THE BIG ONE',
                      'CAL', 'UTILITY', 'SNOW'],
    'THE VU':        ['-20 dB', '-10 dB', '0 dB', '+3 dB', 'RED',
                      'CAL', 'UTILITY', 'SNOW'],
    'THE POLYGRAPH': ['BASELINE', 'QUESTION', 'STRESS', 'SPIKE', 'VERDICT',
                      'CAL', 'UTILITY', 'SNOW'],
    'THE GEIGER':    ['BACKGROUND', 'TRACE', 'ELEVATED', 'HOT', 'MELTDOWN',
                      'CAL', 'UTILITY', 'SNOW'],
}

# ---------------------------------------------------------------- helpers
def T(text, **kw):
    d = {'kind': 'text', 'text': text}
    d.update(kw)
    return d

def L(lines, label, **kw):
    d = {'kind': 'text', 'lines': lines, 'label': label}
    d.update(kw)
    return d

def SNOW():
    """The one non-text bed cell per deck: raw StaticGenerator noise."""
    return {'kind': 'static', 'label': 'SNOW', 'fft': 'none'}

def PILOT(c1, c2):
    """One stroboscope per deck, FFT-gated on a narrowed bass band."""
    return {'kind': 'strobe', 'label': 'PILOT', 'fft': 'strobe',
            'color1': c1, 'color2': c2}

def CAL(color, outline):
    """The calibration dial: a Shaper the relative tempo encoder rotates."""
    return {'kind': 'shaper', 'label': 'CAL DIAL', 'fft': 'none',
            'color': color, 'outline': outline}

GRID_H = '┼───┼───┼───┼───┼───┼───┼───┼'
GRID_V = '│   │   │   │   │   │   │   │'
RULE   = '─────────────────────────────'

def bars(n, label):
    """A VU column: n stacked bar segments over a caption."""
    return ['████████'] * n + [label]

# ---------------------------------------------------------------- the grids
# GRID[deck][row] = list of 8 cells. Rows keyed PAPER/TRACE/NEEDLE/STAMP/READOUT.

GRID = {}

# ---------------------------------------------------------------- deck 1: EKG
GRID['THE EKG'] = {
 'PAPER': [
    L([GRID_H, GRID_V, GRID_H, GRID_V, GRID_H, GRID_V, GRID_H], 'GRAPH PAPER'),
    L([GRID_V, GRID_H, GRID_V, GRID_H, GRID_V, GRID_H, GRID_V], 'GRAPH PAPER FINE'),
    L([GRID_H, GRID_H, GRID_H, GRID_H, GRID_H, GRID_H, GRID_H], 'DENSE RULE'),
    L(['░░░░░░░░░░░░░░░░░░░░░░░░░░░░░'] * 5, 'ALARM HATCH'),
    L(['▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒'] * 5, 'CRASH HATCH'),
    T('CAL 1 kHz ' + RULE[:14] + ' 0 dBFS', label='TONE', fft='none'),
    L(['█▓▒░ █▓▒░ █▓▒░ █▓▒░ █▓▒░', '░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█'] * 2,
      'BARS', fft='none'),
    SNOW(),
 ],
 'TRACE': [
    L(['▁▁▁▂▁▁▁▁▇▁▁▁▂▁▁▁▁▁▂▁▁▁▁▇▁▁▁'], 'SINUS 62'),
    L(['▁▂▁▇█▇▁▂▁▁▇█▇▁▂▁▁▇█▇▁▂▁▁▇█▇▁'], 'SINUS 98'),
    L(['▂▇█▇▂▇█▇▂▇█▇▂▇█▇▂▇█▇▂▇█▇▂▇█▇'], 'TACHYCARDIA'),
    L(['▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁'], 'FLATLINE'),
    L(['▇█▇▇█▇██▇█▇██▇▁▁▇██▇█▇██▇█▇▇'], 'DEFIB CHAOS'),
    L(['────────────  CAL  ────────────'], 'FLAT CAL', fft='none'),
    L(['▲▲▲▲▲▲▲  OFF SCALE  ▲▲▲▲▲▲▲'], 'OFF SCALE'),
    L(['████████  SATURATED  ████████'], 'SATURATED'),
 ],
 'NEEDLE': [
    T('HR 62', label='HR 62'),
    T('HR 98', label='HR 98'),
    T('HR 147', label='HR 147'),
    T('HR ---', label='HR ---'),
    T('CHARGING 200 J', label='CHARGING'),
    T('SpO2 98%', label='SpO2', fft='none'),
    T('BP 120/80', label='BP'),
    CAL((0x39, 0xFF, 0x14, 0xFF), (0x0C, 0x50, 0x08, 0xFF)),
 ],
 'STAMP': [
    T('SINUS'), T('ELEVATED'), T('TACHYCARDIA'), T('ASYSTOLE'),
    T('CLEAR!'), T('STEMI?'), T('ARTIFACT'),
    PILOT((0x39, 0xFF, 0x14, 0xFF), (0x00, 0x00, 0x00, 0xFF)),
 ],
 'READOUT': [
    T('PATIENT: THE ROOM'), T('MONITORING'), T('CALL CARDIO'),
    T('CODE BLUE'), T('STAND CLEAR'),
    T('TELEMETRY UNIT 5 — LIVE', label='SLATE', fft='none'),
    T('SIGNAL LOST', label='SIGNAL LOST', fft='none'),
    L(['▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜', '▌ TEST CARD · CH 05 ▐', '▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟'],
      'TEST CARD', fft='none'),
 ],
}

# ------------------------------------------------------------ deck 2: RICHTER
GRID['THE RICHTER'] = {
 'PAPER': [
    L([RULE] * 7, 'DRUM PAPER'),
    L([RULE, GRID_V, RULE, GRID_V, RULE], 'DRUM PAPER RULED'),
    L([GRID_H, GRID_V, GRID_H, GRID_V, GRID_H], 'SWARM GRID'),
    L(['╱ ╱ ╱ ╱ ╱ ╱ ╱ ╱ ╱ ╱ ╱ ╱ ╱'] * 5, 'TORN PAPER'),
    L(['▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓'] * 5, 'RUBBLE FIELD'),
    T('CAL 1 kHz ' + RULE[:14] + ' 0 dBFS', label='TONE', fft='none'),
    L(['█▓▒░ █▓▒░ █▓▒░ █▓▒░ █▓▒░', '░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█'] * 2,
      'BARS', fft='none'),
    SNOW(),
 ],
 'TRACE': [
    L(['────────────────────────────'], 'CALM LINE'),
    L(['──~──~────~──~──~────~──~───'], 'TREMOR LINE'),
    L(['─~^v~─^v─~^v~─^v─~^v~─^v─~^v'], 'SWARM LINE'),
    L(['/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/'], 'MAJOR LINE'),
    L(['█▇█▆█▇██▇█▆██▇█▇█▆█▇██▇█▆███'], 'THE BIG LINE'),
    L(['────────────  CAL  ────────────'], 'FLAT CAL', fft='none'),
    L(['▲▲▲▲▲▲▲  OFF SCALE  ▲▲▲▲▲▲▲'], 'OFF SCALE'),
    L(['████████  CLIPPED  ████████'], 'CLIPPED'),
 ],
 'NEEDLE': [
    T('MAG 0.8'), T('MAG 2.4'), T('MAG 4.7 SWARM', label='MAG 4.7'),
    T('MAG 6.9'), T('MAG 9.1'),
    T('DEPTH 10 KM', fft='none'), T('P-WAVE ETA 4 S', label='P-WAVE'),
    CAL((0xF5, 0xE9, 0xD0, 0xFF), (0x55, 0x40, 0x20, 0xFF)),
 ],
 'STAMP': [
    T('STABLE'), T('TREMOR'), T('SWARM'), T('MAJOR EVENT'),
    T('THE BIG ONE'), T('AFTERSHOCK'), T('NOT A DRILL'),
    PILOT((0xFF, 0x3C, 0x28, 0xFF), (0x00, 0x00, 0x00, 0xFF)),
 ],
 'READOUT': [
    T('EPICENTER: DANCEFLOOR'), T('SEISMIC WATCH'), T('EVACUATE THE BAR'),
    T('DROP · HOLD ON'), T('SURF THE WAVE'),
    T('SEISMO STATION 12 — LIVE', label='SLATE', fft='none'),
    T('SIGNAL LOST', label='SIGNAL LOST', fft='none'),
    L(['▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜', '▌ TEST CARD · CH 12 ▐', '▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟'],
      'TEST CARD', fft='none'),
 ],
}

# ----------------------------------------------------------------- deck 3: VU
# The analyzer deck. TRACE = BASS column (transform X -520), NEEDLE = MID
# column (X 0), STAMP = HIGH column (X +520); each row's opacity rides its own
# band, so the three columns ARE the spectrum. Columns 1-5 raise the meter.
VU_Y = -40.0
GRID['THE VU'] = {
 'PAPER': [
    L(['-20 ── -10 ── -7 ── -3 ── 0 ── +3', GRID_H, GRID_V, GRID_H, GRID_V],
      'METER SCALE'),
    L([GRID_H, GRID_V, GRID_H, GRID_V, GRID_H], 'METER GRID'),
    L(['· · · · · · · · · · · · · · · · ·'] * 6, 'PEAK DOTS'),
    L(['░░░░░░░░░  LOUD ZONE  ░░░░░░░░░'] * 3, 'LOUD ZONE'),
    L(['▒▒▒▒▒▒▒▒▒  THE RED  ▒▒▒▒▒▒▒▒▒'] * 3, 'THE RED'),
    T('CAL 1 kHz ' + RULE[:14] + ' 0 dBFS', label='TONE', fft='none'),
    L(['█▓▒░ █▓▒░ █▓▒░ █▓▒░ █▓▒░', '░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█'] * 2,
      'BARS', fft='none'),
    SNOW(),
 ],
 'TRACE': [
    L(bars(2, 'BASS'), 'BASS 2', posX=-520.0, posY=VU_Y, cap=1.0),
    L(bars(3, 'BASS'), 'BASS 3', posX=-520.0, posY=VU_Y, cap=1.0),
    L(bars(5, 'BASS'), 'BASS 5', posX=-520.0, posY=VU_Y, cap=1.0),
    L(bars(7, 'BASS'), 'BASS 7', posX=-520.0, posY=VU_Y, cap=0.85),
    L(bars(9, 'BASS'), 'BASS 9', posX=-520.0, posY=VU_Y, cap=0.75),
    L(['────────────  CAL  ────────────'], 'FLAT CAL', fft='none'),
    L(['▲▲▲▲▲▲▲  OFF SCALE  ▲▲▲▲▲▲▲'], 'OFF SCALE'),
    L(['████████  PINNED  ████████'], 'PINNED'),
 ],
 'NEEDLE': [
    L(bars(2, 'MID'), 'MID 2', posX=0.0, posY=VU_Y, cap=1.0),
    L(bars(3, 'MID'), 'MID 3', posX=0.0, posY=VU_Y, cap=1.0),
    L(bars(5, 'MID'), 'MID 5', posX=0.0, posY=VU_Y, cap=1.0),
    L(bars(7, 'MID'), 'MID 7', posX=0.0, posY=VU_Y, cap=0.85),
    L(bars(9, 'MID'), 'MID 9', posX=0.0, posY=VU_Y, cap=0.75),
    T('0 VU = +4 dBu', label='0 VU', fft='none'),
    T('PEAK HOLD: ON', label='PEAK HOLD'),
    CAL((0xFF, 0xB0, 0x20, 0xFF), (0x66, 0x40, 0x00, 0xFF)),
 ],
 'STAMP': [
    L(bars(2, 'HIGH'), 'HIGH 2', posX=520.0, posY=VU_Y, cap=1.0),
    L(bars(3, 'HIGH'), 'HIGH 3', posX=520.0, posY=VU_Y, cap=1.0),
    L(bars(5, 'HIGH'), 'HIGH 5', posX=520.0, posY=VU_Y, cap=1.0),
    L(bars(7, 'HIGH'), 'HIGH 7', posX=520.0, posY=VU_Y, cap=0.85),
    L(bars(9, 'HIGH'), 'HIGH 9', posX=520.0, posY=VU_Y, cap=0.75),
    T('LIMITER: OFF', label='LIMITER', posY=330.0),
    T('+3 dB AND CLIMBING', label='+3 dB', posY=330.0),
    PILOT((0xFF, 0xB0, 0x20, 0xFF), (0x20, 0x08, 0x00, 0xFF)),
 ],
 'READOUT': [
    T('MONITORING THE MIX'), T('HEADROOM SHRINKING'), T('ZERO VU'),
    T('PIN THE NEEDLE'), T('WELCOME TO THE RED'),
    T('MASTER CONTROL — ON AIR', label='SLATE', fft='none'),
    T('SIGNAL LOST', label='SIGNAL LOST', fft='none'),
    L(['▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜', '▌ TEST CARD · CH 00 ▐', '▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟'],
      'TEST CARD', fft='none'),
 ],
}

# ---------------------------------------------------------- deck 4: POLYGRAPH
GRID['THE POLYGRAPH'] = {
 'PAPER': [
    L([RULE, GRID_V, RULE, GRID_V, RULE], 'STRIP CHART'),
    L([GRID_H, GRID_V, GRID_H, GRID_V, GRID_H], 'STRIP CHART FINE'),
    L(['· ˙ · ˙˙ · ˙ · · ˙ · ˙˙ · ˙ ·'] * 5, 'SWEAT FIELD'),
    L(['░░▒░░░▒▒░░▒░░░▒░░▒▒░░░▒░░▒░░'] * 5, 'INK BLEED'),
    L(['▒▓▒▒▓▓▒▒▓▒▒▓▓▒▒▓▒▒▓▓▒▒▓▒▒▓▓▒'] * 5, 'INK FLOOD'),
    T('CAL 1 kHz ' + RULE[:14] + ' 0 dBFS', label='TONE', fft='none'),
    L(['█▓▒░ █▓▒░ █▓▒░ █▓▒░ █▓▒░', '░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█'] * 2,
      'BARS', fft='none'),
    SNOW(),
 ],
 'TRACE': [
    L(['_____________________________'], 'BASELINE'),
    L(['__/\\______/\\____/\\______/\\___'], 'QUESTION LINE'),
    L(['_/\\/\\_/\\__/\\/\\_/\\_/\\/\\__/\\/\\_'], 'STRESS LINE'),
    L(['/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/'], 'SPIKE LINE'),
    L(['████ INK EVERYWHERE ████'], 'INK LINE'),
    L(['────────────  CAL  ────────────'], 'FLAT CAL', fft='none'),
    L(['▲▲▲▲▲▲▲  OFF SCALE  ▲▲▲▲▲▲▲'], 'OFF SCALE'),
    L(['████████  PEGGED  ████████'], 'PEGGED'),
 ],
 'NEEDLE': [
    T('GSR 3.2 uS', label='GSR'),
    T('PULSE RISING', label='PULSE'),
    T('RESP HELD', label='RESP'),
    T('ALL CHANNELS SPIKE', label='ALL SPIKE'),
    T('TRUTH 12%', label='TRUTH 12%'),
    T('Q BANK READY', fft='none'), T('CONTROL Q OK', label='CONTROL Q'),
    CAL((0x46, 0xA0, 0xFF, 0xFF), (0x10, 0x2C, 0x55, 0xFF)),
 ],
 'STAMP': [
    T('CALM'), T('QUESTION ASKED'), T('EVASIVE'), T('DECEPTION'),
    T('GUILTY FEET'), T('INCONCLUSIVE'), T('RETEST'),
    PILOT((0xFF, 0x30, 0x30, 0xFF), (0x00, 0x00, 0x00, 0xFF)),
 ],
 'READOUT': [
    T('Q: DID YOU DANCE?'), T('ANSWER THE QUESTION'), T('SUBJECT IS SWEATING'),
    T('THE NEEDLE KNOWS'), T('CASE CLOSED'),
    T('EXAM ROOM B — RECORDING', label='SLATE', fft='none'),
    T('SIGNAL LOST', label='SIGNAL LOST', fft='none'),
    L(['▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜', '▌ TEST CARD · RM B ▐', '▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟'],
      'TEST CARD', fft='none'),
 ],
}

# ------------------------------------------------------------- deck 5: GEIGER
GRID['THE GEIGER'] = {
 'PAPER': [
    L(['·      ·        ·     ·      ·'] * 6, 'QUIET FIELD'),
    L(['·  ·   ·   ·  ·   ·  ·   ·  ·'] * 6, 'SPARSE FIELD'),
    L(['· · ·· · · ·· ·· · · ·· · · ·'] * 6, 'BUSY FIELD'),
    L(['░·░·░··░·░··░░·░·░··░·░··░░·░'] * 5, 'HOT FIELD'),
    L(['▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲',
       '  ▲   ▲   ▲   ▲   ▲   ▲   ▲  '] * 3, 'TREFOIL FIELD'),
    T('CAL 1 kHz ' + RULE[:14] + ' 0 dBFS', label='TONE', fft='none'),
    L(['█▓▒░ █▓▒░ █▓▒░ █▓▒░ █▓▒░', '░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█ ░▒▓█'] * 2,
      'BARS', fft='none'),
    SNOW(),
 ],
 'TRACE': [
    L(['│·         │·        ·│      '], 'CLICKS 12'),
    L(['│· │·   ·│    │·  ·│   │·  · '], 'CLICKS 88'),
    L(['│·│· │·│ ·│·│ │·│· │·│ ·│·│ ·'], 'CLICKS 347'),
    L(['│││·│││·││·│││·││·│││·│││·││·'], 'CLICKS 2100'),
    L(['█│█│█│█│█│█│█│█│█│█│█│█│█│█│█'], 'CONTINUOUS'),
    L(['────────────  CAL  ────────────'], 'FLAT CAL', fft='none'),
    L(['▲▲▲▲▲▲▲  OFF SCALE  ▲▲▲▲▲▲▲'], 'OFF SCALE'),
    L(['████████  SCREAMING  ████████'], 'SCREAMING'),
 ],
 'NEEDLE': [
    T('12 CPM'), T('88 CPM'), T('347 CPM'), T('2.1 kCPM'),
    T('OFF SCALE', label='OFF SCALE N'),
    T('K-40 · IT IS THE BANANAS', label='K-40', fft='none'),
    T('DOSE 0.2 uSv/h', label='DOSE'),
    CAL((0xFF, 0xE0, 0x20, 0xFF), (0x40, 0x38, 0x00, 0xFF)),
 ],
 'STAMP': [
    T('BACKGROUND'), T('TRACE'), T('ELEVATED'), T('HOT'),
    T('MELTDOWN'), T('DECON'), T('LEAD APRON'),
    PILOT((0xFF, 0xE0, 0x20, 0xFF), (0x00, 0x00, 0x00, 0xFF)),
 ],
 'READOUT': [
    T('COUNTING THE ROOM'), T('SOMETHING GLOWS'), T('STEP AWAY FROM THE SUB'),
    T('CHERENKOV BLUE'), T('CRITICAL MASS ON FLOOR'),
    T('RAD LAB 7 — MONITORING', label='SLATE', fft='none'),
    T('SIGNAL LOST', label='SIGNAL LOST', fft='none'),
    L(['▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜', '▌ TEST CARD · LAB 7 ▐', '▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟'],
      'TEST CARD', fft='none'),
 ],
}
