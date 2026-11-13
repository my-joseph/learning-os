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
  return path.join(getWorkspaceRoot(), "progress");
}
