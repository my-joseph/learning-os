import { test } from "vitest";
import assert from "node:assert/strict";
import React from "react";
import { act, render, screen } from "@testing-library/react";

const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);
const { useStore } = await import(`${srcDir}/use_store.tsx`);

test("Milestone 3: React subscription hook", () => {
  const store = createMiniStore({ saved: 1 });
  function SavedCount() {
    const saved = useStore(store, (state) => state.saved);
    return <output aria-label="Saved count">{saved}</output>;
  }
  render(<SavedCount />);
  assert.equal(screen.getByLabelText("Saved count").textContent, "1");
  act(() => { store.setState({ saved: 3 }); });
  assert.equal(screen.getByLabelText("Saved count").textContent, "3");
});
