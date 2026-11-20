"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Workspace } from "@/lib/routes";
import { plainTitle } from "@/lib/titleText";
import { warningTone } from "@/lib/statusTone";
import type { DueTodayUnit, UnitMasteryContext, WeakSpotUnit } from "@/lib/dueToday";
import { FormattedText } from "@/components/FormattedText";

const FALLBACK_MINUTES_PER_ITEM = 1.5;

export interface StudioSidePanelProps {
  workspace: Workspace;
  currentUnitCode?: string | null;
  drillLoading?: boolean;
  dueReviewCount?: number;
  reviewSessionSize?: number;
  otherWorkspaceDueCount?: number;
  estimatedMinutes?: number;
  nextDueDate?: string | null;
  currentUnitMastery?: UnitMasteryContext | null;
  /** Optional unit schedule context; never rendered as a to-do list or counted in Due today. */
  dueUnits?: DueTodayUnit[];
  dueLoading?: boolean;
  dueError?: string | null;
  weakSpotUnits: WeakSpotUnit[];
  weakLoading?: boolean;
  weakError?: string | null;
  embedded?: boolean;
  onNavigate?: () => void;
}

function estimateFallbackMinutes(count: number): number {
  if (count <= 0) return 0;
  return Math.max(1, Math.round(count * FALLBACK_MINUTES_PER_ITEM));
}

function MasteryDots({ mastery }: { mastery: number }) {
  const level = Math.max(0, Math.min(4, Math.round(mastery)));
  return (
    <span
      className="inline-flex items-center gap-1 shrink-0"
      aria-label={`Mastery ${level} of 4`}
      title={`Mastery ${level} of 4`}
    >
      {[0, 1, 2, 3].map((dot) => (
        <span
          key={dot}
          aria-hidden="true"
          className={`w-1.5 h-1.5 rounded-full ${
            dot < level
              ? "bg-zinc-700 dark:bg-zinc-300"
              : "bg-zinc-200 dark:bg-zinc-700"
          }`}
        />
      ))}
    </span>
  );
}

/** Quiet side panel showing the workspace's item-level review queue and open weak spots for the current unit. */
export const StudioSidePanel: React.FC<StudioSidePanelProps> = ({
  workspace,
  currentUnitCode,
  drillLoading = false,
  dueReviewCount = 0,
  reviewSessionSize = 0,
  otherWorkspaceDueCount = 0,
  estimatedMinutes,
  nextDueDate = null,
  currentUnitMastery = null,
  dueUnits = [],
  dueLoading = false,
  dueError = null,
  weakSpotUnits,
  weakLoading = false,
  weakError = null,
  embedded = false,
  onNavigate,
}) => {
  const isPrg = workspace === "code";
  const workspaceSubject = isPrg ? "PRG" : "MTH";
  const otherSubject = isPrg ? "MTH" : "PRG";
  const workspaceReviewHref = `/review?scope=subject:${workspaceSubject}`;
  const otherReviewHref = `/review?scope=subject:${otherSubject}`;

  const resolvedMinutes =
    typeof estimatedMinutes === "number" && estimatedMinutes > 0
      ? estimatedMinutes
      : estimateFallbackMinutes(dueReviewCount);
  const sessionSize = Math.min(reviewSessionSize, dueReviewCount);
  const sessionMinutes = dueReviewCount > 0
    ? Math.max(1, Math.round((resolvedMinutes * sessionSize) / dueReviewCount))
    : 0;

  const unitContext: UnitMasteryContext | null =
    currentUnitMastery ??
    (currentUnitCode
      ? (() => {
          const match = dueUnits.find((u) => u.unitCode === currentUnitCode);
          if (!match) return null;
          return {
            unitCode: match.unitCode,
            title: match.title,
            mastery: match.mastery,
            masteryCap: match.masteryCap,
          };
        })()
      : null);

  const openSpots = weakSpotUnits.flatMap((u) =>
    u.open.map((spot) => ({
      ...spot,
      unitCode: u.unitCode,
      unitTitle: u.unitTitle,
    }))
  );
  const showUnitHeading = weakSpotUnits.length > 1;

  const weakSubtitle = isPrg ? "Checks and lint rules" : "Repeated traps";
  const isWeakSkeleton = drillLoading || (weakLoading && openSpots.length === 0);
  const weakEmptyText = !currentUnitCode
    ? "Open a drill to see unit weak spots."
    : isPrg
    ? "No open check or lint issues in this unit."
    : "No open traps for this unit yet.";

  return (
    <div
      className={
        embedded
          ? "min-w-0 max-w-full overflow-x-hidden divide-y divide-zinc-200 dark:divide-zinc-800"
          : "min-w-0 max-w-full overflow-x-hidden bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 divide-y divide-zinc-200 dark:divide-zinc-800"
      }
    >
      {/* Section 1: Due today (single item-level queue, split by workspace) */}
      <section aria-labelledby="side-panel-due-heading" className="pb-4 space-y-2.5 min-w-0">
        <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5 min-w-0">
          <h2
            id="side-panel-due-heading"
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            Due today
          </h2>
          {!dueLoading && dueReviewCount + otherWorkspaceDueCount > 0 && (
            <span className="font-display tabular-nums text-xs text-zinc-500 dark:text-zinc-400">
              {dueReviewCount + otherWorkspaceDueCount} total across workspaces
            </span>
          )}
        </div>

        {dueLoading && dueReviewCount === 0 ? (
          <div
            role="status"
            aria-label="Loading due reviews"
            className="space-y-2.5 animate-pulse"
          >
            <div className="h-3.5 w-32 bg-zinc-200 dark:bg-zinc-800 rounded" />
            <div className="h-10 w-full bg-zinc-200 dark:bg-zinc-800 rounded-xl" />
          </div>
        ) : dueError && dueReviewCount === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Could not load reviews.
          </p>
        ) : dueReviewCount > 0 ? (
          <div className="space-y-2.5 min-w-0">
            <p className="font-display tabular-nums text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed break-words">
              <span className="font-medium text-zinc-800 dark:text-zinc-200">
                {dueReviewCount} due · next {sessionSize} · ~{sessionMinutes} min
              </span>
            </p>

            {otherWorkspaceDueCount > 0 && (
              <Link
                href={otherReviewHref}
                onClick={onNavigate}
                className="flex w-full min-h-[36px] items-center rounded-lg px-2 text-xs text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors"
              >
                {otherWorkspaceDueCount} due in the other workspace
              </Link>
            )}

            <Link
              href={workspaceReviewHref}
              onClick={onNavigate}
              className="inline-flex w-full items-center justify-center gap-1.5 min-h-[40px] px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition-colors"
            >
              <span>Start review · {sessionSize} of {dueReviewCount}</span>
              <ChevronRight aria-hidden="true" className="w-3.5 h-3.5 shrink-0" />
            </Link>
          </div>
        ) : (
          <div className="space-y-1.5 min-w-0">
            <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
              Nothing due today — you&apos;re all caught up.
            </p>
            {nextDueDate && (
              <p className="font-display tabular-nums text-xs text-zinc-500 dark:text-zinc-400">
                Next due: {nextDueDate}
              </p>
            )}
            {otherWorkspaceDueCount > 0 && (
              <Link
                href={otherReviewHref}
                onClick={onNavigate}
                className="flex w-full min-h-[36px] items-center rounded-lg px-2 text-xs font-display tabular-nums text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors"
              >
                {otherWorkspaceDueCount} due in the other workspace
              </Link>
            )}
          </div>
        )}
      </section>

      {/* Section 2: Current unit context & weak spots */}
      <section aria-labelledby="side-panel-weak-heading" className="pt-4 space-y-2.5 min-w-0">
        <div className="flex flex-wrap items-baseline justify-between gap-x-2 gap-y-0.5 min-w-0">
          <h2
            id="side-panel-weak-heading"
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            Weak spots
          </h2>
          <span className="text-xs text-zinc-500 dark:text-zinc-400 min-w-0">
            {weakSubtitle}
          </span>
        </div>

        {!drillLoading && unitContext && (
          <div className="space-y-1 min-w-0 pb-1">
            <div className="flex items-center justify-between gap-2 min-w-0">
              <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300 leading-snug truncate min-w-0">
                {plainTitle(unitContext.title)}
              </span>
              <MasteryDots mastery={unitContext.mastery} />
            </div>
            {unitContext.masteryCap?.capped && unitContext.masteryCap.reason && (
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 leading-snug break-words">
                Capped at {unitContext.mastery} · {unitContext.masteryCap.reason}
              </p>
            )}
          </div>
        )}

        {isWeakSkeleton ? (
          <div
            role="status"
            aria-label="Loading unit weak spots"
            className="space-y-2 animate-pulse"
          >
            <div className="h-3.5 w-3/4 bg-zinc-200 dark:bg-zinc-800 rounded" />
            <div className="h-3 w-full bg-zinc-100 dark:bg-zinc-800/70 rounded" />
            <div className="h-3.5 w-2/3 bg-zinc-200 dark:bg-zinc-800 rounded" />
          </div>
        ) : weakError ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Could not load weak spots.
          </p>
        ) : openSpots.length === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            {weakEmptyText}
          </p>
        ) : (
          <ul className="space-y-2.5 min-w-0">
            {openSpots.map((spot) => (
              <li
                key={`${spot.unitCode}:${spot.id}`}
                className={`min-w-0 max-w-full ${warningTone.leftBorderSoft} pl-2.5 py-0.5 space-y-0.5`}
              >
                <div className="flex items-baseline justify-between gap-2 min-w-0">
                  <span
                    className={`text-xs font-medium text-zinc-800 dark:text-zinc-200 break-words [overflow-wrap:anywhere] min-w-0 ${
                      spot.name ? "" : "font-display"
                    }`}
                    title={spot.name ? spot.id : undefined}
                  >
                    {spot.name ?? spot.id}
                  </span>
                  <span className="text-[11px] font-display tabular-nums text-zinc-500 dark:text-zinc-400 shrink-0">
                    {spot.matches}x
                  </span>
                </div>
                {spot.detail && (
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-snug break-words [overflow-wrap:anywhere]">
                    <FormattedText text={spot.detail} />
                  </p>
                )}
                {showUnitHeading && spot.unitTitle && (
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400 truncate">
                    {plainTitle(spot.unitTitle)}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
};
