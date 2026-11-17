import assert from "node:assert/strict";
import test from "node:test";
const { createDoublyLinkedList } = await import(`${process.env.LAB_SRC_DIR || "../src"}/index.ts`);

test("DoublyLinkedList keeps links encapsulated, handles head/tail removal, reuse after empty, and isolates instances", () => {
  const listA = createDoublyLinkedList<string>();
  const listB = createDoublyLinkedList<string>();

  const h1 = listA.pushFront("a");
  const h2 = listA.pushFront("b");
  const h3 = listA.pushFront("c");
  const hB = listB.pushFront("only-b");

  assert.deepEqual(Object.keys(h1).sort(), ["value"]);
  assert.equal("prev" in h1, false);
  assert.equal("next" in h2, false);
  assert.deepEqual(listA.toArray(), ["c", "b", "a"]);

  listA.moveToFront(h1);
  assert.deepEqual(listA.toArray(), ["a", "c", "b"]);

  // Removing tail and head explicitly, then ignoring detached handles
  assert.equal(listA.remove(h2), true);
  assert.equal(listA.remove(h2), false);
  assert.equal(listA.remove(h1), true);
  assert.equal(listA.remove(h1), false);
  assert.deepEqual(listA.toArray(), ["c"]);
  assert.equal(listA.remove(h3), true);
  assert.equal(listA.size(), 0);
  assert.equal(listA.popBack(), undefined);

  // Cross-instance handle rejection and reuse after becoming empty
  assert.equal(listA.remove(hB), false);
  assert.deepEqual(listB.toArray(), ["only-b"]);

  const h4 = listA.pushFront("reused-1");
  const h5 = listA.pushFront("reused-2");
  listA.moveToFront(h4);
  assert.deepEqual(listA.toArray(), ["reused-1", "reused-2"]);
  assert.equal(listA.popBack(), "reused-2");
  assert.equal(listA.remove(h5), false);
  assert.equal(listA.popBack(), "reused-1");
  assert.equal(listA.size(), 0);
});
