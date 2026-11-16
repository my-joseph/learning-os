import assert from "node:assert/strict";
import test from "node:test";
const { PromisePool } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("pool preserves input order when task completion order differs", async () => {
  const pool = new PromisePool(2);
  const outcomes = await pool.run([
    async () => "first",
    async () => "second",
    () => "third",
  ]);
  assert.deepEqual(outcomes, [
    { status: "fulfilled", value: "first" },
    { status: "fulfilled", value: "second" },
    { status: "fulfilled", value: "third" },
  ]);
});

test("a failed task is recorded while later tasks still run", async () => {
  const pool = new PromisePool(1);
  const marker = new Error("delivery failed");
  let laterTaskRan = false;
  const outcomes = await pool.run([
    () => { throw marker; },
    () => { laterTaskRan = true; return "continued"; },
  ]);
  assert.equal(outcomes[0]?.status, "rejected");
  assert.equal(laterTaskRan, true);
  assert.deepEqual(outcomes[1], { status: "fulfilled", value: "continued" });
});
