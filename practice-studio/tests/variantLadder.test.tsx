/**
 * Tests for the swap-in-place similar question & progressive worked example help ladder:
 * - Every state of the ladder ([A] wrong #1, [B] similar open, [C] similar correct,
 *   [D] similar wrong / cluster >= 2, [E] progressive worked example, [F] back on Q2
 *   with collapsed disclosure & own steps after subsequent wrong)
 * - Full control parity on MathItemView (Math input / Plain text toggle, palette, `=`,
 *   Hint, Show equation set-up, Show steps, Reset, Timer)
 * - Zero-leak invariants (no answer, steps, bank variantId, or method/archetype names)
 * - Deletion of VariantPracticePanel.tsx
 * Run: npx tsx tests/variantLadder.test.tsx
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { AnswerResultCard } from "../src/components/AnswerResultCard";
import { MathItemView } from "../src/components/math/MathItemView";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import {
  WorkedExampleDisclosure,
  WorkedExampleView,
} from "../src/components/math/WorkedExampleView";
import { QuestionTimer } from "../src/components/QuestionTimer";
import {
  getOriginalLadderActions,
  getSimilarLadderActions,
} from "../src/lib/variantLadder";
import type { Problem, WorkedExampleVariant } from "../src/types/drill";

const noop = () => {};

function makeProblem(overrides: Partial<Problem> = {}): Problem {
  return {
    id: "Q02",
    templateKey: "c04-fraction-multiplication-product",
    level: 1,
    levelLabel: "Level 1 - Foundation",
    category: "Fraction Multiplication",
    prompt: "Multiply $\\frac{7}{8} \\times \\frac{4}{15}$ and write the answer as a reduced fraction.",
    hasVariants: true,
    hasSetup: true,
    answerSpec: { type: "number" },
    checkpointHint: "Multiply numerators together and denominators together, then simplify.",
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

const sampleExample: WorkedExampleVariant = {
  token: "v2",
  id: "v2",
  level: 1,
  prompt: "Multiply $\\frac{3}{4} \\times \\frac{8}{9}$ and write the answer as a reduced fraction.",
  answerDisplay: "\\frac{2}{3}",
  answerPlain: "2/3",
  steps: [
    {
      latex: "\\frac{3}{4} \\times \\frac{8}{9} = \\frac{3 \\cdot 8}{4 \\cdot 9}",
      explain: "Multiply numerators together and denominators together.",
    },
    {
      latex: "\\frac{24}{36} = \\frac{2}{3}",
      explain: "Divide numerator and denominator by 12 to reduce.",
    },
  ],
};

// ---------------------------------------------------------------------------
// 1. Pure ladder state machine tests ([A] through [F])
// ---------------------------------------------------------------------------
{
  // Unattempted or no variants -> nothing shown
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 0,
      clusterWrongAttempts: 0,
      hasActiveSimilar: false,
      remainingCount: null,
      exampleViewed: false,
      wrongAfterExample: false,
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: false,
      showSeeExample: false,
      showOwnSteps: false,
    }
  );
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: false,
      originalWrongAttempts: 3,
      clusterWrongAttempts: 3,
      hasActiveSimilar: false,
      remainingCount: 3,
      exampleViewed: false,
      wrongAfterExample: false,
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: false,
      showSeeExample: false,
      showOwnSteps: false,
    }
  );

  // [A] Wrong #1 on Q2 -> ONLY "Try a similar question" (no example, no own steps)
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 1,
      clusterWrongAttempts: 1,
      hasActiveSimilar: false,
      remainingCount: null,
      exampleViewed: false,
      wrongAfterExample: false,
      lastVerdict: "incorrect",
    }),
    {
      showTrySimilar: true,
      showResumeSimilar: false,
      showSeeExample: false,
      showOwnSteps: false,
    }
  );

  // [A] Wrong #1 + learner left an unfinished similar question -> "Resume similar question"
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 1,
      clusterWrongAttempts: 1,
      hasActiveSimilar: true,
      remainingCount: 2,
      exampleViewed: false,
      wrongAfterExample: false,
      lastVerdict: "incorrect",
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: true,
      showSeeExample: false,
      showOwnSteps: false,
    }
  );

  // [A] Wrong #2 on Q2 (or 1 on Q2 + 1 on similar -> cluster wrongs == 2) -> adds "See a worked example"
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 1,
      clusterWrongAttempts: 2,
      hasActiveSimilar: true,
      remainingCount: 2,
      exampleViewed: false,
      wrongAfterExample: false,
      lastVerdict: "incorrect",
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: true,
      showSeeExample: true,
      showOwnSteps: false,
    }
  );

  // Bank exhausted (remainingCount == 0), example not viewed -> ONLY "See a worked example" (no Try link, no error)
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 2,
      clusterWrongAttempts: 2,
      hasActiveSimilar: false,
      remainingCount: 0,
      exampleViewed: false,
      wrongAfterExample: false,
      lastVerdict: "incorrect",
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: false,
      showSeeExample: true,
      showOwnSteps: false,
    }
  );

  // [F] Back on Q2 right after viewing worked example (no new wrong yet) -> no duplicate example link, no own steps yet
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 2,
      clusterWrongAttempts: 2,
      hasActiveSimilar: false,
      remainingCount: 0,
      exampleViewed: true,
      wrongAfterExample: false,
      lastVerdict: "incorrect",
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: false,
      showSeeExample: false,
      showOwnSteps: false,
    }
  );

  // [F] The assist row remains the single entry point for the learner's own steps.
  assert.deepEqual(
    getOriginalLadderActions({
      hasVariants: true,
      originalWrongAttempts: 3,
      clusterWrongAttempts: 3,
      hasActiveSimilar: false,
      remainingCount: 0,
      exampleViewed: true,
      wrongAfterExample: true,
      lastVerdict: "incorrect",
    }),
    {
      showTrySimilar: false,
      showResumeSimilar: false,
      showSeeExample: false,
      showOwnSteps: true,
    }
  );

  // Similar question states:
  // [B] Unattempted similar -> no "Another similar question" (cannot skip ahead to easier numbers)
  assert.deepEqual(
    getSimilarLadderActions({
      hasAttemptOnCurrent: false,
      isCurrentCorrect: false,
      clusterWrongAttempts: 1,
      remainingCount: 2,
      stepsOpen: false,
    }),
    {
      showBackToOriginal: false,
      showStepsLink: false,
      showSeeExample: false,
      showAnotherSimilar: false,
    }
  );

  // [C] Similar correct -> Back to Question N + optional "Another one", with no duplicate Show steps.
  assert.deepEqual(
    getSimilarLadderActions({
      hasAttemptOnCurrent: true,
      isCurrentCorrect: true,
      clusterWrongAttempts: 1,
      remainingCount: 2,
      stepsOpen: false,
    }),
    {
      showBackToOriginal: true,
      showStepsLink: false,
      showSeeExample: false,
      showAnotherSimilar: true,
    }
  );

  // [D] Similar wrong (cluster wrongs >= 2, remaining > 0) -> See a worked example + Another similar question
  assert.deepEqual(
    getSimilarLadderActions({
      hasAttemptOnCurrent: true,
      isCurrentCorrect: false,
      clusterWrongAttempts: 2,
      remainingCount: 2,
      stepsOpen: false,
    }),
    {
      showBackToOriginal: false,
      showStepsLink: false,
      showSeeExample: true,
      showAnotherSimilar: true,
    }
  );
}

// ---------------------------------------------------------------------------
// 2. Render tests: MathWorkspace ladder states on original Q2
// ---------------------------------------------------------------------------
{
  const renderQ2 = (prob: Problem) =>
    renderToStaticMarkup(
      <MathWorkspace
        problem={prob}
        drillId="DRL-MTH-T01-C04-01"
        index={1}
        totalQuestions={6}
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
        onPrevQuestion={noop}
        onNextQuestion={noop}
      />
    );

  // [A] Wrong #1: result card contains Try again + Try a similar question (no See a worked example, no extra answer field)
  const htmlWrong1 = renderQ2(
    makeProblem({
      state: {
        userInput: "12",
        score: 0,
        divergedStep: null,
        mistakes: [],
        lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
        attempts: [{ input: "12", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
      },
    })
  );
  assert.ok(htmlWrong1.includes("Try again"));
  assert.ok(htmlWrong1.includes("Try a similar question"));
  assert.ok(!htmlWrong1.includes("See a worked example"));
  assert.ok(htmlWrong1.includes('aria-live="polite"'));
  assert.ok(!htmlWrong1.includes("VAR-MTH-"));
  assert.ok(!htmlWrong1.includes("fraction-multiplication-product"));

  // [A] Wrong #2: adds "See a worked example" inside the result card
  const htmlWrong2 = renderQ2(
    makeProblem({
      state: {
        userInput: "1/3",
        score: 0,
        divergedStep: null,
        mistakes: [],
        lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
        attempts: [
          { input: "12", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
          { input: "1/3", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
        ],
      },
    })
  );
  assert.ok(htmlWrong2.includes("Try a similar question"));
  assert.ok(htmlWrong2.includes("See a worked example"));

  // [A] Unfinished activeVariant -> shows "Resume similar question"
  const htmlResume = renderQ2(
    makeProblem({
      state: {
        userInput: "12",
        score: 0,
        divergedStep: null,
        mistakes: [],
        activeVariant: "v1",
        lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
        attempts: [{ input: "12", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" }],
      },
    })
  );
  assert.ok(htmlResume.includes("Resume similar question"));
  assert.ok(!htmlResume.includes("Try a similar question"));

  // [F] Wrong again AFTER viewing worked example -> the assist row is the only "Show steps" entry.
  const htmlAfterExWrong = renderQ2(
    makeProblem({
      state: {
        userInput: "1/4",
        score: 0,
        divergedStep: null,
        mistakes: [],
        exampleViewedAt: "2026-11-19T10:02:00Z",
        lastCheck: { verdict: "incorrect", message: "Not quite.", components: [], diagnostics: [] },
        attempts: [
          { input: "12", ts: "2026-11-19T10:00:00Z", verdict: "incorrect" },
          { input: "1/3", ts: "2026-11-19T10:01:00Z", verdict: "incorrect" },
          { input: "1/4", ts: "2026-11-19T10:03:00Z", verdict: "incorrect", exampleViewed: true },
        ],
      },
    })
  );
  // Count occurrences of "Show steps": one in the assist row.
  const showStepsMatches = htmlAfterExWrong.match(/Show steps/g) || [];
  assert.equal(showStepsMatches.length, 1);
}

// ---------------------------------------------------------------------------
// 3. Render tests: Similar question via shared MathItemView (full control parity!)
//    and AnswerResultCard [C] ("Correct · now try Question 2" + "Back to Question 2")
// ---------------------------------------------------------------------------
{
  const similarProb = makeProblem({
    id: "v1",
    prompt: "Multiply $\\frac{5}{6} \\times \\frac{9}{10}$ and write the answer as a reduced fraction.",
    hasSetup: true,
    state: {
      userInput: "",
      score: null,
      divergedStep: null,
      mistakes: [],
      lastCheck: null,
      attempts: [],
    },
  });

  const similarHtml = renderToStaticMarkup(
    <MathItemView
      problem={similarProb}
      header={
        <div>
          <span>Question 2</span>
          <span>Similar question 1 of 3</span>
          <QuestionTimer questionMs={5000} totalMs={5000} />
        </div>
      }
      unitCode="MTH-T01-C04"
      drillTitle="Fractions"
      mistakeTags={[]}
      activeStep={null}
      autoRevealOnCorrect={false}
      ariaLabel="Answer for similar question 1 of 3"
      onInputChange={noop}
      onCheckAnswer={noop}
      onToggleStepHighlight={noop}
      onReset={noop}
      onHintRevealed={noop}
      onSetupRevealed={noop}
      onSolutionRevealed={noop}
    />
  );

  // Full parity with original question:
  assert.ok(similarHtml.includes("Similar question 1 of 3"));
  assert.ok(similarHtml.includes("Math input"), "Similar question must offer Math input mode");
  assert.ok(similarHtml.includes("Plain text"), "Similar question must offer Plain text toggle");
  assert.ok(similarHtml.includes('aria-label="Check answer"'), "Similar question must offer embedded = check button");
  assert.ok(similarHtml.includes("Show equation set-up"), "Similar question must offer equation set-up");
  assert.ok(similarHtml.includes("Hint"), "Similar question must offer Hint");
  assert.equal((similarHtml.match(/Show steps/g) || []).length, 1, "Similar question has one Show steps action");
  assert.ok(similarHtml.includes("00:05"), "Similar question must offer its own timer");
  assert.ok(!similarHtml.includes("Self-score"), "Similar question must NOT render Self-score");
  assert.ok(!similarHtml.includes("Diverged here"), "Similar question must NOT render Diverged here");

  // [C] Correct similar answer offers Back and Another one without a duplicate Show steps action.
  const similarCorrectCard = renderToStaticMarkup(
    <AnswerResultCard
      lastCheck={{ verdict: "correct", message: "Correct.", components: [], diagnostics: [] }}
      state={{
        userInput: "3/4",
        score: 1,
        divergedStep: null,
        mistakes: [],
        attempts: [{ input: "3/4", ts: "2026-11-19T10:05:00Z", verdict: "correct", kind: "variant" }],
      }}
      titleOverride="Correct · now try Question 2"
      backLabel="Back to Question 2"
      onBack={noop}
      secondaryActions={[{ label: "Another one", onClick: noop }]}
    />
  );
  assert.ok(similarCorrectCard.includes("Correct · now try Question 2"));
  assert.ok(similarCorrectCard.includes("Back to Question 2"));
  assert.ok(similarCorrectCard.includes("Another one"));
  assert.ok(!similarCorrectCard.includes("Another similar question"));
  assert.ok(similarCorrectCard.includes("min-h-[44px]"), "Mobile tap targets must be >= 44px");
}

// ---------------------------------------------------------------------------
// 4. Render tests: WorkedExampleView progressive stepping [E] & collapsed disclosure [F]
// ---------------------------------------------------------------------------
{
  // Step 0: prompt first, Show next step + Show all steps, final Answer not shown yet
  const ex0Html = renderToStaticMarkup(
    <WorkedExampleView
      questionNumber={2}
      example={sampleExample}
      onBackToQuestion={noop}
      initialRevealedCount={0}
    />
  );
  assert.ok(ex0Html.includes(`Step 1 of ${sampleExample.steps.length}`));
  assert.ok(ex0Html.includes("Question 2"));
  assert.ok(ex0Html.includes("Worked example"));
  assert.ok(ex0Html.includes("A similar question, not yours"));
  assert.ok(ex0Html.includes("Show next step"));
  assert.ok(ex0Html.includes("Show all steps"));
  assert.ok(!ex0Html.includes("Step 1:"), "Steps start hidden until Show next step");
  assert.ok(!ex0Html.includes("Try Question 2 again"), "Final CTA waits until all steps are revealed");
  assert.ok(!ex0Html.includes("VAR-MTH-"));

  // Step 1: Step 1 shown, Step 2 still hidden, Show next step still present
  const ex1Html = renderToStaticMarkup(
    <WorkedExampleView
      questionNumber={2}
      example={sampleExample}
      onBackToQuestion={noop}
      initialRevealedCount={1}
    />
  );
  assert.ok(ex1Html.includes("Step 1:"));
  assert.ok(ex1Html.includes("Multiply numerators together"));
  assert.ok(!ex1Html.includes("Step 2:"));
  assert.ok(ex1Html.includes("Show next step"));

  // Step 2 (all revealed): all steps + Answer + "Try Question 2 again"
  const exAllHtml = renderToStaticMarkup(
    <WorkedExampleView
      questionNumber={2}
      example={sampleExample}
      onBackToQuestion={noop}
      initialRevealedCount={2}
    />
  );
  assert.ok(exAllHtml.includes("Step 1:"));
  assert.ok(exAllHtml.includes("Step 2:"));
  assert.ok(exAllHtml.includes("Answer"));
  assert.ok(exAllHtml.includes("Try Question 2 again"));
  assert.ok(!exAllHtml.includes("Show next step"));
  assert.ok(!exAllHtml.includes("Diverged here"));

  // Collapsed disclosure on Q2 [F]
  const collapsedHtml = renderToStaticMarkup(
    <WorkedExampleDisclosure example={sampleExample} defaultOpen={false} />
  );
  assert.ok(collapsedHtml.includes("Worked example"));
  assert.ok(collapsedHtml.includes('aria-expanded="false"'));
  assert.ok(!collapsedHtml.includes("Step 1:"));

  const expandedHtml = renderToStaticMarkup(
    <WorkedExampleDisclosure example={sampleExample} defaultOpen={true} />
  );
  assert.ok(expandedHtml.includes('aria-expanded="true"'));
  assert.ok(expandedHtml.includes("A similar question, not yours"));
  assert.ok(expandedHtml.includes("Step 1:"));
  assert.ok(expandedHtml.includes("Step 2:"));
}

// ---------------------------------------------------------------------------
// 5. Legacy VariantPracticePanel.tsx is deleted
// ---------------------------------------------------------------------------
{
  const legacyPath = path.resolve(
    process.cwd(),
    "src/components/workspace/VariantPracticePanel.tsx"
  );
  assert.equal(
    fs.existsSync(legacyPath),
    false,
    "Legacy VariantPracticePanel.tsx must be deleted"
  );
}

console.log("PASS: variantLadder.test.tsx (all ladder states, MathItemView parity, progressive example, zero-leak)");
