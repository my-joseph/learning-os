"use client";

import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";

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
    <div className="flex items-center justify-between px-space-1 text-xs text-muted">
      <Button
        variant="answerNav"
        size="answerNav"
        onClick={onPrevQuestion}
        disabled={index === 0}
      >
        <ChevronLeft className="size-space-4" />
        <span>Previous</span>
      </Button>

      {hideNext ? null : isLastQuestion && onOpenReview ? (
        <Button
          variant="answerNavReview"
          size="answerNav"
          onClick={onOpenReview}
          disabled={nextDisabled}
        >
          <span>{lastQuestionLabel || <>Review &amp; sync</>}</span>
          <ChevronRight className="size-space-4" />
        </Button>
      ) : (
        <Button
          variant="answerNav"
          size="answerNav"
          onClick={onNextQuestion}
          disabled={isLastQuestion || nextDisabled}
        >
          <span>Next</span>
          <ChevronRight className="size-space-4" />
        </Button>
      )}
    </div>
  );
};
