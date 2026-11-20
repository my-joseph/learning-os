import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import {
  buildSessionSummary,
  computeSessionMetrics,
  getCoveredUnits,
} from "../src/lib/sessionSummary";
import type { DrillDocument } from "../src/types/drill";

interface CoveredUnitsCase {
  id: string;
  drill: DrillDocument;
  expected: string[];
}

interface SummaryCase {
  id: string;
  drill: DrillDocument;
  expected: {
    score: number;
    maxScore: number;
    accuracyPct: number;
    practiceStatus: "Graded" | "Needs Retry";
    skippedCount: number;
  };
}

const fixturePath = path.resolve(
  process.cwd(),
  "..",
  "tests",
  "fixtures",
  "session_summary_cases.json"
);
const fixture = JSON.parse(readFileSync(fixturePath, "utf-8")) as {
  coveredUnitsCases: CoveredUnitsCase[];
  summaryCases: SummaryCase[];
};

for (const c of fixture.coveredUnitsCases) {
  const actual = getCoveredUnits(c.drill);
  assert.deepEqual(
    actual,
    c.expected,
    `getCoveredUnits mismatch on case "${c.id}": got ${JSON.stringify(actual)}`
  );
}

for (const c of fixture.summaryCases) {
  const metrics = computeSessionMetrics(c.drill, null);
  assert.equal(metrics.liveScore, c.expected.score, `liveScore mismatch on "${c.id}"`);
  assert.equal(metrics.maxScore, c.expected.maxScore, `maxScore mismatch on "${c.id}"`);
  assert.equal(metrics.accuracyPct, c.expected.accuracyPct, `accuracyPct mismatch on "${c.id}"`);
  assert.equal(
    metrics.computedPracticeStatus,
    c.expected.practiceStatus,
    `practiceStatus mismatch on "${c.id}"`
  );
  assert.equal(metrics.skippedCount, c.expected.skippedCount, `skippedCount mismatch on "${c.id}"`);

  const summary = buildSessionSummary(c.drill, null, { attemptDate: "2026-11-20" });
  assert.equal(summary.score, c.expected.score);
  assert.equal(summary.maxScore, c.expected.maxScore);
  assert.equal(summary.accuracyPct, c.expected.accuracyPct);
  assert.equal(summary.practiceStatus, c.expected.practiceStatus);
  assert.equal(summary.skippedCount, c.expected.skippedCount);
}

console.log(
  `sessionSummaryParity tests passed (${fixture.coveredUnitsCases.length} covered-unit + ${fixture.summaryCases.length} summary cases)`
);
