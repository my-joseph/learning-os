import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { MathPalette, MathPaletteView } from "../src/components/math/MathPalette";
import { MathWorkspace } from "../src/components/math/MathWorkspace";
import {
  getMathPaletteSections,
  insertLatexIntoMathField,
  preloadPaletteRenderer,
  QUICK_PALETTE_KEYS,
  renderPaletteKeyMarkup,
  type MathFieldInsertTarget,
} from "../src/lib/mathPalette";
import type { Problem } from "../src/types/drill";

async function main() {
  const loaded = await preloadPaletteRenderer();
  assert.ok(loaded, "Expected MathLive static renderer to preload");

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
      onClosePanel={noop}
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
      onClosePanel={noop}
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
      onClosePanel={noop}
      onInsertLatex={noop}
    />
  );

  assert.match(openNoTrigHtml, /role="region" aria-label="Math symbol palette"/);
  assert.match(openNoTrigHtml, /aria-label="Close math palette"/);
  assert.match(openNoTrigHtml, />BASIC</);
  assert.match(openNoTrigHtml, />FUNCTIONS</);
  assert.match(openNoTrigHtml, />SYMBOLS</);
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
      onClosePanel={noop}
      onInsertLatex={noop}
    />
  );

  assert.match(openWithTrigHtml, /aria-label="Sine"/);
  assert.match(openWithTrigHtml, /aria-label="Cosine"/);
  assert.match(openWithTrigHtml, /aria-label="Tangent"/);
  assert.match(openWithTrigHtml, /aria-label="Inverse sine \(arcsin\)"/);
  assert.match(openWithTrigHtml, /aria-label="Inverse cosine \(arccos\)"/);
  assert.match(openWithTrigHtml, /aria-label="Inverse tangent \(arctan\)"/);

  // Every template key renders valid MathLive static markup with placeholder square boxes and no errors
  for (const section of getMathPaletteSections({ trig: true })) {
    for (const key of section.keys) {
      const html = renderPaletteKeyMarkup(key.displayLatex);
      assert.ok(html.includes("ML__latex"), `Key ${key.id} should render ML__latex markup`);
      assert.ok(!html.includes("ML__error"), `Key ${key.id} should render without ML__error`);
      if (key.displayLatex.includes("\\placeholder{}")) {
        assert.ok(
          html.includes("□"),
          `Template key ${key.id} should render visible placeholder square(s)`
        );
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 3. Clicking a key calls insert with the right LaTeX (mock field)
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
    onClosePanel: noop,
    onInsertLatex: (latex) => {
      insertLatexIntoMathField(mockField, latex);
    },
    rendererReady: true,
  });

  const fracButtons = findElements(
    tree,
    (el) => el.type === "button" && el.props["aria-label"] === "Fraction"
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
    (el) => el.type === "button" && el.props["aria-label"] === "Logarithm with base"
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
    (el) => el.type === "button" && el.props["aria-label"] === "Inverse sine (arcsin)"
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
  // 4. Floating virtual keyboard is disabled everywhere (policy manual) & no purple accent
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
    `${mathLiveInputSource}\n${mathPaletteSource}\n${mathLiveCss}`,
    /\bpurple-\d+/,
    "Palette and math input must use zinc neutrals + indigo accent, never purple"
  );

  // ---------------------------------------------------------------------------
  // 5. MathWorkspace integration: choice questions unaffected, math gets toolbar
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
  assert.doesNotMatch(choiceHtml, /Answer input mode/);
  assert.doesNotMatch(choiceHtml, /Quick math templates/);

  console.log("mathPalette tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
