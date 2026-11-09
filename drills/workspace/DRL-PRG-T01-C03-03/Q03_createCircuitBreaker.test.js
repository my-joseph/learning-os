// Auto-generated visible test suite for DRL-PRG-T01-C03-03 Q03
const test = require('node:test');
const assert = require('node:assert');
const { createCircuitBreaker } = require('./Q03_createCircuitBreaker.js');


test("[Q03-T01] should execute normally in CLOSED state and trip to OPEN after failure threshold", async () => {
  let failures = 0;
const flakyClearingHouse = async () => {
  failures++;
  throw new Error('Clearing house gateway error');
};

const breaker = createCircuitBreaker(flakyClearingHouse, { failureThreshold: 3, resetTimeoutMs: 40 });

for (let i = 0; i < 3; i++) {
  await assert.rejects(async () => breaker.execute(), /Clearing house gateway error/);
}

assert.strictEqual(breaker.getState(), 'OPEN');
await assert.rejects(async () => breaker.execute(), /CIRCUIT_BREAKER_OPEN/);
assert.strictEqual(failures, 3);
});

test("[Q03-T02] should transition to HALF_OPEN after cooldown and recover to CLOSED on probe success", async () => {
  let healthy = false;
const remoteService = async () => {
  if (!healthy) throw new Error('Outage');
  return 'SETTLED_TX_OK';
};

const breaker = createCircuitBreaker(remoteService, { failureThreshold: 2, resetTimeoutMs: 30 });
await assert.rejects(async () => breaker.execute(), /Outage/);
await assert.rejects(async () => breaker.execute(), /Outage/);
assert.strictEqual(breaker.getState(), 'OPEN');

await new Promise(r => setTimeout(r, 40));
assert.strictEqual(breaker.getState(), 'HALF_OPEN');

healthy = true;
const probeResult = await breaker.execute();
assert.strictEqual(probeResult, 'SETTLED_TX_OK');
assert.strictEqual(breaker.getState(), 'CLOSED');
});
