import type { DrillFilter } from "@/hooks/types";
import type { LabListItem } from "@/lib/labModel";
import type { DrillListItem } from "@/types/drill";

export type PickerStatus = "Ready" | "In Progress" | "Graded" | "Needs Retry";

export interface DrillSetEntry {
  drill: DrillListItem;
  setLabel: string;
  setNumber: number | null;
}

export type DrillSwitcherEntry =
  | {
      kind: "single";
      key: string;
      drill: DrillListItem;
    }
  | {
      kind: "group";
      key: string;
      unitCode: string;
      unitTitle: string;
      items: DrillSetEntry[];
    };

export interface PickerItem {
  kind: "drill" | "lab";
  subject: "MATH" | "PRG";
  id: string;
  title: string;
  setLabel: string | null;
  unitCode: string;
  chapterCode: string;
  chapterTitle: string;
  topicCode: string;
  topicTitle: string;
  practiceStatus: PickerStatus;
  score: number;
  maxScore: number;
  countLabel: string;
  createdAt: string;
  answeredCount: number;
  hasNotes: boolean;
}

export interface PickerSetEntry {
  item: PickerItem;
  setLabel: string;
  setNumber: number | null;
}

export type PickerChapterEntry =
  | {
      kind: "single";
      key: string;
      item: PickerItem;
    }
  | {
      kind: "unit-group";
      key: string;
      unitCode: string;
      unitTitle: string;
      inlineInChapter: boolean;
      containsCurrent: boolean;
      items: PickerSetEntry[];
    };

export interface PickerChapterGroup {
  chapterCode: string;
  chapterTitle: string;
  itemCount: number;
  containsCurrent: boolean;
  entries: PickerChapterEntry[];
}

export interface PickerTopicGroup {
  topicCode: string;
  topicTitle: string;
  itemCount: number;
  containsCurrent: boolean;
  chapters: PickerChapterGroup[];
}

export interface PickerSectionsResult {
  isSearching: boolean;
  currentItem: PickerItem | null;
  continueItems: PickerItem[];
  topicGroups: PickerTopicGroup[];
  defaultExpandedTopics: string[];
  defaultExpandedChapters: string[];
  defaultExpandedUnits: string[];
  totalVisibleCount: number;
}

export interface NavigablePickerRow {
  navIndex: number;
  id: string;
  section: "current" | "continue" | "tree";
}

/** Extract the trailing set number from a drill ID like `DRL-MTH-T01-C04-02` -> `2`. */
export function extractDrillSetNumber(drillId: string): number | null {
  const match = /-(\d+)$/.exec(drillId.trim());
  if (!match) return null;
  const parsed = Number.parseInt(match[1], 10);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Format a compact child label like `"Set 1"` from a drill ID, falling back to `drillId`. */
export function formatDrillSetLabel(drillId: string): string {
  const num = extractDrillSetNumber(drillId);
  return num !== null ? `Set ${num}` : drillId;
}

/** Strip inline markdown backticks and trim whitespace from curriculum titles. */
export function cleanCurriculumTitle(title: string | null | undefined): string {
  if (typeof title !== "string") return "";
  return title.replace(/`/g, "").trim();
}

/**
 * Derive `topicCode` and `chapterCode` from a unit code (e.g. `MTH-T02-C01-U01` ->
 * `MTH-T02` and `MTH-T02-C01`), honoring explicit overrides when present.
 */
export function parseCurriculumCodes(
  unitCode: string,
  explicitTopicCode?: string | null,
  explicitChapterCode?: string | null
): { topicCode: string; chapterCode: string } {
  const cleanUnit = (unitCode || "").trim();
  const cleanTopic = (explicitTopicCode || "").trim();
  const cleanChapter = (explicitChapterCode || "").trim();

  const match = /^([A-Za-z]+-T\d+)(?:-(C\d+))?(?:-U\d+)?$/i.exec(cleanUnit);
  const derivedTopic = match ? match[1].toUpperCase() : "";
  const derivedChapter = match && match[2] ? `${match[1].toUpperCase()}-${match[2].toUpperCase()}` : "";

  const chapterMatch = /^([A-Za-z]+-T\d+)-C\d+/i.exec(cleanChapter);
  const topicFromChapter = chapterMatch ? chapterMatch[1].toUpperCase() : "";

  const topicCode = cleanTopic || topicFromChapter || derivedTopic || "OTHER";
  const chapterCode = cleanChapter || derivedChapter || cleanUnit || topicCode;
  return { topicCode, chapterCode };
}

/** Natural alphanumeric comparison for curriculum codes (`T00` < `T01` < `T02` < `T10`). */
export function compareCurriculumCodes(a: string, b: string): number {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
}

/**
 * Group drills that share a unit/chapter code under one unit header while keeping
 * single-drill units as flat rows. Preserves group insertion order and sorts sets
 * within a multi-drill unit by trailing set number ascending.
 */
export function groupDrillsByUnit(
  drills: readonly DrillListItem[]
): DrillSwitcherEntry[] {
  const buckets = new Map<string, DrillListItem[]>();

  for (const drill of drills) {
    const key = drill.unitCode.trim() || drill.drillId;
    const existing = buckets.get(key);
    if (existing) {
      existing.push(drill);
    } else {
      buckets.set(key, [drill]);
    }
  }

  const entries: DrillSwitcherEntry[] = [];

  for (const [key, list] of Array.from(buckets.entries())) {
    if (list.length === 1) {
      entries.push({
        kind: "single",
        key,
        drill: list[0],
      });
      continue;
    }

    const sorted = sortDrillsBySetNumber(list);
    const unitCode = sorted[0].unitCode.trim() || key;
    const unitTitle =
      sorted.find((d) => d.unitTitle && d.unitTitle.trim())?.unitTitle.trim() ||
      unitCode;

    entries.push({
      kind: "group",
      key,
      unitCode,
      unitTitle,
      items: sorted.map((drill) => ({
        drill,
        setNumber: extractDrillSetNumber(drill.drillId),
        setLabel: formatDrillSetLabel(drill.drillId),
      })),
    });
  }

  return entries;
}

function sortDrillsBySetNumber<T extends { drillId: string }>(list: readonly T[]): T[] {
  return [...list].sort((a, b) => {
    const aNum = extractDrillSetNumber(a.drillId);
    const bNum = extractDrillSetNumber(b.drillId);
    if (aNum !== null && bNum !== null && aNum !== bNum) {
      return aNum - bNum;
    }
    if (aNum !== null && bNum === null) return -1;
    if (aNum === null && bNum !== null) return 1;
    return a.drillId.localeCompare(b.drillId);
  });
}

function normalizeStatus(raw?: string): PickerStatus {
  if (raw === "In Progress" || raw === "Graded" || raw === "Needs Retry") {
    return raw;
  }
  return "Ready";
}

/** Normalize raw `DrillListItem[]` into uniform `PickerItem[]` with Topic/Chapter metadata. */
export function normalizeDrillPickerItems(drills: readonly DrillListItem[]): PickerItem[] {
  const unitCounts = new Map<string, number>();
  for (const d of drills) {
    const key = d.unitCode.trim() || d.drillId;
    unitCounts.set(key, (unitCounts.get(key) ?? 0) + 1);
  }

  return drills.map((d) => {
    const unitCode = d.unitCode.trim() || d.drillId;
    const { topicCode, chapterCode } = parseCurriculumCodes(
      unitCode,
      d.topicCode,
      d.chapterCode
    );
    const title = cleanCurriculumTitle(d.unitTitle) || unitCode;
    const chapterTitle =
      cleanCurriculumTitle(d.chapterTitle) ||
      (chapterCode === unitCode ? title : chapterCode);
    const topicTitle = cleanCurriculumTitle(d.topicTitle) || topicCode;
    const hasMultipleSets = (unitCounts.get(unitCode) ?? 0) > 1;
    const setLabel = hasMultipleSets ? formatDrillSetLabel(d.drillId) : null;

    return {
      kind: "drill",
      subject:
        d.subject === "PRG" || unitCode.toUpperCase().startsWith("PRG-") ? "PRG" : "MATH",
      id: d.drillId,
      title,
      setLabel,
      unitCode,
      chapterCode,
      chapterTitle,
      topicCode,
      topicTitle,
      practiceStatus: normalizeStatus(d.practiceStatus),
      score: d.score ?? 0,
      maxScore: d.maxScore ?? d.questionCount,
      countLabel: `${d.questionCount} Qs`,
      createdAt: d.createdAt || "",
      answeredCount: d.answeredCount ?? 0,
      hasNotes: Boolean(d.hasNotes),
    };
  });
}

/** Normalize raw `LabListItem[]` into uniform `PickerItem[]` with Topic/Chapter metadata. */
export function normalizeLabPickerItems(labs: readonly LabListItem[]): PickerItem[] {
  return labs.map((l) => {
    const primaryCode = (l.chapterCode || l.unitCode || l.id).trim();
    const { topicCode, chapterCode } = parseCurriculumCodes(
      primaryCode,
      l.topicCode,
      l.chapterCode
    );
    const chapterTitle = cleanCurriculumTitle(l.chapterTitle) || chapterCode;
    const topicTitle = cleanCurriculumTitle(l.topicTitle) || topicCode;

    return {
      kind: "lab",
      subject: "PRG",
      id: l.id,
      title: cleanCurriculumTitle(l.title) || l.id,
      setLabel: null,
      unitCode: primaryCode,
      chapterCode,
      chapterTitle,
      topicCode,
      topicTitle,
      practiceStatus: normalizeStatus(l.practiceStatus),
      score: l.passedCount ?? l.score ?? 0,
      maxScore: l.milestoneCount ?? l.maxScore ?? 0,
      countLabel: `${l.milestoneCount} Ms`,
      createdAt: "",
      answeredCount: (l.passedCount ?? 0) + (l.reviseCount ?? 0),
      hasNotes: Boolean(l.hasNotes),
    };
  });
}

/** Tokenized case-insensitive match across titles, unit/chapter/topic codes, and full IDs. */
export function matchesSearchTokens(
  fields: readonly (string | null | undefined)[],
  query: string
): boolean {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return true;
  const tokens = trimmed.split(/\s+/).filter(Boolean);
  const haystack = fields
    .filter((f): f is string => typeof f === "string" && f.length > 0)
    .join(" ")
    .toLowerCase();
  return tokens.every((token) => haystack.includes(token));
}

function matchesStatusFilter(practiceStatus: string | undefined, filter: DrillFilter): boolean {
  if (filter === "UNFINISHED") return practiceStatus !== "Graded";
  if (filter === "GRADED") return practiceStatus === "Graded";
  return true;
}

/** Filter raw drills by status filter and search query (matches title, codes, and drill ID). */
export function filterDrills(
  drills: readonly DrillListItem[],
  search: string,
  filter: DrillFilter
): DrillListItem[] {
  return drills.filter((d) => {
    if (!matchesStatusFilter(d.practiceStatus, filter)) return false;
    const { topicCode, chapterCode } = parseCurriculumCodes(
      d.unitCode,
      d.topicCode,
      d.chapterCode
    );
    return matchesSearchTokens(
      [
        d.drillId,
        d.unitCode,
        d.unitTitle,
        chapterCode,
        d.chapterTitle,
        topicCode,
        d.topicTitle,
      ],
      search
    );
  });
}

/** Filter raw labs by status filter and search query (matches title, codes, and lab ID). */
export function filterLabs(
  labs: readonly LabListItem[],
  search: string,
  filter: DrillFilter
): LabListItem[] {
  return labs.filter((l) => {
    if (!matchesStatusFilter(l.practiceStatus, filter)) return false;
    const { topicCode, chapterCode } = parseCurriculumCodes(
      l.chapterCode || l.unitCode,
      l.topicCode,
      l.chapterCode
    );
    return matchesSearchTokens(
      [
        l.id,
        l.labId,
        l.title,
        l.unitCode,
        chapterCode,
        l.chapterTitle,
        topicCode,
        l.topicTitle,
      ],
      search
    );
  });
}

/** Filter normalized picker items by status filter and search query. */
export function filterPickerItems(
  items: readonly PickerItem[],
  search: string,
  filter: DrillFilter
): PickerItem[] {
  return items.filter((item) => {
    if (!matchesStatusFilter(item.practiceStatus, filter)) return false;
    return matchesSearchTokens(
      [
        item.id,
        item.title,
        item.setLabel,
        item.unitCode,
        item.chapterCode,
        item.chapterTitle,
        item.topicCode,
        item.topicTitle,
      ],
      search
    );
  });
}

export function isUnfinishedPracticeStatus(status: PickerStatus): boolean {
  return status === "In Progress" || status === "Needs Retry";
}

/**
 * Pick up to `limit` items for the "Continue" section, excluding `currentId`.
 * Prioritizes recently opened unfinished items (MRU order), then other unfinished items,
 * then recently opened Ready items, then recently opened Graded items.
 */
export function selectContinueItems(
  items: readonly PickerItem[],
  currentId: string,
  recentIds: readonly string[],
  limit = 3
): PickerItem[] {
  if (limit <= 0) return [];
  const recentOrder = new Map<string, number>();
  recentIds.forEach((id, idx) => {
    const trimmed = id.trim();
    if (trimmed && !recentOrder.has(trimmed)) {
      recentOrder.set(trimmed, idx);
    }
  });

  const candidates = items.filter((item) => {
    if (item.id === currentId) return false;
    const isRecent = recentOrder.has(item.id);
    const isUnfinished = isUnfinishedPracticeStatus(item.practiceStatus);
    return isRecent || isUnfinished;
  });

  const tierOf = (item: PickerItem): number => {
    const isRecent = recentOrder.has(item.id);
    const isUnfinished = isUnfinishedPracticeStatus(item.practiceStatus);
    if (isRecent && isUnfinished) return 0;
    if (isUnfinished) return 1;
    if (isRecent && item.practiceStatus === "Ready") return 2;
    return 3;
  };

  candidates.sort((a, b) => {
    const tierA = tierOf(a);
    const tierB = tierOf(b);
    if (tierA !== tierB) return tierA - tierB;

    if (tierA === 0 || tierA === 2 || tierA === 3) {
      const recA = recentOrder.get(a.id) ?? Number.MAX_SAFE_INTEGER;
      const recB = recentOrder.get(b.id) ?? Number.MAX_SAFE_INTEGER;
      if (recA !== recB) return recA - recB;
    }

    if (a.practiceStatus !== b.practiceStatus) {
      if (a.practiceStatus === "In Progress") return -1;
      if (b.practiceStatus === "In Progress") return 1;
    }
    if (a.answeredCount !== b.answeredCount) {
      return b.answeredCount - a.answeredCount;
    }
    if (a.createdAt !== b.createdAt) {
      return b.createdAt.localeCompare(a.createdAt);
    }
    return compareCurriculumCodes(a.unitCode, b.unitCode);
  });

  return candidates.slice(0, limit);
}

/**
 * Group normalized picker items hierarchically by Topic -> Chapter -> Unit/Sets,
 * sorted naturally by curriculum code. Marks `containsCurrent` on groups containing `currentId`.
 */
export function groupItemsByTopicAndChapter(
  items: readonly PickerItem[],
  currentId: string
): PickerTopicGroup[] {
  const topicMap = new Map<
    string,
    {
      topicCode: string;
      topicTitle: string;
      chapters: Map<
        string,
        {
          chapterCode: string;
          chapterTitle: string;
          items: PickerItem[];
        }
      >;
    }
  >();

  for (const item of items) {
    let topicBucket = topicMap.get(item.topicCode);
    if (!topicBucket) {
      topicBucket = {
        topicCode: item.topicCode,
        topicTitle: item.topicTitle || item.topicCode,
        chapters: new Map(),
      };
      topicMap.set(item.topicCode, topicBucket);
    } else if (topicBucket.topicTitle === topicBucket.topicCode && item.topicTitle !== item.topicCode) {
      topicBucket.topicTitle = item.topicTitle;
    }

    let chapterBucket = topicBucket.chapters.get(item.chapterCode);
    if (!chapterBucket) {
      chapterBucket = {
        chapterCode: item.chapterCode,
        chapterTitle: item.chapterTitle || item.chapterCode,
        items: [],
      };
      topicBucket.chapters.set(item.chapterCode, chapterBucket);
    } else if (
      chapterBucket.chapterTitle === chapterBucket.chapterCode &&
      item.chapterTitle !== item.chapterCode
    ) {
      chapterBucket.chapterTitle = item.chapterTitle;
    }

    chapterBucket.items.push(item);
  }

  const topics = Array.from(topicMap.values()).sort((a, b) =>
    compareCurriculumCodes(a.topicCode, b.topicCode)
  );

  return topics.map((topic) => {
    const rawChapters = Array.from(topic.chapters.values()).sort((a, b) =>
      compareCurriculumCodes(a.chapterCode, b.chapterCode)
    );

    const chapters: PickerChapterGroup[] = rawChapters.map((chapter) => {
      const entries = buildChapterEntries(chapter.items, chapter.chapterCode, currentId);
      const containsCurrent = chapter.items.some((item) => item.id === currentId);
      return {
        chapterCode: chapter.chapterCode,
        chapterTitle: chapter.chapterTitle,
        itemCount: chapter.items.length,
        containsCurrent,
        entries,
      };
    });

    return {
      topicCode: topic.topicCode,
      topicTitle: topic.topicTitle,
      itemCount: chapters.reduce((sum, ch) => sum + ch.itemCount, 0),
      containsCurrent: chapters.some((ch) => ch.containsCurrent),
      chapters,
    };
  });
}

function buildChapterEntries(
  items: readonly PickerItem[],
  chapterCode: string,
  currentId = ""
): PickerChapterEntry[] {
  const unitBuckets = new Map<string, PickerItem[]>();
  for (const item of items) {
    const bucketKey = item.kind === "lab" ? item.id : item.unitCode;
    const existing = unitBuckets.get(bucketKey);
    if (existing) {
      existing.push(item);
    } else {
      unitBuckets.set(bucketKey, [item]);
    }
  }

  const sortedKeys = Array.from(unitBuckets.keys()).sort(compareCurriculumCodes);
  const entries: PickerChapterEntry[] = [];

  for (const key of sortedKeys) {
    const unitItems = unitBuckets.get(key) ?? [];
    if (unitItems.length === 1) {
      entries.push({
        kind: "single",
        key: unitItems[0].id,
        item: unitItems[0],
      });
      continue;
    }

    const sortedSets = [...unitItems].sort((a, b) => {
      const aNum = extractDrillSetNumber(a.id);
      const bNum = extractDrillSetNumber(b.id);
      if (aNum !== null && bNum !== null && aNum !== bNum) return aNum - bNum;
      if (aNum !== null && bNum === null) return -1;
      if (aNum === null && bNum !== null) return 1;
      return a.id.localeCompare(b.id);
    });

    const unitCode = sortedSets[0].unitCode;
    const unitTitle = sortedSets[0].title;
    entries.push({
      kind: "unit-group",
      key: unitCode,
      unitCode,
      unitTitle,
      inlineInChapter: sortedKeys.length === 1 && unitCode === chapterCode,
      containsCurrent: sortedSets.some((item) => item.id === currentId),
      items: sortedSets.map((item) => ({
        item,
        setNumber: extractDrillSetNumber(item.id),
        setLabel: formatDrillSetLabel(item.id),
      })),
    });
  }

  return entries;
}

/**
 * Build all picker sections (`Current`, `Continue`, `Topic -> Chapter` groups) and
 * determine which groups start expanded.
 */
export function buildPickerSections(options: {
  items: readonly PickerItem[];
  currentId: string;
  recentIds: readonly string[];
  search: string;
  filter: DrillFilter;
  continueLimit?: number;
}): PickerSectionsResult {
  const { items, currentId, recentIds, search, filter, continueLimit = 3 } = options;
  const isSearching = search.trim().length > 0;
  const filtered = filterPickerItems(items, search, filter);

  const currentItem = !isSearching
    ? filtered.find((item) => item.id === currentId) ?? null
    : null;

  const continueItems =
    !isSearching && filter !== "GRADED"
      ? selectContinueItems(filtered, currentId, recentIds, continueLimit)
      : [];

  const topicGroups = groupItemsByTopicAndChapter(filtered, currentId);

  const defaultExpandedTopics = isSearching
    ? topicGroups.map((t) => t.topicCode)
    : topicGroups.filter((t) => t.containsCurrent).map((t) => t.topicCode);

  const defaultExpandedChapters = isSearching
    ? topicGroups.flatMap((t) => t.chapters.map((c) => c.chapterCode))
    : topicGroups.flatMap((t) =>
        t.chapters.filter((c) => c.containsCurrent).map((c) => c.chapterCode)
      );

  const defaultExpandedUnits = topicGroups.flatMap((t) =>
    t.chapters.flatMap((c) =>
      c.entries
        .filter(
          (entry): entry is Extract<PickerChapterEntry, { kind: "unit-group" }> =>
            entry.kind === "unit-group" &&
            !entry.inlineInChapter &&
            (isSearching || entry.containsCurrent)
        )
        .map((entry) => entry.unitCode)
    )
  );

  return {
    isSearching,
    currentItem,
    continueItems,
    topicGroups,
    defaultExpandedTopics,
    defaultExpandedChapters,
    defaultExpandedUnits,
    totalVisibleCount: filtered.length,
  };
}

/**
 * Flatten currently visible picker rows in top-to-bottom visual order for ArrowUp/ArrowDown/Enter navigation.
 */
export function buildNavigableRows(
  sections: PickerSectionsResult,
  expandedTopics: ReadonlySet<string>,
  expandedChapters: ReadonlySet<string>
): NavigablePickerRow[] {
  const rows: NavigablePickerRow[] = [];

  if (sections.currentItem) {
    rows.push({
      navIndex: rows.length,
      id: sections.currentItem.id,
      section: "current",
    });
  }

  for (const item of sections.continueItems) {
    rows.push({
      navIndex: rows.length,
      id: item.id,
      section: "continue",
    });
  }

  for (const topic of sections.topicGroups) {
    const topicExpanded = sections.isSearching || expandedTopics.has(topic.topicCode);
    if (!topicExpanded) continue;

    for (const chapter of topic.chapters) {
      const chapterExpanded =
        sections.isSearching || expandedChapters.has(chapter.chapterCode);
      if (!chapterExpanded) continue;

      for (const entry of chapter.entries) {
        if (entry.kind === "single") {
          rows.push({
            navIndex: rows.length,
            id: entry.item.id,
            section: "tree",
          });
        } else {
          for (const setEntry of entry.items) {
            rows.push({
              navIndex: rows.length,
              id: setEntry.item.id,
              section: "tree",
            });
          }
        }
      }
    }
  }

  return rows;
}

/** Step keyboard highlight index up or down with wrap-around across visible rows. */
export function stepKeyboardIndex(
  currentIndex: number,
  totalItems: number,
  direction: "up" | "down"
): number {
  if (totalItems <= 0) return -1;
  if (direction === "down") {
    if (currentIndex < 0 || currentIndex >= totalItems - 1) return 0;
    return currentIndex + 1;
  }
  if (currentIndex <= 0) return totalItems - 1;
  return currentIndex - 1;
}

/** Clamp or reset the keyboard highlight index when the visible list changes. */
export function clampKeyboardIndex(
  currentIndex: number,
  totalItems: number,
  autoSelectFirst: boolean
): number {
  if (totalItems <= 0) return -1;
  if (currentIndex >= 0 && currentIndex < totalItems) return currentIndex;
  return autoSelectFirst ? 0 : -1;
}

export type DrillTypeIconKind = "math-unit" | "code-unit" | "chapter-mixed" | "lab";

/** Return true when `unitCode` represents a chapter-level mixed drill (no `-U##` unit suffix). */
export function isChapterMixedUnitCode(unitCode: string): boolean {
  return /^[A-Za-z]+-T\d+-C\d+$/i.test(unitCode.trim());
}

/** Extract short code from a unit code (`U01` / `C04`) or lab ID (`LAB-02`). */
export function extractShortCode(
  item: Pick<PickerItem, "kind" | "id" | "unitCode">
): string {
  if (item.kind === "lab") {
    const match = /-(\d+)$/.exec(item.id.trim());
    if (match) return `LAB-${match[1]}`;
    return item.id.trim();
  }
  const code = item.unitCode.trim();
  const unitMatch = /-(U\d+)$/i.exec(code);
  if (unitMatch) return unitMatch[1].toUpperCase();
  const chapterMatch = /-(C\d+)$/i.exec(code);
  if (chapterMatch) return chapterMatch[1].toUpperCase();
  return code || item.id.trim();
}

/** Format full curriculum/drill code for row tooltip (`title` attribute). */
export function formatFullRowCode(
  item: Pick<PickerItem, "kind" | "id" | "unitCode" | "setLabel">
): string {
  if (item.kind === "lab") return item.id;
  if (item.setLabel) return `${item.unitCode} · ${item.id}`;
  return item.unitCode;
}

/** Classify picker item for leaf type iconography. */
export function classifyPickerItemType(
  item: Pick<PickerItem, "kind" | "subject" | "unitCode">
): DrillTypeIconKind {
  if (item.kind === "lab") return "lab";
  if (isChapterMixedUnitCode(item.unitCode)) return "chapter-mixed";
  if (item.subject === "PRG" || item.unitCode.trim().toUpperCase().startsWith("PRG-")) {
    return "code-unit";
  }
  return "math-unit";
}

/** Map internal practice status to concise human-readable status words. */
export function getPickerStatusLabel(status: PickerStatus): string {
  switch (status) {
    case "Graded":
      return "Graded";
    case "In Progress":
      return "In progress";
    case "Needs Retry":
      return "Needs retry";
    default:
      return "Not started";
  }
}

/** Collect all topic, chapter, and expandable unit codes in the currently visible tree. */
export function collectAllTreeCodes(topicGroups: readonly PickerTopicGroup[]): {
  topicCodes: string[];
  chapterCodes: string[];
  unitCodes: string[];
} {
  const topicCodes: string[] = [];
  const chapterCodes: string[] = [];
  const unitCodes: string[] = [];

  for (const topic of topicGroups) {
    topicCodes.push(topic.topicCode);
    for (const chapter of topic.chapters) {
      chapterCodes.push(chapter.chapterCode);
      for (const entry of chapter.entries) {
        if (entry.kind === "unit-group" && !entry.inlineInChapter) {
          unitCodes.push(entry.unitCode);
        }
      }
    }
  }

  return { topicCodes, chapterCodes, unitCodes };
}

export type VisibleTreeRow =
  | {
      kind: "topic";
      nodeId: string;
      level: 1;
      parentNodeId: null;
      topicCode: string;
      title: string;
      itemCount: number;
      expandable: true;
      expanded: boolean;
      containsCurrent: boolean;
      treeIndex: number;
    }
  | {
      kind: "chapter";
      nodeId: string;
      level: 2;
      parentNodeId: string;
      topicCode: string;
      chapterCode: string;
      title: string;
      itemCount: number;
      expandable: true;
      expanded: boolean;
      containsCurrent: boolean;
      treeIndex: number;
    }
  | {
      kind: "unit";
      nodeId: string;
      level: 3;
      parentNodeId: string;
      topicCode: string;
      chapterCode: string;
      unitCode: string;
      shortCode: string;
      title: string;
      itemCount: number;
      expandable: true;
      expanded: boolean;
      containsCurrent: boolean;
      treeIndex: number;
    }
  | {
      kind: "leaf";
      nodeId: string;
      level: 3 | 4;
      parentNodeId: string;
      topicCode: string;
      chapterCode: string;
      item: PickerItem;
      label: string;
      shortCode: string;
      fullCode: string;
      drillType: DrillTypeIconKind;
      status: PickerStatus;
      hasNotes: boolean;
      isDueToday: boolean;
      isCurrent: boolean;
      expandable: false;
      expanded: false;
      treeIndex: number;
    };

/**
 * Flatten the visible curriculum tree (Topic -> Chapter -> [Unit] -> Leaf) in top-to-bottom
 * visual order with `level`, `expanded`, `status`, and parent references.
 */
export function buildVisibleTreeRows(options: {
  topicGroups: readonly PickerTopicGroup[];
  currentId: string;
  expandedTopics: ReadonlySet<string>;
  expandedChapters: ReadonlySet<string>;
  expandedUnits: ReadonlySet<string>;
  dueUnitCodes?: ReadonlySet<string>;
  currentHasNotesOverride?: boolean | null;
}): VisibleTreeRow[] {
  const {
    topicGroups,
    currentId,
    expandedTopics,
    expandedChapters,
    expandedUnits,
    dueUnitCodes,
    currentHasNotesOverride = null,
  } = options;

  const rows: VisibleTreeRow[] = [];

  const pushLeaf = (
    item: PickerItem,
    label: string,
    level: 3 | 4,
    parentNodeId: string,
    topicCode: string,
    chapterCode: string
  ) => {
    const isCurrent = item.id === currentId;
    const hasNotes =
      isCurrent && currentHasNotesOverride !== null
        ? item.hasNotes || currentHasNotesOverride
        : item.hasNotes;
    rows.push({
      kind: "leaf",
      nodeId: `leaf:${item.id}`,
      level,
      parentNodeId,
      topicCode,
      chapterCode,
      item,
      label,
      shortCode: extractShortCode(item),
      fullCode: formatFullRowCode(item),
      drillType: classifyPickerItemType(item),
      status: item.practiceStatus,
      hasNotes,
      isDueToday: Boolean(dueUnitCodes?.has(item.unitCode)),
      isCurrent,
      expandable: false,
      expanded: false,
      treeIndex: rows.length,
    });
  };

  for (const topic of topicGroups) {
    const topicNodeId = `topic:${topic.topicCode}`;
    const isTopicExpanded = expandedTopics.has(topic.topicCode);
    rows.push({
      kind: "topic",
      nodeId: topicNodeId,
      level: 1,
      parentNodeId: null,
      topicCode: topic.topicCode,
      title: topic.topicTitle,
      itemCount: topic.itemCount,
      expandable: true,
      expanded: isTopicExpanded,
      containsCurrent: topic.containsCurrent,
      treeIndex: rows.length,
    });

    if (!isTopicExpanded) continue;

    for (const chapter of topic.chapters) {
      const chapterNodeId = `chapter:${chapter.chapterCode}`;
      const isChapterExpanded = expandedChapters.has(chapter.chapterCode);
      rows.push({
        kind: "chapter",
        nodeId: chapterNodeId,
        level: 2,
        parentNodeId: topicNodeId,
        topicCode: topic.topicCode,
        chapterCode: chapter.chapterCode,
        title: chapter.chapterTitle,
        itemCount: chapter.itemCount,
        expandable: true,
        expanded: isChapterExpanded,
        containsCurrent: chapter.containsCurrent,
        treeIndex: rows.length,
      });

      if (!isChapterExpanded) continue;

      for (const entry of chapter.entries) {
        if (entry.kind === "single") {
          pushLeaf(
            entry.item,
            entry.item.title,
            3,
            chapterNodeId,
            topic.topicCode,
            chapter.chapterCode
          );
          continue;
        }

        if (entry.inlineInChapter) {
          for (const setEntry of entry.items) {
            pushLeaf(
              setEntry.item,
              setEntry.setLabel,
              3,
              chapterNodeId,
              topic.topicCode,
              chapter.chapterCode
            );
          }
          continue;
        }

        const unitNodeId = `unit:${entry.unitCode}`;
        const isUnitExpanded = expandedUnits.has(entry.unitCode);
        const unitShortCode = extractShortCode({
          kind: "drill",
          id: entry.unitCode,
          unitCode: entry.unitCode,
        });
        rows.push({
          kind: "unit",
          nodeId: unitNodeId,
          level: 3,
          parentNodeId: chapterNodeId,
          topicCode: topic.topicCode,
          chapterCode: chapter.chapterCode,
          unitCode: entry.unitCode,
          shortCode: unitShortCode,
          title: entry.unitTitle,
          itemCount: entry.items.length,
          expandable: true,
          expanded: isUnitExpanded,
          containsCurrent: entry.containsCurrent,
          treeIndex: rows.length,
        });

        if (!isUnitExpanded) continue;

        for (const setEntry of entry.items) {
          pushLeaf(
            setEntry.item,
            setEntry.setLabel,
            4,
            unitNodeId,
            topic.topicCode,
            chapter.chapterCode
          );
        }
      }
    }
  }

  return rows;
}

export type TreeNavKey = "ArrowDown" | "ArrowUp" | "ArrowRight" | "ArrowLeft" | "Enter";

export type TreeKeyAction =
  | { type: "focus"; nodeId: string }
  | { type: "expand"; nodeKind: "topic" | "chapter" | "unit"; code: string }
  | { type: "collapse"; nodeKind: "topic" | "chapter" | "unit"; code: string }
  | { type: "toggle"; nodeKind: "topic" | "chapter" | "unit"; code: string }
  | { type: "select"; itemId: string }
  | { type: "none" };

function branchCodeOf(
  row: Extract<VisibleTreeRow, { expandable: true }>
): string {
  if (row.kind === "topic") return row.topicCode;
  if (row.kind === "chapter") return row.chapterCode;
  return row.unitCode;
}

/** Resolve WAI-ARIA tree keyboard navigation (`ArrowUp/Down/Left/Right`, `Enter`) on flattened rows. */
export function resolveTreeKeyAction(
  rows: readonly VisibleTreeRow[],
  currentNodeId: string | null,
  key: TreeNavKey
): TreeKeyAction {
  if (rows.length === 0) return { type: "none" };
  const idx = currentNodeId ? rows.findIndex((r) => r.nodeId === currentNodeId) : -1;

  if (key === "ArrowDown") {
    const nextIdx = idx < 0 || idx >= rows.length - 1 ? 0 : idx + 1;
    return { type: "focus", nodeId: rows[nextIdx].nodeId };
  }

  if (key === "ArrowUp") {
    const prevIdx = idx <= 0 ? rows.length - 1 : idx - 1;
    return { type: "focus", nodeId: rows[prevIdx].nodeId };
  }

  if (idx < 0) return { type: "none" };
  const row = rows[idx];

  if (key === "ArrowRight") {
    if (!row.expandable) return { type: "none" };
    if (!row.expanded) {
      return { type: "expand", nodeKind: row.kind, code: branchCodeOf(row) };
    }
    const next = rows[idx + 1];
    if (next && next.parentNodeId === row.nodeId) {
      return { type: "focus", nodeId: next.nodeId };
    }
    return { type: "none" };
  }

  if (key === "ArrowLeft") {
    if (row.expandable && row.expanded) {
      return { type: "collapse", nodeKind: row.kind, code: branchCodeOf(row) };
    }
    if (row.parentNodeId) {
      return { type: "focus", nodeId: row.parentNodeId };
    }
    return { type: "none" };
  }

  // Enter
  if (row.kind === "leaf") {
    return { type: "select", itemId: row.item.id };
  }
  return { type: "toggle", nodeKind: row.kind, code: branchCodeOf(row) };
}

/** Find the first visible leaf nodeId (used to auto-target first search match on Enter). */
export function findFirstLeafNodeId(rows: readonly VisibleTreeRow[]): string | null {
  const found = rows.find((r) => r.kind === "leaf");
  return found ? found.nodeId : null;
}

/** Find the nodeId of `currentId` if it is currently visible in the tree. */
export function findCurrentLeafNodeId(
  rows: readonly VisibleTreeRow[],
  currentId: string
): string | null {
  const found = rows.find((r) => r.kind === "leaf" && r.item.id === currentId);
  return found ? found.nodeId : null;
}
