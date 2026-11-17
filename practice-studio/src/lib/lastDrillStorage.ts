import type { Workspace } from "./routes";

export const LAST_DRILL_STORAGE_KEY = "practice_studio_last_drill";
export const LAST_WORKSPACE_DRILL_STORAGE_PREFIX = "practice_studio_last_drill_";

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

/** Persist the last opened drill ID (overall and per-workspace) safely to localStorage. */
export function writeLastDrillId(drillId: string, workspace: Workspace): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LAST_DRILL_STORAGE_KEY, drillId);
    window.localStorage.setItem(`${LAST_WORKSPACE_DRILL_STORAGE_PREFIX}${workspace}`, drillId);
  } catch {
    // ignore storage access/quota failures
  }
}
