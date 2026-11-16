import assert from "node:assert";
import { canRevealVerifiedAnswer, canShowReferenceSolution } from "../src/lib/reviewGuard";
import type { ProblemState, ReviewRecord } from "../src/types/drill";

const baseState = (): ProblemState => ({
  userInput: "",
  score: null,
  divergedStep: null,
  mistakes: [],
});

const makeReview = (verdict: "pass" | "revise"): ReviewRecord => ({
  at: "2026-11-16T10:00:00Z",
  attempt: 1,
  codeHash: "sha256:abc",
  code: "export function f() {}",
  tests: { passed: 1, total: 1, failed: [] },
  lint: [],
  typecheck: [],
  findings: [],
  verdict,
  explain: null,
});

// 1. Pre-Sync Review verified answer guard (2280fc)
assert.strictEqual(canRevealVerifiedAnswer(null), false);
assert.strictEqual(canRevealVerifiedAnswer(baseState()), false);
assert.strictEqual(
  canRevealVerifiedAnswer({ ...baseState(), userInput: "42" }),
  false,
  "Draft input alone without checking must not reveal verified answer"
);
assert.strictEqual(
  canRevealVerifiedAnswer({ ...baseState(), skipped: true }),
  true,
  "Skipped problem may reveal verified answer"
);
assert.strictEqual(
  canRevealVerifiedAnswer({
    ...baseState(),
    attempts: [{ input: "42", ts: "2026-11-16T10:00:00Z", verdict: "correct" }],
  }),
  true,
  "Checked problem may reveal verified answer"
);
assert.strictEqual(
  canRevealVerifiedAnswer({
    ...baseState(),
    lastTestReport: {
      allPassed: true,
      score: 1,
      passedCount: 2,
      totalCount: 2,
      visibleResults: [],
      hiddenPassed: 0,
      hiddenTotal: 0,
      executionTimeMs: 10,
    },
  }),
  true,
  "PRG problem with test report may reveal verified answer"
);
assert.strictEqual(
  canRevealVerifiedAnswer({ ...baseState(), score: 0 }),
  true,
  "Explicitly scored problem may reveal verified answer"
);

// 2. PRG Reference Solution guard (fc1405)
assert.strictEqual(canShowReferenceSolution(null), false);
assert.strictEqual(canShowReferenceSolution(baseState()), false);
assert.strictEqual(
  canShowReferenceSolution({ ...baseState(), reviews: [makeReview("revise")] }),
  false,
  "Revise verdict must keep reference solution locked"
);
assert.strictEqual(
  canShowReferenceSolution({ ...baseState(), reviews: [makeReview("pass")] }),
  true,
  "Pass verdict unlocks reference solution"
);
assert.strictEqual(
  canShowReferenceSolution({
    ...baseState(),
    reviews: [makeReview("pass"), makeReview("revise")],
  }),
  false,
  "Latest verdict must be pass (pass followed by revise locks it again)"
);
assert.strictEqual(
  canShowReferenceSolution({
    ...baseState(),
    reviews: [makeReview("revise"), makeReview("pass")],
  }),
  true,
  "Revise followed by pass unlocks reference solution"
);

console.log("reviewGuard tests passed");
