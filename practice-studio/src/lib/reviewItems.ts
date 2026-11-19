import fs from "fs";
import path from "path";
import { formatLocalDate } from "@/lib/dueToday";
import {
  getDrillsDataDir,
  getLabsDir,
  getProgressDir,
  getWorkspaceRoot,
  isSafeId,
  loadIdMapTitles,
} from "@/lib/paths";
import { plainTitle } from "@/lib/titleText";

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
export const DEFAULT_ITEM_DURATION_MS = 90_000; // 1.5 minutes fallback per item

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SAFE_TRAP_RE = /^[A-Za-z0-9@._/-]{1,128}$/;
const NON_SUBSTANTIVE_VERDICTS = new Set(["invalid input", "parse_error"]);

export type ReviewScopeKind = "subject" | "unit" | "chapter" | "trap" | "drill";

export interface ParsedReviewScope {
  kind: ReviewScopeKind;
  value: string;
}

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
  lastWrong?: boolean;
}

export interface ReviewEvent {
  date: string;
  correct: boolean;
  assisted: boolean;
  kind?: "variant";
}

export interface ReviewStoreOptions {
  today?: string;
  limit?: number;
  scope?: string | null;
  dataDir?: string;
  progressDir?: string;
  labsDir?: string;
  rootDir?: string;
}

export interface DueReviewItemsResult {
  today: string;
  items: ReviewItem[];
  totalDue: number;
  bySubject: { MTH: number; PRG: number };
  nextDueDate: string | null;
  nextDueCount: number;
  medianDurationMs: number;
  estimatedMinutes: number;
  unitTitles: Record<string, string>;
  scope?: string;
}

/**
 * Parse and validate a review scope filter:
 * `subject:MTH|PRG`, `unit:<code>`, `chapter:<code>`, `trap:<tag>`, `drill:<id>`.
 */
export function parseReviewScope(raw?: string | null): ParsedReviewScope | null {
  if (raw === undefined || raw === null) return null;
  const text = raw.trim();
  if (!text) return null;
  const colonIdx = text.indexOf(":");
  if (colonIdx <= 0) {
    throw new Error(`Invalid scope '${raw}': expected '<kind>:<value>'`);
  }
  const kind = text.slice(0, colonIdx).trim().toLowerCase();
  const value = text.slice(colonIdx + 1).trim();
  if (!value) {
    throw new Error(`Invalid scope '${raw}': missing value`);
  }
  if (kind === "subject") {
    const upper = value.toUpperCase();
    if (upper !== "MTH" && upper !== "PRG") {
      throw new Error(`Invalid subject scope '${raw}': expected MTH or PRG`);
    }
    return { kind: "subject", value: upper };
  }
  if (kind === "unit" || kind === "chapter" || kind === "drill") {
    if (!isSafeId(value)) {
      throw new Error(`Invalid ${kind} scope value: '${value}'`);
    }
    return { kind, value };
  }
  if (kind === "trap") {
    if (!SAFE_TRAP_RE.test(value) || value.includes("..")) {
      throw new Error(`Invalid trap scope value: '${value}'`);
    }
    return { kind: "trap", value };
  }
  throw new Error(`Unknown scope kind '${kind}'`);
}

export function matchesReviewScope(
  item: Pick<ReviewItem, "subject" | "unitCode" | "commonTrapTag" | "drillId"> & {
    qid?: string;
  },
  parsedScope: ParsedReviewScope | null,
  tagsByKey?: ReadonlyMap<string, ReadonlySet<string>>
): boolean {
  if (!parsedScope) return true;
  const { kind, value } = parsedScope;
  switch (kind) {
    case "subject":
      return item.subject === value;
    case "unit":
      return item.unitCode === value;
    case "chapter":
      return item.unitCode === value || item.unitCode.startsWith(`${value}-U`);
    case "trap": {
      if (item.commonTrapTag === value) return true;
      if (tagsByKey && item.drillId && item.qid) {
        return Boolean(tagsByKey.get(reviewItemKey(item.drillId, item.qid))?.has(value));
      }
      return false;
    }
    case "drill":
      return item.drillId === value;
  }
}

export function estimateReviewMinutes(
  itemCount: number,
  medianDurationMs: number = DEFAULT_ITEM_DURATION_MS
): number {
  if (itemCount <= 0) return 0;
  const ms =
    typeof medianDurationMs === "number" &&
    Number.isFinite(medianDurationMs) &&
    medianDurationMs > 0
      ? medianDurationMs
      : DEFAULT_ITEM_DURATION_MS;
  return Math.max(1, Math.round((itemCount * ms) / 60_000));
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
  const exampleViewedAt =
    typeof state.exampleViewedAt === "string" && state.exampleViewedAt.trim()
      ? state.exampleViewedAt.trim()
      : "";
  const stateAssisted = Boolean(
    state.setupRevealedBeforeAnswer ||
      state.solutionRevealedBeforeAnswer ||
      (typeof state.hintsRevealed === "number" && state.hintsRevealed > 0)
  );
  const stateAssistedWithExample = stateAssisted || Boolean(exampleViewedAt);

  const rawAttempts = Array.isArray(state.attempts)
    ? (state.attempts as Array<Record<string, unknown>>)
    : [];
  const substantive = rawAttempts.filter(
    (a) =>
      a &&
      typeof a === "object" &&
      a.kind !== "variant" &&
      !NON_SUBSTANTIVE_VERDICTS.has(String(a.verdict || ""))
  );

  if (substantive.length > 0) {
    const singleHalfScore =
      substantive.length === 1 &&
      substantive[0]?.verdict === "correct" &&
      state.score === 0.5;
    return substantive.map((att) => {
      const attTs = typeof att.ts === "string" ? att.ts.trim() : "";
      const evDate = normalizeReviewDate(attTs, fallbackDate);
      const verdict = String(att.verdict || "");
      const correct = verdict === "correct";
      const hasExplicitHint =
        "hintsUsed" in att || "assisted" in att || "hintsRevealed" in att;
      const afterExample = Boolean(
        att.exampleViewed || (exampleViewedAt && (!attTs || attTs >= exampleViewedAt))
      );
      const attRevealed = Boolean(
        att.setupRevealed || att.solutionRevealed || afterExample
      );
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
        : stateAssistedWithExample;
      return { date: evDate, correct, assisted };
    });
  }

  if (state.skipped) {
    return [{ date: fallbackDate, correct: false, assisted: stateAssistedWithExample }];
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
    const assisted = stateAssistedWithExample || (correct && state.score === 0.5);
    return [{ date: fallbackDate, correct, assisted }];
  }

  if (typeof state.score === "number" && !Number.isNaN(state.score)) {
    const correct = state.score > 0;
    const assisted = stateAssistedWithExample || (state.score > 0 && state.score < 1.0);
    return [{ date: fallbackDate, correct, assisted }];
  }

  return [];
}

export function replayReviewEvents(
  events: ReviewEvent[]
): { level: number; lastReviewed: string; dueDate: string; lastWrong: boolean } | null {
  if (!Array.isArray(events) || events.length === 0) return null;
  const itemEvents = events.filter((ev) => ev && ev.kind !== "variant");
  if (itemEvents.length === 0) return null;
  let level = MIN_REVIEW_LEVEL;
  let lastReviewed = "";
  let dueDate = "";
  let lastWrongDate: string | null = null;

  for (const ev of itemEvents) {
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

  return {
    level,
    lastReviewed,
    dueDate,
    lastWrong: !Boolean(itemEvents[itemEvents.length - 1]?.correct),
  };
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
    lastWrong: Boolean(rec.lastWrong),
  };
}

function cmpStr(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

function comparePriorityOrder(
  a: ReviewItem,
  b: ReviewItem,
  openWeakTraps?: ReadonlySet<string>
): number {
  const aWrong = a.lastWrong ? 0 : 1;
  const bWrong = b.lastWrong ? 0 : 1;
  if (aWrong !== bWrong) return aWrong - bWrong;

  const aWeak = a.commonTrapTag && openWeakTraps?.has(a.commonTrapTag) ? 0 : 1;
  const bWeak = b.commonTrapTag && openWeakTraps?.has(b.commonTrapTag) ? 0 : 1;
  if (aWeak !== bWeak) return aWeak - bWeak;

  if (a.dueDate !== b.dueDate) return cmpStr(a.dueDate, b.dueDate);
  if (a.level !== b.level) return a.level - b.level;
  if (a.unitCode !== b.unitCode) return cmpStr(a.unitCode, b.unitCode);
  if (a.drillId !== b.drillId) return cmpStr(a.drillId, b.drillId);
  return cmpStr(a.qid, b.qid);
}

/**
 * Sort due items by priority:
 * (a) wrong on last attempt,
 * (b) commonTrapTag is an open weak spot,
 * (c) most overdue (dueDate ascending), then level / unitCode / drillId / qid.
 */
export function prioritizeDueItems(
  items: ReviewItem[],
  openWeakTraps?: ReadonlySet<string>
): ReviewItem[] {
  const cleaned = items.map((it) => redactReviewItem(it));
  cleaned.sort((a, b) => comparePriorityOrder(a, b, openWeakTraps));
  return cleaned;
}

/**
 * Pick the top `limit` highest-priority due items first, then interleave them so no two
 * consecutive items come from the same unit when avoidable, mixing MTH and PRG subjects
 * (deterministic parity with `scripts.review_items.interleave_due_items`).
 */
export function interleaveDueItems(
  items: ReviewItem[],
  limit?: number,
  openWeakTraps?: ReadonlySet<string>
): ReviewItem[] {
  let remaining = prioritizeDueItems(items, openWeakTraps);
  if (typeof limit === "number" && limit >= 0) {
    remaining = remaining.slice(0, limit);
  }

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
      } else if (comparePriorityOrder(cand, chosen, openWeakTraps) < 0) {
        chosen = cand;
      }
    }

    const idx = remaining.indexOf(chosen);
    if (idx >= 0) remaining.splice(idx, 1);
    result.push(chosen);
    lastUnit = chosen.unitCode;
    lastSubject = chosen.subject;
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
  qualityChecks: string[];
}

interface DrillMeta {
  drillId: string;
  unitCode: string;
  unitTitle: string;
  subject: "MTH" | "PRG";
  lintOverrides: Set<string>;
  problems: Map<string, ProblemMeta>;
}

interface VaultMeta {
  unitOf: Map<string, string>;
  archChecks: Map<string, Set<string>>;
  universalIds: Set<string>;
}

function loadVaultMeta(rootDir: string): VaultMeta {
  const unitOf = new Map<string, string>();
  const archChecks = new Map<string, Set<string>>();
  const universalIds = new Set<string>();

  const universalPath = path.join(rootDir, "code_engine", "quality_checks.json");
  if (fs.existsSync(universalPath)) {
    try {
      const raw = JSON.parse(fs.readFileSync(universalPath, "utf-8")) as unknown;
      const list = Array.isArray(raw)
        ? raw
        : raw && typeof raw === "object" && Array.isArray((raw as { checks?: unknown }).checks)
        ? ((raw as { checks: unknown[] }).checks)
        : [];
      for (const c of list) {
        if (c && typeof c === "object" && typeof (c as { id?: unknown }).id === "string") {
          const cid = (c as { id: string }).id;
          if (cid) universalIds.add(cid);
        }
      }
    } catch {
      // ignore unreadable universal checks
    }
  }

  for (const sub of [
    path.join("math_engine", "reasoning_vault"),
    path.join("code_engine", "reasoning_vault"),
  ]) {
    const dir = path.join(rootDir, sub);
    if (!fs.existsSync(dir)) continue;
    const isCodeVault = sub.startsWith("code_engine");
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => cmpStr(a.name, b.name))) {
      if (!entry.isFile() || !entry.name.endsWith(".json")) continue;
      try {
        const doc = JSON.parse(fs.readFileSync(path.join(dir, entry.name), "utf-8")) as {
          archetypes?: Array<{
            archetypeKey?: unknown;
            unitCode?: unknown;
            qualityChecks?: Array<{ id?: unknown }>;
          }>;
        };
        for (const arch of doc.archetypes || []) {
          if (!arch || typeof arch.archetypeKey !== "string" || !arch.archetypeKey) continue;
          if (
            typeof arch.unitCode === "string" &&
            arch.unitCode &&
            !unitOf.has(arch.archetypeKey)
          ) {
            unitOf.set(arch.archetypeKey, arch.unitCode);
          }
          if (isCodeVault) {
            const cids = new Set<string>();
            for (const c of arch.qualityChecks || []) {
              if (c && typeof c.id === "string" && c.id) {
                cids.add(c.id);
              }
            }
            archChecks.set(arch.archetypeKey, cids);
          }
        }
      } catch {
        continue;
      }
    }
  }
  return { unitOf, archChecks, universalIds };
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
              unitTitle?: unknown;
              lintOverrides?: Array<{ rule?: unknown }>;
              problems?: Array<Record<string, unknown>>;
            };
            if (typeof doc.drillId !== "string" || !doc.drillId) continue;
            const drillUnit = typeof doc.unitCode === "string" ? doc.unitCode : "";
            const drillUnitTitle = typeof doc.unitTitle === "string" ? doc.unitTitle : "";
            const isPrg =
              doc.subject === "PRG" ||
              drillUnit.startsWith("PRG-") ||
              doc.drillId.startsWith("DRL-PRG-");
            const lintOverrides = new Set<string>();
            for (const o of doc.lintOverrides || []) {
              if (o && typeof o.rule === "string" && o.rule) {
                lintOverrides.add(o.rule);
              }
            }
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
              const qualityChecks = Array.isArray(p.qualityChecks)
                ? p.qualityChecks.filter((c): c is string => typeof c === "string" && Boolean(c))
                : [];
              problems.set(p.id, {
                id: p.id,
                unitCode: pUnit,
                commonTrapTag: trap,
                archetypeKey: archKey,
                qualityChecks,
              });
            }
            drills.set(doc.drillId, {
              drillId: doc.drillId,
              unitCode: drillUnit,
              unitTitle: drillUnitTitle,
              subject: isPrg ? "PRG" : "MTH",
              lintOverrides,
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
          title?: unknown;
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
          const qualityChecks = Array.isArray(ms.qualityChecks)
            ? ms.qualityChecks.filter((c): c is string => typeof c === "string" && Boolean(c))
            : [];
          problems.set(ms.id, {
            id: ms.id,
            unitCode: msUnit,
            commonTrapTag: null,
            archetypeKey: null,
            qualityChecks,
          });
        }
        drills.set(cfg.labId, {
          drillId: cfg.labId,
          unitCode: defaultUnit,
          unitTitle: typeof cfg.title === "string" ? cfg.title : "",
          subject: "PRG",
          lintOverrides: new Set<string>(),
          problems,
        });
      } catch {
        continue;
      }
    }
  }

  return drills;
}

const WEAK_SPOT_MIN_MATCHES = 2;
const WEAK_SPOT_CLOSE_AFTER = 2;

interface LoadedProgressItem {
  drillId: string;
  unitCode: string;
  qid: string;
  subject: "MTH" | "PRG";
  trap: string | null;
  archetypeKey: string | null;
  ts: string;
  score: number;
  skipped: boolean;
  assisted: boolean;
  passed: boolean;
  matched: string[];
  signals: string[];
  applicableChecks: Set<string>;
  lintOverrides: Set<string>;
  revisitNote: string | null;
  state: Record<string, unknown>;
}

function firstAttemptTs(state: Record<string, unknown>, fallback: string): string {
  const attempts = Array.isArray(state.attempts)
    ? (state.attempts as Array<Record<string, unknown>>)
    : [];
  if (attempts.length > 0) {
    const t = attempts[0]?.ts;
    return typeof t === "string" ? t : fallback;
  }
  const reviews = Array.isArray(state.reviews)
    ? (state.reviews as Array<Record<string, unknown>>)
    : [];
  if (reviews.length > 0) {
    const t = reviews[0]?.at;
    return typeof t === "string" ? t : fallback;
  }
  return fallback;
}

function isAssistedState(state: Record<string, unknown>): boolean {
  const attempts = (
    Array.isArray(state.attempts)
      ? (state.attempts as Array<Record<string, unknown>>)
      : []
  ).filter((a) => a && typeof a === "object" && a.kind !== "variant");
  return Boolean(
    state.setupRevealedBeforeAnswer ||
      state.solutionRevealedBeforeAnswer ||
      state.exampleViewedAt ||
      (typeof state.hintsRevealed === "number" && state.hintsRevealed > 0) ||
      attempts.some((a) => a.setupRevealed || a.solutionRevealed || a.exampleViewed)
  );
}

/** Collect matchedTrap tags from original attempts and server-stored variant attempts (mirrors `scripts.weak_spots._collect_matched_traps`). */
function collectMatchedTraps(state: Record<string, unknown>): string[] {
  const matched: string[] = [];
  const attempts = Array.isArray(state.attempts)
    ? (state.attempts as Array<Record<string, unknown>>)
    : [];
  for (const a of attempts) {
    if (a && typeof a.matchedTrap === "string" && a.matchedTrap) {
      matched.push(a.matchedTrap);
    }
  }
  const variants =
    state.variants && typeof state.variants === "object"
      ? (state.variants as Record<string, Record<string, unknown>>)
      : null;
  if (variants) {
    for (const token of Object.keys(variants).sort(cmpStr)) {
      const rec = variants[token];
      if (!rec || !Array.isArray(rec.attempts)) continue;
      for (const a of rec.attempts as Array<Record<string, unknown>>) {
        if (a && typeof a.matchedTrap === "string" && a.matchedTrap) {
          matched.push(a.matchedTrap);
        }
      }
    }
  }
  return matched;
}

/** Mirrors `progress_store.item_score`. */
function computeMathItemScore(state: Record<string, unknown>): [number, boolean] {
  const attempts = (
    Array.isArray(state.attempts)
      ? (state.attempts as Array<Record<string, unknown>>)
      : []
  ).filter((a) => a && typeof a === "object" && a.kind !== "variant");
  const assisted = isAssistedState(state);
  if (state.skipped) {
    return [0.0, assisted];
  }
  const substantive = attempts.filter(
    (a) => a && typeof a === "object" && !NON_SUBSTANTIVE_VERDICTS.has(String(a.verdict || ""))
  );
  if (substantive.length > 0) {
    const first = substantive[0]?.verdict;
    if (first === "correct" && !assisted) {
      return [1.0, false];
    }
    if (
      substantive.some(
        (a) =>
          a.verdict === "correct" ||
          a.verdict === "equivalent_not_in_form" ||
          a.verdict === "partial"
      )
    ) {
      return [0.5, assisted];
    }
    return [0.0, assisted];
  }
  if (typeof state.score !== "number" || Number.isNaN(state.score)) {
    return [-1.0, assisted];
  }
  return [assisted ? Math.min(state.score, 0.5) : state.score, assisted];
}

/** Mirrors `scripts.weak_spots._prg_item_score`. */
function computePrgItemScore(state: Record<string, unknown>): number {
  if (state.skipped) return 0.0;
  const assisted = isAssistedState(state);
  const reviews = Array.isArray(state.reviews)
    ? (state.reviews as Array<Record<string, unknown>>)
    : [];
  if (reviews.length > 0) {
    if (reviews[reviews.length - 1]?.verdict === "pass") {
      const raw = reviews[0]?.verdict === "pass" ? 1.0 : 0.5;
      return assisted ? Math.min(raw, 0.5) : raw;
    }
    return 0.0;
  }
  if (
    (state.lastTestReport !== undefined && state.lastTestReport !== null) ||
    (state.score !== undefined && state.score !== null)
  ) {
    return 0.0;
  }
  if (Array.isArray(state.attempts) && state.attempts.length > 0) {
    const [sc] = computeMathItemScore(state);
    return sc;
  }
  return -1.0;
}

function extractPrgSignals(state: Record<string, unknown>): string[] {
  const sigs: string[] = [];
  const reviews = Array.isArray(state.reviews)
    ? (state.reviews as Array<Record<string, unknown>>)
    : [];
  for (const r of reviews) {
    if (!r || typeof r !== "object") continue;
    const findings = Array.isArray(r.findings)
      ? (r.findings as Array<Record<string, unknown>>)
      : [];
    for (const f of findings) {
      if (f && !f.disputed && typeof f.check === "string" && f.check && !sigs.includes(f.check)) {
        sigs.push(f.check);
      }
    }
    const lint = Array.isArray(r.lint)
      ? (r.lint as Array<Record<string, unknown>>)
      : [];
    for (const l of lint) {
      if (l && typeof l.rule === "string" && l.rule && !sigs.includes(l.rule)) {
        sigs.push(l.rule);
      }
    }
  }
  return sigs;
}

function isPrgSignalApplicable(sig: string, item: LoadedProgressItem): boolean {
  if (sig.startsWith("U-") || sig.startsWith("QC-")) {
    return item.applicableChecks.has(sig);
  }
  return !item.lintOverrides.has(sig);
}

/**
 * Compute open weak-spot trap/check tags from loaded progress items
 * (exact deterministic parity with `scripts.weak_spots.trap_status`).
 */
function computeOpenWeakTrapsFromLoaded(loaded: LoadedProgressItem[]): Set<string> {
  const open = new Set<string>();

  const mthItems = loaded.filter((i) => i.subject !== "PRG");
  const mthTraps = new Set<string>();
  for (const it of mthItems) {
    for (const t of it.matched) mthTraps.add(t);
    if (it.trap) mthTraps.add(it.trap);
  }
  mthTraps.forEach((trap) => {
    const hits = mthItems.filter((i) => i.matched.includes(trap));
    let n = 0;
    for (const h of hits) {
      for (const m of h.matched) {
        if (m === trap) n += 1;
      }
    }
    if (n < WEAK_SPOT_MIN_MATCHES) return;
    let lastHit = "";
    for (const h of hits) {
      if (h.ts > lastHit) lastHit = h.ts;
    }
    const laterByDrill = new Map<string, LoadedProgressItem[]>();
    for (const it of mthItems) {
      if (
        (it.trap === trap || it.matched.includes(trap)) &&
        it.ts > lastHit &&
        !it.matched.includes(trap)
      ) {
        const list = laterByDrill.get(it.drillId) || [];
        list.push(it);
        laterByDrill.set(it.drillId, list);
      }
    }
    let cleanCount = 0;
    laterByDrill.forEach((its) => {
      if (its.every((x) => x.score === 1.0)) {
        cleanCount += 1;
      }
    });
    if (cleanCount < WEAK_SPOT_CLOSE_AFTER) {
      open.add(trap);
    }
  });

  const prgItems = loaded.filter((i) => i.subject === "PRG");
  const prgSignals = new Set<string>();
  for (const it of prgItems) {
    for (const s of it.signals) prgSignals.add(s);
  }
  prgSignals.forEach((sig) => {
    const hitIndices: number[] = [];
    for (let idx = 0; idx < prgItems.length; idx += 1) {
      if (prgItems[idx].signals.includes(sig)) {
        hitIndices.push(idx);
      }
    }
    if (hitIndices.length < WEAK_SPOT_MIN_MATCHES) return;
    const lastIdx = hitIndices[hitIndices.length - 1];
    let cleanCount = 0;
    for (let idx = lastIdx + 1; idx < prgItems.length; idx += 1) {
      const it = prgItems[idx];
      if (it.passed && isPrgSignalApplicable(sig, it) && !it.signals.includes(sig)) {
        cleanCount += 1;
      }
    }
    if (cleanCount < WEAK_SPOT_CLOSE_AFTER) {
      open.add(sig);
    }
  });

  return open;
}

/**
 * Compute median positive `durationMs` across past attempts (fallback 1.5 min = 90_000 ms).
 * Mirrors `scripts.review_items.estimate_median_duration_ms`.
 */
export function computeMedianDurationMsFromLoaded(
  loaded: ReadonlyArray<{ subject: "MTH" | "PRG"; state: Record<string, unknown> }>,
  subject?: "MTH" | "PRG" | null
): number {
  const allDurations: number[] = [];
  const bySubject: Record<"MTH" | "PRG", number[]> = { MTH: [], PRG: [] };

  for (const item of loaded) {
    const state = item.state;
    const attempts = Array.isArray(state.attempts)
      ? (state.attempts as Array<Record<string, unknown>>)
      : [];
    const perAttempt: number[] = [];
    for (const att of attempts) {
      if (!att || typeof att !== "object") continue;
      if (att.kind === "variant") continue;
      if (NON_SUBSTANTIVE_VERDICTS.has(String(att.verdict || ""))) continue;
      const dur = att.durationMs;
      if (typeof dur === "number" && Number.isFinite(dur) && dur > 0) {
        perAttempt.push(dur);
      }
    }
    if (perAttempt.length > 0) {
      allDurations.push(...perAttempt);
      bySubject[item.subject].push(...perAttempt);
    } else {
      const stateDur = state.durationMs;
      if (typeof stateDur === "number" && Number.isFinite(stateDur) && stateDur > 0) {
        allDurations.push(stateDur);
        bySubject[item.subject].push(stateDur);
      }
    }
  }

  const pool =
    subject && (subject === "MTH" || subject === "PRG") && bySubject[subject].length > 0
      ? bySubject[subject]
      : allDurations;
  if (pool.length === 0) {
    return DEFAULT_ITEM_DURATION_MS;
  }
  const sorted = [...pool].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 1) {
    return Math.round(sorted[mid]);
  }
  return Math.round((sorted[mid - 1] + sorted[mid]) / 2);
}

function loadProgressContext(options?: ReviewStoreOptions): {
  loaded: LoadedProgressItem[];
  drills: Map<string, DrillMeta>;
} {
  const rootDir = options?.rootDir ?? getWorkspaceRoot();
  const dataDir = options?.dataDir ?? getDrillsDataDir();
  const progressDir = options?.progressDir ?? getProgressDir();
  const labsDir = options?.labsDir ?? getLabsDir();

  const { unitOf, archChecks, universalIds } = loadVaultMeta(rootDir);
  const drills = loadAllDrillMeta(dataDir, labsDir, unitOf);

  if (!fs.existsSync(progressDir)) {
    return { loaded: [], drills };
  }

  const files = fs
    .readdirSync(progressDir, { withFileTypes: true })
    .filter((e) => e.isFile() && e.name.endsWith(".json"))
    .map((e) => e.name)
    .sort(cmpStr);

  const loaded: LoadedProgressItem[] = [];

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
      const revisitNote = cleanRevisitNote(state.revisitNote);

      if (drill.subject === "PRG") {
        const score = computePrgItemScore(state);
        if (score < 0) return;
        const assisted = isAssistedState(state);
        const reviews = Array.isArray(state.reviews)
          ? (state.reviews as Array<Record<string, unknown>>)
          : [];
        const sigs = extractPrgSignals(state);
        const applicableChecks = new Set<string>(universalIds);
        if (probMeta.qualityChecks.length > 0) {
          for (const cid of probMeta.qualityChecks) applicableChecks.add(cid);
        } else if (probMeta.archetypeKey) {
          const ac = archChecks.get(probMeta.archetypeKey);
          if (ac) ac.forEach((cid) => applicableChecks.add(cid));
        }
        loaded.push({
          drillId,
          unitCode: probMeta.unitCode,
          qid,
          subject: "PRG",
          trap: probMeta.commonTrapTag || (sigs[0] ?? null),
          archetypeKey: probMeta.archetypeKey,
          ts: firstAttemptTs(state, fallbackTs),
          score,
          skipped: Boolean(state.skipped),
          assisted,
          passed:
            (reviews.length > 0 && reviews[reviews.length - 1]?.verdict === "pass") ||
            score === 1.0,
          matched: [],
          signals: sigs,
          applicableChecks,
          lintOverrides: drill.lintOverrides,
          revisitNote,
          state,
        });
      } else {
        const [score, assisted] = computeMathItemScore(state);
        if (score < 0) return;
        const matched = collectMatchedTraps(state);
        loaded.push({
          drillId,
          unitCode: probMeta.unitCode,
          qid,
          subject: "MTH",
          trap: probMeta.commonTrapTag,
          archetypeKey: probMeta.archetypeKey,
          ts: firstAttemptTs(state, fallbackTs),
          score,
          skipped: Boolean(state.skipped),
          assisted,
          passed: score === 1.0,
          matched,
          signals: [],
          applicableChecks: new Set<string>(),
          lintOverrides: new Set<string>(),
          revisitNote,
          state,
        });
      }
    });
  }

  loaded.sort((a, b) => cmpStr(a.ts, b.ts));
  return { loaded, drills };
}

function buildScheduleFromLoaded(
  loaded: LoadedProgressItem[]
): Record<string, ReviewItem> {
  const schedule: Record<string, ReviewItem> = {};
  for (const item of loaded) {
    if (!item.drillId || !item.qid) continue;
    let events = extractReviewEvents(item.state, item.ts);
    if (events.length === 0) {
      events = [
        {
          date: normalizeReviewDate(item.ts),
          correct: item.score > 0 && !item.skipped,
          assisted: Boolean(item.assisted || (item.score > 0 && item.score < 1.0)),
        },
      ];
    }
    const replayed = replayReviewEvents(events);
    if (!replayed) continue;

    const trapTag =
      item.trap ||
      (item.matched.length > 0 ? item.matched[item.matched.length - 1] : null);

    const key = reviewItemKey(item.drillId, item.qid);
    schedule[key] = redactReviewItem({
      drillId: item.drillId,
      qid: item.qid,
      unitCode: item.unitCode,
      subject: item.subject,
      commonTrapTag: trapTag,
      archetypeKey: item.archetypeKey,
      level: replayed.level,
      lastReviewed: replayed.lastReviewed,
      dueDate: replayed.dueDate,
      revisitNote: item.revisitNote,
      lastWrong: replayed.lastWrong,
    });
  }

  const sortedKeys = Object.keys(schedule).sort(cmpStr);
  const ordered: Record<string, ReviewItem> = {};
  for (const k of sortedKeys) {
    ordered[k] = schedule[k];
  }
  return ordered;
}

/**
 * Backfill `{ "<drillId>/<qid>": ReviewItem }` from `progress/<DRILL_ID>.json` and drill definitions.
 */
export function buildScheduleFromProgress(
  options?: ReviewStoreOptions
): Record<string, ReviewItem> {
  const { loaded } = loadProgressContext(options);
  return buildScheduleFromLoaded(loaded);
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

function mergeSavedSchedule(
  backfilled: Record<string, ReviewItem>,
  saved: Record<string, ReviewItem>
): Record<string, ReviewItem> {
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

export function getReviewItemsSchedule(
  options?: ReviewStoreOptions
): Record<string, ReviewItem> {
  const progressDir = options?.progressDir ?? getProgressDir();
  const backfilled = buildScheduleFromProgress({ ...options, progressDir });
  const saved = loadSavedReviewItems(progressDir);
  return mergeSavedSchedule(backfilled, saved);
}

function buildTagsByKeyFromLoaded(
  loaded: ReadonlyArray<LoadedProgressItem>
): Map<string, Set<string>> {
  const out = new Map<string, Set<string>>();
  for (const it of loaded) {
    if (!it.drillId || !it.qid) continue;
    const key = reviewItemKey(it.drillId, it.qid);
    let tags = out.get(key);
    if (!tags) {
      tags = new Set<string>();
      out.set(key, tags);
    }
    if (it.trap) tags.add(it.trap);
    for (const m of it.matched) {
      if (m) tags.add(m);
    }
    for (const s of it.signals) {
      if (s) tags.add(s);
    }
  }
  return out;
}

export function getDueReviewItems(options?: ReviewStoreOptions): DueReviewItemsResult {
  const parsedScope = parseReviewScope(options?.scope);
  const today = normalizeReviewDate(options?.today);
  const rootDir = options?.rootDir ?? getWorkspaceRoot();
  const progressDir = options?.progressDir ?? getProgressDir();

  const { loaded, drills } = loadProgressContext({ ...options, rootDir, progressDir });
  const tagsByKey = buildTagsByKeyFromLoaded(loaded);
  const openWeakTraps = computeOpenWeakTrapsFromLoaded(loaded);
  const backfilled = buildScheduleFromLoaded(loaded);
  const saved = loadSavedReviewItems(progressDir);
  const schedule = mergeSavedSchedule(backfilled, saved);

  const allItems = Object.values(schedule);
  const allDue = allItems.filter((it) => it.dueDate <= today);
  const bySubject = {
    MTH: allDue.filter((it) => it.subject === "MTH").length,
    PRG: allDue.filter((it) => it.subject === "PRG").length,
  };

  const scopedAll = allItems.filter((it) => matchesReviewScope(it, parsedScope, tagsByKey));
  const scopedDue = scopedAll.filter((it) => it.dueDate <= today);
  const futureDates = scopedAll
    .filter((it) => it.dueDate > today)
    .map((it) => it.dueDate)
    .sort(cmpStr);
  const nextDueDate = futureDates[0] ?? null;
  const nextDueCount = nextDueDate
    ? futureDates.filter((d) => d === nextDueDate).length
    : 0;

  const picked = interleaveDueItems(scopedDue, options?.limit, openWeakTraps);

  const scopeSubject =
    parsedScope?.kind === "subject" ? (parsedScope.value as "MTH" | "PRG") : null;
  const medianDurationMs = computeMedianDurationMsFromLoaded(loaded, scopeSubject);
  const estimatedMinutes = estimateReviewMinutes(scopedDue.length, medianDurationMs);

  const idMapTitles = loadIdMapTitles(rootDir);
  const drillTitleByUnit = new Map<string, string>();
  drills.forEach((d) => {
    if (d.unitCode && d.unitTitle && !drillTitleByUnit.has(d.unitCode)) {
      drillTitleByUnit.set(d.unitCode, d.unitTitle);
    }
  });
  const unitTitles: Record<string, string> = {};
  for (const it of picked) {
    if (it.unitCode && !unitTitles[it.unitCode]) {
      const rawTitle =
        idMapTitles.get(it.unitCode) ||
        drillTitleByUnit.get(it.unitCode) ||
        it.unitCode;
      unitTitles[it.unitCode] = plainTitle(rawTitle) || it.unitCode;
    }
  }

  return {
    today,
    items: picked,
    totalDue: scopedDue.length,
    bySubject,
    nextDueDate,
    nextDueCount,
    medianDurationMs,
    estimatedMinutes,
    unitTitles,
    ...(parsedScope ? { scope: `${parsedScope.kind}:${parsedScope.value}` } : {}),
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

  const { unitOf } = loadVaultMeta(rootDir);
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
  base.lastWrong = !Boolean(input.correct);

  const updated = redactReviewItem(base);
  schedule[key] = updated;
  writeReviewItemsStore(schedule, progressDir);
  return updated;
}
