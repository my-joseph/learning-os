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
import { GET as drillGET } from "../src/app/api/drill/route";
import { GET as revealGET, POST as revealPOST } from "../src/app/api/reveal/route";
import { POST as reviewItemsPOST } from "../src/app/api/review-items/route";
import { POST as saveStatePOST } from "../src/app/api/save-state/route";
import { GET as variantGET, POST as variantPOST } from "../src/app/api/variant/route";
import { POST as checkAnswerPOST } from "../src/app/api/check-answer/route";
import { SimilarTabStrip } from "../src/components/math/SimilarTabStrip";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { QuizPaginationBar } from "../src/components/QuizPaginationBar";
import { Tabs, TabsList, TabsTrigger } from "../src/components/ui/shadcn/Tabs";
import {
  SIMILAR_LIST_ERROR_MESSAGE,
  SIMILAR_LIST_RETRY_DELAYS_MS,
  applySimilarCheckToLatestProblem,
  applySimilarHintToLatestProblem,
  executeSimilarStepsReveal,
  getSimilarListRetryDelayMs,
  shouldPersistVariantStepsReveal,
} from "../src/hooks/useSimilarTabs";
import {
  applyCheckResult,
  resetAnswerForReviewRetry,
} from "../src/lib/applyCheckResult";
import { readProgress } from "../src/lib/progress";
import { rowReason } from "../src/lib/reviewRow";
import {
  executeReviewItemCheck,
  prepareProblemForReviewItem,
} from "../src/lib/reviewSession";
import { createTelemetryTimerState } from "../src/lib/telemetryTimer";
import { statusTone } from "../src/lib/statusTone";
import {
  countCycleOriginalWrongAttempts,
  countPractisedSimilar,
  deriveRealTabStatus,
  deriveTabStatuses,
  deriveVariantStatus,
  nextTabIndexForKey,
  resolveInitialTab,
  resultCardActions,
  similarUnlock,
  type SimilarTabSummary,
} from "../src/lib/similarTabs";
import type { DrillDocument, Problem, ProblemState } from "../src/types/drill";

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
  // Skipped in a previous cycle + new cycleStartedAt -> still locked until a new attempt
  const skippedPrevCycle = baseState({
    skipped: true,
    score: 0,
    attempts: [{ input: "(Skipped)", ts: "2026-11-01T10:00:00Z", verdict: "skipped" }],
    cycleStartedAt: "2026-11-20T09:00:00Z",
  });
  assert.equal(
    similarUnlock(skippedPrevCycle),
    false,
    "prior-cycle skip must not unlock the strip after cycleStartedAt"
  );
  assert.equal(deriveRealTabStatus(skippedPrevCycle), "untried");
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
  assert.equal(deriveRealTabStatus(baseState({ hintsRevealed: 1 })), "usedHelp");
  assert.equal(deriveRealTabStatus(baseState({ setupRevealedBeforeAnswer: true })), "usedHelp");
  assert.equal(deriveRealTabStatus(baseState({ solutionRevealedBeforeAnswer: true })), "usedHelp");
  assert.equal(deriveRealTabStatus(baseState({ skipped: true, score: 0 })), "skipped");

  assert.equal(
    deriveVariantStatus({
      role: "try",
      servedAt: "2026-11-19T10:01:00Z",
      attempts: [],
      stepsRevealed: true,
    }),
    "usedHelp",
    "revealing steps before answering marks similar question as usedHelp"
  );
  assert.equal(
    deriveVariantStatus({
      role: "try",
      servedAt: "2026-11-19T10:01:00Z",
      attempts: [],
      hintsRevealed: 1,
    }),
    "usedHelp",
    "revealing hint before answering marks similar question as usedHelp"
  );
  assert.equal(
    deriveVariantStatus({
      role: "try",
      servedAt: "2026-11-19T10:01:00Z",
      attempts: [],
      setupRevealed: true,
    }),
    "usedHelp",
    "revealing equation set-up before answering marks similar question as usedHelp"
  );
  assert.equal(
    deriveVariantStatus({
      role: "try",
      servedAt: "2026-11-19T10:01:00Z",
      attempts: [{ input: "1/8", ts: "2026-11-19T10:02:00Z", verdict: "correct", kind: "variant" }],
      stepsRevealed: true,
    }),
    "assisted",
    "answering similar correctly after revealing steps marks it assisted"
  );
  assert.equal(
    deriveVariantStatus({
      role: "try",
      servedAt: "2026-11-19T10:01:00Z",
      attempts: [
        { input: "9/8", ts: "2026-11-19T10:02:00Z", verdict: "incorrect", kind: "variant" },
        { input: "1/8", ts: "2026-11-19T10:03:00Z", verdict: "correct", kind: "variant" },
      ],
    }),
    "assisted",
    "wrong then correct on a similar question must score assisted (same rule as main question)"
  );
  // B4: bounded backoff schedule for failed mode=list fetches
  assert.equal(getSimilarListRetryDelayMs(0), null);
  assert.equal(getSimilarListRetryDelayMs(1), SIMILAR_LIST_RETRY_DELAYS_MS[0]);
  assert.equal(getSimilarListRetryDelayMs(2), SIMILAR_LIST_RETRY_DELAYS_MS[1]);
  assert.equal(
    getSimilarListRetryDelayMs(SIMILAR_LIST_RETRY_DELAYS_MS.length + 1),
    null,
    "auto-retry backoff must stop after bounded attempts"
  );
  const useSimilarSrc = fs.readFileSync("src/hooks/useSimilarTabs.ts", "utf8");
  assert.match(
    useSimilarSrc,
    /const scheduleFailureRetry = \(\) => \{[\s\S]*?fetchedListKeyRef\.current = null;[\s\S]*?setListError\(SIMILAR_LIST_ERROR_MESSAGE\);/,
    "B4: failed variant list fetch must clear fetchedListKeyRef, surface quiet error, and schedule backoff retry"
  );
  assert.match(
    useSimilarSrc,
    /pendingTabRef\.current = nextTabId;[\s\S]*?retrySimilarList\(\)/,
    "B4: clicking Practise a similar question while list is unloaded must queue tab and retry list"
  );
  assert.equal(
    deriveVariantStatus(
      {
        role: "try",
        servedAt: "2026-11-18T10:01:00Z",
        attempts: [],
        stepsRevealed: true,
      },
      "2026-11-19T10:00:00Z"
    ),
    "untried",
    "prior-cycle help must reset to untried in a new review cycle"
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
// 3. SimilarTabStrip ARIA, roving tabIndex, unified status icons, locked ghost tabs, NO Example tab
// ---------------------------------------------------------------------------
{
  const tabs: SimilarTabSummary[] = [
    { token: "va11111", slot: 1, status: "correct" },
    { token: "vb22222", slot: 2, status: "untried" },
    { token: "vc33333", slot: 3, status: "assisted" },
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
  assert.match(html, /<button(?=[^>]*id="tab-Q02-q")(?=[^>]*aria-selected="false")(?=[^>]*aria-controls="panel-Q02")[^>]*>/);
  function assertMark(markup: string, status: string, tone: string) {
    const tag = markup.match(new RegExp(`<span(?=[^>]*data-status="${status}")[^>]*>`))?.[0];
    assert.ok(tag, `Expected a ${status} status marker`);
    const classes = tag.match(/class="([^"]+)"/)?.[1].split(" ") ?? [];
    for (const cls of ["size-space-4", "rounded-full", ...tone.split(" ")]) {
      assert.ok(classes.includes(cls), `${status} status marker uses ${cls}`);
    }
  }
  assert.match(html, /aria-label="Question 2, not correct yet"/);
  assertMark(html, "wrong", statusTone.wrong.tabMark);
  assert.match(html, /<button(?=[^>]*id="tab-Q02-s1")(?=[^>]*aria-selected="true")(?=[^>]*aria-controls="panel-Q02")(?=[^>]*aria-label="Similar question 1, correct")(?=[^>]*tabindex="0")[^>]*>/);
  assertMark(html, "correct", statusTone.correct.tabMark);
  assert.match(html, /<button(?=[^>]*id="tab-Q02-s2")(?=[^>]*aria-selected="false")(?=[^>]*aria-controls="panel-Q02")(?=[^>]*aria-label="Similar question 2, not tried")(?=[^>]*tabindex="-1")[^>]*>/);
  assertMark(html, "untried", statusTone.notTried.tabMark);
  assert.match(html, /<button(?=[^>]*id="tab-Q02-s3")(?=[^>]*aria-selected="false")(?=[^>]*aria-controls="panel-Q02")(?=[^>]*aria-label="Similar question 3, correct with help")(?=[^>]*tabindex="-1")[^>]*>/);
  assertMark(html, "assisted", statusTone.assisted.tabMark);
  assert.match(html, /Q2/, "mobile compact label Q2");
  assert.doesNotMatch(html, /tab-Q02-example/, "Example tab must NOT be rendered (binding scope change)");
  assert.doesNotMatch(html, /Shown in example/i, "Shown in example must NOT exist (binding scope change)");

  // Skipped (dashed outline), usedHelp (plain outline like notTried, no colour), partial (assisted pale green)
  const skippedAndHelpHtml = renderToStaticMarkup(
    <SimilarTabStrip
      problemId="Q03"
      questionNumber={3}
      realStatus="skipped"
      tabs={[
        { token: "va11111", slot: 1, status: "usedHelp" },
        { token: "vb22222", slot: 2, status: "partial" },
      ]}
      selectedTab="q"
      onSelectTab={noop}
    />
  );
  assert.match(skippedAndHelpHtml, /aria-label="Question 3, skipped"/);
  assertMark(skippedAndHelpHtml, "skipped", statusTone.skipped.tabMark);
  assert.match(skippedAndHelpHtml, /aria-label="Similar question 1, used help"/);
  assertMark(skippedAndHelpHtml, "usedHelp", statusTone.notTried.tabMark);
  assert.match(skippedAndHelpHtml, /aria-label="Similar question 2, almost"/);
  assertMark(skippedAndHelpHtml, "partial", statusTone.assisted.tabMark);

  // Locked ghost tabs before first attempt (zero-leak: no tokens, aria-disabled="true", Answer Question N first)
  const lockedStripHtml = renderToStaticMarkup(
    <SimilarTabStrip
      problemId="Q02"
      questionNumber={2}
      realStatus="untried"
      tabs={[]}
      selectedTab="q"
      locked
      onSelectTab={noop}
    />
  );
  assert.match(lockedStripHtml, /id="similar-lock-desc-Q02"[^>]*>Answer Question 2 first<\/span>/);
  assert.match(
    lockedStripHtml,
    /<button(?=[^>]*id="tab-Q02-s1")(?=[^>]*aria-selected="false")(?=[^>]*aria-disabled="true")(?=[^>]*aria-label="Similar question 1")(?=[^>]*aria-describedby="similar-lock-desc-Q02")(?=[^>]*title="Answer Question 2 first")(?=[^>]*tabindex="-1")[^>]*>/
  );
  assert.match(lockedStripHtml, /id="tab-Q02-s2"[^>]*aria-disabled="true"/);
  assert.match(lockedStripHtml, /id="tab-Q02-s3"[^>]*aria-disabled="true"/);
  assert.match(lockedStripHtml, /cursor-not-allowed/);

  // Square corners on SimilarTabStrip (underline variant) vs rounded corners on default segmented Tabs
  for (const stripMarkup of [html, lockedStripHtml]) {
    const stripListTag = stripMarkup.match(/<div\b[^>]*\brole="tablist"[^>]*>/)?.[0] ?? "";
    assert.match(stripListTag, /\brounded-none\b/, "SimilarTabStrip TabsList must use rounded-none");
    assert.doesNotMatch(
      stripListTag,
      /\brounded-(?:md|lg|t-md)\b/,
      "SimilarTabStrip TabsList must not include rounded-md, rounded-lg, or rounded-t-md"
    );
    const stripTabs = stripMarkup.match(/<button\b[^>]*\brole="tab"[^>]*>/g) ?? [];
    assert.equal(stripTabs.length, 4);
    for (const tabTag of stripTabs) {
      assert.match(tabTag, /min-h-touch/, "each selected, unselected and locked tab keeps a 44px minimum");
      assert.match(tabTag, /sm:h-space-9 sm:min-h-0/, "each tab is 36px high on desktop");
      assert.match(tabTag, /\brounded-none\b/, "SimilarTabStrip tab trigger must use rounded-none");
      assert.doesNotMatch(
        tabTag,
        /\brounded-(?:md|lg|t-md)\b/,
        "SimilarTabStrip tab trigger must not include rounded-md, rounded-lg, or rounded-t-md"
      );
    }
  }

  const defaultTabsHtml = renderToStaticMarkup(
    <Tabs defaultValue="drills">
      <TabsList aria-label="Default segmented tabs">
        <TabsTrigger value="drills">Drills</TabsTrigger>
        <TabsTrigger value="labs">Labs</TabsTrigger>
      </TabsList>
    </Tabs>
  );
  const defaultListTag = defaultTabsHtml.match(/<div\b[^>]*\brole="tablist"[^>]*>/)?.[0] ?? "";
  assert.match(defaultListTag, /\brounded-lg\b/, "Default TabsList must include rounded-lg");
  assert.doesNotMatch(defaultListTag, /\brounded-none\b/);
  const defaultTriggers = defaultTabsHtml.match(/<button\b[^>]*\brole="tab"[^>]*>/g) ?? [];
  assert.equal(defaultTriggers.length, 2);
  for (const triggerTag of defaultTriggers) {
    assert.match(triggerTag, /\brounded-md\b/, "Default TabsTrigger must include rounded-md");
    assert.doesNotMatch(triggerTag, /\brounded-none\b/);
  }

  const underlineTabsHtml = renderToStaticMarkup(
    <Tabs defaultValue="one">
      <TabsList variant="underline" aria-label="Underline tabs">
        <TabsTrigger value="one">One</TabsTrigger>
        <TabsTrigger value="two">Two</TabsTrigger>
      </TabsList>
    </Tabs>
  );
  const underlineListTag = underlineTabsHtml.match(/<div\b[^>]*\brole="tablist"[^>]*>/)?.[0] ?? "";
  assert.match(underlineListTag, /\brounded-none\b/, "Underline TabsList must include rounded-none");
  assert.doesNotMatch(underlineListTag, /\brounded-(?:md|lg|t-md)\b/);
  const underlineTriggers = underlineTabsHtml.match(/<button\b[^>]*\brole="tab"[^>]*>/g) ?? [];
  assert.equal(underlineTriggers.length, 2);
  for (const triggerTag of underlineTriggers) {
    assert.match(triggerTag, /\brounded-none\b/, "Underline TabsTrigger must include rounded-none");
    assert.doesNotMatch(triggerTag, /\brounded-(?:md|lg|t-md)\b/);
  }

  // B4: Unlocked strip with failed list load shows quiet error + Retry action instead of permanent "Answer Question N first" lock
  const listErrorStripHtml = renderToStaticMarkup(
    <SimilarTabStrip
      problemId="Q02"
      questionNumber={2}
      realStatus="wrong"
      tabs={[]}
      selectedTab="q"
      locked={false}
      listError={SIMILAR_LIST_ERROR_MESSAGE}
      onRetryList={noop}
      onSelectTab={noop}
    />
  );
  assert.match(listErrorStripHtml, /data-similar-list-error="true"/);
  assert.match(listErrorStripHtml, /Couldn&#x27;t load similar questions\./);
  assert.match(listErrorStripHtml, />Retry</);
  assert.doesNotMatch(
    listErrorStripHtml,
    /Answer Question 2 first/,
    "failed list load must NOT show locked 'Answer Question N first' tooltip"
  );
  assert.doesNotMatch(
    listErrorStripHtml,
    /aria-disabled="true"/,
    "failed list load must NOT render locked ghost tabs"
  );

  // Loading state while list is fetching after unlock must also not render fake lock tooltip
  const listLoadingStripHtml = renderToStaticMarkup(
    <SimilarTabStrip
      problemId="Q02"
      questionNumber={2}
      realStatus="wrong"
      tabs={[]}
      selectedTab="q"
      locked={false}
      loadingList={true}
      onSelectTab={noop}
    />
  );
  assert.match(listLoadingStripHtml, /Loading similar\.\.\./);
  assert.doesNotMatch(listLoadingStripHtml, /Answer Question 2 first/);
}

// ---------------------------------------------------------------------------
// 4. MathWorkspace SSR states (untouched locked strip, usedHelp before attempt, R wrong #1/#2, R correct, bank empty)
// ---------------------------------------------------------------------------
{
  // Unlocked question whose similarSlots have not loaded yet must NOT show locked ghost tabs
  const unlockedBeforeListHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({
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
      onInputChange={noop}
      onCheckAnswer={noop}
      onMarkDivergedStep={noop}
      onSetScore={noop}
      onToggleMistakeTag={noop}
      onMistakeNoteChange={noop}
      onResetProblem={noop}
    />
  );
  assert.doesNotMatch(
    unlockedBeforeListHtml,
    /Answer Question 2 first/,
    "answered question must not show locked 'Answer Question N first' even while tabs array is empty"
  );
  const untouchedHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({ similarCount: 3 })}
      drillId="DRL-MTH-T01-C04-01"
      index={1}
      totalQuestions={6}
      mistakeTags={[]}
      onInputChange={noop}
      onCheckAnswer={noop}
      onMarkDivergedStep={noop}
      onSetScore={noop}
      onToggleMistakeTag={noop}
      onMistakeNoteChange={noop}
      onResetProblem={noop}
    />
  );
  assert.match(untouchedHtml, /role="tablist"/, "strip must be visible before first attempt");
  assert.match(untouchedHtml, /aria-disabled="true"/, "similar tabs must be locked ghost tabs before attempt");
  assert.match(untouchedHtml, /Answer Question 2 first/);
  assert.match(untouchedHtml, /pt-2 sm:px-6 sm:pb-6 sm:pt-3/, "reduced top padding above strip");
  assert.doesNotMatch(untouchedHtml, /Level 1/, "Level N tag must not appear in card meta line");
  assert.doesNotMatch(untouchedHtml, /Practice only/i, "Practice only text must not appear");

  const usedHelpBeforeAttemptHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={makeProblem({
        state: baseState({ hintsRevealed: 1 }),
      })}
      drillId="DRL-MTH-T01-C04-01"
      index={1}
      totalQuestions={6}
      mistakeTags={[]}
      onInputChange={noop}
      onCheckAnswer={noop}
      onMarkDivergedStep={noop}
      onSetScore={noop}
      onToggleMistakeTag={noop}
      onMistakeNoteChange={noop}
      onResetProblem={noop}
    />
  );
  assert.match(usedHelpBeforeAttemptHtml, /aria-label="Question 2, used help"/);
  assertMark(usedHelpBeforeAttemptHtml, "usedHelp", statusTone.notTried.tabMark);
  assert.match(usedHelpBeforeAttemptHtml, /aria-disabled="true"/, "using help before answering must keep similar tabs locked");

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
      onInputChange={noop}
      onCheckAnswer={noop}
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
      onInputChange={noop}
      onCheckAnswer={noop}
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
      onInputChange={noop}
      onCheckAnswer={noop}
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
      onInputChange={noop}
      onCheckAnswer={noop}
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
    /title="Question 1, Level 1, correct, practised 2 similar, current"/
  );
  assert.match(
    pagHtml,
    /aria-label="Question 1, Level 1, correct, practised 2 similar, current"/
  );
  assert.match(pagHtml, /lucide-check/);
  assert.ok(
    pagHtml.includes(statusTone.correct.solidCircle),
    "stepper circle colour must come from R only (correct recipe for 1.0)"
  );
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

// ---------------------------------------------------------------------------
// 7. Review cycle isolation (/review item start + drill review retry)
// ---------------------------------------------------------------------------
async function testReviewCycleIsolation() {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-review-cycle-"));
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

  const drillId = "DRL-MTH-T01-C04-89";
  const unitCode = "MTH-T01-C04";

  try {
    fs.writeFileSync(
      path.join(drillsDir, unitCode, `${drillId}.json`),
      JSON.stringify({
        schemaVersion: "2.0-math",
        drillId,
        subject: "MATH",
        unitCode,
        unitTitle: "Fractions",
        chapterCode: unitCode,
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
            display: "\\frac{27}{45}",
            plainText: "27/45",
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
      path.join(variantsDir, `${unitCode}.json`),
      JSON.stringify({
        unitCode,
        variants: [
          {
            variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
            archetypeKey: "c04-fraction-simplification-gcf",
            level: 1,
            prompt: "Reduce $\\frac{88}{165}$.",
            display: "\\frac{88}{165}",
            plainText: "88/165",
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
            display: "\\frac{42}{90}",
            plainText: "42/90",
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
            display: "\\frac{36}{60}",
            plainText: "36/60",
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

    // Seed progress fixture from an earlier cycle: Q01 wrong, Similar 2 answered correctly, example viewed.
    fs.writeFileSync(
      path.join(progressDir, `${drillId}.json`),
      JSON.stringify({
        drillId,
        unitCode,
        updatedAt: "2026-11-01T10:05:00Z",
        problems: {
          Q01: {
            userInput: "1/2",
            score: 0,
            divergedStep: null,
            mistakes: [],
            lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
            attempts: [
              { input: "1/2", ts: "2026-11-01T10:00:00Z", verdict: "incorrect" },
            ],
            exampleViewedAt: "2026-11-01T10:05:00Z",
            similarSlots: ["va11111", "vb22222", "vc33333"],
            variants: {
              va11111: {
                variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
                role: "try",
                attempts: [],
                hintsRevealed: 0,
                setupRevealed: false,
                stepsRevealed: false,
                durationMs: 0,
                servedAt: "",
              },
              vb22222: {
                variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
                role: "try",
                attempts: [
                  { input: "7/15", ts: "2026-11-01T10:02:00Z", verdict: "correct", kind: "variant" },
                ],
                hintsRevealed: 1,
                setupRevealed: true,
                stepsRevealed: true,
                durationMs: 9000,
                servedAt: "2026-11-01T10:01:00Z",
              },
              vc33333: {
                variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-03",
                role: "try",
                attempts: [],
                hintsRevealed: 0,
                setupRevealed: false,
                stepsRevealed: false,
                durationMs: 0,
                servedAt: "",
              },
            },
          },
        },
      }),
      "utf-8"
    );

    // Sanity check: before the new review cycle starts, slot 2 is "assisted" (hints/setup/steps used) and Practised 1 similar.
    const preListRes = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
      )
    );
    const preList = (await preListRes.json()) as {
      unlocked: boolean;
      tabs: SimilarTabSummary[];
    };
    assert.equal(preList.unlocked, true);
    assert.deepEqual(
      preList.tabs.map((t) => t.status),
      ["untried", "assisted", "untried"]
    );
    assert.equal(
      countPractisedSimilar(readProgress(drillId)?.problems?.Q01 as ProblemState),
      1
    );

    // 7a. Start a new /review cycle: load /api/drill?review=1, prepare item, and start a server review cycle.
    const reviewDrillRes = await drillGET(
      new NextRequest(`http://127.0.0.1:3000/api/drill?id=${drillId}&review=1`)
    );
    assert.equal(reviewDrillRes.status, 200);
    const reviewDoc = (await reviewDrillRes.json()) as DrillDocument;
    const preparedQ1 = prepareProblemForReviewItem(reviewDoc.problems[0], {
      subject: "MTH",
      revisitNote: "",
    });
    assert.ok(
      typeof preparedQ1.state.cycleStartedAt === "string" && preparedQ1.state.cycleStartedAt,
      "prepareProblemForReviewItem must stamp cycleStartedAt"
    );
    const preparedReviewDoc: DrillDocument = { ...reviewDoc, problems: [preparedQ1] };

    const customFetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      const urlStr = typeof input === "string" ? input : input.toString();
      const method = (init?.method || "GET").toUpperCase();
      if (urlStr === "/api/variant" && method === "POST") {
        return variantPOST(
          new NextRequest("http://127.0.0.1:3000/api/variant", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: init?.body as string,
          })
        );
      }
      if (urlStr === "/api/check-answer" && method === "POST") {
        return checkAnswerPOST(
          new NextRequest("http://127.0.0.1:3000/api/check-answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: init?.body as string,
          })
        );
      }
      if (urlStr === "/api/save-state" && method === "POST") {
        return saveStatePOST(
          new NextRequest("http://127.0.0.1:3000/api/save-state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
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
            headers: { "Content-Type": "application/json" },
            body: init?.body as string,
          })
        );
      }
      throw new Error(`Unexpected fetch: ${method} ${urlStr}`);
    }) as typeof fetch;

    const startReview = await revealPOST(new NextRequest("http://127.0.0.1:3000/api/reveal", {
      method: "POST",
      body: JSON.stringify({ drillId, qid: "Q01", action: "start-review" }),
    }));
    assert.equal(startReview.status, 200);

    // Before the new review attempt: cycleStartedAt is persisted on disk, strip is hidden, mode=list locked.
    const stateBeforeReviewAttempt = readProgress(drillId)?.problems?.Q01 as ProblemState;
    assert.ok(stateBeforeReviewAttempt.cycleStartedAt);
    preparedQ1.state.cycleStartedAt = stateBeforeReviewAttempt.cycleStartedAt;
    assert.equal(similarUnlock(stateBeforeReviewAttempt), false);
    assert.equal(countPractisedSimilar(stateBeforeReviewAttempt), 0);

    const lockedListRes = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
      )
    );
    assert.deepEqual(await lockedListRes.json(), { unlocked: false, tabs: [] });

    const lockedOpenRes = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=open&token=vb22222`
      )
    );
    assert.equal(lockedOpenRes.status, 403, "mode=open must be 403 before new review attempt");

    const preReviewHtml = renderToStaticMarkup(
      <MathWorkspace
        problem={preparedQ1}
        drillId={drillId}
        index={0}
        totalQuestions={1}
        mistakeTags={[]}
        isReviewSession
        onInputChange={noop}
        onCheckAnswer={noop}
        onMarkDivergedStep={noop}
        onSetScore={noop}
        onToggleMistakeTag={noop}
        onMistakeNoteChange={noop}
        onResetProblem={noop}
      />
    );
    assert.match(
      preReviewHtml,
      /role="tablist"/,
      "strip must be visible on /review before the new review attempt (with locked ghost tabs)"
    );
    assert.match(
      preReviewHtml,
      /aria-disabled="true"[^>]*aria-label="Similar question 1"[^>]*aria-describedby="similar-lock-desc-Q01"[^>]*title="Answer Question 1 first"/,
      "similar tabs on /review must be locked ghost tabs before the new review attempt"
    );
    assert.doesNotMatch(
      preReviewHtml,
      /vb22222/,
      "zero-leak: no variant tokens in locked strip before new review attempt"
    );

    // 7b. Submit a wrong review attempt via executeReviewItemCheck: strip unlocks with ALL tabs "not tried".
    const reviewTimer = createTelemetryTimerState(`${drillId}/Q01`, true, false, 1_000);
    const reviewCheck = await executeReviewItemCheck({
      drillDoc: preparedReviewDoc,
      item: {
        drillId,
        qid: "Q01",
        unitCode,
        subject: "MATH",
        level: 1,
        dueDate: "2026-11-19",
        lastReviewed: "2026-11-01",
        commonTrapTag: null,
        revisitNote: "",
      },
      inputVal: "2/5",
      hintsUsed: 0,
      timerState: reviewTimer,
      now: 5_000,
      today: "2026-11-19",
      fetchFn: customFetch,
    });
    assert.ok(reviewCheck);
    assert.equal(reviewCheck.result.verdict, "incorrect");

    const stateAfterReviewAttempt = readProgress(drillId)?.problems?.Q01 as ProblemState;
    assert.equal(stateAfterReviewAttempt.cycleStartedAt, preparedQ1.state.cycleStartedAt);
    assert.equal(stateAfterReviewAttempt.attempts?.length, 2, "prior attempt preserved + new review attempt appended");
    assert.equal(similarUnlock(stateAfterReviewAttempt), true);
    assert.equal(countPractisedSimilar(stateAfterReviewAttempt), 0, "old similar attempts must not count in new cycle");
    assert.doesNotMatch(
      rowReason(makeProblem({ state: stateAfterReviewAttempt }), "wrong", false, false),
      /Practised/,
      "Review & Sync row must not count previous-cycle similar practice"
    );

    const postListRes = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
      )
    );
    const postList = (await postListRes.json()) as {
      unlocked: boolean;
      tabs: SimilarTabSummary[];
      exampleViewedAt: string | null;
    };
    assert.equal(postList.unlocked, true);
    assert.deepEqual(
      postList.tabs.map((t) => t.status),
      ["untried", "untried", "untried"],
      "mode=list must report all tabs untried after a new review attempt"
    );
    assert.equal(postList.exampleViewedAt, null, "prior-cycle exampleViewedAt must not bleed into new cycle");

    // Strip SSR with the post-attempt state shows all similar tabs as "not tried"
    const postReviewHtml = renderToStaticMarkup(
      <MathWorkspace
        problem={{ ...preparedQ1, state: stateAfterReviewAttempt }}
        drillId={drillId}
        index={0}
        totalQuestions={1}
        mistakeTags={[]}
        isReviewSession
        onInputChange={noop}
        onCheckAnswer={noop}
        onMarkDivergedStep={noop}
        onSetScore={noop}
        onToggleMistakeTag={noop}
        onMistakeNoteChange={noop}
        onResetProblem={noop}
      />
    );
    assert.match(postReviewHtml, /role="tablist"/);
    assert.match(postReviewHtml, /aria-label="Similar question 1, not tried"/);
    assert.match(postReviewHtml, /aria-label="Similar question 2, not tried"/);
    assert.match(postReviewHtml, /aria-label="Similar question 3, not tried"/);
    assert.doesNotMatch(postReviewHtml, /Similar question 2, correct/);

    // Opening Similar 2 in the new cycle starts clean (0 attempts, 0 duration, no revealed steps/setup).
    const openCleanRes = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=open&token=vb22222`
      )
    );
    assert.equal(openCleanRes.status, 200);
    const openClean = (await openCleanRes.json()) as {
      session: {
        attempts: unknown[];
        hintsRevealed: number;
        setupRevealed: boolean;
        stepsRevealed: boolean;
        durationMs: number;
      };
      revealed?: unknown;
    };
    assert.equal(openClean.session.attempts.length, 0);
    assert.equal(openClean.session.hintsRevealed, 0);
    assert.equal(openClean.session.setupRevealed, false);
    assert.equal(openClean.session.stepsRevealed, false);
    assert.equal(openClean.session.durationMs, 0);
    assert.equal(openClean.revealed, undefined);

    const stepsStillLockedRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${drillId}&q=Q01&variantToken=vb22222&part=steps`
      )
    );
    assert.equal(
      stepsStillLockedRes.status,
      403,
      "similar tab steps must stay locked in the new cycle until requested via reveal-steps or attempted"
    );

    // Clicking "Show steps" before answering (action: reveal-steps) unlocks steps and marks the similar tab as usedHelp!
    const preAnswerRevealStepsRes = await variantPOST(
      new NextRequest("http://127.0.0.1:3000/api/variant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId,
          qid: "Q01",
          variantToken: "va11111",
          action: "reveal-steps",
        }),
      })
    );
    assert.equal(preAnswerRevealStepsRes.status, 200);
    const preAnswerStepsPayloadRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${drillId}&q=Q01&variantToken=va11111&part=steps`
      )
    );
    assert.equal(
      preAnswerStepsPayloadRes.status,
      200,
      "steps must be available on a similar question before answering once reveal-steps is recorded"
    );
    const listAfterUsedHelp = (await (
      await variantGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
        )
      )
    ).json()) as { tabs: SimilarTabSummary[] };
    assert.deepEqual(
      listAfterUsedHelp.tabs.map((t) => t.status),
      ["usedHelp", "untried", "untried"],
      "revealing steps before answering must mark Similar 1 as usedHelp"
    );

    // Answering Similar 1 correctly after revealing steps marks it assisted;
    // answering Similar 2 correctly without help marks it correct.
    const sim1CheckRes = await checkAnswerPOST(
      new NextRequest("http://127.0.0.1:3000/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId,
          qid: "Q01",
          variantToken: "va11111",
          input: "8/15",
        }),
      })
    );
    assert.equal(sim1CheckRes.status, 200);
    assert.equal((await sim1CheckRes.json()).verdict, "correct");

    const simCheckRes = await checkAnswerPOST(
      new NextRequest("http://127.0.0.1:3000/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId,
          qid: "Q01",
          variantToken: "vb22222",
          input: "7/15",
        }),
      })
    );
    assert.equal(simCheckRes.status, 200);
    assert.equal((await simCheckRes.json()).verdict, "correct");

    const afterSimListRes = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
      )
    );
    const afterSimList = (await afterSimListRes.json()) as {
      unlocked: boolean;
      tabs: SimilarTabSummary[];
    };
    assert.deepEqual(
      afterSimList.tabs.map((t) => t.status),
      ["assisted", "correct", "untried"]
    );
    assert.equal(
      countPractisedSimilar(readProgress(drillId)?.problems?.Q01 as ProblemState),
      2
    );

    // 7c. The server starts a new cycle, locking Similar until another original check.
    const retry = await revealPOST(new NextRequest("http://127.0.0.1:3000/api/reveal", {
      method: "POST",
      body: JSON.stringify({ drillId, qid: "Q01", action: "reset" }),
    }));
    assert.equal(retry.status, 200);
    const { cycleStartedAt } = await retry.json();

    const retryLockedList = await variantGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
      )
    );
    assert.deepEqual(await retryLockedList.json(), { unlocked: false, tabs: [] });

    const checkedRetry = await checkAnswerPOST(new NextRequest("http://127.0.0.1:3000/api/check-answer", {
      method: "POST",
      body: JSON.stringify({ drillId, qid: "Q01", input: "1/9", cycleStartedAt }),
    }));
    assert.equal(checkedRetry.status, 200);
    assert.ok((await checkedRetry.json()).eventId);

    const retryUnlockedList = (await (
      await variantGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/variant?drillId=${drillId}&qid=Q01&mode=list`
        )
      )
    ).json()) as { unlocked: boolean; tabs: SimilarTabSummary[] };
    assert.equal(retryUnlockedList.unlocked, true);
    assert.deepEqual(
      retryUnlockedList.tabs.map((t) => t.status),
      ["untried", "untried", "untried"],
      "drill review retry must reset all similar tab statuses to untried in the new cycle"
    );
    assert.equal(
      countPractisedSimilar(readProgress(drillId)?.problems?.Q01 as ProblemState),
      0
    );
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

// ---------------------------------------------------------------------------
// 7. useSimilarTabs async race & cached-steps server persistence regressions
//    (similar.md B1, B2, B5)
// ---------------------------------------------------------------------------
{
  // B1: Set-up or hint opened while /api/check-answer is in flight is preserved in post-await state
  const latestAfterMidCheckSetup = makeProblem({
    id: "vtok1",
    state: baseState({
      userInput: "7/30",
      hintsRevealed: 1,
      setupRevealedBeforeAnswer: true,
      attempts: [],
    }),
  });
  const checkedRes = applySimilarCheckToLatestProblem(
    latestAfterMidCheckSetup,
    "7/30",
    { verdict: "correct", message: "Correct", components: [], diagnostics: [] },
    1_200,
    "2026-11-20T01:00:00.000Z",
    "2026-11-20T00:59:00.000Z"
  );
  assert.equal(checkedRes.nextProblem.state.score, 0.5, "mid-check hint/setup must cap score at 0.5");
  assert.equal(checkedRes.nextProblem.state.hintsRevealed, 1);
  assert.equal(checkedRes.nextProblem.state.setupRevealedBeforeAnswer, true);
  assert.equal(checkedRes.nextRecord.hintsRevealed, 1);
  assert.equal(checkedRes.nextRecord.setupRevealed, true);
  assert.equal(checkedRes.nextRecord.servedAt, "2026-11-20T00:59:00.000Z");
  assert.equal(checkedRes.nextRecord.attempts[0].setupRevealed, true);
  assert.equal(deriveVariantStatus(checkedRes.nextRecord, null), "assisted");

  // B5: Check completing while /api/reveal?part=hint is in flight is not dropped by hint sync
  const latestAfterConcurrentWrong = makeProblem({
    id: "vtok1",
    state: baseState({
      userInput: "1/2",
      score: 0,
      hintsRevealed: 0,
      attempts: [{ input: "1/2", ts: "2026-11-20T01:00:05.000Z", verdict: "incorrect", kind: "variant" }],
    }),
  });
  const hintedAfterWrong = applySimilarHintToLatestProblem(
    latestAfterConcurrentWrong,
    "Cancel common factors.",
    "2026-11-20T01:00:06.000Z",
    "2026-11-20T00:59:00.000Z"
  );
  assert.equal(hintedAfterWrong.didIncrement, true);
  assert.equal(hintedAfterWrong.nextRecord.attempts.length, 1, "hint reveal must preserve concurrent attempt");
  assert.equal(hintedAfterWrong.nextRecord.hintsRevealed, 1);
  assert.equal(deriveVariantStatus(hintedAfterWrong.nextRecord, null), "wrong");

  const latestAfterConcurrentCorrect = makeProblem({
    id: "vtok1",
    state: baseState({
      userInput: "7/30",
      score: 1,
      hintsRevealed: 0,
      attempts: [{ input: "7/30", ts: "2026-11-20T01:00:05.000Z", verdict: "correct", kind: "variant" }],
    }),
  });
  const hintedAfterCorrect = applySimilarHintToLatestProblem(
    latestAfterConcurrentCorrect,
    "Cancel common factors.",
    "2026-11-20T01:00:06.000Z"
  );
  assert.equal(hintedAfterCorrect.didIncrement, false, "hint finishing after correct check must not increment hintsRevealed");
  assert.equal(hintedAfterCorrect.nextRecord.attempts.length, 1);
  assert.equal(deriveVariantStatus(hintedAfterCorrect.nextRecord, null), "correct");

  // B2: Reopened similar tab with a wrong attempt and cached steps still persists reveal-steps to server
  const reopenedWrongWithCachedSteps = makeProblem({
    id: "vtok1",
    steps: [{ latex: "7/30", explain: "Simplify." }],
    state: baseState({
      score: 0,
      solutionRevealedBeforeAnswer: false,
      attempts: [{ input: "1/2", ts: "2026-11-20T01:00:00.000Z", verdict: "incorrect", kind: "variant" }],
    }),
  });
  assert.equal(
    shouldPersistVariantStepsReveal(reopenedWrongWithCachedSteps),
    true,
    "Show steps before a correct answer must persist to server even when steps are already cached"
  );
}

async function testExecuteSimilarStepsReveal() {
  // 1. Cached steps + wrong attempt (!hasCorrect): MUST POST reveal-steps idempotently, must NOT re-fetch /api/reveal
  const calls1: Array<{ url: string; method: string; body?: string }> = [];
  const mockFetch1 = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls1.push({
      url,
      method: (init?.method || "GET").toUpperCase(),
      body: typeof init?.body === "string" ? init.body : undefined,
    });
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }) as typeof fetch;

  const cachedWrongProb = makeProblem({
    id: "vtok1",
    steps: [{ latex: "7/30", explain: "Simplify." }],
    state: baseState({
      score: 0,
      solutionRevealedBeforeAnswer: false,
      attempts: [{ input: "1/2", ts: "2026-11-20T01:00:00.000Z", verdict: "incorrect", kind: "variant" }],
    }),
  });
  const res1 = await executeSimilarStepsReveal({
    drillId: "DRL-MTH-T01-C04-01",
    qid: "Q02",
    token: "vtok1",
    existing: cachedWrongProb,
    fetchFn: mockFetch1,
  });
  assert.equal(res1.recordedServerReveal, true);
  assert.equal(res1.fetchedSteps, false);
  assert.equal(res1.stepsPatch, null);
  assert.equal(calls1.length, 1);
  assert.equal(calls1[0].url, "/api/variant");
  assert.equal(calls1[0].method, "POST");
  assert.deepEqual(JSON.parse(calls1[0].body || "{}"), {
    drillId: "DRL-MTH-T01-C04-01",
    qid: "Q02",
    variantToken: "vtok1",
    action: "reveal-steps",
  });

  // 2. Cached steps + local solutionRevealedBeforeAnswer already true (e.g. retry after transient network error):
  //    still sends idempotent POST reveal-steps because !hasCorrect
  const calls2: string[] = [];
  const mockFetch2 = (async (input: RequestInfo | URL) => {
    calls2.push(typeof input === "string" ? input : input.toString());
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }) as typeof fetch;
  const cachedAlreadyFlagged = makeProblem({
    id: "vtok1",
    steps: [{ latex: "7/30", explain: "Simplify." }],
    state: baseState({
      score: 0,
      solutionRevealedBeforeAnswer: true,
      attempts: [{ input: "1/2", ts: "2026-11-20T01:00:00.000Z", verdict: "incorrect", kind: "variant" }],
    }),
  });
  const res2 = await executeSimilarStepsReveal({
    drillId: "DRL-MTH-T01-C04-01",
    qid: "Q02",
    token: "vtok1",
    existing: cachedAlreadyFlagged,
    fetchFn: mockFetch2,
  });
  assert.equal(res2.recordedServerReveal, true);
  assert.deepEqual(calls2, ["/api/variant"]);

  // 3. Cached steps + already solved (hasCorrect): calls neither endpoint
  const calls3: string[] = [];
  const mockFetch3 = (async (input: RequestInfo | URL) => {
    calls3.push(typeof input === "string" ? input : input.toString());
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }) as typeof fetch;
  const cachedSolved = makeProblem({
    id: "vtok1",
    steps: [{ latex: "7/30", explain: "Simplify." }],
    state: baseState({
      score: 1,
      attempts: [{ input: "7/30", ts: "2026-11-20T01:00:00.000Z", verdict: "correct", kind: "variant" }],
    }),
  });
  const res3 = await executeSimilarStepsReveal({
    drillId: "DRL-MTH-T01-C04-01",
    qid: "Q02",
    token: "vtok1",
    existing: cachedSolved,
    fetchFn: mockFetch3,
  });
  assert.equal(res3.recordedServerReveal, false);
  assert.equal(res3.fetchedSteps, false);
  assert.deepEqual(calls3, []);

  // 4. Uncached steps + wrong attempt: records POST reveal-steps BEFORE GET /api/reveal?part=steps
  const calls4: string[] = [];
  const mockFetch4 = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = (init?.method || "GET").toUpperCase();
    calls4.push(`${method} ${url}`);
    if (url.startsWith("/api/reveal")) {
      return new Response(
        JSON.stringify({
          steps: [{ latex: "7/30", explain: "Simplify." }],
          answerDisplay: "\\frac{7}{30}",
          answerPlain: "7/30",
        }),
        { status: 200 }
      );
    }
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
  }) as typeof fetch;
  const uncachedWrong = makeProblem({
    id: "vtok1",
    state: baseState({
      score: 0,
      attempts: [{ input: "1/2", ts: "2026-11-20T01:00:00.000Z", verdict: "incorrect", kind: "variant" }],
    }),
  });
  const res4 = await executeSimilarStepsReveal({
    drillId: "DRL-MTH-T01-C04-01",
    qid: "Q02",
    token: "vtok1",
    existing: uncachedWrong,
    fetchFn: mockFetch4,
  });
  assert.equal(res4.recordedServerReveal, true);
  assert.equal(res4.fetchedSteps, true);
  assert.equal(res4.stepsPatch?.steps.length, 1);
  assert.equal(res4.stepsPatch?.answerPlain, "7/30");
  assert.equal(calls4.length, 2);
  assert.equal(calls4[0], "POST /api/variant");
  assert.match(calls4[1], /^GET \/api\/reveal\?.*part=steps/);
}

testV1Migration()
  .then(() => testReviewCycleIsolation())
  .then(() => testExecuteSimilarStepsReveal())
  .then(() => {
    console.log("PASS: similarTabs.test.tsx (state model, cycle rule, migration, ARIA, copy, deep link, Review & Sync)");
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
