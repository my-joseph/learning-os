// Hidden Trap Test Suite for DRL-PRG-T01-C03-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { createTokenBucketLimiter } = require('../Q01_createTokenBucketLimiter.js');


test("[Q01-HIDDEN-T01] should clamp accrued tokens at maximum capacity during long idle", async () => {
  const limiter = createTokenBucketLimiter({ capacity: 4, refillRate: 1000, initialTokens: 0 });
await new Promise(r => setTimeout(r, 20));
assert.strictEqual(limiter.consume(4), true);
assert.strictEqual(limiter.consume(1), false);
});
