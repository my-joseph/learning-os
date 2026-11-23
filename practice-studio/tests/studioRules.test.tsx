import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FormattedText } from "../src/components/FormattedText";
import { QuizPaginationBar } from "../src/components/QuizPaginationBar";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { DrillNotFoundCard } from "../src/components/shell/DrillNotFoundCard";
import { StudioHeader } from "../src/components/shell/StudioHeader";
import { StudioSidebar } from "../src/components/shell/StudioSidebar";
import { GeneratePopover } from "../src/components/shell/GeneratePopover";
import { ReviewSyncPage } from "../src/components/review-sync/ReviewSyncPage";
import {
  getPrgScore,
  getReviewRequest,
  hasCheckpointHint,
  isContextSlug,
  resolveTheme,
  THEME_INIT_SCRIPT,
} from "../src/lib/studioRules";
import { statusTone } from "../src/lib/statusTone";
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
assert.equal(getPrgScore(report, [review("pass"), review("revise")]), 0, "latest revise review scores 0");
assert.equal(getPrgScore(report, [review("revise"), review("pass")]), 0.5, "pass after earlier revise scores 0.5");
assert.equal(getPrgScore({ ...report, allPassed: false }, [review("pass")]), 0);
assert.equal(getPrgScore(undefined, [review("pass")]), 1, "pass review with passing tests scores 1 without re-running tests");
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
const mathItemView = readFileSync("src/components/math/MathItemView.tsx", "utf8");
const problemAssistSection = readFileSync("src/components/workspace/ProblemAssistSection.tsx", "utf8");
const problemSelfEval = readFileSync("src/components/workspace/ProblemSelfEval.tsx", "utf8");
const problemNavFooter = readFileSync("src/components/workspace/ProblemNavFooter.tsx", "utf8");
const answerResultCard = readFileSync("src/components/AnswerResultCard.tsx", "utf8");
const stepper = readFileSync("src/components/Stepper.tsx", "utf8");
const studioShell = readFileSync("src/components/shell/StudioShell.tsx", "utf8");
const studioHeader = readFileSync("src/components/shell/StudioHeader.tsx", "utf8");
const studioSidebar = readFileSync("src/components/shell/StudioSidebar.tsx", "utf8");
const workspaceRoute = readFileSync("src/app/api/workspace/route.ts", "utf8");
const runTestsRoute = readFileSync("src/app/api/run-tests/route.ts", "utf8");
assert.match(codeDashboard, /hasCheckpointHint\(problem\.checkpointHint\)\s*&&\s*(?:\(\s*)?(?:<CollapsibleTrigger\s+asChild>\s*)?<button/);
assert.match(problemAssistSection, /hasCheckpointHint\(problem\.checkpointHint\)\)?\s*&&\s*(?:\(\s*)?(?:<Collapsible\b[\s\S]*?<CollapsibleTrigger\s+asChild>\s*)?<button/);
assert.match(problemAssistSection, /<StepRow/);
assert.doesNotMatch(codeDashboard, /Diverged here/);
assert.match(answerResultCard, /FormattedText text=\{c\.label\}/);
assert.doesNotMatch(answerResultCard, /border-l-/);
assert.match(codeDashboard, /<AnswerResultCard/);
assert.match(codeDashboard, /aria-label=\{isReviewSession\s*\? `Answer for \$\{isLab \? "milestone" : "problem"\} \$\{index \+ 1\} of \$\{totalQuestions \?\? 1\}`\s*:\s*`Answer for \$\{isLab \? "milestone" : "problem"\} \$\{problem\.id\}`\}/);
assert.match(codeDashboard, /Copy review request/);
assert.match(codeDashboard, /Run checks/);
assert.match(codeDashboard, /Unlocks after review passes/);
assert.doesNotMatch(codeDashboard, /review-code skill/);
assert.match(codeDashboard, /Ask Claude to review your code/);
assert.match(codeDashboard, /method: "POST"[\s\S]*?JSON\.stringify\(\{ drillId \}\)/);
assert.match(codeDashboard, /workspace file from disk/);
assert.match(mathItemView, /<AnswerResultCard/);
assert.match(mathItemView, /`Answer for question \$\{problem\.id\}`/);
assert.match(mathItemView, /<ProblemAssistSection/);
assert.match(
  mathWorkspace,
  /ariaLabel=\{\s*isReviewSession\s*\?\s*`Answer for question \$\{index \+ 1\} of \$\{totalQuestions \?\? 1\}`\s*:\s*`Answer for question \$\{problem\.id\}`\s*\}/
);
assert.match(codeDashboard, /<ProblemAssistSection/);
assert.match(mathWorkspace, /max-w-\[720px\]/);
assert.match(mathWorkspace, /<ProblemSelfEval/);
assert.match(codeDashboard, /<ProblemSelfEval/);
assert.match(problemSelfEval, /statusTone\.wrong\.selfScoreActive/);
assert.doesNotMatch(mathWorkspace, /Review &amp; Sync|Review & Sync/);
assert.doesNotMatch(codeDashboard, /Review &amp; Sync|Review & Sync/);
assert.doesNotMatch(problemNavFooter, /Review &amp; Sync|Review & Sync/);
assert.match(stepper, /statusTone\.correct\.solidCircle/);
assert.match(stepper, /bg-indigo-600/);
assert.match(stepper, /overflow-x-auto/);
assert.match(stepper, /justify-center/);
assert.match(stepper, /^\s*Review$/m);
assert.match(stepper, /w-\[22px\] h-\[22px\] sm:w-6 sm:h-6/);
assert.match(stepper, /text-\[10px\] sm:text-\[11px\]/);
// Learner 2026-11-19: no keyboard focus ring on the stepper (the current-step halo is enough).
assert.doesNotMatch(stepper, /group-focus-visible:outline/);
assert.doesNotMatch(stepper, /focus-visible:ring-2/);
assert.match(studioShell, /<h1 className="sr-only"/);
assert.doesNotMatch(studioShell, /fixed left-3 top-1\/2/);
assert.match(studioShell, /<StudioSidebar/);
assert.match(studioShell, /Due today &amp; weak spots/);
assert.doesNotMatch(studioShell, /Study queue/);
assert.match(studioHeader, /lg:hidden/);
assert.doesNotMatch(studioHeader, /MoreHorizontal|More actions/);
assert.doesNotMatch(studioHeader, /Review &amp; Sync|Review & Sync/);
assert.doesNotMatch(studioHeader, /Score:/);
assert.doesNotMatch(studioHeader, /currentDrill\.drillId/);
assert.doesNotMatch(studioHeader, /DrillSwitcher|Generate drill set|Reset all/);
assert.match(studioHeader, /Open navigation sidebar/);
assert.match(studioHeader, /Due today & weak spots/);
assert.match(studioSidebar, /Generate drill set/);
assert.match(studioSidebar, /Reset all questions/);
assert.match(studioSidebar, /Reset all problems/);
assert.match(studioSidebar, /Reset all milestones/);
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
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(beforeAttemptHtml, /<h1[^>]*>Linear Equations<\/h1>/);
assert.doesNotMatch(
  beforeAttemptHtml,
  /Level 1/,
  "Math question card meta line must not show Level N (level lives under the pagination stepper)"
);
assert.doesNotMatch(beforeAttemptHtml, /Practice only/i, "Math card must not show Practice only text");
assert.doesNotMatch(beforeAttemptHtml, /Self-score:/, "self-score must not appear before an attempt");
assert.match(
  beforeAttemptHtml,
  /title="Opening before checking counts as assisted"[^>]*>[\s\S]*Show steps/,
  "Show steps button must carry assisted tooltip before first attempt"
);
assert.doesNotMatch(
  beforeAttemptHtml,
  /Opening steps before checking counts as assisted\./,
  "No assisted note line under the buttons (learner removed it; the button title keeps the hint)"
);
assert.doesNotMatch(mathWorkspace, /Practice only|· Practice|isPracticeOnly/);
assert.doesNotMatch(mathWorkspace, /!similarHasAttempt/);

// With variants available, untouched MathWorkspace renders locked ghost similar tabs & reduced top padding
const beforeAttemptWithVariantsHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={{ ...sampleMathProblem, hasVariants: true }}
    drillId="DRL-MTH-T01-C01-01"
    index={0}
    totalQuestions={5}
    drillTitle="Linear Equations"
    mistakeTags={[]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(beforeAttemptWithVariantsHtml, /role="tablist"/);
assert.match(beforeAttemptWithVariantsHtml, /aria-disabled="true"/);
assert.match(beforeAttemptWithVariantsHtml, /Answer Question 1 first/);
assert.match(beforeAttemptWithVariantsHtml, /pt-2 sm:px-6 sm:pb-6 sm:pt-3/);
assert.doesNotMatch(beforeAttemptWithVariantsHtml, /Level 1/);
assert.doesNotMatch(beforeAttemptWithVariantsHtml, /Practice only/i);

// Invalid input check must not mark problem as attempted or hide Skip / show Self-score
const afterInvalidHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={{
      ...sampleMathProblem,
      state: {
        ...sampleMathProblem.state,
        userInput: "(((",
        lastCheck: {
          verdict: "invalid input",
          message: "Invalid input: Could not tokenize expression",
          components: [],
          diagnostics: [],
        },
        attempts: [{ input: "(((", ts: "2026-11-18T00:00:00Z", verdict: "invalid input" }],
      },
    }}
    index={0}
    totalQuestions={5}
    drillTitle="Linear Equations"
    mistakeTags={[]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onSkip={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(afterInvalidHtml, /Couldn&#x27;t read that — check brackets and operators\.|Couldn't read that — check brackets and operators\./);
assert.doesNotMatch(afterInvalidHtml, /Could not tokenize expression/);
assert.doesNotMatch(afterInvalidHtml, /Self-score:/, "invalid input must not reveal self-score");
assert.match(afterInvalidHtml, />Skip<\/span>/, "invalid input must keep Skip available");

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
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(afterAttemptHtml, /Self-score:/, "self-score must appear after an attempt");
assert.ok(
  afterAttemptHtml.includes(statusTone.wrong.softCard),
  "wrong feedback uses wrong statusTone softCard"
);
assert.match(afterAttemptHtml, /Not quite/, "wrong feedback shows calm title");

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
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(codeInitialHtml, /clamps above 100 to 100/, "visible test name must render");
assert.match(
  codeInitialHtml,
  /<button(?=[^>]*aria-expanded="false")(?=[^>]*aria-controls="visible-test-code-0")[^>]*>[\s\S]*?<\/button><\/div><div(?=[^>]*id="visible-test-code-0")(?=[^>]*hidden="")[^>]*>/,
  "visible test disclosure must render collapsed by default"
);
assert.doesNotMatch(
  codeInitialHtml,
  /assert\.strictEqual/,
  "closed visible test CollapsibleContent must stay unmounted until expanded"
);
const codeExpandedTestHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={sampleCodeProblem}
    drillId="DRL-PRG-T00-C03-02"
    index={0}
    totalQuestions={5}
    drillTitle="JavaScript & TypeScript Baseline"
    mistakeTags={[]}
    initialExpandedVisibleTests={[0]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
  />
);
assert.match(
  codeExpandedTestHtml,
  /<button(?=[^>]*aria-expanded="true")(?=[^>]*aria-controls="visible-test-code-0")[^>]*>[\s\S]*?<\/button><\/div><div(?=[^>]*id="visible-test-code-0")(?![^>]*hidden="")[^>]*>[\s\S]*?assert\.strictEqual/,
  "visible test assertion code must mount inside its expanded CollapsibleContent"
);
assert.match(codeInitialHtml, /Open in VS Code/);
assert.match(codeInitialHtml, /Run checks/);
assert.doesNotMatch(codeInitialHtml, /Open in Cursor/);
assert.match(codeInitialHtml, /title="Level 1"[^>]*>Level 1<\/span>/);
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
    onInputChange={noop}
    onCheckAnswer={noop}
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
    onInputChange={noop}
    onCheckAnswer={noop}
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

// Verify type scale, translucent ::selection, and icon-only Check button across MathWorkspace, CodeDashboard, and ReviewSyncPage
const globalsCss = readFileSync("src/app/globals.css", "utf8");
assert.match(globalsCss, /::selection\s*\{[^}]*rgba\(250,\s*204,\s*21,\s*0\.4\)[^}]*color:\s*inherit/s);
assert.match(globalsCss, /\.dark ::selection\s*\{[^}]*rgba\(250,\s*204,\s*21,\s*0\.3\)[^}]*color:\s*inherit/s);
assert.match(globalsCss, /:focus:not\(:focus-visible\)\s*\{\s*outline:\s*none;/s);
assert.match(globalsCss, /:focus-visible\s*\{\s*outline:\s*2px solid #4f46e5;\s*outline-offset:\s*2px;/s);
assert.match(globalsCss, /\.dark :focus-visible\s*\{\s*outline-color:\s*#818cf8;/s);

for (const file of [
  "src/components/ui/ConfirmDialog.tsx",
  "src/components/shell/GeneratePopover.tsx",
  "src/components/code/CodeDashboard.tsx",
]) {
  const src = readFileSync(file, "utf8");
  assert.doesNotMatch(
    src,
    /\bfocus:(?:ring|border)-/,
    `${file} must use focus-visible: instead of focus:ring/focus:border`
  );
}

assert.match(beforeAttemptHtml, /<h1[^>]*class="[^"]*text-lg[^"]*"[^>]*>Linear Equations<\/h1>/);
assert.match(beforeAttemptHtml, /class="text-base leading-relaxed[^"]*">[^]*Solve/);
assert.match(
  beforeAttemptHtml,
  /<button[^>]*disabled=""[^>]*aria-label="Check answer"[^>]*title="Check \(Enter\)"[^>]*class="[^"]*w-8 h-8 rounded-lg[^"]*"[^>]*><svg[^>]*lucide-equal/
);
assert.doesNotMatch(beforeAttemptHtml, />Check<\/span>/);

const inBrowserCodeProblem: Problem = {
  ...sampleCodeProblem,
  workspaceFile: undefined,
  vscodeFolderUrl: undefined,
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
    onInputChange={noop}
    onCheckAnswer={noop}
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
  /<button[^>]*disabled=""[^>]*aria-label="Check answer"[^>]*title="Check \(Enter\)"[^>]*class="[^"]*w-8 h-8 rounded-lg[^"]*"[^>]*><svg[^>]*lucide-equal/
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
  <ReviewSyncPage
    currentDrill={sampleDrillDoc}
    liveScore={1}
    maxScore={1}
    accuracyPct={100}
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
assert.match(reviewHtml, /<h1[^>]*class="[^"]*text-lg[^"]*"[^>]*>Linear Equations<\/h1>/);
assert.match(
  reviewHtml,
  /class="[^"]*font-display[^\"]*tabular-nums[^\"]*"[^>]*>1<\/span>/,
  "Review & Sync counts must use the display typeface"
);
assert.match(
  reviewHtml,
  /class="[^"]*font-display[^\"]*tabular-nums[^\"]*"[^>]*>1<\/span>/,
  "Review & Sync totals must use the display typeface"
);

const quizTilesHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={0}
    problems={[sampleMathProblem]}
    viewMode="quiz"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(
  quizTilesHtml,
  /<button[^>]*aria-label="Review &amp; sync"[^>]*aria-pressed="false"[^>]*title="Review &amp; sync"[^>]*>.*<svg[^>]*>.*<\/svg>.*<\/button><\/li><\/ol><\/div><\/nav><\/div>$/
);
assert.match(quizTilesHtml, />Review<\/span>/);
assert.doesNotMatch(quizTilesHtml, /of 1 answered|&amp; sync<\/span>/);

const reviewTilesHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={0}
    problems={[sampleMathProblem]}
    viewMode="review"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(
  reviewTilesHtml,
  /<button[^>]*aria-label="Review &amp; sync"[^>]*aria-pressed="true"[^>]*aria-current="step"[^>]*title="Review &amp; sync"[^>]*>.*ring-indigo-600\/15.*<svg[^>]*>.*<\/svg>.*<\/button><\/li><\/ol><\/div><\/nav><\/div>$/
);

// Verify DrillNotFoundCard renders visible h1 for drills and labs
const drillNotFoundHtml = renderToStaticMarkup(<DrillNotFoundCard drillId="DRL-MTH-01" />);
assert.match(drillNotFoundHtml, /<h1[^>]*>Drill not found<\/h1>/);
const labNotFoundHtml = renderToStaticMarkup(<DrillNotFoundCard drillId="LAB-PRG-01" />);
assert.match(labNotFoundHtml, /<h1[^>]*>Lab not found<\/h1>/);
const labRouteNotFoundHtml = renderToStaticMarkup(
  <DrillNotFoundCard drillId="DOES-NOT-EXIST" isLab={true} />
);
assert.match(labRouteNotFoundHtml, /<h1[^>]*>Lab not found<\/h1>/);

// Verify GeneratePopover uses workspace item nouns and includes Level 5 (A-10)
const mathGenerateHtml = renderToStaticMarkup(
  <GeneratePopover
    isOpen={true}
    onClose={noop}
    workspace="math"
    drills={[]}
    currentDrill={null}
    onGenerated={async () => {}}
    onStatusChange={noop}
  />
);
assert.match(mathGenerateHtml, />5 questions<\/option>/);
assert.doesNotMatch(mathGenerateHtml, />5 Qs<\/option>/);
assert.match(mathGenerateHtml, />Level 5<\/option>/);

const codeGenerateHtml = renderToStaticMarkup(
  <GeneratePopover
    isOpen={true}
    onClose={noop}
    workspace="code"
    drills={[]}
    currentDrill={null}
    onGenerated={async () => {}}
    onStatusChange={noop}
  />
);
assert.match(codeGenerateHtml, />5 problems<\/option>/);
assert.doesNotMatch(codeGenerateHtml, />5 Qs<\/option>/);
assert.match(codeGenerateHtml, />Level 5<\/option>/);

// Learner 2026-11-19: 32px palette keys, no stray vertical scrollbar on line choices,
// no CAS copy row on choice questions (their plain text is only the prompt).
const mathPaletteSrc = readFileSync("src/components/math/MathPalette.tsx", "utf8");
const lineChoiceSrc = readFileSync("src/components/LineChoicePrompt.tsx", "utf8");
assert.match(mathPaletteSrc, /justify-center w-8 h-8 rounded-lg bg-zinc-100/);
assert.doesNotMatch(mathPaletteSrc, /sm:w-10 sm:h-10/);
assert.match(lineChoiceSrc, /overflow-x-auto overflow-y-hidden/);
assert.match(mathItemView, /problem\.plainText && !isChoice/);

// Learner 2026-11-19: one global list bullet (ListDot, small indigo dot); no "•" glyph bullets.
{
  const walk = (dir: string): string[] =>
    readdirSync(dir).flatMap((f) => {
      const p = `${dir}/${f}`;
      return statSync(p).isDirectory() ? walk(p) : p.endsWith(".tsx") ? [p] : [];
    });
  for (const file of walk("src/components")) {
    assert.doesNotMatch(readFileSync(file, "utf8"), />\s*•\s*</, `${file} renders a "•" glyph bullet; use <ListDot />`);
  }
}

// Learner 2026-11-22: Geist / Geist Fallback (font-sans), Roboto Slab (font-display accent), Geist Mono (code only), KaTeX (math).
{
  const layoutSrc = readFileSync("src/app/layout.tsx", "utf8");
  const tw = readFileSync("tailwind.config.ts", "utf8");
  const packageJson = readFileSync("package.json", "utf8");
  assert.match(layoutSrc, /GeistVF\.woff/);
  assert.match(layoutSrc, /--font-geist-sans/);
  assert.match(layoutSrc, /@fontsource-variable\/roboto-slab/);
  assert.doesNotMatch(layoutSrc, /@fontsource\/source-sans-pro/);
  assert.doesNotMatch(packageJson, /@fontsource\/source-sans-pro/);
  assert.match(tw, /sans: \[\s*"var\(--font-geist-sans\)",\s*'"Geist"',\s*'"Geist Fallback"'/);
  assert.match(tw, /display: \['"Roboto Slab Variable"'/);
}

// Left Sidebar prototype SSR + invariant checks
{
  const expandedSidebarHtml = renderToStaticMarkup(
    <StudioSidebar
      workspace="math"
      pillWorkspace="math"
      onSelectWorkspace={noop}
      mathHref="/math/DRL-MTH-T01-C01-01"
      codeHref="/code/DRL-PRG-T01-C01-01"
      currentDrill={sampleDrillDoc}
      theme="light"
      onToggleTheme={noop}
      onResetAll={noop}
      drills={[
        {
          drillId: "DRL-MTH-T01-C01-01",
          subject: "MATH",
          unitCode: "MTH-T01-C01-U01",
          unitTitle: "Linear Equations",
          createdAt: "2026-11-17",
          questionCount: 5,
          difficultyMode: "Mixed",
          practiceStatus: "Ready",
          score: 0,
          maxScore: 5,
          localFilePath: "",
        },
      ]}
      labs={[]}
      selectedDrillId="DRL-MTH-T01-C01-01"
      drillSearch=""
      onSearchChange={noop}
      drillFilter="ALL"
      onFilterChange={noop}
      onSelectDrill={noop}
      onOpenGenPopover={noop}
    />
  );
  assert.match(expandedSidebarHtml, /role="tree"/);
  assert.match(expandedSidebarHtml, />MTH</);
  assert.match(expandedSidebarHtml, />PRG</);
  assert.match(expandedSidebarHtml, /aria-label="Collapse sidebar"/);
  assert.match(expandedSidebarHtml, /aria-label="Generate drill set"/);
  assert.match(expandedSidebarHtml, /aria-label="Reset all questions"/);

  const collapsedSidebarHtml = renderToStaticMarkup(
    <StudioSidebar
      workspace="math"
      pillWorkspace="math"
      onSelectWorkspace={noop}
      mathHref="/math/DRL-MTH-T01-C01-01"
      codeHref="/code/DRL-PRG-T01-C01-01"
      currentDrill={sampleDrillDoc}
      theme="light"
      onToggleTheme={noop}
      onResetAll={noop}
      drills={[]}
      labs={[]}
      selectedDrillId="DRL-MTH-T01-C01-01"
      drillSearch=""
      onSearchChange={noop}
      drillFilter="ALL"
      onFilterChange={noop}
      onSelectDrill={noop}
      onOpenGenPopover={noop}
      initialCollapsed={true}
    />
  );
  assert.match(collapsedSidebarHtml, /aria-label="Expand sidebar"/);
  assert.match(collapsedSidebarHtml, /aria-label="Browse drills"/);
  assert.doesNotMatch(collapsedSidebarHtml, /role="tree"/);

  const embeddedSidebarHtml = renderToStaticMarkup(
    <StudioSidebar
      workspace="math"
      pillWorkspace="math"
      onSelectWorkspace={noop}
      mathHref="/math/DRL-MTH-T01-C01-01"
      codeHref="/code/DRL-PRG-T01-C01-01"
      currentDrill={sampleDrillDoc}
      theme="light"
      onToggleTheme={noop}
      onResetAll={noop}
      drills={[]}
      labs={[]}
      selectedDrillId="DRL-MTH-T01-C01-01"
      drillSearch=""
      onSearchChange={noop}
      drillFilter="ALL"
      onFilterChange={noop}
      onSelectDrill={noop}
      onOpenGenPopover={noop}
      embedded={true}
      initialCollapsed={true}
    />
  );
  assert.doesNotMatch(embeddedSidebarHtml, /aria-label="Collapse sidebar"/);
  assert.match(embeddedSidebarHtml, /aria-label="Generate drill set"/);

  const headerHtml = renderToStaticMarkup(
    <StudioHeader
      showHeader={true}
      currentDrill={sampleDrillDoc}
      onOpenSidebarDrawer={noop}
      onOpenSideDrawer={noop}
      sidePanelCount={2}
      tiles={<div data-testid="tiles" />}
    />
  );
  assert.match(headerHtml, /aria-label="Open navigation sidebar"/);
  assert.match(headerHtml, /aria-label="Due today &amp; weak spots"/);
  assert.match(headerHtml, /Linear Equations/);
  assert.doesNotMatch(headerHtml, /Generate drill set|Reset all/);

  for (const [label, src] of [
    ["StudioSidebar.tsx", studioSidebar],
    ["StudioHeader.tsx", studioHeader],
    ["StudioShell.tsx", studioShell],
    ["WorkspaceSwitch.tsx", readFileSync("src/components/workspace/WorkspaceSwitch.tsx", "utf8")],
  ] as const) {
    assert.doesNotMatch(src, /\b(?:amber|yellow|emerald|rose)-\d/, `${label} must not use raw palette classes`);
    assert.doesNotMatch(src, /forceMount/, `${label} must not use forceMount`);
    assert.doesNotMatch(src, /\bimport\s+(?:type\s+)?\{[^}]*\bmotion\b/, `${label} must not import motion`);
    assert.doesNotMatch(src, /<motion\./, `${label} must not render <motion.*>`);
    assert.doesNotMatch(src, /\blayout(?:Id)?\b/, `${label} must not use layout or layoutId`);
    assert.doesNotMatch(src, /[\u0E00-\u0E7F]/, `${label} must stay 100% English`);
    assert.doesNotMatch(src, /\p{Extended_Pictographic}/u, `${label} must use Lucide icons only`);
  }
}

console.log("studio rules tests passed");
