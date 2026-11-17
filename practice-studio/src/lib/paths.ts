import path from "path";
import fs from "fs";

/**
 * Returns the directory that holds `math_engine`, `drills/data`, and `.venv`.
 * Supports both standalone execution (inside practice-studio/) and parent repo execution.
 */
export function getWorkspaceRoot(): string {
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

export function getPythonBin(rootDir: string): string {
  const localVenv = path.join(rootDir, ".venv", "bin", "python");
  if (fs.existsSync(localVenv)) {
    return localVenv;
  }
  const studioVenv = path.join(rootDir, "practice-studio", ".venv", "bin", "python");
  if (fs.existsSync(studioVenv)) {
    return studioVenv;
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
  if (path.basename(full).startsWith(".env")) return null;
  return full;
}

/** Validates an ID used as a path segment (drillId, unitCode). */
export function isSafeId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
}

/** Where learner progress lives (progress/<DRILL_ID>.json); mirrors progress_store.py. */
export function getProgressDir(): string {
  if (process.env.PROGRESS_DIR) {
    return path.resolve(process.env.PROGRESS_DIR);
  }
  const pilot = (process.env.LEARNINGOS_PILOT || "").trim().toLowerCase();
  if (pilot === "1" || pilot === "true" || pilot === "yes") {
    return path.join(getWorkspaceRoot(), "pilot", "progress");
  }
  return path.join(getWorkspaceRoot(), "progress");
}

/** Locate a drill JSON file under getDrillsDataDir() by drillId. */
export function findDrillFilePath(drillId: string): string | null {
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
