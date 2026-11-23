"use client";

import React from "react";
import type { Problem } from "@/types/drill";
import type { DrillDocument } from "@/types/drill";
import type { SyncState } from "@/hooks/useProgressSync";
import type { PracticeStatusOverride } from "@/hooks/types";
import type { Workspace } from "@/lib/routes";
import {
  buildDrillSteps,
  buildLabSteps,
  buildReviewStepMeta,
} from "@/lib/stepperModel";
import { buildSyncPreview } from "@/lib/sessionSummary";
import { isSyncedUpToDate } from "@/lib/syncStatus";
import { Stepper } from "@/components/Stepper";

export interface QuizPaginationBarProps {
  currentIndex: number;
  problems: Problem[];
  currentDrill?: DrillDocument | null;
  statusOverride?: PracticeStatusOverride;
  syncState?: SyncState;
  isSyncing?: boolean;
  viewMode: "quiz" | "review";
  workspace?: Workspace;
  isLab?: boolean;
  onSelectQuestion: (index: number) => void;
  onToggleViewMode: (mode: "quiz" | "review") => void;
  compact?: boolean;
}

/** Thin adapter rendering the shared horizontal Stepper for Math drills, Programming drills, and Project Labs. */
export const QuizPaginationBar: React.FC<QuizPaginationBarProps> = ({
  currentIndex,
  problems,
  currentDrill,
  statusOverride = null,
  syncState,
  isSyncing = false,
  viewMode,
  workspace,
  isLab,
  onSelectQuestion,
  onToggleViewMode,
  compact = false,
}) => {
  const labMode =
    isLab ?? (problems.length > 0 && problems.every((p) => /^M\d+$/i.test(p.id)));
  const isReview = viewMode === "review";
  const steps = labMode
    ? buildLabSteps(problems)
    : buildDrillSteps(problems, workspace);
  const synced = Boolean(
    currentDrill &&
      isSyncedUpToDate(
        currentDrill,
        buildSyncPreview(currentDrill, statusOverride).summary,
        syncState,
        isSyncing
      )
  );
  const review = buildReviewStepMeta({ synced });
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
      compact={compact}
    />
  );
};
