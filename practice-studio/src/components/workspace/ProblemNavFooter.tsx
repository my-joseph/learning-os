"use client";

import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export interface ProblemNavFooterProps {
  index: number;
  isLastQuestion: boolean;
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  lastQuestionLabel?: string;
  nextDisabled?: boolean;
  hideNext?: boolean;
}

/** Shared quiet Previous / Next / Review & sync navigation footer below the problem card. */
export const ProblemNavFooter: React.FC<ProblemNavFooterProps> = ({
  index,
  isLastQuestion,
  onPrevQuestion,
  onNextQuestion,
  onOpenReview,
  lastQuestionLabel,
  nextDisabled = false,
  hideNext = false,
}) => {
  if (!onPrevQuestion && !onNextQuestion && !onOpenReview) {
    return null;
  }

  return (
    <div className="flex items-center justify-between px-1 text-xs text-zinc-500 dark:text-zinc-400">
      <button
        type="button"
        onClick={onPrevQuestion}
        disabled={index === 0}
        className="inline-flex items-center gap-1 py-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        <span>Previous</span>
      </button>

      {hideNext ? null : isLastQuestion && onOpenReview ? (
        <button
          type="button"
          onClick={onOpenReview}
          disabled={nextDisabled}
          className="inline-flex items-center gap-1 py-1.5 font-medium text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
        >
          <span>{lastQuestionLabel || <>Review &amp; sync</>}</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      ) : (
        <button
          type="button"
          onClick={onNextQuestion}
          disabled={isLastQuestion || nextDisabled}
          className="inline-flex items-center gap-1 py-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-30 disabled:pointer-events-none transition-colors"
        >
          <span>Next</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
