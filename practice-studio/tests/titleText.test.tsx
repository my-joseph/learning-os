/**
 * Unit and SSR render tests for plainTitle() stripping Markdown backtick markers
 * from curriculum/drill titles across DrillSwitcher, workspaces, ReviewPanel, and side panel.
 * Run: npx tsx tests/titleText.test.tsx (from practice-studio/)
 */

import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { plainTitle } from "../src/lib/titleText";
import { DrillSwitcher } from "../src/components/shell/DrillSwitcher";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { ReviewPanel } from "../src/components/shell/ReviewPanel";
import { StudioSidePanel } from "../src/components/shell/StudioSidePanel";
import type { DrillDocument, DrillListItem, Problem } from "../src/types/drill";

// 1. Unit cases for plainTitle
assert.equal(plainTitle("`this` and Binding"), "this and Binding");
assert.equal(plainTitle("`Map`, `Set` & Hashing Patterns"), "Map, Set & Hashing Patterns");
assert.equal(plainTitle("`INNER` and `OUTER JOIN`s"), "INNER and OUTER JOINs");
assert.equal(plainTitle("  PostgreSQL Queries, `pg` Driver  "), "PostgreSQL Queries, pg Driver");
assert.equal(plainTitle("Plain Title"), "Plain Title");
assert.equal(plainTitle(""), "");
assert.equal(plainTitle(null), "");
assert.equal(plainTitle(undefined), "");

const noop = () => {};

const sampleProb: Problem = {
  id: "Q01",
  templateKey: "trace",
  level: 1,
  levelLabel: "Level 1",
  category: "JS",
  prompt: "What does this log?",
  checkpointHint: "",
  answerSpec: { type: "output", expected: "42" },
  state: {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    durationMs: 0,
  },
};

const backtickDrill: DrillDocument = {
  schemaVersion: "2.0",
  drillId: "DRL-PRG-T01-C01-U03-01",
  subject: "PRG",
  unitCode: "PRG-T01-C01-U03",
  unitTitle: "`this` and Binding",
  chapterCode: "PRG-T01-C01",
  topicCode: "PRG-T01",
  unitNotionUrl: null,
  createdAt: "2026-11-18T00:00:00Z",
  config: { questionCount: 1, difficulty: "ALL", difficultyMode: "Mixed" },
  mistakeTags: [],
  problems: [sampleProb],
  sessionSummary: {
    practiceStatus: "Ready",
    score: 0,
    maxScore: 1,
    accuracyPct: 0,
    mistakeCategories: [],
    divergedStepsSummary: "",
    attemptDate: null,
  },
  localFilePath: "",
};

const backtickListItem: DrillListItem = {
  drillId: "DRL-PRG-T01-C01-U03-01",
  subject: "PRG",
  unitCode: "PRG-T01-C01-U03",
  unitTitle: "`this` and Binding",
  chapterCode: "PRG-T01-C01",
  chapterTitle: "`Map`, `Set` & Hashing Patterns",
  topicCode: "PRG-T01",
  topicTitle: "`INNER` and `OUTER JOIN`s",
  createdAt: "2026-11-18",
  questionCount: 1,
  difficultyMode: "Mixed",
  practiceStatus: "Ready",
  score: 0,
  maxScore: 1,
  answeredCount: 0,
  localFilePath: "",
};

// 2. DrillSwitcher trigger & tree rows strip backticks
const switcherHtml = renderToStaticMarkup(
  <DrillSwitcher
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={backtickDrill}
    drills={[backtickListItem]}
    labs={[]}
    selectedDrillId={backtickDrill.drillId}
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.doesNotMatch(switcherHtml, /`/);
assert.match(switcherHtml, />this and Binding</);
assert.match(switcherHtml, />Map, Set &amp; Hashing Patterns</);
assert.match(switcherHtml, />INNER and OUTER JOINs</);

// 3. CodeDashboard & MathWorkspace h1 strip backticks
const codeHtml = renderToStaticMarkup(
  <CodeDashboard
    problem={sampleProb}
    drillId={backtickDrill.drillId}
    index={0}
    totalQuestions={1}
    drillTitle="`this` and Binding"
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
assert.match(codeHtml, /<h1[^>]*>this and Binding<\/h1>/);
assert.doesNotMatch(codeHtml, /`this`/);

const mathHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={{ ...sampleProb, answerSpec: { type: "number", value: "42" } }}
    index={0}
    totalQuestions={1}
    drillTitle="`f(x)` Notation"
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
assert.match(mathHtml, /<h1[^>]*>f\(x\) Notation<\/h1>/);
assert.doesNotMatch(mathHtml, /`f\(x\)`/);

// 4. ReviewPanel h1 & StudioSidePanel strip backticks
const reviewHtml = renderToStaticMarkup(
  <ReviewPanel
    currentDrill={backtickDrill}
    liveScore={0}
    maxScore={1}
    accuracyPct={0}
    skippedCount={0}
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
assert.match(reviewHtml, /<h1[^>]*>this and Binding<\/h1>/);
assert.doesNotMatch(reviewHtml, /`this`/);

const sideHtml = renderToStaticMarkup(
  <StudioSidePanel
    workspace="code"
    currentUnitCode="PRG-T01-C01-U03"
    dueUnits={[
      {
        unitCode: "PRG-T01-C01-U03",
        title: "`this` and Binding",
        mastery: 1,
        lastReviewed: "2026-11-18",
        nextReview: "2026-11-19",
        drillId: backtickDrill.drillId,
        href: `/code/${backtickDrill.drillId}`,
      },
    ]}
    weakSpotUnits={[]}
  />
);
assert.match(sideHtml, />this and Binding</);
assert.doesNotMatch(sideHtml, /`this`/);

console.log("titleText tests passed");
