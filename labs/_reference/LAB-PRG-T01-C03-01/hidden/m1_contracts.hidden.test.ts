import assert from "node:assert/strict";
import test from "node:test";
const { CacheConfigError, validateCapacity } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("validateCapacity rejects zero, negative, fractional, NaN, and Infinity", () => {
  assert.equal(validateCapacity(1), 1);
  assert.equal(validateCapacity(100), 100);
  for (const bad of [0, -1, -100, 0.5, 3.14, Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
    assert.throws(
      () => validateCapacity(bad),
      (err: unknown) => err instanceof CacheConfigError && err.name === "CacheConfigError",
      `Expected CacheConfigError for capacity ${String(bad)}`
    );
  }
});
