import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  buildPickerSections,
  buildVisibleTreeRows,
  classifyPickerItemType,
  collectAllTreeCodes,
  extractChapterShortCode,
  extractLeafHoverCode,
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
import { DrillSwitcher } from "../src/components/shell/DrillSwitcher";
import { WorkspaceSwitch } from "../src/components/workspace/WorkspaceSwitch";
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

assert.equal(extractChapterShortCode("MTH-T02-C01"), "C01");
assert.equal(extractChapterShortCode("PRG-T01-C04"), "C04");
assert.equal(extractChapterShortCode("OTHER"), "OTHER");

assert.equal(extractLeafHoverCode(mathItems[0]), "C04-01");
assert.equal(extractLeafHoverCode(mathItems[2]), "U01-03");
assert.equal(extractLeafHoverCode(mathItems[4]), "U02");
assert.equal(extractLeafHoverCode(codeDrill), "U02");
assert.equal(extractLeafHoverCode(labItems[0]), "LAB-02");

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
  defaultRows.map((r) => [r.kind, r.level, r.nodeId, r.hoverCode]),
  [
    ["topic", 1, "topic:MTH-T01", "MTH-T01"],
    ["topic", 1, "topic:MTH-T02", "MTH-T02"],
    ["chapter", 2, "chapter:MTH-T02-C01", "C01"],
    ["unit", 3, "unit:MTH-T02-C01-U01", "U01"],
    ["leaf", 4, "leaf:DRL-MTH-T02-C01-U01-03", "U01-03"],
    ["leaf", 4, "leaf:DRL-MTH-T02-C01-U01-04", "U01-04"],
    ["leaf", 3, "leaf:DRL-MTH-T02-C01-U02-01", "U02"],
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

// ---------------------------------------------------------------------------
// 4. Tree UI polish invariants (hover codes, no empty note slot, no type icons, focus-visible)
// ---------------------------------------------------------------------------
const noop = () => {};

const mathTreeHtml = renderToStaticMarkup(
  <DrillSwitcher
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="math"
    currentDrill={null}
    drills={sampleDrills}
    labs={[]}
    dueUnitCodes={["MTH-T02-C01-U02"]}
    selectedDrillId="DRL-MTH-T02-C01-U01-03"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);

// 1) Hover codes on every level (topic, chapter, unit, set, single-unit) use hidden (no reserved width)
//    and sit to the left of the count pill without overlapping it.
assert.doesNotMatch(mathTreeHtml, /opacity-0/, "hover codes must not reserve width with opacity-0");
assert.match(mathTreeHtml, /hidden group-hover:block group-focus-visible:block[^>]*>MTH-T02</);
assert.match(
  mathTreeHtml,
  /hidden group-hover:block group-focus-visible:block[^>]*>C01<\/span><\/span><span[^>]*rounded-full[^>]*>3<\/span>/,
  "chapter hover code sits left of count pill"
);
assert.match(
  mathTreeHtml,
  /hidden group-hover:block group-focus-visible:block[^>]*>U01<\/span><\/span><span[^>]*rounded-full[^>]*>2<\/span>/,
  "unit hover code sits left of count pill"
);
assert.match(mathTreeHtml, /hidden group-hover:block group-focus-visible:block[^>]*>U01-03</);
assert.match(mathTreeHtml, /hidden group-hover:block group-focus-visible:block[^>]*>U01-04</);
assert.match(mathTreeHtml, /hidden group-hover:block group-focus-visible:block[^>]*>U02</);

// 2) No empty note slot when a leaf has neither notes nor due-today status;
//    status dot precedes any note/due icon so dots stay vertically aligned.
assert.doesNotMatch(
  mathTreeHtml,
  /<span class="w-3\.5 h-3\.5 shrink-0" aria-hidden="true"><\/span>/,
  "leaf rows without notes/due must not render an empty note slot"
);
// Set 3 (current, no notes, not due) renders StatusDot directly followed by label "Set 3"
assert.match(
  mathTreeHtml,
  /aria-selected="true"[^>]*>(?:(?!<\/button>).)*?<span class="sr-only">In progress<\/span><\/span><span class="text-xs truncate min-w-0 flex-1 font-medium[^>]*>Set 3<\/span>/
);
// Set 4 (hasNotes: true) renders StatusDot followed by NoteBadge
assert.match(mathTreeHtml, /<span class="sr-only">Needs retry<\/span>/);
const noteBadgeClasses =
  mathTreeHtml.match(/<span class="([^"]*)" title="Has notes or mistake tags">/)?.[1] ?? "";
assert.match(noteBadgeClasses, /w-3\.5/);
assert.match(noteBadgeClasses, /h-3\.5/);
assert.doesNotMatch(noteBadgeClasses, /bg-/);

// 3) All type icons (Sigma, Code2, FlaskConical, Shuffle) removed; only Layers kept on Topic rows
assert.doesNotMatch(mathTreeHtml, /lucide-sigma/);
assert.doesNotMatch(mathTreeHtml, /lucide-code-2/);
assert.doesNotMatch(mathTreeHtml, /lucide-flask-conical/);
assert.doesNotMatch(mathTreeHtml, /lucide-shuffle/);
assert.match(mathTreeHtml, /lucide-layers/);

// 4) Branch rows use focus-visible only (no static ring/selected highlight)
assert.match(mathTreeHtml, /aria-level="1" aria-expanded="true"[^>]*focus-visible:ring-2/);
assert.match(mathTreeHtml, /aria-level="2" aria-expanded="true"[^>]*focus-visible:ring-2/);
assert.match(mathTreeHtml, /aria-level="3" aria-expanded="true"[^>]*focus-visible:ring-2/);
assert.doesNotMatch(mathTreeHtml, /aria-expanded="(true|false)"[^>]*class="[^"]*bg-indigo-50/);
assert.doesNotMatch(mathTreeHtml, /aria-expanded="(true|false)"[^>]*class="[^"]*(?<!:)\bring-2\b/);

// Labs tab also shows hover code on lab leaf and removes FlaskConical
const labTreeHtml = renderToStaticMarkup(
  <DrillSwitcher
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={[makeDrill("DRL-PRG-T01-C01-U02-01", "PRG-T01-C01-U02", "Closures")]}
    labs={[makeLab("LAB-PRG-T01-C04-02", "PRG-T01-C04", "SQL Ledger")]}
    selectedDrillId="LAB-PRG-T01-C04-02"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.match(labTreeHtml, /hidden group-hover:block group-focus-visible:block[^>]*>LAB-02</);
assert.doesNotMatch(labTreeHtml, /lucide-flask-conical/);
assert.doesNotMatch(labTreeHtml, /lucide-code-2/);
assert.doesNotMatch(labTreeHtml, /aria-label="Actions for LAB-/);

const sidebarTreeHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="math"
    currentDrill={null}
    drills={sampleDrills}
    selectedDrillId="DRL-MTH-T02-C01-U01-03"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.doesNotMatch(sidebarTreeHtml, />Expand all|>Collapse all|>View</);
assert.doesNotMatch(sidebarTreeHtml, /border-l/);
assert.doesNotMatch(sidebarTreeHtml, /aria-label="Actions for MTH-T02-C01"/);
assert.doesNotMatch(sidebarTreeHtml, /aria-label="Actions for MTH-T02-C01-U01"/);
assert.match(sidebarTreeHtml, /aria-label="Actions for DRL-MTH-T02-C01-U01-03"/);
assert.match(sidebarTreeHtml, /h-11 w-11/);
assert.match(sidebarTreeHtml, /lg:h-7 lg:w-7/);
const sidebarActionSource = readFileSync("src/components/shell/DrillSwitcher.tsx", "utf8");
assert.match(sidebarActionSource, /data-menu-open=\{openActionNodeId === item\.id/);
assert.match(sidebarActionSource, /isCurrent \|\| openActionNodeId === item\.id/);
assert.match(sidebarActionSource, /role="menuitem"[\s\S]*?Copy ID/);
assert.match(sidebarActionSource, /role="menuitem"[\s\S]*?Reset/);
assert.match(sidebarActionSource, /role="menuitem"[\s\S]*?Delete/);
assert.match(sidebarTreeHtml, /aria-label="Actions for DRL-MTH-T02-C01-U01-03"/);
assert.match(sidebarTreeHtml, /aria-current="true"/);
const selectedLeafMarkup = sidebarTreeHtml.match(
  /<div[^>]*data-sidebar-leaf="DRL-MTH-T02-C01-U01-03"[\s\S]*?<\/div>/
)?.[0];
assert.ok(selectedLeafMarkup, "sidebar drill leaf has a shared visual wrapper");
const sidebarRows = [...sidebarTreeHtml.matchAll(/data-sidebar-row="([^"]+)"[^>]*class="([^"]+)"/g)];
assert.ok(sidebarRows.length > 4, "sidebar renders folder and leaf surfaces");
for (const [, row, classes] of sidebarRows) {
  assert.match(classes, /\bh-8 rounded-md\b/, `${row} uses the shared 32 px surface and radius`);
  assert.doesNotMatch(classes, /focus-within:|ring-indigo/, `${row} has no pointer-focus ring`);
}
const sidebarCodes = [...sidebarTreeHtml.matchAll(/data-sidebar-row-code="true" aria-hidden="true" class="([^"]+)"[^>]*>([^<]+)/g)];
for (const code of ["MTH-T02", "C01", "U01", "U01-03", "U01-04"]) {
  assert.ok(sidebarCodes.some(([, , label]) => label === code), `sidebar has a row-owned badge for ${code}`);
}
assert.ok(sidebarCodes.every(([, classes]) => !classes.includes("group-hover")));
assert.match(selectedLeafMarkup, /bg-zinc-200\/70/);
assert.match(selectedLeafMarkup, /aria-current="true"/);
assert.match(selectedLeafMarkup, /h-11 w-11/);
assert.match(selectedLeafMarkup, /lg:h-7 lg:w-7/);
assert.match(
  selectedLeafMarkup,
  /<\/button><button[^>]*aria-label="Actions for DRL-MTH-T02-C01-U01-03"/,
  "drill selection and action targets are sibling buttons, never nested"
);
assert.match(sidebarTreeHtml, /aria-level="1" aria-expanded="true"/);
assert.match(sidebarTreeHtml, /data-sidebar-row="topic"[^>]*class="[^"]*w-full h-8[^"]*px-1\.5/);
assert.match(sidebarTreeHtml, /data-sidebar-row="chapter"[^>]*class="[^"]*w-full h-8[^"]*pl-4/);
assert.match(sidebarTreeHtml, /data-sidebar-row="unit"[^>]*class="[^"]*w-full h-8[^"]*pl-\[26px\]/);
assert.match(sidebarTreeHtml, /data-sidebar-row="leaf-4"/);
assert.match(sidebarTreeHtml, /data-sidebar-row="leaf-4"[^>]*class="[^"]*w-full[^\"]*h-8/);
assert.match(sidebarTreeHtml, /pl-\[36px\]/, "deep drill contents indent independently of the full-width row");
assert.doesNotMatch(sidebarTreeHtml, /role="group" class="ml-3/, "sidebar branches keep a shared left edge");
assert.match(sidebarTreeHtml, /bg-transparent[^>]*>2<\/span>/, "sidebar counts have no fill");
assert.ok(
  (sidebarTreeHtml.match(/h-8/g) ?? []).length >= 10,
  "sidebar branch and leaf rows use fixed 32px classes"
);

for (const workspace of ["math", "code"] as const) {
  const workspaceSwitchHtml = renderToStaticMarkup(
    <WorkspaceSwitch
      variant="sidebar"
      workspace={workspace}
      pillWorkspace={workspace}
      onSelectWorkspace={noop}
      mathHref="/math/DRL-MTH-T01-C04-01"
      codeHref="/code/DRL-PRG-T01-C01-U02-01"
    />
  );
  assert.match(workspaceSwitchHtml, /aria-label="Math"[^>]*href="\/math\/DRL-MTH-T01-C04-01"/);
  assert.match(workspaceSwitchHtml, /aria-label="Programming"[^>]*href="\/code\/DRL-PRG-T01-C01-U02-01"/);
  const tabs = [...workspaceSwitchHtml.matchAll(/<a aria-label="(Math|Programming)"([^>]*)>/g)];
  assert.equal(tabs.length, 2);
  for (const [, name, attributes] of tabs) {
    assert.match(attributes, /\bsize-11 lg:size-8\b/);
    assert.equal(attributes.includes('aria-current="page"'), name === (workspace === "math" ? "Math" : "Programming"));
  }
  const track = workspaceSwitchHtml.match(/<nav aria-label="Workspace" class="([^"]+)"/)?.[1];
  assert.match(track ?? "", /grid-cols-2.*p-0\.5/);
  assert.doesNotMatch(track ?? "", /\b(?:min-h-|h-)/, "cell size and padding determine track height");
}

// Cross-unit bridge drills (MTH-BRIDGE) appear in the Math drill picker under a clean Bridge group
const bridgeDrills: DrillListItem[] = [
  ...sampleDrills,
  makeDrill("DRL-MTH-BRIDGE-01", "MTH-BRIDGE", "Cross-Unit Bridge Synthesis", {
    topicCode: "MTH-BRIDGE",
    topicTitle: "MTH-BRIDGE",
    chapterCode: "MTH-BRIDGE",
    chapterTitle: "Cross-Unit Bridge Synthesis",
    practiceStatus: "Ready",
  }),
];
const bridgeItems = normalizeDrillPickerItems(bridgeDrills);
const bridgeItem = bridgeItems.find((i) => i.id === "DRL-MTH-BRIDGE-01");
assert.ok(bridgeItem, "MTH-BRIDGE drill must be normalized for the picker");
assert.equal(bridgeItem.subject, "MATH");
assert.equal(bridgeItem.topicCode, "MTH-BRIDGE");
assert.equal(bridgeItem.topicTitle, "Cross-Unit Bridge Synthesis");
assert.equal(extractShortCode(bridgeItem), "BRIDGE");
assert.equal(extractChapterShortCode(bridgeItem.chapterCode), "BRIDGE");
assert.equal(classifyPickerItemType(bridgeItem), "chapter-mixed");

const bridgeSections = buildPickerSections({
  items: bridgeItems,
  currentId: "DRL-MTH-BRIDGE-01",
  recentIds: [],
  search: "",
  filter: "ALL",
});
const bridgeTopic = bridgeSections.topicGroups.find((t) => t.topicCode === "MTH-BRIDGE");
assert.ok(bridgeTopic, "MTH-BRIDGE topic group must appear in drill picker");
assert.equal(bridgeTopic.containsCurrent, true);

console.log("drill tree tests passed");
