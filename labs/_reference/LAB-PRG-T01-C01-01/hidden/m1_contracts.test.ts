import assert from "node:assert/strict";
import test from "node:test";
const { TinyEventEmitter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("distinct event keys keep distinct payloads at runtime", () => {
  type Events = { published: { revision: number }; revoked: { reason: string } };
  const emitter = new TinyEventEmitter<Events>();
  let publishedRevision = 0;
  let revokedReason = "";
  const release = emitter.on("published", ({ revision }) => { publishedRevision = revision; });
  emitter.on("revoked", ({ reason }) => { revokedReason = reason; });
  assert.equal(typeof release, "function");
  emitter.emit("published", { revision: 12 });
  emitter.emit("revoked", { reason: "policy" });
  assert.equal(publishedRevision, 12);
  assert.equal(revokedReason, "policy");
});
