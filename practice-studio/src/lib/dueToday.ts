import fs from "fs";
import path from "path";
import { getDrillsDataDir, getProgressDir, getWorkspaceRoot, loadIdMapTitles } from "@/lib/paths";
import { drillHref } from "@/lib/routes";
import { plainTitle } from "@/lib/titleText";
export { formatReviewDueDate } from "@/lib/reviewDate";

export interface MasteryCap {
  capped: boolean;
  reason: string;
}

export interface ReviewScheduleEntry {
  mastery?: number | null;
  lastReviewed?: string | null;
  nextReview?: string | null;
  title?: string | null;
  masteryCap?: MasteryCap | null;
}

export interface DueTodayUnit {
  unitCode: string;
  title: string;
  mastery: number;
  lastReviewed: string | null;
  nextReview: string;
  drillId: string | null;
  href: string | null;
  masteryCap: MasteryCap;
}

export interface UnitMasteryContext {
  unitCode: string;
  title: string;
  mastery: number;
  masteryCap: MasteryCap;
}

export interface DueTodayResponse {
  today: string;
  units: DueTodayUnit[];
  unitMastery?: Record<string, UnitMasteryContext>;
}

export interface WeakSpotItem {
  id: string;
  /** Plain-language trap name (MTH); PRG rows show the check id. */
  name?: string;
  detail?: string;
  matches: number;
  drills: number;
  last: string;
  subject: "MTH" | "PRG";
}

export interface WeakSpotUnit {
  unitCode: string;
  unitTitle: string;
  subject: "MTH" | "PRG";
  itemCount: number;
  drillCount: number;
  open: WeakSpotItem[];
  closed: WeakSpotItem[];
  levels: Record<string, { pct: number; n: number; move: "up" | "down" | "stay" }>;
  assistedCount: number;
  skipped: string[];
  masteryCap?: MasteryCap;
}

export interface WeakSpotsResponse {
  scope: string | null;
  units: WeakSpotUnit[];
}

/** Return today's local calendar date as YYYY-MM-DD (never UTC). */
export function formatLocalDate(date: Date = new Date()): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

interface DrillCandidate {
  drillId: string;
  createdAt: string;
}

function isNewerDrill(candidate: DrillCandidate, existing: DrillCandidate | undefined): boolean {
  if (!existing) return true;
  if (candidate.createdAt !== existing.createdAt) {
    return candidate.createdAt > existing.createdAt;
  }
  return candidate.drillId > existing.drillId;
}

/** Find the latest drill ID for each unitCode under `dataDir` (prefers unit drills over chapter mixed drills). */
function findLatestDrillsByUnit(dataDir: string): Map<string, string> {
  const direct = new Map<string, DrillCandidate>();
  const covered = new Map<string, DrillCandidate>();
  if (!fs.existsSync(dataDir)) {
    return new Map();
  }

  const visit = (dir: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        visit(fullPath);
      } else if (entry.isFile() && entry.name.endsWith(".json")) {
        try {
          const doc = JSON.parse(fs.readFileSync(fullPath, "utf-8")) as {
            drillId?: unknown;
            unitCode?: unknown;
            createdAt?: unknown;
            problems?: Array<{ unitCode?: unknown }>;
          };
          if (typeof doc.drillId !== "string" || !doc.drillId) continue;
          const candidate: DrillCandidate = {
            drillId: doc.drillId,
            createdAt: typeof doc.createdAt === "string" ? doc.createdAt : "",
          };
          if (typeof doc.unitCode === "string" && doc.unitCode) {
            if (isNewerDrill(candidate, direct.get(doc.unitCode))) {
              direct.set(doc.unitCode, candidate);
            }
          }
          if (Array.isArray(doc.problems)) {
            for (const prob of doc.problems) {
              if (prob && typeof prob.unitCode === "string" && prob.unitCode) {
                if (isNewerDrill(candidate, covered.get(prob.unitCode))) {
                  covered.set(prob.unitCode, candidate);
                }
              }
            }
          }
        } catch {
          continue;
        }
      }
    }
  };

  visit(dataDir);

  const result = new Map<string, string>();
  covered.forEach((cand, unitCode) => {
    result.set(unitCode, cand.drillId);
  });
  direct.forEach((cand, unitCode) => {
    result.set(unitCode, cand.drillId);
  });
  return result;
}

function readReviewSchedule(progressDir: string = getProgressDir()): Record<string, ReviewScheduleEntry> {
  const cachePath = path.join(progressDir, "_review_schedule.json");
  if (!fs.existsSync(cachePath)) return {};
  try {
    const raw = JSON.parse(fs.readFileSync(cachePath, "utf-8")) as unknown;
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) return {};
    return raw as Record<string, ReviewScheduleEntry>;
  } catch {
    return {};
  }
}

function clampMastery(raw: unknown): number {
  if (typeof raw !== "number" || Number.isNaN(raw)) return 0;
  return Math.max(0, Math.min(4, Math.round(raw)));
}

const L4_CHALLENGE_CAP_REASON = "needs one L4 challenge without hints";

function unitsWithL4Challenge(dataDir: string, progressDir: string): Set<string> {
  const passedUnits = new Set<string>();
  if (!fs.existsSync(dataDir) || !fs.existsSync(progressDir)) {
    return passedUnits;
  }

  const drillsById = new Map<
    string,
    { unitCode: string; isPrg: boolean; problems: Array<{ id: string; level: number; unitCode: string }> }
  >();

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
            problems?: Array<{ id?: unknown; level?: unknown; unitCode?: unknown }>;
          };
          if (typeof doc.drillId !== "string" || !doc.drillId) continue;
          const drillUnit = typeof doc.unitCode === "string" ? doc.unitCode : "";
          const isPrg =
            doc.subject === "PRG" || drillUnit.startsWith("PRG-") || doc.drillId.startsWith("DRL-PRG-");
          const problems: Array<{ id: string; level: number; unitCode: string }> = [];
          for (const p of doc.problems || []) {
            if (!p || typeof p.id !== "string") continue;
            const lv = typeof p.level === "number" ? p.level : 0;
            const pUnit = typeof p.unitCode === "string" && p.unitCode ? p.unitCode : drillUnit;
            problems.push({ id: p.id, level: lv, unitCode: pUnit });
          }
          drillsById.set(doc.drillId, { unitCode: drillUnit, isPrg, problems });
        } catch {
          continue;
        }
      }
    }
  };
  visit(dataDir);

  for (const entry of fs.readdirSync(progressDir, { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith(".json") || entry.name.startsWith("_") || entry.name === "review_items.json") {
      continue;
    }
    try {
      const prog = JSON.parse(fs.readFileSync(path.join(progressDir, entry.name), "utf-8")) as {
        drillId?: unknown;
        problems?: Record<string, Record<string, unknown>>;
      };
      if (typeof prog.drillId !== "string") continue;
      const drill = drillsById.get(prog.drillId);
      if (!drill || !prog.problems) continue;

      for (const prob of drill.problems) {
        if (prob.level < 4 || !prob.unitCode) continue;
        const st = prog.problems[prob.id];
        if (!st || typeof st !== "object" || st.skipped) continue;
        const attempts = Array.isArray(st.attempts) ? (st.attempts as Array<Record<string, unknown>>) : [];
        const assisted = Boolean(
          st.setupRevealedBeforeAnswer ||
            st.solutionRevealedBeforeAnswer ||
            st.exampleViewedAt ||
            (typeof st.hintsRevealed === "number" && st.hintsRevealed > 0) ||
            attempts.some(
              (a) => a && a.kind !== "variant" && (a.setupRevealed || a.solutionRevealed || a.exampleViewed)
            )
        );
        if (assisted) continue;

        if (drill.isPrg) {
          const reviews = Array.isArray(st.reviews) ? (st.reviews as Array<Record<string, unknown>>) : [];
          if (reviews.length > 0 && reviews[0]?.verdict === "pass" && reviews[reviews.length - 1]?.verdict === "pass") {
            passedUnits.add(prob.unitCode);
          }
        } else {
          const substantive = attempts.filter(
            (a) => a && a.verdict !== "invalid input" && a.verdict !== "parse_error"
          );
          if (substantive.length > 0 && substantive[0]?.verdict === "correct") {
            passedUnits.add(prob.unitCode);
          } else if (substantive.length === 0 && st.score === 1) {
            passedUnits.add(prob.unitCode);
          }
        }
      }
    } catch {
      continue;
    }
  }

  return passedUnits;
}

function resolveMasteryCap(
  unitCode: string,
  mastery: number,
  entryCap: MasteryCap | null | undefined,
  l4Units: Set<string>
): MasteryCap {
  if (entryCap && typeof entryCap === "object" && typeof entryCap.capped === "boolean") {
    return {
      capped: entryCap.capped,
      reason: typeof entryCap.reason === "string" ? entryCap.reason : "",
    };
  }
  if (mastery === 2 && !l4Units.has(unitCode)) {
    return { capped: true, reason: L4_CHALLENGE_CAP_REASON };
  }
  return { capped: false, reason: "" };
}

/** Read `_review_schedule.json` and return units with `nextReview <= today` (local date) plus deep links. */
export function getDueTodayUnits(options?: {
  today?: string;
  progressDir?: string;
  dataDir?: string;
  rootDir?: string;
}): DueTodayResponse {
  const today = options?.today ?? formatLocalDate();
  const progressDir = options?.progressDir ?? getProgressDir();
  const dataDir = options?.dataDir ?? getDrillsDataDir();
  const rootDir = options?.rootDir ?? getWorkspaceRoot();

  const schedule = readReviewSchedule(progressDir);
  const latestDrills = findLatestDrillsByUnit(dataDir);
  const idMapTitles = loadIdMapTitles(rootDir);
  const l4Units = unitsWithL4Challenge(dataDir, progressDir);

  const units: DueTodayUnit[] = [];
  const unitMastery: Record<string, UnitMasteryContext> = {};
  for (const [unitCode, entry] of Object.entries(schedule)) {
    if (!entry || typeof entry !== "object") continue;
    const title =
      plainTitle(typeof entry.title === "string" ? entry.title : "") ||
      plainTitle(idMapTitles.get(unitCode)) ||
      unitCode;
    const mastery = clampMastery(entry.mastery);
    const masteryCap = resolveMasteryCap(unitCode, mastery, entry.masteryCap, l4Units);
    unitMastery[unitCode] = {
      unitCode,
      title,
      mastery,
      masteryCap,
    };

    const rawNext = typeof entry.nextReview === "string" ? entry.nextReview.trim().slice(0, 10) : "";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(rawNext) || rawNext > today) {
      continue;
    }
    const rawLast =
      typeof entry.lastReviewed === "string" && entry.lastReviewed.trim()
        ? entry.lastReviewed.trim().slice(0, 10)
        : null;
    const drillId = latestDrills.get(unitCode) ?? null;
    const href = drillId ? drillHref(drillId) : null;

    units.push({
      unitCode,
      title,
      mastery,
      lastReviewed: rawLast,
      nextReview: rawNext,
      drillId,
      href: href && href !== "/" ? href : null,
      masteryCap,
    });
  }

  units.sort((a, b) => {
    if (a.nextReview !== b.nextReview) return a.nextReview.localeCompare(b.nextReview);
    return a.unitCode.localeCompare(b.unitCode);
  });

  return { today, units, unitMastery };
}

/** Read-only lookup of current `_review_schedule.json` entries for a list of unit codes. */
export function getReviewScheduleForUnits(
  unitCodes: readonly string[],
  options?: {
    progressDir?: string;
    dataDir?: string;
    rootDir?: string;
  }
): Record<string, ReviewScheduleEntry> {
  const progressDir = options?.progressDir ?? getProgressDir();
  const dataDir = options?.dataDir ?? getDrillsDataDir();
  const rootDir = options?.rootDir ?? getWorkspaceRoot();

  const schedule = readReviewSchedule(progressDir);
  const idMapTitles = loadIdMapTitles(rootDir);
  const l4Units = unitsWithL4Challenge(dataDir, progressDir);

  const result: Record<string, ReviewScheduleEntry> = {};
  for (const rawCode of unitCodes) {
    const unitCode = rawCode.trim();
    if (!unitCode) continue;
    const entry = schedule[unitCode];
    if (!entry || typeof entry !== "object") {
      const title = plainTitle(idMapTitles.get(unitCode)) || unitCode;
      result[unitCode] = {
        title,
        mastery: null,
        lastReviewed: null,
        nextReview: null,
        masteryCap: null,
      };
      continue;
    }
    const mastery = typeof entry.mastery === "number" ? clampMastery(entry.mastery) : null;
    const rawLast =
      typeof entry.lastReviewed === "string" && entry.lastReviewed.trim()
        ? entry.lastReviewed.trim().slice(0, 10)
        : null;
    const rawNext =
      typeof entry.nextReview === "string" && entry.nextReview.trim()
        ? entry.nextReview.trim().slice(0, 10)
        : null;
    const title =
      plainTitle(typeof entry.title === "string" ? entry.title : "") ||
      plainTitle(idMapTitles.get(unitCode)) ||
      unitCode;

    result[unitCode] = {
      title,
      mastery,
      lastReviewed: rawLast,
      nextReview: rawNext,
      masteryCap:
        mastery !== null
          ? resolveMasteryCap(unitCode, mastery, entry.masteryCap, l4Units)
          : null,
    };
  }
  return result;
}
