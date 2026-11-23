import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  buildNavigableRows,
  buildPickerSections,
  clampKeyboardIndex,
  cleanCurriculumTitle,
  compareCurriculumCodes,
  filterDrills,
  filterLabs,
  groupItemsByTopicAndChapter,
  normalizeDrillPickerItems,
  normalizeLabPickerItems,
  parseCurriculumCodes,
  selectContinueItems,
  stepKeyboardIndex,
} from "../src/lib/drillGrouping";
import { updateRecentDrillIds } from "../src/lib/lastDrillStorage";
import { statusTone } from "../src/lib/statusTone";
import { DrillSwitcher } from "../src/components/shell/DrillSwitcher";
import type { LabListItem } from "../src/lib/labModel";
import type { DrillListItem } from "../src/types/drill";

const makeDrill = (
  drillId: string,
  unitCode: string,
  unitTitle: string,
  overrides: Partial<DrillListItem> = {}
): DrillListItem => ({
  drillId,
  subject: unitCode.startsWith("PRG-") ? "PRG" : "MATH",
  unitCode,
  unitTitle,
  createdAt: "2026-11-17",
  questionCount: 5,
  difficultyMode: "Mixed",
  practiceStatus: "Ready",
  score: 0,
  maxScore: 5,
  answeredCount: 0,
  localFilePath: "",
  ...overrides,
});

const makeLab = (
  id: string,
  chapterCode: string,
  title: string,
  overrides: Partial<LabListItem> = {}
): LabListItem => ({
  id,
  labId: id,
  title,
  unitCode: chapterCode,
  chapterCode,
  chapterTitle: `Chapter ${chapterCode}`,
  topicCode: chapterCode.split("-").slice(0, 2).join("-"),
  topicTitle: "JS, TS & Data Structures",
  unitsUsed: [],
  kind: "chapter-lab",
  milestoneCount: 3,
  practiceStatus: "Ready",
  passedCount: 0,
  reviseCount: 0,
  score: 0,
  maxScore: 3,
  progress: {
    passedCount: 0,
    reviseCount: 0,
    notStartedCount: 3,
    totalCount: 3,
    practiceStatus: "Ready",
    score: 0,
    maxScore: 3,
    updatedAt: null,
    milestones: {},
  },
  ...overrides,
});

// ---------------------------------------------------------------------------
// 1. Curriculum code parsing, sorting, and title cleaning
// ---------------------------------------------------------------------------
assert.deepEqual(parseCurriculumCodes("MTH-T02-C01-U01"), {
  topicCode: "MTH-T02",
  chapterCode: "MTH-T02-C01",
});
assert.deepEqual(parseCurriculumCodes("MTH-T01-C04"), {
  topicCode: "MTH-T01",
  chapterCode: "MTH-T01-C04",
});
assert.deepEqual(parseCurriculumCodes("PRG-T00-C03"), {
  topicCode: "PRG-T00",
  chapterCode: "PRG-T00-C03",
});
assert.deepEqual(parseCurriculumCodes("MTH-T02-C01-U01", "MTH-T02", "MTH-T02-C01"), {
  topicCode: "MTH-T02",
  chapterCode: "MTH-T02-C01",
});
assert.equal(
  cleanCurriculumTitle("PostgreSQL Queries, `pg` Driver & Transactions"),
  "PostgreSQL Queries, pg Driver & Transactions"
);

const codes = ["MTH-T02-C10", "MTH-T01-C04", "MTH-T02-C02", "MTH-T01-C12"];
assert.deepEqual([...codes].sort(compareCurriculumCodes), [
  "MTH-T01-C04",
  "MTH-T01-C12",
  "MTH-T02-C02",
  "MTH-T02-C10",
]);

// ---------------------------------------------------------------------------
// 2. Local recent drill list updates (MRU dedup & cap)
// ---------------------------------------------------------------------------
assert.deepEqual(
  updateRecentDrillIds(["DRL-2", "DRL-1", "DRL-3"], "DRL-1", 3),
  ["DRL-1", "DRL-2", "DRL-3"]
);
assert.deepEqual(
  updateRecentDrillIds(["DRL-3", "DRL-2", "DRL-1"], "DRL-4", 3),
  ["DRL-4", "DRL-3", "DRL-2"]
);
assert.deepEqual(updateRecentDrillIds(["DRL-1"], "   ", 3), ["DRL-1"]);

// ---------------------------------------------------------------------------
// 3. Normalization, search, status filtering, and Continue selection
// ---------------------------------------------------------------------------
const mathDrills: DrillListItem[] = [
  makeDrill("DRL-MTH-T02-C02-U01-01", "MTH-T02-C02-U01", "Functions & Notation", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C02",
    chapterTitle: "Functions",
    practiceStatus: "Graded",
    score: 5,
  }),
  makeDrill("DRL-MTH-T01-C04-02", "MTH-T01-C04", "Fractions", {
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C04",
    chapterTitle: "Fractions",
    practiceStatus: "In Progress",
    score: 2,
    answeredCount: 2,
  }),
  makeDrill("DRL-MTH-T01-C04-01", "MTH-T01-C04", "Fractions", {
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C04",
    chapterTitle: "Fractions",
    practiceStatus: "Ready",
  }),
  makeDrill("DRL-MTH-T02-C01-U01-04", "MTH-T02-C01-U01", "Complex Numbers", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C01",
    chapterTitle: "Equations and Inequalities",
    practiceStatus: "Needs Retry",
    score: 1,
    answeredCount: 3,
  }),
  makeDrill("DRL-MTH-T02-C01-U01-03", "MTH-T02-C01-U01", "Complex Numbers", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C01",
    chapterTitle: "Equations and Inequalities",
    practiceStatus: "In Progress",
    score: 3,
    answeredCount: 4,
  }),
  makeDrill("DRL-MTH-T02-C01-U02-01", "MTH-T02-C01-U02", "Quadratic Equations", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C01",
    chapterTitle: "Equations and Inequalities",
    practiceStatus: "Ready",
  }),
];

assert.equal(
  filterDrills(mathDrills, "DRL-MTH-T02-C01-U01-04", "ALL").length,
  1,
  "search matches full drill ID"
);
assert.equal(
  filterDrills(mathDrills, "MTH-T02-C01", "ALL").length,
  3,
  "search matches chapter code"
);
assert.equal(
  filterDrills(mathDrills, "equations complex", "ALL").length,
  2,
  "multi-token search matches across chapter title and unit title"
);
assert.equal(filterDrills(mathDrills, "", "GRADED").length, 1);
assert.equal(filterDrills(mathDrills, "", "UNFINISHED").length, 5);

const pickerItems = normalizeDrillPickerItems(mathDrills);

// Continue prioritizes MRU unfinished > other unfinished > MRU Ready, excluding currentId, max 3
const continuePick = selectContinueItems(
  pickerItems,
  "DRL-MTH-T02-C01-U01-03",
  ["DRL-MTH-T02-C01-U01-03", "DRL-MTH-T01-C04-02", "DRL-MTH-T02-C01-U02-01"],
  3
);
assert.deepEqual(
  continuePick.map((item) => item.id),
  [
    "DRL-MTH-T01-C04-02", // recent + In Progress
    "DRL-MTH-T02-C01-U01-04", // other unfinished (Needs Retry)
    "DRL-MTH-T02-C01-U02-01", // recent + Ready
  ]
);

// ---------------------------------------------------------------------------
// 4. Topic -> Chapter grouping & sectioning
// ---------------------------------------------------------------------------
const topicGroups = groupItemsByTopicAndChapter(pickerItems, "DRL-MTH-T02-C01-U01-03");
assert.deepEqual(
  topicGroups.map((t) => t.topicCode),
  ["MTH-T01", "MTH-T02"],
  "topics sorted naturally"
);
assert.equal(topicGroups[0].containsCurrent, false);
assert.equal(topicGroups[1].containsCurrent, true);
assert.deepEqual(
  topicGroups[1].chapters.map((c) => c.chapterCode),
  ["MTH-T02-C01", "MTH-T02-C02"],
  "chapters sorted naturally"
);
assert.equal(topicGroups[1].chapters[0].containsCurrent, true);
assert.equal(topicGroups[1].chapters[1].containsCurrent, false);

// MTH-T01-C04 has only unit MTH-T01-C04 === chapterCode -> inlineInChapter = true
assert.equal(topicGroups[0].chapters[0].entries[0].kind, "unit-group");
if (topicGroups[0].chapters[0].entries[0].kind === "unit-group") {
  assert.equal(topicGroups[0].chapters[0].entries[0].inlineInChapter, true);
  assert.deepEqual(
    topicGroups[0].chapters[0].entries[0].items.map((s) => s.setLabel),
    ["Set 1", "Set 2"]
  );
}

// MTH-T02-C01 has U01 (multi-set) + U02 (single) -> inlineInChapter = false
assert.equal(topicGroups[1].chapters[0].entries[0].kind, "unit-group");
if (topicGroups[1].chapters[0].entries[0].kind === "unit-group") {
  assert.equal(topicGroups[1].chapters[0].entries[0].inlineInChapter, false);
  assert.deepEqual(
    topicGroups[1].chapters[0].entries[0].items.map((s) => s.setLabel),
    ["Set 3", "Set 4"]
  );
}
assert.equal(topicGroups[1].chapters[0].entries[1].kind, "single");

// Sectioning: default (non-search) pins Current, fills Continue, expands only current Topic/Chapter
const defaultSections = buildPickerSections({
  items: pickerItems,
  currentId: "DRL-MTH-T02-C01-U01-03",
  recentIds: ["DRL-MTH-T01-C04-02"],
  search: "",
  filter: "ALL",
});
assert.equal(defaultSections.isSearching, false);
assert.equal(defaultSections.currentItem?.id, "DRL-MTH-T02-C01-U01-03");
assert.deepEqual(defaultSections.defaultExpandedTopics, ["MTH-T02"]);
assert.deepEqual(defaultSections.defaultExpandedChapters, ["MTH-T02-C01"]);

// Sectioning: when searching, Current & Continue hide and ALL matching Topic/Chapter groups expand
const searchSections = buildPickerSections({
  items: pickerItems,
  currentId: "DRL-MTH-T02-C01-U01-03",
  recentIds: ["DRL-MTH-T01-C04-02"],
  search: "MTH-T0",
  filter: "ALL",
});
assert.equal(searchSections.isSearching, true);
assert.equal(searchSections.currentItem, null);
assert.equal(searchSections.continueItems.length, 0);
assert.deepEqual(searchSections.defaultExpandedTopics, ["MTH-T01", "MTH-T02"]);
assert.deepEqual(searchSections.defaultExpandedChapters, [
  "MTH-T01-C04",
  "MTH-T02-C01",
  "MTH-T02-C02",
]);

// Sectioning: Graded filter omits Continue and filters currentItem if not Graded
const gradedSections = buildPickerSections({
  items: pickerItems,
  currentId: "DRL-MTH-T02-C01-U01-03",
  recentIds: [],
  search: "",
  filter: "GRADED",
});
assert.equal(gradedSections.currentItem, null);
assert.equal(gradedSections.continueItems.length, 0);
assert.equal(gradedSections.totalVisibleCount, 1);

// ---------------------------------------------------------------------------
// 5. Keyboard navigation rows & index stepping
// ---------------------------------------------------------------------------
const navRows = buildNavigableRows(
  defaultSections,
  new Set(defaultSections.defaultExpandedTopics),
  new Set(defaultSections.defaultExpandedChapters)
);
// Expected: Current (1) + Continue (2: C04-02, U01-04) + expanded MTH-T02-C01 (3: Set 3, Set 4, Quadratic)
assert.equal(navRows.length, 6);
assert.deepEqual(
  navRows.map((r) => [r.section, r.id]),
  [
    ["current", "DRL-MTH-T02-C01-U01-03"],
    ["continue", "DRL-MTH-T01-C04-02"],
    ["continue", "DRL-MTH-T02-C01-U01-04"],
    ["tree", "DRL-MTH-T02-C01-U01-03"],
    ["tree", "DRL-MTH-T02-C01-U01-04"],
    ["tree", "DRL-MTH-T02-C01-U02-01"],
  ]
);

assert.equal(stepKeyboardIndex(-1, 6, "down"), 0);
assert.equal(stepKeyboardIndex(0, 6, "down"), 1);
assert.equal(stepKeyboardIndex(5, 6, "down"), 0);
assert.equal(stepKeyboardIndex(-1, 6, "up"), 5);
assert.equal(stepKeyboardIndex(0, 6, "up"), 5);
assert.equal(stepKeyboardIndex(3, 6, "up"), 2);
assert.equal(stepKeyboardIndex(0, 0, "down"), -1);

assert.equal(clampKeyboardIndex(-1, 4, true), 0);
assert.equal(clampKeyboardIndex(-1, 4, false), -1);
assert.equal(clampKeyboardIndex(5, 3, true), 0);
assert.equal(clampKeyboardIndex(2, 0, true), -1);

// ---------------------------------------------------------------------------
// 6. Labs filtering & normalization
// ---------------------------------------------------------------------------
const prgLabs: LabListItem[] = [
  makeLab("LAB-PRG-T01-C01-01", "PRG-T01-C01", "TinyEventEmitter & PromisePool", {
    practiceStatus: "In Progress",
    passedCount: 1,
    score: 1,
  }),
  makeLab("LAB-PRG-T02-C01-01", "PRG-T02-C01", "MiniStore and useStore", {
    topicTitle: "Frontend Engineering",
    practiceStatus: "Graded",
    passedCount: 3,
    score: 3,
  }),
];
assert.equal(filterLabs(prgLabs, "promise", "ALL").length, 1);
assert.equal(filterLabs(prgLabs, "", "GRADED").length, 1);
assert.equal(normalizeLabPickerItems(prgLabs)[0].countLabel, "3 Ms");

// ---------------------------------------------------------------------------
// 7. DrillSwitcher SSR rendering (Math vs Programming, tree roles, search expansion, no full IDs)
// ---------------------------------------------------------------------------
const noop = () => {};

const mathHtml = renderToStaticMarkup(
  <DrillSwitcher
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="math"
    currentDrill={null}
    drills={mathDrills}
    labs={prgLabs}
    dueUnitCodes={["MTH-T02-C01-U02"]}
    selectedDrillId="DRL-MTH-T02-C01-U01-03"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.doesNotMatch(mathHtml, />Labs</, "Math workspace must never show a Labs tab");
assert.match(mathHtml, />Current</);
assert.doesNotMatch(mathHtml, />Continue</, "separate Continue list is removed");
assert.match(mathHtml, />Expand all</);
assert.match(mathHtml, />Collapse all</);
assert.match(mathHtml, />View</);
assert.doesNotMatch(mathHtml, />Synced</);
assert.match(mathHtml, /role="tree"/);
assert.match(mathHtml, /role="treeitem"/);
assert.match(mathHtml, /aria-level="1"/);
assert.match(mathHtml, /aria-level="2"/);
assert.match(mathHtml, /aria-level="3"/);
assert.match(mathHtml, /aria-level="4"/);
assert.match(mathHtml, /aria-selected="true"/);
assert.match(mathHtml, /Algebra and Trigonometry/);
assert.match(mathHtml, /Equations and Inequalities/);
assert.match(mathHtml, /Complex Numbers/);
assert.match(mathHtml, />U01</);
assert.match(mathHtml, />U02</);
assert.match(mathHtml, />Set 3</);
assert.match(mathHtml, /Due today/);
assert.match(mathHtml, /bg-indigo-600 dark:bg-indigo-400/);
assert.ok(mathHtml.includes(statusTone.wrong.dot));
// MTH-T01 starts collapsed so Fractions drills inside aren't expanded
assert.match(mathHtml, /Prealgebra/);
assert.doesNotMatch(mathHtml, />C04</, "collapsed topic must hide its child drills");
assert.doesNotMatch(mathHtml, />DRL-MTH-/);
assert.match(mathHtml, /class="sm:relative min-w-0 flex-1 sm:flex-initial"/, "mobile wrapper stays static so popover anchors to header row");
assert.match(mathHtml, /role="dialog"[^>]*class="[^"]*left-0 right-0 top-full[^"]*sm:right-auto/, "mobile popover spans header row without overflowing viewport");

const codeSearchHtml = renderToStaticMarkup(
  <DrillSwitcher
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={[
      makeDrill("DRL-PRG-T01-C01-U02-01", "PRG-T01-C01-U02", "Closures", {
        topicCode: "PRG-T01",
        topicTitle: "JS, TS & Data Structures",
        chapterCode: "PRG-T01-C01",
        chapterTitle: "JS Execution & Async",
        hasNotes: true,
      }),
    ]}
    labs={prgLabs}
    selectedDrillId="DRL-PRG-T01-C01-U02-01"
    drillSearch="closures"
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.match(codeSearchHtml, />Drills</);
assert.match(codeSearchHtml, />Labs</);
assert.match(codeSearchHtml, /role="tablist"[^>]*aria-label="Practice type"/);
assert.match(codeSearchHtml, /role="tab"[^>]*aria-selected="true"[^>]*data-state="active"/);
assert.match(codeSearchHtml, /role="tab"[^>]*aria-selected="false"[^>]*data-state="inactive"/);
assert.match(codeSearchHtml, /aria-expanded="false"[^>]*aria-haspopup="dialog"[^>]*data-state="closed"/);
assert.match(codeSearchHtml, /aria-expanded="false"[^>]*aria-haspopup="dialog"[^>]*data-state="closed"[^>]*>[^<]*<svg/);
assert.match(codeSearchHtml, /Closures/);
assert.match(codeSearchHtml, />U02</);
assert.match(codeSearchHtml, /Has notes/);
assert.doesNotMatch(codeSearchHtml, />Current</, "searching hides Current section");
assert.doesNotMatch(codeSearchHtml, />DRL-PRG-/);

console.log("drill picker tests passed");
