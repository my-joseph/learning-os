"use client";

import React, { useMemo } from "react";
import katex from "katex";
import { BookOpen } from "lucide-react";
import { MATH_TOKEN, isMathSegment, unescapeDollar } from "@/lib/mathText";

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

  const lines = useMemo(() => {
    if (!text) return [];
    return text.split("\n");
  }, [text]);

  const renderInline = (content: string) => {
    if (!content) return null;
    const segments = content.split(inlineRegex).filter(Boolean);

    return segments.map((seg, idx) => {
      // 1. LaTeX Math: $...$
      if (isMathSegment(seg)) {
        const tex = seg.slice(1, -1);
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

  if (lines.length <= 1) {
    return <span className={className}>{renderInline(text)}</span>;
  }

  return (
    <div className={`space-y-1.5 ${className}`}>
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={lineIdx} className="h-1.5" />;
        }

        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const bulletContent = trimmed.slice(2);
          return (
            <div
              key={lineIdx}
              className="flex items-start gap-2 text-zinc-800 dark:text-zinc-200 leading-relaxed pl-2 py-0.5"
            >
              <span className="text-zinc-400 dark:text-zinc-500 font-bold select-none text-xs mt-1 shrink-0">
                •
              </span>
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
              <span className="font-mono text-zinc-500 dark:text-zinc-400 font-semibold select-none text-xs mt-0.5 shrink-0">
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
