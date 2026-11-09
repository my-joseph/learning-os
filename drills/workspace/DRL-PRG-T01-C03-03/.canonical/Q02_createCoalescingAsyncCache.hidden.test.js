// Hidden Trap Test Suite for DRL-PRG-T01-C03-03 Q02
const test = require('node:test');
const assert = require('node:assert');
const { createCoalescingAsyncCache } = require('../Q02_createCoalescingAsyncCache.js');


test("[Q02-HIDDEN-T01] should handle synchronous and asynchronous errors and clean up in-flight state", async () => {
  let attempt = 0;
const syncFailingFetcher = (symbol) => {
  attempt++;
  if (attempt === 1) throw new Error('Synchronous API crash');
  return Promise.resolve({ symbol, status: 'RECOVERED' });
};

const cache = createCoalescingAsyncCache(syncFailingFetcher);
await assert.rejects(async () => cache.get('SOL-USD'), /Synchronous API crash/);
const recovered = await cache.get('SOL-USD');
assert.strictEqual(recovered.status, 'RECOVERED');
assert.strictEqual(attempt, 2);
});
