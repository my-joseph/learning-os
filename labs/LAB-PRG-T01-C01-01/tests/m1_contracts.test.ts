import assert from "node:assert/strict";
import test from "node:test";
const { TinyEventEmitter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

type NotificationEvents = {
  delivered: { messageId: string; recipientId: string };
  failed: { messageId: string; retryable: boolean };
};

test("event subscriptions expose a release function", () => {
  const emitter = new TinyEventEmitter<NotificationEvents>();
  const release = emitter.on("delivered", (payload) => assert.equal(typeof payload.messageId, "string"));
  assert.equal(typeof release, "function");
});

test("payload type remains tied to the selected event name", () => {
  const emitter = new TinyEventEmitter<NotificationEvents>();
  emitter.on("failed", (payload) => assert.equal(typeof payload.retryable, "boolean"));
  assert.doesNotThrow(() => emitter.emit("delivered", { messageId: "msg-7", recipientId: "user-4" }));
});
