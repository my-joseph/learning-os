import assert from "node:assert/strict";
import test from "node:test";
const { CacheConfigError, createLRUCache } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("multiple LRUCache instances remain completely isolated and respect capacity 1", () => {
  assert.throws(() => createLRUCache<string, number>(0), CacheConfigError);

  const first = createLRUCache<string, number>(2);
  const second = createLRUCache<string, number>(2);

  first.put("sharedKey", 10);
  first.put("onlyFirst", 20);
  second.put("sharedKey", 99);

  assert.equal(first.get("sharedKey"), 10);
  assert.equal(second.get("sharedKey"), 99);
  assert.equal(second.has("onlyFirst"), false);
  assert.deepEqual(first.keysInRecencyOrder(), ["sharedKey", "onlyFirst"]);
  assert.deepEqual(second.keysInRecencyOrder(), ["sharedKey"]);

  const tiny = createLRUCache<string, string>(1);
  tiny.put("a", "alpha");
  tiny.put("a", "alpha-2");
  assert.equal(tiny.size(), 1);
  assert.equal(tiny.stats().evictions, 0);
  tiny.put("b", "beta");
  assert.equal(tiny.get("a"), undefined);
  assert.equal(tiny.get("b"), "beta");
  assert.deepEqual(tiny.stats(), { hits: 1, misses: 1, evictions: 1, size: 1 });
});
