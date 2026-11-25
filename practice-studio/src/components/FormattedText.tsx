"use client";

import React, { useMemo } from "react";
import katex from "katex";
import { BookOpen } from "lucide-react";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { ListDot, listKindForHeading } from "@/components/ui/ListDot";
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
}

export const FormattedText: React.FC<FormattedTextProps> = ({
  text,
  className = "",
}) => {
  // Regex to split inline tokens: math ($...$), bold (**...**), backtick code (`...`), concept vault token ([[...]]), or quoted identifier ('...')
  const inlineRegex = useMemo(
    () =>
      new RegExp(
        String.raw`(${MATH_TOKEN}|\*\*[^*]+\*\*|` +
          "`[^`]+`" +
          String.raw`|\[\[[\w-]+\]\]|(?<=^|[\s(,;])'[\w$][\w$.():\s,\-=><\[\]]*?'(?=[\s),;.:!?]|$))`,
        "g"
      ),
    []
  );

  const blocks = useMemo(() => {
    if (!text) return [];
    const rawLines = text.split("\n");
    const out: Array<
      | { kind: "line"; line: string; lineIdx: number }
      | { kind: "code"; code: string; info: ReturnType<typeof parseFenceInfo>; lineIdx: number }
    > = [];
    let i = 0;
    while (i < rawLines.length) {
      const current = rawLines[i];
      const trimmedCurrent = current.trim();
      if (trimmedCurrent.startsWith("```")) {
        const startIdx = i;
        const fenceInfo = trimmedCurrent.slice(3).trim();
        const info = parseFenceInfo(fenceInfo);
        i++;
        const codeLines: string[] = [];
        while (i < rawLines.length && !rawLines[i].trim().startsWith("```")) {
          codeLines.push(rawLines[i]);
          i++;
        }
        if (i < rawLines.length && rawLines[i].trim().startsWith("```")) {
          i++;
        }
        out.push({ kind: "code", code: codeLines.join("\n"), info, lineIdx: startIdx });
      } else {
        out.push({ kind: "line", line: current, lineIdx: i });
        i++;
      }
    }
    return out;
  }, [text]);

  const renderInline = (content: string) => {
    if (!content) return null;
    const segments = content.split(inlineRegex).filter(Boolean);

    return segments.map((seg, idx) => {
      // 1. LaTeX Math: $...$
      if (isMathSegment(seg)) {
        const tex = wrapBareWordsInLatex(seg.slice(1, -1));
        try {
          const html = katex.renderToString(tex, {
            displayMode: false,
            throwOnError: false,
          });
          return (
            <span
              key={idx}
              dangerouslySetInnerHTML={{ __html: html }}
              className="inline-math"
            />
          );
        } catch {
          return (
            <code
              key={idx}
              className="font-mono text-zinc-800 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 px-1.5 py-0.5 rounded text-[0.88em]"
            >
              {tex}
            </code>
          );
        }
      }

      // 2. Markdown Bold: **...**
      if (seg.startsWith("**") && seg.endsWith("**") && seg.length >= 4) {
        const boldText = seg.slice(2, -2);
        return (
          <strong key={idx} className="font-semibold text-zinc-900 dark:text-zinc-100">
            {boldText}
          </strong>
        );
      }

      // 3. Markdown Backtick Code: `...`
      if (seg.startsWith("`") && seg.endsWith("`") && seg.length >= 2) {
        const code = seg.slice(1, -1);
        return (
          <code
            key={idx}
            className="font-mono text-zinc-800 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 px-1.5 py-0.5 rounded text-[0.88em]"
          >
            {code}
          </code>
        );
      }

      // 4. Concept Vault Token: [[KEY]]
      if (seg.startsWith("[[") && seg.endsWith("]]") && seg.length >= 4) {
        const key = seg.slice(2, -2);
        const displayLabel = key.startsWith("CON-")
          ? key.replace("CON-", "").replace(/-/g, " ")
          : key;
        return (
          <span
            key={idx}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.85em] font-normal bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 align-baseline"
            title={`Concept Vault: ${key}`}
          >
            <BookOpen className="w-3 h-3 shrink-0 opacity-70" />
            <span>{displayLabel}</span>
          </span>
        );
      }

      // 5. Quoted Code identifier: '...'
      if (seg.startsWith("'") && seg.endsWith("'") && seg.length > 2) {
        const code = seg.slice(1, -1);
        return (
          <code
            key={idx}
            className="font-mono text-zinc-800 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 px-1.5 py-0.5 rounded text-[0.88em]"
          >
            {code}
          </code>
        );
      }

      // Plain text (`\$` is a literal dollar sign)
      return <React.Fragment key={idx}>{unescapeDollar(seg)}</React.Fragment>;
    });
  };

  if (blocks.length <= 1 && blocks[0]?.kind !== "code") {
    return <span className={className}>{renderInline(text)}</span>;
  }

  // Each bullet takes its style from the nearest heading-like line above its list
  // ("Requirements:", "**Observed Symptoms:**", "### Return Contract").
  const listKindByLine = new Map<number, ReturnType<typeof listKindForHeading>>();
  {
    let heading: string | null = null;
    for (const block of blocks) {
      if (block.kind !== "line") {
        heading = null;
        continue;
      }
      const t = block.line.trim();
      if (!t) continue;
      if (t.startsWith("- ") || t.startsWith("* ")) {
        listKindByLine.set(block.lineIdx, listKindForHeading(heading));
        continue;
      }
      heading = t.replace(/^#{1,4}\s+/, "").replace(/\*\*/g, "").replace(/:\s*$/, "").trim();
    }
  }

  return (
    <div className={`space-y-1.5 ${className}`}>
      {blocks.map((block) => {
        if (block.kind === "code") {
          const { lang, title, highlightedLines } = block.info;
          if (lang && TERMINAL_LANGUAGES.has(lang.toLowerCase())) {
            return <CodeBlock key={block.lineIdx} variant="terminal" code={block.code} title={title} />;
          }
          return (
            <CodeBlock
              key={block.lineIdx}
              variant="full-file"
              code={block.code}
              language={lang}
              filename={title ?? codeLanguageLabel(lang)}
              highlightedLines={highlightedLines}
              preserveWhitespace
            />
          );
        }

        const { line, lineIdx } = block;
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={lineIdx} className="h-1.5" />;
        }

        const headingMatch = trimmed.match(/^#{1,4}\s+(.+)$/);
        if (headingMatch) {
          // Markdown heading ("### Requirements") renders like the bold section labels used elsewhere.
          return (
            <div
              key={lineIdx}
              className="font-semibold text-zinc-900 dark:text-zinc-100 leading-relaxed pt-1"
            >
              {renderInline(headingMatch[1])}
            </div>
          );
        }

        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const bulletContent = trimmed.slice(2);
          return (
            <div
              key={lineIdx}
              className="flex items-start gap-2 text-zinc-800 dark:text-zinc-200 leading-relaxed pl-2 py-0.5"
            >
              <ListDot kind={listKindByLine.get(lineIdx) ?? "info"} />
              <div className="flex-1">{renderInline(bulletContent)}</div>
            </div>
          );
        }

        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numMatch) {
          const num = numMatch[1];
          const numContent = numMatch[2];
          return (
            <div
              key={lineIdx}
              className="flex items-start gap-2 text-zinc-800 dark:text-zinc-200 leading-relaxed pl-2 py-0.5"
            >
              <span className="font-sans tabular-nums text-zinc-500 dark:text-zinc-400 font-semibold select-none text-xs mt-0.5 shrink-0">
                {num}.
              </span>
              <div className="flex-1">{renderInline(numContent)}</div>
            </div>
          );
        }

        return (
          <div key={lineIdx} className="text-zinc-800 dark:text-zinc-200 leading-relaxed">
            {renderInline(line)}
          </div>
        );
      })}
    </div>
  );
};
