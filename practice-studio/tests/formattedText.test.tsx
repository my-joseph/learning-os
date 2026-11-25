/** FormattedText renders Markdown headings and Shiki-highlighted fenced code blocks. */
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FormattedText } from "../src/components/FormattedText";
import { preloadShiki } from "../src/lib/shiki";

async function main() {
  // 1. Studio prose preserves semantic structure and escapes plain text.
  const proseHtml = renderToStaticMarkup(
    <FormattedText text={[
      "## API reference",
      "### formatBadge",
      "Use `formatBadge` to format a label.",
      "",
      "**Requirements:**",
      "- Accept a `name`",
      "  - Trim whitespace",
      "- Keep the input unchanged",
      "",
      "Return Contract:",
      "3. Return a label",
      "4. Return an empty string when needed",
      "",
      "| Field | Type |",
      "| --- | :---: |",
      "| `status` | pending\\|active |",
      "",
      "> Use short labels.",
      "",
      "---",
      "",
      "Inline math $x^2$ stays with the sentence.",
      "$$",
      String.raw`\frac{1}{2}`,
      "$$",
      "",
      "<script>untrusted</script>",
    ].join("\n")} />
  );
  assert.match(proseHtml, /<div class="typeset typeset-studio">/);
  assert.match(proseHtml, /<h2>API reference<\/h2><h3>formatBadge<\/h3><p>Use <code class="inline-code">formatBadge<\/code>/);
  assert.match(proseHtml, /<h4>Requirements:<\/h4><ul><li>.*<ul><li><p>Trim whitespace<\/p><\/li><\/ul><\/li>/);
  assert.match(proseHtml, /<h4>Return Contract:<\/h4><ol start="3">.*<li value="4">/);
  assert.match(proseHtml, /<th scope="col" align="center">Type<\/th>.*<td align="center">pending\|active<\/td>/);
  assert.match(proseHtml, /<blockquote><p>Use short labels\.<\/p><\/blockquote><hr\/>/);
  assert.match(proseHtml, /class="inline-math"><span class="katex"/);
  assert.match(proseHtml, /class="typeset-math"><span class="katex-display"/);
  assert.match(proseHtml, /&lt;script&gt;untrusted&lt;\/script&gt;/);

  assert.match(
    renderToStaticMarkup(<FormattedText text="One `token`" />),
    /^<span class="typeset">One <code class="inline-code">token<\/code><\/span>$/
  );
  assert.match(
    renderToStaticMarkup(<FormattedText text="One paragraph." block />),
    /<div class="typeset typeset-studio"><p>One paragraph\.<\/p><\/div>/
  );
  assert.match(
    renderToStaticMarkup(<FormattedText text={"A note\n\n- Details"} density="compact" />),
    /^<div class="typeset typeset-compact">/
  );

  // 2. Fenced code blocks highlight supported languages with dual-theme Shiki tokens
  await preloadShiki();

  const supportedSamples: Array<{ fence: string; code: string; token: string }> = [
    { fence: "js", code: "const n = 42;", token: "const" },
    { fence: "ts", code: "type Pair = [number, string];", token: "type" },
    { fence: "tsx", code: "const el = <button>Go</button>;", token: "const" },
    { fence: "python", code: "def greet(name):\n    return name", token: "def" },
    { fence: "sql", code: "SELECT id FROM users WHERE active = 1;", token: "SELECT" },
    { fence: "json", code: '{"ok": true}', token: "true" },
  ];

  for (const sample of supportedSamples) {
    const md = `Trace this:\n\`\`\`${sample.fence}\n${sample.code}\n\`\`\``;
    const html = renderToStaticMarkup(<FormattedText text={md} />);
    assert.match(
      html,
      new RegExp(
        `<span class="shiki-token" style="--shiki-light:#[^;]+;--shiki-dark:#[^"]+">${sample.token}<\\/span>`
      ),
      `expected dual-theme Shiki highlighting for \`\`\`${sample.fence}`
    );
    assert.match(html, /data-code-variant="full-file">.*title="[^"]+">[^<]+<.*<span>Copy<\/span>.*<pre[^>]*data-numbered="true"[^>]*dir="ltr"[^>]*tabindex="0"/s);
  }

  // 3. Unknown or missing fence language falls back to plain text inside the same frame
  const unknownHtml = renderToStaticMarkup(
    <FormattedText text={"```rust\nfn main() {}\n```"} />
  );
  assert.doesNotMatch(unknownHtml, /class="shiki-token"/);
  assert.match(unknownHtml, /title="rust">rust</);
  assert.match(unknownHtml, /data-slot="code-block-line-content">fn main\(\) \{\}<\/span>/);

  const plainHtml = renderToStaticMarkup(
    <FormattedText text={"```\nplain output line\n```"} />
  );
  assert.doesNotMatch(plainHtml, /class="shiki-token"/);
  assert.match(plainHtml, /title="Code">Code</);
  assert.match(plainHtml, /data-slot="code-block-line-content">plain output line<\/span>/);

  const delimiter = "```";
  const fence = (info: string, code: string) =>
    renderToStaticMarkup(<FormattedText text={[delimiter + info, code, delimiter].join("\n")} />);
  const highlighted = (html: string) =>
    Array.from(html.matchAll(/data-variant="highlighted"[^>]*><span[^>]*>(\d+)<\/span>/g), ([, line]) => Number(line));
  const numbered = Array.from({ length: 9 }, (_, i) => i === 0 ? "" : "line " + (i + 1)).join("\n");
  const metaHtml = fence('text title="src/app config.js" unknown="{5}" {3, 7-9} {0, 99}', numbered);
  assert.match(metaHtml, /title="src\/app config\.js">src\/app config\.js</);
  assert.deepEqual(highlighted(metaHtml), [3, 7, 8, 9]);
  assert.deepEqual(highlighted(fence("text {4-2} {-1} {2,wrong} {9007199254740992}", numbered)), []);
  assert.deepEqual(highlighted(fence('text {2} title="unclosed {3}', numbered)), [2]);
  assert.match(fence('text title="& <img>"', "sample"), /title="&amp; &lt;img&gt;"/);

  for (const alias of ["terminal", "console", "shell-session"]) {
    const html = fence(alias, "$ npm run start\n\n<script>log</script>");
    assert.match(html, /data-code-variant="terminal"/);
    assert.match(html, /title="Terminal">Terminal</);
    assert.match(html, /<span class="text-muted">\$ <\/span>npm run start\n\n&lt;script&gt;log&lt;\/script&gt;/);
    assert.doesNotMatch(html, /data-numbered|data-code-block-line|shiki-token/);
  }
  assert.match(fence('terminal title="node app.js"', "Ready"), /title="node app\.js">node app\.js</);

  console.log("formattedText tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
