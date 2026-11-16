import test from "node:test";
import assert from "node:assert/strict";

const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);

test("Milestone 2: immutable updates and selectors", () => {
  const initial = { saved: 2, selectedId: "note-7" };
  const store = createMiniStore(initial);
  const update = { saved: 4 };
  store.setState(update);
  const snapshot = store.getState();

  assert.deepEqual(initial, { saved: 2, selectedId: "note-7" });
  assert.notEqual(snapshot, initial);
  assert.equal(snapshot.saved, 4);
  assert.equal(snapshot.selectedId, "note-7");

  store.setState((current) => ({ saved: current.saved + 1 }));
  assert.equal(store.getState().saved, 5);
});
