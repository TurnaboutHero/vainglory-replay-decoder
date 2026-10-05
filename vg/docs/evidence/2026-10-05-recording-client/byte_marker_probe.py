"""Find byte positions in early fixed-length records constant within a corpus but different across corpora."""
import glob, os, struct, collections
def records(b):
    o = 0
    while o + 10 <= len(b):
        ts, n = struct.unpack_from('>fI', b, o); op = struct.unpack_from('>H', b, o + 8)[0]
        if n < 2 or o + 8 + n > len(b): break
        yield op, b[o + 10:o + 8 + n]; o += 8 + n
corp = {'dev': [p for p in glob.glob('D:/Desktop/My Folder/Game/VG/vg replay/**/*.0.vgr', recursive=True) if not os.path.basename(p).startswith('._')],
        'vgna': glob.glob('D:/VG_EVAL/vgna-20261005/families/*/*.0.vgr'),
        'steamtemp': [p for p in glob.glob('D:/DevCache/Temp/a8d06624*.0.vgr') if os.path.getsize(p) > 0]}
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
    shared = [i for i in range(n) if all(i in const[c] for c in corp if first[c][op])]
    print('  positions constant in every corpus:', len(shared), 'of', n)
