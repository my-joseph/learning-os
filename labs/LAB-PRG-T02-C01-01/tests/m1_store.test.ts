import test from "node:test";
import assert from "node:assert/strict";

const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);

test("Milestone 1: store state and listener contracts", async (t) => {
  await t.test("starts with the provided state and reports updates", () => {
    const store = createMiniStore({ saved: 2 });
    let notifications = 0;
    store.subscribe(() => { notifications += 1; });
    store.setState({ saved: 3 });
    assert.equal(store.getState().saved, 3);
    assert.equal(notifications, 1);
  });

  await t.test("releases a listener when its subscription ends", () => {
    const store = createMiniStore({ saved: 0 });
    let notifications = 0;
    const unsubscribe = store.subscribe(() => { notifications += 1; });
    unsubscribe();
    store.setState({ saved: 1 });
    assert.equal(notifications, 0);
  });
});
