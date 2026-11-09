// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q05
const test = require('node:test');
const assert = require('node:assert');
const { createEventEmitter } = require('./Q05_createEventEmitter.js');


test("[Q05-T01] registers listener and emits multiple events", async () => {
  const emitter = createEventEmitter(); const calls = []; emitter.on('data', x => calls.push(x)); emitter.emit('data', 10); emitter.emit('data', 20); assert.deepStrictEqual(calls, [10, 20]);
});

test("[Q05-T02] unsubscribe removes the specific listener", async () => {
  const emitter = createEventEmitter(); let count = 0; const unsub = emitter.on('tick', () => { count++; }); emitter.emit('tick'); unsub(); emitter.emit('tick'); assert.strictEqual(count, 1); assert.strictEqual(emitter.listenerCount('tick'), 0);
});
