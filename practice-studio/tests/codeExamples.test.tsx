/**
 * Render tests for LeetCode-style `examples` and `constraints` in CodeDashboard
 * (both PRG drills and lab milestones).
 */
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { WorkedExampleDisclosure } from "../src/components/math/WorkedExampleView";
import { ProblemAssistSection } from "../src/components/workspace/ProblemAssistSection";
import { labToDrillDocument, type LabDetailResponse } from "../src/lib/labModel";
import { projectTestRunReport } from "../src/lib/redact";
import { preloadShiki } from "../src/lib/shiki";
import type { Problem, ProblemState } from "../src/types/drill";

const noop = () => {};

const makeState = (overrides: Partial<ProblemState> = {}): ProblemState => ({
  userInput: "",
  score: null,
  divergedStep: null,
  mistakes: [],
  ...overrides,
});

// 1. PRG drill problem with 2 examples (one with explanation, one without) + constraints
const drillProblem: Problem = {
  id: "Q01",
  templateKey: "prg-search-insert",
  level: 1,
  levelLabel: "Foundation",
  category: "Core Skill",
  entryPoint: "searchInsert",
  prompt: "Implement `searchInsert(nums, target)`.\n\n**Requirements**\n- Return the insertion index.",
  starterCode: "export function searchInsert() { return 0; }",
  workspaceFile: "drills/workspace/DRL-PRG-TEST-01/Q01_searchInsert.ts",
  visibleTests: [
    {
      id: "T1",
      name: "finds existing target",
      testCode: "assert.equal(searchInsert([1, 3, 5], 3), 1);",
    },
    { id: "T2", name: "inserts before the first value", testCode: "assert.equal(searchInsert([2], 1), 0);" },
    { id: "T3", name: "keeps the name only", testCode: "" },
  ],
  examples: [
    {
      input: "nums = [1, 3, 5, 6], target = 5",
      output: "2",
      explanation: "5 is already at index 2.",
    },
    {
      input: "nums = [1, 3, 5, 6], target = 2",
      output: "1",
    },
  ],
  constraints: ["0 <= nums.length <= 10^4", "`nums` is sorted ascending"],
  answerSpec: { type: "code_output" },
  checkpointHint: "",
  state: makeState(),
};

const renderDashboard = (problem: Problem, drillId = "DRL-PRG-TEST-01") => renderToStaticMarkup(
  <CodeDashboard
    problem={problem}
    drillId={drillId}
    index={0}
    totalQuestions={1}
    drillTitle="Sorted Search"
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
const drillHtml = renderDashboard(drillProblem);
assert.match(drillHtml, /data-code-variant="terminal"[\s\S]*npm run check[\s\S]*Not run yet/);
assert.doesNotMatch(drillHtml, /Checks (passed|failed)/);

const rawOutput = "private runner transcript";
const failedReport = projectTestRunReport({
  allPassed: false,
  passedCount: 0,
  totalCount: 2,
  hiddenTotal: 1,
  rawOutput,
  visibleResults: [
    { name: "Visible check", passed: false, error: "Result differed" },
    { name: "[HIDDEN-1] private check name", passed: false, error: "private check body" },
  ],
});
assert.equal(failedReport.rawOutput, undefined);
for (const drillId of ["DRL-PRG-TEST-01", "LAB-PRG-TEST-01"]) {
  const failedHtml = renderDashboard({
    ...drillProblem,
    state: makeState({ lastTestReport: { ...failedReport, rawOutput } }),
  }, drillId);
  assert.match(failedHtml, /data-code-variant="terminal"[\s\S]*Tests  <span[^>]*>2 failed<\/span> \| <span[^>]*>0 passed<\/span><span[^>]*> \(2\)[\s\S]*Visible check Result differed[\s\S]*1 hidden check failed[\s\S]*text-status-wrong[^>]*>Checks failed/);
  assert.doesNotMatch(failedHtml, /private runner transcript|private check name|private check body/);

  const passedHtml = renderDashboard({
    ...drillProblem,
    state: makeState({
      lastTestReport: projectTestRunReport({ allPassed: true, passedCount: 2, totalCount: 2, rawOutput }),
    }),
  }, drillId);
  assert.match(passedHtml, /data-code-variant="terminal"[\s\S]*Tests  <span[^>]*>2 passed<\/span><span[^>]*> \(2\)[\s\S]*text-status-correct-text[^>]*>Checks passed/);
  assert.doesNotMatch(passedHtml, /private runner transcript/);
}

// Examples appear right after requirements and before Visible tests
const reqIdx = drillHtml.indexOf("Return the insertion index.");
const exIdx = drillHtml.indexOf("Examples");
const conIdx = drillHtml.indexOf("Constraints");
const visIdx = drillHtml.indexOf("Visible tests");
assert.ok(reqIdx !== -1 && exIdx > reqIdx, "Examples must appear after requirements");
assert.ok(conIdx > exIdx, "Constraints must appear after Examples");
assert.ok(visIdx > conIdx, "Visible tests must appear after Constraints");

assert.match(drillHtml, /<h4[^>]*text-sm font-semibold[^>]*>Example 1<\/h4>/);
assert.match(drillHtml, /<h4[^>]*text-sm font-semibold[^>]*>Example 2<\/h4>/);
assert.match(drillHtml, /Input:\s*<\/span><span[^>]*>nums = \[1, 3, 5, 6\], target = 5<\/span>/);
assert.match(drillHtml, /Output:\s*<\/span><span[^>]*>2<\/span>/);
assert.doesNotMatch(drillHtml, /Explanation:/, "no Explanation: prefix");
assert.doesNotMatch(drillHtml, />Examples</, "no small Examples label");
// explanation sits between the Example heading and its code block
assert.match(drillHtml, />Example 1<\/h4><div[^>]*>[\s\S]*?5 is already at index 2\.[\s\S]*?<\/div><div[^>]*data-code-variant="inline-example"/);
assert.match(drillHtml, /0 &lt;= nums\.length &lt;= 10\^4/);
assert.match(drillHtml, /<code[^>]*>nums<\/code> is sorted ascending/);
// Paired examples use the shared wrapping code surface.
assert.match(drillHtml, /data-code-variant="inline-example"><pre[^>]*data-wrap="true"/);

// Visible test names with code are collapsed Radix Collapsible disclosures by default.
assert.match(drillHtml, /<button(?=[^>]*aria-expanded="false")(?=[^>]*aria-controls="visible-test-code-0")[^>]*>/);
assert.match(drillHtml, /<button(?=[^>]*aria-expanded="false")(?=[^>]*aria-controls="visible-test-code-1")[^>]*>/);
assert.match(drillHtml, /<div(?=[^>]*id="visible-test-code-0")(?=[^>]*hidden="")[^>]*>/);
assert.doesNotMatch(drillHtml, /searchInsert\(\[1, 3, 5\], 3\)/, "collapsed visible test code stays unmounted");
// Learner 2026-11-26: PRG prompt lists (Visible tests, Constraints, findings) have no dot bullets.
assert.doesNotMatch(drillHtml, /data-list-kind=/);
assert.match(drillHtml, /inserts before the first value/);
assert.doesNotMatch(drillHtml, /aria-controls="visible-test-code-2"/, "tests without code stay plain names");

// Expanding a single visible test mounts only that test's assertion code.
const expandedDrillHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={drillProblem}
    drillId="DRL-PRG-TEST-01"
    index={0}
    totalQuestions={1}
    drillTitle="Sorted Search"
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
assert.match(expandedDrillHtml, /<button(?=[^>]*aria-expanded="true")(?=[^>]*aria-controls="visible-test-code-0")[^>]*>/);
assert.match(expandedDrillHtml, /searchInsert\(\[1, 3, 5\], 3\), 1/);
assert.match(expandedDrillHtml, /data-code-variant="wrapped"/);
assert.doesNotMatch(expandedDrillHtml, /searchInsert\(\[2\], 1\)/, "other collapsed tests stay unmounted");

// Zero-leak Collapsible guard: closed hints, reference solutions, review history, and explain stay unmounted.
const gatedProblem: Problem = {
  ...drillProblem,
  checkpointHint: "SECRET_CHECKPOINT_HINT_TEXT",
  solutionCode: "export function searchInsert() { return SECRET_REF_CODE; }",
};
const gatedHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={gatedProblem}
    drillId="DRL-PRG-TEST-01"
    index={0}
    totalQuestions={1}
    drillTitle="Sorted Search"
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
assert.match(gatedHtml, /<button[^>]*aria-expanded="false"[^>]*>[\s\S]*?Hint<\/span>/);
assert.match(gatedHtml, /Unlocks after review passes/);
assert.doesNotMatch(gatedHtml, /SECRET_CHECKPOINT_HINT_TEXT/, "closed checkpoint hint must not mount in DOM");
assert.doesNotMatch(gatedHtml, /SECRET_REF_CODE/, "locked/closed reference solution must never mount in DOM");
assert.doesNotMatch(gatedHtml, /No reviews recorded yet\./, "closed review history must remain unmounted");

// WorkedExampleDisclosure keeps steps and answer unmounted until open.
const sampleExample = {
  token: "ex-1",
  prompt: "SECRET_EXAMPLE_PROMPT",
  answerDisplay: "SECRET_EXAMPLE_ANS",
  answerPlain: "SECRET_EXAMPLE_ANS",
  steps: [{ explain: "SECRET_EXAMPLE_STEP" }],
};
const closedExampleHtml = renderToStaticMarkup(<WorkedExampleDisclosure example={sampleExample} />);
assert.match(closedExampleHtml, /aria-expanded="false"/);
assert.doesNotMatch(closedExampleHtml, /SECRET_EXAMPLE_PROMPT|SECRET_EXAMPLE_ANS|SECRET_EXAMPLE_STEP/);
const openExampleHtml = renderToStaticMarkup(<WorkedExampleDisclosure example={sampleExample} defaultOpen />);
assert.match(openExampleHtml, /aria-expanded="true"/);
assert.match(openExampleHtml, /SECRET_EXAMPLE_PROMPT/);
assert.match(openExampleHtml, /SECRET_EXAMPLE_STEP/);

// ProblemAssistSection keeps hint, setup, and steps unmounted when closed and preserves assisted hint title.
const assistProblem: Problem = {
  ...drillProblem,
  checkpointHint: "SECRET_ASSIST_HINT",
  answerDisplay: "SECRET_ASSIST_ANSWER",
  steps: [{ explain: "SECRET_ASSIST_STEP" }],
};
const closedAssistHtml = renderToStaticMarkup(
  <ProblemAssistSection
    problem={assistProblem}
    hasAttempt={false}
    showHint={false}
    onToggleHint={noop}
    showSolution={false}
    onToggleSolution={noop}
    stepsUnopenedUnattempted={true}
    hasSetup={true}
    showSetup={false}
    setupUnopenedUnattempted={true}
    onToggleSetup={noop}
    setupDisclosure={<div>SECRET_ASSIST_SETUP</div>}
    onReset={noop}
  />
);
assert.match(closedAssistHtml, /title="Opening before checking counts as assisted"[^>]*>[\s\S]*Show equation set-up/);
assert.match(closedAssistHtml, /title="Opening before checking counts as assisted"[^>]*>[\s\S]*Show steps/);
assert.doesNotMatch(closedAssistHtml, /SECRET_ASSIST_HINT|SECRET_ASSIST_SETUP|SECRET_ASSIST_STEP|SECRET_ASSIST_ANSWER/);
const openAssistHtml = renderToStaticMarkup(
  <ProblemAssistSection
    problem={assistProblem}
    hasAttempt={false}
    showHint={true}
    onToggleHint={noop}
    showSolution={true}
    onToggleSolution={noop}
    stepsUnopenedUnattempted={false}
    showStepsHeader={true}
    hasSetup={true}
    showSetup={true}
    setupUnopenedUnattempted={false}
    onToggleSetup={noop}
    setupDisclosure={<div>VISIBLE_ASSIST_SETUP</div>}
    onReset={noop}
  />
);
assert.match(openAssistHtml, /SECRET_ASSIST_HINT/);
assert.match(openAssistHtml, /VISIBLE_ASSIST_SETUP/);
assert.match(openAssistHtml, /SECRET_ASSIST_STEP/);

// Hidden test implementations and trap mutants must never render in the learner list.
const secretProblem = {
  ...drillProblem,
  hiddenTests: [{ id: "H1", name: "SECRET_HIDDEN_TEST_NAME", testCode: "SECRET_HIDDEN_TEST_CODE" }],
  trapMutants: ["SECRET_TRAP_MUTANT_CODE"],
} as Problem;
const secretHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={secretProblem}
    drillId="DRL-PRG-TEST-01"
    index={0}
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
assert.doesNotMatch(secretHtml, /SECRET_HIDDEN_TEST_NAME|SECRET_HIDDEN_TEST_CODE|SECRET_TRAP_MUTANT_CODE/);

// 2. Drill problem WITHOUT examples or constraints omits both headings cleanly
const plainProblem: Problem = {
  ...drillProblem,
  examples: undefined,
  constraints: undefined,
};
const plainHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={plainProblem}
    drillId="DRL-PRG-TEST-01"
    index={0}
    totalQuestions={1}
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
assert.doesNotMatch(plainHtml, /aria-label="Examples"/);
assert.doesNotMatch(plainHtml, /aria-label="Constraints"/);

// 3. Lab milestone via labToDrillDocument renders Examples and Constraints
const labDetail: LabDetailResponse = {
  id: "LAB-PRG-T01-C01-90",
  labId: "LAB-PRG-T01-C01-90",
  title: "Retry Budget",
  unitCode: "PRG-T01-C01",
  chapterCode: "PRG-T01-C01",
  topicCode: "PRG-T01",
  unitsUsed: ["PRG-T01-C01-U02"],
  kind: "chapter-lab",
  level: 2,
  domain: "retry-budget",
  scenario: "Retry budget manager.",
  readme: "",
  workspaceDir: "/tmp/lab",
  vscodeFolderUrl: "vscode://file//tmp/lab",
  testCommand: "npm test",
  checkCommand: "npm run check",
  unitNotionUrl: null,
  milestones: [
    {
      id: "M1",
      title: "Counter",
      goal: "Deduct retry cost.",
      description: "Implement `consumeRetry(budget, cost)`.",
      units: ["PRG-T01-C01-U02"],
      visibleTestFiles: ["tests/m1_budget.test.ts"],
      visibleTests: [
        { id: "M1-T1", name: "deducts cost", testCode: "assert.equal(consumeRetry(4, 1), 3);" },
      ],
      examples: [
        { input: "budget = 4, cost = 1", output: "3", explanation: "4 - 1 = 3" },
        { input: "budget = 6, cost = 2", output: "4" },
      ],
      constraints: ["budget >= 0"],
      testCommand: "npm run test:m1",
      checkCommand: "npm run check:m1",
      mainFile: "src/budget.ts",
      vscodeFolderUrl: "vscode://file//tmp/lab",
      vscodeUrl: null,
      reviewStatus: "not_requested",
      state: makeState(),
    },
  ],
  progress: {
    passedCount: 0,
    reviseCount: 0,
    notStartedCount: 1,
    totalCount: 1,
    practiceStatus: "Ready",
    score: 0,
    maxScore: 1,
    updatedAt: null,
    milestones: { M1: "not_requested" },
  },
  sessionSummary: {
    practiceStatus: "Ready",
    score: 0,
    maxScore: 1,
    accuracyPct: 0,
    mistakeCategories: [],
    divergedStepsSummary: "",
    attemptDate: null,
  },
};

const labDrillDoc = labToDrillDocument(labDetail);
const labHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={labDrillDoc.problems[0]}
    drillId={labDrillDoc.drillId}
    index={0}
    totalQuestions={1}
    drillTitle={labDrillDoc.unitTitle}
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
assert.match(labHtml, /Example 1/);
assert.match(labHtml, /budget = 4, cost = 1/);
assert.match(labHtml, /Example 2/);
assert.match(labHtml, /budget &gt;= 0/);
assert.match(labHtml, /<button(?=[^>]*aria-expanded="false")(?=[^>]*aria-controls="visible-test-code-0")[^>]*>/);
assert.doesNotMatch(labHtml, /consumeRetry\(4, 1\), 3\);/, "closed lab visible test code stays unmounted");
const labExpandedHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={labDrillDoc.problems[0]}
    drillId={labDrillDoc.drillId}
    index={0}
    totalQuestions={1}
    drillTitle={labDrillDoc.unitTitle}
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
assert.match(labExpandedHtml, /<button(?=[^>]*aria-expanded="true")(?=[^>]*aria-controls="visible-test-code-0")[^>]*>/);
assert.match(labExpandedHtml, /consumeRetry\(4, 1\), 3\);/);

// 4. After Shiki warms up, Examples Input and Output render highlighted JS token spans
//    while Input:/Output: labels and inline code in prose stay plain.
async function testHighlightedExamples() {
  await preloadShiki(["javascript"]);
  const highlightedHtml = renderToStaticMarkup(
    <CodeDashboard
      problem={drillProblem}
      drillId="DRL-PRG-TEST-01"
      index={0}
      totalQuestions={1}
      drillTitle="Sorted Search"
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

  // Labels stay unhighlighted.
  assert.match(
    highlightedHtml,
    /<span class="select-none text-muted">Input: <\/span>/
  );
  assert.match(
    highlightedHtml,
    /<span class="select-none text-muted">Output: <\/span>/
  );

  // Input value contains Shiki dual-theme token spans (e.g. `=` and numbers)
  assert.match(
    highlightedHtml,
    /Input: <\/span><span>(?:<span class="shiki-token" style="--shiki-light:[^;]+;--shiki-dark:[^"]+">[^<]*<\/span>)+<\/span>/
  );
  // Output value (`2`) is highlighted as a JS number token
  assert.match(
    highlightedHtml,
    /Output: <\/span><span><span class="shiki-token" style="--shiki-light:[^;]+;--shiki-dark:[^"]+">2<\/span><\/span>/
  );
  // Inline <code> in requirements and constraints stays as plain <code> without shiki-token spans
  assert.match(
    highlightedHtml,
    /<code class="inline-code">searchInsert\(nums, target\)<\/code>/
  );
  assert.match(highlightedHtml, /<code class="inline-code">nums<\/code> is sorted ascending/);
  // Learner 2026-11-26: no entry-point badge beside "Problem X of Y".
  assert.doesNotMatch(highlightedHtml, /<code class="inline-code text-foreground-control">searchInsert<\/code>/);

  console.log("codeExamples render tests passed");
}

void testHighlightedExamples();
