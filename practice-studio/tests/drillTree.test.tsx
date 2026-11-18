import assert from "node:assert/strict";
import {
  buildPickerSections,
  buildVisibleTreeRows,
  classifyPickerItemType,
  collectAllTreeCodes,
  extractShortCode,
  findCurrentLeafNodeId,
  findFirstLeafNodeId,
  formatFullRowCode,
  getPickerStatusLabel,
  isChapterMixedUnitCode,
  normalizeDrillPickerItems,
  normalizeLabPickerItems,
  resolveTreeKeyAction,
} from "../src/lib/drillGrouping";
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
// 1. Short codes, full tooltip codes, type classification, status labels
// ---------------------------------------------------------------------------
assert.equal(isChapterMixedUnitCode("MTH-T01-C04"), true);
assert.equal(isChapterMixedUnitCode("PRG-T00-C03"), true);
assert.equal(isChapterMixedUnitCode("MTH-T02-C01-U01"), false);

const sampleDrills: DrillListItem[] = [
  makeDrill("DRL-MTH-T01-C04-01", "MTH-T01-C04", "Fractions", {
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C04",
    chapterTitle: "Fractions",
    practiceStatus: "Graded",
    score: 5,
  }),
  makeDrill("DRL-MTH-T01-C04-02", "MTH-T01-C04", "Fractions", {
    topicCode: "MTH-T01",
    topicTitle: "Prealgebra",
    chapterCode: "MTH-T01-C04",
    chapterTitle: "Fractions",
    practiceStatus: "In Progress",
    hasNotes: true,
  }),
  makeDrill("DRL-MTH-T02-C01-U01-03", "MTH-T02-C01-U01", "Complex Numbers", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C01",
    chapterTitle: "Equations and Inequalities",
    practiceStatus: "In Progress",
  }),
  makeDrill("DRL-MTH-T02-C01-U01-04", "MTH-T02-C01-U01", "Complex Numbers", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C01",
    chapterTitle: "Equations and Inequalities",
    practiceStatus: "Needs Retry",
    hasNotes: true,
  }),
  makeDrill("DRL-MTH-T02-C01-U02-01", "MTH-T02-C01-U02", "Quadratic Equations", {
    topicCode: "MTH-T02",
    topicTitle: "Algebra and Trigonometry",
    chapterCode: "MTH-T02-C01",
    chapterTitle: "Equations and Inequalities",
    practiceStatus: "Ready",
  }),
];

const codeDrill = normalizeDrillPickerItems([
  makeDrill("DRL-PRG-T01-C01-U02-01", "PRG-T01-C01-U02", "Closures"),
])[0];
const mathItems = normalizeDrillPickerItems(sampleDrills);
const labItems = normalizeLabPickerItems([
  makeLab("LAB-PRG-T01-C04-02", "PRG-T01-C04", "SQL Ledger", { hasNotes: true }),
]);

assert.equal(extractShortCode(mathItems[0]), "C04");
assert.equal(extractShortCode(mathItems[2]), "U01");
assert.equal(extractShortCode(mathItems[4]), "U02");
assert.equal(extractShortCode(labItems[0]), "LAB-02");

assert.equal(formatFullRowCode(mathItems[0]), "MTH-T01-C04 · DRL-MTH-T01-C04-01");
assert.equal(formatFullRowCode(mathItems[4]), "MTH-T02-C01-U02");
assert.equal(formatFullRowCode(labItems[0]), "LAB-PRG-T01-C04-02");

assert.equal(classifyPickerItemType(mathItems[0]), "chapter-mixed");
assert.equal(classifyPickerItemType(mathItems[2]), "math-unit");
assert.equal(classifyPickerItemType(codeDrill), "code-unit");
assert.equal(classifyPickerItemType(labItems[0]), "lab");

assert.equal(getPickerStatusLabel("Ready"), "Not started");
assert.equal(getPickerStatusLabel("In Progress"), "In progress");
assert.equal(getPickerStatusLabel("Graded"), "Graded");
assert.equal(getPickerStatusLabel("Needs Retry"), "Needs retry");

// ---------------------------------------------------------------------------
// 2. Tree flattening (levels, expanded flags, status, notes, due-today)
// ---------------------------------------------------------------------------
const sections = buildPickerSections({
  items: mathItems,
  currentId: "DRL-MTH-T02-C01-U01-03",
  recentIds: [],
  search: "",
  filter: "ALL",
});

assert.deepEqual(sections.defaultExpandedTopics, ["MTH-T02"]);
assert.deepEqual(sections.defaultExpandedChapters, ["MTH-T02-C01"]);
assert.deepEqual(sections.defaultExpandedUnits, ["MTH-T02-C01-U01"]);

const allCodes = collectAllTreeCodes(sections.topicGroups);
assert.deepEqual(allCodes, {
  topicCodes: ["MTH-T01", "MTH-T02"],
  chapterCodes: ["MTH-T01-C04", "MTH-T02-C01"],
  unitCodes: ["MTH-T02-C01-U01"], // MTH-T01-C04 is inlineInChapter so excluded
});

// Default expanded: MTH-T01 collapsed (1 row), MTH-T02 -> C01 -> U01 -> Set 3, Set 4 + U02
const defaultRows = buildVisibleTreeRows({
  topicGroups: sections.topicGroups,
  currentId: "DRL-MTH-T02-C01-U01-03",
  expandedTopics: new Set(sections.defaultExpandedTopics),
  expandedChapters: new Set(sections.defaultExpandedChapters),
  expandedUnits: new Set(sections.defaultExpandedUnits),
  dueUnitCodes: new Set(["MTH-T02-C01-U02"]),
  currentHasNotesOverride: true,
});

assert.deepEqual(
  defaultRows.map((r) => [r.kind, r.level, r.nodeId]),
  [
    ["topic", 1, "topic:MTH-T01"],
    ["topic", 1, "topic:MTH-T02"],
    ["chapter", 2, "chapter:MTH-T02-C01"],
    ["unit", 3, "unit:MTH-T02-C01-U01"],
    ["leaf", 4, "leaf:DRL-MTH-T02-C01-U01-03"],
    ["leaf", 4, "leaf:DRL-MTH-T02-C01-U01-04"],
    ["leaf", 3, "leaf:DRL-MTH-T02-C01-U02-01"],
  ]
);

const currentLeaf = defaultRows[4];
assert.equal(currentLeaf.kind, "leaf");
if (currentLeaf.kind === "leaf") {
  assert.equal(currentLeaf.isCurrent, true);
  assert.equal(currentLeaf.label, "Set 3");
  assert.equal(currentLeaf.shortCode, "U01");
  assert.equal(currentLeaf.status, "In Progress");
  assert.equal(currentLeaf.hasNotes, true, "currentHasNotesOverride merges live notes");
  assert.equal(currentLeaf.isDueToday, false);
}

const u02Leaf = defaultRows[6];
assert.equal(u02Leaf.kind, "leaf");
if (u02Leaf.kind === "leaf") {
  assert.equal(u02Leaf.isDueToday, true);
  assert.equal(u02Leaf.hasNotes, false);
  assert.equal(u02Leaf.status, "Ready");
}

assert.equal(findFirstLeafNodeId(defaultRows), "leaf:DRL-MTH-T02-C01-U01-03");
assert.equal(
  findCurrentLeafNodeId(defaultRows, "DRL-MTH-T02-C01-U01-03"),
  "leaf:DRL-MTH-T02-C01-U01-03"
);

// Expand all shows inlineInChapter Set 1 & Set 2 at level 3
const expandedAllRows = buildVisibleTreeRows({
  topicGroups: sections.topicGroups,
  currentId: "DRL-MTH-T02-C01-U01-03",
  expandedTopics: new Set(allCodes.topicCodes),
  expandedChapters: new Set(allCodes.chapterCodes),
  expandedUnits: new Set(allCodes.unitCodes),
});
assert.equal(expandedAllRows.length, 10);
assert.equal(expandedAllRows[2].kind, "leaf");
assert.equal(expandedAllRows[2].level, 3);
assert.equal(expandedAllRows[2].parentNodeId, "chapter:MTH-T01-C04");

// ---------------------------------------------------------------------------
// 3. Keyboard navigation resolution (ArrowUp/Down/Right/Left, Enter)
// ---------------------------------------------------------------------------
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, null, "ArrowDown"),
  { type: "focus", nodeId: "topic:MTH-T01" }
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "leaf:DRL-MTH-T02-C01-U02-01", "ArrowDown"),
  { type: "focus", nodeId: "topic:MTH-T01" },
  "ArrowDown wraps to top"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "topic:MTH-T01", "ArrowUp"),
  { type: "focus", nodeId: "leaf:DRL-MTH-T02-C01-U02-01" },
  "ArrowUp wraps to bottom"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "topic:MTH-T01", "ArrowRight"),
  { type: "expand", nodeKind: "topic", code: "MTH-T01" },
  "ArrowRight expands collapsed branch"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "topic:MTH-T02", "ArrowRight"),
  { type: "focus", nodeId: "chapter:MTH-T02-C01" },
  "ArrowRight on expanded branch focuses first child"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "leaf:DRL-MTH-T02-C01-U01-03", "ArrowRight"),
  { type: "none" },
  "ArrowRight on leaf is a no-op"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "unit:MTH-T02-C01-U01", "ArrowLeft"),
  { type: "collapse", nodeKind: "unit", code: "MTH-T02-C01-U01" },
  "ArrowLeft collapses expanded branch"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "leaf:DRL-MTH-T02-C01-U01-04", "ArrowLeft"),
  { type: "focus", nodeId: "unit:MTH-T02-C01-U01" },
  "ArrowLeft on leaf jumps to parent"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "topic:MTH-T01", "ArrowLeft"),
  { type: "none" },
  "ArrowLeft on collapsed root topic is a no-op"
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "topic:MTH-T01", "Enter"),
  { type: "toggle", nodeKind: "topic", code: "MTH-T01" }
);
assert.deepEqual(
  resolveTreeKeyAction(defaultRows, "leaf:DRL-MTH-T02-C01-U01-04", "Enter"),
  { type: "select", itemId: "DRL-MTH-T02-C01-U01-04" }
);
assert.deepEqual(resolveTreeKeyAction([], null, "ArrowDown"), { type: "none" });

console.log("drill tree tests passed");
