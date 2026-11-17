import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FormattedText } from "../src/components/FormattedText";
import {
  getPrgScore,
  getReviewRequest,
  hasCheckpointHint,
  isContextSlug,
  resolveTheme,
  THEME_INIT_SCRIPT,
} from "../src/lib/studioRules";
import type { ReviewRecord, TestRunReport } from "../src/types/drill";

const report: TestRunReport = {
  allPassed: true,
  score: 0.25,
  passedCount: 1,
  totalCount: 4,
  visibleResults: [],
  hiddenPassed: 0,
  hiddenTotal: 1,
  executionTimeMs: 1,
};

const review = (verdict: "pass" | "revise"): ReviewRecord => ({
  at: "2026-11-17T00:00:00Z",
  attempt: 1,
  codeHash: "sha256:test",
  code: "",
  tests: { passed: 1, total: 1, failed: [] },
  lint: [],
  typecheck: [],
  findings: [],
  verdict,
  explain: null,
});

assert.match(
  renderToStaticMarkup(<FormattedText text="Solution 1: $-\\sqrt{7}$" />),
  /katex/,
  "answer check labels must render TeX through FormattedText"
);
assert.equal(isContextSlug("phasor_gain_stage_check"), true);
assert.equal(isContextSlug("A phasor gain stage"), false);
assert.equal(getPrgScore(report, undefined), null, "tests alone must not mark PRG correct");
assert.equal(getPrgScore(report, [review("pass")]), 1);
assert.equal(getPrgScore(report, [review("pass"), review("revise")]), null);
assert.equal(getPrgScore({ ...report, allPassed: false }, [review("pass")]), 0);
assert.equal(getReviewRequest("DRL-PRG-T01-C01-U01-01", "Q01"), "ตรวจโค้ด DRL-PRG-T01-C01-U01-01 Q01");
assert.equal(hasCheckpointHint(undefined), false);
assert.equal(hasCheckpointHint("  \n "), false);
assert.equal(hasCheckpointHint("Inspect the input boundary."), true);
assert.equal(resolveTheme(null, false), "light");
assert.equal(resolveTheme(null, true), "dark");
assert.equal(resolveTheme("light", true), "light", "saved preference must override system preference");
assert.match(THEME_INIT_SCRIPT, /matchMedia/);

const card = readFileSync("src/components/CodeProblemCard.tsx", "utf8");
const mathCard = readFileSync("src/components/MathProblemCard.tsx", "utf8");
const pagination = readFileSync("src/components/QuizPaginationBar.tsx", "utf8");
const studioShell = readFileSync("src/components/shell/StudioShell.tsx", "utf8");
const studioHeader = readFileSync("src/components/shell/StudioHeader.tsx", "utf8");
const workspaceRoute = readFileSync("src/app/api/workspace/route.ts", "utf8");
const runTestsRoute = readFileSync("src/app/api/run-tests/route.ts", "utf8");
assert.match(card, /hasCheckpointHint\(problem\.checkpointHint\)\s*&&\s*<button/);
assert.match(card, /FormattedText text=\{c\.label\}/);
assert.match(card, /aria-label=\{`Answer for question \$\{problem\.id\}`\}/);
assert.match(card, /Tests passed — ask for review:/);
assert.match(card, /method: "POST"[\s\S]*?JSON\.stringify\(\{ drillId \}\)/);
assert.match(card, /workspace file from disk/);
assert.match(mathCard, /FormattedText text=\{c\.label\}/);
assert.match(mathCard, /aria-label=\{`Answer for question \$\{problem\.id\}`\}/);
assert.match(mathCard, /hasCheckpointHint\(problem\.checkpointHint\)\s*&&\s*<button/);
assert.match(pagination, /bg-emerald-700/);
assert.match(pagination, /overflow-x-auto/);
assert.match(studioShell, /<h1 className="sr-only"/);
assert.match(studioHeader, /flex-col sm:flex-row sm:items-center/);
assert.match(workspaceRoute, /materializeWorkspace\(drillId, rootDir\)/);
assert.match(runTestsRoute, /userCode = fs\.readFileSync\(fullPath, "utf-8"\)/);

console.log("studio rules tests passed");
