"use client";

import { useState, useEffect, useCallback } from "react";
import { Problem } from "@/types/drill";
import {
  getChoiceResultStatus,
  isChoiceInteractionLocked,
  isChoiceQuestion,
  isEditableEventTarget,
  resolveChoiceKeyOption,
  submitChoiceSelection,
} from "@/lib/answerFeedback";

export interface UseChoiceControllerOptions {
  problem: Problem;
  isChecking: boolean;
  setIsChecking: (checking: boolean) => void;
  onInputChange: (val: string) => void;
  onCheckAnswer: (inputOverride?: string) => Promise<void> | void;
  enabled?: boolean;
  isVariant?: boolean;
}

/**
 * Shared multiple-choice controller managing checking option state, retry unlock,
 * interaction lock, result status, auto-submit on selection, and 1–9 keyboard shortcuts.
 */
export function useChoiceController({
  problem,
  isChecking,
  setIsChecking,
  onInputChange,
  onCheckAnswer,
  enabled = true,
  isVariant = false,
}: UseChoiceControllerOptions) {
  const [checkingOptionId, setCheckingOptionId] = useState<string | null>(null);
  const [choiceRetryUnlocked, setChoiceRetryUnlocked] = useState(false);

  const resetChoiceState = useCallback(() => {
    setCheckingOptionId(null);
    setChoiceRetryUnlocked(false);
  }, []);

  useEffect(() => {
    resetChoiceState();
  }, [problem.id, resetChoiceState]);

  const isChoice = isChoiceQuestion(problem);
  const choiceOptions = problem.answerSpec?.options;
  const lastCheck = problem.state.lastCheck;

  const choiceLocked = isChoiceInteractionLocked({
    isChecking,
    lastCheck,
    skipped: problem.state.skipped,
    retryUnlocked: choiceRetryUnlocked,
    state: problem.state,
    isVariant,
  });

  const choiceResultStatus = getChoiceResultStatus({
    isChecking,
    lastCheck,
    skipped: problem.state.skipped,
    state: problem.state,
    isVariant,
  });

  const handleChoiceSelect = useCallback(
    async (optionId: string) => {
      await submitChoiceSelection({
        optionId,
        disabled: choiceLocked,
        isChecking,
        onStart: (id) => {
          setChoiceRetryUnlocked(false);
          setCheckingOptionId(id);
          setIsChecking(true);
        },
        onInputChange,
        onCheckAnswer,
        onFinish: () => {
          setIsChecking(false);
          setCheckingOptionId(null);
        },
      });
    },
    [choiceLocked, isChecking, setIsChecking, onInputChange, onCheckAnswer]
  );

  useEffect(() => {
    if (!enabled || !isChoice || !choiceOptions?.length) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (!/^[1-9]$/.test(e.key)) return;
      if (isEditableEventTarget(e.target)) return;
      if (document.querySelector('[role="alertdialog"], [role="dialog"]')) return;
      if (choiceLocked || isChecking) return;
      const matched = resolveChoiceKeyOption(e.key, choiceOptions);
      if (!matched) return;
      e.preventDefault();
      void handleChoiceSelect(matched.id);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [enabled, isChoice, choiceOptions, choiceLocked, isChecking, handleChoiceSelect]);

  const unlockChoiceRetry = useCallback(() => {
    setChoiceRetryUnlocked(true);
  }, []);

  return {
    isChoice,
    choiceOptions,
    checkingOptionId,
    choiceLocked,
    choiceResultStatus,
    handleChoiceSelect,
    unlockChoiceRetry,
    resetChoiceState,
  };
}
