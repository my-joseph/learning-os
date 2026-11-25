import assert from "node:assert/strict";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import React, { act, useState } from "react";

test("Search opens via keyboard, filters fuzzy matches, and Enter navigates", async () => {
  const { window } = new JSDOM("<div id='root'></div>", {
    url: "http://localhost/",
    pretendToBeVisual: true,
  });
  const globals = [
    "document", "navigator", "HTMLElement", "Element", "Node", "NodeFilter",
    "MutationObserver", "Event", "CustomEvent", "getComputedStyle",
    "requestAnimationFrame", "cancelAnimationFrame",
  ] as const;
  Object.assign(globalThis, { window });
  for (const key of globals) {
    Object.defineProperty(globalThis, key, {
      configurable: true,
      value: window[key],
    });
  }
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
  window.HTMLElement.prototype.scrollIntoView = () => {};
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

  const { createRoot } = await import("react-dom/client");
  const { MotionConfig, LazyMotion, domAnimation } = await import("motion/react");
  const { StudioSearchPalette, StudioSearchTrigger, useStudioSearchShortcut } =
    await import("../src/components/shell/StudioSearchPalette");
  const { buildSearchEntries } = await import("../src/lib/studioSearch");
  const { writeLastDrillId } = await import("../src/lib/lastDrillStorage");

  const drillId = "DRL-PRG-T01-C01-U02-01";
  const labId = "LAB-PRG-T01-C01-01";
  const unitCode = "PRG-T01-C01-U02";
  const entries = buildSearchEntries(
    [{
      drillId,
      unitCode,
      unitTitle: "Array Utilities",
      createdAt: "2026-11-25",
      questionCount: 3,
      difficultyMode: "Mixed",
      localFilePath: "",
    }],
    [{
      id: labId,
      labId,
      title: "Array Utilities Lab",
      unitCode: "PRG-T01-C01",
      chapterCode: "PRG-T01-C01",
      topicCode: "PRG-T01",
      unitsUsed: [],
      kind: "project",
      milestoneCount: 0,
      practiceStatus: "Ready",
      passedCount: 0,
      reviseCount: 0,
      score: 0,
      maxScore: 0,
      progress: {
        passedCount: 0,
        reviseCount: 0,
        notStartedCount: 0,
        totalCount: 0,
        practiceStatus: "Ready",
        score: 0,
        maxScore: 0,
        updatedAt: null,
        milestones: {},
      },
    }]
  );
  writeLastDrillId(labId, "code");
  const navigations: string[] = [];

  function Harness() {
    const [open, setOpen] = useState(false);
    const shortcut = useStudioSearchShortcut(() => setOpen(true));
    return (
      <LazyMotion features={domAnimation} strict>
        <MotionConfig reducedMotion="always">
          <StudioSearchTrigger shortcut={shortcut} onClick={() => setOpen(true)} />
          <StudioSearchPalette
            open={open}
            onClose={() => setOpen(false)}
            onCloseAutoFocus={(event) => event.preventDefault()}
            workspace="code"
            entries={entries}
            dueIds={[drillId]}
            loading={false}
            loadError={false}
            dueLoading={false}
            dueError={false}
            reviewHref="/review?scope=subject:PRG"
            switchHref={null}
            onNavigate={(href) => navigations.push(href)}
          />
        </MotionConfig>
      </LazyMotion>
    );
  }

  const root = createRoot(window.document.getElementById("root")!);
  const press = async (target: EventTarget, key: string, options: KeyboardEventInit = {}) => {
    await act(async () => {
      target.dispatchEvent(new window.KeyboardEvent("keydown", { key, bubbles: true, ...options }));
    });
  };

  try {
    await act(async () => root.render(<Harness />));
    await press(window, "k", { ctrlKey: true });
    let input = window.document.querySelector<HTMLInputElement>("[role=combobox]")!;
    assert.equal(window.document.activeElement, input);
    const list = window.document.querySelector("[role=listbox]")!;
    assert.match(list.textContent ?? "", /Needs attention.*Array Utilities.*Recents.*Array Utilities Lab.*Actions.*Daily review/);

    await press(input, "ArrowRight");
    await press(input, "ArrowRight");
    assert.equal(
      window.document.querySelector("button[aria-pressed=true]")?.textContent,
      "Labs"
    );
    await act(async () => {
      const setValue = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")!.set!;
      setValue.call(input, "arry utl lab");
      input.dispatchEvent(new window.Event("input", { bubbles: true }));
    });
    assert.equal(list.querySelectorAll("[role=option]").length, 1);
    assert.match(list.querySelector("[aria-selected=true]")?.textContent ?? "", /Array Utilities Lab/);

    await press(input, "Enter");
    assert.deepEqual(navigations, [`/code/lab/${labId}`]);
    assert.equal(window.document.querySelector("[role=dialog]"), null);

    await press(window, "k", { metaKey: true });
    input = window.document.querySelector<HTMLInputElement>("[role=combobox]")!;
    await press(input, "Escape");
    assert.equal(window.document.querySelector("[role=dialog]"), null);
  } finally {
    await act(async () => root.unmount());
    window.close();
  }
});
