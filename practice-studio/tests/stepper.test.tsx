import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { Problem, ProblemState, ReviewRecord } from "../src/types/drill";
import {
  buildDrillSteps,
  buildLabSteps,
  buildReviewStepMeta,
  drillStepResult,
  labStatusLine,
  labStepResult,
} from "../src/lib/stepperModel";
import { QuizPaginationBar } from "../src/components/QuizPaginationBar";

const noop = () => {};

function makeState(overrides: Partial<ProblemState> = {}): ProblemState {
  return {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    lastCheck: null,
    ...overrides,
  };
}

function makeProblem(
  id: string,
  overrides: Partial<Problem> = {},
  stateOverrides: Partial<ProblemState> = {}
): Problem {
  return {
    id,
    templateKey: "tpl",
    level: 2,
    levelLabel: "Level 2 - Standard Exam",
    category: "Linear Equations",
    prompt: "Solve $x = 2$.",
    answerSpec: { type: "number" },
    checkpointHint: "",
    state: makeState(stateOverrides),
    ...overrides,
  };
}

function makeReview(
  verdict: "pass" | "revise",
  testsPassed = 2,
  testsTotal = 2
): ReviewRecord {
  return {
    at: "2026-11-19T10:00:00.000Z",
    attempt: 1,
    codeHash: "abc123",
    code: "export const ok = true;",
    tests: {
      passed: testsPassed,
      total: testsTotal,
      failed: testsPassed === testsTotal ? [] : ["failing case"],
    },
    lint: [],
    typecheck: [],
    findings: [],
    verdict,
    explain: null,
  };
}

// ---------------------------------------------------------------------------
// 1. drillStepResult truth table (all 6 drill results + assisted signals)
// ---------------------------------------------------------------------------
assert.equal(drillStepResult(makeProblem("Q01", {}, {})), "notTried");
assert.equal(drillStepResult(makeProblem("Q01", {}, { score: 1 })), "correct");
assert.equal(drillStepResult(makeProblem("Q01", {}, { score: 0 })), "wrong");
assert.equal(drillStepResult(makeProblem("Q01", {}, { skipped: true })), "skipped");
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { skipped: true, score: 0 })),
  "skipped",
  "skipped flag takes precedence over zero score"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { score: 0.5 })),
  "partial",
  "0 < score < 1 without help is partial"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { score: 1, hintsRevealed: 1 })),
  "assisted",
  "hint revealed before full score is assisted"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { score: 1, setupRevealedBeforeAnswer: true })),
  "assisted",
  "set-up revealed before answer is assisted"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { score: 1, solutionRevealedBeforeAnswer: true })),
  "assisted",
  "solution revealed before answer is assisted"
);
assert.equal(
  drillStepResult(
    makeProblem("Q01", {}, {
      score: 0.5,
      hintsRevealed: 1,
    })
  ),
  "assisted",
  "help used with score > 0 is assisted"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { hintsRevealed: 1 })),
  "usedHelp",
  "hint revealed before answering is usedHelp"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { setupRevealedBeforeAnswer: true })),
  "usedHelp",
  "set-up revealed before answering is usedHelp"
);
assert.equal(
  drillStepResult(makeProblem("Q01", {}, { solutionRevealedBeforeAnswer: true })),
  "usedHelp",
  "steps revealed before answering is usedHelp"
);
assert.equal(
  drillStepResult(
    makeProblem("Q01", {}, {
      score: 1,
      cycleStartedAt: "2026-11-19T12:00:00.000Z",
      attempts: [
        {
          input: "2",
          ts: "2026-11-19T12:05:00.000Z",
          verdict: "correct",
          exampleViewed: true,
        },
      ],
    })
  ),
  "assisted",
  "worked example viewed in active review cycle is assisted"
);
assert.equal(
  drillStepResult(
    makeProblem("Q01", {}, {
      score: 1,
      cycleStartedAt: "2026-11-19T12:00:00.000Z",
      attempts: [
        {
          input: "2",
          ts: "2026-11-18T10:00:00.000Z",
          verdict: "correct",
          exampleViewed: true,
        },
        {
          input: "2",
          ts: "2026-11-19T12:05:00.000Z",
          verdict: "correct",
        },
      ],
    })
  ),
  "correct",
  "example viewed in an earlier review cycle must not taint the current cycle"
);

// Drill step labels & accessible names (Math vs Code)
const mathSteps = buildDrillSteps(
  [
    makeProblem("Q01", { level: 1 }, { score: 1 }),
    makeProblem("Q02", { level: 2 }, { score: 1, hintsRevealed: 1 }),
    makeProblem("Q03", { level: 2 }, { score: 0.5 }),
    makeProblem("Q04", { level: 3 }, { score: 0 }),
    makeProblem("Q05", { level: 3 }, { skipped: true }),
    makeProblem("Q06", { level: 4 }, {}),
  ],
  "math"
);
assert.deepEqual(
  mathSteps.map((s) => [s.title, s.secondary, s.result, s.ariaLabel]),
  [
    ["Question 1", "Level 1", "correct", "Question 1, Level 1, correct"],
    ["Question 2", "Level 2", "assisted", "Question 2, Level 2, correct with help"],
    ["Question 3", "Level 2", "partial", "Question 3, Level 2, partly correct"],
    ["Question 4", "Level 3", "wrong", "Question 4, Level 3, wrong"],
    ["Question 5", "Level 3", "skipped", "Question 5, Level 3, skipped"],
    ["Question 6", "Level 4", "notTried", "Question 6, Level 4, not tried"],
  ]
);
assert.deepEqual(buildReviewStepMeta(mathSteps, false), {
  secondary: "4 of 6 answered",
  ariaLabel: "Review & sync, 4 of 6 answered",
});

const codeSteps = buildDrillSteps([makeProblem("Q01", { level: 3 }, {})], "code");
assert.equal(codeSteps[0].title, "Problem 1");
assert.equal(codeSteps[0].secondary, "Level 3");
assert.equal(codeSteps[0].ariaLabel, "Problem 1, Level 3, not tried");

// ---------------------------------------------------------------------------
// 2. Lab mapping: passed, tests-pass-awaiting-review, regressed, in-progress, empty
// ---------------------------------------------------------------------------
const labPassed = makeProblem(
  "M1",
  { category: "Schema Types & Result Union" },
  { reviews: [makeReview("pass")] }
);
const labTestsOnly = makeProblem(
  "M2",
  { category: "Primitive & Object Parsers" },
  {
    lastTestReport: {
      allPassed: true,
      score: 1,
      passedCount: 4,
      totalCount: 4,
      visibleResults: [],
      hiddenPassed: 0,
      hiddenTotal: 0,
      executionTimeMs: 12,
    },
  }
);
const labRegressed = makeProblem(
  "M3",
  { category: "Validators" },
  {
    reviews: [makeReview("pass")],
    lastTestReport: {
      allPassed: false,
      score: 0.5,
      passedCount: 1,
      totalCount: 2,
      visibleResults: [{ name: "checks bounds", passed: false }],
      hiddenPassed: 0,
      hiddenTotal: 0,
      executionTimeMs: 9,
    },
  }
);
const labInProgressUserCode = makeProblem(
  "M4",
  { category: "Error Paths" },
  { userCode: "export function parse() {}" }
);
const labEmpty = makeProblem("M5", { category: "CLI Wiring" }, {});

assert.equal(labStepResult(labPassed), "passed");
assert.equal(labStatusLine(labPassed), "Tests passing");

assert.equal(labStepResult(labTestsOnly), "inProgress");
assert.equal(labStatusLine(labTestsOnly), "Tests passing");

assert.equal(labStepResult(labRegressed), "regressed");
assert.equal(labStatusLine(labRegressed), "In progress");

assert.equal(labStepResult(labInProgressUserCode), "inProgress");
assert.equal(labStatusLine(labInProgressUserCode), "In progress");

assert.equal(labStepResult(labEmpty), "notStarted");
assert.equal(labStatusLine(labEmpty), "Not started");

const labSteps = buildLabSteps([
  labPassed,
  labTestsOnly,
  labRegressed,
  labInProgressUserCode,
  labEmpty,
]);
assert.deepEqual(
  labSteps.map((s) => [s.title, s.secondary, s.result, s.ariaLabel]),
  [
    [
      "Schema Types & Result Union",
      "Tests passing",
      "passed",
      "Milestone 1, Schema Types & Result Union, tests passing, passed",
    ],
    [
      "Primitive & Object Parsers",
      "Tests passing",
      "inProgress",
      "Milestone 2, Primitive & Object Parsers, tests passing",
    ],
    [
      "Validators",
      "In progress",
      "regressed",
      "Milestone 3, Validators, in progress, regressed",
    ],
    [
      "Error Paths",
      "In progress",
      "inProgress",
      "Milestone 4, Error Paths, in progress",
    ],
    [
      "CLI Wiring",
      "Not started",
      "notStarted",
      "Milestone 5, CLI Wiring, not started",
    ],
  ]
);
assert.deepEqual(buildReviewStepMeta(labSteps, true), {
  secondary: "1 of 5 passed",
  ariaLabel: "Review & sync, 1 of 5 passed",
});

// Verify rendered lab circles match state table (passed -> emerald ✓, testsOnly -> outlined + "02", regressed -> amber + "03")
const labHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={0}
    problems={[labPassed, labTestsOnly, labRegressed, labEmpty]}
    viewMode="quiz"
    isLab={true}
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(
  labHtml,
  /aria-label="Milestone 1, Schema Types &amp; Result Union, tests passing, passed, current"[^>]*aria-current="step"[\s\S]*?bg-emerald-600[\s\S]*?ring-4 ring-indigo-600\/15[\s\S]*?<svg/
);
assert.match(
  labHtml,
  /aria-label="Milestone 2, Primitive &amp; Object Parsers, tests passing"[\s\S]*?border-zinc-400[\s\S]*?>02<\/span>[\s\S]*?>Tests passing<\/span>/
);
assert.match(
  labHtml,
  /aria-label="Milestone 3, Validators, in progress, regressed"[\s\S]*?bg-amber-600[\s\S]*?>03<\/span>[\s\S]*?>In progress<\/span>/
);
assert.match(
  labHtml,
  /aria-label="Milestone 4, CLI Wiring, not started"[\s\S]*?border-zinc-300[\s\S]*?>04<\/span>[\s\S]*?>Not started<\/span>/
);

// ---------------------------------------------------------------------------
// 3. Markup: nav > ol > li > button, one aria-current="step", Review last with svg,
//    numbers "01".."12", labels aria-hidden + hidden sm:block, all drill state tokens
// ---------------------------------------------------------------------------
const drillSixProblems = [
  makeProblem("Q01", { level: 1 }, { score: 1 }),
  makeProblem("Q02", { level: 1 }, { score: 0 }),
  makeProblem("Q03", { level: 2 }, {}),
  makeProblem("Q04", { level: 2 }, { score: 1, hintsRevealed: 1 }),
  makeProblem("Q05", { level: 3 }, { score: 0.5 }),
  makeProblem("Q06", { level: 3 }, { skipped: true }),
];
const sixHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={2}
    problems={drillSixProblems}
    viewMode="quiz"
    workspace="math"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);

assert.match(sixHtml, /<nav[^>]*aria-label="Questions"[^>]*><div[^>]*><ol[^>]*><li/);
assert.match(sixHtml, /<\/button><\/li><\/ol><\/div><\/nav><\/div>$/);

const ariaCurrentMatches = sixHtml.match(/aria-current="step"/g) ?? [];
assert.equal(ariaCurrentMatches.length, 1, "exactly one step carries aria-current='step'");

// Current step Q03 shows "03" with indigo outline + halo
assert.match(
  sixHtml,
  /aria-label="Question 3, Level 2, not tried, current"[^>]*aria-current="step"[\s\S]*?border-indigo-600[\s\S]*?ring-4 ring-indigo-600\/15[\s\S]*?>03<\/span>/
);
// Q01 correct -> emerald + svg check
assert.match(
  sixHtml,
  /aria-label="Question 1, Level 1, correct"[\s\S]*?bg-emerald-600[\s\S]*?<svg/
);
// Q02 wrong -> rose + svg X
assert.match(
  sixHtml,
  /aria-label="Question 2, Level 1, wrong"[\s\S]*?bg-rose-600[\s\S]*?<svg/
);
// Q04 assisted -> amber + svg check
assert.match(
  sixHtml,
  /aria-label="Question 4, Level 2, correct with help"[\s\S]*?bg-amber-600[\s\S]*?<svg/
);
// Q05 partial -> amber + svg minus
assert.match(
  sixHtml,
  /aria-label="Question 5, Level 3, partly correct"[\s\S]*?bg-amber-600[\s\S]*?<svg/
);
// Q06 skipped -> dashed border + "06"
assert.match(
  sixHtml,
  /aria-label="Question 6, Level 3, skipped"[\s\S]*?border-dashed[\s\S]*?>06<\/span>/
);

// Used help before answering -> amber circle with step number (no ✓) and not counted as answered
const usedHelpSteps = buildDrillSteps([makeProblem("Q01", { level: 1 }, { hintsRevealed: 1 })], "math");
assert.equal(usedHelpSteps[0].result, "usedHelp");
assert.equal(usedHelpSteps[0].ariaLabel, "Question 1, Level 1, used help");
assert.equal(buildReviewStepMeta(usedHelpSteps, false).secondary, "0 of 1 answered");
const usedHelpHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={0}
    problems={[makeProblem("Q01", { level: 1 }, { hintsRevealed: 1 })]}
    viewMode="quiz"
    workspace="math"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(
  usedHelpHtml,
  /aria-label="Question 1, Level 1, used help, current"[\s\S]*?bg-amber-600[\s\S]*?ring-4 ring-indigo-600\/15[\s\S]*?>01<\/span>/
);

// Review step is last, has an svg, and has no step number inside its circle
const lastLiMatch = sixHtml.match(/<li[^>]*>(?:(?!<li).)*<\/li><\/ol>/);
assert.ok(lastLiMatch, "last <li> must exist");
assert.match(lastLiMatch[0], /aria-label="Review &amp; sync, 4 of 6 answered"/);
assert.match(lastLiMatch[0], /<svg[^>]*>/);
assert.doesNotMatch(lastLiMatch[0], />07<\/span>/);

// Visible desktop labels carry aria-hidden="true" and hidden sm:block + font-display
assert.match(
  sixHtml,
  /<span aria-hidden="true" class="[^"]*hidden sm:block[^"]*font-display[^"]*">Question 3<\/span>/
);
assert.match(
  sixHtml,
  /<span aria-hidden="true" class="[^"]*hidden sm:block[^"]*font-display[^"]*">Level 2<\/span>/
);

// Mobile 44px tap targets on every step button
assert.match(sixHtml, /min-w-11 h-11/);

// ---------------------------------------------------------------------------
// 4. Connectors: current = 2 => segments 0 & 1 indigo, rest zinc; review => all indigo
// ---------------------------------------------------------------------------
const extractConnectorStates = (html: string): string[] =>
  Array.from(html.matchAll(/data-connector-active="(true|false)"/g), (m) => m[1]);

assert.deepEqual(
  extractConnectorStates(sixHtml),
  ["true", "true", "false", "false", "false", "false"],
  "with currentIndex=2, segments 0 and 1 are indigo and segments 2..5 are zinc"
);

const sixReviewHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={2}
    problems={drillSixProblems}
    viewMode="review"
    workspace="math"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.deepEqual(
  extractConnectorStates(sixReviewHtml),
  ["true", "true", "true", "true", "true", "true"],
  "in review mode, every connector segment is indigo"
);
assert.equal(
  (sixReviewHtml.match(/aria-current="step"/g) ?? []).length,
  1,
  "review mode also has exactly one aria-current='step'"
);
assert.match(
  sixReviewHtml,
  /aria-label="Review &amp; sync, 4 of 6 answered"[^>]*aria-pressed="true"[^>]*aria-current="step"/
);

// ---------------------------------------------------------------------------
// 5. No role="tablist" (guards global arrow keys) and no scrollIntoView
// ---------------------------------------------------------------------------
assert.doesNotMatch(sixHtml, /role="tablist"/);
assert.doesNotMatch(labHtml, /role="tablist"/);
const stepperSrc = readFileSync("src/components/Stepper.tsx", "utf8");
const paginationSrc = readFileSync("src/components/QuizPaginationBar.tsx", "utf8");
assert.doesNotMatch(stepperSrc, /role="tablist"/);
assert.doesNotMatch(stepperSrc, /scrollIntoView/);
assert.doesNotMatch(paginationSrc, /scrollIntoView/);
assert.match(stepperSrc, /scroller\.scrollTo\(/);

// ---------------------------------------------------------------------------
// 6. 12 problems render 13 <li> with min-w-[72px], zero-padded "01".."12", and text-xs title
// ---------------------------------------------------------------------------
const twelveProblems = Array.from({ length: 12 }, (_, i) =>
  makeProblem(`Q${String(i + 1).padStart(2, "0")}`, { level: (i % 4) + 1 }, {})
);
const twelveHtml = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={6}
    problems={twelveProblems}
    viewMode="quiz"
    workspace="math"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
const liMatches = twelveHtml.match(/<li\b/g) ?? [];
assert.equal(liMatches.length, 13, "12 problems + Review step must render 13 <li> items");
assert.match(twelveHtml, /min-w-\[72px\]/);
assert.match(twelveHtml, />01<\/span>/);
assert.match(twelveHtml, />07<\/span>/);
assert.match(twelveHtml, />12<\/span>/);
assert.match(
  twelveHtml,
  /<span aria-hidden="true" class="[^"]*font-display text-xs font-semibold[^"]*">Question 12<\/span>/,
  ">9 columns drops the title size to text-xs"
);

console.log("stepper tests passed");
