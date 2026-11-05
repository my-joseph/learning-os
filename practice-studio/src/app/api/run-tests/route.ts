import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { getPythonBin, getWorkspaceRoot } from "@/lib/paths";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    let userCode = body.userCode || "";

    // If workspaceFile path is supplied and userCode is empty, read directly from local disk!
    if (!userCode.trim() && body.workspaceFile) {
      const fullPath = path.isAbsolute(body.workspaceFile)
        ? body.workspaceFile
        : path.join(rootDir, body.workspaceFile);

      if (fs.existsSync(fullPath)) {
        userCode = fs.readFileSync(fullPath, "utf-8");
      }
    }

    if (!userCode.trim()) {
      return NextResponse.json(
        {
          allPassed: false,
          score: 0,
          passedCount: 0,
          totalCount: (body.visibleTests?.length || 0) + (body.hiddenTests?.length || 0),
          visibleResults: [
            {
              name: "Empty Code",
              passed: false,
              error: "No implementation found. Write your solution in VS Code / Cursor or in the editor.",
            },
          ],
          hiddenPassed: 0,
          hiddenTotal: body.hiddenTests?.length || 0,
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
      visibleTests: body.visibleTests || [],
      hiddenTests: body.hiddenTests || [],
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
          resolve(
            NextResponse.json(
              {
                allPassed: false,
                score: 0,
                passedCount: 0,
                totalCount: (body.visibleTests?.length || 0) + (body.hiddenTests?.length || 0),
                visibleResults: [
                  {
                    name: "Test Runner Process Error",
                    passed: false,
                    error: stderr || `Exited with code ${code}`,
                  },
                ],
                hiddenPassed: 0,
                hiddenTotal: body.hiddenTests?.length || 0,
                executionTimeMs: 0,
                rawOutput: stdout + "\n" + stderr,
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
