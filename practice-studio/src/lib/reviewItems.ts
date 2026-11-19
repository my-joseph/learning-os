import fs from "fs";
import path from "path";
import { formatLocalDate } from "@/lib/dueToday";
import {
  getDrillsDataDir,
  getLabsDir,
  getProgressDir,
  getWorkspaceRoot,
  isSafeId,
} from "@/lib/paths";

/**
 * Per-item review schedule (mirrors `scripts/review_items.py`):
 * - 5 levels with intervals 1, 3, 7, 16, 35 days
 * - correct without hint -> level + 1 (max 5), due in INTERVALS[newLevel] days
 * - correct with hints/assisted -> same level, due in INTERVALS[level] days
 * - wrong -> level halved (floor, min 1), due next day (+1 day)
 * - persisted to `progress/review_items.json` (`pilot/progress/review_items.json` in pilot mode)
 */

export const REVIEW_INTERVALS: Record<number, number> = {
  1: 1,
  2: 3,
  3: 7,
  4: 16,
  5: 35,
};

export const MIN_REVIEW_LEVEL = 1;
export const MAX_REVIEW_LEVEL = 5;

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const NON_SUBSTANTIVE_VERDICTS = new Set(["invalid input", "parse_error"]);

export interface ReviewItem {
  drillId: string;
  qid: string;
  unitCode: string;
  subject: "MTH" | "PRG";
  commonTrapTag: string | null;
  archetypeKey: string | null;
  level: number;
  lastReviewed: string;
  dueDate: string;
  revisitNote: string | null;
}

export interface ReviewEvent {
  date: string;
  correct: boolean;
  assisted: boolean;
}

export interface ReviewStoreOptions {
  today?: string;
  limit?: number;
  dataDir?: string;
  progressDir?: string;
  labsDir?: string;
  rootDir?: string;
}

export function reviewItemKey(drillId: string, qid: string): string {
  return `${drillId}/${qid}`;
}

export function normalizeReviewDate(raw?: string | null, fallback?: string | null): string {
  const cand = typeof raw === "string" ? raw.trim().slice(0, 10) : "";
  if (DATE_RE.test(cand)) return cand;
  const fb = typeof fallback === "string" ? fallback.trim().slice(0, 10) : "";
  if (DATE_RE.test(fb)) return fb;
  return formatLocalDate();
}

export function addDays(dateStr: string, days: number): string {
  const norm = normalizeReviewDate(dateStr);
  const [y, m, d] = norm.split("-").map((x) => parseInt(x, 10));
  const utc = new Date(Date.UTC(y, m - 1, d + Math.trunc(days)));
  const yy = utc.getUTCFullYear();
  const mm = String(utc.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(utc.getUTCDate()).padStart(2, "0");
  return `${yy}-${mm}-${dd}`;
}

export function clampReviewLevel(level: unknown): number {
  if (typeof level !== "number" || Number.isNaN(level)) return MIN_REVIEW_LEVEL;
  return Math.max(MIN_REVIEW_LEVEL, Math.min(MAX_REVIEW_LEVEL, Math.trunc(level)));
}

export function stepReviewSchedule(
  currentLevel: number,
  outcome: {
    correct: boolean;
    hintsUsed?: boolean | number;
    date: string;
  }
): { level: number; lastReviewed: string; dueDate: string } {
  const lvl = clampReviewLevel(currentLevel);
  const revDate = normalizeReviewDate(outcome.date);
  const assisted =
    typeof outcome.hintsUsed === "number"
      ? outcome.hintsUsed > 0
      : Boolean(outcome.hintsUsed);

  if (outcome.correct && !assisted) {
    const nextLevel = Math.min(MAX_REVIEW_LEVEL, lvl + 1);
    return {
      level: nextLevel,
      lastReviewed: revDate,
      dueDate: addDays(revDate, REVIEW_INTERVALS[nextLevel]),
    };
  }
  if (outcome.correct && assisted) {
    return {
      level: lvl,
      lastReviewed: revDate,
      dueDate: addDays(revDate, REVIEW_INTERVALS[lvl]),
    };
  }
  const nextLevel = Math.max(MIN_REVIEW_LEVEL, Math.floor(lvl / 2));
  return {
    level: nextLevel,
    lastReviewed: revDate,
    dueDate: addDays(revDate, 1),
  };
}

export function extractReviewEvents(
  state: Record<string, unknown> | null | undefined,
  fallbackTs: string = ""
): ReviewEvent[] {
  if (!state || typeof state !== "object") return [];
  const fallbackDate = normalizeReviewDate(fallbackTs);
  const stateAssisted = Boolean(
    state.setupRevealedBeforeAnswer ||
      state.solutionRevealedBeforeAnswer ||
      (typeof state.hintsRevealed === "number" && state.hintsRevealed > 0)
  );

  const rawAttempts = Array.isArray(state.attempts)
    ? (state.attempts as Array<Record<string, unknown>>)
    : [];
  const substantive = rawAttempts.filter(
    (a) =>
      a &&
      typeof a === "object" &&
      !NON_SUBSTANTIVE_VERDICTS.has(String(a.verdict || ""))
  );

  if (substantive.length > 0) {
    const singleHalfScore =
      substantive.length === 1 &&
      substantive[0]?.verdict === "correct" &&
      state.score === 0.5;
    return substantive.map((att) => {
      const evDate = normalizeReviewDate(
        typeof att.ts === "string" ? att.ts : "",
        fallbackDate
      );
      const verdict = String(att.verdict || "");
      const correct = verdict === "correct";
      const hasExplicitHint =
        "hintsUsed" in att || "assisted" in att || "hintsRevealed" in att;
      const attRevealed = Boolean(att.setupRevealed || att.solutionRevealed);
      let assisted: boolean;
      if (hasExplicitHint) {
        assisted = Boolean(
          att.hintsUsed ||
            att.assisted ||
            (typeof att.hintsRevealed === "number" && att.hintsRevealed > 0) ||
            attRevealed
        );
      } else {
        assisted = stateAssisted || attRevealed || singleHalfScore;
      }
      return { date: evDate, correct, assisted };
    });
  }

  const rawReviews = Array.isArray(state.reviews)
    ? (state.reviews as Array<Record<string, unknown>>)
    : [];
  const validReviews = rawReviews.filter(
    (r) => r && typeof r === "object" && typeof r.verdict === "string" && r.verdict
  );
  if (validReviews.length > 0) {
    return validReviews.map((rev) => {
      const evDate = normalizeReviewDate(
        typeof rev.at === "string" ? rev.at : "",
        fallbackDate
      );
      const correct = rev.verdict === "pass";
      const hasExplicitHint =
        "hintsUsed" in rev || "assisted" in rev || "hintsRevealed" in rev;
      const assisted = hasExplicitHint
        ? Boolean(
            rev.hintsUsed ||
              rev.assisted ||
              (typeof rev.hintsRevealed === "number" && rev.hintsRevealed > 0)
          )
        : stateAssisted;
      return { date: evDate, correct, assisted };
    });
  }

  if (state.skipped) {
    return [{ date: fallbackDate, correct: false, assisted: stateAssisted }];
  }

  const lastCheck = state.lastCheck as Record<string, unknown> | null | undefined;
  if (
    lastCheck &&
    typeof lastCheck === "object" &&
    typeof lastCheck.verdict === "string" &&
    lastCheck.verdict &&
    !NON_SUBSTANTIVE_VERDICTS.has(lastCheck.verdict)
  ) {
    const correct = lastCheck.verdict === "correct";
    const assisted = stateAssisted || (correct && state.score === 0.5);
    return [{ date: fallbackDate, correct, assisted }];
  }

  if (typeof state.score === "number" && !Number.isNaN(state.score)) {
    const correct = state.score > 0;
    const assisted = stateAssisted || (state.score > 0 && state.score < 1.0);
    return [{ date: fallbackDate, correct, assisted }];
  }

  return [];
}

export function replayReviewEvents(
  events: ReviewEvent[]
): { level: number; lastReviewed: string; dueDate: string } | null {
  if (!Array.isArray(events) || events.length === 0) return null;
  let level = MIN_REVIEW_LEVEL;
  let lastReviewed = "";
  let dueDate = "";
  let lastWrongDate: string | null = null;

  for (const ev of events) {
    const evDate = normalizeReviewDate(ev.date);
    const correct = Boolean(ev.correct);
    const assisted = Boolean(ev.assisted);
    if (!correct) {
      const step = stepReviewSchedule(level, {
        correct: false,
        hintsUsed: assisted,
        date: evDate,
      });
      level = step.level;
      lastReviewed = step.lastReviewed;
      dueDate = step.dueDate;
      lastWrongDate = evDate;
    } else if (lastWrongDate === evDate) {
      lastReviewed = evDate;
    } else {
      const step = stepReviewSchedule(level, {
        correct: true,
        hintsUsed: assisted,
        date: evDate,
      });
      level = step.level;
      lastReviewed = step.lastReviewed;
      dueDate = step.dueDate;
    }
  }

  return { level, lastReviewed, dueDate };
}

function cleanRevisitNote(raw: unknown): string | null {
  if (typeof raw === "string" && raw.trim()) {
    return raw.trim();
  }
  return null;
}

/**
 * Redact a review item so only schedule & identification metadata (+ revisitNote) can leave the server.
 * Never includes answers, steps, display, solutionCode, or answerSpec.
 */
export function redactReviewItem(
  raw: Partial<ReviewItem> | Record<string, unknown>
): ReviewItem {
  const rec = raw as Record<string, unknown>;
  const subj = String(rec.subject || "").toUpperCase() === "PRG" ? "PRG" : "MTH";
  const unitCode =
    typeof rec.unitCode === "string" && rec.unitCode
      ? rec.unitCode
      : typeof rec.unit === "string"
      ? rec.unit
      : "";
  return {
    drillId: typeof rec.drillId === "string" ? rec.drillId : "",
    qid: typeof rec.qid === "string" ? rec.qid : "",
    unitCode,
    subject: subj,
    commonTrapTag:
      typeof rec.commonTrapTag === "string" && rec.commonTrapTag ? rec.commonTrapTag : null,
    archetypeKey:
      typeof rec.archetypeKey === "string" && rec.archetypeKey ? rec.archetypeKey : null,
    level: clampReviewLevel(rec.level),
    lastReviewed: normalizeReviewDate(
      typeof rec.lastReviewed === "string" ? rec.lastReviewed : undefined
    ),
    dueDate: normalizeReviewDate(
      typeof rec.dueDate === "string" ? rec.dueDate : undefined
    ),
    revisitNote: cleanRevisitNote(rec.revisitNote),
  };
}

function cmpStr(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

function compareBaseOrder(a: ReviewItem, b: ReviewItem): number {
  if (a.dueDate !== b.dueDate) return cmpStr(a.dueDate, b.dueDate);
  if (a.level !== b.level) return a.level - b.level;
  if (a.unitCode !== b.unitCode) return cmpStr(a.unitCode, b.unitCode);
  if (a.drillId !== b.drillId) return cmpStr(a.drillId, b.drillId);
  return cmpStr(a.qid, b.qid);
}

/**
 * Interleave due items so no two consecutive items come from the same unit when avoidable,
 * mixing MTH and PRG subjects (deterministic parity with `scripts.review_items.interleave_due_items`).
 */
export function interleaveDueItems(items: ReviewItem[], limit?: number): ReviewItem[] {
  const remaining = items.map((it) => redactReviewItem(it));
  remaining.sort(compareBaseOrder);

  const result: ReviewItem[] = [];
  let lastUnit: string | null = null;
  let lastSubject: "MTH" | "PRG" | null = null;

  while (remaining.length > 0) {
    const unitCounts = new Map<string, number>();
    for (const it of remaining) {
      unitCounts.set(it.unitCode, (unitCounts.get(it.unitCode) || 0) + 1);
    }
    const total = remaining.length;

    const diffUnit = remaining.filter((it) => it.unitCode !== lastUnit);
    let pool = diffUnit.length > 0 ? diffUnit : remaining;

    let maxCount = 0;
    for (const it of pool) {
      const c = unitCounts.get(it.unitCode) || 0;
      if (c > maxCount) maxCount = c;
    }
    if (maxCount > Math.floor(total / 2)) {
      pool = pool.filter((it) => (unitCounts.get(it.unitCode) || 0) === maxCount);
    }

    if (lastSubject !== null) {
      const diffSubj = pool.filter((it) => it.subject !== lastSubject);
      if (diffSubj.length > 0) {
        pool = diffSubj;
      }
    }

    let chosen = pool[0];
    for (let i = 1; i < pool.length; i += 1) {
      const cand = pool[i];
      const candCount = unitCounts.get(cand.unitCode) || 0;
      const chosenCount = unitCounts.get(chosen.unitCode) || 0;
      if (candCount !== chosenCount) {
        if (candCount > chosenCount) {
          chosen = cand;
        }
      } else if (compareBaseOrder(cand, chosen) < 0) {
        chosen = cand;
      }
    }

    const idx = remaining.indexOf(chosen);
    if (idx >= 0) remaining.splice(idx, 1);
    result.push(chosen);
    lastUnit = chosen.unitCode;
    lastSubject = chosen.subject;
  }

  if (typeof limit === "number" && limit >= 0) {
    return result.slice(0, limit);
  }
  return result;
}

export function getReviewItemsPath(progressDir: string = getProgressDir()): string {
  return path.join(progressDir, "review_items.json");
}

interface ProblemMeta {
  id: string;
  unitCode: string;
  commonTrapTag: string | null;
  archetypeKey: string | null;
}

interface DrillMeta {
  drillId: string;
  unitCode: string;
  subject: "MTH" | "PRG";
  problems: Map<string, ProblemMeta>;
}

function loadVaultUnitMap(rootDir: string): Map<string, string> {
  const unitOf = new Map<string, string>();
  for (const sub of [
    path.join("math_engine", "reasoning_vault"),
    path.join("code_engine", "reasoning_vault"),
  ]) {
    const dir = path.join(rootDir, sub);
    if (!fs.existsSync(dir)) continue;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => cmpStr(a.name, b.name))) {
      if (!entry.isFile() || !entry.name.endsWith(".json")) continue;
      try {
        const doc = JSON.parse(fs.readFileSync(path.join(dir, entry.name), "utf-8")) as {
          archetypes?: Array<{ archetypeKey?: unknown; unitCode?: unknown }>;
        };
        for (const arch of doc.archetypes || []) {
          if (
            arch &&
            typeof arch.archetypeKey === "string" &&
            arch.archetypeKey &&
            typeof arch.unitCode === "string" &&
            arch.unitCode &&
            !unitOf.has(arch.archetypeKey)
          ) {
            unitOf.set(arch.archetypeKey, arch.unitCode);
          }
        }
      } catch {
        continue;
      }
    }
  }
  return unitOf;
}

function loadAllDrillMeta(
  dataDir: string,
  labsDir: string,
  unitOf: Map<string, string>
): Map<string, DrillMeta> {
  const drills = new Map<string, DrillMeta>();

  if (fs.existsSync(dataDir)) {
    const visit = (dir: string) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          visit(fullPath);
        } else if (entry.isFile() && entry.name.endsWith(".json")) {
          try {
            const doc = JSON.parse(fs.readFileSync(fullPath, "utf-8")) as {
              drillId?: unknown;
              subject?: unknown;
              unitCode?: unknown;
              problems?: Array<Record<string, unknown>>;
            };
            if (typeof doc.drillId !== "string" || !doc.drillId) continue;
            const drillUnit = typeof doc.unitCode === "string" ? doc.unitCode : "";
            const isPrg =
              doc.subject === "PRG" ||
              drillUnit.startsWith("PRG-") ||
              doc.drillId.startsWith("DRL-PRG-");
            const problems = new Map<string, ProblemMeta>();
            for (const p of doc.problems || []) {
              if (!p || typeof p.id !== "string" || !p.id) continue;
              const archKey =
                typeof p.archetypeKey === "string" && p.archetypeKey
                  ? p.archetypeKey
                  : typeof p.templateKey === "string" && p.templateKey
                  ? p.templateKey
                  : null;
              const pUnit =
                (typeof p.unitCode === "string" && p.unitCode) ||
                (archKey && unitOf.get(archKey)) ||
                drillUnit;
              const trap =
                typeof p.commonTrapTag === "string" && p.commonTrapTag
                  ? p.commonTrapTag
                  : null;
              problems.set(p.id, {
                id: p.id,
                unitCode: pUnit,
                commonTrapTag: trap,
                archetypeKey: archKey,
              });
            }
            drills.set(doc.drillId, {
              drillId: doc.drillId,
              unitCode: drillUnit,
              subject: isPrg ? "PRG" : "MTH",
              problems,
            });
          } catch {
            continue;
          }
        }
      }
    };
    visit(dataDir);
  }

  if (fs.existsSync(labsDir)) {
    for (const entry of fs.readdirSync(labsDir, { withFileTypes: true })) {
      if (!entry.isDirectory() || !entry.name.startsWith("LAB-")) continue;
      const cfgPath = path.join(labsDir, entry.name, "lab.config.json");
      if (!fs.existsSync(cfgPath)) continue;
      try {
        const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf-8")) as {
          labId?: unknown;
          chapterCode?: unknown;
          unitsUsed?: unknown[];
          milestones?: Array<Record<string, unknown>>;
        };
        if (typeof cfg.labId !== "string" || !cfg.labId) continue;
        const defaultUnit =
          (typeof cfg.chapterCode === "string" && cfg.chapterCode) ||
          (Array.isArray(cfg.unitsUsed) && typeof cfg.unitsUsed[0] === "string"
            ? cfg.unitsUsed[0]
            : "");
        const problems = new Map<string, ProblemMeta>();
        for (const ms of cfg.milestones || []) {
          if (!ms || typeof ms.id !== "string" || !ms.id) continue;
          const msUnits = Array.isArray(ms.units) ? ms.units : [];
          const msUnit =
            (typeof msUnits[0] === "string" && msUnits[0]) || defaultUnit;
          problems.set(ms.id, {
            id: ms.id,
            unitCode: msUnit,
            commonTrapTag: null,
            archetypeKey: null,
          });
        }
        drills.set(cfg.labId, {
          drillId: cfg.labId,
          unitCode: defaultUnit,
          subject: "PRG",
          problems,
        });
      } catch {
        continue;
      }
    }
  }

  return drills;
}

function extractFirstProgSignal(state: Record<string, unknown>): string | null {
  const reviews = Array.isArray(state.reviews)
    ? (state.reviews as Array<Record<string, unknown>>)
    : [];
  for (const r of reviews) {
    if (!r || typeof r !== "object") continue;
    const findings = Array.isArray(r.findings)
      ? (r.findings as Array<Record<string, unknown>>)
      : [];
    for (const f of findings) {
      if (f && !f.disputed && typeof f.check === "string" && f.check) {
        return f.check;
      }
    }
    const lint = Array.isArray(r.lint)
      ? (r.lint as Array<Record<string, unknown>>)
      : [];
    for (const l of lint) {
      if (l && typeof l.rule === "string" && l.rule) {
        return l.rule;
      }
    }
  }
  return null;
}

function extractLastMatchedTrap(state: Record<string, unknown>): string | null {
  const attempts = Array.isArray(state.attempts)
    ? (state.attempts as Array<Record<string, unknown>>)
    : [];
  let last: string | null = null;
  for (const a of attempts) {
    if (a && typeof a.matchedTrap === "string" && a.matchedTrap) {
      last = a.matchedTrap;
    }
  }
  return last;
}

function isPracticedState(
  state: Record<string, unknown>,
  subject: "MTH" | "PRG"
): boolean {
  if (state.skipped) return true;
  if (subject === "PRG") {
    const reviews = Array.isArray(state.reviews) ? state.reviews : [];
    if (reviews.length > 0) return true;
    if (state.lastTestReport !== undefined && state.lastTestReport !== null) return true;
    if (state.score !== undefined && state.score !== null) return true;
    const attempts = Array.isArray(state.attempts)
      ? (state.attempts as Array<Record<string, unknown>>)
      : [];
    if (
      attempts.some(
        (a) => a && !NON_SUBSTANTIVE_VERDICTS.has(String(a.verdict || ""))
      )
    ) {
      return true;
    }
    if (state.score !== null && state.score !== undefined) return true;
    return false;
  }
  const attempts = Array.isArray(state.attempts)
    ? (state.attempts as Array<Record<string, unknown>>)
    : [];
  const substantive = attempts.filter(
    (a) => a && !NON_SUBSTANTIVE_VERDICTS.has(String(a.verdict || ""))
  );
  if (substantive.length > 0) return true;
  const lastCheck = state.lastCheck as Record<string, unknown> | null | undefined;
  if (
    lastCheck &&
    typeof lastCheck === "object" &&
    typeof lastCheck.verdict === "string" &&
    lastCheck.verdict &&
    !NON_SUBSTANTIVE_VERDICTS.has(lastCheck.verdict)
  ) {
    return true;
  }
  return typeof state.score === "number" && !Number.isNaN(state.score);
}

/**
 * Backfill `{ "<drillId>/<qid>": ReviewItem }` from `progress/<DRILL_ID>.json` and drill definitions.
 */
export function buildScheduleFromProgress(
  options?: ReviewStoreOptions
): Record<string, ReviewItem> {
  const rootDir = options?.rootDir ?? getWorkspaceRoot();
  const dataDir = options?.dataDir ?? getDrillsDataDir();
  const progressDir = options?.progressDir ?? getProgressDir();
  const labsDir = options?.labsDir ?? getLabsDir();

  if (!fs.existsSync(progressDir)) return {};

  const unitOf = loadVaultUnitMap(rootDir);
  const drills = loadAllDrillMeta(dataDir, labsDir, unitOf);
  const schedule: Record<string, ReviewItem> = {};

  const files = fs
    .readdirSync(progressDir, { withFileTypes: true })
    .filter((e) => e.isFile() && e.name.endsWith(".json"))
    .map((e) => e.name)
    .sort(cmpStr);

  for (const name of files) {
    if (name === "review_items.json" || name.startsWith("_")) continue;
    let prog: Record<string, unknown>;
    try {
      prog = JSON.parse(
        fs.readFileSync(path.join(progressDir, name), "utf-8")
      ) as Record<string, unknown>;
    } catch {
      continue;
    }
    if (!prog || typeof prog !== "object" || Array.isArray(prog)) continue;
    const drillId = typeof prog.drillId === "string" ? prog.drillId : "";
    if (!drillId) continue;
    const drill = drills.get(drillId);
    if (!drill) continue;

    const summary =
      prog.sessionSummary && typeof prog.sessionSummary === "object"
        ? (prog.sessionSummary as Record<string, unknown>)
        : {};
    const fallbackTs =
      (typeof prog.updatedAt === "string" && prog.updatedAt) ||
      (typeof summary.attemptDate === "string" && summary.attemptDate) ||
      "";
    const progProblems =
      prog.problems && typeof prog.problems === "object"
        ? (prog.problems as Record<string, Record<string, unknown>>)
        : {};

    drill.problems.forEach((probMeta, qid) => {
      const state = progProblems[qid];
      if (!state || typeof state !== "object") return;
      if (!isPracticedState(state, drill.subject)) return;

      const events = extractReviewEvents(state, fallbackTs);
      const replayed = replayReviewEvents(events);
      if (!replayed) return;

      const trapTag =
        probMeta.commonTrapTag ||
        (drill.subject === "PRG"
          ? extractFirstProgSignal(state)
          : extractLastMatchedTrap(state));

      const key = reviewItemKey(drillId, qid);
      schedule[key] = redactReviewItem({
        drillId,
        qid,
        unitCode: probMeta.unitCode,
        subject: drill.subject,
        commonTrapTag: trapTag,
        archetypeKey: probMeta.archetypeKey,
        level: replayed.level,
        lastReviewed: replayed.lastReviewed,
        dueDate: replayed.dueDate,
        revisitNote: cleanRevisitNote(state.revisitNote),
      });
    });
  }

  const sortedKeys = Object.keys(schedule).sort(cmpStr);
  const ordered: Record<string, ReviewItem> = {};
  for (const k of sortedKeys) {
    ordered[k] = schedule[k];
  }
  return ordered;
}

export function loadSavedReviewItems(
  progressDir: string = getProgressDir()
): Record<string, ReviewItem> {
  const filePath = getReviewItemsPath(progressDir);
  if (!fs.existsSync(filePath)) return {};
  try {
    const raw = JSON.parse(fs.readFileSync(filePath, "utf-8")) as unknown;
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
    const obj = raw as Record<string, unknown>;
    const source =
      obj.items && typeof obj.items === "object" && !Array.isArray(obj.items)
        ? (obj.items as Record<string, unknown>)
        : obj;
    const out: Record<string, ReviewItem> = {};
    for (const val of Object.values(source)) {
      if (!val || typeof val !== "object" || Array.isArray(val)) continue;
      const rec = val as Record<string, unknown>;
      if (typeof rec.drillId !== "string" || !rec.drillId || typeof rec.qid !== "string" || !rec.qid) {
        continue;
      }
      const redacted = redactReviewItem(rec);
      out[reviewItemKey(redacted.drillId, redacted.qid)] = redacted;
    }
    return out;
  } catch {
    return {};
  }
}

export function writeReviewItemsStore(
  schedule: Record<string, ReviewItem>,
  progressDir: string = getProgressDir()
): string {
  const filePath = getReviewItemsPath(progressDir);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const cleaned: Record<string, ReviewItem> = {};
  const keys = Object.keys(schedule).sort(cmpStr);
  for (const k of keys) {
    const v = schedule[k];
    if (!v || !v.drillId || !v.qid) continue;
    const redacted = redactReviewItem(v);
    cleaned[reviewItemKey(redacted.drillId, redacted.qid)] = redacted;
  }
  const tmpPath = `${filePath}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(tmpPath, `${JSON.stringify(cleaned, null, 2)}\n`, "utf-8");
  fs.renameSync(tmpPath, filePath);
  return filePath;
}

export function getReviewItemsSchedule(
  options?: ReviewStoreOptions
): Record<string, ReviewItem> {
  const progressDir = options?.progressDir ?? getProgressDir();
  const backfilled = buildScheduleFromProgress({ ...options, progressDir });
  const saved = loadSavedReviewItems(progressDir);
  if (Object.keys(saved).length === 0) {
    return backfilled;
  }
  const merged: Record<string, ReviewItem> = { ...backfilled };
  for (const [key, savedEntry] of Object.entries(saved)) {
    const entry: ReviewItem = { ...savedEntry };
    const bf = backfilled[key];
    if (bf && (bf.lastReviewed || "") > (entry.lastReviewed || "")) {
      // A newer attempt in a normal drill session wins over an older saved review result.
      merged[key] = bf;
      continue;
    }
    if (bf) {
      if (bf.revisitNote !== null) {
        entry.revisitNote = bf.revisitNote;
      }
      if (!entry.unitCode && bf.unitCode) {
        entry.unitCode = bf.unitCode;
      }
      if (!entry.commonTrapTag && bf.commonTrapTag) {
        entry.commonTrapTag = bf.commonTrapTag;
      }
      if (!entry.archetypeKey && bf.archetypeKey) {
        entry.archetypeKey = bf.archetypeKey;
      }
    }
    merged[key] = redactReviewItem(entry);
  }
  const sortedKeys = Object.keys(merged).sort(cmpStr);
  const ordered: Record<string, ReviewItem> = {};
  for (const k of sortedKeys) {
    ordered[k] = merged[k];
  }
  return ordered;
}

export function getDueReviewItems(options?: ReviewStoreOptions): {
  today: string;
  items: ReviewItem[];
  totalDue: number;
  nextDueDate: string | null;
} {
  const today = normalizeReviewDate(options?.today);
  const schedule = getReviewItemsSchedule(options);
  const allItems = Object.values(schedule);
  const due = allItems.filter((it) => it.dueDate <= today);
  const futureDates = allItems
    .filter((it) => it.dueDate > today)
    .map((it) => it.dueDate)
    .sort(cmpStr);
  return {
    today,
    items: interleaveDueItems(due, options?.limit),
    totalDue: due.length,
    nextDueDate: futureDates[0] ?? null,
  };
}

function lookupProblemMetadata(
  drillId: string,
  qid: string,
  options?: ReviewStoreOptions
): {
  unitCode: string;
  subject: "MTH" | "PRG";
  commonTrapTag: string | null;
  archetypeKey: string | null;
  revisitNote: string | null;
} {
  const rootDir = options?.rootDir ?? getWorkspaceRoot();
  const dataDir = options?.dataDir ?? getDrillsDataDir();
  const labsDir = options?.labsDir ?? getLabsDir();
  const progressDir = options?.progressDir ?? getProgressDir();

  const unitOf = loadVaultUnitMap(rootDir);
  const drills = loadAllDrillMeta(dataDir, labsDir, unitOf);
  const drill = drills.get(drillId);
  const prob = drill?.problems.get(qid);

  let revisitNote: string | null = null;
  const progFile = path.join(progressDir, `${drillId}.json`);
  if (fs.existsSync(progFile)) {
    try {
      const prog = JSON.parse(fs.readFileSync(progFile, "utf-8")) as {
        problems?: Record<string, Record<string, unknown>>;
      };
      const st = prog.problems?.[qid];
      if (st) {
        revisitNote = cleanRevisitNote(st.revisitNote);
      }
    } catch {
      revisitNote = null;
    }
  }

  return {
    unitCode: prob?.unitCode || drill?.unitCode || "",
    subject:
      drill?.subject ||
      (drillId.startsWith("DRL-PRG-") || drillId.startsWith("LAB-") ? "PRG" : "MTH"),
    commonTrapTag: prob?.commonTrapTag ?? null,
    archetypeKey: prob?.archetypeKey ?? null,
    revisitNote,
  };
}

export function recordReviewItemResult(
  input: {
    drillId: string;
    qid: string;
    correct: boolean;
    hintsUsed?: boolean | number;
    date?: string;
  },
  options?: ReviewStoreOptions
): ReviewItem {
  if (!isSafeId(input.drillId) || !isSafeId(input.qid)) {
    throw new Error("Invalid drillId or qid");
  }
  const progressDir = options?.progressDir ?? getProgressDir();
  const schedule = getReviewItemsSchedule({ ...options, progressDir });
  const key = reviewItemKey(input.drillId, input.qid);
  const existing = schedule[key];
  const currentLevel = existing ? existing.level : MIN_REVIEW_LEVEL;
  const revDate = normalizeReviewDate(input.date, options?.today);

  const step = stepReviewSchedule(currentLevel, {
    correct: Boolean(input.correct),
    hintsUsed: input.hintsUsed,
    date: revDate,
  });

  const base: ReviewItem = existing
    ? { ...existing }
    : {
        drillId: input.drillId,
        qid: input.qid,
        ...lookupProblemMetadata(input.drillId, input.qid, { ...options, progressDir }),
        level: MIN_REVIEW_LEVEL,
        lastReviewed: revDate,
        dueDate: revDate,
      };

  base.level = step.level;
  base.lastReviewed = step.lastReviewed;
  base.dueDate = step.dueDate;

  const updated = redactReviewItem(base);
  schedule[key] = updated;
  writeReviewItemsStore(schedule, progressDir);
  return updated;
}
