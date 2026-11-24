import { spawn } from "child_process";

export const DEFAULT_DRILL_SYNC_TIMEOUT_MS = 90_000;

export interface NotionDrillSyncSpawnArgs {
  pythonBin: string;
  args: string[];
  cwd: string;
  env: NodeJS.ProcessEnv;
  stdinPayload: string;
  timeoutMs?: number;
}

export interface NotionDrillSyncProcessResult {
  code: number | null;
  stdout: string;
  stderr: string;
  timedOut?: boolean;
}

export interface NotionSyncRetry {
  drillPageId: string;
  failedSteps: string[];
  cleanupBlockIds: string[];
}

export type NotionDrillSyncSpawner = (
  spawnArgs: NotionDrillSyncSpawnArgs
) => Promise<NotionDrillSyncProcessResult>;

let activeTimeoutMs: number = DEFAULT_DRILL_SYNC_TIMEOUT_MS;

export const spawnNotionDrillSync: NotionDrillSyncSpawner = ({
  pythonBin,
  args,
  cwd,
  env,
  stdinPayload,
  timeoutMs = activeTimeoutMs,
}) =>
  new Promise<NotionDrillSyncProcessResult>((resolve) => {
    const useProcessGroup = process.platform !== "win32";
    const proc = spawn(pythonBin, args, { cwd, env, detached: useProcessGroup });
    let stdout = "";
    let stderr = "";
    let settled = false;
    let closed = false;
    let timeoutMessage: string | null = null;
    let timeoutHandle: ReturnType<typeof setTimeout> | null = null;
    let killHandle: ReturnType<typeof setTimeout> | null = null;

    const clearTimers = () => {
      if (timeoutHandle !== null) {
        clearTimeout(timeoutHandle);
        timeoutHandle = null;
      }
      if (killHandle !== null) {
        clearTimeout(killHandle);
        killHandle = null;
      }
    };

    const finish = (result: NotionDrillSyncProcessResult) => {
      if (settled) return;
      settled = true;
      clearTimers();
      resolve(result);
    };

    const signalTree = (signal: NodeJS.Signals) => {
      try {
        if (useProcessGroup && proc.pid) process.kill(-proc.pid, signal);
        else proc.kill(signal);
      } catch (err) {
        if ((err as NodeJS.ErrnoException).code !== "ESRCH") {
          stderr += `${String(err)}\n`;
        }
      }
    };

    const processGroupExists = () => {
      if (!useProcessGroup || !proc.pid) return false;
      try {
        process.kill(-proc.pid, 0);
        return true;
      } catch (err) {
        return (err as NodeJS.ErrnoException).code !== "ESRCH";
      }
    };

    const finishTimeout = () => finish({
      code: null,
      stdout,
      stderr: [stderr.trim(), timeoutMessage].filter(Boolean).join("\n"),
      timedOut: true,
    });

    if (typeof timeoutMs === "number" && Number.isFinite(timeoutMs) && timeoutMs > 0) {
      timeoutHandle = setTimeout(() => {
        timeoutHandle = null;
        const timeoutLabel =
          timeoutMs >= 1_000 ? `${Math.round(timeoutMs / 1_000)}s` : `${timeoutMs}ms`;
        timeoutMessage = `Notion sync timed out after ${timeoutLabel}.`;
        signalTree("SIGTERM");
        killHandle = setTimeout(() => {
          killHandle = null;
          signalTree("SIGKILL");
          if (closed) finishTimeout();
        }, 1_000);
      }, timeoutMs);
    }

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("error", (err) => {
      if (timeoutMessage) return;
      const msg = err instanceof Error ? err.message : String(err);
      finish({
        code: null,
        stdout,
        stderr: stderr ? `${stderr.trim()}\n${msg}` : msg,
      });
    });

    proc.on("close", (code) => {
      closed = true;
      if (!timeoutMessage) finish({ code, stdout, stderr });
      // A descendant may survive its parent and close its own streams early.
      else if (!killHandle || !processGroupExists()) finishTimeout();
    });

    proc.stdin.on("error", () => {
      // Ignore EPIPE when the child exits before consuming stdin.
    });
    proc.stdin.write(stdinPayload);
    proc.stdin.end();
  });

let activeSpawner: NotionDrillSyncSpawner = spawnNotionDrillSync;

/** Override the child_process spawner in unit tests so Notion is never called. */
export function setNotionDrillSyncSpawnerForTests(
  spawner: NotionDrillSyncSpawner | null
): void {
  activeSpawner = spawner ?? spawnNotionDrillSync;
}

/** Override the child_process sync timeout in unit tests (pass null to restore default). */
export function setNotionDrillSyncTimeoutForTests(timeoutMs: number | null): void {
  activeTimeoutMs =
    typeof timeoutMs === "number" && Number.isFinite(timeoutMs) && timeoutMs > 0
      ? timeoutMs
      : DEFAULT_DRILL_SYNC_TIMEOUT_MS;
}

export const DRILL_SYNC_INLINE_SCRIPT = `
import json, sys
from notion_sync.drill_sync import sync_drill_to_notion
payload = json.loads(sys.stdin.read())
res = sync_drill_to_notion(payload["doc"], save_local=False, studio_results=True, retry=payload.get("retry"))
print(json.dumps(res))
`;

export async function runNotionDrillSync(options: {
  mergedDoc: Record<string, unknown>;
  rootDir: string;
  pythonBin: string;
  dataDir: string;
  isDryRun: boolean;
  timeoutMs?: number;
  retry?: NotionSyncRetry;
}): Promise<NotionDrillSyncProcessResult> {
  const { mergedDoc, rootDir, pythonBin, dataDir, isDryRun, timeoutMs } = options;
  return activeSpawner({
    pythonBin,
    args: ["-c", DRILL_SYNC_INLINE_SCRIPT],
    cwd: rootDir,
    env: {
      ...process.env,
      PYTHONPATH: rootDir,
      DRILLS_DATA_DIR: dataDir,
      NOTION_DRY_RUN: isDryRun ? "1" : process.env.NOTION_DRY_RUN || "",
    },
    stdinPayload: JSON.stringify({ doc: mergedDoc, retry: options.retry }),
    timeoutMs: timeoutMs ?? activeTimeoutMs,
  });
}
