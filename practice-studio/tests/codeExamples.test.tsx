/**
 * Render tests for LeetCode-style `examples` and `constraints` in CodeDashboard
 * (both PRG drills and lab milestones).
 */
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { labToDrillDocument, type LabDetailResponse } from "../src/lib/labModel";
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

const drillHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={drillProblem}
    drillId="DRL-PRG-TEST-01"
    index={0}
    totalQuestions={1}
    drillTitle="Sorted Search"
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
assert.match(drillHtml, />Example 1<\/h4><p[^>]*>[\s\S]*?5 is already at index 2\.[\s\S]*?<\/p><div[^>]*font-mono/);
assert.match(drillHtml, /0 &lt;= nums\.length &lt;= 10\^4/);
assert.match(drillHtml, /<code[^>]*>nums<\/code> is sorted ascending/);
// Quiet zinc rounded block with no left accent border
assert.match(drillHtml, /bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3\.5 py-2\.5 font-mono/);
assert.doesNotMatch(drillHtml, /aria-label="Examples"[\s\S]*border-l-2/);

// Visible test names with code are collapsed disclosure buttons by default.
assert.match(drillHtml, /<button[^>]*aria-expanded="false"[^>]*aria-controls="visible-test-code-0"[^>]*>/);
assert.match(drillHtml, /<button[^>]*aria-expanded="false"[^>]*aria-controls="visible-test-code-1"[^>]*>/);
assert.match(drillHtml, /<div id="visible-test-code-0" hidden=""/);
assert.match(drillHtml, /rounded-full bg-indigo-600 dark:bg-indigo-400/);
assert.match(drillHtml, /inserts before the first value/);
assert.doesNotMatch(drillHtml, /aria-controls="visible-test-code-2"/, "tests without code stay plain names");

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
assert.match(labHtml, /Example 1/);
assert.match(labHtml, /budget = 4, cost = 1/);
assert.match(labHtml, /Example 2/);
assert.match(labHtml, /budget &gt;= 0/);
assert.match(labHtml, /aria-expanded="false"[^>]*aria-controls="visible-test-code-0"/);
assert.match(labHtml, /consumeRetry\(4, 1\), 3\);/);

// 4. After Shiki warms up, Examples Input and Output render highlighted JS token spans
//    while Input:/Output: labels remain plain zinc and inline <code> in requirements/constraints stays plain.
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

  // Plain zinc labels stay unhighlighted
  assert.match(
    highlightedHtml,
    /<span class="text-zinc-500 dark:text-zinc-400 select-none">Input: <\/span>/
  );
  assert.match(
    highlightedHtml,
    /<span class="text-zinc-500 dark:text-zinc-400 select-none">Output: <\/span>/
  );

  // Input value contains Shiki dual-theme token spans (e.g. `=` and numbers)
  assert.match(
    highlightedHtml,
    /Input: <\/span><span class="whitespace-pre-wrap break-words">(?:<span class="shiki-token" style="--shiki-light:[^;]+;--shiki-dark:[^"]+">[^<]*<\/span>)+<\/span>/
  );
  // Output value (`2`) is highlighted as a JS number token
  assert.match(
    highlightedHtml,
    /Output: <\/span><span class="whitespace-pre-wrap break-words"><span class="shiki-token" style="--shiki-light:[^;]+;--shiki-dark:[^"]+">2<\/span><\/span>/
  );
  // Inline <code> in requirements and constraints stays as plain <code> without shiki-token spans
  assert.match(
    highlightedHtml,
    /<code class="font-mono[^"]*">searchInsert\(nums, target\)<\/code>/
  );
  assert.match(highlightedHtml, /<code class="font-mono[^"]*">nums<\/code> is sorted ascending/);

  console.log("codeExamples render tests passed");
}

void testHighlightedExamples();
