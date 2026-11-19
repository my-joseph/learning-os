import { NextRequest, NextResponse } from "next/server";
import path from "path";
import fs from "fs";
import {
  getDrillWorkspaceDir,
  getPythonBin,
  getWorkspaceRoot,
  isSafeId,
  loadDrillFromDisk,
  resolveInsideDrillWorkspace,
} from "@/lib/paths";
import { spawn } from "child_process";

function extractRelativeWorkspaceFile(rawWorkspaceFile: string, drillId: string): string | null {
  const normalized = rawWorkspaceFile.replace(/\\/g, "/").replace(/^\/+/, "");
  const prefixes = [
    `drills/workspace/${drillId}/`,
    `pilot/workspace/${drillId}/`,
  ];
  for (const prefix of prefixes) {
    if (normalized.startsWith(prefix)) {
      const rel = normalized.slice(prefix.length);
      if (!rel || rel.includes("\0")) return null;
      const segments = rel.split("/").filter(Boolean);
      if (segments.length === 0 || segments.some((s) => s === "." || s === "..")) {
        return null;
      }
      return path.join(...segments);
    }
  }
  return null;
}

function getAllowedWorkspaceFilePaths(
  drillDoc: Record<string, unknown>,
  drillId: string,
  rootDir: string
): Set<string> {
  const allowed = new Set<string>();
  const wsDir = getDrillWorkspaceDir(drillId, rootDir);
  if (!wsDir || !Array.isArray(drillDoc.problems)) return allowed;

  const root = path.resolve(rootDir);
  const realRoot = fs.existsSync(root) ? fs.realpathSync(root) : root;
  const canonicalWsDir = fs.existsSync(wsDir)
    ? fs.realpathSync(wsDir)
    : path.join(realRoot, path.relative(root, wsDir));

  for (const prob of drillDoc.problems) {
    if (!prob || typeof prob !== "object") continue;
    const raw = (prob as { workspaceFile?: unknown }).workspaceFile;
    if (typeof raw !== "string") continue;
    const rel = extractRelativeWorkspaceFile(raw, drillId);
    if (!rel) continue;
    const target = path.resolve(canonicalWsDir, rel);
    const check = path.relative(canonicalWsDir, target);
    if (check && !check.startsWith("..") && !path.isAbsolute(check)) {
      allowed.add(target);
    }
  }
  return allowed;
}

async function materializeWorkspace(
  drillId: string,
  rootDir: string
): Promise<{ ok: boolean; error?: string }> {
  if (!isSafeId(drillId)) return { ok: false, error: "Invalid drillId" };
  const drillDoc = loadDrillFromDisk(drillId);
  if (!drillDoc) return { ok: false, error: `Drill not found: ${drillId}` };
  const pythonBin = getPythonBin(rootDir);
  const repoParent = path.resolve(process.cwd(), "..");
  const pythonPath = [
    rootDir,
    path.resolve(rootDir, ".."),
    path.join(rootDir, "practice-studio"),
    process.cwd(),
    repoParent,
  ].join(path.delimiter);
  const pyCode = `
import json, sys
from code_engine.workspace import materialize_drill_workspace
drill_doc = json.loads(sys.stdin.read() or "{}")
print(json.dumps(materialize_drill_workspace(drill_doc, root_dir=${JSON.stringify(rootDir)})))
`;
  return new Promise((resolve) => {
    const proc = spawn(pythonBin, ["-c", pyCode], {
      cwd: rootDir,
      env: { ...process.env, PYTHONPATH: pythonPath },
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (data) => (stdout += data.toString()));
    proc.stderr.on("data", (data) => (stderr += data.toString()));
    proc.on("close", (code) => {
      if (code !== 0) {
        resolve({ ok: false, error: stderr || `Exited with code ${code}` });
        return;
      }
      try {
        JSON.parse(stdout.trim());
        resolve({ ok: true });
      } catch (err) {
        resolve({ ok: false, error: err instanceof Error ? err.message : String(err) });
      }
    });
    proc.stdin.end(JSON.stringify(drillDoc));
  });
}

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const relOrAbs = searchParams.get("file");
    const drillId = searchParams.get("drillId");

    if (!relOrAbs) {
      return NextResponse.json({ error: "Missing file param" }, { status: 400 });
    }
    if (!isSafeId(drillId)) {
      return NextResponse.json({ error: "Missing or invalid drillId" }, { status: 400 });
    }

    const rootDir = getWorkspaceRoot();
    let fullPath = resolveInsideDrillWorkspace(relOrAbs, drillId, rootDir);
    if (!fullPath) {
      return NextResponse.json({ error: "Path is outside the drill workspace" }, { status: 403 });
    }

    const drillDoc = loadDrillFromDisk(drillId);
    if (!drillDoc) {
      return NextResponse.json({ error: "Drill not found" }, { status: 404 });
    }

    const allowedPaths = getAllowedWorkspaceFilePaths(drillDoc, drillId, rootDir);
    if (!allowedPaths.has(fullPath)) {
      return NextResponse.json(
        { error: "File is not an allowed workspace file for this drill" },
        { status: 403 }
      );
    }

    if (!fs.existsSync(fullPath)) {
      const materialized = await materializeWorkspace(drillId, rootDir);
      if (!materialized.ok) {
        return NextResponse.json({ error: materialized.error || "File not found" }, { status: 404 });
      }
      fullPath = resolveInsideDrillWorkspace(relOrAbs, drillId, rootDir);
      if (!fullPath) {
        return NextResponse.json({ error: "Path is outside the drill workspace" }, { status: 403 });
      }
      if (!fs.existsSync(fullPath)) {
        return NextResponse.json({ error: "Workspace file not found in drill manifest" }, { status: 404 });
      }
    }

    if (!fs.statSync(fullPath).isFile()) {
      return NextResponse.json({ error: "Workspace path must be a regular file" }, { status: 403 });
    }

    const content = fs.readFileSync(fullPath, "utf-8");
    return NextResponse.json({ content });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
  try {
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
    }

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return NextResponse.json({ error: "Request body must be a JSON object" }, { status: 400 });
    }

    const { drillId, file, content } = body as {
      drillId?: unknown;
      file?: unknown;
      content?: unknown;
    };

    if (!isSafeId(drillId)) {
      return NextResponse.json({ error: "Missing or invalid drillId" }, { status: 400 });
    }
    if (typeof file !== "string" || !file.trim()) {
      return NextResponse.json({ error: "Missing file parameter" }, { status: 400 });
    }
    if (content !== undefined && typeof content !== "string") {
      return NextResponse.json({ error: "Invalid content parameter" }, { status: 400 });
    }

    const rootDir = getWorkspaceRoot();
    const fullPath = resolveInsideDrillWorkspace(file, drillId, rootDir);
    if (!fullPath) {
      return NextResponse.json({ error: "Path is outside the drill workspace" }, { status: 403 });
    }

    const drillDoc = loadDrillFromDisk(drillId);
    if (!drillDoc) {
      return NextResponse.json({ error: "Drill not found" }, { status: 404 });
    }

    const allowedPaths = getAllowedWorkspaceFilePaths(drillDoc, drillId, rootDir);
    if (!allowedPaths.has(fullPath)) {
      return NextResponse.json(
        { error: "File is not an allowed workspace file for this drill" },
        { status: 403 }
      );
    }

    if (!fs.existsSync(path.dirname(fullPath))) {
      return NextResponse.json(
        { error: "Workspace is not materialized; materialize it first" },
        { status: 404 }
      );
    }

    if (fs.existsSync(fullPath) && !fs.statSync(fullPath).isFile()) {
      return NextResponse.json({ error: "Workspace path must be a regular file" }, { status: 403 });
    }

    fs.writeFileSync(fullPath, content ?? "", "utf-8");
    return NextResponse.json({ ok: true });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
    }

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      return NextResponse.json({ error: "Request body must be { drillId }" }, { status: 400 });
    }

    const keys = Object.keys(body);
    const drillId = (body as { drillId?: unknown }).drillId;
    if (keys.length !== 1 || keys[0] !== "drillId" || !isSafeId(drillId)) {
      return NextResponse.json(
        { error: "Request body must contain only a valid drillId" },
        { status: 400 }
      );
    }

    const rootDir = getWorkspaceRoot();
    const result = await materializeWorkspace(drillId, rootDir);
    return NextResponse.json(result, { status: result.ok ? 200 : 404 });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}
