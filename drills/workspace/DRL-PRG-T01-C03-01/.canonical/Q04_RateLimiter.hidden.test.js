// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q04
const test = require('node:test');
const assert = require('node:assert');
const { RateLimiter } = require('../Q04_RateLimiter.js');


test("[Q04-HIDDEN-T01] should track separate keys independently", async () => {
  const limiter = new RateLimiter({ maxRequests: 1, windowMs: 100 });
            assert.strictEqual(limiter.consume('user:1').allowed, true);
            assert.strictEqual(limiter.consume('user:1').allowed, false);
            assert.strictEqual(limiter.consume('user:2').allowed, true, "Separate keys must have independent quotas");
});

test("[Q04-HIDDEN-T02] should reset quota when reset(key) is invoked", async () => {
  const limiter = new RateLimiter({ maxRequests: 1, windowMs: 500 });
            limiter.consume('keyA');
            limiter.reset('keyA');
            assert.strictEqual(limiter.consume('keyA').allowed, true);
});
