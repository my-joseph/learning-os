"use client";

import React, { useEffect, useId, useState } from "react";
import dynamic from "next/dynamic";
import { LoaderCircle } from "lucide-react";
import { Heading } from "@/components/ui/Heading";
import { Numeral } from "@/components/ui/Numeral";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
import type { PracticeStatusOverride } from "@/hooks/types";
import { INITIAL_SYNC_STATE, type SyncState } from "@/hooks/useProgressSync";
import type { ReviewScheduleEntry } from "@/lib/dueToday";
import { buildSyncPreview, getCoveredUnits } from "@/lib/sessionSummary";
import { isSyncedUpToDate, syncFailureLabel } from "@/lib/syncStatus";
import { statusTone, warningTone } from "@/lib/statusTone";
import type { DrillDocument } from "@/types/drill";
import { countReviewSyncOutcomes, outcomeLabels, type OutcomeCounts } from "./reviewSyncOutcomes";

function DonutPlaceholder({ loading = false }: { loading?: boolean }) {
  return (
    <div
      aria-hidden="true"
      className={`absolute inset-space-1 rounded-full bg-status-neutral after:absolute after:inset-space-6 after:rounded-full after:bg-surface-raised ${loading ? "animate-pulse motion-reduce:animate-none" : ""}`}
    />
  );
}

const DonutChart = dynamic(
  () => import("./DonutChart").then((mod) => mod.DonutChart),
  { ssr: false, loading: () => <DonutPlaceholder loading /> }
);

const reviewDateFormatter = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  day: "numeric",
  month: "short",
  timeZone: "UTC",
});

function formatSchedule(
  coveredUnits: ReturnType<typeof buildSyncPreview>["coveredUnits"],
  unitReviews: SyncState["unitReviews"],
): string {
  const units = coveredUnits.map((unit) => unitReviews?.[unit.unitCode] ?? unit);
  const earliest = units
    .filter((unit) => unit.nextReview && /^\d{4}-\d{2}-\d{2}$/.test(unit.nextReview) && !Number.isNaN(Date.parse(unit.nextReview)))
    .sort((a, b) => (a.nextReview ?? "").localeCompare(b.nextReview ?? ""))[0];
  const mastery = earliest?.mastery ?? (units.length === 1 ? units[0].mastery : null);
  const label = units.length > 1 ? "Earliest review" : "Next review";
  const date = earliest?.nextReview
    ? `${label} ${reviewDateFormatter.format(new Date(earliest.nextReview))}`
    : null;

  return [mastery === null ? null : `Unit mastery ${mastery}`, date]
    .filter(Boolean)
    .join(" · ") || "Progress synced to Notion";
}

export interface ReviewSyncPageProps {
  currentDrill: DrillDocument;
  statusOverride: PracticeStatusOverride;
  isSyncing: boolean;
  syncState?: SyncState;
  scheduleCache?: Record<string, ReviewScheduleEntry>;
  onBackToQuiz: () => void;
  onConfirmSync: () => void;
}

export function ReviewSyncPage({
  currentDrill,
  statusOverride,
  isSyncing,
  syncState = INITIAL_SYNC_STATE,
  scheduleCache,
  onBackToQuiz,
  onConfirmSync,
}: ReviewSyncPageProps) {
  const headingId = useId();
  const [schedule, setSchedule] = useState<Record<string, ReviewScheduleEntry>>({});
  const coveredUnitKey = getCoveredUnits(currentDrill).join(",");
  const syncedAt = syncState.at || currentDrill.sessionSummary?.syncedToNotionAt;
  const preview = buildSyncPreview(currentDrill, statusOverride, scheduleCache ?? schedule);
  const { accuracyPct, maxScore } = preview.summary;
  const syncing = isSyncing || syncState.phase === "syncing";
  const synced = isSyncedUpToDate(currentDrill, preview.summary, syncState, syncing);

  useEffect(() => {
    if (scheduleCache !== undefined || !synced || !coveredUnitKey) return;
    const controller = new AbortController();
    fetch(`/api/review-schedule?units=${encodeURIComponent(coveredUnitKey)}`, {
      cache: "no-store",
      signal: controller.signal,
    })
      .then((response) => response.ok ? response.json() : null)
      .then((data: { units?: Record<string, ReviewScheduleEntry> } | null) => {
        if (data?.units && !controller.signal.aborted) setSchedule(data.units);
      })
      .catch(() => {}); // The local cache may be unavailable after a successful sync.
    return () => controller.abort();
  }, [coveredUnitKey, scheduleCache, synced, syncedAt]);

  const counts = countReviewSyncOutcomes(currentDrill);
  const outcomes = (Object.keys(outcomeLabels) as (keyof OutcomeCounts)[])
    .map((key) => ({ label: outcomeLabels[key], count: counts[key] }));
  const headline = accuracyPct >= 80 ? "Great work!" : accuracyPct >= 50 ? "Good progress" : "Keep practising";
  const failedSteps = syncState.failedSteps ?? currentDrill.notionSyncProblems ?? [];
  const partial = syncState.phase === "partial"
    || syncState.phase === "degraded"
    || (syncState.phase === "idle" && failedSteps.length > 0);
  const error = syncState.phase === "error" || syncState.phase === "offline";
  const canRetry = partial || error;

  let next = "Sync to update mastery and schedule";
  let nextTone = "text-foreground-secondary";
  let failureDetails: string | undefined;
  if (syncing) {
    next = "Updating mastery and review schedule…";
  } else if (error) {
    next = syncState.phase === "offline"
      ? "You’re offline. Your progress is saved locally."
      : "Couldn’t sync. Try again.";
    nextTone = statusTone.wrong.text;
  } else if (partial) {
    next = "Synced with problems. Retry to finish.";
    nextTone = warningTone.text;
    failureDetails = failedSteps.map(syncFailureLabel).join(" · ");
  } else if (syncState.phase === "dryRun") {
    next = syncState.isPilot ? "Pilot sync saved locally" : "Dry run saved locally";
  } else if (synced) {
    next = formatSchedule(preview.coveredUnits, syncState.unitReviews);
  } else if (!preview.hasAnyAttempt) {
    next = "Complete or skip an item to sync";
  }

  return (
    <Card asChild className="mx-auto max-w-md border-border bg-surface-raised px-space-5 py-space-8 text-center shadow-none dark:border-border dark:bg-surface-raised sm:px-space-8 sm:py-space-10">
      <section aria-labelledby={headingId}>
        <div
          role="img"
          aria-label={`Score ${accuracyPct}%. ${outcomes.map(({ label, count }) => `${label} ${count}`).join(", ")}.`}
          className="relative mx-auto size-space-52"
        >
          {maxScore > 0 ? <DonutChart counts={counts} /> : <DonutPlaceholder />}
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-space-0_5">
            <Numeral variant="lg" className="text-4xl">{accuracyPct}%</Numeral>
            <span className="text-sm text-foreground-secondary">score</span>
          </div>
        </div>

        <table className="sr-only">
          <caption>Drill outcomes</caption>
          <tbody>
            {outcomes.map(({ label, count }) => (
              <tr key={label}><th scope="row">{label}</th><td>{count}</td></tr>
            ))}
          </tbody>
        </table>

        <Heading id={headingId} variant="section" className="mt-space-5">{headline}</Heading>
        <p className="mt-space-2 font-semibold text-sm">
          {[
            `${counts.correct} of ${maxScore} correct`,
            counts.assisted > 0 && `${counts.assisted} with help`,
            counts.wrong > 0 && `${counts.wrong} wrong`,
            counts.unattempted > 0 && `${counts.unattempted} skipped / not tried`,
          ].filter(Boolean).join(" · ")}
        </p>
        <div role="status" className={`mt-space-1 h-space-12 overflow-y-auto text-sm ${nextTone}`}>
          <p>{next}</p>
          {failureDetails && <p className="text-xs">{failureDetails}</p>}
        </div>
        <div className="mx-auto mt-space-2 grid max-w-xs grid-cols-2 gap-space-3">
          <Button variant="resultOutline" size={null} className="h-touch text-sm font-semibold" onClick={onBackToQuiz}>
            Back
          </Button>
          <Button
            variant="resultPrimary"
            size={null}
            className={`h-touch text-sm ${synced ? `${statusTone.correct.solidBadge} disabled:opacity-100` : ""}`}
            disabled={syncing || synced || (!preview.hasAnyAttempt && !canRetry)}
            onClick={onConfirmSync}
          >
            {syncing && <LoaderCircle aria-hidden="true" className="size-space-4 animate-spin motion-reduce:animate-none" />}
            {syncing ? "Syncing…" : synced ? "Synced" : canRetry ? "Retry" : "Sync"}
          </Button>
        </div>
      </section>
    </Card>
  );
}
