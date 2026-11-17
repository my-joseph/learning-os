"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DrillDocument, Problem, CheckResult } from "@/types/drill";
import { applyCheckResult, applySkip, applyDivergedStep } from "@/lib/applyCheckResult";
import {
  createTelemetryTimerState,
  setActiveProblem,
  setVisibility,
  recordHint,
  consumeAttempt,
  resetProblemTimer,
  TelemetryTimerState,
} from "@/lib/telemetryTimer";
import { StatusMessage, ViewMode } from "./types";

interface UseDrillOptions {
  triggerAutoSave: (doc: DrillDocument) => void;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
  onDrillLoaded?: () => void;
}

/** Manage active drill loading, problem navigation, telemetry timer, and problem state updates. */
export function useDrill({ triggerAutoSave, setStatus, onDrillLoaded }: UseDrillOptions) {
  const [currentDrill, setCurrentDrill] = useState<DrillDocument | null>(null);
  const [activeSteps, setActiveSteps] = useState<{ [probId: string]: number | null }>({});
  const [currentProblemIndex, setCurrentProblemIndex] = useState<number>(0);
  const [viewMode, setViewMode] = useState<ViewMode>("quiz");
  const [isLoadingDrill, setIsLoadingDrill] = useState<boolean>(true);

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
    async (id: string) => {
      setIsLoadingDrill(true);
      try {
        const res = await fetch(`/api/drill?id=${encodeURIComponent(id)}`);
        if (!res.ok) throw new Error("Could not load drill");
        const doc: DrillDocument = await res.json();
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
        setCurrentProblemIndex(0);
        setViewMode("quiz");
        onDrillLoaded?.();
        setActiveSteps({});
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `Failed to load drill ${id}: ${errMsg}`, type: "fail" });
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

  const handleCheckAnswer = async (probId: string) => {
    if (!currentDrill) return;
    const p = currentDrill.problems.find((item) => item.id === probId);
    if (!p) return;

    const inputVal = p.state.userInput.trim();
    if (!inputVal) return;

    try {
      const res = await fetch("/api/check-answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: currentDrill.subject,
          answerSpec: p.answerSpec,
          trapValue: p.trapValue,
          input: inputVal,
        }),
      });

      const result: CheckResult = await res.json();

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

  // Equation set-up opened by the learner. Only counts as assistance before the first check.
  const handleSetupRevealed = (probId: string) => {
    if (!currentDrill) return;
    const target = currentDrill.problems.find((p) => p.id === probId);
    if (!target || target.state.lastCheck || target.state.setupRevealedBeforeAnswer) return;
    updateProblem(probId, (p) => ({
      ...p,
      state: { ...p.state, setupRevealedBeforeAnswer: true },
    }));
  };

  // Step-by-step solution opened by the learner before their first correct answer.
  const handleSolutionRevealed = (probId: string) => {
    if (!currentDrill) return;
    const target = currentDrill.problems.find((p) => p.id === probId);
    if (!target || target.state.solutionRevealedBeforeAnswer) return;
    const hasCorrect =
      target.state.score === 1 ||
      Boolean(target.state.attempts?.some((a) => a.verdict === "correct"));
    if (hasCorrect) return;
    updateProblem(probId, (p) => ({
      ...p,
      state: { ...p.state, solutionRevealedBeforeAnswer: true },
    }));
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

    updateProblem(probId, (prob) => ({
      ...prob,
      state: applySkip(prob, {
        durationMs,
        hintsRevealed: hintsCount,
      }),
    }));
  };

  const handleResetProblem = (probId: string) => {
    if (!currentDrill) return;
    timerStateRef.current = resetProblemTimer(timerStateRef.current, probId);
    updateProblem(probId, (p) => ({
      ...p,
      state: {
        userInput: "",
        userCode: p.starterCode || p.codeSnippet || "",
        score: null,
        divergedStep: null,
        mistakes: [],
        mistakeNote: "",
        skipped: false,
        lastCheck: null,
        lastTestReport: null,
        attempts: [],
        hintsRevealed: 0,
        setupRevealedBeforeAnswer: false,
        solutionRevealedBeforeAnswer: false,
        durationMs: 0,
      },
    }));
  };

  const handleResetAll = () => {
    if (!currentDrill) return;
    const ok = window.confirm(`Reset all questions in ${currentDrill.drillId} to start over?`);
    if (!ok) return;

    const updated: DrillDocument = {
      ...currentDrill,
      problems: currentDrill.problems.map((p) => ({
        ...p,
        state: {
          userInput: "",
          userCode: p.starterCode || p.codeSnippet || "",
          score: null,
          divergedStep: null,
          mistakes: [],
          mistakeNote: "",
          skipped: false,
          lastCheck: null,
          lastTestReport: null,
        },
      })),
      sessionSummary: {
        ...currentDrill.sessionSummary,
        score: 0,
        accuracyPct: 0,
        practiceStatus: "Ready",
        mistakeCategories: [],
        divergedStepsSummary: "",
        attemptDate: null,
      },
    };
    setCurrentDrill(updated);
    setCurrentProblemIndex(0);
    setViewMode("quiz");
    triggerAutoSave(updated);
    setStatus({
      text: `Reset ${currentDrill.drillId} to initial state.`,
      type: "pass",
    });
  };

  const handlePrevQuestion = useCallback(() => {
    setCurrentProblemIndex((prev) => (prev > 0 ? prev - 1 : prev));
  }, []);

  const handleNextQuestion = useCallback(() => {
    setCurrentProblemIndex((prev) => {
      const maxIdx = (currentDrill?.problems.length ?? 1) - 1;
      return prev < maxIdx ? prev + 1 : prev;
    });
  }, [currentDrill]);

  const handleSelectQuestion = useCallback(
    (idx: number) => {
      setCurrentProblemIndex(idx);
      if (viewMode !== "quiz") {
        setViewMode("quiz");
      }
    },
    [viewMode]
  );

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT")
      ) {
        return;
      }
      if (viewMode !== "quiz") return;
      if (e.key === "ArrowLeft") {
        handlePrevQuestion();
      } else if (e.key === "ArrowRight") {
        handleNextQuestion();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [viewMode, handlePrevQuestion, handleNextQuestion]);

  return {
    currentDrill,
    setCurrentDrill,
    activeSteps,
    currentProblemIndex,
    viewMode,
    setViewMode,
    isLoadingDrill,
    setIsLoadingDrill,
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
    handleToggleMistakeTag,
    handleSkipProblem,
    handleResetProblem,
    handleResetAll,
    handlePrevQuestion,
    handleNextQuestion,
    handleSelectQuestion,
  };
}
