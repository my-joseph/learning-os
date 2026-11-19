import { loadVariantBankFromDisk } from "./paths";

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

/** Cheap boolean check used to annotate drill payloads with `hasVariants`. */
export function hasVariantsForProblem(
  doc: Record<string, unknown>,
  problem: Record<string, unknown>,
  bankCache?: Map<string, Array<Record<string, unknown>>>
): boolean {
  return findVariantsForProblem(doc, problem, bankCache).length > 0;
}

/** Pick the first unseen variant for `mode=try`, returning null if all have been seen. */
export function pickUnseenVariant(
  variants: Array<Record<string, unknown>>,
  variantsSeen: string[]
): { variant: Record<string, unknown>; remainingCount: number } | null {
  const seenSet = new Set(variantsSeen);
  const unseen = variants.filter(
    (v) => typeof v.variantId === "string" && !seenSet.has(v.variantId)
  );
  if (unseen.length === 0) return null;
  return {
    variant: unseen[0],
    remainingCount: unseen.length - 1,
  };
}

/**
 * Pick one variant for `mode=example` (fully solved), preferring one that does not
 * match `excludeVariantId` (so an open "Try a similar question" is not spoiled) and
 * preferring an unseen variant when available.
 */
export function pickExampleVariant(
  variants: Array<Record<string, unknown>>,
  variantsSeen: string[],
  excludeVariantId?: string | null
): Record<string, unknown> | null {
  if (variants.length === 0) return null;
  const seenSet = new Set(variantsSeen);
  const notExcluded = excludeVariantId
    ? variants.filter((v) => v.variantId !== excludeVariantId)
    : variants;
  const pool = notExcluded.length > 0 ? notExcluded : variants;
  const unseen = pool.find(
    (v) => typeof v.variantId === "string" && !seenSet.has(v.variantId)
  );
  return unseen ?? pool[0];
}
