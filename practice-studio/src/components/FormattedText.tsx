"use client";

import React, { useMemo } from "react";
import katex from "katex";
import { BookOpen } from "lucide-react";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { parseFormattedText, type ProseBlock } from "@/lib/formattedTextBlocks";
import { cn } from "@/lib/cn";
import { MATH_TOKEN, isMathSegment, unescapeDollar, wrapBareWordsInLatex } from "@/lib/mathText";

const CODE_LANGUAGE_LABELS: Record<string, string> = {
  js: "JavaScript", javascript: "JavaScript", jsx: "JSX", mjs: "JavaScript", cjs: "JavaScript",
  ts: "TypeScript", typescript: "TypeScript", tsx: "TSX",
  py: "Python", python: "Python", json: "JSON", bash: "Shell", sh: "Shell", shell: "Shell", zsh: "Shell",
  sql: "SQL", html: "HTML", css: "CSS", md: "Markdown", markdown: "Markdown", text: "Text", txt: "Text",
};

/** Header label for a fenced code block: its language, or "Code" when the fence has none. */
export function codeLanguageLabel(lang: string | null | undefined): string {
  if (!lang) return "Code";
  return CODE_LANGUAGE_LABELS[lang.toLowerCase()] ?? lang;
}

const TERMINAL_LANGUAGES = new Set(["terminal", "console", "shell-session"]);

function parseFenceInfo(info: string) {
  const firstWord = info.split(/\s+/, 1)[0];
  const lang = firstWord && !firstWord.startsWith("{") && !firstWord.includes("=") ? firstWord : null;
  let title: string | undefined;
  const highlightedLines: Array<readonly [number, number]> = [];
  // Consume quoted values and brace groups whole, including in unknown options.
  const tokens = info.slice(lang?.length ?? 0).match(/(?:[^\s"{]+|"(?:\\.|[^"\\])*(?:"|\\?$)|\{[^}]*\}?)+/g) ?? [];
  for (const token of tokens) {
    const titleMatch = /^title="((?:\\.|[^"\\])*)"$/.exec(token);
    if (titleMatch) {
      title = titleMatch[1].replace(/\\(["\\])/g, "$1").trim() || title;
      continue;
    }

    const rangeMatch = /^\{\s*(\d+(?:\s*-\s*\d+)?(?:\s*,\s*\d+(?:\s*-\s*\d+)?)*)\s*\}$/.exec(token);
    if (!rangeMatch) continue;
    for (const entry of rangeMatch[1].split(",")) {
      const [first, last = first] = entry.split("-").map(Number);
      if (first > 0 && first <= last && Number.isSafeInteger(last)) {
        highlightedLines.push([first, last]);
      }
    }
  }
  return { lang, title, highlightedLines };
}

interface FormattedTextProps {
  text: string;
  className?: string;
  density?: "studio" | "compact";
  block?: boolean;
}

const INLINE_TOKEN = new RegExp(
  String.raw`(${MATH_TOKEN}|\*\*[^*]+\*\*|` +
    "`[^`]+`" +
    String.raw`|\[\[[\w-]+\]\]|(?<=^|[\s(,;])'[\w$][\w$.():\s,\-=><\[\]]*?'(?=[\s),;.:!?]|$))`,
  "g"
);
const HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"] as const;

function renderMath(latex: string, displayMode: boolean) {
  const tex = wrapBareWordsInLatex(latex);
  try {
    const html = katex.renderToString(tex, { displayMode, throwOnError: false });
    return displayMode ? (
      <div className="typeset-math" dangerouslySetInnerHTML={{ __html: html }} />
    ) : (
      <span className="inline-math" dangerouslySetInnerHTML={{ __html: html }} />
    );
  } catch {
    return <code className="inline-code">{tex}</code>;
  }
}

function renderInline(text: string): React.ReactNode {
  return text.split(INLINE_TOKEN).filter(Boolean).map((token, index) => {
    let content: React.ReactNode;
    if (isMathSegment(token)) {
      content = renderMath(token.slice(1, -1), false);
    } else if (token.startsWith("**") && token.endsWith("**") && token.length >= 4) {
      content = <strong>{renderInline(token.slice(2, -2))}</strong>;
    } else if (/^(`.+`|'.+')$/.test(token)) {
      content = <code className="inline-code">{token.slice(1, -1)}</code>;
    } else if (/^\[\[[\w-]+\]\]$/.test(token)) {
      const id = token.slice(2, -2);
      const label = id.startsWith("CON-") ? id.slice(4).replace(/-/g, " ") : id;
      content = (
        <span
          className="inline-flex items-center gap-space-1 px-space-1_5 py-space-0_5 rounded text-xs font-normal bg-surface-hover text-foreground-control border border-border-control align-baseline"
          title={`Concept Vault: ${id}`}
        >
          <BookOpen className="size-space-3 shrink-0 opacity-soft" />
          <span>{label}</span>
        </span>
      );
    } else {
      content = unescapeDollar(token);
    }
    return <React.Fragment key={index}>{content}</React.Fragment>;
  });
}

function renderBlocks(blocks: ProseBlock[]): React.ReactNode {
  return blocks.map((block, index) => {
    let content: React.ReactNode;
    switch (block.kind) {
      case "paragraph":
        content = (
          <p>
            {block.lines.map((line, lineIndex) => (
              <React.Fragment key={lineIndex}>
                {lineIndex > 0 && <br />}
                {renderInline(line)}
              </React.Fragment>
            ))}
          </p>
        );
        break;
      case "heading": {
        const Heading = HEADINGS[block.level - 1];
        content = <Heading>{renderInline(block.text)}</Heading>;
        break;
      }
      case "list": {
        const List = block.ordered ? "ol" : "ul";
        content = (
          <List start={block.items[0].number}>
            {block.items.map((item, itemIndex) => (
              <li key={itemIndex} value={itemIndex > 0 ? item.number : undefined}>
                {renderBlocks(item.blocks)}
              </li>
            ))}
          </List>
        );
        break;
      }
      case "table":
        content = (
          <div className="typeset-scroll" tabIndex={0} role="region" aria-label="Table">
            <table>
              <thead>
                <tr>
                  {block.cells[0].map((cell, column) => (
                    <th key={column} scope="col" align={block.align[column]}>{renderInline(cell)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {block.cells.slice(1).map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {row.map((cell, column) => (
                      <td key={column} align={block.align[column]}>{renderInline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        break;
      case "quote":
        content = <blockquote>{renderBlocks(block.blocks)}</blockquote>;
        break;
      case "rule":
        content = <hr />;
        break;
      case "math":
        content = renderMath(block.latex, true);
        break;
      case "code": {
        const { lang, title, highlightedLines } = parseFenceInfo(block.info);
        content = lang && TERMINAL_LANGUAGES.has(lang.toLowerCase()) ? (
          <CodeBlock variant="terminal" code={block.code} title={title} />
        ) : (
          <CodeBlock
            variant="full-file"
            code={block.code}
            language={lang}
            filename={title ?? codeLanguageLabel(lang)}
            highlightedLines={highlightedLines}
            preserveWhitespace
          />
        );
        break;
      }
    }
    return <React.Fragment key={index}>{content}</React.Fragment>;
  });
}

export const FormattedText: React.FC<FormattedTextProps> = ({
  text,
  className,
  density = "studio",
  block = false,
}) => {
  const blocks = useMemo(() => parseFormattedText(text), [text]);
  const first = blocks[0];

  // Keep one-line labels phrasing content so they can sit inside controls and figure labels.
  if (!block && (!first || (blocks.length === 1 && first.kind === "paragraph" && first.lines.length === 1))) {
    return <span className={cn("typeset", className)}>{renderInline(text)}</span>;
  }

  return (
    <div className={cn("typeset", density === "compact" ? "typeset-compact" : "typeset-studio", className)}>
      {renderBlocks(blocks)}
    </div>
  );
};
