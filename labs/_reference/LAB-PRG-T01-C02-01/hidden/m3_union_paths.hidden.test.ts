import assert from "node:assert/strict";
import test from "node:test";
const { arraySchema, literalSchema, numberSchema, objectSchema, optionalSchema, stringSchema, unionSchema } =
  await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("M3 hidden: nested array inside object preserves full path on failure", () => {
  const orderSchema = objectSchema({
    items: arraySchema(
      objectSchema({
        qty: numberSchema(),
        tag: optionalSchema(stringSchema()),
      }),
    ),
  });

  const fail = orderSchema.parse({ items: [{ qty: 1 }, { qty: "two", tag: 5 }] });
  assert.equal(fail.ok, false);
  assert.deepEqual(
    fail.error.issues.map((i: { path: string }) => i.path),
    ["items[1].qty", "items[1].tag"],
  );
});

test("M3 hidden: unionSchema reports issues from every branch when all fail", () => {
  const u = unionSchema(
    objectSchema({ kind: literalSchema("a"), count: numberSchema() }),
    objectSchema({ kind: literalSchema("b"), label: stringSchema() }),
  );
  const fail = u.parse({ kind: "c", count: "bad", label: 9 });
  assert.equal(fail.ok, false);
  const paths = fail.error.issues.map((i: { path: string }) => i.path);
  assert.equal(paths.includes("count"), true);
  assert.equal(paths.includes("label"), true);
});
