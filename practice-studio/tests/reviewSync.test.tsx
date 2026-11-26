import assert from "node:assert/strict";
import React from "react";
import { NextRequest } from "next/server";
import { renderToStaticMarkup } from "react-dom/server";
import { POST as syncNotionPost } from "../src/app/api/sync-notion/route";
import { ReviewSyncPage } from "../src/components/review-sync/ReviewSyncPage";
import { LabReviewPage } from "../src/components/review-sync/LabReviewPage";
import { NextActions } from "../src/components/review-sync/NextActions";
import { executeNotionSync, mergeSyncStampIntoLatestDrill } from "../src/hooks/useProgressSync";
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
import type { ReviewSyncPageProps } from "../src/components/review-sync/ReviewSyncPage";
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

function render(drill: DrillDocument, overrides: Partial<ReviewSyncPageProps> = {}): string {
  return renderToStaticMarkup(
    <ReviewSyncPage
      currentDrill={drill}
      statusOverride={null}
      isSyncing={false}
      onBackToQuiz={noop}
      onConfirmSync={noop}
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
  ...baseState(), score: 1,
  lastTestReport: { allPassed: true, score: 1, passedCount: 3, totalCount: 3, visibleResults: [], hiddenPassed: 1, hiddenTotal: 1, executionTimeMs: 2 },
  reviews: [{ at: "2026-11-19T00:00:00Z", attempt: 1, codeHash: "sha256:lab", code: "", tests: { passed: 3, total: 3, failed: [] }, lint: [], typecheck: [], findings: [], verdict: "pass", explain: null }],
})] };
const labAwaitingReviewDrill = { ...prgDrill, drillId: "LAB-PRG-T01-C02-01", problems: [makeProblem("M1", {
  ...baseState(), score: null,
  lastTestReport: { allPassed: true, score: 1, passedCount: 3, totalCount: 3, visibleResults: [], hiddenPassed: 1, hiddenTotal: 1, executionTimeMs: 2 },
})] };
assert.equal(buildSessionSummary(labAwaitingReviewDrill, null, { attemptDate: "2026-11-19" }).score, 0, "lab with passing tests but no review must not score 1");
const skippedDrill = { ...mathDrill, problems: [makeProblem("Q01", { ...baseState(), skipped: true, score: 0 })] };
for (const [label, fixture] of [["math", mathDrill], ["PRG", prgDrill], ["lab", labDrill]] as const) {
  const actual = JSON.stringify(buildSyncPayload(fixture, null, { attemptDate: "2026-11-19" }));
  const expected = JSON.stringify(oldInlinePayload(fixture, null));
  assert.equal(actual, expected, `${label} payload must stay byte-identical to the old builder`);
}
const skippedSummary = buildSessionSummary(skippedDrill, null, { attemptDate: "2026-11-19" });
assert.equal(skippedSummary.skippedCount, 1);
assert.deepEqual(skippedSummary.skippedProblems, ["Q01 (Complex Numbers)"]);
const partialDrill = {
  ...mathDrill,
  problems: [
    ...mathDrill.problems,
    {
      ...makeProblem("Q02", { ...baseState(), divergedStep: 0 }),
      steps: [{ latex: "fixture", explain: "Unattempted fixture step" }],
    },
  ],
};
assert.doesNotMatch(buildSessionSummary(partialDrill).divergedStepsSummary, /Unattempted fixture step/);
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
const noNextDrillActionsHtml = renderToStaticMarkup(
  <NextActions
    dueReviewCount={0}
    topWeakSpot={null}
    firstWrong={null}
    nextDrill={null}
    primary={false}
  />
);
assert.equal(noNextDrillActionsHtml, "", "no next-drill action leaves the What next slot empty");
const otherActionWithoutNextDrillHtml = renderToStaticMarkup(
  <NextActions
    dueReviewCount={2}
    topWeakSpot={null}
    firstWrong={null}
    nextDrill={null}
    primary={false}
  />
);
assert.match(otherActionWithoutNextDrillHtml, /Daily review/);
assert.doesNotMatch(otherActionWithoutNextDrillHtml, /Next drill|Generate a drill/,
  "other next actions remain when there is no next drill");

// Sync state and metadata adoption: server is the source of truth; client only adopts stamps on real success.
const reply = (data: unknown, ok = true, status?: number) =>
  new Response(JSON.stringify(data), { status: status ?? (ok ? 200 : 500) });
async function verifyStamping() {
  let syncPostBody: string | null = null;
  let saveStateCalled = false;
  const expectedFp = summaryFingerprint(buildSessionSummary(mathDrill, null, { attemptDate: "2026-11-19" }));
  const successful = await executeNotionSync({
    currentDrill: mathDrill, statusOverride: null, nowIso: "2026-11-19T09:00:00.000Z",
    attemptDate: "2026-11-19",
    fetchFn: async (input, init) => {
      const url = String(input);
      if (url === "/api/sync-notion") {
        syncPostBody = String(init?.body || "");
        return reply({
          ok: true,
          drillPageId: "real-page-id",
          notionPageId: "real-page-id",
          syncedToNotionAt: "2026-11-19T10:00:00.000Z",
          syncedFingerprint: expectedFp,
          unitReviews: { "MTH-T02-C01-U01": { mastery: 2, lastReviewed: "2026-11-19", nextReview: "2026-11-22" } },
        });
      }
      saveStateCalled = true;
      return reply({ ok: true });
    },
  });
  assert.equal(syncPostBody, JSON.stringify(buildSyncPayload(mathDrill, null, { attemptDate: "2026-11-19" })));
  assert.equal(saveStateCalled, false, "client must adopt server-persisted stamps without a second /api/save-state POST");
  assert.equal(successful.syncState.phase, "synced");
  assert.equal(successful.syncState.at, "2026-11-19T10:00:00.000Z");
  assert.equal(successful.stampedDoc?.sessionSummary.syncedToNotionAt, "2026-11-19T10:00:00.000Z");
  assert.equal(successful.stampedDoc?.sessionSummary.notionPageId, "real-page-id");
  assert.equal(successful.stampedDoc?.sessionSummary.syncedFingerprint, expectedFp);

  const scenarios: Array<[string, (url: RequestInfo | URL, init?: RequestInit) => Promise<Response>, boolean, boolean?]> = [
    ["degraded", async () => reply({ ok: true, degraded: true, warning: "missing token" }), false],
    ["dryRun", async () => reply({ ok: true, dryRun: true }), false],
    ["pilotSkipped", async () => reply({ ok: true, pilotSkipped: true }), false, true],
    ["ok:false", async () => reply({ ok: false, error: "failed" }, false), false],
    ["server 504 timeout", async () => reply({ ok: false, timedOut: true, error: "Notion sync timed out after 90s." }, false, 504), false],
    ["thrown fetch", async () => { throw new Error("network down"); }, false],
  ];
  for (const [label, fetchFn, shouldStamp] of scenarios) {
    const result = await executeNotionSync({ currentDrill: mathDrill, statusOverride: null, fetchFn });
    assert.equal(Boolean(result.stampedDoc), shouldStamp, `${label} must not stamp sync metadata`);
  }

  const partial = await executeNotionSync({
    currentDrill: mathDrill,
    statusOverride: null,
    fetchFn: async () => reply({ ok: false, partial: true, failedSteps: ["mistakeLog", "unitReview:MTH-T01-C01-U01"] }),
  });
  assert.equal(partial.syncState.phase, "partial");
  assert.equal(partial.toast?.type, "warn");
  assert.equal(partial.stampedDoc, null);
  const partialHtml = render(mathDrill, { syncState: partial.syncState });
  assert.match(partialHtml, /Synced with problems/);
  assert.match(partialHtml, /Mistake Log/);
  assert.match(partialHtml, /Unit review \(MTH-T01-C01-U01\)/);
  assert.match(partialHtml, />Retry<\/button>/);
  assert.doesNotMatch(partialHtml, /Synced to Notion/);

  // Hang path: a fetch that never settles aborts and enters error phase with Retry enabled
  let abortSignalAborted = false;
  const hungResult = await executeNotionSync({
    currentDrill: mathDrill,
    statusOverride: null,
    timeoutMs: 30,
    fetchFn: async (_input, init) =>
      new Promise<Response>(() => {
        init?.signal?.addEventListener("abort", () => {
          abortSignalAborted = true;
        });
      }),
  });
  assert.equal(abortSignalAborted, true, "client timeout must abort the in-flight sync fetch");
  assert.equal(hungResult.syncState.phase, "error", "hung sync must transition to error phase");
  assert.match(hungResult.syncState.message || "", /timed out/i);
  assert.equal(hungResult.stampedDoc, null, "timed out sync must not stamp");
  const timeoutErrorHtml = render(mathDrill, { syncState: hungResult.syncState, isSyncing: false });
  assert.match(timeoutErrorHtml, /Couldn’t sync/);
  const retryLabelIndex = timeoutErrorHtml.indexOf(">Retry</button>");
  const retryButtonStart = timeoutErrorHtml.lastIndexOf("<button", retryLabelIndex);
  const retryButtonEnd = timeoutErrorHtml.indexOf(">", retryButtonStart);
  assert.ok(
    retryLabelIndex >= 0 && retryButtonStart >= 0 && retryButtonEnd > retryButtonStart,
    "Retry button must render after timeout"
  );
  assert.doesNotMatch(timeoutErrorHtml.slice(retryButtonStart, retryButtonEnd), /\sdisabled(?:=|\s|>)/, "Retry button must be enabled after timeout");

  // Merge server stamps into LATEST drill doc without rolling back mid-sync edits (review_sync C2)
  let latestDrill: DrillDocument | null = mathDrill;
  const mergedResult = await executeNotionSync({
    currentDrill: mathDrill,
    statusOverride: null,
    nowIso: "2026-11-20T01:00:00.000Z",
    attemptDate: "2026-11-20",
    getLatestDrill: () => latestDrill,
    fetchFn: async (input) => {
      assert.equal(String(input), "/api/sync-notion");
      // Simulate an edit arriving while /api/sync-notion is in flight
      latestDrill = {
        ...mathDrill,
        problems: mathDrill.problems.map((p, idx) =>
          idx === 0
            ? { ...p, state: { ...p.state, mistakeNote: "Edited while sync ran", revisitNote: "Check sign" } }
            : p
        ),
      };
      return reply({
        ok: true,
        drillPageId: "page-merged-1",
        notionPageId: "page-merged-1",
        syncedToNotionAt: "2026-11-20T01:00:00.000Z",
        syncedFingerprint: expectedFp,
      });
    },
  });
  assert.equal(mergedResult.ignored, undefined);
  assert.ok(mergedResult.stampedDoc);
  assert.equal(
    mergedResult.stampedDoc.problems[0].state.mistakeNote,
    "Edited while sync ran",
    "sync stamp must merge into latest doc without rolling back mid-sync edits"
  );
  assert.equal(
    mergedResult.stampedDoc.problems[0].state.revisitNote,
    "Check sign",
    "mid-sync revisitNote must be preserved after sync completes"
  );
  assert.equal(mergedResult.stampedDoc.sessionSummary.syncedToNotionAt, "2026-11-20T01:00:00.000Z");

  // Ignore sync result when the learner switches drills mid-sync (review_sync C2)
  const otherDrill: DrillDocument = { ...mathDrill, drillId: "DRL-MTH-OTHER-99" };
  let activeDrillDuringSwitch: DrillDocument | null = mathDrill;
  const switchedResult = await executeNotionSync({
    currentDrill: mathDrill,
    statusOverride: null,
    nowIso: "2026-11-20T01:05:00.000Z",
    getLatestDrill: () => activeDrillDuringSwitch,
    fetchFn: async () => {
      activeDrillDuringSwitch = otherDrill;
      return reply({
        ok: true,
        drillPageId: "page-switched-1",
        notionPageId: "page-switched-1",
        syncedToNotionAt: "2026-11-20T01:05:00.000Z",
        syncedFingerprint: expectedFp,
      });
    },
  });
  assert.equal(switchedResult.ignored, true, "sync result must be marked ignored when drill switched");
  assert.equal(switchedResult.stampedDoc, null, "switched drill must not produce a stampedDoc");
  assert.equal(
    mergeSyncStampIntoLatestDrill(otherDrill, mathDrill.drillId, mergedResult.stampedDoc.sessionSummary),
    null,
    "mergeSyncStampIntoLatestDrill returns null on drillId mismatch"
  );
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

// The card only includes score, outcome totals, and sync feedback.
const idleHtml = render(mathDrill);
assert.match(idleHtml, /<h2[^>]*>Keep practising<\/h2>/);
assert.match(idleHtml, />16\.7%<\/span>/);
assert.match(idleHtml, /0 of 3 correct · 1 with help · 1 wrong · 1 skipped \/ not tried/);
assert.match(idleHtml, /Sync to update mastery and schedule/);
assert.doesNotMatch(idleHtml, /To review|Got right|What next|Self-score|Positive last term|Check the final product/);
assert.doesNotMatch(idleHtml, /Find the product|2\+16i|14\s*\+\s*8i|Expand each term|Distribute each term/);
assert.deepEqual([...idleHtml.matchAll(/<button[^>]*>([^<]+)<\/button>/g)].map((match) => match[1]), ["Back", "Sync"]);

const scoreDrill = (correct: number, assisted: number, wrong: number, skipped: number, total = 10) => ({
  ...mathDrill,
  problems: Array.from({ length: total }, (_, index) => {
    const id = `Q${index + 1}`;
    if (index >= correct + assisted + wrong) {
      return makeProblem(id, index < correct + assisted + wrong + skipped
        ? { ...baseState(), skipped: true } : undefined);
    }
    return makeProblem(id, {
      ...baseState(),
      hintsRevealed: index >= correct && index < correct + assisted ? 1 : 0,
      attempts: [{ input: "fixture", ts: "2026-11-19T00:00:00Z", verdict: index < correct + assisted ? "correct" : "incorrect" }],
    });
  }),
});

for (const [correct, assisted, wrong, skipped, score, headline] of [
  [9, 0, 1, 0, 90, "Great work!"],
  [7, 2, 1, 0, 80, "Great work!"],
  [7, 1, 1, 1, 75, "Good progress"],
  [4, 2, 2, 1, 50, "Good progress"],
  [4, 1, 3, 0, 45, "Keep practising"],
] as const) {
  const card = render(scoreDrill(correct, assisted, wrong, skipped));
  assert.ok(card.includes(`Score ${score}%. Correct ${correct}, Correct with help ${assisted}, Wrong ${wrong}, Skipped / not tried ${10 - correct - assisted - wrong}.`));
  assert.ok(card.includes(`>${score}%</span>`));
  assert.ok(card.includes(`>${headline}</h2>`));
  const counts = [...card.matchAll(/<td>(\d+)<\/td>/g)].map((match) => Number(match[1]));
  assert.equal(counts.reduce((sum, count) => sum + count, 0), 10);
}
assert.match(render(scoreDrill(7, 2, 1, 0)), /7 of 10 correct · 2 with help · 1 wrong/);

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

for (const total of [0, 2]) {
  const untouchedHtml = render(scoreDrill(0, 0, 0, 0, total));
  assert.match(untouchedHtml, />0%<\/span>/);
  assert.match(untouchedHtml, /Complete or skip an item to sync/);
  assert.match(untouchedHtml, /<button[^>]*disabled=""[^>]*>Sync<\/button>/);
}
assert.doesNotMatch(render(skippedDrill), /<button[^>]*disabled=""[^>]*>Sync<\/button>/);

for (const [state, expected] of [
  [{ phase: "syncing" }, /Syncing…/],
  [{ phase: "degraded" }, /Synced with problems/],
  [{ phase: "error", message: "PRIVATE_RUNNER_OUTPUT" }, /Couldn’t sync/],
  [{ phase: "offline" }, /You’re offline/],
  [{ phase: "dryRun", isPilot: true }, /Pilot sync saved locally/],
] as const) {
  const html = render(mathDrill, { syncState: state });
  assert.match(html, expected);
  assert.doesNotMatch(html, /PRIVATE_RUNNER_OUTPUT/);
}
const syncingHtml = render(mathDrill, { isSyncing: true });
assert.match(syncingHtml, /<button[^>]*disabled=""[^>]*>.*Syncing…<\/button>/);
assert.match(syncingHtml, /animate-spin/);

const syncedFingerprint = summaryFingerprint(buildSessionSummary(mathDrill));
const syncedDrill = { ...mathDrill, sessionSummary: { ...mathDrill.sessionSummary,
  syncedToNotionAt: "2026-11-19T10:00:00.000Z", syncedFingerprint } };
const schedule = { mastery: 2, lastReviewed: "2026-11-19", nextReview: "2026-11-24" };
const syncedHtml = render(syncedDrill, {
  syncState: { phase: "synced", unitReviews: { [mathDrill.unitCode]: schedule } },
});
assert.match(syncedHtml, /<button[^>]*bg-status-correct[^>]*disabled=""[^>]*>Synced<\/button>/);
assert.match(syncedHtml, /Unit mastery 2 · Next review Tue 24 Nov/);
assert.match(render(syncedDrill, { scheduleCache: { [mathDrill.unitCode]: schedule } }), /Next review Tue 24 Nov/);
const pendingHtml = render({ ...syncedDrill, notionSyncProblems: ["blockCleanup"] });
assert.match(pendingHtml, /Synced with problems/);
assert.doesNotMatch(pendingHtml, />Synced<\/button>/);
const changedSinceSync = { ...syncedDrill, problems: syncedDrill.problems.map((problem, i) =>
  i === 0 ? { ...problem, state: { ...problem.state, mistakeNote: "Updated after sync" } } : problem) };
assert.match(render(changedSinceSync), /Sync to update mastery and schedule/);

const labHtml = renderToStaticMarkup(
  <LabReviewPage
    currentDrill={{ ...labDrill, problems: [makeProblem("M1")] }}
    statusOverride={null}
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
assert.match(labHtml, /Submit lab/);
assert.match(labHtml, /Copy submit command/);
assert.match(labHtml, /Start M1/);
assert.doesNotMatch(labHtml, /Sync to Notion/);

// PRG totals use the canonical scoring rule, including work awaiting review.
const prgPassNoReport = {
  ...prgDrill,
  problems: [
    makeProblem("Q01", {
      ...baseState(),
      score: null,
      reviews: [
        {
          at: "2026-11-19T00:00:00Z",
          attempt: 1,
          codeHash: "sha256:pass",
          code: "",
          tests: { passed: 3, total: 3, failed: [] },
          lint: [],
          typecheck: [],
          findings: [],
          verdict: "pass",
          explain: null,
        },
      ],
    }),
  ],
};
assert.equal(buildSessionSummary(prgPassNoReport, null, { attemptDate: "2026-11-19" }).score, 1, "PRG pass review without test report must score 1");

const prgAwaitingHtml = render(
  {
    ...prgDrill,
    problems: [
      makeProblem("Q01", {
        ...baseState(),
        score: null,
        lastTestReport: {
          allPassed: true,
          score: 1,
          passedCount: 3,
          totalCount: 3,
          visibleResults: [],
          hiddenPassed: 0,
          hiddenTotal: 0,
          executionTimeMs: 2,
        },
      }),
    ],
  }
);
assert.match(prgAwaitingHtml, /Score 0%. Correct 0, Correct with help 0, Wrong 0, Skipped \/ not tried 1/);

// Rule 3: Self-score may only lower auto score or set unverified; never raises wrong/skipped or clears skipped.
{
  const { applySelfScore } = await import("../src/lib/scoring");
  const cleanCorrect = {
    ...baseState(),
    score: 1,
    attempts: [{ input: "14+8i", ts: "2026-11-19T00:00:00Z", verdict: "correct" }],
  };
  assert.equal(applySelfScore(cleanCorrect, 0.5).score, 0.5, "can lower 1 -> 0.5");
  assert.equal(applySelfScore(cleanCorrect, 0).score, 0, "can lower 1 -> 0");
  const wrongState = {
    ...baseState(),
    score: 0,
    attempts: [{ input: "wrong", ts: "2026-11-19T00:00:00Z", verdict: "incorrect" }],
  };
  assert.equal(applySelfScore(wrongState, 1).score, 0, "cannot raise wrong -> 1");
  assert.equal(applySelfScore(wrongState, 0.5).score, 0, "cannot raise wrong -> 0.5");
  const skippedState = { ...baseState(), skipped: true, score: 0 };
  const afterSkipSelf = applySelfScore(skippedState, 1);
  assert.equal(afterSkipSelf.skipped, true, "self-score must never clear skipped");
  assert.equal(afterSkipSelf.score, 0, "self-score must never raise skipped");
  assert.equal(applySelfScore(baseState(), 1).score, 1, "unverified item may set self-score");
}

console.log("reviewSync tests passed");
}

void runAsyncTests();
