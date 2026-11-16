import test from "node:test";
import assert from "node:assert/strict";
const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);
test("Milestone 2: partial updates remain caller-owned", () => {
  const store = createMiniStore({ saved: 1, activeFilter: "all" });
  const update = { saved: 2 };
  store.setState(update);
  assert.deepEqual(update, { saved: 2 });
});
