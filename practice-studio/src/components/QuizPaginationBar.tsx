"use client";

import React, { useEffect, useRef } from "react";
import { ClipboardCheck } from "lucide-react";
import { Problem } from "@/types/drill";
import { deriveMilestoneTileState } from "@/lib/codeStatus";

interface QuizPaginationBarProps {
  totalQuestions: number;
  currentIndex: number;
  problems: Problem[];
  viewMode: "quiz" | "review";
  isLab?: boolean;
  onSelectQuestion: (index: number) => void;
  onPrev: () => void;
  onNext: () => void;
  onToggleViewMode: (mode: "quiz" | "review") => void;
}

/** Question/milestone tiles row under the header: one small square per question/milestone. */
export const QuizPaginationBar: React.FC<QuizPaginationBarProps> = ({
  currentIndex,
  problems,
  viewMode,
  isLab,
  onSelectQuestion,
  onToggleViewMode,
}) => {
  const labMode =
    isLab ?? (problems.length > 0 && problems.every((p) => /^M\d+$/i.test(p.id)));
  const isReview = viewMode === "review";
  const reviewBtnRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (isReview) {
      reviewBtnRef.current?.scrollIntoView({ inline: "nearest", block: "nearest" });
    }
  }, [isReview]);

  return (
    <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-800/80">
      <div
        role="navigation"
        aria-label={labMode ? "Milestones" : "Questions"}
        className="flex items-center gap-1.5 overflow-x-auto p-1.5 -m-1.5 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden"
      >
        {problems.map((prob, idx) => {
          const isActive = viewMode === "quiz" && currentIndex === idx;
          let colorCls =
            "bg-zinc-50 dark:bg-zinc-950 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600";
          let statusLabel = labMode ? "Not started" : "Unanswered";

          if (labMode) {
            const tileState = deriveMilestoneTileState(prob.state);
            if (tileState === "pass") {
              colorCls =
                "bg-emerald-700 hover:bg-emerald-800 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-zinc-950 border-emerald-700 dark:border-emerald-500";
              statusLabel = "Review passed";
            } else if (tileState === "revise") {
              colorCls =
                "bg-amber-600 hover:bg-amber-700 dark:bg-amber-400 dark:hover:bg-amber-300 text-white dark:text-zinc-950 border-amber-600 dark:border-amber-400";
              statusLabel = "Needs revision";
            }
          } else {
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
                "bg-transparent hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 dark:text-zinc-500 border-dashed border-zinc-300 dark:border-zinc-700";
              statusLabel = "Skipped";
            }
          }

          const activeRing = isActive
            ? "ring-2 ring-indigo-600 dark:ring-indigo-500 ring-offset-1 ring-offset-white dark:ring-offset-zinc-900 z-10 font-semibold"
            : "font-medium";

          const itemTitle = labMode
            ? `Milestone ${prob.id} — ${statusLabel}`
            : `Question ${idx + 1} — ${statusLabel}`;

          return (
            <button
              key={prob.id}
              type="button"
              onClick={() => onSelectQuestion(idx)}
              title={itemTitle}
              aria-label={itemTitle}
              aria-current={isActive ? "step" : undefined}
              className={`relative min-w-[1.75rem] h-7 px-1.5 rounded-md border text-xs flex items-center justify-center font-mono transition-colors shrink-0 ${colorCls} ${activeRing}`}
            >
              {labMode ? prob.id : idx + 1}
            </button>
          );
        })}

        <button
          ref={reviewBtnRef}
          type="button"
          onClick={() => onToggleViewMode(isReview ? "quiz" : "review")}
          aria-label="Review & sync"
          aria-pressed={isReview}
          title={isReview ? "Back to questions" : "Review & sync"}
          className={`relative h-7 px-2 rounded-md border text-xs inline-flex items-center justify-center gap-1 font-sans transition-colors shrink-0 ${
            isReview
              ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 border-zinc-400 dark:border-zinc-600 ring-2 ring-indigo-600 dark:ring-indigo-500 ring-offset-1 ring-offset-white dark:ring-offset-zinc-900 z-10 font-semibold"
              : "bg-zinc-50 dark:bg-zinc-950 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-600 hover:text-zinc-900 dark:hover:text-zinc-100 font-medium"
          }`}
        >
          <ClipboardCheck className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>Review</span>
        </button>
      </div>
    </div>
  );
};
