import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FormattedText } from "../src/components/FormattedText";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { ReviewPanel } from "../src/components/shell/ReviewPanel";
import {
  getPrgScore,
  getReviewRequest,
  hasCheckpointHint,
  isContextSlug,
  resolveTheme,
  THEME_INIT_SCRIPT,
} from "../src/lib/studioRules";
import type { DrillDocument, Problem, ReviewRecord, TestRunReport } from "../src/types/drill";

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

const codeDashboard = readFileSync("src/components/code/CodeDashboard.tsx", "utf8");
const mathWorkspace = readFileSync("src/components/math/MathWorkspace.tsx", "utf8");
const pagination = readFileSync("src/components/QuizPaginationBar.tsx", "utf8");
const studioShell = readFileSync("src/components/shell/StudioShell.tsx", "utf8");
const studioHeader = readFileSync("src/components/shell/StudioHeader.tsx", "utf8");
const workspaceRoute = readFileSync("src/app/api/workspace/route.ts", "utf8");
const runTestsRoute = readFileSync("src/app/api/run-tests/route.ts", "utf8");
assert.match(codeDashboard, /hasCheckpointHint\(problem\.checkpointHint\)\s*&&\s*<button/);
assert.match(codeDashboard, /FormattedText text=\{c\.label\}/);
assert.match(codeDashboard, /aria-label=\{`Answer for question \$\{problem\.id\}`\}/);
assert.match(codeDashboard, /Copy review request/);
assert.match(codeDashboard, /Run checks/);
assert.match(codeDashboard, /Unlocks after review passes/);
assert.match(codeDashboard, /method: "POST"[\s\S]*?JSON\.stringify\(\{ drillId \}\)/);
assert.match(codeDashboard, /workspace file from disk/);
assert.match(mathWorkspace, /FormattedText text=\{c\.label\}/);
assert.match(mathWorkspace, /aria-label=\{`Answer for question \$\{problem\.id\}`\}/);
assert.match(mathWorkspace, /hasCheckpointHint\(problem\.checkpointHint\)\s*&&\s*<button/);
assert.match(mathWorkspace, /max-w-\[720px\]/);
assert.match(mathWorkspace, /border-rose-600/);
assert.match(pagination, /bg-emerald-700/);
assert.match(pagination, /overflow-x-auto/);
assert.match(studioShell, /<h1 className="sr-only"/);
assert.match(studioHeader, /hidden sm:inline-flex/);
assert.match(studioHeader, /MoreHorizontal/);
assert.match(workspaceRoute, /materializeWorkspace\(drillId, rootDir\)/);
assert.match(runTestsRoute, /userCode = fs\.readFileSync\(fullPath, "utf-8"\)/);

// Verify MathWorkspace hides self-score before an attempt and shows it after an attempt
const sampleMathProblem: Problem = {
  id: "Q01",
  templateKey: "tpl",
  level: 1,
  levelLabel: "Level 1",
  category: "Algebra",
  prompt: "Solve $2x = 10$.",
  answerSpec: { type: "number" },
  state: {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    lastCheck: null,
    attempts: [],
  },
};

const noop = () => {};
const beforeAttemptHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={sampleMathProblem}
    index={0}
    totalQuestions={5}
    drillTitle="Linear Equations"
    mistakeTags={[]}
    activeStep={null}
    onInputChange={noop}
    onCheckAnswer={noop}
    onToggleStepHighlight={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(beforeAttemptHtml, /<h1[^>]*>Linear Equations<\/h1>/);
assert.doesNotMatch(beforeAttemptHtml, /Self-score:/, "self-score must not appear before an attempt");

const afterAttemptHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={{
      ...sampleMathProblem,
      state: {
        ...sampleMathProblem.state,
        score: 0,
        lastCheck: {
          verdict: "incorrect",
          message: "Not quite — check your division.",
          components: [],
          diagnostics: [],
        },
        attempts: [{ input: "4", ts: "2026-11-17T00:00:00Z", verdict: "incorrect" }],
      },
    }}
    index={0}
    totalQuestions={5}
    drillTitle="Linear Equations"
    mistakeTags={[]}
    activeStep={null}
    onInputChange={noop}
    onCheckAnswer={noop}
    onToggleStepHighlight={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(afterAttemptHtml, /Self-score:/, "self-score must appear after an attempt");
assert.match(afterAttemptHtml, /border-rose-600/, "wrong feedback uses rose left border");

// Verify CodeDashboard renders layered status, visible test names only, primary action transitions, and locked reference
const sampleCodeProblem: Problem = {
  id: "Q01",
  templateKey: "prg-tpl",
  level: 1,
  levelLabel: "Level 1",
  category: "Core Skill",
  entryPoint: "clampBatteryPercent",
  prompt: "Implement `clampBatteryPercent(val)`.",
  workspaceFile: "drills/workspace/DRL-PRG-T00-C03-02/Q01_clampBatteryPercent.js",
  vscodeFolderUrl: "vscode://file/drills/workspace/DRL-PRG-T00-C03-02",
  cursorFolderUrl: "cursor://file/drills/workspace/DRL-PRG-T00-C03-02",
  visibleTests: [
    {
      id: "T1",
      name: "clamps above 100 to 100",
      testCode: "assert.strictEqual(clampBatteryPercent(150), 100);",
    },
  ],
  answerSpec: { type: "code_output" },
  checkpointHint: "",
  state: {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    lastCheck: null,
    lastTestReport: null,
    reviews: [],
  },
};

const codeInitialHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={sampleCodeProblem}
    drillId="DRL-PRG-T00-C03-02"
    index={0}
    totalQuestions={5}
    drillTitle="JavaScript & TypeScript Baseline"
    mistakeTags={[]}
    activeStep={null}
    onInputChange={noop}
    onCheckAnswer={noop}
    onToggleStepHighlight={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(codeInitialHtml, /clamps above 100 to 100/, "visible test name must render");
assert.doesNotMatch(
  codeInitialHtml,
  /assert\.strictEqual/,
  "visible test assertion code must not render on dashboard"
);
assert.match(codeInitialHtml, /Open in VS Code/);
assert.match(codeInitialHtml, /Run checks/);
assert.match(codeInitialHtml, /Open in Cursor/);
assert.match(codeInitialHtml, /Unlocks after review passes/);
assert.match(codeInitialHtml, /\(not requested\)/);

const codeAfterTestsHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={{
      ...sampleCodeProblem,
      state: {
        ...sampleCodeProblem.state,
        lastTestReport: {
          allPassed: true,
          score: 1,
          passedCount: 2,
          totalCount: 2,
          visibleResults: [],
          hiddenPassed: 1,
          hiddenTotal: 1,
          executionTimeMs: 12,
        },
      },
    }}
    drillId="DRL-PRG-T00-C03-02"
    index={0}
    totalQuestions={5}
    drillTitle="JavaScript & TypeScript Baseline"
    mistakeTags={[]}
    activeStep={null}
    onInputChange={noop}
    onCheckAnswer={noop}
    onToggleStepHighlight={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(codeAfterTestsHtml, /Copy review request/);
assert.match(codeAfterTestsHtml, /ตรวจโค้ด DRL-PRG-T00-C03-02 Q01/);

const codeAfterReviewPassHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={{
      ...sampleCodeProblem,
      state: {
        ...sampleCodeProblem.state,
        reviews: [review("pass")],
      },
    }}
    drillId="DRL-PRG-T00-C03-02"
    index={0}
    totalQuestions={5}
    drillTitle="JavaScript & TypeScript Baseline"
    mistakeTags={[]}
    activeStep={null}
    onInputChange={noop}
    onCheckAnswer={noop}
    onToggleStepHighlight={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(codeAfterReviewPassHtml, /Next problem/);
assert.match(codeAfterReviewPassHtml, /\(pass\)/);
assert.doesNotMatch(codeAfterReviewPassHtml, /Unlocks after review passes/);

// Verify type scale, translucent ::selection, and icon-only Check button across MathWorkspace, CodeDashboard, and ReviewPanel
const globalsCss = readFileSync("src/app/globals.css", "utf8");
assert.match(globalsCss, /::selection\s*\{[^}]*rgba\(250,\s*204,\s*21,\s*0\.4\)[^}]*color:\s*inherit/s);
assert.match(globalsCss, /\.dark ::selection\s*\{[^}]*rgba\(250,\s*204,\s*21,\s*0\.3\)[^}]*color:\s*inherit/s);

assert.match(beforeAttemptHtml, /<h1[^>]*class="[^"]*text-lg[^"]*"[^>]*>Linear Equations<\/h1>/);
assert.match(beforeAttemptHtml, /class="text-base leading-relaxed[^"]*">[^]*Solve/);
assert.match(
  beforeAttemptHtml,
  /<button[^>]*disabled=""[^>]*aria-label="Check answer"[^>]*title="Check answer \(Enter\)"[^>]*class="[^"]*w-11 h-11[^"]*"[^>]*><svg[^>]*lucide-check/
);
assert.doesNotMatch(beforeAttemptHtml, />Check<\/span>/);

const inBrowserCodeProblem: Problem = {
  ...sampleCodeProblem,
  workspaceFile: undefined,
  vscodeFolderUrl: undefined,
  cursorFolderUrl: undefined,
  visibleTests: undefined,
  answerSpec: { type: "output", expected: "42" },
  codeSnippet: "console.log(42);",
};
const inBrowserCodeHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={inBrowserCodeProblem}
    drillId="DRL-PRG-T00-C01-01"
    index={0}
    totalQuestions={3}
    drillTitle="Output Prediction"
    mistakeTags={[]}
    activeStep={null}
    onInputChange={noop}
    onCheckAnswer={noop}
    onToggleStepHighlight={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(inBrowserCodeHtml, /<h1[^>]*class="[^"]*text-lg[^"]*"[^>]*>Output Prediction<\/h1>/);
assert.match(inBrowserCodeHtml, /class="text-base leading-relaxed[^"]*"/);
assert.match(
  inBrowserCodeHtml,
  /<button[^>]*disabled=""[^>]*aria-label="Check answer"[^>]*title="Check answer \(Enter\)"[^>]*class="[^"]*w-11 h-11[^"]*"[^>]*><svg[^>]*lucide-check/
);
assert.doesNotMatch(inBrowserCodeHtml, />Check<\/span>/);

const sampleDrillDoc: DrillDocument = {
  drillId: "DRL-MTH-T01-C01-01",
  subject: "MTH",
  unitCode: "MTH-T01-C01-U01",
  unitTitle: "Linear Equations",
  problems: [sampleMathProblem],
  mistakeTags: [],
};
const reviewHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={sampleDrillDoc}
    liveScore={1}
    maxScore={1}
    accuracyPct={100}
    skippedCount={0}
    computedPracticeStatus="Graded"
    isSyncing={false}
    onStatusOverrideChange={noop}
    onBackToQuiz={noop}
    onConfirmSync={noop}
    onSelectQuestion={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
  />
);
assert.match(reviewHtml, /<h1[^>]*class="[^"]*text-lg[^"]*"[^>]*>Review &amp; Sync to Notion<\/h1>/);

console.log("studio rules tests passed");
