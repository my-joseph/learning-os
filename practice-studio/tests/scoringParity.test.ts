import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  applySelfScore,
  isAwaitingReview,
  isLockedAfterCorrect,
  maxAllowedSelfScore,
  outcomeToStatusTone,
  scoreProblem,
  scoreVariant,
  type ScoreProblemOptions,
} from "../src/lib/scoring";
import { statusTone } from "../src/lib/statusTone";
import type { ProblemState, VariantSessionRecord } from "../src/types/drill";

interface ScoringFixtureCase {
  id: string;
  kind?: "variant";
  opts?: ScoreProblemOptions;
  state?: Partial<ProblemState>;
  record?: VariantSessionRecord;
  cycleStartedAt?: string | null;
  expected: {
    score: 1 | 0.5 | 0 | null;
    outcome: "correct" | "assisted" | "wrong" | "skipped" | "notTried";
    firstTry: boolean;
    usedHelp: boolean;
    awaitingReview?: boolean;
  };
}

const fixturePath = path.resolve(process.cwd(), "..", "tests", "fixtures", "scoring_cases.json");
const fixture = JSON.parse(readFileSync(fixturePath, "utf-8")) as { cases: ScoringFixtureCase[] };

assert.ok(fixture.cases.length >= 25, `Expected >=25 fixture cases, got ${fixture.cases.length}`);

for (const c of fixture.cases) {
  if (c.kind === "variant") {
    const actual = scoreVariant(c.record, c.cycleStartedAt ?? null);
    assert.deepEqual(
      actual,
      {
        score: c.expected.score,
        outcome: c.expected.outcome,
        firstTry: c.expected.firstTry,
        usedHelp: c.expected.usedHelp,
      },
      `Variant scoring mismatch on case "${c.id}"`
    );
    assert.ok(statusTone[outcomeToStatusTone(actual.outcome)], `Missing statusTone for ${actual.outcome}`);
    continue;
  }

  const actual = scoreProblem(c.state, c.opts ?? {});
  assert.deepEqual(
    actual,
    {
      score: c.expected.score,
      outcome: c.expected.outcome,
      firstTry: c.expected.firstTry,
      usedHelp: c.expected.usedHelp,
    },
    `Problem scoring mismatch on case "${c.id}"`
  );
  assert.ok(statusTone[outcomeToStatusTone(actual.outcome)], `Missing statusTone for ${actual.outcome}`);

  if (typeof c.expected.awaitingReview === "boolean") {
    assert.equal(
      isAwaitingReview(c.state, c.opts ?? {}),
      c.expected.awaitingReview,
      `isAwaitingReview mismatch on case "${c.id}"`
    );
  }
}

// Verify helper invariants: lock-after-correct, lower-only self-score
const firstTryState: ProblemState = {
  userInput: "5",
  score: 1,
  divergedStep: null,
  mistakes: [],
  attempts: [{ input: "5", ts: "2026-11-20T10:00:00Z", verdict: "correct" }],
};
assert.equal(isLockedAfterCorrect(firstTryState), true);
assert.equal(
  isLockedAfterCorrect({ ...firstTryState, cycleStartedAt: "2026-11-20T12:00:00Z" }),
  false,
  "Resetting to a new cycle unlocks input"
);
assert.equal(maxAllowedSelfScore(firstTryState), 1);

const loweredHalf = applySelfScore(firstTryState, 0.5);
assert.equal(loweredHalf.score, 0.5);
assert.equal(scoreProblem(loweredHalf).outcome, "assisted");

const loweredZero = applySelfScore(firstTryState, 0);
assert.equal(loweredZero.score, 0);
assert.equal(scoreProblem(loweredZero).outcome, "wrong");

const wrongState: ProblemState = {
  userInput: "4",
  score: 0,
  divergedStep: null,
  mistakes: [],
  attempts: [{ input: "4", ts: "2026-11-20T10:00:00Z", verdict: "incorrect" }],
};
assert.equal(maxAllowedSelfScore(wrongState), 0);
assert.equal(applySelfScore(wrongState, 1).score, 0, "self-score must never raise a wrong item");

const skippedState: ProblemState = {
  userInput: "(Skipped)",
  score: 0,
  skipped: true,
  divergedStep: null,
  mistakes: ["concept-gap"],
  attempts: [{ input: "(Skipped)", ts: "2026-11-20T10:00:00Z", verdict: "skipped" }],
};
const afterSkipSelfScore = applySelfScore(skippedState, 1);
assert.equal(afterSkipSelfScore.skipped, true, "self-score must never clear skipped");
assert.equal(afterSkipSelfScore.score, 0, "self-score must never raise skipped");

console.log(`scoringParity tests passed (${fixture.cases.length} shared cases verified)`);
