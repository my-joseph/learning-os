import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getDrillsDataDir, getWorkspaceRoot, isSafeId } from "@/lib/paths";
import { applyProgress, readProgress } from "@/lib/progress";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json({ error: "Missing drill id" }, { status: 400 });
  }
  if (!isSafeId(id)) {
    return NextResponse.json({ error: "Invalid drill id" }, { status: 400 });
  }

  const dataDir = getDrillsDataDir();

  if (!fs.existsSync(dataDir)) {
    return NextResponse.json({ error: "No data dir" }, { status: 404 });
  }

  const unitDirs = fs.readdirSync(dataDir);
  for (const unit of unitDirs) {
    const filePath = path.join(dataDir, unit, `${id}.json`);
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, "utf-8");
      const doc = applyProgress(JSON.parse(content), readProgress(id));

      const rootDir = getWorkspaceRoot();

      if (!doc.unitTitle && doc.unitCode) {
        try {
          const idMapPath = path.join(rootDir, "id_map.json");
          if (fs.existsSync(idMapPath)) {
            const idMap = JSON.parse(fs.readFileSync(idMapPath, "utf-8"));
            doc.unitTitle = idMap[doc.unitCode]?.title || doc.unitCode;
          } else {
            doc.unitTitle = doc.unitCode;
          }
        } catch {
          doc.unitTitle = doc.unitCode;
        }
      }

      // Compute local IDE workspace paths at runtime from repo root (never baked into drill JSON)
      if (Array.isArray(doc.problems) && doc.drillId) {
        const wsDir = path.join(rootDir, "drills", "workspace", doc.drillId);
        for (const prob of doc.problems) {
          if (prob && typeof prob === "object" && prob.workspaceFile) {
            const absFile = path.resolve(rootDir, prob.workspaceFile);
            prob.workspaceDir = wsDir;
            prob.vscodeFolderUrl = `vscode://file/${wsDir}`;
            prob.cursorFolderUrl = `cursor://file/${wsDir}`;
            prob.vscodeUrl = `vscode://file/${absFile}`;
            prob.cursorUrl = `cursor://file/${absFile}`;
          }
        }
      }

      return NextResponse.json(doc);
    }
  }

  return NextResponse.json({ error: "Drill not found" }, { status: 404 });
}
