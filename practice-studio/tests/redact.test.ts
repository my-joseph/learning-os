/**
 * Unit tests for drill redaction and reveal unlock rules (src/lib/redact.ts, /api/reveal, /api/check-answer).
 * Run: npx tsx tests/redact.test.ts
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { NextRequest } from "next/server";
import { getDrillsDataDir } from "../src/lib/paths";
import { startProblemCycle, writeProgress } from "../src/lib/progress";
import { resetProblemForRetry } from "../src/lib/applyCheckResult";
import {
  ALWAYS_STRIPPED_PROBLEM_FIELDS,
  CONDITIONAL_STRIPPED_PROBLEM_FIELDS,
  STRIPPED_ANSWER_SPEC_FIELDS,
  STRIPPED_OPTION_FIELDS,
  canRevealDisplay,
  canRevealSolution,
  canRevealSteps,
  computeSafePlaceholder,
  isPartUnlocked,
  redactDrill,
  redactProblem,
  sanitizeInputHint,
} from "../src/lib/redact";
import { GET as revealGET } from "../src/app/api/reveal/route";
import { POST as checkAnswerPOST } from "../src/app/api/check-answer/route";
import type { DrillDocument, Problem, ProblemState, ReviewRecord } from "../src/types/drill";

function collectDrillFiles(dir: string): string[] {
  const results: string[] = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectDrillFiles(full));
    } else if (entry.isFile() && entry.name.endsWith(".json")) {
      results.push(full);
    }
  }
  return results.sort();
}

const makeState = (overrides: Partial<ProblemState> = {}): ProblemState => ({
  userInput: "",
  score: null,
  divergedStep: null,
  mistakes: [],
  ...overrides,
});

const makeReview = (verdict: "pass" | "revise"): ReviewRecord => ({
  at: "2026-11-17T10:00:00Z",
  attempt: 1,
  codeHash: "sha256:test",
  code: "export function solve() { return 1; }",
  tests: { passed: 2, total: 2, failed: [] },
  lint: [],
  typecheck: [],
  findings: [],
  verdict,
  explain: null,
});

// ---------------------------------------------------------------------------
// 1. Redact every real drill under drills/data and assert zero secret leaks
// ---------------------------------------------------------------------------
const drillFiles = collectDrillFiles(getDrillsDataDir());
assert.ok(drillFiles.length > 0, "Expected real drill JSON files under drills/data");

let totalProblemsChecked = 0;
let mthDrillSample: { drillId: string; problemId: string } | null = null;
let prgDrillSample: { drillId: string; problemId: string } | null = null;

for (const filePath of drillFiles) {
  const rawText = fs.readFileSync(filePath, "utf-8");
  const rawDoc = JSON.parse(rawText) as DrillDocument;
  const rawSnapshot = JSON.stringify(rawDoc);

  const redacted = redactDrill(rawDoc);

  // Pure function check: input document must not be mutated
  assert.equal(
    JSON.stringify(rawDoc),
    rawSnapshot,
    `redactDrill must not mutate input document (${rawDoc.drillId})`
  );

  const redactedDocJson = JSON.stringify(redacted);

  for (let i = 0; i < (rawDoc.problems || []).length; i++) {
    totalProblemsChecked++;
    const origProb = rawDoc.problems[i] as unknown as Record<string, unknown>;
    const redProb = redacted.problems[i] as unknown as Record<string, unknown>;
    const loc = `${rawDoc.drillId}#${origProb.id}`;

    if (
      !mthDrillSample &&
      rawDoc.subject === "MATH" &&
      (origProb.answerSpec as { type?: string } | undefined)?.type === "number" &&
      origProb.display
    ) {
      mthDrillSample = { drillId: rawDoc.drillId, problemId: String(origProb.id) };
    }
    if (!prgDrillSample && rawDoc.subject === "PRG" && origProb.solutionCode) {
      prgDrillSample = { drillId: rawDoc.drillId, problemId: String(origProb.id) };
    }

    // UI-essential fields kept
    assert.equal(redProb.id, origProb.id, `${loc}: id must be kept`);
    assert.equal(redProb.prompt, origProb.prompt, `${loc}: prompt must be kept`);
    assert.equal(typeof redProb.placeholder, "string", `${loc}: placeholder must be computed`);
    assert.equal(
      redProb.hasSetup,
      Boolean(origProb.display || origProb.plainText),
      `${loc}: hasSetup must reflect display/plainText presence`
    );

    // Every always-stripped and conditional-stripped field must be absent on unattempted problems
    for (const secretKey of [
      ...ALWAYS_STRIPPED_PROBLEM_FIELDS,
      ...CONDITIONAL_STRIPPED_PROBLEM_FIELDS,
    ]) {
      assert.equal(
        secretKey in redProb,
        false,
        `${loc}: secret problem field '${secretKey}' must be stripped`
      );
    }

    // answerSpec secret fields must be absent
    const origSpec = (origProb.answerSpec || {}) as Record<string, unknown>;
    const redSpec = (redProb.answerSpec || {}) as Record<string, unknown>;
    assert.equal(redSpec.type, origSpec.type, `${loc}: answerSpec.type must be kept`);

    for (const specSecret of STRIPPED_ANSWER_SPEC_FIELDS) {
      assert.equal(
        specSecret in redSpec,
        false,
        `${loc}: answerSpec.${specSecret} must be stripped`
      );
    }

    if (Array.isArray(origSpec.options)) {
      assert.ok(Array.isArray(redSpec.options), `${loc}: choice options must be kept`);
      for (const opt of redSpec.options as Array<Record<string, unknown>>) {
        for (const optSecret of STRIPPED_OPTION_FIELDS) {
          assert.equal(
            optSecret in opt,
            false,
            `${loc}: option.${optSecret} must be stripped`
          );
        }
      }
    }

    // Assert accepted / expected answer strings do not appear in the redacted problem JSON
    const redProbJson = JSON.stringify(redProb);
    if (origSpec.type !== "choice") {
      const secretAnswerStrings: string[] = [];
      const addAns = (v: unknown) => {
        if (v === undefined || v === null) return;
        const s = String(v).trim();
        if (s) secretAnswerStrings.push(s);
      };
      addAns(origProb.answerPlain);
      addAns(origProb.answerDisplay);
      addAns(origSpec.value);
      if (Array.isArray(origSpec.values)) origSpec.values.forEach(addAns);
      if (Array.isArray(origSpec.accepted)) origSpec.accepted.forEach(addAns);

      for (const ans of secretAnswerStrings) {
        // Exact JSON string value must never appear as a JSON string in the redacted problem
        assert.equal(
          redProbJson.includes(JSON.stringify(ans)),
          false,
          `${loc}: exact answer value must not appear in redacted JSON`
        );
        // Substring check for non-trivial answer strings
        if (ans.length >= 4) {
          assert.equal(
            redProbJson.includes(ans),
            false,
            `${loc}: answer substring (len=${ans.length}) must not appear in redacted JSON`
          );
        }
      }
    }

    if (typeof origProb.solutionCode === "string" && origProb.solutionCode.trim()) {
      assert.equal(
        redactedDocJson.includes(JSON.stringify(origProb.solutionCode)),
        false,
        `${loc}: solutionCode must not appear in redacted JSON`
      );
    }
  }
}

assert.ok(totalProblemsChecked >= 200, `Expected >= 200 problems, checked ${totalProblemsChecked}`);

// ---------------------------------------------------------------------------
// 2. Server-side placeholder & inputHint sanitization tests
// ---------------------------------------------------------------------------
const leakingMathProblem: Problem = {
  id: "Q01",
  templateKey: "tpl",
  level: 1,
  levelLabel: "L1",
  category: "Algebra",
  prompt: "Solve for x.",
  display: "2x = 84",
  plainText: "2*x = 84",
  answerSpec: { type: "number", value: "42", accepted: ["42", "x=42"] },
  answerDisplay: "42",
  answerPlain: "42",
  inputHint: "Enter integer (e.g. 42)",
  checkpointHint: "Divide both sides by 2.",
  steps: [{ latex: "x = 42", explain: "Divide by 2." }],
  state: makeState(),
};

assert.equal(sanitizeInputHint(leakingMathProblem), "Enter integer");
assert.equal(computeSafePlaceholder(leakingMathProblem, "MATH"), "Enter integer");

const redactedLeaking = redactProblem(leakingMathProblem, null, "MATH");
assert.equal(redactedLeaking.inputHint, "Enter integer");
assert.equal(redactedLeaking.placeholder, "Enter integer");
assert.equal(redactedLeaking.hasSetup, true);
assert.equal("display" in redactedLeaking, false);
assert.equal("steps" in redactedLeaking, false);
assert.equal("value" in redactedLeaking.answerSpec, false);
assert.equal("accepted" in redactedLeaking.answerSpec, false);

// PRG examples & constraints stay visible before any attempt, while `call` is stripped server-side
const prgWithExamples: Problem = {
  id: "Q01",
  templateKey: "tpl",
  level: 1,
  levelLabel: "Foundation",
  category: "Core Skill",
  prompt: "Implement `searchInsert(nums, target)`.",
  starterCode: "export function searchInsert() { return 0; }",
  solutionCode: "export function searchInsert() { return 2; }",
  examples: [
    {
      input: "nums = [1, 3, 5, 6], target = 5",
      output: "2",
      explanation: "5 appears at index 2.",
      call: "searchInsert([1, 3, 5, 6], 5)",
    },
    {
      input: "nums = [1, 3, 5, 6], target = 2",
      output: "1",
      call: "searchInsert([1, 3, 5, 6], 2)",
    },
  ],
  constraints: ["1 <= nums.length <= 10^4"],
  answerSpec: { type: "code_output" },
  checkpointHint: "",
  state: makeState(),
};

const redactedExamplesProb = redactProblem(prgWithExamples, makeState(), "PRG");
assert.equal(redactedExamplesProb.examples?.length, 2);
assert.equal(redactedExamplesProb.examples?.[0].input, "nums = [1, 3, 5, 6], target = 5");
assert.equal(redactedExamplesProb.examples?.[0].output, "2");
assert.equal(redactedExamplesProb.examples?.[0].explanation, "5 appears at index 2.");
assert.equal("call" in (redactedExamplesProb.examples?.[0] ?? {}), false);
assert.equal("call" in (redactedExamplesProb.examples?.[1] ?? {}), false);
assert.deepEqual(redactedExamplesProb.constraints, ["1 <= nums.length <= 10^4"]);
assert.equal("solutionCode" in redactedExamplesProb, false);

// ---------------------------------------------------------------------------
// 3. Unlock rules unit tests
// ---------------------------------------------------------------------------
assert.equal(canRevealSteps(null), false);
assert.equal(canRevealDisplay(null), false);
assert.equal(canRevealSolution(null), false);

// Draft userInput alone does not unlock anything
const draftState = makeState({ userInput: "123" });
assert.equal(canRevealSteps(draftState), false);
assert.equal(canRevealDisplay(draftState), false);
assert.equal(canRevealSolution(draftState), false);

// Non-substantive verdicts ("invalid input" / "parse_error") must not unlock steps/display/solution
const invalidInputState = makeState({
  userInput: "(((",
  lastCheck: {
    verdict: "invalid input",
    message: "Couldn't read that — check brackets and operators.",
    components: [],
    diagnostics: [],
  },
  attempts: [{ input: "(((", ts: "2026-11-18T00:00:00Z", verdict: "invalid input" }],
});
assert.equal(canRevealSteps(invalidInputState), false);
assert.equal(canRevealDisplay(invalidInputState), false);
assert.equal(canRevealSolution(invalidInputState), false);
const afterInvalidInput = redactProblem(leakingMathProblem, invalidInputState, "MATH");
assert.equal("display" in afterInvalidInput, false);
assert.equal("steps" in afterInvalidInput, false);
assert.equal("answerDisplay" in afterInvalidInput, false);
assert.equal("answerPlain" in afterInvalidInput, false);

const parseErrorState = makeState({
  userInput: "abc",
  lastCheck: {
    verdict: "parse_error",
    message: "Could not read input.",
    components: [],
    diagnostics: [],
  },
  attempts: [{ input: "abc", ts: "2026-11-18T00:00:00Z", verdict: "parse_error" }],
});
assert.equal(canRevealSteps(parseErrorState), false);
assert.equal(canRevealDisplay(parseErrorState), false);
assert.equal(canRevealSolution(parseErrorState), false);

// Self-score alone without a substantive attempt/skip must not unlock steps/display/solution
const scoreOnlyState = makeState({ score: 1 });
assert.equal(canRevealSteps(scoreOnlyState), false);
assert.equal(canRevealDisplay(scoreOnlyState), false);
assert.equal(canRevealSolution(scoreOnlyState), false);

// Assisted setup reveal unlocks ONLY display/plainText, not steps or solutionCode
const setupAssistedState = makeState({ setupRevealedBeforeAnswer: true });
assert.equal(canRevealDisplay(setupAssistedState), true);
assert.equal(canRevealSteps(setupAssistedState), false);
assert.equal(canRevealSolution(setupAssistedState), false);
const afterSetupReveal = redactProblem(leakingMathProblem, setupAssistedState, "MATH");
assert.equal(afterSetupReveal.display, "2x = 84");
assert.equal(afterSetupReveal.plainText, "2*x = 84");
assert.equal("steps" in afterSetupReveal, false);
assert.equal("answerDisplay" in afterSetupReveal, false);

// Assisted steps reveal unlocks steps/answerDisplay/answerPlain
const stepsAssistedState = makeState({ solutionRevealedBeforeAnswer: true });
assert.equal(canRevealSteps(stepsAssistedState), true);
assert.equal(canRevealDisplay(stepsAssistedState), false);
assert.equal(canRevealSolution(stepsAssistedState), false);
const afterStepsReveal = redactProblem(leakingMathProblem, stepsAssistedState, "MATH");
assert.equal(afterStepsReveal.steps?.length, 1);
assert.equal(afterStepsReveal.answerDisplay, "42");
assert.equal(afterStepsReveal.answerPlain, "42");
assert.equal("display" in afterStepsReveal, false);
// Secret answerSpec fields stay stripped even after steps are revealed
assert.equal("value" in afterStepsReveal.answerSpec, false);

// Checked problem unlocks both steps and display, but not PRG solutionCode
const checkedState = makeState({
  lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
  attempts: [{ input: "10", ts: "2026-11-17T00:00:00Z", verdict: "incorrect" }],
});
assert.equal(canRevealSteps(checkedState), true);
assert.equal(canRevealDisplay(checkedState), true);
assert.equal(canRevealSolution(checkedState), false);

// PRG solutionCode unlocks ONLY on review pass
const prgReviseState = makeState({ reviews: [makeReview("revise")] });
assert.equal(canRevealSolution(prgReviseState), false);
assert.equal(isPartUnlocked("solution", prgReviseState), false);

const prgPassState = makeState({ reviews: [makeReview("pass")] });
assert.equal(canRevealSolution(prgPassState), true);
assert.equal(isPartUnlocked("solution", prgPassState), true);

// Reset cycle isolation: pre-reset attempts/flags do not unlock steps, display, or solution
const postResetState = makeState({
  attempts: [
    {
      input: "42",
      ts: "2026-11-17T10:00:00Z",
      verdict: "correct",
      setupRevealed: true,
      solutionRevealed: true,
    },
  ],
  reviews: [makeReview("pass")],
  cycleStartedAt: "2026-11-20T00:00:00Z",
});
assert.equal(canRevealSteps(postResetState), false, "pre-reset attempts must not unlock steps after Reset");
assert.equal(canRevealDisplay(postResetState), false, "pre-reset attempts must not unlock display after Reset");
assert.equal(canRevealSolution(postResetState), false, "pre-reset pass review must not unlock solution after Reset");

// Cycle-scoped review reveal timestamps unlock reveal in the current cycle without mutating original help flags
const reviewRevealState = makeState({
  ...postResetState,
  reviewSetupRevealedAt: "2026-11-20T00:01:00Z",
  reviewStepsRevealedAt: "2026-11-20T00:02:00Z",
});
assert.equal(canRevealDisplay(reviewRevealState), true);
assert.equal(canRevealSteps(reviewRevealState), true);
assert.equal(reviewRevealState.setupRevealedBeforeAnswer, undefined);
assert.equal(reviewRevealState.solutionRevealedBeforeAnswer, undefined);

// Review cycle with preserved original drill flags (lastCheck, skipped, setup/solution flags, stale review timestamps):
// NONE of the prior-cycle fields may unlock steps, display, or solution in the new cycle.
const activeReviewCycleWithPriorFlags = makeState({
  userInput: "42",
  score: 0.5,
  skipped: true,
  lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
  setupRevealedBeforeAnswer: true,
  solutionRevealedBeforeAnswer: true,
  reviewSetupRevealedAt: "2026-11-19T10:00:00Z",
  reviewStepsRevealedAt: "2026-11-19T10:01:00Z",
  attempts: [
    {
      input: "42",
      ts: "2026-11-17T10:00:00Z",
      verdict: "correct",
      setupRevealed: true,
      solutionRevealed: true,
    },
  ],
  reviews: [makeReview("pass")],
  cycleStartedAt: "2026-11-20T09:00:00Z",
});
assert.equal(
  canRevealSteps(activeReviewCycleWithPriorFlags),
  false,
  "prior-cycle lastCheck/skipped/solutionRevealedBeforeAnswer/stale reviewStepsRevealedAt must not unlock steps in new cycle"
);
assert.equal(
  canRevealDisplay(activeReviewCycleWithPriorFlags),
  false,
  "prior-cycle lastCheck/skipped/setupRevealedBeforeAnswer/stale reviewSetupRevealedAt must not unlock display in new cycle"
);
assert.equal(
  canRevealSolution(activeReviewCycleWithPriorFlags),
  false,
  "prior-cycle pass review must not unlock solution in new cycle"
);

// ---------------------------------------------------------------------------
// 4. Route handler integration tests (/api/reveal and /api/check-answer)
// ---------------------------------------------------------------------------
async function runRouteTests() {
  assert.ok(mthDrillSample, "Found sample MATH drill");
  assert.ok(prgDrillSample, "Found sample PRG drill");

  const tmpProgress = fs.mkdtempSync(path.join(os.tmpdir(), "studio-redact-progress-"));
  const prevProgressDir = process.env.PROGRESS_DIR;
  process.env.PROGRESS_DIR = tmpProgress;

  try {
    // 4a. Unanswered, malformed-input, and score-only problems return 403 for steps, display, and solution
    for (const part of ["steps", "display", "solution"] as const) {
      const req = new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=${part}`
      );
      const res = await revealGET(req);
      assert.equal(res.status, 403, `Expected 403 for unanswered ${part}`);
    }

    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [{ id: mthDrillSample.problemId, state: invalidInputState }],
    });
    for (const part of ["steps", "display", "solution"] as const) {
      const res = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=${part}`
        )
      );
      assert.equal(res.status, 403, `Expected 403 after invalid input for ${part}`);
    }

    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [{ id: mthDrillSample.problemId, state: scoreOnlyState }],
    });
    for (const part of ["steps", "display", "solution"] as const) {
      const res = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=${part}`
        )
      );
      assert.equal(res.status, 403, `Expected 403 for score-only ${part}`);
    }

    // 4b. Assisted setup reveal persists setupRevealedBeforeAnswer and unlocks display (403 for steps)
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [
        {
          id: mthDrillSample.problemId,
          state: makeState({ setupRevealedBeforeAnswer: true }),
        },
      ],
    });

    const dispRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=display`
      )
    );
    assert.equal(dispRes.status, 200, "display should unlock after setupRevealedBeforeAnswer");
    const dispData = await dispRes.json();
    assert.equal(dispData.part, "display");
    assert.ok(typeof dispData.display === "string" && dispData.display.length > 0);

    const stepsStillLocked = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=steps`
      )
    );
    assert.equal(stepsStillLocked.status, 403, "steps must remain 403 when only setup was revealed");

    // 4c. Checked problem unlocks steps
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [
        {
          id: mthDrillSample.problemId,
          state: checkedState,
        },
      ],
    });
    const stepsRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=steps`
      )
    );
    assert.equal(stepsRes.status, 200, "steps should unlock after a check attempt");
    const stepsData = await stepsRes.json();
    assert.ok(Array.isArray(stepsData.steps) && stepsData.steps.length > 0);

    // 4d. PRG solutionCode stays 403 on revise, unlocks on pass
    writeProgress({
      drillId: prgDrillSample.drillId,
      unitCode: "PRG-TEST",
      problems: [
        {
          id: prgDrillSample.problemId,
          state: prgReviseState,
        },
      ],
    });
    const solReviseRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${prgDrillSample.drillId}&q=${prgDrillSample.problemId}&part=solution`
      )
    );
    assert.equal(solReviseRes.status, 403, "PRG solution must stay 403 when review verdict is revise");

    writeProgress({
      drillId: prgDrillSample.drillId,
      unitCode: "PRG-TEST",
      problems: [
        {
          id: prgDrillSample.problemId,
          state: prgPassState,
        },
      ],
    });
    const solPassRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${prgDrillSample.drillId}&q=${prgDrillSample.problemId}&part=solution`
      )
    );
    assert.equal(solPassRes.status, 200, "PRG solution must unlock when review verdict is pass");
    const solPassData = await solPassRes.json();
    assert.ok(typeof solPassData.solutionCode === "string" && solPassData.solutionCode.length > 0);

    // 4e. /api/check-answer ignores client-spoofed answerSpec (server copy wins)
    const spoofReq = new NextRequest("http://127.0.0.1:3000/api/check-answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        drillId: mthDrillSample.drillId,
        problemId: mthDrillSample.problemId,
        input: "999999991",
        answerSpec: { type: "number", value: "999999991" },
      }),
    });
    const spoofRes = await checkAnswerPOST(spoofReq);
    const spoofBody = await spoofRes.json();
    assert.equal(
      spoofBody.verdict,
      "incorrect",
      "Server answerSpec must win over client-spoofed answerSpec"
    );

    // 4f. /api/reveal respects review cycles (startProblemCycle + reviewMerge)
    const oldCycleState = makeState({
      userInput: "42",
      score: 0.5,
      skipped: true,
      lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
      setupRevealedBeforeAnswer: true,
      solutionRevealedBeforeAnswer: true,
      reviewSetupRevealedAt: "2026-11-18T10:00:00Z",
      reviewStepsRevealedAt: "2026-11-18T10:01:00Z",
      attempts: [
        {
          input: "42",
          ts: "2026-11-18T10:02:00Z",
          verdict: "correct",
          setupRevealed: true,
          solutionRevealed: true,
        },
      ],
    });
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [{ id: mthDrillSample.problemId, state: oldCycleState }],
    });
    const cycleTs = "2026-11-20T09:00:00.000Z";
    startProblemCycle(mthDrillSample.drillId, "MTH-TEST", mthDrillSample.problemId, cycleTs);

    // Immediately after starting a new review cycle, old attempts/lastCheck/flags must NOT unlock /api/reveal
    for (const part of ["steps", "display"] as const) {
      const res = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=${part}`
        )
      );
      assert.equal(
        res.status,
        403,
        `Expected 403 for ${part} in a new review cycle before any current-cycle attempt or reveal`
      );
    }

    // Non-substantive attempt in the new cycle must keep steps and display locked
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      reviewMerge: true,
      problems: [
        {
          id: mthDrillSample.problemId,
          state: makeState({
            cycleStartedAt: cycleTs,
            attempts: [
              { input: "(((", ts: "2026-11-20T09:00:10.000Z", verdict: "parse_error" },
            ],
          }),
        },
      ],
    });
    for (const part of ["steps", "display"] as const) {
      const res = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=${part}`
        )
      );
      assert.equal(res.status, 403, `parse_error in new cycle must keep ${part} locked`);
    }

    // Explicit set-up reveal in the new review cycle unlocks display ONLY (steps stays 403)
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      reviewMerge: true,
      problems: [
        {
          id: mthDrillSample.problemId,
          state: makeState({
            cycleStartedAt: cycleTs,
            setupRevealedBeforeAnswer: true,
          }),
        },
      ],
    });
    const revDispRes = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=display`
      )
    );
    assert.equal(revDispRes.status, 200, "explicit setup reveal in review cycle must unlock display");
    const revStepsStillLocked = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=steps`
      )
    );
    assert.equal(revStepsStillLocked.status, 403, "explicit setup reveal must not unlock steps");

    // Explicit steps reveal in the new review cycle unlocks steps
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      reviewMerge: true,
      problems: [
        {
          id: mthDrillSample.problemId,
          state: makeState({
            cycleStartedAt: cycleTs,
            solutionRevealedBeforeAnswer: true,
          }),
        },
      ],
    });
    const revStepsUnlocked = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=steps`
      )
    );
    assert.equal(revStepsUnlocked.status, 200, "explicit steps reveal in review cycle must unlock steps");

    // 4g. Drill Reset (resetProblemForRetry) locks /api/reveal until answered or explicitly revealed in the new cycle
    // Must be later than every timestamp stamped with the real clock earlier in this test.
    const resetTs = new Date(Date.now() + 60_000).toISOString();
    const resetProb = resetProblemForRetry(
      {
        ...leakingMathProblem,
        id: mthDrillSample.problemId,
        state: oldCycleState,
      },
      resetTs
    );
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [{ id: mthDrillSample.problemId, state: resetProb.state }],
    });
    for (const part of ["steps", "display"] as const) {
      const res = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=${part}`
        )
      );
      assert.equal(res.status, 403, `Reset must re-lock /api/reveal?part=${part} until answered`);
    }

    // Explicit setup reveal after Drill Reset unlocks display (steps stays 403)
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [
        {
          id: mthDrillSample.problemId,
          state: { ...resetProb.state, setupRevealedBeforeAnswer: true },
        },
      ],
    });
    assert.equal(
      (
        await revealGET(
          new NextRequest(
            `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=display`
          )
        )
      ).status,
      200,
      "explicit setup reveal after Reset must unlock display"
    );
    assert.equal(
      (
        await revealGET(
          new NextRequest(
            `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=steps`
          )
        )
      ).status,
      403,
      "explicit setup reveal after Reset must keep steps locked"
    );

    // Substantive attempt in the new cycle after Reset unlocks steps
    writeProgress({
      drillId: mthDrillSample.drillId,
      unitCode: "MTH-TEST",
      problems: [
        {
          id: mthDrillSample.problemId,
          state: {
            ...resetProb.state,
            attempts: [
              ...(resetProb.state.attempts || []),
              { input: "99", ts: new Date(Date.parse(resetTs) + 60_000).toISOString(), verdict: "incorrect" },
            ],
          },
        },
      ],
    });
    assert.equal(
      (
        await revealGET(
          new NextRequest(
            `http://127.0.0.1:3000/api/reveal?drill=${mthDrillSample.drillId}&q=${mthDrillSample.problemId}&part=steps`
          )
        )
      ).status,
      200,
      "substantive attempt in new cycle after Reset must unlock steps"
    );

    // 4h. PRG problem with prior pass review re-locks solution after startProblemCycle until new-cycle pass
    startProblemCycle(
      prgDrillSample.drillId,
      "PRG-TEST",
      prgDrillSample.problemId,
      "2026-11-20T11:00:00.000Z"
    );
    const prgRelocked = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${prgDrillSample.drillId}&q=${prgDrillSample.problemId}&part=solution`
      )
    );
    assert.equal(prgRelocked.status, 403, "old-cycle PRG pass must not unlock solution in new cycle");

    writeProgress({
      drillId: prgDrillSample.drillId,
      unitCode: "PRG-TEST",
      reviewMerge: true,
      problems: [
        {
          id: prgDrillSample.problemId,
          state: makeState({
            cycleStartedAt: "2026-11-20T11:00:00.000Z",
            reviews: [{ ...makeReview("pass"), at: "2026-11-20T11:05:00.000Z", attempt: 2 }],
          }),
        },
      ],
    });
    const prgReunlocked = await revealGET(
      new NextRequest(
        `http://127.0.0.1:3000/api/reveal?drill=${prgDrillSample.drillId}&q=${prgDrillSample.problemId}&part=solution`
      )
    );
    assert.equal(prgReunlocked.status, 200, "new-cycle PRG pass must unlock solution");
  } finally {
    if (prevProgressDir === undefined) {
      delete process.env.PROGRESS_DIR;
    } else {
      process.env.PROGRESS_DIR = prevProgressDir;
    }
    fs.rmSync(tmpProgress, { recursive: true, force: true });
  }
}

runRouteTests().then(() => {
  console.log(
    `redact & unlock tests passed (${drillFiles.length} drills, ${totalProblemsChecked} problems verified)`
  );
});
