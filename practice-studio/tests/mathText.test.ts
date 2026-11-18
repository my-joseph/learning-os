/**
 * Escaped dollar signs in drill text (src/lib/mathText.ts).
 * Run: npx tsx tests/mathText.test.ts
 */
import {
  findBareWordSpansInLatex,
  isMathSegment,
  splitMath,
  toMathText,
  unescapeDollar,
  wrapBareWordsInLatex,
} from "../src/lib/mathText";

function assert(cond: boolean, msg: string) {
  if (!cond) throw new Error(`FAIL: ${msg}`);
}

const prompt =
  "A fee of $\\$15$, plus $\\$2$ per cubic meter for the first $20$ cubic meters. The bill is \\$83 in total.";
const parts = splitMath(prompt);
const math = parts.filter(isMathSegment);
assert(JSON.stringify(math) === JSON.stringify(["$\\$15$", "$\\$2$", "$20$"]), `math tokens: ${JSON.stringify(math)}`);
const plain = parts.filter((p) => !isMathSegment(p)).map(unescapeDollar).join("|");
assert(plain.includes("The bill is $83 in total."), `plain text: ${plain}`);
assert(parts.join("") === prompt, "split loses no text");
assert(JSON.stringify(splitMath("$x^2$ and $y$")) === JSON.stringify(["$x^2$", " and ", "$y$"]), "plain math unchanged");
console.log("mathText tests passed");

// Figure labels: plain sqrt()/cbrt() become LaTeX roots; $...$ labels pass through.
assert(toMathText("y = sqrt(x - 3)") === "$y = \\sqrt{x - 3}$", `sqrt label: ${toMathText("y = sqrt(x - 3)")}`);
assert(toMathText("y = -cbrt(x)") === "$y = -\\sqrt[3]{x}$", "cbrt label");
assert(toMathText("$A$") === "$A$", "dollar label unchanged");
assert(toMathText("P") === "$P$", "plain label wrapped");

// Bare English words safety net (must match math_engine/latex_guard.py)
const unchangedCases = [
  "2x+3",
  "\\frac{a}{b}",
  "\\sin x",
  "mx + b",
  "\\text{if } x>0",
  "abc",
  "V = abc",
  "\\triangle ABC",
  "\\text{Trapezoid } ABCD",
  "\\begin{aligned}x&=1\\\\y&=2\\end{aligned}",
  "x_{max}=8",
  "(f o g)(x)=1/sqrt(sqrt(2x-2))",
  "3+sqrt(x)",
  "\\operatorname{Dom}(f^{-1})=\\operatorname{Range}(f)",
  "ac - bd",
  "mx, ny",
];
for (const c of unchangedCases) {
  assert(findBareWordSpansInLatex(c).length === 0, `expected no bare words in ${c}`);
  assert(wrapBareWordsInLatex(c) === c, `expected unchanged output for ${c}`);
}

assert(
  wrapBareWordsInLatex("y = mx + b; exchange the variables and isolate the new output") ===
    "y = mx + b;\\text{ exchange the variables and isolate the new output}",
  "wraps prose run after equation"
);
assert(
  wrapBareWordsInLatex("y=3x-8; solve for x, then exchange x and y") ===
    "y=3x-8;\\text{ solve for }x,\\text{ then exchange }x\\text{ and }y",
  "wraps prose while preserving math variables and spacing"
);
assert(
  wrapBareWordsInLatex("f(k)=0 iff x-k is a factor") ===
    "f(k)=0\\text{ iff }x-k\\text{ is a factor}",
  "wraps 3-letter English words and bridged phrases"
);
assert(
  wrapBareWordsInLatex("Domain(f)=[0,4]; Range(f)=[1,9)") ===
    "\\text{Domain}(f)=[0,4];\\text{ Range}(f)=[1,9)",
  "wraps Domain and Range"
);
assert(
  wrapBareWordsInLatex("is it") === "\\text{is it}",
  "wraps sequence of >=2 short words"
);
const wrappedOnce = wrapBareWordsInLatex("For a real square root, the radicand must be nonnegative.");
assert(
  wrapBareWordsInLatex(wrappedOnce) === wrappedOnce,
  "wrapBareWordsInLatex is idempotent"
);
console.log("bare word safety net tests passed");
