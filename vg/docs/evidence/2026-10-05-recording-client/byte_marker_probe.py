"""Find byte positions in early fixed-length records constant within a corpus but different across corpora."""
import glob, os, struct, sys, collections
# Usage: byte_marker_probe.py DEV_ROOT VGNA_ROOT STEAM_TEMP_ROOT
def records(b):
    o = 0
    while o + 10 <= len(b):
        ts, n = struct.unpack_from('>fI', b, o); op = struct.unpack_from('>H', b, o + 8)[0]
        if n < 2 or o + 8 + n > len(b): break
        yield op, b[o + 10:o + 8 + n]; o += 8 + n
dev_root, vgna_root, steam_root = sys.argv[1:4]
real = lambda paths: [p for p in paths if not os.path.basename(p).startswith('._') and os.path.getsize(p) > 0]
corp = {'dev': real(glob.glob(os.path.join(dev_root, '**', '*.0.vgr'), recursive=True)),
        'vgna': real(glob.glob(os.path.join(vgna_root, '**', '*.0.vgr'), recursive=True)),
        'steamtemp': real(glob.glob(os.path.join(steam_root, '*.0.vgr')))}
TARGET = {0x3ee: 216, 0x3e9: 101, 0x46f: 69}
first = {c: collections.defaultdict(list) for c in corp}
for c, files in corp.items():
    for p in files:
        seen = set()
        for op, pl in records(open(p, 'rb').read()):
            if op in TARGET and op not in seen and len(pl) == TARGET[op]: first[c][op].append(pl); seen.add(op)
            if len(seen) == len(TARGET): break
for op, n in TARGET.items():
    print(f'== op {op:#x} len {n} samples', {c: len(first[c][op]) for c in corp})
    const = {}
    for c in corp:
        s = first[c][op]
        const[c] = {i: s[0][i] for i in range(n) if s and all(x[i] == s[0][i] for x in s)}
    cand = []
    for i in range(n):
        vals = {c: const[c].get(i) for c in corp if first[c][op]}
        if all(v is not None for v in vals.values()) and len(set(vals.values())) > 1: cand.append((i, vals))
    print('  constant-within/different-across positions:', cand[:20] or 'NONE')
    # Weaker marker: constant within one corpus, and that value never occurs at the position in any other corpus.
    exclusive = []
    for c in corp:
        for i, v in const[c].items():
            if all(x[i] != v for o in corp if o != c for x in first[o][op]):
                exclusive.append((c, i, v))
    print('  corpus-exclusive constant positions:', exclusive[:20] or 'NONE')
    shared = [i for i in range(n) if all(i in const[c] for c in corp if first[c][op])]
    print('  positions constant in every corpus:', len(shared), 'of', n)
