// Auto-generated visible test suite for DRL-PRG-T01-C03-02 Q01
const test = require('node:test');
const assert = require('node:assert');
const { RateLimiter } = require('./Q01_RateLimiter.js');


test("[Q01-T01] should allow up to maxRequests within window and decrement remaining", async () => {
  const limiter = new RateLimiter({ maxRequests: 3, windowMs: 150 });
            const r1 = limiter.consume('client:A');
            const r2 = limiter.consume('client:A');
            const r3 = limiter.consume('client:A');

            assert.strictEqual(r1.allowed, true);
            assert.strictEqual(r1.remaining, 2);
            assert.strictEqual(r2.remaining, 1);
            assert.strictEqual(r3.remaining, 0);

            const r4 = limiter.consume('client:A');
            assert.strictEqual(r4.allowed, false);
            assert.strictEqual(r4.remaining, 0);
            assert.ok(r4.resetMs > 0, "resetMs should indicate time until window slides");
});

test("[Q01-T02] should emit 'blocked' event on rate limit breach", async () => {
  const limiter = new RateLimiter({ maxRequests: 1, windowMs: 100 });
            let blockedKey = null;
            let blockedReset = null;

            limiter.on('blocked', (key, resetMs) => {
              blockedKey = key;
              blockedReset = resetMs;
            });

            limiter.consume('ip:192.168.1.1'); // allowed
            limiter.consume('ip:192.168.1.1'); // blocked!

            assert.strictEqual(blockedKey, 'ip:192.168.1.1');
            assert.ok(blockedReset > 0);
});

test("[Q01-T03] should slide window over time and restore allowance", async () => {
  const limiter = new RateLimiter({ maxRequests: 1, windowMs: 50 });
            assert.strictEqual(limiter.consume('user:99').allowed, true);
            assert.strictEqual(limiter.consume('user:99').allowed, false);

            await new Promise(r => setTimeout(r, 65));
            assert.strictEqual(limiter.consume('user:99').allowed, true, "Allowance restored after window expires");
});
