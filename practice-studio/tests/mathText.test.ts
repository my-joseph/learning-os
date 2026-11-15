/**
 * Escaped dollar signs in drill text (src/lib/mathText.ts).
 * Run: npx tsx tests/mathText.test.ts
 */
import { isMathSegment, splitMath, unescapeDollar } from "../src/lib/mathText";

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
