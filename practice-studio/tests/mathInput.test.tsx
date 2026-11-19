import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type {
  convertAsciiMathToLatex as ConvertAsciiFn,
  convertLatexToAsciiMath as ConvertLatexFn,
} from "mathlive";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import { isEditableEventTarget } from "../src/lib/answerFeedback";
import {
  getUnitKeyboardProfile,
  isMathLiveSupportedAnswerSpec,
  MATH_INPUT_MODE_STORAGE_KEY,
  normalizeMathLiveAsciiMath,
  plainTextToLatex,
  readMathInputMode,
  writeMathInputMode,
} from "../src/lib/mathInput";
import type { AnswerSpec, DrillDocument, Problem } from "../src/types/drill";

async function main() {
const mlSsr = (await import("mathlive")) as {
  convertAsciiMathToLatex: typeof ConvertAsciiFn;
  convertLatexToAsciiMath: typeof ConvertLatexFn;
};
const { convertAsciiMathToLatex, convertLatexToAsciiMath } = mlSsr;

function latexToPlain(latex: string, variables: readonly string[] = []): string {
  const ascii = convertLatexToAsciiMath(latex);
  return normalizeMathLiveAsciiMath(ascii, latex, variables);
}

// ---------------------------------------------------------------------------
// 1. Normaliser unit tests across every math notation format
// ---------------------------------------------------------------------------
const normCases: Array<{
  name: string;
  latex: string;
  expected: string;
  variables?: string[];
}> = [
  { name: "integer", latex: "900", expected: "900" },
  { name: "negative integer", latex: "-13", expected: "-13" },
  { name: "decimal", latex: "92.86", expected: "92.86" },
  { name: "fraction", latex: "\\frac{3}{5}", expected: "(3)/(5)" },
  { name: "negative fraction", latex: "-\\frac{7}{4}", expected: "-(7)/(4)" },
  { name: "algebraic fraction", latex: "\\frac{x-9}{4}", expected: "(x-9)/(4)" },
  { name: "square root", latex: "\\sqrt{7}", expected: "sqrt(7)" },
  { name: "radical sum", latex: "3+\\sqrt{x}", expected: "3+sqrt(x)" },
  { name: "radical fraction", latex: "\\frac{-1+\\sqrt{5}}{2}", expected: "(-1+sqrt(5))/(2)" },
  { name: "cube root", latex: "\\sqrt[3]{8}", expected: "(8)^(1/(3))" },
  { name: "nth root", latex: "\\sqrt[n]{x+1}", expected: "(x+1)^(1/(n))" },
  { name: "complex a+bi", latex: "-1+2i", expected: "-1+2*i" },
  { name: "complex fraction", latex: "\\frac{3}{5}+\\frac{4}{5}i", expected: "(3)/(5)+(4)/(5)*i" },
  { name: "plus-minus complex", latex: "3\\pm 4i", expected: "3+-4*i" },
  { name: "polynomial implicit mul", latex: "2x^2+7x+7", expected: "2*x^2+7*x+7" },
  {
    name: "nested fraction power",
    latex: "2\\left(\\frac{x-1}{3}\\right)^2+4",
    expected: "2*((x-1)/(3))^2+4",
  },
  { name: "factored product", latex: "-3(x+1)(x-2)", expected: "-3*(x+1)*(x-2)" },
  { name: "pi multiple with i", latex: "2\\pi i", expected: "2*pi*i" },
  { name: "concatenated variables", latex: "xy", expected: "x*y" },
  { name: "abs simple", latex: "|x-3|", expected: "abs(x-3)" },
  { name: "abs left-right", latex: "\\left|2x+1\\right|", expected: "abs(2*x+1)" },
  { name: "abs multiple terms", latex: "|x-1|+|x+2|", expected: "abs(x-1)+abs(x+2)" },
  { name: "abs nested", latex: "||x|-1|", expected: "abs(abs(x)-1)" },
  { name: "abs with coefficient", latex: "2|x-3|", expected: "2*abs(x-3)" },
  { name: "interval half-open", latex: "\\left[-\\frac{2}{3}, 2\\right]", expected: "[-(2)/(3), 2]" },
  { name: "interval mixed", latex: "[1, 9)", expected: "[1, 9)" },
  {
    name: "interval union with infinity",
    latex: "(-\\infty, -1) \\cup (-1, 3) \\cup (3, \\infty)",
    expected: "(-oo, -1) U (-1, 3) U (3, oo)",
  },
  { name: "solution set braces", latex: "\\{-5, 11\\}", expected: "{-5, 11}" },
  { name: "solution set left-right braces", latex: "\\left\\{-5, 11\\right\\}", expected: "{-5, 11}" },
  { name: "solution set radicals", latex: "\\{-\\sqrt{7},\\; \\sqrt{7}\\}", expected: "{-sqrt(7), sqrt(7)}" },
  { name: "solution set subscripted", latex: "x_1 = 2, x_2 = -3", expected: "x_1=2, x_2=-3" },
  { name: "inequality le", latex: "x \\le 5", expected: "x<=5" },
  { name: "inequality ge", latex: "x \\ge -2", expected: "x>=-2" },
  { name: "inequality ne", latex: "x \\ne 0", expected: "x!=0" },
  { name: "trig sin", latex: "\\sin(x)", expected: "sin(x)" },
  { name: "trig power", latex: "\\sin^2(x)", expected: "(sin(x))^2" },
  { name: "log natural", latex: "\\ln(x+1)", expected: "ln(x+1)" },
  { name: "log natural simple", latex: "\\ln(x)", expected: "ln(x)" },
  { name: "log common", latex: "\\log(x)", expected: "log(x)" },
  { name: "log base 10", latex: "\\log_{10}(x)", expected: "log(x, 10)" },
  { name: "log base 2 braced", latex: "\\log_{2}(8)", expected: "log(8, 2)" },
  { name: "log base 2 unbraced", latex: "\\log_2(8)", expected: "log(8, 2)" },
  { name: "log base single letter", latex: "\\log_b(x+1)", expected: "log(x+1, b)" },
  { name: "log base expression", latex: "\\log_{a+1}(2x)", expected: "log(2*x, a+1)" },
  { name: "log base fraction", latex: "\\log_{\\frac{1}{2}}(4)", expected: "log(4, (1)/(2))" },
  { name: "log base with coefficient", latex: "2\\log_2(8)+1", expected: "2*log(8, 2)+1" },
  { name: "log base nested", latex: "\\log_2(\\log_3(x))", expected: "log(log(x, 3), 2)" },
  { name: "log base power", latex: "\\log_2^2(8)", expected: "(log(8, 2))^2" },
  { name: "vector angle brackets", latex: "\\langle 1, -2, 3 \\rangle", expected: "<1, -2, 3>" },
  { name: "empty placeholder fraction", latex: "\\frac{\\placeholder{}}{\\placeholder{}}", expected: "" },
];

for (const tc of normCases) {
  const actual = latexToPlain(tc.latex, tc.variables);
  assert.equal(actual, tc.expected, `Failed normaliser case "${tc.name}" for ${tc.latex}`);
}

// Direct ASCII-math log-base normalization cases (e.g. MathLive single-char and braced bases)
assert.equal(normalizeMathLiveAsciiMath("log _2(8)"), "log(8, 2)");
assert.equal(normalizeMathLiveAsciiMath("log_2(8)"), "log(8, 2)");
assert.equal(normalizeMathLiveAsciiMath("log _b(x)"), "log(x, b)");
assert.equal(normalizeMathLiveAsciiMath("log_{2}(8)"), "log(8, 2)");
assert.equal(normalizeMathLiveAsciiMath("log_{10}(x)"), "log(x, 10)");
assert.equal(normalizeMathLiveAsciiMath("log _(10)(x)"), "log(x, 10)");
assert.equal(normalizeMathLiveAsciiMath("ln(x)"), "ln(x)");

// Plain text -> LaTeX -> Plain text idempotency
const roundTripPlains = [
  "3/5",
  "-7/4",
  "2*x^2 + 3*x - 2 + 3/(2*x - 1)",
  "2*((x-1)/3)^2+4",
  "3 + 4*i, 3 - 4*i",
  "3 +- 4*i",
  "-sqrt(7), sqrt(7)",
  "[-2/3, 2]",
  "[1,9)",
  "(1, 9]",
  "(-oo, -1) U (-1, 3) U (3, oo)",
  "abs(x-3)",
  "(x-1)^(1/3)",
];
for (const plain of roundTripPlains) {
  const latex = plainTextToLatex(plain, convertAsciiMathToLatex);
  const back = latexToPlain(latex);
  assert.ok(back.length > 0, `Round-trip produced empty string for ${plain}`);
}
assert.equal(latexToPlain(plainTextToLatex("[1,9)", convertAsciiMathToLatex)), "[1, 9)");
assert.equal(latexToPlain(plainTextToLatex("(1, 9]", convertAsciiMathToLatex)), "(1, 9]");

// ---------------------------------------------------------------------------
// 2. AnswerSpec support, unit keyboard profile, storage & editable-target guards
// ---------------------------------------------------------------------------
assert.equal(isMathLiveSupportedAnswerSpec({ type: "number" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "complex" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "expression" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "solution_set" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "interval" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "tuple" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "vector" }), true);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "choice" }), false);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "text" }), false);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "code_output" }), false);
assert.equal(isMathLiveSupportedAnswerSpec({ type: "unknown_future" as AnswerSpec["type"] }), false);

assert.deepEqual(
  getUnitKeyboardProfile({ unitCode: "MTH-T02-C02-U04", drillTitle: "Composition of Functions" }),
  { trig: false, log: false }
);
assert.deepEqual(
  getUnitKeyboardProfile({ unitCode: "MTH-T02-C05-U03", drillTitle: "Logarithmic Functions" }),
  { trig: false, log: true }
);
assert.deepEqual(
  getUnitKeyboardProfile({ unitCode: "MTH-T02-C06-U03", drillTitle: "Unit Circle" }),
  { trig: true, log: false }
);
assert.deepEqual(
  getUnitKeyboardProfile({ prompt: "Evaluate $\\sin(x) + \\ln(x)$." }),
  { trig: true, log: true }
);

assert.equal(
  isEditableEventTarget({ tagName: "MATH-FIELD" } as unknown as EventTarget),
  true
);

// localStorage helper safety (including throwing storage)
const g = globalThis as unknown as { window?: unknown };
const prevWindow = g.window;
try {
  const store = new Map<string, string>();
  g.window = {
    localStorage: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => store.set(k, v),
    },
  };
  assert.equal(readMathInputMode(), "math");
  writeMathInputMode("plain");
  assert.equal(store.get(MATH_INPUT_MODE_STORAGE_KEY), "plain");
  assert.equal(readMathInputMode(), "plain");

  g.window = {
    localStorage: {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
    },
  };
  assert.equal(readMathInputMode(), "math");
  writeMathInputMode("plain"); // must not throw
} finally {
  g.window = prevWindow;
}

// ---------------------------------------------------------------------------
// 3. UI fallback tests in MathWorkspace
// ---------------------------------------------------------------------------
const noop = () => {};
function makeProblem(answerSpec: AnswerSpec): Problem {
  return {
    id: "Q01",
    templateKey: "tpl",
    level: 1,
    levelLabel: "Level 1",
    category: "Algebra",
    prompt: "Evaluate $1 + 1$.",
    answerSpec,
    checkpointHint: "",
    state: {
      userInput: "",
      score: null,
      divergedStep: null,
      mistakes: [],
      lastCheck: null,
      attempts: [],
    },
  };
}

const mathEntryHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={makeProblem({ type: "number" })}
    index={0}
    totalQuestions={1}
    unitCode="MTH-T01-C04-U01"
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
assert.match(mathEntryHtml, />Plain text</, "Supported math entry should expose Plain text toggle");
assert.match(
  mathEntryHtml,
  /<button[^>]*aria-label="Check answer"[^>]*title="Check \(Enter\)"[^>]*class="[^"]*w-8 h-8 rounded-lg[^"]*"[^>]*><svg[^>]*lucide-equal/
);

const unsupportedFallbackHtml = renderToStaticMarkup(
  <MathWorkspace
    problem={makeProblem({ type: "text", accepted: ["even"] })}
    index={0}
    totalQuestions={1}
    unitCode="MTH-T02-C02-U01"
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
assert.match(
  unsupportedFallbackHtml,
  /<input[^>]*type="text"[^>]*aria-label="Answer for question Q01"[^>]*class="[^"]*pr-12[^"]*"/,
  "Unsupported answerSpec type must fall back to plain-text input with reserved right padding"
);
assert.match(
  unsupportedFallbackHtml,
  /<button[^>]*aria-label="Check answer"[^>]*title="Check \(Enter\)"[^>]*class="[^"]*w-8 h-8 rounded-lg[^"]*"[^>]*><svg[^>]*lucide-equal/
);
assert.doesNotMatch(
  unsupportedFallbackHtml,
  />Plain text</,
  "Plain-text fallback should not show Math/Plain toggle"
);

// ---------------------------------------------------------------------------
// 4. Corpus-wide round-trip check across every MTH drill in drills/data/
// ---------------------------------------------------------------------------
const repoRoot = path.resolve(process.cwd(), "..");
const drillsDataDir = path.join(repoRoot, "drills", "data");

interface CheckerBatchItem {
  label: string;
  answerSpec: AnswerSpec;
  input: string;
}

const batch: CheckerBatchItem[] = [];
const unsupportedInDrills: string[] = [];
let mthDrillFiles = 0;
let mthNonChoiceCount = 0;

if (fs.existsSync(drillsDataDir)) {
  for (const dirEntry of fs.readdirSync(drillsDataDir, { withFileTypes: true })) {
    if (!dirEntry.isDirectory() || !dirEntry.name.startsWith("MTH-")) continue;
    const dirPath = path.join(drillsDataDir, dirEntry.name);
    for (const fileEntry of fs.readdirSync(dirPath)) {
      if (!fileEntry.endsWith(".json")) continue;
      mthDrillFiles++;
      const doc = JSON.parse(
        fs.readFileSync(path.join(dirPath, fileEntry), "utf8")
      ) as DrillDocument;
      for (const prob of doc.problems || []) {
        if (prob.answerSpec?.type === "choice") continue;
        mthNonChoiceCount++;
        if (!isMathLiveSupportedAnswerSpec(prob.answerSpec)) {
          unsupportedInDrills.push(`${doc.drillId}:${prob.id}:${prob.answerSpec?.type}`);
          continue;
        }
        const vars = prob.answerSpec.variables || [];
        if (prob.answerDisplay && !prob.answerDisplay.includes("\\text")) {
          // Some drills store plain-text `oo` / `sqrt(` in answerDisplay without backslashes;
          // normalize those to canonical LaTeX just as MathLive inline shortcuts produce.
          const displayLatex = prob.answerDisplay
            .replace(/(?<![\\A-Za-z])oo(?![A-Za-z])/g, "\\infty")
            .replace(/(?<![\\A-Za-z])sqrt\(/g, "\\sqrt{")
            .replace(/(\\sqrt\{[^}]*)\)/g, "$1}");
          const fromDisplay = latexToPlain(displayLatex, vars);
          batch.push({
            label: `${doc.drillId}:${prob.id}:answerDisplay`,
            answerSpec: prob.answerSpec,
            input: fromDisplay,
          });
        }
        if (prob.answerPlain) {
          const roundTripped = latexToPlain(
            plainTextToLatex(prob.answerPlain, convertAsciiMathToLatex),
            vars
          );
          batch.push({
            label: `${doc.drillId}:${prob.id}:answerPlain`,
            answerSpec: prob.answerSpec,
            input: roundTripped,
          });
        }
      }
    }
  }
}

assert.equal(
  unsupportedInDrills.length,
  0,
  `Unexpected unsupported MTH answerSpecs: ${unsupportedInDrills.join(", ")}`
);
assert.ok(mthNonChoiceCount > 0, "Expected MTH non-choice problems in drills/data");

// Evaluate every converted answer using the canonical Python math_engine.answer_check
const venvPython = path.join(repoRoot, ".venv", "bin", "python");
const pythonBin = fs.existsSync(venvPython) ? venvPython : "python3";
const pyScript = [
  "import json, sys",
  "from math_engine.answer_check import check_answer",
  "items = json.loads(sys.stdin.read())",
  "failures = []",
  "for item in items:",
  "    res = check_answer(item['answerSpec'], item['input'])",
  "    if res.get('verdict') != 'correct':",
  "        failures.append({'label': item['label'], 'input': item['input'], 'res': res})",
  "print(json.dumps({'checked': len(items), 'failures': failures}))",
].join("\n");

const pyRun = spawnSync(pythonBin, ["-c", pyScript], {
  cwd: repoRoot,
  input: JSON.stringify(batch),
  encoding: "utf8",
  env: { ...process.env, PYTHONPATH: repoRoot },
});
assert.equal(pyRun.status, 0, `Python checker failed: ${pyRun.stderr}`);
const pyResult = JSON.parse(pyRun.stdout) as {
  checked: number;
  failures: Array<{ label: string; input: string; res: unknown }>;
};
assert.equal(
  pyResult.failures.length,
  0,
  `Round-trip checker failures:\n${JSON.stringify(pyResult.failures, null, 2)}`
);

console.log(
  `mathInput tests passed (${normCases.length} unit cases, ${mthDrillFiles} MTH drills, ${mthNonChoiceCount} problems, ${pyResult.checked} checker round-trips verified)`
);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
