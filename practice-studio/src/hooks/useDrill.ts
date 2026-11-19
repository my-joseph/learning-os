"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DrillDocument, Problem, CheckResult, TestRunReport } from "@/types/drill";
import { plainTitle } from "@/lib/titleText";
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
  pauseTimer,
  resumeTimer,
  recordHint,
  consumeAttempt,
  resetProblemTimer,
  getAttemptElapsedMs,
  TelemetryTimerState,
} from "@/lib/telemetryTimer";
import { labToDrillDocument, type LabDetailResponse } from "@/lib/labModel";
import { stepStudyPosition } from "@/lib/pagination";
import { findProblemIndex, isLabId } from "@/lib/routes";
import { StatusMessage, ViewMode } from "./types";

export type RevealPart = "steps" | "display" | "solution";

/** Normalize a freshly loaded drill document with default problem state fields while preserving saved telemetry. */
export function normalizeLoadedDrillDoc(doc: DrillDocument): DrillDocument {
  return {
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
}

/** Merge a revealed problem patch (`steps`, `display`, `solutionCode`) into the active drill document if drillId still matches. */
export function mergeRevealedPatchIntoDrill(
  prev: DrillDocument | null,
  drillId: string,
  probId: string,
  patch: Partial<Problem>
): DrillDocument | null {
  if (!prev || prev.drillId !== drillId || Object.keys(patch).length === 0) {
    return prev;
  }
  return {
    ...prev,
    problems: prev.problems.map((p) => (p.id === probId ? { ...p, ...patch } : p)),
  };
}

/** Save updated progress to `/api/save-state` and fetch each requested `/api/reveal` part, returning the problem patch. */
export async function executeSaveAndReveal(
  updatedDoc: DrillDocument,
  probId: string,
  parts: RevealPart[],
  fetchFn: typeof fetch = fetch
): Promise<Partial<Problem>> {
  try {
    await fetchFn("/api/save-state", {
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
      const res = await fetchFn(
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
  return patch;
}

/** Pure transition for checking an answer: consumes attempt timer, updates problem state, and selects parts to reveal. */
export function computeCheckAnswerTransition(
  currentDrill: DrillDocument,
  probId: string,
  inputVal: string,
  rawResult: CheckResult,
  timerState: TelemetryTimerState,
  now: number
): {
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  result: CheckResult;
  partsToReveal: Array<"steps" | "display">;
} | null {
  const p = currentDrill.problems.find((item) => item.id === probId);
  if (!p) return null;

  const calmMessage = sanitizeCheckMessage(rawResult.verdict, rawResult.message);
  const result: CheckResult =
    calmMessage === rawResult.message
      ? rawResult
      : { ...rawResult, message: calmMessage };

  const { durationMs, hintsRevealed, nextState } = consumeAttempt(
    timerState,
    probId,
    now
  );
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

  const partsToReveal: Array<"steps" | "display"> = [];
  if (isSubstantiveVerdict(result.verdict)) {
    partsToReveal.push("steps");
    if (p.hasSetup && !p.display && !p.plainText) {
      partsToReveal.push("display");
    }
  }

  return {
    updatedDoc,
    nextTimerState: nextState,
    result,
    partsToReveal,
  };
}

/** Pure transition when the learner opens the equation set-up disclosure. */
export function computeSetupRevealTransition(
  currentDrill: DrillDocument,
  probId: string
): {
  updatedDoc: DrillDocument;
  shouldMarkAssisted: boolean;
  partsToReveal: Array<"display">;
} | null {
  const target = currentDrill.problems.find((p) => p.id === probId);
  if (!target) return null;
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
  const partsToReveal: Array<"display"> =
    !target.display && !target.plainText ? ["display"] : [];
  return {
    updatedDoc,
    shouldMarkAssisted,
    partsToReveal,
  };
}

/** Pure transition when the learner opens the step-by-step solution disclosure. */
export function computeSolutionRevealTransition(
  currentDrill: DrillDocument,
  probId: string
): {
  updatedDoc: DrillDocument;
  shouldMarkAssisted: boolean;
  partsToReveal: Array<"steps">;
} | null {
  const target = currentDrill.problems.find((p) => p.id === probId);
  if (!target) return null;
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
  const partsToReveal: Array<"steps"> =
    !target.steps || target.steps.length === 0 ? ["steps"] : [];
  return {
    updatedDoc,
    shouldMarkAssisted,
    partsToReveal,
  };
}

/** Pure transition for skipping a problem: consumes attempt timer, applies skip state, and selects parts to reveal. */
export function computeSkipProblemTransition(
  currentDrill: DrillDocument,
  probId: string,
  timerState: TelemetryTimerState,
  now: number
): {
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  partsToReveal: Array<"steps" | "display">;
} | null {
  const p = currentDrill.problems.find((item) => item.id === probId);
  if (!p) return null;

  const { durationMs, hintsRevealed, nextState } = consumeAttempt(
    timerState,
    probId,
    now
  );
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

  const partsToReveal: Array<"steps" | "display"> = ["steps"];
  if (p.hasSetup && !p.display && !p.plainText) {
    partsToReveal.push("display");
  }

  return {
    updatedDoc,
    nextTimerState: nextState,
    partsToReveal,
  };
}

/** Pure transition for resetting a single problem's state, revealed fields, active step highlight, and timer. */
export function computeResetProblemTransition(
  currentDrill: DrillDocument,
  probId: string,
  timerState: TelemetryTimerState,
  activeSteps: { [probId: string]: number | null },
  now: number
): {
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  nextActiveSteps: { [probId: string]: number | null };
} {
  const nextTimerState = resetProblemTimer(timerState, probId, now);
  const nextActiveSteps = { ...activeSteps, [probId]: null };
  const updatedDoc: DrillDocument = {
    ...currentDrill,
    problems: currentDrill.problems.map((p) =>
      p.id === probId ? resetProblemForRetry(p) : p
    ),
  };
  return {
    updatedDoc,
    nextTimerState,
    nextActiveSteps,
  };
}

/** Pure transition for resetting the entire drill, timer state, active steps, and status banner. */
export function computeResetAllTransition(
  currentDrill: DrillDocument,
  timerState: TelemetryTimerState,
  isVisible: boolean,
  now: number
): {
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  nextActiveSteps: { [probId: string]: number | null };
  firstProblemId: string | null;
  statusMessage: StatusMessage;
} {
  const updatedDoc = resetDrillForRetry(currentDrill);
  const firstProblemId = updatedDoc.problems[0]?.id ?? null;
  const nextTimerState = createTelemetryTimerState(
    firstProblemId,
    isVisible,
    timerState.paused,
    now
  );
  const drillLabel =
    plainTitle(currentDrill.unitTitle) || currentDrill.unitCode || currentDrill.drillId;
  return {
    updatedDoc,
    nextTimerState,
    nextActiveSteps: {},
    firstProblemId,
    statusMessage: {
      text: `Reset ${drillLabel} to initial state.`,
      type: "pass",
    },
  };
}

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
  const [timerState, setTimerState] = useState<TelemetryTimerState>(() => timerStateRef.current);
  const [timerNow, setTimerNow] = useState<number>(() => Date.now());

  const commitTimerState = useCallback(
    (next: TelemetryTimerState, now: number = Date.now()) => {
      timerStateRef.current = next;
      setTimerState(next);
      setTimerNow(now);
    },
    []
  );

  const activeProbId =
    viewMode === "quiz" && currentDrill && currentDrill.problems.length > 0
      ? currentDrill.problems[currentProblemIndex]?.id ?? null
      : null;

  useEffect(() => {
    if (!currentDrill || !currentDrill.problems.length) return;
    if (timerStateRef.current.activeProblemId === activeProbId) return;
    const now = Date.now();
    commitTimerState(setActiveProblem(timerStateRef.current, activeProbId, now), now);
  }, [currentDrill, activeProbId, commitTimerState]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      const isVisible = !document.hidden;
      const now = Date.now();
      commitTimerState(setVisibility(timerStateRef.current, isVisible, now), now);
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [commitTimerState]);

  const isTimerRunning =
    Boolean(currentDrill) &&
    viewMode === "quiz" &&
    timerState.activeProblemId !== null &&
    timerState.isDocumentVisible &&
    !timerState.paused;

  useEffect(() => {
    if (!isTimerRunning || !activeProbId) return;
    let lastWholeSec = Math.floor(
      getAttemptElapsedMs(timerStateRef.current, activeProbId, Date.now()) / 1000
    );
    const id = window.setInterval(() => {
      const now = Date.now();
      const wholeSec = Math.floor(
        getAttemptElapsedMs(timerStateRef.current, activeProbId, now) / 1000
      );
      if (wholeSec !== lastWholeSec) {
        lastWholeSec = wholeSec;
        setTimerNow(now);
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [isTimerRunning, activeProbId]);

  const pausedBeforeVariantRef = useRef<boolean | null>(null);
  const handleToggleTimerPause = useCallback(() => {
    const now = Date.now();
    const next = timerStateRef.current.paused
      ? resumeTimer(timerStateRef.current, now)
      : pauseTimer(timerStateRef.current, now);
    commitTimerState(next, now);
  }, [commitTimerState]);

  const handleVariantModeChange = useCallback(
    (inVariantMode: boolean) => {
      const now = Date.now();
      if (inVariantMode) {
        if (pausedBeforeVariantRef.current === null) {
          pausedBeforeVariantRef.current = timerStateRef.current.paused;
        }
        if (!timerStateRef.current.paused) {
          commitTimerState(pauseTimer(timerStateRef.current, now), now);
        }
      } else if (pausedBeforeVariantRef.current !== null) {
        const wasPaused = pausedBeforeVariantRef.current;
        pausedBeforeVariantRef.current = null;
        if (!wasPaused && timerStateRef.current.paused) {
          commitTimerState(resumeTimer(timerStateRef.current, now), now);
        }
      }
    },
    [commitTimerState]
  );

  const handleExampleViewed = useCallback((probId: string, viewedAt: string) => {
    setCurrentDrill((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        problems: prev.problems.map((p) =>
          p.id === probId
            ? {
                ...p,
                state: {
                  ...p.state,
                  exampleViewedAt: p.state.exampleViewedAt || viewedAt,
                },
              }
            : p
        ),
      };
    });
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
        const normalizedDoc = normalizeLoadedDrillDoc(doc);
        const targetIndex = findProblemIndex(normalizedDoc.problems, initialQuestionId);
        const initialProbId = normalizedDoc.problems[targetIndex]?.id ?? null;
        const now = Date.now();
        const isVisible = typeof document !== "undefined" ? !document.hidden : true;
        commitTimerState(
          createTelemetryTimerState(initialProbId, isVisible, timerStateRef.current.paused, now),
          now
        );
        setCurrentDrill(normalizedDoc);
        setCurrentProblemIndex(targetIndex);
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
    [commitTimerState, onDrillLoaded, setStatus]
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
      parts: RevealPart[]
    ) => {
      const patch = await executeSaveAndReveal(updatedDoc, probId, parts);
      if (Object.keys(patch).length > 0) {
        setCurrentDrill((prev) =>
          mergeRevealedPatchIntoDrill(prev, updatedDoc.drillId, probId, patch)
        );
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
      const now = Date.now();
      const transition = computeCheckAnswerTransition(
        currentDrill,
        probId,
        inputVal,
        rawResult,
        timerStateRef.current,
        now
      );
      if (!transition) return;
      if (transition.result.message !== rawResult.message) {
        console.error("[check-answer] raw error:", rawResult.message);
      }

      commitTimerState(transition.nextTimerState, now);
      setCurrentDrill(transition.updatedDoc);
      triggerAutoSave(transition.updatedDoc);
      if (transition.partsToReveal.length > 0) {
        void saveAndReveal(transition.updatedDoc, probId, transition.partsToReveal);
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
    const transition = computeSetupRevealTransition(currentDrill, probId);
    if (!transition) return;
    if (transition.shouldMarkAssisted) {
      setCurrentDrill(transition.updatedDoc);
      triggerAutoSave(transition.updatedDoc);
    }
    if (transition.partsToReveal.length > 0) {
      void saveAndReveal(transition.updatedDoc, probId, transition.partsToReveal);
    }
  };

  // Step-by-step solution opened by the learner before their first correct answer.
  const handleSolutionRevealed = (probId: string) => {
    if (!currentDrill) return;
    const transition = computeSolutionRevealTransition(currentDrill, probId);
    if (!transition) return;
    if (transition.shouldMarkAssisted) {
      setCurrentDrill(transition.updatedDoc);
      triggerAutoSave(transition.updatedDoc);
    }
    if (transition.partsToReveal.length > 0) {
      void saveAndReveal(transition.updatedDoc, probId, transition.partsToReveal);
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
    const now = Date.now();
    const transition = computeSkipProblemTransition(
      currentDrill,
      probId,
      timerStateRef.current,
      now
    );
    if (!transition) return;
    commitTimerState(transition.nextTimerState, now);
    setCurrentDrill(transition.updatedDoc);
    triggerAutoSave(transition.updatedDoc);
    void saveAndReveal(transition.updatedDoc, probId, transition.partsToReveal);
  };

  const handleResetProblem = (probId: string) => {
    if (!currentDrill) return;
    const now = Date.now();
    const transition = computeResetProblemTransition(
      currentDrill,
      probId,
      timerStateRef.current,
      activeSteps,
      now
    );
    commitTimerState(transition.nextTimerState, now);
    setActiveSteps(transition.nextActiveSteps);
    setCurrentDrill(transition.updatedDoc);
    triggerAutoSave(transition.updatedDoc);
  };

  const handleResetAll = () => {
    if (!currentDrill) return;

    const now = Date.now();
    const isVisible = typeof document !== "undefined" ? !document.hidden : true;
    const transition = computeResetAllTransition(
      currentDrill,
      timerStateRef.current,
      isVisible,
      now
    );
    commitTimerState(
      createTelemetryTimerState(
        transition.firstProblemId,
        isVisible,
        timerStateRef.current.paused,
        now
      ),
      now
    );
    setActiveSteps({});
    setCurrentDrill(transition.updatedDoc);
    setCurrentProblemIndex(0);
    setViewMode("quiz");
    triggerAutoSave(transition.updatedDoc);
    if (transition.firstProblemId) {
      onQuestionChange?.(transition.updatedDoc.drillId, transition.firstProblemId);
    }
    setStatus(transition.statusMessage);
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
          target.tagName === "MATH-FIELD" ||
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
      } else if (
        !e.repeat &&
        e.key.toLowerCase() === "p" &&
        viewMode === "quiz" &&
        Boolean(currentDrill)
      ) {
        e.preventDefault();
        handleToggleTimerPause();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlePrevQuestion, handleNextQuestion, handleToggleTimerPause, viewMode, currentDrill]);

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
    timerState,
    timerNow,
    handleToggleTimerPause,
    handleVariantModeChange,
    handleExampleViewed,
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
