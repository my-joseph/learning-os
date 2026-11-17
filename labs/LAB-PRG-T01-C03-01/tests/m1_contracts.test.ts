import assert from "node:assert/strict";
import test from "node:test";
const { CacheConfigError, validateCapacity } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("validateCapacity returns positive integers and rejects invalid capacities", () => {
  assert.equal(validateCapacity(1), 1);
  assert.equal(validateCapacity(64), 64);
  assert.throws(() => validateCapacity(0), (err: unknown) => err instanceof CacheConfigError);
  assert.throws(() => validateCapacity(-5), (err: unknown) => err instanceof CacheConfigError);
  assert.throws(() => validateCapacity(2.5), (err: unknown) => err instanceof CacheConfigError);
});
