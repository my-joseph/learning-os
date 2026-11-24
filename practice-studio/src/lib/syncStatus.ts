import type { DrillDocument, SessionSummary } from "@/types/drill";
import type { SyncState } from "@/hooks/useProgressSync";
import { summaryFingerprint } from "@/lib/sessionSummary";

/** Whether the current drill summary still matches a successful real Notion sync. */
export function isSyncedUpToDate(
  drill: DrillDocument,
  currentSummary: Partial<SessionSummary> | null | undefined,
  syncState?: SyncState,
  isSyncing = false
): boolean {
  if (
    isSyncing ||
    Boolean(drill.notionSyncProblems?.length) ||
    syncState?.isPilot ||
    syncState?.phase === "syncing" ||
    syncState?.phase === "partial" ||
    syncState?.phase === "degraded" ||
    syncState?.phase === "error" ||
    syncState?.phase === "offline" ||
    syncState?.phase === "dryRun"
  ) {
    return false;
  }

  const persistedSummary = drill.sessionSummary;
  const syncedAt =
    syncState?.phase === "synced"
      ? syncState.at || persistedSummary?.syncedToNotionAt
      : persistedSummary?.syncedToNotionAt;
  if (!syncedAt) return false;

  const savedFingerprint = persistedSummary?.syncedFingerprint ||
    summaryFingerprint(persistedSummary);
  return !savedFingerprint || summaryFingerprint(currentSummary) === savedFingerprint;
}

export function syncFailureLabel(step: string): string {
  if (step.startsWith("unitReview:")) {
    return `Unit review (${step.slice("unitReview:".length)})`;
  }
  switch (step) {
    case "pageContent": return "Drill page content";
    case "blockCleanup": return "Removal of outdated drill page blocks";
    case "mistakeLog": return "Mistake Log";
    default: return "Notion update";
  }
}
