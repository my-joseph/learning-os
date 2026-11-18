import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ConfirmDialog } from "../src/components/ui/ConfirmDialog";
import { formatSyncToast } from "../src/hooks/useProgressSync";
import {
  TOAST_DURATION_MS,
  dismissToast,
  enqueueToast,
  getToastDurationMs,
  isInProgressToast,
  type ToastItem,
} from "../src/lib/toast";

// 1. Pure toast timing rules
assert.equal(TOAST_DURATION_MS.pass, 4000);
assert.equal(TOAST_DURATION_MS.warn, 6000);
assert.equal(TOAST_DURATION_MS.fail, 8000);

assert.equal(getToastDurationMs({ text: "Reset DRL-MTH-01 to initial state.", type: "pass" }), 4000);
assert.equal(getToastDurationMs({ text: "Saved locally, Notion unavailable", type: "warn" }), 6000);
assert.equal(getToastDurationMs({ text: "Notion Sync error: timeout", type: "fail" }), 8000);

assert.equal(
  getToastDurationMs({ text: "Syncing DRL-MTH-01 (4/5) to Notion...", type: "warn" }),
  null,
  "in-progress messages ending with '...' must stay until replaced"
);
assert.equal(
  getToastDurationMs({ text: "Generating 5 questions...  ", type: "pass" }),
  null
);
assert.equal(isInProgressToast({ text: "Loading...", type: "warn" }), true);
assert.equal(isInProgressToast({ text: "Loaded.", type: "pass" }), false);

// 2. Pure toast queue stacking & in-progress replacement
let queue: ToastItem[] = [];
queue = enqueueToast(queue, { text: "Syncing to Notion...", type: "warn" }, "t1");
assert.equal(queue.length, 1);

// Arriving completion toast replaces the in-progress toast
queue = enqueueToast(queue, { text: "Synced!", type: "pass" }, "t2");
assert.deepEqual(
  queue.map((t) => t.id),
  ["t2"]
);

// Additional completed/error toasts stack rather than overwriting prior non-progress toasts
queue = enqueueToast(queue, { text: "Check failed", type: "fail" }, "t3");
assert.deepEqual(
  queue.map((t) => t.id),
  ["t2", "t3"]
);

queue = dismissToast(queue, "t2");
assert.deepEqual(
  queue.map((t) => t.id),
  ["t3"]
);

// 3. ConfirmDialog SSR markup & accessibility attributes
const closedHtml = renderToStaticMarkup(
  <ConfirmDialog
    open={false}
    title="Reset all questions?"
    description="Reset all questions in DRL-01 to start over."
    onConfirm={() => {}}
    onCancel={() => {}}
  />
);
assert.equal(closedHtml, "");

const openHtml = renderToStaticMarkup(
  <ConfirmDialog
    open={true}
    title="Reset all questions?"
    description="Reset all questions in DRL-01 to start over."
    confirmLabel="Reset all"
    cancelLabel="Cancel"
    onConfirm={() => {}}
    onCancel={() => {}}
  />
);
assert.match(openHtml, /role="alertdialog"/);
assert.match(openHtml, /aria-modal="true"/);
assert.match(openHtml, /aria-labelledby="/);
assert.match(openHtml, /aria-describedby="/);
assert.match(openHtml, />Cancel<\/button>/);
assert.match(openHtml, /bg-rose-600[^>]*>Reset all<\/button>/);

// 4. Source invariants: no window.confirm / window.alert anywhere in src/, toast styling, sticky aside
function walkTsFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (statSync(full).isDirectory()) {
      out.push(...walkTsFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

for (const file of walkTsFiles("src")) {
  const src = readFileSync(file, "utf8");
  assert.doesNotMatch(
    src,
    /\bwindow\.(confirm|alert)\b/,
    `${file} must not use window.confirm or window.alert`
  );
}

const toastStackSrc = readFileSync("src/components/ui/ToastStack.tsx", "utf8");
assert.doesNotMatch(
  toastStackSrc,
  /border-l-/,
  "toasts must not have left accent borders"
);
assert.match(toastStackSrc, /role=\{isFail \? "alert" : "status"\}/);
assert.match(toastStackSrc, /aria-live=/);
assert.match(toastStackSrc, /sm:right-4/);
assert.match(toastStackSrc, /left-2 right-2/);

const studioShellSrc = readFileSync("src/components/shell/StudioShell.tsx", "utf8");
assert.match(studioShellSrc, /lg:sticky/);
assert.match(studioShellSrc, /lg:overflow-y-auto/);

// 5. Dry-run and pilot sync toast must never claim "Synced"
const dryRunToast = formatSyncToast({ ok: true, dryRun: true }, "DRL-MTH-01", "MTH-T01-C04", 4, 5, 80);
assert.equal(dryRunToast.type, "warn");
assert.match(dryRunToast.text, /Dry run — nothing written to Notion/);
assert.doesNotMatch(dryRunToast.text, /\bSynced\b/);

const pilotToast = formatSyncToast({ ok: true, pilotSkipped: true }, "DRL-MTH-01", "MTH-T01-C04", 4, 5, 80);
assert.equal(pilotToast.type, "warn");
assert.match(pilotToast.text, /Dry run — nothing written to Notion/);
assert.doesNotMatch(pilotToast.text, /\bSynced\b/);

const liveToast = formatSyncToast({ ok: true }, "Fractions", "MTH-T01-C04", 4, 5, 80);
assert.equal(liveToast.type, "pass");
assert.match(liveToast.text, /^Synced Fractions/);
assert.doesNotMatch(liveToast.text, /DRL-/);

console.log("toast and dialog tests passed");
