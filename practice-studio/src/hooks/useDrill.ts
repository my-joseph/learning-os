"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DrillDocument, Problem, CheckResult, TestRunReport, VariantSessionRecord } from "@/types/drill";
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
  isTimestampInCycle,
  sanitizeCheckMessage,
} from "@/lib/reviewGuard";
import {
  applySelfScore,
  isLockedAfterCorrect,
  scoreProblem,
} from "@/lib/scoring";
import {
  createTelemetryTimerState,
  setActiveProblem,
  setVisibility,
  pauseTimer,
  resumeTimer,
  consumeAttempt,
  resetProblemTimer,
  getAttemptElapsedMs,
  TelemetryTimerState,
} from "@/lib/telemetryTimer";
import { labToDrillDocument, type LabDetailResponse } from "@/lib/labModel";
import { stepStudyPosition } from "@/lib/pagination";
import { findProblemIndex, isLabId } from "@/lib/routes";
import { SkipOptions, StatusMessage, ViewMode } from "./types";

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

/** Save updated progress (via the ordered save queue when supplied) and fetch each requested `/api/reveal` part, returning the problem patch. */
export async function executeSaveAndReveal(
  updatedDoc: DrillDocument,
  probId: string,
  parts: RevealPart[],
  fetchFn: typeof fetch = fetch,
  saveFn?: (doc: DrillDocument) => Promise<boolean>
): Promise<Partial<Problem>> {
  try {
    if (saveFn) {
      await saveFn(updatedDoc);
    } else {
      await fetchFn("/api/save-state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedDoc),
      });
    }
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
      }
    } catch {
      // ignore transient reveal error
    }
  }
  return patch;
}

/** Pure transition for recording a PRG test run report, test run history, and canonical score in one atomic update. */
export function computeTestRunTransition(
  currentDrill: DrillDocument,
  probId: string,
  report: TestRunReport,
  _score?: number | null,
  nowIso: string = new Date().toISOString()
): DrillDocument | null {
  const exists = currentDrill.problems.some((p) => p.id === probId);
  if (!exists) return null;
  const runTs = report.ts || nowIso;
  const stampedReport: TestRunReport = { ...report, ts: runTs };
  const allPassed = Boolean(
    stampedReport.allPassed &&
      (typeof stampedReport.totalCount !== "number" || stampedReport.totalCount > 0)
  );
  return {
    ...currentDrill,
    problems: currentDrill.problems.map((p) => {
      if (p.id !== probId) return p;
      const prevRuns = Array.isArray(p.state?.testRuns) ? p.state.testRuns : [];
      const nextRuns = [
        ...prevRuns,
        {
          ts: runTs,
          allPassed,
          passedCount: stampedReport.passedCount,
          totalCount: stampedReport.totalCount,
        },
      ];
      const candidateState = {
        ...p.state,
        lastTestReport: stampedReport,
        testRuns: nextRuns,
        skipped: false,
      };
      const computedScore = scoreProblem(candidateState, {
        isPrg: true,
        ignoreStateScore: true,
      }).score;
      return {
        ...p,
        state: {
          ...candidateState,
          score: computedScore,
        },
      };
    }),
  };
}

/** Pure transition when the learner opens a checkpoint hint before answering correctly in the current cycle. */
export function computeHintRevealTransition(
  currentDrill: DrillDocument,
  probId: string
): DrillDocument | null {
  const target = currentDrill.problems.find((p) => p.id === probId);
  if (!target) return null;
  if (isLockedAfterCorrect(target.state)) return null;
  const cycleStartedAt = target.state.cycleStartedAt;
  const nowIso = new Date().toISOString();
  const revealTs =
    cycleStartedAt && nowIso < cycleStartedAt ? cycleStartedAt : nowIso;
  return {
    ...currentDrill,
    problems: currentDrill.problems.map((p) =>
      p.id === probId
        ? {
            ...p,
            state: {
              ...p.state,
              hintsRevealed: (p.state.hintsRevealed || 0) + 1,
              ...(cycleStartedAt ? { reviewHintRevealedAt: revealTs } : {}),
            },
          }
        : p
    ),
  };
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
  if (rawResult.verdict !== "skipped" && isLockedAfterCorrect(p.state)) return null;

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
  const cycleStartedAt = target.state.cycleStartedAt;
  const alreadyRevealedInCycle = cycleStartedAt
    ? Boolean(
        target.state.reviewSetupRevealedAt &&
          isTimestampInCycle(target.state.reviewSetupRevealedAt, cycleStartedAt)
      )
    : Boolean(target.state.setupRevealedBeforeAnswer);
  const shouldMarkAssisted = !hasSubstantiveAttempt(target.state) && !alreadyRevealedInCycle;
  const nowIso = new Date().toISOString();
  const revealTs =
    cycleStartedAt && nowIso < cycleStartedAt ? cycleStartedAt : nowIso;
  const updatedDoc: DrillDocument = shouldMarkAssisted
    ? {
        ...currentDrill,
        problems: currentDrill.problems.map((p) =>
          p.id === probId
            ? {
                ...p,
                state: {
                  ...p.state,
                  setupRevealedBeforeAnswer: true,
                  ...(cycleStartedAt ? { reviewSetupRevealedAt: revealTs } : {}),
                },
              }
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
  const hasCorrect = isLockedAfterCorrect(target.state);
  const cycleStartedAt = target.state.cycleStartedAt;
  const alreadyRevealedInCycle = cycleStartedAt
    ? Boolean(
        target.state.reviewStepsRevealedAt &&
          isTimestampInCycle(target.state.reviewStepsRevealedAt, cycleStartedAt)
      )
    : Boolean(target.state.solutionRevealedBeforeAnswer);
  const shouldMarkAssisted = !hasCorrect && !alreadyRevealedInCycle;
  const nowIso = new Date().toISOString();
  const revealTs =
    cycleStartedAt && nowIso < cycleStartedAt ? cycleStartedAt : nowIso;
  const updatedDoc: DrillDocument = shouldMarkAssisted
    ? {
        ...currentDrill,
        problems: currentDrill.problems.map((p) =>
          p.id === probId
            ? {
                ...p,
                state: {
                  ...p.state,
                  solutionRevealedBeforeAnswer: true,
                  ...(cycleStartedAt ? { reviewStepsRevealedAt: revealTs } : {}),
                },
              }
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
  now: number,
  opts: SkipOptions = {}
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
  const hintsCount =
    hintsRevealed + (p.state?.hintsRevealed || 0) + (opts.countHint ? 1 : 0);
  const cycleStartedAt = p.state?.cycleStartedAt;
  const nowIso = new Date(now).toISOString();
  const hintRevealTs =
    opts.countHint && cycleStartedAt
      ? nowIso < cycleStartedAt
        ? cycleStartedAt
        : nowIso
      : null;

  const updatedDoc: DrillDocument = {
    ...currentDrill,
    problems: currentDrill.problems.map((prob) =>
      prob.id === probId
        ? {
            ...prob,
            state: {
              ...applySkip(prob, {
                durationMs,
                hintsRevealed: hintsCount,
              }),
              ...(hintRevealTs ? { reviewHintRevealedAt: hintRevealTs } : {}),
            },
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

/** Pure transition for resetting a single problem's state, revealed fields, and timer. */
export function computeResetProblemTransition(
  currentDrill: DrillDocument,
  probId: string,
  timerState: TelemetryTimerState,
  now: number
): {
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
} {
  const nextTimerState = resetProblemTimer(timerState, probId, now);
  const nowIso = new Date(now).toISOString();
  const updatedDoc: DrillDocument = {
    ...currentDrill,
    problems: currentDrill.problems.map((p) =>
      p.id === probId ? resetProblemForRetry(p, nowIso) : p
    ),
  };
  return { updatedDoc, nextTimerState };
}

/** Pure transition for resetting the entire drill, timer state, and status banner. */
export function computeResetAllTransition(
  currentDrill: DrillDocument,
  timerState: TelemetryTimerState,
  isVisible: boolean,
  now: number
): {
  updatedDoc: DrillDocument;
  nextTimerState: TelemetryTimerState;
  firstProblemId: string | null;
  statusMessage: StatusMessage;
} {
  const nowIso = new Date(now).toISOString();
  const updatedDoc = resetDrillForRetry(currentDrill, nowIso);
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
    firstProblemId,
    statusMessage: {
      text: `Reset ${drillLabel} to initial state.`,
      type: "pass",
    },
  };
}

interface UseDrillOptions {
  triggerAutoSave: (doc: DrillDocument) => void;
  saveNow?: (doc?: DrillDocument) => Promise<boolean>;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
  onDrillLoaded?: (doc: DrillDocument) => void;
  onQuestionChange?: (drillId: string, problemId: string) => void;
}

/** Manage active drill loading, problem navigation, telemetry timer, and problem state updates. */
export function useDrill({
  triggerAutoSave,
  saveNow,
  setStatus,
  onDrillLoaded,
  onQuestionChange,
}: UseDrillOptions) {
  const [currentDrill, setCurrentDrillState] = useState<DrillDocument | null>(null);
  const drillRef = useRef<DrillDocument | null>(null);
  const loadSeqRef = useRef<number>(0);
  const [currentProblemIndex, setCurrentProblemIndex] = useState<number>(0);
  const [viewMode, setViewMode] = useState<ViewMode>("quiz");
  const [isLoadingDrill, setIsLoadingDrill] = useState<boolean>(true);
  const [drillNotFound, setDrillNotFound] = useState<boolean>(false);

  const setCurrentDrill: React.Dispatch<React.SetStateAction<DrillDocument | null>> = useCallback(
    (action) => {
      if (typeof action === "function") {
        const next = action(drillRef.current);
        drillRef.current = next;
        setCurrentDrillState(() => next);
      } else {
        drillRef.current = action;
        setCurrentDrillState(action);
      }
    },
    []
  );

  const getLatestDrill = useCallback(() => drillRef.current, []);

  const persistNow = useCallback(
    async (doc: DrillDocument): Promise<boolean> => {
      if (saveNow) return saveNow(doc);
      try {
        const res = await fetch("/api/save-state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(doc),
        });
        return res.ok;
      } catch {
        return false;
      }
    },
    [saveNow]
  );

  /**
   * Apply a problem/drill transition against the latest in-memory document (`drillRef.current`),
   * update React state functionally with zero side effects inside the updater, and enqueue at
   * most one save outside the updater.
   */
  const commitDrillUpdate = useCallback(
    (
      expectedDrillId: string | null,
      compute: (latest: DrillDocument) => DrillDocument | null,
      saveMode: "debounce" | "immediate" | "none" = "debounce"
    ): DrillDocument | null => {
      const latest = drillRef.current;
      if (!latest) return null;
      if (expectedDrillId && latest.drillId !== expectedDrillId) return null;
      const next = compute(latest);
      if (!next || next === latest) return null;
      drillRef.current = next;
      setCurrentDrillState((prev) => {
        if (!prev || prev.drillId !== next.drillId) return prev;
        return next;
      });
      if (saveMode === "debounce") {
        triggerAutoSave(next);
      } else if (saveMode === "immediate") {
        void persistNow(next);
      }
      return next;
    },
    [persistNow, triggerAutoSave]
  );

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

  const handleExampleViewed = useCallback(
    (probId: string, viewedAt: string) => {
      commitDrillUpdate(
        null,
        (prev) => ({
          ...prev,
          problems: prev.problems.map((p) =>
            p.id === probId
              ? {
                  ...p,
                  state: {
                    ...p.state,
                    exampleViewedAt:
                      p.state.exampleViewedAt &&
                      (!p.state.cycleStartedAt ||
                        p.state.exampleViewedAt >= p.state.cycleStartedAt)
                        ? p.state.exampleViewedAt
                        : viewedAt,
                  },
                }
              : p
          ),
        }),
        "none"
      );
    },
    [commitDrillUpdate]
  );

  const handleSimilarProgressSync = useCallback(
    (
      probId: string,
      patch: {
        similarSlots?: string[];
        variantToken?: string;
        variantRecord?: VariantSessionRecord;
      }
    ) => {
      commitDrillUpdate(
        null,
        (prev) => ({
          ...prev,
          problems: prev.problems.map((p) => {
            if (p.id !== probId) return p;
            const nextState = { ...p.state };
            if (Array.isArray(patch.similarSlots)) {
              nextState.similarSlots = patch.similarSlots;
            }
            if (patch.variantToken && patch.variantRecord) {
              nextState.variants = {
                ...(nextState.variants || {}),
                [patch.variantToken]: patch.variantRecord,
              };
            }
            return { ...p, state: nextState };
          }),
        }),
        "none"
      );
    },
    [commitDrillUpdate]
  );

  const handleHintRevealed = useCallback(
    (probId: string) => {
      commitDrillUpdate(
        null,
        (latest) => computeHintRevealTransition(latest, probId),
        "debounce"
      );
    },
    [commitDrillUpdate]
  );

  const loadDrill = useCallback(
    async (id: string, initialQuestionId?: string | null) => {
      const seq = ++loadSeqRef.current;
      setIsLoadingDrill(true);
      setDrillNotFound(false);
      try {
        const endpoint = isLabId(id)
          ? `/api/lab?id=${encodeURIComponent(id)}`
          : `/api/drill?id=${encodeURIComponent(id)}`;
        const res = await fetch(endpoint);
        if (seq !== loadSeqRef.current) return;
        if (res.status === 404 || res.status === 400) {
          setCurrentDrill(null);
          setDrillNotFound(true);
          return;
        }
        if (!res.ok) throw new Error(isLabId(id) ? "Could not load lab" : "Could not load drill");
        const rawPayload = await res.json();
        if (seq !== loadSeqRef.current) return;
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
      } catch (err: unknown) {
        if (seq !== loadSeqRef.current) return;
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `Failed to load ${id}: ${errMsg}`, type: "fail" });
      } finally {
        if (seq === loadSeqRef.current) {
          setIsLoadingDrill(false);
        }
      }
    },
    [commitTimerState, onDrillLoaded, setCurrentDrill, setStatus]
  );

  const updateProblem = useCallback(
    (probId: string, updater: (prob: Problem) => Problem) => {
      commitDrillUpdate(
        null,
        (latest) => ({
          ...latest,
          problems: latest.problems.map((p) => (p.id === probId ? updater(p) : p)),
        }),
        "debounce"
      );
    },
    [commitDrillUpdate]
  );

  const saveAndReveal = useCallback(
    async (
      updatedDoc: DrillDocument,
      probId: string,
      parts: RevealPart[]
    ) => {
      const patch = await executeSaveAndReveal(updatedDoc, probId, parts, fetch, persistNow);
      if (Object.keys(patch).length > 0) {
        commitDrillUpdate(
          updatedDoc.drillId,
          (latest) => mergeRevealedPatchIntoDrill(latest, updatedDoc.drillId, probId, patch),
          "none"
        );
      }
    },
    [commitDrillUpdate, persistNow]
  );

  const handleCheckAnswer = useCallback(
    async (probId: string, inputOverride?: string) => {
      const snap = drillRef.current;
      if (!snap) return;
      const p = snap.problems.find((item) => item.id === probId);
      if (!p) return;
      if (isLockedAfterCorrect(p.state)) return;

      const targetDrillId = snap.drillId;
      const targetSubject = snap.subject;
      const inputVal = (
        inputOverride !== undefined ? inputOverride : p.state.userInput
      ).trim();
      if (!inputVal) return;

      try {
        const res = await fetch("/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId: targetDrillId,
            problemId: p.id,
            subject: targetSubject,
            input: inputVal,
          }),
        });

        const rawResult: CheckResult = await res.json();
        const now = Date.now();
        let computedTransition: ReturnType<typeof computeCheckAnswerTransition> = null;
        const nextDoc = commitDrillUpdate(
          targetDrillId,
          (latest) => {
            const transition = computeCheckAnswerTransition(
              latest,
              probId,
              inputVal,
              rawResult,
              timerStateRef.current,
              now
            );
            computedTransition = transition;
            return transition ? transition.updatedDoc : null;
          },
          "none"
        );
        const applied = computedTransition as ReturnType<typeof computeCheckAnswerTransition>;
        if (!applied || !nextDoc) return;
        if (applied.result.message !== rawResult.message) {
          console.error("[check-answer] raw error:", rawResult.message);
        }

        commitTimerState(applied.nextTimerState, now);
        if (applied.partsToReveal.length > 0) {
          void saveAndReveal(nextDoc, probId, applied.partsToReveal);
        } else {
          triggerAutoSave(nextDoc);
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `SymPy Check error: ${errMsg}`, type: "fail" });
      }
    },
    [commitDrillUpdate, commitTimerState, saveAndReveal, setStatus, triggerAutoSave]
  );

  const handleInputChange = useCallback(
    (probId: string, val: string) => {
      updateProblem(probId, (p) => ({ ...p, state: { ...p.state, userInput: val } }));
    },
    [updateProblem]
  );

  const handleMistakeNoteChange = useCallback(
    (probId: string, note: string) => {
      updateProblem(probId, (p) => ({ ...p, state: { ...p.state, mistakeNote: note } }));
    },
    [updateProblem]
  );

  const handleRevisitNoteChange = useCallback(
    (probId: string, note: string) => {
      updateProblem(probId, (p) => ({ ...p, state: { ...p.state, revisitNote: note } }));
    },
    [updateProblem]
  );

  // Equation set-up opened by the learner. Only counts as assistance before the first substantive check.
  const handleSetupRevealed = useCallback(
    (probId: string) => {
      const latest = drillRef.current;
      if (!latest) return;
      const transition = computeSetupRevealTransition(latest, probId);
      if (!transition) return;
      let docForSave = latest;
      if (transition.shouldMarkAssisted) {
        const nextDoc = commitDrillUpdate(
          latest.drillId,
          (cur) => computeSetupRevealTransition(cur, probId)?.updatedDoc ?? null,
          transition.partsToReveal.length > 0 ? "none" : "debounce"
        );
        if (nextDoc) docForSave = nextDoc;
      }
      if (transition.partsToReveal.length > 0) {
        void saveAndReveal(docForSave, probId, transition.partsToReveal);
      }
    },
    [commitDrillUpdate, saveAndReveal]
  );

  // Step-by-step solution opened by the learner before their first correct answer.
  const handleSolutionRevealed = useCallback(
    (probId: string) => {
      const latest = drillRef.current;
      if (!latest) return;
      const transition = computeSolutionRevealTransition(latest, probId);
      if (!transition) return;
      let docForSave = latest;
      if (transition.shouldMarkAssisted) {
        const nextDoc = commitDrillUpdate(
          latest.drillId,
          (cur) => computeSolutionRevealTransition(cur, probId)?.updatedDoc ?? null,
          transition.partsToReveal.length > 0 ? "none" : "debounce"
        );
        if (nextDoc) docForSave = nextDoc;
      }
      if (transition.partsToReveal.length > 0) {
        void saveAndReveal(docForSave, probId, transition.partsToReveal);
      }
    },
    [commitDrillUpdate, saveAndReveal]
  );

  const handleMarkDivergedStep = useCallback(
    (probId: string, stepIdx: number) => {
      updateProblem(probId, (p) => ({ ...p, state: applyDivergedStep(p, stepIdx) }));
    },
    [updateProblem]
  );

  const handleSetScore = useCallback(
    (probId: string, score: number | null) => {
      updateProblem(probId, (p) => ({
        ...p,
        state: applySelfScore(p.state, score),
      }));
    },
    [updateProblem]
  );

  const handleTestReportChange = useCallback(
    (probId: string, report: TestRunReport, score?: number | null) => {
      commitDrillUpdate(
        null,
        (latest) => computeTestRunTransition(latest, probId, report, score),
        "debounce"
      );
    },
    [commitDrillUpdate]
  );

  const handleToggleMistakeTag = useCallback(
    (probId: string, tagId: string) => {
      updateProblem(probId, (p) => {
        const list = p.state.mistakes || [];
        const next = list.includes(tagId) ? list.filter((t) => t !== tagId) : [...list, tagId];
        return {
          ...p,
          state: { ...p.state, mistakes: next },
        };
      });
    },
    [updateProblem]
  );

  const handleSkipProblem = useCallback(
    (probId: string, opts: SkipOptions = {}) => {
      const now = Date.now();
      let computed: ReturnType<typeof computeSkipProblemTransition> = null;
      const nextDoc = commitDrillUpdate(
        null,
        (latest) => {
          const transition = computeSkipProblemTransition(
            latest,
            probId,
            timerStateRef.current,
            now,
            opts
          );
          computed = transition;
          return transition ? transition.updatedDoc : null;
        },
        "none"
      );
      const applied = computed as ReturnType<typeof computeSkipProblemTransition>;
      if (!applied || !nextDoc) return;
      commitTimerState(applied.nextTimerState, now);
      void saveAndReveal(nextDoc, probId, applied.partsToReveal);
    },
    [commitDrillUpdate, commitTimerState, saveAndReveal]
  );

  const handleResetProblem = useCallback(
    (probId: string) => {
      const now = Date.now();
      let computed: ReturnType<typeof computeResetProblemTransition> | null = null;
      const nextDoc = commitDrillUpdate(
        null,
        (latest) => {
          const transition = computeResetProblemTransition(
            latest,
            probId,
            timerStateRef.current,
            now
          );
          computed = transition;
          return transition.updatedDoc;
        },
        "immediate"
      );
      const applied = computed as ReturnType<typeof computeResetProblemTransition> | null;
      if (!applied || !nextDoc) return;
      commitTimerState(applied.nextTimerState, now);
    },
    [commitDrillUpdate, commitTimerState]
  );

  const handleResetAll = useCallback(async () => {
    const now = Date.now();
    const isVisible = typeof document !== "undefined" ? !document.hidden : true;
    let computed: ReturnType<typeof computeResetAllTransition> | null = null;
    const nextDoc = commitDrillUpdate(
      null,
      (latest) => {
        const transition = computeResetAllTransition(
          latest,
          timerStateRef.current,
          isVisible,
          now
        );
        computed = transition;
        return transition.updatedDoc;
      },
      "none"
    );
    const applied = computed as ReturnType<typeof computeResetAllTransition> | null;
    if (!applied || !nextDoc) return;

    commitTimerState(
      createTelemetryTimerState(
        applied.firstProblemId,
        isVisible,
        timerStateRef.current.paused,
        now
      ),
      now
    );
    setCurrentProblemIndex(0);
    setViewMode("quiz");
    if (applied.firstProblemId) {
      onQuestionChange?.(nextDoc.drillId, applied.firstProblemId);
    }
    setStatus(applied.statusMessage);
    await persistNow(nextDoc);
  }, [commitDrillUpdate, commitTimerState, onQuestionChange, persistNow, setStatus]);

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
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.tagName === "MATH-FIELD" ||
          target.isContentEditable ||
          Boolean(
            target.closest('[role="alertdialog"], [role="dialog"], [role="tablist"]')
          ))
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
    getLatestDrill,
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
    handleSimilarProgressSync,
    handleHintRevealed,
    handleCheckAnswer,
    handleInputChange,
    handleMistakeNoteChange,
    handleRevisitNoteChange,
    handleSetupRevealed,
    handleSolutionRevealed,
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
