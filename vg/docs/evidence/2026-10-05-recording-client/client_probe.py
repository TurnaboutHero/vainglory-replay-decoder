"""Compare section-0 structure across replay corpora (no payload or player data printed)."""
import glob, json, os, re, struct, sys, collections, hashlib
# Usage: client_probe.py DEV_ROOT VGNA_ROOT STEAM_TEMP_ROOT OUT_JSON
def records(b):
    o = 0
    while o + 10 <= len(b):
        ts, n = struct.unpack_from('>fI', b, o); op = struct.unpack_from('>H', b, o + 8)[0]
        if n < 2 or o + 8 + n > len(b): break
        yield o, ts, op, n, b[o + 10:o + 8 + n]; o += 8 + n
def family(p0):
    base = p0[:-6]; secs = []
    i = 0
    while os.path.exists(f'{base}.{i}.vgr'): secs.append(f'{base}.{i}.vgr'); i += 1
    return secs
dev_root, vgna_root, steam_root, out_path = sys.argv[1:5]
real = lambda paths: [p for p in paths if not os.path.basename(p).startswith('._') and os.path.getsize(p) > 0]
corp = {'dev': real(glob.glob(os.path.join(dev_root, '**', '*.0.vgr'), recursive=True)),
        'vgna': real(glob.glob(os.path.join(vgna_root, '**', '*.0.vgr'), recursive=True)),
        'steamtemp': real(glob.glob(os.path.join(steam_root, '*.0.vgr')))}
# Only version/build-shaped tokens are counted; free-text payload strings (names) are never kept.
VERSION = re.compile(r'(?:\d+\.){1,3}\d+|(?i:build|version|vgna|steam|android|ios)[ _-]?\d*')
out = {}
for name, files in corp.items():
    head_sig = collections.Counter(); first_ops = collections.Counter(); oplen = collections.defaultdict(collections.Counter)
    strings = collections.Counter(); first_len = collections.Counter()
    for p in files:
        b0 = open(p, 'rb').read()
        rs = list(records(b0))
        head_sig[tuple(op for _, _, op, _, _ in rs[:12])] += 1
        first_len[tuple((op, n) for _, _, op, n, _ in rs[:3])] += 1
        for _, _, op, n, pl in rs[:200]:
            for text in re.findall(rb'[ -~]{6,}', pl):
                for token in VERSION.findall(text.decode()):
                    strings['version_like'] += 1
        for sec in family(p):
            for _, _, op, n, _ in records(open(sec, 'rb').read()): oplen[op][n] += 1
    out[name] = {'files': len(files), 'head_sig_top': [(list(map(hex, k)), v) for k, v in head_sig.most_common(4)],
                 'first3_op_len': [([(hex(a), b) for a, b in k], v) for k, v in first_len.most_common(6)],
                 'version_like_strings': strings.most_common(25),
                 'oplen': {hex(op): dict(c.most_common(8)) for op, c in oplen.items()}}
json.dump(out, open(out_path, 'w'), indent=1)
for name, o in out.items():
    print('==', name, o['files']); print(' head', o['head_sig_top'][:2]); print(' first3', o['first3_op_len'][:4]); print(' strings', o['version_like_strings'][:12])
ops = {n: set(o['oplen']) for n, o in out.items()}
print('ops only in vgna', sorted(ops['vgna'] - ops['dev'] - ops['steamtemp'])[:30])
print('ops only in dev', sorted(ops['dev'] - ops['vgna'])[:30])
