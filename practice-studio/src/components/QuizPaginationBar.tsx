"use client";

import React, { useEffect, useRef } from "react";
import { ClipboardCheck } from "lucide-react";
import { Problem } from "@/types/drill";
import { Workspace } from "@/lib/routes";
import { LabMilestoneStepper } from "@/components/LabMilestoneStepper";

interface QuizPaginationBarProps {
  currentIndex: number;
  problems: Problem[];
  viewMode: "quiz" | "review";
  workspace?: Workspace;
  isLab?: boolean;
  onSelectQuestion: (index: number) => void;
  onToggleViewMode: (mode: "quiz" | "review") => void;
}

const TILE_BASE_CLS =
  "relative min-w-[1.75rem] h-7 px-1.5 rounded-md border text-xs flex items-center justify-center font-mono transition-colors shrink-0 focus:outline-none focus-visible:border-indigo-500 dark:focus-visible:border-indigo-400";
const NEUTRAL_TILE_CLS =
  "bg-zinc-50 dark:bg-zinc-950 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600";
const ACTIVE_TILE_RING_CLS =
  "ring-2 ring-indigo-600 dark:ring-indigo-500 ring-offset-1 ring-offset-white dark:ring-offset-zinc-900 z-10 font-semibold";
const INACTIVE_TILE_CLS = "font-medium";

/** Question/milestone tiles row under the header: one small square per question/milestone, followed by Review & sync. */
export const QuizPaginationBar: React.FC<QuizPaginationBarProps> = ({
  currentIndex,
  problems,
  viewMode,
  workspace,
  isLab,
  onSelectQuestion,
  onToggleViewMode,
}) => {
  const labMode =
    isLab ?? (problems.length > 0 && problems.every((p) => /^M\d+$/i.test(p.id)));
  const isReview = viewMode === "review";
  const reviewBtnRef = useRef<HTMLButtonElement | null>(null);
  const navRef = useRef<HTMLDivElement | null>(null);

  // Keep keyboard focus on the current tile: when the question changes (keys, Next/Prev) while
  // focus is inside this bar, move focus to the new current tile so no stale ring stays behind.
  useEffect(() => {
    const nav = navRef.current;
    if (!nav || isReview) return;
    const active = document.activeElement;
    if (active && nav.contains(active)) {
      const current = nav.querySelector<HTMLButtonElement>('button[aria-current="step"]');
      if (current && current !== active) current.focus({ preventScroll: true });
    }
  }, [currentIndex, isReview]);

  useEffect(() => {
    if (isReview && !labMode) {
      reviewBtnRef.current?.scrollIntoView({ inline: "nearest", block: "nearest" });
    }
  }, [isReview, labMode]);

  if (labMode) {
    return (
      <LabMilestoneStepper
        problems={problems}
        currentIndex={currentIndex}
        viewMode={viewMode}
        onSelectQuestion={onSelectQuestion}
        onToggleViewMode={onToggleViewMode}
      />
    );
  }

  const itemNoun = workspace === "code" ? "Problem" : "Question";
  const navLabel = workspace === "code" ? "Problems" : "Questions";

  return (
    <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-800/80 overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
      <div
        ref={navRef}
        role="navigation"
        aria-label={navLabel}
        className="flex items-center justify-center gap-1.5 w-max mx-auto p-1"
      >
        {problems.map((prob, idx) => {
          const isActive = viewMode === "quiz" && currentIndex === idx;
          let colorCls = NEUTRAL_TILE_CLS;
          let statusLabel = "Unanswered";

          const isSkipped = prob.state?.skipped === true;
          const hasScore = prob.state?.score !== null && prob.state?.score !== undefined;
          const scoreVal = prob.state?.score ?? 0;
          const isAssisted = Boolean(
            prob.state?.setupRevealedBeforeAnswer ||
              prob.state?.solutionRevealedBeforeAnswer ||
              (prob.state?.hintsRevealed ?? 0) > 0 ||
              prob.state?.attempts?.some((a) => a.setupRevealed || a.solutionRevealed)
          );
          const isIndependentFull = hasScore && scoreVal >= 1 && !isAssisted && !isSkipped;
          const isPartialOrAssisted =
            hasScore && scoreVal > 0 && !isIndependentFull && !isSkipped;
          const isIncorrect = hasScore && scoreVal === 0 && !isSkipped;

          if (isIndependentFull) {
            colorCls =
              "bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-zinc-950 border-emerald-700 dark:border-emerald-500";
            statusLabel = `Correct on first attempt (${scoreVal})`;
          } else if (isPartialOrAssisted) {
            colorCls =
              "bg-amber-600 hover:bg-amber-700 dark:bg-amber-400 dark:hover:bg-amber-300 text-white dark:text-zinc-950 border-amber-600 dark:border-amber-400";
            statusLabel = `Assisted or partial (${scoreVal})`;
          } else if (isIncorrect) {
            colorCls =
              "bg-rose-600 hover:bg-rose-700 dark:bg-rose-400 dark:hover:bg-rose-300 text-white dark:text-zinc-950 border-rose-600 dark:border-rose-400";
            statusLabel = "Incorrect (0)";
          } else if (isSkipped) {
            colorCls =
              "bg-transparent hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-500 dark:text-zinc-400 border-dashed border-zinc-300 dark:border-zinc-700";
            statusLabel = "Skipped";
          }

          const activeRing = isActive ? ACTIVE_TILE_RING_CLS : INACTIVE_TILE_CLS;
          const itemTitle = `${itemNoun} ${idx + 1} — ${statusLabel}`;

          return (
            <button
              key={prob.id}
              type="button"
              onClick={() => onSelectQuestion(idx)}
              title={itemTitle}
              aria-label={itemTitle}
              aria-current={isActive ? "step" : undefined}
              className={`${TILE_BASE_CLS} ${colorCls} ${activeRing}`}
            >
              {idx + 1}
            </button>
          );
        })}

        <button
          ref={reviewBtnRef}
          type="button"
          onClick={() => onToggleViewMode(isReview ? "quiz" : "review")}
          aria-label="Review & sync"
          aria-pressed={isReview}
          aria-current={isReview ? "step" : undefined}
          title="Review & sync"
          className={`${TILE_BASE_CLS} ${NEUTRAL_TILE_CLS} ${
            isReview ? ACTIVE_TILE_RING_CLS : INACTIVE_TILE_CLS
          }`}
        >
          <ClipboardCheck className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
};
