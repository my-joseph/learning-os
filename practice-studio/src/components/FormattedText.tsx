"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface FormattedTextProps {
  text: string;
  className?: string;
}

export const FormattedText: React.FC<FormattedTextProps> = ({
  text,
  className = "",
}) => {
  const segments = useMemo(() => {
    if (!text) return [];

    // Match $...$ (math), `...` (backtick code), or '...' (single-quoted code identifiers)
    const regex =
      /(\$[^$]+\$|`[^`]+`|(?<=^|[\s(,;])'[\w$][\w$.():\s,\-=><\[\]]*?'(?=[\s),;.:!?]|$))/g;

    return text.split(regex).filter(Boolean);
  }, [text]);

  return (
    <span className={className}>
      {segments.map((seg, idx) => {
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
                className="inline-math"
              />
            );
          } catch {
            return (
              <code
                key={idx}
                className="font-mono text-indigo-300 bg-[#171d2c] border border-indigo-700/40 px-1.5 py-0.5 rounded text-[0.88em]"
              >
                {tex}
              </code>
            );
          }
        }

        // 2. Markdown Backtick Code: `...`
        if (seg.startsWith("`") && seg.endsWith("`") && seg.length >= 2) {
          const code = seg.slice(1, -1);
          return (
            <code
              key={idx}
              className="font-mono text-sky-300 bg-[#131a29] border border-sky-500/40 px-1.5 py-0.5 rounded text-[0.88em] font-medium shadow-sm"
            >
              {code}
            </code>
          );
        }

        // 3. Quoted Code identifier: '...'
        if (seg.startsWith("'") && seg.endsWith("'") && seg.length > 2) {
          const code = seg.slice(1, -1);
          return (
            <code
              key={idx}
              className="font-mono text-sky-300 bg-[#131a29] border border-sky-500/40 px-1.5 py-0.5 rounded text-[0.88em] font-medium shadow-sm"
            >
              {code}
            </code>
          );
        }

        // Plain text
        return <React.Fragment key={idx}>{seg}</React.Fragment>;
      })}
    </span>
  );
};
