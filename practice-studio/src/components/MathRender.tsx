"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface MathTextProps {
  text: string;
  className?: string;
}

export const MathText: React.FC<MathTextProps> = ({ text, className = "" }) => {
  const parts = useMemo(() => {
    if (!text) return [];
    // Split by $...$
    return text.split(/(\$[^$]+\$)/g);
  }, [text]);

  return (
    <span className={className}>
      {parts.map((part, idx) => {
        if (part.startsWith("$") && part.endsWith("$") && part.length > 2) {
          const tex = part.slice(1, -1);
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
            return <code key={idx}>{tex}</code>;
          }
        }
        return <React.Fragment key={idx}>{part}</React.Fragment>;
      })}
    </span>
  );
};

interface MathBlockProps {
  latex: string;
  className?: string;
}

export const MathBlock: React.FC<MathBlockProps> = ({ latex, className = "" }) => {
  const html = useMemo(() => {
    if (!latex) return "";
    try {
      return katex.renderToString(latex, {
        displayMode: true,
        throwOnError: false,
      });
    } catch {
      return `<code>${latex}</code>`;
    }
  }, [latex]);

  return (
    <div
      className={`overflow-x-auto my-2 ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
