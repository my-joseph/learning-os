"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Reveal } from "@/components/motion/Reveal";
import {
  Problem,
  MistakeTag,
  RedactedVariant,
  WorkedExampleVariant,
} from "@/types/drill";
import { QuestionTimer } from "@/components/QuestionTimer";
import { ProblemNavFooter } from "@/components/workspace/ProblemNavFooter";
import { ProblemSelfEval } from "@/components/workspace/ProblemSelfEval";
import {
  VariantActionButtons,
  VariantPracticeCard,
  WorkedExampleCard,
} from "@/components/workspace/VariantPracticePanel";
import { MathItemView } from "@/components/math/MathItemView";
import { countWrongAttempts, hasSubstantiveAttempt } from "@/lib/reviewGuard";
import { plainTitle } from "@/lib/titleText";

export interface MathWorkspaceProps {
  problem: Problem;
  drillId?: string;
  index: number;
  totalQuestions?: number;
  unitCode?: string;
  drillTitle?: string;
  mistakeTags: MistakeTag[];
  activeStep: number | null;
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  onSkip?: () => void;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep: (stepIdx: number) => void;
  onSetScore: (score: number | null) => void;
  onToggleMistakeTag: (tagId: string) => void;
  onMistakeNoteChange: (note: string) => void;
  onResetProblem: () => void;
  onHintRevealed?: () => void;
  onSetupRevealed?: () => void;
  onSolutionRevealed?: () => void;
  onBeforeFetchVariant?: () => Promise<void>;
  onPrevQuestion?: () => void;
  onNextQuestion?: () => void;
  onOpenReview?: () => void;
  questionTimerMs?: number;
  totalTimerMs?: number;
  isTimerPaused?: boolean;
  onToggleTimerPause?: () => void;
  reviewSupplement?: React.ReactNode;
  isReviewSession?: boolean;
  nextCardLabel?: string;
  lastQuestionNavLabel?: string;
}

/** Clean centred Math workspace following docs/studio_design.md. */
export const MathWorkspace: React.FC<MathWorkspaceProps> = ({
  problem,
  drillId,
  index,
  totalQuestions,
  unitCode,
  drillTitle,
  mistakeTags,
  activeStep,
  onInputChange,
  onCheckAnswer,
  onSkip,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onSetScore,
  onToggleMistakeTag,
  onMistakeNoteChange,
  onResetProblem,
  onHintRevealed,
  onSetupRevealed,
  onSolutionRevealed,
  onBeforeFetchVariant,
  onPrevQuestion,
  onNextQuestion,
  onOpenReview,
  questionTimerMs,
  totalTimerMs,
  isTimerPaused = false,
  onToggleTimerPause,
  reviewSupplement,
  isReviewSession = false,
  nextCardLabel,
  lastQuestionNavLabel,
}) => {
  const [tryVariant, setTryVariant] = useState<{
    variant: RedactedVariant;
    remainingCount: number;
  } | null>(null);
  const [exampleVariant, setExampleVariant] = useState<WorkedExampleVariant | null>(null);
  const [variantLoading, setVariantLoading] = useState<"try" | "example" | null>(null);
  const [variantError, setVariantError] = useState<string | null>(null);

  const hasAttempt = hasSubstantiveAttempt(problem.state);
  const score = problem.state.score;

  useEffect(() => {
    setTryVariant(null);
    setExampleVariant(null);
    setVariantLoading(null);
    setVariantError(null);
  }, [problem.id]);

  const wrongAttempts = countWrongAttempts(problem.state);

  const handleFetchVariant = useCallback(
    async (mode: "try" | "example") => {
      if (!drillId || variantLoading) return;
      setVariantLoading(mode);
      setVariantError(null);
      try {
        if (onBeforeFetchVariant) {
          await onBeforeFetchVariant();
        }
        const qs = new URLSearchParams({
          drillId,
          qid: problem.id,
          mode,
        });
        if (mode === "example" && tryVariant?.variant.variantId) {
          qs.set("exclude", tryVariant.variant.variantId);
        }
        const res = await fetch(`/api/variant?${qs.toString()}`);
        const data = (await res.json()) as {
          variant?: RedactedVariant | WorkedExampleVariant;
          remainingCount?: number;
          error?: string;
        };
        if (!res.ok || !data.variant) {
          setVariantError(data.error || "No similar question is available right now.");
          return;
        }
        if (mode === "try") {
          setTryVariant({
            variant: data.variant as RedactedVariant,
            remainingCount: typeof data.remainingCount === "number" ? data.remainingCount : 0,
          });
        } else {
          setExampleVariant(data.variant as WorkedExampleVariant);
        }
      } catch {
        setVariantError("Couldn't load a similar question right now.");
      } finally {
        setVariantLoading(null);
      }
    },
    [drillId, onBeforeFetchVariant, problem.id, tryVariant, variantLoading]
  );

  const isLastQuestion =
    typeof totalQuestions === "number" && totalQuestions > 0 && index === totalQuestions - 1;

  const displayTitle = plainTitle(drillTitle);

  const questionHeader = (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span>
          Question {index + 1}
          {typeof totalQuestions === "number" && totalQuestions > 0
            ? ` of ${totalQuestions}`
            : ""}
        </span>
        {typeof problem.level === "number" && problem.level > 0 && (
          <span title={problem.levelLabel?.trim() || undefined}>
            Level {problem.level}
          </span>
        )}
      </div>
      <QuestionTimer
        questionMs={questionTimerMs ?? (problem.state?.durationMs || 0)}
        totalMs={totalTimerMs ?? (questionTimerMs ?? (problem.state?.durationMs || 0))}
        isPaused={isTimerPaused}
        onTogglePause={onToggleTimerPause}
      />
    </div>
  );

  return (
    <div className="mx-auto w-full max-w-[720px] space-y-4">
      {displayTitle && (
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight px-0.5">
          {displayTitle}
        </h1>
      )}

      <article className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-6">
        <MathItemView
          problem={problem}
          header={questionHeader}
          unitCode={unitCode}
          drillTitle={drillTitle}
          mistakeTags={mistakeTags}
          activeStep={activeStep}
          isLastQuestion={isReviewSession ? false : isLastQuestion}
          nextLabel={nextCardLabel ?? "Next question"}
          onInputChange={onInputChange}
          onCheckAnswer={onCheckAnswer}
          onSkip={onSkip}
          onToggleStepHighlight={onToggleStepHighlight}
          onMarkDivergedStep={onMarkDivergedStep}
          onReset={() => {
            setTryVariant(null);
            setExampleVariant(null);
            setVariantError(null);
            onResetProblem();
          }}
          onHintRevealed={onHintRevealed}
          onSetupRevealed={onSetupRevealed}
          onSolutionRevealed={onSolutionRevealed}
          onNextQuestion={onNextQuestion}
          onOpenReview={onOpenReview}
          afterResultCard={
            drillId ? (
              <VariantActionButtons
                hasVariants={problem.hasVariants}
                wrongAttempts={wrongAttempts}
                loadingMode={variantLoading}
                errorMessage={variantError}
                onTrySimilar={() => void handleFetchVariant("try")}
                onSeeExample={() => void handleFetchVariant("example")}
              />
            ) : undefined
          }
          supplement={reviewSupplement}
          footer={
            <ProblemSelfEval
              hasAttempt={hasAttempt}
              score={score}
              mistakes={problem.state.mistakes}
              mistakeNote={problem.state.mistakeNote}
              mistakeTags={mistakeTags}
              noteAriaLabel={`Note for question ${index + 1}`}
              onSetScore={onSetScore}
              onToggleMistakeTag={onToggleMistakeTag}
              onMistakeNoteChange={onMistakeNoteChange}
            />
          }
        />
      </article>

      {/* Inline similar-question practice and worked example under the problem card */}
      <Reveal show={Boolean(drillId && tryVariant)}>
        {drillId && tryVariant && (
          <VariantPracticeCard
            key={tryVariant.variant.variantId}
            drillId={drillId}
            qid={problem.id}
            variant={tryVariant.variant}
            remainingCount={tryVariant.remainingCount}
            loadingAnother={variantLoading === "try"}
            onAnother={() => void handleFetchVariant("try")}
            onClose={() => setTryVariant(null)}
          />
        )}
      </Reveal>

      <Reveal show={Boolean(exampleVariant)}>
        {exampleVariant && (
          <WorkedExampleCard
            key={exampleVariant.variantId}
            example={exampleVariant}
            onClose={() => setExampleVariant(null)}
          />
        )}
      </Reveal>

      {/* Quiet question navigation footer */}
      <ProblemNavFooter
        index={index}
        isLastQuestion={isLastQuestion}
        onPrevQuestion={onPrevQuestion}
        onNextQuestion={onNextQuestion}
        onOpenReview={onOpenReview}
        lastQuestionLabel={lastQuestionNavLabel}
      />
    </div>
  );
};
