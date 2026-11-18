/**
 * Render tests for LeetCode-style `examples` and `constraints` in CodeDashboard
 * (both PRG drills and lab milestones).
 */
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { labToDrillDocument, type LabDetailResponse } from "../src/lib/labModel";
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
  visibleTests: [{ id: "T1", name: "finds existing target", testCode: "" }],
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
assert.match(drillHtml, /Explanation:/);
assert.match(drillHtml, /5 is already at index 2\./);
assert.match(drillHtml, /0 &lt;= nums\.length &lt;= 10\^4/);
assert.match(drillHtml, /<code[^>]*>nums<\/code> is sorted ascending/);
// Quiet zinc rounded block with no left accent border
assert.match(drillHtml, /bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl px-3\.5 py-2\.5 font-mono/);
assert.doesNotMatch(drillHtml, /aria-label="Examples"[\s\S]*border-l-2/);

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
  cursorFolderUrl: "cursor://file//tmp/lab",
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
      visibleTests: [{ id: "M1-T1", name: "deducts cost", testCode: "" }],
      examples: [
        { input: "budget = 4, cost = 1", output: "3", explanation: "4 - 1 = 3" },
        { input: "budget = 6, cost = 2", output: "4" },
      ],
      constraints: ["budget >= 0"],
      testCommand: "npm run test:m1",
      checkCommand: "npm run check:m1",
      mainFile: "src/budget.ts",
      vscodeFolderUrl: "vscode://file//tmp/lab",
      cursorFolderUrl: "cursor://file//tmp/lab",
      vscodeUrl: null,
      cursorUrl: null,
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

console.log("codeExamples render tests passed");
