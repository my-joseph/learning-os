// Hidden Trap Test Suite for DRL-PRG-T01-C03-03 Q02
const test = require('node:test');
const assert = require('node:assert');
const { createCoalescingAsyncCache } = require('../Q02_createCoalescingAsyncCache.js');


test("[Q02-HIDDEN-T01] should clean up in-flight map after promise rejects", async () => {
  let attempt = 0;
const failingFetcher = async (symbol) => {
  attempt++;
  if (attempt === 1) throw new Error('Network timeout');
  return { symbol, status: 'RECOVERED' };
};

const cache = createCoalescingAsyncCache(failingFetcher);
await assert.rejects(async () => cache.get('SOL-USD'), /Network timeout/);
const recovered = await cache.get('SOL-USD');
assert.strictEqual(recovered.status, 'RECOVERED');
});
