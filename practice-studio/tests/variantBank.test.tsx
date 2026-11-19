/**
 * Tests for server-side variant sessions (`/api/variant`, `/api/check-answer` with opaque variantToken,
 * `/api/reveal` with opaque variantToken, `/api/drill` redaction + `hasVariants`, review-schedule isolation,
 * weak-spot trap collection, and assisted-after-example scoring).
 * Run: npx tsx tests/variantBank.test.tsx
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NextRequest } from "next/server";
import { GET as drillGET } from "../src/app/api/drill/route";
import {
  GET as variantGET,
  HEAD as variantHEAD,
  POST as variantPOST,
} from "../src/app/api/variant/route";
import { POST as checkAnswerPOST } from "../src/app/api/check-answer/route";
import { GET as revealGET } from "../src/app/api/reveal/route";
import { readProgress, writeProgress } from "../src/lib/progress";
import { applyCheckResult } from "../src/lib/applyCheckResult";
import { buildScheduleFromProgress } from "../src/lib/reviewItems";
import {
  VariantActionButtons,
  VariantPracticeCard,
  WorkedExampleCard,
  getVariantButtonState,
} from "../src/components/workspace/VariantPracticePanel";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import type { Problem, RedactedVariant, WorkedExampleVariant } from "../src/types/drill";

function makeTempEnv() {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), "learningos-variant-test-"));
  const drillsDir = path.join(base, "drills");
  const variantsDir = path.join(base, "variants");
  const progressDir = path.join(base, "progress");
  fs.mkdirSync(path.join(drillsDir, "MTH-T01-C04"), { recursive: true });
  fs.mkdirSync(variantsDir, { recursive: true });
  fs.mkdirSync(progressDir, { recursive: true });

  const sampleDrill = {
    schemaVersion: "2.0-math",
    drillId: "DRL-MTH-T01-C04-99",
    subject: "MATH",
    unitCode: "MTH-T01-C04",
    unitTitle: "Fractions",
    chapterCode: "MTH-T01-C04",
    topicCode: "MTH-T01",
    problems: [
      {
        id: "Q01",
        level: 1,
        levelLabel: "Level 1 - Foundation",
        category: "Fraction Simplification",
        archetypeKey: "c04-fraction-simplification-gcf",
        templateKey: "c04-fraction-simplification-gcf",
        prompt: "Simplify $\\frac{27}{45}$ to lowest terms.",
        display: "\\frac{27}{45}",
        plainText: "27/45",
        answerSpec: { type: "number", value: "3/5" },
        answerPlain: "3/5",
        answerDisplay: "\\frac{3}{5}",
        commonTrapTag: "c04-partial-common-factor-reduction",
        trapValue: "2/5",
        checkpointHint: "Factor out the greatest common divisor.",
        steps: [
          {
            latex: "\\frac{27}{45} = \\frac{3}{5}",
            explain: "Divide numerator and denominator by their greatest common divisor.",
          },
        ],
      },
      {
        id: "Q02",
        level: 4,
        levelLabel: "Level 4 - Applied",
        category: "Limiting Resource",
        archetypeKey: "c04-no-variants-archetype",
        templateKey: "c04-no-variants-archetype",
        prompt: "Evaluate $2 + 3$.",
        display: "2 + 3",
        plainText: "2 + 3",
        answerSpec: { type: "number", value: "5" },
        answerPlain: "5",
        answerDisplay: "5",
        commonTrapTag: "c04-dummy-trap",
        trapValue: "6",
        checkpointHint: "Add the two numbers.",
        steps: [{ latex: "2 + 3 = 5", explain: "Sum the two integers." }],
      },
    ],
  };

  fs.writeFileSync(
    path.join(drillsDir, "MTH-T01-C04", "DRL-MTH-T01-C04-99.json"),
    JSON.stringify(sampleDrill, null, 2),
    "utf-8"
  );

  const sampleBank = {
    unitCode: "MTH-T01-C04",
    variants: [
      {
        variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
        id: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
        sourceArchetype: "c04-fraction-simplification-gcf",
        archetypeKey: "c04-fraction-simplification-gcf",
        level: 1,
        levelLabel: "Level 1 - Foundation",
        category: "Fraction Simplification",
        prompt: "Reduce $\\frac{88}{165}$ to lowest terms.",
        display: "SECRET_DISPLAY_88_165",
        plainText: "SECRET_PLAINTEXT_88_165",
        givens: { a: 88, b: 165 },
        constants: {},
        answerSpec: { type: "number", value: "8/15", tol: 0, forms: ["reduced_fraction", "exact"] },
        answerPlain: "8/15",
        answerDisplay: "\\frac{8}{15}",
        inputHint: "Enter a reduced fraction",
        commonTrapTag: "c04-partial-common-factor-reduction",
        trapDerivation: "(165 - 88) / 165",
        trapValue: "7/15",
        verify: { source: "88 / 165", trapValue: "7/15" },
        checkpointHint: "Factor out the greatest common divisor.",
        steps: [
          {
            latex: "\\frac{88}{165} = \\frac{8 \\cdot 11}{15 \\cdot 11}",
            explain: "SECRET_STEP_EXPLAIN_ONE",
          },
          {
            latex: "\\frac{8 \\cdot 11}{15 \\cdot 11} = \\frac{8}{15}",
            explain: "SECRET_STEP_EXPLAIN_TWO",
          },
        ],
      },
      {
        variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
        id: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
        sourceArchetype: "c04-fraction-simplification-gcf",
        archetypeKey: "c04-fraction-simplification-gcf",
        level: 1,
        levelLabel: "Level 1 - Foundation",
        category: "Fraction Simplification",
        prompt: "Reduce $\\frac{42}{90}$ to lowest terms.",
        display: "\\frac{42}{90}",
        plainText: "42/90",
        givens: { a: 42, b: 90 },
        constants: {},
        answerSpec: { type: "number", value: "7/15", tol: 0, forms: ["reduced_fraction", "exact"] },
        answerPlain: "7/15",
        answerDisplay: "\\frac{7}{15}",
        inputHint: "Enter a reduced fraction",
        commonTrapTag: "c04-partial-common-factor-reduction",
        trapDerivation: "(90 - 42) / 90",
        trapValue: "8/15",
        verify: { source: "42 / 90", trapValue: "8/15" },
        checkpointHint: "Factor out the greatest common divisor.",
        steps: [
          {
            latex: "\\frac{42}{90} = \\frac{7 \\cdot 6}{15 \\cdot 6}",
            explain: "Factor out the greatest common divisor.",
          },
          {
            latex: "\\frac{7 \\cdot 6}{15 \\cdot 6} = \\frac{7}{15}",
            explain: "Cancel the common factor.",
          },
        ],
      },
      {
        variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-03",
        id: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-03",
        sourceArchetype: "c04-fraction-simplification-gcf",
        archetypeKey: "c04-fraction-simplification-gcf",
        level: 1,
        levelLabel: "Level 1 - Foundation",
        category: "Fraction Simplification",
        prompt: "Reduce $\\frac{36}{60}$ to lowest terms.",
        display: "\\frac{36}{60}",
        plainText: "36/60",
        givens: { a: 36, b: 60 },
        constants: {},
        answerSpec: { type: "number", value: "3/5", tol: 0, forms: ["reduced_fraction", "exact"] },
        answerPlain: "3/5",
        answerDisplay: "\\frac{3}{5}",
        inputHint: "Enter a reduced fraction",
        commonTrapTag: "c04-partial-common-factor-reduction",
        trapDerivation: "(60 - 36) / 60",
        trapValue: "2/5",
        verify: { source: "36 / 60", trapValue: "2/5" },
        checkpointHint: "Factor out the greatest common divisor.",
        steps: [
          {
            latex: "\\frac{36}{60} = \\frac{3 \\cdot 12}{5 \\cdot 12}",
            explain: "Factor out the greatest common divisor.",
          },
          {
            latex: "\\frac{3 \\cdot 12}{5 \\cdot 12} = \\frac{3}{5}",
            explain: "Cancel the common factor.",
          },
        ],
      },
    ],
  };

  fs.writeFileSync(
    path.join(variantsDir, "MTH-T01-C04.json"),
    JSON.stringify(sampleBank, null, 2),
    "utf-8"
  );

  return { base, drillsDir, variantsDir, progressDir };
}

function makeMathProblem(overrides: Partial<Problem> = {}): Problem {
  return {
    id: "Q01",
    templateKey: "c04-fraction-simplification-gcf",
    level: 1,
    levelLabel: "Level 1 - Foundation",
    category: "Fraction Simplification",
    prompt: "Simplify $\\frac{27}{45}$ to lowest terms.",
    hasVariants: true,
    answerSpec: { type: "number" },
    checkpointHint: "Factor out the greatest common divisor.",
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

async function runTests() {
  const { base, drillsDir, variantsDir, progressDir } = makeTempEnv();
  const prevDrills = process.env.DRILLS_DATA_DIR;
  const prevVariants = process.env.VARIANTS_DIR;
  const prevProgress = process.env.PROGRESS_DIR;

  process.env.DRILLS_DATA_DIR = drillsDir;
  process.env.VARIANTS_DIR = variantsDir;
  process.env.PROGRESS_DIR = progressDir;

  try {
    // -----------------------------------------------------------------------
    // 1. /api/drill annotates `hasVariants` per problem & HEAD /api/variant
    // -----------------------------------------------------------------------
    {
      const drillRes = await drillGET(
        new NextRequest("http://127.0.0.1:3000/api/drill?id=DRL-MTH-T01-C04-99")
      );
      assert.equal(drillRes.status, 200);
      const drillData = (await drillRes.json()) as { problems: Problem[] };
      assert.equal(drillData.problems[0].hasVariants, true);
      assert.equal(drillData.problems[1].hasVariants, false);

      const headHit = await variantHEAD(
        new NextRequest("http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01")
      );
      assert.equal(headHit.status, 200);

      const headMiss = await variantHEAD(
        new NextRequest("http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q02")
      );
      assert.equal(headMiss.status, 404);
    }

    // Seed 1 wrong attempt on Q01 (sets Q01 to Level 1, due next day)
    writeProgress({
      drillId: "DRL-MTH-T01-C04-99",
      unitCode: "MTH-T01-C04",
      problems: [
        {
          id: "Q01",
          state: {
            userInput: "2/5",
            score: 0,
            attempts: [{ input: "2/5", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
          },
        },
      ],
    });
    const scheduleBeforeVariants = buildScheduleFromProgress({
      dataDir: drillsDir,
      progressDir,
    });

    // -----------------------------------------------------------------------
    // 2. GET /api/variant?mode=try — opaque token, zero-leak, refuse skip-ahead, mode=active
    // -----------------------------------------------------------------------
    let firstToken = "";
    {
      const res1 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(res1.status, 200);
      const body1 = (await res1.json()) as {
        mode: string;
        token: string;
        index: number;
        total: number;
        remainingCount: number;
        variant: Record<string, unknown>;
      };
      assert.equal(body1.mode, "try");
      assert.equal(body1.token, "v1");
      assert.equal(body1.index, 1);
      assert.equal(body1.total, 3);
      assert.equal(body1.remainingCount, 2);
      firstToken = body1.token;

      // Zero-leak assertions: NO variantId, NO archetype/method name, NO answer/steps/display/trap!
      const rawJson = JSON.stringify(body1);
      assert.equal(body1.variant.variantId, undefined);
      assert.equal(body1.variant.id, "v1");
      assert.equal(body1.variant.answerPlain, undefined);
      assert.equal(body1.variant.answerDisplay, undefined);
      assert.equal(body1.variant.steps, undefined);
      assert.equal(body1.variant.display, undefined);
      assert.equal(body1.variant.plainText, undefined);
      assert.equal(body1.variant.trapValue, undefined);
      assert.equal(body1.variant.trapDerivation, undefined);
      assert.equal(body1.variant.commonTrapTag, undefined);
      assert.equal(body1.variant.verify, undefined);
      assert.equal((body1.variant.answerSpec as Record<string, unknown>).value, undefined);
      assert.ok(!rawJson.includes("VAR-MTH-"), "try payload must never leak bank variantId");
      assert.ok(!rawJson.includes("fraction-simplification-gcf"), "try payload must never leak archetype/method name");
      assert.ok(!rawJson.includes("8/15"), "try payload must never leak answerPlain");
      assert.ok(!rawJson.includes("7/15"), "try payload must never leak trapValue");
      assert.ok(!rawJson.includes("SECRET_DISPLAY_88_165"), "try payload must never leak display");
      assert.ok(!rawJson.includes("SECRET_PLAINTEXT_88_165"), "try payload must never leak plainText");
      assert.ok(!rawJson.includes("SECRET_STEP_EXPLAIN_ONE"), "try payload must never leak steps");

      // Refuses a new try while the active try has no substantive attempt (prevents skipping to easier numbers)
      const skipRes = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(skipRes.status, 409);

      // GET ?mode=active restores active variant without leaking variantId or secrets
      const activeRes = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=active"
        )
      );
      assert.equal(activeRes.status, 200);
      const activeText = await activeRes.text();
      assert.ok(!activeText.includes("VAR-MTH-"));
      assert.ok(!activeText.includes("fraction-simplification-gcf"));
      assert.ok(!activeText.includes("SECRET_DISPLAY_88_165"));
      const activeJson = JSON.parse(activeText) as { active: { token: string; index: number; total: number } };
      assert.equal(activeJson.active.token, "v1");
      assert.equal(activeJson.active.index, 1);
      assert.equal(activeJson.active.total, 3);

      // /api/drill also redacts state.variants[*].variantId and variantsSeen
      const drillAfterRes = await drillGET(
        new NextRequest("http://127.0.0.1:3000/api/drill?id=DRL-MTH-T01-C04-99")
      );
      const drillAfterText = await drillAfterRes.text();
      assert.ok(!drillAfterText.includes("VAR-MTH-"), "/api/drill must never leak bank variantId in state");
      const drillAfterJson = JSON.parse(drillAfterText) as { problems: Problem[] };
      assert.equal(drillAfterJson.problems[0].state.activeVariant, "v1");
      assert.equal(drillAfterJson.problems[0].state.variantsSeen, undefined);
      assert.equal(drillAfterJson.problems[0].state.variants?.v1?.variantId, undefined);
    }

    // -----------------------------------------------------------------------
    // 3. Reveal gates (`display` on request marks assisted; `steps` locked until attempt/give-up)
    // -----------------------------------------------------------------------
    {
      // Steps BEFORE attempting -> 403
      const lockedSteps = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${firstToken}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps`
        )
      );
      assert.equal(lockedSteps.status, 403);

      // Raw variantId rejected -> 400
      const rawIdReveal = await revealGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/reveal?variantId=VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps"
        )
      );
      assert.equal(rawIdReveal.status, 400);

      // Display on request -> 200 and marks setupRevealed on server
      const displayRes = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${firstToken}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=display`
        )
      );
      assert.equal(displayRes.status, 200);
      const displayData = (await displayRes.json()) as { display: string; plainText: string };
      assert.equal(displayData.display, "SECRET_DISPLAY_88_165");
      assert.equal(displayData.plainText, "SECRET_PLAINTEXT_88_165");

      const progAfterDisplay = readProgress("DRL-MTH-T01-C04-99");
      const v1AfterDisplay = (progAfterDisplay?.problems?.Q01 as Problem["state"])?.variants?.v1;
      assert.equal(v1AfterDisplay?.setupRevealed, true);

      // Worked example still 403 with only 1 cluster wrong (Q01 wrong #1, variant not yet attempted)
      const exLocked = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=example"
        )
      );
      assert.equal(exLocked.status, 403);
    }

    // -----------------------------------------------------------------------
    // 4. POST /api/check-answer with opaque variantToken: records kind:"variant", trap,
    //    never changes review schedule, unlocks steps AND unlocks example at 2 cluster wrongs
    // -----------------------------------------------------------------------
    {
      // Wrong trap answer on variant v1 -> cluster wrongs becomes 2 (1 on Q01 + 1 on v1)
      const wrongChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: firstToken,
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "7/15",
            durationMs: 4200,
          }),
        })
      );
      assert.equal(wrongChk.status, 200);
      const wrongData = (await wrongChk.json()) as { verdict: string; trapMatched?: boolean };
      assert.equal(wrongData.verdict, "incorrect");
      assert.equal(wrongData.trapMatched, true);

      // Check progress file: attempt recorded with kind:"variant", matchedTrap, setupRevealed, durationMs
      const progAfterChk = readProgress("DRL-MTH-T01-C04-99");
      const q01State = progAfterChk?.problems?.Q01 as Problem["state"];
      assert.equal(q01State.variants?.v1?.attempts.length, 1);
      assert.equal(q01State.variants?.v1?.attempts[0]?.kind, "variant");
      assert.equal(
        q01State.variants?.v1?.attempts[0]?.matchedTrap,
        "c04-partial-common-factor-reduction"
      );
      assert.equal(q01State.variants?.v1?.attempts[0]?.setupRevealed, true);
      assert.equal(q01State.variants?.v1?.durationMs, 4200);

      // Review schedule is UNTOUCHED by variant attempts (no review_items.json created, backfilled schedule identical)
      assert.equal(fs.existsSync(path.join(progressDir, "review_items.json")), false);
      const scheduleAfterVariant = buildScheduleFromProgress({
        dataDir: drillsDir,
        progressDir,
      });
      assert.deepEqual(scheduleAfterVariant, scheduleBeforeVariants);

      // Reveal steps AFTER substantive attempt -> 200
      const unlockedSteps = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${firstToken}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps`
        )
      );
      assert.equal(unlockedSteps.status, 200);
      const revData = (await unlockedSteps.json()) as {
        steps: Array<{ explain: string }>;
        answerPlain: string;
      };
      assert.equal(revData.answerPlain, "8/15");
      assert.equal(revData.steps.length, 2);

      // Unknown token -> 404
      const missingChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: "v99",
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "1",
          }),
        })
      );
      assert.equal(missingChk.status, 404);
    }

    // -----------------------------------------------------------------------
    // 5. GET /api/variant?mode=example — unlocks at 2 cluster wrongs, marks example seen,
    //    never serves the active try, and never serves the example again as a try
    // -----------------------------------------------------------------------
    {
      const exRes = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=example"
        )
      );
      assert.equal(exRes.status, 200);
      const exText = await exRes.text();
      assert.ok(!exText.includes("VAR-MTH-"), "example payload must not leak bank variantId");
      assert.ok(!exText.includes("fraction-simplification-gcf"), "example payload must not leak archetype");
      const exBody = JSON.parse(exText) as {
        mode: string;
        token: string;
        exampleViewedAt: string;
        remainingCount: number;
        variant: WorkedExampleVariant;
      };
      assert.equal(exBody.mode, "example");
      assert.equal(exBody.token, "v2");
      assert.ok(exBody.exampleViewedAt);
      // Variant 01 was active try, so example picked variant 02 (42/90), leaving only variant 03 (remainingCount = 1)
      assert.equal(exBody.variant.answerPlain, "7/15");
      assert.equal(exBody.remainingCount, 1);
      assert.ok(exBody.variant.steps.length >= 2);

      // Worked example variant is marked seen on disk -> next mode=try MUST skip variant 02 and serve variant 03!
      const try2Res = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(try2Res.status, 200);
      const try2Body = (await try2Res.json()) as {
        token: string;
        index: number;
        remainingCount: number;
        variant: RedactedVariant;
      };
      assert.equal(try2Body.token, "v3");
      assert.equal(try2Body.index, 2);
      assert.equal(try2Body.remainingCount, 0);
      assert.ok(try2Body.variant.prompt.includes("36"), "Worked example variant 02 must never come back as a try");

      // Explicit give-up on v3 unlocks steps via POST /api/variant { action: "reveal-steps" }
      const giveUpRes = await variantPOST(
        new NextRequest("http://127.0.0.1:3000/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            variantToken: "v3",
            action: "reveal-steps",
          }),
        })
      );
      assert.equal(giveUpRes.status, 200);
      const stepsAfterGiveUp = await revealGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/reveal?variantToken=v3&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps"
        )
      );
      assert.equal(stepsAfterGiveUp.status, 200);

      // Attempt v3, then requesting another try hits exhaustion (404, allSeen: true)
      await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: "v3",
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "3/5",
          }),
        })
      );
      const exhaustedRes = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(exhaustedRes.status, 404);
      const exhaustedBody = (await exhaustedRes.json()) as { allSeen?: boolean };
      assert.equal(exhaustedBody.allSeen, true);

      // Answer on the original after seeing the worked example counts as assisted (score = 0.5, exampleViewed: true)
      const qAfterExample = makeMathProblem({
        state: {
          userInput: "",
          score: null,
          divergedStep: null,
          mistakes: [],
          attempts: [],
          exampleViewedAt: exBody.exampleViewedAt,
        },
      });
      const assistedState = applyCheckResult(
        qAfterExample,
        "3/5",
        { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
        []
      );
      assert.equal(assistedState.score, 0.5);
      assert.equal(assistedState.attempts?.[0]?.exampleViewed, true);

      // Archetype with no variants -> 404
      const noVar = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q02&mode=try"
        )
      );
      assert.equal(noVar.status, 404);
    }

    // -----------------------------------------------------------------------
    // 6. UI smoke checks (before Commit 3 replaces VariantPracticePanel)
    // -----------------------------------------------------------------------
    {
      assert.deepEqual(getVariantButtonState({ hasVariants: false, wrongAttempts: 3 }), {
        showTry: false,
        showExample: false,
      });
      assert.deepEqual(getVariantButtonState({ hasVariants: true, wrongAttempts: 1 }), {
        showTry: true,
        showExample: false,
      });
      assert.deepEqual(getVariantButtonState({ hasVariants: true, wrongAttempts: 2 }), {
        showTry: true,
        showExample: true,
      });

      const noop = () => {};
      const btnHtml = renderToStaticMarkup(
        <VariantActionButtons
          hasVariants={true}
          wrongAttempts={2}
          loadingMode={null}
          onTrySimilar={noop}
          onSeeExample={noop}
        />
      );
      assert.ok(btnHtml.includes("Try a similar question"));
      assert.ok(btnHtml.includes("See a worked example"));

      const sampleTry: RedactedVariant = {
        token: "v1",
        id: "v1",
        level: 1,
        prompt: "Reduce $\\frac{88}{165}$ to lowest terms.",
        answerSpec: { type: "number" },
        placeholder: "Enter a reduced fraction",
        checkpointHint: "Factor out the greatest common divisor.",
        hasSetup: true,
      };
      const tryHtml = renderToStaticMarkup(
        <VariantPracticeCard
          drillId="DRL-MTH-T01-C04-99"
          qid="Q01"
          variant={sampleTry}
          remainingCount={1}
          onAnother={noop}
          onClose={noop}
        />
      );
      assert.ok(tryHtml.includes("Similar question"));
      assert.ok(!tryHtml.includes("8/15"));

      const sampleExample: WorkedExampleVariant = {
        token: "v2",
        id: "v2",
        level: 1,
        prompt: "Reduce $\\frac{42}{90}$ to lowest terms.",
        answerDisplay: "\\frac{7}{15}",
        answerPlain: "7/15",
        steps: [
          {
            latex: "\\frac{42}{90} = \\frac{7 \\cdot 6}{15 \\cdot 6}",
            explain: "Factor out the greatest common divisor.",
          },
          {
            latex: "\\frac{7 \\cdot 6}{15 \\cdot 6} = \\frac{7}{15}",
            explain: "Cancel the common factor.",
          },
        ],
      };
      const exHtml = renderToStaticMarkup(
        <WorkedExampleCard example={sampleExample} onClose={noop} />
      );
      assert.ok(exHtml.includes("Worked example — a similar question, not yours"));

      const html0 = renderToStaticMarkup(
        <MathWorkspace
          problem={makeMathProblem()}
          drillId="DRL-MTH-T01-C04-99"
          index={0}
          totalQuestions={2}
          unitCode="MTH-T01-C04"
          drillTitle="Fractions"
          mistakeTags={[]}
          activeStep={null}
          onInputChange={noop}
          onCheckAnswer={noop}
          onToggleStepHighlight={noop}
          onMarkDivergedStep={noop}
          onSetScore={noop}
          onToggleMistakeTag={noop}
          onMistakeNoteChange={noop}
          onResetProblem={noop}
        />
      );
      assert.ok(!html0.includes("Try a similar question"));
    }

    console.log("PASS: variantBank.test.tsx (opaque tokens, zero-leak, server state, review isolation)");
  } finally {
    if (prevDrills === undefined) delete process.env.DRILLS_DATA_DIR;
    else process.env.DRILLS_DATA_DIR = prevDrills;
    if (prevVariants === undefined) delete process.env.VARIANTS_DIR;
    else process.env.VARIANTS_DIR = prevVariants;
    if (prevProgress === undefined) delete process.env.PROGRESS_DIR;
    else process.env.PROGRESS_DIR = prevProgress;
    fs.rmSync(base, { recursive: true, force: true });
  }
}

runTests().catch((err) => {
  console.error(err);
  process.exit(1);
});
