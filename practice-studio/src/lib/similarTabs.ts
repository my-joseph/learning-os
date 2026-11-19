import type {
  AttemptRecord,
  ProblemState,
  VariantSessionRecord,
} from "../types/drill";
import { isSubstantiveVerdict, isWrongAttemptVerdict } from "./reviewGuard";
import { scoreProblem, scoreVariant } from "./scoring";

export type SimilarTabStatus =
  | "untried"
  | "usedHelp"
  | "correct"
  | "assisted"
  | "wrong"
  | "partial";
export type RealTabStatus =
  | "untried"
  | "usedHelp"
  | "correct"
  | "assisted"
  | "wrong"
  | "partial"
  | "skipped";
export type SimilarSlotNumber = 1 | 2 | 3;
export type SimilarTabId = "q" | "s1" | "s2" | "s3";

export interface SimilarTabSummary {
  token: string;
  slot: SimilarSlotNumber;
  status: SimilarTabStatus;
}

export const MAX_SIMILAR_TABS = 3;

/** Return ordered slot numbers (1..count, default 3) for locked ghost similar tabs before unlock. */
export function buildLockedSimilarPlaceholders(
  count?: number
): SimilarSlotNumber[] {
  const n =
    typeof count === "number" && Number.isFinite(count)
      ? Math.max(0, Math.min(Math.trunc(count), MAX_SIMILAR_TABS))
      : MAX_SIMILAR_TABS;
  const slots: SimilarSlotNumber[] = [];
  for (let i = 1; i <= n; i += 1) {
    slots.push(i as SimilarSlotNumber);
  }
  return slots;
}

/** Return true when `ts` falls at or after `cycleStartedAt` (absent `cycleStartedAt` counts all history). */
export function isInCycle(
  ts?: string | null,
  cycleStartedAt?: string | null
): boolean {
  if (!cycleStartedAt) return true;
  return typeof ts === "string" && ts.length > 0 && ts >= cycleStartedAt;
}

/** Return attempts made at or after `cycleStartedAt` (all attempts when `cycleStartedAt` is absent). */
export function cycleAttempts(
  attempts?: AttemptRecord[] | null,
  cycleStartedAt?: string | null
): AttemptRecord[] {
  if (!Array.isArray(attempts) || attempts.length === 0) return [];
  if (!cycleStartedAt) return attempts;
  return attempts.filter((a) => a && isInCycle(a.ts, cycleStartedAt));
}

/** Return non-variant attempts on the real question in the current cycle. */
export function cycleOriginalAttempts(
  state?: ProblemState | null
): AttemptRecord[] {
  if (!state) return [];
  return cycleAttempts(state.attempts, state.cycleStartedAt).filter(
    (a) => a.kind !== "variant"
  );
}

/** Count wrong substantive attempts on the real question in the current cycle (excludes variant attempts). */
export function countCycleOriginalWrongAttempts(
  state?: ProblemState | null
): number {
  if (!state) return 0;
  const origAttempts = Array.isArray(state.attempts)
    ? state.attempts.filter((a) => a && a.kind !== "variant")
    : [];
  if (origAttempts.length > 0) {
    return cycleAttempts(origAttempts, state.cycleStartedAt).filter((a) =>
      isWrongAttemptVerdict(a.verdict)
    ).length;
  }
  if (state.cycleStartedAt) {
    // Only count fallback lastCheck if there are no prior attempts and lastCheck is present.
    return state.lastCheck && isWrongAttemptVerdict(state.lastCheck.verdict) ? 1 : 0;
  }
  if (state.lastCheck && isWrongAttemptVerdict(state.lastCheck.verdict)) {
    return 1;
  }
  return 0;
}

/**
 * Unlock gate for the similar-question tab strip and similar API endpoints:
 * true once the real question has a substantive attempt or skip in the current cycle
 * (wrong, partial, equivalent_not_in_form, correct, or skipped).
 */
export function similarUnlock(state?: ProblemState | null): boolean {
  if (!state) return false;

  const origInCycle = cycleOriginalAttempts(state);
  if (origInCycle.some((a) => isSubstantiveVerdict(a.verdict))) {
    return true;
  }

  if (state.cycleStartedAt) {
    const hasOriginalHistory =
      Array.isArray(state.attempts) &&
      state.attempts.some((a) => a && a.kind !== "variant");
    if (hasOriginalHistory) {
      return false;
    }
    if (state.skipped) return true;
    if (state.lastCheck && isSubstantiveVerdict(state.lastCheck.verdict)) {
      return true;
    }
    return false;
  }

  if (state.skipped) return true;
  if (state.lastCheck && isSubstantiveVerdict(state.lastCheck.verdict)) {
    return true;
  }
  return false;
}

/** Derive a single similar tab's status from the canonical `scoreVariant` rule in the current cycle. */
export function deriveVariantStatus(
  record?: VariantSessionRecord | null,
  cycleStartedAt?: string | null
): SimilarTabStatus {
  const scored = scoreVariant(record, cycleStartedAt);
  if (scored.outcome === "correct") return "correct";
  if (scored.outcome === "assisted") return "assisted";
  if (scored.outcome === "wrong") return "wrong";
  return scored.usedHelp ? "usedHelp" : "untried";
}

/** Derive the real question tab's status mark from the canonical `scoreProblem` rule in the current cycle. */
export function deriveRealTabStatus(state?: ProblemState | null): RealTabStatus {
  const scored = scoreProblem(state);
  if (scored.outcome === "correct") return "correct";
  if (scored.outcome === "assisted") return "assisted";
  if (scored.outcome === "wrong") return "wrong";
  if (scored.outcome === "skipped") return "skipped";
  return scored.usedHelp ? "usedHelp" : "untried";
}

/** Derive the ordered Similar 1..3 tab summaries from `state.similarSlots` and `state.variants`. */
export function deriveTabStatuses(
  state?: ProblemState | null
): SimilarTabSummary[] {
  if (!state || !Array.isArray(state.similarSlots) || state.similarSlots.length === 0) {
    return [];
  }
  const slots = state.similarSlots.slice(0, MAX_SIMILAR_TABS);
  return slots.map((token, idx) => ({
    token,
    slot: (idx + 1) as SimilarSlotNumber,
    status: deriveVariantStatus(state.variants?.[token], state.cycleStartedAt),
  }));
}

/**
 * Count how many similar questions in `similarSlots` have at least 1 substantive attempt
 * with `ts >= cycleStartedAt`. Viewing a worked example does not count.
 * Falls back to `role === "try"` records for un-migrated v1 state.
 */
export function countPractisedSimilar(state?: ProblemState | null): number {
  if (!state?.variants || typeof state.variants !== "object") return 0;
  const cycleStartedAt = state.cycleStartedAt;

  if (Array.isArray(state.similarSlots) && state.similarSlots.length > 0) {
    const seen = new Set<string>();
    let count = 0;
    for (const token of state.similarSlots.slice(0, MAX_SIMILAR_TABS)) {
      if (!token || seen.has(token)) continue;
      seen.add(token);
      const rec = state.variants[token];
      if (!rec || rec.role === "example") continue;
      const hasSub = cycleAttempts(rec.attempts, cycleStartedAt).some((a) =>
        isSubstantiveVerdict(a.verdict)
      );
      if (hasSub) count += 1;
    }
    return count;
  }

  // Fallback for un-migrated v1 progress before first mode=list
  let count = 0;
  for (const rec of Object.values(state.variants)) {
    if (!rec || rec.role !== "try") continue;
    const hasSub = cycleAttempts(rec.attempts, cycleStartedAt).some((a) =>
      isSubstantiveVerdict(a.verdict)
    );
    if (hasSub) count += 1;
  }
  return Math.min(count, MAX_SIMILAR_TABS);
}

/** Convert slot number 1..3 to tab id "s1".."s3". */
export function slotToTabId(slot: SimilarSlotNumber): SimilarTabId {
  return `s${slot}` as SimilarTabId;
}

/** Parse a URL `tab` query parameter ("s1" | "s2" | "s3"); invalid or missing returns null. */
export function parseTabParam(raw?: string | null): SimilarTabId | null {
  if (raw === "s1" || raw === "s2" || raw === "s3") return raw;
  return null;
}

/** Pick the first untried similar tab, else the first used-help/wrong/partial similar tab, else null (all correct or none). */
export function pickNextUntriedOrWrongTab(
  tabs: readonly SimilarTabSummary[]
): SimilarTabSummary | null {
  const untried = tabs.find((t) => t.status === "untried");
  if (untried) return untried;
  const notCorrect = tabs.find(
    (t) =>
      t.status === "usedHelp" ||
      t.status === "wrong" ||
      t.status === "partial"
  );
  return notCorrect ?? null;
}

/** Pick the first untried (or used-help unattempted) similar tab (optionally excluding the currently selected token). */
export function pickNextUntriedTab(
  tabs: readonly SimilarTabSummary[],
  excludeToken?: string | null
): SimilarTabSummary | null {
  const untried = tabs.find(
    (t) => t.status === "untried" && (!excludeToken || t.token !== excludeToken)
  );
  if (untried) return untried;
  return (
    tabs.find(
      (t) => t.status === "usedHelp" && (!excludeToken || t.token !== excludeToken)
    ) ?? null
  );
}

/**
 * Resolve the initial tab from URL parameters (`?tab=s1..s3` or `?similar=1` deep link).
 * Locked strips always fall back to `"q"`.
 */
export function resolveInitialTab(params: {
  unlocked: boolean;
  tabs: readonly SimilarTabSummary[];
  tabParam?: string | null;
  similarParam?: boolean;
}): SimilarTabId {
  const { unlocked, tabs, tabParam, similarParam } = params;
  if (!unlocked || tabs.length === 0) return "q";

  const parsed = parseTabParam(tabParam);
  if (parsed) {
    const slotNum = Number(parsed.slice(1));
    if (tabs.some((t) => t.slot === slotNum)) {
      return parsed;
    }
    return "q";
  }

  if (similarParam) {
    const target = pickNextUntriedOrWrongTab(tabs) ?? tabs[0];
    return target ? slotToTabId(target.slot) : "q";
  }

  return "q";
}

/** Compute next focused tab index for WAI-ARIA manual-activation keyboard navigation. */
export function nextTabIndexForKey(
  key: string,
  currentIndex: number,
  totalTabs: number
): number | null {
  if (totalTabs <= 0) return null;
  if (key === "ArrowRight") return (currentIndex + 1) % totalTabs;
  if (key === "ArrowLeft") return (currentIndex - 1 + totalTabs) % totalTabs;
  if (key === "Home") return 0;
  if (key === "End") return totalTabs - 1;
  return null;
}

export function tabStatusAccessibleSuffix(
  status: SimilarTabStatus | RealTabStatus
): string {
  switch (status) {
    case "untried":
      return ", not tried";
    case "usedHelp":
      return ", used help";
    case "correct":
      return ", correct";
    case "assisted":
      return ", correct with help";
    case "wrong":
      return ", not correct yet";
    case "partial":
      return ", almost";
    case "skipped":
      return ", skipped";
  }
}

export interface ResultCardActionPlan {
  retryLabel?: string;
  retryAriaLabel?: string;
  footnote?: string;
  showPractiseSimilarFirst: boolean;
  showPractiseSimilarConfidence: boolean;
  targetSimilarSlot: SimilarSlotNumber | null;
  showSeeExample: boolean;
  showNextSimilar: boolean;
  nextSimilarSlot: SimilarSlotNumber | null;
  showSimilarShowSteps: boolean;
  showSimilarBackLink: boolean;
}

/**
 * Pure presentation plan for result-card buttons and footnotes on R and Similar tabs
 * (per design_v2.md §3 + binding scope change keeping existing worked example entry point).
 */
export function resultCardActions(params: {
  tab: SimilarTabId;
  hasVariants: boolean;
  isReviewSession?: boolean;
  rState: ProblemState;
  statuses: readonly SimilarTabSummary[];
  exampleViewed: boolean;
  activeSimilarToken?: string | null;
  activeSimilarVerdict?: string | null;
  similarStepsOpen?: boolean;
}): ResultCardActionPlan {
  const {
    tab,
    hasVariants,
    isReviewSession = false,
    rState,
    statuses,
    exampleViewed,
    activeSimilarToken,
    activeSimilarVerdict,
    similarStepsOpen = false,
  } = params;

  const empty: ResultCardActionPlan = {
    showPractiseSimilarFirst: false,
    showPractiseSimilarConfidence: false,
    targetSimilarSlot: null,
    showSeeExample: false,
    showNextSimilar: false,
    nextSimilarSlot: null,
    showSimilarShowSteps: false,
    showSimilarBackLink: false,
  };

  if (tab === "q") {
    const lastVerdict = rState.lastCheck?.verdict ?? null;
    const isSkipped = Boolean(rState.skipped || lastVerdict === "skipped");
    const isSubstantive = isSubstantiveVerdict(lastVerdict);
    if (!isSubstantive || isSkipped) {
      return empty;
    }

    const isCorrect = lastVerdict === "correct";
    const isWrongOrPartial =
      lastVerdict === "incorrect" ||
      lastVerdict === "partial" ||
      lastVerdict === "equivalent_not_in_form";

    if (isWrongOrPartial) {
      const target =
        statuses.length > 0 ? pickNextUntriedOrWrongTab(statuses) : null;
      const targetSlot: SimilarSlotNumber | null =
        statuses.length > 0 ? target?.slot ?? null : hasVariants ? 1 : null;
      const origWrongs = countCycleOriginalWrongAttempts(rState);
      const showSeeExample =
        hasVariants && !exampleViewed && origWrongs >= 2;
      return {
        ...empty,
        retryLabel: isReviewSession ? "Try again" : "Try again (max 0.5)",
        retryAriaLabel: isReviewSession
          ? undefined
          : "Try again. A correct answer now scores at most 0.5",
        footnote:
          hasVariants && !isReviewSession
            ? "A correct answer now scores 0.5. Similar questions are practice and don't change your score."
            : undefined,
        showPractiseSimilarFirst: hasVariants && targetSlot !== null,
        targetSimilarSlot: targetSlot,
        showSeeExample,
      };
    }

    if (isCorrect && hasVariants) {
      const target =
        statuses.length > 0
          ? pickNextUntriedOrWrongTab(statuses) ?? statuses[0] ?? null
          : null;
      const targetSlot: SimilarSlotNumber | null =
        statuses.length > 0 ? target?.slot ?? null : 1;
      return {
        ...empty,
        footnote: isReviewSession
          ? undefined
          : "Similar questions don't change your score.",
        showPractiseSimilarConfidence: targetSlot !== null,
        targetSimilarSlot: targetSlot,
      };
    }

    return empty;
  }

  // Similar tab (s1..s3)
  if (!activeSimilarVerdict || !isSubstantiveVerdict(activeSimilarVerdict)) {
    return empty;
  }

  if (activeSimilarVerdict === "correct") {
    const nextUntried = pickNextUntriedTab(statuses, activeSimilarToken);
    return {
      ...empty,
      showNextSimilar: nextUntried !== null,
      nextSimilarSlot: nextUntried?.slot ?? null,
    };
  }

  return {
    ...empty,
    retryLabel: "Try again",
    showSimilarShowSteps: !similarStepsOpen,
    showSimilarBackLink: true,
  };
}
