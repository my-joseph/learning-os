import type { HighlighterCore, LanguageRegistration, ThemedToken, ThemeRegistrationAny } from "shiki/core";
import {
  SUPPORTED_SHIKI_LANGS,
  getExtensionForLanguage,
  inferShikiLanguageFromFilename,
  normalizeShikiLanguage,
  type SupportedShikiLang,
} from "./shikiLanguages";
import { registerShikiHighlighter } from "./shikiRegistry";

export {
  SUPPORTED_SHIKI_LANGS,
  getExtensionForLanguage,
  inferShikiLanguageFromFilename,
  normalizeShikiLanguage,
  type SupportedShikiLang,
};

export const SHIKI_THEMES = {
  light: "github-light",
  dark: "github-dark",
} as const;

type LangModule =
  | LanguageRegistration
  | LanguageRegistration[]
  | { default: LanguageRegistration | LanguageRegistration[] };

type ThemeModule = ThemeRegistrationAny | { default: ThemeRegistrationAny };

const LANG_LOADERS: Record<SupportedShikiLang, () => Promise<LangModule>> = {
  javascript: () => import("shiki/langs/javascript.mjs"),
  typescript: () => import("shiki/langs/typescript.mjs"),
  tsx: () => import("shiki/langs/tsx.mjs"),
  jsx: () => import("shiki/langs/jsx.mjs"),
  json: () => import("shiki/langs/json.mjs"),
  python: () => import("shiki/langs/python.mjs"),
  sql: () => import("shiki/langs/sql.mjs"),
  bash: () => import("shiki/langs/bash.mjs"),
};

let highlighterInstance: HighlighterCore | null = null;
let highlighterPromise: Promise<HighlighterCore> | null = null;
const loadedLangs = new Set<SupportedShikiLang>();
const langPromises = new Map<SupportedShikiLang, Promise<void>>();

function unwrapDefault<T>(mod: T | { default: T }): T {
  if (mod && typeof mod === "object" && "default" in mod) {
    return mod.default;
  }
  return mod;
}

/**
 * Lazily initialize the singleton Shiki highlighter (`shiki/core` + JS regex engine, no WASM).
 * Only imported and invoked when code highlighting is actually rendered.
 */
export async function getShikiHighlighter(): Promise<HighlighterCore> {
  if (highlighterInstance) {
    return highlighterInstance;
  }
  if (!highlighterPromise) {
    highlighterPromise = (async () => {
      try {
        const [{ createHighlighterCore }, { createJavaScriptRegexEngine }, lightMod, darkMod] =
          await Promise.all([
            import("shiki/core"),
            import("shiki/engine/javascript"),
            import("shiki/themes/github-light.mjs") as Promise<ThemeModule>,
            import("shiki/themes/github-dark.mjs") as Promise<ThemeModule>,
          ]);

        const hl = await createHighlighterCore({
          themes: [unwrapDefault(lightMod), unwrapDefault(darkMod)],
          langs: [],
          engine: createJavaScriptRegexEngine(),
        });
        highlighterInstance = hl;
        return hl;
      } catch (err) {
        highlighterPromise = null;
        throw err;
      }
    })();
  }
  return highlighterPromise;
}

async function ensureLanguageLoaded(hl: HighlighterCore, lang: SupportedShikiLang): Promise<void> {
  if (loadedLangs.has(lang)) return;
  let pending = langPromises.get(lang);
  if (!pending) {
    pending = (async () => {
      try {
        const mod = await LANG_LOADERS[lang]();
        await hl.loadLanguage(unwrapDefault(mod));
        loadedLangs.add(lang);
      } catch (err) {
        langPromises.delete(lang);
        throw err;
      }
    })();
    langPromises.set(lang, pending);
  }
  await pending;
}

function tokenizeWithHighlighter(
  hl: HighlighterCore,
  code: string,
  lang: SupportedShikiLang
): ThemedToken[][] {
  return hl.codeToTokens(code, {
    lang,
    themes: SHIKI_THEMES,
    defaultColor: false,
  }).tokens;
}

/**
 * Synchronously tokenize code if the Shiki singleton and target grammar are already loaded.
 * Returns `null` before initialization or for unsupported languages so first paint stays unblocked.
 */
export function highlightTokensSync(
  code: string,
  language?: string | null
): ThemedToken[][] | null {
  const lang = normalizeShikiLanguage(language);
  if (!lang || !highlighterInstance || !loadedLangs.has(lang)) {
    return null;
  }
  return tokenizeWithHighlighter(highlighterInstance, code, lang);
}

/**
 * Highlight `code` into dual-theme Shiki tokens (`--shiki-light` / `--shiki-dark`).
 * Returns `null` for unsupported languages or if highlighting fails.
 */
export async function highlightCode(
  code: string,
  language?: string | null
): Promise<ThemedToken[][] | null> {
  const lang = normalizeShikiLanguage(language);
  if (!lang) return null;
  try {
    const hl = await getShikiHighlighter();
    await ensureLanguageLoaded(hl, lang);
    return tokenizeWithHighlighter(hl, code, lang);
  } catch {
    return null;
  }
}

/**
 * Preload the Shiki singleton and the given languages (defaults to all 7 supported languages).
 */
export async function preloadShiki(
  langs: readonly SupportedShikiLang[] = SUPPORTED_SHIKI_LANGS
): Promise<void> {
  const hl = await getShikiHighlighter();
  await Promise.all(langs.map((lang) => ensureLanguageLoaded(hl, lang)));
}

registerShikiHighlighter({ highlightTokensSync, highlightCode });
