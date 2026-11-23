"use client";

import React from "react";
import { ChevronDown, Loader2, RotateCcw } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { FormattedText } from "@/components/FormattedText";
import { StepRow } from "@/components/StepRow";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/shadcn/Collapsible";
import { hasCheckpointHint } from "@/lib/studioRules";
import { warningTone } from "@/lib/statusTone";
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
        <div className={`${warningTone.leftBorder} pl-3.5 py-1 text-sm text-zinc-700 dark:text-zinc-300`}>
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
  hideShowStepsButton?: boolean;
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
  onMarkDivergedStep,
  onReset,
  onSkip,
  skipLabel = "Skip",
  hasSetup = false,
  showSetup = false,
  setupUnopenedUnattempted = false,
  onToggleSetup,
  setupDisclosure,
  hideShowStepsButton = false,
}) => {
  const canShowHint = Boolean(problem.hasHint || hasCheckpointHint(problem.checkpointHint));
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 pt-1">
      {hasAttempt && (
        <button
          type="button"
          onClick={onReset}
          className="order-1 inline-flex min-h-[44px] sm:min-h-0 items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
        >
          <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Reset</span>
        </button>
      )}

      {hasSetup && (
        <Collapsible
          open={Boolean(showSetup)}
          onOpenChange={(nextOpen) => {
            if (nextOpen !== Boolean(showSetup)) onToggleSetup?.();
          }}
          className="contents"
        >
          {onToggleSetup && (
            <CollapsibleTrigger asChild>
              <button
                type="button"
                title={
                  setupUnopenedUnattempted
                    ? "Opening before checking counts as assisted"
                    : undefined
                }
                className="order-2 inline-flex min-h-[44px] sm:min-h-0 items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
              >
                <ChevronDown
                  aria-hidden="true"
                  className={`w-3.5 h-3.5 transition-transform duration-200 motion-reduce:transition-none ${
                    showSetup ? "rotate-180" : ""
                  }`}
                />
                <span>{showSetup ? "Hide equation set-up" : "Show equation set-up"}</span>
              </button>
            </CollapsibleTrigger>
          )}
          <CollapsibleContent className="order-11 basis-full w-full">
            {showSetup && setupDisclosure ? (
              <div className="pt-1">{setupDisclosure}</div>
            ) : null}
          </CollapsibleContent>
        </Collapsible>
      )}

      {(canShowHint || hasCheckpointHint(problem.checkpointHint)) && (
        <Collapsible
          open={showHint}
          onOpenChange={(nextOpen) => {
            if (nextOpen !== showHint) onToggleHint();
          }}
          className="contents"
        >
          <CollapsibleTrigger asChild>
            <button
              type="button"
              className="order-3 inline-flex min-h-[44px] sm:min-h-0 items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
            >
              <ChevronDown
                aria-hidden="true"
                className={`w-3.5 h-3.5 transition-transform duration-200 motion-reduce:transition-none ${
                  showHint ? "rotate-180" : ""
                }`}
              />
              <span>{showHint ? "Hide hint" : "Hint"}</span>
            </button>
          </CollapsibleTrigger>
          <CollapsibleContent className="order-10 basis-full w-full">
            {hasCheckpointHint(problem.checkpointHint) ? (
              <div className="pt-1">
                <CheckpointHintDisclosure
                  checkpointHint={problem.checkpointHint}
                  show={showHint}
                />
              </div>
            ) : null}
          </CollapsibleContent>
        </Collapsible>
      )}

      <Collapsible
        open={Boolean(showSolution)}
        onOpenChange={(nextOpen) => {
          if (nextOpen !== Boolean(showSolution)) onToggleSolution();
        }}
        className="contents"
      >
        {!hideShowStepsButton && (
          <CollapsibleTrigger asChild>
            <button
              type="button"
              title={
                stepsUnopenedUnattempted
                  ? "Opening before checking counts as assisted"
                  : undefined
              }
              className="order-4 inline-flex min-h-[44px] sm:min-h-0 items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
            >
              <ChevronDown
                aria-hidden="true"
                className={`w-3.5 h-3.5 transition-transform duration-200 motion-reduce:transition-none ${
                  showSolution ? "rotate-180" : ""
                }`}
              />
              <span>{showSolution ? "Hide steps" : "Show steps"}</span>
            </button>
          </CollapsibleTrigger>
        )}

        {/* Step-by-Step Derivation Disclosure */}
        <CollapsibleContent className="order-12 basis-full w-full">
          <Reveal show={Boolean(showSolution)}>
            {showSolution && (
              <div
                ref={stepsRef}
                className="mt-1 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-3"
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
                    <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                    <span>Loading steps…</span>
                  </div>
                ) : (
                  <div>
                    {(problem.steps || []).map((st, sIdx) => (
                      <StepRow
                        key={sIdx}
                        step={st}
                        index={sIdx}
                        isDiverged={onMarkDivergedStep ? problem.state.divergedStep === sIdx : false}
                        onMarkDiverged={onMarkDivergedStep ? () => onMarkDivergedStep(sIdx) : undefined}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </Reveal>
        </CollapsibleContent>
      </Collapsible>

      {onSkip && !hasAttempt && (
        <button
          type="button"
          onClick={onSkip}
          className="order-5 inline-flex min-h-[44px] sm:min-h-[36px] items-center gap-1 px-2 text-xs text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors motion-reduce:transition-none rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ml-auto"
        >
          <span>{skipLabel}</span>
        </button>
      )}
    </div>
  );
};
