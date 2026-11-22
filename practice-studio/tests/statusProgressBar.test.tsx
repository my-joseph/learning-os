import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { StatusProgressBar, getProgressStageMessage, type ProgressStage } from "../src/components/ui/StatusProgressBar";
import { ReviewSyncPage } from "../src/components/review-sync/ReviewSyncPage";
import { INITIAL_SYNC_STATE } from "../src/hooks/useProgressSync";
import { SyncCard } from "../src/components/review-sync/SyncCard";
import { buildSyncPreview } from "../src/lib/sessionSummary";
import type { DrillDocument, Problem } from "../src/types/drill";

const stages: ProgressStage[] = [
  { minPct: 0, message: "Starting..." },
  { minPct: 35, message: "Loading saved progress..." },
  { minPct: 70, message: "Preparing workspace..." },
];

assert.equal(getProgressStageMessage(0, stages), "Starting...");
assert.equal(getProgressStageMessage(34.9, stages), "Starting...");
assert.equal(getProgressStageMessage(35, stages), "Loading saved progress...");
assert.equal(getProgressStageMessage(69.9, stages), "Loading saved progress...");
assert.equal(getProgressStageMessage(70, stages), "Preparing workspace...");
assert.equal(getProgressStageMessage(120, stages), "Preparing workspace...");

const controlled = renderToStaticMarkup(
  <StatusProgressBar
    label="Controlled task"
    value={64}
    statusMessage="Backend update received."
    stages={stages}
  />
);
assert.match(controlled, /role="progressbar"/);
assert.match(controlled, /aria-label="Controlled task"/);
assert.match(controlled, /aria-valuenow="64"/);
assert.match(controlled, />64%/);
assert.match(controlled, /Backend update received\./);
assert.doesNotMatch(controlled, /Loading saved progress/);

const problem: Problem = {
  id: "Q01",
  templateKey: "status-progress-test",
  level: 1,
  levelLabel: "Level 1",
  category: "Complex Numbers",
  context: "Multiplying phasors",
  prompt: "Find the product $$(2+3i)(4-2i)$$.",
  answerPlain: "14+8i",
  answerDisplay: "14 + 8i",
  answerSpec: { type: "text" },
  steps: [{ explain: "Distribute each term." }],
  state: { userInput: "", score: null, divergedStep: null, mistakes: [] },
};
const drill: DrillDocument = {
  schemaVersion: "2.0",
  drillId: "DRL-MTH-T02-C01-U01-04",
  subject: "MATH",
  unitCode: "MTH-T02-C01-U01",
  unitTitle: "Complex Numbers",
  chapterCode: "MTH-T02-C01",
  topicCode: "MTH-T02",
  unitNotionUrl: null,
  createdAt: "2026-11-19T00:00:00Z",
  config: { questionCount: 1, difficulty: "Mixed", difficultyMode: "Mixed" },
  mistakeTags: [],
  problems: [problem],
  sessionSummary: {
    practiceStatus: "Needs Retry",
    score: 0,
    maxScore: 1,
    accuracyPct: 0,
    skippedCount: 0,
    skippedProblems: [],
    mistakeCategories: [],
    divergedStepsSummary: "",
    attemptDate: null,
  },
  localFilePath: "drills/data/MTH-T02-C01-U01/DRL-MTH-T02-C01-U01-04.json",
};
const noop = () => {};
const syncingReviewPage = renderToStaticMarkup(
  <ReviewSyncPage
    currentDrill={drill}
    statusOverride={null}
    isSyncing
    syncState={{ ...INITIAL_SYNC_STATE, phase: "syncing" }}
    scheduleCache={{}}
    dueReviewCount={0}
    weakSpotUnits={[]}
    onStatusOverrideChange={noop}
    onBackToQuiz={noop}
    onConfirmSync={noop}
    onSelectQuestion={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
  />
);
assert.match(syncingReviewPage, /Syncing to Notion/);
assert.match(syncingReviewPage, /role="progressbar"/);
assert.match(syncingReviewPage, /Saving progress locally\.\.\./);
assert.match(syncingReviewPage, /aria-valuenow="0"/);

const syncingSyncCard = renderToStaticMarkup(
  <SyncCard
    preview={buildSyncPreview(drill)}
    syncState={{ ...INITIAL_SYNC_STATE, phase: "syncing" }}
    effectiveSyncPhase="syncing"
    changedCount={0}
    isLab={false}
    onSync={noop}
    onStatusOverrideChange={noop}
  />
);
assert.match(syncingSyncCard, /Syncing to Notion/);
assert.match(syncingSyncCard, /role="progressbar"/);
assert.match(syncingSyncCard, /Saving progress locally\.\.\./);

const source = [
  readFileSync("src/components/ui/Progress.tsx", "utf8"),
  readFileSync("src/components/ui/StatusProgressBar.tsx", "utf8"),
  readFileSync("src/components/review-sync/SyncCard.tsx", "utf8"),
].join("\n");
assert.doesNotMatch(source, /\b(?:emerald|rose|amber|yellow)-\d{2,3}\b/);
assert.doesNotMatch(`${source}${controlled}${syncingReviewPage}`, /[\u{1F300}-\u{1FAFF}]/u);

console.log("statusProgressBar tests passed");
