import React from "react";
import type { ThemedToken } from "shiki/core";

/**
 * Render one tokenized line as Shiki dual-theme `<span>` elements.
 */
export function renderShikiLineTokens(tokens: ThemedToken[]): React.ReactNode {
  return tokens.map((tok, tIdx) => {
    if (!tok.htmlStyle) {
      return <React.Fragment key={tIdx}>{tok.content}</React.Fragment>;
    }
    return (
      <span
        key={tIdx}
        className="shiki-token"
        style={tok.htmlStyle as React.CSSProperties}
      >
        {tok.content}
      </span>
    );
  });
}
