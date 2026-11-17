import assert from "node:assert/strict";
import test from "node:test";
const { err, flatMapResult, mapResult, ok } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("M1 hidden: flatMapResult does not invoke callback on err and preserves error", () => {
  let called = false;
  const res = flatMapResult(err("early-stop"), () => {
    called = true;
    return ok("never");
  });
  assert.equal(called, false);
  assert.deepEqual(res, { ok: false, error: "early-stop" });

  const mapped = mapResult(ok(0), (n: number) => n + 1);
  assert.deepEqual(mapped, { ok: true, value: 1 });
});
