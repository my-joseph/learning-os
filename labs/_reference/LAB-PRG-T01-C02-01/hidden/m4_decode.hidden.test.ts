import assert from "node:assert/strict";
import test from "node:test";
const { decodeApiPayload, formatDecodeError, numberSchema, objectSchema, stringSchema } = await import(
  `${process.env.LAB_SRC_DIR || "../src"}/index.ts`
);

test("M4 hidden: decodeApiPayload rejects JSON primitives and missing required fields", () => {
  const userSchema = objectSchema({
    id: numberSchema(),
    email: stringSchema(),
  });

  const nullPayload = decodeApiPayload("null", userSchema);
  assert.equal(nullPayload.ok, false);
  assert.equal(nullPayload.error.kind, "validation-failed");

  const wrongType = decodeApiPayload('{"id":1,"email":false}', userSchema);
  assert.equal(wrongType.ok, false);
  assert.equal(wrongType.error.kind, "validation-failed");
  assert.match(formatDecodeError(wrongType.error), /email:/);
});
