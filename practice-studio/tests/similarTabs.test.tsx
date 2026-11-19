/**
 * Comprehensive tests for Similar Questions v2 (tab strip, state model, cycleStartedAt rule,
 * lazy v1 migration, scoring & review_items isolation, ARIA/keyboard nav, deep links,
 * Review & Sync + pagination tooltip, and binding scope change keeping worked example intact).
 * Run: npx tsx tests/similarTabs.test.tsx
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextRequest } from "next/server";
import { GET as variantGET } from "../src/app/api/variant/route";
import { POST as checkAnswerPOST } from "../src/app/api/check-answer/route";
import { SimilarTabStrip } from "../src/components/math/SimilarTabStrip";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { QuizPaginationBar } from "../src/components/QuizPaginationBar";
import {
  applyCheckResult,
  resetAnswerForReviewRetry,
} from "../src/lib/applyCheckResult";
import { readProgress } from "../src/lib/progress";
import { rowReason } from "../src/lib/reviewRow";
import {
  countCycleOriginalWrongAttempts,
  countPractisedSimilar,
  deriveRealTabStatus,
  deriveTabStatuses,
  nextTabIndexForKey,
  resolveInitialTab,
  resultCardActions,
  similarUnlock,
  type SimilarTabSummary,
} from "../src/lib/similarTabs";
import type { Problem, ProblemState } from "../src/types/drill";

const noop = () => {};

function baseState(overrides: Partial<ProblemState> = {}): ProblemState {
  return {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    lastCheck: null,
    attempts: [],
    ...overrides,
  };
}

function makeProblem(overrides: Partial<Problem> = {}): Problem {
  return {
    id: "Q02",
    templateKey: "c04-fraction-simplification-gcf",
    level: 1,
    levelLabel: "Level 1 - Foundation",
    category: "Fraction Simplification",
    prompt: "Multiply $\\frac{7}{8} \\times \\frac{4}{15}$ and simplify.",
    hasVariants: true,
    answerSpec: { type: "number" },
    checkpointHint: "Cancel common factors before multiplying.",
    state: baseState(),
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// 1. State model: similarUnlock & cycleStartedAt
// ---------------------------------------------------------------------------
{
  // Untried -> locked
  assert.equal(similarUnlock(baseState()), false);
  // Parse error / invalid input -> still locked
  assert.equal(
    similarUnlock(
      baseState({
        lastCheck: { verdict: "parse_error", message: "Bad syntax", components: [], diagnostics: [] },
        attempts: [{ input: "1//2", ts: "2026-11-19T10:00:00Z", verdict: "parse_error" }],
      })
    ),
    false
  );
  // 1 wrong -> unlocked
  assert.equal(
    similarUnlock(
      baseState({
        score: 0,
        lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
        attempts: [{ input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
      })
    ),
    true
  );
  // 1st-try correct -> unlocked (new in v2!)
  assert.equal(
    similarUnlock(
      baseState({
        score: 1,
        lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
        attempts: [{ input: "7/30", ts: "2026-11-19T10:00:00Z", verdict: "correct" }],
      })
    ),
    true
  );
  // Skipped -> unlocked
  assert.equal(similarUnlock(baseState({ skipped: true, score: 0 })), true);

  // Review retry sets cycleStartedAt -> strip is LOCKED again until a new attempt!
  const beforeRetry = baseState({
    userInput: "1/2",
    score: 0,
    lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
    attempts: [{ input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
    exampleViewedAt: "2026-11-19T10:05:00Z",
    similarSlots: ["va11111", "vb22222", "vc33333"],
    variants: {
      va11111: {
        role: "try",
        servedAt: "2026-11-19T10:01:00Z",
        attempts: [{ input: "1/4", ts: "2026-11-19T10:02:00Z", verdict: "correct", kind: "variant" }],
      },
    },
  });
  const afterRetry = resetAnswerForReviewRetry(beforeRetry, "2026-11-20T09:00:00Z");
  assert.equal(afterRetry.cycleStartedAt, "2026-11-20T09:00:00Z");
  assert.equal(similarUnlock(afterRetry), false, "strip must be hidden again after review retry");
  assert.equal(countCycleOriginalWrongAttempts(afterRetry), 0, "prior cycle wrongs must not count");
  assert.equal(countPractisedSimilar(afterRetry), 0, "prior cycle similar attempts must not count");
  assert.deepEqual(
    deriveTabStatuses(afterRetry).map((t) => t.status),
    ["untried", "untried", "untried"],
    "prior cycle similar statuses must reset to untried in the new cycle"
  );

  // Scoring in the new review cycle: first-try correct scores 1.0 even though prior cycle had wrong + example!
  const retryCorrect = applyCheckResult(
    makeProblem({ state: afterRetry }),
    "7/30",
    { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
    [],
    { ts: "2026-11-20T09:01:00Z" }
  );
  assert.equal(retryCorrect.score, 1, "first-try correct in a new review cycle must score 1.0");
  assert.equal(similarUnlock(retryCorrect), true, "new-cycle attempt unlocks the strip");

  // Wrong in the new cycle then correct in the new cycle -> scores 0.5
  const retryWrong = applyCheckResult(
    makeProblem({ state: afterRetry }),
    "1/5",
    { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
    [],
    { ts: "2026-11-20T09:01:00Z" }
  );
  const retrySecondTry = applyCheckResult(
    makeProblem({ state: retryWrong }),
    "7/30",
    { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
    [],
    { ts: "2026-11-20T09:02:00Z" }
  );
  assert.equal(retrySecondTry.score, 0.5, "correct after a new-cycle wrong must cap at 0.5");
}

// ---------------------------------------------------------------------------
// 2. Tab statuses, countPractisedSimilar, deep links, keyboard nav, resultCardActions
// ---------------------------------------------------------------------------
{
  const stateWithTabs = baseState({
    score: 1,
    lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
    attempts: [{ input: "7/30", ts: "2026-11-19T10:00:00Z", verdict: "correct" }],
    similarSlots: ["va11111", "vb22222", "vc33333"],
    variants: {
      va11111: {
        role: "try",
        servedAt: "2026-11-19T10:01:00Z",
        attempts: [{ input: "1/8", ts: "2026-11-19T10:02:00Z", verdict: "correct", kind: "variant" }],
      },
      vb22222: {
        role: "try",
        servedAt: "2026-11-19T10:03:00Z",
        attempts: [{ input: "9/9", ts: "2026-11-19T10:04:00Z", verdict: "incorrect", kind: "variant" }],
      },
      vc33333: {
        role: "try",
        servedAt: "",
        attempts: [],
      },
      vex9999: {
        role: "example",
        servedAt: "2026-11-19T10:05:00Z",
        attempts: [],
      },
    },
  });
  assert.equal(deriveRealTabStatus(stateWithTabs), "correct");
  assert.equal(
    deriveRealTabStatus(baseState({
      score: 0.5,
      lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
      attempts: [
        { input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
        { input: "7/30", ts: "2026-11-19T10:01:00Z", verdict: "correct" },
      ],
    })),
    "assisted"
  );
  const statuses = deriveTabStatuses(stateWithTabs);
  assert.deepEqual(
    statuses.map((s) => s.status),
    ["correct", "wrong", "untried"]
  );
  assert.equal(countPractisedSimilar(stateWithTabs), 2, "example record must not count toward Practised N similar");

  // Deep-link resolution: ?similar=1 opens first untried when unlocked; locked -> "q"
  assert.equal(
    resolveInitialTab({ unlocked: true, tabs: statuses, similarParam: true }),
    "s3",
    "?similar=1 must open the first untried similar tab (s3)"
  );
  assert.equal(
    resolveInitialTab({ unlocked: false, tabs: statuses, similarParam: true }),
    "q",
    "?similar=1 while locked must stay on Question tab"
  );
  assert.equal(
    resolveInitialTab({ unlocked: true, tabs: statuses, tabParam: "s2" }),
    "s2",
    "?tab=s2 restores Similar 2"
  );
  assert.equal(
    resolveInitialTab({ unlocked: true, tabs: statuses, tabParam: "example" }),
    "q",
    "?tab=example (out of scope) must fall back to Question tab"
  );
  assert.equal(
    resolveInitialTab({ unlocked: false, tabs: statuses, tabParam: "s2" }),
    "q",
    "?tab=s2 while locked must fall back to Question tab"
  );

  // Manual-activation keyboard navigation
  assert.equal(nextTabIndexForKey("ArrowRight", 0, 4), 1);
  assert.equal(nextTabIndexForKey("ArrowRight", 3, 4), 0, "ArrowRight wraps from last to first");
  assert.equal(nextTabIndexForKey("ArrowLeft", 0, 4), 3, "ArrowLeft wraps from first to last");
  assert.equal(nextTabIndexForKey("Home", 2, 4), 0);
  assert.equal(nextTabIndexForKey("End", 1, 4), 3);
  assert.equal(nextTabIndexForKey("Enter", 1, 4), null);

  // resultCardActions: R wrong #1 vs wrong #2 vs all-3-correct vs R correct vs Similar correct/wrong
  const rWrong1 = resultCardActions({
    tab: "q",
    hasVariants: true,
    rState: baseState({
      score: 0,
      lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
      attempts: [{ input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
    }),
    statuses,
    exampleViewed: false,
  });
  assert.equal(rWrong1.retryLabel, "Try again (max 0.5)");
  assert.equal(rWrong1.showPractiseSimilarFirst, true);
  assert.equal(rWrong1.targetSimilarSlot, 3);
  assert.equal(rWrong1.showSeeExample, false, "no worked example link after only 1 wrong on R");
  assert.match(rWrong1.footnote || "", /scores 0\.5/);

  const allCorrectStatuses: SimilarTabSummary[] = [
    { token: "va11111", slot: 1, status: "correct" },
    { token: "vb22222", slot: 2, status: "correct" },
    { token: "vc33333", slot: 3, status: "correct" },
  ];
  const rWrongAllDone = resultCardActions({
    tab: "q",
    hasVariants: true,
    rState: baseState({
      score: 0,
      lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
      attempts: [
        { input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
        { input: "1/3", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
      ],
    }),
    statuses: allCorrectStatuses,
    exampleViewed: false,
  });
  assert.equal(rWrongAllDone.showPractiseSimilarFirst, false, "hidden when all 3 similar tabs are correct");
  assert.equal(rWrongAllDone.showSeeExample, true, "worked example entry appears at 2 wrongs on R");

  const simCorrect = resultCardActions({
    tab: "s1",
    hasVariants: true,
    rState: stateWithTabs,
    statuses,
    exampleViewed: false,
    activeSimilarToken: "va11111",
    activeSimilarVerdict: "correct",
  });
  assert.equal(simCorrect.showNextSimilar, true);
  assert.equal(simCorrect.nextSimilarSlot, 3);

  const simCorrectNoUntried = resultCardActions({
    tab: "s1",
    hasVariants: true,
    rState: stateWithTabs,
    statuses: allCorrectStatuses,
    exampleViewed: false,
    activeSimilarToken: "va11111",
    activeSimilarVerdict: "correct",
  });
  assert.equal(simCorrectNoUntried.showNextSimilar, false, "Next similar hidden when no other tab is untried");

  const simWrong = resultCardActions({
    tab: "s2",
    hasVariants: true,
    rState: stateWithTabs,
    statuses,
    exampleViewed: false,
    activeSimilarToken: "vb22222",
    activeSimilarVerdict: "incorrect",
    similarStepsOpen: false,
  });
  assert.equal(simWrong.retryLabel, "Try again");
  assert.equal(simWrong.showSimilarShowSteps, true);
  assert.equal(simWrong.showSimilarBackLink, true);
}

// ---------------------------------------------------------------------------
// 3. SimilarTabStrip ARIA, roving tabIndex, status labels, mobile targets, NO Example tab
// ---------------------------------------------------------------------------
{
  const tabs: SimilarTabSummary[] = [
    { token: "va11111", slot: 1, status: "correct" },
    { token: "vb22222", slot: 2, status: "untried" },
    { token: "vc33333", slot: 3, status: "partial" },
  ];
  const html = renderToStaticMarkup(
    <SimilarTabStrip
      problemId="Q02"
      questionNumber={2}
      realStatus="wrong"
      tabs={tabs}
      selectedTab="s1"
      onSelectTab={noop}
    />
  );
  assert.match(html, /role="tablist"/);
  assert.match(html, /aria-label="Question 2 and similar questions"/);
  assert.match(html, /id="tab-Q02-q"[^>]*aria-selected="false"[^>]*aria-controls="panel-Q02"/);
  assert.match(html, /aria-label="Question 2, not correct yet"/);
  assert.match(html, /id="tab-Q02-s1"[^>]*aria-selected="true"[^>]*aria-controls="panel-Q02"[^>]*aria-label="Similar question 1, correct"[^>]*tabindex="0"/);
  assert.match(html, /id="tab-Q02-s2"[^>]*aria-selected="false"[^>]*aria-controls="panel-Q02"[^>]*aria-label="Similar question 2, not tried"[^>]*tabindex="-1"/);
  assert.match(html, /id="tab-Q02-s3"[^>]*aria-selected="false"[^>]*aria-controls="panel-Q02"[^>]*aria-label="Similar question 3, almost"[^>]*tabindex="-1"/);
  assert.match(html, /min-h-\[44px\]/, "mobile tabs must be at least 44px tall");
  assert.match(html, /Q2/, "mobile compact label Q2");
  assert.doesNotMatch(html, /tab-Q02-example/, "Example tab must NOT be rendered (binding scope change)");
  assert.doesNotMatch(html, /Shown in example/i, "Shown in example must NOT exist (binding scope change)");
}

// ---------------------------------------------------------------------------
// 4. MathWorkspace SSR states (R wrong #1, R wrong #2, R correct, bank empty, review retry)
// ---------------------------------------------------------------------------
{
  const slots = ["va11111", "vb22222", "vc33333"];
  const wrong1Html = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({
        state: baseState({
          userInput: "1/2",
          score: 0,
          lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
          attempts: [{ input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
          similarSlots: slots,
        }),
      })}
      drillId="DRL-MTH-T01-C04-01"
      index={1}
      totalQuestions={6}
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
  assert.match(wrong1Html, /role="tablist"/);
  assert.match(wrong1Html, /role="tabpanel"/);
  assert.match(wrong1Html, /Try again \(max 0\.5\)/);
  assert.match(wrong1Html, /Practise a similar question first/);
  assert.match(wrong1Html, /A correct answer now scores 0\.5\. Similar questions are practice/);
  assert.doesNotMatch(wrong1Html, /See a worked example/);
  assert.doesNotMatch(wrong1Html, /Resume similar question/);

  const wrong2Html = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({
        state: baseState({
          userInput: "1/3",
          score: 0,
          lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
          attempts: [
            { input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
            { input: "1/3", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
          ],
          similarSlots: slots,
        }),
      })}
      drillId="DRL-MTH-T01-C04-01"
      index={1}
      totalQuestions={6}
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
  assert.match(wrong2Html, /See a worked example/, "existing worked example entry appears after 2 wrongs on R");

  const correctHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({
        state: baseState({
          userInput: "7/30",
          score: 1,
          lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
          attempts: [{ input: "7/30", ts: "2026-11-19T10:00:00Z", verdict: "correct" }],
          similarSlots: slots,
        }),
      })}
      drillId="DRL-MTH-T01-C04-01"
      index={1}
      totalQuestions={6}
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
  assert.match(correctHtml, /role="tablist"/);
  assert.match(correctHtml, /Practise a similar question for confidence/);
  assert.match(correctHtml, /Similar questions don&#x27;t change your score\./);

  // Bank empty: no strip, no links, no footnote
  const noBankHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({
        hasVariants: false,
        state: baseState({
          userInput: "1/2",
          score: 0,
          lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
          attempts: [{ input: "1/2", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
        }),
      })}
      drillId="DRL-MTH-T01-C04-01"
      index={1}
      totalQuestions={6}
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
  assert.doesNotMatch(noBankHtml, /role="tablist"/);
  assert.doesNotMatch(noBankHtml, /Practise a similar question/);
  assert.doesNotMatch(noBankHtml, /Similar questions/);
}

// ---------------------------------------------------------------------------
// 5. Review & Sync ("Practised N similar") + Pagination tooltip (", practised N similar")
// ---------------------------------------------------------------------------
{
  const practisedProblem = makeProblem({
    state: baseState({
      score: 1,
      lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
      attempts: [{ input: "7/30", ts: "2026-11-19T10:00:00Z", verdict: "correct" }],
      similarSlots: ["va11111", "vb22222", "vc33333"],
      variants: {
        va11111: {
          role: "try",
          servedAt: "2026-11-19T10:01:00Z",
          attempts: [{ input: "1/8", ts: "2026-11-19T10:02:00Z", verdict: "correct", kind: "variant" }],
        },
        vb22222: {
          role: "try",
          servedAt: "2026-11-19T10:03:00Z",
          attempts: [{ input: "1/9", ts: "2026-11-19T10:04:00Z", verdict: "incorrect", kind: "variant" }],
        },
        vex9999: {
          role: "example",
          servedAt: "2026-11-19T10:05:00Z",
          attempts: [],
        },
      },
    }),
  });
  assert.equal(
    rowReason(practisedProblem, "correct_first", false, false),
    "First try · Practised 2 similar"
  );
  assert.equal(
    rowReason(practisedProblem, "correct_first", true, false),
    "Passed",
    "Code rows must never append Practised N similar"
  );

  const pagHtml = renderToStaticMarkup(
    <QuizPaginationBar
      currentIndex={0}
      problems={[practisedProblem]}
      viewMode="quiz"
      workspace="math"
      onSelectQuestion={noop}
      onToggleViewMode={noop}
    />
  );
  assert.match(
    pagHtml,
    /title="Question 1 — Correct on first attempt \(1\), practised 2 similar"/
  );
  assert.match(
    pagHtml,
    /aria-label="Question 1 — Correct on first attempt \(1\), practised 2 similar"/
  );
  assert.match(pagHtml, /bg-emerald-700/, "tile colour must come from R only (emerald for 1.0)");
}

// ---------------------------------------------------------------------------
// 6. Lazy v1 migration fixture (activeVariant + role:"try" + role:"example")
// ---------------------------------------------------------------------------
async function testV1Migration() {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-v1-migrate-"));
  const drillsDir = path.join(base, "drills");
  const variantsDir = path.join(base, "variants");
  const progressDir = path.join(base, "progress");
  fs.mkdirSync(path.join(drillsDir, "MTH-T01-C04"), { recursive: true });
  fs.mkdirSync(variantsDir, { recursive: true });
  fs.mkdirSync(progressDir, { recursive: true });

  const prevDrills = process.env.DRILLS_DATA_DIR;
  const prevVariants = process.env.VARIANTS_DIR;
  const prevProgress = process.env.PROGRESS_DIR;
  process.env.DRILLS_DATA_DIR = drillsDir;
  process.env.VARIANTS_DIR = variantsDir;
  process.env.PROGRESS_DIR = progressDir;

  try {
    fs.writeFileSync(
      path.join(drillsDir, "MTH-T01-C04", "DRL-MTH-T01-C04-88.json"),
      JSON.stringify({
        schemaVersion: "2.0-math",
        drillId: "DRL-MTH-T01-C04-88",
        subject: "MATH",
        unitCode: "MTH-T01-C04",
        unitTitle: "Fractions",
        chapterCode: "MTH-T01-C04",
        topicCode: "MTH-T01",
        problems: [
          {
            id: "Q01",
            level: 1,
            levelLabel: "Level 1",
            category: "Fractions",
            archetypeKey: "c04-fraction-simplification-gcf",
            templateKey: "c04-fraction-simplification-gcf",
            prompt: "Simplify $\\frac{27}{45}$.",
            answerSpec: { type: "number", value: "3/5" },
            answerPlain: "3/5",
            answerDisplay: "\\frac{3}{5}",
            checkpointHint: "Find GCD.",
            steps: [{ explain: "Divide by 9." }],
          },
        ],
      }),
      "utf-8"
    );

    fs.writeFileSync(
      path.join(variantsDir, "MTH-T01-C04.json"),
      JSON.stringify({
        unitCode: "MTH-T01-C04",
        variants: [
          {
            variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
            archetypeKey: "c04-fraction-simplification-gcf",
            level: 1,
            prompt: "Reduce $\\frac{88}{165}$.",
            answerSpec: { type: "number", value: "8/15" },
            answerPlain: "8/15",
            answerDisplay: "\\frac{8}{15}",
            checkpointHint: "Divide by 11.",
            steps: [{ explain: "Divide by 11." }],
          },
          {
            variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
            archetypeKey: "c04-fraction-simplification-gcf",
            level: 1,
            prompt: "Reduce $\\frac{42}{90}$.",
            answerSpec: { type: "number", value: "7/15" },
            answerPlain: "7/15",
            answerDisplay: "\\frac{7}{15}",
            checkpointHint: "Divide by 6.",
            steps: [{ explain: "Divide by 6." }],
          },
          {
            variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-03",
            archetypeKey: "c04-fraction-simplification-gcf",
            level: 1,
            prompt: "Reduce $\\frac{36}{60}$.",
            answerSpec: { type: "number", value: "3/5" },
            answerPlain: "3/5",
            answerDisplay: "\\frac{3}{5}",
            checkpointHint: "Divide by 12.",
            steps: [{ explain: "Divide by 12." }],
          },
        ],
      }),
      "utf-8"
    );

    // Seed a v1 progress file: activeVariant="v1", v1 points to bank variant 02, v2 is role:"example"
    fs.writeFileSync(
      path.join(progressDir, "DRL-MTH-T01-C04-88.json"),
      JSON.stringify({
        drillId: "DRL-MTH-T01-C04-88",
        unitCode: "MTH-T01-C04",
        problems: {
          Q01: {
            userInput: "1/2",
            score: 0,
            divergedStep: null,
            mistakes: [],
            lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
            attempts: [{ input: "1/2", ts: "2026-11-18T10:00:00Z", verdict: "incorrect" }],
            activeVariant: "v1",
            exampleViewedAt: "2026-11-18T10:05:00Z",
            variants: {
              v1: {
                variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
                role: "try",
                attempts: [
                  { input: "7/15", ts: "2026-11-18T10:02:00Z", verdict: "correct", kind: "variant" },
                ],
                hintsRevealed: 0,
                setupRevealed: false,
                stepsRevealed: false,
                durationMs: 5000,
                servedAt: "2026-11-18T10:01:00Z",
              },
              v2: {
                variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-03",
                role: "example",
                attempts: [],
                hintsRevealed: 0,
                setupRevealed: false,
                stepsRevealed: false,
                durationMs: 0,
                servedAt: "2026-11-18T10:05:00Z",
              },
            },
          },
        },
      }),
      "utf-8"
    );

    // First mode=list lazily migrates v1 state
    const listRes = await variantGET(
      new NextRequest(
        "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-88&qid=Q01&mode=list"
      )
    );
    assert.equal(listRes.status, 200);
    const listData = (await listRes.json()) as {
      unlocked: boolean;
      tabs: Array<{ token: string; slot: number; status: string }>;
    };
    assert.equal(listData.unlocked, true);
    assert.equal(listData.tabs.length, 3);
    // Bank variant 02 was v1, so slot 2 keeps token "v1" and status "correct"!
    assert.equal(listData.tabs[1].token, "v1");
    assert.equal(listData.tabs[1].status, "correct");
    assert.equal(listData.tabs[0].status, "untried");
    assert.equal(listData.tabs[2].status, "untried");

    // Disk state: activeVariant deleted, similarSlots persisted, role:"example" record preserved
    const migrated = readProgress("DRL-MTH-T01-C04-88")?.problems?.Q01 as Record<string, unknown>;
    assert.equal(migrated.activeVariant, undefined, "activeVariant must be deleted on migration");
    assert.deepEqual(migrated.similarSlots, listData.tabs.map((t) => t.token));
    assert.ok(
      (migrated.variants as Record<string, { role: string }>).v2?.role === "example",
      "existing v1 example record must be preserved"
    );

    // Old v1 token stays valid for mode=open and check-answer!
    const openOld = await variantGET(
      new NextRequest(
        "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-88&qid=Q01&mode=open&token=v1"
      )
    );
    assert.equal(openOld.status, 200);
    const openOldData = (await openOld.json()) as {
      slot: number;
      session: { durationMs: number; attempts: unknown[] };
    };
    assert.equal(openOldData.slot, 2);
    assert.equal(openOldData.session.durationMs, 5000);
    assert.equal(openOldData.session.attempts.length, 1);

    const chkOld = await checkAnswerPOST(
      new NextRequest("http://127.0.0.1:3000/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId: "DRL-MTH-T01-C04-88",
          qid: "Q01",
          variantToken: "v1",
          input: "7/15",
        }),
      })
    );
    assert.equal(chkOld.status, 200);
    assert.equal((await chkOld.json()).verdict, "correct");
  } finally {
    if (prevDrills === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrills;
    if (prevVariants === undefined) delete process.env.VARIANTS_DIR;
    else process.env.VARIANTS_DIR = prevVariants;
    if (prevProgress === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgress;
    fs.rmSync(base, { recursive: true, force: true });
  }
}

testV1Migration()
  .then(() => {
    console.log("PASS: similarTabs.test.tsx (state model, cycle rule, migration, ARIA, copy, deep link, Review & Sync)");
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
