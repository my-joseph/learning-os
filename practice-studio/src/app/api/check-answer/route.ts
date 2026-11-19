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
import { recordVariantAttempt, resolveVariantToken } from "@/lib/progress";

const TIMEOUT_MS = 5000;

function extractVariantMatchedTrap(
  variant: Record<string, unknown>,
  userInput: string,
  result: { verdict?: string; trapMatched?: boolean }
): string | undefined {
  if (result.verdict !== "incorrect" && result.verdict !== "partial") return undefined;
  const spec = variant.answerSpec as Record<string, unknown> | undefined;
  if (spec?.type === "choice" && Array.isArray(spec.options)) {
    const trimmed = userInput.trim();
    const chosen = (spec.options as Array<Record<string, unknown>>).find(
      (o) => o && String(o.id ?? "").trim() === trimmed
    );
    const choiceTrap =
      (typeof chosen?.trapTag === "string" && chosen.trapTag) ||
      (typeof chosen?.tag === "string" && chosen.tag) ||
      "";
    if (choiceTrap) return choiceTrap;
  }
  if (result.trapMatched && typeof variant.commonTrapTag === "string" && variant.commonTrapTag) {
    return variant.commonTrapTag;
  }
  return undefined;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const variantToken =
      typeof body.variantToken === "string" ? body.variantToken.trim() : "";
    const rawVariantId =
      typeof body.variantId === "string" ? body.variantId.trim() : "";
    const drillId = body.drillId || body.drill;
    const problemId = body.problemId || body.qid || body.q;
    const userInput = typeof body.input === "string" ? body.input : "";
    const durationMs =
      typeof body.durationMs === "number" && Number.isFinite(body.durationMs)
        ? body.durationMs
        : undefined;

    if (rawVariantId && !variantToken) {
      return NextResponse.json(
        {
          verdict: "invalid input",
          message: "Use opaque variantToken instead of variantId",
          components: [],
          diagnostics: [],
        },
        { status: 400 }
      );
    }

    let engineModule = "math_engine.answer_check";
    let enginePayload: Record<string, unknown>;
    let variantMeta: {
      variantToken: string;
      variant: Record<string, unknown>;
      unitCode: string;
      drillId: string;
      qid: string;
    } | null = null;

    if (variantToken) {
      if (
        !isSafeId(variantToken) ||
        !isSafeId(drillId) ||
        !isSafeId(problemId)
      ) {
        return NextResponse.json(
          {
            verdict: "invalid input",
            message: "Missing or invalid drillId, qid, or variantToken",
            components: [],
            diagnostics: [],
          },
          { status: 400 }
        );
      }

      const resolved = resolveVariantToken(drillId, problemId, variantToken);
      if (!resolved || !resolved.record.variantId) {
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

      const loadedVariant = loadVariantFromDisk(resolved.record.variantId);
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

      // Server bank wins: resolve variantId strictly on the server from opaque variantToken.
      enginePayload = {
        variantId: resolved.record.variantId,
        input: userInput,
      };
      variantMeta = {
        variantToken,
        variant: loadedVariant.variant,
        unitCode: loadedVariant.unitCode,
        drillId,
        qid: problemId,
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
          const result = JSON.parse(stdout) as {
            verdict?: string;
            trapMatched?: boolean;
            diagnostics?: Array<{ code?: string }>;
          };
          if (variantMeta && userInput.trim()) {
            try {
              const diagCodes = Array.isArray(result.diagnostics)
                ? result.diagnostics
                    .map((d) => (typeof d?.code === "string" ? d.code : ""))
                    .filter(Boolean)
                : [];
              const matchedTrap = extractVariantMatchedTrap(
                variantMeta.variant,
                userInput,
                result
              );
              // Persist variant attempt with kind: "variant" under opaque token.
              // Review schedule is NEVER modified by variant attempts.
              recordVariantAttempt(
                variantMeta.drillId,
                variantMeta.unitCode,
                variantMeta.qid,
                variantMeta.variantToken,
                {
                  input: userInput.trim(),
                  ts: new Date().toISOString(),
                  verdict: String(result.verdict || "invalid input"),
                  kind: "variant",
                  ...(diagCodes.length > 0 ? { diagnosticCodes: diagCodes } : {}),
                  ...(matchedTrap ? { matchedTrap } : {}),
                },
                durationMs
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
