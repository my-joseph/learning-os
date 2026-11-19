import fs from "fs";
import path from "path";
import { getProgressDir, isSafeId } from "@/lib/paths";

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

/** Save only the learner-owned part of a document; never touches drill content. */
export function writeProgress(doc: DocLike): string {
  if (!doc.drillId || !isSafeId(doc.drillId)) throw new Error("Invalid drillId");
  const existing = readProgress(doc.drillId);
  const existingProblems = (existing?.problems || {}) as Record<string, Record<string, unknown>>;
  const problems: Record<string, unknown> = doc.reviewMerge ? { ...existingProblems } : {};
  for (const p of doc.problems || []) {
    if (!p.id) continue;
    const prev = existingProblems[p.id];
    if (p.state) {
      const st = { ...(p.state as Record<string, unknown>) };
      if (doc.reviewMerge && prev && Array.isArray(prev.attempts)) {
        const prevAttempts = prev.attempts as Array<Record<string, unknown>>;
        const nextAttempts = Array.isArray(st.attempts)
          ? (st.attempts as Array<Record<string, unknown>>)
          : [];
        const seenTs = new Set(
          prevAttempts
            .map((a) => (a && typeof a.ts === "string" ? a.ts : ""))
            .filter(Boolean)
        );
        const appended = nextAttempts.filter(
          (a) => !a || typeof a.ts !== "string" || !seenTs.has(a.ts)
        );
        st.attempts = [...prevAttempts, ...appended];
      }
      if (doc.reviewMerge && prev) {
        // A review session starts from a clean state; never erase learner notes/tags it did not set.
        const isEmpty = (v: unknown) =>
          v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
        for (const key of ["mistakes", "mistakeNote", "revisitNote"] as const) {
          if (isEmpty(st[key]) && !isEmpty(prev[key])) {
            st[key] = prev[key];
          }
        }
      }
      if (st.reviews === undefined && prev && prev.reviews !== undefined) {
        st.reviews = prev.reviews;
      }
      if (st.revisitNote === undefined && prev && typeof prev.revisitNote === "string") {
        st.revisitNote = prev.revisitNote;
      }
      for (const variantKey of ["variantsSeen", "variantsAttempted"] as const) {
        const prevList =
          prev && Array.isArray(prev[variantKey])
            ? (prev[variantKey] as unknown[]).filter((x): x is string => typeof x === "string")
            : [];
        const nextList = Array.isArray(st[variantKey])
          ? (st[variantKey] as unknown[]).filter((x): x is string => typeof x === "string")
          : [];
        if (prevList.length > 0 || nextList.length > 0) {
          st[variantKey] = Array.from(new Set([...prevList, ...nextList]));
        }
      }
      problems[p.id] = st;
    } else if (
      prev &&
      (prev.reviews !== undefined ||
        typeof prev.revisitNote === "string" ||
        Array.isArray(prev.variantsSeen) ||
        Array.isArray(prev.variantsAttempted))
    ) {
      const preserved: Record<string, unknown> = {};
      if (prev.reviews !== undefined) preserved.reviews = prev.reviews;
      if (typeof prev.revisitNote === "string") preserved.revisitNote = prev.revisitNote;
      if (Array.isArray(prev.variantsSeen)) preserved.variantsSeen = prev.variantsSeen;
      if (Array.isArray(prev.variantsAttempted)) preserved.variantsAttempted = prev.variantsAttempted;
      problems[p.id] = preserved;
    }
  }
  const data: ProgressFile = {
    drillId: doc.drillId,
    unitCode: doc.unitCode || existing?.unitCode,
    updatedAt: new Date().toISOString(),
    sessionSummary:
      (doc.sessionSummary as Record<string, unknown>) ||
      (doc.reviewMerge ? existing?.sessionSummary : undefined) ||
      {},
    problems,
  };
  const file = progressFile(doc.drillId);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2), "utf-8");
  return file;
}

function appendVariantTrackingField(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  field: "variantsSeen" | "variantsAttempted",
  variantId: string
): string[] {
  if (!isSafeId(drillId) || !isSafeId(qid) || !isSafeId(variantId)) {
    throw new Error("Invalid drillId, qid, or variantId");
  }
  const existing = readProgress(drillId);
  const problems = { ...((existing?.problems || {}) as Record<string, Record<string, unknown>>) };
  const prevState = { ...(problems[qid] || {}) };
  const prevList = Array.isArray(prevState[field])
    ? (prevState[field] as unknown[]).filter((x): x is string => typeof x === "string")
    : [];
  const nextList = prevList.includes(variantId) ? prevList : [...prevList, variantId];
  prevState[field] = nextList;
  problems[qid] = prevState;

  const data: ProgressFile = {
    drillId,
    unitCode: unitCode || existing?.unitCode,
    updatedAt: new Date().toISOString(),
    sessionSummary: existing?.sessionSummary || {},
    problems,
  };
  const file = progressFile(drillId);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2), "utf-8");
  return nextList;
}

/** Record that `variantId` was served to the learner for `(drillId, qid)` in `progress/<DRILL_ID>.json`. */
export function recordVariantSeen(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  variantId: string
): string[] {
  return appendVariantTrackingField(drillId, unitCode, qid, "variantsSeen", variantId);
}

/** Record that the learner submitted a substantive attempt on `variantId` for `(drillId, qid)`. */
export function recordVariantAttempted(
  drillId: string,
  unitCode: string | undefined,
  qid: string,
  variantId: string
): string[] {
  return appendVariantTrackingField(drillId, unitCode, qid, "variantsAttempted", variantId);
}
