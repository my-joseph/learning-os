import { test } from "vitest";
import assert from "node:assert/strict";
import React from "react";
import { act, render } from "@testing-library/react";
const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);
const { useStore } = await import(`${srcDir}/use_store.tsx`);
test("Milestone 4: an unchanged selection keeps its render count", () => {
  const store = createMiniStore({ saved: 1, activeFilter: "all" });
  let renders = 0;
  function FilterView() { const filter = useStore(store, (state) => state.activeFilter); renders += 1; return <output>{filter}</output>; }
  render(<FilterView />);
  const before = renders;
  act(() => { store.setState({ saved: 2 }); });
  assert.equal(renders, before);
});
