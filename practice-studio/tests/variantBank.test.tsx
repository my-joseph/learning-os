/**
 * Tests for Similar Questions v2 server-side sessions (`/api/variant` modes `list`/`open`/`example`,
 * `/api/check-answer` with opaque slot token, `/api/reveal` with opaque slot token, `/api/drill`
 * redaction + `hasVariants`, `action: "open-next"` and `action: "duration"`,
 * zero-leak invariants, and review-schedule isolation at level >= 2).
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
  POST as variantPOST,
} from "../src/app/api/variant/route";
import { POST as checkAnswerPOST } from "../src/app/api/check-answer/route";
import { GET as revealGET } from "../src/app/api/reveal/route";
import { readProgress, writeProgress } from "../src/lib/progress";
import { applyCheckResult } from "../src/lib/applyCheckResult";
import { buildScheduleFromProgress } from "../src/lib/reviewItems";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import type { Problem, ProblemState, WorkedExampleVariant } from "../src/types/drill";

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
      {
        id: "Q03",
        level: 1,
        levelLabel: "Level 1 - Foundation",
        category: "Fraction Simplification",
        archetypeKey: "c04-fraction-simplification-gcf",
        templateKey: "c04-fraction-simplification-gcf",
        prompt: "Simplify $\\frac{18}{24}$ to lowest terms.",
        display: "\\frac{18}{24}",
        plainText: "18/24",
        answerSpec: { type: "number", value: "3/4" },
        answerPlain: "3/4",
        answerDisplay: "\\frac{3}{4}",
        commonTrapTag: "c04-partial-common-factor-reduction",
        trapValue: "6/8",
        checkpointHint: "Divide numerator and denominator by 6.",
        steps: [{ latex: "\\frac{18}{24} = \\frac{3}{4}", explain: "Divide by 6." }],
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

  for (const [slot, numerator, denominator, answer] of [
    [4, 30, 42, "5/7"],
    [5, 42, 54, "7/9"],
  ] as const) {
    const variantId = `VAR-MTH-T01-C04-c04-fraction-simplification-gcf-0${slot}`;
    sampleBank.variants.push({
      ...sampleBank.variants[0],
      id: variantId,
      variantId,
      prompt: `Reduce ${numerator}/${denominator}.`,
      answerSpec: { ...sampleBank.variants[0].answerSpec, value: answer },
      answerPlain: answer,
      answerDisplay: answer,
    });
  }

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

function openNext(qid: string) {
  return variantPOST(new NextRequest("http://127.0.0.1:3000/api/variant", {
    method: "POST",
    body: JSON.stringify({ drillId: "DRL-MTH-T01-C04-99", qid, action: "open-next" }),
  }));
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
    // 1. /api/drill annotates `hasVariants`, and v1 modes are removed
    // -----------------------------------------------------------------------
    {
      const drillRes = await drillGET(
        new NextRequest("http://127.0.0.1:3000/api/drill?id=DRL-MTH-T01-C04-99")
      );
      assert.equal(drillRes.status, 200);
      const drillData = (await drillRes.json()) as { problems: Problem[] };
      assert.equal(drillData.problems[0].hasVariants, true);
      assert.equal(drillData.problems[1].hasVariants, false);

      // Legacy v1 modes `try` and `active` and `deactivate` action are removed (400).
      for (const legacyMode of ["try", "active"]) {
        const res = await variantGET(
          new NextRequest(
            `http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=${legacyMode}`
          )
        );
        assert.equal(res.status, 400, `legacy mode=${legacyMode} must be rejected`);
      }
      const deactRes = await variantPOST(
        new NextRequest("http://127.0.0.1:3000/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            variantToken: "v1",
            action: "deactivate",
          }),
        })
      );
      assert.equal(deactRes.status, 400, "legacy action=deactivate must be rejected");
    }

    // -----------------------------------------------------------------------
    // 2. Locked before any substantive attempt: mode=list -> unlocked:false (no tokens), mode=open -> 403
    // -----------------------------------------------------------------------
    {
      const lockedList = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=list"
        )
      );
      assert.equal(lockedList.status, 200);
      const lockedJson = (await lockedList.json()) as {
        unlocked: boolean;
        tabs: unknown[];
      };
      assert.equal(lockedJson.unlocked, false);
      assert.deepEqual(lockedJson.tabs, []);
      assert.equal(readProgress("DRL-MTH-T01-C04-99"), null, "locked list must not persist progress");

      const lockedOpen = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=open&token=vabc123"
        )
      );
      assert.equal(lockedOpen.status, 403);
      assert.equal((await openNext("Q01")).status, 403);
      assert.equal(readProgress("DRL-MTH-T01-C04-99"), null);
    }

    // -----------------------------------------------------------------------
    // 3. Seed Q01 with multi-day correct history (Level 3, due +7d) + Q03 with 1 wrong attempt
    // -----------------------------------------------------------------------
    writeProgress({
      drillId: "DRL-MTH-T01-C04-99",
      unitCode: "MTH-T01-C04",
      problems: [
        {
          id: "Q01",
          state: {
            userInput: "3/5",
            score: 1,
            lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
            similarSlots: ["vreserv"],
            variants: {
              vreserv: {
                variantId: "VAR-MTH-T01-C04-c04-fraction-simplification-gcf-01",
                role: "try",
                servedAt: "",
                attempts: [],
              },
            },
            attempts: [
              { input: "3/5", ts: "2026-11-10T10:00:00Z", verdict: "correct" },
              { input: "3/5", ts: "2026-11-14T10:00:00Z", verdict: "correct" },
            ],
          },
        },
        {
          id: "Q03",
          state: {
            userInput: "6/8",
            score: 0,
            lastCheck: { verdict: "incorrect", message: "Not reduced.", components: [], diagnostics: [] },
            attempts: [{ input: "6/8", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
          },
        },
      ],
    });
    const scheduleBeforeVariants = buildScheduleFromProgress({
      dataDir: drillsDir,
      progressDir,
    });
    const q01Before = scheduleBeforeVariants["DRL-MTH-T01-C04-99/Q01"];
    assert.ok(q01Before && q01Before.level >= 2, "Q01 must start at level >= 2 for isolation check");

    // -----------------------------------------------------------------------
    // 4. The list makes no reservations. Each open-next appends one opaque session in bank order.
    // -----------------------------------------------------------------------
    let q01Tokens: string[] = [];
    let q03Tokens: string[] = [];
    {
      const beforeList = readProgress("DRL-MTH-T01-C04-99");
      const listRes = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=list"
        )
      );
      assert.equal(listRes.status, 200);
      assert.deepEqual(await listRes.json(), {
        unlocked: true, tabs: [], exhausted: false, exampleViewedAt: null,
      });
      assert.deepEqual(readProgress("DRL-MTH-T01-C04-99"), beforeList);
      assert.equal((await variantGET(new NextRequest(
        "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=open&token=vreserv"
      ))).status, 403);
      assert.equal((await revealGET(new NextRequest(
        "http://127.0.0.1:3000/api/reveal?drillId=DRL-MTH-T01-C04-99&qid=Q01&part=hint&variantToken=vreserv"
      ))).status, 403);

      let firstOpen: unknown;
      for (const slot of [1, 2, 3]) {
        const response = await openNext("Q01");
        assert.equal(response.status, 200);
        const opened = await response.json();
        assert.equal(opened.slot, slot);
        assert.equal(opened.exhausted, false);
        assert.match(opened.token, /^v[a-z0-9]{6}$/);
        assert.ok(opened.session.servedAt);
        assert.deepEqual(opened.tabs.map((t: { token: string }) => t.token), [...q01Tokens, opened.token]);
        q01Tokens.push(opened.token);
        if (slot === 1) firstOpen = opened;
        const saved = readProgress("DRL-MTH-T01-C04-99")?.problems?.Q01 as ProblemState | undefined;
        assert.match(saved?.variants?.[opened.token]?.variantId ?? "", new RegExp(`-0${slot}$`));
      }
      assert.equal(new Set(q01Tokens).size, 3);
      assert.ok(!q01Tokens.includes("vreserv"));
      const q03Open = await openNext("Q03");
      assert.equal(q03Open.status, 200);
      q03Tokens = [(await q03Open.json()).token];

      // A previously opened tab can be resumed without consuming the next variant.
      const openS2 = await variantGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=open&token=${q01Tokens[1]}`
        )
      );
      assert.equal(openS2.status, 200);
      const openS2Body = (await openS2.json()) as {
        slot: number;
        total: number;
        variant: Record<string, unknown>;
        session: { servedAt: string; attempts: unknown[] };
      };
      assert.equal(openS2Body.slot, 2);
      assert.equal(openS2Body.total, 3);
      assert.ok(openS2Body.session.servedAt);
      const openS1Body = firstOpen as { variant: Record<string, unknown> };
      const rawJson = JSON.stringify(openS1Body);
      assert.equal(openS1Body.variant.variantId, undefined);
      assert.equal(openS1Body.variant.checkpointHint, undefined);
      assert.equal(openS1Body.variant.hasHint, true);
      assert.equal(openS1Body.variant.answerPlain, undefined);
      assert.equal(openS1Body.variant.answerDisplay, undefined);
      assert.equal(openS1Body.variant.steps, undefined);
      assert.equal(openS1Body.variant.display, undefined);
      assert.equal(openS1Body.variant.plainText, undefined);
      assert.equal(openS1Body.variant.trapValue, undefined);
      assert.equal((openS1Body.variant.answerSpec as Record<string, unknown>).value, undefined);
      assert.ok(!rawJson.includes("VAR-MTH-"));
      assert.ok(!rawJson.includes("fraction-simplification-gcf"));
      assert.ok(!rawJson.includes("8/15"));
      assert.ok(!rawJson.includes("7/15"));
      assert.ok(!rawJson.includes("SECRET_DISPLAY_88_165"));
      assert.ok(!rawJson.includes("SECRET_PLAINTEXT_88_165"));
      assert.ok(!rawJson.includes("SECRET_STEP_EXPLAIN_ONE"));
      assert.ok(!rawJson.includes("greatest common divisor"), "checkpointHint must not ship in mode=open");

      // Token bound to question: using Q03's token on Q01 -> 403
      const crossOpen = await variantGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=open&token=${q03Tokens[0]}`
        )
      );
      assert.equal(crossOpen.status, 403);

      // /api/drill redacts state.variants[*].variantId, variantsSeen, and never exposes activeVariant
      const drillAfterRes = await drillGET(
        new NextRequest("http://127.0.0.1:3000/api/drill?id=DRL-MTH-T01-C04-99")
      );
      const drillAfterText = await drillAfterRes.text();
      assert.ok(!drillAfterText.includes("VAR-MTH-"));
      const drillAfterJson = JSON.parse(drillAfterText) as { problems: Problem[] };
      assert.deepEqual(drillAfterJson.problems[0].state.similarSlots, q01Tokens);
      assert.equal(drillAfterJson.problems[0].state.variantsSeen, undefined);
      assert.equal(
        (drillAfterJson.problems[0].state as unknown as Record<string, unknown>).activeVariant,
        undefined
      );
    }

    // -----------------------------------------------------------------------
    // 5. Reveal gates + duration action + check-answer slot verification + review_items isolation
    // -----------------------------------------------------------------------
    {
      const tok1 = q01Tokens[0];
      const tok2 = q01Tokens[1];

      // Steps BEFORE attempting -> 403
      const lockedSteps = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${tok1}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps`
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

      // Display + Hint via /api/reveal -> 200
      const displayRes = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${tok1}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=display`
        )
      );
      assert.equal(displayRes.status, 200);
      const displayData = (await displayRes.json()) as { display: string; plainText: string };
      assert.equal(displayData.display, "SECRET_DISPLAY_88_165");
      assert.equal(displayData.plainText, "SECRET_PLAINTEXT_88_165");

      const hintRes = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${tok1}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=hint`
        )
      );
      assert.equal(hintRes.status, 200);
      assert.equal(
        (await hintRes.json()).checkpointHint,
        "Factor out the greatest common divisor."
      );

      // POST /api/variant { action: "duration" } persists per-tab elapsed time
      const durRes = await variantPOST(
        new NextRequest("http://127.0.0.1:3000/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            variantToken: tok1,
            action: "duration",
            durationMs: 3100,
          }),
        })
      );
      assert.equal(durRes.status, 200);

      // Check-answer with wrong answer on Similar 2 and correct on Similar 1
      const wrongChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: tok2,
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "8/15",
            durationMs: 2500,
          }),
        })
      );
      assert.equal(wrongChk.status, 200);
      assert.equal((await wrongChk.json()).verdict, "incorrect");

      const rightChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: tok1,
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "8/15",
            durationMs: 4200,
          }),
        })
      );
      assert.equal(rightChk.status, 200);
      assert.equal((await rightChk.json()).verdict, "correct");

      // Check progress file: duration accumulated, kind:"variant", original score still 1.0
      const progAfterChk = readProgress("DRL-MTH-T01-C04-99");
      const q01State = progAfterChk?.problems?.Q01 as Problem["state"];
      assert.equal(q01State.score, 1, "similar answers must never change R's score");
      assert.equal(q01State.variants?.[tok1]?.durationMs, 7300);
      assert.equal(q01State.variants?.[tok1]?.attempts[0]?.kind, "variant");

      // mode=list now reflects [assisted, wrong, untried] because tok1 revealed display & hint before answering
      const listAfter = (await (
        await variantGET(
          new NextRequest(
            "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=list"
          )
        )
      ).json()) as { tabs: Array<{ status: string }> };
      assert.deepEqual(
        listAfter.tabs.map((t) => t.status),
        ["assisted", "wrong", "untried"]
      );

      // Answering tok3 correctly WITHOUT prior help gives status "correct"; revealing steps/display/hint AFTERWARDS keeps it "correct"
      const tok3 = q01Tokens[2];
      const openS3 = await variantGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=open&token=${tok3}`
        )
      );
      assert.equal(openS3.status, 200);
      const rightS3 = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: tok3,
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "3/5",
          }),
        })
      );
      assert.equal(rightS3.status, 200);
      assert.equal((await rightS3.json()).verdict, "correct");
      // Post-correct reveals must not downgrade "correct" to "assisted"
      for (const part of ["steps", "display", "hint"]) {
        const postRev = await revealGET(
          new NextRequest(
            `http://127.0.0.1:3000/api/reveal?variantToken=${tok3}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=${part}`
          )
        );
        assert.equal(postRev.status, 200);
      }
      const listAfterS3 = (await (
        await variantGET(
          new NextRequest(
            "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=list"
          )
        )
      ).json()) as { tabs: Array<{ status: string }> };
      assert.deepEqual(
        listAfterS3.tabs.map((t) => t.status),
        ["assisted", "wrong", "correct"]
      );

      const responses = await Promise.all([openNext("Q01"), openNext("Q01")]);
      const remaining = await Promise.all(responses.map(async (response) => {
        assert.equal(response.status, 200);
        return response.json();
      }));
      remaining.sort((a, b) => a.slot - b.slot);
      assert.deepEqual(remaining.map((tab) => tab.slot), [4, 5]);
      assert.deepEqual(remaining.map((tab) => tab.exhausted), [false, true]);
      const allTokens = [...q01Tokens, ...remaining.map((tab) => tab.token)];
      const saved = readProgress("DRL-MTH-T01-C04-99")?.problems?.Q01 as ProblemState | undefined;
      assert.deepEqual(saved?.similarSlots, allTokens);
      assert.deepEqual(allTokens.map((token) => saved?.variants?.[token]?.variantId?.slice(-2)), [
        "01", "02", "03", "04", "05",
      ]);
      const listed = await (await variantGET(new NextRequest(
        "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q01&mode=list"
      ))).json();
      assert.deepEqual(listed.tabs.map((tab: { token: string }) => tab.token), allTokens);
      assert.deepEqual(listed.tabs.map((tab: { status: string }) => tab.status), [
        "assisted", "wrong", "correct", "untried", "untried",
      ]);
      assert.deepEqual(Object.keys(listed.tabs[4]).sort(), ["slot", "status", "token"]);
      assert.equal(listed.exhausted, true);
      assert.deepEqual(await (await openNext("Q01")).json(), { exhausted: true, tabs: listed.tabs });

      // Review schedule at level >= 2 is UNTOUCHED by similar attempts!
      assert.equal(fs.existsSync(path.join(progressDir, "review_items.json")), false);
      const scheduleAfterVariant = buildScheduleFromProgress({
        dataDir: drillsDir,
        progressDir,
      });
      const q01After = scheduleAfterVariant["DRL-MTH-T01-C04-99/Q01"];
      assert.deepEqual(q01After, q01Before, "review_items level and dueDate at level >= 2 must be untouched");
      assert.deepEqual(scheduleAfterVariant, scheduleBeforeVariants);

      // Cross-question token in check-answer -> 404 (not in Q01's variants) or 403
      const crossChk = await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: q03Tokens[0],
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q01",
            input: "8/15",
          }),
        })
      );
      assert.ok(crossChk.status === 403 || crossChk.status === 404);

      // Reveal steps AFTER substantive attempt -> 200
      const unlockedSteps = await revealGET(
        new NextRequest(
          `http://127.0.0.1:3000/api/reveal?variantToken=${tok1}&drillId=DRL-MTH-T01-C04-99&qid=Q01&part=steps`
        )
      );
      assert.equal(unlockedSteps.status, 200);
      assert.equal((await unlockedSteps.json()).answerPlain, "8/15");
    }

    // -----------------------------------------------------------------------
    // 6. Existing worked-example path (SCOPE CHANGE: 2-wrong gate on R only; similar wrongs do NOT count)
    // -----------------------------------------------------------------------
    {
      // Q03 has 1 wrong on R. Answer a similar question on Q03 wrong — example must STAY 403!
      await checkAnswerPOST(
        new NextRequest("http://127.0.0.1:3000/api/check-answer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            variantToken: q03Tokens[0],
            drillId: "DRL-MTH-T01-C04-99",
            qid: "Q03",
            input: "7/15",
          }),
        })
      );
      const exStillLocked = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q03&mode=example"
        )
      );
      assert.equal(
        exStillLocked.status,
        403,
        "similar wrongs must NOT unlock mode=example; 2 wrongs on R required"
      );

      // Add 2nd wrong on Q03 itself -> mode=example unlocks (200) and is idempotent!
      writeProgress({
        drillId: "DRL-MTH-T01-C04-99",
        unitCode: "MTH-T01-C04",
        problems: [
          {
            id: "Q03",
            state: {
              userInput: "1/2",
              score: 0,
              lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
              attempts: [
                { input: "6/8", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
                { input: "1/2", ts: "2026-11-19T10:05:00Z", verdict: "incorrect" },
              ],
            },
          },
        ],
      });
      const exRes = await variantGET(
        new NextRequest(
          "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q03&mode=example"
        )
      );
      assert.equal(exRes.status, 200);
      const exText = await exRes.text();
      assert.ok(!exText.includes("VAR-MTH-"));
      assert.ok(!exText.includes("fraction-simplification-gcf"));
      const exBody = JSON.parse(exText) as {
        token: string;
        exampleViewedAt: string;
        variant: WorkedExampleVariant;
      };
      assert.ok(exBody.exampleViewedAt);
      assert.ok(exBody.variant.steps.length >= 2);

      // Idempotent second call returns same token
      const exRes2 = (await (
        await variantGET(
          new NextRequest(
            "http://127.0.0.1:3000/api/variant?drillId=DRL-MTH-T01-C04-99&qid=Q03&mode=example"
          )
        )
      ).json()) as { token: string };
      assert.equal(exRes2.token, exBody.token);

      // Answering R correctly after viewing worked example scores 0.5
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
    }

    // -----------------------------------------------------------------------
    // 7. UI smoke check: untouched MathWorkspace shows the locked add button (zero-leak) & hides result links
    // -----------------------------------------------------------------------
    {
      const noop = () => {};
      const html0 = renderToStaticMarkup(
        <MathWorkspace
          problem={makeMathProblem()}
          drillId="DRL-MTH-T01-C04-99"
          index={0}
          totalQuestions={2}
          unitCode="MTH-T01-C04"
          drillTitle="Fractions"
          mistakeTags={[]}
          onInputChange={noop}
          onCheckAnswer={noop}
          onMarkDivergedStep={noop}
          onSetScore={noop}
          onToggleMistakeTag={noop}
          onMistakeNoteChange={noop}
          onResetProblem={noop}
        />
      );
      assert.ok(html0.includes('role="tablist"'), "tab strip must be visible before first attempt");
      assert.ok(html0.includes('aria-disabled="true"'), "the add button must be disabled before attempt");
      assert.ok(html0.includes("Answer the question first"), "the add button explains how to unlock");
      assert.ok(!html0.includes("VAR-MTH-"), "zero-leak: no bank variant IDs before unlock");
      assert.ok(!html0.includes("Practise a similar question"));
      assert.ok(!html0.includes("See a worked example"));
    }

    // -----------------------------------------------------------------------
    // 8. Quarantined variants (item-level and bank-level) are never served
    // -----------------------------------------------------------------------
    {
      const qUnit = "MTH-T99-C02-U05";
      const qDrillId = "DRL-MTH-T99-C02-U05-01";
      fs.mkdirSync(path.join(drillsDir, qUnit), { recursive: true });
      fs.writeFileSync(
        path.join(drillsDir, qUnit, `${qDrillId}.json`),
        JSON.stringify(
          {
            schemaVersion: "2.0-math",
            drillId: qDrillId,
            subject: "MATH",
            unitCode: qUnit,
            unitTitle: "Quarantine Test",
            chapterCode: "MTH-T99-C02",
            topicCode: "MTH-T99",
            problems: [
              {
                id: "Q01",
                level: 2,
                archetypeKey: "q-arch",
                prompt: "Evaluate $2 + 2$.",
                display: "2 + 2",
                plainText: "2 + 2",
                answerSpec: { type: "number", value: "4" },
                answerPlain: "4",
                answerDisplay: "4",
                commonTrapTag: "q-trap",
                trapValue: "5",
                checkpointHint: "Add both terms.",
                steps: [{ latex: "2 + 2 = 4", explain: "Add." }],
              },
            ],
          },
          null,
          2
        ),
        "utf-8"
      );
      fs.writeFileSync(
        path.join(variantsDir, `${qUnit}.json`),
        JSON.stringify(
          {
            unitCode: qUnit,
            variants: [
              {
                variantId: `VAR-${qUnit}-q-arch-01`,
                id: `VAR-${qUnit}-q-arch-01`,
                archetypeKey: "q-arch",
                sourceArchetype: "q-arch",
                level: 2,
                status: "quarantined",
                quarantineReason: "pre-distractor-provenance gate; parent drill retired in #338",
                since: "2026-11-27",
                prompt: "Evaluate $3 + 3$.",
                display: "3 + 3",
                plainText: "3 + 3",
                answerSpec: { type: "number", value: "6" },
                answerPlain: "6",
                answerDisplay: "6",
                commonTrapTag: "q-trap",
                trapValue: "7",
                checkpointHint: "Add both terms.",
                steps: [{ latex: "3 + 3 = 6", explain: "Add." }],
              },
            ],
          },
          null,
          2
        ),
        "utf-8"
      );

      // /api/drill must report hasVariants = false when only quarantined variants exist
      const qDrillRes = await drillGET(new NextRequest(`http://127.0.0.1:3000/api/drill?id=${qDrillId}`));
      assert.equal(qDrillRes.status, 200);
      const qDrillJson = (await qDrillRes.json()) as {
        problems: Array<{ id: string; hasVariants?: boolean }>;
      };
      assert.equal(qDrillJson.problems[0].hasVariants, false, "quarantined variant must not enable Similar");

      // Seed two wrong attempts so both Similar "+" and worked example unlock, then verify neither serves quarantined variants
      writeProgress({
        drillId: qDrillId,
        problems: [
          {
            id: "Q01",
            state: {
              userInput: "5",
              score: 0,
              divergedStep: null,
              mistakes: [],
              lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
              attempts: [
                { input: "5", ts: "2026-11-27T10:00:00Z", verdict: "incorrect" },
                { input: "6", ts: "2026-11-27T10:05:00Z", verdict: "incorrect" },
              ],
            },
          },
        ],
      });
      const qExRes = await variantGET(
        new NextRequest(`http://127.0.0.1:3000/api/variant?drillId=${qDrillId}&qid=Q01&mode=example`)
      );
      assert.equal(qExRes.status, 404, "mode=example must not serve quarantined variant");

      const qNextRes = await variantPOST(
        new NextRequest("http://127.0.0.1:3000/api/variant", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ drillId: qDrillId, qid: "Q01", action: "open-next" }),
        })
      );
      assert.equal(qNextRes.status, 200);
      const qNextBody = (await qNextRes.json()) as { exhausted?: boolean; token?: string };
      assert.equal(qNextBody.exhausted, true, "open-next must skip quarantined variants");
      assert.equal(qNextBody.token, undefined, "no variant token should be minted for quarantined variants");
    }

    console.log("PASS: variantBank.test.tsx (v2 list/open/example, opaque tokens, zero-leak, review isolation, quarantine)");
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
