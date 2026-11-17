import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import { getPythonBin, getWorkspaceRoot, isSafeId, loadProblemFromDisk } from "@/lib/paths";

const TIMEOUT_MS = 5000;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const drillId = body.drillId || body.drill;
    const problemId = body.problemId || body.q;

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

    const enginePayload = {
      subject,
      answerSpec,
      trapValue: problem.trapValue,
      input: typeof body.input === "string" ? body.input : "",
    };

    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const isPrg =
      subject === "PRG" ||
      ["code_output", "predict_output", "line_number", "find_bug"].includes(
        String(answerSpec.type || "")
      );
    const engineModule = isPrg
      ? "code_engine.answer_check"
      : "math_engine.answer_check";

    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
    ].join(path.delimiter);

    return new Promise<NextResponse>((resolve) => {
      let isSettled = false;

      const proc = spawn(pythonBin, ["-m", engineModule], {
        cwd: rootDir,
        env: { ...process.env, PYTHONPATH: pythonPath },
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
          const result = JSON.parse(stdout);
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
