import fs from "fs";
import path from "path";
import { getProgressDir, isSafeId } from "@/lib/paths";
import { isSubstantiveVerdict } from "@/lib/reviewGuard";
import { allocateNextVariantToken } from "@/lib/variants";
import { AttemptRecord, ProblemState, VariantSessionRecord } from "@/types/drill";

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
      seen.add(rec.variantId);
      if (
        Array.isArray(rec.attempts) &&
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

      // Server-authoritative variant session fields: client receives redacted state without variantId,
      // so preserve server-stored `variants`, `activeVariant`, `exampleViewedAt`, and derived lists.
      if (prev && prev.variants && typeof prev.variants === "object") {
        st.variants = prev.variants;
      } else if (st.variants && typeof st.variants === "object") {
        // Only keep incoming `variants` if it already has server variantIds (e.g., unit test fixtures).
        const entries = Object.values(st.variants as Record<string, Record<string, unknown>>);
        if (entries.length > 0 && entries.every((e) => !e || typeof e.variantId !== "string")) {
          delete st.variants;
        }
      }
      if (prev && prev.activeVariant !== undefined) {
        st.activeVariant = prev.activeVariant;
      }
      if (prev && typeof prev.exampleViewedAt === "string" && prev.exampleViewedAt) {
        st.exampleViewedAt = prev.exampleViewedAt;
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
    } else if (
      prev &&
      (prev.reviews !== undefined ||
        typeof prev.revisitNote === "string" ||
        prev.variants !== undefined ||
        prev.activeVariant !== undefined ||
        typeof prev.exampleViewedAt === "string" ||
        Array.isArray(prev.variantsSeen) ||
        Array.isArray(prev.variantsAttempted))
    ) {
      const preserved: Record<string, unknown> = {};
      if (prev.reviews !== undefined) preserved.reviews = prev.reviews;
      if (typeof prev.revisitNote === "string") preserved.revisitNote = prev.revisitNote;
      if (prev.variants !== undefined) preserved.variants = prev.variants;
      if (prev.activeVariant !== undefined) preserved.activeVariant = prev.activeVariant;
      if (typeof prev.exampleViewedAt === "string") preserved.exampleViewedAt = prev.exampleViewedAt;
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
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2), "utf-8");
  return nextState;
}

/**
 * Allocate an opaque per-problem token ("v1", "v2", ...) for a served bank variant,
 * persist `variants[token]` (with `role: "try" | "example"`), update `activeVariant`
 * or `exampleViewedAt`, and always mark `variantId` seen so examples never return as tries.
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
  let assignedToken = "v1";
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    const variants = st.variants ? { ...st.variants } : {};
    assignedToken = allocateNextVariantToken(variants);
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
    if (role === "try") {
      st.activeVariant = assignedToken;
    } else if (!st.exampleViewedAt) {
      st.exampleViewedAt = nowIso;
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
    const entry: AttemptRecord = {
      ...attempt,
      kind: "variant",
      ...(prev.setupRevealed ? { setupRevealed: true } : {}),
      ...(prev.stepsRevealed ? { solutionRevealed: true } : {}),
    };
    const nextRec: VariantSessionRecord = {
      ...prev,
      attempts: [...(Array.isArray(prev.attempts) ? prev.attempts : []), entry],
      durationMs: (prev.durationMs || 0) + safeDuration,
    };
    st.variants = { ...st.variants, [token]: nextRec };
    updatedRecord = nextRec;
  });
  return updatedRecord ? { record: updatedRecord, state } : null;
}

/** Update variant session telemetry flags (`hint`, `setupRevealed`, `stepsRevealed`, `reset`, `deactivate`). */
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
    deactivate?: boolean;
  }
): { record: VariantSessionRecord | null; state: ProblemState } {
  let updatedRecord: VariantSessionRecord | null = null;
  const state = mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    if (patch.deactivate && st.activeVariant === token) {
      st.activeVariant = null;
    }
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
  let result: string[] = [];
  mutateProblemVariantState(drillId, unitCode, qid, (st) => {
    const prevList = Array.isArray(st[field])
      ? st[field]!.filter((x): x is string => typeof x === "string")
      : [];
    const nextList = prevList.includes(variantId) ? prevList : [...prevList, variantId];
    st[field] = nextList;
    result = nextList;
  });
  return result;
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
