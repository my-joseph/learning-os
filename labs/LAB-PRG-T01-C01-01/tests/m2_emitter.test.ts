import assert from "node:assert/strict";
import test from "node:test";
const { TinyEventEmitter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

type NotificationEvents = { queued: { id: string }; delivered: { id: string; at: number } };

test("emit delivers the payload in listener registration order", () => {
  const emitter = new TinyEventEmitter<NotificationEvents>();
  const received: string[] = [];
  emitter.on("queued", ({ id }) => received.push(`first:${id}`));
  emitter.on("queued", ({ id }) => received.push(`second:${id}`));
  emitter.emit("queued", { id: "job-2" });
  assert.deepEqual(received, ["first:job-2", "second:job-2"]);
});

test("unsubscribe prevents future deliveries and repeated removal is safe", () => {
  const emitter = new TinyEventEmitter<NotificationEvents>();
  let deliveries = 0;
  const listener = () => { deliveries += 1; };
  const release = emitter.on("queued", listener);
  emitter.emit("queued", { id: "job-5" });
  release();
  release();
  emitter.off("queued", listener);
  emitter.emit("queued", { id: "job-6" });
  assert.equal(deliveries, 1);
});

test("a listener added during delivery begins on the next emission", () => {
  const emitter = new TinyEventEmitter<NotificationEvents>();
  const received: string[] = [];
  emitter.on("queued", ({ id }) => {
    received.push(`original:${id}`);
    if (id === "job-1") emitter.on("queued", ({ id: nextId }) => received.push(`late:${nextId}`));
  });
  emitter.emit("queued", { id: "job-1" });
  assert.deepEqual(received, ["original:job-1"]);
  emitter.emit("queued", { id: "job-2" });
  assert.deepEqual(received, ["original:job-1", "original:job-2", "late:job-2"]);
});
