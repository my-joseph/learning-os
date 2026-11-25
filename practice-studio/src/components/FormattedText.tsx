"use client";

import React, { useEffect, useMemo, useState } from "react";
import katex from "katex";
import { BookOpen } from "lucide-react";
import type { ThemedToken } from "shiki/core";
import { ListDot, listKindForHeading } from "@/components/ui/ListDot";
import { MATH_TOKEN, isMathSegment, unescapeDollar, wrapBareWordsInLatex } from "@/lib/mathText";
import { normalizeShikiLanguage, type SupportedShikiLang } from "@/lib/shikiLanguages";
import { getRegisteredShikiHighlighter } from "@/lib/shikiRegistry";
import { renderShikiLineTokens } from "@/lib/shikiTokens";

interface CodeFenceSpanProps {
  code: string;
  language: SupportedShikiLang;
}

const CodeFenceSpan: React.FC<CodeFenceSpanProps> = ({ code, language }) => {
  const lines = useMemo(() => code.split("\n"), [code]);
  const highlighter = getRegisteredShikiHighlighter();
  const syncTokens = useMemo(
    () => (highlighter ? highlighter.highlightTokensSync(code, language) : null),
    [highlighter, code, language]
  );
  const requestKey = `${language}:${code}`;
  const [asyncResult, setAsyncResult] = useState<{
    key: string;
    tokens: ThemedToken[][];
  } | null>(null);

  useEffect(() => {
    if (!highlighter || syncTokens) return;
    let cancelled = false;
    void highlighter.highlightCode(code, language).then((tokens) => {
      if (!cancelled && tokens) {
        setAsyncResult({ key: requestKey, tokens });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [highlighter, code, language, requestKey, syncTokens]);

  const highlightedLines =
    syncTokens ?? (asyncResult?.key === requestKey ? asyncResult.tokens : null);

  if (!highlightedLines || highlightedLines.length !== lines.length) {
    return <span>{code}</span>;
  }

  return (
    <span>
      {highlightedLines.map((lineTokens, lineIdx) => (
        <React.Fragment key={lineIdx}>
          {lineIdx > 0 ? "\n" : null}
          {renderShikiLineTokens(lineTokens)}
        </React.Fragment>
      ))}
    </span>
  );
};

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
      | { kind: "code"; code: string; lang: string | null; lineIdx: number }
    > = [];
    let i = 0;
    while (i < rawLines.length) {
      const current = rawLines[i];
      const trimmedCurrent = current.trim();
      if (trimmedCurrent.startsWith("```")) {
        const startIdx = i;
        const fenceInfo = trimmedCurrent.slice(3).trim();
        const lang = fenceInfo.split(/\s+/)[0] || null;
        i++;
        const codeLines: string[] = [];
        while (i < rawLines.length && !rawLines[i].trim().startsWith("```")) {
          codeLines.push(rawLines[i]);
          i++;
        }
        if (i < rawLines.length && rawLines[i].trim().startsWith("```")) {
          i++;
        }
        out.push({ kind: "code", code: codeLines.join("\n"), lang, lineIdx: startIdx });
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
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.85em] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 align-baseline"
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
          const supportedLang = normalizeShikiLanguage(block.lang);
          return (
            <pre
              key={block.lineIdx}
              className="px-3.5 py-2.5 bg-surface-panel border border-zinc-200 dark:border-zinc-800 rounded-xl font-mono text-xs text-zinc-800 dark:text-zinc-200 overflow-x-auto whitespace-pre my-2"
            >
              <code>
                {supportedLang ? (
                  <CodeFenceSpan code={block.code} language={supportedLang} />
                ) : (
                  block.code
                )}
              </code>
            </pre>
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
              <span className="font-display tabular-nums text-zinc-500 dark:text-zinc-400 font-semibold select-none text-xs mt-0.5 shrink-0">
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
