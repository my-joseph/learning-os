import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import {
  getPythonBin,
  getWorkspaceRoot,
  isSafeId,
  loadProblemFromDisk,
  resolveInsideDrillWorkspace,
} from "@/lib/paths";
import { currentPracticeCycle, recordTestReport } from "@/lib/practiceEvidence";
import { projectTestRunReport } from "@/lib/redact";
import type { TestRunReport } from "@/types/drill";
import { sanitizeCodeCheckError } from "@/lib/codeStatus";
import {
  appendBoundedOutput,
  buildPrgPythonEnv,
  killProcessTree,
  RUN_TESTS_TIMEOUT_MS,
} from "@/lib/runnerEnv";

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

    const { doc, problem } = loaded;
    const cycle = currentPracticeCycle(drillId, problemId);
    if (body.cycleStartedAt !== undefined && body.cycleStartedAt !== cycle) {
      return NextResponse.json({ error: "The practice cycle has changed" }, { status: 409 });
    }
    const unitCode = typeof doc.unitCode === "string" ? doc.unitCode : undefined;
    const persist = (report: TestRunReport) => recordTestReport(drillId, problemId, unitCode, cycle, report);
    // Server copy wins: load visibleTests, hiddenTests, environment, entryPoint, and workspaceFile from drills/data.
    const visibleTests = Array.isArray(problem.visibleTests) ? problem.visibleTests : [];
    const hiddenTests = Array.isArray(problem.hiddenTests) ? problem.hiddenTests : [];
    const environment =
      typeof doc.environment === "string" && doc.environment
        ? doc.environment
        : "node-vanilla";
    const entryPoint =
      typeof problem.entryPoint === "string" ? problem.entryPoint : "";
    const workspaceFile =
      typeof problem.workspaceFile === "string" && problem.workspaceFile
        ? problem.workspaceFile
        : body.workspaceFile;

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    let userCode = body.userCode || "";

    // Workspace-backed PRG tests always execute the source currently saved on disk.
    if (workspaceFile) {
      const fullPath = resolveInsideDrillWorkspace(workspaceFile, drillId, rootDir);
      if (!fullPath) return NextResponse.json({ error: "Workspace file path is invalid" }, { status: 403 });
      if (!fs.existsSync(fullPath)) {
        return NextResponse.json({ error: "Workspace file is missing; materialize the workspace first" }, { status: 404 });
      }
      userCode = fs.readFileSync(fullPath, "utf-8");
    }

    if (!userCode.trim()) {
      return NextResponse.json({
          allPassed: false,
          score: 0,
          passedCount: 0,
          totalCount: visibleTests.length + hiddenTests.length,
          visibleResults: [
            {
              name: "Empty Code",
              passed: false,
              error: "No implementation found. Write your solution in your local editor.",
            },
          ],
          hiddenPassed: 0,
          hiddenTotal: hiddenTests.length,
          executionTimeMs: 0,
      });
    }

    const repoParent = path.resolve(process.cwd(), "..");
    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
      repoParent,
    ].join(path.delimiter);

    const payload = {
      userCode,
      visibleTests,
      hiddenTests,
      environment,
      entryPoint,
    };

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(pythonBin, ["-m", "code_engine.test_runner"], {
        cwd: rootDir,
        env: buildPrgPythonEnv(rootDir, pythonPath, { includeWorkspaceHints: false }),
        detached: process.platform !== "win32",
      });

      let stdout = "";
      let stderr = "";
      let settled = false;
      let outputExceeded = false;

      const finish = (response: NextResponse) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(response);
      };

      const timer = setTimeout(() => {
        killProcessTree(proc);
        finish(
          NextResponse.json(
            {
              allPassed: false,
              score: 0,
              passedCount: 0,
              totalCount: visibleTests.length + hiddenTests.length,
              visibleResults: [
                {
                  name: "Timeout",
                  passed: false,
                  error: `Test runner exceeded ${Math.round(RUN_TESTS_TIMEOUT_MS / 1000)}s limit`,
                },
              ],
              hiddenPassed: 0,
              hiddenTotal: hiddenTests.length,
              executionTimeMs: RUN_TESTS_TIMEOUT_MS,
            },
            { status: 504 }
          )
        );
      }, RUN_TESTS_TIMEOUT_MS);

      proc.stdout.on("data", (data) => {
        const next = appendBoundedOutput(stdout, data);
        stdout = next.value;
        if (next.exceeded && !outputExceeded) {
          outputExceeded = true;
          killProcessTree(proc);
        }
      });

      proc.stderr.on("data", (data) => {
        const next = appendBoundedOutput(stderr, data);
        stderr = next.value;
        if (next.exceeded && !outputExceeded) {
          outputExceeded = true;
          killProcessTree(proc);
        }
      });

      proc.on("error", (err) => {
        finish(
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
                  error: sanitizeCodeCheckError(err.message),
                },
              ],
              hiddenPassed: 0,
              hiddenTotal: hiddenTests.length,
              executionTimeMs: 0,
            },
            { status: 500 }
          )
        );
      });

      proc.on("close", (code) => {
        if (settled) return;
        if (outputExceeded) {
          finish(
            NextResponse.json(
              {
                allPassed: false,
                score: 0,
                passedCount: 0,
                totalCount: visibleTests.length + hiddenTests.length,
                visibleResults: [
                  {
                    name: "Output limit exceeded",
                    passed: false,
                    error: "Test runner exceeded output size limit",
                  },
                ],
                hiddenPassed: 0,
                hiddenTotal: hiddenTests.length,
                executionTimeMs: 0,
              },
              { status: 200 }
            )
          );
          return;
        }
        if (code !== 0) {
          const rawErr = (stderr || `Exited with code ${code}`).split(`${rootDir}/`).join("");
          finish(
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
              },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const report = JSON.parse(stdout.trim()) as Record<string, unknown>;
          const safeReport = projectTestRunReport(report, {
            trustedHiddenTotal: hiddenTests.length,
            trustedVisibleCount: visibleTests.length,
            recomputeFromRunnerResults: true,
          });
          const persisted = persist(safeReport);
          finish(
            persisted
              ? NextResponse.json(projectTestRunReport(persisted))
              : NextResponse.json({ error: "The practice cycle has changed" }, { status: 409 })
          );
        } catch {
          finish(
            NextResponse.json(
              {
                allPassed: false,
                score: 0,
                passedCount: 0,
                totalCount: visibleTests.length + hiddenTests.length,
                visibleResults: [
                  {
                    name: "JSON Parse Error",
                    passed: false,
                    error: "Test runner returned an invalid report",
                  },
                ],
                hiddenPassed: 0,
                hiddenTotal: hiddenTests.length,
                executionTimeMs: 0,
              },
              { status: 500 }
            )
          );
        }
      });

      proc.stdin.write(JSON.stringify(payload));
      proc.stdin.end();
    });
  } catch {
    return NextResponse.json(
      {
        allPassed: false,
        score: 0,
        passedCount: 0,
        totalCount: 0,
        visibleResults: [{ name: "Server Error", passed: false, error: "Test execution failed" }],
        hiddenPassed: 0,
        hiddenTotal: 0,
        executionTimeMs: 0,
      },
      { status: 500 }
    );
  }
}
