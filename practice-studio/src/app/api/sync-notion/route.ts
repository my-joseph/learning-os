import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { getPythonBin, getWorkspaceRoot } from "@/lib/paths";

export async function POST(req: NextRequest) {
  try {
    const drillDoc = await req.json();
    const drillId = drillDoc.drillId;
    const unitCode = drillDoc.unitCode || "MTH-T02-C01-U01";

    if (!drillId) {
      return NextResponse.json({ ok: false, error: "Missing drillId" }, { status: 400 });
    }

    const rootDir = getWorkspaceRoot();
    const unitDir = path.join(rootDir, "drills", "data", unitCode);
    if (!fs.existsSync(unitDir)) {
      fs.mkdirSync(unitDir, { recursive: true });
    }

    const targetPath = path.join(unitDir, `${drillId}.json`);
    drillDoc.localFilePath = targetPath;
    fs.writeFileSync(targetPath, JSON.stringify(drillDoc, null, 2), "utf-8");

    // Call python notion sync helper
    const pythonBin = getPythonBin(rootDir);

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(
        pythonBin,
        [
          "-c",
          `
import json, sys
from drill_sync import sync_drill_to_notion
doc = json.loads(sys.stdin.read())
res = sync_drill_to_notion(doc)
print(json.dumps(res))
`,
        ],
        {
          cwd: rootDir,
          env: { ...process.env, PYTHONPATH: rootDir },
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
