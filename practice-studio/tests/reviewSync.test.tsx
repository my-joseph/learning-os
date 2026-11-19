import assert from "node:assert/strict";
import React from "react";
import { NextRequest } from "next/server";
import { renderToStaticMarkup } from "react-dom/server";
import { POST as syncNotionPost } from "../src/app/api/sync-notion/route";
import { ReviewPanel } from "../src/components/shell/ReviewPanel";
import { executeNotionSync } from "../src/hooks/useProgressSync";
import { setNotionDrillSyncSpawnerForTests } from "../src/lib/notionSyncRunner";
import { buildSessionSummary, buildSyncPayload, getPersistedStatusOverride, summaryFingerprint } from "../src/lib/sessionSummary";
import {
  formatChoiceAnswerLabel,
  findNextDrill,
  getDefaultExpandedRowIds,
  lastAnswerText,
  latestReviewVerdict,
  matchedTraps,
  normaliseTestReport,
  shortRowTitle,
  verifiedAnswerLabel,
} from "../src/lib/reviewRow";
import type { DrillDocument, Problem, ProblemState } from "../src/types/drill";

const noop = () => {};
const baseState = (): ProblemState => ({ userInput: "", score: null, divergedStep: null, mistakes: [] });

const makeProblem = (id: string, state?: ProblemState): Problem => ({
  id,
  templateKey: "review-sync-test",
  level: 1,
  levelLabel: "Level 1",
  category: "Complex Numbers",
  context: "Multiplying phasors",
  prompt: "Find the product $$(2+3i)(4-2i)$$.",
  answerPlain: "14+8i",
  answerDisplay: "14 + 8i",
  checkpointHint: "Expand each term.",
  answerSpec: { type: "text" },
  steps: [{ explain: "Distribute each term." }],
  state: state || baseState(),
});

const mathDrill: DrillDocument = {
  schemaVersion: "2.0",
  drillId: "DRL-MTH-T02-C01-U01-04",
  subject: "MATH",
  unitCode: "MTH-T02-C01-U01",
  unitTitle: "Complex Numbers",
  chapterCode: "MTH-T02-C01",
  topicCode: "MTH-T02",
  unitNotionUrl: null,
  createdAt: "2026-11-19T00:00:00Z",
  config: { questionCount: 3, difficulty: "Mixed", difficultyMode: "Mixed" },
  mistakeTags: [{ id: "positive-last-term", name: "Positive last term", label: "Positive last term", autoFrom: [] }],
  problems: [
    makeProblem("Q01", {
      ...baseState(), score: 0, userInput: "2+16i",
      attempts: [
        { input: "2+16i", ts: "2026-11-19T00:00:00Z", verdict: "incorrect", matchedTrap: "positive-last-term" },
        { input: "2+16i", ts: "2026-11-19T00:01:00Z", verdict: "incorrect" },
      ], mistakes: ["positive-last-term"], mistakeNote: "Check the final product.", divergedStep: 0,
    }),
    makeProblem("Q02", {
      ...baseState(), score: 0.5, userInput: "14+8i", hintsRevealed: 2,
      attempts: [{ input: "14+8i", ts: "2026-11-19T00:02:00Z", verdict: "correct" }],
    }),
    makeProblem("Q03"),
  ],
  sessionSummary: {
    practiceStatus: "Needs Retry", score: 0.5, maxScore: 3, accuracyPct: 16.7,
    skippedCount: 0, skippedProblems: [], mistakeCategories: [], divergedStepsSummary: "", attemptDate: null,
  },
  localFilePath: "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-04.json",
};

function render(drill: DrillDocument, overrides: Record<string, unknown> = {}): string {
  return renderToStaticMarkup(
    <ReviewPanel
      currentDrill={drill}
      statusOverride={null}
      isSyncing={false}
      onStatusOverrideChange={noop}
      onBackToQuiz={noop}
      onConfirmSync={noop}
      onSelectQuestion={noop}
      onSetScore={noop}
      onToggleMistakeTag={noop}
      onMistakeNoteChange={noop}
      onRevisitNoteChange={noop}
      {...overrides}
    />
  );
}

/** The payload construction from the pre-redesign confirmSyncToNotion implementation. */
function oldInlinePayload(drill: DrillDocument, statusOverride: "Graded" | "Needs Retry" | null) {
  const liveScore = drill.problems.reduce((acc, p) => acc + (p.state?.score || 0), 0);
  const maxScore = drill.problems.length || 0;
  const accuracyPct = maxScore > 0 ? Math.round((liveScore / maxScore) * 1000) / 10 : 0;
  const computedPracticeStatus = statusOverride || (maxScore > 0 && liveScore / maxScore >= 0.8 ? "Graded" : "Needs Retry");
  const tagMap = new Map((drill.mistakeTags || []).map((t) => [t.id, t.name]));
  const mistakeNames = new Set<string>();
  const divergedList: string[] = [];
  const skippedProblems: string[] = [];
  drill.problems.forEach((p) => {
    const parts: string[] = [];
    if (p.state?.skipped) {
      skippedProblems.push(`${p.id} (${p.context || p.category})`);
      parts.push("SKIPPED - Concept Gap");
    }
    (p.state?.mistakes || []).forEach((tid) => {
      const rawName = tagMap.get(tid) || tid;
      mistakeNames.add(rawName.replace(/,/g, " /").trim());
    });
    if (typeof p.state?.divergedStep === "number") {
      const st = p.steps?.[p.state.divergedStep];
      parts.push(`Step ${p.state.divergedStep + 1}: ${st ? st.explain : "Diverged"}`);
    } else if (p.state?.score !== null && p.state?.score !== undefined && p.state.score < 1 &&
      (p.state?.mistakes || []).length > 0 && !p.state?.skipped) {
      parts.push((p.state?.mistakes || []).map((t) => tagMap.get(t) || t).join(", "));
    }
    if (p.state?.mistakeNote && p.state.mistakeNote.trim()) parts.push(`Note: ${p.state.mistakeNote.trim()}`);
    if (parts.length > 0) divergedList.push(`${p.id} (${parts.join(" · ")})`);
  });
  return {
    ...drill,
    sessionSummary: {
      practiceStatus: computedPracticeStatus,
      score: liveScore,
      maxScore,
      accuracyPct,
      skippedCount: skippedProblems.length,
      skippedProblems,
      mistakeCategories: Array.from(mistakeNames),
      divergedStepsSummary: divergedList.length > 0 ? divergedList.join(" | ") : "No diverged steps logged.",
      attemptDate: "2026-11-19",
    },
  };
}

// Payload parity across math, PRG, lab-shaped, and skipped-item fixtures.
const prgDrill = { ...mathDrill, drillId: "DRL-PRG-T01-C03-U05-01", subject: "PRG" as const,
  problems: [makeProblem("Q01", { ...baseState(), score: 1, reviews: [{ at: "2026-11-19T00:00:00Z", attempt: 1, codeHash: "sha256:test", code: "", tests: { passed: 3, total: 3, failed: [] }, lint: [], typecheck: [], findings: [], verdict: "pass", explain: null }] })] };
const labDrill = { ...prgDrill, drillId: "LAB-PRG-T01-C02-01", problems: [makeProblem("M1", {
  ...baseState(), score: 1, lastTestReport: { allPassed: true, score: 1, passedCount: 3, totalCount: 3, visibleResults: [], hiddenPassed: 1, hiddenTotal: 1, executionTimeMs: 2 },
})] };
const skippedDrill = { ...mathDrill, problems: [makeProblem("Q01", { ...baseState(), skipped: true, score: 0 })] };
for (const [label, fixture] of [["math", mathDrill], ["PRG", prgDrill], ["lab", labDrill], ["skipped", skippedDrill]] as const) {
  const actual = JSON.stringify(buildSyncPayload(fixture, null, { attemptDate: "2026-11-19" }));
  const expected = JSON.stringify(oldInlinePayload(fixture, null));
  assert.equal(actual, expected, `${label} payload must stay byte-identical to the old builder`);
}
assert.equal(buildSessionSummary(skippedDrill, null, { attemptDate: "2026-11-19" }).skippedCount, 1);
assert.equal(summaryFingerprint({ ...buildSessionSummary(mathDrill), attemptDate: "old", syncedToNotionAt: "x" }),
  summaryFingerprint({ ...buildSessionSummary(mathDrill), attemptDate: "new", syncedToNotionAt: "y" }));
assert.equal(lastAnswerText(mathDrill.problems[0]), "2+16i", "the final substantive attempt is shown");
assert.deepEqual(matchedTraps(mathDrill.problems[0].state), ["positive-last-term"]);
assert.equal(normaliseTestReport({ passed: 2, total: 4 }).passed, 2);
assert.equal(normaliseTestReport({ passedCount: 3, totalCount: 4 }).total, 4);
assert.equal(latestReviewVerdict({ ...baseState(), reviews: [{ verdict: "changes", findings: [] }] } as unknown as ProblemState).status, "revise");
assert.equal(formatChoiceAnswerLabel({ ...makeProblem("Q01"), prompt: "Line 1: parse logs\nLine 2: write report",
  answerSpec: { type: "choice", options: [{ id: "B", label: "Second line" }] } }, "B"), "Second line");
const lineChoiceProblem = { ...makeProblem("Q01"), prompt: "Choose the correct step:\nLine 1: Add terms\nLine 2: Combine terms\nLine 3: Simplify result",
  answerPlain: "step-c",
  answerSpec: { type: "choice" as const, correct: "step-c", options: [{ id: "step-a", label: "Line 1" }, { id: "step-b", label: "Line 2" }, { id: "step-c", label: "Line 3" }] },
  state: { ...baseState(), userInput: "step-c", attempts: [{ input: "step-c", ts: "2026-11-19T00:00:00Z", verdict: "incorrect" }] } };
assert.equal(lastAnswerText(lineChoiceProblem), "Line 3", "choice IDs display their option labels");
assert.equal(formatChoiceAnswerLabel(lineChoiceProblem, "step-b"), "Line 2", "line-choice option IDs map to their visible label");
assert.equal(formatChoiceAnswerLabel(lineChoiceProblem, "unmatched-id"), "unmatched-id", "unknown inputs remain raw");
assert.equal(verifiedAnswerLabel(lineChoiceProblem), "Line 3", "verified choice answers stay label-based");
assert.equal(shortRowTitle(makeProblem("Q01")), "Find the product $$(2+3i)(4-2i)$$.", "row title uses the prompt's first line");
const attentionItems = ["Q01", "Q02", "Q03"].map((id, index) => ({ problem: makeProblem(id), index, outcome: "wrong" as const }));
assert.deepEqual(Object.keys(getDefaultExpandedRowIds(attentionItems)), ["Q01", "Q02", "Q03"], "all rows expand when To review has three items");
assert.deepEqual(getDefaultExpandedRowIds([...attentionItems, { problem: makeProblem("Q04"), index: 3, outcome: "unanswered" as const }]), {}, "rows collapse when To review has more than three items");
const nextDrill = findNextDrill(mathDrill, [{ drillId: "DRL-MTH-T02-C01-U01-04", unitCode: mathDrill.unitCode, unitTitle: "Complex Numbers", chapterCode: mathDrill.chapterCode, createdAt: "2026-11-19", questionCount: 4, difficultyMode: "Mixed" }, { drillId: "DRL-MTH-T02-C01-U01-03", unitCode: mathDrill.unitCode, unitTitle: "Complex Numbers", chapterCode: mathDrill.chapterCode, createdAt: "2026-11-18", questionCount: 4, difficultyMode: "Mixed" }]);
assert.equal(nextDrill?.drillId, "DRL-MTH-T02-C01-U01-03", "next drill excludes the current drill");
assert.equal(nextDrill?.title, "Complex Numbers · Set 3", "next drill names its unit and set");
assert.notEqual(nextDrill?.href, "/math/DRL-MTH-T02-C01-U01-04", "next drill never links to the current drill");

// Sync state and metadata stamping: only a real successful response stamps.
const reply = (data: unknown, ok = true) => new Response(JSON.stringify(data), { status: ok ? 200 : 500 });
async function verifyStamping() {
  let syncPostBody: string | null = null;
  let savePostBody: string | null = null;
  const successful = await executeNotionSync({
    currentDrill: mathDrill, statusOverride: null, nowIso: "2026-11-19T10:00:00.000Z",
    attemptDate: "2026-11-19",
    fetchFn: async (input, init) => {
      const url = String(input);
      if (url === "/api/sync-notion") {
        syncPostBody = String(init?.body || "");
        return reply({ ok: true, drillPageId: "real-page-id", unitReviews: { "MTH-T02-C01-U01": { mastery: 2, lastReviewed: "2026-11-19", nextReview: "2026-11-22" } } });
      }
      savePostBody = String(init?.body || "");
      return reply({ ok: true });
    },
  });
  assert.equal(syncPostBody, JSON.stringify(buildSyncPayload(mathDrill, null, { attemptDate: "2026-11-19" })));
  assert.ok(savePostBody);
  const savedDoc = JSON.parse(savePostBody || "{}") as DrillDocument;
  assert.equal(savedDoc.sessionSummary.syncedToNotionAt, "2026-11-19T10:00:00.000Z");
  assert.equal(successful.syncState.phase, "synced");
  assert.equal(successful.stampedDoc?.sessionSummary.syncedToNotionAt, "2026-11-19T10:00:00.000Z");
  assert.equal(successful.stampedDoc?.sessionSummary.notionPageId, "real-page-id");
  assert.ok(successful.stampedDoc?.sessionSummary.syncedFingerprint);

  const scenarios: Array<[string, (url: RequestInfo | URL, init?: RequestInit) => Promise<Response>, boolean, boolean?]> = [
    ["degraded", async () => reply({ ok: true, degraded: true, warning: "missing token" }), false],
    ["dryRun", async () => reply({ ok: true, dryRun: true }), false],
    ["pilotSkipped", async () => reply({ ok: true, pilotSkipped: true }), false, true],
    ["ok:false", async () => reply({ ok: false, error: "failed" }, false), false],
    ["thrown fetch", async () => { throw new Error("network down"); }, false],
  ];
  for (const [label, fetchFn, shouldStamp] of scenarios) {
    const result = await executeNotionSync({ currentDrill: mathDrill, statusOverride: null, fetchFn });
    assert.equal(Boolean(result.stampedDoc), shouldStamp, `${label} must not stamp sync metadata`);
  }
}
async function runAsyncTests() {
await verifyStamping();

// The lab endpoint must reject the lab id before invoking the Python drill sync runner.
let spawned = false;
setNotionDrillSyncSpawnerForTests(async () => { spawned = true; return { code: 0, stdout: "{}", stderr: "" }; });
const labResponse = await syncNotionPost(new NextRequest("http://localhost/api/sync-notion", {
  method: "POST", body: JSON.stringify({ drillId: "LAB-PRG-T01-C02-01", unitCode: "PRG-T01-C02" }),
  headers: { "content-type": "application/json" },
}));
assert.equal(labResponse.status, 400);
assert.equal(spawned, false, "lab submit must never call the drill sync runner");
setNotionDrillSyncSpawnerForTests(null);

// State render coverage, zero-leak assertions, and PRG/lab variants.
const idleHtml = render(mathDrill, { initialExpandedIds: ["Q01", "Q02", "Q03"] });
assert.match(idleHtml, /Not synced yet/);
assert.match(idleHtml, /Level 1/, "the question level remains a secondary row label");
assert.match(idleHtml, /Your answer:/);
assert.match(idleHtml, /2\+16i/);
assert.match(idleHtml, /Trap:.*Positive last term/);
assert.match(idleHtml, /Correct after 2 hints/);
assert.match(idleHtml, /Not tried yet/);
assert.doesNotMatch(idleHtml, /Verified answer:.*14 \+ 8i/, "unanswered row must not reveal the verified answer");
assert.doesNotMatch(idleHtml, /aria-label="Set Q3 score to/);
assert.doesNotMatch(idleHtml, /Note for Q3/);
const revisitNoteDrill = {
  ...mathDrill,
  problems: mathDrill.problems.map((problem, index) =>
    index === 0
      ? { ...problem, state: { ...problem.state!, revisitNote: "Check the final product." } }
      : problem
  ),
};
const revisitPayload = buildSyncPayload(revisitNoteDrill, null, { attemptDate: "2026-11-19" });
assert.equal(revisitPayload.problems[0].state?.revisitNote, "Check the final product.");
assert.equal("revisitNote" in revisitPayload.sessionSummary, false);

const overriddenSummary = buildSessionSummary(mathDrill, "Graded", { attemptDate: "2026-11-19" });
assert.equal(overriddenSummary.statusOverride, "Graded");
assert.equal(getPersistedStatusOverride(overriddenSummary), "Graded");
assert.equal(getPersistedStatusOverride({ ...overriddenSummary, statusOverride: "Needs Retry" }), "Needs Retry");
assert.equal(getPersistedStatusOverride({ ...overriddenSummary, statusOverride: null }), null);

const untouched = { ...mathDrill, problems: [makeProblem("Q01"), makeProblem("Q02")] };
const untouchedHtml = render(untouched);
assert.match(untouchedHtml, /Nothing answered yet/);
assert.match(untouchedHtml, /Nothing to sync yet — answer at least one question/);
assert.match(untouchedHtml, /Start Q1/);
assert.match(untouchedHtml, /disabled=""/);
assert.doesNotMatch(untouchedHtml, /0 \/ 2 points/);
assert.doesNotMatch(untouchedHtml, /No mistakes logged/);
assert.doesNotMatch(untouchedHtml, /Mark as graded/);
assert.doesNotMatch(untouchedHtml, /They are sent as not tried/);

for (const [state, expected] of [
  [{ phase: "syncing" }, /Syncing…/],
  [{ phase: "degraded", message: "missing token" }, /Saved locally/],
  [{ phase: "error", message: "sync failed" }, /Couldn&#x27;t sync/],
  [{ phase: "offline", message: "You're offline." }, /You&#x27;re offline/],
  [{ phase: "dryRun", isPilot: true, message: "Pilot mode: nothing was written to Notion." }, /Pilot mode: nothing was written to Notion/],
] as const) {
  assert.match(render(mathDrill, { syncState: state, isSyncing: state.phase === "syncing" }), expected);
}

const syncedFingerprint = summaryFingerprint(buildSessionSummary(mathDrill));
const syncedDrill = { ...mathDrill, sessionSummary: { ...mathDrill.sessionSummary,
  syncedToNotionAt: "2026-11-19T10:00:00.000Z", syncedFingerprint } };
assert.match(render(syncedDrill, { syncState: { phase: "synced", at: "2026-11-19T10:00:00.000Z" } }), /Synced to Notion/);
const changedSinceSync = { ...syncedDrill, problems: syncedDrill.problems.map((problem, i) =>
  i === 0 ? { ...problem, state: { ...problem.state, mistakeNote: "Updated after sync" } } : problem) };
assert.match(render(changedSinceSync), /You changed/);

const allCorrect = { ...mathDrill, problems: [makeProblem("Q01", { ...baseState(), score: 1,
  attempts: [{ input: "14+8i", ts: "2026-11-19T00:00:00Z", verdict: "correct" }] })] };
assert.match(render(allCorrect), /right on the first try/);
assert.match(render(allCorrect), /Nothing to fix/);
assert.match(render(allCorrect), /1 \/ 1 points/);
assert.match(render(mathDrill), /0\.5 \/ 3 points/);
assert.match(render(mathDrill), /0\.5 \/ 3 points/);
const pointsHtml = render(mathDrill);
assert.ok((pointsHtml.match(/0\.5 \/ 3/g) || []).length >= 2,
  "summary and sync card use the same points figure");
assert.match(pointsHtml, /1 of 3 right/, "right-answer count is secondary to the shared points figure");
const manyWrong = { ...mathDrill, problems: ["Q01", "Q02", "Q03", "Q04"].map((id) =>
  makeProblem(id, { ...baseState(), score: 0, userInput: "wrong", attempts: [{ input: "wrong", ts: "2026-11-19T00:00:00Z", verdict: "incorrect", matchedTrap: "positive-last-term" }] })) };
const manyWrongHtml = render(manyWrong);
assert.match(manyWrongHtml, /Same trap/);
assert.match(manyWrongHtml, /aria-expanded="false"/);
const weakSpotHtml = render(mathDrill, {
  dueReviewCount: 0,
  weakSpotUnits: [{ unitCode: mathDrill.unitCode, unitTitle: mathDrill.unitTitle, subject: "MTH", itemCount: 2, drillCount: 1, open: [{ id: "positive-last-term", name: "Positive last term", matches: 2, drills: 1, last: "2026-11-19", subject: "MTH" }], closed: [], levels: {}, assistedCount: 0, skipped: [] }],
  workspaceDrills: [{ drillId: "DRL-MTH-T02-C01-U01-03", unitCode: mathDrill.unitCode, unitTitle: "Complex Numbers", chapterCode: mathDrill.chapterCode, createdAt: "2026-11-18", questionCount: 4, difficultyMode: "Mixed" }],
  onTrySimilarQuestion: noop,
});
assert.match(weakSpotHtml, /href="\/review\?trap=positive-last-term"/);
assert.match(weakSpotHtml, /Practise Positive last term/);
assert.doesNotMatch(weakSpotHtml, /Practise positive-last-term/);
assert.match(weakSpotHtml, /Next drill: Complex Numbers · Set 3/);
assert.match(weakSpotHtml, /id="review-row-Q01" class="[^"]*"><button[^>]*aria-expanded="true"/,
  "To review rows start expanded when there are three items");
const prgWeakSpotHtml = render({ ...prgDrill, problems: [makeProblem("Q01", {
  ...baseState(), score: 0, attempts: [{ input: "wrong", ts: "2026-11-19T00:00:00Z", verdict: "incorrect" }],
})] }, {
  dueReviewCount: 0,
  weakSpotUnits: [{ unitCode: "PRG-T01-C03-U05", unitTitle: "Naming", subject: "PRG", itemCount: 1,
    drillCount: 1, open: [{ id: "QC-NAMING", name: "QC-NAMING", matches: 1, drills: 1,
      last: "2026-11-19", subject: "PRG" }], closed: [], levels: {}, assistedCount: 0, skipped: [] }],
});
assert.match(prgWeakSpotHtml, /href="\/review\?trap=QC-NAMING"/);
assert.match(prgWeakSpotHtml, /Practise QC naming/);
assert.doesNotMatch(prgWeakSpotHtml, /Practise QC-NAMING/);
const similarRowHtml = render({ ...mathDrill, problems: [{ ...mathDrill.problems[0], hasVariants: true }] }, { initialExpandedIds: ["Q01"], onTrySimilarQuestion: noop });
assert.match(similarRowHtml, /Try a similar question/);
assert.match(similarRowHtml, /min-h-\[44px\]/, "row text actions have mobile tap targets");
assert.match(weakSpotHtml, /min-h-\[44px\]/, "What next links have mobile tap targets");

const lineChoiceHtml = render({ ...mathDrill, problems: [{ ...lineChoiceProblem, state: {
  ...baseState(), userInput: "step-c", score: 0,
  attempts: [{ input: "step-c", ts: "2026-11-19T00:00:00Z", verdict: "incorrect" }],
} }] }, { initialExpandedIds: ["Q01"] });
assert.match(lineChoiceHtml, /Your answer: <\/span><span[^>]*><span[^>]*>Line 3/,
  "choice answer display resolves an option ID to the learner-facing label");

const prgHtml = render({ ...prgDrill, problems: [makeProblem("Q01", { ...baseState(), score: 0,
  lastTestReport: { allPassed: false, score: 0.5, passedCount: 2, totalCount: 4, visibleResults: [], hiddenPassed: 0, hiddenTotal: 0, executionTimeMs: 2 },
  reviews: [{ at: "2026-11-19T00:00:00Z", attempt: 1, codeHash: "sha256:test", code: "", tests: { passed: 2, total: 4, failed: [] }, lint: [], typecheck: [], findings: [{ check: "QC-ERRORS", severity: "must", line: 1, note: "Use a typed error." }], verdict: "revise", explain: null }] })] },
  { initialExpandedIds: ["Q01"] });
assert.doesNotMatch(prgHtml, /undefined/);
assert.doesNotMatch(prgHtml, /Set Q1 score to/);
assert.match(prgHtml, /Tests 2\/4/);
assert.match(prgHtml, /QC-ERRORS/);
assert.doesNotMatch(prgHtml, /SECRET_SOLUTION_CODE/);
const labHtml = render({ ...labDrill, problems: [makeProblem("M1")] });
assert.match(labHtml, /Submit lab/);
assert.match(labHtml, /Copy submit command/);
assert.match(labHtml, /Start M1/);
assert.doesNotMatch(labHtml, /Sync to Notion/);

console.log("reviewSync tests passed");
}

void runAsyncTests();
