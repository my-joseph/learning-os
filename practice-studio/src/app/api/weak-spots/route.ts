import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import {
  getDrillsDataDir,
  getPythonBin,
  getWorkspaceRoot,
  isSafeId,
} from "@/lib/paths";

export const dynamic = "force-dynamic";

const WEAK_SPOTS_TIMEOUT_MS = 15_000;

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const rawScope = searchParams.get("scope");
    const scope = rawScope ? rawScope.trim() : "";

    if (scope && !isSafeId(scope)) {
      return NextResponse.json({ error: "Invalid scope" }, { status: 400 });
    }

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);
    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
    ].join(path.delimiter);

    const args = ["-m", "scripts.weak_spots", ...(scope ? [scope] : []), "--json"];

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(pythonBin, args, {
        cwd: rootDir,
        env: {
          ...process.env,
          PYTHONPATH: pythonPath,
          DRILLS_DATA_DIR: getDrillsDataDir(),
        },
      });

      let stdout = "";
      let stderr = "";
      let timedOut = false;

      const timer = setTimeout(() => {
        timedOut = true;
        proc.kill("SIGKILL");
        resolve(NextResponse.json({ error: "Weak-spots lookup timed out" }, { status: 504 }));
      }, WEAK_SPOTS_TIMEOUT_MS);

      proc.stdout.on("data", (chunk) => {
        stdout += chunk.toString();
      });

      proc.stderr.on("data", (chunk) => {
        stderr += chunk.toString();
      });

      proc.on("close", (code) => {
        clearTimeout(timer);
        if (timedOut) return;

        if (code !== 0) {
          resolve(
            NextResponse.json(
              { error: stderr.trim() || stdout.trim() || `weak_spots exited with code ${code}` },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const parsed = JSON.parse(stdout.trim());
          resolve(NextResponse.json(parsed));
        } catch (err: unknown) {
          const errMsg = err instanceof Error ? err.message : String(err);
          resolve(
            NextResponse.json(
              { error: `Could not parse weak_spots output: ${errMsg}` },
              { status: 500 }
            )
          );
        }
      });
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}
