import crypto from "crypto";
import { loadVariantBankFromDisk } from "./paths";
import { ProblemState, VariantSessionRecord } from "@/types/drill";

const TOKEN_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz";

/** Collect every bank `variantId` already seen/served for a problem (both `try` and `example` roles). */
export function collectSeenVariantIds(state?: ProblemState | null): string[] {
  const seen = new Set<string>();
  if (Array.isArray(state?.variantsSeen)) {
    for (const v of state.variantsSeen) {
      if (typeof v === "string" && v) seen.add(v);
    }
  }
  if (state?.variants && typeof state.variants === "object") {
    for (const rec of Object.values(state.variants)) {
      if (
        rec &&
        typeof rec.variantId === "string" &&
        rec.variantId &&
        (Boolean(rec.servedAt) || (Array.isArray(rec.attempts) && rec.attempts.length > 0))
      ) {
        seen.add(rec.variantId);
      }
    }
  }
  return Array.from(seen);
}

/** Generate a random-suffixed opaque per-problem token (`v` + 6 base36 chars, unique per problem). */
export function generateVariantToken(
  variants?: Record<string, VariantSessionRecord> | null
): string {
  const existing = new Set(
    variants && typeof variants === "object" ? Object.keys(variants) : []
  );
  for (let attempt = 0; attempt < 64; attempt += 1) {
    const bytes = crypto.randomBytes(6);
    let suffix = "";
    for (let i = 0; i < 6; i += 1) {
      suffix += TOKEN_ALPHABET[bytes[i] % TOKEN_ALPHABET.length];
    }
    const token = `v${suffix}`;
    if (!existing.has(token)) return token;
  }
  return `v${Date.now().toString(36).slice(-6)}`;
}

function normPrompt(val: unknown): string {
  return String(val || "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function candidateBankCodes(
  doc: Record<string, unknown>,
  problem: Record<string, unknown>
): string[] {
  const seen = new Set<string>();
  const add = (code: unknown) => {
    if (typeof code !== "string") return;
    const trimmed = code.trim();
    if (!trimmed || seen.has(trimmed)) return;
    seen.add(trimmed);
    const chapterMatch = trimmed.match(/^(.+)-U\d+$/);
    if (chapterMatch && !seen.has(chapterMatch[1])) {
      seen.add(chapterMatch[1]);
    }
  };
  add(problem.unitCode);
  add(doc.unitCode);
  add(doc.chapterCode);
  return Array.from(seen);
}

/**
 * Return all bank variants matching a problem's `archetypeKey`,
 * strictly excluding any item identical to the learner's original problem.
 */
export function findVariantsForProblem(
  doc: Record<string, unknown>,
  problem: Record<string, unknown>,
  bankCache?: Map<string, Array<Record<string, unknown>>>
): Array<Record<string, unknown>> {
  const isPrg =
    doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-");
  if (isPrg) return [];

  const archetypeKey =
    typeof problem.archetypeKey === "string" && problem.archetypeKey.trim()
      ? problem.archetypeKey.trim()
      : typeof problem.templateKey === "string" && problem.templateKey.trim()
      ? problem.templateKey.trim()
      : "";
  if (!archetypeKey) return [];

  const origPrompt = normPrompt(problem.prompt);
  const origId = typeof problem.id === "string" ? problem.id : "";
  const seenIds = new Set<string>();
  const matches: Array<Record<string, unknown>> = [];

  for (const code of candidateBankCodes(doc, problem)) {
    let variants: Array<Record<string, unknown>>;
    if (bankCache && bankCache.has(code)) {
      variants = bankCache.get(code)!;
    } else {
      const bank = loadVariantBankFromDisk(code);
      variants = bank ? bank.variants : [];
      if (bankCache) bankCache.set(code, variants);
    }

    for (const v of variants) {
      const vid = typeof v.variantId === "string" ? v.variantId : "";
      if (!vid || seenIds.has(vid)) continue;
      const vArch =
        (typeof v.archetypeKey === "string" && v.archetypeKey.trim()) ||
        (typeof v.sourceArchetype === "string" && v.sourceArchetype.trim()) ||
        "";
      if (vArch !== archetypeKey) continue;
      // Defensive guard: never return the learner's own problem.
      if (vid === origId || (origPrompt && normPrompt(v.prompt) === origPrompt)) {
        continue;
      }
      seenIds.add(vid);
      matches.push(v);
    }
  }

  return matches;
}

/**
 * Pick one variant for `mode=example` (fully solved), preferring an unseen variant when available.
 */
export function pickExampleVariant(
  variants: Array<Record<string, unknown>>,
  variantsSeen: string[]
): Record<string, unknown> | null {
  if (variants.length === 0) return null;
  const seenSet = new Set(variantsSeen);
  const unseen = variants.find(
    (v) => typeof v.variantId === "string" && !seenSet.has(v.variantId)
  );
  return unseen ?? variants[0];
}
