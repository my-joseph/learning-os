"use client";

import { Numeral } from "@/components/ui/Numeral";
import React, { useId, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Workspace } from "@/lib/routes";
import { plainTitle } from "@/lib/titleText";
import { mistakePracticeHref, type RecentMistake } from "@/lib/mistakePractice";
import type { DueTodayUnit, UnitMasteryContext } from "@/lib/dueToday";
import { ListRow } from "@/components/ui/ListRow";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { FormattedText } from "@/components/FormattedText";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";

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
  mistakes?: RecentMistake[];
  showMistakes?: boolean;
  mistakesLoading?: boolean;
  mistakesError?: boolean;
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
      className="inline-flex items-center gap-space-1 shrink-0"
      aria-label={`Mastery ${level} of 4`}
      title={`Mastery ${level} of 4`}
    >
      {[0, 1, 2, 3].map((dot) => (
        <span
          key={dot}
          aria-hidden="true"
          className={`size-space-1_5 rounded-full ${
            dot < level
              ? "bg-foreground-control"
              : "bg-border-control"
          }`}
        />
      ))}
    </span>
  );
}

/** Quiet side panel showing the workspace's item-level review queue and recent mistakes for the current workspace. */
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
  mistakes = [],
  showMistakes = false,
  mistakesLoading = false,
  mistakesError = false,
  embedded = false,
  onNavigate,
}) => {
  const [mistakesExpanded, setMistakesExpanded] = useState(true);
  const mistakesId = useId();
  const mistakesOpen = showMistakes && !drillLoading && mistakesExpanded;
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

  const content = (
    <>
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
            <span className="font-sans tabular-nums text-xs text-zinc-500 dark:text-zinc-400">
              {dueReviewCount + otherWorkspaceDueCount} total across workspaces
            </span>
          )}
        </div>

        {dueLoading && dueReviewCount === 0 ? (
          <div
            role="status"
            aria-label="Loading due reviews"
            className="space-y-2.5"
          >
            <Skeleton className="h-3.5 w-32 rounded" />
            <Skeleton className="h-10 w-full rounded-xl" />
          </div>
        ) : dueError && dueReviewCount === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Could not load reviews.
          </p>
        ) : dueReviewCount > 0 ? (
          <div className="space-y-2.5 min-w-0">
            <p className="font-sans tabular-nums text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed break-words">
              <Numeral variant="lg" className="leading-none text-foreground">{dueReviewCount}</Numeral>
              {" "}due · next {sessionSize} · ~{sessionMinutes} min
            </p>

            {otherWorkspaceDueCount > 0 && (
              <Link
                href={otherReviewHref}
                onClick={onNavigate}
                className="flex w-full min-h-[36px] items-center rounded-lg px-2 text-xs tabular-nums text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors"
              >
                {otherWorkspaceDueCount} due in the other workspace
              </Link>
            )}

            <Button
              asChild
              variant="primary"
              size="compact"
              className="w-full rounded-xl px-3.5 text-xs"
            >
              <Link href={workspaceReviewHref} onClick={onNavigate}>
                <Numeral>Start review · {sessionSize} of {dueReviewCount}</Numeral>
                <ChevronRight aria-hidden="true" className="w-3.5 h-3.5 shrink-0" />
              </Link>
            </Button>
          </div>
        ) : (
          <div className="space-y-1.5 min-w-0">
            <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
              Nothing due today — you&apos;re all caught up.
            </p>
            {nextDueDate && (
              <p className="font-sans tabular-nums text-xs text-zinc-500 dark:text-zinc-400">
                Next due: {nextDueDate}
              </p>
            )}
            {otherWorkspaceDueCount > 0 && (
              <Link
                href={otherReviewHref}
                onClick={onNavigate}
                className="flex w-full min-h-[36px] items-center rounded-lg px-2 text-xs font-sans tabular-nums text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 transition-colors"
              >
                {otherWorkspaceDueCount} due in the other workspace
              </Link>
            )}
          </div>
        )}
      </section>

      <section aria-labelledby={`${mistakesId}-heading`} className="min-w-0 pt-space-4">
        <h2 id={`${mistakesId}-heading`}>
          <SectionHeader
            expanded={mistakesOpen}
            controls={mistakesId}
            disabled={!showMistakes || drillLoading}
            onClick={() => setMistakesExpanded((expanded) => !expanded)}
            className="min-h-touch text-sm font-semibold text-foreground disabled:text-foreground-secondary lg:min-h-control-sm"
          >
            What I get wrong
          </SectionHeader>
        </h2>

        <div id={mistakesId} hidden={!mistakesOpen}>
          {mistakesOpen && (
            <div className="min-w-0 space-y-space-2">
              {unitContext && (
                <div className="min-w-0 space-y-space-1 px-space-1_5">
                  <div className="flex min-w-0 items-center justify-between gap-space-2">
                    <span className="min-w-0 truncate text-xs text-foreground-secondary">
                      <FormattedText text={plainTitle(unitContext.title)} />
                    </span>
                    <MasteryDots mastery={unitContext.mastery} />
                  </div>
                  {unitContext.masteryCap?.capped && unitContext.masteryCap.reason && (
                    <p className="break-words text-xs text-foreground-secondary">
                      Capped at <Numeral variant="sm" className="leading-none">{unitContext.mastery}</Numeral>
                      {" "}· <FormattedText text={unitContext.masteryCap.reason} />
                    </p>
                  )}
                </div>
              )}

              {mistakesLoading ? (
                <div role="status" aria-label="Loading recent mistakes" className="flex h-control-md items-center px-space-1_5">
                  <Skeleton className="h-space-3 w-full rounded-md" />
                </div>
              ) : mistakesError ? (
                <p role="status" className="px-space-1_5 text-xs text-foreground-secondary">
                  Could not load recent mistakes.
                </p>
              ) : mistakes.length === 0 ? (
                <p className="px-space-1_5 text-xs text-foreground-secondary">
                  Nothing you keep getting wrong in this unit yet.
                </p>
              ) : (
                <ul className="divide-y divide-border">
                  {mistakes.map((mistake) => (
                    <ListRow key={mistake.key} asChild variant="summary" size="md">
                      <li>
                        <div className="min-w-0 space-y-space-0_5 [overflow-wrap:anywhere]">
                          <p className="text-foreground">
                            <FormattedText text={mistake.name} />
                          </p>
                          {mistake.fixed ? (
                            <p className="text-status-correct-text">Fixed</p>
                          ) : (
                            <p className="tabular-nums text-foreground-secondary">
                              Missed {mistake.recentMisses} of last {mistake.recentTries}
                            </p>
                          )}
                        </div>
                        <Button asChild variant="resultLink" size="resultLink" className="shrink-0 lg:min-h-control-xs">
                          <Link href={mistakePracticeHref(mistake.key)} prefetch={false} onClick={onNavigate}>
                            Practise<span className="sr-only"> <FormattedText text={mistake.name} /></span>
                          </Link>
                        </Button>
                      </li>
                    </ListRow>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </section>
    </>
  );

  if (embedded) {
    return (
      <div className="min-w-0 max-w-full overflow-x-hidden divide-y divide-border">
        {content}
      </div>
    );
  }

  return (
    <Card className="max-w-full overflow-x-hidden shadow-none p-4 divide-y divide-border">
      {content}
    </Card>
  );
};
