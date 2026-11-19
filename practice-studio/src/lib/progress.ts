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
      problems[p.id] = st;
    } else if (prev && (prev.reviews !== undefined || typeof prev.revisitNote === "string")) {
      const preserved: Record<string, unknown> = {};
      if (prev.reviews !== undefined) preserved.reviews = prev.reviews;
      if (typeof prev.revisitNote === "string") preserved.revisitNote = prev.revisitNote;
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
