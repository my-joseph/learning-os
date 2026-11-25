"use client";

import React from "react";
import { ChevronDown, Loader2, RotateCcw } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { FormattedText } from "@/components/FormattedText";
import { StepRow } from "@/components/StepRow";
import { Button } from "@/components/ui/shadcn/Button";
import { Card } from "@/components/ui/shadcn/Card";
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
        <div className={`${warningTone.leftBorder} pl-space-3_5 py-space-1 text-sm text-foreground-control`}>
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
    <div className="flex flex-wrap items-center gap-x-space-3 sm:gap-x-space-4 gap-y-0 sm:gap-y-space-2 pt-space-1">
      {hasAttempt && (
        <Button
          type="button"
          onClick={onReset}
          variant="assist"
          size="assistInline"
          className="order-1 gap-space-1_5"
        >
          <RotateCcw className="size-space-3_5" aria-hidden="true" />
          <span>Reset</span>
        </Button>
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
              <Button
                type="button"
                title={
                  setupUnopenedUnattempted
                    ? "Opening before checking counts as assisted"
                    : undefined
                }
                variant="assist"
                size="assistInline"
                className="order-2"
              >
                <ChevronDown
                  aria-hidden="true"
                  className={`size-space-3_5 transition-transform duration-panel motion-reduce:transition-none ${
                    showSetup ? "rotate-180" : ""
                  }`}
                />
                <span>{showSetup ? "Hide equation set-up" : "Show equation set-up"}</span>
              </Button>
            </CollapsibleTrigger>
          )}
          <CollapsibleContent className="order-11 basis-full w-full">
            {showSetup && setupDisclosure ? (
              <div className="pt-space-1">{setupDisclosure}</div>
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
            <Button
              type="button"
              variant="assist"
              size="assistInline"
              className="order-3"
            >
              <ChevronDown
                aria-hidden="true"
                className={`size-space-3_5 transition-transform duration-panel motion-reduce:transition-none ${
                  showHint ? "rotate-180" : ""
                }`}
              />
              <span>{showHint ? "Hide hint" : "Hint"}</span>
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="order-10 basis-full w-full">
            {hasCheckpointHint(problem.checkpointHint) ? (
              <div className="pt-space-1">
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
            <Button
              type="button"
              title={
                stepsUnopenedUnattempted
                  ? "Opening before checking counts as assisted"
                  : undefined
              }
              variant="assist"
              size="assistInline"
              className="order-4"
            >
              <ChevronDown
                aria-hidden="true"
                className={`size-space-3_5 transition-transform duration-panel motion-reduce:transition-none ${
                  showSolution ? "rotate-180" : ""
                }`}
              />
              <span>{showSolution ? "Hide steps" : "Show steps"}</span>
            </Button>
          </CollapsibleTrigger>
        )}

        {/* Step-by-Step Derivation Disclosure */}
        <CollapsibleContent className="order-12 basis-full w-full">
          <Reveal show={Boolean(showSolution)}>
            {showSolution && (
              <Card
                variant="assistPanel"
                ref={stepsRef}
                className="mt-space-1 space-y-space-3"
              >
                {showStepsHeader && (
                  <div className="flex flex-wrap justify-between items-center gap-space-2 pb-space-2 border-b border-border text-xs text-muted">
                    <span className="font-normal">Steps</span>
                    {problem.answerDisplay && (
                      <span>
                        Answer:{" "}
                        <strong className="text-foreground font-semibold">
                          <FormattedText text={`$${problem.answerDisplay}$`} />
                        </strong>
                      </span>
                    )}
                  </div>
                )}
                {loadingSteps ? (
                  <div className="flex items-center gap-space-2 text-xs text-muted py-space-1">
                    <Loader2 className="size-space-3_5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
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
              </Card>
            )}
          </Reveal>
        </CollapsibleContent>
      </Collapsible>

      {onSkip && !hasAttempt && (
        <Button
          type="button"
          onClick={onSkip}
          variant="assist"
          size="assistSkip"
          className="order-5 ml-auto"
        >
          <span>{skipLabel}</span>
        </Button>
      )}
    </div>
  );
};
