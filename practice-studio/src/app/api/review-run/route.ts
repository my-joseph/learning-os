import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import {
  getDrillWorkspaceDir,
  getDrillWorkspacesDir,
  getLabWorkspaceDir,
  getLabsDir,
  getPythonBin,
  getWorkspaceRoot,
  isPilotMode,
  isSafeId,
  loadProblemFromDisk,
} from "@/lib/paths";
import { maskHiddenTestFailures, sanitizeCodeCheckError } from "@/lib/codeStatus";
import {
  appendBoundedOutput,
  buildPrgPythonEnv,
  killProcessTree,
  REVIEW_RUN_TIMEOUT_MS,
} from "@/lib/runnerEnv";

function formatServerCheckError(raw: string, rootDir: string): string {
  const withoutRoot = rootDir
    ? raw
        .split(`file://${rootDir}/`)
        .join("")
        .split(`${rootDir}/`)
        .join("")
        .split(rootDir)
        .join(".")
    : raw;
  return sanitizeCodeCheckError(withoutRoot);
}

function getExpectedWorkspaceDir(drillId: string, rootDir: string): string {
  return (
    getDrillWorkspaceDir(drillId, rootDir) ??
    path.join(getDrillWorkspacesDir(rootDir), drillId)
  );
}

async function ensureWorkspaceMaterialized(
  drillDoc: Record<string, unknown>,
  rootDir: string,
  pythonBin: string,
  pythonPath: string
): Promise<{ ok: boolean; error?: string }> {
  const pyCode = [
    "import json, sys",
    "from code_engine.workspace import materialize_drill_workspace",
    "doc = json.loads(sys.stdin.read() or '{}')",
    `materialize_drill_workspace(doc, root_dir=${JSON.stringify(rootDir)})`,
  ].join("\n");

  return new Promise((resolve) => {
    const proc = spawn(pythonBin, ["-c", pyCode], {
      cwd: rootDir,
      env: buildPrgPythonEnv(rootDir, pythonPath, { includeWorkspaceHints: true }),
      detached: process.platform !== "win32",
    });
    let stderr = "";
    let settled = false;
    const finish = (res: { ok: boolean; error?: string }) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(res);
    };
    const timer = setTimeout(() => {
      killProcessTree(proc);
      finish({ ok: false, error: "Workspace materialization timed out" });
    }, REVIEW_RUN_TIMEOUT_MS);

    proc.stderr.on("data", (chunk) => {
      stderr = appendBoundedOutput(stderr, chunk).value;
    });

    proc.on("error", (err) => {
      finish({ ok: false, error: err.message });
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        finish({ ok: false, error: stderr.trim() || `Exited with code ${code}` });
      } else {
        finish({ ok: true });
      }
    });

    proc.stdin.end(JSON.stringify(drillDoc));
  });
}

async function ensurePilotLabMaterialized(
  labId: string,
  rootDir: string,
  pythonBin: string,
  pythonPath: string
): Promise<{ ok: boolean; error?: string }> {
  const pyCode = [
    "from code_engine.workspace import materialize_pilot_lab",
    `materialize_pilot_lab(${JSON.stringify(labId)}, root_dir=${JSON.stringify(rootDir)})`,
  ].join("\n");

  return new Promise((resolve) => {
    const proc = spawn(pythonBin, ["-c", pyCode], {
      cwd: rootDir,
      env: buildPrgPythonEnv(rootDir, pythonPath, { includeWorkspaceHints: true }),
      detached: process.platform !== "win32",
    });
    let stderr = "";
    let settled = false;
    const finish = (res: { ok: boolean; error?: string }) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(res);
    };
    const timer = setTimeout(() => {
      killProcessTree(proc);
      finish({ ok: false, error: "Pilot lab materialization timed out" });
    }, REVIEW_RUN_TIMEOUT_MS);

    proc.stderr.on("data", (chunk) => {
      stderr = appendBoundedOutput(stderr, chunk).value;
    });

    proc.on("error", (err) => {
      finish({ ok: false, error: err.message });
    });

    proc.on("close", (code) => {
      if (code !== 0) {
        finish({ ok: false, error: stderr.trim() || `Exited with code ${code}` });
      } else {
        finish({ ok: true });
      }
    });
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const drillId = body.drillId || body.labId || body.drill || body.lab;
    const problemId = body.problemId || body.milestone || body.m || body.q;

    if (!drillId || !problemId || !isSafeId(drillId) || !isSafeId(problemId)) {
      return NextResponse.json(
        { error: "Missing or invalid drillId or problemId" },
        { status: 400 }
      );
    }

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);
    const repoParent = path.resolve(process.cwd(), "..");
    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
      repoParent,
    ].join(path.delimiter);

    if (drillId.startsWith("LAB-")) {
      const labCfgPath = path.join(getLabsDir(), drillId, "lab.config.json");
      if (!fs.existsSync(labCfgPath)) {
        return NextResponse.json(
          { error: "Lab not found" },
          { status: 404 }
        );
      }
      if (isPilotMode() && !process.env.LABS_DIR) {
        const pilotLabDir =
          getLabWorkspaceDir(drillId, rootDir) ??
          path.join(rootDir, "pilot", "labs", drillId);
        const pilotCfg = path.join(pilotLabDir, "lab.config.json");
        if (!fs.existsSync(pilotCfg)) {
          const materialized = await ensurePilotLabMaterialized(
            drillId,
            rootDir,
            pythonBin,
            pythonPath
          );
          if (!materialized.ok) {
            return NextResponse.json(
              {
                error: formatServerCheckError(
                  materialized.error || "Failed to materialize pilot lab",
                  rootDir
                ),
              },
              { status: 500 }
            );
          }
        }
      }
    } else {
      const loaded = loadProblemFromDisk(drillId, problemId);
      if (!loaded) {
        return NextResponse.json(
          { error: "Drill or problem not found" },
          { status: 404 }
        );
      }

      const wsDir = getExpectedWorkspaceDir(drillId, rootDir);
      if (!fs.existsSync(wsDir)) {
        const materialized = await ensureWorkspaceMaterialized(
          loaded.doc,
          rootDir,
          pythonBin,
          pythonPath
        );
        if (!materialized.ok) {
          return NextResponse.json(
            {
              error: formatServerCheckError(
                materialized.error || "Failed to materialize workspace",
                rootDir
              ),
            },
            { status: 500 }
          );
        }
      }
    }

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(
        pythonBin,
        ["-m", "code_engine.review_run", drillId, problemId, "--json"],
        {
          cwd: rootDir,
          env: buildPrgPythonEnv(rootDir, pythonPath, { includeWorkspaceHints: true }),
          detached: process.platform !== "win32",
        }
      );

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
            { error: "Review check timed out" },
            { status: 504 }
          )
        );
      }, REVIEW_RUN_TIMEOUT_MS);

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
            { error: formatServerCheckError(err.message, rootDir) },
            { status: 500 }
          )
        );
      });

      proc.on("close", (code) => {
        if (settled) return;
        if (outputExceeded) {
          finish(
            NextResponse.json(
              { error: "Review check exceeded output size limit" },
              { status: 500 }
            )
          );
          return;
        }

        if (code !== 0) {
          const rawErr =
            stderr.trim() || stdout.trim() || `review_run exited with code ${code}`;
          finish(
            NextResponse.json(
              {
                error: formatServerCheckError(rawErr, rootDir),
              },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const parsed = JSON.parse(stdout.trim());
          const safeTests =
            parsed?.tests && typeof parsed.tests === "object"
              ? {
                  ...parsed.tests,
                  failed: Array.isArray(parsed.tests.failed)
                    ? maskHiddenTestFailures(parsed.tests.failed)
                    : [],
                }
              : parsed?.tests;
          finish(
            NextResponse.json({
              ...parsed,
              ...(safeTests !== undefined ? { tests: safeTests } : {}),
              types: parsed.typecheck ?? [],
            })
          );
        } catch (err: unknown) {
          const errMsg = err instanceof Error ? err.message : String(err);
          finish(
            NextResponse.json(
              { error: `Could not parse review_run output: ${errMsg}` },
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
