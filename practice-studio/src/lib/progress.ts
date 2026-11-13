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
  const problems: Record<string, unknown> = {};
  for (const p of doc.problems || []) {
    if (p.id && p.state) problems[p.id] = p.state;
  }
  const data: ProgressFile = {
    drillId: doc.drillId,
    unitCode: doc.unitCode,
    updatedAt: new Date().toISOString(),
    sessionSummary: (doc.sessionSummary as Record<string, unknown>) || {},
    problems,
  };
  const file = progressFile(doc.drillId);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2), "utf-8");
  return file;
}
