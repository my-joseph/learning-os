import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  classifyReviewOutcome,
  ensureExpandedRow,
  formatDuration,
  getProblemOutcomeMeta,
  getQuestionLabel,
  getReviewOutcomeMeta,
  groupReviewProblems,
  toSingleLinePrompt,
  toggleExpandedRow,
} from "../src/lib/reviewOutcome";
import { ReviewPanel } from "../src/components/shell/ReviewPanel";
import { statusTone } from "../src/lib/statusTone";
import type { DrillDocument, Problem, ProblemState } from "../src/types/drill";

const baseState = (): ProblemState => ({
  userInput: "",
  score: null,
  divergedStep: null,
  mistakes: [],
});

// 1. Outcome classification
assert.equal(classifyReviewOutcome(null), "unanswered");
assert.equal(classifyReviewOutcome(undefined), "unanswered");
assert.equal(classifyReviewOutcome(baseState()), "unanswered");
assert.equal(
  classifyReviewOutcome({ ...baseState(), userInput: "42" }),
  "unanswered",
  "Draft input without score or review remains unanswered"
);
assert.equal(
  classifyReviewOutcome({ ...baseState(), skipped: true, score: 0 }),
  "skipped"
);
assert.equal(
  classifyReviewOutcome({ ...baseState(), score: 1 }),
  "correct_first"
);
assert.equal(
  classifyReviewOutcome({
    ...baseState(),
    score: 1,
    setupRevealedBeforeAnswer: true,
  }),
  "assisted_or_partial",
  "Opening setup before answering must not classify as first-try correct"
);
assert.equal(
  classifyReviewOutcome({
    ...baseState(),
    score: 1,
    solutionRevealedBeforeAnswer: true,
  }),
  "assisted_or_partial"
);
assert.equal(
  classifyReviewOutcome({ ...baseState(), score: 1, hintsRevealed: 1 }),
  "assisted_or_partial"
);
assert.equal(
  classifyReviewOutcome({
    ...baseState(),
    score: 1,
    attempts: [{ input: "5", ts: "2026-11-18T00:00:00Z", verdict: "correct", setupRevealed: true }],
  }),
  "assisted_or_partial"
);
assert.equal(
  classifyReviewOutcome({ ...baseState(), score: 0.5 }),
  "assisted_or_partial"
);
assert.equal(classifyReviewOutcome({ ...baseState(), score: 0 }), "wrong");
assert.equal(
  classifyReviewOutcome({
    ...baseState(),
    reviews: [
      {
        at: "2026-11-18T00:00:00Z",
        attempt: 1,
        codeHash: "sha256:abc",
        code: "",
        tests: { passed: 1, total: 1, failed: [] },
        lint: [],
        typecheck: [],
        findings: [],
        verdict: "pass",
        explain: null,
      },
    ],
  }),
  "correct_first"
);
assert.equal(
  classifyReviewOutcome({
    ...baseState(),
    reviews: [
      {
        at: "2026-11-18T00:00:00Z",
        attempt: 1,
        codeHash: "sha256:abc",
        code: "",
        tests: { passed: 1, total: 1, failed: [] },
        lint: [],
        typecheck: [],
        findings: [],
        verdict: "revise",
        explain: null,
      },
    ],
  }),
  "wrong"
);
assert.equal(
  classifyReviewOutcome({
    ...baseState(),
    lastTestReport: {
      allPassed: true,
      score: 1,
      passedCount: 2,
      totalCount: 2,
      visibleResults: [],
      hiddenPassed: 0,
      hiddenTotal: 0,
      executionTimeMs: 5,
    },
  }),
  "awaiting_review",
  "PRG passing tests without a review classify as awaiting_review"
);

// 2. Outcome colours & labels
assert.equal(getReviewOutcomeMeta("correct_first").nodeClassName, statusTone.correct.dot);
assert.equal(getReviewOutcomeMeta("assisted_or_partial").nodeClassName, statusTone.assisted.dot);
assert.equal(getReviewOutcomeMeta("wrong").nodeClassName, statusTone.wrong.dot);
assert.equal(getReviewOutcomeMeta("skipped").nodeClassName, statusTone.skipped.dot);
assert.equal(getReviewOutcomeMeta("unanswered").nodeClassName, statusTone.notTried.dot);
assert.equal(getProblemOutcomeMeta({ ...baseState(), score: 1 }).label, "Correct");

// 3. Labels, durations, and single-line prompt formatting
assert.equal(getQuestionLabel("Q03", 2, false), "Q3");
assert.equal(getQuestionLabel("M2", 1, true), "M2");
assert.equal(formatDuration(0), "—");
assert.equal(formatDuration(45_000), "45s");
assert.equal(formatDuration(252_000), "4m 12s");
assert.equal(formatDuration(120_000), "2m");
assert.equal(formatDuration(3_720_000), "1h 2m");
assert.equal(
  toSingleLinePrompt("Solve $2x = 6$\n\n```js\nconst a = 1;\n```\nReturn value."),
  "Solve $2x = 6$ Return value."
);

// 4. Grouping & counts
const makeProblem = (id: string, state: ProblemState): Problem => ({
  id,
  templateKey: "tpl",
  level: 1,
  levelLabel: "Level 1",
  category: "Algebra",
  prompt: `Solve for $x$ in ${id}.`,
  answerPlain: "SECRET_42",
  answerDisplay: "SECRET_42",
  checkpointHint: "",
  answerSpec: { type: "number" },
  state,
});

const sampleDrill: DrillDocument = {
  schemaVersion: "2.0",
  drillId: "DRL-MTH-T01-C01-U01-01",
  subject: "MATH",
  unitCode: "MTH-T01-C01-U01",
  unitTitle: "Linear Equations",
  chapterCode: "MTH-T01-C01",
  topicCode: "MTH-T01",
  unitNotionUrl: null,
  createdAt: "2026-11-18T00:00:00Z",
  config: { questionCount: 5, difficulty: "ALL", difficultyMode: "Mixed" },
  mistakeTags: [
    { id: "sign-error", label: "Sign error ($-$)", name: "Sign error", autoFrom: [] },
  ],
  problems: [
    makeProblem("Q01", {
      ...baseState(),
      score: 0,
      userInput: "3",
      durationMs: 30_000,
      attempts: [{ input: "3", ts: "2026-11-18T00:00:00Z", verdict: "incorrect" }],
    }),
    makeProblem("Q02", {
      ...baseState(),
      score: 0.5,
      userInput: "42",
      hintsRevealed: 1,
      durationMs: 45_000,
      attempts: [{ input: "42", ts: "2026-11-18T00:01:00Z", verdict: "correct" }],
    }),
    makeProblem("Q03", {
      ...baseState(),
      score: 1,
      userInput: "42",
      durationMs: 25_000,
      attempts: [{ input: "42", ts: "2026-11-18T00:02:00Z", verdict: "correct" }],
    }),
    makeProblem("Q04", { ...baseState(), skipped: true, score: 0, durationMs: 10_000 }),
    makeProblem("Q05", { ...baseState(), durationMs: 0 }),
  ],
  sessionSummary: {
    practiceStatus: "Needs Retry",
    score: 1.5,
    maxScore: 5,
    accuracyPct: 30,
    mistakeCategories: [],
    divergedStepsSummary: "",
    attemptDate: null,
  },
  localFilePath: "drills/data/MTH-T01-C01-U01/DRL-MTH-T01-C01-U01-01.json",
};

const grouped = groupReviewProblems(sampleDrill.problems);
assert.deepEqual(
  grouped.needsAttention.map((g) => g.problem.id),
  ["Q01", "Q02", "Q04", "Q05"]
);
assert.deepEqual(
  grouped.correct.map((g) => g.problem.id),
  ["Q03"]
);
assert.equal(grouped.firstTryCount, 1);
assert.equal(grouped.unansweredCount, 1);
assert.equal(grouped.totalDurationMs, 110_000);

// 5. ReviewPanel layout invariants & reveal guard
const noop = () => {};
const html = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={sampleDrill}
    initialExpandedIds={["Q01", "Q05"]}
    liveScore={1.5}
    maxScore={5}
    accuracyPct={30}
    computedPracticeStatus="Needs Retry"
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

assert.match(html, /<h1[^>]*>Linear Equations<\/h1>/);
assert.match(html, /MTH-T01-C01-U01/);
assert.doesNotMatch(html, /· Review &amp; sync|· Review & sync/);
assert.match(html, /1\.5 \/ 5/);
assert.match(html, /title="Q3 · correct"/);
assert.match(html, /title="Q1 · wrong"/);
assert.match(html, /title="Q2 · assisted \/ partial"/);
assert.match(html, /title="Q4 · skipped"/);
assert.match(html, /title="Q5 · unanswered"/);
assert.match(html, /on the first try/);
assert.match(html, /30%/);
assert.match(html, /1m 50s/);
assert.match(html, /Sync to Notion/);
assert.match(html, /Back to questions/);
assert.match(html, /not tried\. They are sent as not tried/);
assert.match(html, /To review/);
assert.match(html, /aria-expanded="false"[^>]*>.*Got right/);
assert.doesNotMatch(
  html,
  /id="review-row-Q03"/,
  "Correct group must be collapsed by default"
);
assert.match(html, /id="review-row-Q01"/);
assert.match(html, /id="review-row-Q05"/);
assert.match(
  html,
  /Not tried yet/,
  "Unanswered Q05 must keep verified answer hidden"
);
assert.match(html, /aria-label="Question outcomes"/);
// Lab & Code noun parity in ReviewPanel
const labReviewHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={{ ...sampleDrill, drillId: "LAB-PRG-T01-C01-01", subject: "PRG" }}
    liveScore={0}
    maxScore={5}
    accuracyPct={0}
    computedPracticeStatus="Needs Retry"
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
assert.match(labReviewHtml, /Back to milestones/);
const codeReviewHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={{ ...sampleDrill, drillId: "DRL-PRG-T01-C01-U01-01", subject: "PRG" }}
    liveScore={0}
    maxScore={5}
    accuracyPct={0}
    computedPracticeStatus="Needs Retry"
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
assert.match(codeReviewHtml, /Back to problems/);

// Bug 2: Unattempted rows (including invalid-input-only or score-only) hide score buttons, mistake tags, and notes
assert.match(html, /Self-score:/);
assert.doesNotMatch(
  html,
  /Note for Q5/,
  "Unattempted Q5 must not render note input in ReviewPanel"
);

const invalidAndScoreOnlyDrill: DrillDocument = {
  ...sampleDrill,
  problems: [
    makeProblem("Q01", {
      ...baseState(),
      userInput: "(((",
      lastCheck: {
        verdict: "invalid input",
        message: "Couldn't read that — check brackets and operators.",
        components: [],
        diagnostics: [],
      },
      attempts: [{ input: "(((", ts: "2026-11-18T00:00:00Z", verdict: "invalid input" }],
    }),
    makeProblem("Q02", { ...baseState(), score: 1 }),
  ],
};
const guardedHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={invalidAndScoreOnlyDrill}
    liveScore={0}
    maxScore={2}
    accuracyPct={0}
    computedPracticeStatus="Needs Retry"
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
assert.doesNotMatch(guardedHtml, /Self-score:/);
assert.doesNotMatch(guardedHtml, /Note for Q1/);
assert.doesNotMatch(guardedHtml, /Note for Q2/);
assert.doesNotMatch(guardedHtml, /SECRET_42/, "Neither invalid input nor score-only may reveal verified answer");

// Bug 3: Back to questions leaves review without jumping to last question
const studioClientSrc = readFileSync("src/components/shell/StudioClient.tsx", "utf8");
assert.match(
  studioClientSrc,
  /onBackToQuiz=\{\(\)\s*=>\s*setViewMode\("quiz"\)\}/,
  "Back to questions must simply return to quiz mode on the active question"
);
assert.doesNotMatch(
  studioClientSrc,
  /onBackToQuiz=\{handlePrevQuestion\}/
);

const reviewSource = readFileSync("src/components/review-sync/ReviewItemRow.tsx", "utf8");
assert.doesNotMatch(
  reviewSource,
  /border-l-[24]/,
  "ReviewPanel must not use left accent borders on rounded boxes"
);
const reviewPageSource = readFileSync("src/components/review-sync/ReviewSyncPage.tsx", "utf8");
assert.match(reviewPageSource, /ensureExpandedRow/, "Score-strip jump must expand the target row");
assert.match(reviewSource, /<Reveal\s+show=\{expanded\}/, "Row accordion must animate with Reveal");

// 6. Accordion state helpers & collapsed vs expanded HTML (no steps/solution leakage)
let expandedState: Record<string, boolean> = {};
expandedState = toggleExpandedRow(expandedState, "Q01");
assert.equal(expandedState.Q01, true);
expandedState = toggleExpandedRow(expandedState, "Q01");
assert.equal(expandedState.Q01, false);
expandedState = ensureExpandedRow(expandedState, "Q02");
assert.equal(expandedState.Q02, true);
assert.equal(ensureExpandedRow(expandedState, "Q02"), expandedState);

const accordionProblem: Problem = {
  id: "Q01",
  templateKey: "tpl-acc",
  level: 2,
  levelLabel: "Level 2",
  category: "Geometry",
  prompt: "Find $x$ in the triangle.\n\n```txt\nEXPANDED_PROMPT_BLOCK\n```",
  display: "SECRET_DISPLAY_SETUP",
  solutionCode: "SECRET_SOLUTION_CODE",
  checkpointHint: "SECRET_CHECKPOINT_HINT",
  steps: [
    {
      title: "SECRET_STEP_TITLE",
      math: "SECRET_STEP_MATH",
      explanation: "SECRET_STEP_EXPLANATION",
    },
  ],
  figure: {
    kind: "geometry_2d",
    title: "Right triangle ABC",
    points: { A: [0, 0], B: [3, 0], C: [0, 4] },
    shapes: [{ type: "polygon", vertices: ["A", "B", "C"] }],
  },
  answerPlain: "SECRET_42",
  answerDisplay: "SECRET_42",
  answerSpec: { type: "number" },
  state: baseState(),
};

const accordionDrill: DrillDocument = {
  ...sampleDrill,
  problems: [accordionProblem],
};

const collapsedHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={accordionDrill}
    liveScore={0}
    maxScore={1}
    accuracyPct={0}
    computedPracticeStatus="Needs Retry"
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

assert.match(collapsedHtml, /aria-expanded="true"/,
  "a To review section with one item expands its row by default");
assert.match(collapsedHtml, /aria-controls="review-panel-Q01"/);
assert.match(collapsedHtml, /id="review-panel-Q01"/);
assert.match(collapsedHtml, /EXPANDED_PROMPT_BLOCK/);
assert.match(collapsedHtml, /Right triangle ABC/);

const expandedHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={accordionDrill}
    liveScore={0}
    maxScore={1}
    accuracyPct={0}
    computedPracticeStatus="Needs Retry"
    isSyncing={false}
    initialExpandedIds={["Q01"]}
    onStatusOverrideChange={noop}
    onBackToQuiz={noop}
    onConfirmSync={noop}
    onSelectQuestion={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
  />
);

assert.match(expandedHtml, /aria-expanded="true"/);
assert.match(expandedHtml, /aria-controls="review-panel-Q01"/);
assert.match(expandedHtml, /id="review-panel-Q01"/);
assert.match(expandedHtml, /EXPANDED_PROMPT_BLOCK/);
assert.match(expandedHtml, /katex/);
assert.match(expandedHtml, /Right triangle ABC/);
assert.match(expandedHtml, /<svg/);
assert.match(expandedHtml, /Not tried yet/);
assert.match(
  reviewSource,
  /sm:pl-\[72px\]/,
  "Review detail aligns under the row content on desktop"
);
assert.doesNotMatch(
  reviewSource,
  /toSingleLinePrompt/,
  "Review row must not truncate the full prompt"
);
assert.doesNotMatch(expandedHtml, /SECRET_DISPLAY_SETUP/);
assert.doesNotMatch(expandedHtml, /SECRET_SOLUTION_CODE/);
assert.doesNotMatch(expandedHtml, /SECRET_CHECKPOINT_HINT/);
assert.doesNotMatch(expandedHtml, /SECRET_STEP_TITLE/);
assert.doesNotMatch(expandedHtml, /SECRET_STEP_MATH/);
assert.doesNotMatch(expandedHtml, /SECRET_STEP_EXPLANATION/);
assert.doesNotMatch(expandedHtml, /SECRET_42/);

console.log("reviewOutcome tests passed");
