// Append after the byte-identical stock player_state_probe.js.
// start({verified_executable_sha256, handoff_marker: 'cooldown-live-laa-v1',
//        actor_id, max_samples?: 1..600, duration_ms?: 1..120000}).
;(() => {
  'use strict';
  const original = rpc.exports;
  const stock = {
    start: original.start.bind(original), sample: original.sample.bind(original),
    stop: original.stop.bind(original)
  };
  const HASH = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc';
  let active = false, alarm = null, moduleBase, actorId, pinnedActor = null;
  let count = 0, maxSamples = 600, started = 0, duration = 120000, reads = 0;
  let stopReason = 'not_started';
  let failureCode = null;
  class CollectorError extends Error {
    constructor(code) { super('Collector: ' + code); this.code = code; }
  }
  const fail = code => { throw new CollectorError(code); };
  function stop(reason) {
    if (alarm !== null) clearTimeout(alarm);
    alarm = null;
    if (active) {
      active = false;
      stopReason = reason;
      stock.stop();
    }
    return {samples: count, stopped: true, reason: stopReason, failure_code: failureCode};
  }
  function address(p, nullable = false) {
    const text = p.toString();
    if (!/^0x[0-9a-f]{1,8}$/i.test(text)) fail('malformed_pointer');
    const value = Number(text);
    if (nullable && value === 0) return p;
    if (value < 0x10000 || value % 4 !== 0) fail('malformed_pointer');
    return p;
  }
  function read(p, offset, width, method) {
    address(p);
    if (++reads > 4096) fail('read_budget');
    const start = Number(p.toString()) + offset;
    if (!Number.isInteger(offset) || start < 0x10000 || start + width > 0x100000000) fail('pointer_overflow');
    const at = p.add(offset), range = Process.findRangeByAddress(at);
    if (!range || !range.protection.includes('r') ||
        start + width > Number(range.base.toString()) + range.size) fail('unreadable_pointer');
    return at[method]();
  }
  const u32 = (p, off) => read(p, off, 4, 'readU32');
  const u8 = (p, off) => read(p, off, 1, 'readU8');
  function pointer(p, off) {
    const result = address(read(p, off, 4, 'readPointer'), true);
    if (!result.isNull()) read(result, 0, 4, 'readU32');
    return result;
  }
  const va = value => moduleBase.add(value - 0x400000);
  function selected(snapshot) {
    if (!snapshot || !Array.isArray(snapshot.players) || snapshot.players.length > 200)
      fail('stock_players');
    const rows = snapshot.players.filter(row => row.native_actor_id === actorId);
    if (rows.length !== 1) fail('actor_selection');
    const row = rows[0];
    if (typeof row.actor !== 'string' || !/^0x[0-9a-f]{1,8}$/i.test(row.actor))
      fail('malformed_pointer');
    address(ptr(row.actor));
    return row;
  }
  function identity(actor) {
    const id = u32(actor, 0x178);
    if (id !== actorId) fail('changed_actor');
    return {id, type: pointer(actor, 4).toString(),
      component: pointer(actor, 0x20).toString(), inventory: pointer(actor, 0x34).toString()};
  }
  function children(actor) {
    const seen = new Set();
    let child = pointer(actor, 0x0c);
    while (!child.isNull()) {
      const key = child.toString();
      if (seen.has(key)) fail('child_cycle');
      if (seen.size >= 256) fail('child_capacity');
      seen.add(key);
      child = pointer(child, 0x10);
    }
    return seen;
  }
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  function floatBits(bits) {
    const view = new DataView(new ArrayBuffer(4));
    view.setUint32(0, bits, true);
    const value = view.getFloat32(0, true);
    return {bits, signed_bits: bits | 0, value: Number.isFinite(value) ? value : null,
      negative_zero: Object.is(value, -0), nonfinite: !Number.isFinite(value)};
  }
  function timerGuards(inner) {
    // Timer ctor 00958d70 and resolver 00541fa0, for the verified LAA build only.
    if (u32(inner, 0) !== va(0x0127baac).toUInt32()) fail('timer_inner_vtable');
    if (u32(va(0x0127baac), 8) !== va(0x00541fa0).toUInt32()) fail('timer_resolver_slot');
    const bytes = [0x8d, 0x41, 0xec, 0xf7, 0xd9, 0x1b, 0xc9, 0x23, 0xc1, 0xc3];
    for (let i = 0; i < bytes.length; i++)
      if (u8(va(0x00541fa0), i) !== bytes[i]) fail('timer_resolver_bytes');
  }
  function timerBody(body, p) {
    if (u32(body, 0) !== va(0x0127ba9c).toUInt32()) fail('timer_body_vtable');
    const descriptor = pointer(body, 4), classIndex = u32(va(0x0209133c), 0);
    if (classIndex > 65535 || descriptor.isNull() || u32(descriptor, 0x54) !== classIndex)
      fail('timer_class');
    const root = pointer(va(0x020ec828), 0);
    if (root.isNull()) fail('timer_pool_missing');
    const table = pointer(root, 0);
    if (table.isNull() || !descriptor.equals(table.add(classIndex * 0x17c)))
      fail('timer_pool_identity');
    if (!pointer(body, 8).equals(p) || !children(p).has(body.toString()))
      fail('timer_owner_membership');
    const callback = u32(body, 0x1c);
    if (callback !== p.add(0x1c).toUInt32()) fail('timer_callback');
    const storage = pointer(descriptor, 0x168), stride = u32(descriptor, 0x58);
    if (storage.isNull() || stride < 0x2c || stride > 0x100000) fail('timer_stride');
    const delta = Number(body.toString()) - Number(storage.toString());
    const slot = delta / stride;
    if (delta < 0 || !Number.isInteger(slot) || slot > 65535) fail('timer_slot');
    const bits = pointer(descriptor, 0x178);
    if (bits.isNull()) fail('timer_pending_bits');
    if ((u8(bits, Math.floor(slot / 8)) & (1 << (slot % 8))) !== 0) fail('timer_pending');
    return {descriptor: descriptor.toString(), class_index: classIndex,
      storage: storage.toString(), stride, slot, pending_bits: bits.toString(), callback,
      pending: false};
  }
  function timer(p) {
    const result = {pointer: null, body_pointer: null,
      expected_generation: null, actual_generation: null, generation_equal: null,
      native_handle_proof: 'bounded_timer_specific_static_checks_only',
      native_handle_verified: false, lifetime_unverified: true, atomic: false,
      status: 'unavailable', availability: 'unknown', reason: 'null_timer',
      remaining_f32: null, initial_f32: null, pause_byte: null,
      legacy_inner_plus_24: {semantics: 'unverified_raw_bits_not_cooldown', raw: null}};
    try {
      const inner = pointer(p, 0x20), expected = u32(p, 0x24);
      result.pointer = inner.isNull() ? null : inner.toString();
      result.expected_generation = expected;
      if (inner.isNull()) return result;
      const actual = u32(inner, 4);
      Object.assign(result, {actual_generation: actual, generation_equal: actual === expected});
      if (actual !== expected) fail('generation_mismatch');
      timerGuards(inner);
      // Exact timer resolver: null => 0, otherwise inner - 0x14. Never an actor rule.
      const body = address(inner.add(-0x14));
      const before = timerBody(body, p);
      const initial = floatBits(u32(body, 0x20)), remaining = floatBits(u32(body, 0x24));
      const pause = u8(body, 0x28);
      let legacy = null;
      try { legacy = floatBits(u32(inner, 0x24)); } catch (_) { /* Optional legacy diagnostic. */ }
      timerGuards(inner);
      if (!same(before, timerBody(body, p)) || u32(inner, 4) !== actual ||
          !pointer(p, 0x20).equals(inner) || u32(p, 0x24) !== expected)
        fail('changed_timer_handle');
      Object.assign(result, {status: 'observed', reason: null, body_pointer: body.toString(),
        remaining_f32: remaining, initial_f32: initial, pause_byte: pause,
        pool_checks: before,
        legacy_inner_plus_24: {semantics: 'unverified_raw_bits_not_cooldown', raw: legacy}});
    } catch (error) {
      const message = String(error.message);
      result.reason = message.startsWith('Collector: ') ? message.slice(11) : 'timer_read_failed';
    }
    return result;
  }
  function state(p, actor, childSet, classIndex) {
    if (p.isNull()) return {status: 'unavailable', reason: 'null_state', pointer: null};
    const owner = pointer(p, 8), type = pointer(p, 4);
    if (!owner.equals(actor) || !childSet.has(p.toString())) fail('state_owner_membership');
    if (type.isNull() || u32(type, 0x54) !== classIndex) fail('state_class');
    const charges = u8(p, 0x42), key = u32(p, 0x28);
    const result = {status: 'observed', pointer: p.toString(), owner: owner.toString(),
      class_index: classIndex, key, charges, lifetime_unverified: true, atomic: false,
      charge_gate: {charges_nonzero: charges !== 0, getter_short_circuits_to_zero: charges !== 0},
      timer: timer(p)};
    if (u8(p, 0x42) !== charges || u32(p, 0x28) !== key ||
        !pointer(p, 8).equals(owner) || !pointer(p, 4).equals(type) ||
        u32(type, 0x54) !== classIndex) fail('changed_state');
    return result;
  }
  function clocks() {
    const session = pointer(va(0x02091c24), 0);
    return {game_clock: session.isNull() ? null : floatBits(u32(session, 0x194)),
      record_index: u32(va(0x01ef0b38), 0)};
  }
  function inventory(actor, stockInventory, childSet, classIndex) {
    const component = pointer(actor, 0x34);
    if (component.isNull()) {
      if (stockInventory !== null) fail('changed_inventory');
      return null;
    }
    const flags = u8(component, 0x71), capacity = flags & 0x7f, occupied = u8(component, 0x70);
    if (capacity > 10 || occupied > capacity) fail('inventory_capacity');
    if (!stockInventory || stockInventory.capacity !== capacity || stockInventory.flags !== flags ||
        stockInventory.occupied !== occupied || !Array.isArray(stockInventory.items) ||
        stockInventory.items.length !== capacity) fail('changed_inventory');
    const items = [];
    for (let slot = 0; slot < capacity; slot++) {
      const item = pointer(component, 0x1c + slot * 4), prior = stockInventory.items[slot];
      if (item.isNull()) {
        if (prior !== null) fail('changed_inventory');
        items.push(null);
        continue;
      }
      const definition = pointer(item, 0x14), ability = pointer(item, 0x18);
      const row = {array_index: slot, definition_id: u32(item, 0x2c),
        instance_id: u32(item, 0x30), quantity: read(item, 0x34, 2, 'readU16'),
        item_flags: u8(item, 0x38)};
      if (!prior || !Object.keys(row).every(key => row[key] === prior[key])) fail('changed_inventory');
      Object.assign(row, {item_pointer: item.toString(),
        definition_pointer: definition.isNull() ? null : definition.toString(),
        ability_pointer: ability.isNull() ? null : ability.toString(),
        primary: ability.isNull() ? {status: 'unavailable', reason: 'null_ability'} :
          state(pointer(ability, 0x124), actor, childSet, classIndex),
        secondary: ability.isNull() ? {status: 'unavailable', reason: 'null_ability'} :
          state(pointer(ability, 0x120), actor, childSet, classIndex)});
      if (!pointer(component, 0x1c + slot * 4).equals(item) ||
          !pointer(item, 0x18).equals(ability) || !pointer(item, 0x14).equals(definition))
        fail('changed_item');
      items.push(row);
    }
    return {pointer: component.toString(), capacity, occupied, flags, items,
      order_semantics: 'native_array_index_only'};
  }
  function checkTime() {
    const elapsed = Date.now() - started;
    if (elapsed < 0 || elapsed >= duration) fail('time_limit');
  }
  rpc.exports = Object.assign({}, original, {
    start(options) {
      if (active) fail('already_started');
      if (!options || options.verified_executable_sha256 !== HASH) fail('laa_hash_required');
      if (options.handoff_marker !== 'cooldown-live-laa-v1') fail('handoff_marker_required');
      if (!Number.isInteger(options.actor_id) || options.actor_id < 0 || options.actor_id >= 0xffffffff)
        fail('actor_id_required');
      const limit = options.max_samples === undefined ? 600 : options.max_samples;
      const ms = options.duration_ms === undefined ? 120000 : options.duration_ms;
      if (!Number.isInteger(limit) || limit < 1 || limit > 600 ||
          !Number.isInteger(ms) || ms < 1 || ms > 120000) fail('invalid_limits');
      // Preserve the five stock guards; timer guards run before each body observation.
      stock.start(options);
      active = true;
      try {
        moduleBase = address(Process.getModuleByName('Vainglory.exe').base);
        actorId = options.actor_id; maxSamples = limit; duration = ms;
        count = 0; pinnedActor = null; started = Date.now(); stopReason = null; failureCode = null;
        alarm = setTimeout(() => stop('time_limit'), duration);
        return {collector_version: 2, actor_id: actorId, passive: true, max_samples: limit,
          duration_ms: ms, handoff_marker: options.handoff_marker,
          executable_hash_source: 'caller_verified_handoff', verified_executable_sha256: HASH};
      } catch (_) { stop('start_failed'); fail('start_failed'); }
    },
    sample() {
      if (!active) fail('not_started');
      try {
        checkTime();
        reads = 0;
        const clockBefore = clocks();
        const before = selected(stock.sample()), actor = ptr(before.actor);
        if (pinnedActor !== null && !actor.equals(ptr(pinnedActor))) fail('changed_actor');
        const idBefore = identity(actor), childSet = children(actor);
        if (idBefore.component !== before.component) fail('changed_actor');
        const classIndex = u32(va(0x01ef0b3c), 0);
        if (classIndex > 65535) fail('state_class_index');
        const items = inventory(actor, before.inventory, childSet, classIndex);
        const after = selected(stock.sample());
        if (!actor.equals(ptr(after.actor)) || before.definition_id !== after.definition_id ||
            before.team_raw !== after.team_raw || before.component !== after.component ||
            !same(idBefore, identity(actor)) || !same(before.inventory, after.inventory) ||
            !same([...childSet], [...children(actor)])) fail('changed_actor_or_inventory');
        const clockAfter = clocks();
        checkTime();
        pinnedActor = actor.toString();
        const result = {tag: 'cooldown_live_sample', sequence: ++count, actor_id: actorId,
          actor_pointer: pinnedActor, actor_identity_before: idBefore, actor_identity_after: idBefore,
          actor_identity_unchanged: true, lifetime_unverified: true, atomic: false,
          native_handle_verified: false, inventory: items,
          game_clock_before: clockBefore.game_clock, game_clock_after: clockAfter.game_clock,
          record_index_before: clockBefore.record_index, record_index_after: clockAfter.record_index};
        if (count >= maxSamples) stop('sample_limit');
        return result;
      } catch (error) {
        failureCode = error instanceof CollectorError ? error.code : 'native_or_stock_read_failed';
        stop('sample_failed'); fail('sample_failed');
      }
    },
    stop() { return stop('requested'); }
  });
})();
