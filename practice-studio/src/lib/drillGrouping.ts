import type { DrillDocument, DrillListItem } from "@/types/drill";
import { workspaceOfListItem, type Workspace } from "./routes";

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

export interface GenerateUnitOption {
  unitCode: string;
  unitTitle: string;
  groupCode: string;
}

export interface GenerateUnitGroup {
  groupCode: string;
  items: GenerateUnitOption[];
}

function unitWorkspace(unitCode: string, subject?: string): Workspace | null {
  const code = unitCode.trim().toUpperCase();
  if (subject === "PRG" || code.startsWith("PRG-")) return "code";
  if (subject === "MATH" || code.startsWith("MTH-") || code.startsWith("PHY-")) {
    return "math";
  }
  return null;
}

function topicGroupOf(unitCode: string): string {
  const parts = unitCode.trim().split("-");
  if (parts.length >= 2) return `${parts[0]}-${parts[1]}`;
  return parts[0] || "Other";
}

/**
 * Build sorted unit options for the Generate drill panel dynamically from served drills,
 * filtered to the active workspace, always ensuring `currentDrill.unitCode` is included.
 */
export function buildGenerateUnitOptions(
  drills: readonly DrillListItem[],
  workspace: Workspace,
  currentDrill?: Pick<DrillDocument, "unitCode" | "unitTitle" | "subject"> | null
): GenerateUnitOption[] {
  const byCode = new Map<string, string>();

  for (const d of drills) {
    const code = (d.unitCode || "").trim();
    if (!code) continue;
    const ws = workspaceOfListItem(d) ?? unitWorkspace(code, d.subject);
    if (ws !== workspace) continue;
    const title = (d.unitTitle || "").trim();
    const prev = byCode.get(code);
    if (!prev || (prev === code && title && title !== code)) {
      byCode.set(code, title || code);
    }
  }

  const currentCode = currentDrill?.unitCode?.trim() || "";
  if (currentCode) {
    const currentWs = unitWorkspace(currentCode, currentDrill?.subject);
    if (currentWs === null || currentWs === workspace) {
      const currentTitle = (currentDrill?.unitTitle || "").trim();
      const prev = byCode.get(currentCode);
      if (!prev || (prev === currentCode && currentTitle && currentTitle !== currentCode)) {
        byCode.set(currentCode, currentTitle || currentCode);
      }
    }
  }

  return Array.from(byCode.entries())
    .map(([unitCode, unitTitle]) => ({
      unitCode,
      unitTitle,
      groupCode: topicGroupOf(unitCode),
    }))
    .sort((a, b) => a.unitCode.localeCompare(b.unitCode));
}

/** Group sorted unit options by topic prefix (e.g. MTH-T01, MTH-T02, PRG-T01). */
export function groupGenerateUnitOptions(
  options: readonly GenerateUnitOption[]
): GenerateUnitGroup[] {
  const groups = new Map<string, GenerateUnitOption[]>();
  for (const opt of options) {
    const list = groups.get(opt.groupCode);
    if (list) list.push(opt);
    else groups.set(opt.groupCode, [opt]);
  }
  return Array.from(groups.entries()).map(([groupCode, items]) => ({
    groupCode,
    items,
  }));
}
