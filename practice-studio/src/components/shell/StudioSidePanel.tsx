"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Workspace } from "@/lib/routes";
import type { DueTodayUnit, WeakSpotUnit } from "@/lib/dueToday";
import { FormattedText } from "@/components/FormattedText";

export interface StudioSidePanelProps {
  workspace: Workspace;
  currentUnitCode?: string | null;
  dueUnits: DueTodayUnit[];
  dueLoading?: boolean;
  dueError?: string | null;
  weakSpotUnits: WeakSpotUnit[];
  weakLoading?: boolean;
  weakError?: string | null;
  onNavigate?: () => void;
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

/** Quiet side panel showing spaced-review units due today and open weak spots for the current unit. */
export const StudioSidePanel: React.FC<StudioSidePanelProps> = ({
  workspace,
  currentUnitCode,
  dueUnits,
  dueLoading = false,
  dueError = null,
  weakSpotUnits,
  weakLoading = false,
  weakError = null,
  onNavigate,
}) => {
  const isPrg = workspace === "code";
  const openSpots = weakSpotUnits.flatMap((u) =>
    u.open.map((spot) => ({
      ...spot,
      unitCode: u.unitCode,
      unitTitle: u.unitTitle,
    }))
  );
  const showUnitHeading = weakSpotUnits.length > 1;

  const weakSubtitle = isPrg ? "Checks and lint rules" : "Repeated traps";
  const weakEmptyText = !currentUnitCode
    ? "Open a drill to see unit weak spots."
    : isPrg
    ? "No open check or lint issues in this unit."
    : "No open traps for this unit yet.";

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 divide-y divide-zinc-200 dark:divide-zinc-800">
      {/* Section 1: Due today */}
      <section aria-labelledby="side-panel-due-heading" className="pb-4 space-y-2.5">
        <div className="flex items-baseline justify-between gap-2">
          <h2
            id="side-panel-due-heading"
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            Due today
          </h2>
          {dueUnits.length > 0 && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400 tabular-nums">
              {dueUnits.length}
            </span>
          )}
        </div>

        {dueLoading && dueUnits.length === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Checking schedule…
          </p>
        ) : dueError ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Could not load due units.
          </p>
        ) : dueUnits.length === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            Nothing due today — you&apos;re all caught up.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {dueUnits.map((unit) => {
              const inner = (
                <>
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="text-xs font-medium text-zinc-800 dark:text-zinc-200 leading-snug line-clamp-2">
                      {unit.title}
                    </div>
                    <div className="flex items-center gap-2">
                      <MasteryDots mastery={unit.mastery} />
                      {!unit.href && (
                        <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
                          No drill yet
                        </span>
                      )}
                    </div>
                  </div>
                  {unit.href && (
                    <ChevronRight
                      aria-hidden="true"
                      className="w-3.5 h-3.5 text-zinc-400 dark:text-zinc-500 group-hover:text-zinc-700 dark:group-hover:text-zinc-200 shrink-0 transition-colors"
                    />
                  )}
                </>
              );

              return (
                <li key={unit.unitCode}>
                  {unit.href ? (
                    <Link
                      href={unit.href}
                      onClick={onNavigate}
                      className="group flex items-center justify-between gap-2 rounded-xl px-2.5 py-2 -mx-2.5 hover:bg-zinc-50 dark:hover:bg-zinc-800/70 transition-colors"
                    >
                      {inner}
                    </Link>
                  ) : (
                    <div className="flex items-center justify-between gap-2 rounded-xl px-2.5 py-2 -mx-2.5">
                      {inner}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {/* Section 2: Weak spots */}
      <section aria-labelledby="side-panel-weak-heading" className="pt-4 space-y-2.5">
        <div className="flex items-baseline justify-between gap-2">
          <h2
            id="side-panel-weak-heading"
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            Weak spots
          </h2>
          <span className="text-xs text-zinc-500 dark:text-zinc-400">
            {weakSubtitle}
          </span>
        </div>

        {weakLoading && openSpots.length === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Scanning unit progress…
          </p>
        ) : weakError ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Could not load weak spots.
          </p>
        ) : openSpots.length === 0 ? (
          <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
            {weakEmptyText}
          </p>
        ) : (
          <ul className="space-y-2.5">
            {openSpots.map((spot) => (
              <li
                key={`${spot.unitCode}:${spot.id}`}
                className="border-l-2 border-amber-600/70 dark:border-amber-400/70 pl-2.5 py-0.5 space-y-0.5"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span
                    className={`text-xs font-medium text-zinc-800 dark:text-zinc-200 break-words min-w-0 ${
                      isPrg || spot.subject === "PRG" ? "font-mono" : ""
                    }`}
                  >
                    {spot.id}
                  </span>
                  <span className="text-[11px] text-zinc-500 dark:text-zinc-400 tabular-nums shrink-0">
                    {spot.matches}x
                  </span>
                </div>
                {spot.detail && (
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-snug">
                    <FormattedText text={spot.detail} />
                  </p>
                )}
                {showUnitHeading && spot.unitTitle && (
                  <p className="text-[11px] text-zinc-400 dark:text-zinc-500 truncate">
                    {spot.unitTitle}
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
