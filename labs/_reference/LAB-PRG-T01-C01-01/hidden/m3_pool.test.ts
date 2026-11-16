import assert from "node:assert/strict";
import test from "node:test";
const { PromisePool } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("active task count never exceeds the configured limit", async () => {
  let active = 0;
  let maximumActive = 0;
  const tasks = Array.from({ length: 7 }, (_, index) => async () => {
    active += 1;
    maximumActive = Math.max(maximumActive, active);
    await Promise.resolve();
    active -= 1;
    return index;
  });
  const outcomes = await new PromisePool(3).run(tasks);
  assert.equal(maximumActive, 3);
  assert.equal(outcomes.length, 7);
});

test("invalid capacity is rejected and an empty batch needs no workers", async () => {
  assert.throws(() => new PromisePool(0), RangeError);
  assert.throws(() => new PromisePool(1.5), RangeError);
  assert.deepEqual(await new PromisePool(2).run([]), []);
});
