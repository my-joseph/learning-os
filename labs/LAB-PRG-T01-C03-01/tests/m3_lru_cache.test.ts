import assert from "node:assert/strict";
import test from "node:test";
const { CacheConfigError, createLRUCache } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("createLRUCache rejects invalid capacity and evicts least-recently-used entries", () => {
  assert.throws(() => createLRUCache(0), (err: unknown) => err instanceof CacheConfigError);
  const cache = createLRUCache<string, number>(2);
  cache.put("alpha", 1);
  cache.put("beta", 2);
  assert.equal(cache.get("alpha"), 1);
  cache.put("gamma", 3);

  assert.equal(cache.has("beta"), false);
  assert.equal(cache.get("beta"), undefined);
  assert.deepEqual(cache.keysInRecencyOrder(), ["gamma", "alpha"]);
  assert.deepEqual(cache.stats(), { hits: 1, misses: 1, evictions: 1, size: 2 });
});

test("createLRUCache promotes updated keys without triggering eviction", () => {
  const cache = createLRUCache<string, string>(2);
  cache.put("k1", "v1");
  cache.put("k2", "v2");
  cache.put("k1", "v1-updated");
  cache.put("k3", "v3");
  assert.equal(cache.get("k1"), "v1-updated");
  assert.equal(cache.has("k2"), false);
  assert.equal(cache.delete("k1"), true);
  assert.equal(cache.delete("k1"), false);
  assert.equal(cache.size(), 1);
});
