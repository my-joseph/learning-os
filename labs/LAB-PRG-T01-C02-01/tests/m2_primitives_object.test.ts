import assert from "node:assert/strict";
import test from "node:test";
const { booleanSchema, literalSchema, numberSchema, objectSchema, stringSchema } = await import(
  `${process.env.LAB_SRC_DIR || "../src"}/index.ts`
);

test("primitive schemas preserve valid falsy values and reject non-finite numbers", () => {
  assert.deepEqual(stringSchema().parse(""), { ok: true, value: "" });
  assert.deepEqual(numberSchema().parse(0), { ok: true, value: 0 });
  assert.deepEqual(booleanSchema().parse(false), { ok: true, value: false });
  assert.equal(numberSchema().parse(Number.NaN).ok, false);
  assert.equal(numberSchema().parse(Number.POSITIVE_INFINITY).ok, false);
  assert.deepEqual(literalSchema("active").parse("active"), { ok: true, value: "active" });
  assert.equal(literalSchema("active").parse("paused").ok, false);
});

test("objectSchema validates nested own properties and reports field paths", () => {
  const userSchema = objectSchema({
    id: numberSchema(),
    name: stringSchema(),
    flags: objectSchema({
      verified: booleanSchema(),
    }),
  });

  const valid = userSchema.parse({ id: 0, name: "", flags: { verified: false } });
  assert.deepEqual(valid, { ok: true, value: { id: 0, name: "", flags: { verified: false } } });

  const invalid = userSchema.parse({ id: "zero", name: "Ada", flags: { verified: "yes" } });
  assert.equal(invalid.ok, false);
  assert.deepEqual(
    invalid.error.issues.map((i: { path: string }) => i.path),
    ["id", "flags.verified"],
  );
});
