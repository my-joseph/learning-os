import { test } from "vitest";
import assert from "node:assert/strict";
import React from "react";
import { act, render, screen } from "@testing-library/react";

const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);
const { useStore } = await import(`${srcDir}/use_store.tsx`);

test("Milestone 4: independent views follow their selected values", () => {
  const store = createMiniStore({ saved: 1, activeFilter: "all" });
  let filterRenders = 0;
  function FilterLabel() {
    const filter = useStore(store, (state) => state.activeFilter);
    filterRenders += 1;
    return <output aria-label="Active filter">{filter}</output>;
  }
  function SavedCount() {
    const saved = useStore(store, (state) => state.saved);
    return <output aria-label="Saved count">{saved}</output>;
  }
  render(<><FilterLabel /><SavedCount /></>);
  const initialFilterRenders = filterRenders;
  act(() => { store.setState({ saved: 4 }); });
  assert.equal(screen.getByLabelText("Saved count").textContent, "4");
  assert.equal(screen.getByLabelText("Active filter").textContent, "all");
  assert.equal(filterRenders, initialFilterRenders);
});
