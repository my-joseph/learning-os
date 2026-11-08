// Auto-generated visible test suite for DRL-PRG-T01-C03-01 Q03
const test = require('node:test');
const assert = require('node:assert');
const { AsyncCache } = require('./Q03_AsyncCache.js');


test("[Q03-T01] should deduplicate concurrent fetches for the same key (prevent cache stampede)", async () => {
  const cache = new AsyncCache(200);
            let fetchCount = 0;
            const slowFetcher = async (key) => {
              fetchCount++;
              await new Promise(r => setTimeout(r, 40));
              return { key, count: fetchCount };
            };

            const [r1, r2, r3] = await Promise.all([
              cache.getOrFetch('user:101', slowFetcher),
              cache.getOrFetch('user:101', slowFetcher),
              cache.getOrFetch('user:101', slowFetcher),
            ]);

            assert.strictEqual(fetchCount, 1, "Fetcher should be called exactly once for concurrent requests");
            assert.deepStrictEqual(r1, { key: 'user:101', count: 1 });
            assert.deepStrictEqual(r2, { key: 'user:101', count: 1 });
            assert.deepStrictEqual(r3, { key: 'user:101', count: 1 });
});

test("[Q03-T02] should isolate returned cached objects from external caller mutations", async () => {
  const cache = new AsyncCache(200);
            const fetcher = async () => ({ roles: ['viewer'], metadata: { active: true } });

            const firstResult = await cache.getOrFetch('user:roles', fetcher);
            firstResult.roles.push('superadmin');
            firstResult.metadata.active = false;

            const secondResult = await cache.getOrFetch('user:roles', fetcher);
            assert.deepStrictEqual(secondResult.roles, ['viewer'], "Cache must not be corrupted by caller mutation");
            assert.strictEqual(secondResult.metadata.active, true);
});

test("[Q03-T03] should refetch data once TTL expires", async () => {
  const cache = new AsyncCache(50);
            let fetchCount = 0;
            const fetcher = async () => ++fetchCount;

            assert.strictEqual(await cache.getOrFetch('counter', fetcher), 1);
            await new Promise(r => setTimeout(r, 70));
            assert.strictEqual(await cache.getOrFetch('counter', fetcher), 2, "Must refetch after TTL expires");
});
