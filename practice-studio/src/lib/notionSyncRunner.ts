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

export type NotionDrillSyncSpawner = (
  spawnArgs: NotionDrillSyncSpawnArgs
) => Promise<NotionDrillSyncProcessResult>;

let activeTimeoutMs: number = DEFAULT_DRILL_SYNC_TIMEOUT_MS;

const defaultDrillSyncSpawner: NotionDrillSyncSpawner = ({
  pythonBin,
  args,
  cwd,
  env,
  stdinPayload,
  timeoutMs = activeTimeoutMs,
}) =>
  new Promise<NotionDrillSyncProcessResult>((resolve) => {
    const proc = spawn(pythonBin, args, { cwd, env });
    let stdout = "";
    let stderr = "";
    let settled = false;
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

    if (typeof timeoutMs === "number" && Number.isFinite(timeoutMs) && timeoutMs > 0) {
      timeoutHandle = setTimeout(() => {
        timeoutHandle = null;
        try {
          proc.kill("SIGTERM");
        } catch {
          // Process may have already exited.
        }
        killHandle = setTimeout(() => {
          killHandle = null;
          try {
            proc.kill("SIGKILL");
          } catch {
            // Process may have already exited.
          }
        }, 1_000);
        killHandle.unref?.();
        const timeoutLabel =
          timeoutMs >= 1_000 ? `${Math.round(timeoutMs / 1_000)}s` : `${timeoutMs}ms`;
        const timeoutMsg = `Notion sync timed out after ${timeoutLabel}.`;
        finish({
          code: null,
          stdout,
          stderr: stderr ? `${stderr.trim()}\n${timeoutMsg}` : timeoutMsg,
          timedOut: true,
        });
      }, timeoutMs);
    }

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("error", (err) => {
      const msg = err instanceof Error ? err.message : String(err);
      finish({
        code: null,
        stdout,
        stderr: stderr ? `${stderr.trim()}\n${msg}` : msg,
      });
    });

    proc.on("close", (code) => {
      finish({ code, stdout, stderr });
    });

    proc.stdin.on("error", () => {
      // Ignore EPIPE when the child exits before consuming stdin.
    });
    proc.stdin.write(stdinPayload);
    proc.stdin.end();
  });

let activeSpawner: NotionDrillSyncSpawner = defaultDrillSyncSpawner;

/** Override the child_process spawner in unit tests so Notion is never called. */
export function setNotionDrillSyncSpawnerForTests(
  spawner: NotionDrillSyncSpawner | null
): void {
  activeSpawner = spawner ?? defaultDrillSyncSpawner;
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
doc = json.loads(sys.stdin.read())
res = sync_drill_to_notion(doc, save_local=False, studio_results=True)
print(json.dumps(res))
`;

export async function runNotionDrillSync(options: {
  mergedDoc: Record<string, unknown>;
  rootDir: string;
  pythonBin: string;
  dataDir: string;
  isDryRun: boolean;
  timeoutMs?: number;
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
    stdinPayload: JSON.stringify(mergedDoc),
    timeoutMs: timeoutMs ?? activeTimeoutMs,
  });
}
