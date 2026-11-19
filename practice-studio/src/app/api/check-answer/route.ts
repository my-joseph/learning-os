import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import {
  getPythonBin,
  getVariantsDir,
  getWorkspaceRoot,
  isSafeId,
  loadProblemFromDisk,
  loadVariantFromDisk,
} from "@/lib/paths";
import { recordVariantAttempted } from "@/lib/progress";
import { isSubstantiveVerdict } from "@/lib/reviewGuard";

const TIMEOUT_MS = 5000;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const variantId = typeof body.variantId === "string" ? body.variantId.trim() : "";
    const drillId = body.drillId || body.drill;
    const problemId = body.problemId || body.qid || body.q;
    const userInput = typeof body.input === "string" ? body.input : "";

    let engineModule = "math_engine.answer_check";
    let enginePayload: Record<string, unknown>;
    let variantMeta: { variantId: string; unitCode: string; drillId?: string; qid?: string } | null =
      null;

    if (variantId) {
      if (!isSafeId(variantId)) {
        return NextResponse.json(
          {
            verdict: "invalid input",
            message: "Invalid variantId",
            components: [],
            diagnostics: [],
          },
          { status: 400 }
        );
      }

      const loadedVariant = loadVariantFromDisk(variantId);
      if (!loadedVariant) {
        return NextResponse.json(
          {
            verdict: "invalid input",
            message: "Variant not found",
            components: [],
            diagnostics: [],
          },
          { status: 404 }
        );
      }

      // Server bank wins: Python checker resolves answerSpec & trapValue by variantId from disk.
      enginePayload = {
        variantId,
        input: userInput,
      };
      variantMeta = {
        variantId,
        unitCode: loadedVariant.unitCode,
        drillId: isSafeId(drillId) ? drillId : undefined,
        qid: isSafeId(problemId) ? problemId : undefined,
      };
    } else {
      if (!drillId || !problemId || !isSafeId(drillId) || !isSafeId(problemId)) {
        return NextResponse.json(
          {
            verdict: "invalid input",
            message: "Missing or invalid drillId or problemId",
            components: [],
            diagnostics: [],
          },
          { status: 400 }
        );
      }

      const loaded = loadProblemFromDisk(drillId, problemId);
      if (!loaded) {
        return NextResponse.json(
          {
            verdict: "invalid input",
            message: "Drill or problem not found",
            components: [],
            diagnostics: [],
          },
          { status: 404 }
        );
      }

      const { doc, problem } = loaded;
      // Server copy wins: ignore any answerSpec or trapValue sent by the client.
      const answerSpec = (problem.answerSpec || {}) as Record<string, unknown>;
      const subject =
        doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-")
          ? "PRG"
          : body.subject || "MATH";

      enginePayload = {
        subject,
        answerSpec,
        trapValue: problem.trapValue,
        input: userInput,
      };

      const isPrg =
        subject === "PRG" ||
        ["code_output", "predict_output", "line_number", "find_bug"].includes(
          String(answerSpec.type || "")
        );
      engineModule = isPrg
        ? "code_engine.answer_check"
        : "math_engine.answer_check";
    }

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
    ].join(path.delimiter);

    const spawnEnv: NodeJS.ProcessEnv = {
      ...process.env,
      PYTHONPATH: pythonPath,
      VARIANTS_DIR: getVariantsDir(),
    };

    return new Promise<NextResponse>((resolve) => {
      let isSettled = false;

      const proc = spawn(pythonBin, ["-m", engineModule], {
        cwd: rootDir,
        env: spawnEnv,
      });

      const timer = setTimeout(() => {
        if (!isSettled) {
          isSettled = true;
          try {
            proc.kill("SIGKILL");
          } catch {
            // Process might have already closed
          }
          resolve(
            NextResponse.json({
              verdict: "invalid input",
              message: "The input is too complex and evaluation timed out (Evaluation timed out after 5s)",
              components: [],
              diagnostics: [],
            })
          );
        }
      }, TIMEOUT_MS);

      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        clearTimeout(timer);
        if (isSettled) return;
        isSettled = true;

        if (code !== 0) {
          resolve(
            NextResponse.json(
              {
                verdict: "invalid input",
                message: `Calculation error: ${stderr || "Process exited with code " + code}`,
                components: [],
                diagnostics: [],
              },
              { status: 200 }
            )
          );
          return;
        }

        try {
          const result = JSON.parse(stdout) as { verdict?: string };
          if (
            variantMeta &&
            variantMeta.drillId &&
            variantMeta.qid &&
            isSubstantiveVerdict(result?.verdict)
          ) {
            try {
              recordVariantAttempted(
                variantMeta.drillId,
                variantMeta.unitCode,
                variantMeta.qid,
                variantMeta.variantId
              );
            } catch {
              // Do not fail answer check if progress tracking write fails transiently.
            }
          }
          resolve(NextResponse.json(result));
        } catch (e: unknown) {
          const errMsg = e instanceof Error ? e.message : String(e);
          resolve(
            NextResponse.json(
              {
                verdict: "invalid input",
                message: `Failed to parse result: ${errMsg}`,
                components: [],
                diagnostics: [],
              },
              { status: 200 }
            )
          );
        }
      });

      proc.stdin.write(JSON.stringify(enginePayload));
      proc.stdin.end();
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      {
        verdict: "invalid input",
        message: `Internal server error: ${errMsg}`,
        components: [],
        diagnostics: [],
      },
      { status: 500 }
    );
  }
}
