/**
 * Unit and render tests for Shiki syntax highlighting, VSCodeBlock features,
 * dual-theme CSS variables, unknown-language fallback, and /math isolation.
 * Run: npx tsx tests/shiki.test.tsx (from practice-studio/)
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { VSCodeBlock, getSelectableLineRowProps } from "../src/components/VSCodeBlock";
import { HighlightedCode } from "../src/components/HighlightedCode";
import {
  SUPPORTED_SHIKI_LANGS,
  getExtensionForLanguage,
  highlightCode,
  highlightTokensSync,
  inferShikiLanguageFromFilename,
  normalizeShikiLanguage,
  preloadShiki,
} from "../src/lib/shiki";

async function main() {
  // 1. Language normalization & filename inference
  assert.equal(normalizeShikiLanguage("javascript"), "javascript");
  assert.equal(normalizeShikiLanguage("JS"), "javascript");
  assert.equal(normalizeShikiLanguage("typescript"), "typescript");
  assert.equal(normalizeShikiLanguage("ts"), "typescript");
  assert.equal(normalizeShikiLanguage("tsx"), "tsx");
  assert.equal(normalizeShikiLanguage("jsx"), "jsx");
  assert.equal(normalizeShikiLanguage("json"), "json");
  assert.equal(normalizeShikiLanguage("python"), "python");
  assert.equal(normalizeShikiLanguage("py"), "python");
  assert.equal(normalizeShikiLanguage("bash"), "bash");
  assert.equal(normalizeShikiLanguage("sh"), "bash");
  assert.equal(normalizeShikiLanguage("unknown"), null);
  assert.equal(normalizeShikiLanguage("rust"), null);
  assert.equal(normalizeShikiLanguage(""), null);
  assert.equal(normalizeShikiLanguage(null), null);

  assert.equal(inferShikiLanguageFromFilename("solution.ts"), "typescript");
  assert.equal(inferShikiLanguageFromFilename("App.tsx"), "tsx");
  assert.equal(inferShikiLanguageFromFilename("Card.jsx"), "jsx");
  assert.equal(inferShikiLanguageFromFilename("config.json"), "json");
  assert.equal(inferShikiLanguageFromFilename("main.py"), "python");
  assert.equal(inferShikiLanguageFromFilename("run.sh"), "bash");
  assert.equal(inferShikiLanguageFromFilename("README.md"), null);

  assert.equal(getExtensionForLanguage("typescript"), "ts");
  assert.equal(getExtensionForLanguage("python"), "py");
  assert.equal(getExtensionForLanguage("bash"), "sh");
  assert.equal(getExtensionForLanguage("unknown"), "js");

  // 2. Non-blocking first paint: cold sync lookup returns null, plain text renders immediately
  const tsSnippet = [
    "type Item = { id: number; name: string };",
    "export function findItem(items: Item[], id: number): Item | undefined {",
    "  return items.find((item) => item.id === id);",
    "}",
  ].join("\n");

  assert.equal(highlightTokensSync(tsSnippet, "typescript"), null);
  const coldHtml = renderToStaticMarkup(
    <VSCodeBlock
      code={tsSnippet}
      language="typescript"
      filename="findItem.ts"
      selectableLines={true}
      selectedLine={2}
    />
  );
  assert.doesNotMatch(coldHtml, /class="shiki-token"/);
  assert.match(coldHtml, /findItem\.ts/);
  assert.match(coldHtml, /Selected: Line 2/);
  assert.match(coldHtml, /export function findItem/);

  // 3. Unknown language never triggers highlighting and falls back to plain text
  assert.equal(await highlightCode("fn main() {}", "rust"), null);

  // 4. Preload Shiki and verify all 7 supported grammars tokenize with dual-theme CSS vars
  await preloadShiki();
  for (const lang of SUPPORTED_SHIKI_LANGS) {
    const tokens = await highlightCode("const x = 1;", lang);
    assert.ok(tokens && tokens.length === 1 && tokens[0].length > 0, `expected tokens for ${lang}`);
    assert.ok(
      tokens[0].some(
        (t) => Boolean(t.htmlStyle?.["--shiki-light"]) && Boolean(t.htmlStyle?.["--shiki-dark"])
      ),
      `expected dual-theme CSS vars for ${lang}`
    );
  }

  // 5. Highlighted VSCodeBlock render for a TS snippet contains token spans with colours
  const tsHtml = renderToStaticMarkup(
    <VSCodeBlock
      code={tsSnippet}
      language="typescript"
      filename="findItem.ts"
    />
  );
  assert.match(
    tsHtml,
    /<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">export<\/span>/
  );
  assert.match(
    tsHtml,
    /<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">function<\/span>/
  );
  // Line numbers, filename header, breadcrumbs, and Copy button preserved
  assert.match(tsHtml, />1<\/td>/);
  assert.match(tsHtml, />4<\/td>/);
  assert.match(tsHtml, />TS<\/span>/);
  assert.match(tsHtml, />findItem\.ts<\/span>/);
  assert.match(tsHtml, />Copy<\/span>/);

  // 6. Unknown language falls back to plain text even when Shiki is warmed
  const unknownHtml = renderToStaticMarkup(
    <VSCodeBlock
      code={"fn main() {\n  println!(\"hi\");\n}"}
      language="unknown"
      filename="main.rs"
    />
  );
  assert.doesNotMatch(unknownHtml, /class="shiki-token"/);
  assert.match(unknownHtml, /fn main\(\) \{/);
  assert.match(unknownHtml, />TXT<\/span>/);

  // 7. Selectable lines keep aria attributes and click/keyboard handlers
  const selectableHtml = renderToStaticMarkup(
    <VSCodeBlock
      code={tsSnippet}
      language="typescript"
      filename="buggy.ts"
      selectableLines={true}
      selectedLine={3}
    />
  );
  assert.match(selectableHtml, /Click defective line in code|Selected: Line 3/);
  assert.match(selectableHtml, /role="button"/);
  assert.match(selectableHtml, /tabindex="0"/);
  assert.match(selectableHtml, /aria-pressed="false"[^>]*aria-label="Select line 1"/);
  assert.match(selectableHtml, /aria-pressed="true"[^>]*aria-label="Select line 3"/);

  const selectedCalls: number[] = [];
  const row3Props = getSelectableLineRowProps(3, true, false, (line) => selectedCalls.push(line));
  assert.equal(row3Props.role, "button");
  assert.equal(row3Props["aria-pressed"], false);
  assert.equal(row3Props["aria-label"], "Select line 3");
  row3Props.onClick?.({} as React.MouseEvent<HTMLTableRowElement>);
  assert.deepEqual(selectedCalls, [3]);

  let prevented = false;
  row3Props.onKeyDown?.({
    key: "Enter",
    preventDefault: () => {
      prevented = true;
    },
  } as unknown as React.KeyboardEvent<HTMLTableRowElement>);
  assert.equal(prevented, true);
  assert.deepEqual(selectedCalls, [3, 3]);

  const nonSelectableProps = getSelectableLineRowProps(3, false, false, (line) =>
    selectedCalls.push(line)
  );
  assert.equal(nonSelectableProps.role, undefined);
  assert.equal(nonSelectableProps.onClick, undefined);
  assert.deepEqual(selectedCalls, [3, 3]);

  // 8. HighlightedCode inline component renders JS tokens with dual-theme colors
  const inlineHtml = renderToStaticMarkup(
    <HighlightedCode code="nums = [1, 3], target = 5" language="javascript" />
  );
  assert.match(
    inlineHtml,
    /<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">=<\/span>/
  );
  assert.match(
    inlineHtml,
    /<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">5<\/span>/
  );

  // 9. Old regex tokenizer and CSS overrides are removed; /math never imports shiki or VSCodeBlock
  const vsCodeBlockSrc = readFileSync("src/components/VSCodeBlock.tsx", "utf8");
  assert.doesNotMatch(vsCodeBlockSrc, /tokenizeLine|TOKEN_COLOR_MAP|vscode-token-/);
  const globalsCss = readFileSync("src/app/globals.css", "utf8");
  assert.doesNotMatch(globalsCss, /vscode-token-/);
  assert.match(globalsCss, /\.shiki-token/);

  const mathWorkspaceSrc = readFileSync("src/components/math/MathWorkspace.tsx", "utf8");
  assert.doesNotMatch(mathWorkspaceSrc, /VSCodeBlock|HighlightedCode|shiki/);
  const mathPageSrc = readFileSync("src/app/math/[drillId]/page.tsx", "utf8");
  assert.doesNotMatch(mathPageSrc, /VSCodeBlock|HighlightedCode|shiki/);

  // 10. shiki.ts uses fine-grained shiki/core + JS regex engine (no WASM / full bundle)
  const shikiLibSrc = readFileSync("src/lib/shiki.ts", "utf8");
  assert.match(shikiLibSrc, /shiki\/core/);
  assert.match(shikiLibSrc, /shiki\/engine\/javascript/);
  assert.doesNotMatch(shikiLibSrc, /oniguruma|wasm|bundle\/full|bundle\/web/);

  console.log("shiki tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
