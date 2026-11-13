// Auto-generated visible test suite for DRL-PRG-T00-C02-01 Q02
const test = require('node:test');
const assert = require('node:assert');
const { createCounterRegistry } = require('./Q02_createCounterRegistry.js');


test("[Q02-T01] should record and accumulate counts across multiple metrics", async () => {
  const registry = createCounterRegistry();
assert.strictEqual(registry.getCount('http_requests'), 0);
registry.increment('http_requests');
registry.increment('http_requests', 4);
registry.increment('db_errors', 2);
assert.strictEqual(registry.getCount('http_requests'), 5);
assert.strictEqual(registry.getCount('db_errors'), 2);
});

test("[Q02-T02] should protect internal registry state from external mutation via snapshot", async () => {
  const registry = createCounterRegistry();
registry.increment('api_calls', 10);
const snapshot = registry.getSnapshot();
assert.strictEqual(snapshot.api_calls, 10);
snapshot.api_calls = 999; // Attempt external corruption
assert.strictEqual(registry.getCount('api_calls'), 10);
});
