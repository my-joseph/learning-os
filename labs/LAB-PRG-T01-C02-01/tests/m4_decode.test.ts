import assert from "node:assert/strict";
import test from "node:test";
const { decodeApiPayload, formatDecodeError, numberSchema, objectSchema, stringSchema } = await import(
  `${process.env.LAB_SRC_DIR || "../src"}/index.ts`
);

test("decodeApiPayload narrows JSON payloads and formats errors exhaustively", () => {
  const payloadSchema = objectSchema({
    status: numberSchema(),
    cursor: stringSchema(),
  });

  const valid = decodeApiPayload('{"status":200,"cursor":""}', payloadSchema);
  assert.deepEqual(valid, { ok: true, value: { status: 200, cursor: "" } });

  const badJson = decodeApiPayload("{not-json", payloadSchema);
  assert.equal(badJson.ok, false);
  assert.equal(badJson.error.kind, "invalid-json");
  assert.match(formatDecodeError(badJson.error), /Invalid JSON/);

  const badShape = decodeApiPayload('{"status":"200"}', payloadSchema);
  assert.equal(badShape.ok, false);
  assert.equal(badShape.error.kind, "validation-failed");
  assert.match(formatDecodeError(badShape.error), /status:/);
  assert.match(formatDecodeError(badShape.error), /cursor:/);
});
