import assert from "node:assert/strict";
import { test } from "node:test";
import { setTimeout } from "node:timers/promises";
import { JSDOM } from "jsdom";
import React, { act } from "react";
import type { DrillListItem } from "../src/types/drill";

test("sidebar hover renders the full title and ID only for a desktop pointer", async () => {
  const { window } = new JSDOM("<div id='root'></div>", {
    url: "http://localhost/",
    pretendToBeVisual: true,
  });
  Object.assign(globalThis, { window, IS_REACT_ACT_ENVIRONMENT: true });
  for (const key of [
    "document", "navigator", "HTMLElement", "Element", "Node", "NodeFilter",
    "MutationObserver", "Event", "CustomEvent", "getComputedStyle",
    "requestAnimationFrame", "cancelAnimationFrame",
  ] as const) {
    Object.defineProperty(globalThis, key, { configurable: true, value: window[key] });
  }
  window.HTMLElement.prototype.scrollIntoView = () => {};
  let desktopPointer = true;
  Object.defineProperty(window, "matchMedia", {
    value: (query: string) => ({ matches: query.includes("pointer: fine") && desktopPointer }),
  });

  const { createRoot } = await import("react-dom/client");
  const { DrillSwitcher } = await import("../src/components/shell/DrillSwitcher");
  const root = createRoot(window.document.getElementById("root")!);
  const title = "Arithmetic with fractions, proportional relationships, and mixed numbers";
  const drill: DrillListItem = {
    drillId: "DRL-MTH-T01-C04-U01-03",
    subject: "MATH",
    unitCode: "MTH-T01-C04-U01",
    unitTitle: title,
    createdAt: "2026-11-26",
    practiceStatus: "Ready",
    difficultyMode: "Mixed",
    questionCount: 3,
    answeredCount: 0,
    localFilePath: "",
  };
  const noop = () => {};
  const preview = () => window.document.querySelector("[data-tree-row-preview]");
  try {
    await act(async () => root.render(
      <DrillSwitcher
        mode="sidebar"
        isOpen
        onToggle={noop}
        onClose={noop}
        currentDrill={null}
        drills={[drill]}
        selectedDrillId={drill.drillId}
        onSelectDrill={noop}
      />
    ));
    const row = window.document.querySelector<HTMLElement>("[data-sidebar-leaf] > button")!;
    const pointer = (type: string, pointerType: string) =>
      row.dispatchEvent(new window.PointerEvent(type, { bubbles: true, pointerType }));

    assert.ok(row);
    assert.doesNotMatch(row.textContent ?? "", /DRL-MTH-/);
    assert.equal(preview(), null);
    await act(async () => {
      pointer("pointerover", "touch");
      await setTimeout(520);
    });
    assert.equal(preview(), null);
    desktopPointer = false;
    await act(async () => {
      pointer("pointerover", "mouse");
      await setTimeout(520);
    });
    assert.equal(preview(), null);

    desktopPointer = true;
    await act(async () => {
      pointer("pointerover", "mouse");
      await setTimeout(520);
    });
    const card = preview();
    assert.ok(card);
    assert.deepEqual(Array.from(card.children, (child) => child.textContent), [title, drill.drillId]);
    assert.ok(card.children[0].classList.contains("break-words"));
    assert.ok(card.children[1].classList.contains("font-normal"));
    assert.ok(card.children[1].classList.contains("font-mono"));
    assert.equal(window.document.activeElement, window.document.body);
  } finally {
    await act(async () => root.unmount());
    window.close();
  }
});
