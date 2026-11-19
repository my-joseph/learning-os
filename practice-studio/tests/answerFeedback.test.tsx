import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { AnswerResultCard } from "../src/components/AnswerResultCard";
import { ChoiceOptionGroup } from "../src/components/ChoiceOptionGroup";
import { LineChoicePrompt, parseLineChoicePrompt } from "../src/components/LineChoicePrompt";
import { CodeDashboard } from "../src/components/code/CodeDashboard";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import {
  buildResultCardModel,
  formatDiagnosticBody,
  getChoiceResultStatus,
  getResultCardTitle,
  getResultCardTone,
  getSubstantiveAttemptCount,
  isChoiceInteractionLocked,
  isEditableEventTarget,
  resolveChoiceKeyOption,
  submitChoiceSelection,
} from "../src/lib/answerFeedback";
import { CALM_PARSE_ERROR_MESSAGE } from "../src/lib/reviewGuard";
import type { MistakeTag, Problem, ProblemState } from "../src/types/drill";

const noop = () => {};

function baseState(overrides: Partial<ProblemState> = {}): ProblemState {
  return {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    lastCheck: null,
    attempts: [],
    ...overrides,
  };
}

function baseMathProblem(overrides: Partial<Problem> = {}): Problem {
  return {
    id: "Q01",
    templateKey: "tpl",
    level: 1,
    levelLabel: "Level 1",
    category: "Algebra",
    prompt: "Solve $2x = 10$.",
    answerSpec: { type: "number" },
    checkpointHint: "",
    state: baseState(),
    ...overrides,
  };
}

const sampleTags: MistakeTag[] = [
  {
    id: "sign-trap",
    name: "Sign Trap",
    label: "Check the sign of $i^2 = -1$.",
    autoFrom: [],
  },
];

// ---------------------------------------------------------------------------
// 1. Pure Result Card logic tests
// ---------------------------------------------------------------------------
assert.equal(getResultCardTone({ verdict: "correct", message: "Correct.", components: [], diagnostics: [] }), "correct");
assert.equal(getResultCardTone({ verdict: "equivalent_not_in_form", message: "Not factored", components: [], diagnostics: [] }), "almost");
assert.equal(getResultCardTone({ verdict: "partial", message: "Some match", components: [], diagnostics: [] }), "almost");
assert.equal(getResultCardTone({ verdict: "invalid input", message: "Bad", components: [], diagnostics: [] }), "almost");
assert.equal(getResultCardTone({ verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] }), "wrong");
assert.equal(getResultCardTone({ verdict: "skipped", message: "Skipped", components: [], diagnostics: [] }), "skipped");
assert.equal(
  getResultCardTone({ verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] }, baseState({ skipped: true })),
  "skipped"
);

assert.equal(getResultCardTitle({ verdict: "correct", message: "", components: [], diagnostics: [] }, "correct"), "Correct");
assert.equal(
  getResultCardTitle({ verdict: "equivalent_not_in_form", message: "", components: [], diagnostics: [] }, "almost"),
  "Almost — check the form"
);
assert.equal(getResultCardTitle({ verdict: "partial", message: "", components: [], diagnostics: [] }, "almost"), "Almost");
assert.equal(getResultCardTitle({ verdict: "invalid input", message: "", components: [], diagnostics: [] }, "almost"), "Check your input");
assert.equal(getResultCardTitle({ verdict: "incorrect", message: "", components: [], diagnostics: [] }, "wrong"), "Not quite");
assert.equal(getResultCardTitle({ verdict: "skipped", message: "", components: [], diagnostics: [] }, "skipped"), "Skipped");

// Skipped results keep the next action visible without implying that hidden steps are open.
assert.equal(
  formatDiagnosticBody(
    {
      verdict: "skipped",
      message: "Skipped (Concept Gap / Unsure) — Review step-by-step solution below to solidify mental model.",
      components: [],
      diagnostics: [],
    },
    undefined,
    baseState({ skipped: true })
  ),
  null
);
assert.equal(
  formatDiagnosticBody({
    verdict: "incorrect",
    message: "Incorrect option selected.",
    components: [],
    diagnostics: [{ code: "wrong_choice", message: "Selected option is not the intended resolution." }],
  }),
  "That option isn't the right one."
);
assert.equal(
  formatDiagnosticBody({
    verdict: "invalid input",
    message: "Invalid input: Could not tokenize expression",
    components: [],
    diagnostics: [{ code: "err", message: "Traceback (most recent call last):" }],
  }),
  CALM_PARSE_ERROR_MESSAGE
);
assert.equal(
  formatDiagnosticBody(
    {
      verdict: "incorrect",
      message: "Not equal to the verified answer.",
      components: [],
      diagnostics: [],
      trapMatched: true,
    },
    { commonTrapTag: "sign-trap", answerSpec: { type: "number" } },
    baseState({ userInput: "-5" }),
    sampleTags
  ),
  "Check the sign of $i^2 = -1$."
);

// Attempt counter counts substantive attempts only
assert.equal(
  getSubstantiveAttemptCount(
    baseState({
      attempts: [
        { input: "((", ts: "2026-11-18T00:00:00Z", verdict: "invalid input" },
        { input: "4", ts: "2026-11-18T00:00:01Z", verdict: "incorrect" },
      ],
    })
  ),
  1
);
const secondAttemptModel = buildResultCardModel({
  lastCheck: { verdict: "incorrect", message: "Check the sign.", components: [], diagnostics: [] },
  state: baseState({
    attempts: [
      { input: "4", ts: "2026-11-18T00:00:00Z", verdict: "incorrect" },
      { input: "3", ts: "2026-11-18T00:00:05Z", verdict: "incorrect" },
    ],
  }),
});
assert.equal(secondAttemptModel.attemptNumber, 2);
assert.equal(secondAttemptModel.actionKind, "retry");

const lastCorrectModel = buildResultCardModel({
  lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
  state: baseState({ attempts: [{ input: "5", ts: "2026-11-18T00:00:00Z", verdict: "correct" }] }),
  isLastQuestion: true,
});
assert.equal(lastCorrectModel.actionKind, "review");
assert.equal(lastCorrectModel.attemptNumber, 1);

const lockedSkippedModel = buildResultCardModel({
  lastCheck: { verdict: "skipped", message: "Skipped", components: [], diagnostics: [] },
  state: baseState({ skipped: false, attempts: [] }),
});
assert.equal(lockedSkippedModel.actionKind, null, "Show steps must remain gated by reveal rules");

// ---------------------------------------------------------------------------
// 2. Render tests for all 4 AnswerResultCard states
// ---------------------------------------------------------------------------
const correctCardHtml = renderToStaticMarkup(
  <AnswerResultCard
    lastCheck={{ verdict: "correct", message: "Correct.", components: [], diagnostics: [] }}
    state={baseState({ attempts: [{ input: "5", ts: "2026-11-18T00:00:00Z", verdict: "correct" }] })}
    isLastQuestion={false}
    onNextQuestion={noop}
  />
);
assert.match(correctCardHtml, /rounded-xl/);
assert.match(correctCardHtml, /bg-emerald-50/);
assert.doesNotMatch(correctCardHtml, /border-l-/);
assert.match(correctCardHtml, /lucide-check/);
assert.match(correctCardHtml, />Correct</);
assert.match(correctCardHtml, />Next question</);
assert.match(correctCardHtml, /Attempt 1/);

const lastCorrectCardHtml = renderToStaticMarkup(
  <AnswerResultCard
    lastCheck={{ verdict: "correct", message: "Correct.", components: [], diagnostics: [] }}
    state={baseState({
      attempts: [
        { input: "4", ts: "2026-11-18T00:00:00Z", verdict: "incorrect" },
        { input: "5", ts: "2026-11-18T00:00:02Z", verdict: "correct" },
      ],
    })}
    isLastQuestion={true}
    onOpenReview={noop}
  />
);
assert.match(lastCorrectCardHtml, />Review</);
assert.match(lastCorrectCardHtml, />Attempt 2</);

const almostCardHtml = renderToStaticMarkup(
  <AnswerResultCard
    lastCheck={{
      verdict: "equivalent_not_in_form",
      message: "The value is correct, but a fraction is not reduced to lowest terms.",
      components: [{ label: "Value $x_1$", ok: true }, { label: "Value $x_2$", ok: false }],
      diagnostics: [
        {
          code: "unreduced_fraction",
          message: "The value is correct, but a fraction is not reduced to lowest terms.",
        },
      ],
    }}
    state={baseState({ attempts: [{ input: "2/4", ts: "2026-11-18T00:00:00Z", verdict: "equivalent_not_in_form" }] })}
    onTryAgain={noop}
  />
);
assert.match(almostCardHtml, /bg-amber-50/);
assert.doesNotMatch(almostCardHtml, /border-l-/);
assert.match(almostCardHtml, /lucide-minus/);
assert.match(almostCardHtml, /Almost — check the form/);
assert.match(almostCardHtml, /not reduced to lowest terms/);
assert.match(almostCardHtml, /katex/, "component label TeX must render via FormattedText");
assert.match(almostCardHtml, />Try again</);

const wrongCardHtml = renderToStaticMarkup(
  <AnswerResultCard
    lastCheck={{
      verdict: "incorrect",
      message: "Not equal to the verified answer.",
      components: [],
      diagnostics: [{ code: "whole_sign_flip", message: "Check the negative sign." }],
    }}
    state={baseState({
      attempts: [
        { input: "-5", ts: "2026-11-18T00:00:00Z", verdict: "incorrect" },
        { input: "-4", ts: "2026-11-18T00:00:02Z", verdict: "incorrect" },
      ],
    })}
    onTryAgain={noop}
  />
);
assert.match(wrongCardHtml, /bg-rose-50/);
assert.doesNotMatch(wrongCardHtml, /border-l-/);
assert.match(wrongCardHtml, /lucide-x/);
assert.match(wrongCardHtml, />Not quite</);
assert.match(wrongCardHtml, /Check the negative sign\./);
assert.match(wrongCardHtml, />Attempt 2</);
assert.match(wrongCardHtml, />Try again</);

const skippedCardHtml = renderToStaticMarkup(
  <AnswerResultCard
    lastCheck={{
      verdict: "skipped",
      message: "Skipped (Concept Gap / Unsure) — Review step-by-step solution below to solidify mental model.",
      components: [],
      diagnostics: [],
    }}
    state={baseState({ skipped: true, attempts: [{ input: "(Skipped)", ts: "2026-11-18T00:00:00Z", verdict: "skipped" }] })}
    onShowSteps={noop}
  />
);
assert.match(skippedCardHtml, /bg-zinc-50/);
assert.doesNotMatch(skippedCardHtml, /border-l-/);
assert.match(skippedCardHtml, /lucide-skip-forward/);
assert.match(skippedCardHtml, />Skipped</);
assert.doesNotMatch(skippedCardHtml, /Review the steps below/);
assert.match(skippedCardHtml, />Show steps</);

const gatedSkippedCardHtml = renderToStaticMarkup(
  <AnswerResultCard
    lastCheck={{ verdict: "skipped", message: "Skipped", components: [], diagnostics: [] }}
    state={baseState({ skipped: false, attempts: [] })}
    onShowSteps={noop}
  />
);
assert.doesNotMatch(gatedSkippedCardHtml, />Show steps</);

// ---------------------------------------------------------------------------
// 3. Choice auto-submit logic, keyboard shortcuts, and component rendering
// ---------------------------------------------------------------------------
const lineOptions = [
  { id: "1", label: "Line 1" },
  { id: "2", label: "Line 2" },
  { id: "3", label: "Line 3" },
];
const letterOptions = [
  { id: "A", label: "$x-2$" },
  { id: "B", label: "$x+2$" },
  { id: "C", label: "$x-1$" },
];
assert.equal(resolveChoiceKeyOption("2", lineOptions)?.id, "2");
assert.equal(resolveChoiceKeyOption("2", letterOptions)?.id, "B");
assert.equal(resolveChoiceKeyOption("4", letterOptions), null);
assert.equal(resolveChoiceKeyOption("a", letterOptions), null);

assert.equal(isEditableEventTarget({ tagName: "INPUT" } as unknown as EventTarget), true);
assert.equal(isEditableEventTarget({ tagName: "TEXTAREA" } as unknown as EventTarget), true);
assert.equal(isEditableEventTarget({ tagName: "BODY" } as unknown as EventTarget), false);

assert.equal(
  isChoiceInteractionLocked({
    isChecking: true,
    lastCheck: null,
    skipped: false,
    retryUnlocked: false,
  }),
  true
);
assert.equal(
  isChoiceInteractionLocked({
    isChecking: false,
    lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
    skipped: false,
    retryUnlocked: false,
  }),
  true
);
assert.equal(
  isChoiceInteractionLocked({
    isChecking: false,
    lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
    skipped: false,
    retryUnlocked: true,
  }),
  false,
  "Try again must re-enable choice options"
);
assert.equal(
  getChoiceResultStatus({
    isChecking: false,
    lastCheck: { verdict: "incorrect", message: "Wrong", components: [], diagnostics: [] },
    skipped: false,
  }),
  "wrong"
);
assert.equal(
  getChoiceResultStatus({
    isChecking: false,
    lastCheck: { verdict: "correct", message: "Correct.", components: [], diagnostics: [] },
    skipped: false,
  }),
  "correct"
);

// Choice auto-submit guard: calls handler once per click and ignores clicks while checking
async function testChoiceAutoSubmit() {
  const inputCalls: string[] = [];
  const checkCalls: Array<string | undefined> = [];
  let resolveCheck!: () => void;
  let disabled = false;
  let isChecking = false;

  const firstClickPromise = submitChoiceSelection({
    optionId: "2",
    disabled,
    isChecking,
    onStart: () => {
      disabled = true;
      isChecking = true;
    },
    onInputChange: (id) => inputCalls.push(id),
    onCheckAnswer: (id) => {
      checkCalls.push(id);
      return new Promise<void>((resolve) => {
        resolveCheck = resolve;
      });
    },
    onFinish: () => {
      isChecking = false;
      disabled = false;
    },
  });

  // Second click while checking must be ignored
  const secondAccepted = await submitChoiceSelection({
    optionId: "3",
    disabled,
    isChecking,
    onStart: noop,
    onInputChange: (id) => inputCalls.push(id),
    onCheckAnswer: (id) => {
      checkCalls.push(id);
    },
    onFinish: noop,
  });
  assert.equal(secondAccepted, false);
  assert.deepEqual(inputCalls, ["2"]);
  assert.deepEqual(checkCalls, ["2"]);

  resolveCheck();
  const firstAccepted = await firstClickPromise;
  assert.equal(firstAccepted, true);
  assert.equal(isChecking, false);
}

void testChoiceAutoSubmit().then(() => {
  // Check button absent for choice questions in both MathWorkspace and CodeDashboard
  const linePromptText = [
    "A student solved $x^2 = 4$:",
    "Line 1: $x = 2$",
    "Line 2: $x = -2$",
    "Which line is the first one that is wrong?",
  ].join("\n");
  const lineProblem = baseMathProblem({
    prompt: linePromptText,
    answerSpec: {
      type: "choice",
      correct: "1",
      options: [
        { id: "1", label: "Line 1" },
        { id: "2", label: "Line 2" },
      ],
    },
  });
  const lineChoiceMathHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={lineProblem}
      index={0}
      totalQuestions={3}
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
  assert.doesNotMatch(
    lineChoiceMathHtml,
    /aria-label="Check answer"/,
    "Check button must be absent for Math LineChoicePrompt questions"
  );

  const regularChoiceMathHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={baseMathProblem({
        prompt: "Factor $x^2 - 4$.",
        answerSpec: {
          type: "choice",
          correct: "B",
          options: letterOptions,
        },
        state: baseState({
          userInput: "A",
          score: 0,
          lastCheck: { verdict: "incorrect", message: "Not quite", components: [], diagnostics: [] },
          attempts: [{ input: "A", ts: "2026-11-18T00:00:00Z", verdict: "incorrect" }],
        }),
      })}
      index={0}
      totalQuestions={3}
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
  assert.doesNotMatch(
    regularChoiceMathHtml,
    /aria-label="Check answer"/,
    "Check button must be absent for Math choice questions"
  );
  // Chosen wrong option A gets rose styling; correct option B must NOT get emerald styling!
  assert.match(regularChoiceMathHtml, /bg-rose-50/);
  assert.doesNotMatch(
    regularChoiceMathHtml,
    /bg-emerald-50/,
    "Correct choice option must not be highlighted on wrong result"
  );

  const choiceCodeProblem: Problem = {
    id: "Q01",
    templateKey: "prg-choice",
    level: 1,
    levelLabel: "Level 1",
    category: "Tracing",
    prompt: "Which statement is true?",
    answerSpec: {
      type: "choice",
      correct: "B",
      options: letterOptions,
    },
    checkpointHint: "",
    state: baseState({
      userInput: "B",
      score: 1,
      lastCheck: { verdict: "correct", message: "Correct option selected.", components: [], diagnostics: [] },
      attempts: [{ input: "B", ts: "2026-11-18T00:00:00Z", verdict: "correct" }],
    }),
  };
  const choiceCodeHtml = renderToStaticMarkup(
    <CodeDashboard
      problem={choiceCodeProblem}
      drillId="DRL-PRG-T01-C01-01"
      index={0}
      totalQuestions={3}
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
      onNextQuestion={noop}
    />
  );
  assert.doesNotMatch(
    choiceCodeHtml,
    /aria-label="Check answer"/,
    "Check button must be absent for Code choice questions"
  );
  assert.match(choiceCodeHtml, /bg-emerald-50/);
  assert.match(choiceCodeHtml, /Next problem/);

  // Checking spinner + disabled state on ChoiceOptionGroup and LineChoicePrompt
  const checkingGroupHtml = renderToStaticMarkup(
    <ChoiceOptionGroup
      options={letterOptions}
      selectedValue=""
      onSelect={noop}
      disabled={true}
      checkingOptionId="B"
    />
  );
  assert.match(checkingGroupHtml, /disabled=""/);
  assert.match(checkingGroupHtml, /animate-spin/);

  const parsedLine = parseLineChoicePrompt(linePromptText, [
    { id: "1", label: "Line 1" },
    { id: "2", label: "Line 2" },
  ])!;
  const checkingLineHtml = renderToStaticMarkup(
    <LineChoicePrompt
      parsed={parsedLine}
      selectedValue=""
      onSelect={noop}
      disabled={true}
      checkingOptionId="2"
    />
  );
  assert.match(checkingLineHtml, /disabled=""/);
  assert.match(checkingLineHtml, /animate-spin/);

  console.log("answerFeedback tests passed");
});
