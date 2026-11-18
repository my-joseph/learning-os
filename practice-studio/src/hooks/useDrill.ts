"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DrillDocument, Problem, CheckResult, TestRunReport } from "@/types/drill";
import {
  applyCheckResult,
  applySkip,
  applyDivergedStep,
  resetDrillForRetry,
  resetProblemForRetry,
} from "@/lib/applyCheckResult";
import {
  hasSubstantiveAttempt,
  isSubstantiveVerdict,
  sanitizeCheckMessage,
} from "@/lib/reviewGuard";
import {
  createTelemetryTimerState,
  setActiveProblem,
  setVisibility,
  recordHint,
  consumeAttempt,
  resetProblemTimer,
  TelemetryTimerState,
} from "@/lib/telemetryTimer";
import { labToDrillDocument, type LabDetailResponse } from "@/lib/labModel";
import { stepStudyPosition } from "@/lib/pagination";
import { findProblemIndex, isLabId } from "@/lib/routes";
import { StatusMessage, ViewMode } from "./types";

interface UseDrillOptions {
  triggerAutoSave: (doc: DrillDocument) => void;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
  onDrillLoaded?: (doc: DrillDocument) => void;
  onQuestionChange?: (drillId: string, problemId: string) => void;
}

/** Manage active drill loading, problem navigation, telemetry timer, and problem state updates. */
export function useDrill({
  triggerAutoSave,
  setStatus,
  onDrillLoaded,
  onQuestionChange,
}: UseDrillOptions) {
  const [currentDrill, setCurrentDrill] = useState<DrillDocument | null>(null);
  const [activeSteps, setActiveSteps] = useState<{ [probId: string]: number | null }>({});
  const [currentProblemIndex, setCurrentProblemIndex] = useState<number>(0);
  const [viewMode, setViewMode] = useState<ViewMode>("quiz");
  const [isLoadingDrill, setIsLoadingDrill] = useState<boolean>(true);
  const [drillNotFound, setDrillNotFound] = useState<boolean>(false);

  // Minimal telemetry: robust timer measuring visible active problem time & hint telemetry
  const timerStateRef = useRef<TelemetryTimerState>(createTelemetryTimerState());

  useEffect(() => {
    if (!currentDrill || !currentDrill.problems.length) return;
    const currentProb = currentDrill.problems[currentProblemIndex];
    if (currentProb) {
      timerStateRef.current = setActiveProblem(timerStateRef.current, currentProb.id, Date.now());
    }
  }, [currentDrill, currentProblemIndex]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = !document.hidden;
      timerStateRef.current = setVisibility(timerStateRef.current, isVisible, Date.now());
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  const handleHintRevealed = useCallback((probId: string) => {
    timerStateRef.current = recordHint(timerStateRef.current, probId);
  }, []);

  const loadDrill = useCallback(
    async (id: string, initialQuestionId?: string | null) => {
      setIsLoadingDrill(true);
      setDrillNotFound(false);
      try {
        const endpoint = isLabId(id)
          ? `/api/lab?id=${encodeURIComponent(id)}`
          : `/api/drill?id=${encodeURIComponent(id)}`;
        const res = await fetch(endpoint);
        if (res.status === 404 || res.status === 400) {
          setCurrentDrill(null);
          setDrillNotFound(true);
          return;
        }
        if (!res.ok) throw new Error(isLabId(id) ? "Could not load lab" : "Could not load drill");
        const rawPayload = await res.json();
        const doc: DrillDocument = isLabId(id)
          ? labToDrillDocument(rawPayload as LabDetailResponse)
          : (rawPayload as DrillDocument);
        const normalizedDoc: DrillDocument = {
          ...doc,
          problems: (doc.problems || []).map((p) => ({
            ...p,
            state: {
              // Keep every saved field (attempts, hintsRevealed, durationMs, setupRevealedBeforeAnswer, ...)
              ...p.state,
              userInput: p.state?.userInput || "",
              userCode: p.state?.userCode || p.starterCode || p.codeSnippet || "",
              score: p.state?.score ?? null,
              divergedStep: p.state?.divergedStep ?? null,
              mistakes: p.state?.mistakes || [],
              mistakeNote: p.state?.mistakeNote || "",
              skipped: p.state?.skipped || false,
              lastCheck: p.state?.lastCheck || null,
              lastTestReport: p.state?.lastTestReport || null,
            },
          })),
        };
        setCurrentDrill(normalizedDoc);
        setCurrentProblemIndex(findProblemIndex(normalizedDoc.problems, initialQuestionId));
        setViewMode("quiz");
        onDrillLoaded?.(normalizedDoc);
        setActiveSteps({});
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `Failed to load ${id}: ${errMsg}`, type: "fail" });
      } finally {
        setIsLoadingDrill(false);
      }
    },
    [onDrillLoaded, setStatus]
  );

  const updateProblem = useCallback(
    (probId: string, updater: (prob: Problem) => Problem) => {
      if (!currentDrill) return;
      const updated: DrillDocument = {
        ...currentDrill,
        problems: currentDrill.problems.map((p) => (p.id === probId ? updater(p) : p)),
      };
      setCurrentDrill(updated);
      triggerAutoSave(updated);
    },
    [currentDrill, triggerAutoSave]
  );

  const saveAndReveal = useCallback(
    async (
      updatedDoc: DrillDocument,
      probId: string,
      parts: Array<"steps" | "display" | "solution">
    ) => {
      try {
        await fetch("/api/save-state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(updatedDoc),
        });
      } catch {
        // ignore transient save error
      }
      const patch: Partial<Problem> = {};
      for (const part of parts) {
        try {
          const res = await fetch(
            `/api/reveal?drill=${encodeURIComponent(updatedDoc.drillId)}&q=${encodeURIComponent(probId)}&part=${part}`
          );
          if (!res.ok) continue;
          const data = await res.json();
          if (part === "steps") {
            if (Array.isArray(data.steps)) patch.steps = data.steps;
            if (typeof data.answerDisplay === "string") patch.answerDisplay = data.answerDisplay;
            if (typeof data.answerPlain === "string") patch.answerPlain = data.answerPlain;
          } else if (part === "display") {
            if (typeof data.display === "string") patch.display = data.display;
            if (typeof data.plainText === "string") patch.plainText = data.plainText;
          } else if (part === "solution") {
            if (typeof data.solutionCode === "string") patch.solutionCode = data.solutionCode;
          }
        } catch {
          // ignore transient reveal error
        }
      }
      if (Object.keys(patch).length > 0) {
        setCurrentDrill((prev) => {
          if (!prev || prev.drillId !== updatedDoc.drillId) return prev;
          return {
            ...prev,
            problems: prev.problems.map((p) => (p.id === probId ? { ...p, ...patch } : p)),
          };
        });
      }
    },
    []
  );

  const handleCheckAnswer = async (probId: string, inputOverride?: string) => {
    if (!currentDrill) return;
    const p = currentDrill.problems.find((item) => item.id === probId);
    if (!p) return;

    const inputVal = (
      inputOverride !== undefined ? inputOverride : p.state.userInput
    ).trim();
    if (!inputVal) return;

    try {
      const res = await fetch("/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drillId: currentDrill.drillId,
          problemId: p.id,
          subject: currentDrill.subject,
          input: inputVal,
        }),
      });

      const rawResult: CheckResult = await res.json();
      const calmMessage = sanitizeCheckMessage(rawResult.verdict, rawResult.message);
      if (calmMessage !== rawResult.message) {
        console.error("[check-answer] raw error:", rawResult.message);
      }
      const result: CheckResult =
        calmMessage === rawResult.message
          ? rawResult
          : { ...rawResult, message: calmMessage };

      const { durationMs, hintsRevealed, nextState } = consumeAttempt(
        timerStateRef.current,
        probId,
        Date.now()
      );
      timerStateRef.current = nextState;
      const hintsCount = hintsRevealed + (p.state?.hintsRevealed || 0);

      const updatedProblems = currentDrill.problems.map((prob) => {
        if (prob.id !== probId) return prob;
        return {
          ...prob,
          state: applyCheckResult(prob, inputVal, result, currentDrill.mistakeTags || [], {
            durationMs,
            hintsRevealed: hintsCount,
          }),
        };
      });

      const updatedDoc: DrillDocument = {
        ...currentDrill,
        problems: updatedProblems,
      };

      setCurrentDrill(updatedDoc);
      triggerAutoSave(updatedDoc);
      if (isSubstantiveVerdict(result.verdict)) {
        const partsToReveal: Array<"steps" | "display"> = ["steps"];
        if (p.hasSetup && !p.display && !p.plainText) {
          partsToReveal.push("display");
        }
        void saveAndReveal(updatedDoc, probId, partsToReveal);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `SymPy Check error: ${errMsg}`, type: "fail" });
    }
  };

  const handleInputChange = (probId: string, val: string) => {
    updateProblem(probId, (p) => ({ ...p, state: { ...p.state, userInput: val } }));
  };

  const handleMistakeNoteChange = (probId: string, note: string) => {
    updateProblem(probId, (p) => ({ ...p, state: { ...p.state, mistakeNote: note } }));
  };

  // Equation set-up opened by the learner. Only counts as assistance before the first substantive check.
  const handleSetupRevealed = (probId: string) => {
    if (!currentDrill) return;
    const target = currentDrill.problems.find((p) => p.id === probId);
    if (!target) return;
    const shouldMarkAssisted =
      !hasSubstantiveAttempt(target.state) && !target.state.setupRevealedBeforeAnswer;
    const updatedDoc: DrillDocument = shouldMarkAssisted
      ? {
          ...currentDrill,
          problems: currentDrill.problems.map((p) =>
            p.id === probId
              ? { ...p, state: { ...p.state, setupRevealedBeforeAnswer: true } }
              : p
          ),
        }
      : currentDrill;
    if (shouldMarkAssisted) {
      setCurrentDrill(updatedDoc);
      triggerAutoSave(updatedDoc);
    }
    if (!target.display && !target.plainText) {
      void saveAndReveal(updatedDoc, probId, ["display"]);
    }
  };

  // Step-by-step solution opened by the learner before their first correct answer.
  const handleSolutionRevealed = (probId: string) => {
    if (!currentDrill) return;
    const target = currentDrill.problems.find((p) => p.id === probId);
    if (!target) return;
    const hasCorrect =
      target.state.score === 1 ||
      Boolean(target.state.attempts?.some((a) => a.verdict === "correct"));
    const shouldMarkAssisted = !hasCorrect && !target.state.solutionRevealedBeforeAnswer;
    const updatedDoc: DrillDocument = shouldMarkAssisted
      ? {
          ...currentDrill,
          problems: currentDrill.problems.map((p) =>
            p.id === probId
              ? { ...p, state: { ...p.state, solutionRevealedBeforeAnswer: true } }
              : p
          ),
        }
      : currentDrill;
    if (shouldMarkAssisted) {
      setCurrentDrill(updatedDoc);
      triggerAutoSave(updatedDoc);
    }
    if (!target.steps || target.steps.length === 0) {
      void saveAndReveal(updatedDoc, probId, ["steps"]);
    }
  };

  const handleToggleStepHighlight = (probId: string, stepIdx: number) => {
    setActiveSteps((prev) => ({
      ...prev,
      [probId]: prev[probId] === stepIdx ? null : stepIdx,
    }));
  };

  const handleMarkDivergedStep = (probId: string, stepIdx: number) => {
    updateProblem(probId, (p) => ({ ...p, state: applyDivergedStep(p, stepIdx) }));
  };

  const handleSetScore = (probId: string, score: number | null) => {
    updateProblem(probId, (p) => ({ ...p, state: { ...p.state, score, skipped: false } }));
  };

  const handleTestReportChange = (probId: string, report: TestRunReport) => {
    updateProblem(probId, (p) => ({
      ...p,
      state: { ...p.state, lastTestReport: report },
    }));
  };

  const handleToggleMistakeTag = (probId: string, tagId: string) => {
    updateProblem(probId, (p) => {
      const list = p.state.mistakes || [];
      const next = list.includes(tagId) ? list.filter((t) => t !== tagId) : [...list, tagId];
      return {
        ...p,
        state: { ...p.state, mistakes: next },
      };
    });
  };

  const handleSkipProblem = (probId: string) => {
    if (!currentDrill) return;
    const p = currentDrill.problems.find((item) => item.id === probId);
    if (!p) return;

    const { durationMs, hintsRevealed, nextState } = consumeAttempt(
      timerStateRef.current,
      probId,
      Date.now()
    );
    timerStateRef.current = nextState;
    const hintsCount = hintsRevealed + (p.state?.hintsRevealed || 0);

    const updatedDoc: DrillDocument = {
      ...currentDrill,
      problems: currentDrill.problems.map((prob) =>
        prob.id === probId
          ? {
              ...prob,
              state: applySkip(prob, {
                durationMs,
                hintsRevealed: hintsCount,
              }),
            }
          : prob
      ),
    };
    setCurrentDrill(updatedDoc);
    triggerAutoSave(updatedDoc);
    const partsToReveal: Array<"steps" | "display"> = ["steps"];
    if (p.hasSetup && !p.display && !p.plainText) {
      partsToReveal.push("display");
    }
    void saveAndReveal(updatedDoc, probId, partsToReveal);
  };

  const handleResetProblem = (probId: string) => {
    if (!currentDrill) return;
    timerStateRef.current = resetProblemTimer(timerStateRef.current, probId);
    setActiveSteps((prev) => ({ ...prev, [probId]: null }));
    updateProblem(probId, resetProblemForRetry);
  };

  const handleResetAll = () => {
    if (!currentDrill) return;

    const updated = resetDrillForRetry(currentDrill);
    const isVisible = typeof document !== "undefined" ? !document.hidden : true;
    timerStateRef.current = createTelemetryTimerState(
      updated.problems[0]?.id ?? null,
      isVisible
    );
    setActiveSteps({});
    setCurrentDrill(updated);
    setCurrentProblemIndex(0);
    setViewMode("quiz");
    triggerAutoSave(updated);
    if (updated.problems[0]) {
      onQuestionChange?.(updated.drillId, updated.problems[0].id);
    }
    const drillLabel = currentDrill.unitTitle || currentDrill.unitCode || currentDrill.drillId;
    setStatus({
      text: `Reset ${drillLabel} to initial state.`,
      type: "pass",
    });
  };

  const selectQuestionIndex = useCallback(
    (nextIdx: number) => {
      if (!currentDrill) return;
      const clamped = Math.max(0, Math.min(nextIdx, currentDrill.problems.length - 1));
      setCurrentProblemIndex(clamped);
      const prob = currentDrill.problems[clamped];
      if (prob) {
        onQuestionChange?.(currentDrill.drillId, prob.id);
      }
    },
    [currentDrill, onQuestionChange]
  );

  const handlePrevQuestion = useCallback(() => {
    if (!currentDrill || currentDrill.problems.length === 0) return;
    const nextPos = stepStudyPosition(
      { viewMode, index: currentProblemIndex },
      currentDrill.problems.length,
      "prev"
    );
    if (nextPos.viewMode === viewMode && nextPos.index === currentProblemIndex) return;
    setViewMode(nextPos.viewMode);
    if (nextPos.viewMode === "quiz") {
      selectQuestionIndex(nextPos.index);
    }
  }, [currentDrill, viewMode, currentProblemIndex, selectQuestionIndex]);

  const handleNextQuestion = useCallback(() => {
    if (!currentDrill || currentDrill.problems.length === 0) return;
    const nextPos = stepStudyPosition(
      { viewMode, index: currentProblemIndex },
      currentDrill.problems.length,
      "next"
    );
    if (nextPos.viewMode === viewMode && nextPos.index === currentProblemIndex) return;
    setViewMode(nextPos.viewMode);
    if (nextPos.viewMode === "quiz") {
      selectQuestionIndex(nextPos.index);
    }
  }, [currentDrill, viewMode, currentProblemIndex, selectQuestionIndex]);

  const handleSelectQuestion = useCallback(
    (idx: number) => {
      selectQuestionIndex(idx);
      if (viewMode !== "quiz") {
        setViewMode("quiz");
      }
    },
    [selectQuestionIndex, viewMode]
  );

  // Keyboard navigation across questions/milestones and the trailing Review step
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable ||
          Boolean(target.closest('[role="alertdialog"], [role="dialog"]')))
      ) {
        return;
      }
      if (document.querySelector('[role="alertdialog"], [role="dialog"]')) {
        return;
      }
      if (e.key === "ArrowLeft") {
        handlePrevQuestion();
      } else if (e.key === "ArrowRight") {
        handleNextQuestion();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlePrevQuestion, handleNextQuestion]);

  return {
    currentDrill,
    setCurrentDrill,
    activeSteps,
    currentProblemIndex,
    setCurrentProblemIndex,
    viewMode,
    setViewMode,
    isLoadingDrill,
    setIsLoadingDrill,
    drillNotFound,
    loadDrill,
    handleHintRevealed,
    handleCheckAnswer,
    handleInputChange,
    handleMistakeNoteChange,
    handleSetupRevealed,
    handleSolutionRevealed,
    handleToggleStepHighlight,
    handleMarkDivergedStep,
    handleSetScore,
    handleTestReportChange,
    handleToggleMistakeTag,
    handleSkipProblem,
    handleResetProblem,
    handleResetAll,
    handlePrevQuestion,
    handleNextQuestion,
    handleSelectQuestion,
  };
}
