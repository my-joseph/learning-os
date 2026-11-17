import assert from "node:assert/strict";
import test from "node:test";
const { arraySchema, literalSchema, numberSchema, objectSchema, optionalSchema, stringSchema, unionSchema } =
  await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("arraySchema and optionalSchema preserve indexed paths and undefined", () => {
  const listSchema = arraySchema(
    objectSchema({
      sku: stringSchema(),
      note: optionalSchema(stringSchema()),
    }),
  );

  const valid = listSchema.parse([{ sku: "BOOK-1" }, { sku: "PEN-2", note: "gift" }]);
  assert.deepEqual(valid, {
    ok: true,
    value: [
      { sku: "BOOK-1", note: undefined },
      { sku: "PEN-2", note: "gift" },
    ],
  });

  const invalid = listSchema.parse([{ sku: "BOOK-1" }, { sku: 99 }]);
  assert.equal(invalid.ok, false);
  assert.equal(invalid.error.issues[0].path, "[1].sku");
});

test("unionSchema parses matching variants and surfaces all branch failures", () => {
  const eventSchema = unionSchema(
    objectSchema({ kind: literalSchema("created"), id: stringSchema() }),
    objectSchema({ kind: literalSchema("deleted"), code: numberSchema() }),
  );

  const okRes = eventSchema.parse({ kind: "deleted", code: 410 });
  assert.deepEqual(okRes, { ok: true, value: { kind: "deleted", code: 410 } });

  const failRes = eventSchema.parse({ kind: "unknown", id: 1, code: "bad" });
  assert.equal(failRes.ok, false);
  assert.equal(failRes.error.issues.length >= 2, true);
});
