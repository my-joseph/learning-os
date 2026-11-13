"use client";

import React, { useMemo } from "react";
import katex from "katex";

/**
 * Defensively cleans and recovers LaTeX strings corrupted by language escape collisions:
 * e.g. Python \frac -> \x0crac (formfeed), \right -> \r ight (carriage return), \begin -> \x08egin (backspace)
 */
export function normalizeLatex(tex: string): string {
  if (!tex) return "";
  let clean = tex;
  // 1. Repair common Python escape artifact collisions:
  // \f + rac or stray form feed -> \frac
  clean = clean.replace(/\x0crac\{/g, "\\frac{");
  clean = clean.replace(/[\x0c]/g, "");
  // \r + ight or carriage return -> \right
  clean = clean.replace(/\r/g, "");
  // \b + egin / bar -> \begin / \bar
  clean = clean.replace(/\x08egin\{/g, "\\begin{");
  clean = clean.replace(/\x08ar\{/g, "\\bar{");
  clean = clean.replace(/[\x08]/g, "");
  // Repair unescaped rac{ or ight) if preceded by space or bracket
  clean = clean.replace(/(?:^|[\s({\[])rac\{/g, (match) => match.replace("rac{", "\\frac{"));
  clean = clean.replace(/(?:^|[\s({\[])ight([)\]}|.])/g, (match) => match.replace("ight", "\\right"));
  return clean.trim();
}

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
          const tex = normalizeLatex(part.slice(1, -1));
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
    const cleanTex = normalizeLatex(latex);
    try {
      return katex.renderToString(cleanTex, {
        displayMode: true,
        throwOnError: false,
      });
    } catch {
      return `<code>${cleanTex}</code>`;
    }
  }, [latex]);

  return (
    <div
      className={`overflow-x-auto my-2 ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
