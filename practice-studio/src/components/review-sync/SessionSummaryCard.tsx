"use client";

import React from "react";
import { ArrowDown, ArrowLeft, ArrowRight } from "lucide-react";
import type { DrillDocument, Problem } from "@/types/drill";
import {
  classifyReviewOutcome,
  formatDuration,
  getQuestionLabel,
  getReviewOutcomeMeta,
  type GroupedReviewSummary,
  type ReviewOutcome,
} from "@/lib/reviewOutcome";
import { countRightItems, type SessionPattern } from "@/lib/reviewRow";
import { scoreProblem } from "@/lib/scoring";
import { formatSyncTimestamp } from "@/lib/sessionSummary";
import { statusTone, warningTone } from "@/lib/statusTone";
import { Button } from "@/components/ui/shadcn/Button";
import { plainTitle } from "@/lib/titleText";

export type EffectiveSyncPhase =
  | "idle"
  | "syncing"
  | "synced"
  | "changed"
  | "degraded"
  | "error"
  | "offline"
  | "dryRun";

export interface SessionSummaryCardProps {
  drill: DrillDocument;
  groups: GroupedReviewSummary<Problem>;
  durationMs: number;
  pattern: SessionPattern | null;
  effectiveSyncPhase: EffectiveSyncPhase;
  syncedAt?: string | null;
  isLab: boolean;
  isCode: boolean;
  hasAnyAttempt: boolean;
  onJumpToRow: (probId: string, inCorrectGroup: boolean) => void;
  onScrollToSync: () => void;
  onBackToQuiz: () => void;
  onStartFirst: () => void;
}

const TILE_COLORS: Record<ReviewOutcome, string> = {
  correct_first: statusTone.correct.tile,
  assisted_or_partial: statusTone.assisted.tile,
  wrong: statusTone.wrong.tile,
  skipped: statusTone.skipped.tile,
  awaiting_review:
    "bg-zinc-50 hover:bg-zinc-100 dark:bg-zinc-950 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border-zinc-400 dark:border-zinc-500",
  unanswered: statusTone.notTried.tile,
};

function syncStatusLinkText(
  phase: EffectiveSyncPhase,
  syncedAt: string | null | undefined,
  isLab: boolean
): { label: string; showArrow: boolean; toneClass: string } {
  if (isLab) {
    return {
      label: "Submit from terminal",
      showArrow: true,
      toneClass: "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100",
    };
  }
  switch (phase) {
    case "syncing":
      return {
        label: "Syncing…",
        showArrow: false,
        toneClass: "text-zinc-500 dark:text-zinc-400",
      };
    case "synced": {
      const { relativeLabel } = formatSyncTimestamp(syncedAt);
      return {
        label: relativeLabel ? `Synced ${relativeLabel}` : "Synced",
        showArrow: false,
        toneClass: `${statusTone.correct.text} hover:opacity-80`,
      };
    }
    case "changed":
      return {
        label: "Changed since sync",
        showArrow: true,
        toneClass: warningTone.textLink,
      };
    case "degraded":
      return {
        label: "Saved locally · retry",
        showArrow: true,
        toneClass: warningTone.textLink,
      };
    case "error":
    case "offline":
      return {
        label: phase === "offline" ? "Offline · retry" : "Couldn't sync",
        showArrow: true,
        toneClass: `${statusTone.wrong.text} hover:opacity-80`,
      };
    case "dryRun":
      return {
        label: "Not written (dry run)",
        showArrow: true,
        toneClass: "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100",
      };
    default:
      return {
        label: "Not synced yet",
        showArrow: true,
        toneClass: "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100",
      };
  }
}

/** Section A: Session summary card with verdict sentence, labelled outcome strip, pattern line, and sync status link. */
export const SessionSummaryCard: React.FC<SessionSummaryCardProps> = ({
  drill,
  groups,
  durationMs,
  pattern,
  effectiveSyncPhase,
  syncedAt,
  isLab,
  isCode,
  hasAnyAttempt,
  onJumpToRow,
  onScrollToSync,
  onBackToQuiz,
  onStartFirst,
}) => {
  const drillTitle = plainTitle(drill.unitTitle) || drill.unitCode;
  const totalCount = drill.problems.length;
  const rightCount = countRightItems(drill.problems);
  const points = drill.problems.reduce(
    (sum, problem) => sum + (scoreProblem(problem.state, { isPrg: isCode || isLab }).score ?? 0),
    0
  );
  const firstTryCount = groups.firstTryCount;
  const allFirstTry = totalCount > 0 && firstTryCount === totalCount;
  const formattedTime = durationMs > 0 ? formatDuration(durationMs) : null;
  const statusLink = syncStatusLinkText(effectiveSyncPhase, syncedAt, isLab);

  const firstLabel =
    totalCount > 0 ? getQuestionLabel(drill.problems[0].id, 0, isLab) : isLab ? "M1" : "Q1";
  const backLabel = isLab
    ? "Back to milestones"
    : isCode
    ? "Back to problems"
    : "Back to questions";
  const outcomeGroupLabel = isLab
    ? "Milestone outcomes"
    : isCode
    ? "Problem outcomes"
    : "Question outcomes";

  return (
    <section
      aria-labelledby="review-sync-heading"
      className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-4"
    >
      {/* Top row: h1 title + right-aligned quiet sync status link */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
        <div className="min-w-0 space-y-0.5">
          <h1
            id="review-sync-heading"
            className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight break-words"
          >
            {drillTitle}
          </h1>
          <p className="font-display text-xs text-zinc-500 dark:text-zinc-400">
            {drill.unitCode}
          </p>
        </div>

        <Button
          variant="ghost"
          size="compact"
          onClick={onScrollToSync}
          className={`self-start sm:self-auto inline-flex items-center gap-1 min-h-[44px] sm:min-h-[32px] text-xs transition-colors rounded-md py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 shrink-0 ${statusLink.toneClass}`}
        >
          <span className="font-display tabular-nums">{statusLink.label}</span>
          {statusLink.showArrow && <ArrowDown className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />}
        </Button>
      </div>

      {/* Verdict sentence (text-base, numbers/time in font-display) */}
      <p className="text-base text-zinc-800 dark:text-zinc-200 leading-relaxed">
        {!hasAnyAttempt ? (
          <>
            <span>Nothing answered yet</span>
            {formattedTime && (
              <>
                <span className="mx-1.5 text-zinc-400 dark:text-zinc-500">·</span>
                <span className="font-display tabular-nums text-zinc-600 dark:text-zinc-300">
                  {formattedTime}
                </span>
              </>
            )}
          </>
        ) : allFirstTry ? (
          <>
            <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
              {points} / {totalCount}
            </span>
            <span> points · All {totalCount} right on the first try</span>
            {formattedTime && (
              <>
                <span className="mx-1.5 text-zinc-400 dark:text-zinc-500">·</span>
                <span className="font-display tabular-nums text-zinc-600 dark:text-zinc-300">
                  {formattedTime}
                </span>
              </>
            )}
          </>
        ) : (
          <>
            <span className="font-display font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">
              {points} / {totalCount}
            </span>
            <span> points · {rightCount} of {totalCount} right</span>
            {firstTryCount > 0 && (
              <>
                <span className="mx-1.5 text-zinc-400 dark:text-zinc-500">·</span>
                <span className="font-display tabular-nums text-zinc-900 dark:text-zinc-100">
                  {firstTryCount}
                </span>
                <span> on the first try</span>
              </>
            )}
            {formattedTime && (
              <>
                <span className="mx-1.5 text-zinc-400 dark:text-zinc-500">·</span>
                <span className="font-display tabular-nums text-zinc-600 dark:text-zinc-300">
                  {formattedTime}
                </span>
              </>
            )}
          </>
        )}
      </p>

      {/* Labelled outcome strip (no legend — tooltips + aria-labels + rows carry the meaning) */}
      {totalCount > 0 && (
        <div
          role="group"
          aria-label={outcomeGroupLabel}
          className="flex flex-wrap items-center gap-1.5"
        >
          {drill.problems.map((prob, idx) => {
            const outcome = classifyReviewOutcome(prob.state);
            const meta = getReviewOutcomeMeta(outcome);
            const qLabel = getQuestionLabel(prob.id, idx, isLab);
            const tooltip = `${qLabel} · ${meta.label.toLowerCase()}`;
            return (
              <button
                key={prob.id}
                type="button"
                onClick={() => onJumpToRow(prob.id, outcome === "correct_first")}
                title={tooltip}
                aria-label={tooltip}
                className={`min-w-[44px] sm:min-w-[36px] min-h-[44px] sm:min-h-[32px] px-2 rounded-lg border font-display text-xs font-semibold tabular-nums inline-flex items-center justify-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${TILE_COLORS[outcome]}`}
              >
                {qLabel}
              </button>
            );
          })}
        </div>
      )}

      {/* Pattern line — only when a trap or mistake tag repeats >= 2 times */}
      {pattern && (
        <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-snug">
          <span>
            {pattern.kind === "trap" ? "Same trap " : "Same mistake "}
            {pattern.count === 2 ? (
              "twice"
            ) : (
              <span className="font-display tabular-nums">{pattern.count}×</span>
            )}
            :{" "}
          </span>
          <span className="font-semibold text-zinc-900 dark:text-zinc-100">
            {pattern.label}
          </span>{" "}
          <span className="font-display text-xs text-zinc-500 dark:text-zinc-400">
            ({pattern.itemLabels.join(", ")})
          </span>
        </p>
      )}

      {/* Footer row: Start Q1 primary when nothing attempted (drills), plus quiet Back link */}
      <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-800/80 flex flex-wrap items-center justify-between gap-3">
        <Button
          variant="ghost"
          size="compact"
          onClick={onBackToQuiz}
          className="inline-flex items-center gap-1.5 min-h-[44px] sm:min-h-[32px] px-1 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
        >
          <ArrowLeft className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>{backLabel}</span>
        </Button>

        {!hasAnyAttempt && totalCount > 0 && (
          <Button
            variant={isLab ? "outline" : "primary"}
            size="compact"
            onClick={onStartFirst}
            className={
              isLab
                ? "inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-[36px] px-3.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-700 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
                : "inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:min-h-[36px] px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
            }
          >
            <span>Start {firstLabel}</span>
            <ArrowRight className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          </Button>
        )}
      </div>
    </section>
  );
};
