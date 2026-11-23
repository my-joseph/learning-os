/** FormattedText renders Markdown headings and Shiki-highlighted fenced code blocks. */
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { FormattedText } from "../src/components/FormattedText";
import { preloadShiki } from "../src/lib/shiki";

async function main() {
  // 1. Markdown headings render as bold labels, never raw "###"
  // Learner 2026-11-19: list bullets use the same small indigo dot as the Visible tests list.
  const bulletHtml = renderToStaticMarkup(<FormattedText text={"Requirements:\n- Return a fresh array\n- Keep order"} />);
  assert.match(bulletHtml, /w-1\.5 h-1\.5 rounded-full bg-indigo-600 dark:bg-indigo-400/);
  assert.doesNotMatch(bulletHtml, /•/);

  // Learner 2026-11-19: three list kinds picked from the heading above the list.
  const kindsHtml = renderToStaticMarkup(
    <FormattedText
      text={[
        "**Observed Symptoms:**",
        "- Clients share defaults",
        "**Requirements:**",
        "- Return a fresh array",
        "**Return Contract:**",
        "- Return string[]",
        "Something else",
        "- plain note",
      ].join("\n")}
    />
  );
  const kinds = [...kindsHtml.matchAll(/data-list-kind="(\w+)"/g)].map((m) => m[1]);
  assert.deepEqual(kinds, ["info", "task", "limit", "info"]);
  assert.match(kindsHtml, /border-indigo-600 dark:border-indigo-400/);
  assert.match(kindsHtml, /bg-zinc-400 dark:bg-zinc-500/);

  const headingHtml = renderToStaticMarkup(
    <FormattedText text={"### Requirements\n- keep order\n#### Return contract"} />
  );
  assert.doesNotMatch(headingHtml, /###/, "raw ### must not be shown");
  assert.match(headingHtml, /font-semibold[^>]*>Requirements</);
  assert.match(headingHtml, /font-semibold[^>]*>Return contract</);
  assert.match(headingHtml, /keep order/);

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
    assert.match(html, /bg-surface-panel border border-zinc-200 dark:border-zinc-800 rounded-xl/);
  }

  // 3. Unknown or missing fence language falls back to plain text inside the same frame
  const unknownHtml = renderToStaticMarkup(
    <FormattedText text={"```rust\nfn main() {}\n```"} />
  );
  assert.doesNotMatch(unknownHtml, /class="shiki-token"/);
  assert.match(unknownHtml, /<pre[^>]*rounded-xl[^>]*><code>fn main\(\) \{\}<\/code><\/pre>/);

  const plainHtml = renderToStaticMarkup(
    <FormattedText text={"```\nplain output line\n```"} />
  );
  assert.doesNotMatch(plainHtml, /class="shiki-token"/);
  assert.match(plainHtml, /<pre[^>]*rounded-xl[^>]*><code>plain output line<\/code><\/pre>/);

  console.log("formattedText tests passed");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
