import fs from "fs";
import path from "path";
import { getDrillsDataDir, getProgressDir, getWorkspaceRoot } from "@/lib/paths";
import { drillHref } from "@/lib/routes";

export interface ReviewScheduleEntry {
  mastery?: number | null;
  lastReviewed?: string | null;
  nextReview?: string | null;
  title?: string | null;
}

export interface DueTodayUnit {
  unitCode: string;
  title: string;
  mastery: number;
  lastReviewed: string | null;
  nextReview: string;
  drillId: string | null;
  href: string | null;
}

export interface DueTodayResponse {
  today: string;
  units: DueTodayUnit[];
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
export function findLatestDrillsByUnit(dataDir: string): Map<string, string> {
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

function loadIdMapTitles(rootDir: string): Map<string, string> {
  const titles = new Map<string, string>();
  const idMapPath = path.join(rootDir, "id_map.json");
  if (!fs.existsSync(idMapPath)) return titles;
  try {
    const raw = JSON.parse(fs.readFileSync(idMapPath, "utf-8")) as Record<string, unknown>;
    for (const [key, val] of Object.entries(raw)) {
      if (val && typeof val === "object" && typeof (val as { title?: unknown }).title === "string") {
        titles.set(key, (val as { title: string }).title);
      }
    }
  } catch {
    return titles;
  }
  return titles;
}

export function readReviewSchedule(progressDir: string = getProgressDir()): Record<string, ReviewScheduleEntry> {
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

  const units: DueTodayUnit[] = [];
  for (const [unitCode, entry] of Object.entries(schedule)) {
    if (!entry || typeof entry !== "object") continue;
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
    const title =
      (typeof entry.title === "string" && entry.title.trim()) ||
      idMapTitles.get(unitCode) ||
      unitCode;

    units.push({
      unitCode,
      title,
      mastery: clampMastery(entry.mastery),
      lastReviewed: rawLast,
      nextReview: rawNext,
      drillId,
      href: href && href !== "/" ? href : null,
    });
  }

  units.sort((a, b) => {
    if (a.nextReview !== b.nextReview) return a.nextReview.localeCompare(b.nextReview);
    return a.unitCode.localeCompare(b.unitCode);
  });

  return { today, units };
}
