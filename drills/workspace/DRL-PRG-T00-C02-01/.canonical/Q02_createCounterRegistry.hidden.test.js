// Hidden Trap Test Suite for DRL-PRG-T00-C02-01 Q02
const test = require('node:test');
const assert = require('node:assert');
const { createCounterRegistry } = require('../Q02_createCounterRegistry.js');


test("[Q02-HIDDEN-T01] should handle default increment amount and multiple distinct metrics", async () => {
  const registry = createCounterRegistry();
registry.increment('m1');
registry.increment('m2', 0);
assert.strictEqual(registry.getCount('m1'), 1);
assert.strictEqual(registry.getCount('m2'), 0);
assert.strictEqual(registry.getCount('unknown'), 0);
});
