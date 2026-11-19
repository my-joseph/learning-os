import type { Workspace } from "./routes";

const LAST_DRILL_STORAGE_KEY = "practice_studio_last_drill";
const LAST_WORKSPACE_DRILL_STORAGE_PREFIX = "practice_studio_last_drill_";
const RECENT_DRILLS_STORAGE_PREFIX = "practice_studio_recent_drills_";
const MAX_RECENT_DRILLS = 10;

/** Prepend `drillId` to an MRU list, deduplicating and capping at `limit`. */
export function updateRecentDrillIds(
  existing: readonly string[],
  drillId: string,
  limit: number = MAX_RECENT_DRILLS
): string[] {
  const trimmed = drillId.trim();
  if (!trimmed) return [...existing].slice(0, limit);
  return [trimmed, ...existing.filter((id) => id.trim() && id !== trimmed)].slice(0, limit);
}

/** Read the last opened drill ID (overall or per-workspace) safely from localStorage. */
export function readLastDrillId(workspace?: Workspace): string | null {
  if (typeof window === "undefined") return null;
  try {
    const key = workspace
      ? `${LAST_WORKSPACE_DRILL_STORAGE_PREFIX}${workspace}`
      : LAST_DRILL_STORAGE_KEY;
    const value = window.localStorage.getItem(key);
    return value && value.trim() ? value.trim() : null;
  } catch {
    return null;
  }
}

/** Read the MRU list of recently opened drill/lab IDs for a workspace from localStorage. */
function readRecentDrillIds(workspace: Workspace): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(`${RECENT_DRILLS_STORAGE_PREFIX}${workspace}`);
    if (!raw) {
      const last = readLastDrillId(workspace);
      return last ? [last] : [];
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  } catch {
    return [];
  }
}

/** Persist the last opened drill ID (overall, per-workspace, and MRU history) safely to localStorage. */
export function writeLastDrillId(drillId: string, workspace: Workspace): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LAST_DRILL_STORAGE_KEY, drillId);
    window.localStorage.setItem(`${LAST_WORKSPACE_DRILL_STORAGE_PREFIX}${workspace}`, drillId);
    const updated = updateRecentDrillIds(readRecentDrillIds(workspace), drillId);
    window.localStorage.setItem(
      `${RECENT_DRILLS_STORAGE_PREFIX}${workspace}`,
      JSON.stringify(updated)
    );
  } catch {
    // ignore storage access/quota failures
  }
}
