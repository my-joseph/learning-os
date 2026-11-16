import test from "node:test";
import assert from "node:assert/strict";
const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);
test("Milestone 1: separate stores do not cross-notify", () => {
  const first = createMiniStore({ saved: 1 });
  const second = createMiniStore({ saved: 2 });
  let firstUpdates = 0;
  first.subscribe(() => { firstUpdates += 1; });
  second.setState({ saved: 3 });
  assert.equal(firstUpdates, 0);
});
