import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import { getDrillsDataDir, getPythonBin, getWorkspaceRoot } from "@/lib/paths";

export async function POST(req: NextRequest) {
  try {
    const { unitCode = "MTH-T02-C01-U01", count = 5, difficulty = "ALL" } =
      await req.json();

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const engineModule = unitCode.startsWith("PRG-")
      ? "code_engine.generate"
      : "math_engine.generate";

    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
    ].join(path.delimiter);

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(
        pythonBin,
        [
          "-m",
          engineModule,
          "--unit",
          unitCode,
          "--count",
          String(count),
          "--difficulty",
          String(difficulty),
        ],
        {
          cwd: rootDir,
          env: {
            ...process.env,
            PYTHONPATH: pythonPath,
            DRILLS_DATA_DIR: getDrillsDataDir(),
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
              { ok: false, error: stderr || `Exited with code ${code}` },
              { status: 500 }
            )
          );
          return;
        }

        // Parse generated file path from stdout: [Verified & Saved] drills/data/.../DRL-....json
        const match = stdout.match(/\[Verified & Saved\]\s+([^\s]+)/);
        if (match && match[1]) {
          const filePath = match[1];
          const drillId = path.basename(filePath, ".json");
          resolve(
            NextResponse.json({ ok: true, drillId, localFilePath: filePath })
          );
        } else {
          resolve(
            NextResponse.json({ ok: true, message: stdout })
          );
        }
      });
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      { ok: false, error: errMsg },
      { status: 500 }
    );
  }
}
