import assert from "node:assert/strict";
import test from "node:test";
const { TinyEventEmitter } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("removing a listener during delivery does not corrupt the current listener pass", () => {
  type Events = { updated: { version: number } };
  const emitter = new TinyEventEmitter<Events>();
  const received: string[] = [];
  const later = () => received.push("later");
  emitter.on("updated", () => { received.push("first"); emitter.off("updated", later); });
  emitter.on("updated", later);
  emitter.emit("updated", { version: 3 });
  assert.deepEqual(received, ["first", "later"]);
  received.length = 0;
  emitter.emit("updated", { version: 4 });
  assert.deepEqual(received, ["first"]);
});

test("separate event names do not share listener registrations", () => {
  type Events = { created: { id: string }; removed: { id: string } };
  const emitter = new TinyEventEmitter<Events>();
  let count = 0;
  emitter.on("created", () => { count += 1; });
  emitter.emit("removed", { id: "record-8" });
  assert.equal(count, 0);
});

test("event subscribers belong to their emitter instance", () => {
  type Events = { published: { revision: number } };
  const firstEmitter = new TinyEventEmitter<Events>();
  const secondEmitter = new TinyEventEmitter<Events>();
  let firstCount = 0;
  let secondCount = 0;
  firstEmitter.on("published", () => { firstCount += 1; });
  secondEmitter.on("published", () => { secondCount += 1; });
  firstEmitter.emit("published", { revision: 1 });
  assert.equal(firstCount, 1);
  assert.equal(secondCount, 0);
});
