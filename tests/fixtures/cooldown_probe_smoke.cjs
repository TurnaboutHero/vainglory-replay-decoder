'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {execFileSync, spawnSync} = require('node:child_process');
const crypto = require('node:crypto');
const repo = path.resolve(__dirname, '../..');
const evidence = path.resolve(process.argv[2] || '.omo/evidence/cooldown-collector');
fs.mkdirSync(evidence, {recursive: true});
const git = (...args) => execFileSync('git', ['-C', repo, ...args], {encoding: 'utf8'});
const head = git('rev-parse', 'HEAD').trim(), status = git('status', '--porcelain');
const sourcePath = 'vg/tools/player_state_capture/player_state_probe.js';
const stock = git('show', `33611314a29d2ad57a4c56a2f6da569b22ec9641:${sourcePath}`);
assert.equal(fs.readFileSync(path.join(repo, sourcePath), 'utf8'), stock);
const extensionPath = path.join(repo, 'vg/tools/player_state_capture/cooldown_probe.js');
const extension = fs.readFileSync(extensionPath, 'utf8');
const combined = stock + '\n' + extension;
const combinedPath = path.join(evidence, 'stock-plus-collector.js');
fs.writeFileSync(combinedPath, combined);
const HASH = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc';
const options = {verified_executable_sha256: HASH, handoff_marker: 'cooldown-live-laa-v1', actor_id: 1500};
const A = 0x100000, I = 0x110000, ITEM = 0x120000, DEF = 0x130000, AB = 0x140000;
const S = 0x150000, S2 = 0x160000, T = 0x170000, TYPE = 0x180000, ATYPE = 0x190000, COMP = 0x1a0000;
function fixture(useStock = false, delta = 0) {
  const pages = new Map(), alarms = new Map();
  let now = 1000, timerSerial = 0, samples = 0, starts = 0, stops = 0, nativeReads = 0;
  const f = {onRead: null, onSample: null, rejectStart: false, denied: null};
  const va = n => n + delta;
  function page(n) {
    const key = Math.floor(n / 4096) * 4096;
    if (!pages.has(key)) pages.set(key, Buffer.alloc(4096));
    return pages.get(key);
  }
  function put(n, value, width = 4) {
    const bytes = Buffer.alloc(width);
    bytes.writeUIntLE(value, 0, width);
    for (let j = 0; j < width; j++) page(n + j)[(n + j) % 4096] = bytes[j];
  }
  function bytes(n, len) {
    nativeReads++;
    if (f.onRead) f.onRead(n, len);
    const b = Buffer.alloc(len);
    for (let j = 0; j < len; j++) {
      const p = pages.get(Math.floor((n + j) / 4096) * 4096);
      if (!p) throw Error('unmapped mock read');
      b[j] = p[(n + j) % 4096];
    }
    return b;
  }
  class Pointer {
    constructor(n) { this.n = Number(n); }
    add(n) { return new Pointer(this.n + n); }
    sub(p) { return new Pointer(this.n - p.n); }
    toUInt32() { return this.n >>> 0; }
    toString() { return '0x' + this.n.toString(16); }
    isNull() { return this.n === 0; }
    equals(p) { return this.n === p.n; }
    readU32() { return bytes(this.n, 4).readUInt32LE(); }
    readFloat() { return bytes(this.n, 4).readFloatLE(); }
    readU16() { return bytes(this.n, 2).readUInt16LE(); }
    readU8() { return bytes(this.n, 1)[0]; }
    readPointer() { return new Pointer(this.readU32()); }
    readByteArray(n) { return Uint8Array.from(bytes(this.n, n)).buffer; }
  }
  for (const p of [A, I, ITEM, DEF, AB, S, S2, T, TYPE, ATYPE, COMP]) page(p);
  put(A + 0x178, 1500); put(A + 4, ATYPE); put(A + 0xc, S);
  put(A + 0x20, COMP); put(A + 0x34, I);
  put(I + 0x71, 1, 1); put(I + 0x70, 1, 1); put(I + 0x1c, ITEM);
  put(ITEM + 0x14, DEF); put(ITEM + 0x18, AB); put(ITEM + 0x2c, 487);
  put(ITEM + 0x30, 23); put(ITEM + 0x34, 2, 2); put(ITEM + 0x38, 3, 1);
  put(AB + 0x124, S); put(AB + 0x120, S2);
  put(S + 0x10, S2); put(TYPE + 0x54, 7); put(va(0x1ef0b3c), 7);
  for (const [p, key] of [[S, 0x6f056481], [S2, 0xabcdef01]]) {
    put(p + 8, A); put(p + 4, TYPE); put(p + 0x28, key); put(p + 0x42, 3, 1);
    put(p + 0x20, p === S ? T + 0x14 : 0); put(p + 0x24, 99);
  }
  const pool = 0x200000 + 9 * 0x17c, root = 0x210000, bitset = 0x220000;
  put(T, va(0x0127ba9c)); put(T + 4, pool); put(T + 8, S); put(S + 0xc, T);
  put(T + 0x14, va(0x0127baac)); put(T + 0x18, 99);
  put(T + 0x1c, S + 0x1c); put(S + 0x1c, 0x541000);
  put(T + 0x20, 0x41a00000); put(T + 0x24, 0x41200000); put(T + 0x28, 1, 1);
  put(T + 0x38, 0);
  put(va(0x0209133c), 9); put(pool + 0x54, 9);
  put(va(0x020ec828), root); put(root, 0x200000); page(0x200000);
  put(pool + 0x168, T - 8 * 0x40); page(T - 8 * 0x40);
  put(pool + 0x58, 0x40); put(pool + 0x178, bitset); page(bitset);
  put(va(0x0127baac) + 8, va(0x00541fa0));
  for (const [i, byte] of Buffer.from('8d41ecf7d91bc923c1c3', 'hex').entries())
    put(va(0x00541fa0) + i, byte, 1);
  put(va(0x02091c24), COMP); put(COMP + 0x194, 0x41400000);
  put(va(0x01ef0b38), 42);
  put(va(0x01e6ee20), 1);
  put(0x200000 + 0x17c + 0x170, 0x10001);
  put(0x200000 + 0x17c + 0x58, 0x200);
  put(0x200000 + 0x17c + 0x168, A);
  put(0x200000 + 0x17c + 0x16c, 0x230000); put(0x230000, 0);
  put(0x200000 + 0x17c + 0x178, 0x240000); put(0x240000, 0);
  put(va(0x020e7408), 1); put(va(0x020e7404), 0x250000);
  put(0x250000 + 4, 1500); put(0x250000 + 0x78, 999); put(0x250000 + 0xb0, 1, 1);
  for (const addr of [0x01a5961c, 0x01a59620, 0x0209c7c4, 0x0209c7c8, 0x01ef0e80, 0x01ef0b30])
    put(va(addr), 0);
  const row = {native_actor_id: 1500, actor: '0x100000', component: '0x1a0000',
    definition_id: 999, team_raw: 1, display_name: 'DO_NOT_EXPORT_NAME',
    inventory: {capacity: 1, occupied: 1, flags: 1, items: [{array_index: 0,
      definition_id: 487, instance_id: 23, quantity: 2, item_flags: 3}]}};
  const original = {
    start(o) { starts++; assert.equal(o, f.startOptions); if (f.rejectStart) throw Error('Build guard failed'); },
    sample() {
      samples++;
      const out = {players: [structuredClone(row)], replay_reader_before: {
        content_hex: 'DO_NOT_EXPORT_CONTENT', slot_name: 'DO_NOT_EXPORT_SLOT'}};
      if (f.onSample) f.onSample(samples, out);
      return out;
    },
    stop() { stops++; return {secret: 'DO_NOT_EXPORT_STOP'}; }
  };
  const context = vm.createContext({rpc: {exports: original}, ptr: n => new Pointer(n),
    Process: {arch: 'ia32', id: 123, getModuleByName: () => ({base: new Pointer(va(0x400000))}),
      findRangeByAddress(p) {
        if (f.denied && p.n >= f.denied[0] && p.n < f.denied[1]) return null;
        const base = Math.floor(p.n / 4096) * 4096;
        return pages.has(base) ? {base: new Pointer(base), size: 4096, protection: 'rw-'} : null;
      }}, Date: {now: () => now},
    setTimeout(cb, ms) { const id = ++timerSerial; alarms.set(id, {cb, at: now + ms}); return id; },
    clearTimeout(id) { alarms.delete(id); }
  });
  if (useStock) {
    vm.runInContext(stock, context);
    for (const guard of vm.runInContext('guards', context)) {
      const b = Buffer.from(guard.bytes, 'hex');
      for (const offset of guard.relocations) b.writeUInt32LE((b.readUInt32LE(offset) + delta) >>> 0, offset);
      for (let j = 0; j < b.length; j++) put(va(0x400000) + guard.rva + j, b[j], 1);
    }
    vm.runInContext(extension, context);
  } else vm.runInContext(extension, context);
  Object.assign(f, {pool, bitset, root, va, api: context.rpc.exports, original, context, put, row,
    begin(extra = {}) { f.startOptions = {...options, ...extra}; return f.api.start(f.startOptions); },
    advance(ms, fire = true) {
      now += ms;
      if (fire) for (const [id, alarm] of [...alarms]) if (alarm.at <= now) {
        alarms.delete(id); alarm.cb();
      }
    },
    counts: () => ({starts, samples, stops, alarms: alarms.size, nativeReads})});
  return f;
}
const results = [];
function test(scenario, observable, run) {
  try { const details = run(); results.push({scenario, observable, pass: true, details}); }
  catch (error) { results.push({scenario, observable, pass: false, error: error.stack}); }
}
function failsClosed(f) {
  assert.throws(() => f.api.sample(), /Collector: sample_failed/);
  assert.equal(f.counts().stops, 1);
  assert.equal(f.counts().alarms, 0);
  assert.throws(() => f.api.sample(), /not_started/);
}
test('syntax: standalone, smoke, concatenated stock', 'each node --check exits 0', () => {
  return [extensionPath, __filename, combinedPath].map(file => {
    const command = [process.execPath, '--check', file];
    const run = spawnSync(command[0], command.slice(1), {encoding: 'utf8'});
    assert.equal(run.status, 0, run.stderr);
    return {command, exit_code: run.status};
  });
});
test('start input gates', 'invalid hash, marker, actor and limits rejected before stock start', () => {
  const invalid = [{verified_executable_sha256: '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642'},
    {verified_executable_sha256: HASH.toUpperCase()}, {handoff_marker: undefined}, {handoff_marker: true},
    {actor_id: undefined}, {actor_id: '1500'}, {actor_id: -1}, {actor_id: 0xffffffff}, {actor_id: 1.5},
    {max_samples: 601}, {max_samples: 0}, {max_samples: 1.5}, {duration_ms: 120001}, {duration_ms: 0}];
  for (const options of invalid) {
    const f = fixture(); assert.throws(() => f.begin(options), /Collector:/); assert.equal(f.counts().starts, 0);
  }
  return {rejected_cases: invalid.length};
});
test('captured stock exports and clean stop', 'start/sample/stop delegate; repeated stop is idempotent', () => {
  const f = fixture(); assert.notEqual(f.api, f.original); f.begin();
  f.original.sample = () => { throw Error('exports were not captured'); };
  assert.throws(() => f.begin(), /already_started/);
  const output = f.api.sample(); f.api.stop(); f.api.stop();
  assert.equal(f.counts().starts, 1); assert.equal(f.counts().samples, 2);
  assert.equal(f.counts().stops, 1); assert.equal(f.counts().alarms, 0);
  return {counts: f.counts(), output};
});
test('stock start rejection', 'stock byteguard error propagates and sampling stays unavailable', () => {
  const f = fixture(); f.rejectStart = true;
  assert.throws(() => f.begin(), /Build guard failed/); assert.throws(() => f.api.sample(), /not_started/);
  assert.equal(f.counts().alarms, 0);
});
test('real stock byteguard delegation', 'real stock accepts fixture bytes and rejects corruption in all five guards', () => {
  const good = fixture(true); good.begin(); good.api.stop();
  const guards = vm.runInContext('guards', good.context);
  for (const guard of guards) {
    const f = fixture(true); f.put(0x400000 + guard.rva, 0, 1);
    assert.throws(() => f.begin(), /Build guard failed/);
    assert.throws(() => f.api.sample(), /not_started/);
  }
  const wrongArch = fixture(true); wrongArch.context.Process.arch = 'x64';
  assert.throws(() => wrongArch.begin(), /requires PE32/);
  return {guard_names: Array.from(guards, g => g.name), source: sourcePath};
});
test('independent item/state/timer reads and redaction', 'exact fields match fixture; sensitive stock fields absent', () => {
  const f = fixture(); f.begin(); const out = f.api.sample(), item = out.inventory.items[0];
  assert.equal(item.definition_pointer, '0x130000'); assert.equal(item.ability_pointer, '0x140000');
  assert.equal(item.definition_id, 487); assert.equal(item.instance_id, 23); assert.equal(item.quantity, 2);
  assert.equal(item.primary.key, 0x6f056481); assert.equal(item.secondary.key, 0xabcdef01);
  assert.equal(item.primary.charges, 3); assert.equal(item.primary.owner, '0x100000');
  assert.equal(item.primary.class_index, 7); assert.equal(item.primary.timer.pointer, '0x170014');
  assert.equal(item.primary.timer.expected_generation, 99); assert.equal(item.primary.timer.actual_generation, 99);
  assert.equal(item.primary.timer.remaining_f32.bits, 0x41200000);
  assert.equal(item.primary.timer.remaining_f32.value, 10); assert.equal(item.primary.timer.pause_byte, 1);
  assert.equal(out.atomic, false); assert.equal(out.lifetime_unverified, true);
  assert.equal(item.primary.timer.native_handle_verified, false);
  assert.equal(item.primary.timer.native_handle_proof, 'bounded_timer_specific_static_checks_only');
  assert.doesNotMatch(JSON.stringify(out), /DO_NOT_EXPORT|display_name|content_hex|slot_name/);
  fs.writeFileSync(path.join(evidence, 'sample.json'), JSON.stringify(out, null, 2) + '\n');
});
test('nonfinite and negative zero float bits', 'NaN payloads/infinities retained with null; finite -0 retained in JS', () => {
  for (const bits of [0x7fc01234, 0x7f800000, 0xff800000, 0x80000000]) {
    const f = fixture(); f.put(T + 0x24, bits); f.begin();
    const value = f.api.sample().inventory.items[0].primary.timer.remaining_f32;
    assert.equal(value.bits, bits);
    if (bits === 0x80000000) assert.equal(Object.is(value.value, -0), true);
    else assert.equal(value.value, null);
  }
});
test('null state, ability, inventory and empty slot', 'safe unavailable objects or null inventory/slot', () => {
  const state = fixture(); state.put(AB + 0x124, 0); state.put(AB + 0x120, 0); state.begin();
  assert.equal(state.api.sample().inventory.items[0].primary.reason, 'null_state');
  const ability = fixture(); ability.put(ITEM + 0x18, 0); ability.begin();
  assert.equal(ability.api.sample().inventory.items[0].secondary.reason, 'null_ability');
  const inv = fixture(); inv.put(A + 0x34, 0); inv.row.inventory = null; inv.begin();
  assert.equal(inv.api.sample().inventory, null);
  const slot = fixture(); slot.put(I + 0x1c, 0); slot.row.inventory.items[0] = null; slot.begin();
  assert.equal(slot.api.sample().inventory.items[0], null);
});
test('null timer and mismatched generations', 'remaining/pause unavailable; mismatch payload never read', () => {
  for (const nullTimer of [true, false]) {
    const f = fixture(); f.put(nullTimer ? S + 0x20 : T + 0x18, nullTimer ? 0 : 100);
    if (!nullTimer) f.onRead = n => { if (n === T + 0x24 || n === T + 0x28) throw Error('stale payload read'); };
    f.begin(); const timer = f.api.sample().inventory.items[0].primary.timer;
    assert.equal(timer.status, 'unavailable'); assert.equal(timer.remaining_f32, null);
    assert.equal(timer.pause_byte, null); assert.equal(timer.reason, nullTimer ? 'null_timer' : 'generation_mismatch');
  }
});
const mutations = {
  'malformed pointer': f => f.put(ITEM + 0x18, 3),
  'unmapped pointer': f => f.put(ITEM + 0x18, 0xdead0000),
  'oversized pointer string': f => { f.row.actor = '0x100100000'; },
  'child cycle': f => f.put(S2 + 0x10, S),
  'wrong owner': f => f.put(S + 8, I),
  'state outside childlist': f => f.put(A + 0xc, S2),
  'wrong state class': f => f.put(TYPE + 0x54, 8),
  'null class': f => f.put(S + 4, 0),
  'class global bound': f => f.put(0x1ef0b3c, 65536),
  'inventory capacity': f => f.put(I + 0x71, 11, 1),
  'occupied capacity': f => f.put(I + 0x70, 2, 1),
  'independent inventory mismatch': f => f.put(ITEM + 0x30, 24),
  'actor id mismatch': f => f.put(A + 0x178, 1501),
  'missing actor': f => { f.row.native_actor_id = 1501; },
  'duplicate actor': f => { f.onSample = (_, out) => out.players.push({...out.players[0]}); },
  'changed actor after reads': f => { f.onSample = n => { if (n === 2) f.put(A + 0x178, 1501); }; },
  'changed actor pointer after reads': f => { f.onSample = (n, out) => { if (n === 2) out.players[0].actor = '0x110000'; }; },
  'changed inventory after reads': f => { f.onSample = (n, out) => { if (n === 2) out.players[0].inventory.items[0].quantity++; }; },
  'childlist capacity': f => {
    f.put(A + 0xc, 0x300000);
    for (let i = 0; i < 257; i++) f.put(0x300000 + i * 0x100 + 0x10, i === 256 ? 0 : 0x300100 + i * 0x100);
  }
};
for (const [name, mutate] of Object.entries(mutations)) test(name, 'sample rejects, stock stops once, alarm cleared', () => {
  const f = fixture(); mutate(f); f.begin(); failsClosed(f);
  assert.ok(f.counts().nativeReads < 4096);
});
test('stock sample exception redaction', 'arbitrary stock error text cannot escape', () => {
  const f = fixture(); f.onSample = () => { throw Error('DO_NOT_EXPORT_NAME'); }; f.begin(); failsClosed(f);
});
test('sample limits including hard 600 cap', 'Nth sample succeeds and stops; N+1 fails without stock reads', () => {
  for (const limit of [1, 600]) {
    const f = fixture(); f.begin({max_samples: limit});
    for (let i = 1; i <= limit; i++) assert.equal(f.api.sample().sequence, i);
    const calls = f.counts().samples;
    assert.throws(() => f.api.sample(), /not_started/);
    assert.equal(calls, limit * 2); assert.equal(f.counts().samples, calls);
    assert.equal(f.api.stop().reason, 'sample_limit'); assert.equal(f.counts().stops, 1);
  }
});
test('120 second timer stop without polling', 'idle alarm invokes stock stop and rejects future sample', () => {
  const f = fixture(); f.begin(); f.advance(119999); f.api.sample(); f.advance(1);
  assert.equal(f.api.stop().reason, 'time_limit'); assert.equal(f.counts().stops, 1);
  assert.throws(() => f.api.sample(), /not_started/);
});
test('deadline gates and backwards clock', 'delayed timer dispatch, mid-read expiry, backwards time fail closed', () => {
  const delayed = fixture(); delayed.begin(); delayed.advance(120000, false); failsClosed(delayed);
  assert.equal(delayed.counts().samples, 0);
  const mid = fixture(); mid.onSample = n => { if (n === 2) mid.advance(120000, false); };
  mid.begin(); failsClosed(mid);
  const back = fixture(); back.begin(); back.advance(-1, false); failsClosed(back);
});
test('static passive API boundary', 'extension has no native calls, writes, hooks, or timestamp reconstruction', () => {
  assert.doesNotMatch(extension, /NativeFunction|Interceptor|Memory\s*\.\s*write|\.write(?:U|S|Float|Double|Pointer|Byte|Utf)|content_hex|display_name|slot_name/);
  assert.equal(Object.keys(fixture().api).sort().join(','), 'sample,start,stop');
});
test('stock byte preservation', 'stock matches existing baseline bytes independent of current commit', () => {
  assert.equal(fs.readFileSync(path.join(repo, sourcePath), 'utf8'), stock);
});

test('original inner-offset bug', 'inner+24 is zero while resolved body+24 is positive', () => {
  const f = fixture(); f.begin();
  const state = f.api.sample().inventory.items[0].primary, timer = state.timer;
  assert.equal(timer.body_pointer, '0x170000');
  assert.equal(timer.legacy_inner_plus_24.raw.bits, 0);
  assert.equal(timer.legacy_inner_plus_24.raw.value, 0);
  assert.match(timer.legacy_inner_plus_24.semantics, /unverified/);
  assert.equal(timer.remaining_f32.value, 10);
  assert.equal(timer.initial_f32.value, 20);
  assert.equal(timer.pool_checks.slot, 8);
  assert.equal(timer.pool_checks.pending, false);
  assert.equal(timer.availability, 'unknown');
  assert.equal(state.charge_gate.getter_short_circuits_to_zero, true);
  return {state};
});
test('charge gate independent of missing timer', 'nonzero and zero charges keep missing timer unknown', () => {
  for (const charges of [0, 3]) {
    const f = fixture(); f.put(S + 0x20, 0); f.put(S + 0x42, charges, 1); f.begin();
    const state = f.api.sample().inventory.items[0].primary;
    assert.equal(state.charges, charges);
    assert.equal(state.charge_gate.getter_short_circuits_to_zero, charges !== 0);
    assert.equal(state.timer.status, 'unavailable');
    assert.equal(state.timer.availability, 'unknown');
    assert.equal(state.timer.remaining_f32, null);
  }
});
test('ASLR-adjusted timer and stock guards', 'relocated guards accept correct pointers and reject preferred-address slot', () => {
  const delta = 0x10000000, f = fixture(false, delta);
  f.begin(); assert.equal(f.api.sample().inventory.items[0].primary.timer.remaining_f32.value, 10);
  const real = fixture(true, delta); real.begin(); real.api.stop();
  f.put(f.va(0x0127baac) + 8, 0x00541fa0);
  assert.equal(f.api.sample().inventory.items[0].primary.timer.reason, 'timer_resolver_slot');
});
const timerMutations = {
  'inner vtable': [f => f.put(T + 0x14, 0), 'timer_inner_vtable'],
  'virtual slot': [f => f.put(f.va(0x0127baac) + 8, 0x541fb0), 'timer_resolver_slot'],
  'resolver bytes': [f => f.put(f.va(0x00541fa0) + 2, 0xed, 1), 'timer_resolver_bytes'],
  'body vtable': [f => f.put(T, 0), 'timer_body_vtable'],
  'timer type': [f => f.put(f.pool + 0x54, 10), 'timer_class'],
  'null descriptor': [f => f.put(T + 4, 0), 'timer_class'],
  'timer global class bound': [f => f.put(f.va(0x0209133c), 65536), 'timer_class'],
  'pool identity': [f => f.put(f.root, TYPE), 'timer_pool_identity'],
  'missing pool': [f => f.put(f.va(0x020ec828), 0), 'timer_pool_missing'],
  'timer owner': [f => f.put(T + 8, S2), 'timer_owner_membership'],
  'timer child membership': [f => f.put(S + 0xc, 0), 'timer_owner_membership'],
  'timer child cycle': [f => f.put(T + 0x10, T), 'child_cycle'],
  'timer callback': [f => f.put(T + 0x1c, 0), 'timer_callback'],
  'callback vtable is not callback subobject': [f => f.put(T + 0x1c, 0x541000), 'timer_callback'],
  'pending second bitset byte': [f => f.put(f.bitset + 1, 1, 1), 'timer_pending'],
  'null pending bitset': [f => f.put(f.pool + 0x178, 0), 'timer_pending_bits'],
  'zero stride': [f => f.put(f.pool + 0x58, 0), 'timer_stride'],
  'small stride': [f => f.put(f.pool + 0x58, 0x28), 'timer_stride'],
  'huge stride': [f => f.put(f.pool + 0x58, 0x100001), 'timer_stride'],
  'misaligned slot': [f => f.put(f.pool + 0x168, T - 4), 'timer_slot'],
  'negative slot': [f => f.put(f.pool + 0x168, T + 0x40), 'timer_slot'],
  'slot out of bounds': [f => { f.put(f.pool + 0x168, 0x10000); f.put(f.pool + 0x58, 0x40);
    f.put(S + 0x20, 0x410000 + 0x14); f.put(0x410000 + 0x14, f.va(0x0127baac));
    f.put(0x410000 + 0x18, 99); f.put(0x410000, f.va(0x0127ba9c));
    f.put(0x410000 + 4, f.pool); f.put(0x410000 + 8, S);
    f.put(0x410000 + 0x1c, S + 0x1c); f.put(S + 0xc, 0x410000); f.put(0x10000, 0);
  }, 'timer_slot'],
  'unreadable payload': [f => { f.denied = [T + 0x24, T + 0x28]; }, 'unreadable_pointer'],
  'unreadable bitset': [f => { f.denied = [f.bitset + 1, f.bitset + 2]; }, 'unreadable_pointer'],
  'unreadable resolver': [f => { f.denied = [f.va(0x00541fa0), f.va(0x00541fa0) + 10]; }, 'unreadable_pointer'],
  'initial generation mismatch': [f => f.put(T + 0x18, 100), 'generation_mismatch'],
  'state generation mismatch': [f => f.put(S + 0x24, 100), 'generation_mismatch'],
  'changed generation': [f => { f.onRead = n => { if (n === T + 0x24) f.put(T + 0x18, 100); }; }, 'changed_timer_handle'],
  'changed expected generation': [f => { f.onRead = n => { if (n === T + 0x24) f.put(S + 0x24, 100); }; }, 'changed_timer_handle'],
  'changed handle': [f => { f.onRead = n => { if (n === T + 0x24) f.put(S + 0x20, 0); }; }, 'changed_timer_handle'],
  'pending after payload': [f => { f.onRead = n => { if (n === T + 0x24) f.put(f.bitset + 1, 1, 1); }; }, 'timer_pending'],
  'owner after payload': [f => { f.onRead = n => { if (n === T + 0x24) f.put(T + 8, S2); }; }, 'timer_owner_membership'],
  'membership after payload': [f => { f.onRead = n => { if (n === T + 0x24) f.put(S + 0xc, 0); }; }, 'timer_owner_membership'],
  'callback after payload': [f => { f.onRead = n => { if (n === T + 0x24) f.put(T + 0x1c, 0); }; }, 'timer_callback']
};
for (const [name, [mutate, reason]] of Object.entries(timerMutations))
  test('timer reject: ' + name, 'unavailable/unknown with no remaining, initial or pause payload', () => {
    const f = fixture(); mutate(f); f.begin();
    const timer = f.api.sample().inventory.items[0].primary.timer;
    assert.equal(timer.status, 'unavailable'); assert.equal(timer.availability, 'unknown');
    assert.equal(timer.reason, reason); assert.equal(timer.remaining_f32, null);
    assert.equal(timer.initial_f32, null); assert.equal(timer.pause_byte, null);
    assert.equal(timer.native_handle_verified, false); assert.equal(timer.lifetime_unverified, true);
    return {timer};
  });
test('guards precede body reads', 'corrupt resolver never touches derived body fields', () => {
  for (const corrupt of ['virtual slot', 'resolver bytes', 'inner vtable']) {
    const f = fixture(); timerMutations[corrupt][0](f);
    const bodyReads = [];
    f.onRead = n => { if (n >= T && n < T + 0x2c && n !== T + 0x14 && n !== T + 0x18) bodyReads.push(n); };
    f.begin(); const timer = f.api.sample().inventory.items[0].primary.timer;
    assert.equal(timer.status, 'unavailable'); assert.equal(timer.reason, timerMutations[corrupt][1]);
    assert.deepEqual(bodyReads, []);
  }
});
test('all resolver instruction bytes guarded', 'each of ten byte corruptions rejects before body read', () => {
  const code = Buffer.from('8d41ecf7d91bc923c1c3', 'hex');
  for (let i = 0; i < code.length; i++) {
    const f = fixture(); f.put(f.va(0x00541fa0) + i, code[i] ^ 1, 1); f.begin();
    assert.equal(f.api.sample().inventory.items[0].primary.timer.reason, 'timer_resolver_bytes');
  }
});
test('full stock concatenation samples native mock pools', 'real stock start/sample/stop works with corrected extension at two bases', () => {
  const outputs = [];
  for (const delta of [0, 0x10000000]) {
    const f = fixture(true, delta); f.begin(); const out = f.api.sample(); f.api.stop();
    assert.equal(out.inventory.items[0].primary.timer.remaining_f32.value, 10);
    assert.equal(out.inventory.items[0].primary.timer.legacy_inner_plus_24.raw.value, 0);
    assert.equal(out.actor_id, 1500); assert.equal(out.game_clock_before.value, 12);
    assert.doesNotMatch(JSON.stringify(out), /display_name|content_hex|slot_name/);
    outputs.push(out);
  }
  return {outputs};
});
test('pending bit is specific to timer slot', 'other pending slots do not reject nonpending slot 8', () => {
  const f = fixture(); f.put(f.bitset, 0xff, 1); f.put(f.bitset + 1, 0xfe, 1); f.begin();
  assert.equal(f.api.sample().inventory.items[0].primary.timer.status, 'observed');
});
test('missing clock and legacy diagnostic', 'missing clock is null; unreadable legacy field does not change verified body field', () => {
  const f = fixture(); f.put(f.va(0x02091c24), 0); f.denied = [T + 0x38, T + 0x3c]; f.begin();
  const out = f.api.sample(), timer = out.inventory.items[0].primary.timer;
  assert.equal(out.game_clock_before, null); assert.equal(out.game_clock_after, null);
  assert.equal(timer.remaining_f32.value, 10); assert.equal(timer.legacy_inner_plus_24.raw, null);
});
test('clock and record boundaries', 'raw game clocks and indices independently captured before/after with no atomic claim', () => {
  const f = fixture();
  f.onSample = n => { if (n === 2) { f.put(COMP + 0x194, 0x41500000); f.put(f.va(0x01ef0b38), 43); } };
  f.begin(); const out = f.api.sample();
  assert.equal(out.game_clock_before.bits, 0x41400000);
  assert.equal(out.game_clock_before.value, 12); assert.equal(out.game_clock_after.value, 13);
  assert.equal(out.record_index_before, 42); assert.equal(out.record_index_after, 43);
  assert.equal(out.atomic, false); return {out};
});
test('JSON roundtrip float fidelity', 'signed bits, NaN payload and negative zero survive serialization for both timer floats', () => {
  const observed = [];
  for (const bits of [0x80000000, 0x7fc01234, 0xff800000, 0x7f800000, 0xbf800000, 0]) {
    const f = fixture(); f.put(T + 0x24, bits); f.put(T + 0x20, bits); f.begin();
    const timer = JSON.parse(JSON.stringify(f.api.sample())).inventory.items[0].primary.timer;
    for (const raw of [timer.remaining_f32, timer.initial_f32]) {
      assert.equal(raw.bits, bits); assert.equal(raw.signed_bits, bits | 0);
      assert.equal(raw.negative_zero, bits === 0x80000000);
      assert.equal(raw.nonfinite, [0x7fc01234, 0xff800000, 0x7f800000].includes(bits));
      if (raw.nonfinite) assert.equal(raw.value, null);
    }
    observed.push(timer);
  }
  return {observed};
});

test('guard failure diagnostic stays typed', 'identity race is rejected and only its stable code is retained', () => {
  const f = fixture();
  f.onSample = n => { if (n === 2) f.put(A + 0x178, 1501); };
  f.begin(); failsClosed(f);
  assert.equal(f.api.stop().failure_code, 'changed_actor');
});
test('native and stock diagnostics remain redacted', 'untrusted exception text never escapes through stop receipt', () => {
  const f = fixture();
  f.onSample = () => { throw Error('private_actor_name_and_record_content'); };
  f.begin(); failsClosed(f);
  assert.equal(f.api.stop().failure_code, 'native_or_stock_read_failed');
  assert.doesNotMatch(JSON.stringify(f.api.stop()), /private_actor_name|record_content/);
});
test('volatile actor child list remains rejected', 'new unrelated child between snapshots is not accepted as a stable sample', () => {
  const f = fixture();
  f.onSample = n => { if (n === 2) { f.put(S2 + 0x10, 0x310000); f.put(0x310000 + 0x10, 0); } };
  f.begin(); failsClosed(f);
  assert.equal(f.api.stop().failure_code, 'changed_actor_or_inventory');
});
const report = {scope: 'offline Node VM mocks and syntax only; no native runtime validation',
  invocation: `${process.execPath} ${__filename} ${evidence}`, repo_head: head, repo_status: status,
  source_sha256: Object.fromEntries([['stock', stock], ['extension', extension], ['combined', combined]]
    .map(([key, data]) => [key, crypto.createHash('sha256').update(data).digest('hex')])),
  passed: results.filter(r => r.pass).length, failed: results.filter(r => !r.pass).length,
  results: results.map(result => ({...result,
    invocation: `${process.execPath} ${__filename} ${evidence}`,
    artifact_path: path.join(evidence, 'smoke-results.json')}))};
fs.writeFileSync(path.join(evidence, 'smoke-results.json'), JSON.stringify(report, null, 2) + '\n');
process.stdout.write(JSON.stringify(report, null, 2) + '\n');
process.exitCode = report.failed ? 1 : 0;
