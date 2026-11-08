import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import { getPythonBin, getWorkspaceRoot } from "@/lib/paths";

const TIMEOUT_MS = 5000;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const isPrg =
      body.subject === "PRG" ||
      ["code_output", "predict_output", "line_number", "find_bug"].includes(
        body.answerSpec?.type
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

      proc.stdin.write(JSON.stringify(body));
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
