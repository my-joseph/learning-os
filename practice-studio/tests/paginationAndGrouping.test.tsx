import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { stepStudyPosition } from "../src/lib/pagination";
import {
  buildGenerateUnitOptions,
  extractDrillSetNumber,
  formatDrillSetLabel,
  groupDrillsByUnit,
  groupGenerateUnitOptions,
} from "../src/lib/drillGrouping";
import { QuizPaginationBar } from "../src/components/QuizPaginationBar";
import { DrillSwitcher } from "../src/components/shell/DrillSwitcher";
import type { DrillListItem, Problem } from "../src/types/drill";

// ---------------------------------------------------------------------------
// 1. stepStudyPosition pure navigation logic (drills + labs + review step)
// ---------------------------------------------------------------------------
assert.deepEqual(
  stepStudyPosition({ viewMode: "quiz", index: 0 }, 4, "prev"),
  { viewMode: "quiz", index: 0 },
  "prev at first question stays at index 0"
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "quiz", index: 0 }, 4, "next"),
  { viewMode: "quiz", index: 1 }
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "quiz", index: 3 }, 4, "next"),
  { viewMode: "review", index: 3 },
  "next on last question opens Review view"
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "review", index: 3 }, 4, "next"),
  { viewMode: "review", index: 3 },
  "next on Review stays on Review"
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "review", index: 3 }, 4, "prev"),
  { viewMode: "quiz", index: 3 },
  "prev from Review returns to last question"
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "review", index: 0 }, 4, "prev"),
  { viewMode: "quiz", index: 3 },
  "prev from Review returns to last question even when opened from an earlier tile"
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "quiz", index: 0 }, 1, "next"),
  { viewMode: "review", index: 0 },
  "single-question drill/lab transitions straight from index 0 to Review"
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "review", index: 0 }, 1, "prev"),
  { viewMode: "quiz", index: 0 }
);
assert.deepEqual(
  stepStudyPosition({ viewMode: "quiz", index: 0 }, 0, "next"),
  { viewMode: "quiz", index: 0 },
  "empty problem list is a no-op"
);

// Keyboard handler invariants in useDrill.ts
const useDrillSrc = readFileSync("src/hooks/useDrill.ts", "utf8");
assert.doesNotMatch(
  useDrillSrc,
  /if\s*\(\s*viewMode\s*!==\s*"quiz"\s*\)\s*return/,
  "keyboard handler must not block ArrowLeft/ArrowRight while in review mode"
);
assert.match(useDrillSrc, /target\.tagName === "INPUT"/);
assert.match(useDrillSrc, /\[role="alertdialog"\], \[role="dialog"\]/);
assert.match(useDrillSrc, /stepStudyPosition\(/);

// ---------------------------------------------------------------------------
// 2. QuizPaginationBar icon-only Review tile matches number/milestone tiles
// ---------------------------------------------------------------------------
const makeProblem = (id: string): Problem => ({
  id,
  templateKey: "tpl",
  level: 1,
  levelLabel: "Level 1",
  category: "Algebra",
  prompt: "Solve $x = 1$.",
  answerSpec: { type: "number" },
  checkpointHint: "",
  state: {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    lastCheck: null,
  },
});

const noop = () => {};
const drillQuizTiles = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={1}
    problems={[makeProblem("Q01"), makeProblem("Q02")]}
    viewMode="quiz"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(drillQuizTiles, /role="navigation"[^>]*aria-label="Questions"/);
assert.match(drillQuizTiles, /justify-center[^>]*w-max mx-auto|w-max mx-auto/);
assert.doesNotMatch(drillQuizTiles, /aria-label="Lab milestones"/);
assert.match(drillQuizTiles, /aria-label="Review &amp; sync"/);
assert.match(drillQuizTiles, /title="Review &amp; sync"/);
assert.doesNotMatch(drillQuizTiles, />Review<\/span>/);

const codeQuizTiles = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={0}
    problems={[makeProblem("Q01"), makeProblem("Q02")]}
    viewMode="quiz"
    workspace="code"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(codeQuizTiles, /role="navigation"[^>]*aria-label="Problems"/);
assert.match(codeQuizTiles, /aria-label="Problem 1 — Unanswered"/);

const drillReviewTiles = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={1}
    problems={[makeProblem("Q01"), makeProblem("Q02")]}
    viewMode="review"
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(
  drillReviewTiles,
  /aria-label="Review &amp; sync"[^>]*aria-pressed="true"[^>]*aria-current="step"[^>]*title="Review &amp; sync"[^>]*class="[^"]*min-w-\[1\.75rem\] h-7[^"]*ring-2 ring-indigo-600/
);

const labQuizStepper = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={0}
    problems={[makeProblem("M1"), makeProblem("M2")]}
    viewMode="quiz"
    isLab={true}
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(labQuizStepper, /<nav[^>]*aria-label="Lab milestones"/);
assert.doesNotMatch(labQuizStepper, /aria-label="Questions"/);
assert.doesNotMatch(labQuizStepper, /min-w-\[1\.75rem\] h-7/);
assert.match(labQuizStepper, /aria-label="M1 — not passed yet"[^>]*aria-current="step"/);
assert.match(labQuizStepper, /aria-label="M2 — not passed yet"/);
assert.doesNotMatch(labQuizStepper, />Review<\/span>/); // icon-only Review step

const labReviewStepper = renderToStaticMarkup(
  <QuizPaginationBar
    currentIndex={1}
    problems={[makeProblem("M1"), makeProblem("M2")]}
    viewMode="review"
    isLab={true}
    onSelectQuestion={noop}
    onToggleViewMode={noop}
  />
);
assert.match(labReviewStepper, /<nav[^>]*aria-label="Lab milestones"/);
assert.match(
  labReviewStepper,
  /aria-label="Review &amp; sync"[^>]*aria-pressed="true"[^>]*aria-current="step"/
);
assert.match(
  labReviewStepper,
  /aria-label="Review &amp; sync"[\s\S]*ring-2 ring-indigo-600/
);

// ---------------------------------------------------------------------------
// 3. Drill grouping pure functions & DrillSwitcher rendering
// ---------------------------------------------------------------------------
assert.equal(extractDrillSetNumber("DRL-MTH-T01-C04-01"), 1);
assert.equal(extractDrillSetNumber("DRL-MTH-T02-C01-U01-04"), 4);
assert.equal(extractDrillSetNumber("DRL-MTH-T01-C04-12"), 12);
assert.equal(extractDrillSetNumber("DRL-CUSTOM"), null);

assert.equal(formatDrillSetLabel("DRL-MTH-T01-C04-01"), "Set 1");
assert.equal(formatDrillSetLabel("DRL-MTH-T02-C01-U01-03"), "Set 3");
assert.equal(formatDrillSetLabel("DRL-CUSTOM"), "DRL-CUSTOM");

const makeDrillItem = (
  drillId: string,
  unitCode: string,
  unitTitle: string,
  overrides: Partial<DrillListItem> = {}
): DrillListItem => ({
  drillId,
  subject: "MATH",
  unitCode,
  unitTitle,
  createdAt: "2026-11-17",
  questionCount: 5,
  difficultyMode: "Mixed",
  practiceStatus: "Ready",
  score: 0,
  maxScore: 5,
  localFilePath: "",
  ...overrides,
});

const sampleDrills: DrillListItem[] = [
  makeDrillItem("DRL-MTH-T01-C04-03", "MTH-T01-C04", "Fractions", {
    practiceStatus: "In Progress",
    score: 2,
  }),
  makeDrillItem("DRL-MTH-T01-C07-01", "MTH-T01-C07", "Proportional & Ratio"),
  makeDrillItem("DRL-MTH-T01-C04-01", "MTH-T01-C04", "Fractions", {
    practiceStatus: "Graded",
    score: 5,
  }),
  makeDrillItem("DRL-MTH-T01-C04-02", "MTH-T01-C04", "Fractions"),
];

const grouped = groupDrillsByUnit(sampleDrills);
assert.equal(grouped.length, 2, "two distinct units in insertion order");
assert.equal(grouped[0].kind, "group");
if (grouped[0].kind === "group") {
  assert.equal(grouped[0].unitCode, "MTH-T01-C04");
  assert.equal(grouped[0].unitTitle, "Fractions");
  assert.deepEqual(
    grouped[0].items.map((item) => item.setLabel),
    ["Set 1", "Set 2", "Set 3"],
    "multi-drill unit sets must sort by drill number ascending"
  );
  assert.deepEqual(
    grouped[0].items.map((item) => item.drill.drillId),
    ["DRL-MTH-T01-C04-01", "DRL-MTH-T01-C04-02", "DRL-MTH-T01-C04-03"]
  );
}
assert.equal(grouped[1].kind, "single", "unit with one drill stays a single row");
if (grouped[1].kind === "single") {
  assert.equal(grouped[1].drill.drillId, "DRL-MTH-T01-C07-01");
}

assert.deepEqual(groupDrillsByUnit([]), []);

const switcherHtml = renderToStaticMarkup(
  <DrillSwitcher
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    currentDrill={null}
    drills={sampleDrills}
    labs={[]}
    selectedDrillId="DRL-MTH-T01-C04-02"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);

// Single code per row: full drill IDs must not appear in visible row text
assert.doesNotMatch(switcherHtml, />DRL-MTH-T01-C04-01</);
assert.doesNotMatch(switcherHtml, />DRL-MTH-T01-C04-02</);
assert.doesNotMatch(switcherHtml, />DRL-MTH-T01-C07-01</);

// Grouped unit shows chapter header + count pill + hover code, with Set 1 / Set 2 / Set 3 leaf rows,
// while non-current chapters start collapsed.
assert.match(switcherHtml, />Current</);
assert.doesNotMatch(switcherHtml, />Continue</);
assert.match(switcherHtml, />Expand all</);
assert.match(switcherHtml, />Collapse all</);
assert.match(switcherHtml, />View</);
assert.doesNotMatch(switcherHtml, />Synced</);
assert.doesNotMatch(switcherHtml, />Labs</);
assert.match(switcherHtml, />C04</);
assert.match(switcherHtml, />C04-01</);
assert.match(switcherHtml, />Set 1</);
assert.match(switcherHtml, />Set 2</);
assert.match(switcherHtml, />Set 3</);
assert.match(switcherHtml, /Proportional &amp; Ratio/);
assert.match(
  switcherHtml,
  /aria-level="2" aria-expanded="false"[^>]*title="MTH-T01-C07"[^>]*>(?:(?!<\/button>).)*?Proportional &amp; Ratio(?:(?!<\/button>).)*?hidden group-hover:block[^>]*>C07<\/span>/,
  "collapsed chapter shows its hover code without expanding its child leaf"
);
assert.doesNotMatch(
  switcherHtml,
  /aria-level="3"[^>]*title="MTH-T01-C07"/,
  "other chapters must start collapsed without rendering child drill rows"
);
assert.match(switcherHtml, /bg-indigo-50[^>]*>.*?Set 2/);

// 4. Dynamic Generate unit options filtered by workspace, always including current unit
const mixedWorkspaceDrills: DrillListItem[] = [
  makeDrillItem("DRL-MTH-T02-C02-U01-01", "MTH-T02-C02-U01", "Transformations of Functions"),
  makeDrillItem("DRL-MTH-T01-C04-01", "MTH-T01-C04", "Fractions"),
  makeDrillItem("DRL-PRG-T02-C01-U03-01", "PRG-T02-C01-U03", "State Management", {
    subject: "PRG",
  }),
];

const mathUnitOpts = buildGenerateUnitOptions(mixedWorkspaceDrills, "math", {
  unitCode: "MTH-T02-C03-U01",
  unitTitle: "Quadratic Functions",
  subject: "MATH",
});
assert.deepEqual(
  mathUnitOpts.map((u) => u.unitCode),
  ["MTH-T01-C04", "MTH-T02-C02-U01", "MTH-T02-C03-U01"],
  "Math unit options must exclude PRG and always include currentDrill.unitCode"
);
const mathUnitGroups = groupGenerateUnitOptions(mathUnitOpts);
assert.deepEqual(
  mathUnitGroups.map((g) => g.groupCode),
  ["MTH-T01", "MTH-T02"]
);

const codeUnitOpts = buildGenerateUnitOptions(mixedWorkspaceDrills, "code", null);
assert.deepEqual(
  codeUnitOpts.map((u) => u.unitCode),
  ["PRG-T02-C01-U03"],
  "Code unit options must include only PRG units"
);

console.log("pagination and drill grouping tests passed");
