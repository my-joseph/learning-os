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
      const entries = buildChapterEntries(chapter.items, chapter.chapterCode);
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
  chapterCode: string
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

  return {
    isSearching,
    currentItem,
    continueItems,
    topicGroups,
    defaultExpandedTopics,
    defaultExpandedChapters,
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
