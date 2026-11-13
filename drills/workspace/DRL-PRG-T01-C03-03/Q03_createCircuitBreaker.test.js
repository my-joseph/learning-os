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

let fakeTime = 1000;
const breaker = createCircuitBreaker(flakyClearingHouse, { failureThreshold: 3, resetTimeoutMs: 40, now: () => fakeTime });

for (let i = 0; i < 3; i++) {
  await assert.rejects(async () => breaker.execute(), /Clearing house gateway error/);
}

assert.strictEqual(breaker.getState(), 'OPEN');
await assert.rejects(async () => breaker.execute(), /CIRCUIT_BREAKER_OPEN/);
assert.strictEqual(failures, 3);
});

test("[Q03-T02] should reset failure counter on successful execution preventing premature tripping", async () => {
  let calls = 0;
const unstableGateway = async () => {
  calls++;
  if (calls === 1 || calls === 3) throw new Error('Transient error');
  return 'SUCCESS';
};

let fakeTime = 1000;
const breaker = createCircuitBreaker(unstableGateway, { failureThreshold: 2, now: () => fakeTime });

await assert.rejects(async () => breaker.execute(), /Transient error/);
assert.strictEqual(breaker.getState(), 'CLOSED');

const res = await breaker.execute();
assert.strictEqual(res, 'SUCCESS');
assert.strictEqual(breaker.getState(), 'CLOSED');

await assert.rejects(async () => breaker.execute(), /Transient error/);
assert.strictEqual(breaker.getState(), 'CLOSED');
});
