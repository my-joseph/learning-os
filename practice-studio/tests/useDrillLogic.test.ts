import assert from "node:assert/strict";
import {
  computeCheckAnswerTransition,
  computeResetAllTransition,
  computeResetProblemTransition,
  computeSetupRevealTransition,
  computeSkipProblemTransition,
  computeSolutionRevealTransition,
  executeSaveAndReveal,
  mergeRevealedPatchIntoDrill,
  normalizeLoadedDrillDoc,
} from "../src/hooks/useDrill";
import {
  createTelemetryTimerState,
  getAttemptElapsedMs,
  pauseTimer,
  recordHint,
  setActiveProblem,
} from "../src/lib/telemetryTimer";
import type { DrillDocument, Problem } from "../src/types/drill";

function makeProblem(id: string, overrides: Partial<Problem> = {}): Problem {
  return {
    id,
    templateKey: "tpl-linear",
    level: 1,
    levelLabel: "Level 1",
    category: "Algebra",
    prompt: `Solve problem ${id}.`,
    hasSetup: true,
    checkpointHint: "Isolate x.",
    commonTrapTag: "sign-error",
    answerSpec: { type: "number" },
    state: {
      userInput: "",
      score: null,
      divergedStep: null,
      mistakes: [],
      lastCheck: null,
      attempts: [],
    },
    ...overrides,
  };
}

function makeDrillDoc(problems: Problem[] = [makeProblem("Q01"), makeProblem("Q02")]): DrillDocument {
  return {
    schemaVersion: "2.0",
    drillId: "DRL-MTH-T01-C01-01",
    subject: "MATH",
    unitCode: "MTH-T01-C01-U01",
    unitTitle: "Linear Equations",
    chapterCode: "MTH-T01-C01",
    topicCode: "MTH-T01",
    unitNotionUrl: null,
    createdAt: "2026-11-19T00:00:00Z",
    config: { questionCount: problems.length, difficulty: "ALL", difficultyMode: "Mixed" },
    mistakeTags: [
      { id: "sign-error", name: "Sign Error", label: "Sign Error", autoFrom: [] },
    ],
    problems,
    sessionSummary: {
      practiceStatus: "In Progress",
      score: 1,
      maxScore: problems.length,
      accuracyPct: 50,
      mistakeCategories: ["sign-error"],
      divergedStepsSummary: "Q01#1",
      attemptDate: "2026-11-19",
    },
    localFilePath: "drills/data/MTH-T01-C01-U01/DRL-MTH-T01-C01-01.json",
  };
}

async function main() {
  // 1. normalizeLoadedDrillDoc preserves telemetry and defaults missing state fields
  {
    const rawDoc = makeDrillDoc([
      makeProblem("Q01", {
        starterCode: "function solve() {}",
        state: {
          userInput: "42",
          score: 0.5,
          divergedStep: 1,
          mistakes: ["sign-error"],
          hintsRevealed: 2,
          durationMs: 12_500,
          setupRevealedBeforeAnswer: true,
          solutionRevealedBeforeAnswer: true,
          attempts: [{ input: "42", ts: "2026-11-19T00:00:00Z", verdict: "correct" }],
        },
      }),
    ]);
    const normalized = normalizeLoadedDrillDoc(rawDoc);
    const st = normalized.problems[0].state;
    assert.equal(st.userInput, "42");
    assert.equal(st.userCode, "function solve() {}");
    assert.equal(st.score, 0.5);
    assert.equal(st.hintsRevealed, 2);
    assert.equal(st.durationMs, 12_500);
    assert.equal(st.setupRevealedBeforeAnswer, true);
    assert.equal(st.solutionRevealedBeforeAnswer, true);
  }

  // 2. computeCheckAnswerTransition: invalid input does not reveal steps/display or penalize score
  {
    const doc = makeDrillDoc();
    let timer = createTelemetryTimerState("Q01", true, false, 1_000);
    timer = recordHint(timer, "Q01");

    const invalidStep = computeCheckAnswerTransition(
      doc,
      "Q01",
      "(((",
      {
        verdict: "invalid input",
        message: "Traceback (most recent call last): SymPy parse error",
        components: [],
        diagnostics: [],
      },
      timer,
      4_000
    );
    assert.ok(invalidStep);
    assert.deepEqual(
      invalidStep.partsToReveal,
      [],
      "Invalid input must not request any /api/reveal parts"
    );
    assert.equal(invalidStep.updatedDoc.problems[0].state.score, null);
    assert.doesNotMatch(
      invalidStep.result.message,
      /Traceback|SymPy/,
      "Raw SymPy error message must be sanitized"
    );

    // Substantive correct attempt after invalid input still earns 1.0 (or 0.5 if hint was revealed)
    const correctStep = computeCheckAnswerTransition(
      invalidStep.updatedDoc,
      "Q01",
      "5",
      {
        verdict: "correct",
        message: "Correct.",
        components: [],
        diagnostics: [],
      },
      invalidStep.nextTimerState,
      9_000
    );
    assert.ok(correctStep);
    assert.deepEqual(
      correctStep.partsToReveal,
      ["steps", "display"],
      "Substantive check on problem with hasSetup must reveal steps and display"
    );
    assert.equal(
      correctStep.updatedDoc.problems[0].state.durationMs,
      8_000,
      "Duration must accumulate across both intervals (3000ms + 5000ms)"
    );
    assert.equal(
      correctStep.updatedDoc.problems[0].state.hintsRevealed,
      1,
      "Hint revealed during first interval must be preserved"
    );
    assert.equal(
      correctStep.updatedDoc.problems[0].state.score,
      0.5,
      "Hint revealed before correct answer caps score at 0.5"
    );
  }

  // 3. computeSetupRevealTransition & computeSolutionRevealTransition assistance gating
  {
    const doc = makeDrillDoc();

    // Opening set-up before any attempt marks setupRevealedBeforeAnswer = true and fetches display
    const setupBefore = computeSetupRevealTransition(doc, "Q01");
    assert.ok(setupBefore);
    assert.equal(setupBefore.shouldMarkAssisted, true);
    assert.equal(
      setupBefore.updatedDoc.problems[0].state.setupRevealedBeforeAnswer,
      true
    );
    assert.deepEqual(setupBefore.partsToReveal, ["display"]);

    // Opening steps before any correct attempt marks solutionRevealedBeforeAnswer = true and fetches steps
    const solBefore = computeSolutionRevealTransition(doc, "Q01");
    assert.ok(solBefore);
    assert.equal(solBefore.shouldMarkAssisted, true);
    assert.equal(
      solBefore.updatedDoc.problems[0].state.solutionRevealedBeforeAnswer,
      true
    );
    assert.deepEqual(solBefore.partsToReveal, ["steps"]);

    // After a correct attempt, opening set-up or steps does not mark assisted and skips fetch if already populated
    const solvedDoc = makeDrillDoc([
      makeProblem("Q01", {
        display: "2x = 10",
        steps: [{ latex: "x = 5", explain: "Divide by 2." }],
        state: {
          userInput: "5",
          score: 1,
          divergedStep: null,
          mistakes: [],
          attempts: [{ input: "5", ts: "2026-11-19T00:00:00Z", verdict: "correct" }],
        },
      }),
    ]);
    const setupAfter = computeSetupRevealTransition(solvedDoc, "Q01");
    assert.ok(setupAfter);
    assert.equal(setupAfter.shouldMarkAssisted, false);
    assert.deepEqual(setupAfter.partsToReveal, []);

    const solAfter = computeSolutionRevealTransition(solvedDoc, "Q01");
    assert.ok(solAfter);
    assert.equal(solAfter.shouldMarkAssisted, false);
    assert.deepEqual(solAfter.partsToReveal, []);
  }

  // 4. computeSkipProblemTransition consumes timer, marks skipped, and reveals steps + display
  {
    const doc = makeDrillDoc();
    const timer = createTelemetryTimerState("Q01", true, false, 10_000);
    const skipped = computeSkipProblemTransition(doc, "Q01", timer, 16_000);
    assert.ok(skipped);
    const q1State = skipped.updatedDoc.problems[0].state;
    assert.equal(q1State.skipped, true);
    assert.equal(q1State.score, 0);
    assert.equal(q1State.durationMs, 6_000);
    assert.deepEqual(skipped.partsToReveal, ["steps", "display"]);
  }

  // 5. executeSaveAndReveal & mergeRevealedPatchIntoDrill orchestration
  {
    const doc = makeDrillDoc();
    const calls: Array<{ url: string; method: string }> = [];
    const mockFetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method || "GET";
      calls.push({ url, method });
      if (url === "/api/save-state") {
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      }
      if (url.includes("part=steps")) {
        return new Response(
          JSON.stringify({
            steps: [{ latex: "x = 5", explain: "Divide by 2." }],
            answerDisplay: "5",
            answerPlain: "5",
          }),
          { status: 200 }
        );
      }
      if (url.includes("part=display")) {
        return new Response(
          JSON.stringify({
            display: "2x = 10",
            plainText: "2*x = 10",
          }),
          { status: 200 }
        );
      }
      return new Response("{}", { status: 403 });
    }) as typeof fetch;

    const patch = await executeSaveAndReveal(doc, "Q01", ["steps", "display"], mockFetch);
    assert.equal(calls.length, 3);
    assert.equal(calls[0].url, "/api/save-state", "save-state must be called before reveal");
    assert.equal(calls[0].method, "POST");
    assert.equal(patch.answerPlain, "5");
    assert.equal(patch.display, "2x = 10");
    assert.equal(patch.steps?.length, 1);

    const merged = mergeRevealedPatchIntoDrill(doc, doc.drillId, "Q01", patch);
    assert.ok(merged);
    assert.equal(merged.problems[0].answerPlain, "5");
    assert.equal(merged.problems[0].display, "2x = 10");
    assert.equal(merged.problems[1].answerPlain, undefined);

    // Stale drillId is ignored
    const staleMerged = mergeRevealedPatchIntoDrill(doc, "DRL-OTHER-01", "Q01", patch);
    assert.equal(staleMerged, doc);
  }

  // 6. computeResetProblemTransition & computeResetAllTransition
  {
    const doc = makeDrillDoc([
      makeProblem("Q01", {
        display: "2x = 10",
        plainText: "2*x = 10",
        answerPlain: "5",
        answerDisplay: "5",
        steps: [{ latex: "x = 5", explain: "Divide by 2." }],
        state: {
          userInput: "5",
          score: 1,
          divergedStep: 0,
          mistakes: ["sign-error"],
          durationMs: 4_000,
          attempts: [{ input: "5", ts: "2026-11-19T00:00:00Z", verdict: "correct" }],
        },
      }),
      makeProblem("Q02", {
        answerPlain: "10",
        state: {
          userInput: "10",
          score: 1,
          divergedStep: null,
          mistakes: [],
          durationMs: 7_000,
          attempts: [{ input: "10", ts: "2026-11-19T00:01:00Z", verdict: "correct" }],
        },
      }),
    ]);

    let timer = createTelemetryTimerState("Q01", true, false, 1_000);
    timer = setActiveProblem(timer, "Q02", 5_000); // Q01 accrued 4000ms in timer
    timer = setActiveProblem(timer, "Q01", 8_000); // Q02 accrued 3000ms in timer

    const singleReset = computeResetProblemTransition(
      doc,
      "Q01",
      timer,
      { Q01: 0, Q02: 1 },
      10_000
    );
    assert.equal(singleReset.nextActiveSteps.Q01, null);
    assert.equal(singleReset.nextActiveSteps.Q02, 1);
    assert.equal(singleReset.updatedDoc.problems[0].state.userInput, "");
    assert.equal(singleReset.updatedDoc.problems[0].state.score, null);
    assert.equal("steps" in singleReset.updatedDoc.problems[0], false);
    assert.equal("display" in singleReset.updatedDoc.problems[0], false);
    assert.equal("answerPlain" in singleReset.updatedDoc.problems[0], false);
    // Q02 remains intact
    assert.equal(singleReset.updatedDoc.problems[1].state.score, 1);
    assert.equal(
      getAttemptElapsedMs(singleReset.nextTimerState, "Q01", 10_000),
      0,
      "Q01 timer must reset to 0"
    );
    assert.equal(
      getAttemptElapsedMs(singleReset.nextTimerState, "Q02", 10_000),
      3_000,
      "Q02 timer must remain untouched"
    );

    // Reset all while paused preserves paused state and resets all problems + sessionSummary
    const pausedTimer = pauseTimer(timer, 12_000);
    const allReset = computeResetAllTransition(doc, pausedTimer, true, 15_000);
    assert.deepEqual(allReset.nextActiveSteps, {});
    assert.equal(allReset.firstProblemId, "Q01");
    assert.equal(allReset.nextTimerState.paused, true, "Global pause state must be preserved across Reset all");
    assert.equal(allReset.updatedDoc.sessionSummary.practiceStatus, "Ready");
    assert.equal(allReset.updatedDoc.problems[0].state.score, null);
    assert.equal(allReset.updatedDoc.problems[1].state.score, null);
    assert.equal("answerPlain" in allReset.updatedDoc.problems[1], false);
    assert.match(allReset.statusMessage.text, /Reset Linear Equations to initial state\./);
  }

  console.log("useDrill reveal, timer, and reset logic tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
