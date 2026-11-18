import type { DrillListItem } from "@/types/drill";

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

    const sorted = [...list].sort((a, b) => {
      const aNum = extractDrillSetNumber(a.drillId);
      const bNum = extractDrillSetNumber(b.drillId);
      if (aNum !== null && bNum !== null && aNum !== bNum) {
        return aNum - bNum;
      }
      if (aNum !== null && bNum === null) return -1;
      if (aNum === null && bNum !== null) return 1;
      return a.drillId.localeCompare(b.drillId);
    });

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
