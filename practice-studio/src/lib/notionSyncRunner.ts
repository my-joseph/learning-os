import { spawn } from "child_process";

export interface NotionDrillSyncSpawnArgs {
  pythonBin: string;
  args: string[];
  cwd: string;
  env: NodeJS.ProcessEnv;
  stdinPayload: string;
}

export interface NotionDrillSyncProcessResult {
  code: number | null;
  stdout: string;
  stderr: string;
}

export type NotionDrillSyncSpawner = (
  spawnArgs: NotionDrillSyncSpawnArgs
) => Promise<NotionDrillSyncProcessResult>;

const defaultDrillSyncSpawner: NotionDrillSyncSpawner = ({
  pythonBin,
  args,
  cwd,
  env,
  stdinPayload,
}) =>
  new Promise<NotionDrillSyncProcessResult>((resolve) => {
    const proc = spawn(pythonBin, args, { cwd, env });
    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    proc.on("close", (code) => {
      resolve({ code, stdout, stderr });
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

/**
 * Rehydrates canonical server drill content (steps, answerPlain, solutionCode, etc.)
 * while overlaying the learner's client problem states and sessionSummary.
 */
export function mergeDrillForNotionSync(
  serverDoc: Record<string, unknown> | null,
  clientDoc: Record<string, unknown>
): Record<string, unknown> {
  const clientStateById = new Map<string, unknown>();
  const clientProblems = Array.isArray(clientDoc.problems) ? clientDoc.problems : [];
  for (const p of clientProblems) {
    if (p && typeof p === "object" && typeof (p as { id?: unknown }).id === "string") {
      const probObj = p as { id: string; state?: unknown };
      if (probObj.state) {
        clientStateById.set(probObj.id, probObj.state);
      }
    }
  }

  if (!serverDoc) {
    return clientDoc;
  }

  return {
    ...serverDoc,
    ...(clientDoc.sessionSummary ? { sessionSummary: clientDoc.sessionSummary } : {}),
    ...(clientDoc.dryRun !== undefined ? { dryRun: clientDoc.dryRun } : {}),
    problems: Array.isArray(serverDoc.problems)
      ? (serverDoc.problems as Array<Record<string, unknown>>).map((sp) => {
          const pid = typeof sp.id === "string" ? sp.id : "";
          return clientStateById.has(pid)
            ? { ...sp, state: clientStateById.get(pid) }
            : sp;
        })
      : clientDoc.problems,
  };
}

export const DRILL_SYNC_INLINE_SCRIPT = `
import json, sys
from notion_sync.drill_sync import sync_drill_to_notion
doc = json.loads(sys.stdin.read())
res = sync_drill_to_notion(doc)
print(json.dumps(res))
`;

export async function runNotionDrillSync(options: {
  mergedDoc: Record<string, unknown>;
  rootDir: string;
  pythonBin: string;
  dataDir: string;
  isDryRun: boolean;
}): Promise<NotionDrillSyncProcessResult> {
  const { mergedDoc, rootDir, pythonBin, dataDir, isDryRun } = options;
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
  });
}
