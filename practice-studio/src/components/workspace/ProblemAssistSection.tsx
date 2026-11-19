"use client";

import React from "react";
import { ChevronDown, Loader2, RotateCcw } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { FormattedText } from "@/components/FormattedText";
import { StepRow } from "@/components/StepRow";
import { hasCheckpointHint } from "@/lib/studioRules";
import { Problem } from "@/types/drill";

export interface CheckpointHintDisclosureProps {
  checkpointHint?: string;
  show: boolean;
}

/** Shared checkpoint hint disclosure block animated with Reveal. */
export const CheckpointHintDisclosure: React.FC<CheckpointHintDisclosureProps> = ({
  checkpointHint,
  show,
}) => {
  const visible = Boolean(show && hasCheckpointHint(checkpointHint));
  return (
    <Reveal show={visible}>
      {visible && (
        <div className="border-l-2 border-amber-600 dark:border-amber-400 pl-3.5 py-1 text-sm text-zinc-700 dark:text-zinc-300">
          <FormattedText text={checkpointHint!} />
        </div>
      )}
    </Reveal>
  );
};

export interface ProblemAssistSectionProps {
  problem: Problem;
  hasAttempt: boolean;
  showHint: boolean;
  onToggleHint: () => void;
  showSolution: boolean;
  onToggleSolution: () => void;
  stepsUnopenedUnattempted: boolean;
  stepsRef?: React.RefObject<HTMLDivElement>;
  showStepsHeader?: boolean;
  loadingSteps?: boolean;
  activeStep: number | null;
  onToggleStepHighlight: (stepIdx: number) => void;
  onMarkDivergedStep?: (stepIdx: number) => void;
  onReset: () => void;
  onSkip?: () => void;
  skipLabel?: string;
  // Optional equation set-up props (Math workspace)
  hasSetup?: boolean;
  showSetup?: boolean;
  setupUnopenedUnattempted?: boolean;
  onToggleSetup?: () => void;
  setupDisclosure?: React.ReactNode;
}

/**
 * Shared secondary action toolbar (Reset / Set-up / Hint / Show steps / Skip)
 * and disclosures for checkpointHint, optional equation set-up, and StepRow list.
 */
export const ProblemAssistSection: React.FC<ProblemAssistSectionProps> = ({
  problem,
  hasAttempt,
  showHint,
  onToggleHint,
  showSolution,
  onToggleSolution,
  stepsUnopenedUnattempted,
  stepsRef,
  showStepsHeader = false,
  loadingSteps = false,
  activeStep,
  onToggleStepHighlight,
  onMarkDivergedStep,
  onReset,
  onSkip,
  skipLabel = "Skip",
  hasSetup = false,
  showSetup = false,
  setupUnopenedUnattempted = false,
  onToggleSetup,
  setupDisclosure,
}) => {
  return (
    <div className="space-y-3 pt-1">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-zinc-500 dark:text-zinc-400 [&_button]:min-h-[32px] sm:[&_button]:min-h-0">
        {hasAttempt && (
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        )}

        {hasSetup && onToggleSetup && (
          <button
            type="button"
            onClick={onToggleSetup}
            aria-expanded={showSetup}
            title={
              setupUnopenedUnattempted
                ? "Opening before checking counts as assisted"
                : undefined
            }
            className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            <ChevronDown
              className={`w-3.5 h-3.5 transition-transform duration-200 ${
                showSetup ? "rotate-180" : ""
              }`}
            />
            <span>{showSetup ? "Hide equation set-up" : "Show equation set-up"}</span>
          </button>
        )}

        {hasCheckpointHint(problem.checkpointHint) && <button
          type="button"
          onClick={onToggleHint}
          aria-expanded={showHint}
          className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
        >
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform duration-200 ${
              showHint ? "rotate-180" : ""
            }`}
          />
          <span>{showHint ? "Hide hint" : "Hint"}</span>
        </button>}

        <button
          type="button"
          onClick={onToggleSolution}
          aria-expanded={showSolution}
          title={
            stepsUnopenedUnattempted
              ? "Opening before checking counts as assisted"
              : undefined
          }
          className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
        >
          <ChevronDown
            className={`w-3.5 h-3.5 transition-transform duration-200 ${
              showSolution ? "rotate-180" : ""
            }`}
          />
          <span>{showSolution ? "Hide steps" : "Show steps"}</span>
        </button>

        {onSkip && !hasAttempt && (
          <button
            type="button"
            onClick={onSkip}
            className="inline-flex min-h-[36px] items-center gap-1 px-2 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors ml-auto"
          >
            <span>{skipLabel}</span>
          </button>
        )}
      </div>

      {/* Checkpoint Hint Disclosure */}
      <CheckpointHintDisclosure
        checkpointHint={problem.checkpointHint}
        show={showHint}
      />

      {/* Equation Set-up Disclosure */}
      {setupDisclosure}

      {/* Step-by-Step Derivation Disclosure */}
      <Reveal show={Boolean(showSolution)}>
        {showSolution && (
          <div
            ref={stepsRef}
            className={`bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-3 ${
              activeStep !== null ? "has-active" : ""
            }`}
          >
            {showStepsHeader && (
              <div className="flex flex-wrap justify-between items-center gap-2 pb-2 border-b border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
                <span className="font-medium">Steps</span>
                {problem.answerDisplay && (
                  <span>
                    Answer:{" "}
                    <strong className="text-zinc-900 dark:text-zinc-100 font-semibold">
                      <FormattedText text={`$${problem.answerDisplay}$`} />
                    </strong>
                  </span>
                )}
              </div>
            )}
            {loadingSteps ? (
              <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 py-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                <span>Loading steps…</span>
              </div>
            ) : (
              <div>
                {(problem.steps || []).map((st, sIdx) => (
                  <StepRow
                    key={sIdx}
                    step={st}
                    index={sIdx}
                    isActive={activeStep === sIdx}
                    isDiverged={onMarkDivergedStep ? problem.state.divergedStep === sIdx : false}
                    onToggleHighlight={() => onToggleStepHighlight(sIdx)}
                    onMarkDiverged={onMarkDivergedStep ? () => onMarkDivergedStep(sIdx) : undefined}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </Reveal>
    </div>
  );
};
