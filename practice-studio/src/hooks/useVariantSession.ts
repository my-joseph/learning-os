"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  isSubstantiveVerdict,
  isWrongAttemptVerdict,
  sanitizeCheckMessage,
} from "@/lib/reviewGuard";
import {
  AttemptRecord,
  CheckResult,
  Problem,
  RedactedVariant,
  Step,
  WorkedExampleVariant,
} from "@/types/drill";

export type VariantWorkspaceMode = "original" | "similar" | "example";

export interface ActiveSimilarSession {
  token: string;
  index: number;
  total: number;
  remainingCount: number;
  problem: Problem;
}

interface ActiveVariantApiResponse {
  active?: {
    token: string;
    index: number;
    total: number;
    remainingCount: number;
    variant: RedactedVariant;
    session: {
      attempts: AttemptRecord[];
      hintsRevealed: number;
      setupRevealed: boolean;
      stepsRevealed: boolean;
      durationMs: number;
      servedAt: string;
    };
    revealed?: {
      display?: string;
      plainText?: string;
      steps?: Step[];
      answerDisplay?: string;
      answerPlain?: string;
    };
  } | null;
  example?: {
    token: string;
    variant: WorkedExampleVariant;
  } | null;
  total?: number;
  remainingCount?: number;
  clusterWrongAttempts?: number;
  exampleViewedAt?: string | null;
}

function buildSimilarProblem(
  variant: RedactedVariant,
  session?: {
    attempts?: AttemptRecord[];
    hintsRevealed?: number;
    setupRevealed?: boolean;
    stepsRevealed?: boolean;
    durationMs?: number;
  },
  revealed?: {
    display?: string;
    plainText?: string;
    steps?: Step[];
    answerDisplay?: string;
    answerPlain?: string;
  }
): Problem {
  const attempts = Array.isArray(session?.attempts) ? session!.attempts : [];
  const lastAttempt = attempts.length > 0 ? attempts[attempts.length - 1] : null;
  const restoredLastCheck: CheckResult | null = lastAttempt
    ? {
        verdict: lastAttempt.verdict as CheckResult["verdict"],
        message: lastAttempt.verdict === "correct" ? "Correct." : "",
        components: [],
        diagnostics: [],
      }
    : null;
  const restoredScore =
    lastAttempt?.verdict === "correct"
      ? 1
      : lastAttempt?.verdict === "incorrect"
      ? 0
      : null;

  return {
    id: variant.token,
    templateKey: "",
    level: variant.level,
    levelLabel: variant.levelLabel || `Level ${variant.level}`,
    category: variant.category || "",
    context: variant.context,
    prompt: variant.prompt,
    figure: variant.figure,
    visual: variant.visual,
    answerSpec: variant.answerSpec,
    inputHint: variant.inputHint,
    placeholder: variant.placeholder,
    checkpointHint: variant.checkpointHint || "",
    hasSetup: variant.hasSetup,
    ...(revealed?.display !== undefined ? { display: revealed.display } : {}),
    ...(revealed?.plainText !== undefined ? { plainText: revealed.plainText } : {}),
    ...(Array.isArray(revealed?.steps) ? { steps: revealed.steps } : {}),
    ...(revealed?.answerDisplay !== undefined ? { answerDisplay: revealed.answerDisplay } : {}),
    ...(revealed?.answerPlain !== undefined ? { answerPlain: revealed.answerPlain } : {}),
    state: {
      userInput: lastAttempt?.input || "",
      score: restoredScore,
      divergedStep: null,
      mistakes: [],
      lastCheck: restoredLastCheck,
      attempts,
      hintsRevealed: session?.hintsRevealed || 0,
      setupRevealedBeforeAnswer: Boolean(session?.setupRevealed),
      solutionRevealedBeforeAnswer: Boolean(session?.stepsRevealed),
      durationMs: session?.durationMs || 0,
    },
  };
}

function syncSimilarUrlParam(enabled: boolean, isReviewSession: boolean) {
  if (typeof window === "undefined" || isReviewSession) return;
  try {
    const url = new URL(window.location.href);
    const hasParam = url.searchParams.has("similar");
    if (enabled && !hasParam) {
      url.searchParams.set("similar", "1");
      window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    } else if (!enabled && hasParam) {
      url.searchParams.delete("similar");
      window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    }
  } catch {
    // ignore in non-browser / synthetic test environments
  }
}

function hasSimilarUrlParam(isReviewSession: boolean): boolean {
  if (typeof window === "undefined" || isReviewSession) return false;
  try {
    return new URLSearchParams(window.location.search).get("similar") === "1";
  } catch {
    return false;
  }
}

export interface UseVariantSessionOptions {
  drillId?: string;
  problem: Problem;
  questionNumber: number;
  isReviewSession?: boolean;
  onBeforeFetchVariant?: () => Promise<void>;
  onExampleViewed?: (viewedAt: string) => void;
  onModeSwap?: (nextMode: VariantWorkspaceMode, opts?: { selectOriginal?: boolean }) => void;
}

/**
 * Manages the swap-in-place variant session for one Math question:
 * `mode: "original" | "similar" | "example"`, active similar question, worked example,
 * server restore (`?mode=active` only when needed — zero-leak in state [A]), per-variant
 * timer, `?similar=1` URL sync, and `aria-live` announcements.
 */
export function useVariantSession({
  drillId,
  problem,
  questionNumber,
  isReviewSession = false,
  onBeforeFetchVariant,
  onExampleViewed,
  onModeSwap,
}: UseVariantSessionOptions) {
  const [mode, setMode] = useState<VariantWorkspaceMode>("original");
  const [activeSimilar, setActiveSimilar] = useState<ActiveSimilarSession | null>(null);
  const [example, setExample] = useState<WorkedExampleVariant | null>(null);
  const [exampleViewedAt, setExampleViewedAt] = useState<string | null>(
    problem.state.exampleViewedAt ?? null
  );
  const [remainingCount, setRemainingCount] = useState<number | null>(null);
  const [serverVariantWrongs, setServerVariantWrongs] = useState<number>(() => {
    let count = 0;
    if (problem.state.variants && typeof problem.state.variants === "object") {
      for (const rec of Object.values(problem.state.variants)) {
        if (!rec?.attempts) continue;
        for (const a of rec.attempts) {
          if (isWrongAttemptVerdict(a?.verdict)) count += 1;
        }
      }
    }
    return count;
  });
  const [loadingAction, setLoadingAction] = useState<"try" | "example" | null>(null);
  const [loadingSteps, setLoadingSteps] = useState(false);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const [hasUnfinishedActiveOnServer, setHasUnfinishedActiveOnServer] = useState<boolean>(
    Boolean(problem.state.activeVariant)
  );

  // Per-similar-question timer (separate from Q_N's timer)
  const [similarBaseMs, setSimilarBaseMs] = useState(0);
  const [similarElapsedMs, setSimilarElapsedMs] = useState(0);
  const [isSimilarPaused, setIsSimilarPaused] = useState(false);
  const similarTickStartRef = useRef<number | null>(null);
  const onModeSwapRef = useRef(onModeSwap);
  onModeSwapRef.current = onModeSwap;
  const onExampleViewedRef = useRef(onExampleViewed);
  onExampleViewedRef.current = onExampleViewed;

  // Reset local state when switching to a different question, and restore ONLY if
  // `?similar=1` is in the URL or server progress already recorded an activeVariant / exampleViewedAt.
  useEffect(() => {
    setMode("original");
    setActiveSimilar(null);
    setExample(null);
    setExampleViewedAt(problem.state.exampleViewedAt ?? null);
    setRemainingCount(null);
    setLoadingAction(null);
    setLoadingSteps(false);
    setActiveStep(null);
    setSimilarBaseMs(0);
    setSimilarElapsedMs(0);
    setIsSimilarPaused(false);
    similarTickStartRef.current = null;
    setHasUnfinishedActiveOnServer(Boolean(problem.state.activeVariant));

    let initialVariantWrongs = 0;
    if (problem.state.variants && typeof problem.state.variants === "object") {
      for (const rec of Object.values(problem.state.variants)) {
        if (!rec?.attempts) continue;
        for (const a of rec.attempts) {
          if (isWrongAttemptVerdict(a?.verdict)) initialVariantWrongs += 1;
        }
      }
    }
    setServerVariantWrongs(initialVariantWrongs);

    const wantsSimilarFromUrl = hasSimilarUrlParam(isReviewSession);
    const shouldRestore =
      Boolean(drillId) &&
      (wantsSimilarFromUrl ||
        Boolean(problem.state.activeVariant) ||
        Boolean(problem.state.exampleViewedAt));

    if (!shouldRestore || !drillId) {
      return;
    }

    let cancelled = false;
    const qs = new URLSearchParams({
      drillId,
      qid: problem.id,
      mode: "active",
    });

    fetch(`/api/variant?${qs.toString()}`, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) return null;
        return (await res.json()) as ActiveVariantApiResponse;
      })
      .then((data) => {
        if (cancelled || !data) return;
        if (typeof data.remainingCount === "number") {
          setRemainingCount(data.remainingCount);
        }
        if (data.exampleViewedAt) {
          setExampleViewedAt(data.exampleViewedAt);
        }
        if (data.example?.variant) {
          setExample(data.example.variant);
        }
        if (data.active?.variant) {
          const restoredProb = buildSimilarProblem(
            data.active.variant,
            data.active.session,
            data.active.revealed
          );
          setActiveSimilar({
            token: data.active.token,
            index: data.active.index,
            total: data.active.total,
            remainingCount: data.active.remainingCount,
            problem: restoredProb,
          });
          setSimilarBaseMs(data.active.session.durationMs || 0);
          setSimilarElapsedMs(0);
          const alreadySolved = restoredProb.state.lastCheck?.verdict === "correct";
          setHasUnfinishedActiveOnServer(!alreadySolved);
          if (wantsSimilarFromUrl) {
            setMode("similar");
            setAnnouncement(
              `Similar question ${data.active.index} of ${data.active.total}`
            );
            onModeSwapRef.current?.("similar");
          }
        } else {
          setHasUnfinishedActiveOnServer(false);
          if (wantsSimilarFromUrl) {
            syncSimilarUrlParam(false, isReviewSession);
          }
        }
      })
      .catch(() => {
        // Non-blocking restore
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drillId, problem.id]);

  // Run per-similar-question timer only while in `similar` mode and unpaused
  useEffect(() => {
    if (mode !== "similar" || isSimilarPaused) {
      if (similarTickStartRef.current !== null) {
        const delta = Math.max(0, Date.now() - similarTickStartRef.current);
        similarTickStartRef.current = null;
        setSimilarElapsedMs((prev) => Math.min(600_000, prev + delta));
      }
      return;
    }

    similarTickStartRef.current = Date.now();
    const id = window.setInterval(() => {
      if (document.hidden) {
        if (similarTickStartRef.current !== null) {
          const delta = Math.max(0, Date.now() - similarTickStartRef.current);
          similarTickStartRef.current = null;
          setSimilarElapsedMs((prev) => Math.min(600_000, prev + delta));
        }
        return;
      }
      if (similarTickStartRef.current === null) {
        similarTickStartRef.current = Date.now();
        return;
      }
      const now = Date.now();
      const delta = now - similarTickStartRef.current;
      similarTickStartRef.current = now;
      setSimilarElapsedMs((prev) => Math.min(600_000, prev + delta));
    }, 500);

    return () => {
      window.clearInterval(id);
      if (similarTickStartRef.current !== null) {
        const delta = Math.max(0, Date.now() - similarTickStartRef.current);
        similarTickStartRef.current = null;
        setSimilarElapsedMs((prev) => Math.min(600_000, prev + delta));
      }
    };
  }, [mode, isSimilarPaused]);

  const enterMode = useCallback(
    (
      nextMode: VariantWorkspaceMode,
      nextAnnouncement: string,
      opts?: { selectOriginal?: boolean }
    ) => {
      setMode(nextMode);
      setAnnouncement(nextAnnouncement);
      syncSimilarUrlParam(nextMode === "similar", isReviewSession);
      onModeSwapRef.current?.(nextMode, opts);
    },
    [isReviewSession]
  );

  const openSimilar = useCallback(async () => {
    if (!drillId || loadingAction) return;

    // If an unfinished similar question is already loaded in memory, resume it directly.
    if (activeSimilar && activeSimilar.problem.state.lastCheck?.verdict !== "correct") {
      enterMode(
        "similar",
        `Similar question ${activeSimilar.index} of ${activeSimilar.total}`
      );
      return;
    }

    setLoadingAction("try");
    try {
      if (onBeforeFetchVariant) {
        await onBeforeFetchVariant();
      }

      // If the server already has an unfinished active variant, restore it via mode=active.
      if (hasUnfinishedActiveOnServer) {
        const activeQs = new URLSearchParams({
          drillId,
          qid: problem.id,
          mode: "active",
        });
        const activeRes = await fetch(`/api/variant?${activeQs.toString()}`, {
          cache: "no-store",
        });
        if (activeRes.ok) {
          const activeData = (await activeRes.json()) as ActiveVariantApiResponse;
          if (typeof activeData.remainingCount === "number") {
            setRemainingCount(activeData.remainingCount);
          }
          if (activeData.active?.variant) {
            const restoredProb = buildSimilarProblem(
              activeData.active.variant,
              activeData.active.session,
              activeData.active.revealed
            );
            setActiveSimilar({
              token: activeData.active.token,
              index: activeData.active.index,
              total: activeData.active.total,
              remainingCount: activeData.active.remainingCount,
              problem: restoredProb,
            });
            setSimilarBaseMs(activeData.active.session.durationMs || 0);
            setSimilarElapsedMs(0);
            setActiveStep(null);
            enterMode(
              "similar",
              `Similar question ${activeData.active.index} of ${activeData.active.total}`
            );
            return;
          }
        }
        setHasUnfinishedActiveOnServer(false);
      }

      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        mode: "try",
      });
      const res = await fetch(`/api/variant?${qs.toString()}`, { cache: "no-store" });
      if (!res.ok) {
        if (res.status === 404) {
          setRemainingCount(0);
        }
        return;
      }
      const data = (await res.json()) as {
        token: string;
        index: number;
        total: number;
        remainingCount: number;
        variant: RedactedVariant;
      };
      if (!data.variant) return;

      const freshProb = buildSimilarProblem(data.variant);
      setActiveSimilar({
        token: data.token,
        index: data.index,
        total: data.total,
        remainingCount: data.remainingCount,
        problem: freshProb,
      });
      setRemainingCount(data.remainingCount);
      setHasUnfinishedActiveOnServer(true);
      setSimilarBaseMs(0);
      setSimilarElapsedMs(0);
      setIsSimilarPaused(false);
      setActiveStep(null);
      enterMode("similar", `Similar question ${data.index} of ${data.total}`);
    } finally {
      setLoadingAction(null);
    }
  }, [
    activeSimilar,
    drillId,
    enterMode,
    hasUnfinishedActiveOnServer,
    loadingAction,
    onBeforeFetchVariant,
    problem.id,
  ]);

  const loadAnotherSimilar = useCallback(async () => {
    if (!drillId || loadingAction) return;
    setLoadingAction("try");
    try {
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        mode: "try",
      });
      const res = await fetch(`/api/variant?${qs.toString()}`, { cache: "no-store" });
      if (!res.ok) {
        if (res.status === 404) {
          setRemainingCount(0);
        }
        return;
      }
      const data = (await res.json()) as {
        token: string;
        index: number;
        total: number;
        remainingCount: number;
        variant: RedactedVariant;
      };
      if (!data.variant) return;

      const freshProb = buildSimilarProblem(data.variant);
      setActiveSimilar({
        token: data.token,
        index: data.index,
        total: data.total,
        remainingCount: data.remainingCount,
        problem: freshProb,
      });
      setRemainingCount(data.remainingCount);
      setHasUnfinishedActiveOnServer(true);
      setSimilarBaseMs(0);
      setSimilarElapsedMs(0);
      setIsSimilarPaused(false);
      setActiveStep(null);
      enterMode("similar", `Similar question ${data.index} of ${data.total}`);
    } finally {
      setLoadingAction(null);
    }
  }, [drillId, enterMode, loadingAction, problem.id]);

  const openWorkedExample = useCallback(async () => {
    if (!drillId || loadingAction) return;
    if (example) {
      enterMode("example", `Worked example for Question ${questionNumber}`);
      return;
    }
    setLoadingAction("example");
    try {
      if (onBeforeFetchVariant) {
        await onBeforeFetchVariant();
      }
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        mode: "example",
      });
      const res = await fetch(`/api/variant?${qs.toString()}`, { cache: "no-store" });
      if (!res.ok) return;
      const data = (await res.json()) as {
        token: string;
        variant: WorkedExampleVariant;
        exampleViewedAt?: string;
        remainingCount?: number;
      };
      if (!data.variant) return;

      setExample(data.variant);
      const viewedTs = data.exampleViewedAt || new Date().toISOString();
      setExampleViewedAt(viewedTs);
      onExampleViewedRef.current?.(viewedTs);
      if (typeof data.remainingCount === "number") {
        setRemainingCount(data.remainingCount);
      }
      enterMode("example", `Worked example for Question ${questionNumber}`);
    } finally {
      setLoadingAction(null);
    }
  }, [drillId, enterMode, example, loadingAction, onBeforeFetchVariant, problem.id, questionNumber]);

  const backToOriginal = useCallback(
    (opts?: { selectOriginal?: boolean; markSimilarDone?: boolean }) => {
      if (opts?.markSimilarDone && drillId && activeSimilar) {
        setHasUnfinishedActiveOnServer(false);
        void fetch("/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId,
            qid: problem.id,
            variantToken: activeSimilar.token,
            action: "deactivate",
          }),
        }).catch(() => {
          // non-blocking
        });
      }
      enterMode("original", `Back to Question ${questionNumber}`, {
        selectOriginal: opts?.selectOriginal ?? true,
      });
    },
    [activeSimilar, drillId, enterMode, problem.id, questionNumber]
  );

  const handleSimilarInputChange = useCallback((val: string) => {
    setActiveSimilar((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        problem: {
          ...prev.problem,
          state: {
            ...prev.problem.state,
            userInput: val,
          },
        },
      };
    });
  }, []);

  const handleSimilarCheckAnswer = useCallback(
    async (inputOverride?: string) => {
      if (!drillId || !activeSimilar) return;
      const resolved = (
        inputOverride !== undefined ? inputOverride : activeSimilar.problem.state.userInput
      ).trim();
      if (!resolved) return;

      const attemptElapsed =
        similarElapsedMs +
        (similarTickStartRef.current !== null
          ? Math.max(0, Date.now() - similarTickStartRef.current)
          : 0);

      try {
        const res = await fetch("/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId,
            qid: problem.id,
            variantToken: activeSimilar.token,
            input: resolved,
            durationMs: attemptElapsed,
          }),
        });
        const raw = (await res.json()) as CheckResult;
        const calmMsg = sanitizeCheckMessage(raw.verdict, raw.message);
        const checked: CheckResult =
          calmMsg === raw.message ? raw : { ...raw, message: calmMsg };

        const nextAttempt: AttemptRecord = {
          input: resolved,
          ts: new Date().toISOString(),
          verdict: checked.verdict,
          kind: "variant",
        };

        if (isWrongAttemptVerdict(checked.verdict)) {
          setServerVariantWrongs((prev) => prev + 1);
        }
        if (checked.verdict === "correct") {
          setHasUnfinishedActiveOnServer(false);
        }

        setSimilarBaseMs((prev) => prev + attemptElapsed);
        setSimilarElapsedMs(0);
        if (similarTickStartRef.current !== null) {
          similarTickStartRef.current = Date.now();
        }

        setActiveSimilar((prev) => {
          if (!prev) return prev;
          const prevAttempts = prev.problem.state.attempts || [];
          const nextScore =
            checked.verdict === "correct"
              ? 1
              : checked.verdict === "incorrect"
              ? 0
              : checked.verdict === "partial" || checked.verdict === "equivalent_not_in_form"
              ? 0.5
              : prev.problem.state.score;
          return {
            ...prev,
            problem: {
              ...prev.problem,
              state: {
                ...prev.problem.state,
                userInput: resolved,
                score: nextScore,
                lastCheck: checked,
                attempts: [...prevAttempts, nextAttempt],
                durationMs: (prev.problem.state.durationMs || 0) + attemptElapsed,
              },
            },
          };
        });
      } catch {
        setActiveSimilar((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            problem: {
              ...prev.problem,
              state: {
                ...prev.problem.state,
                lastCheck: {
                  verdict: "invalid input",
                  message: "Couldn't check that answer right now. Please try again.",
                  components: [],
                  diagnostics: [],
                },
              },
            },
          };
        });
      }
    },
    [activeSimilar, drillId, problem.id, similarElapsedMs]
  );

  const handleSimilarHintRevealed = useCallback(() => {
    if (!drillId || !activeSimilar) return;
    setActiveSimilar((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        problem: {
          ...prev.problem,
          state: {
            ...prev.problem.state,
            hintsRevealed: (prev.problem.state.hintsRevealed || 0) + 1,
          },
        },
      };
    });
    void fetch("/api/variant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        drillId,
        qid: problem.id,
        variantToken: activeSimilar.token,
        action: "hint",
      }),
    }).catch(() => {
      // non-blocking
    });
  }, [activeSimilar, drillId, problem.id]);

  const handleSimilarSetupRevealed = useCallback(async () => {
    if (!drillId || !activeSimilar) return;
    setActiveSimilar((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        problem: {
          ...prev.problem,
          state: {
            ...prev.problem.state,
            setupRevealedBeforeAnswer: true,
          },
        },
      };
    });
    if (activeSimilar.problem.display || activeSimilar.problem.plainText) return;
    try {
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        variantToken: activeSimilar.token,
        part: "display",
      });
      const res = await fetch(`/api/reveal?${qs.toString()}`);
      if (!res.ok) return;
      const data = (await res.json()) as { display?: string; plainText?: string };
      setActiveSimilar((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          problem: {
            ...prev.problem,
            ...(typeof data.display === "string" ? { display: data.display } : {}),
            ...(typeof data.plainText === "string" ? { plainText: data.plainText } : {}),
          },
        };
      });
    } catch {
      // ignore transient error
    }
  }, [activeSimilar, drillId, problem.id]);

  const handleSimilarSolutionRevealed = useCallback(async () => {
    if (!drillId || !activeSimilar) return;
    const hasSubstantive = (activeSimilar.problem.state.attempts || []).some((a) =>
      isSubstantiveVerdict(a.verdict)
    );
    setActiveSimilar((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        problem: {
          ...prev.problem,
          state: {
            ...prev.problem.state,
            solutionRevealedBeforeAnswer: true,
          },
        },
      };
    });
    if (activeSimilar.problem.steps && activeSimilar.problem.steps.length > 0) return;
    setLoadingSteps(true);
    try {
      if (!hasSubstantive) {
        await fetch("/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId,
            qid: problem.id,
            variantToken: activeSimilar.token,
            action: "reveal-steps",
          }),
        });
      }
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        variantToken: activeSimilar.token,
        part: "steps",
      });
      const res = await fetch(`/api/reveal?${qs.toString()}`);
      if (!res.ok) return;
      const data = (await res.json()) as {
        steps?: Step[];
        answerDisplay?: string;
        answerPlain?: string;
      };
      setActiveSimilar((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          problem: {
            ...prev.problem,
            steps: Array.isArray(data.steps) ? data.steps : [],
            answerDisplay: data.answerDisplay || data.answerPlain || "",
            answerPlain: data.answerPlain || "",
          },
        };
      });
    } finally {
      setLoadingSteps(false);
    }
  }, [activeSimilar, drillId, problem.id]);

  const handleSimilarReset = useCallback(() => {
    if (!drillId || !activeSimilar) return;
    setActiveStep(null);
    setSimilarBaseMs(0);
    setSimilarElapsedMs(0);
    setHasUnfinishedActiveOnServer(true);
    setActiveSimilar((prev) => {
      if (!prev) return prev;
      const cleaned = { ...prev.problem };
      delete cleaned.display;
      delete cleaned.plainText;
      delete cleaned.steps;
      delete cleaned.answerDisplay;
      delete cleaned.answerPlain;
      return {
        ...prev,
        problem: {
          ...cleaned,
          state: {
            userInput: "",
            score: null,
            divergedStep: null,
            mistakes: [],
            lastCheck: null,
            attempts: [],
            hintsRevealed: 0,
            setupRevealedBeforeAnswer: false,
            solutionRevealedBeforeAnswer: false,
            durationMs: 0,
          },
        },
      };
    });
    void fetch("/api/variant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        drillId,
        qid: problem.id,
        variantToken: activeSimilar.token,
        action: "reset",
      }),
    }).catch(() => {
      // non-blocking
    });
  }, [activeSimilar, drillId, problem.id]);

  const resetAllVariantUi = useCallback(() => {
    setMode("original");
    setActiveSimilar(null);
    setActiveStep(null);
    setLoadingAction(null);
    syncSimilarUrlParam(false, isReviewSession);
  }, [isReviewSession]);

  return {
    mode,
    activeSimilar,
    example,
    exampleViewedAt,
    remainingCount,
    serverVariantWrongs,
    hasUnfinishedActiveSimilar:
      hasUnfinishedActiveOnServer ||
      Boolean(
        activeSimilar && activeSimilar.problem.state.lastCheck?.verdict !== "correct"
      ),
    loadingAction,
    loadingSteps,
    activeStep,
    setActiveStep,
    announcement,
    similarTimerMs: similarBaseMs + similarElapsedMs,
    isSimilarPaused,
    toggleSimilarPaused: () => setIsSimilarPaused((prev) => !prev),
    openSimilar,
    loadAnotherSimilar,
    openWorkedExample,
    backToOriginal,
    handleSimilarInputChange,
    handleSimilarCheckAnswer,
    handleSimilarHintRevealed,
    handleSimilarSetupRevealed,
    handleSimilarSolutionRevealed,
    handleSimilarReset,
    resetAllVariantUi,
  };
}
