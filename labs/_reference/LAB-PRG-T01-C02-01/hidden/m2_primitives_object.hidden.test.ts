import assert from "node:assert/strict";
import test from "node:test";
const { booleanSchema, numberSchema, objectSchema, stringSchema } = await import(
  `${process.env.LAB_SRC_DIR || "../src"}/index.ts`
);

test("M2 hidden: objectSchema rejects arrays, null, and inherited prototype properties", () => {
  const schema = objectSchema({ toString: stringSchema(), count: numberSchema(), active: booleanSchema() });
  assert.equal(schema.parse(null).ok, false);
  assert.equal(schema.parse(["a"]).ok, false);
  const protoCarrier = Object.create({ toString: "inherited", count: 1, active: true });
  const res = schema.parse(protoCarrier);
  assert.equal(res.ok, false);
  assert.deepEqual(
    res.error.issues.map((i: { path: string }) => i.path),
    ["toString", "count", "active"],
  );
});

test("M2 hidden: objectSchema preserves falsy own properties without mutating input", () => {
  const input = Object.freeze({ count: 0, label: "", enabled: false });
  const schema = objectSchema({ count: numberSchema(), label: stringSchema(), enabled: booleanSchema() });
  const parsed = schema.parse(input);
  assert.deepEqual(parsed, { ok: true, value: { count: 0, label: "", enabled: false } });
});
