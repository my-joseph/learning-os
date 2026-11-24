import fs from "fs";
import path from "path";
import { getProgressDir, isSafeId } from "@/lib/paths";
import { isSubstantiveVerdict } from "@/lib/reviewGuard";
import { MAX_SIMILAR_TABS } from "@/lib/similarTabs";
import { generateVariantToken } from "@/lib/variants";
import { AttemptRecord, ProblemState, VariantSessionRecord } from "@/types/drill";
import type { NotionSyncRetry } from "@/lib/notionSyncRunner";

/**
 * Learner progress is stored apart from drill content (mirrors progress_store.py):
 * drills/data/<UNIT>/<DRILL_ID>.json = content only, progress/<DRILL_ID>.json =
 * { drillId, unitCode, updatedAt, sessionSummary, problems: { [problemId]: state } }.
 */
export interface ProgressFile {
  drillId: string;
  unitCode?: string;
  updatedAt?: string;
  sessionSummary?: Record<string, unknown>;
  problems?: Record<string, unknown>;
}

type DocLike = {
  drillId?: string;
  unitCode?: string;
  sessionSummary?: unknown;
  problems?: Array<{ id?: string; state?: unknown }>;
  reviewMerge?: boolean;
};

function progressFile(drillId: string): string {
  return path.join(getProgressDir(), `${drillId}.json`);
}

interface PendingNotionSync {
  fingerprint: string;
  attemptDate?: string;
  retry: NotionSyncRetry;
}

// Keep sync checkpoints outside the autosaved learner record so an edit cannot overwrite them.
function pendingNotionSyncFile(drillId: string): string {
  if (!isSafeId(drillId)) throw new Error("Invalid drillId");
  return path.join(getProgressDir(), "_notion_sync", `${drillId}.json`);
}

export function readPendingNotionSync(drillId: string): PendingNotionSync | null {
  const file = pendingNotionSyncFile(drillId);
  if (!fs.existsSync(file)) return null;
  return JSON.parse(fs.readFileSync(file, "utf-8")) as PendingNotionSync;
}

export function writePendingNotionSync(drillId: string, pending: PendingNotionSync | null): void {
  const file = pendingNotionSyncFile(drillId);
  if (pending) writeJsonAtomic(file, pending);
  else fs.rmSync(file, { force: true });
}

/** Write JSON atomically using a unique sibling temp file + rename so concurrent readers never see a half-written file. */
function writeJsonAtomic(filePath: string, data: unknown): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const suffix = `${process.pid}.${Date.now()}.${Math.random().toString(36).slice(2, 8)}`;
  const tmpPath = `${filePath}.${suffix}.tmp`;
  try {
    fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2), "utf-8");
    fs.renameSync(tmpPath, filePath);
  } catch (err) {
    try {
      if (fs.existsSync(tmpPath)) {
        fs.unlinkSync(tmpPath);
      }
    } catch {
      // ignore cleanup error
    }
    throw err;
  }
}

const ISO_DATE_PREFIX_RE = /^\d{4}-\d{2}-\d{2}/;

function isEmptyValue(v: unknown): boolean {
  return v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
}

function attemptKey(a: unknown): string {
  if (a && typeof a === "object") {
    const ts = (a as Record<string, unknown>).ts;
    if (typeof ts === "string" && ts.length > 0) {
      return `ts:${ts}`;
    }
  }
  return `raw:${JSON.stringify(a)}`;
}

/** Union attempt lists by `ts` (falling back to serialized equality), preserving order and keeping chronological order when all carry ISO timestamps. */
function mergeAttempts(
  prevRaw: unknown,
  nextRaw: unknown
): Array<Record<string, unknown>> | undefined {
  const prev = Array.isArray(prevRaw)
    ? (prevRaw.filter((a) => a && typeof a === "object") as Array<Record<string, unknown>>)
    : [];
  const next = Array.isArray(nextRaw)
    ? (nextRaw.filter((a) => a && typeof a === "object") as Array<Record<string, unknown>>)
    : [];
  if (prev.length === 0 && next.length === 0) {
    return Array.isArray(nextRaw) ? [] : Array.isArray(prevRaw) ? [] : undefined;
  }
  const seen = new Set<string>();
  const merged: Array<Record<string, unknown>> = [];
  for (const item of prev) {
    const key = attemptKey(item);
    if (!seen.has(key)) {
      seen.add(key);
      merged.push(item);
    }
  }
  let addedFromNext = false;
  for (const item of next) {
    const key = attemptKey(item);
    if (!seen.has(key)) {
      seen.add(key);
      merged.push(item);
      addedFromNext = true;
    }
  }
  if (
    addedFromNext &&
    prev.length > 0 &&
    merged.every((a) => typeof a.ts === "string" && ISO_DATE_PREFIX_RE.test(a.ts))
  ) {
    merged.sort((a, b) => String(a.ts).localeCompare(String(b.ts)));
  }
  return merged;
}

function reviewKey(r: unknown): string {
  if (r && typeof r === "object") {
    const rec = r as Record<string, unknown>;
    if (typeof rec.id === "string" && rec.id) return `id:${rec.id}`;
    const ts =
      (typeof rec.at === "string" && rec.at) ||
      (typeof rec.ts === "string" && rec.ts) ||
      "";
    const verdict = typeof rec.verdict === "string" ? rec.verdict : "";
    const attempt = typeof rec.attempt === "number" ? String(rec.attempt) : "";
    if (ts) return `ts:${ts}|attempt:${attempt}|verdict:${verdict}`;
    if (attempt) return `attempt:${attempt}|hash:${String(rec.codeHash || "")}|verdict:${verdict}`;
  }
  return `raw:${JSON.stringify(r)}`;
}

function reviewSlotKey(r: unknown): string | null {
  if (!r || typeof r !== "object") return null;
  const rec = r as Record<string, unknown>;
  const ts =
    (typeof rec.at === "string" && rec.at) ||
    (typeof rec.ts === "string" && rec.ts) ||
    "";
  const attempt = typeof rec.attempt === "number" ? String(rec.attempt) : "";
  return ts && attempt ? `ts:${ts}|attempt:${attempt}` : null;
}

function reviewDisputedCount(r: unknown): number {
  if (!r || typeof r !== "object") return 0;
  const findings = (r as Record<string, unknown>).findings;
  if (!Array.isArray(findings)) return 0;
  return findings.filter(
    (f) => f && typeof f === "object" && Boolean((f as Record<string, unknown>).disputed)
  ).length;
}

/** Union server-owned `reviews[]` with incoming reviews by id/at/ts; server copies win on key collision so explain/dispute updates are never lost. */
function mergeReviews(prevRaw: unknown, nextRaw: unknown): unknown[] | undefined {
  const prev = Array.isArray(prevRaw) ? prevRaw : [];
  const next = Array.isArray(nextRaw) ? nextRaw : [];
  if (prev.length === 0 && next.length === 0) {
    return Array.isArray(nextRaw) ? [] : Array.isArray(prevRaw) ? [] : undefined;
  }
  const seen = new Set<string>();
  const prevDisputesBySlot = new Map<string, number>();
  const merged: unknown[] = [];
  for (const item of prev) {
    const key = reviewKey(item);
    if (!seen.has(key)) {
      seen.add(key);
      merged.push(item);
      const slot = reviewSlotKey(item);
      if (slot) {
        const count = reviewDisputedCount(item);
        prevDisputesBySlot.set(slot, Math.max(prevDisputesBySlot.get(slot) ?? 0, count));
      }
    }
  }
  for (const item of next) {
    const key = reviewKey(item);
    if (seen.has(key)) continue;
    const slot = reviewSlotKey(item);
    if (slot && (prevDisputesBySlot.get(slot) ?? 0) > reviewDisputedCount(item)) {
      // Stale client copy predating a server-side finding dispute for the same (at, attempt).
      continue;
    }
    seen.add(key);
    merged.push(item);
  }
  return merged;
}

function maxIsoTimestamp(a: unknown, b: unknown): string | null {
  const sa = typeof a === "string" && a.trim() ? a.trim() : null;
  const sb = typeof b === "string" && b.trim() ? b.trim() : null;
  if (sa && sb) return sa > sb ? sa : sb;
  return sa || sb;
}

function mergeStringTags(prevRaw: unknown, nextRaw: unknown): string[] {
  const prev = Array.isArray(prevRaw)
    ? prevRaw.filter((t): t is string => typeof t === "string" && t.length > 0)
    : [];
  const next = Array.isArray(nextRaw)
    ? nextRaw.filter((t): t is string => typeof t === "string" && t.length > 0)
    : [];
  const seen = new Set<string>(prev);
  const out = [...prev];
  for (const tag of next) {
    if (!seen.has(tag)) {
      seen.add(tag);
      out.push(tag);
    }
  }
  return out;
}

export function readProgress(drillId: string): ProgressFile | null {
  if (!isSafeId(drillId)) return null;
  const file = progressFile(drillId);
  if (!fs.existsSync(file)) return null;
  try {
    return JSON.parse(fs.readFileSync(file, "utf-8")) as ProgressFile;
  } catch {
    return null;
  }
}

/** Overlay saved progress onto a content document (mutates and returns it). */
export function applyProgress<T extends DocLike>(doc: T, progress: ProgressFile | null): T {
  if (!progress) return doc;
  if (progress.sessionSummary) doc.sessionSummary = progress.sessionSummary;
  const states = progress.problems || {};
  for (const p of doc.problems || []) {
    if (p.id && Object.prototype.hasOwnProperty.call(states, p.id)) {
      p.state = states[p.id];
    }
  }
  return doc;
}

function deriveVariantLists(
  variants: Record<string, VariantSessionRecord> | undefined,
  existingSeen: unknown,
  existingAttempted: unknown
): { variantsSeen: string[]; variantsAttempted: string[] } {
  const seen = new Set<string>(
    Array.isArray(existingSeen)
      ? existingSeen.filter((x): x is string => typeof x === "string" && Boolean(x))
      : []
  );
  const attempted = new Set<string>(
    Array.isArray(existingAttempted)
      ? existingAttempted.filter((x): x is string => typeof x === "string" && Boolean(x))
      : []
  );
  if (variants && typeof variants === "object") {
    for (const rec of Object.values(variants)) {
      if (!rec || typeof rec !== "object" || typeof rec.variantId !== "string" || !rec.variantId) {
        continue;
      }
      const hasAttempts = Array.isArray(rec.attempts) && rec.attempts.length > 0;
      if (Boolean(rec.servedAt) || hasAttempts) {
        seen.add(rec.variantId);
      }
      if (
        hasAttempts &&
        rec.attempts.some((a) => isSubstantiveVerdict(a?.verdict))
      ) {
        attempted.add(rec.variantId);
      }
    }
  }
  return {
    variantsSeen: Array.from(seen),
    variantsAttempted: Array.from(attempted),
  };
}

export interface WriteProgressOptions {
  /**
   * When false (used by client-facing `/api/save-state` and pre-sync writes),
   * existing sync stamps on disk are always preserved and incoming client stamps
   * can never clear or forge them. Defaults to true for server/test callers.
   */
  allowSyncStampUpdate?: boolean;
}

function nonEmptyString(v: unknown): string | null {
  return typeof v === "string" && v.trim().length > 0 ? v.trim() : null;
}

/**
 * Merge `sessionSummary` field-wise while protecting server-owned Notion sync stamps
 * (`syncedToNotionAt`, `notionPageId`, `syncedFingerprint`):
 * - Existing non-empty stamps can NEVER be cleared (`null`, `""`, or omitted).
 * - When `allowSyncStampUpdate` is false, disk stamps always win and client-supplied
 *   stamps are ignored.
 * - When `allowSyncStampUpdate` is true, only a strictly newer `syncedToNotionAt`
 *   (or the first stamp when none existed) replaces the existing stamps.
 */
export function mergeSessionSummary(
  prevRaw: unknown,
  nextRaw: unknown,
  options: { allowSyncStampUpdate?: boolean } = {}
): Record<string, unknown> {
  const allowSyncStampUpdate = options.allowSyncStampUpdate ?? true;
  const prev =
    prevRaw && typeof prevRaw === "object" && !Array.isArray(prevRaw)
      ? (prevRaw as Record<string, unknown>)
      : {};
  const next =
    nextRaw && typeof nextRaw === "object" && !Array.isArray(nextRaw)
      ? (nextRaw as Record<string, unknown>)
      : {};

  const merged: Record<string, unknown> = { ...prev };
  for (const [k, v] of Object.entries(next)) {
    if (v !== undefined) {
      merged[k] = v;
    }
  }

  const prevSyncedAt = nonEmptyString(prev.syncedToNotionAt);
  const nextSyncedAt = nonEmptyString(next.syncedToNotionAt);
  const prevPageId = nonEmptyString(prev.notionPageId);
  const nextPageId = nonEmptyString(next.notionPageId);
  const prevFp = nonEmptyString(prev.syncedFingerprint);
  const nextFp = nonEmptyString(next.syncedFingerprint);

  if (!allowSyncStampUpdate) {
    if (prevSyncedAt) {
      merged.syncedToNotionAt = prevSyncedAt;
    } else {
      delete merged.syncedToNotionAt;
    }
    if (prevPageId) {
      merged.notionPageId = prevPageId;
    } else {
      delete merged.notionPageId;
    }
    if (prevFp) {
      merged.syncedFingerprint = prevFp;
    } else {
      delete merged.syncedFingerprint;
    }
    return merged;
  }

  const isNewerStamp = Boolean(
    nextSyncedAt && (!prevSyncedAt || nextSyncedAt > prevSyncedAt)
  );

  if (isNewerStamp) {
    merged.syncedToNotionAt = nextSyncedAt;
    if (nextPageId || prevPageId) {
      merged.notionPageId = nextPageId || prevPageId;
    }
    if (nextFp || prevFp) {
      merged.syncedFingerprint = nextFp || prevFp;
    }
  } else {
    if (prevSyncedAt) {
      merged.syncedToNotionAt = prevSyncedAt;
    }
    if (prevPageId || nextPageId) {
      merged.notionPageId = prevPageId || nextPageId;
    }
    if (prevFp || nextFp) {
      merged.syncedFingerprint = prevFp || nextFp;
    }
  }

  return merged;
}

/** Save only the learner-owned part of a document; never touches drill content. */
export function writeProgress(doc: DocLike, options: WriteProgressOptions = {}): string {
  if (!doc.drillId || !isSafeId(doc.drillId)) throw new Error("Invalid drillId");
  const existing = readProgress(doc.drillId);
  const existingProblems = (existing?.problems || {}) as Record<string, Record<string, unknown>>;
  const problems: Record<string, unknown> = { ...existingProblems };
  const nowIso = new Date().toISOString();

  for (const p of doc.problems || []) {
    if (!p.id) continue;
    const prev = existingProblems[p.id];
    if (p.state) {
      const incoming = p.state as Record<string, unknown>;
      let st: Record<string, unknown>;

      if (doc.reviewMerge && prev) {
        // Daily Review merge: start from the original persisted state and ONLY append
        // attempts, merge server reviews, fill notes/tags, and advance cycle metadata.
        // Never overwrite original score, help flags, skipped, lastCheck, lastTestReport, or durationMs.
        st = { ...prev };

        const mergedAttempts = mergeAttempts(prev.attempts, incoming.attempts);
        if (mergedAttempts !== undefined) {
          st.attempts = mergedAttempts;
        }

        const mergedReviews = mergeReviews(prev.reviews, incoming.reviews);
        if (mergedReviews !== undefined) {
          st.reviews = mergedReviews;
        }

        const mergedTestRuns = mergeAttempts(prev.testRuns, incoming.testRuns);
        if (mergedTestRuns !== undefined) {
          st.testRuns = mergedTestRuns;
        }

        if (Array.isArray(incoming.mistakes) && incoming.mistakes.length > 0) {
          st.mistakes = mergeStringTags(prev.mistakes, incoming.mistakes);
        }
        if (typeof incoming.mistakeNote === "string" && incoming.mistakeNote.trim().length > 0) {
          st.mistakeNote = incoming.mistakeNote;
        }
        if (typeof incoming.revisitNote === "string" && incoming.revisitNote.trim().length > 0) {
          st.revisitNote = incoming.revisitNote;
        }

        const maxCycle = maxIsoTimestamp(prev.cycleStartedAt, incoming.cycleStartedAt);
        if (maxCycle) {
          st.cycleStartedAt = maxCycle;
        }

        const revealStamp = maxIsoTimestamp(nowIso, st.cycleStartedAt) || nowIso;
        if (incoming.setupRevealedBeforeAnswer === true) {
          st.reviewSetupRevealedAt = maxIsoTimestamp(prev.reviewSetupRevealedAt, revealStamp);
        }
        if (incoming.solutionRevealedBeforeAnswer === true) {
          st.reviewStepsRevealedAt = maxIsoTimestamp(prev.reviewStepsRevealedAt, revealStamp);
        }
        if (typeof incoming.hintsRevealed === "number" && incoming.hintsRevealed > 0) {
          st.reviewHintRevealedAt = maxIsoTimestamp(prev.reviewHintRevealedAt, revealStamp);
        }
        const maxIncomingRevSetup = maxIsoTimestamp(
          st.reviewSetupRevealedAt,
          incoming.reviewSetupRevealedAt
        );
        if (maxIncomingRevSetup) {
          st.reviewSetupRevealedAt = maxIncomingRevSetup;
        }
        const maxIncomingRevSteps = maxIsoTimestamp(
          st.reviewStepsRevealedAt,
          incoming.reviewStepsRevealedAt
        );
        if (maxIncomingRevSteps) {
          st.reviewStepsRevealedAt = maxIncomingRevSteps;
        }
        const maxIncomingRevHint = maxIsoTimestamp(
          st.reviewHintRevealedAt,
          incoming.reviewHintRevealedAt
        );
        if (maxIncomingRevHint) {
          st.reviewHintRevealedAt = maxIncomingRevHint;
        }
      } else {
        st = { ...incoming };

        const incomingCycle =
          typeof incoming.cycleStartedAt === "string" && incoming.cycleStartedAt.trim()
            ? incoming.cycleStartedAt.trim()
            : null;
        const prevCycle =
          typeof prev?.cycleStartedAt === "string" && prev.cycleStartedAt.trim()
            ? prev.cycleStartedAt.trim()
            : null;
        const isNewCycle = Boolean(incomingCycle && (!prevCycle || incomingCycle > prevCycle));
        const isSameCycle = Boolean(incomingCycle && prevCycle && incomingCycle === prevCycle);
        if (isNewCycle || isSameCycle) {
          const revealStamp = maxIsoTimestamp(nowIso, incomingCycle) || nowIso;
          const prevHints = typeof prev?.hintsRevealed === "number" ? prev.hintsRevealed : 0;
          const incomingHints =
            typeof incoming.hintsRevealed === "number" ? incoming.hintsRevealed : 0;
          if (
            incoming.setupRevealedBeforeAnswer === true &&
            (isNewCycle || prev?.setupRevealedBeforeAnswer !== true)
          ) {
            st.reviewSetupRevealedAt = maxIsoTimestamp(st.reviewSetupRevealedAt, revealStamp);
          }
          if (
            incoming.solutionRevealedBeforeAnswer === true &&
            (isNewCycle || prev?.solutionRevealedBeforeAnswer !== true)
          ) {
            st.reviewStepsRevealedAt = maxIsoTimestamp(st.reviewStepsRevealedAt, revealStamp);
          }
          if (incomingHints > 0 && (isNewCycle || incomingHints > prevHints)) {
            st.reviewHintRevealedAt = maxIsoTimestamp(st.reviewHintRevealedAt, revealStamp);
          }
        }

        if (prev) {
          // Server-owned history is never dropped by a normal autosave.
          const mergedAttempts = mergeAttempts(prev.attempts, st.attempts);
          if (mergedAttempts !== undefined) {
            st.attempts = mergedAttempts;
          }

          const mergedReviews = mergeReviews(prev.reviews, st.reviews);
          if (mergedReviews !== undefined) {
            st.reviews = mergedReviews;
          }

          const mergedTestRuns = mergeAttempts(prev.testRuns, st.testRuns);
          if (mergedTestRuns !== undefined) {
            st.testRuns = mergedTestRuns;
          }

          if (prev.lastTestReport && typeof prev.lastTestReport === "object") {
            if (st.lastTestReport == null) {
              if (!isNewCycle) {
                st.lastTestReport = prev.lastTestReport;
              }
            } else if (typeof st.lastTestReport === "object") {
              const prevRepTs = (prev.lastTestReport as Record<string, unknown>).ts;
              const nextRepTs = (st.lastTestReport as Record<string, unknown>).ts;
              if (
                typeof prevRepTs === "string" &&
                prevRepTs &&
                typeof nextRepTs === "string" &&
                nextRepTs &&
                prevRepTs > nextRepTs
              ) {
                st.lastTestReport = prev.lastTestReport;
              }
            }
          }

          for (const key of ["mistakes", "mistakeNote", "revisitNote"] as const) {
            if (isEmptyValue(st[key]) && !isEmptyValue(prev[key])) {
              st[key] = prev[key];
            }
          }

          const maxRevSetup = maxIsoTimestamp(prev.reviewSetupRevealedAt, st.reviewSetupRevealedAt);
          if (maxRevSetup) {
            st.reviewSetupRevealedAt = maxRevSetup;
          }
          const maxRevSteps = maxIsoTimestamp(prev.reviewStepsRevealedAt, st.reviewStepsRevealedAt);
          if (maxRevSteps) {
            st.reviewStepsRevealedAt = maxRevSteps;
          }
          const maxRevHint = maxIsoTimestamp(prev.reviewHintRevealedAt, st.reviewHintRevealedAt);
          if (maxRevHint) {
            st.reviewHintRevealedAt = maxRevHint;
          }
        }
      }

      // Server-authoritative variant session fields: client receives redacted state without variantId,
      // so preserve server-stored `variants`, `similarSlots`, `exampleViewedAt`, and derived lists.
      if (prev && prev.variants && typeof prev.variants === "object") {
        st.variants = prev.variants;
      } else if (st.variants && typeof st.variants === "object") {
        // Only keep incoming `variants` if it already has server variantIds (e.g., unit test fixtures).
        const entries = Object.values(st.variants as Record<string, Record<string, unknown>>);
        if (entries.length > 0 && entries.every((e) => !e || typeof e.variantId !== "string")) {
          delete st.variants;
        }
      }
      if (prev && Array.isArray(prev.similarSlots)) {
        st.similarSlots = prev.similarSlots;
      } else if (Array.isArray(st.similarSlots)) {
        // Only keep incoming similarSlots if variants were kept alongside them (e.g., test fixtures).
        if (!st.variants || typeof st.variants !== "object") {
          delete st.similarSlots;
        }
      }
      delete st.activeVariant;
      if (prev && typeof prev.exampleViewedAt === "string" && prev.exampleViewedAt) {
        st.exampleViewedAt = prev.exampleViewedAt;
      }
      const maxCycle = maxIsoTimestamp(prev?.cycleStartedAt, st.cycleStartedAt);
      if (maxCycle) {
        st.cycleStartedAt = maxCycle;
      }

      const derived = deriveVariantLists(
        st.variants as Record<string, VariantSessionRecord> | undefined,
        [
          ...(Array.isArray(prev?.variantsSeen) ? prev.variantsSeen : []),
          ...(Array.isArray(st.variantsSeen) ? st.variantsSeen : []),
        ],
        [
          ...(Array.isArray(prev?.variantsAttempted) ? prev.variantsAttempted : []),
          ...(Array.isArray(st.variantsAttempted) ? st.variantsAttempted : []),
        ]
      );
      if (derived.variantsSeen.length > 0) {
        st.variantsSeen = derived.variantsSeen;
      } else {
        delete st.variantsSeen;
      }
      if (derived.variantsAttempted.length > 0) {
        st.variantsAttempted = derived.variantsAttempted;
      } else {
        delete st.variantsAttempted;
      }

      problems[p.id] = st;
    }
  }
  const data: ProgressFile = {
    drillId: doc.drillId,
    unitCode: doc.unitCode || existing?.unitCode,
    updatedAt: nowIso,
    sessionSummary: mergeSessionSummary(existing?.sessionSummary, doc.sessionSummary, {
      allowSyncStampUpdate: options.allowSyncStampUpdate ?? true,
    }),
    problems,
  };
  const file = progressFile(doc.drillId);
  writeJsonAtomic(file, data);
  return file;
}

/**
 * Server-authoritative stamp write after a real (non-pilot, non-dry-run, non-degraded)
 * Notion sync succeeds. Reads the latest progress on disk so concurrent problem edits
 * made while Python ran are never overwritten, advances `syncedToNotionAt` monotonically,
 * and persists `syncedToNotionAt`, `notionPageId`, and `syncedFingerprint` atomically.
 */
export function stampSyncMetadata(
  drillId: string,
  stamp: {
    syncedToNotionAt?: string;
    notionPageId?: string | null;
    syncedFingerprint: string;
    unitCode?: string;
  }
): {
  progress: ProgressFile;
  syncedToNotionAt: string;
  notionPageId: string | null;
  syncedFingerprint: string;
} {
  if (!drillId || !isSafeId(drillId)) throw new Error("Invalid drillId");
  const existing = readProgress(drillId);
  const prevSyncedAt = nonEmptyString(existing?.sessionSummary?.syncedToNotionAt);
  let effectiveSyncedAt = nonEmptyString(stamp.syncedToNotionAt) || new Date().toISOString();
  if (prevSyncedAt && effectiveSyncedAt <= prevSyncedAt) {
    const prevMs = Date.parse(prevSyncedAt);
    effectiveSyncedAt = Number.isFinite(prevMs)
      ? new Date(prevMs + 1).toISOString()
      : new Date().toISOString();
  }
  const effectivePageId =
    nonEmptyString(stamp.notionPageId) ??
    nonEmptyString(existing?.sessionSummary?.notionPageId) ??
    null;
  const effectiveFingerprint = stamp.syncedFingerprint || "";

  const nextSummary = mergeSessionSummary(
    existing?.sessionSummary,
    {
      syncedToNotionAt: effectiveSyncedAt,
      ...(effectivePageId ? { notionPageId: effectivePageId } : {}),
      ...(effectiveFingerprint ? { syncedFingerprint: effectiveFingerprint } : {}),
    },
    { allowSyncStampUpdate: true }
  );

  const data: ProgressFile = {
    drillId,
    unitCode: existing?.unitCode || stamp.unitCode,
    updatedAt: effectiveSyncedAt,
    sessionSummary: nextSummary,
    problems: existing?.problems || {},
  };
  const file = progressFile(drillId);
  writeJsonAtomic(file, data);
  return {
    progress: data,
    syncedToNotionAt: effectiveSyncedAt,
    notionPageId: effectivePageId,
    syncedFingerprint:
      nonEmptyString(nextSummary.syncedFingerprint) || effectiveFingerprint,
  };
}

function mutateProblemVariantState(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  mutator: (state: ProblemState) => void
): ProblemState {
  if (!isSafeId(drillId) || !isSafeId(qid)) {
    throw new Error("Invalid drillId or qid");
  }
  const existing = readProgress(drillId);
  const problems = {
    ...((existing?.problems || {}) as Record<string, Partial<ProblemState>>),
  };
  const nextState: ProblemState = {
    userInput: "",
    score: null,
    divergedStep: null,
    mistakes: [],
    ...(problems[qid] || {}),
  };
  if (nextState.variants) {
    nextState.variants = { ...nextState.variants };
  }
  mutator(nextState);

  const derived = deriveVariantLists(
    nextState.variants,
    nextState.variantsSeen,
    nextState.variantsAttempted
  );
  if (derived.variantsSeen.length > 0) {
    nextState.variantsSeen = derived.variantsSeen;
  } else {
    delete nextState.variantsSeen;
  }
  if (derived.variantsAttempted.length > 0) {
    nextState.variantsAttempted = derived.variantsAttempted;
  } else {
    delete nextState.variantsAttempted;
  }

  problems[qid] = nextState;

  const data: ProgressFile = {
    drillId,
    unitCode: unitCode || existing?.unitCode,
    updatedAt: new Date().toISOString(),
    sessionSummary: existing?.sessionSummary || {},
    problems,
  };
  const file = progressFile(drillId);
  writeJsonAtomic(file, data);
  return nextState;
}

/**
 * Allocate (or lazily migrate from v1) up to 3 stable opaque `similarSlots` tokens
 * in bank order for `(drillId, qid)`. Preserves existing v1 `role:"try"` tokens and
 * `role:"example"` records, and deletes legacy `activeVariant`.
 */
export function allocateSimilarSlots(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  bankVariants: Array<Record<string, unknown>>
): { slots: string[]; state: ProblemState } {
  const existingProgress = readProgress(drillId);
  const existingState = (existingProgress?.problems?.[qid] as ProblemState | undefined) ?? null;
  const hasLegacyActive =
    existingState != null &&
    Object.prototype.hasOwnProperty.call(existingState, "activeVariant");

  if (
    existingState &&
    Array.isArray(existingState.similarSlots) &&
    existingState.similarSlots.length > 0 &&
    existingState.variants &&
    existingState.similarSlots.every(
      (tok) =>
        typeof tok === "string" &&
        tok.length > 0 &&
        Boolean(existingState.variants?.[tok]?.variantId)
    ) &&
    !hasLegacyActive
  ) {
    return {
      slots: existingState.similarSlots.slice(0, MAX_SIMILAR_TABS),
      state: existingState,
    };
  }

  const targetVariants = bankVariants
    .filter((v) => typeof v.variantId === "string" && isSafeId(v.variantId))
    .slice(0, MAX_SIMILAR_TABS);

  let assignedSlots: string[] = [];
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    const variants: Record<string, VariantSessionRecord> = st.variants
      ? { ...st.variants }
      : {};

    // Map existing role:"try" tokens by variantId so v1 tokens stay valid in bank order.
    const tryTokenByVariantId = new Map<string, string>();
    for (const [tok, rec] of Object.entries(variants)) {
      if (
        rec &&
        rec.role === "try" &&
        typeof rec.variantId === "string" &&
        rec.variantId &&
        !tryTokenByVariantId.has(rec.variantId)
      ) {
        tryTokenByVariantId.set(rec.variantId, tok);
      }
    }

    const slots: string[] = [];
    for (const v of targetVariants) {
      const vid = String(v.variantId);
      const existingTok = tryTokenByVariantId.get(vid);
      if (existingTok) {
        slots.push(existingTok);
      } else {
        const tok = generateVariantToken(variants);
        variants[tok] = {
          variantId: vid,
          role: "try",
          attempts: [],
          hintsRevealed: 0,
          setupRevealed: false,
          stepsRevealed: false,
          durationMs: 0,
          servedAt: "",
        };
        slots.push(tok);
      }
    }

    st.variants = variants;
    st.similarSlots = slots;
    delete (st as unknown as Record<string, unknown>).activeVariant;
    assignedSlots = slots;
  });

  return { slots: assignedSlots, state };
}

/**
 * Start a new attempt cycle for `(drillId, qid)` by stamping `cycleStartedAt`
 * (keeping the later timestamp if one already exists) without erasing attempt
 * history, notes, tags, or variant records.
 */
export function startProblemCycle(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  cycleStartedAt: string = new Date().toISOString()
): { cycleStartedAt: string; state: ProblemState } {
  const safeTs =
    typeof cycleStartedAt === "string" && cycleStartedAt.trim()
      ? cycleStartedAt.trim()
      : new Date().toISOString();
  let effectiveCycle = safeTs;
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    const prevCycle =
      typeof st.cycleStartedAt === "string" && st.cycleStartedAt
        ? st.cycleStartedAt
        : null;
    effectiveCycle = prevCycle && prevCycle > safeTs ? prevCycle : safeTs;
    st.cycleStartedAt = effectiveCycle;
  });
  return { cycleStartedAt: effectiveCycle, state };
}

/** Mark `servedAt` on the first open of a similar-tab token in the current cycle. */
export function markVariantServed(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  token: string,
  nowIso: string = new Date().toISOString()
): { record: VariantSessionRecord | null; state: ProblemState } {
  const existing = resolveVariantToken(drillId, qid, token);
  if (
    existing &&
    existing.record.servedAt &&
    (!existing.state.cycleStartedAt ||
      existing.record.servedAt >= existing.state.cycleStartedAt)
  ) {
    return existing;
  }
  let updatedRecord: VariantSessionRecord | null = null;
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    if (!st.variants || !st.variants[token]) return;
    const prev = st.variants[token];
    const inCurrentCycle = Boolean(
      prev.servedAt && (!st.cycleStartedAt || prev.servedAt >= st.cycleStartedAt)
    );
    const nextRec: VariantSessionRecord = inCurrentCycle
      ? prev
      : {
          ...prev,
          // New cycle: keep attempt history (filtered by cycleStartedAt) but reset per-cycle UI telemetry.
          hintsRevealed: 0,
          setupRevealed: false,
          stepsRevealed: false,
          durationMs: 0,
          servedAt: nowIso,
        };
    st.variants = { ...st.variants, [token]: nextRec };
    updatedRecord = nextRec;
  });
  return { record: updatedRecord, state };
}

/** Add elapsed time (ms) to a similar tab's server-stored `durationMs` when leaving the tab. */
export function addVariantDuration(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  token: string,
  durationMs: number
): { record: VariantSessionRecord | null; state: ProblemState } {
  const safeDuration =
    typeof durationMs === "number" && Number.isFinite(durationMs) && durationMs > 0
      ? Math.min(Math.round(durationMs), 600_000)
      : 0;
  let updatedRecord: VariantSessionRecord | null = null;
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    if (!st.variants || !st.variants[token]) return;
    const prev = st.variants[token];
    const nextRec: VariantSessionRecord = {
      ...prev,
      durationMs: (prev.durationMs || 0) + safeDuration,
    };
    st.variants = { ...st.variants, [token]: nextRec };
    updatedRecord = nextRec;
  });
  return { record: updatedRecord, state };
}

/**
 * Allocate an opaque per-problem token for a served bank variant (used by `mode=example`),
 * persist `variants[token]`, and update `exampleViewedAt`.
 */
export function registerServedVariant(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  variantId: string,
  role: "try" | "example",
  nowIso: string = new Date().toISOString()
): { token: string; state: ProblemState } {
  if (!isSafeId(variantId)) {
    throw new Error("Invalid variantId");
  }
  let assignedToken = "";
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    const variants = st.variants ? { ...st.variants } : {};
    assignedToken = generateVariantToken(variants);
    variants[assignedToken] = {
      variantId,
      role,
      attempts: [],
      hintsRevealed: 0,
      setupRevealed: false,
      stepsRevealed: false,
      durationMs: 0,
      servedAt: nowIso,
    };
    st.variants = variants;
    if (role === "example") {
      if (!st.exampleViewedAt || (st.cycleStartedAt && st.exampleViewedAt < st.cycleStartedAt)) {
        st.exampleViewedAt = nowIso;
      }
    }
  });
  return { token: assignedToken, state };
}

/** Resolve an opaque `variantToken` for `(drillId, qid)` on the server. */
export function resolveVariantToken(
  drillId: string,
  qid: string,
  token: string
): { record: VariantSessionRecord; state: ProblemState } | null {
  if (!isSafeId(drillId) || !isSafeId(qid) || !isSafeId(token)) return null;
  const progress = readProgress(drillId);
  const state = (progress?.problems?.[qid] as ProblemState | undefined) ?? null;
  if (!state?.variants || typeof state.variants !== "object") return null;
  const record = state.variants[token];
  if (!record || typeof record !== "object" || typeof record.variantId !== "string" || !record.variantId) {
    return null;
  }
  return { record, state };
}

/** Append a `kind: "variant"` attempt to `variants[token]` without touching the review schedule. */
export function recordVariantAttempt(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  token: string,
  attempt: AttemptRecord,
  durationMs?: number
): { record: VariantSessionRecord; state: ProblemState } | null {
  let updatedRecord: VariantSessionRecord | null = null;
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    if (!st.variants || !st.variants[token]) return;
    const prev = st.variants[token];
    const safeDuration =
      typeof durationMs === "number" && Number.isFinite(durationMs) && durationMs > 0
        ? Math.min(Math.round(durationMs), 600_000)
        : 0;
    const prevInCycle = Boolean(
      !st.cycleStartedAt || (prev.servedAt && prev.servedAt >= st.cycleStartedAt)
    );
    const entry: AttemptRecord = {
      ...attempt,
      kind: "variant",
      ...(prevInCycle && prev.setupRevealed ? { setupRevealed: true } : {}),
      ...(prevInCycle && prev.stepsRevealed ? { solutionRevealed: true } : {}),
    };
    const nextRec: VariantSessionRecord = {
      ...prev,
      attempts: [...(Array.isArray(prev.attempts) ? prev.attempts : []), entry],
      ...(prevInCycle
        ? { durationMs: (prev.durationMs || 0) + safeDuration }
        : {
            hintsRevealed: 0,
            setupRevealed: false,
            stepsRevealed: false,
            durationMs: safeDuration,
            servedAt: attempt.ts || new Date().toISOString(),
          }),
    };
    st.variants = { ...st.variants, [token]: nextRec };
    updatedRecord = nextRec;
  });
  return updatedRecord ? { record: updatedRecord, state } : null;
}

/** Update variant session telemetry flags (`hint`, `setupRevealed`, `stepsRevealed`, `reset`). */
export function updateVariantSession(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  token: string,
  patch: {
    hintIncrement?: number;
    setupRevealed?: boolean;
    stepsRevealed?: boolean;
    reset?: boolean;
  }
): { record: VariantSessionRecord | null; state: ProblemState } {
  let updatedRecord: VariantSessionRecord | null = null;
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    if (!st.variants || !st.variants[token]) return;
    const prev = st.variants[token];
    let nextRec: VariantSessionRecord = { ...prev };
    if (patch.reset) {
      nextRec = {
        ...prev,
        attempts: [],
        hintsRevealed: 0,
        setupRevealed: false,
        stepsRevealed: false,
        durationMs: 0,
      };
    } else {
      if (st.cycleStartedAt && (!prev.servedAt || prev.servedAt < st.cycleStartedAt)) {
        nextRec = {
          ...prev,
          hintsRevealed: 0,
          setupRevealed: false,
          stepsRevealed: false,
          durationMs: 0,
          servedAt: new Date().toISOString(),
        };
      }
      if (typeof patch.hintIncrement === "number" && patch.hintIncrement > 0) {
        nextRec.hintsRevealed = (nextRec.hintsRevealed || 0) + patch.hintIncrement;
      }
      if (patch.setupRevealed) {
        nextRec.setupRevealed = true;
      }
      if (patch.stepsRevealed) {
        nextRec.stepsRevealed = true;
      }
    }
    st.variants = { ...st.variants, [token]: nextRec };
    updatedRecord = nextRec;
  });
  return { record: updatedRecord, state };
}

/** Clear server-owned variant UI state for one or every problem in a drill. */
export function resetVariantProgress(
  drillId: string,
  unitCode: string | undefined,
  qid?: string
): void {
  if (!isSafeId(drillId) || (qid !== undefined && !isSafeId(qid))) {
    throw new Error("Invalid drillId or qid");
  }
  const existing = readProgress(drillId);
  if (!existing) return;
  const problems = { ...(existing.problems || {}) } as Record<string, Record<string, unknown>>;
  const ids = qid ? [qid] : Object.keys(problems);
  for (const id of ids) {
    const state = { ...(problems[id] || {}) };
    delete state.variants;
    delete state.similarSlots;
    delete state.activeVariant;
    delete state.exampleViewedAt;
    delete state.cycleStartedAt;
    delete state.variantsSeen;
    delete state.variantsAttempted;
    problems[id] = state;
  }
  const file = progressFile(drillId);
  writeJsonAtomic(file, {
    ...existing,
    unitCode: unitCode || existing.unitCode,
    updatedAt: new Date().toISOString(),
    problems,
  });
}
