// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q05
const test = require('node:test');
const assert = require('node:assert');
const { createEventEmitter } = require('../Q05_createEventEmitter.js');


test("[Q05-HIDDEN-T01] once listener triggers only once and self-unsubscribes", async () => {
  const emitter = createEventEmitter(); const log = []; emitter.once('greet', name => log.push('Hello ' + name)); emitter.emit('greet', 'Alice'); emitter.emit('greet', 'Bob'); assert.deepStrictEqual(log, ['Hello Alice']); assert.strictEqual(emitter.listenerCount('greet'), 0);
});

test("[Q05-HIDDEN-T02] passes multiple arguments and preserves listener order", async () => {
  const emitter = createEventEmitter(); let sum = 0, prod = 1; emitter.on('calc', (a, b) => sum = a + b); emitter.on('calc', (a, b) => prod = a * b); emitter.emit('calc', 4, 5); assert.strictEqual(sum, 9); assert.strictEqual(prod, 20);
});
