import assert from "node:assert/strict";
import test from "node:test";
const { createDoublyLinkedList } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("doublyLinkedList supports pushFront, moveToFront, remove, and popBack", () => {
  const list = createDoublyLinkedList<string>();
  const h1 = list.pushFront("first");
  const h2 = list.pushFront("second");
  const h3 = list.pushFront("third");
  assert.deepEqual(list.toArray(), ["third", "second", "first"]);
  assert.equal(list.size(), 3);

  list.moveToFront(h1);
  assert.deepEqual(list.toArray(), ["first", "third", "second"]);

  assert.equal(list.remove(h3), true);
  assert.equal(list.remove(h3), false);
  assert.deepEqual(list.toArray(), ["first", "second"]);

  assert.equal(list.popBack(), "second");
  assert.equal(list.popBack(), "first");
  assert.equal(list.popBack(), undefined);
  assert.equal(list.size(), 0);
  assert.equal(h2.value, "second");
});
