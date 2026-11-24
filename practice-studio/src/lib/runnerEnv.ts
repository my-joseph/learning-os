import type { ChildProcess } from "child_process";

export const MAX_RUNNER_OUTPUT_BYTES = 2 * 1024 * 1024; // 2 MiB per stream
export const RUN_TESTS_TIMEOUT_MS = 35_000;
export const REVIEW_RUN_TIMEOUT_MS = 35_000;

const BASE_ALLOWED_ENV_KEYS = [
  "PATH",
  "LANG",
  "LC_ALL",
  "TZ",
  "TMPDIR",
  "TEMP",
  "TMP",
  "SYSTEMROOT",
] as const;

const WORKSPACE_HINT_ENV_KEYS = [
  "DRILLS_DATA_DIR",
  "LABS_DIR",
  "WORKSPACE_DIR",
  "PROGRESS_DIR",
  "LEARNINGOS_PILOT",
] as const;

/**
 * Build an explicit allowlisted environment for spawning PRG Python runner helpers
 * from Practice Studio. Never forwards `NOTION_TOKEN`, `NOTION_DATABASE_ID`,
 * `NODE_OPTIONS`, or arbitrary parent process secrets.
 */
export function buildPrgPythonEnv(
  rootDir: string,
  pythonPath: string,
  options: { includeWorkspaceHints?: boolean } = {}
): NodeJS.ProcessEnv {
  const clean: Record<string, string> = {
    LEARNINGOS_ROOT: rootDir,
    PYTHONPATH: pythonPath,
  };

  for (const key of BASE_ALLOWED_ENV_KEYS) {
    const val = process.env[key];
    if (typeof val === "string" && val.length > 0) {
      clean[key] = val;
    }
  }

  if (options.includeWorkspaceHints) {
    for (const key of WORKSPACE_HINT_ENV_KEYS) {
      const val = process.env[key];
      if (typeof val === "string" && val.length > 0) {
        clean[key] = val;
      }
    }
  }

  return clean as NodeJS.ProcessEnv;
}

/**
 * Terminate a spawned runner and its entire POSIX process group when detached.
 */
export function killProcessTree(proc: ChildProcess): void {
  if (proc.exitCode !== null || proc.signalCode !== null) return;
  const pid = proc.pid;
  if (pid && process.platform !== "win32") {
    try {
      process.kill(-pid, "SIGTERM");
    } catch {
      try {
        proc.kill("SIGTERM");
      } catch {
        // Process already exited.
      }
    }
    const escalate = setTimeout(() => {
      if (proc.exitCode !== null || proc.signalCode !== null) return;
      try {
        process.kill(-pid, "SIGKILL");
      } catch {
        try {
          proc.kill("SIGKILL");
        } catch {
          // Process already exited.
        }
      }
    }, 250);
    escalate.unref();
    return;
  }

  try {
    proc.kill("SIGKILL");
  } catch {
    // Process already exited.
  }
}

/**
 * Append chunk to a bounded string buffer and return whether the cap was exceeded.
 */
export function appendBoundedOutput(
  current: string,
  chunk: Buffer | string,
  maxBytes: number = MAX_RUNNER_OUTPUT_BYTES
): { value: string; exceeded: boolean } {
  const text = typeof chunk === "string" ? chunk : chunk.toString("utf-8");
  const remaining = maxBytes - Buffer.byteLength(current, "utf-8");
  if (remaining <= 0) {
    return { value: current, exceeded: true };
  }
  const chunkBytes = Buffer.byteLength(text, "utf-8");
  if (chunkBytes <= remaining) {
    return { value: current + text, exceeded: false };
  }
  const slice = Buffer.from(text, "utf-8").subarray(0, remaining).toString("utf-8");
  return { value: current + slice, exceeded: true };
}
