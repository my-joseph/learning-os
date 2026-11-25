export type SupportedShikiLang =
  | "javascript"
  | "typescript"
  | "tsx"
  | "jsx"
  | "json"
  | "python"
  | "sql"
  | "bash";

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
 * Normalize a language name or common alias to one of the bundled Shiki grammars,
 * or return `null` when the language is unknown (so callers fall back to plain text).
 */
export function normalizeShikiLanguage(language?: string | null): SupportedShikiLang | null {
  if (!language) return null;
  const key = language.trim().toLowerCase();
  if (!key) return null;
  return LANGUAGE_ALIASES[key] ?? null;
}

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
