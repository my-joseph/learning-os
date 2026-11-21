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
    syncState?.isPilot ||
    syncState?.phase === "syncing" ||
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
