import assert from "node:assert/strict";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import React, { act, useState } from "react";

test("Search opens via keyboard, filters fuzzy matches, and Enter navigates", async (t) => {
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
  const copies: string[] = [];
  const resets: string[] = [];
  const deletions: string[] = [];
  Object.defineProperty(window.navigator, "clipboard", {
    value: { writeText: async (id: string) => { copies.push(id); } },
  });

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
            onResetDrill={(id) => resets.push(id)}
            onDeleteDrill={(id) => deletions.push(id)}
          />
        </MotionConfig>
      </LazyMotion>
    );
  }

  const root = createRoot(window.document.getElementById("root")!);
  const press = async (target: EventTarget, key: string, options: KeyboardEventInit = {}) => {
    const event = new window.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...options });
    await act(async () => {
      target.dispatchEvent(event);
    });
    return event.defaultPrevented;
  };
  const activeType = () => window.document.querySelector("button[aria-pressed=true]")?.textContent;

  try {
    await act(async () => root.render(<Harness />));
    await press(window, "k", { ctrlKey: true });
    let input = window.document.querySelector<HTMLInputElement>("[role=combobox]")!;
    assert.equal(window.document.activeElement, input);
    const list = window.document.querySelector("[role=listbox]")!;
    assert.match(list.textContent ?? "", /Needs attention.*Array Utilities.*Recents.*Array Utilities Lab.*Actions.*Daily review/);

    await t.test("Search dialog is anchored to the top on phones and desktop", () => {
      const position = input.closest("[role=dialog]")?.parentElement?.classList;
      assert.ok(position?.contains("items-start"));
      assert.ok(position.contains("pt-[max(1rem,env(safe-area-inset-top))]"));
      assert.ok(position.contains("lg:pt-[max(12dvh,env(safe-area-inset-top))]"));
      assert.equal(position.contains("items-center"), false);
    });

    await t.test("Type chips gate hover on device capability and keep keyboard focus visible", async () => {
      const chips = window.document.querySelectorAll<HTMLButtonElement>("[aria-label='Result type'] button");
      assert.equal(chips.length, 4);
      for (const chip of chips) {
        const hoverClasses = [...chip.classList].filter((name) => name.split(":").includes("hover"));
        assert.deepEqual(hoverClasses, [
          "[@media(hover:hover)]:hover:bg-surface-hover",
        ]);
        assert.ok(chip.classList.contains("focus-visible:ring-2"));
        assert.equal([...chip.classList].some((name) => name.split(":").includes("focus")), false);
      }
      const pressedTypes = () => [...chips].filter((chip) => chip.getAttribute("aria-pressed") === "true")
        .map((chip) => chip.textContent);
      assert.deepEqual(pressedTypes(), ["All"]);
      await act(async () => chips[2].click());
      assert.deepEqual(pressedTypes(), ["Labs"]);
      assert.equal(window.document.activeElement, input);
      await act(async () => chips[0].click());
    });

    await t.test("Keyboard help starts at sm and the close button remains usable", async () => {
      const dialog = input.closest("[role=dialog]")!;
      const footer = [...dialog.querySelectorAll("kbd")].find((key) => key.textContent === "Esc")?.parentElement?.parentElement;
      assert.ok(footer?.classList.contains("hidden"));
      assert.ok(footer.classList.contains("sm:flex"));

      const close = dialog.querySelector<HTMLButtonElement>("button[aria-label='Close dialog']")!;
      await act(async () => close.click());
      assert.equal(window.document.querySelector("[role=dialog]"), null);
      await press(window, "k", { ctrlKey: true });
      input = window.document.querySelector<HTMLInputElement>("[role=combobox]")!;
    });

    await t.test("Only drill results offer Actions, and Escape dismisses the menu first", async () => {
      const buttons = window.document.querySelectorAll<HTMLButtonElement>("[role=listbox] button");
      assert.equal(buttons.length, 1);
      const trigger = buttons[0];
      assert.equal(trigger.getAttribute("aria-label"), `Actions for ${drillId}`);
      assert.equal(trigger.tabIndex, 0);
      assert.ok(!trigger.closest("[role=option]"));

      await press(input, "ArrowDown");
      assert.equal(trigger.tabIndex, -1);
      await press(input, "ArrowUp");
      assert.equal(trigger.tabIndex, 0);
      await act(async () => trigger.focus());
      assert.equal(await press(trigger, "Enter"), false);
      await act(async () => trigger.click());
      const menu = window.document.querySelector("[role=menu]")!;
      const items = [...menu.querySelectorAll<HTMLButtonElement>("[role=menuitem]")];
      assert.deepEqual(items.map((item) => item.textContent), ["Copy ID", "Reset", "Delete"]);
      await act(async () => items[0].click());
      assert.deepEqual(copies, [drillId]);
      assert.deepEqual(navigations, []);
      await press(items[0], "Escape");
      assert.ok(!window.document.querySelector("[role=menu]"));
      assert.ok(window.document.querySelector("[role=dialog]"));
      await press(trigger, "Escape");
      assert.ok(!window.document.querySelector("[role=dialog]"));
    });

    await t.test("Reset and Delete close Search and pass the drill to the shared confirmation handlers", async () => {
      for (const action of ["Reset", "Delete"]) {
        await press(window, "k", { ctrlKey: true });
        const trigger = window.document.querySelector<HTMLButtonElement>(`button[aria-label="Actions for ${drillId}"]`)!;
        await act(async () => trigger.click());
        const item = [...window.document.querySelectorAll<HTMLButtonElement>("[role=menuitem]")]
          .find((button) => button.textContent === action)!;
        await act(async () => item.click());
        assert.ok(!window.document.querySelector("[role=dialog]"));
        assert.ok(!window.document.querySelector("[role=menu]"));
      }
      assert.deepEqual(resets, [drillId]);
      assert.deepEqual(deletions, [drillId]);
      assert.deepEqual(navigations, []);
      await press(window, "k", { ctrlKey: true });
      input = window.document.querySelector<HTMLInputElement>("[role=combobox]")!;
    });

    await t.test("Horizontal arrows cycle types when the input is empty", async () => {
      assert.equal(await press(input, "ArrowLeft"), true);
      assert.equal(activeType(), "Units");
      const unitList = window.document.querySelector("[role=listbox]")!;
      assert.equal(unitList.querySelectorAll("[role=option]").length, 1);
      assert.equal(unitList.querySelectorAll("button").length, 0);
      assert.equal(await press(input, "ArrowRight"), true);
      assert.equal(activeType(), "All");
      await press(input, "ArrowRight");
      await press(input, "ArrowRight");
      assert.equal(activeType(), "Labs");
    });

    await act(async () => {
      const setValue = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")!.set!;
      setValue.call(input, "arry utl lab");
      input.dispatchEvent(new window.Event("input", { bubbles: true }));
    });

    await t.test("A nonempty query keeps native editing until the matching caret edge", async () => {
      const end = input.value.length;
      input.setSelectionRange(2, 2);
      assert.equal(await press(input, "ArrowLeft"), false);
      assert.equal(await press(input, "ArrowRight"), false);
      input.setSelectionRange(0, end);
      assert.equal(await press(input, "ArrowLeft"), false);
      assert.equal(await press(input, "ArrowRight"), false);
      assert.equal(activeType(), "Labs");

      input.setSelectionRange(0, 0);
      assert.equal(await press(input, "ArrowRight"), false);
      assert.equal(await press(input, "ArrowLeft", { shiftKey: true }), false);
      assert.equal(await press(input, "ArrowLeft"), true);
      assert.equal(activeType(), "Drills");

      input.setSelectionRange(end, end);
      assert.equal(await press(input, "ArrowLeft"), false);
      assert.equal(await press(input, "ArrowRight"), true);
      assert.equal(activeType(), "Labs");
    });

    const filteredList = window.document.querySelector("[role=listbox]")!;
    assert.equal(filteredList.querySelectorAll("[role=option]").length, 1);
    assert.match(filteredList.querySelector("[aria-selected=true]")?.textContent ?? "", /Array Utilities Lab/);

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
