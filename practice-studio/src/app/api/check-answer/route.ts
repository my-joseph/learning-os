import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import { getPythonBin, getWorkspaceRoot } from "@/lib/paths";

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
      const proc = spawn(pythonBin, ["-m", engineModule], {
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
                verdict: "parse_error",
                message: `SymPy error: ${stderr || "Process exited with code " + code}`,
                components: [],
                diagnostics: [],
              },
              { status: 500 }
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
                verdict: "parse_error",
                message: `Failed to parse SymPy result: ${errMsg}`,
                components: [],
                diagnostics: [],
              },
              { status: 500 }
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
        verdict: "parse_error",
        message: `Internal server error: ${errMsg}`,
        components: [],
        diagnostics: [],
      },
      { status: 500 }
    );
  }
}
