import assert from "node:assert/strict";
import test from "node:test";
const { PromisePool } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("cancellation requested while tasks are active blocks subsequent queued work", async () => {
  const controller = new AbortController();
  let started = 0;
  const outcomes = await new PromisePool(2).run([
    () => { started += 1; controller.abort(new Error("stop")); return "one"; },
    () => { started += 1; return "two"; },
    () => { started += 1; return "three"; },
  ], controller.signal);
  assert.equal(started, 1);
  assert.equal(outcomes.length, 3);
  assert.equal(outcomes[2]?.status, "rejected");
});

test("the pool removes its abort listener after normal settlement", async () => {
  const controller = new AbortController();
  const signal = controller.signal;
  let added = 0;
  let removed = 0;
  const add = signal.addEventListener.bind(signal);
  const remove = signal.removeEventListener.bind(signal);
  signal.addEventListener = ((type, listener, options) => { if (type === "abort") added += 1; add(type, listener, options); }) as typeof signal.addEventListener;
  signal.removeEventListener = ((type, listener, options) => { if (type === "abort") removed += 1; remove(type, listener, options); }) as typeof signal.removeEventListener;
  await new PromisePool(1).run([() => "complete"], signal);
  assert.equal(added, 1);
  assert.equal(removed, 1);
});
