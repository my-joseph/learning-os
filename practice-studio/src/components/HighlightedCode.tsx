"use client";

import React, { useEffect, useMemo, useState } from "react";
import type { ThemedToken } from "shiki/core";
import {
  highlightCode,
  highlightTokensSync,
  normalizeShikiLanguage,
} from "@/lib/shiki";
import { renderShikiLineTokens } from "@/lib/shikiTokens";

export { renderShikiLineTokens };

/**
 * React hook that yields Shiki dual-theme tokens without blocking first paint:
 * returns `null` initially on cold start (plain text renders immediately), then
 * swaps in highlighted tokens once the lazy singleton and grammar are ready.
 * When the singleton + grammar are already warm, returns tokens synchronously.
 */
export function useShikiTokens(
  code: string,
  language?: string | null
): ThemedToken[][] | null {
  const normalizedLang = normalizeShikiLanguage(language);
  const syncTokens = useMemo(
    () => highlightTokensSync(code, normalizedLang),
    [code, normalizedLang]
  );
  const requestKey = normalizedLang ? `${normalizedLang}:${code}` : null;
  const [asyncResult, setAsyncResult] = useState<{
    key: string;
    tokens: ThemedToken[][];
  } | null>(null);

  useEffect(() => {
    if (!normalizedLang || !requestKey || syncTokens) return;
    let cancelled = false;
    void highlightCode(code, normalizedLang).then((tokens) => {
      if (!cancelled && tokens) {
        setAsyncResult({ key: requestKey, tokens });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [code, normalizedLang, requestKey, syncTokens]);

  if (!normalizedLang) return null;
  if (syncTokens) return syncTokens;
  if (requestKey && asyncResult?.key === requestKey) {
    return asyncResult.tokens;
  }
  return null;
}

interface HighlightedCodeProps {
  code: string;
  language?: string;
  className?: string;
}

/**
 * Inline syntax-highlighted code span used for quiet blocks such as Example Input/Output.
 * Renders plain text immediately on first paint and swaps in Shiki tokens when ready.
 */
export const HighlightedCode: React.FC<HighlightedCodeProps> = ({
  code,
  language = "javascript",
  className,
}) => {
  const lines = useMemo(() => code.split("\n"), [code]);
  const highlightedLines = useShikiTokens(code, language);

  if (!highlightedLines || highlightedLines.length !== lines.length) {
    return <span className={className}>{code}</span>;
  }

  return (
    <span className={className}>
      {highlightedLines.map((lineTokens, lineIdx) => (
        <React.Fragment key={lineIdx}>
          {lineIdx > 0 ? "\n" : null}
          {renderShikiLineTokens(lineTokens)}
        </React.Fragment>
      ))}
    </span>
  );
};
