"""Compare section-0 structure across replay corpora (no payload or player data printed)."""
import glob, json, os, re, struct, sys, collections, hashlib
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
corp = {'dev': [p for p in glob.glob('D:/Desktop/My Folder/Game/VG/vg replay/**/*.0.vgr', recursive=True) if not os.path.basename(p).startswith('._')],
        'vgna': glob.glob('D:/VG_EVAL/vgna-20261005/families/*/*.0.vgr'),
        'steamtemp': [p for p in glob.glob('D:/DevCache/Temp/a8d06624*.0.vgr') if os.path.getsize(p) > 0]}
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
            for s in re.findall(rb'[ -~]{6,}', pl):
                s = s.decode()
                if re.search(r'\d+\.\d+|ver|build|client|vgna|steam|ios|android|win', s, re.I): strings[s[:60]] += 1
        for sec in family(p):
            for _, _, op, n, _ in records(open(sec, 'rb').read()): oplen[op][n] += 1
    out[name] = {'files': len(files), 'head_sig_top': [(list(map(hex, k)), v) for k, v in head_sig.most_common(4)],
                 'first3_op_len': [([(hex(a), b) for a, b in k], v) for k, v in first_len.most_common(6)],
                 'version_like_strings': strings.most_common(25),
                 'oplen': {hex(op): dict(c.most_common(8)) for op, c in oplen.items()}}
json.dump(out, open('D:/VG_EVAL/client_probe.json', 'w'), indent=1)
for name, o in out.items():
    print('==', name, o['files']); print(' head', o['head_sig_top'][:2]); print(' first3', o['first3_op_len'][:4]); print(' strings', o['version_like_strings'][:12])
ops = {n: set(o['oplen']) for n, o in out.items()}
print('ops only in vgna', sorted(ops['vgna'] - ops['dev'] - ops['steamtemp'])[:30])
print('ops only in dev', sorted(ops['dev'] - ops['vgna'])[:30])
