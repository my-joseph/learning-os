// Auto-generated visible test suite for DRL-PRG-T01-C03-03 Q02
const test = require('node:test');
const assert = require('node:assert');
const { createCoalescingAsyncCache } = require('./Q02_createCoalescingAsyncCache.js');


test("[Q02-T01] should retrieve cached values on subsequent sequential requests", async () => {
  let fetchCount = 0;
const mockFetcher = async (symbol) => {
  fetchCount++;
  return { symbol, price: 65000 };
};

const cache = createCoalescingAsyncCache(mockFetcher);
const first = await cache.get('BTC-USD');
const second = await cache.get('BTC-USD');

assert.strictEqual(first.price, 65000);
assert.strictEqual(second.price, 65000);
assert.strictEqual(fetchCount, 1);
});

test("[Q02-T02] should coalesce concurrent in-flight requests into a single fetch (Reproducer Test)", async () => {
  let fetchCount = 0;
const slowFetcher = async (symbol) => {
  fetchCount++;
  await new Promise(r => setTimeout(r, 25));
  return { symbol, depth: 100 };
};

const cache = createCoalescingAsyncCache(slowFetcher);
const results = await Promise.all([
  cache.get('ETH-USD'),
  cache.get('ETH-USD'),
  cache.get('ETH-USD'),
  cache.get('ETH-USD'),
  cache.get('ETH-USD')
]);

assert.strictEqual(results.length, 5);
assert.strictEqual(results[0].depth, 100);
assert.strictEqual(fetchCount, 1);
});
