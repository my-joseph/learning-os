import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import { getDrillsDataDir, getPythonBin, getWorkspaceRoot, isSafeId } from "@/lib/paths";

export async function POST(req: NextRequest) {
  try {
    const drillDoc = await req.json();
    const drillId = drillDoc.drillId;
    const unitCode = drillDoc.unitCode || "MTH-T02-C01-U01";

    if (!drillId) {
      return NextResponse.json({ ok: false, error: "Missing drillId" }, { status: 400 });
    }
    if (!isSafeId(drillId) || !isSafeId(unitCode)) {
      return NextResponse.json({ ok: false, error: "Invalid drillId or unitCode" }, { status: 400 });
    }

    // Progress is saved by notion_sync.drill_sync.save_drill_doc (progress/<DRILL_ID>.json);
    // the drill content file is never rewritten from the Studio.
    const dataDir = getDrillsDataDir();

    // Call python notion sync helper
    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const isDryRun =
      Boolean(drillDoc.dryRun) ||
      process.env.NOTION_DRY_RUN === "1" ||
      process.env.NOTION_DRY_RUN === "true";

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(
        pythonBin,
        [
          "-c",
          `
import json, sys
from notion_sync.drill_sync import sync_drill_to_notion
doc = json.loads(sys.stdin.read())
res = sync_drill_to_notion(doc)
print(json.dumps(res))
`,
        ],
        {
          cwd: rootDir,
          env: {
            ...process.env,
            PYTHONPATH: rootDir,
            DRILLS_DATA_DIR: dataDir,
            NOTION_DRY_RUN: isDryRun ? "1" : (process.env.NOTION_DRY_RUN || ""),
          },
        }
      );

      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        if (code !== 0) {
          resolve(
            NextResponse.json(
              { ok: false, error: stderr || `Sync helper exited with code ${code}` },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const res = JSON.parse(stdout);
          resolve(NextResponse.json(res));
        } catch {
          resolve(
            NextResponse.json(
              { ok: false, error: `Invalid response from sync helper: ${stdout}` },
              { status: 500 }
            )
          );
        }
      });

      proc.stdin.write(JSON.stringify(drillDoc));
      proc.stdin.end();
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
