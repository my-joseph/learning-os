// Hidden Trap Test Suite for DRL-PRG-T01-C03-03 Q03
const test = require('node:test');
const assert = require('node:assert');
const { createCircuitBreaker } = require('../Q03_createCircuitBreaker.js');


test("[Q03-HIDDEN-T01] should re-trip to OPEN if probe fails in HALF_OPEN state", async () => {
  const failingService = async () => { throw new Error('Permanent failure'); };
const breaker = createCircuitBreaker(failingService, { failureThreshold: 1, resetTimeoutMs: 20 });
await assert.rejects(async () => breaker.execute(), /Permanent failure/);
assert.strictEqual(breaker.getState(), 'OPEN');

await new Promise(r => setTimeout(r, 25));
assert.strictEqual(breaker.getState(), 'HALF_OPEN');

await assert.rejects(async () => breaker.execute(), /Permanent failure/);
assert.strictEqual(breaker.getState(), 'OPEN');
});
