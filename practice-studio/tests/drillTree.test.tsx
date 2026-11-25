import assert from "node:assert/strict";
import { JSDOM } from "jsdom";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  buildPickerSections,
  buildVisibleTreeRows,
  classifyPickerItemType,
  collectAllTreeCodes,
  findCurrentLeafNodeId,
  findFirstLeafNodeId,
  getPickerStatusLabel,
  isChapterMixedUnitCode,
  normalizeDrillPickerItems,
  normalizeLabPickerItems,
  resolveTreeKeyAction,
} from "../src/lib/drillGrouping";
import {
  DrillSwitcher,
  PRG_SECTION_STORAGE_KEYS,
  readSidebarSectionExpanded,
  writeSidebarSectionExpanded,
} from "../src/components/shell/DrillSwitcher";
import { ListRow } from "../src/components/ui/ListRow";
import { SectionHeader } from "../src/components/ui/SectionHeader";
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
// 4. Tree UI polish invariants (curriculum titles, no empty note slot, no type icons, focus-visible)
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

assert.doesNotMatch(mathTreeHtml, />(?:MTH-T02|C01|U01|U01-03|U01-04|U02)</);
assert.doesNotMatch(mathTreeHtml, /title="(?:MTH-|DRL-)/);

// 2) No empty note slot when a leaf has neither notes nor due-today status;
//    status dot precedes any note/due icon so dots stay vertically aligned.
assert.doesNotMatch(
  mathTreeHtml,
  /<span class="size-space-3_5 shrink-0" aria-hidden="true"><\/span>/,
  "leaf rows without notes/due must not render an empty note slot"
);
// Set 3 (current, no notes, not due) renders StatusDot directly followed by label "Set 3"
assert.match(
  mathTreeHtml,
  /aria-selected="true"[^>]*>(?:(?!<\/button>).)*?<span class="sr-only">In progress<\/span><\/span><span class="[^"]*font-semibold[^>]*>Set 3<\/span>/
);
// Set 4 (hasNotes: true) renders StatusDot followed by NoteBadge
assert.match(mathTreeHtml, /<span class="sr-only">Needs retry<\/span>/);
const noteBadgeClasses =
  mathTreeHtml.match(/<span class="([^"]*)" title="Has notes or mistake tags">/)?.[1] ?? "";
assert.match(noteBadgeClasses, /size-space-3_5/);
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

// Legacy Labs tab renders lab titles without badges or action menus
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
assert.doesNotMatch(labTreeHtml, />LAB-02<|title="LAB-/);
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
assert.doesNotMatch(sidebarTreeHtml, />(?:MTH-T02|C01|U01|U01-03|U01-04|U02)<|title="(?:MTH-|DRL-)/);
const sidebarTree = JSDOM.fragment(sidebarTreeHtml);
const sidebarRows = sidebarTree.querySelectorAll("[data-sidebar-row]");
assert.ok(sidebarRows.length > 4, "sidebar renders folder and leaf surfaces");
for (const row of Array.from(sidebarRows)) {
  const treeItem = row.querySelector(':scope > [role="treeitem"]');
  assert.ok(treeItem);
  const action = row.querySelector(':scope > [data-tree-row-action] > button');
  const title = treeItem.querySelector("[data-tree-row-label]");
  assert.ok(title);
  const selected = treeItem.hasAttribute("aria-current");
  assert.ok(row.classList.contains("h-control-sm"));
  assert.ok(row.classList.contains("rounded-md"));
  assert.ok(action, "every tree row has an independent menu button");
  assert.ok(title.classList.contains(selected ? "font-semibold" : "font-normal"));
  assert.ok(!title.classList.contains(selected ? "font-normal" : "font-semibold"));
  const depth = Number(treeItem.getAttribute("aria-level"));
  assert.ok(treeItem.classList.contains(["pl-space-1_5", "pl-space-4", "pl-tree-depth-3", "pl-control-md"][depth - 1]));
  assert.ok(treeItem.classList.contains(depth === 1 ? "text-foreground" : "text-foreground-control"));
}
const selectedLeaf = sidebarTree.querySelector('[data-sidebar-leaf="DRL-MTH-T02-C01-U01-03"]');
assert.ok(selectedLeaf);
assert.ok(selectedLeaf.classList.contains("bg-surface-selected/70"));
assert.ok(selectedLeaf.matches('[data-selected="true"]'));
assert.ok(selectedLeaf.querySelector('button[aria-label$="Set 3"].size-touch'));
assert.ok(selectedLeaf.querySelector('button[aria-label$="Set 3"]')?.classList.contains("lg:size-control-xs"));
assert.match(sidebarTreeHtml, /aria-level="1" aria-expanded="true"/);
assert.doesNotMatch(sidebarTreeHtml, /role="group" class="ml-space-3/, "sidebar branches keep a shared left edge");
assert.match(sidebarTreeHtml, /bg-transparent[^>]*>2<\/span>/, "sidebar counts have no fill");

const depthTokens = ["pl-space-1_5", "pl-space-4", "pl-tree-depth-3", "pl-control-md"];
for (const depth of [1, 2, 3, 4] as const) {
  const row = renderToStaticMarkup(<ListRow variant="tree" treeDepth={depth} label="Curriculum row" />);
  const classes = row.match(/class="([^"]+)"/)?.[1].split(" ") ?? [];
  assert.deepEqual(classes.filter((name) => name.startsWith("pl-")), [depthTokens[depth - 1]]);
  assert.ok(classes.includes("w-full") && classes.includes("h-control-sm") && classes.includes("rounded-md"));
}

const leafLayout = (selected: boolean, actionOpen: boolean) => {
  const markup = renderToStaticMarkup(
    <ListRow
      variant="tree"
      treeDepth={4}
      selected={selected}
      label="Drill"
      treeRow={{ action: <button type="button">Actions</button>, actionOpen }}
    />
  );
  if (actionOpen) assert.match(markup, /data-menu-open="true"/);
  const [surface, button] = Array.from(markup.matchAll(/class="([^"]+)"/g), ([, classes]) => classes);
  return {
    surface: surface.split(" ").filter((name) => !name.includes("bg-")),
    button: button.split(" ").filter((name) => !name.startsWith("text-foreground")),
  };
};
const idleLeaf = leafLayout(false, false);
assert.deepEqual(leafLayout(true, false), idleLeaf, "selection preserves the leaf box");
assert.deepEqual(leafLayout(false, true), idleLeaf, "opening actions preserves the leaf box");

const sectionClass = (expanded: boolean) => {
  const html = renderToStaticMarkup(
    <SectionHeader expanded={expanded} controls="labs-panel">Labs</SectionHeader>
  );
  assert.match(html, new RegExp(`aria-expanded="${expanded}" aria-controls="labs-panel"`));
  assert.equal(html.includes("rotate-90"), expanded);
  return html.match(/class="([^"]+)"/)?.[1];
};
assert.equal(sectionClass(true), sectionClass(false), "section header preserves its box when toggled");

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
    assert.match(attributes, /\bsize-touch\b.*\blg:size-control-sm\b/);
    assert.equal(attributes.includes('aria-current="page"'), name === (workspace === "math" ? "Math" : "Programming"));
  }
  const track = workspaceSwitchHtml.match(/<nav aria-label="Workspace" class="([^"]+)"/)?.[1];
  assert.match(track ?? "", /grid-cols-2.*p-space-0_5.*lg:p-space-0/);
  assert.match(track ?? "", /rounded-lg/);
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

// ---------------------------------------------------------------------------
// 5. PRG sidebar unified Labs + Drills sections, collapsible headers & localStorage
// ---------------------------------------------------------------------------
const prgSidebarDrills: DrillListItem[] = [
  makeDrill("DRL-PRG-T01-C01-U01-01", "PRG-T01-C01-U01", "Execution Context & Scope", {
    topicCode: "PRG-T01",
    topicTitle: "JS, TS & Data Structures",
    chapterCode: "PRG-T01-C01",
    chapterTitle: "JS Execution & Async",
    practiceStatus: "In Progress",
  }),
  makeDrill("DRL-PRG-T01-C01-U02-01", "PRG-T01-C01-U02", "Closures", {
    topicCode: "PRG-T01",
    topicTitle: "JS, TS & Data Structures",
    chapterCode: "PRG-T01-C01",
    chapterTitle: "JS Execution & Async",
    hasNotes: true,
  }),
];
const prgSidebarLabs: LabListItem[] = [
  makeLab("LAB-PRG-T01-C01-02", "PRG-T01-C01", "Rate-Limited Web Page Fetcher", {
    chapterTitle: "JavaScript Execution & Async Internals",
    practiceStatus: "Ready",
    hasNotes: true,
  }),
  makeLab("LAB-PRG-T01-C01-01", "PRG-T01-C01", "TinyEventEmitter & PromisePool", {
    chapterTitle: "JavaScript Execution & Async Internals",
    practiceStatus: "In Progress",
  }),
  makeLab("LAB-PRG-T01-C04-02", "PRG-T01-C04", "Full-Stack E-Commerce Core & Checkout Engine", {
    unitCode: "PRG-T01-C04-U06",
    unitTitle: "Packaging, Exports & DevVault Core",
    chapterTitle: "Problem Solving, Clean Utilities & Unit Testing",
    practiceStatus: "Ready",
  }),
];

const prgLabSections = buildPickerSections({
  items: normalizeLabPickerItems(prgSidebarLabs),
  currentId: "LAB-PRG-T01-C01-01",
  recentIds: [],
  search: "",
  filter: "ALL",
});
assert.equal(prgLabSections.topicGroups.length, 1);
assert.equal(prgLabSections.topicGroups[0].topicCode, "PRG-T01");
assert.equal(prgLabSections.topicGroups[0].chapters.length, 2);

const c01LabChapter = prgLabSections.topicGroups[0].chapters[0];
assert.equal(c01LabChapter.chapterCode, "PRG-T01-C01");
assert.equal(c01LabChapter.itemCount, 2, "two labs under one chapter share the chapter group");
assert.deepEqual(
  c01LabChapter.entries.map((entry) => (entry.kind === "single" ? entry.item.id : entry.key)),
  ["LAB-PRG-T01-C01-01", "LAB-PRG-T01-C01-02"],
  "two labs under one chapter sort naturally as sibling chapter leaves"
);

const c04LabChapter = prgLabSections.topicGroups[0].chapters[1];
assert.equal(c04LabChapter.chapterCode, "PRG-T01-C04");
assert.equal(c04LabChapter.entries.length, 1);
assert.equal(c04LabChapter.entries[0].kind, "unit-group", "unit-scoped lab nests under a Unit folder");
if (c04LabChapter.entries[0].kind === "unit-group") {
  assert.equal(c04LabChapter.entries[0].unitCode, "PRG-T01-C04-U06");
  assert.equal(c04LabChapter.entries[0].unitTitle, "Packaging, Exports & DevVault Core");
  assert.equal(c04LabChapter.entries[0].inlineInChapter, false);
  assert.equal(
    c04LabChapter.entries[0].items[0].setLabel,
    "Full-Stack E-Commerce Core & Checkout Engine",
    "unit-scoped lab leaf uses the lab title rather than Set N"
  );
}

const labTreeRows = buildVisibleTreeRows({
  topicGroups: prgLabSections.topicGroups,
  currentId: "LAB-PRG-T01-C01-01",
  expandedTopics: new Set(prgLabSections.defaultExpandedTopics),
  expandedChapters: new Set(prgLabSections.defaultExpandedChapters),
  expandedUnits: new Set(prgLabSections.defaultExpandedUnits),
  dueUnitCodes: new Set(["PRG-T01-C01"]),
  nodeIdPrefix: "lab:",
});
assert.deepEqual(
  labTreeRows.map((r) => [r.kind, r.level, r.nodeId]),
  [
    ["topic", 1, "lab:topic:PRG-T01"],
    ["chapter", 2, "lab:chapter:PRG-T01-C01"],
    ["leaf", 3, "leaf:LAB-PRG-T01-C01-01"],
    ["leaf", 3, "leaf:LAB-PRG-T01-C01-02"],
    ["chapter", 2, "lab:chapter:PRG-T01-C04"],
  ]
);
if (labTreeRows[2].kind === "leaf" && labTreeRows[3].kind === "leaf") {
  assert.equal(labTreeRows[2].isCurrent, true);
  assert.equal(labTreeRows[2].label, "TinyEventEmitter & PromisePool");
  assert.equal(labTreeRows[2].isDueToday, true);
  assert.equal(labTreeRows[3].label, "Rate-Limited Web Page Fetcher");
  assert.equal(labTreeRows[3].hasNotes, true);
}

const prgDrillSections = buildPickerSections({
  items: normalizeDrillPickerItems(prgSidebarDrills),
  currentId: "DRL-PRG-T01-C01-U01-01",
  recentIds: [],
  search: "",
  filter: "ALL",
});
const combinedRows = [
  ...labTreeRows,
  ...buildVisibleTreeRows({
    topicGroups: prgDrillSections.topicGroups,
    currentId: "DRL-PRG-T01-C01-U01-01",
    expandedTopics: new Set(prgDrillSections.defaultExpandedTopics),
    expandedChapters: new Set(prgDrillSections.defaultExpandedChapters),
    expandedUnits: new Set(prgDrillSections.defaultExpandedUnits),
  }),
];
assert.deepEqual(
  resolveTreeKeyAction(combinedRows, "lab:chapter:PRG-T01-C04", "ArrowDown"),
  { type: "focus", nodeId: "topic:PRG-T01" },
  "ArrowDown navigates seamlessly from Labs tree into Drills tree"
);
assert.deepEqual(
  resolveTreeKeyAction(combinedRows, "topic:PRG-T01", "ArrowUp"),
  { type: "focus", nodeId: "lab:chapter:PRG-T01-C04" },
  "ArrowUp navigates seamlessly from Drills tree back to Labs tree"
);
assert.deepEqual(
  resolveTreeKeyAction(combinedRows, "leaf:LAB-PRG-T01-C01-01", "Enter"),
  { type: "select", itemId: "LAB-PRG-T01-C01-01" },
  "Enter selects a lab row"
);
assert.deepEqual(
  resolveTreeKeyAction(combinedRows, "leaf:LAB-PRG-T01-C01-01", "ArrowLeft"),
  { type: "focus", nodeId: "lab:chapter:PRG-T01-C01" },
  "ArrowLeft on lab leaf focuses its parent chapter"
);
assert.deepEqual(
  resolveTreeKeyAction(combinedRows, "lab:topic:PRG-T01", "ArrowLeft"),
  { type: "collapse", nodeKind: "topic", code: "PRG-T01" },
  "ArrowLeft on expanded Labs topic collapses Labs topic without colliding with Drills topic"
);

// PRG sidebar SSR: no Drills/Labs tabs, both sections in one scrolling tree, collapsible headers with trailing chevrons
const prgSidebarHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={prgSidebarDrills}
    labs={prgSidebarLabs}
    dueUnitCodes={["PRG-T01-C01", "PRG-T01-C01-U02"]}
    selectedDrillId="LAB-PRG-T01-C01-01"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.doesNotMatch(prgSidebarHtml, /role="tablist"/, "PRG sidebar removes Drills/Labs switch tabs");
assert.doesNotMatch(prgSidebarHtml, /aria-label="Practice type"/);
assert.match(prgSidebarHtml, /data-sidebar-section="labs"/);
assert.match(prgSidebarHtml, /data-sidebar-section="drills"/);
assert.ok(
  prgSidebarHtml.indexOf('data-sidebar-section="labs"') <
    prgSidebarHtml.indexOf('data-sidebar-section="drills"'),
  "Labs section appears before Drills section"
);
assert.match(
  prgSidebarHtml,
  /<button[^>]*aria-expanded="true"[^>]*><span>Labs<\/span><svg[^>]*lucide-chevron-right[^>]*rotate-90[^>]*><path[^>]*><\/path><\/svg><\/button>/,
  "Labs section header has aria-expanded and small muted trailing chevron rotated when expanded"
);
assert.match(
  prgSidebarHtml,
  /<button[^>]*aria-expanded="true"[^>]*><span>Drills<\/span><svg[^>]*lucide-chevron-right[^>]*rotate-90[^>]*><path[^>]*><\/path><\/svg><\/button>/,
  "Drills section header has aria-expanded and small muted trailing chevron rotated when expanded"
);
assert.match(prgSidebarHtml, /motion-reduce:transition-none/);
assert.match(prgSidebarHtml, /JavaScript Execution &amp; Async Internals/);
assert.match(prgSidebarHtml, /TinyEventEmitter &amp; PromisePool/);
assert.match(prgSidebarHtml, /Rate-Limited Web Page Fetcher/);
assert.doesNotMatch(prgSidebarHtml, />LAB-0[12]</);
assert.match(prgSidebarHtml, /data-sidebar-leaf="LAB-PRG-T01-C01-01"/);
assert.match(prgSidebarHtml, /data-sidebar-leaf="LAB-PRG-T01-C01-02"/);
assert.match(prgSidebarHtml, /data-sidebar-row="leaf-3"/);
assert.match(prgSidebarHtml, /aria-label="Actions for TinyEventEmitter &amp; PromisePool"/);
assert.match(prgSidebarHtml, /Due today/);
assert.match(prgSidebarHtml, /aria-current="true"/);

// Unit-scoped lab selected in PRG sidebar expands Topic -> Chapter -> Unit -> Lab leaf (level 4)
const prgSidebarUnitLabHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={prgSidebarDrills}
    labs={prgSidebarLabs}
    selectedDrillId="LAB-PRG-T01-C04-02"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.match(prgSidebarUnitLabHtml, /Problem Solving, Clean Utilities &amp; Unit Testing/);
assert.match(prgSidebarUnitLabHtml, /data-sidebar-row="unit"[^>]*>[\s\S]*?Packaging, Exports &amp; DevVault Core/);
assert.doesNotMatch(prgSidebarUnitLabHtml, />U06</);
assert.match(prgSidebarUnitLabHtml, /data-sidebar-leaf="LAB-PRG-T01-C04-02"/);
assert.match(prgSidebarUnitLabHtml, /data-sidebar-row="leaf-4"/);
assert.match(prgSidebarUnitLabHtml, /Full-Stack E-Commerce Core &amp; Checkout Engine/);

const prgSidebarDrillSelectedHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={prgSidebarDrills}
    labs={prgSidebarLabs}
    dueUnitCodes={["PRG-T01-C04", "PRG-T01-C01-U02"]}
    selectedDrillId="DRL-PRG-T01-C01-U01-01"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.match(
  prgSidebarDrillSelectedHtml,
  /aria-label="Actions for Execution Context &amp; Scope"/,
  "Drill leaves keep action menus"
);
assert.match(prgSidebarDrillSelectedHtml, /data-sidebar-leaf="DRL-PRG-T01-C01-U01-01"/);

// Empty Labs section shows quiet "No labs yet"
const prgSidebarNoLabsHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={prgSidebarDrills}
    labs={[]}
    selectedDrillId="DRL-PRG-T01-C01-U01-01"
    drillSearch=""
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.match(prgSidebarNoLabsHtml, />No labs yet</);
assert.match(prgSidebarNoLabsHtml, /data-sidebar-section="drills"/);

// Searching hides non-matching empty section; no matches shows combined empty state
const prgSidebarSearchDrillsHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={prgSidebarDrills}
    labs={prgSidebarLabs}
    selectedDrillId="DRL-PRG-T01-C01-U01-01"
    drillSearch="closures"
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.doesNotMatch(prgSidebarSearchDrillsHtml, /data-sidebar-section="labs"/);
assert.match(prgSidebarSearchDrillsHtml, /data-sidebar-section="drills"/);

const prgSidebarSearchEmptyHtml = renderToStaticMarkup(
  <DrillSwitcher
    mode="sidebar"
    isOpen={true}
    onToggle={noop}
    onClose={noop}
    switcherRef={{ current: null }}
    workspace="code"
    currentDrill={null}
    drills={prgSidebarDrills}
    labs={prgSidebarLabs}
    selectedDrillId="DRL-PRG-T01-C01-U01-01"
    drillSearch="nonexistent-xyz"
    onSearchChange={noop}
    drillFilter="ALL"
    onFilterChange={noop}
    onSelectDrill={noop}
  />
);
assert.match(prgSidebarSearchEmptyHtml, /No drills or labs match the current search or filter\./);

// Math sidebar remains unchanged (no Labs/Drills section headers)
assert.doesNotMatch(sidebarTreeHtml, /data-sidebar-section="labs"/);
assert.doesNotMatch(sidebarTreeHtml, /data-sidebar-section="drills"/);

// localStorage persistence for PRG sidebar sections (defaults true, persists, wraps errors safely)
{
  const originalWindow = (globalThis as { window?: unknown }).window;
  try {
    const store = new Map<string, string>();
    (globalThis as { window: unknown }).window = {
      localStorage: {
        getItem: (k: string) => store.get(k) ?? null,
        setItem: (k: string, v: string) => {
          store.set(k, String(v));
        },
      },
    };
    assert.equal(readSidebarSectionExpanded("labs"), true);
    assert.equal(readSidebarSectionExpanded("drills"), true);
    writeSidebarSectionExpanded("labs", false);
    assert.equal(store.get(PRG_SECTION_STORAGE_KEYS.labs), "false");
    assert.equal(readSidebarSectionExpanded("labs"), false);
    assert.equal(readSidebarSectionExpanded("drills"), true);
    writeSidebarSectionExpanded("labs", true);
    assert.equal(readSidebarSectionExpanded("labs"), true);

    // Throwing localStorage falls back safely
    (globalThis as { window: unknown }).window = {
      localStorage: {
        getItem: () => {
          throw new Error("denied");
        },
        setItem: () => {
          throw new Error("quota");
        },
      },
    };
    assert.equal(readSidebarSectionExpanded("labs"), true);
    writeSidebarSectionExpanded("drills", false);
  } finally {
    if (originalWindow === undefined) {
      delete (globalThis as { window?: unknown }).window;
    } else {
      (globalThis as { window: unknown }).window = originalWindow;
    }
  }
}

console.log("drill tree tests passed");
