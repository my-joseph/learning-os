"use client";

import React, { useMemo } from "react";
import katex from "katex";
import { BookOpen } from "lucide-react";

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
      /(\$[^$]+\$|\*\*[^*]+\*\*|`[^`]+`|\[\[[\w-]+\]\]|(?<=^|[\s(,;])'[\w$][\w$.():\s,\-=><\[\]]*?'(?=[\s),;.:!?]|$))/g,
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
      if (seg.startsWith("$") && seg.endsWith("$") && seg.length > 2) {
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
              className="inline-math text-indigo-700 dark:text-indigo-200"
            />
          );
        } catch {
          return (
            <code
              key={idx}
              className="font-mono text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-[#171d2c] border border-indigo-200 dark:border-indigo-700/40 px-1.5 py-0.5 rounded text-[0.88em]"
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
          <strong key={idx} className="font-semibold text-slate-900 dark:text-white tracking-wide">
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
            className="font-mono text-sky-700 dark:text-sky-300 bg-sky-50 dark:bg-[#131a29] border border-sky-200 dark:border-sky-500/40 px-1.5 py-0.5 rounded text-[0.88em] font-medium shadow-sm"
          >
            {code}
          </code>
        );
      }

      // 4. Concept Vault Token: [[KEY]]
      if (seg.startsWith("[[") && seg.endsWith("]]") && seg.length >= 4) {
        const key = seg.slice(2, -2);
        const displayLabel = key.startsWith("CON-") ? key.replace("CON-", "").replace(/-/g, " ") : key;
        return (
          <span
            key={idx}
            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.85em] font-medium bg-emerald-50 dark:bg-emerald-950/70 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/50 shadow-sm align-baseline"
            title={`Concept Vault: ${key}`}
          >
            <BookOpen className="w-3 h-3 shrink-0 opacity-80" />
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
            className="font-mono text-sky-700 dark:text-sky-300 bg-sky-50 dark:bg-[#131a29] border border-sky-200 dark:border-sky-500/40 px-1.5 py-0.5 rounded text-[0.88em] font-medium shadow-sm"
          >
            {code}
          </code>
        );
      }

      // Plain text
      return <React.Fragment key={idx}>{seg}</React.Fragment>;
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
              className="flex items-start gap-2 text-slate-700 dark:text-slate-200 leading-relaxed pl-2 py-0.5"
            >
              <span className="text-sky-600 dark:text-sky-400 font-bold select-none text-xs mt-1 shrink-0">
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
              className="flex items-start gap-2 text-slate-700 dark:text-slate-200 leading-relaxed pl-2 py-0.5"
            >
              <span className="font-mono text-sky-600 dark:text-sky-400 font-bold select-none text-xs mt-0.5 shrink-0">
                {num}.
              </span>
              <div className="flex-1">{renderInline(numContent)}</div>
            </div>
          );
        }

        return (
          <div key={lineIdx} className="text-slate-800 dark:text-slate-200 leading-relaxed">
            {renderInline(line)}
          </div>
        );
      })}
    </div>
  );
};
