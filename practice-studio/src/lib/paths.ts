import path from "path";
import fs from "fs";

/**
 * Returns the directory that holds `math_engine`, `drills/data`, and `.venv`.
 * Supports both standalone execution (inside practice-studio/) and parent repo execution.
 */
export function getWorkspaceRoot(): string {
  if (process.env.LEARNINGOS_ROOT) {
    return path.resolve(process.env.LEARNINGOS_ROOT);
  }
  const cwd = process.cwd();
  const parent = path.resolve(cwd, "..");

  // If parent contains both math_engine and code_engine, that is the true project root
  if (
    fs.existsSync(path.join(parent, "math_engine")) &&
    fs.existsSync(path.join(parent, "code_engine"))
  ) {
    return parent;
  }

  // Check if current directory has math_engine
  if (fs.existsSync(path.join(cwd, "math_engine"))) {
    return cwd;
  }

  return parent;
}

export function getDrillsDataDir(): string {
  if (process.env.DRILLS_DATA_DIR) {
    return path.resolve(process.env.DRILLS_DATA_DIR);
  }
  return path.join(getWorkspaceRoot(), "drills", "data");
}

/** Directory holding variant bank JSON files (`drills/variants/<UNIT>.json`). */
export function getVariantsDir(): string {
  if (process.env.VARIANTS_DIR) {
    return path.resolve(process.env.VARIANTS_DIR);
  }
  return path.join(getWorkspaceRoot(), "drills", "variants");
}

export function getLabsDir(): string {
  if (process.env.LABS_DIR) {
    return path.resolve(process.env.LABS_DIR);
  }
  return path.join(getWorkspaceRoot(), "labs");
}

export function getPythonBin(rootDir: string): string {
  const candidates = [
    path.join(rootDir, ".venv", "bin", "python"),
    path.join(rootDir, "practice-studio", ".venv", "bin", "python"),
    path.resolve(process.cwd(), "..", ".venv", "bin", "python"),
    path.resolve(process.cwd(), ".venv", "bin", "python"),
  ];
  for (const cand of candidates) {
    if (fs.existsSync(cand)) {
      return cand;
    }
  }
  return "python3";
}

/**
 * Resolves a user-supplied file path and guarantees it stays inside the
 * project root. Returns null for anything outside (e.g. `/etc/passwd`,
 * `../../.ssh/id_rsa`, or the `.env` file that holds the Notion token).
 */
export function resolveInsideRoot(relOrAbs: string, rootDir: string = getWorkspaceRoot()): string | null {
  if (typeof relOrAbs !== "string" || !relOrAbs.trim()) return null;
  const root = path.resolve(rootDir);
  const full = path.resolve(root, relOrAbs);
  const rel = path.relative(root, full);
  if (rel === "" || rel.startsWith("..") || path.isAbsolute(rel)) return null;
  const segments = rel.split(/[\\/]+/);
  if (segments.includes("_reference") || segments.includes(".canonical")) return null;
  const base = path.basename(full);
  if (base.startsWith(".env") || base.includes(".hidden.")) return null;
  return full;
}

/** Validates an ID used as a path segment (drillId, unitCode). */
export function isSafeId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
}

/** True when LEARNINGOS_PILOT is enabled ('1', 'true', 'yes'); mirrors progress_store.pilot_mode(). */
export function isPilotMode(): boolean {
  const pilot = (process.env.LEARNINGOS_PILOT || "").trim().toLowerCase();
  return pilot === "1" || pilot === "true" || pilot === "yes";
}

/** Base directory holding materialized drill workspaces (`pilot/workspace` in pilot mode, else `drills/workspace`). */
export function getDrillWorkspacesDir(rootDir: string = getWorkspaceRoot()): string {
  const sub = isPilotMode()
    ? path.join("pilot", "workspace")
    : path.join("drills", "workspace");
  return path.resolve(rootDir, sub);
}

/** Materialized workspace directory for a single drill (`<wsBase>/<drillId>`). */
export function getDrillWorkspaceDir(
  drillId: string,
  rootDir: string = getWorkspaceRoot()
): string | null {
  if (!isSafeId(drillId)) return null;
  return path.join(getDrillWorkspacesDir(rootDir), drillId);
}

/** Base directory holding active project lab workspaces (`LABS_DIR`, else `pilot/labs` in pilot mode, else `labs`). */
export function getLabWorkspacesDir(rootDir: string = getWorkspaceRoot()): string {
  if (process.env.LABS_DIR) {
    return path.resolve(process.env.LABS_DIR);
  }
  const sub = isPilotMode() ? path.join("pilot", "labs") : "labs";
  return path.resolve(rootDir, sub);
}

/** Active workspace directory for a single lab (`<labWsBase>/<labId>`). */
export function getLabWorkspaceDir(
  labId: string,
  rootDir: string = getWorkspaceRoot()
): string | null {
  if (!isSafeId(labId)) return null;
  return path.join(getLabWorkspacesDir(rootDir), labId);
}

/**
 * Maps a relative workspace file path (`drills/workspace/<drillId>/...` or
 * `pilot/workspace/<drillId>/...`) to the active workspace directory for the
 * current mode (`pilot/workspace/<drillId>/...` in pilot mode, else
 * `drills/workspace/<drillId>/...`). Leaves other paths unchanged so
 * traversal/escape checks can reject them.
 */
export function remapWorkspaceFileForMode(
  relOrAbs: string,
  drillId: string
): string {
  if (typeof relOrAbs !== "string" || !isSafeId(drillId)) return relOrAbs;
  const trimmed = relOrAbs.trim();
  if (!trimmed || path.isAbsolute(trimmed)) return relOrAbs;
  const normalized = trimmed.replace(/\\/g, "/").replace(/^\.\/+/, "");
  const activePrefix = isPilotMode()
    ? `pilot/workspace/${drillId}/`
    : `drills/workspace/${drillId}/`;
  const altPrefix = isPilotMode()
    ? `drills/workspace/${drillId}/`
    : `pilot/workspace/${drillId}/`;
  if (normalized.startsWith(altPrefix)) {
    return activePrefix + normalized.slice(altPrefix.length);
  }
  return relOrAbs;
}

function isStrictlyInsideDir(baseDir: string, targetPath: string): boolean {
  const rel = path.relative(baseDir, targetPath);
  return rel !== "" && !rel.startsWith("..") && !path.isAbsolute(rel);
}

/**
 * Resolves a file path and guarantees it stays strictly inside the given drill's
 * workspace directory (`<root>/drills/workspace/<drillId>/` or
 * `<root>/pilot/workspace/<drillId>/` in pilot mode), rejecting `..` traversal,
 * hidden/reference paths, and symlink escapes (including dangling symlinks).
 */
export function resolveInsideDrillWorkspace(
  relOrAbs: string,
  drillId: string,
  rootDir: string = getWorkspaceRoot()
): string | null {
  if (typeof relOrAbs !== "string" || !relOrAbs.trim() || relOrAbs.includes("\0")) {
    return null;
  }
  const wsDir = getDrillWorkspaceDir(drillId, rootDir);
  if (!wsDir) return null;

  const root = path.resolve(rootDir);
  const mappedRelOrAbs = remapWorkspaceFileForMode(relOrAbs, drillId);
  const candidate = path.resolve(root, mappedRelOrAbs);
  if (!isStrictlyInsideDir(wsDir, candidate)) return null;

  const rel = path.relative(wsDir, candidate);
  const segments = rel.split(/[\\/]+/);
  if (segments.includes("_reference") || segments.includes(".canonical")) return null;
  const base = path.basename(candidate);
  if (base.startsWith(".env") || base.includes(".hidden.")) return null;

  const realRoot = fs.existsSync(root) ? fs.realpathSync(root) : root;
  const wsRelFromRoot = path.relative(root, wsDir);
  const expectedRealWsDir = path.join(realRoot, wsRelFromRoot);

  // Verify no existing ancestor between root and wsDir is a symlink redirecting outside its canonical path.
  let ancestorCursor = root;
  for (const seg of wsRelFromRoot.split(/[\\/]+/)) {
    ancestorCursor = path.join(ancestorCursor, seg);
    let st: fs.Stats;
    try {
      st = fs.lstatSync(ancestorCursor);
    } catch {
      break;
    }
    if (st.isSymbolicLink()) {
      return null;
    }
  }

  if (!fs.existsSync(wsDir)) {
    return path.join(expectedRealWsDir, rel);
  }

  const realWsDir = fs.realpathSync(wsDir);
  if (realWsDir !== expectedRealWsDir) return null;

  // Walk every segment inside wsDir to reject symlink escapes and dangling symlinks.
  let segCursor = wsDir;
  for (const seg of segments) {
    segCursor = path.join(segCursor, seg);
    let st: fs.Stats;
    try {
      st = fs.lstatSync(segCursor);
    } catch {
      break;
    }
    if (st.isSymbolicLink()) {
      try {
        const realSeg = fs.realpathSync(segCursor);
        if (!isStrictlyInsideDir(realWsDir, realSeg)) return null;
      } catch {
        return null;
      }
    }
  }

  if (fs.existsSync(candidate)) {
    const realTarget = fs.realpathSync(candidate);
    if (!isStrictlyInsideDir(realWsDir, realTarget)) return null;
    return realTarget;
  }

  return path.join(realWsDir, rel);
}

/** Where learner progress lives (progress/<DRILL_ID>.json); mirrors progress_store.py. */
export function getProgressDir(): string {
  if (process.env.PROGRESS_DIR) {
    return path.resolve(process.env.PROGRESS_DIR);
  }
  if (isPilotMode()) {
    return path.join(getWorkspaceRoot(), "pilot", "progress");
  }
  return path.join(getWorkspaceRoot(), "progress");
}

/** Locate a drill JSON file under getDrillsDataDir() by drillId. */
function findDrillFilePath(drillId: string): string | null {
  if (!isSafeId(drillId)) return null;
  const dataDir = getDrillsDataDir();
  if (!fs.existsSync(dataDir)) return null;

  for (const entry of fs.readdirSync(dataDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const candidate = path.join(dataDir, entry.name, `${drillId}.json`);
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  const visit = (dir: string): string | null => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        const match = visit(fullPath);
        if (match) return match;
      } else if (entry.isFile() && entry.name === `${drillId}.json`) {
        return fullPath;
      }
    }
    return null;
  };
  return visit(dataDir);
}

/** Load an unredacted canonical drill document from drills/data on the server. */
export function loadDrillFromDisk(drillId: string): Record<string, unknown> | null {
  const filePath = findDrillFilePath(drillId);
  if (!filePath) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as Record<string, unknown>;
  } catch {
    return null;
  }
}

/** Load a specific problem and its parent drill document from drills/data on the server. */
export function loadProblemFromDisk(
  drillId: string,
  problemId: string
): { doc: Record<string, unknown>; problem: Record<string, unknown> } | null {
  if (!isSafeId(drillId) || !isSafeId(problemId)) return null;
  const doc = loadDrillFromDisk(drillId);
  if (!doc || !Array.isArray(doc.problems)) return null;
  const problem = (doc.problems as Array<Record<string, unknown>>).find(
    (p) => p && typeof p === "object" && p.id === problemId
  );
  if (!problem) return null;
  return { doc, problem };
}

/** Load an unredacted variant bank JSON file (`drills/variants/<unitCode>.json`) on the server. */
export function loadVariantBankFromDisk(
  unitCode: string
): { unitCode: string; variants: Array<Record<string, unknown>> } | null {
  if (!isSafeId(unitCode)) return null;
  const filePath = path.join(getVariantsDir(), `${unitCode}.json`);
  if (!fs.existsSync(filePath)) return null;
  try {
    const raw = JSON.parse(fs.readFileSync(filePath, "utf-8")) as Record<string, unknown>;
    if (!raw || typeof raw !== "object" || !Array.isArray(raw.variants)) return null;
    return {
      unitCode: typeof raw.unitCode === "string" ? raw.unitCode : unitCode,
      variants: raw.variants.filter(
        (v): v is Record<string, unknown> => Boolean(v && typeof v === "object")
      ),
    };
  } catch {
    return null;
  }
}

/** Locate an unredacted variant by `variantId` across `drills/variants/*.json` on the server. */
export function loadVariantFromDisk(
  variantId: string
): { unitCode: string; variant: Record<string, unknown> } | null {
  if (!isSafeId(variantId)) return null;
  const dir = getVariantsDir();
  if (!fs.existsSync(dir)) return null;

  const files = fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .sort();

  // Prefer the bank whose unitCode matches the prefix after "VAR-".
  if (variantId.startsWith("VAR-")) {
    const tail = variantId.slice(4);
    files.sort((a, b) => {
      const aMatch = tail.startsWith(a.slice(0, -5) + "-") ? 0 : 1;
      const bMatch = tail.startsWith(b.slice(0, -5) + "-") ? 0 : 1;
      return aMatch - bMatch || a.localeCompare(b);
    });
  }

  for (const file of files) {
    const unitCode = file.slice(0, -5);
    const bank = loadVariantBankFromDisk(unitCode);
    if (!bank) continue;
    const match = bank.variants.find((v) => v.variantId === variantId);
    if (match) {
      return { unitCode: bank.unitCode, variant: match };
    }
  }
  return null;
}

/** Load curriculum code -> title mappings from `id_map.json` at the workspace root. */
export function loadIdMapTitles(rootDir: string = getWorkspaceRoot()): Map<string, string> {
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
