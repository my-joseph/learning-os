import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { JSDOM } from "jsdom";
import postcss from "postcss";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import tailwindcss from "tailwindcss";
import { ListRow } from "../src/components/ui/ListRow";
import { IconButton } from "../src/components/ui/shadcn/Button";
import { Dialog, DialogOverlay } from "../src/components/ui/shadcn/Dialog";
import { RowMenuItem } from "../src/components/ui/shadcn/Popover";
import { SegmentedChips } from "../src/components/ui/shadcn/Tabs";
import config from "../tailwind.config";

const sizes = { xs: "28px", sm: "32px", md: "36px" } as const;
const options = [{ value: "all", label: "All" }, { value: "drill", label: "Drills" }] as const;

test("Shared search controls use size and tone tokens and keep the same box styles across states", async () => {
  const html = renderToStaticMarkup(
    <>
      {(Object.keys(sizes) as (keyof typeof sizes)[]).map((size) => (
        <section key={size} data-size={size}>
          {[
            { selected: false },
            { selected: true },
            { selected: false, disabled: true },
            { selected: false, loading: true },
          ].map(({ selected, disabled, loading }, index) => (
            <div key={index} data-state={index}>
              <IconButton aria-label="Actions" size={size} tone="primary" selected={selected} disabled={disabled} loading={loading}>
                <svg aria-hidden="true" />
              </IconButton>
              <ListRow size={size} tone="secondary" selected={selected} disabled={disabled} loading={loading} label="Search" trailing={<kbd>Ctrl K</kbd>} />
              <RowMenuItem size={size} tone="destructive" selected={selected} disabled={disabled} loading={loading}>Delete</RowMenuItem>
              <SegmentedChips
                label="Result type"
                options={options}
                value={selected ? "drill" : "all"}
                onValueChange={() => {}}
                size={size}
                disabled={disabled}
                loading={loading}
              />
            </div>
          ))}
        </section>
      ))}
    </>
  );
  const stylesheet = new URL("../src/app/globals.css", import.meta.url);
  const { css } = await postcss([tailwindcss({ ...config, content: [{ raw: html }] })])
    .process(readFileSync(stylesheet, "utf8"), { from: stylesheet.pathname });
  const { window } = new JSDOM(`<!doctype html><html class="light"><head><style>${css}</style></head><body>${html}</body></html>`);

  const boxStyles = (button: HTMLButtonElement) => {
    const { boxSizing, width, height, minWidth, minHeight, padding, borderWidth, fontWeight, lineHeight } = window.getComputedStyle(button);
    return { boxSizing, width, height, minWidth, minHeight, padding, borderWidth, fontWeight, lineHeight };
  };

  try {
    for (const [size, height] of Object.entries(sizes)) {
      const states = Array.from(window.document.querySelectorAll(`[data-size="${size}"] [data-state]`));
      const [idle, selected, disabled, loading] = states.map((state) => Array.from(state.querySelectorAll("button")));
      const [icon, row, item, all, drills] = idle;
      assert.equal(boxStyles(icon).width, height);
      assert.equal(boxStyles(icon).height, height);
      assert.equal(boxStyles(row).minHeight, height);
      assert.equal(boxStyles(item).minHeight, height);
      assert.equal(boxStyles(all).height, height);
      assert.equal(boxStyles(drills).height, height);

      assert.ok(icon.classList.contains("bg-accent-primary"));
      assert.ok(row.classList.contains("text-foreground-secondary"));
      assert.ok(item.classList.contains("text-status-wrong"));
      assert.ok(all.classList.contains("text-foreground"));
      assert.ok(row.querySelector(".truncate"));
      assert.equal(row.querySelector("kbd")?.textContent, "Ctrl K");
      assert.equal(item.getAttribute("role"), "menuitem");

      assert.deepEqual(selected.map((button) => button.dataset.selected), ["true", "true", "true", "false", "true"]);
      assert.equal(all.getAttribute("aria-pressed"), "true");
      assert.equal(selected[4].getAttribute("aria-pressed"), "true");
      assert.ok(disabled.every((button) => button.disabled));
      assert.ok(loading.every((button) => button.disabled));
      assert.ok(loading.slice(0, 3).every((button) => button.getAttribute("aria-busy") === "true"));
      assert.equal(loading[3].parentElement?.getAttribute("aria-busy"), "true");
      for (const state of [selected, disabled, loading]) {
        assert.deepEqual(state.map(boxStyles), idle.map(boxStyles));
      }
    }
  } finally {
    window.close();
  }
});

test("Search opts into its scrim token without blur", () => {
  const html = renderToStaticMarkup(<Dialog open><DialogOverlay preset="search" /></Dialog>);
  assert.match(html, /\bbg-overlay-scrim-search\b/);
  assert.doesNotMatch(html, /backdrop-blur/);
});
