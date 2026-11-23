"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Plus } from "lucide-react";
import type {
  NextDrillSuggestion,
  ProblemJumpTarget,
  WeakSpotSuggestion,
} from "@/lib/reviewRow";
import { trapName } from "@/lib/titleText";
import { Button } from "@/components/ui/shadcn/Button";

export interface NextActionsProps {
  dueReviewCount: number;
  topWeakSpot: WeakSpotSuggestion | null;
  firstWrong: ProblemJumpTarget | null;
  nextDrill: NextDrillSuggestion | null;
  l4Challenge?: ProblemJumpTarget | null;
  allCorrect?: boolean;
  isCapped?: boolean;
  manyWrong?: boolean;
  primary: boolean;
  onOpenItem?: (index: number) => void;
  onSelectDrill?: (drillId: string) => void;
  onGenerate?: () => void;
}

interface ActionDescriptor {
  key: string;
  label: React.ReactNode;
  href?: string;
  onClick?: () => void;
  icon?: "plus" | "arrow";
}

const PRIMARY_CLS =
  "w-full sm:w-auto inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:h-9 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

const GHOST_CLS =
  "w-full sm:w-auto inline-flex items-center justify-center gap-1.5 min-h-[44px] sm:h-9 px-3.5 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 text-zinc-800 dark:text-zinc-200 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

/** Section E: "What next" actions. Ghost before sync; first action becomes primary after a successful sync. */
export const NextActions: React.FC<NextActionsProps> = ({
  dueReviewCount,
  topWeakSpot,
  firstWrong,
  nextDrill,
  l4Challenge = null,
  allCorrect = false,
  isCapped = false,
  manyWrong = false,
  primary,
  onOpenItem,
  onSelectDrill,
  onGenerate,
}) => {
  const dailyReviewAction: ActionDescriptor | null =
    dueReviewCount > 0
      ? {
          key: "daily-review",
          label: (
            <>
              <span>Daily review · </span>
              <span className="font-display tabular-nums">{dueReviewCount}</span>
              <span> due</span>
            </>
          ),
          href: "/review",
          icon: "arrow",
        }
      : null;

  const weakSpotAction: ActionDescriptor | null = topWeakSpot
    ? {
        key: `weak-spot-${topWeakSpot.id}`,
        label: <span>Practise {topWeakSpot.label || trapName(topWeakSpot.id)}</span>,
        href: `/review?trap=${encodeURIComponent(topWeakSpot.id)}`,
      }
    : firstWrong && onOpenItem
    ? {
        key: `retry-${firstWrong.problemId}`,
        label: (
          <>
            <span>Retry </span>
            <span className="font-display">{firstWrong.label}</span>
          </>
        ),
        onClick: () => onOpenItem(firstWrong.index),
      }
    : null;

  const l4Action: ActionDescriptor | null =
    l4Challenge && onOpenItem
      ? {
          key: `l4-${l4Challenge.problemId}`,
          label: <span>Try an L4 challenge</span>,
          onClick: () => onOpenItem(l4Challenge.index),
          icon: "arrow",
        }
      : null;

  const nextOrGenerateAction: ActionDescriptor | null = nextDrill
    ? {
        key: `next-${nextDrill.drillId}`,
        label: <span className="truncate max-w-[240px]">Next drill: {nextDrill.title}</span>,
        href: onSelectDrill ? undefined : nextDrill.href,
        onClick: onSelectDrill ? () => onSelectDrill(nextDrill.drillId) : undefined,
        icon: "arrow",
      }
    : onGenerate
    ? {
        key: "generate-drill",
        label: <span>Generate a drill</span>,
        onClick: onGenerate,
        icon: "plus",
      }
    : null;

  const actions: ActionDescriptor[] = [];
  if (allCorrect && !isCapped) {
    if (l4Action) actions.push(l4Action);
    if (dailyReviewAction) actions.push(dailyReviewAction);
    if (nextOrGenerateAction) actions.push(nextOrGenerateAction);
  } else if (manyWrong) {
    if (weakSpotAction) actions.push(weakSpotAction);
    if (dailyReviewAction) actions.push(dailyReviewAction);
    if (nextOrGenerateAction) actions.push(nextOrGenerateAction);
  } else {
    if (dailyReviewAction) actions.push(dailyReviewAction);
    if (weakSpotAction) actions.push(weakSpotAction);
    if (nextOrGenerateAction) actions.push(nextOrGenerateAction);
  }

  if (actions.length === 0) return null;

  return (
    <section
      aria-labelledby="what-next-heading"
      className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-3"
    >
      <h2
        id="what-next-heading"
        className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
      >
        What next
      </h2>

      <div className="flex flex-col sm:flex-row sm:flex-wrap items-stretch sm:items-center gap-2">
        {actions.map((action, idx) => {
          const isPrimary = primary && idx === 0;
          const cls = isPrimary ? PRIMARY_CLS : GHOST_CLS;
          const iconEl =
            action.icon === "plus" ? (
              <Plus className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            ) : action.icon === "arrow" ? (
              <ArrowRight className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
            ) : null;

          if (action.href) {
            return (
              <Button
                key={action.key}
                asChild
                variant={isPrimary ? "primary" : "outline"}
                size="compact"
                className={cls}
              >
                <Link href={action.href}>
                  {action.icon === "plus" && iconEl}
                  {action.label}
                  {action.icon === "arrow" && iconEl}
                </Link>
              </Button>
            );
          }

          return (
            <Button
              variant={isPrimary ? "primary" : "outline"}
              size="compact"
              key={action.key}
              type="button"
              onClick={action.onClick}
              className={cls}
            >
              {action.icon === "plus" && iconEl}
              {action.label}
              {action.icon === "arrow" && iconEl}
            </Button>
          );
        })}
      </div>
    </section>
  );
};
