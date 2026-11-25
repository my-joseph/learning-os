/**
 * Unit and render tests for Shiki syntax highlighting, CodeBlock variants,
 * dual-theme CSS variables, unknown-language fallback, and /math isolation.
 * Run: npx tsx tests/shiki.test.tsx (from practice-studio/)
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import React, { act } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CodeBlock } from "../src/components/ui/CodeBlock";
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
    <CodeBlock
      variant="full-file"
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

  // 4. Preload Shiki and verify all supported grammars tokenize with dual-theme CSS vars
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

  // 5. Highlighted full-file render for a TS snippet contains token spans with colours
  const tsHtml = renderToStaticMarkup(
    <CodeBlock
      variant="full-file"
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
  // Line numbers, filename, and Copy remain available. Numbering is visual.
  assert.match(tsHtml, /data-numbered="true"/);
  assert.match(tsHtml, /aria-hidden="true"[^>]*>1<\/span>/);
  assert.match(tsHtml, /aria-hidden="true"[^>]*>4<\/span>/);
  assert.match(tsHtml, /data-slot="code-block-title"[^>]*>findItem\.ts<\/div>/);
  assert.doesNotMatch(tsHtml, /role="button"/, "plain lines do not become controls");
  assert.match(tsHtml, />Copy<\/span>/);

  // 6. Unknown language falls back to plain text even when Shiki is warmed
  const unknownHtml = renderToStaticMarkup(
    <CodeBlock
      variant="full-file"
      code={"fn main() {\n  println!(\"hi\");\n}"}
      language="unknown"
      filename="main.rs"
    />
  );
  assert.doesNotMatch(unknownHtml, /class="shiki-token"/);
  assert.match(unknownHtml, /fn main\(\) \{/);

  // 7. Selectable lines keep aria attributes and click/keyboard handlers
  const selectableHtml = renderToStaticMarkup(
    <CodeBlock
      variant="full-file"
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

  const { window } = new JSDOM("<div id='root'></div>");
  Object.assign(globalThis, { window, document: window.document, IS_REACT_ACT_ENVIRONMENT: true });
  const { createRoot } = await import("react-dom/client");
  const root = createRoot(window.document.getElementById("root")!);
  try {
    const selectedCalls: number[] = [];
    await act(() => root.render(
      <CodeBlock
        variant="full-file"
        code={tsSnippet}
        language="typescript"
        filename="buggy.ts"
        selectableLines
        onSelectLine={(line) => selectedCalls.push(line)}
      />
    ));
    const row = window.document.querySelector<HTMLElement>('[aria-label="Select line 3"]');
    assert.ok(row);
    row.click();
    for (const key of ["Enter", " "]) {
      const event = new window.KeyboardEvent("keydown", { key, bubbles: true, cancelable: true });
      assert.equal(row.dispatchEvent(event), false);
    }
    assert.deepEqual(selectedCalls, [3, 3, 3]);
  } finally {
    await act(() => root.unmount());
    window.close();
    for (const key of ["window", "document", "IS_REACT_ACT_ENVIRONMENT"]) {
      Reflect.deleteProperty(globalThis, key);
    }
  }

  // 8. The inline example renders JS tokens with dual-theme colors
  const inlineHtml = renderToStaticMarkup(
    <CodeBlock variant="inline-example" input="nums = [1, 3], target = 5" output="5" language="javascript" />
  );
  assert.match(
    inlineHtml,
    /<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">=<\/span>/
  );
  assert.match(
    inlineHtml,
    /<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">5<\/span>/
  );

  // 9. Shared code surfaces never load the Shiki runtime on Math routes.
  const codeBlockSrc = readFileSync("src/components/ui/CodeBlock.tsx", "utf8");
  assert.doesNotMatch(codeBlockSrc, /@\/lib\/shiki["']/);
  assert.doesNotMatch(codeBlockSrc, /tokenizeLine|TOKEN_COLOR_MAP|vscode-token-/);
  const globalsCss = readFileSync("src/app/globals.css", "utf8");
  assert.doesNotMatch(globalsCss, /vscode-token-/);
  assert.match(globalsCss, /\.shiki-token/);

  const mathWorkspaceSrc = readFileSync("src/components/math/MathWorkspace.tsx", "utf8");
  assert.doesNotMatch(mathWorkspaceSrc, /CodeBlock|shiki/);
  const mathPageSrc = readFileSync("src/app/math/[drillId]/page.tsx", "utf8");
  assert.doesNotMatch(mathPageSrc, /CodeBlock|shiki|CodeStudioClient|CodeDashboard/);
  const mathClientSrc = readFileSync("src/components/shell/MathStudioClient.tsx", "utf8");
  assert.doesNotMatch(mathClientSrc, /from\s+["'][^"']*(?:CodeDashboard|CodeBlock|shiki)[^"']*["']/);
  const codeClientSrc = readFileSync("src/components/shell/CodeStudioClient.tsx", "utf8");
  assert.doesNotMatch(codeClientSrc, /from\s+["'][^"']*(?:MathWorkspace|MathLiveInput|Interactive3DCylinder)[^"']*["']/);
  const formattedTextSrc = readFileSync("src/components/FormattedText.tsx", "utf8");
  assert.doesNotMatch(formattedTextSrc, /@\/lib\/shiki["']/);

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
