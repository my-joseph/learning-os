import { test } from "vitest";
import assert from "node:assert/strict";
import React from "react";
import { render, screen } from "@testing-library/react";
const srcDir = process.env.LAB_SRC_DIR || "../src";
const { createMiniStore } = await import(`${srcDir}/mini_store.ts`);
const { useStore } = await import(`${srcDir}/use_store.tsx`);
test("Milestone 3: hook returns the selected value", () => {
  const store = createMiniStore({ saved: 3, activeFilter: "all" });
  function SavedCount() { return <output>{useStore(store, (state) => state.saved)}</output>; }
  render(<SavedCount />);
  assert.equal(screen.getByText("3").textContent, "3");
});
