import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs";
import { getPythonBin, getWorkspaceRoot, resolveInsideRoot } from "@/lib/paths";
import { spawn } from "child_process";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const relOrAbs = searchParams.get("file");
    if (!relOrAbs) {
      return NextResponse.json({ error: "Missing file param" }, { status: 400 });
    }

    const rootDir = getWorkspaceRoot();
    const fullPath = resolveInsideRoot(relOrAbs, rootDir);
    if (!fullPath) {
      return NextResponse.json({ error: "Path is outside the project" }, { status: 403 });
    }

    if (!fs.existsSync(fullPath)) {
      return NextResponse.json({ error: "File not found" }, { status: 404 });
    }

    const content = fs.readFileSync(fullPath, "utf-8");
    return NextResponse.json({ content, fullPath });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    const { file, content } = await req.json();
    if (!file) {
      return NextResponse.json({ error: "Missing file parameter" }, { status: 400 });
    }

    const rootDir = getWorkspaceRoot();
    const fullPath = resolveInsideRoot(file, rootDir);
    if (!fullPath) {
      return NextResponse.json({ error: "Path is outside the project" }, { status: 403 });
    }

    fs.writeFileSync(fullPath, content || "", "utf-8");
    return NextResponse.json({ ok: true, fullPath });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const pythonPath = [
      rootDir,
      path.resolve(rootDir, ".."),
      path.join(rootDir, "practice-studio"),
      process.cwd(),
    ].join(path.delimiter);

    const pyCode = `
import json, sys
from code_engine.workspace import materialize_drill_workspace

drill_doc = json.loads(sys.stdin.read() or "{}")
manifest = materialize_drill_workspace(drill_doc, root_dir=${JSON.stringify(rootDir)})
print(json.dumps(manifest))
`;

    return new Promise<NextResponse>((resolve) => {
      const proc = spawn(pythonBin, ["-c", pyCode], {
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
              { error: stderr || `Exited with code ${code}` },
              { status: 500 }
            )
          );
          return;
        }

        try {
          const manifest = JSON.parse(stdout.trim());
          resolve(NextResponse.json({ ok: true, manifest }));
        } catch (e: unknown) {
          const errMsg = e instanceof Error ? e.message : String(e);
          resolve(NextResponse.json({ error: errMsg }, { status: 500 }));
        }
      });

      proc.stdin.write(JSON.stringify(body));
      proc.stdin.end();
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}
