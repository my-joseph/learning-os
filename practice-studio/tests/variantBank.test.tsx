/**
 * Tests for Phase 2a variant bank APIs (`/api/variant`, `/api/check-answer` with variantId,
 * `/api/reveal` with variantId, `/api/drill` `hasVariants`) and MathWorkspace UI states.
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
import { GET as variantGET, HEAD as variantHEAD } from "../src/app/api/variant/route";
import { POST as checkAnswerPOST } from "../src/app/api/check-answer/route";
import { GET as revealGET } from "../src/app/api/reveal/route";
import { readProgress, writeProgress } from "../src/lib/progress";
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

    // -----------------------------------------------------------------------
    // 2. GET /api/variant?mode=try — zero-leak + unseen tracking + exhaustion
    // -----------------------------------------------------------------------
    let firstVariantId = "";
    {
      const res1 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(res1.status, 200);
      const body1 = (await res1.json()) as {
        mode: string;
        remainingCount: number;
        variant: Record<string, unknown>;
      };
      assert.equal(body1.mode, "try");
      assert.equal(body1.remainingCount, 1);
      firstVariantId = String(body1.variant.variantId);
      assert.equal(firstVariantId, "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01");

      // Zero-leak assertions: NO answer, steps, display, plainText, trap, or secret strings!
      const rawJson = JSON.stringify(body1);
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
      assert.ok(!rawJson.includes("8/15"), "try payload must never leak answerPlain");
      assert.ok(!rawJson.includes("7/15"), "try payload must never leak trapValue");
      assert.ok(!rawJson.includes("SECRET_DISPLAY_88_165"), "try payload must never leak display");
      assert.ok(!rawJson.includes("SECRET_PLAINTEXT_88_165"), "try payload must never leak plainText");
      assert.ok(!rawJson.includes("SECRET_STEP_EXPLAIN_ONE"), "try payload must never leak steps");

      // Progress file tracks variantsSeen
      const progAfter1 = readProgress("DRL-MTH-T01-C04-99");
      const q01State1 = progAfter1?.problems?.Q01 as { variantsSeen?: string[] };
      assert.deepEqual(q01State1?.variantsSeen, [firstVariantId]);

      // Second call serves the second unseen variant
      const res2 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(res2.status, 200);
      const body2 = (await res2.json()) as { remainingCount: number; variant: { variantId: string } };
      assert.equal(body2.variant.variantId, "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02");
      assert.equal(body2.remainingCount, 0);

      // Third call: all variants seen -> 404 with clear message
      const res3 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=try"
        )
      );
      assert.equal(res3.status, 404);
      const body3 = (await res3.json()) as { error: string; allSeen?: boolean };
      assert.equal(body3.allSeen, true);
      assert.ok(body3.error.length > 0);
    }

    // -----------------------------------------------------------------------
    // 3. GET /api/variant?mode=example — 403 (<2 wrong), 200 (>=2 wrong), 404 (no variants)
    // -----------------------------------------------------------------------
    {
      // 0 wrong attempts -> 403
      const ex0 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=example"
        )
      );
      assert.equal(ex0.status, 403);

      // 1 wrong attempt -> still 403
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
      // Also confirm writeProgress preserved variantsSeen!
      const progPreserved = readProgress("DRL-MTH-T01-C04-99");
      const q01Preserved = progPreserved?.problems?.Q01 as { variantsSeen?: string[] };
      assert.equal(q01Preserved.variantsSeen?.length, 2);

      const ex1 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=example"
        )
      );
      assert.equal(ex1.status, 403);

      // 2 wrong attempts -> 200 with fully solved variant (prompt, answer, steps with explain)
      writeProgress({
        drillId: "DRL-MTH-T01-C04-99",
        unitCode: "MTH-T01-C04",
        problems: [
          {
            id: "Q01",
            state: {
              userInput: "1/5",
              score: 0,
              attempts: [
                { input: "2/5", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
                { input: "1/5", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
              ],
            },
          },
        ],
      });

      const ex2 = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=example"
        )
      );
      assert.equal(ex2.status, 200);
      const exBody = (await ex2.json()) as {
        mode: string;
        variant: WorkedExampleVariant;
      };
      assert.equal(exBody.mode, "example");
      assert.notEqual(exBody.variant.prompt, "Simplify $\\frac{27}{45}$ to lowest terms.");
      assert.ok(exBody.variant.answerPlain.length > 0);
      assert.ok(exBody.variant.answerDisplay.length > 0);
      assert.ok(exBody.variant.steps.length >= 2);
      assert.ok(exBody.variant.steps.every((s) => s.explain.length > 0));

      // Archetype with no variants -> 404 with clear message
      const noVar = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q02&mode=try"
        )
      );
      assert.equal(noVar.status, 404);
      const noVarBody = (await noVar.json()) as { error: string };
      assert.match(noVarBody.error, /no variants/i);
    }

    // -----------------------------------------------------------------------
    // 4. /api/check-answer with variantId + /api/reveal unlock after attempt
    // -----------------------------------------------------------------------
    {
      // Reveal BEFORE attempting the variant -> 403
      const lockedReveal = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantId=${firstVariantId}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps`
        )
      );
      assert.equal(lockedReveal.status, 403);

      // Check wrong trap answer against bank
      const wrongChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantId: firstVariantId,
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "7/15",
          }),
        })
      );
      assert.equal(wrongChk.status, 200);
      const wrongData = (await wrongChk.json()) as { verdict: string; trapMatched?: boolean };
      assert.equal(wrongData.verdict, "incorrect");
      assert.equal(wrongData.trapMatched, true);

      // Reveal AFTER substantive attempt -> 200 with steps & answer
      const unlockedReveal = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantId=${firstVariantId}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps`
        )
      );
      assert.equal(unlockedReveal.status, 200);
      const revData = (await unlockedReveal.json()) as {
        steps: Array<{ explain: string }>;
        answerPlain: string;
      };
      assert.equal(revData.answerPlain, "8/15");
      assert.equal(revData.steps.length, 2);

      // Check correct answer against bank (without drillId/qid also works)
      const okChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ variantId: firstVariantId, input: "8/15" }),
        })
      );
      assert.equal(okChk.status, 200);
      const okData = (await okChk.json()) as { verdict: string };
      assert.equal(okData.verdict, "correct");

      // Missing variantId -> 404
      const missingChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ variantId: "VAR-DOES-NOT-EXIST-01", input: "1" }),
        })
      );
      assert.equal(missingChk.status, 404);
    }

    // -----------------------------------------------------------------------
    // 5. UI states: visibility rules, MathWorkspace buttons, Try card, WorkedExampleCard
    // -----------------------------------------------------------------------
    {
      // Pure visibility helper
      assert.deepEqual(getVariantButtonState({ hasVariants: false, wrongAttempts: 3 }), {
        showTry: false,
        showExample: false,
      });
      assert.deepEqual(getVariantButtonState({ hasVariants: true, wrongAttempts: 0 }), {
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
      const renderWorkspace = (prob: Problem) =>
        renderToStaticMarkup(
          <MathWorkspace
            problem={prob}
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

      // 0 wrong attempts -> no variant buttons
      const html0 = renderWorkspace(makeMathProblem());
      assert.ok(!html0.includes("Try a similar question"));
      assert.ok(!html0.includes("See a worked example"));

      // 1 wrong attempt + hasVariants -> only "Try a similar question"
      const html1 = renderWorkspace(
        makeMathProblem({
          hasVariants: true,
          state: {
            userInput: "2/5",
            score: 0,
            divergedStep: null,
            mistakes: [],
            lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
            attempts: [{ input: "2/5", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
          },
        })
      );
      assert.ok(html1.includes("Try a similar question"));
      assert.ok(!html1.includes("See a worked example"));

      // 2 wrong attempts + hasVariants -> both buttons
      const html2 = renderWorkspace(
        makeMathProblem({
          hasVariants: true,
          state: {
            userInput: "1/5",
            score: 0,
            divergedStep: null,
            mistakes: [],
            lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
            attempts: [
              { input: "2/5", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
              { input: "1/5", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
            ],
          },
        })
      );
      assert.ok(html2.includes("Try a similar question"));
      assert.ok(html2.includes("See a worked example"));

      // 2 wrong attempts + hasVariants: false -> buttons hidden
      const htmlHidden = renderWorkspace(
        makeMathProblem({
          hasVariants: false,
          state: {
            userInput: "1/5",
            score: 0,
            divergedStep: null,
            mistakes: [],
            lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
            attempts: [
              { input: "2/5", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
              { input: "1/5", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
            ],
          },
        })
      );
      assert.ok(!htmlHidden.includes("Try a similar question"));
      assert.ok(!htmlHidden.includes("See a worked example"));

      // VariantActionButtons standalone
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

      // VariantPracticeCard renders prompt + input + check button, zero leaked answers
      const sampleTry: RedactedVariant = {
        variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
        id: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
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
      assert.ok(tryHtml.includes("Another one"));
      assert.ok(tryHtml.includes("Check answer"));
      assert.ok(!tryHtml.includes("Show steps"), "Show steps hidden until substantive attempt");
      assert.ok(!tryHtml.includes("8/15"));

      // WorkedExampleCard renders label, prompt, final answer, and StepRow steps with explain
      const sampleExample: WorkedExampleVariant = {
        variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
        id: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-02",
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
      assert.ok(exHtml.includes("Answer:"));
      assert.ok(exHtml.includes("Step 1:"));
      assert.ok(exHtml.includes("Factor out the greatest common divisor."));
      assert.ok(exHtml.includes("Step 2:"));
      assert.ok(exHtml.includes("Cancel the common factor."));
      assert.ok(!exHtml.includes("Diverged here"));
    }

    console.log("PASS: variantBank.test.tsx (API zero-leak, 403/404, check-answer/reveal, UI states)");
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
