import type { ThemedToken } from "shiki/core";

export interface ShikiHighlighterHooks {
  highlightTokensSync: (code: string, language?: string | null) => ThemedToken[][] | null;
  highlightCode: (code: string, language?: string | null) => Promise<ThemedToken[][] | null>;
}

let registeredHighlighter: ShikiHighlighterHooks | null = null;

/**
 * Register the Shiki highlighter functions when `src/lib/shiki` is loaded so shared
 * components like `FormattedText` can render tokens without importing Shiki on Math routes.
 */
export function registerShikiHighlighter(hooks: ShikiHighlighterHooks): void {
  registeredHighlighter = hooks;
}

/**
 * Return the registered Shiki highlighter hooks if `src/lib/shiki` has been loaded.
 */
export function getRegisteredShikiHighlighter(): ShikiHighlighterHooks | null {
  return registeredHighlighter;
}
