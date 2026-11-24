"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { DrillDocument, SessionSummary } from "@/types/drill";
import { plainTitle } from "@/lib/titleText";
import { isLabId } from "@/lib/routes";
import { createSaveQueue, type SaveQueue } from "@/lib/saveQueue";
import {
  buildSyncPayload,
  computeSessionMetrics,
  summaryFingerprint,
  type SessionMetrics,
} from "@/lib/sessionSummary";
import { PracticeStatusOverride, StatusMessage } from "./types";

export { computeSessionMetrics, type SessionMetrics };

export type SyncPhase =
  | "idle"
  | "syncing"
  | "synced"
  | "degraded"
  | "error"
  | "offline"
  | "dryRun";

export interface UnitReviewResult {
  mastery: number;
  lastReviewed: string;
  nextReview: string;
  masteryCap?: { capped: boolean; reason: string } | null;
}

export interface SyncState {
  phase: SyncPhase;
  at?: string | null;
  unitReviews?: Record<string, UnitReviewResult>;
  drillPageId?: string | null;
  message?: string | null;
  isPilot?: boolean;
}

export const INITIAL_SYNC_STATE: SyncState = { phase: "idle" };

/** Client-side ceiling slightly above the server's 90s subprocess timeout so `/api/sync-notion` can never hang in `syncing`. */
export const DEFAULT_SYNC_TIMEOUT_MS = 100_000;

interface UseProgressSyncOptions {
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
}

interface ConfirmSyncCallbacks {
  getLatestDrill?: () => DrillDocument | null;
  onDrillUpdated: (doc: DrillDocument) => void;
  onSynced: (drillId: string) => Promise<void>;
}

/**
 * Merge a Notion sync stamp (`sessionSummary`) into the latest in-memory drill document.
 * Returns null if the learner has switched to a different drill, preserving any edits
 * made while the sync was in flight.
 */
export function mergeSyncStampIntoLatestDrill(
  latestDrill: DrillDocument | null,
  syncedDrillId: string,
  stampedSummary: SessionSummary
): DrillDocument | null {
  if (!latestDrill || latestDrill.drillId !== syncedDrillId) {
    return null;
  }
  return {
    ...latestDrill,
    sessionSummary: stampedSummary,
  };
}

export interface SyncResponseLike {
  ok?: boolean;
  dryRun?: boolean;
  pilotSkipped?: boolean;
  degraded?: boolean;
  timedOut?: boolean;
  warning?: string;
  error?: string;
  drillPageId?: string | null;
  parentPageId?: string | null;
  syncedToNotionAt?: string | null;
  notionPageId?: string | null;
  syncedFingerprint?: string | null;
  unitReviews?: Record<string, UnitReviewResult>;
}

/** Build the status toast message after a Notion sync response (handling dry-run and pilot mode). */
export function formatSyncToast(
  data: SyncResponseLike,
  drillTitle: string,
  unitCode: string,
  liveScore: number,
  maxScore: number,
  accuracyPct: number
): StatusMessage {
  if (data.dryRun || data.pilotSkipped) {
    return {
      text: `Dry run — nothing written to Notion (${liveScore}/${maxScore} · ${accuracyPct}% saved locally).`,
      type: "warn",
    };
  }
  const cleanTitle = plainTitle(drillTitle) || unitCode;
  if (data.degraded) {
    // Saved locally, but Notion was unreachable (or no token): do not report it as synced.
    return {
      text: `Saved ${cleanTitle} locally, but Notion was not updated: ${data.warning || "Notion unavailable"}`,
      type: "warn",
    };
  }
  return {
    text: `Synced ${cleanTitle} (${liveScore}/${maxScore} · ${accuracyPct}%) to Notion Database & ${unitCode} Mistake Log!`,
    type: "pass",
  };
}

export interface ExecuteNotionSyncResult {
  syncState: SyncState;
  toast: StatusMessage | null;
  stampedDoc: DrillDocument | null;
  stampedSummary?: SessionSummary | null;
  postedPayload: DrillDocument | null;
  ignored?: boolean;
}

/**
 * Pure async coordinator for syncing a drill to `/api/sync-notion` and adopting
 * server-persisted `syncedToNotionAt`, `notionPageId`, and `syncedFingerprint`
 * ONLY on a real non-degraded, non-dry-run, non-pilot success.
 */
export async function executeNotionSync(options: {
  currentDrill: DrillDocument;
  statusOverride: PracticeStatusOverride;
  fetchFn?: typeof fetch;
  getLatestDrill?: () => DrillDocument | null;
  isOffline?: boolean;
  nowIso?: string;
  attemptDate?: string;
  timeoutMs?: number;
}): Promise<ExecuteNotionSyncResult> {
  const {
    currentDrill,
    statusOverride,
    fetchFn = fetch,
    getLatestDrill,
    isOffline = typeof navigator !== "undefined" && navigator.onLine === false,
    nowIso = new Date().toISOString(),
    attemptDate,
    timeoutMs = DEFAULT_SYNC_TIMEOUT_MS,
  } = options;

  // Hard guard: labs are submitted via `labs/common/submit_lab.py` (`npm run submit`), never drill sync.
  if (isLabId(currentDrill.drillId)) {
    return {
      syncState: {
        phase: "error",
        message: "Labs must be submitted from the terminal with `npm run submit`.",
      },
      toast: {
        text: "Labs must be submitted from the terminal with `npm run submit`.",
        type: "warn",
      },
      stampedDoc: null,
      postedPayload: null,
    };
  }

  if (isOffline) {
    return {
      syncState: {
        phase: "offline",
        message: "You're offline.",
      },
      toast: {
        text: "You're offline. Your progress is saved locally.",
        type: "fail",
      },
      stampedDoc: null,
      postedPayload: null,
    };
  }

  const fullDocToSync = buildSyncPayload(currentDrill, statusOverride, {
    attemptDate,
  });
  const { score: liveScore, maxScore, accuracyPct } = fullDocToSync.sessionSummary;
  const drillLabel =
    plainTitle(currentDrill.unitTitle) || currentDrill.unitCode || currentDrill.drillId;

  const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
  let timedOut = false;
  let timeoutHandle: ReturnType<typeof setTimeout> | null = null;

  let res: Response;
  try {
    const fetchPromise = fetchFn("/api/sync-notion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fullDocToSync),
      ...(controller ? { signal: controller.signal } : {}),
    });

    if (typeof timeoutMs === "number" && Number.isFinite(timeoutMs) && timeoutMs > 0) {
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutHandle = setTimeout(() => {
          timeoutHandle = null;
          timedOut = true;
          controller?.abort();
          const label =
            timeoutMs >= 1_000 ? `${Math.round(timeoutMs / 1_000)}s` : `${timeoutMs}ms`;
          reject(new Error(`Notion sync timed out after ${label}.`));
        }, timeoutMs);
      });
      // Prevent unhandled rejection if fetch rejects after timeout wins the race.
      fetchPromise.catch(() => {});
      res = await Promise.race([fetchPromise, timeoutPromise]);
    } else {
      res = await fetchPromise;
    }
  } catch (err: unknown) {
    if (timedOut) {
      const errMsg = err instanceof Error ? err.message : "Notion sync timed out.";
      return {
        syncState: {
          phase: "error",
          message: errMsg,
        },
        toast: {
          text: `${errMsg} Your progress is saved locally — retry when ready.`,
          type: "fail",
        },
        stampedDoc: null,
        postedPayload: fullDocToSync,
      };
    }
    const isNetworkTypeError = err instanceof TypeError;
    const errMsg = err instanceof Error ? err.message : String(err);
    return {
      syncState: {
        phase: isNetworkTypeError ? "offline" : "error",
        message: isNetworkTypeError ? "You're offline." : errMsg,
      },
      toast: {
        text: isNetworkTypeError
          ? "You're offline. Your progress is saved locally."
          : `Notion Sync error: ${errMsg}`,
        type: "fail",
      },
      stampedDoc: null,
      postedPayload: fullDocToSync,
    };
  } finally {
    if (timeoutHandle !== null) {
      clearTimeout(timeoutHandle);
      timeoutHandle = null;
    }
  }

  let data: SyncResponseLike;
  try {
    data = (await res.json()) as SyncResponseLike;
  } catch {
    return {
      syncState: {
        phase: "error",
        message: `Sync failed (HTTP ${res.status}).`,
      },
      toast: {
        text: `Notion Sync error: HTTP ${res.status}`,
        type: "fail",
      },
      stampedDoc: null,
      postedPayload: fullDocToSync,
    };
  }

  if (!res.ok || !data.ok) {
    const errMsg = data.error || `Notion Sync failed (HTTP ${res.status})`;
    return {
      syncState: {
        phase: "error",
        message: errMsg,
      },
      toast: {
        text: `Notion Sync error: ${errMsg}`,
        type: "fail",
      },
      stampedDoc: null,
      postedPayload: fullDocToSync,
    };
  }

  const toast = formatSyncToast(
    data,
    drillLabel,
    currentDrill.unitCode,
    liveScore,
    maxScore,
    accuracyPct
  );

  // Pilot mode or dry run: NEVER adopt or stamp syncedToNotionAt or syncedFingerprint.
  if (data.dryRun || data.pilotSkipped) {
    const isPilot = Boolean(data.pilotSkipped);
    return {
      syncState: {
        phase: "dryRun",
        isPilot,
        message: isPilot
          ? "Pilot mode: nothing was written to Notion."
          : "Dry run: nothing was written to Notion.",
      },
      toast,
      stampedDoc: null,
      postedPayload: fullDocToSync,
    };
  }

  // Degraded (saved locally, Notion unreachable): NEVER adopt or stamp syncedToNotionAt or syncedFingerprint.
  if (data.degraded) {
    return {
      syncState: {
        phase: "degraded",
        message: data.warning || "Notion unavailable.",
      },
      toast,
      stampedDoc: null,
      postedPayload: fullDocToSync,
    };
  }

  // Real successful Notion sync: adopt server-persisted stamps into the LATEST in-memory drill doc.
  const syncedAt =
    typeof data.syncedToNotionAt === "string" && data.syncedToNotionAt.trim()
      ? data.syncedToNotionAt.trim()
      : nowIso;

  const drillPageId =
    (typeof data.notionPageId === "string" && data.notionPageId.trim()) ||
    (typeof data.drillPageId === "string" && data.drillPageId.trim()) ||
    currentDrill.sessionSummary?.notionPageId ||
    null;

  const syncedFingerprint =
    typeof data.syncedFingerprint === "string" && data.syncedFingerprint.trim()
      ? data.syncedFingerprint.trim()
      : summaryFingerprint(fullDocToSync.sessionSummary);

  const stampedSummary: SessionSummary = {
    ...fullDocToSync.sessionSummary,
    syncedToNotionAt: syncedAt,
    notionPageId: drillPageId,
    syncedFingerprint,
  };

  const unitReviews =
    data.unitReviews && typeof data.unitReviews === "object"
      ? data.unitReviews
      : undefined;

  const latestTarget = getLatestDrill
    ? mergeSyncStampIntoLatestDrill(getLatestDrill(), currentDrill.drillId, stampedSummary)
    : {
        ...fullDocToSync,
        sessionSummary: stampedSummary,
      };

  // Learner switched to a different drill while the sync was in flight: ignore UI update
  // (the server already persisted the sync stamps on disk).
  if (!latestTarget) {
    return {
      syncState: {
        phase: "synced",
        at: syncedAt,
        unitReviews,
        drillPageId,
      },
      toast,
      stampedDoc: null,
      stampedSummary: null,
      postedPayload: fullDocToSync,
      ignored: true,
    };
  }

  return {
    syncState: {
      phase: "synced",
      at: syncedAt,
      unitReviews,
      drillPageId,
    },
    toast,
    stampedDoc: latestTarget,
    stampedSummary,
    postedPayload: fullDocToSync,
  };
}

/** Manage ordered local progress autosave and Notion sync payloads. */
export function useProgressSync({ setStatus }: UseProgressSyncOptions) {
  const [statusOverride, setStatusOverride] = useState<PracticeStatusOverride>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncState, setSyncState] = useState<SyncState>(INITIAL_SYNC_STATE);
  const saveQueueRef = useRef<SaveQueue | null>(null);
  const syncingRef = useRef(false);
  const syncGenRef = useRef(0);

  const getSaveQueue = useCallback((): SaveQueue => {
    if (!saveQueueRef.current) {
      saveQueueRef.current = createSaveQueue();
    }
    return saveQueueRef.current;
  }, []);

  useEffect(() => {
    return () => {
      saveQueueRef.current?.dispose();
    };
  }, []);

  const resetSyncState = useCallback(() => {
    syncGenRef.current += 1;
    syncingRef.current = false;
    setIsSyncing(false);
    setSyncState(INITIAL_SYNC_STATE);
  }, []);

  const flushAutoSave = useCallback(async () => {
    await getSaveQueue().flush();
  }, [getSaveQueue]);

  const saveNow = useCallback(
    (doc?: DrillDocument) => getSaveQueue().saveNow(doc),
    [getSaveQueue]
  );

  const triggerAutoSave = useCallback(
    (updatedDoc: DrillDocument) => {
      getSaveQueue().enqueue(updatedDoc);
    },
    [getSaveQueue]
  );

  const confirmSyncToNotion = useCallback(
    async (
      currentDrill: DrillDocument | null,
      { getLatestDrill, onDrillUpdated, onSynced }: ConfirmSyncCallbacks
    ) => {
      if (syncingRef.current || !currentDrill || isLabId(currentDrill.drillId)) return;

      const syncedDrillId = currentDrill.drillId;
      const syncGen = syncGenRef.current;
      const { liveScore, maxScore } = computeSessionMetrics(currentDrill, statusOverride);
      const drillLabel =
        plainTitle(currentDrill.unitTitle) || currentDrill.unitCode || currentDrill.drillId;

      syncingRef.current = true;
      setIsSyncing(true);
      setSyncState({ phase: "syncing" });
      setStatus({
        text: `Syncing ${drillLabel} (${liveScore}/${maxScore}) to Notion...`,
        type: "warn",
      });

      try {
        const docToSync = getLatestDrill?.() ?? currentDrill;
        const saved = await saveNow(docToSync);
        if (
          syncGenRef.current !== syncGen ||
          (getLatestDrill && getLatestDrill()?.drillId !== syncedDrillId)
        ) {
          if (syncGenRef.current === syncGen) {
            setSyncState(INITIAL_SYNC_STATE);
          }
          return;
        }
        if (!saved) {
          throw new Error("Progress could not be saved. Try syncing again.");
        }
        const result = await executeNotionSync({
          currentDrill: docToSync,
          statusOverride,
          getLatestDrill,
        });

        // Ignore the result if the learner switched drills while the sync ran.
        if (
          result.ignored ||
          syncGenRef.current !== syncGen ||
          (getLatestDrill && getLatestDrill()?.drillId !== syncedDrillId)
        ) {
          if (syncGenRef.current === syncGen) {
            setSyncState(INITIAL_SYNC_STATE);
          }
          return;
        }

        setSyncState(result.syncState);
        if (result.toast) {
          setStatus(result.toast);
        }
        if (result.stampedDoc) {
          onDrillUpdated(result.stampedDoc);
        }
        if (
          result.stampedDoc ||
          result.syncState.phase === "degraded" ||
          result.syncState.phase === "dryRun"
        ) {
          try {
            await onSynced(syncedDrillId);
          } catch {
            // Non-fatal: drill list refresh failure must not revert sync state.
          }
        }
      } catch (err: unknown) {
        if (syncGenRef.current === syncGen) {
          const errMsg = err instanceof Error ? err.message : String(err);
          setSyncState({
            phase: "error",
            message: errMsg || "Notion sync failed.",
          });
          setStatus({
            text: `Notion Sync error: ${errMsg || "Notion sync failed."}`,
            type: "fail",
          });
        }
      } finally {
        if (syncGenRef.current === syncGen) {
          syncingRef.current = false;
          setIsSyncing(false);
        }
      }
    },
    [saveNow, setStatus, statusOverride]
  );

  return {
    statusOverride,
    setStatusOverride,
    isSyncing,
    syncState,
    resetSyncState,
    triggerAutoSave,
    saveNow,
    flushAutoSave,
    confirmSyncToNotion,
  };
}
