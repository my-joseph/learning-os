"use client";

import React, { useMemo, useRef, useState } from "react";
import { BookOpen, ChevronDown, Loader2, RefreshCw, Shuffle, X } from "lucide-react";
import { Reveal } from "@/components/motion/Reveal";
import { FormattedText } from "@/components/FormattedText";
import { MathFigure } from "@/components/MathFigure";
import { LineChoicePrompt, parseLineChoicePrompt } from "@/components/LineChoicePrompt";
import { ChoiceOptionGroup } from "@/components/ChoiceOptionGroup";
import { AnswerResultCard } from "@/components/AnswerResultCard";
import { StepRow } from "@/components/StepRow";
import { PlainAnswerField } from "@/components/workspace/PlainAnswerField";
import { CheckpointHintDisclosure } from "@/components/workspace/ProblemAssistSection";
import { hasCheckpointHint } from "@/lib/studioRules";
import { isSubstantiveVerdict, sanitizeCheckMessage } from "@/lib/reviewGuard";
import {
  AttemptRecord,
  CheckResult,
  ProblemState,
  RedactedVariant,
  Step,
  WorkedExampleVariant,
} from "@/types/drill";

export interface VariantButtonState {
  showTry: boolean;
  showExample: boolean;
}

/**
 * Visibility contract for variant bank actions:
 * - Hidden whenever the archetype has no bank variants (`hasVariants` is falsy).
 * - "Try a similar question" unlocks after >= 1 wrong attempt on the original problem.
 * - "See a worked example" unlocks after >= 2 wrong attempts on the original problem.
 */
export function getVariantButtonState({
  hasVariants,
  wrongAttempts,
}: {
  hasVariants?: boolean;
  wrongAttempts: number;
}): VariantButtonState {
  if (!hasVariants) {
    return { showTry: false, showExample: false };
  }
  return {
    showTry: wrongAttempts >= 1,
    showExample: wrongAttempts >= 2,
  };
}

export interface VariantActionButtonsProps {
  hasVariants?: boolean;
  wrongAttempts: number;
  loadingMode: "try" | "example" | null;
  errorMessage?: string | null;
  onTrySimilar: () => void;
  onSeeExample: () => void;
}

/** Quiet secondary outline buttons shown beneath feedback once wrong-attempt thresholds are met. */
export const VariantActionButtons: React.FC<VariantActionButtonsProps> = ({
  hasVariants,
  wrongAttempts,
  loadingMode,
  errorMessage,
  onTrySimilar,
  onSeeExample,
}) => {
  const { showTry, showExample } = getVariantButtonState({ hasVariants, wrongAttempts });
  if (!showTry && !showExample) return null;

  const btnCls =
    "inline-flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-zinc-100 hover:border-zinc-300 dark:hover:border-zinc-700 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {showTry && (
          <button
            type="button"
            onClick={onTrySimilar}
            disabled={loadingMode !== null}
            className={btnCls}
          >
            {loadingMode === "try" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Shuffle className="w-3.5 h-3.5" aria-hidden="true" />
            )}
            <span>Try a similar question</span>
          </button>
        )}

        {showExample && (
          <button
            type="button"
            onClick={onSeeExample}
            disabled={loadingMode !== null}
            className={btnCls}
          >
            {loadingMode === "example" ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
            )}
            <span>See a worked example</span>
          </button>
        )}
      </div>

      {errorMessage && (
        <p role="status" className="text-xs text-zinc-500 dark:text-zinc-400">
          {errorMessage}
        </p>
      )}
    </div>
  );
};

export interface VariantPracticeCardProps {
  drillId: string;
  qid: string;
  variant: RedactedVariant;
  remainingCount: number;
  loadingAnother?: boolean;
  onAnother?: () => void;
  onClose: () => void;
}

/**
 * Inline practice card for `mode=try` rendered directly under the problem card.
 * Uses the shared workspace answer field + `=` check button and records substantive
 * results on the ORIGINAL problem's review item via `POST /api/review-items`.
 */
export const VariantPracticeCard: React.FC<VariantPracticeCardProps> = ({
  drillId,
  qid,
  variant,
  remainingCount,
  loadingAnother = false,
  onAnother,
  onClose,
}) => {
  const [userInput, setUserInput] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [checkingOptionId, setCheckingOptionId] = useState<string | null>(null);
  const [choiceUnlocked, setChoiceUnlocked] = useState(false);
  const [lastCheck, setLastCheck] = useState<CheckResult | null>(null);
  const [attempts, setAttempts] = useState<AttemptRecord[]>([]);
  const [showHint, setShowHint] = useState(false);
  const [hintRevealed, setHintRevealed] = useState(false);
  const [showSteps, setShowSteps] = useState(false);
  const [loadingSteps, setLoadingSteps] = useState(false);
  const [revealedSteps, setRevealedSteps] = useState<Step[] | null>(null);
  const [revealedAnswerDisplay, setRevealedAnswerDisplay] = useState<string>("");
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const isChoice = variant.answerSpec?.type === "choice";
  const choiceOptions = isChoice ? variant.answerSpec.options || [] : [];
  const lineChoiceData = useMemo(
    () =>
      isChoice
        ? parseLineChoicePrompt(variant.prompt, variant.answerSpec.options)
        : null,
    [isChoice, variant.prompt, variant.answerSpec.options]
  );

  const hasSubstantive = attempts.some((a) => isSubstantiveVerdict(a.verdict));
  const choiceResultStatus =
    isChoice && lastCheck && !choiceUnlocked
      ? lastCheck.verdict === "correct"
        ? "correct"
        : lastCheck.verdict === "incorrect"
        ? "wrong"
        : null
      : null;
  const choiceLocked =
    isChoice && (isChecking || (choiceResultStatus !== null && !choiceUnlocked));

  const syntheticState: ProblemState = {
    userInput,
    score:
      lastCheck?.verdict === "correct"
        ? 1
        : lastCheck?.verdict === "incorrect"
        ? 0
        : null,
    divergedStep: null,
    mistakes: [],
    lastCheck,
    attempts,
    hintsRevealed: hintRevealed ? 1 : 0,
  };

  const fetchStepsReveal = async () => {
    if (revealedSteps !== null || loadingSteps) return;
    setLoadingSteps(true);
    try {
      const qs = new URLSearchParams({
        variantId: variant.variantId,
        drillId,
        qid,
        part: "steps",
      });
      const res = await fetch(`/api/reveal?${qs.toString()}`);
      if (!res.ok) return;
      const data = (await res.json()) as {
        steps?: Step[];
        answerDisplay?: string;
        answerPlain?: string;
      };
      setRevealedSteps(Array.isArray(data.steps) ? data.steps : []);
      setRevealedAnswerDisplay(data.answerDisplay || data.answerPlain || "");
    } finally {
      setLoadingSteps(false);
    }
  };

  const runCheck = async (rawValue: string) => {
    const trimmed = rawValue.trim();
    if (!trimmed || isChecking) return;
    setIsChecking(true);
    setChoiceUnlocked(false);
    try {
      const res = await fetch("/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          variantId: variant.variantId,
          drillId,
          qid,
          input: trimmed,
        }),
      });
      const raw = (await res.json()) as CheckResult;
      const calmMsg = sanitizeCheckMessage(raw.verdict, raw.message);
      const checked: CheckResult =
        calmMsg === raw.message ? raw : { ...raw, message: calmMsg };

      setLastCheck(checked);
      const nextAttempt: AttemptRecord = {
        input: trimmed,
        ts: new Date().toISOString(),
        verdict: checked.verdict,
      };
      setAttempts((prev) => [...prev, nextAttempt]);

      if (isSubstantiveVerdict(checked.verdict)) {
        // Record result as an attempt on the ORIGINAL problem's review item.
        void fetch("/api/review-items", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId,
            qid,
            correct: checked.verdict === "correct",
            hintsUsed: hintRevealed ? 1 : 0,
          }),
        }).catch(() => {
          // Non-blocking review schedule update
        });

        if (checked.verdict === "correct") {
          setShowSteps(true);
          void fetchStepsReveal();
        }
      }
    } catch {
      setLastCheck({
        verdict: "invalid input",
        message: "Couldn't check that answer right now. Please try again.",
        components: [],
        diagnostics: [],
      });
    } finally {
      setIsChecking(false);
      setCheckingOptionId(null);
    }
  };

  const handleChoiceSelect = async (optionId: string) => {
    if (choiceLocked) return;
    setUserInput(optionId);
    setCheckingOptionId(optionId);
    await runCheck(optionId);
  };

  const handleToggleSteps = () => {
    if (!hasSubstantive) return;
    if (!showSteps && revealedSteps === null) {
      void fetchStepsReveal();
    }
    setShowSteps((prev) => !prev);
  };

  const placeholder =
    variant.placeholder ||
    variant.inputHint ||
    "Enter final answer (press Enter to check)...";

  return (
    <section
      aria-label="Similar question"
      className="bg-zinc-50 dark:bg-zinc-900/70 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500 dark:text-zinc-400">
        <span className="font-medium text-zinc-700 dark:text-zinc-300">
          Similar question
        </span>
        <div className="flex items-center gap-3">
          {remainingCount > 0 && onAnother && (
            <button
              type="button"
              onClick={onAnother}
              disabled={loadingAnother}
              className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 disabled:opacity-50 transition-colors"
            >
              {loadingAnother ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
              )}
              <span>Another one</span>
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close similar question"
            className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
          >
            <X className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Close</span>
          </button>
        </div>
      </div>

      <div className="text-base leading-relaxed text-zinc-900 dark:text-zinc-100">
        {lineChoiceData ? (
          <LineChoicePrompt
            parsed={lineChoiceData}
            selectedValue={userInput}
            onSelect={(optId) => void handleChoiceSelect(optId)}
            disabled={choiceLocked}
            checkingOptionId={checkingOptionId}
            resultStatus={choiceResultStatus}
          />
        ) : (
          <FormattedText text={variant.prompt} />
        )}
      </div>

      {(variant.figure || variant.visual) && (
        <div className="w-full">
          <MathFigure figure={variant.figure || variant.visual!} className="w-full" />
        </div>
      )}

      <div className="space-y-3">
        {isChoice && !lineChoiceData ? (
          <ChoiceOptionGroup
            options={choiceOptions}
            selectedValue={userInput}
            onSelect={(optId) => void handleChoiceSelect(optId)}
            disabled={choiceLocked}
            checkingOptionId={checkingOptionId}
            resultStatus={choiceResultStatus}
            layout="wrap"
          />
        ) : (
          <PlainAnswerField
            inputRef={inputRef}
            value={userInput}
            onChange={setUserInput}
            onCheck={() => void runCheck(userInput)}
            placeholder={placeholder}
            aria-label="Answer for similar question"
            isChecking={isChecking}
          />
        )}

        <AnswerResultCard
          lastCheck={lastCheck}
          state={syntheticState}
          onTryAgain={() => {
            if (isChoice) {
              setChoiceUnlocked(true);
            } else {
              inputRef.current?.focus();
              inputRef.current?.select();
            }
          }}
          onShowSteps={
            hasSubstantive
              ? () => {
                  setShowSteps(true);
                  void fetchStepsReveal();
                }
              : undefined
          }
        />
      </div>

      <div className="space-y-3 pt-1">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-zinc-500 dark:text-zinc-400">
          {hasCheckpointHint(variant.checkpointHint) && (
            <button
              type="button"
              onClick={() => {
                if (!showHint) setHintRevealed(true);
                setShowHint((prev) => !prev);
              }}
              aria-expanded={showHint}
              className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              <ChevronDown
                className={`w-3.5 h-3.5 transition-transform duration-200 ${
                  showHint ? "rotate-180" : ""
                }`}
              />
              <span>{showHint ? "Hide hint" : "Hint"}</span>
            </button>
          )}

          {hasSubstantive && (
            <button
              type="button"
              onClick={handleToggleSteps}
              aria-expanded={showSteps}
              className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              <ChevronDown
                className={`w-3.5 h-3.5 transition-transform duration-200 ${
                  showSteps ? "rotate-180" : ""
                }`}
              />
              <span>{showSteps ? "Hide steps" : "Show steps"}</span>
            </button>
          )}
        </div>

        <CheckpointHintDisclosure checkpointHint={variant.checkpointHint} show={showHint} />

        <Reveal show={Boolean(hasSubstantive && showSteps)}>
          {hasSubstantive && showSteps && (
            <div className="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-3">
              <div className="flex flex-wrap justify-between items-center gap-2 pb-2 border-b border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
                <span className="font-medium">Steps</span>
                {revealedAnswerDisplay && (
                  <span>
                    Answer:{" "}
                    <strong className="text-zinc-900 dark:text-zinc-100 font-semibold">
                      <FormattedText text={`$${revealedAnswerDisplay}$`} />
                    </strong>
                  </span>
                )}
              </div>
              {loadingSteps ? (
                <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 py-1">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                  <span>Loading steps…</span>
                </div>
              ) : (
                <div>
                  {(revealedSteps || []).map((st, sIdx) => (
                    <StepRow
                      key={sIdx}
                      step={st}
                      index={sIdx}
                      isActive={activeStep === sIdx}
                      onToggleHighlight={() =>
                        setActiveStep((prev) => (prev === sIdx ? null : sIdx))
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </Reveal>
      </div>
    </section>
  );
};

export interface WorkedExampleCardProps {
  example: WorkedExampleVariant;
  onClose: () => void;
}

/**
 * Fully solved worked example of a similar bank variant (`mode=example`),
 * rendered inline under the problem card using existing `StepRow`.
 */
export const WorkedExampleCard: React.FC<WorkedExampleCardProps> = ({
  example,
  onClose,
}) => {
  const [activeStep, setActiveStep] = useState<number | null>(null);

  return (
    <section
      aria-label="Worked example — a similar question, not yours"
      className="bg-zinc-50 dark:bg-zinc-900/70 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 sm:p-6 space-y-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-zinc-500 dark:text-zinc-400">
        <span className="font-medium text-zinc-700 dark:text-zinc-300">
          Worked example — a similar question, not yours
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close worked example"
          className="inline-flex items-center gap-1 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
        >
          <X className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Close</span>
        </button>
      </div>

      <div className="text-base leading-relaxed text-zinc-900 dark:text-zinc-100">
        <FormattedText text={example.prompt} />
      </div>

      {(example.figure || example.visual) && (
        <div className="w-full">
          <MathFigure figure={example.figure || example.visual!} className="w-full" />
        </div>
      )}

      <div className="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 space-y-3">
        <div className="flex flex-wrap justify-between items-center gap-2 pb-2 border-b border-zinc-200 dark:border-zinc-800 text-xs text-zinc-500 dark:text-zinc-400">
          <span className="font-medium">Steps</span>
          {(example.answerDisplay || example.answerPlain) && (
            <span>
              Answer:{" "}
              <strong className="text-zinc-900 dark:text-zinc-100 font-semibold">
                <FormattedText
                  text={
                    example.answerDisplay
                      ? `$${example.answerDisplay}$`
                      : example.answerPlain
                  }
                />
              </strong>
            </span>
          )}
        </div>
        <div>
          {(example.steps || []).map((st, sIdx) => (
            <StepRow
              key={sIdx}
              step={st}
              index={sIdx}
              isActive={activeStep === sIdx}
              onToggleHighlight={() =>
                setActiveStep((prev) => (prev === sIdx ? null : sIdx))
              }
            />
          ))}
        </div>
      </div>
    </section>
  );
};
