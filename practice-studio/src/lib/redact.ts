import {
  AnswerSpec,
  AttemptRecord,
  ChoiceOption,
  CodeExample,
  DrillDocument,
  Problem,
  ProblemState,
  RedactedVariant,
  Step,
  VariantSessionRecord,
  WorkedExampleVariant,
} from "../types/drill";
import {
  canRevealVerifiedAnswer,
  canShowReferenceSolution,
  isSubstantiveVerdict,
} from "./reviewGuard";
import { cycleAttempts, cycleOriginalAttempts, isInCycle } from "./similarTabs";
import { hasCheckpointHint } from "./studioRules";

/**
 * Secret fields stripped by `redactProblem` / `redactDrill` before sending a drill to the browser:
 *
 * 1. Problem-level fields ALWAYS stripped:
 *    - `hiddenTests`: hidden test cases for PRG execution problems
 *    - `trapValue`: expected trap answer value used by `math_engine.answer_check`
 *    - `trapMutant`: buggy mutant code for PRG trap verification
 *    - `mutants`: list of trap mutant objects (`{ name, code }`)
 *    - `trapDerivation`: derivation/formula of how the trap answer was constructed
 *    - `trapGivens`: intermediate parameters/givens used to construct the trap
 *    - `trapKind`: internal trap classification
 *    - `flawTag`: internal flaw classification tag
 *    - `verify`: verification metadata (`{ source, flaw, trapValue }`)
 *    - `blindSolve`: blind-solver output (`{ setup, strategy, steps, answer, check, reverse, ... }`)
 *    - `review`: reviewer subagent verdict and notes (`{ id, verdict, note }`)
 *    - `contextCheck`: context-check subagent verdict and notes (`{ verdict, note }`)
 *    - `qualityGates`: quality gate audit results (`G1`, `G2`, `G4`, `G6`, `antiLeak`, ...)
 *    - `givens`: template generator givens / intermediate values
 *    - `constants`: template generator constants / intermediate values
 *    - `starterLintExpected`: internal lint gate metadata
 *
 * 2. Problem-level fields stripped UNTIL unlocked by learner `state`:
 *    - `display`, `plainText` (the hidden "Show equation set-up" box and CAS plain-text):
 *      stripped until the problem is checked/answered (`canRevealVerifiedAnswer`) or
 *      explicitly revealed (`setupRevealedBeforeAnswer` / `attempts[].setupRevealed`).
 *    - `steps`, `answerDisplay`, `answerPlain` (step-by-step derivation and verified answer):
 *      stripped until the problem is checked/answered (`canRevealVerifiedAnswer`) or
 *      explicitly revealed (`solutionRevealedBeforeAnswer` / `attempts[].solutionRevealed`).
 *    - `solutionCode` (PRG reference implementation):
 *      stripped until the latest code review record has `verdict === "pass"` (`canShowReferenceSolution`).
 *
 * 3. `answerSpec` fields ALWAYS stripped:
 *    - `value`: expected scalar / expression / interval answer
 *    - `values`: expected tuple / solution_set answer values
 *    - `components`: expected vector components
 *    - `correct`: correct option ID for multiple-choice problems
 *    - `accepted`: list of accepted answer strings
 *    - `tokens`: expected output token sequence for `predict_output` / `code_output`
 *    - `correctLine`: buggy line number for `line_number` / `find_bug`
 *    - `flawExplanation`: explanation of the flaw on `correctLine`
 *    - `trapValue`: trap answer value if present on `answerSpec`
 *    - `flawTag`: flaw tag if present on `answerSpec`
 *
 * 4. `answerSpec.options[]` fields ALWAYS stripped:
 *    - `provenance`: distractor derivation string on multiple-choice options
 */

export const ALWAYS_STRIPPED_PROBLEM_FIELDS = [
  "hiddenTests",
  "trapValue",
  "trapMutant",
  "mutants",
  "trapDerivation",
  "trapGivens",
  "trapKind",
  "flawTag",
  "verify",
  "blindSolve",
  "review",
  "contextCheck",
  "qualityGates",
  "givens",
  "constants",
  "starterLintExpected",
] as const;

export const CONDITIONAL_STRIPPED_PROBLEM_FIELDS = [
  "display",
  "plainText",
  "steps",
  "answerDisplay",
  "answerPlain",
  "solutionCode",
] as const;

export const STRIPPED_ANSWER_SPEC_FIELDS = [
  "value",
  "values",
  "components",
  "correct",
  "accepted",
  "tokens",
  "correctLine",
  "flawExplanation",
  "trapValue",
  "flawTag",
] as const;

export const STRIPPED_OPTION_FIELDS = ["provenance"] as const;

export type RevealPart = "steps" | "display" | "solution";

const DEFAULT_MATH_PLACEHOLDER_BY_TYPE: Record<string, string> = {
  interval: "Enter interval, e.g. [a, b) or (-inf, a) U (a, inf)...",
};

const DEFAULT_MATH_PLACEHOLDER = "Enter final answer (press Enter to check)...";
const DEFAULT_CODE_PLACEHOLDER = "Enter predicted terminal output (press Enter to check)...";

/**
 * Unlock rule for math/code step-by-step derivations (`steps`, `answerDisplay`, `answerPlain`):
 * available once the problem has been checked/answered (`canRevealVerifiedAnswer`) or
 * the learner explicitly revealed steps before answering (`solutionRevealedBeforeAnswer`).
 */
export function canRevealSteps(state?: ProblemState | null): boolean {
  if (!state) return false;
  if (canRevealVerifiedAnswer(state)) return true;
  if (state.solutionRevealedBeforeAnswer) return true;
  if (
    state.reviewStepsRevealedAt &&
    isInCycle(state.reviewStepsRevealedAt, state.cycleStartedAt)
  ) {
    return true;
  }
  if (cycleOriginalAttempts(state).some((a) => a.solutionRevealed)) return true;
  return false;
}

/**
 * Unlock rule for math equation set-up (`display`, `plainText`):
 * available once the problem has been checked/answered (`canRevealVerifiedAnswer`) or
 * the learner explicitly revealed set-up before answering (`setupRevealedBeforeAnswer`).
 */
export function canRevealDisplay(state?: ProblemState | null): boolean {
  if (!state) return false;
  if (canRevealVerifiedAnswer(state)) return true;
  if (state.setupRevealedBeforeAnswer) return true;
  if (
    state.reviewSetupRevealedAt &&
    isInCycle(state.reviewSetupRevealedAt, state.cycleStartedAt)
  ) {
    return true;
  }
  if (cycleOriginalAttempts(state).some((a) => a.setupRevealed)) return true;
  return false;
}

/**
 * Unlock rule for PRG reference `solutionCode`:
 * available only when `canShowReferenceSolution(state)` is true (latest review verdict is "pass").
 */
export function canRevealSolution(state?: ProblemState | null): boolean {
  return canShowReferenceSolution(state);
}

export function isPartUnlocked(part: RevealPart, state?: ProblemState | null): boolean {
  if (part === "steps") return canRevealSteps(state);
  if (part === "display") return canRevealDisplay(state);
  if (part === "solution") return canRevealSolution(state);
  return false;
}

/** Unlock rule for variant step-by-step derivation: after a substantive attempt in the current cycle or explicit reveal/give-up. */
export function canRevealVariantSteps(
  record?: VariantSessionRecord | null,
  cycleStartedAt?: string | null
): boolean {
  if (!record) return false;
  const attemptsInCycle = cycleAttempts(record.attempts, cycleStartedAt);
  if (attemptsInCycle.some((a) => isSubstantiveVerdict(a?.verdict))) {
    return true;
  }
  if (record.stepsRevealed) {
    if (!cycleStartedAt) return true;
    if (record.servedAt && record.servedAt >= cycleStartedAt) return true;
  }
  return false;
}

/**
 * Strip bank `variantId`s, `variantsSeen`/`variantsAttempted`, legacy `activeVariant`,
 * and variant trap tags from `ProblemState` before sending it to the browser so
 * method/archetype names never leak.
 */
export function redactProblemStateForClient(
  state?: ProblemState | null
): ProblemState | undefined {
  if (!state || typeof state !== "object") return undefined;
  const copy: ProblemState = { ...state };
  delete copy.variantsSeen;
  delete copy.variantsAttempted;
  delete (copy as unknown as Record<string, unknown>).activeVariant;
  if (state.variants && typeof state.variants === "object") {
    const cleanVariants: Record<string, VariantSessionRecord> = {};
    for (const [token, rec] of Object.entries(state.variants)) {
      if (!rec || typeof rec !== "object") continue;
      const cleanAttempts: AttemptRecord[] = Array.isArray(rec.attempts)
        ? rec.attempts.map((a) => {
            const attCopy: AttemptRecord = { ...a };
            delete attCopy.matchedTrap;
            return attCopy;
          })
        : [];
      cleanVariants[token] = {
        role: rec.role === "example" ? "example" : "try",
        attempts: cleanAttempts,
        ...(typeof rec.hintsRevealed === "number" ? { hintsRevealed: rec.hintsRevealed } : {}),
        ...(rec.setupRevealed ? { setupRevealed: true } : {}),
        ...(rec.stepsRevealed ? { stepsRevealed: true } : {}),
        ...(typeof rec.durationMs === "number" ? { durationMs: rec.durationMs } : {}),
        servedAt: rec.servedAt,
      };
    }
    copy.variants = cleanVariants;
  }
  return copy;
}

export function extractRevealedPart(
  problem: Partial<Problem>,
  part: RevealPart
):
  | { part: "steps"; steps: Step[]; answerDisplay: string; answerPlain: string }
  | { part: "display"; display: string; plainText: string }
  | { part: "solution"; solutionCode: string } {
  if (part === "steps") {
    return {
      part: "steps",
      steps: Array.isArray(problem.steps) ? problem.steps : [],
      answerDisplay: problem.answerDisplay ?? "",
      answerPlain: problem.answerPlain ?? "",
    };
  }
  if (part === "display") {
    return {
      part: "display",
      display: problem.display ?? "",
      plainText: problem.plainText ?? "",
    };
  }
  return {
    part: "solution",
    solutionCode: problem.solutionCode ?? "",
  };
}

function collectSecretAnswerTokens(problem: Partial<Problem>): string[] {
  const acceptedList: string[] = [];
  const pushToken = (val: unknown) => {
    if (val === undefined || val === null) return;
    const s = String(val).toLowerCase().trim();
    if (s.length >= 2) {
      acceptedList.push(s);
    }
  };

  const spec = problem.answerSpec;
  if (spec) {
    if (Array.isArray(spec.accepted)) {
      spec.accepted.forEach(pushToken);
    }
    if (spec.value !== undefined) {
      pushToken(spec.value);
    }
    if (Array.isArray(spec.values)) {
      spec.values.forEach(pushToken);
    }
    if (Array.isArray(spec.tokens)) {
      spec.tokens.forEach(pushToken);
    }
  }
  if (problem.answerPlain) {
    pushToken(problem.answerPlain);
  }
  if (problem.answerDisplay) {
    pushToken(problem.answerDisplay);
    const raw = String(problem.answerDisplay)
      .replace(/[\$\\]/g, "")
      .replace(/\\[a-zA-Z]+/g, "")
      .replace(/\^\{\\circ\}/g, "")
      .trim()
      .toLowerCase();
    if (raw.length >= 2) {
      acceptedList.push(raw);
    }
  }
  return acceptedList;
}

/**
 * Scrub `inputHint` on the server against secret answer fields so no answer leak reaches the client.
 */
export function sanitizeInputHint(problem: Partial<Problem>): string | undefined {
  const hint = problem.inputHint;
  if (!hint || typeof hint !== "string") return undefined;

  const acceptedList = collectSecretAnswerTokens(problem);
  const lowerHint = hint.toLowerCase();
  const hasLeak = acceptedList.some((ans) => lowerHint.includes(ans));
  if (!hasLeak) return hint;

  const stripped = hint.replace(/\s*\([^)]*e\.g\.[^)]*\)/gi, "").trim();
  if (stripped && !acceptedList.some((ans) => stripped.toLowerCase().includes(ans))) {
    return stripped;
  }
  return undefined;
}

function isCodeProblem(problem: Partial<Problem>, subject?: "MATH" | "PRG"): boolean {
  return (
    subject === "PRG" ||
    Boolean(problem.codeSnippet) ||
    Boolean(problem.workspaceFile) ||
    problem.codeType === "predict-output" ||
    problem.codeType === "find-bug" ||
    ["code_output", "predict_output", "line_number", "find_bug"].includes(
      problem.answerSpec?.type || ""
    )
  );
}

/**
 * Compute the safe input placeholder on the server so the client does not need
 * `answerSpec.accepted`, `answerPlain`, or `answerDisplay`.
 */
export function computeSafePlaceholder(
  problem: Partial<Problem>,
  subject?: "MATH" | "PRG"
): string {
  const fallback = isCodeProblem(problem, subject)
    ? DEFAULT_CODE_PLACEHOLDER
    : (problem.answerSpec?.type && DEFAULT_MATH_PLACEHOLDER_BY_TYPE[problem.answerSpec.type]) ||
      DEFAULT_MATH_PLACEHOLDER;

  const safeHint = sanitizeInputHint(problem);
  return safeHint || fallback;
}

/**
 * Strip secret answer fields from `answerSpec`, keeping only `type`, choice `options`
 * (without `provenance`), and non-secret format/unit/variable metadata.
 */
function redactAnswerSpec(spec?: AnswerSpec | null): AnswerSpec {
  if (!spec || typeof spec !== "object") {
    return { type: "text" };
  }
  const copy: Record<string, unknown> = { ...spec };
  for (const field of STRIPPED_ANSWER_SPEC_FIELDS) {
    delete copy[field];
  }
  if (Array.isArray(spec.options)) {
    copy.options = spec.options.map((opt) => {
      if (!opt || typeof opt !== "object") return opt;
      const optCopy: Record<string, unknown> = { ...(opt as ChoiceOption) };
      for (const field of STRIPPED_OPTION_FIELDS) {
        delete optCopy[field];
      }
      return optCopy as unknown as ChoiceOption;
    });
  }
  return copy as unknown as AnswerSpec;
}

/**
 * Pure function that removes secret answer material from a single problem according to `state`.
 */
export function redactProblem(
  problem: Problem,
  state?: ProblemState | null,
  subject?: "MATH" | "PRG"
): Problem {
  const effectiveState = state !== undefined ? state : problem.state;
  const safeHint = sanitizeInputHint(problem);
  const placeholder = computeSafePlaceholder(problem, subject);
  const hasSetup = Boolean(problem.hasSetup || problem.display || problem.plainText);
  const hiddenTestCount =
    typeof problem.hiddenTestCount === "number"
      ? problem.hiddenTestCount
      : Array.isArray(problem.hiddenTests)
      ? problem.hiddenTests.length
      : undefined;

  const raw: Record<string, unknown> = { ...problem };

  for (const field of ALWAYS_STRIPPED_PROBLEM_FIELDS) {
    delete raw[field];
  }

  if (!canRevealDisplay(effectiveState)) {
    delete raw.display;
    delete raw.plainText;
  }

  if (!canRevealSteps(effectiveState)) {
    delete raw.steps;
    delete raw.answerDisplay;
    delete raw.answerPlain;
  }

  if (!canRevealSolution(effectiveState)) {
    delete raw.solutionCode;
  }

  if (problem.answerSpec) {
    raw.answerSpec = redactAnswerSpec(problem.answerSpec);
  }
  if (Array.isArray(problem.examples)) {
    raw.examples = problem.examples.map((ex) => {
      if (!ex || typeof ex !== "object") return ex;
      const sanitized: CodeExample = {
        input: ex.input,
        output: ex.output,
        ...(ex.explanation !== undefined ? { explanation: ex.explanation } : {}),
      };
      return sanitized;
    });
  }
  raw.placeholder = placeholder;
  raw.hasSetup = hasSetup;

  if (safeHint !== undefined) {
    raw.inputHint = safeHint;
  } else {
    delete raw.inputHint;
  }

  if (hiddenTestCount !== undefined) {
    raw.hiddenTestCount = hiddenTestCount;
  }

  if (state !== undefined) {
    if (state === null) {
      delete raw.state;
    } else {
      raw.state = redactProblemStateForClient(state);
    }
  } else if (raw.state && typeof raw.state === "object") {
    raw.state = redactProblemStateForClient(raw.state as ProblemState);
  }

  return raw as unknown as Problem;
}

/**
 * Pure function that redacts every problem in a drill document before sending it to the browser.
 */
export function redactDrill<T extends DrillDocument>(doc: T): T {
  const subject: "MATH" | "PRG" =
    doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-") ? "PRG" : "MATH";
  return {
    ...doc,
    problems: Array.isArray(doc.problems)
      ? doc.problems.map((p) => redactProblem(p, p.state, subject))
      : [],
  };
}

/**
 * Pure function that prepares a single problem for a fresh Daily Review attempt:
 * resets the in-session state to unattempted (preserving only `revisitNote`) so no steps,
 * answers, equation set-up, or reference solutions are leaked from past attempts, and
 * strips trap tags and archetype keys before the learner answers.
 */
export function redactProblemForReview(
  problem: Problem,
  subject?: "MATH" | "PRG",
  cycleStartedAt?: string
): Problem {
  const startedAt =
    typeof cycleStartedAt === "string" && cycleStartedAt.trim()
      ? cycleStartedAt.trim()
      : new Date().toISOString();
  const cleanState: ProblemState = {
    userInput: "",
    userCode: problem.starterCode || problem.codeSnippet || "",
    score: null,
    divergedStep: null,
    mistakes: [],
    mistakeNote: "",
    ...(problem.state?.revisitNote ? { revisitNote: problem.state.revisitNote } : {}),
    skipped: false,
    lastCheck: null,
    lastTestReport: null,
    attempts: [],
    hintsRevealed: 0,
    setupRevealedBeforeAnswer: false,
    solutionRevealedBeforeAnswer: false,
    durationMs: 0,
    cycleStartedAt: startedAt,
  };

  const base = redactProblem(problem, cleanState, subject) as unknown as Record<string, unknown>;
  delete base.commonTrapTag;
  delete base.archetypeKey;
  delete base.archetype;
  base.templateKey = "";

  if (base.answerSpec && typeof base.answerSpec === "object") {
    const specCopy: Record<string, unknown> = { ...(base.answerSpec as Record<string, unknown>) };
    delete specCopy.commonTrapTag;
    if (Array.isArray(specCopy.options)) {
      specCopy.options = (specCopy.options as Array<Record<string, unknown>>).map((opt) => {
        if (!opt || typeof opt !== "object") return opt;
        const optCopy: Record<string, unknown> = { ...opt };
        delete optCopy.trapTag;
        delete optCopy.tag;
        return optCopy;
      });
    }
    base.answerSpec = specCopy;
  }

  return base as unknown as Problem;
}

/**
 * Pure function that redacts every problem in a drill document for a fresh Daily Review session.
 */
export function redactDrillForReview<T extends DrillDocument>(
  doc: T,
  cycleStartedAt?: string
): T {
  const subject: "MATH" | "PRG" =
    doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-") ? "PRG" : "MATH";
  const startedAt =
    typeof cycleStartedAt === "string" && cycleStartedAt.trim()
      ? cycleStartedAt.trim()
      : new Date().toISOString();
  return {
    ...doc,
    problems: Array.isArray(doc.problems)
      ? doc.problems.map((p) => redactProblemForReview(p, subject, startedAt))
      : [],
    ...(doc.sessionSummary
      ? {
          sessionSummary: {
            ...doc.sessionSummary,
            mistakeCategories: [],
            divergedStepsSummary: "",
          },
        }
      : {}),
  };
}

/**
 * Zero-leak redaction for a bank variant served in `mode=try`:
 * strips every answer, step, display/plainText, trap, archetype, bank `variantId`, and internal metadata field.
 * Uses only the opaque per-problem `token` (e.g. "v1") as client identifier.
 */
export function redactVariantForTry(
  variant: Record<string, unknown>,
  token: string
): RedactedVariant {
  const safeToken = String(token || "v1");
  const asProblem = {
    ...(variant as unknown as Problem),
    id: safeToken,
    templateKey: "",
  };
  const redacted = redactProblem(asProblem, null, "MATH") as unknown as Record<string, unknown>;

  // Strip archetype / trap / bank ID / internal identifiers so mode=try never leaks method or trap.
  delete redacted.variantId;
  delete redacted.commonTrapTag;
  delete redacted.archetypeKey;
  delete redacted.sourceArchetype;
  delete redacted.archetype;
  delete redacted.templateKey;
  delete redacted.fingerprint;
  delete redacted.references;
  delete redacted.referenceBadges;

  if (redacted.answerSpec && typeof redacted.answerSpec === "object") {
    const specCopy: Record<string, unknown> = { ...(redacted.answerSpec as Record<string, unknown>) };
    delete specCopy.commonTrapTag;
    if (Array.isArray(specCopy.options)) {
      specCopy.options = (specCopy.options as Array<Record<string, unknown>>).map((opt) => {
        if (!opt || typeof opt !== "object") return opt;
        const optCopy: Record<string, unknown> = { ...opt };
        delete optCopy.trapTag;
        delete optCopy.tag;
        return optCopy;
      });
    }
    redacted.answerSpec = specCopy;
  }

  const hasHint = hasCheckpointHint(
    typeof variant.checkpointHint === "string" ? variant.checkpointHint : undefined
  );

  return {
    token: safeToken,
    id: safeToken,
    level: typeof redacted.level === "number" ? redacted.level : 1,
    ...(typeof redacted.levelLabel === "string" ? { levelLabel: redacted.levelLabel } : {}),
    ...(typeof redacted.category === "string" ? { category: redacted.category } : {}),
    ...(typeof redacted.context === "string" && redacted.context ? { context: redacted.context } : {}),
    prompt: String(redacted.prompt || ""),
    ...(redacted.figure ? { figure: redacted.figure as Problem["figure"] } : {}),
    ...(redacted.visual ? { visual: redacted.visual as Problem["visual"] } : {}),
    answerSpec: (redacted.answerSpec as AnswerSpec) || { type: "number" },
    ...(typeof redacted.inputHint === "string" ? { inputHint: redacted.inputHint } : {}),
    ...(typeof redacted.placeholder === "string" ? { placeholder: redacted.placeholder } : {}),
    hasSetup: Boolean(redacted.hasSetup),
    hasHint,
  };
}

/**
 * Format a bank variant as a fully solved worked example (`mode=example`),
 * returning only learner-facing prompt, figure, final answer, and steps with explain
 * under an opaque per-problem `token` (never leaking bank `variantId` or archetype).
 */
export function formatWorkedExampleVariant(
  variant: Record<string, unknown>,
  token: string
): WorkedExampleVariant {
  const safeToken = String(token || "v1");
  const rawSteps = Array.isArray(variant.steps) ? (variant.steps as Array<Record<string, unknown>>) : [];
  const steps: Step[] = rawSteps
    .filter((st) => st && typeof st === "object")
    .map((st) => ({
      ...(typeof st.latex === "string" ? { latex: st.latex } : {}),
      explain: typeof st.explain === "string" ? st.explain : "",
    }));

  return {
    token: safeToken,
    id: safeToken,
    level: typeof variant.level === "number" ? variant.level : 1,
    ...(typeof variant.levelLabel === "string" ? { levelLabel: variant.levelLabel } : {}),
    ...(typeof variant.category === "string" ? { category: variant.category } : {}),
    ...(typeof variant.context === "string" && variant.context ? { context: variant.context } : {}),
    prompt: String(variant.prompt || ""),
    ...(variant.figure ? { figure: variant.figure as Problem["figure"] } : {}),
    ...(variant.visual ? { visual: variant.visual as Problem["visual"] } : {}),
    answerDisplay: String(variant.answerDisplay ?? variant.answerPlain ?? ""),
    answerPlain: String(variant.answerPlain ?? ""),
    steps,
  };
}
