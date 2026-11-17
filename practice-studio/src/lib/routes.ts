export type Workspace = "math" | "code";

export type LegacyQueryParams =
  | URLSearchParams
  | { get(name: string): string | null }
  | Record<string, string | string[] | undefined>
  | null
  | undefined;

export interface ParsedLegacyQuery {
  drillId: string;
  qid?: string;
}

/**
 * Return true when `value` is a valid project lab ID (`LAB-...`).
 */
export function isLabId(value: unknown): boolean {
  if (typeof value !== "string") return false;
  const normalized = value.trim();
  if (!normalized || normalized.length > 128) return false;
  return /^LAB-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/i.test(normalized);
}

/**
 * Determine the studio workspace for a drill or lab ID by prefix.
 * `DRL-MTH*` and `DRL-PHY*` map to `"math"`; `DRL-PRG*` and `LAB-*` map to `"code"`.
 */
export function subjectOf(drillId: string): Workspace | null {
  if (typeof drillId !== "string") return null;
  const normalized = drillId.trim();
  if (!normalized) return null;
  if (/^DRL-(MTH|PHY)(?:-|$)/i.test(normalized)) return "math";
  if (/^DRL-PRG(?:-|$)/i.test(normalized)) return "code";
  if (isLabId(normalized)) return "code";
  return null;
}

/**
 * Build the canonical studio URL for a project lab and optional milestone ID (`M1..Mn`).
 * Falls back to `"/"` when `labId` is not a valid lab ID.
 */
export function labHref(labId: string, milestoneId?: string | null): string {
  if (!isLabId(labId)) return "/";
  const base = `/code/lab/${encodeURIComponent(labId.trim())}`;
  const trimmedM = typeof milestoneId === "string" ? milestoneId.trim() : "";
  if (!trimmedM) return base;
  return `${base}?m=${encodeURIComponent(trimmedM)}`;
}

/**
 * Build the canonical studio URL for a drill (or lab) and optional question/milestone ID.
 * Falls back to `"/"` when the ID does not belong to a known workspace.
 */
export function drillHref(drillId: string, qid?: string | null): string {
  if (isLabId(drillId)) {
    return labHref(drillId, qid);
  }
  const workspace = subjectOf(drillId);
  if (!workspace) return "/";

  const base = `/${workspace}/${encodeURIComponent(drillId.trim())}`;
  const trimmedQ = typeof qid === "string" ? qid.trim() : "";
  if (!trimmedQ) return base;
  return `${base}?q=${encodeURIComponent(trimmedQ)}`;
}

function readParam(params: LegacyQueryParams, key: string): string | null {
  if (!params) return null;
  if (typeof (params as { get?: unknown }).get === "function") {
    return (params as { get(name: string): string | null }).get(key);
  }
  const record = params as Record<string, string | string[] | undefined>;
  const value = record[key];
  if (Array.isArray(value)) return value[0] ?? null;
  return typeof value === "string" ? value : null;
}

/**
 * Parse legacy `/?drill=<ID>&q=<QID>` query parameters.
 * Returns `null` when `drill` is absent or blank.
 */
export function parseLegacyQuery(params: LegacyQueryParams): ParsedLegacyQuery | null {
  const rawDrill = readParam(params, "drill");
  const drillId = typeof rawDrill === "string" ? rawDrill.trim() : "";
  if (!drillId) return null;

  const rawQ = readParam(params, "q") ?? readParam(params, "m");
  const qid = typeof rawQ === "string" ? rawQ.trim() : "";
  return qid ? { drillId, qid } : { drillId };
}

/**
 * Resolve the problem index matching `qid` by problem ID.
 * Ignores unknown or missing IDs and falls back to index `0`.
 */
export function findProblemIndex(
  problems: readonly { id: string }[],
  qid?: string | null
): number {
  if (!problems.length || typeof qid !== "string") return 0;
  const target = qid.trim();
  if (!target) return 0;
  const exactIndex = problems.findIndex((problem) => problem.id === target);
  if (exactIndex >= 0) return exactIndex;
  const upper = target.toUpperCase();
  const ciIndex = problems.findIndex((problem) => problem.id.toUpperCase() === upper);
  return ciIndex >= 0 ? ciIndex : 0;
}

/**
 * Resolve the milestone index matching `m` (e.g. `M2` or `m2`) by milestone ID.
 * Ignores unknown or missing IDs and falls back to index `0` (`M1`).
 */
export function findMilestoneIndex(
  milestones: readonly { id: string }[],
  m?: string | null
): number {
  return findProblemIndex(milestones, m);
}

/** Infer workspace for a drill list item using its drill ID prefix, then subject fallback. */
export function workspaceOfListItem(item: {
  drillId: string;
  subject?: "MATH" | "PRG";
}): Workspace | null {
  const byId = subjectOf(item.drillId);
  if (byId) return byId;
  if (item.subject === "PRG") return "code";
  if (item.subject === "MATH") return "math";
  return null;
}

/**
 * Pick the target drill ID for a workspace switch: the last opened drill in that
 * workspace if still present, otherwise the first drill of that workspace.
 */
export function resolveWorkspaceDrill(
  drills: readonly { drillId: string; subject?: "MATH" | "PRG" }[],
  workspace: Workspace,
  lastDrillId?: string | null
): string | null {
  const matching = drills.filter((d) => workspaceOfListItem(d) === workspace);
  if (matching.length === 0) return null;

  const candidate = typeof lastDrillId === "string" ? lastDrillId.trim() : "";
  if (candidate && matching.some((d) => d.drillId === candidate)) {
    return candidate;
  }
  return matching[0].drillId;
}

/**
 * Pick the landing drill ID for plain `/`: the last opened drill if still present
 * and routable, otherwise the first routable drill in the list.
 */
export function resolveLandingDrill(
  drills: readonly { drillId: string }[],
  lastDrillId?: string | null
): string | null {
  const candidate = typeof lastDrillId === "string" ? lastDrillId.trim() : "";
  if (
    candidate &&
    subjectOf(candidate) !== null &&
    drills.some((d) => d.drillId === candidate)
  ) {
    return candidate;
  }
  const firstRoutable = drills.find((d) => subjectOf(d.drillId) !== null);
  return firstRoutable ? firstRoutable.drillId : null;
}
