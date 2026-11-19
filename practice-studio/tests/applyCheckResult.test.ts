/**
 * Test suite for applyCheckResult (8 cases)
 * Run command: npx tsx practice-studio/tests/applyCheckResult.test.ts
 */
import { readFileSync } from "node:fs";
import {
  applyCheckResult,
  applySkip,
  applyDivergedStep,
  resetDrillForRetry,
  resetProblemForRetry,
  resetAnswerForReviewRetry,
} from "../src/lib/applyCheckResult";
import {
  CALM_PARSE_ERROR_MESSAGE,
  canRevealVerifiedAnswer,
} from "../src/lib/reviewGuard";
import { DrillDocument, Problem, MistakeTag } from "../src/types/drill";

function assert(condition: boolean, msg: string) {
  if (!condition) {
    throw new Error(`FAIL: ${msg}`);
  }
}

const mockMistakeTags: MistakeTag[] = [
  {
    id: "sign-error",
    name: "Sign Error",
    label: "Flipped positive/negative sign",
    autoFrom: ["whole_sign_flip", "off_by_sign"],
  },
  {
    id: "off-factor",
    name: "Scale Factor Trap",
    label: "Missing multiplier constant",
    autoFrom: ["off_by_factor"],
  },
];

function createBaseProblem(overrides?: Partial<Problem>): Problem {
  return {
    id: "Q01",
    templateKey: "sample-tpl",
    level: 1,
    levelLabel: "Level 1",
    category: "Core Skill",
    prompt: "Solve for x",
    commonTrapTag: "c01-place-value-shift",
    trapValue: "460",
    answerDisplay: "360",
    answerPlain: "360",
    checkpointHint: "Check the steps",
    steps: [],
    answerSpec: { type: "number", value: "360" },
    state: {
      userInput: "",
      score: null,
      divergedStep: null,
      mistakes: [],
      lastCheck: null,
      attempts: [],
      hintsRevealed: 0,
      durationMs: 0,
    },
    ...overrides,
  };
}

let passed = 0;

function runCase(name: string, fn: () => void) {
  try {
    fn();
    console.log(`[PASS] Case ${passed + 1}: ${name}`);
    passed++;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[FAIL] Case ${passed + 1}: ${name} -> ${msg}`);
    process.exit(1);
  }
}

// Case 1: ว่าง (Empty input)
runCase("Empty input returns unchanged state and logs no attempts", () => {
  const prob = createBaseProblem();
  const res = applyCheckResult(prob, "   ", {
    verdict: "incorrect",
    message: "Invalid",
    components: [],
    diagnostics: [],
  });
  assert(res.score === null, "Score should remain null");
  assert((res.attempts || []).length === 0, "No attempt should be logged for empty input");
  assert(res.mistakes.length === 0, "No mistakes should be added");
});

// Case 2: ผิดตรง trap (Wrong matching trapValue -> trapMatched: true)
runCase("Wrong answer matching trap sets trapMatched tag and logs attempt", () => {
  const prob = createBaseProblem();
  const res = applyCheckResult(
    prob,
    "460",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [],
      trapMatched: true,
    },
    mockMistakeTags,
    { durationMs: 1500, ts: "2026-11-08T12:00:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("c01-place-value-shift"), "Must attach prob.commonTrapTag");
  assert(!res.mistakes.includes("unclassified"), "Must not attach unclassified");
  assert(res.attempts?.length === 1, "Must log 1 attempt");
  assert(res.attempts![0].matchedTrap === "c01-place-value-shift", "Attempt must record matchedTrap");
  assert(res.durationMs === 1500, "DurationMs must accumulate");
});

// Case 3: ผิดไม่ตรง trap (Unmatched wrong answer)
runCase("Wrong answer not matching any trap attaches unclassified fallback", () => {
  const prob = createBaseProblem();
  const res = applyCheckResult(
    prob,
    "9999",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [],
      trapMatched: false,
    },
    mockMistakeTags,
    { durationMs: 2000, ts: "2026-11-08T12:01:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("unclassified"), "Must fallback to unclassified");
  assert(!res.mistakes.includes("c01-place-value-shift"), "Must not falsely attach commonTrapTag");
  assert(res.attempts?.length === 1, "Must log 1 attempt");
  assert(res.attempts![0].matchedTrap === undefined, "MatchedTrap should be undefined");
});

// Case 4: Skip (User skips problem)
runCase("Skip problem sets score 0, skipped true, and concept-gap without commonTrapTag", () => {
  const prob = createBaseProblem();
  const res = applySkip(prob, { durationMs: 800, ts: "2026-11-08T12:02:00Z" });
  assert(res.score === 0, "Score must be 0");
  assert(res.skipped === true, "Skipped must be true");
  assert(res.mistakes.includes("concept-gap"), "Must include concept-gap");
  assert(!res.mistakes.includes("c01-place-value-shift"), "Must NOT include commonTrapTag");
  assert(res.attempts?.length === 1, "Must record skipped attempt");
  assert(res.attempts![0].verdict === "skipped", "Attempt verdict must be skipped");
});

// Case 5: ถูก (Correct answer)
runCase("Correct answer sets score 1, skipped false, and does not attach mistakes", () => {
  const prob = createBaseProblem();
  const res = applyCheckResult(
    prob,
    "360",
    {
      verdict: "correct",
      message: "Correct!",
      components: [],
      diagnostics: [],
    },
    mockMistakeTags,
    { durationMs: 3000, ts: "2026-11-08T12:03:00Z" }
  );
  assert(res.score === 1, "Score must be 1");
  assert(res.skipped === false, "Skipped must be false");
  assert(res.mistakes.length === 0, "No mistakes on correct answer");
  assert(res.attempts?.length === 1, "Must log correct attempt");
  assert(res.attempts![0].verdict === "correct", "Attempt verdict must be correct");
});

// Case 6: ปรนัยเลือกตัวลวงที่มี trapTag (Multiple choice distractor with trapTag)
runCase("Choice question selecting distractor with trapTag attaches option trapTag", () => {
  const prob = createBaseProblem({
    answerSpec: {
      type: "choice",
      options: [
        { id: "A", label: "360" },
        { id: "B", label: "460", trapTag: "choice-distractor-trap" },
      ],
    },
  });
  const res = applyCheckResult(
    prob,
    "B",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [],
    },
    mockMistakeTags,
    { durationMs: 1200, ts: "2026-11-08T12:04:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("choice-distractor-trap"), "Must attach choice trapTag");
  assert(!res.mistakes.includes("unclassified"), "Must not fallback to unclassified");
  assert(res.attempts![0].matchedTrap === "choice-distractor-trap", "Must record choice trapTag in attempt");
});

// Case 7: ผิดที่มี diagnostic ตรง autoFrom (Diagnostics matching autoFrom)
runCase("Wrong answer with diagnostic matching autoFrom attaches mapped tag without unclassified", () => {
  const prob = createBaseProblem();
  const res = applyCheckResult(
    prob,
    "-360",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [{ code: "whole_sign_flip", message: "Sign flipped" }],
    },
    mockMistakeTags,
    { durationMs: 2500, ts: "2026-11-08T12:05:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("sign-error"), "Must attach tag mapped from diagnostic");
  assert(!res.mistakes.includes("unclassified"), "Must not attach unclassified when autoFrom matched");
  assert(Boolean(res.attempts![0].diagnosticCodes?.includes("whole_sign_flip")), "Attempt must store diagnosticCodes");
});

// Case 8: ถูกหลังผิด (Correct after previously incorrect -> 0.5, not 1.0)
runCase("Correct answer after incorrect preserves previous attempts and caps score at 0.5", () => {
  const prob = createBaseProblem();
  // 1st attempt: wrong
  const st1 = applyCheckResult(
    prob,
    "999",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [],
    },
    mockMistakeTags,
    { durationMs: 1000, ts: "2026-11-08T12:06:00Z" }
  );
  assert(st1.score === 0, "First attempt score must be 0");
  assert(st1.attempts?.length === 1, "Must have 1 attempt");

  // 2nd attempt: correct
  const probWithSt1 = { ...prob, state: st1 };
  const st2 = applyCheckResult(
    probWithSt1,
    "360",
    {
      verdict: "correct",
      message: "Correct!",
      components: [],
      diagnostics: [],
    },
    mockMistakeTags,
    { durationMs: 2000, ts: "2026-11-08T12:07:00Z" }
  );
  assert(st2.score === 0.5, "Second attempt score after wrong attempt must be 0.5");
  assert(st2.attempts?.length === 2, "Must accumulate both attempts");
  assert(st2.attempts![0].verdict === "incorrect", "First attempt preserved");
  assert(st2.attempts![1].verdict === "correct", "Second attempt appended");
  assert(st2.durationMs === 3000, "Duration must accumulate across attempts");
});

// Case 9: Part D - trapMatched: true with diagnostics suppresses autoFrom tags
runCase("trapMatched: true with diagnostics attaches ONLY commonTrapTag and suppresses autoFrom", () => {
  const prob = createBaseProblem({ commonTrapTag: "c01-place-value-shift" });
  const res = applyCheckResult(
    prob,
    "460",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [{ code: "whole_sign_flip", message: "Sign flipped" }],
      trapMatched: true,
    },
    mockMistakeTags,
    { durationMs: 1200, ts: "2026-11-08T12:08:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("c01-place-value-shift"), "Must attach commonTrapTag");
  assert(!res.mistakes.includes("sign-error"), "Must NOT attach autoFrom tag when trapMatched is true");
  assert(!res.mistakes.includes("unclassified"), "Must NOT attach unclassified fallback");
  assert(res.mistakes.length === 1, "Must have exactly 1 mistake tag (commonTrapTag)");
  assert(Boolean(res.attempts![0].diagnosticCodes?.includes("whole_sign_flip")), "Attempt must still store diagnosticCodes");
  assert(res.attempts![0].matchedTrap === "c01-place-value-shift", "Attempt must record matchedTrap");
});

// Case 10: Part D - trapMatched: false with diagnostics attaches autoFrom tags normally
runCase("trapMatched: false with diagnostics attaches autoFrom tags normally", () => {
  const prob = createBaseProblem({ commonTrapTag: "c01-place-value-shift" });
  const res = applyCheckResult(
    prob,
    "-360",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [{ code: "whole_sign_flip", message: "Sign flipped" }],
      trapMatched: false,
    },
    mockMistakeTags,
    { durationMs: 1400, ts: "2026-11-08T12:09:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("sign-error"), "Must attach autoFrom tag when trapMatched is false");
  assert(!res.mistakes.includes("c01-place-value-shift"), "Must NOT attach commonTrapTag");
  assert(!res.mistakes.includes("unclassified"), "Must NOT attach unclassified when autoFrom matched");
  assert(Boolean(res.attempts![0].diagnosticCodes?.includes("whole_sign_flip")), "Attempt must store diagnosticCodes");
  assert(res.attempts![0].matchedTrap === undefined, "MatchedTrap should be undefined");
});

// Case 11: Part D - trapMatched: false with NO diagnostics falls back to unclassified
runCase("trapMatched: false without diagnostics and no trap falls back to unclassified", () => {
  const prob = createBaseProblem({ commonTrapTag: "c01-place-value-shift" });
  const res = applyCheckResult(
    prob,
    "12345",
    {
      verdict: "incorrect",
      message: "Incorrect",
      components: [],
      diagnostics: [],
      trapMatched: false,
    },
    mockMistakeTags,
    { durationMs: 1600, ts: "2026-11-08T12:10:00Z" }
  );
  assert(res.score === 0, "Score must be 0");
  assert(res.mistakes.includes("unclassified"), "Must fallback to unclassified");
  assert(!res.mistakes.includes("c01-place-value-shift"), "Must NOT attach commonTrapTag");
  assert(!res.mistakes.includes("sign-error"), "Must NOT attach autoFrom tag");
  assert(res.mistakes.length === 1, "Must have only unclassified tag");
  assert(res.attempts![0].matchedTrap === undefined, "MatchedTrap should be undefined");
});

const correctResult = {
  verdict: "correct" as const,
  message: "Correct",
  components: [],
  diagnostics: [],
  trapMatched: false,
};

runCase("Set-up viewed before answering marks the attempt as assisted and caps score at 0.5", () => {
  const prob = createBaseProblem();
  prob.state = { ...prob.state, setupRevealedBeforeAnswer: true };
  const res = applyCheckResult(prob, "360", correctResult, mockMistakeTags, { ts: "2026-11-13T10:00:00Z" });
  assert(res.score === 0.5, "Assisted correct answer must be capped at 0.5");
  assert(res.attempts![0].setupRevealed === true, "Attempt must record setupRevealed");
  assert(res.setupRevealedBeforeAnswer === true, "Flag must persist on state");
});

runCase("Set-up not viewed leaves the attempt unmarked", () => {
  const res = applyCheckResult(createBaseProblem(), "360", correctResult, mockMistakeTags, {
    ts: "2026-11-13T10:00:00Z",
  });
  assert(res.attempts![0].setupRevealed === undefined, "Independent attempt must not carry setupRevealed");
});

runCase("Skip after viewing set-up is also marked as assisted", () => {
  const prob = createBaseProblem();
  prob.state = { ...prob.state, setupRevealedBeforeAnswer: true };
  const res = applySkip(prob, { ts: "2026-11-13T10:00:00Z" });
  assert(res.attempts![res.attempts!.length - 1].setupRevealed === true, "Skip attempt must record setupRevealed");
});

// Partial answer matching the trap (omission trap on a solution set) tags the trap
runCase("Partial answer with trapMatched attaches commonTrapTag and records matchedTrap", () => {
  const prob = createBaseProblem();
  const res = applyCheckResult(
    prob,
    "7",
    { verdict: "partial", message: "Partial", components: [], diagnostics: [], trapMatched: true },
    mockMistakeTags,
    { ts: "2026-11-16T12:00:00Z" }
  );
  assert(res.score === 0.5, "Partial keeps 0.5");
  assert(res.mistakes.includes("c01-place-value-shift"), "Must attach prob.commonTrapTag");
  assert(res.attempts![0].matchedTrap === "c01-place-value-shift", "Attempt must record matchedTrap");
});

runCase("Solution steps viewed before answering marks the attempt as assisted", () => {
  const prob = createBaseProblem();
  prob.state = { ...prob.state, solutionRevealedBeforeAnswer: true };
  const res = applyCheckResult(prob, "360", correctResult, mockMistakeTags, { ts: "2026-11-16T10:00:00Z" });
  assert(res.attempts![0].solutionRevealed === true, "Attempt must record solutionRevealed");
  assert(res.solutionRevealedBeforeAnswer === true, "Flag must persist on state");
});

runCase("Solution steps not viewed leaves solutionRevealed unset", () => {
  const res = applyCheckResult(createBaseProblem(), "360", correctResult, mockMistakeTags, {
    ts: "2026-11-16T10:00:00Z",
  });
  assert(res.attempts![0].solutionRevealed === undefined, "Independent attempt must not carry solutionRevealed");
});

runCase("Skip after viewing solution steps is also marked as assisted", () => {
  const prob = createBaseProblem();
  prob.state = { ...prob.state, solutionRevealedBeforeAnswer: true };
  const res = applySkip(prob, { ts: "2026-11-16T10:00:00Z" });
  assert(res.attempts![res.attempts!.length - 1].solutionRevealed === true, "Skip attempt must record solutionRevealed");
});

runCase("Wrong answer then opening solution then correct caps score at 0.5 (d10d2e)", () => {
  const prob = createBaseProblem();
  const st1 = applyCheckResult(
    prob,
    "999",
    { verdict: "incorrect", message: "Incorrect", components: [], diagnostics: [] },
    mockMistakeTags,
    { ts: "2026-11-16T10:00:00Z" }
  );
  const probAssisted = { ...prob, state: { ...st1, solutionRevealedBeforeAnswer: true } };
  const st2 = applyCheckResult(probAssisted, "360", correctResult, mockMistakeTags, {
    ts: "2026-11-16T10:01:00Z",
  });
  assert(st2.score === 0.5, "Score must be capped at 0.5");
  assert(st2.attempts![1].solutionRevealed === true, "Second attempt must record solutionRevealed");
});

runCase("Hint revealed before correct caps score at 0.5", () => {
  const res = applyCheckResult(createBaseProblem(), "360", correctResult, mockMistakeTags, {
    hintsRevealed: 1,
    ts: "2026-11-16T10:02:00Z",
  });
  assert(res.score === 0.5, "Correct after hint must score 0.5");
});

runCase("Invalid input before correct does not penalize first-try score", () => {
  const prob = createBaseProblem();
  const st1 = applyCheckResult(
    prob,
    "[3, 21",
    { verdict: "invalid input", message: "Unbalanced brackets", components: [], diagnostics: [] },
    mockMistakeTags,
    { ts: "2026-11-16T10:03:00Z" }
  );
  assert(st1.score === null, "Invalid input must leave score null");
  assert(!canRevealVerifiedAnswer(st1), "Invalid input must not unlock verified answer");
  const st2 = applyCheckResult({ ...prob, state: st1 }, "360", correctResult, mockMistakeTags, {
    ts: "2026-11-16T10:04:00Z",
  });
  assert(st2.score === 1, "Format error before first substantive attempt should still score 1");
});

runCase("Raw SymPy/Python error in invalid input is sanitized to calm learner copy", () => {
  const prob = createBaseProblem();
  const st = applyCheckResult(
    prob,
    "(((",
    {
      verdict: "invalid input",
      message:
        "Invalid input: Could not tokenize expression: ('unexpected EOF in multi-line statement', (1, 0))",
      components: [],
      diagnostics: [],
    },
    mockMistakeTags,
    { ts: "2026-11-18T10:00:00Z" }
  );
  assert(
    st.lastCheck?.message === CALM_PARSE_ERROR_MESSAGE,
    `Expected calm message, got ${st.lastCheck?.message}`
  );
  assert(!canRevealVerifiedAnswer(st), "Sanitized invalid input must not unlock verified answer");
});

runCase("resetDrillForRetry and resetProblemForRetry start a new cycle while preserving history", () => {
  const sampleReview = {
    at: "2026-11-18T10:05:00Z",
    attempt: 1,
    codeHash: "sha256:abc",
    code: "// edited",
    tests: { passed: 1, total: 1, failed: [] },
    lint: [],
    typecheck: [],
    findings: [],
    verdict: "pass" as const,
    explain: null,
  };
  const dirtyProblem = createBaseProblem({
    display: "2x = 720",
    plainText: "2*x = 720",
    steps: [{ latex: "x = 360", explain: "Divide by 2" }],
    solutionCode: "export const x = 360;",
    starterCode: "// starter",
    state: {
      userInput: "360",
      userCode: "// edited",
      score: 0.5,
      divergedStep: 0,
      mistakes: ["sign-error"],
      mistakeNote: "Flipped sign",
      revisitNote: "Double-check negative signs",
      skipped: true,
      lastCheck: correctResult,
      lastTestReport: {
        allPassed: true,
        score: 1,
        passedCount: 1,
        totalCount: 1,
        visibleResults: [],
        hiddenPassed: 0,
        hiddenTotal: 0,
        executionTimeMs: 5,
      },
      attempts: [{ input: "360", ts: "2026-11-18T10:00:00Z", verdict: "correct" }],
      reviews: [sampleReview],
      hintsRevealed: 2,
      setupRevealedBeforeAnswer: true,
      solutionRevealedBeforeAnswer: true,
      durationMs: 42_000,
    },
  });

  const resetTs = "2026-11-20T01:00:00.000Z";
  const singleReset = resetProblemForRetry(dirtyProblem, resetTs);
  const sampleDoc: DrillDocument = {
    schemaVersion: "2.0",
    drillId: "DRL-MTH-TEST-01",
    subject: "MATH",
    unitCode: "MTH-TEST",
    unitTitle: "Test",
    chapterCode: "MTH-T01-C01",
    topicCode: "MTH-T01",
    unitNotionUrl: null,
    createdAt: "2026-11-18",
    config: { questionCount: 1, difficulty: "ALL", difficultyMode: "Mixed" },
    mistakeTags: [],
    problems: [dirtyProblem],
    sessionSummary: {
      practiceStatus: "Graded",
      score: 1,
      maxScore: 1,
      accuracyPct: 100,
      mistakeCategories: ["Sign Error"],
      divergedStepsSummary: "Q01",
      attemptDate: "2026-11-18",
    },
    localFilePath: "",
  };

  const allReset = resetDrillForRetry(sampleDoc, resetTs);
  assert(
    JSON.stringify(allReset.problems[0]) === JSON.stringify(singleReset),
    "resetDrillForRetry must match resetProblemForRetry field-for-field"
  );
  // History is preserved
  assert(singleReset.state.attempts?.length === 1, "attempt history must be preserved on reset");
  assert(singleReset.state.mistakes.includes("sign-error"), "mistakes must be preserved on reset");
  assert(singleReset.state.mistakeNote === "Flipped sign", "mistakeNote must be preserved on reset");
  assert(singleReset.state.revisitNote === "Double-check negative signs", "revisitNote must be preserved on reset");
  assert(singleReset.state.reviews?.length === 1, "reviews must be preserved on reset");
  assert(singleReset.state.cycleStartedAt === resetTs, "cycleStartedAt must be stamped to reset time");
  // Visible active state is cleared
  assert(singleReset.state.userInput === "", "userInput must be cleared");
  assert(singleReset.state.score === null, "score must be null");
  assert(singleReset.state.divergedStep === null, "divergedStep must be null");
  assert(singleReset.state.skipped === false, "skipped must be false");
  assert(singleReset.state.lastCheck === null, "lastCheck must be null");
  assert(singleReset.state.lastTestReport === null, "lastTestReport must be null");
  assert(singleReset.state.hintsRevealed === 0, "hintsRevealed must be 0");
  assert(singleReset.state.setupRevealedBeforeAnswer === false, "setupRevealedBeforeAnswer must be false");
  assert(singleReset.state.solutionRevealedBeforeAnswer === false, "solutionRevealedBeforeAnswer must be false");
  assert(singleReset.state.durationMs === 0, "durationMs must be 0");
  assert(singleReset.state.userCode === "// starter", "userCode must revert to starterCode");
  assert(!("display" in singleReset), "display must be stripped");
  assert(!("steps" in singleReset), "steps must be stripped");
  assert(!("answerDisplay" in singleReset), "answerDisplay must be stripped");
  assert(!("solutionCode" in singleReset), "solutionCode must be stripped");
  assert(allReset.sessionSummary.practiceStatus === "Ready", "sessionSummary status must reset to Ready");
  assert(allReset.sessionSummary.attemptDate === null, "attemptDate must reset to null");
  // Cycle-aware readers treat reset state as unattempted
  assert(!canRevealVerifiedAnswer(singleReset.state), "reset problem with prior attempts/reviews must count as unattempted in new cycle");

  const useDrillSrc = readFileSync("src/hooks/useDrill.ts", "utf8");
  assert(
    /handleResetAll[\s\S]*createTelemetryTimerState/.test(useDrillSrc),
    "handleResetAll must reset telemetry timer state"
  );
  assert(
    /handleResetAll[\s\S]*setActiveSteps\(\{\}\)/.test(useDrillSrc),
    "handleResetAll must clear activeSteps"
  );
});

runCase("review retry clears the answer but preserves progress history", () => {
  const state = {
    ...createBaseProblem().state,
    userInput: "27/32",
    score: 0,
    lastCheck: { ...correctResult, verdict: "incorrect" as const },
    attempts: [{ input: "27/32", ts: "2026-11-18T10:00:00Z", verdict: "incorrect" }],
    mistakes: ["sign-error"],
  };
  const reset = resetAnswerForReviewRetry(state);
  assert(reset.userInput === "", "answer field must clear");
  assert(reset.lastCheck === null, "stale result must clear");
  assert(reset.score === null, "stale score must clear");
  assert(reset.attempts?.length === 1, "attempt history must remain");
  assert(reset.mistakes?.[0] === "sign-error", "mistake history must remain");
});

// Extra: Diverged step does not attach mistake tags
const probDiverged = createBaseProblem();
const stDiv = applyDivergedStep(probDiverged, 1);
assert(stDiv.divergedStep === 1, "Diverged step must be set to 1");
assert(stDiv.mistakes.length === 0, "Diverged step must NOT attach commonTrapTag or any mistake tags");

console.log("\n=======================================================");
console.log(`ALL ${passed} TEST CASES PASSED SUCCESSFULLY!`);
console.log("=======================================================");
