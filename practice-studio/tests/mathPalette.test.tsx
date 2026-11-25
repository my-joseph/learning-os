import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MathKeyIcon, MATH_KEY_ICONS } from "../src/components/math/MathKeyIcons";
import { IconButton } from "../src/components/ui/shadcn/Button";
import { MathPalette, MathPaletteView } from "../src/components/math/MathPalette";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import {
  getMathPaletteSections,
  insertLatexIntoMathField,
  QUICK_PALETTE_KEYS,
  type MathFieldInsertTarget,
} from "../src/lib/mathPalette";
import type { Problem } from "../src/types/drill";

async function main() {
  const noop = () => {};

  function findElements(
    node: React.ReactNode,
    predicate: (el: React.ReactElement<Record<string, unknown>>) => boolean
  ): React.ReactElement<Record<string, unknown>>[] {
    const matches: React.ReactElement<Record<string, unknown>>[] = [];
    const visit = (cur: React.ReactNode) => {
      if (Array.isArray(cur)) {
        for (const item of cur) visit(item);
        return;
      }
      if (!React.isValidElement(cur)) return;
      const el = cur as React.ReactElement<Record<string, unknown>>;
      if (predicate(el)) matches.push(el);
      if (el.props && "children" in el.props) {
        visit(el.props.children as React.ReactNode);
      }
    };
    visit(node);
    return matches;
  }

  // ---------------------------------------------------------------------------
  // 1. Toolbar renders both modes with aria-pressed; plain-text hides quick keys & panel
  // ---------------------------------------------------------------------------
  const mathToolbarHtml = renderToStaticMarkup(
    <MathPalette
      inputMode="math"
      onModeChange={noop}
      keyboardProfile={{ trig: false, log: false }}
      panelOpen={false}
      onTogglePanel={noop}
      onInsertLatex={noop}
    />
  );

  assert.match(
    mathToolbarHtml,
    /<button[^>]*aria-pressed="true"[^>]*>.*?Math input<\/span><\/button>/,
    "Math input mode button must render with aria-pressed=true in math mode"
  );
  assert.match(
    mathToolbarHtml,
    /<button[^>]*aria-pressed="false"[^>]*>.*?Plain text<\/span><\/button>/,
    "Plain text mode button must render with aria-pressed=false in math mode"
  );
  for (const qk of QUICK_PALETTE_KEYS) {
    assert.ok(
      mathToolbarHtml.includes(`aria-label="${qk.label}"`),
      `Quick key "${qk.label}" must render in math mode toolbar`
    );
    assert.ok(
      mathToolbarHtml.includes(`title="${qk.label}"`),
      `Quick key "${qk.label}" must have tooltip title`
    );
  }
  assert.match(mathToolbarHtml, /aria-label="Open math palette"/);
  assert.match(mathToolbarHtml, /aria-expanded="false"/);
  assert.doesNotMatch(mathToolbarHtml, /role="region" aria-label="Math symbol palette"/);

  const plainToolbarHtml = renderToStaticMarkup(
    <MathPalette
      inputMode="plain"
      onModeChange={noop}
      keyboardProfile={{ trig: true, log: true }}
      panelOpen={true}
      onTogglePanel={noop}
      onInsertLatex={noop}
    />
  );
  assert.match(
    plainToolbarHtml,
    /<button[^>]*aria-pressed="false"[^>]*>.*?Math input<\/span><\/button>/
  );
  assert.match(
    plainToolbarHtml,
    /<button[^>]*aria-pressed="true"[^>]*>.*?Plain text<\/span><\/button>/
  );
  const modeGeometry = (html: string) =>
    Array.from(html.matchAll(/<button(?=[^>]*aria-pressed)[^>]*class="([^"]+)"[^>]*>/g))
      .slice(0, 2).map((match) => match[1]);
  const modeClasses = modeGeometry(mathToolbarHtml);
  assert.equal(modeClasses.length, 2);
  assert.deepEqual(modeGeometry(plainToolbarHtml), modeClasses);
  assert.ok(modeClasses.every((classes) => classes.includes("min-h-touch") && classes.includes("sm:h-control-xs")));
  assert.doesNotMatch(plainToolbarHtml, /aria-label="Quick math templates"/);
  assert.doesNotMatch(plainToolbarHtml, /aria-label="Fraction"/);
  assert.doesNotMatch(plainToolbarHtml, /aria-label="Math symbol palette"/);

  // ---------------------------------------------------------------------------
  // 2. Panel sections render (BASIC, FUNCTIONS with/without trig, SYMBOLS)
  // ---------------------------------------------------------------------------
  const openNoTrigHtml = renderToStaticMarkup(
    <MathPalette
      inputMode="math"
      onModeChange={noop}
      keyboardProfile={{ trig: false, log: false }}
      panelOpen={true}
      onTogglePanel={noop}
      onInsertLatex={noop}
    />
  );

  assert.match(openNoTrigHtml, /role="region" aria-label="Math symbol palette"/);
  assert.match(
    openNoTrigHtml,
    /role="region" aria-label="Math symbol palette" class="rounded-xl border border-border/,
    "Expanded palette panel must be its own quiet rounded-xl bordered block"
  );
  assert.doesNotMatch(
    openNoTrigHtml,
    /border-t/,
    "MathPalette toolbar and panel must not use attached border-t dividers"
  );
  // Learner 2026-11-19: no X close button in the expanded panel; the "..." toggle closes it.
  assert.doesNotMatch(openNoTrigHtml, /title="Close \(Esc\)"/);
  assert.match(openNoTrigHtml, /aria-label="Close math palette"[^>]*aria-expanded="true"/);
  assert.match(openNoTrigHtml, />Basic</);
  assert.match(openNoTrigHtml, />Functions</);
  assert.match(openNoTrigHtml, />Symbols</);
  assert.match(openNoTrigHtml, /aria-label="Natural logarithm ln"/);
  assert.match(openNoTrigHtml, /aria-label="Common logarithm log"/);
  assert.match(openNoTrigHtml, /aria-label="Logarithm with base"/);
  assert.match(openNoTrigHtml, /aria-label="Empty set \(∅\)"/);
  assert.doesNotMatch(openNoTrigHtml, /aria-label="Sine"/);
  assert.doesNotMatch(openNoTrigHtml, /aria-label="Inverse sine \(arcsin\)"/);

  const openWithTrigHtml = renderToStaticMarkup(
    <MathPalette
      inputMode="math"
      onModeChange={noop}
      keyboardProfile={{ trig: true, log: false }}
      panelOpen={true}
      onTogglePanel={noop}
      onInsertLatex={noop}
    />
  );

  assert.match(openWithTrigHtml, /aria-label="Sine"/);
  assert.match(openWithTrigHtml, /aria-label="Cosine"/);
  assert.match(openWithTrigHtml, /aria-label="Tangent"/);
  assert.match(openWithTrigHtml, /aria-label="Inverse sine \(arcsin\)"/);
  assert.match(openWithTrigHtml, /aria-label="Inverse cosine \(arccos\)"/);
  assert.match(openWithTrigHtml, /aria-label="Inverse tangent \(arctan\)"/);

  // ---------------------------------------------------------------------------
  // 3. Every key renders an <svg> icon and zero MathLive static markup is used
  // ---------------------------------------------------------------------------
  const allKeys = [
    ...QUICK_PALETTE_KEYS,
    ...getMathPaletteSections({ trig: true }).flatMap((section) => section.keys),
  ];

  for (const key of allKeys) {
    assert.ok(key.iconId in MATH_KEY_ICONS, `Missing custom SVG icon for key ${key.id}`);
    const iconHtml = renderToStaticMarkup(<MathKeyIcon iconId={key.iconId} />);
    assert.match(iconHtml, /^<svg\b/, `Key ${key.id} icon must render an <svg> root`);
    assert.doesNotMatch(iconHtml, /ML__latex|ML__ams|ML__error/, `Key ${key.id} must not use MathLive static markup`);
  }

  // Every key button inside the rendered palette contains an <svg> and no MathLive static markup
  assert.doesNotMatch(
    openWithTrigHtml,
    /ML__latex|ML__ams|ML__error/,
    "Open palette must never render MathLive static markup for keycaps"
  );
  const decodeHtmlAttr = (s: string) => s.replaceAll("&#x27;", "'").replaceAll("&amp;", "&");
  const keyButtonMatches = Array.from(
    openWithTrigHtml.matchAll(/<button[^>]*aria-label="([^"]+)"[^>]*>([\s\S]*?)<\/button>/g)
  ).map((m) => [decodeHtmlAttr(m[1]), m[2]] as const);
  for (const key of allKeys) {
    const matchingButtons = keyButtonMatches.filter(([label]) => label === key.label);
    assert.ok(matchingButtons.length >= 1, `Expected rendered button for key "${key.label}"`);
    for (const [, innerHtml] of matchingButtons) {
      assert.match(innerHtml, /<svg\b/, `Button "${key.label}" must contain an <svg> icon`);
    }
  }

  // Template keys with placeholders must render dashed rounded-square <rect> placeholders
  for (const iconId of [
    "frac",
    "square",
    "power",
    "sqrt",
    "cbrt",
    "nroot",
    "abs",
    "exp",
    "le",
    "ge",
    "ne",
    "parens",
    "brackets",
    "ln",
    "log",
    "logb",
    "sin",
    "cos",
    "tan",
    "arcsin",
    "arccos",
    "arctan",
  ] as const) {
    const iconHtml = renderToStaticMarkup(<MathKeyIcon iconId={iconId} />);
    assert.match(
      iconHtml,
      /<rect[^>]*stroke-dasharray="1\.5 1\.5"/,
      `Template icon "${iconId}" must include dashed <Placeholder /> rect`
    );
  }

  // ---------------------------------------------------------------------------
  // 4. Clicking a key calls insert with the right LaTeX (mock field)
  // ---------------------------------------------------------------------------
  const recordedCommands: unknown[] = [];
  let focusCount = 0;
  const mockField: MathFieldInsertTarget = {
    executeCommand: (cmd) => {
      recordedCommands.push(cmd);
      return true;
    },
    focus: () => {
      focusCount++;
    },
  };

  const tree = MathPaletteView({
    inputMode: "math",
    onModeChange: noop,
    keyboardProfile: { trig: true, log: true },
    panelOpen: true,
    onTogglePanel: noop,
    onInsertLatex: (latex) => {
      insertLatexIntoMathField(mockField, latex);
    },
  });

  const fracButtons = findElements(
    tree,
    (el) => el.type === IconButton && el.props["aria-label"] === "Fraction"
  );
  assert.equal(fracButtons.length, 2, "Expected quick-insert + panel Fraction buttons");
  (fracButtons[0].props.onClick as () => void)();
  assert.deepEqual(recordedCommands[0], [
    "insert",
    "\\frac{#@}{#?}",
    { selectionMode: "placeholder", focus: true },
  ]);
  assert.equal(focusCount, 1);

  const logBaseButtons = findElements(
    tree,
    (el) => el.type === IconButton && el.props["aria-label"] === "Logarithm with base"
  );
  assert.equal(logBaseButtons.length, 1);
  (logBaseButtons[0].props.onClick as () => void)();
  assert.deepEqual(recordedCommands[1], [
    "insert",
    "\\log_{#?}(#0)",
    { selectionMode: "placeholder", focus: true },
  ]);
  assert.equal(focusCount, 2);

  const arcsinButtons = findElements(
    tree,
    (el) => el.type === IconButton && el.props["aria-label"] === "Inverse sine (arcsin)"
  );
  assert.equal(arcsinButtons.length, 1);
  (arcsinButtons[0].props.onClick as () => void)();
  assert.deepEqual(recordedCommands[2], [
    "insert",
    "\\arcsin(#0)",
    { selectionMode: "placeholder", focus: true },
  ]);
  assert.equal(focusCount, 3);

  // ---------------------------------------------------------------------------
  // 5. Floating virtual keyboard disabled, no MathLive keycap renderer, no purple accent
  // ---------------------------------------------------------------------------
  const srcDir = path.resolve(process.cwd(), "src");
  const mathLiveInputSource = readFileSync(
    path.join(srcDir, "components/math/MathLiveInput.tsx"),
    "utf8"
  );
  const mathPaletteSource = readFileSync(
    path.join(srcDir, "components/math/MathPalette.tsx"),
    "utf8"
  );
  const mathKeyIconsSource = readFileSync(
    path.join(srcDir, "components/math/MathKeyIcons.tsx"),
    "utf8"
  );
  const mathPaletteLibSource = readFileSync(
    path.join(srcDir, "lib/mathPalette.ts"),
    "utf8"
  );
  const mathLiveCss = readFileSync(
    path.join(srcDir, "components/math/mathlive-studio.css"),
    "utf8"
  );

  assert.match(
    mathLiveInputSource,
    /mf\.mathVirtualKeyboardPolicy\s*=\s*"manual"/,
    "MathLiveInput must set mathVirtualKeyboardPolicy to manual"
  );
  assert.match(
    mathLiveInputSource,
    /"math-virtual-keyboard-policy":\s*"manual"/,
    "math-field element must carry math-virtual-keyboard-policy=manual"
  );
  assert.doesNotMatch(
    mathLiveInputSource,
    /mathVirtualKeyboard\.show\b|mathVirtualKeyboard\?\.\s*show\b|policy\s*=\s*"auto"/,
    "Floating MathLive virtual keyboard must never be shown"
  );
  assert.doesNotMatch(
    `${mathPaletteSource}\n${mathKeyIconsSource}\n${mathPaletteLibSource}\n${mathLiveCss}`,
    /convertLatexToMarkup|ML__latex|ML__ams|renderPaletteKeyMarkup/,
    "Palette keycaps must use custom SVGs, never MathLive static markup"
  );
  assert.doesNotMatch(
    `${mathLiveInputSource}\n${mathPaletteSource}\n${mathKeyIconsSource}\n${mathLiveCss}`,
    /\bpurple-\d+/,
    "Palette and math input must use zinc neutrals + indigo accent, never purple"
  );

  // ---------------------------------------------------------------------------
  // 6. MathWorkspace integration: choice questions unaffected
  // ---------------------------------------------------------------------------
  const choiceProblem: Problem = {
    id: "Q02",
    templateKey: "tpl",
    level: 1,
    levelLabel: "Level 1",
    category: "Algebra",
    prompt: "Pick one:",
    answerSpec: {
      type: "choice",
      options: [
        { id: "A", label: "$1$" },
        { id: "B", label: "$2$" },
      ],
      accepted: ["A"],
    },
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

  const choiceHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={choiceProblem}
      index={0}
      totalQuestions={1}
      unitCode="MTH-T01-C01-U01"
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
  assert.doesNotMatch(choiceHtml, /Answer input mode/);
  assert.doesNotMatch(choiceHtml, /Quick math templates/);

  // ---------------------------------------------------------------------------
  // 7. Focus ring wraps ONLY the input field (+ embedded = button), not MathPalette
  // ---------------------------------------------------------------------------
  const mathProblem: Problem = {
    ...choiceProblem,
    id: "Q01",
    prompt: "Simplify $\\frac{2}{4}$.",
    answerSpec: { type: "number" },
  };
  const mathWorkspaceHtml = renderToStaticMarkup(
    <MathWorkspace
      problem={mathProblem}
      index={0}
      totalQuestions={1}
      unitCode="MTH-T01-C01-U01"
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

  const focusRingMatches = mathWorkspaceHtml.match(/focus-within:ring-2/g) ?? [];
  assert.equal(focusRingMatches.length, 1, "Only the answer field container should carry focus-within:ring-2");

  const focusRingOpenMatch = /<div\b[^>]*focus-within:ring-2[^>]*>/.exec(mathWorkspaceHtml);
  assert.ok(focusRingOpenMatch, "Expected focused field container div");
  const startIdx = focusRingOpenMatch.index;
  let depth = 0;
  let endIdx = -1;
  const tagRegex = /<\/?div\b[^>]*>/g;
  tagRegex.lastIndex = startIdx;
  let m: RegExpExecArray | null;
  while ((m = tagRegex.exec(mathWorkspaceHtml)) !== null) {
    if (m[0].startsWith("</div")) {
      depth--;
      if (depth === 0) {
        endIdx = m.index + m[0].length;
        break;
      }
    } else if (!m[0].endsWith("/>")) {
      depth++;
    }
  }
  assert.ok(endIdx > startIdx, "Expected balanced closing </div> for focused field container");
  const focusRingHtml = mathWorkspaceHtml.slice(startIdx, endIdx);
  assert.match(focusRingHtml, /aria-label="Check answer"/, "Embedded Check button lives inside the focused field");
  assert.match(focusRingHtml, /lucide-equal/, "Embedded Check button uses Equal icon");
  assert.doesNotMatch(focusRingHtml, /Answer input mode/, "Mode switch toolbar must live outside the focused field");
  assert.doesNotMatch(focusRingHtml, /Quick math templates/, "Quick keys toolbar must live outside the focused field");
  assert.doesNotMatch(focusRingHtml, /Math symbol palette/, "Expanded palette must live outside the focused field");

  assert.match(mathWorkspaceHtml, /class="space-y-space-2"/, "Field and toolbar row should use tight 8px spacing");
  assert.match(mathToolbarHtml, /min-h-touch min-w-touch[^"]*sm:h-control-xs/, "Math/Plain mode buttons must keep >=44px mobile target height");
  assert.match(mathToolbarHtml, /size-control-xs[^"]*max-sm:size-touch/, "Quick palette keys must keep 44x44px mobile hit targets");
  assert.match(openNoTrigHtml, /size-control-sm[^"]*max-sm:size-touch/, "Expanded palette keys must keep 44x44px mobile hit targets");

  console.log("mathPalette tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
