import crypto from "crypto";
import { isQuarantinedVariant, isSafeId, loadVariantBankFromDisk } from "./paths";
import { isTimestampInCycle } from "./reviewGuard";
import { openedSimilarTokens } from "./similarTabs";
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

/** Find same-archetype, same-level Similar variants. Worked examples use their existing archetype pool. */
export function findVariantsForProblem(
  doc: Record<string, unknown>,
  problem: Record<string, unknown>,
  options?: {
    mode?: "similar" | "example";
    bankCache?: Map<string, Array<Record<string, unknown>>>;
  }
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

  const sameLevelRequired = options?.mode !== "example";
  const level = problem.level;
  if (sameLevelRequired && (typeof level !== "number" || !Number.isInteger(level))) return [];

  const origPrompt = normPrompt(problem.prompt);
  const origId = typeof problem.id === "string" ? problem.id : "";
  const seenIds = new Set<string>();
  const matches: Array<Record<string, unknown>> = [];
  const bankCache = options?.bankCache;

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
      if (isQuarantinedVariant(v)) continue;
      const vid = typeof v.variantId === "string" ? v.variantId : "";
      if (!vid || seenIds.has(vid)) continue;
      if (sameLevelRequired && (v.level !== level || !isSafeId(vid))) continue;
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

/** Project the saved tab order onto the current bank while retaining session history. */
export function similarStateForVariants(
  state: ProblemState,
  variants: Array<Record<string, unknown>>
): ProblemState {
  const eligibleIds = new Set(variants.map((variant) => variant.variantId));
  return {
    ...state,
    similarSlots: openedSimilarTokens(state).filter((token) =>
      eligibleIds.has(state.variants?.[token]?.variantId)
    ),
  };
}

function matchesParent(
  variant: Record<string, unknown>,
  parent: { drillId: string; problemId: string }
): boolean {
  const { drillId, problemId } = parent;
  return [
    [variant.parentProblemId, variant.parentDrillId],
    [variant.sourceProblemId, variant.sourceDrillId],
  ].some(([variantProblemId, variantDrillId]) =>
    (variantDrillId == null || variantDrillId === drillId) &&
    (variantProblemId === problemId || variantProblemId === `${drillId}/${problemId}`)
  );
}

/**
 * Pick the next matching variant for `"+"` (`action: "open-next"`) in the CURRENT cycle:
 * - Excludes variants already served in the current cycle (either opened as a Similar tab
 *   or viewed as a worked example in the current cycle).
 * - Returns `null` when every matching variant has been served in the current cycle
 *   (per-cycle exhaustion).
 * - Uses variants recorded for the parent first while any are available in the cycle.
 * - Within that pool, prefers variants never served before, then wraps in bank order.
 */
export function pickNextVariantForCycle(
  variants: Array<Record<string, unknown>>,
  state: ProblemState | null | undefined,
  parent: { drillId: string; problemId: string }
): Record<string, unknown> | null {
  const eligible = variants.filter(
    (v) => !isQuarantinedVariant(v) && typeof v.variantId === "string" && isSafeId(v.variantId)
  );
  if (eligible.length === 0) return null;

  const servedInCurrentCycle = new Set<string>();
  const cycleStartedAt = state?.cycleStartedAt ?? null;
  for (const token of openedSimilarTokens(state)) {
    const vid = state?.variants?.[token]?.variantId;
    if (typeof vid === "string" && vid) {
      servedInCurrentCycle.add(vid);
    }
  }
  if (state?.variants && typeof state.variants === "object") {
    for (const rec of Object.values(state.variants)) {
      if (
        rec?.role === "example" &&
        typeof rec.variantId === "string" &&
        rec.variantId &&
        rec.servedAt &&
        (!cycleStartedAt || isTimestampInCycle(rec.servedAt, cycleStartedAt))
      ) {
        servedInCurrentCycle.add(rec.variantId);
      }
    }
  }

  const availableInCycle = eligible.filter(
    (v) => !servedInCurrentCycle.has(String(v.variantId))
  );
  if (availableInCycle.length === 0) return null;

  const parentMatches = availableInCycle.filter((variant) => matchesParent(variant, parent));
  const candidates = parentMatches.length > 0 ? parentMatches : availableInCycle;
  const servedEver = new Set(collectSeenVariantIds(state));
  const neverServed = candidates.find(
    (v) => !servedEver.has(String(v.variantId))
  );
  return neverServed ?? candidates[0];
}

/**
 * Pick one variant for `mode=example` (fully solved), preferring an unseen variant when available.
 */
export function pickExampleVariant(
  variants: Array<Record<string, unknown>>,
  variantsSeen: string[]
): Record<string, unknown> | null {
  const active = variants.filter((v) => !isQuarantinedVariant(v));
  if (active.length === 0) return null;
  const seenSet = new Set(variantsSeen);
  const unseen = active.find(
    (v) => typeof v.variantId === "string" && !seenSet.has(v.variantId)
  );
  return unseen ?? active[0];
}
