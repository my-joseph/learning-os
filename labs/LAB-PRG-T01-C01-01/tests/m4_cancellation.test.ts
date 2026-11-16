import assert from "node:assert/strict";
import test from "node:test";
const { PromisePool } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("cancellation prevents queued tasks from starting", async () => {
  const pool = new PromisePool(1);
  const controller = new AbortController();
  let secondTaskStarted = false;
  const outcomesPromise = pool.run([
    () => { controller.abort(new Error("request cancelled")); return "started"; },
    () => { secondTaskStarted = true; return "queued"; },
  ], controller.signal);
  const outcomes = await outcomesPromise;
  assert.equal(secondTaskStarted, false);
  assert.equal(outcomes.length, 2);
  assert.equal(outcomes[0]?.status, "fulfilled");
  assert.equal(outcomes[1]?.status, "rejected");
});

test("a signal aborted before the run starts prevents all task work", async () => {
  const controller = new AbortController();
  controller.abort(new Error("already cancelled"));
  let taskStarted = false;
  const outcomes = await new PromisePool(2).run([() => { taskStarted = true; }], controller.signal);
  assert.equal(taskStarted, false);
  assert.equal(outcomes[0]?.status, "rejected");
});
