/**
 * Render and source-invariant tests for QuestionTimer across Math, Code, Lab, and ReviewSyncPage.
 * Run: npx tsx tests/questionTimer.test.tsx (from practice-studio/)
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QuestionTimer } from "../src/components/QuestionTimer";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { ReviewSyncPage } from "../src/components/review-sync/ReviewSyncPage";
import { warningTone } from "../src/lib/statusTone";
import type { DrillDocument, Problem } from "../src/types/drill";

const noop = () => {};

// 1. Standalone QuestionTimer running vs paused states & >1h formatting
const runningHtml = renderToStaticMarkup(
  <QuestionTimer
    questionMs={75_000}
    totalMs={195_000}
    isPaused={false}
    onTogglePause={noop}
  />
);
assert.match(runningHtml, /lucide-clock/);
assert.match(runningHtml, /tabular-nums/);
assert.match(runningHtml, /text-zinc-500/);
assert.match(runningHtml, />01:15</);
assert.match(runningHtml, /Total 03:15/);
assert.match(runningHtml, /aria-label="Pause timer"/);
assert.match(runningHtml, /aria-pressed="false"/);
assert.match(runningHtml, /lucide-pause/);
assert.doesNotMatch(runningHtml, />Paused</);

const pausedHtml = renderToStaticMarkup(
  <QuestionTimer
    questionMs={3_665_000}
    totalMs={7_325_000}
    isPaused={true}
    onTogglePause={noop}
  />
);
assert.ok(pausedHtml.includes(warningTone.text));
assert.match(pausedHtml, />Paused</);
assert.match(pausedHtml, />1:01:05</);
assert.match(pausedHtml, /Total 2:02:05/);
assert.match(pausedHtml, /aria-label="Resume timer"/);
assert.match(pausedHtml, /aria-pressed="true"/);
assert.match(pausedHtml, /lucide-play/);

// 2. MathWorkspace meta line renders per-question timer and total on the right
const mathProb: Problem = {
  id: "Q01",
  templateKey: "linear",
  level: 1,
  levelLabel: "Level 1",
  category: "Algebra",
  prompt: "Solve $2x = 8$.",
  checkpointHint: "",
  answerSpec: { type: "number", value: "4" },
  state: {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    durationMs: 30_000,
  },
};

const mathMetaRunning = renderToStaticMarkup(
  <MathWorkspace
    problem={mathProb}
    index={0}
    totalQuestions={5}
    drillTitle="Linear Equations"
    mistakeTags={[]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
    questionTimerMs={42_000}
    totalTimerMs={95_000}
    isTimerPaused={false}
    onToggleTimerPause={noop}
  />
);
assert.match(mathMetaRunning, /Question 1 of 5/);
assert.match(mathMetaRunning, /00:42/);
assert.match(mathMetaRunning, /Total 01:35/);
assert.match(mathMetaRunning, /aria-label="Pause timer"/);

const mathMetaPaused = renderToStaticMarkup(
  <MathWorkspace
    problem={mathProb}
    index={0}
    totalQuestions={5}
    drillTitle="Linear Equations"
    mistakeTags={[]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
    questionTimerMs={42_000}
    totalTimerMs={95_000}
    isTimerPaused={true}
    onToggleTimerPause={noop}
  />
);
assert.match(mathMetaPaused, new RegExp(`${warningTone.text}[^>]*>.*Paused.*00:42`));
assert.match(mathMetaPaused, /aria-label="Resume timer"/);
assert.match(mathMetaPaused, /aria-pressed="true"/);

// 3. CodeDashboard (code drill + lab milestone) meta line renders per-question timer and total
const codeProb: Problem = {
  id: "Q01",
  templateKey: "kata",
  level: 2,
  levelLabel: "Level 2",
  category: "Functions",
  entryPoint: "sumRange(a, b)",
  prompt: "Return the sum from a to b.",
  checkpointHint: "",
  answerSpec: { type: "code_output" },
  workspaceFile: "q01.ts",
  state: {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    durationMs: 0,
  },
};

const codeMetaHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={codeProb}
    drillId="DRL-PRG-T01-C01-U01-01"
    index={0}
    totalQuestions={4}
    drillTitle="Functions"
    mistakeTags={[]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
    questionTimerMs={65_000}
    totalTimerMs={130_000}
    isTimerPaused={false}
    onToggleTimerPause={noop}
  />
);
assert.match(codeMetaHtml, /Problem 1 of 4/);
assert.match(codeMetaHtml, /01:05/);
assert.match(codeMetaHtml, /Total 02:10/);
assert.match(codeMetaHtml, /aria-label="Pause timer"/);

const labMetaHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={{ ...codeProb, id: "M2", entryPoint: "pool(tasks, limit)" }}
    drillId="LAB-PRG-T01-C01-01"
    index={1}
    totalQuestions={3}
    drillTitle="Async Pool"
    mistakeTags={[]}
    onInputChange={noop}
    onCheckAnswer={noop}
    onMarkDivergedStep={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
    onResetProblem={noop}
    questionTimerMs={125_000}
    totalTimerMs={300_000}
    isTimerPaused={true}
    onToggleTimerPause={noop}
  />
);
assert.match(labMetaHtml, /Milestone M2 \(2 of 3\)/);
assert.match(labMetaHtml, /Paused/);
assert.match(labMetaHtml, /02:05/);
assert.match(labMetaHtml, /Total 05:00/);
assert.match(labMetaHtml, /aria-label="Resume timer"/);

// 4. ReviewSyncPage uses totalDurationMs override (recorded + running) when provided
const sampleDrill: DrillDocument = {
  schemaVersion: "2.0",
  drillId: "DRL-PRG-T01-C01-U01-01",
  subject: "PRG",
  unitCode: "PRG-T01-C01-U01",
  unitTitle: "Functions",
  chapterCode: "PRG-T01-C01",
  topicCode: "PRG-T01",
  unitNotionUrl: null,
  createdAt: "2026-11-18T00:00:00Z",
  config: { questionCount: 1, difficulty: "ALL", difficultyMode: "Mixed" },
  mistakeTags: [],
  problems: [codeProb],
  sessionSummary: {
    practiceStatus: "Ready",
    score: 0,
    maxScore: 1,
    accuracyPct: 0,
    mistakeCategories: [],
    divergedStepsSummary: "",
    attemptDate: null,
  },
  localFilePath: "drills/data/PRG-T01-C01-U01/DRL-PRG-T01-C01-U01-01.json",
};

const reviewHtml = renderToStaticMarkup(
  <ReviewSyncPage
    currentDrill={sampleDrill}
    liveScore={0}
    maxScore={1}
    accuracyPct={0}
    computedPracticeStatus="Needs Retry"
    isSyncing={false}
    totalDurationMs={135_000}
    onStatusOverrideChange={noop}
    onBackToQuiz={noop}
    onConfirmSync={noop}
    onSelectQuestion={noop}
    onSetScore={noop}
    onToggleMistakeTag={noop}
    onMistakeNoteChange={noop}
  />
);
assert.match(reviewHtml, /2m 15s/);

// 5. Source invariant: "p" shortcut in useDrill guards inputs and dialogs, and Total tooltip opens below clock
const useDrillSrc = readFileSync("src/hooks/useDrill.ts", "utf8");
assert.match(useDrillSrc, /e\.key\.toLowerCase\(\)\s*===\s*"p"/);
assert.match(useDrillSrc, /\[role="alertdialog"\],\s*\[role="dialog"\]/);

const questionTimerSrc = readFileSync("src/components/QuestionTimer.tsx", "utf8");
assert.match(questionTimerSrc, /\btop-full\b[^\n]*\bmt-2\b/, "Total tooltip must render below clock to clear sticky header");
assert.doesNotMatch(questionTimerSrc, /\bbottom-full\b/);

console.log("questionTimer render and shortcut tests passed");
