import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import {
  getPythonBin,
  getWorkspaceRoot,
  isSafeId,
  loadProblemFromDisk,
  resolveInsideRoot,
} from "@/lib/paths";
import { sanitizeCodeCheckError } from "@/lib/codeStatus";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const drillId = body.drillId || body.drill;
    const problemId = body.problemId || body.q;

    if (!drillId || !problemId || !isSafeId(drillId) || !isSafeId(problemId)) {
      return NextResponse.json(
        { error: "Missing or invalid drillId or problemId" },
        { status: 400 }
      );
    }

    const loaded = loadProblemFromDisk(drillId, problemId);
    if (!loaded) {
      return NextResponse.json(
        { error: "Drill or problem not found" },
        { status: 404 }
      );
    }

    const { problem } = loaded;
    // Server copy wins: load visibleTests, hiddenTests, and workspaceFile from drills/data.
    const visibleTests = Array.isArray(problem.visibleTests) ? problem.visibleTests : [];
    const hiddenTests = Array.isArray(problem.hiddenTests) ? problem.hiddenTests : [];
    const workspaceFile =
      typeof problem.workspaceFile === "string" && problem.workspaceFile
        ? problem.workspaceFile
        : body.workspaceFile;

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    let userCode = body.userCode || "";

    // Workspace-backed PRG tests always execute the source currently saved on disk.
    if (workspaceFile) {
      const fullPath = resolveInsideRoot(workspaceFile, rootDir);
      if (!fullPath) return NextResponse.json({ error: "Workspace file path is invalid" }, { status: 403 });
      if (!fs.existsSync(fullPath)) {
        return NextResponse.json({ error: "Workspace file is missing; materialize the workspace first" }, { status: 404 });
      }
      userCode = fs.readFileSync(fullPath, "utf-8");
    }

    if (!userCode.trim()) {
      return NextResponse.json(
        {
          allPassed: false,
          score: 0,
          passedCount: 0,
          totalCount: visibleTests.length + hiddenTests.length,
          visibleResults: [
            {
              name: "Empty Code",
              passed: false,
              error: "No implementation found. Write your solution in VS Code / Cursor or in the editor.",
            },
          ],
          hiddenPassed: 0,
          hiddenTotal: hiddenTests.length,
          executionTimeMs: 0,
        },
        { status: 200 }
      );
    }

    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
    ].join(path.delimiter);

    const payload = {
      userCode,
      visibleTests,
      hiddenTests,
    };

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(pythonBin, ["-m", "code_engine.test_runner"], {
        cwd: rootDir,
        env: { ...process.env, PYTHONPATH: pythonPath },
      });

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
          const rawErr = (stderr || `Exited with code ${code}`).split(`${rootDir}/`).join("");
          resolve(
            NextResponse.json(
              {
                allPassed: false,
                score: 0,
                passedCount: 0,
                totalCount: visibleTests.length + hiddenTests.length,
                visibleResults: [
                  {
                    name: "Test Runner Process Error",
                    passed: false,
                    error: sanitizeCodeCheckError(rawErr),
                  },
                ],
                hiddenPassed: 0,
                hiddenTotal: hiddenTests.length,
                executionTimeMs: 0,
                rawOutput: sanitizeCodeCheckError(
                  (stdout + "\n" + stderr).split(`${rootDir}/`).join("")
                ),
              },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const report = JSON.parse(stdout.trim());
          resolve(NextResponse.json({ ...report, userCodeUsed: userCode }));
        } catch (e: unknown) {
          const errMsg = e instanceof Error ? e.message : String(e);
          resolve(
            NextResponse.json(
              {
                allPassed: false,
                score: 0,
                passedCount: 0,
                totalCount: 0,
                visibleResults: [
                  {
                    name: "JSON Parse Error",
                    passed: false,
                    error: `Could not parse runner output: ${errMsg}`,
                  },
                ],
                hiddenPassed: 0,
                hiddenTotal: 0,
                executionTimeMs: 0,
                rawOutput: stdout,
              },
              { status: 500 }
            )
          );
        }
      });

      proc.stdin.write(JSON.stringify(payload));
      proc.stdin.end();
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      {
        allPassed: false,
        score: 0,
        passedCount: 0,
        totalCount: 0,
        visibleResults: [{ name: "Server Error", passed: false, error: errMsg }],
        hiddenPassed: 0,
        hiddenTotal: 0,
        executionTimeMs: 0,
      },
      { status: 500 }
    );
  }
}
