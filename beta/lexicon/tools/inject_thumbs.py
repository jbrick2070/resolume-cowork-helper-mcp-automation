# inject_thumbs.py - write the 40 custom pad images into the composition's own
# EmbeddedThumbnail blobs, so they travel with the .avc instead of living in a
# session-only cache. Reads thumbs/LxCy.png, writes a NEW .avc. Never edits anything else.
import re, base64, sys, os
import xml.etree.ElementTree as ET
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else 'final2.avc'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'Res React Lexicon.avc'
ORDER = sys.argv[3] if len(sys.argv) > 3 else 'BGRA'
W, H = 320, 240

# ---------------------------------------------------------------- LZF
MAX_OFF = 1 << 13
MAX_REF = (1 << 8) + (1 << 3)   # 264
MAX_LIT = 1 << 5                # 32

def lzf_compress(inp):
    n = len(inp)
    out = bytearray()
    table = {}
    lit = bytearray()
    i = 0

    def flush():
        nonlocal lit
        while lit:
            take = lit[:MAX_LIT]
            out.append(len(take) - 1)
            out.extend(take)
            lit = lit[len(take):]

    while i < n:
        if i + 2 < n:
            key = inp[i:i + 3]
            ref = table.get(bytes(key), -1)
            table[bytes(key)] = i
            off = i - ref
            if ref >= 0 and 0 < off <= MAX_OFF and inp[ref:ref + 3] == key:
                ln = 3
                lim = min(n - i, MAX_REF)
                while ln < lim and inp[ref + ln] == inp[i + ln]:
                    ln += 1
                flush()
                d = off - 1
                l = ln - 2
                if l < 7:
                    out.append((l << 5) | (d >> 8))
                    out.append(d & 0xFF)
                else:
                    out.append((7 << 5) | (d >> 8))
                    out.append(l - 7)
                    out.append(d & 0xFF)
                # index the interior of the match so later runs can reference it
                for k in range(i + 1, min(i + ln, n - 2)):
                    table[bytes(inp[k:k + 3])] = k
                i += ln
                continue
        lit.append(inp[i])
        if len(lit) == MAX_LIT:
            flush()
        i += 1
    flush()
    return bytes(out)

def lzf_decompress(inp):
    out = bytearray(); i = 0; n = len(inp)
    while i < n:
        c = inp[i]; i += 1
        if c < 32:
            l = c + 1
            out += inp[i:i + l]; i += l
        else:
            l = c >> 5
            if l == 7:
                l += inp[i]; i += 1
            r = len(out) - ((c & 0x1f) << 8) - inp[i] - 1; i += 1
            for _ in range(l + 2):
                out.append(out[r]); r += 1
    return bytes(out)

# ---------------------------------------------------------------- pixels
def png_to_raw(path, order):
    im = Image.open(path).convert('RGBA').resize((W, H), Image.LANCZOS)
    r, g, b, a = im.split()
    packed = {'RGBA': (r, g, b, a), 'BGRA': (b, g, r, a),
              'ARGB': (a, r, g, b), 'ABGR': (a, b, g, r)}[order]
    return Image.merge('RGBA', packed).tobytes()

# ---------------------------------------------------------------- inject
d = open(SRC, encoding='latin-1').read()

def clip_span(s):
    gt = d.index('>', s)
    return (s, gt + 1) if d[gt - 1] == '/' else (s, d.find('</Clip>', s) + 7)

edits = []
for m in re.finditer(r'<Clip[ >/]', d):
    s, e = clip_span(m.start())
    x = d[s:e]
    L = int(re.search(r'layerIndex="(\d+)"', x).group(1)) + 1
    C = int(re.search(r'columnIndex="(\d+)"', x).group(1)) + 1
    png = 'thumbs/L%dC%d.png' % (L, C)
    if not os.path.exists(png):
        continue
    raw = png_to_raw(png, ORDER)
    assert len(raw) == W * H * 4
    comp = lzf_compress(raw)
    assert lzf_decompress(comp) == raw, 'LZF round-trip failed for %s' % png
    b64 = base64.b64encode(comp).decode('ascii')
    block = ('<EmbeddedThumbnail encoding="LZF" width="%d" height="%d" bitdepth="32" data="%s"/>'
             % (W, H, b64))
    tm = re.search(r'<EmbeddedThumbnail[^>]*/>', x)
    if tm:
        nx = x[:tm.start()] + block + x[tm.end():]
    else:
        pm = re.search(r'(<Clip[^>]*>)', x)
        nx = (x[:pm.end()] + '\n\t\t\t<PreloadData>\n\t\t\t\t' + block +
              '\n\t\t\t</PreloadData>' + x[pm.end():])
    edits.append((s, e, nx))
    print('  L%dC%d  raw %d -> lzf %d (%.1f%%)' % (L, C, len(raw), len(comp), 100.0 * len(comp) / len(raw)))

for s, e, nx in sorted(edits, reverse=True):
    d = d[:s] + nx + d[e:]

ET.fromstring(d.encode('latin-1'))
ids = re.findall(r'uniqueId="(\d+)"', d)
assert len(ids) == len(set(ids))
assert d.count('<Clip ') == 40 and d.count('<EmbeddedThumbnail') == 40
open(OUT, 'w', encoding='latin-1', newline='').write(d)
print('WROTE %s  %d bytes | %d thumbnails injected (%s)' %
      (OUT, len(d.encode('latin-1')), len(edits), ORDER))
