// Hidden Trap Test Suite for DRL-PRG-T01-C03-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { AsyncCache } = require('../Q03_AsyncCache.js');


test("[Q03-HIDDEN-T01] should clean up inFlight map even if fetcher throws an error", async () => {
  const cache = new AsyncCache(100);
            let attempts = 0;
            const failingFetcher = async () => {
              attempts++;
              throw new Error("Network timeout");
            };

            await assert.rejects(() => cache.getOrFetch('fail', failingFetcher), /Network timeout/);
            // Subsequent request should not be permanently locked
            await assert.rejects(() => cache.getOrFetch('fail', failingFetcher), /Network timeout/);
            assert.strictEqual(attempts, 2, "inFlight lock must be released on rejection");
});

test("[Q03-HIDDEN-T02] should invalidate key and clear cache cleanly", async () => {
  const cache = new AsyncCache(500);
            let val = 10;
            await cache.getOrFetch('k1', async () => val);
            cache.invalidate('k1');
            val = 20;
            assert.strictEqual(await cache.getOrFetch('k1', async () => val), 20);
});
