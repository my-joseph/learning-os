// Auto-generated visible test suite for DRL-PRG-T01-C03-03 Q01
const test = require('node:test');
const assert = require('node:assert');
const { createTelemetryRateLimiter } = require('./Q01_createTelemetryRateLimiter.js');


test("[Q01-T01] should allow telemetry bursts up to capacity and reject excessive packets", async () => {
  let fakeTime = 1000;
const limiter = createTelemetryRateLimiter({ capacity: 3, refillRate: 10, now: () => fakeTime });
assert.strictEqual(limiter.consume(1), true);
assert.strictEqual(limiter.consume(2), true);
assert.strictEqual(limiter.consume(1), false);
});

test("[Q01-T02] should accumulate transmission tokens incrementally across fractional time intervals", async () => {
  let fakeTime = 1000;
const limiter = createTelemetryRateLimiter({ capacity: 2, refillRate: 1, initialTokens: 0, now: () => fakeTime });
assert.strictEqual(limiter.consume(1), false);
fakeTime += 500;
assert.strictEqual(limiter.consume(1), false);
fakeTime += 500;
assert.strictEqual(limiter.consume(1), true);
assert.strictEqual(limiter.consume(1), false);
});
