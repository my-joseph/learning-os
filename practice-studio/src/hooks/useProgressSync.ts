"use client";

import { useState, useRef, useCallback } from "react";
import { DrillDocument } from "@/types/drill";
import { plainTitle } from "@/lib/titleText";
import { PracticeStatusOverride, StatusMessage } from "./types";

export interface SessionMetrics {
  liveScore: number;
  maxScore: number;
  accuracyPct: number;
  skippedCount: number;
  computedPracticeStatus: "Graded" | "Needs Retry";
}

/** Compute live score, accuracy, skipped count, and target practice status for a drill. */
export function computeSessionMetrics(
  currentDrill: DrillDocument | null,
  statusOverride: PracticeStatusOverride
): SessionMetrics {
  const liveScore = currentDrill
    ? currentDrill.problems.reduce((acc, p) => acc + (p.state?.score || 0), 0)
    : 0;
  const maxScore = currentDrill?.problems.length || 0;
  const accuracyPct = maxScore > 0 ? Math.round((liveScore / maxScore) * 1000) / 10 : 0;
  const skippedCount = currentDrill
    ? currentDrill.problems.filter((p) => p.state?.skipped).length
    : 0;

  const computedPracticeStatus: "Graded" | "Needs Retry" =
    statusOverride || (maxScore > 0 && liveScore / maxScore >= 0.8 ? "Graded" : "Needs Retry");

  return {
    liveScore,
    maxScore,
    accuracyPct,
    skippedCount,
    computedPracticeStatus,
  };
}

interface UseProgressSyncOptions {
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
}

interface ConfirmSyncCallbacks {
  onDrillUpdated: (doc: DrillDocument) => void;
  onSynced: (drillId: string) => Promise<void>;
}

export interface SyncResponseLike {
  ok?: boolean;
  dryRun?: boolean;
  pilotSkipped?: boolean;
  degraded?: boolean;
  warning?: string;
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

/** Manage debounced local progress autosave and Notion sync payloads. */
export function useProgressSync({ setStatus }: UseProgressSyncOptions) {
  const [statusOverride, setStatusOverride] = useState<PracticeStatusOverride>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const saveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pendingDocRef = useRef<DrillDocument | null>(null);

  const flushAutoSave = useCallback(async () => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    const doc = pendingDocRef.current;
    if (!doc) return;
    pendingDocRef.current = null;
    try {
      await fetch("/api/save-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(doc),
      });
    } catch {
      // silent fail on transient autosave
    }
  }, []);

  const triggerAutoSave = useCallback((updatedDoc: DrillDocument) => {
    pendingDocRef.current = updatedDoc;
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(async () => {
      saveTimerRef.current = null;
      const docToSave = pendingDocRef.current;
      pendingDocRef.current = null;
      if (!docToSave) return;
      try {
        await fetch("/api/save-state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(docToSave),
        });
      } catch {
        // silent fail on transient autosave
      }
    }, 400);
  }, []);

  const confirmSyncToNotion = useCallback(
    async (
      currentDrill: DrillDocument | null,
      { onDrillUpdated, onSynced }: ConfirmSyncCallbacks
    ) => {
      if (!currentDrill) return;
      const { liveScore, maxScore, accuracyPct, computedPracticeStatus } = computeSessionMetrics(
        currentDrill,
        statusOverride
      );

      const drillLabel =
        plainTitle(currentDrill.unitTitle) || currentDrill.unitCode || currentDrill.drillId;
      setIsSyncing(true);
      setStatus({
        text: `Syncing ${drillLabel} (${liveScore}/${maxScore}) to Notion...`,
        type: "warn",
      });

      const tagMap = new Map((currentDrill.mistakeTags || []).map((t) => [t.id, t.name]));
      const mistakeNames = new Set<string>();
      const divergedList: string[] = [];
      const skippedProblems: string[] = [];

      currentDrill.problems.forEach((p) => {
        const parts: string[] = [];
        if (p.state?.skipped) {
          skippedProblems.push(`${p.id} (${p.context || p.category})`);
          parts.push("SKIPPED - Concept Gap");
        }
        (p.state?.mistakes || []).forEach((tid) => {
          const rawName = tagMap.get(tid) || tid;
          mistakeNames.add(rawName.replace(/,/g, " /").trim());
        });
        if (typeof p.state?.divergedStep === "number") {
          const st = p.steps?.[p.state.divergedStep];
          parts.push(`Step ${p.state.divergedStep + 1}: ${st ? st.explain : "Diverged"}`);
        } else if (
          p.state?.score !== null &&
          p.state?.score !== undefined &&
          p.state.score < 1 &&
          (p.state?.mistakes || []).length > 0 &&
          !p.state?.skipped
        ) {
          parts.push((p.state?.mistakes || []).map((t) => tagMap.get(t) || t).join(", "));
        }
        if (p.state?.mistakeNote && p.state.mistakeNote.trim()) {
          parts.push(`Note: ${p.state.mistakeNote.trim()}`);
        }
        if (parts.length > 0) {
          divergedList.push(`${p.id} (${parts.join(" · ")})`);
        }
      });

      const fullDocToSync: DrillDocument = {
        ...currentDrill,
        sessionSummary: {
          practiceStatus: computedPracticeStatus,
          score: liveScore,
          maxScore,
          accuracyPct,
          skippedCount: skippedProblems.length,
          skippedProblems,
          mistakeCategories: Array.from(mistakeNames),
          divergedStepsSummary:
            divergedList.length > 0 ? divergedList.join(" | ") : "No diverged steps logged.",
          attemptDate: new Date().toISOString().slice(0, 10),
        },
      };

      try {
        const res = await fetch("/api/sync-notion", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(fullDocToSync),
        });

        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.error || "Notion Sync failed");

        onDrillUpdated(fullDocToSync);
        setStatus(
          formatSyncToast(
            data,
            drillLabel,
            currentDrill.unitCode,
            liveScore,
            maxScore,
            accuracyPct
          )
        );
        await onSynced(currentDrill.drillId);
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `Notion Sync error: ${errMsg}`, type: "fail" });
      } finally {
        setIsSyncing(false);
      }
    },
    [setStatus, statusOverride]
  );

  return {
    statusOverride,
    setStatusOverride,
    isSyncing,
    triggerAutoSave,
    flushAutoSave,
    confirmSyncToNotion,
  };
}
