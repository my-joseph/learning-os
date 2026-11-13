// Auto-generated visible test suite for DRL-PRG-T01-C03-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { createTokenBucketLimiter } = require('./Q01_createTokenBucketLimiter.js');


test("[Q01-T01] should consume tokens up to capacity and reject excessive demand", async () => {
  const limiter = createTokenBucketLimiter({ capacity: 3, refillRate: 10 });
assert.strictEqual(limiter.consume(1), true);
assert.strictEqual(limiter.consume(2), true);
assert.strictEqual(limiter.consume(1), false);
});

test("[Q01-T02] should refill tokens over elapsed time interval", async () => {
  const limiter = createTokenBucketLimiter({ capacity: 2, refillRate: 100, initialTokens: 0 });
assert.strictEqual(limiter.consume(1), false);
await new Promise(r => setTimeout(r, 30));
assert.strictEqual(limiter.consume(1), true);
});
