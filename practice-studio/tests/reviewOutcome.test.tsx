import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
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
  "ReviewSyncPage must not use left accent borders on rounded boxes"
);
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

console.log("reviewOutcome tests passed");
