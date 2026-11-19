import type {
  DrillDocument,
  DrillListItem,
  Problem,
  ProblemState,
} from "../types/drill";
import type { WeakSpotUnit } from "./dueToday";
import { parseLineChoicePrompt } from "./lineChoicePrompt";
import { countWrongAttempts, isSubstantiveVerdict } from "./reviewGuard";
import {
  classifyReviewOutcome,
  getQuestionLabel,
  type GroupedReviewItem,
  type ReviewOutcome,
} from "./reviewOutcome";
import { drillHref } from "./routes";
import { isContextSlug } from "./studioRules";
import { plainTitle, trapName } from "./titleText";

export interface NormalisedTestReport {
  passed: number | null;
  total: number | null;
  hiddenPassed: number | null;
  hiddenTotal: number | null;
  allPassed: boolean;
  hasData: boolean;
}

export interface NormalisedReviewFinding {
  check: string;
  note: string;
  severity?: string;
  line?: number;
}

export interface NormalisedReviewVerdict {
  status: "pass" | "revise" | "not_requested";
  rawVerdict: string | null;
  isUnknownVerdict: boolean;
  findings: NormalisedReviewFinding[];
  lintCount: number | null;
  typecheckCount: number | null;
  testsPassed: number | null;
  testsTotal: number | null;
}

export interface SessionPattern {
  kind: "trap" | "tag";
  label: string;
  count: number;
  itemLabels: string[];
}

export interface NextDrillSuggestion {
  drillId: string;
  title: string;
  href: string;
}

export interface WeakSpotSuggestion {
  id: string;
  label: string;
  matches: number;
  unitCode: string;
}

export interface ProblemJumpTarget {
  index: number;
  problemId: string;
  label: string;
}

function asFiniteNumber(val: unknown): number | null {
  return typeof val === "number" && Number.isFinite(val) ? val : null;
}

/**
 * Defensively normalise `state.lastTestReport`, handling both canonical
 * (`passedCount`/`totalCount`) and lightweight/mock (`passed`/`total`) shapes
 * so the UI never displays `undefined` or `NaN`.
 */
export function normaliseTestReport(report?: unknown): NormalisedTestReport {
  if (!report || typeof report !== "object") {
    return {
      passed: null,
      total: null,
      hiddenPassed: null,
      hiddenTotal: null,
      allPassed: false,
      hasData: false,
    };
  }
  const r = report as Record<string, unknown>;
  const passed = asFiniteNumber(r.passedCount) ?? asFiniteNumber(r.passed);
  const total = asFiniteNumber(r.totalCount) ?? asFiniteNumber(r.total);
  const hiddenPassed = asFiniteNumber(r.hiddenPassed);
  const hiddenTotal = asFiniteNumber(r.hiddenTotal);
  const allPassed =
    typeof r.allPassed === "boolean"
      ? r.allPassed
      : passed !== null && total !== null && total > 0 && passed === total;

  return {
    passed,
    total,
    hiddenPassed,
    hiddenTotal,
    allPassed,
    hasData: true,
  };
}

/**
 * Defensively normalise the latest `state.reviews[]` entry.
 * Unknown non-`pass` verdicts (e.g. `"changes"`) map to `"revise"` while
 * preserving `rawVerdict` for muted display.
 */
export function latestReviewVerdict(state?: ProblemState | null): NormalisedReviewVerdict {
  const reviews = Array.isArray(state?.reviews) ? state!.reviews : [];
  if (reviews.length === 0) {
    return {
      status: "not_requested",
      rawVerdict: null,
      isUnknownVerdict: false,
      findings: [],
      lintCount: null,
      typecheckCount: null,
      testsPassed: null,
      testsTotal: null,
    };
  }

  const latest = reviews[reviews.length - 1] as unknown as Record<string, unknown>;
  const rawVerdict =
    typeof latest?.verdict === "string" && latest.verdict.trim()
      ? latest.verdict.trim()
      : null;

  let status: "pass" | "revise" | "not_requested" = "not_requested";
  let isUnknownVerdict = false;
  if (rawVerdict === "pass") {
    status = "pass";
  } else if (rawVerdict === "revise") {
    status = "revise";
  } else if (rawVerdict) {
    status = "revise";
    isUnknownVerdict = true;
  }

  const rawFindings = Array.isArray(latest?.findings) ? latest.findings : [];
  const findings: NormalisedReviewFinding[] = [];
  for (const item of rawFindings) {
    if (!item || typeof item !== "object") continue;
    const f = item as Record<string, unknown>;
    const check = typeof f.check === "string" ? f.check.trim() : "";
    const note = typeof f.note === "string" ? f.note.trim() : "";
    if (!check && !note) continue;
    findings.push({
      check: check || "Review",
      note,
      ...(typeof f.severity === "string" ? { severity: f.severity } : {}),
      ...(typeof f.line === "number" && Number.isFinite(f.line) ? { line: f.line } : {}),
    });
  }

  const lintCount = Array.isArray(latest?.lint) ? latest.lint.length : null;
  const typecheckCount = Array.isArray(latest?.typecheck)
    ? latest.typecheck.length
    : Array.isArray(latest?.types)
    ? latest.types.length
    : null;

  const latestTests =
    latest?.tests && typeof latest.tests === "object"
      ? (latest.tests as Record<string, unknown>)
      : null;
  const testsPassed = latestTests ? asFiniteNumber(latestTests.passed) : null;
  const testsTotal = latestTests ? asFiniteNumber(latestTests.total) : null;

  return {
    status,
    rawVerdict,
    isUnknownVerdict,
    findings,
    lintCount,
    typecheckCount,
    testsPassed,
    testsTotal,
  };
}

/**
 * Return unique `matchedTrap` IDs actually hit by the learner's own attempts.
 * Zero-leak: never reads `problem.commonTrapTag`.
 */
export function matchedTraps(state?: ProblemState | null): string[] {
  const attempts = Array.isArray(state?.attempts) ? state!.attempts : [];
  const seen = new Set<string>();
  const traps: string[] = [];
  for (const a of attempts) {
    const trap = typeof a?.matchedTrap === "string" ? a.matchedTrap.trim() : "";
    if (trap && !seen.has(trap)) {
      seen.add(trap);
      traps.push(trap);
    }
  }
  return traps;
}

/** Format a choice option ID into its learner-facing label (including "Line N" for line-choice prompts). */
export function formatChoiceAnswerLabel(problem: Problem, rawValue: string): string {
  const trimmed = rawValue.trim();
  if (!trimmed) return "";
  if (problem.answerSpec?.type !== "choice") return trimmed;

  const options = Array.isArray(problem.answerSpec.options) ? problem.answerSpec.options : [];
  const parsedLine = parseLineChoicePrompt(problem.prompt, options);
  if (parsedLine) {
    const matchedItem = parsedLine.items.find(
      (item) =>
        item.option.id.trim() === trimmed ||
        String(item.lineNumber) === trimmed ||
        item.label.trim().toLowerCase() === trimmed.toLowerCase()
    );
    if (matchedItem) {
      return `Line ${matchedItem.lineNumber}`;
    }
    if (/^\d+$/.test(trimmed)) {
      return `Line ${trimmed}`;
    }
  }

  const matchedOpt = options.find((opt) => String(opt.id).trim() === trimmed);
  if (matchedOpt) {
    const label = matchedOpt.label.trim();
    if (label && label.length <= 48 && !label.includes("\n")) {
      return label;
    }
    return `Option ${matchedOpt.id}`;
  }

  return trimmed;
}

/**
 * Return the learner's latest substantive answer text for a math problem.
 * Prefers the last substantive non-skipped attempt's `input` over `state.userInput`
 * (which can be empty on choice / line-choice questions or mock progress).
 */
export function lastAnswerText(problem: Problem): string | null {
  const state = problem.state;
  if (!state) return null;

  const attempts = Array.isArray(state.attempts) ? state.attempts : [];
  let raw: string | null = null;

  for (let i = attempts.length - 1; i >= 0; i -= 1) {
    const a = attempts[i];
    if (!a || !isSubstantiveVerdict(a.verdict) || a.verdict === "skipped") continue;
    const inp = typeof a.input === "string" ? a.input.trim() : "";
    if (inp && inp !== "(Skipped)") {
      raw = inp;
      break;
    }
  }

  if (!raw) {
    const direct = typeof state.userInput === "string" ? state.userInput.trim() : "";
    if (direct && direct !== "(Skipped)") {
      raw = direct;
    }
  }

  if (!raw) return null;
  return formatChoiceAnswerLabel(problem, raw);
}

/** Format the verified answer cleanly (mapping line-choice numeric answers to "Line N"). */
export function verifiedAnswerLabel(problem: Problem): string {
  const raw = (problem.answerPlain || problem.answerDisplay || "").trim();
  if (!raw) return "";
  if (problem.answerSpec?.type === "choice") {
    return formatChoiceAnswerLabel(problem, raw);
  }
  return raw;
}

/** Plain-text collapsed row title (never a truncated KaTeX prompt or raw slug). */
export function shortRowTitle(problem: Problem): string {
  const ctx = typeof problem.context === "string" ? problem.context.trim() : "";
  if (ctx && !isContextSlug(ctx)) {
    return plainTitle(ctx);
  }
  const cat = typeof problem.category === "string" ? problem.category.trim() : "";
  if (cat) {
    return plainTitle(cat);
  }
  if (ctx) {
    return plainTitle(ctx);
  }
  return problem.levelLabel || problem.id;
}

/** Concise muted reason string for a collapsed Review & Sync row. */
export function rowReason(
  problem: Problem,
  outcome: ReviewOutcome,
  isCode: boolean,
  isLab = false
): string {
  if (outcome === "unanswered") return "Not tried yet";
  if (outcome === "skipped") return "Skipped";

  const state = problem.state;
  if (isCode || isLab) {
    const testRep = normaliseTestReport(state?.lastTestReport);
    const rev = latestReviewVerdict(state);
    const parts: string[] = [];

    const passed = testRep.passed ?? rev.testsPassed;
    const total = testRep.total ?? rev.testsTotal;

    if (passed !== null && total !== null) {
      parts.push(`Tests ${passed}/${total}`);
    } else if (testRep.hasData) {
      parts.push("Tests run");
    }

    if (isLab && testRep.hiddenTotal !== null && testRep.hiddenTotal > 0) {
      parts.push(`hidden ${testRep.hiddenPassed ?? 0}/${testRep.hiddenTotal}`);
    }

    if (rev.status !== "not_requested") {
      parts.push(`Review: ${rev.status}`);
      if (rev.findings.length > 0 && rev.status !== "pass") {
        parts.push(
          `${rev.findings.length} ${rev.findings.length === 1 ? "finding" : "findings"}`
        );
      }
    }

    if (parts.length > 0) {
      return parts.join(" · ");
    }
    return outcome === "correct_first" ? "Passed" : "Needs revision";
  }

  // Math row reason
  const traps = matchedTraps(state);
  const firstTrap = traps.length > 0 ? trapName(traps[0]) : "";
  const wrongCount = countWrongAttempts(state);

  if (outcome === "wrong") {
    const tries = Math.max(1, wrongCount);
    const tryText = `${tries} wrong ${tries === 1 ? "try" : "tries"}`;
    return firstTrap ? `${tryText} · trap: ${firstTrap}` : tryText;
  }

  if (outcome === "assisted_or_partial") {
    const hints = state?.hintsRevealed ?? 0;
    const gotCorrect =
      (state?.score ?? 0) >= 1 ||
      Boolean(state?.attempts?.some((a) => a.verdict === "correct"));

    if (hints > 0 && gotCorrect) {
      return `Correct after ${hints} ${hints === 1 ? "hint" : "hints"}`;
    }
    if (state?.solutionRevealedBeforeAnswer) {
      return gotCorrect ? "Correct after steps" : "Used steps";
    }
    if (state?.setupRevealedBeforeAnswer) {
      return gotCorrect ? "Correct after set-up" : "Used set-up";
    }
    if (wrongCount > 0 && gotCorrect) {
      return `Correct after ${wrongCount} wrong ${wrongCount === 1 ? "try" : "tries"}`;
    }
    if (hints > 0) {
      return `Used ${hints} ${hints === 1 ? "hint" : "hints"}`;
    }
    return "Partial credit";
  }

  return "First try";
}

const ATTENTION_ORDER: Record<ReviewOutcome, number> = {
  wrong: 0,
  assisted_or_partial: 1,
  skipped: 2,
  unanswered: 3,
  correct_first: 4,
};

/** Sort "To review" rows worst-first (`wrong`, `assisted_or_partial`, `skipped`, `unanswered`), then by index. */
export function sortNeedsAttention<T>(
  items: readonly GroupedReviewItem<T>[]
): GroupedReviewItem<T>[] {
  return [...items].sort((a, b) => {
    const diff = ATTENTION_ORDER[a.outcome] - ATTENTION_ORDER[b.outcome];
    return diff !== 0 ? diff : a.index - b.index;
  });
}

/**
 * Determine which rows in "To review" start expanded by default:
 * wrong or assisted rows expand when there are 3 or fewer of them AND it is not a "many wrong" session.
 */
export function getDefaultExpandedRowIds(
  needsAttention: readonly GroupedReviewItem<Problem>[],
  totalProblems: number
): Record<string, boolean> {
  const wrongAndAssisted = needsAttention.filter(
    (item) => item.outcome === "wrong" || item.outcome === "assisted_or_partial"
  );
  const isManyWrong = totalProblems > 0 && wrongAndAssisted.length * 2 >= totalProblems;
  if (isManyWrong || wrongAndAssisted.length === 0 || wrongAndAssisted.length > 3) {
    return {};
  }
  const map: Record<string, boolean> = {};
  for (const item of wrongAndAssisted) {
    map[item.problem.id] = true;
  }
  return map;
}

/** Count how many items the learner got right (first-try OR assisted correct). */
export function countRightItems(problems: readonly Problem[]): number {
  let right = 0;
  for (const p of problems) {
    const outcome = classifyReviewOutcome(p.state);
    if (outcome === "correct_first") {
      right += 1;
    } else if (
      outcome === "assisted_or_partial" &&
      ((p.state?.score ?? 0) >= 1 ||
        Boolean(p.state?.attempts?.some((a) => a.verdict === "correct")))
    ) {
      right += 1;
    }
  }
  return right;
}

/**
 * Detect a repeated trap (from `attempts[].matchedTrap`) or repeated mistake tag (>= 2 items)
 * across the session. Zero-leak: never inspects `problem.commonTrapTag`.
 */
export function detectSessionPattern(
  drill: DrillDocument,
  isLab = false
): SessionPattern | null {
  const trapCounts = new Map<string, string[]>();
  drill.problems.forEach((prob, idx) => {
    const qLabel = getQuestionLabel(prob.id, idx, isLab);
    for (const trapId of matchedTraps(prob.state)) {
      const list = trapCounts.get(trapId) ?? [];
      list.push(qLabel);
      trapCounts.set(trapId, list);
    }
  });

  let bestTrap: { id: string; labels: string[] } | null = null;
  trapCounts.forEach((labels, id) => {
    if (labels.length >= 2 && (!bestTrap || labels.length > bestTrap.labels.length)) {
      bestTrap = { id, labels };
    }
  });

  if (bestTrap !== null) {
    const found = bestTrap as { id: string; labels: string[] };
    return {
      kind: "trap",
      label: trapName(found.id),
      count: found.labels.length,
      itemLabels: found.labels,
    };
  }

  // Fallback: repeated explicit mistake tags defined on the drill
  const tagMap = new Map((drill.mistakeTags || []).map((t) => [t.id, t.name || t.label]));
  const tagCounts = new Map<string, string[]>();
  drill.problems.forEach((prob, idx) => {
    const qLabel = getQuestionLabel(prob.id, idx, isLab);
    const seenOnProblem = new Set<string>();
    for (const tid of prob.state?.mistakes || []) {
      if (tid === "unclassified" || tid === "concept-gap" || !tagMap.has(tid)) continue;
      if (seenOnProblem.has(tid)) continue;
      seenOnProblem.add(tid);
      const list = tagCounts.get(tid) ?? [];
      list.push(qLabel);
      tagCounts.set(tid, list);
    }
  });

  let bestTag: { id: string; labels: string[] } | null = null;
  tagCounts.forEach((labels, id) => {
    if (labels.length >= 2 && (!bestTag || labels.length > bestTag.labels.length)) {
      bestTag = { id, labels };
    }
  });

  if (bestTag !== null) {
    const found = bestTag as { id: string; labels: string[] };
    return {
      kind: "tag",
      label: plainTitle(tagMap.get(found.id) || found.id),
      count: found.labels.length,
      itemLabels: found.labels,
    };
  }

  return null;
}

/** Pick the next unpractised drill in the same unit, then same chapter. */
export function findNextDrill(
  currentDrill: DrillDocument,
  drills: readonly DrillListItem[]
): NextDrillSuggestion | null {
  const candidates = drills.filter((d) => {
    if (d.drillId === currentDrill.drillId) return false;
    const practiced =
      d.practiceStatus === "Graded" ||
      d.practiceStatus === "Needs Retry" ||
      (typeof d.answeredCount === "number" && d.answeredCount > 0);
    return !practiced;
  });

  const sameUnit = candidates.find((d) => d.unitCode === currentDrill.unitCode);
  const picked =
    sameUnit ??
    candidates.find(
      (d) => Boolean(currentDrill.chapterCode) && d.chapterCode === currentDrill.chapterCode
    );

  if (!picked) return null;
  const href = drillHref(picked.drillId);
  if (href === "/") return null;
  return {
    drillId: picked.drillId,
    title: plainTitle(picked.unitTitle) || picked.unitCode,
    href,
  };
}

/** Locate an L4 challenge problem in the current drill (preferring one not yet passed cleanly). */
export function findL4ProblemTarget(
  drill: DrillDocument,
  isLab = false
): ProblemJumpTarget | null {
  let fallback: ProblemJumpTarget | null = null;
  for (let i = 0; i < drill.problems.length; i += 1) {
    const p = drill.problems[i];
    if (typeof p.level !== "number" || p.level < 4) continue;
    const target: ProblemJumpTarget = {
      index: i,
      problemId: p.id,
      label: getQuestionLabel(p.id, i, isLab),
    };
    if (classifyReviewOutcome(p.state) !== "correct_first") {
      return target;
    }
    if (!fallback) fallback = target;
  }
  return fallback;
}

/** Pick the top open weak spot for this unit from `/api/weak-spots`. */
export function pickTopWeakSpot(weakSpotUnits: readonly WeakSpotUnit[]): WeakSpotSuggestion | null {
  for (const unit of weakSpotUnits) {
    if (Array.isArray(unit.open) && unit.open.length > 0) {
      const spot = unit.open[0];
      return {
        id: spot.id,
        label: plainTitle(spot.name) || spot.id,
        matches: spot.matches,
        unitCode: unit.unitCode,
      };
    }
  }
  return null;
}

/** Locate the first wrong (or assisted) item in the drill for a "Retry Q1" fallback action. */
export function findFirstWrongItem(
  drill: DrillDocument,
  isLab = false
): ProblemJumpTarget | null {
  let firstAssisted: ProblemJumpTarget | null = null;
  for (let i = 0; i < drill.problems.length; i += 1) {
    const p = drill.problems[i];
    const outcome = classifyReviewOutcome(p.state);
    if (outcome === "wrong") {
      return { index: i, problemId: p.id, label: getQuestionLabel(p.id, i, isLab) };
    }
    if (outcome === "assisted_or_partial" && !firstAssisted) {
      firstAssisted = { index: i, problemId: p.id, label: getQuestionLabel(p.id, i, isLab) };
    }
  }
  return firstAssisted;
}
