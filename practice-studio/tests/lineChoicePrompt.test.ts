/**
 * Unit tests for line-based choice prompt parser (src/lib/lineChoicePrompt.ts).
 * Run: npx tsx tests/lineChoicePrompt.test.ts
 */
import { parseLineChoicePrompt } from "../src/lib/lineChoicePrompt";

function assert(cond: boolean, msg: string) {
  if (!cond) throw new Error(`FAIL: ${msg}`);
}

const samplePrompt = [
  "A student computed the larger root of $3x^2 - 7x - 6 = 0$ using the quadratic formula:",
  "Line 1: $x_+ = \\frac{-(-7) + \\sqrt{(-7)^2 - 4(3)(-6)}}{2(3)}$",
  "Line 2: $= \\frac{7 + \\sqrt{49 + 72}}{2}$",
  "Line 3: $= \\frac{7 + \\sqrt{121}}{2}$",
  "Line 4: $= \\frac{7 + 11}{2}$",
  "Line 5: $= 9$",
  "Which line is the first one that is wrong?",
].join("\n");

const sampleOptions = [
  { id: "1", label: "Line 1" },
  { id: "2", label: "Line 2" },
  { id: "3", label: "Line 3" },
  { id: "4", label: "Line 4" },
  { id: "5", label: "Line 5" },
];

const parsed = parseLineChoicePrompt(samplePrompt, sampleOptions);
assert(parsed !== null, "should parse 5-line choice prompt");
assert(
  parsed!.intro ===
    "A student computed the larger root of $3x^2 - 7x - 6 = 0$ using the quadratic formula:",
  "should extract intro"
);
assert(parsed!.outro === "Which line is the first one that is wrong?", "should extract outro");
assert(parsed!.items.length === 5, `expected 5 items, got ${parsed!.items.length}`);
assert(parsed!.items[1].option.id === "2", "second item should have option id '2'");
assert(parsed!.items[4].content === "$= 9$", `unexpected line 5 content: ${parsed!.items[4].content}`);

// Non-line multiple choice falls back to null
const regular = parseLineChoicePrompt("What is $2 + 2$?", [
  { id: "A", label: "3" },
  { id: "B", label: "4" },
]);
assert(regular === null, "regular choice prompt should return null");

// Mismatched count falls back to null
const mismatched = parseLineChoicePrompt(samplePrompt, sampleOptions.slice(0, 4));
assert(mismatched === null, "mismatched option count should return null");

// Non-contiguous Line blocks fall back to null
const nonContiguous = parseLineChoicePrompt(
  "Line 1: $a$\nSome text\nLine 2: $b$",
  [
    { id: "1", label: "Line 1" },
    { id: "2", label: "Line 2" },
  ]
);
assert(nonContiguous === null, "non-contiguous lines should return null");

console.log("lineChoicePrompt tests passed");
