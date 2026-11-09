// Hidden Trap Test Suite for DRL-PRG-T01-C03-03 Q03
const test = require('node:test');
const assert = require('node:assert');
const { createCircuitBreaker } = require('../Q03_createCircuitBreaker.js');


test("[Q03-HIDDEN-T01] should isolate exactly one canary probe under concurrent requests in HALF_OPEN", async () => {
  let remoteCalls = 0;
let fakeTime = 5000;
let shouldFail = true;
const slowRemote = async () => {
  remoteCalls++;
  if (shouldFail) throw new Error('Upstream down');
  await new Promise(r => setTimeout(r, 20));
  return 'PROBE_SUCCESS';
};

const breaker = createCircuitBreaker(slowRemote, { failureThreshold: 1, resetTimeoutMs: 50, now: () => fakeTime });
await assert.rejects(async () => breaker.execute(), /Upstream down/);
assert.strictEqual(breaker.getState(), 'OPEN');

fakeTime += 60;
assert.strictEqual(breaker.getState(), 'HALF_OPEN');

shouldFail = false;
const outcomes = await Promise.allSettled([
  breaker.execute(),
  breaker.execute(),
  breaker.execute(),
  breaker.execute()
]);

const successes = outcomes.filter(o => o.status === 'fulfilled');
const rejected = outcomes.filter(o => o.status === 'rejected');

assert.strictEqual(successes.length, 1);
assert.strictEqual(successes[0].value, 'PROBE_SUCCESS');
assert.strictEqual(rejected.length, 3);
for (const r of rejected) {
  assert.match(r.reason.message, /CIRCUIT_BREAKER_OPEN/);
}
assert.strictEqual(remoteCalls, 2);
assert.strictEqual(breaker.getState(), 'CLOSED');
});
