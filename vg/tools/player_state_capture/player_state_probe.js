'use strict';
// Passive fixed-build pool observer. The launcher supplies its verified file hash.
let running = false, base = null, sequence = 0;
const guards = [
  {name: 'actor_resolve', rva: 4553072, bytes: '558bec81ec24030000a1284fe40133c58945fc568b750883feff74386a00ff35', relocations: [10]},
  {name: 'actor_enumerate', rva: 13806672, bytes: '558bec51a128c80e02538b5d085657697d107c0100000338897dfc8b8f700100', relocations: [5]},
  {name: 'scoreboard_update', rva: 3111552, bytes: '558bec83ec0c538bd98b4b0c85c90f849a0400008b43103b41047414c7430c00', relocations: []},
  {name: 'replay_read', rva: 827696, bytes: '558bec51a1d809eb01535685c074538b75108a5d14506a01', relocations: [5]},
  {name: 'replay_apply', rva: 963744, bytes: '558bec83ec08568bf18b460483f802747983f8017517e8e5', relocations: []}
];
function va(address) { return base.add(address - 0x400000); }
function rawFloat(address) { return {value: address.readFloat(), bits: address.readU32()}; }
function attribute(component, index, minimum, maximum) {
  const layers = [0x20, 0xd4, 0x188, 0x23c].map(offset => rawFloat(component.add(offset + index * 4)));
  const f = Math.fround;
  const total = f(f(f(f(layers[3].value + 1) * layers[1].value) + layers[0].value) * f(layers[2].value + 1));
  const lower = va(minimum).readFloat(), upper = va(maximum).readFloat();
  return {layers, lower, upper, value: Math.max(lower, Math.min(upper, total))};
}
function actorPointers() {
  const root = va(0x020ec828).readPointer();
  if (root.isNull()) return [];
  const table = root.readPointer(), classIndex = va(0x01e6ee20).readU32();
  if (classIndex > 65535) throw Error('Invalid actor class index');
  const pool = table.add(classIndex * 0x17c), packed = pool.add(0x170).readU32();
  const end = packed & 0xffff, count = (packed >>> 16) & 0x7fff;
  if (count > end || count > 200) throw Error('Actor pool exceeds native lookup bound');
  const stride = pool.add(0x58).readU32();
  if (stride < 0x17c || stride > 0x100000) throw Error('Invalid actor stride');
  const storage = pool.add(0x168).readPointer(), indices = pool.add(0x16c).readPointer();
  const bits = pool.add(0x178).readPointer(), result = [];
  for (let i = end - count; i < end; i++) {
    const index = indices.add(i * 2).readU16();
    if ((bits.add((index >>> 5) * 4).readU32() & (1 << (index & 31))) !== 0) continue;
    result.push(storage.add(index * stride));
  }
  return result;
}
function displayName(row) {
  const length = row.add(8).readU32(), capacity = row.add(12).readU32();
  if (length > 128 || length > capacity) throw Error('Invalid display name length');
  if (length === 0) return '';
  return row.add(16).readPointer().readUtf16String(length).replace(/\u0000$/, '');
}
function inventory(actor) {
  const component = actor.add(0x34).readPointer();
  if (component.isNull()) return null;
  const flags = component.add(0x71).readU8(), capacity = flags & 0x7f;
  if (capacity > 10) throw Error('Invalid inventory capacity');
  const items = [];
  for (let slot = 0; slot < capacity; slot++) {
    const item = component.add(0x1c + slot * 4).readPointer();
    items.push(item.isNull() ? null : {array_index: slot,
      definition_id: item.add(0x2c).readU32(), instance_id: item.add(0x30).readU32(),
      quantity: item.add(0x34).readU16(), item_flags: item.add(0x38).readU8()});
  }
  return {capacity, flags, occupied: component.add(0x70).readU8(), items,
    order_semantics: 'native_array_index_only'};
}
function replayReader() {
  const object = va(0x01ef0e80).readPointer();
  if (object.isNull()) return null;
  if (!object.readPointer().equals(va(0x012179b8))) return {kind: 'not_replay'};
  const length = object.add(0x818).readU32();
  if (length > 2048) throw Error('Native replay buffer exceeds 2048 bytes');
  const nameObject = va(0x018ff124), nameLength = nameObject.add(0x10).readU32();
  const nameCapacity = nameObject.add(0x14).readU32();
  if (nameLength > 240 || nameLength > nameCapacity) throw Error('Invalid replay slot string');
  const nameData = nameCapacity > 15 ? nameObject.readPointer() : nameObject;
  const bytes = new Uint8Array(object.add(0x15).readByteArray(length));
  return {kind: 'replay', object: object.toString(), mode: object.add(4).readU32(),
    playback_time: rawFloat(object.add(0xc)), buffered_record_time: rawFloat(object.add(0x10)),
    needs_record: object.add(0x14).readU8(), content_length: length,
    content_hex: Array.from(bytes, b => b.toString(16).padStart(2, '0')).join(''),
    section: va(0x01ef0b38).readU32(), file_open: !va(0x01eb09d8).readPointer().isNull(),
    slot_name: nameLength ? nameData.readUtf8String(nameLength) : ''};
}
function sample() {
  if (!running) throw Error('Observer not started');
  const readerBefore = replayReader();
  const before = va(0x1ef0b38).readU32();
  const rosterCount = va(0x020e7408).readU32(), rosterBase = va(0x020e7404).readPointer();
  if (rosterCount > 64) throw Error('Invalid native roster count');
  const roster = new Map();
  for (let i = 0; i < rosterCount; i++) {
    const row = rosterBase.add(i * 0xb8), id = row.add(4).readU32();
    if (id !== 0xffffffff) roster.set(id, {native_actor_id: id, display_name: displayName(row), definition_id: row.add(0x78).readU32(), team_raw: row.add(0xb0).readU8()});
  }
  const players = [];
  for (const actor of actorPointers()) {
    const id = actor.add(0x178).readU32();
    if (!roster.has(id)) continue;
    const component = actor.add(0x20).readPointer();
    if (component.isNull()) throw Error('Player lacks stat component');
    const kills = attribute(component, 41, 0x01a5961c, 0x0209c7c4);
    const deaths = attribute(component, 42, 0x01a59620, 0x0209c7c8);
    players.push(Object.assign({}, roster.get(id), {actor: actor.toString(), component: component.toString(),
      inventory: inventory(actor), kills, deaths, assists: rawFloat(component.add(0x31c)),
      resource14: rawFloat(component.add(0x328)), gold_balance: rawFloat(component.add(0x308)),
      net_worth: rawFloat(component.add(0x30c))}));
  }
  const session = va(0x02091c24).readPointer();
  const readerAfter = replayReader();
  return {tag: 'player_state_sample', sequence: ++sequence, utc_ms: Date.now(), pid: Process.id,
    game_clock: session.isNull() ? null : rawFloat(session.add(0x194)),
    game_clock_flags: session.isNull() ? null : session.add(0x19d).readU8(),
    replay_reader_before: readerBefore, replay_reader_after: readerAfter,
    replay_reader_unchanged: JSON.stringify(readerBefore) === JSON.stringify(readerAfter),
    record_clock_unverified: rawFloat(va(0x01ef0b30)), record_index_before: before,
    record_index_after: va(0x01ef0b38).readU32(), atomic_record_boundary: false,
    roster_count: roster.size, players};
}
rpc.exports = {
  start(options) {
    if (running) throw Error('Observer already started');
    if (!options || !['659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642', 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'].includes(options.verified_executable_sha256)) throw Error('Unverified executable build');
    if (Process.arch !== 'ia32') throw Error('Observer requires PE32');
    base = Process.getModuleByName('Vainglory.exe').base;
    const delta = base.sub(ptr('0x400000')).toUInt32();
    for (const guard of guards) {
      const expected = new Uint8Array(guard.bytes.match(/../g).map(x => parseInt(x, 16)));
      const view = new DataView(expected.buffer);
      for (const offset of guard.relocations) view.setUint32(offset, (view.getUint32(offset, true) + delta) >>> 0, true);
      const actual = new Uint8Array(base.add(guard.rva).readByteArray(expected.length));
      if (actual.some((byte, i) => byte !== expected[i])) throw Error('Build guard failed: ' + guard.name);
    }
    running = true;
    return {pid: Process.id, base: base.toString(), guards: guards.length, passive: true, probe_version: 2};
  },
  sample,
  stop() { running = false; return {samples: sequence}; }
};
