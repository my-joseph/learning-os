import assert from "node:assert/strict";
import test from "node:test";
const { err, flatMapResult, mapResult, ok } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("ok and err create discriminated Result variants", () => {
  const success = ok(42);
  const failure = err({ reason: "missing-token" });
  assert.deepEqual(success, { ok: true, value: 42 });
  assert.deepEqual(failure, { ok: false, error: { reason: "missing-token" } });
});

test("mapResult and flatMapResult transform ok values and short-circuit err", () => {
  const doubled = mapResult(ok(21), (n: number) => n * 2);
  assert.deepEqual(doubled, { ok: true, value: 42 });

  const passedErr = mapResult(err("bad-input"), (n: number) => n * 2);
  assert.deepEqual(passedErr, { ok: false, error: "bad-input" });

  const chained = flatMapResult(ok("10"), (raw: string) => {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? ok(parsed) : err("nan");
  });
  assert.deepEqual(chained, { ok: true, value: 10 });
});
