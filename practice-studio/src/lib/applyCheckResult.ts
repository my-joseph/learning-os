import { Problem, ProblemState, CheckResult, MistakeTag, AttemptRecord } from "../types/drill";

export interface ApplyCheckOptions {
  durationMs?: number;
  ts?: string;
  hintsRevealed?: number;
}

/**
 * Pure function to apply SymPy / Code check result to problem state.
 */
export function applyCheckResult(
  prob: Problem,
  inputVal: string,
  result: CheckResult,
  mistakeTags: MistakeTag[] = [],
  options: ApplyCheckOptions = {}
): ProblemState {
  const trimmed = (inputVal || "").trim();
  const ts = options.ts || new Date().toISOString();
  const currentAttempts = prob.state?.attempts || [];
  const currentMistakes = new Set(prob.state?.mistakes || []);

  // 1. Empty input (and not skipped) -> return unchanged state
  if (!trimmed && result.verdict !== "skipped") {
    return { ...prob.state };
  }

  // 4. Skip action
  if (result.verdict === "skipped") {
    currentMistakes.add("concept-gap");
    const attempt: AttemptRecord = {
      input: trimmed || "(Skipped)",
      ts,
      verdict: "skipped",
    };
    return {
      ...prob.state,
      userInput: trimmed || "(Skipped)",
      score: 0,
      skipped: true,
      mistakes: Array.from(currentMistakes),
      lastCheck: result,
      attempts: [...currentAttempts, attempt],
      hintsRevealed: options.hintsRevealed ?? prob.state?.hintsRevealed ?? 0,
      durationMs: (prob.state?.durationMs || 0) + (options.durationMs || 0),
    };
  }

  // Calculate score
  let autoScore = prob.state?.score ?? null;
  if (result.verdict === "correct") {
    autoScore = 1;
  } else if (result.verdict === "equivalent_not_in_form" || result.verdict === "partial") {
    autoScore = 0.5;
  } else if (result.verdict === "incorrect") {
    autoScore = 0;
  }

  const newMistakes = new Set(prob.state?.mistakes || []);
  let matchedTrapTag: string | undefined;

  // Diagnostics codes
  const diagCodes = (result.diagnostics || []).map((d) => d.code);
  const diagCodeSet = new Set(diagCodes);

  if (result.verdict === "incorrect") {
    // Choice option trapTag
    if (prob.answerSpec?.type === "choice" && Array.isArray(prob.answerSpec.options)) {
      const chosen = prob.answerSpec.options.find(
        (o) => String(o.id).trim() === trimmed
      );
      if (chosen && (chosen.trapTag || chosen.tag)) {
        const choiceTrap = chosen.trapTag || chosen.tag;
        if (choiceTrap) {
          newMistakes.add(choiceTrap);
          matchedTrapTag = choiceTrap;
        }
      }
    }

    // trapMatched -> problem.commonTrapTag
    if (result.trapMatched && prob.commonTrapTag) {
      newMistakes.add(prob.commonTrapTag);
      matchedTrapTag = prob.commonTrapTag;
    }

    // When trapMatched is true, attach ONLY commonTrapTag (do not attach autoFrom from diagnostics)
    // When trapMatched is false / absent, autoFrom works as before
    if (!result.trapMatched) {
      mistakeTags.forEach((tag) => {
        if (tag.autoFrom?.some((c) => diagCodeSet.has(c))) {
          newMistakes.add(tag.id);
        }
      });
    }

    // Fallback "unclassified" ONLY when no tag was attached
    if (newMistakes.size === 0) {
      newMistakes.add("unclassified");
    }
  } else if (result.verdict !== "correct") {
    mistakeTags.forEach((tag) => {
      if (tag.autoFrom?.some((c) => diagCodeSet.has(c))) {
        newMistakes.add(tag.id);
      }
    });
  }

  const attempt: AttemptRecord = {
    input: trimmed,
    ts,
    verdict: result.verdict,
    ...(diagCodes.length > 0 ? { diagnosticCodes: diagCodes } : {}),
    ...(matchedTrapTag ? { matchedTrap: matchedTrapTag } : {}),
  };

  return {
    ...prob.state,
    userInput: trimmed,
    score: autoScore,
    skipped: false,
    mistakes: Array.from(newMistakes),
    lastCheck: result,
    attempts: [...currentAttempts, attempt],
    hintsRevealed: options.hintsRevealed ?? prob.state?.hintsRevealed ?? 0,
    durationMs: (prob.state?.durationMs || 0) + (options.durationMs || 0),
  };
}

/**
 * Pure function to apply skip to a problem state.
 */
export function applySkip(
  prob: Problem,
  options: ApplyCheckOptions = {}
): ProblemState {
  const skipResult: CheckResult = {
    verdict: "skipped",
    message: "Skipped (Concept Gap / Unsure) — Review step-by-step solution below to solidify mental model.",
    components: [],
    diagnostics: [],
  };
  return applyCheckResult(prob, prob.state?.userInput || "(Skipped)", skipResult, [], options);
}

/**
 * Pure function to toggle diverged step.
 * Diverged does NOT attach any mistake tags!
 */
export function applyDivergedStep(
  prob: Problem,
  stepIdx: number
): ProblemState {
  const isCurrent = prob.state?.divergedStep === stepIdx;
  const newDiverged = isCurrent ? null : stepIdx;
  return {
    ...prob.state,
    divergedStep: newDiverged,
    score: prob.state?.score === null || prob.state?.score === 1 ? 0.5 : prob.state.score,
  };
}
