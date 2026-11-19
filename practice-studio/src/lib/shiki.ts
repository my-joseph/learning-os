import type { HighlighterCore, LanguageRegistration, ThemedToken, ThemeRegistrationAny } from "shiki/core";

export type SupportedShikiLang =
  | "javascript"
  | "typescript"
  | "tsx"
  | "jsx"
  | "json"
  | "python"
  | "sql"
  | "bash";

export const SHIKI_THEMES = {
  light: "github-light",
  dark: "github-dark",
} as const;

export const SUPPORTED_SHIKI_LANGS: readonly SupportedShikiLang[] = [
  "javascript",
  "typescript",
  "tsx",
  "jsx",
  "json",
  "python",
  "sql",
  "bash",
] as const;

const LANGUAGE_ALIASES: Record<string, SupportedShikiLang> = {
  javascript: "javascript",
  js: "javascript",
  mjs: "javascript",
  cjs: "javascript",
  typescript: "typescript",
  ts: "typescript",
  mts: "typescript",
  cts: "typescript",
  tsx: "tsx",
  jsx: "jsx",
  json: "json",
  python: "python",
  py: "python",
  sql: "sql",
  postgresql: "sql",
  postgres: "sql",
  psql: "sql",
  sqlite: "sql",
  bash: "bash",
  sh: "bash",
  shell: "bash",
  zsh: "bash",
};

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

/**
 * Normalize a language name or common alias to one of the bundled Shiki grammars,
 * or return `null` when the language is unknown (so callers fall back to plain text).
 */
export function normalizeShikiLanguage(language?: string | null): SupportedShikiLang | null {
  if (!language) return null;
  const key = language.trim().toLowerCase();
  if (!key) return null;
  return LANGUAGE_ALIASES[key] ?? null;
}

const LANGUAGE_EXTENSIONS: Record<SupportedShikiLang, string> = {
  javascript: "js",
  typescript: "ts",
  tsx: "tsx",
  jsx: "jsx",
  json: "json",
  python: "py",
  sql: "sql",
  bash: "sh",
};

/**
 * Return the canonical file extension (without leading dot) for a supported language.
 */
export function getExtensionForLanguage(language?: string | null): string {
  const normalized = normalizeShikiLanguage(language);
  return normalized ? LANGUAGE_EXTENSIONS[normalized] : "js";
}

/**
 * Infer a supported language from a filename extension when no explicit language is set.
 */
export function inferShikiLanguageFromFilename(filename?: string | null): SupportedShikiLang | null {
  if (!filename) return null;
  const lower = filename.trim().toLowerCase();
  if (lower.endsWith(".tsx")) return "tsx";
  if (lower.endsWith(".jsx")) return "jsx";
  if (lower.endsWith(".ts") || lower.endsWith(".mts") || lower.endsWith(".cts")) return "typescript";
  if (lower.endsWith(".js") || lower.endsWith(".mjs") || lower.endsWith(".cjs")) return "javascript";
  if (lower.endsWith(".json")) return "json";
  if (lower.endsWith(".py")) return "python";
  if (lower.endsWith(".sql")) return "sql";
  if (lower.endsWith(".sh") || lower.endsWith(".bash") || lower.endsWith(".zsh")) return "bash";
  return null;
}

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
