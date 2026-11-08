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
