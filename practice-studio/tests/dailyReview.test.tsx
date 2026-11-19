/**
 * Render, zero-leak, and API wiring tests for `/review` (Daily review page — Phase 1b).
 * Run: npx tsx tests/dailyReview.test.tsx
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextRequest } from "next/server";
import { DailyReviewView } from "../src/components/review/DailyReviewPage";
import { GET as drillGET } from "../src/app/api/drill/route";
import { GET as revealGET } from "../src/app/api/reveal/route";
import {
  GET as reviewItemsGET,
  POST as reviewItemsPOST,
} from "../src/app/api/review-items/route";
import { POST as saveStatePOST } from "../src/app/api/save-state/route";
import { ReviewItem } from "../src/lib/reviewItems";
import { formatReviewDueDate } from "../src/lib/dueToday";
import {
  executeReviewItemCheck,
  executeReviewItemSkip,
  formatReviewScheduleHint,
  getMissedReviewItems,
  prepareProblemForReviewItem,
  ReviewSessionItemOutcome,
  saveReviewProblemState,
  summarizeReviewSession,
} from "../src/lib/reviewSession";
import { createTelemetryTimerState } from "../src/lib/telemetryTimer";
import type { DrillDocument, Problem } from "../src/types/drill";

function makeSampleItems(): ReviewItem[] {
  return [
    {
      drillId: "DRL-MTH-T01-C04-U01-01",
      qid: "Q01",
      unitCode: "MTH-T01-C04-U01",
      subject: "MTH",
      commonTrapTag: "c04-divide-not-invert-trap",
      archetypeKey: "fraction-division-archetype",
      level: 2,
      lastReviewed: "2026-11-16",
      dueDate: "2026-11-19",
      revisitNote: "Flip the second fraction before cancelling common factors.",
    },
    {
      drillId: "DRL-PRG-T01-C01-U01-01",
      qid: "Q01",
      unitCode: "PRG-T01-C01-U01",
      subject: "PRG",
      commonTrapTag: "U-edge-empty",
      archetypeKey: "array-guard-archetype",
      level: 3,
      lastReviewed: "2026-11-12",
      dueDate: "2026-11-19",
      revisitNote: null,
    },
    {
      drillId: "DRL-MTH-T01-C04-U02-01",
      qid: "Q02",
      unitCode: "MTH-T01-C04-U02",
      subject: "MTH",
      commonTrapTag: "c04-sign-drop-trap",
      archetypeKey: "signed-fractions-archetype",
      level: 2,
      lastReviewed: "2026-11-16",
      dueDate: "2026-11-19",
      revisitNote: null,
    },
  ];
}

function makeUnredactedMathProblem(): Problem {
  return {
    id: "Q01",
    templateKey: "fraction-division-archetype",
    level: 2,
    levelLabel: "Level 2",
    category: "Fractions",
    prompt: "Evaluate $\\frac{3}{4} \\div \\frac{9}{8}$.",
    display: "SECRET_SETUP_DISPLAY_BOX",
    plainText: "SECRET_CAS_PLAIN_TEXT",
    hasSetup: true,
    commonTrapTag: "c04-divide-not-invert-trap",
    trapValue: "SECRET_TRAP_27_32",
    answerDisplay: "SECRET_ANSWER_2_OVER_3",
    answerPlain: "SECRET_ANSWER_2_OVER_3",
    answerSpec: {
      type: "number",
      value: "SECRET_ANSWER_2_OVER_3",
      accepted: ["SECRET_ANSWER_2_OVER_3", "2/3"],
      commonTrapTag: "c04-divide-not-invert-trap",
    },
    checkpointHint: "Multiply by the reciprocal of the divisor.",
    steps: [
      {
        latex: "\\frac{3}{4} \\times \\frac{8}{9}",
        explain: "SECRET_STEP_EXPLANATION_TEXT",
      },
    ],
    state: {
      userInput: "",
      score: null,
      divergedStep: null,
      mistakes: [],
      lastCheck: null,
      attempts: [],
    },
  };
}

async function runTests() {
  const sampleItems = makeSampleItems();

  // -------------------------------------------------------------------------
  // 1. Render tests for DailyReviewView states: loading, empty, item with
  //    revisitNote, PRG non-coding & PRG coding items, and end screen
  // -------------------------------------------------------------------------
  {
    // 1a. Loading state
    const loadingHtml = renderToStaticMarkup(
      <DailyReviewView loading={true} items={[]} />
    );
    assert.match(loadingHtml, /<h1[^>]*>Daily review<\/h1>/);
    assert.match(loadingHtml, /Loading daily review…/);

    // 1b. Empty state ("Nothing to review today" + next due date)
    const emptyHtml = renderToStaticMarkup(
      <DailyReviewView
        loading={false}
        items={[]}
        nextDueDate="2026-11-24"
        lastDrillHref="/math/DRL-MTH-T01-C04-U01-01"
      />
    );
    assert.match(emptyHtml, /<h1[^>]*>Daily review<\/h1>/);
    assert.match(emptyHtml, /Nothing to review today/);
    assert.match(emptyHtml, /Next due: 2026-11-24/);
    assert.match(emptyHtml, /href="\/math\/DRL-MTH-T01-C04-U01-01"/);

    // 1c. Active item with revisitNote shown ABOVE the problem + progress "1 of 3" + timer +
    //     meta line with unit name & Difficulty N + "Skip · due tomorrow" + disabled Next before attempt
    const rawMathProblem = makeUnredactedMathProblem();
    const activeHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={0}
        currentProblem={rawMathProblem}
        unitTitles={{
          "MTH-T01-C04-U01": "Fraction Division",
          "PRG-T01-C01-U01": "Array Guards",
          "MTH-T01-C04-U02": "Signed Fractions",
        }}
        questionTimerMs={14_000}
        totalTimerMs={14_000}
        onSkip={() => {}}
        onNextItem={() => {}}
      />
    );
    assert.match(activeHtml, /<h1[^>]*>Daily review<\/h1>/);
    assert.equal(
      (activeHtml.match(/<h1\b/g) || []).length,
      1,
      "Review page must render exactly one h1"
    );
    assert.match(activeHtml, /1 of 3/);
    assert.match(activeHtml, /Review 1 of 3/);
    const reviewMathSource = fs.readFileSync("src/components/math/MathWorkspace.tsx", "utf8");
    assert.match(reviewMathSource, /Answer for question \$\{index \+ 1\} of \$\{totalQuestions/);
    assert.match(activeHtml, /0:14/);
    assert.match(activeHtml, /Fraction Division/, "Meta line must show unit name");
    assert.match(activeHtml, /Difficulty 2/, "Meta line must rename Level to Difficulty on /review");
    assert.doesNotMatch(activeHtml, /Question 1 of 3/, "Card must not duplicate header counter on /review");
    assert.match(activeHtml, /Skip · due tomorrow/, "Skip button must show due-tomorrow cost on /review");
    assert.match(activeHtml, /min-h-\[36px\]/, "Skip must have a mobile tap target of at least 36px");
    assert.match(
      activeHtml,
      /<button[^>]*disabled=""[^>]*><span>Next<\/span>/,
      "Next button must be disabled before an attempt on /review"
    );
    assert.match(
      activeHtml,
      /Your note from last time:[\s\S]*?Flip the second fraction before cancelling common factors\./
    );
    const notePos = activeHtml.indexOf("Your note from last time:");
    const promptPos = activeHtml.indexOf("Evaluate");
    assert.ok(
      notePos >= 0 && promptPos > notePos,
      "revisitNote must appear ABOVE the problem prompt in markup"
    );

    // 1d. Zero-leak markup test before an attempt: no answers, steps, setup, trap tag/title, or archetype
    assert.doesNotMatch(activeHtml, /SECRET_ANSWER_2_OVER_3/);
    assert.doesNotMatch(activeHtml, /SECRET_STEP_EXPLANATION_TEXT/);
    assert.doesNotMatch(activeHtml, /SECRET_SETUP_DISPLAY_BOX/);
    assert.doesNotMatch(activeHtml, /SECRET_CAS_PLAIN_TEXT/);
    assert.doesNotMatch(activeHtml, /SECRET_TRAP_27_32/);
    assert.doesNotMatch(activeHtml, /c04-divide-not-invert-trap/);
    assert.doesNotMatch(activeHtml, /Divide not invert/);
    assert.doesNotMatch(activeHtml, /Trap:/);
    assert.doesNotMatch(activeHtml, /fraction-division-archetype/);
    assert.doesNotMatch(activeHtml, /Next time I will…/);

    // 1e. After an incorrect attempt: shows "Trap: <plain title>", does not show "Next time I will…"
    const wrongAttemptProblem: Problem = {
      ...prepareProblemForReviewItem(rawMathProblem, sampleItems[0]),
      state: {
        userInput: "27/32",
        score: 0,
        divergedStep: null,
        mistakes: ["c04-divide-not-invert-trap"],
        lastCheck: {
          verdict: "incorrect",
          message: "Not quite — invert the second fraction before multiplying.",
          components: [],
          diagnostics: [],
          trapMatched: true,
        },
        attempts: [
          {
            input: "27/32",
            ts: "2026-11-19T10:00:00Z",
            verdict: "incorrect",
            matchedTrap: "c04-divide-not-invert-trap",
          },
        ],
      },
    };
    const afterWrongHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={0}
        currentProblem={wrongAttemptProblem}
        today="2026-11-19"
        currentOutcome={{
          drillId: "DRL-MTH-T01-C04-U01-01",
          qid: "Q01",
          initialLevel: 2,
          newLevel: 1,
          correct: false,
          hintsUsed: 0,
          dueDate: "2026-11-20",
        }}
        revealedTrapTag="c04-divide-not-invert-trap"
        onNextItem={() => {}}
      />
    );
    assert.match(afterWrongHtml, /Trap:[\s\S]*?Divide not invert/);
    assert.match(afterWrongHtml, /Not quite[\s\S]*?back tomorrow/);
    assert.doesNotMatch(
      afterWrongHtml,
      /<button[^>]*disabled=""[^>]*><span>Next<\/span>/,
      "Next button must be enabled after an attempt"
    );
    assert.doesNotMatch(afterWrongHtml, /Next time I will…/);

    const almostProblem: Problem = {
      ...wrongAttemptProblem,
      state: {
        ...wrongAttemptProblem.state,
        lastCheck: { ...wrongAttemptProblem.state.lastCheck!, verdict: "equivalent_not_in_form", trapMatched: true },
      },
    };
    const almostHtml = renderToStaticMarkup(
      <DailyReviewView items={sampleItems} currentIndex={0} currentProblem={almostProblem} />
    );
    assert.match(almostHtml, /Almost — check the form/);
    assert.doesNotMatch(almostHtml, /Trap:/, "an almost verdict must not be labeled as a trap match");

    // 1f. After a correct attempt: shows "next in N days", "Trap: <plain title>", AND "Next time I will…" input
    const correctAttemptProblem: Problem = {
      ...prepareProblemForReviewItem(rawMathProblem, sampleItems[0]),
      steps: rawMathProblem.steps,
      answerDisplay: "2/3",
      state: {
        userInput: "2/3",
        score: 1,
        divergedStep: null,
        mistakes: [],
        lastCheck: {
          verdict: "correct",
          message: "Correct.",
          components: [],
          diagnostics: [],
        },
        attempts: [
          {
            input: "2/3",
            ts: "2026-11-19T10:01:00Z",
            verdict: "correct",
          },
        ],
      },
    };
    const afterCorrectHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={0}
        currentProblem={correctAttemptProblem}
        today="2026-11-19"
        currentOutcome={{
          drillId: "DRL-MTH-T01-C04-U01-01",
          qid: "Q01",
          initialLevel: 2,
          newLevel: 3,
          correct: true,
          hintsUsed: 0,
          dueDate: "2026-11-26",
        }}
        revealedTrapTag="c04-divide-not-invert-trap"
        revisitNoteDraft="Invert the divisor right away."
      />
    );
    assert.match(afterCorrectHtml, /Correct[\s\S]*?next in 7 days/);
    assert.doesNotMatch(afterCorrectHtml, /Trap:/, "a non-trap verdict must not show a trap line");
    assert.match(afterCorrectHtml, /Next time I will…/);
    assert.match(afterCorrectHtml, /Invert the divisor right away\./);

    const correctOnRetryHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={0}
        currentProblem={correctAttemptProblem}
        today="2026-11-19"
        currentOutcome={{
          drillId: sampleItems[0].drillId,
          qid: sampleItems[0].qid,
          initialLevel: 2,
          newLevel: 1,
          correct: false,
          correctOnRetry: true,
          hintsUsed: 0,
          dueDate: "2026-11-20",
        }}
      />
    );
    assert.match(correctOnRetryHtml, /Correct on retry[\s\S]*?back tomorrow/);

    // Pure schedule-hint helper tests
    assert.equal(
      formatReviewScheduleHint(
        { correct: true, newLevel: 3, dueDate: "2026-11-26" },
        "2026-11-19"
      ),
      "next in 7 days"
    );
    assert.equal(
      formatReviewScheduleHint(
        { correct: true, newLevel: 1, dueDate: "2026-11-20" },
        "2026-11-19"
      ),
      "next in 1 day"
    );
    assert.equal(
      formatReviewScheduleHint(
        { correct: false, newLevel: 1, dueDate: "2026-11-20" },
        "2026-11-19"
      ),
      "back tomorrow"
    );
    assert.equal(formatReviewDueDate("2026-11-20", "2026-11-19"), "Tomorrow");
    assert.equal(formatReviewDueDate("2026-11-20", "2026-11-18"), "Fri 20 Nov");

    const skippedProblem: Problem = {
      ...rawMathProblem,
      state: {
        ...rawMathProblem.state,
        userInput: "(Skipped)",
        score: 0,
        skipped: true,
        lastCheck: { verdict: "skipped", message: "Skipped", components: [], diagnostics: [] },
        attempts: [{ input: "(Skipped)", ts: "2026-11-19T10:00:00Z", verdict: "skipped" }],
      },
    };
    const skippedHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={0}
        currentProblem={skippedProblem}
        currentOutcome={{
          drillId: sampleItems[0].drillId,
          qid: sampleItems[0].qid,
          initialLevel: 2,
          newLevel: 1,
          correct: false,
          skipped: true,
          hintsUsed: 0,
          dueDate: "2026-11-20",
        }}
        today="2026-11-19"
        onNextItem={() => {}}
      />
    );
    assert.match(skippedHtml, /Skipped[\s\S]*?back tomorrow/);
    assert.match(skippedHtml, /data-review-primary-action="true"[^>]*>[\s\S]*?Next/);
    assert.doesNotMatch(skippedHtml, /SECRET_STEP_EXPLANATION_TEXT/);
    assert.doesNotMatch(skippedHtml, /Trap:/);
    assert.match(skippedHtml, /Show steps/);

    const reviewSource = fs.readFileSync("src/components/review/DailyReviewPage.tsx", "utf8");
    const mathWorkspaceSource = fs.readFileSync("src/components/math/MathWorkspace.tsx", "utf8");
    const studioClientSource = fs.readFileSync("src/components/shell/StudioClient.tsx", "utf8");
    assert.match(reviewSource, /sessionStorage\.setItem\(reviewStorageKey/);
    assert.match(reviewSource, /sessionStorage\.getItem\(reviewStorageKey/);
    assert.match(mathWorkspaceSource, /learningos:review-math-input-mode/);
    assert.match(studioClientSource, /You missed this in today&apos;s review/);
    assert.match(studioClientSource, /resetAnswerForReviewRetry/);

    // 1g. PRG coding problem on /review shows prompt and "Open in drill" link instead of inline editor / VS Code
    const prgCodingProblem: Problem = {
      id: "Q01",
      templateKey: "array-guard-archetype",
      level: 3,
      levelLabel: "Level 3",
      category: "Core Skill",
      entryPoint: "firstOrNull",
      prompt: "Implement `firstOrNull(items)` returning the first element or `null`.",
      workspaceFile: "drills/workspace/DRL-PRG-T01-C01-U01-01/Q01_firstOrNull.js",
      solutionCode: "export function firstOrNull(items) { return items[0] ?? null; }",
      visibleTests: [
        {
          id: "T1",
          name: "returns null for empty array",
          testCode: "assert.strictEqual(firstOrNull([]), null);",
        },
      ],
      answerSpec: { type: "code_output" },
      checkpointHint: "Check `items.length === 0` first.",
      state: {
        userInput: "",
        score: null,
        divergedStep: null,
        mistakes: [],
        lastCheck: null,
        attempts: [],
      },
    };
    const prgCodingHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={1}
        currentProblem={prgCodingProblem}
      />
    );
    assert.match(prgCodingHtml, /2 of 3/);
    assert.match(prgCodingHtml, /firstOrNull/);
    assert.match(prgCodingHtml, /Open in drill/);
    assert.match(
      prgCodingHtml,
      /href="\/code\/DRL-PRG-T01-C01-U01-01\?q=Q01"/
    );
    assert.doesNotMatch(prgCodingHtml, /Open in VS Code/);
    assert.doesNotMatch(prgCodingHtml, /Run checks/);
    assert.doesNotMatch(prgCodingHtml, /items\[0\] \?\? null/);

    // 1h. PRG non-coding problem (predict-output) renders normal answer input on /review
    const prgPredictProblem: Problem = {
      id: "Q01",
      templateKey: "closure-trace",
      level: 2,
      levelLabel: "Level 2",
      category: "Code Tracing",
      codeType: "predict-output",
      prompt: "What does this snippet log?",
      codeSnippet: "console.log([1, 2, 3].length);",
      answerSpec: {
        type: "predict_output",
        accepted: ["SECRET_OUTPUT_3"],
      },
      checkpointHint: "Count array elements.",
      state: {
        userInput: "",
        score: null,
        divergedStep: null,
        mistakes: [],
        lastCheck: null,
        attempts: [],
      },
    };
    const prgPredictHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        currentIndex={1}
        currentProblem={prgPredictProblem}
      />
    );
    assert.match(prgPredictHtml, /What does this snippet log\?/);
    assert.match(prgPredictHtml, /aria-label="Check answer"/);
    assert.doesNotMatch(prgPredictHtml, /Open in drill/);
    assert.doesNotMatch(prgPredictHtml, /SECRET_OUTPUT_3/);

    // 1i. End screen: count correct / total, moved up / down a level, next due date, link back to last drill
    const outcomes: Record<string, ReviewSessionItemOutcome> = {
      "DRL-MTH-T01-C04-U01-01/Q01": {
        drillId: "DRL-MTH-T01-C04-U01-01",
        qid: "Q01",
        initialLevel: 2,
        newLevel: 3,
        correct: true,
        hintsUsed: 0,
        dueDate: "2026-11-26",
      },
      "DRL-PRG-T01-C01-U01-01/Q01": {
        drillId: "DRL-PRG-T01-C01-U01-01",
        qid: "Q01",
        initialLevel: 3,
        newLevel: 1,
        correct: false,
        skipped: true,
        hintsUsed: 0,
        dueDate: "2026-11-20",
      },
      "DRL-MTH-T01-C04-U02-01/Q02": {
        drillId: "DRL-MTH-T01-C04-U02-01",
        qid: "Q02",
        initialLevel: 2,
        newLevel: 2,
        correct: true,
        correctOnRetry: true,
        hintsUsed: 1,
        dueDate: "2026-11-22",
      },
    };
    const summary = summarizeReviewSession(sampleItems, outcomes, "2026-11-25");
    assert.equal(summary.correctCount, 2);
    assert.equal(summary.totalCount, 3);
    assert.equal(summary.movedUpCount, 1);
    assert.equal(summary.movedDownCount, 1);
    assert.equal(summary.stayedCount, 1);
    assert.equal(summary.nextDueDate, "2026-11-20");

    const missed = getMissedReviewItems(sampleItems, outcomes, {
      "PRG-T01-C01-U01": "Array Guards",
    }, { "DRL-PRG-T01-C01-U01-01/Q01": "Implement `firstOrNull(items)`\nsecond line" });
    assert.deepEqual(missed, [
      {
        drillId: "DRL-PRG-T01-C01-U01-01",
        qid: "Q01",
        unitCode: "PRG-T01-C01-U01",
        unitTitle: "Array Guards",
        href: "/code/DRL-PRG-T01-C01-U01-01?q=Q01",
        questionLine: "Implement firstOrNull(items)",
        group: "Skipped",
      },
      {
        drillId: "DRL-MTH-T01-C04-U02-01",
        qid: "Q02",
        unitCode: "MTH-T01-C04-U02",
        unitTitle: "MTH-T01-C04-U02",
        href: "/math/DRL-MTH-T01-C04-U02-01?q=Q02",
        questionLine: "",
        group: "Correct on retry",
      },
    ]);

    const groupedOutcomes = {
      ...outcomes,
      "DRL-MTH-T01-C04-U01-01/Q01": {
        ...outcomes["DRL-MTH-T01-C04-U01-01/Q01"],
        correct: false,
      },
    };
    const groupedItems = getMissedReviewItems(sampleItems, groupedOutcomes, {
      "PRG-T01-C01-U01": "Array Guards",
    }, { "DRL-PRG-T01-C01-U01-01/Q01": "Implement `firstOrNull(items)`" });

    const endHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        completed={true}
        summary={summary}
        stillDueCount={4}
        missedItems={groupedItems}
        today="2026-11-19"
        onReviewMore={() => {}}
        lastDrillHref="/math/DRL-MTH-T01-C04-U01-01"
      />
    );
    assert.match(endHtml, /Review complete/);
    assert.match(endHtml, /2 \/ 3 correct/);
    assert.match(endHtml, /Still due 4/);
    assert.match(endHtml, /1 moved up a level/);
    assert.match(endHtml, /1 moved down a level/);
    assert.match(endHtml, /Tomorrow/);
    assert.match(endHtml, /Review 4 more/);
    assert.match(endHtml, /Missed \(1\)/);
    assert.match(endHtml, /Skipped \(1\)/);
    assert.match(endHtml, /Correct on retry \(1\)/);
    assert.match(endHtml, /Array Guards/);
    assert.match(endHtml, /href="\/code\/DRL-PRG-T01-C01-U01-01\?q=Q01&amp;review=missed"/);
    assert.match(endHtml, /Implement firstOrNull\(items\)/);
    assert.doesNotMatch(endHtml, />Q01</, "the row must not show an internal question id as primary text");
    assert.match(endHtml, /Open in drill/);
    assert.match(endHtml, /href="\/math\/DRL-MTH-T01-C04-U01-01"/);

    // When stillDueCount > 8, primary button caps batch size at 8 ("Review 8 more")
    const endLargeBacklogHtml = renderToStaticMarkup(
      <DailyReviewView
        items={sampleItems}
        completed={true}
        summary={summary}
        stillDueCount={20}
        onReviewMore={() => {}}
        lastDrillHref="/math/DRL-MTH-T01-C04-U01-01"
      />
    );
    assert.match(endLargeBacklogHtml, /Still due 20/);
    assert.match(endLargeBacklogHtml, /Review 8 more/);
  }

  // -------------------------------------------------------------------------
  // 2. Zero-leak payload tests & full API wiring tests (/api/review-items,
  //    /api/drill?review=1, /api/save-state reviewMerge, /api/reveal)
  // -------------------------------------------------------------------------
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-daily-review-"));
  const dataDir = path.join(tmp, "drills", "data");
  const progressDir = path.join(tmp, "progress");
  const labsDir = path.join(tmp, "labs");

  const prevProgressDir = process.env.PROGRESS_DIR;
  const prevDrillsDir = process.env.DRILLS_DATA_DIR;
  const prevLabsDir = process.env.LABS_DIR;

  try {
    fs.mkdirSync(path.join(dataDir, "MTH-T01-C04-U01"), { recursive: true });
    fs.mkdirSync(progressDir, { recursive: true });
    fs.mkdirSync(labsDir, { recursive: true });

    const drillId = "DRL-MTH-T01-C04-U01-01";
    const unitCode = "MTH-T01-C04-U01";
    const drillFile = path.join(dataDir, unitCode, `${drillId}.json`);
    const drillFileContent = JSON.stringify(
      {
        schemaVersion: "2.0",
        drillId,
        subject: "MATH",
        unitCode,
        unitTitle: "Fraction Division",
        mistakeTags: [
          {
            id: "arithmetic-slip",
            name: "Arithmetic slip",
            label: "Arithmetic slip",
            autoFrom: [],
          },
        ],
        problems: [
          {
            id: "Q01",
            templateKey: "SECRET_ARCHETYPE_KEY_Q01",
            archetypeKey: "SECRET_ARCHETYPE_KEY_Q01",
            level: 2,
            levelLabel: "Level 2",
            category: "Fractions",
            prompt: "Compute $14 \\div 2$.",
            display: "SECRET_DISPLAY_SETUP_14_DIV_2",
            plainText: "SECRET_PLAINTEXT_14_DIV_2",
            commonTrapTag: "c04-divide-not-invert-trap",
            trapValue: "SECRET_TRAP_28",
            answerDisplay: "SECRET_ANSWER_777",
            answerPlain: "SECRET_ANSWER_777",
            answerSpec: {
              type: "number",
              value: "SECRET_ANSWER_777",
              accepted: ["SECRET_ANSWER_777"],
            },
            checkpointHint: "Half of 14.",
            steps: [
              {
                latex: "14 / 2 = 7",
                explain: "SECRET_STEP_EXPLAIN_777",
              },
            ],
          },
          {
            id: "Q02",
            templateKey: "SECRET_ARCHETYPE_KEY_Q02",
            level: 3,
            levelLabel: "Level 3",
            category: "Fractions",
            prompt: "Compute $20 \\div 4$.",
            answerDisplay: "SECRET_ANSWER_555",
            answerPlain: "SECRET_ANSWER_555",
            answerSpec: { type: "number", value: "SECRET_ANSWER_555" },
            checkpointHint: "Quarter of 20.",
            steps: [{ latex: "5", explain: "SECRET_STEP_555" }],
          },
        ],
      },
      null,
      2
    );
    fs.writeFileSync(drillFile, drillFileContent, "utf-8");

    // Seed previous progress where Q01 was attempted earlier (so normal drill load would unlock steps!)
    // and Q02 was also solved earlier (must not be lost when Q01 is saved in /review).
    fs.writeFileSync(
      path.join(progressDir, `${drillId}.json`),
      JSON.stringify(
        {
          drillId,
          unitCode,
          updatedAt: "2026-11-17T10:00:00Z",
          sessionSummary: {
            practiceStatus: "In Progress",
            score: 1,
            maxScore: 2,
            accuracyPct: 50,
            mistakeCategories: [],
            divergedStepsSummary: "",
            attemptDate: "2026-11-17",
          },
          problems: {
            Q01: {
              userInput: "99",
              score: 0,
              mistakes: ["c04-divide-not-invert-trap"],
              mistakeNote: "Forgot to flip the second fraction.",
              revisitNote: "Remember to invert the divisor first.",
              lastCheck: {
                verdict: "incorrect",
                message: "Not quite.",
                components: [],
                diagnostics: [],
              },
              attempts: [
                {
                  input: "7",
                  ts: "2026-11-10T10:00:00Z",
                  verdict: "correct",
                },
                {
                  input: "99",
                  ts: "2026-11-17T10:00:00Z",
                  verdict: "incorrect",
                },
              ],
            },
            Q02: {
              userInput: "5",
              score: 1,
              mistakes: [],
              attempts: [
                {
                  input: "5",
                  ts: "2026-11-18T10:00:00Z",
                  verdict: "correct",
                },
              ],
            },
          },
        },
        null,
        2
      ),
      "utf-8"
    );

    process.env.PROGRESS_DIR = progressDir;
    process.env.DRILLS_DATA_DIR = dataDir;
    process.env.LABS_DIR = labsDir;

    // 2a. GET /api/review-items?limit=8 zero-leak check
    const dueRes = await reviewItemsGET(
      new NextRequest("http://127.0.0.1:3000/api/review-items?limit=8&today=2026-11-19")
    );
    assert.equal(dueRes.status, 200);
    const duePayloadText = await dueRes.text();
    assert.doesNotMatch(duePayloadText, /SECRET_ANSWER_777/);
    assert.doesNotMatch(duePayloadText, /SECRET_STEP_EXPLAIN_777/);
    assert.doesNotMatch(duePayloadText, /SECRET_DISPLAY_SETUP_14_DIV_2/);
    assert.doesNotMatch(duePayloadText, /SECRET_TRAP_28/);
    assert.doesNotMatch(
      duePayloadText,
      /c04-divide-not-invert-trap/,
      "GET /api/review-items payload must not leak commonTrapTag before an attempt"
    );
    assert.doesNotMatch(
      duePayloadText,
      /SECRET_ARCHETYPE_KEY/,
      "GET /api/review-items payload must not leak archetypeKey before an attempt"
    );

    const dueJson = JSON.parse(duePayloadText) as {
      today: string;
      totalDue: number;
      nextDueDate: string | null;
      items: ReviewItem[];
    };
    assert.equal(dueJson.today, "2026-11-19");
    assert.equal(dueJson.totalDue, 1);
    assert.equal(dueJson.nextDueDate, "2026-11-21");
    assert.equal(dueJson.items.length, 1);
    assert.equal(dueJson.items[0].drillId, drillId);
    assert.equal(dueJson.items[0].qid, "Q01");
    assert.equal(
      dueJson.items[0].revisitNote,
      "Remember to invert the divisor first."
    );

    // 2b. GET /api/drill?id=...&review=1 zero-leak check (even though Q01 has prior attempts in progress!)
    const reviewDrillRes = await drillGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/drill?id=${encodeURIComponent(drillId)}&review=1`
      )
    );
    assert.equal(reviewDrillRes.status, 200);
    const reviewDrillText = await reviewDrillRes.text();
    assert.doesNotMatch(
      reviewDrillText,
      /SECRET_ANSWER_777/,
      "GET /api/drill?review=1 must strip answerDisplay/answerPlain/answerSpec.value"
    );
    assert.doesNotMatch(
      reviewDrillText,
      /SECRET_STEP_EXPLAIN_777/,
      "GET /api/drill?review=1 must strip steps even when problem was attempted in the past"
    );
    assert.doesNotMatch(
      reviewDrillText,
      /SECRET_DISPLAY_SETUP_14_DIV_2/,
      "GET /api/drill?review=1 must strip display/plainText before an attempt"
    );
    assert.doesNotMatch(
      reviewDrillText,
      /c04-divide-not-invert-trap/,
      "GET /api/drill?review=1 must strip commonTrapTag on problems"
    );
    assert.doesNotMatch(
      reviewDrillText,
      /SECRET_ARCHETYPE_KEY/,
      "GET /api/drill?review=1 must strip templateKey/archetypeKey"
    );

    const reviewDrillDoc = JSON.parse(reviewDrillText) as DrillDocument;
    const loadedQ1 = reviewDrillDoc.problems.find((p) => p.id === "Q01")!;
    assert.equal(loadedQ1.state.userInput, "");
    assert.equal(loadedQ1.state.score, null);
    assert.equal(loadedQ1.state.lastCheck, null);
    assert.equal(loadedQ1.state.attempts?.length ?? 0, 0);

    // 2c. API wiring test: executeReviewItemCheck wires check-answer, save-state (reviewMerge),
    //     reveal, and review-items POST
    const calls: Array<{ url: string; method: string; body?: Record<string, unknown> }> = [];
    const customFetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      const urlStr = typeof input === "string" ? input : input.toString();
      const method = (init?.method || "GET").toUpperCase();
      const parsedBody =
        typeof init?.body === "string"
          ? (JSON.parse(init.body) as Record<string, unknown>)
          : undefined;
      calls.push({ url: urlStr, method, body: parsedBody });

      if (urlStr === "/api/check-answer" && method === "POST") {
        const isRight = parsedBody?.input === "7";
        return new Response(
          JSON.stringify({
            verdict: isRight ? "correct" : "incorrect",
            message: isRight ? "Correct." : "Not quite.",
            components: [],
            diagnostics: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      if (urlStr === "/api/save-state" && method === "POST") {
        return saveStatePOST(
          new NextRequest("http://127.0.0.1:3000/api/save-state", {
            method: "POST",
            body: init?.body as string,
          })
        );
      }
      if (urlStr.startsWith("/api/reveal") && method === "GET") {
        return revealGET(new NextRequest(`http://127.0.0.1:3000${urlStr}`));
      }
      if (urlStr === "/api/review-items" && method === "POST") {
        return reviewItemsPOST(
          new NextRequest("http://127.0.0.1:3000/api/review-items", {
            method: "POST",
            body: init?.body as string,
          })
        );
      }
      throw new Error(`Unexpected fetch: ${method} ${urlStr}`);
    }) as typeof fetch;

    const timer = createTelemetryTimerState("DRL-MTH-T01-C04-U01-01/Q01", true, false, 1_000);
    const checkOutcome = await executeReviewItemCheck({
      drillDoc: reviewDrillDoc,
      item: dueJson.items[0],
      inputVal: "7",
      hintsUsed: 0,
      timerState: timer,
      now: 6_000,
      today: "2026-11-19",
      fetchFn: customFetch,
    });
    assert.ok(checkOutcome);
    assert.equal(checkOutcome.result.verdict, "correct");
    assert.ok(checkOutcome.outcome);
    // Q01 started at level 1 (from backfilled 2->1 after wrong) -> correct without hint -> level 2
    assert.equal(checkOutcome.outcome.correct, true);
    assert.equal(checkOutcome.outcome.hintsUsed, 0);
    assert.equal(
      checkOutcome.outcome.newLevel,
      checkOutcome.outcome.initialLevel + 1
    );
    assert.equal(
      checkOutcome.outcome.commonTrapTag,
      "c04-divide-not-invert-trap",
      "POST /api/review-items returns commonTrapTag after answering so the UI can show Trap: <plain title>"
    );

    // Verify all 4 API routes were called in order
    assert.deepEqual(
      calls.map((c) => `${c.method} ${c.url.split("?")[0]}`),
      [
        "POST /api/check-answer",
        "POST /api/review-items",
        "POST /api/save-state",
        "GET /api/reveal",
        "GET /api/reveal",
      ]
    );
    const reviewItemsCall = calls.find((c) => c.url === "/api/review-items")!;
    assert.deepEqual(reviewItemsCall.body, {
      drillId,
      qid: "Q01",
      correct: true,
      hintsUsed: 0,
      date: "2026-11-19",
    });

    // Steps and display were revealed on updatedDoc after the check
    const checkedQ1 = checkOutcome.updatedDoc.problems.find((p) => p.id === "Q01")!;
    assert.equal(checkedQ1.steps?.length, 1);
    assert.equal(checkedQ1.display, "SECRET_DISPLAY_SETUP_14_DIV_2");

    // 2d. Saving "Next time I will…" revisitNote updates progress/<DRILL_ID>.json without
    //     clobbering Q02 or Q01's prior attempts, and never touches drills/data
    const noteSaved = await saveReviewProblemState(
      drillId,
      unitCode,
      "Q01",
      {
        ...checkedQ1.state,
        revisitNote: "Invert the divisor immediately and simplify.",
      },
      customFetch
    );
    assert.equal(noteSaved, true);

    const savedProgress = JSON.parse(
      fs.readFileSync(path.join(progressDir, `${drillId}.json`), "utf-8")
    ) as {
      problems: Record<
        string,
        {
          score: number;
          revisitNote?: string;
          mistakes?: string[];
          mistakeNote?: string;
          attempts: Array<{ input: string; verdict: string }>;
        }
      >;
    };
    assert.equal(
      savedProgress.problems.Q01.revisitNote,
      "Invert the divisor immediately and simplify."
    );
    assert.equal(
      savedProgress.problems.Q01.attempts.length,
      3,
      "reviewMerge must append the new review attempt while preserving prior attempts"
    );
    assert.deepEqual(
      savedProgress.problems.Q01.mistakes,
      ["c04-divide-not-invert-trap"],
      "reviewMerge must not erase earlier mistake tags the review did not set"
    );
    assert.equal(
      savedProgress.problems.Q01.mistakeNote,
      "Forgot to flip the second fraction.",
      "reviewMerge must not erase the learner's earlier mistake note"
    );
    assert.equal(
      savedProgress.problems.Q02.score,
      1,
      "reviewMerge must preserve untouched Q02 progress in the same drill"
    );
    assert.equal(
      fs.readFileSync(drillFile, "utf-8"),
      drillFileContent,
      "Review check and revisitNote save must never modify drills/data"
    );

    // 2e. Verify skip / wrong wiring records correct: false and hintsUsed count
    const skipOutcome = await executeReviewItemSkip({
      drillDoc: reviewDrillDoc,
      item: { ...dueJson.items[0], level: 4 },
      hintsUsed: 2,
      timerState: timer,
      now: 10_000,
      today: "2026-11-19",
      fetchFn: customFetch,
    });
    assert.ok(skipOutcome);
    assert.equal(skipOutcome.outcome.correct, false);
    assert.equal(skipOutcome.outcome.hintsUsed, 2);

    console.log("daily review tests passed");
  } finally {
    if (prevProgressDir === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgressDir;
    if (prevDrillsDir === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrillsDir;
    if (prevLabsDir === undefined) delete process.env.LABS_DIR;
    else process.env.LABS_DIR = prevLabsDir;
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

runTests().catch((err) => {
  console.error(err);
  process.exit(1);
});
