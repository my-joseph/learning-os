"use client";

import React from "react";
import type { Problem } from "@/types/drill";
import type { Workspace } from "@/lib/routes";
import {
  buildDrillSteps,
  buildLabSteps,
  buildReviewStepMeta,
} from "@/lib/stepperModel";
import { Stepper } from "@/components/Stepper";

export interface QuizPaginationBarProps {
  currentIndex: number;
  problems: Problem[];
  viewMode: "quiz" | "review";
  workspace?: Workspace;
  isLab?: boolean;
  onSelectQuestion: (index: number) => void;
  onToggleViewMode: (mode: "quiz" | "review") => void;
}

/** Thin adapter rendering the shared horizontal Stepper for Math drills, Programming drills, and Project Labs. */
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
  const steps = labMode
    ? buildLabSteps(problems)
    : buildDrillSteps(problems, workspace);
  const review = buildReviewStepMeta(steps, labMode);
  const navLabel = labMode
    ? "Lab milestones"
    : workspace === "code"
    ? "Problems"
    : "Questions";

  return (
    <Stepper
      navLabel={navLabel}
      steps={steps}
      currentIndex={currentIndex}
      isReview={isReview}
      review={review}
      onSelect={onSelectQuestion}
      onToggleReview={() => onToggleViewMode(isReview ? "quiz" : "review")}
    />
  );
};
