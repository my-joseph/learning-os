// Hidden Trap Test Suite for DRL-PRG-T01-C03-03 Q01
const test = require('node:test');
const assert = require('node:assert');
const { createTelemetryRateLimiter } = require('../Q01_createTelemetryRateLimiter.js');


test("[Q01-HIDDEN-T01] should enforce capacity ceiling without cheating or overflow", async () => {
  let fakeTime = 10000;
const limiter = createTelemetryRateLimiter({ capacity: 5, refillRate: 2, initialTokens: 0, now: () => fakeTime });
fakeTime += 1000;
assert.strictEqual(limiter.consume(5), false);
assert.strictEqual(limiter.consume(2), true);
fakeTime += 100000;
assert.strictEqual(limiter.consume(5), true);
assert.strictEqual(limiter.consume(1), false);
});
