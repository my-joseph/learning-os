"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  isSubstantiveVerdict,
  sanitizeCheckMessage,
} from "@/lib/reviewGuard";
import { isLockedAfterCorrect, scoreProblem, scoreVariant } from "@/lib/scoring";
import {
  deriveRealTabStatus,
  deriveTabStatuses,
  deriveVariantStatus,
  isInCycle,
  parseTabParam,
  resolveInitialTab,
  SimilarSlotNumber,
  SimilarTabId,
  SimilarTabStatus,
  SimilarTabSummary,
  similarUnlock,
  slotToTabId,
  tabStatusAccessibleSuffix,
} from "@/lib/similarTabs";
import {
  AttemptRecord,
  CheckResult,
  Problem,
  RedactedVariant,
  Step,
  VariantSessionRecord,
  WorkedExampleVariant,
} from "@/types/drill";

interface ListApiResponse {
  unlocked: boolean;
  tabs: SimilarTabSummary[];
  exampleViewedAt?: string | null;
}

interface OpenApiResponse {
  mode: "open";
  drillId: string;
  qid: string;
  token: string;
  slot: SimilarSlotNumber;
  total: number;
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
  const restoredScore = scoreVariant(
    {
      role: "try",
      attempts,
      hintsRevealed: session?.hintsRevealed || 0,
      setupRevealed: Boolean(session?.setupRevealed),
      stepsRevealed: Boolean(session?.stepsRevealed),
      servedAt: "",
    },
    null
  ).score;

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
    checkpointHint: "",
    hasSetup: variant.hasSetup,
    hasHint: variant.hasHint,
    ...(revealed?.display !== undefined ? { display: revealed.display } : {}),
    ...(revealed?.plainText !== undefined ? { plainText: revealed.plainText } : {}),
    ...(Array.isArray(revealed?.steps) ? { steps: revealed.steps } : {}),
    ...(revealed?.answerDisplay !== undefined
      ? { answerDisplay: revealed.answerDisplay }
      : {}),
    ...(revealed?.answerPlain !== undefined
      ? { answerPlain: revealed.answerPlain }
      : {}),
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

function readUrlTabIntent(isReviewSession: boolean): {
  tabParam: string | null;
  similarParam: boolean;
} {
  if (typeof window === "undefined" || isReviewSession) {
    return { tabParam: null, similarParam: false };
  }
  try {
    const params = new URLSearchParams(window.location.search);
    return {
      tabParam: params.get("tab"),
      similarParam: params.get("similar") === "1",
    };
  } catch {
    return { tabParam: null, similarParam: false };
  }
}

function syncTabUrlParam(tabId: SimilarTabId, isReviewSession: boolean) {
  if (typeof window === "undefined" || isReviewSession) return;
  try {
    const url = new URL(window.location.href);
    const currentTab = url.searchParams.get("tab");
    const hasSimilar = url.searchParams.has("similar");
    if (tabId === "q") {
      if (currentTab !== null || hasSimilar) {
        url.searchParams.delete("tab");
        url.searchParams.delete("similar");
        window.history.replaceState(
          window.history.state,
          "",
          url.pathname + url.search + url.hash
        );
      }
    } else if (currentTab !== tabId || hasSimilar) {
      url.searchParams.set("tab", tabId);
      url.searchParams.delete("similar");
      window.history.replaceState(
        window.history.state,
        "",
        url.pathname + url.search + url.hash
      );
    }
  } catch {
    // ignore in non-browser / synthetic test environments
  }
}

export interface TabActivatedInfo {
  tabId: SimilarTabId;
  token?: string;
  isCorrect: boolean;
  selectOriginal?: boolean;
}

export interface SimilarProgressPatch {
  similarSlots?: string[];
  variantToken?: string;
  variantRecord?: VariantSessionRecord;
}

/**
 * Compute updated similar problem + server-sync record from the post-await latest tab problem,
 * preserving any hints, set-up, or steps revealed while `/api/check-answer` was in flight.
 */
export function applySimilarCheckToLatestProblem(
  latestProb: Problem,
  resolvedInput: string,
  checked: CheckResult,
  attemptElapsed: number,
  nowIso: string = new Date().toISOString(),
  existingServedAt?: string
): {
  nextProblem: Problem;
  nextRecord: VariantSessionRecord;
  needsSteps: boolean;
  needsDisplay: boolean;
} {
  const prevAttempts = latestProb.state.attempts || [];
  // Rule 2 & 6: lock after correct on similar tabs just like the main question.
  if (isLockedAfterCorrect(latestProb.state, { isVariant: true })) {
    const unchangedRecord: VariantSessionRecord = {
      role: "try",
      attempts: prevAttempts,
      hintsRevealed: latestProb.state.hintsRevealed || 0,
      setupRevealed: Boolean(latestProb.state.setupRevealedBeforeAnswer),
      stepsRevealed: Boolean(latestProb.state.solutionRevealedBeforeAnswer),
      durationMs: latestProb.state.durationMs || 0,
      servedAt: existingServedAt || nowIso,
    };
    return {
      nextProblem: latestProb,
      nextRecord: unchangedRecord,
      needsSteps: false,
      needsDisplay: false,
    };
  }
  const nextAttempt: AttemptRecord = {
    input: resolvedInput,
    ts: nowIso,
    verdict: checked.verdict,
    kind: "variant",
    ...(latestProb.state.setupRevealedBeforeAnswer ? { setupRevealed: true } : {}),
    ...(latestProb.state.solutionRevealedBeforeAnswer ? { solutionRevealed: true } : {}),
  };
  const updatedAttempts = [...prevAttempts, nextAttempt];
  const nextDuration = (latestProb.state.durationMs || 0) + attemptElapsed;
  const candidateState = {
    ...latestProb.state,
    userInput: resolvedInput,
    lastCheck: checked,
    attempts: updatedAttempts,
    durationMs: nextDuration,
  };
  const nextScore = scoreProblem(candidateState, {
    isVariant: true,
    ignoreStateScore: true,
  }).score;
  const nextProblem: Problem = {
    ...latestProb,
    state: {
      ...candidateState,
      score: nextScore,
    },
  };
  const nextRecord: VariantSessionRecord = {
    role: "try",
    attempts: updatedAttempts,
    hintsRevealed: latestProb.state.hintsRevealed || 0,
    setupRevealed: Boolean(latestProb.state.setupRevealedBeforeAnswer),
    stepsRevealed: Boolean(latestProb.state.solutionRevealedBeforeAnswer),
    durationMs: nextDuration,
    servedAt: existingServedAt || nowIso,
  };
  const needsSteps =
    checked.verdict === "correct" && (!latestProb.steps || latestProb.steps.length === 0);
  const needsDisplay = Boolean(
    checked.verdict === "correct" &&
      latestProb.hasSetup &&
      !latestProb.display &&
      !latestProb.plainText
  );
  return { nextProblem, nextRecord, needsSteps, needsDisplay };
}

/**
 * Compute updated similar problem + sync record after `GET /api/reveal?part=hint` finishes,
 * reading from the post-await latest problem so any concurrent check attempt is never dropped.
 */
export function applySimilarHintToLatestProblem(
  latestProb: Problem,
  checkpointHint: string,
  nowIso: string = new Date().toISOString(),
  existingServedAt?: string
): {
  nextProblem: Problem;
  nextRecord: VariantSessionRecord;
  didIncrement: boolean;
} {
  const hasCorrect = isLockedAfterCorrect(latestProb.state, { isVariant: true });
  const nextHints = hasCorrect
    ? latestProb.state.hintsRevealed || 0
    : (latestProb.state.hintsRevealed || 0) + 1;
  const nextProblem: Problem = {
    ...latestProb,
    checkpointHint,
    state: {
      ...latestProb.state,
      hintsRevealed: nextHints,
    },
  };
  const nextRecord: VariantSessionRecord = {
    role: "try",
    attempts: latestProb.state.attempts || [],
    hintsRevealed: nextHints,
    setupRevealed: Boolean(latestProb.state.setupRevealedBeforeAnswer),
    stepsRevealed: Boolean(latestProb.state.solutionRevealedBeforeAnswer),
    durationMs: latestProb.state.durationMs || 0,
    servedAt: existingServedAt || nowIso,
  };
  return { nextProblem, nextRecord, didIncrement: !hasCorrect };
}

/** Return true when opening steps on a similar tab must persist `stepsRevealed` to the server. */
export function shouldPersistVariantStepsReveal(prob: Problem): boolean {
  const hasCorrect = isLockedAfterCorrect(prob.state, { isVariant: true });
  return !hasCorrect && !prob.state.solutionRevealedBeforeAnswer;
}

export interface UseSimilarTabsOptions {
  drillId?: string;
  problem: Problem;
  questionNumber: number;
  isReviewSession?: boolean;
  autoOpenSimilar?: boolean;
  onAutoOpenSimilarConsumed?: () => void;
  onBeforeFetchVariant?: () => Promise<void>;
  onExampleViewed?: (viewedAt: string) => void;
  onSimilarProgressSync?: (patch: SimilarProgressPatch) => void;
  onTabActivated?: (info: TabActivatedInfo) => void;
}

/**
 * Manages the Similar Questions v2 tab strip (`[Question N]` + `[Similar 1..3]`),
 * lazy server loading (`mode=list` / `mode=open`), per-tab timers, URL `?tab=` / `?similar=1`
 * deep-link sync, and the existing worked-example path (`mode=example`).
 */
export function useSimilarTabs({
  drillId,
  problem,
  questionNumber,
  isReviewSession = false,
  autoOpenSimilar = false,
  onAutoOpenSimilarConsumed,
  onBeforeFetchVariant,
  onExampleViewed,
  onSimilarProgressSync,
  onTabActivated,
}: UseSimilarTabsOptions) {
  const isUnlocked = Boolean(
    drillId && problem.hasVariants && similarUnlock(problem.state)
  );
  const cycleKey = problem.state.cycleStartedAt ?? "";

  const [selectedTab, setSelectedTab] = useState<SimilarTabId>("q");
  const [tabs, setTabs] = useState<SimilarTabSummary[]>(() =>
    isUnlocked ? deriveTabStatuses(problem.state) : []
  );
  const [listEmpty, setListEmpty] = useState(false);
  const [tabProblems, setTabProblems] = useState<Record<string, Problem>>({});
  const [loadingTabToken, setLoadingTabToken] = useState<string | null>(null);
  const [tabErrors, setTabErrors] = useState<Record<string, string>>({});
  const [loadingSteps, setLoadingSteps] = useState(false);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  const [announcement, setAnnouncement] = useState("");

  // Existing worked-example path (unchanged per binding scope change)
  const [showingExample, setShowingExample] = useState(false);
  const [example, setExample] = useState<WorkedExampleVariant | null>(null);
  const [exampleViewedAt, setExampleViewedAt] = useState<string | null>(() =>
    problem.state.exampleViewedAt &&
    isInCycle(problem.state.exampleViewedAt, problem.state.cycleStartedAt)
      ? problem.state.exampleViewedAt
      : null
  );
  const [loadingExample, setLoadingExample] = useState(false);

  // Per-similar-tab timer
  const [similarBaseMs, setSimilarBaseMs] = useState(0);
  const [similarElapsedMs, setSimilarElapsedMs] = useState(0);
  const [isSimilarPaused, setIsSimilarPaused] = useState(false);
  const similarTickStartRef = useRef<number | null>(null);
  const similarElapsedRef = useRef(0);
  similarElapsedRef.current = similarElapsedMs;

  const isUnlockedRef = useRef(isUnlocked);
  isUnlockedRef.current = isUnlocked;
  const selectedTabRef = useRef<SimilarTabId>(selectedTab);
  selectedTabRef.current = selectedTab;
  const tabsRef = useRef<SimilarTabSummary[]>(tabs);
  tabsRef.current = tabs;
  const tabProblemsRef = useRef<Record<string, Problem>>(tabProblems);
  tabProblemsRef.current = tabProblems;
  const tabServedAtRef = useRef<Record<string, string>>({});
  const questionKey = `${drillId ?? ""}:${problem.id}`;
  const questionKeyRef = useRef(questionKey);
  questionKeyRef.current = questionKey;

  const updateTabProblem = useCallback(
    (tok: string, updater: (cur: Problem) => Problem): Problem | null => {
      const cur = tabProblemsRef.current[tok];
      if (!cur) return null;
      const next = updater(cur);
      tabProblemsRef.current = { ...tabProblemsRef.current, [tok]: next };
      setTabProblems((prev) => {
        const existing = prev[tok];
        if (!existing) return prev;
        return { ...prev, [tok]: next };
      });
      return next;
    },
    []
  );

  const onTabActivatedRef = useRef(onTabActivated);
  onTabActivatedRef.current = onTabActivated;
  const onExampleViewedRef = useRef(onExampleViewed);
  onExampleViewedRef.current = onExampleViewed;
  const onSimilarProgressSyncRef = useRef(onSimilarProgressSync);
  onSimilarProgressSyncRef.current = onSimilarProgressSync;
  const onBeforeFetchVariantRef = useRef(onBeforeFetchVariant);
  onBeforeFetchVariantRef.current = onBeforeFetchVariant;
  const onAutoOpenSimilarConsumedRef = useRef(onAutoOpenSimilarConsumed);
  onAutoOpenSimilarConsumedRef.current = onAutoOpenSimilarConsumed;

  const problemStateRef = useRef(problem.state);
  problemStateRef.current = problem.state;

  const activeSimilarTab =
    selectedTab !== "q"
      ? tabs.find((t) => slotToTabId(t.slot) === selectedTab) ?? null
      : null;
  const activeSimilarToken = activeSimilarTab?.token ?? null;
  const activeSimilarProblem = activeSimilarToken
    ? tabProblems[activeSimilarToken] ?? null
    : null;

  const activeTokenRef = useRef<string | null>(activeSimilarToken);
  activeTokenRef.current = activeSimilarToken;

  /** Flush accumulated unsent elapsed time on the currently active similar tab to the server. */
  const flushActiveSimilarDuration = useCallback(
    (tokenOverride?: string | null) => {
      const tok = tokenOverride !== undefined ? tokenOverride : activeTokenRef.current;
      const tickDelta =
        similarTickStartRef.current !== null
          ? Math.max(0, Date.now() - similarTickStartRef.current)
          : 0;
      similarTickStartRef.current = null;
      const unsent = Math.min(600_000, similarElapsedRef.current + tickDelta);
      setSimilarElapsedMs(0);

      if (!tok || !drillId || unsent <= 0) return;

      setTabProblems((prev) => {
        const cur = prev[tok];
        if (!cur) return prev;
        return {
          ...prev,
          [tok]: {
            ...cur,
            state: {
              ...cur.state,
              durationMs: (cur.state.durationMs || 0) + unsent,
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
          variantToken: tok,
          action: "duration",
          durationMs: unsent,
        }),
      }).catch(() => {
        // non-blocking duration sync
      });
    },
    [drillId, problem.id]
  );

  const openTokenFromServer = useCallback(
    async (
      tab: SimilarTabSummary,
      opts?: { announce?: boolean; focusOnLoad?: boolean }
    ) => {
      if (!drillId) return;
      const tabId = slotToTabId(tab.slot);
      setLoadingTabToken(tab.token);
      setTabErrors((prev) => {
        if (!(tab.token in prev)) return prev;
        const copy = { ...prev };
        delete copy[tab.token];
        return copy;
      });
      try {
        const qs = new URLSearchParams({
          drillId,
          qid: problem.id,
          mode: "open",
          token: tab.token,
        });
        const res = await fetch(`/api/variant?${qs.toString()}`, {
          cache: "no-store",
        });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data = (await res.json()) as OpenApiResponse;
        if (!data.variant) {
          throw new Error("Missing variant payload");
        }
        const built = buildSimilarProblem(data.variant, data.session, data.revealed);
        if (data.session?.servedAt) {
          tabServedAtRef.current[tab.token] = data.session.servedAt;
        }
        tabProblemsRef.current = { ...tabProblemsRef.current, [tab.token]: built };
        setTabProblems((prev) => ({ ...prev, [tab.token]: built }));
        const alreadySolved = built.state.lastCheck?.verdict === "correct";
        if (selectedTabRef.current === tabId) {
          setSimilarBaseMs(data.session.durationMs || 0);
          setSimilarElapsedMs(0);
          setIsSimilarPaused(false);
          similarTickStartRef.current = alreadySolved ? null : Date.now();
          if (opts?.announce) {
            const total = tabsRef.current.length || data.total || 3;
            setAnnouncement(
              `Similar question ${tab.slot} of ${total}${tabStatusAccessibleSuffix(
                tab.status
              )}`
            );
          }
          if (opts?.focusOnLoad !== false) {
            onTabActivatedRef.current?.({
              tabId,
              token: tab.token,
              isCorrect: alreadySolved,
            });
          }
        }
      } catch {
        setTabErrors((prev) => ({
          ...prev,
          [tab.token]: "Couldn't load this question. Try again.",
        }));
      } finally {
        setLoadingTabToken((cur) => (cur === tab.token ? null : cur));
      }
    },
    [drillId, problem.id]
  );

  const selectTab = useCallback(
    (
      nextTabId: SimilarTabId,
      opts?: { selectOriginal?: boolean; forceRefetch?: boolean; fromDeepLink?: boolean }
    ) => {
      if (!isUnlockedRef.current && nextTabId !== "q") {
        return;
      }
      const prevTab = selectedTabRef.current;
      if (prevTab !== "q" && prevTab !== nextTabId) {
        flushActiveSimilarDuration();
      }

      setShowingExample(false);
      setActiveStep(null);
      setSelectedTab(nextTabId);
      syncTabUrlParam(nextTabId, isReviewSession);

      if (nextTabId === "q") {
        const realStatus = deriveRealTabStatus(problemStateRef.current);
        setAnnouncement(
          `Question ${questionNumber}${tabStatusAccessibleSuffix(realStatus)}`
        );
        onTabActivatedRef.current?.({
          tabId: "q",
          isCorrect: problemStateRef.current.lastCheck?.verdict === "correct",
          selectOriginal: opts?.selectOriginal ?? true,
        });
        return;
      }

      const targetTab = tabsRef.current.find(
        (t) => slotToTabId(t.slot) === nextTabId
      );
      if (!targetTab) {
        setSelectedTab("q");
        syncTabUrlParam("q", isReviewSession);
        return;
      }

      const cached = opts?.forceRefetch ? undefined : tabProblemsRef.current[targetTab.token];
      if (cached) {
        const alreadySolved = cached.state.lastCheck?.verdict === "correct";
        setSimilarBaseMs(cached.state.durationMs || 0);
        setSimilarElapsedMs(0);
        setIsSimilarPaused(false);
        similarTickStartRef.current = alreadySolved ? null : Date.now();
        setAnnouncement(
          `Similar question ${targetTab.slot} of ${tabsRef.current.length}${tabStatusAccessibleSuffix(
            targetTab.status
          )}`
        );
        onTabActivatedRef.current?.({
          tabId: nextTabId,
          token: targetTab.token,
          isCorrect: alreadySolved,
        });
      } else {
        setSimilarBaseMs(0);
        setSimilarElapsedMs(0);
        setIsSimilarPaused(false);
        similarTickStartRef.current = null;
        void openTokenFromServer(targetTab, { announce: true, focusOnLoad: true });
      }
    },
    [flushActiveSimilarDuration, isReviewSession, openTokenFromServer, questionNumber]
  );

  // Reset per-question state when switching to a different question or cycle.
  useEffect(() => {
    setSelectedTab("q");
    setShowingExample(false);
    setListEmpty(false);
    setTabProblems({});
    setTabErrors({});
    setLoadingTabToken(null);
    setLoadingSteps(false);
    setActiveStep(null);
    setExample(null);
    setExampleViewedAt(
      problem.state.exampleViewedAt &&
        isInCycle(problem.state.exampleViewedAt, problem.state.cycleStartedAt)
        ? problem.state.exampleViewedAt
        : null
    );
    setSimilarBaseMs(0);
    setSimilarElapsedMs(0);
    setIsSimilarPaused(false);
    similarTickStartRef.current = null;
    if (!isUnlocked) {
      setTabs([]);
      const intent = readUrlTabIntent(isReviewSession);
      if (intent.tabParam !== null || intent.similarParam) {
        syncTabUrlParam("q", isReviewSession);
      }
    } else {
      setTabs(deriveTabStatuses(problem.state));
    }
    return () => {
      flushActiveSimilarDuration();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drillId, problem.id, cycleKey]);

  // Fetch mode=list once unlocked (and hydrate initial ?tab= / ?similar=1 or WorkedExampleDisclosure).
  const fetchedListKeyRef = useRef<string | null>(null);
  useEffect(() => {
    if (!isUnlocked || !drillId) {
      fetchedListKeyRef.current = null;
      setTabs([]);
      if (selectedTabRef.current !== "q") {
        setSelectedTab("q");
        syncTabUrlParam("q", isReviewSession);
      }
      if (autoOpenSimilar) {
        onAutoOpenSimilarConsumedRef.current?.();
      }
      const intent = readUrlTabIntent(isReviewSession);
      if (intent.tabParam !== null || intent.similarParam) {
        syncTabUrlParam("q", isReviewSession);
      }
      return;
    }

    const listKey = `${drillId}:${problem.id}:${cycleKey}`;
    if (fetchedListKeyRef.current === listKey && tabsRef.current.length > 0) {
      // Already loaded list for this question/cycle; handle late autoOpenSimilar if triggered.
      if (autoOpenSimilar) {
        onAutoOpenSimilarConsumedRef.current?.();
        const targetId = resolveInitialTab({
          unlocked: true,
          tabs: tabsRef.current,
          similarParam: true,
        });
        if (targetId !== "q") {
          selectTab(targetId, { fromDeepLink: true });
        }
      }
      return;
    }

    let cancelled = false;
    fetchedListKeyRef.current = listKey;

    const run = async () => {
      try {
        if (onBeforeFetchVariantRef.current) {
          await onBeforeFetchVariantRef.current();
        }
        if (cancelled) return;
        const qs = new URLSearchParams({
          drillId,
          qid: problem.id,
          mode: "list",
        });
        const res = await fetch(`/api/variant?${qs.toString()}`, {
          cache: "no-store",
        });
        if (cancelled) return;
        if (!res.ok) {
          fetchedListKeyRef.current = null;
          return;
        }
        const data = (await res.json()) as ListApiResponse;
        if (cancelled) return;

        if (!data.unlocked || !Array.isArray(data.tabs) || data.tabs.length === 0) {
          setTabs([]);
          setListEmpty(Boolean(data.unlocked));
          fetchedListKeyRef.current = null;
          if (autoOpenSimilar) onAutoOpenSimilarConsumedRef.current?.();
          const intent = readUrlTabIntent(isReviewSession);
          if (intent.tabParam !== null || intent.similarParam) {
            syncTabUrlParam("q", isReviewSession);
          }
          return;
        }

        setListEmpty(false);
        setTabs(data.tabs);
        tabsRef.current = data.tabs;
        onSimilarProgressSyncRef.current?.({
          similarSlots: data.tabs.map((t) => t.token),
        });

        // Hydrate WorkedExampleDisclosure if an example was already viewed in this cycle.
        const viewedTs =
          data.exampleViewedAt ??
          (problemStateRef.current.exampleViewedAt &&
          isInCycle(
            problemStateRef.current.exampleViewedAt,
            problemStateRef.current.cycleStartedAt
          )
            ? problemStateRef.current.exampleViewedAt
            : null);
        if (viewedTs) {
          setExampleViewedAt(viewedTs);
          const exQs = new URLSearchParams({
            drillId,
            qid: problem.id,
            mode: "example",
          });
          fetch(`/api/variant?${exQs.toString()}`, { cache: "no-store" })
            .then(async (exRes) => (exRes.ok ? await exRes.json() : null))
            .then((exData: { variant?: WorkedExampleVariant } | null) => {
              if (!cancelled && exData?.variant) {
                setExample(exData.variant);
              }
            })
            .catch(() => {
              // non-blocking
            });
        }

        const intent = readUrlTabIntent(isReviewSession);
        const wantsDeepLink = Boolean(autoOpenSimilar || intent.similarParam);
        if (autoOpenSimilar) {
          onAutoOpenSimilarConsumedRef.current?.();
        }
        const targetId = resolveInitialTab({
          unlocked: true,
          tabs: data.tabs,
          tabParam: intent.tabParam,
          similarParam: wantsDeepLink,
        });
        if (targetId !== "q") {
          selectTab(targetId, { fromDeepLink: true });
        } else if (intent.tabParam !== null || intent.similarParam) {
          syncTabUrlParam("q", isReviewSession);
        }
      } catch {
        fetchedListKeyRef.current = null;
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [
    autoOpenSimilar,
    cycleKey,
    drillId,
    isReviewSession,
    isUnlocked,
    problem.id,
    selectTab,
  ]);

  // Run per-similar-tab timer only while on a similar tab, unpaused, loaded, and not solved.
  const activeSolved = activeSimilarProblem?.state.lastCheck?.verdict === "correct";
  const shouldTickSimilar =
    !showingExample &&
    selectedTab !== "q" &&
    Boolean(activeSimilarProblem) &&
    !isSimilarPaused &&
    !activeSolved;

  useEffect(() => {
    if (!shouldTickSimilar) {
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
  }, [shouldTickSimilar, activeSimilarToken]);

  const retryActiveTab = useCallback(() => {
    if (!activeSimilarTab) return;
    void openTokenFromServer(activeSimilarTab, { announce: true, focusOnLoad: true });
  }, [activeSimilarTab, openTokenFromServer]);

  const openWorkedExample = useCallback(async () => {
    if (!drillId || loadingExample) return;
    if (selectedTabRef.current !== "q") {
      flushActiveSimilarDuration();
    }
    if (example) {
      setShowingExample(true);
      setAnnouncement(`Worked example for Question ${questionNumber}`);
      return;
    }
    setLoadingExample(true);
    try {
      if (onBeforeFetchVariantRef.current) {
        await onBeforeFetchVariantRef.current();
      }
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        mode: "example",
      });
      const res = await fetch(`/api/variant?${qs.toString()}`, {
        cache: "no-store",
      });
      if (!res.ok) return;
      const data = (await res.json()) as {
        token: string;
        variant: WorkedExampleVariant;
        exampleViewedAt?: string;
      };
      if (!data.variant) return;

      setExample(data.variant);
      const viewedTs = data.exampleViewedAt || new Date().toISOString();
      setExampleViewedAt(viewedTs);
      onExampleViewedRef.current?.(viewedTs);
      setShowingExample(true);
      setAnnouncement(`Worked example for Question ${questionNumber}`);
    } finally {
      setLoadingExample(false);
    }
  }, [drillId, example, flushActiveSimilarDuration, loadingExample, problem.id, questionNumber]);

  const closeWorkedExample = useCallback(() => {
    setShowingExample(false);
    selectTab("q", { selectOriginal: true });
  }, [selectTab]);

  const handleSimilarInputChange = useCallback(
    (val: string) => {
      const tok = activeTokenRef.current;
      if (!tok) return;
      updateTabProblem(tok, (cur) => ({
        ...cur,
        state: {
          ...cur.state,
          userInput: val,
        },
      }));
    },
    [updateTabProblem]
  );

  const handleSimilarCheckAnswer = useCallback(
    async (inputOverride?: string) => {
      const tok = activeTokenRef.current;
      if (!drillId || !tok) return;
      const snapProb = tabProblemsRef.current[tok];
      if (!snapProb) return;
      if (isLockedAfterCorrect(snapProb.state, { isVariant: true })) return;
      const targetQuestionKey = questionKeyRef.current;
      const resolved = (
        inputOverride !== undefined ? inputOverride : snapProb.state.userInput
      ).trim();
      if (!resolved) return;

      const attemptElapsed =
        similarElapsedRef.current +
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
            variantToken: tok,
            input: resolved,
            durationMs: attemptElapsed,
          }),
        });
        const raw = (await res.json()) as CheckResult;
        if (questionKeyRef.current !== targetQuestionKey) return;

        const calmMsg = sanitizeCheckMessage(raw.verdict, raw.message);
        const checked: CheckResult =
          calmMsg === raw.message ? raw : { ...raw, message: calmMsg };

        // Read post-await latest tab state so mid-check hints or set-up reveals are never lost.
        const latestProb = tabProblemsRef.current[tok];
        if (!latestProb) return;

        const nowIso = new Date().toISOString();
        const { nextProblem, nextRecord, needsSteps, needsDisplay } =
          applySimilarCheckToLatestProblem(
            latestProb,
            resolved,
            checked,
            attemptElapsed,
            nowIso,
            tabServedAtRef.current[tok]
          );
        tabServedAtRef.current[tok] = nextRecord.servedAt;

        if (checked.verdict === "correct") {
          similarTickStartRef.current = null;
        } else if (similarTickStartRef.current !== null) {
          similarTickStartRef.current = Date.now();
        }
        setSimilarBaseMs((prev) => prev + attemptElapsed);
        setSimilarElapsedMs(0);

        updateTabProblem(tok, () => nextProblem);

        const nextStatus: SimilarTabStatus = deriveVariantStatus(
          nextRecord,
          problemStateRef.current.cycleStartedAt
        );
        setTabs((prev) =>
          prev.map((t) => (t.token === tok ? { ...t, status: nextStatus } : t))
        );
        onSimilarProgressSyncRef.current?.({
          variantToken: tok,
          variantRecord: nextRecord,
        });

        // Auto-reveal steps and equation set-up after a correct answer (identical to the real question),
        // without marking the already-solved similar question as assisted.
        if (checked.verdict === "correct") {
          if (needsSteps) {
            setLoadingSteps(true);
            const stepsQs = new URLSearchParams({
              drillId,
              qid: problem.id,
              variantToken: tok,
              part: "steps",
            });
            void fetch(`/api/reveal?${stepsQs.toString()}`)
              .then(async (r) => (r.ok ? await r.json() : null))
              .then(
                (
                  data: {
                    steps?: Step[];
                    answerDisplay?: string;
                    answerPlain?: string;
                  } | null
                ) => {
                  if (!data || questionKeyRef.current !== targetQuestionKey) return;
                  updateTabProblem(tok, (cur) => ({
                    ...cur,
                    steps: Array.isArray(data.steps) ? data.steps : [],
                    answerDisplay: data.answerDisplay || data.answerPlain || "",
                    answerPlain: data.answerPlain || "",
                  }));
                }
              )
              .catch(() => {
                // non-blocking auto-reveal
              })
              .finally(() => {
                setLoadingSteps(false);
              });
          }
          if (needsDisplay) {
            const dispQs = new URLSearchParams({
              drillId,
              qid: problem.id,
              variantToken: tok,
              part: "display",
            });
            void fetch(`/api/reveal?${dispQs.toString()}`)
              .then(async (r) => (r.ok ? await r.json() : null))
              .then((data: { display?: string; plainText?: string } | null) => {
                if (!data || questionKeyRef.current !== targetQuestionKey) return;
                updateTabProblem(tok, (cur) => ({
                  ...cur,
                  ...(typeof data.display === "string"
                    ? { display: data.display }
                    : {}),
                  ...(typeof data.plainText === "string"
                    ? { plainText: data.plainText }
                    : {}),
                }));
              })
              .catch(() => {
                // non-blocking auto-reveal
              });
          }
        }
      } catch {
        if (questionKeyRef.current !== targetQuestionKey) return;
        updateTabProblem(tok, (existing) => ({
          ...existing,
          state: {
            ...existing.state,
            lastCheck: {
              verdict: "invalid input",
              message: "Couldn't check that answer right now. Please try again.",
              components: [],
              diagnostics: [],
            },
          },
        }));
      }
    },
    [drillId, problem.id, updateTabProblem]
  );

  const syncSimilarHelpStatus = useCallback(
    (
      tok: string,
      baseProb: Problem,
      patch: {
        hintsRevealed?: number;
        setupRevealed?: boolean;
        stepsRevealed?: boolean;
      }
    ) => {
      const servedAt = tabServedAtRef.current[tok] || new Date().toISOString();
      tabServedAtRef.current[tok] = servedAt;
      const nextRecord: VariantSessionRecord = {
        role: "try",
        attempts: baseProb.state.attempts || [],
        hintsRevealed:
          patch.hintsRevealed !== undefined
            ? patch.hintsRevealed
            : baseProb.state.hintsRevealed || 0,
        setupRevealed:
          patch.setupRevealed !== undefined
            ? patch.setupRevealed
            : Boolean(baseProb.state.setupRevealedBeforeAnswer),
        stepsRevealed:
          patch.stepsRevealed !== undefined
            ? patch.stepsRevealed
            : Boolean(baseProb.state.solutionRevealedBeforeAnswer),
        durationMs: baseProb.state.durationMs || 0,
        servedAt,
      };
      const nextStatus = deriveVariantStatus(
        nextRecord,
        problemStateRef.current.cycleStartedAt
      );
      setTabs((prev) =>
        prev.map((t) => (t.token === tok ? { ...t, status: nextStatus } : t))
      );
      onSimilarProgressSyncRef.current?.({
        variantToken: tok,
        variantRecord: nextRecord,
      });
    },
    []
  );

  const handleSimilarHintRevealed = useCallback(async () => {
    const tok = activeTokenRef.current;
    if (!drillId || !tok) return;
    if (!tabProblemsRef.current[tok]) return;
    const targetQuestionKey = questionKeyRef.current;
    const params = new URLSearchParams({
      drill: drillId,
      q: problem.id,
      variantToken: tok,
      part: "hint",
    });
    const res = await fetch(`/api/reveal?${params.toString()}`);
    if (!res.ok || questionKeyRef.current !== targetQuestionKey) return;
    const data = (await res.json()) as { checkpointHint?: string };
    if (questionKeyRef.current !== targetQuestionKey) return;

    // Re-read post-await latest problem so any concurrent check attempt is never overwritten.
    const latest = tabProblemsRef.current[tok];
    if (!latest) return;
    const nowIso = new Date().toISOString();
    const { nextProblem, nextRecord, didIncrement } = applySimilarHintToLatestProblem(
      latest,
      data.checkpointHint || "",
      nowIso,
      tabServedAtRef.current[tok]
    );
    tabServedAtRef.current[tok] = nextRecord.servedAt;
    updateTabProblem(tok, () => nextProblem);
    if (didIncrement) {
      const nextStatus = deriveVariantStatus(
        nextRecord,
        problemStateRef.current.cycleStartedAt
      );
      setTabs((prev) =>
        prev.map((t) => (t.token === tok ? { ...t, status: nextStatus } : t))
      );
      onSimilarProgressSyncRef.current?.({
        variantToken: tok,
        variantRecord: nextRecord,
      });
    }
  }, [drillId, problem.id, updateTabProblem]);

  const handleSimilarSetupRevealed = useCallback(async () => {
    const tok = activeTokenRef.current;
    if (!drillId || !tok) return;
    const existing = tabProblemsRef.current[tok];
    if (!existing) return;
    const targetQuestionKey = questionKeyRef.current;
    const hasSubstantive = (existing.state.attempts || []).some((a) =>
      isSubstantiveVerdict(a.verdict)
    );
    if (!hasSubstantive && !existing.state.setupRevealedBeforeAnswer) {
      const updated = updateTabProblem(tok, (cur) => ({
        ...cur,
        state: {
          ...cur.state,
          setupRevealedBeforeAnswer: true,
        },
      }));
      if (updated) {
        syncSimilarHelpStatus(tok, updated, { setupRevealed: true });
      }
    }
    if (existing.display || existing.plainText) return;
    try {
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        variantToken: tok,
        part: "display",
      });
      const res = await fetch(`/api/reveal?${qs.toString()}`);
      if (!res.ok || questionKeyRef.current !== targetQuestionKey) return;
      const data = (await res.json()) as { display?: string; plainText?: string };
      if (questionKeyRef.current !== targetQuestionKey) return;
      updateTabProblem(tok, (cur) => ({
        ...cur,
        ...(typeof data.display === "string" ? { display: data.display } : {}),
        ...(typeof data.plainText === "string"
          ? { plainText: data.plainText }
          : {}),
      }));
    } catch {
      // ignore transient error
    }
  }, [drillId, problem.id, syncSimilarHelpStatus, updateTabProblem]);

  const handleSimilarSolutionRevealed = useCallback(async () => {
    const tok = activeTokenRef.current;
    if (!drillId || !tok) return;
    const existing = tabProblemsRef.current[tok];
    if (!existing) return;
    const targetQuestionKey = questionKeyRef.current;
    const hasSubstantive = (existing.state.attempts || []).some((a) =>
      isSubstantiveVerdict(a.verdict)
    );
    const shouldPersist = shouldPersistVariantStepsReveal(existing);
    if (shouldPersist) {
      const updated = updateTabProblem(tok, (cur) => ({
        ...cur,
        state: {
          ...cur.state,
          solutionRevealedBeforeAnswer: true,
        },
      }));
      if (updated) {
        syncSimilarHelpStatus(tok, updated, { stepsRevealed: true });
      }
    }
    const needsFetchSteps = !existing.steps || existing.steps.length === 0;
    if (!needsFetchSteps) {
      // Steps were already cached locally (e.g. reopened after a wrong attempt),
      // so still persist `stepsRevealed` on the server so status survives reload.
      if (shouldPersist) {
        try {
          await fetch("/api/variant", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              drillId,
              qid: problem.id,
              variantToken: tok,
              action: "reveal-steps",
            }),
          });
        } catch {
          // ignore transient error
        }
      }
      return;
    }
    setLoadingSteps(true);
    try {
      if (shouldPersist || !hasSubstantive) {
        await fetch("/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId,
            qid: problem.id,
            variantToken: tok,
            action: "reveal-steps",
          }),
        });
      }
      if (questionKeyRef.current !== targetQuestionKey) return;
      const qs = new URLSearchParams({
        drillId,
        qid: problem.id,
        variantToken: tok,
        part: "steps",
      });
      const res = await fetch(`/api/reveal?${qs.toString()}`);
      if (!res.ok || questionKeyRef.current !== targetQuestionKey) return;
      const data = (await res.json()) as {
        steps?: Step[];
        answerDisplay?: string;
        answerPlain?: string;
      };
      if (questionKeyRef.current !== targetQuestionKey) return;
      updateTabProblem(tok, (cur) => ({
        ...cur,
        steps: Array.isArray(data.steps) ? data.steps : [],
        answerDisplay: data.answerDisplay || data.answerPlain || "",
        answerPlain: data.answerPlain || "",
      }));
    } finally {
      setLoadingSteps(false);
    }
  }, [drillId, problem.id, syncSimilarHelpStatus, updateTabProblem]);

  const handleSimilarReset = useCallback(() => {
    const tok = activeTokenRef.current;
    if (!drillId || !tok) return;
    setActiveStep(null);
    setSimilarBaseMs(0);
    setSimilarElapsedMs(0);
    setIsSimilarPaused(false);
    similarTickStartRef.current = Date.now();
    setTabProblems((prev) => {
      const cur = prev[tok];
      if (!cur) return prev;
      const cleaned = { ...cur };
      delete cleaned.display;
      delete cleaned.plainText;
      delete cleaned.steps;
      delete cleaned.answerDisplay;
      delete cleaned.answerPlain;
      cleaned.checkpointHint = "";
      return {
        ...prev,
        [tok]: {
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
    setTabs((prev) =>
      prev.map((t) => (t.token === tok ? { ...t, status: "untried" } : t))
    );
    onSimilarProgressSyncRef.current?.({
      variantToken: tok,
      variantRecord: {
        role: "try",
        attempts: [],
        hintsRevealed: 0,
        setupRevealed: false,
        stepsRevealed: false,
        durationMs: 0,
        servedAt: new Date().toISOString(),
      },
    });
    void fetch("/api/variant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        drillId,
        qid: problem.id,
        variantToken: tok,
        action: "reset",
      }),
    }).catch(() => {
      // non-blocking
    });
  }, [drillId, problem.id]);

  const resetAllVariantUi = useCallback(() => {
    fetchedListKeyRef.current = null;
    tabProblemsRef.current = {};
    tabServedAtRef.current = {};
    setSelectedTab("q");
    setShowingExample(false);
    setListEmpty(false);
    setTabs([]);
    setTabProblems({});
    setTabErrors({});
    setLoadingTabToken(null);
    setExample(null);
    setExampleViewedAt(null);
    setActiveStep(null);
    setLoadingExample(false);
    setLoadingSteps(false);
    setSimilarBaseMs(0);
    setSimilarElapsedMs(0);
    setIsSimilarPaused(false);
    similarTickStartRef.current = null;
    syncTabUrlParam("q", isReviewSession);
  }, [isReviewSession]);

  return {
    isUnlocked,
    listEmpty,
    selectedTab,
    tabs,
    activeSimilarTab,
    activeSimilarToken,
    activeSimilarProblem,
    isLoadingActiveTab: Boolean(
      activeSimilarToken && loadingTabToken === activeSimilarToken
    ),
    activeTabError: activeSimilarToken ? tabErrors[activeSimilarToken] ?? null : null,
    showingExample,
    example,
    exampleViewedAt,
    loadingExample,
    loadingSteps,
    activeStep,
    setActiveStep,
    announcement,
    similarTimerMs: similarBaseMs + similarElapsedMs,
    isSimilarPaused,
    toggleSimilarPaused: () => {
      if (activeSolved) return;
      setIsSimilarPaused((prev) => !prev);
    },
    selectTab,
    retryActiveTab,
    openWorkedExample,
    closeWorkedExample,
    handleSimilarInputChange,
    handleSimilarCheckAnswer,
    handleSimilarHintRevealed,
    handleSimilarSetupRevealed,
    handleSimilarSolutionRevealed,
    handleSimilarReset,
    resetAllVariantUi,
    parseTabParam,
  };
}
