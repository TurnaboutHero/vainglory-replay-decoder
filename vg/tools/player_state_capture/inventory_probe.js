'use strict';
// Passive fixed-build observer. The launcher must verify executable hash and ownership.
// Hooks only read memory. Native functions are never called by this script.
(function () {
  const module = Process.getModuleByName('Vainglory.exe');
  if (Process.arch !== 'ia32') throw Error('Inventory observer requires PE32');
  const base = module.base, va = address => base.add(address - 0x400000);
  const delta = base.sub(ptr('0x400000')).toUInt32();
  const guards = [
  {
    "name": "grant_action",
    "rva": 5562480,
    "bytes": "558bec5156578bf9ff7718e8f098f0ff8bf083c40485f60f84bf000000803d04e20902",
    "relocations": [
      31
    ]
  },
  {
    "name": "baseline_action",
    "rva": 5562736,
    "bytes": "558bec81ec54030000a1284fe40133c58945fc53568bf157ff7618e8e097f0ff",
    "relocations": [
      10
    ]
  },
  {
    "name": "actor_grant",
    "rva": 5492864,
    "bytes": "558bec51f30f104518535657ff751c8bd951f30f110424ff75148b4b34ff7510",
    "relocations": []
  },
  {
    "name": "grant",
    "rva": 5492160,
    "bytes": "558becb8d0120000e843bc8700a1284fe40133c58945fc837d0cff53568bd98b",
    "relocations": [
      14
    ]
  },
  {
    "name": "consume",
    "rva": 4662080,
    "bytes": "558bec6aff6890931f0164a1000000005083ec585657a1284fe40133c5508d45",
    "relocations": [
      6,
      23
    ]
  },
  {
    "name": "stack",
    "rva": 5568240,
    "bytes": "568bf1ff7610e87582f0ff83c40485c074508b480c85c974168b15143f090290",
    "relocations": [
      27
    ]
  },
  {
    "name": "actor_resolve",
    "rva": 4553072,
    "bytes": "558bec81ec24030000a1284fe40133c58945fc568b750883feff74386a00ff35",
    "relocations": [
      10
    ]
  },
  {
    "name": "component_constructor",
    "rva": 5604144,
    "bytes": "558bec6aff6838d11c0164a10000000050515657a1284fe40133c5508d45f464",
    "relocations": [
      6,
      21
    ]
  }
];
  for (const guard of guards) {
    const expected = new Uint8Array(guard.bytes.match(/../g).map(x => parseInt(x, 16)));
    const view = new DataView(expected.buffer);
    for (const offset of guard.relocations)
      view.setUint32(offset, (view.getUint32(offset, true) + delta) >>> 0, true);
    const actual = new Uint8Array(base.add(guard.rva).readByteArray(expected.length));
    if (actual.some((byte, i) => byte !== expected[i])) throw Error('Inventory guard: ' + guard.name);
  }
  const hooks = [], actors = new Map(), contexts = new Map();
  let sequence = 0, stopped = false;
  const LIMIT = 20000;
  function clock() {
    const session = va(0x2091c24).readPointer();
    return {game_time: session.isNull() ? null : session.add(0x194).readFloat(),
      game_time_bits: session.isNull() ? null : session.add(0x194).readU32(),
      record_clock_bits: va(0x1ef0b30).readU32(), record_index: va(0x1ef0b38).readU32()};
  }
  function emit(kind, data) {
    if (stopped) return;
    send(Object.assign({tag: 'inventory_' + kind, sequence: ++sequence, utc_ms: Date.now(),
      thread: Process.getCurrentThreadId(), clock: clock()}, data));
    if (sequence >= LIMIT) { stopped = true; send({tag: 'inventory_limit', limit: LIMIT}); }
  }
  function snapshot(component) {
    if (component.isNull()) return null;
    const flags = component.add(0x71).readU8(), capacity = flags & 0x7f;
    if (capacity > 10) throw Error('Inventory capacity exceeds native 10-pointer arrays');
    const result = {component: component.toString(), capacity, flags,
      occupied: component.add(0x70).readU8(), items: []};
    for (let slot = 0; slot < capacity; slot++) {
      const item = component.add(0x1c + slot * 4).readPointer();
      if (item.isNull()) { result.items.push(null); continue; }
      const definition = item.add(0x14).readPointer();
      result.items.push({array_index: slot, pointer: item.toString(),
        definition_id: item.add(0x2c).readU32(), instance_id: item.add(0x30).readU32(),
        quantity: item.add(0x34).readU16(), item_flags: item.add(0x38).readU8(),
        definition_pointer: definition.toString(), stackable: definition.add(0x1c).readU8(),
        max_stack: definition.add(0x20).readU32(), grant_skip_flag: definition.add(0x125).readU8()});
    }
    return result;
  }
  function actorSnapshot(actor) {
    return actor.isNull() ? null : {actor: actor.toString(), native_actor_id: actor.add(0x178).readU32(),
      inventory: snapshot(actor.add(0x34).readPointer())};
  }
  function context() { return contexts.get(Process.getCurrentThreadId()) || null; }
  function fail(name, error) {
    stopped = true; send({tag: 'inventory_error', hook: name, error: String(error)});
  }
  for (const guard of guards) {
    hooks.push(Interceptor.attach(base.add(guard.rva), {
      onEnter(args) {
        if (stopped) return;
        this.enabled = true; this.kind = guard.name;
        try {
          const object = this.context.ecx;
          if (this.kind === 'actor_resolve') { this.id = args[0].toUInt32(); return; }
          if (this.kind === 'component_constructor') { this.component = args[0]; return; }
          if (this.kind === 'grant_action' || this.kind === 'baseline_action' || this.kind === 'stack') {
            this.thread = Process.getCurrentThreadId(); this.previous = context();
            this.id = object.add(this.kind === 'stack' ? 0x10 : 0x18).readU32();
            const value = {kind: this.kind, native_actor_id: this.id};
            if (this.kind === 'baseline_action') {
              value.spawn_flag = object.add(0x358).readU8();
              value.item_count = object.add(0x45c).readU32();
              if (value.item_count > 10) throw Error('Baseline inventory length exceeds 10');
              value.entries = [];
              for (let n = 0; n < value.item_count; n++) value.entries.push({
                definition_id: object.add(0x368 + n * 4).readU32(),
                instance_id: object.add(0x390 + n * 4).readU32(),
                quantity_argument: object.add(0x3b8 + n * 4).readU32()});
            } else if (this.kind === 'grant_action') {
              value.definition_id = object.add(0x10).readU32(); value.instance_id = object.add(0x14).readU32();
            } else {
              value.instance_id = object.add(0x14).readU32(); value.quantity_argument = object.add(0x18).readU32();
            }
            contexts.set(this.thread, value); emit(this.kind + '_before', {event: value});
          } else if (this.kind === 'actor_grant') {
            const id = object.add(0x178).readU32(); actors.set(id, object); this.actor = object;
            emit('actor_grant_before', {context: context(), state: actorSnapshot(object)});
          } else {
            this.component = object;
            emit(this.kind + '_before', {context: context(), state: snapshot(object),
              args: Array.from({length: this.kind === 'grant' ? 6 : 2}, (_, n) => args[n].toUInt32())});
          }
        } catch (error) { fail(this.kind, error); }
      },
      onLeave(result) {
        if (!this.enabled || stopped) return;
        try {
          if (this.kind === 'actor_resolve') {
            if (context()) {
              if (result.isNull()) actors.delete(this.id); else actors.set(this.id, result);
            }
          } else if (this.component) {
            emit(this.kind + '_after', {context: context(), state: snapshot(this.component)});
          } else if (this.actor) {
            emit('actor_grant_after', {context: context(), state: actorSnapshot(this.actor)});
          } else {
            const actor = actors.get(this.id);
            emit(this.kind + '_after', {event: context(), state: actor ? actorSnapshot(actor) : null});
            if (this.previous) contexts.set(this.thread, this.previous); else contexts.delete(this.thread);
          }
        } catch (error) { fail(this.kind, error); }
      }
    }));
  }
  emit('ready', {pid: Process.id, base: base.toString(), guards: guards.length,
    passive: true, max_events: LIMIT, order_semantics: 'native_array_index_only'});
})();
