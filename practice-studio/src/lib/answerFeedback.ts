import {
  CheckComponent,
  CheckResult,
  ChoiceOption,
  MistakeTag,
  Problem,
  ProblemState,
} from "../types/drill";
import { canRevealSteps } from "./redact";
import { isSubstantiveVerdict, sanitizeCheckMessage } from "./reviewGuard";
import { cycleAttempts } from "./similarTabs";
import { statusTone } from "./statusTone";

export type ResultCardTone = "correct" | "almost" | "wrong" | "skipped";
export type ResultCardActionKind = "next" | "review" | "retry" | "show_steps" | "back";
export type ChoiceResultStatus = "correct" | "wrong" | null;

export const CARD_STYLES: Record<ResultCardTone, string> = {
  correct: statusTone.correct.softCard,
  almost: statusTone.assisted.softCard,
  wrong: statusTone.wrong.softCard,
  skipped: statusTone.skipped.softCard,
};

export const ICON_CIRCLE_STYLES: Record<ResultCardTone, string> = {
  correct: statusTone.correct.iconCircle,
  almost: statusTone.assisted.iconCircle,
  wrong: statusTone.wrong.iconCircle,
  skipped: statusTone.skipped.iconCircle,
};

export interface ResultCardModel {
  tone: ResultCardTone;
  title: string;
  body: string | null;
  components: CheckComponent[];
  attemptNumber: number | null;
  actionKind: ResultCardActionKind | null;
  resultKey: string;
}

const GENERIC_RESULT_MESSAGES = new Set([
  "correct",
  "correct.",
  "correct!",
  "correct option selected.",
  "incorrect",
  "incorrect.",
  "incorrect choice.",
  "incorrect option selected.",
  "not equal to the verified answer.",
  "not equivalent to the verified answer.",
  "not equal to the verified interval.",
  "not equal to the verified vector.",
  "does not match the accepted answers.",
  "some components match.",
  "no component matches.",
  "output sequence does not match.",
  "some outputs matched, but the sequence or values diverged.",
  "some solutions found, others missing or incorrect.",
]);

const INTERNAL_TONE_REWRITES: Array<[RegExp, string]> = [
  [
    /^Skipped\s*\(Concept Gap\s*\/\s*Unsure\).*$/i,
    "Review the steps below when you're ready.",
  ],
  [
    /^Selected option is not the intended resolution\.?$/i,
    "That option isn't the right one.",
  ],
];

const RAW_DIAGNOSTIC_ERROR_PATTERNS: RegExp[] = [
  /^\s*Invalid input:/i,
  /^\s*Calculation error:/i,
  /^\s*Failed to parse result:/i,
  /^\s*Internal server error:/i,
  /^\s*Error evaluating input:/i,
  /Could not tokenize expression/i,
  /unexpected EOF/i,
  /Traceback/i,
  /Disallowed syntax/i,
  /\(<unknown>,\s*line \d+\)/i,
];

function polishFeedbackText(verdict: string, rawText?: string | null): string {
  const sanitized = sanitizeCheckMessage(verdict, rawText).trim();
  if (!sanitized) return "";

  for (const [pattern, replacement] of INTERNAL_TONE_REWRITES) {
    if (pattern.test(sanitized)) {
      return replacement;
    }
  }

  if (RAW_DIAGNOSTIC_ERROR_PATTERNS.some((re) => re.test(sanitized))) {
    return sanitizeCheckMessage("invalid input", sanitized);
  }

  return sanitized;
}

/** Map a check verdict and problem state to one of the 4 calm Result Card tones. */
export function getResultCardTone(
  lastCheck: CheckResult,
  state?: ProblemState | null
): ResultCardTone {
  if (state?.skipped || lastCheck.verdict === "skipped") {
    return "skipped";
  }
  if (lastCheck.verdict === "correct") {
    return "correct";
  }
  if (
    lastCheck.verdict === "equivalent_not_in_form" ||
    lastCheck.verdict === "partial" ||
    lastCheck.verdict === "invalid input" ||
    lastCheck.verdict === "parse_error"
  ) {
    return "almost";
  }
  return "wrong";
}

/** Return the plain-language heading for a Result Card. */
export function getResultCardTitle(
  lastCheck: CheckResult,
  tone: ResultCardTone
): string {
  if (tone === "correct") return "Correct";
  if (tone === "skipped") return "Skipped";
  if (tone === "wrong") return "Not quite";
  if (lastCheck.verdict === "equivalent_not_in_form") {
    return "Almost — check the form";
  }
  if (lastCheck.verdict === "partial") {
    return "Almost";
  }
  return "Check your input";
}

/**
 * Pick one concise learner-facing diagnostic line from the check result,
 * reusing existing messages, removing internal jargon, and never leaking raw errors.
 */
export function formatDiagnosticBody(
  lastCheck: CheckResult,
  problem?: Pick<Problem, "commonTrapTag" | "answerSpec">,
  state?: ProblemState | null,
  mistakeTags: MistakeTag[] = []
): string | null {
  const tone = getResultCardTone(lastCheck, state);
  const cleanMsg = polishFeedbackText(lastCheck.verdict, lastCheck.message);

  if (tone === "skipped") {
    return null;
  }

  const rawDiag = lastCheck.diagnostics?.find((d) => d.message?.trim())?.message;
  const diagMsg = rawDiag ? polishFeedbackText(lastCheck.verdict, rawDiag) : "";

  let trapLabel = "";
  if (lastCheck.verdict === "incorrect" || lastCheck.verdict === "partial") {
    if (
      problem?.answerSpec?.type === "choice" &&
      Array.isArray(problem.answerSpec.options) &&
      state?.userInput
    ) {
      const chosen = problem.answerSpec.options.find(
        (o) => String(o.id).trim() === state.userInput.trim()
      );
      const choiceTrap = chosen?.trapTag || chosen?.tag;
      if (choiceTrap) {
        trapLabel = mistakeTags.find((t) => t.id === choiceTrap)?.label || "";
      }
    }
    if (!trapLabel && lastCheck.trapMatched && problem?.commonTrapTag) {
      trapLabel =
        mistakeTags.find((t) => t.id === problem.commonTrapTag)?.label || "";
    }
  }

  const isGenericMsg = !cleanMsg || GENERIC_RESULT_MESSAGES.has(cleanMsg.toLowerCase());

  if (!isGenericMsg && (!diagMsg || diagMsg === cleanMsg || /^Dimension mismatch:/i.test(diagMsg))) {
    return cleanMsg;
  }

  if (diagMsg) {
    if (!isGenericMsg && cleanMsg !== diagMsg) {
      return `${cleanMsg} ${diagMsg}`;
    }
    return diagMsg;
  }

  if (!isGenericMsg) {
    return cleanMsg;
  }

  if (trapLabel) {
    return trapLabel;
  }

  return null;
}

/** Count substantive (non-parse-error) attempts recorded on a problem in the current cycle. */
export function getSubstantiveAttemptCount(state?: ProblemState | null): number {
  return cycleAttempts(state?.attempts, state?.cycleStartedAt).filter((a) =>
    isSubstantiveVerdict(a.verdict)
  ).length;
}

/** Build the complete presentation model for the Result Card without mutating state. */
export function buildResultCardModel(params: {
  lastCheck: CheckResult;
  state: ProblemState;
  problem?: Pick<Problem, "commonTrapTag" | "answerSpec">;
  mistakeTags?: MistakeTag[];
  isLastQuestion?: boolean;
  preferBackAction?: boolean;
}): ResultCardModel {
  const {
    lastCheck,
    state,
    problem,
    mistakeTags = [],
    isLastQuestion = false,
    preferBackAction = false,
  } = params;
  const tone = getResultCardTone(lastCheck, state);
  const title = getResultCardTitle(lastCheck, tone);
  const body = formatDiagnosticBody(lastCheck, problem, state, mistakeTags);
  const attemptCount = getSubstantiveAttemptCount(state);
  const attemptNumber = attemptCount > 0 ? attemptCount : null;

  let actionKind: ResultCardActionKind | null = null;
  if (tone === "correct") {
    actionKind = preferBackAction ? "back" : isLastQuestion ? "review" : "next";
  } else if (tone === "almost" || tone === "wrong") {
    actionKind = "retry";
  } else if (tone === "skipped" && canRevealSteps(state)) {
    actionKind = "show_steps";
  }

  const resultKey = [
    tone,
    lastCheck.verdict,
    state.attempts?.length ?? 0,
    lastCheck.message || "",
  ].join(":");

  return {
    tone,
    title,
    body,
    components: lastCheck.components || [],
    attemptNumber,
    actionKind,
    resultKey,
  };
}

/** Return true for multiple-choice questions (standard or line-choice). */
export function isChoiceQuestion(problem: Pick<Problem, "answerSpec">): boolean {
  return problem.answerSpec?.type === "choice";
}

/** Determine whether choice options are disabled (while checking, skipped, or awaiting "Try again"). */
export function isChoiceInteractionLocked(params: {
  isChecking: boolean;
  lastCheck?: CheckResult | null;
  skipped?: boolean;
  retryUnlocked: boolean;
}): boolean {
  if (params.isChecking || params.skipped) return true;
  if (!params.lastCheck) return false;
  if (params.lastCheck.verdict === "correct") return true;
  if (isSubstantiveVerdict(params.lastCheck.verdict)) {
    return !params.retryUnlocked;
  }
  return false;
}

/** Derive option result styling for choice questions without revealing unchosen answers. */
export function getChoiceResultStatus(params: {
  isChecking: boolean;
  lastCheck?: CheckResult | null;
  skipped?: boolean;
}): ChoiceResultStatus {
  if (params.isChecking || params.skipped || !params.lastCheck) return null;
  if (params.lastCheck.verdict === "correct") return "correct";
  if (
    params.lastCheck.verdict === "incorrect" ||
    params.lastCheck.verdict === "partial"
  ) {
    return "wrong";
  }
  return null;
}

/** Map key "1"-"9" to the matching choice option (by numeric id or 1-based position). */
export function resolveChoiceKeyOption(
  key: string,
  options?: ChoiceOption[]
): ChoiceOption | null {
  if (!options || options.length === 0 || !/^[1-9]$/.test(key)) return null;
  const byId = options.find((opt) => opt.id.trim() === key);
  if (byId) return byId;
  const idx = Number(key) - 1;
  return idx >= 0 && idx < options.length ? options[idx] : null;
}

/** Return true when a keyboard event originated inside a text input or modal dialog. */
export function isEditableEventTarget(target: EventTarget | null): boolean {
  if (!target || typeof target !== "object") return false;
  const el = target as {
    tagName?: string;
    isContentEditable?: boolean;
    closest?: (selector: string) => unknown;
  };
  const tag = (el.tagName || "").toUpperCase();
  if (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    tag === "MATH-FIELD" ||
    el.isContentEditable
  ) {
    return true;
  }
  if (typeof el.closest === "function") {
    return Boolean(el.closest('[role="alertdialog"], [role="dialog"]'));
  }
  return false;
}

/** Guarded auto-submit helper for choice clicks and 1-9 key presses. */
export async function submitChoiceSelection(params: {
  optionId: string;
  disabled: boolean;
  isChecking: boolean;
  onStart: (optionId: string) => void;
  onInputChange: (optionId: string) => void;
  onCheckAnswer: (optionId?: string) => Promise<void> | void;
  onFinish: () => void;
}): Promise<boolean> {
  if (params.disabled || params.isChecking) return false;
  params.onStart(params.optionId);
  params.onInputChange(params.optionId);
  try {
    await params.onCheckAnswer(params.optionId);
  } finally {
    params.onFinish();
  }
  return true;
}
