import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import {
  getDrillWorkspaceDir,
  getDrillWorkspacesDir,
  getDrillsDataDir,
  getWorkspaceRoot,
  findCanonicalDrillFilePath,
  isCanonicalDrillId,
  isSafeId,
  remapWorkspaceFileForMode,
  resolveInsideDrillWorkspace,
} from "@/lib/paths";
import { applyProgress, readProgress } from "@/lib/progress";
import { redactDrill, redactDrillForReview } from "@/lib/redact";
import { MAX_SIMILAR_TABS } from "@/lib/similarTabs";
import { plainTitle } from "@/lib/titleText";
import { findVariantsForProblem } from "@/lib/variants";

/** Delete exactly one local drill content file; progress, workspaces, and Labs are retained. */
export async function DELETE(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const drillId = searchParams.get("id");
  if (!drillId) {
    return NextResponse.json({ ok: false, error: "Missing drill id" }, { status: 400 });
  }
  if (!isCanonicalDrillId(drillId)) {
    return NextResponse.json({ ok: false, error: "Invalid drill id" }, { status: 400 });
  }

  try {
    const filePath = findCanonicalDrillFilePath(drillId);
    if (!filePath) {
      return NextResponse.json({ ok: false, error: "Drill not found" }, { status: 404 });
    }
    fs.unlinkSync(filePath);
    return NextResponse.json({ ok: true, deleted: true, drillId });
  } catch (error) {
    if (error && typeof error === "object" && "code" in error && error.code === "ENOENT") {
      return NextResponse.json({ ok: false, error: "Drill not found" }, { status: 404 });
    }
    return NextResponse.json(
      { ok: false, error: "Failed to delete drill" },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  const isReview =
    searchParams.get("review") === "1" || searchParams.get("review") === "true";

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
            doc.unitTitle = plainTitle(idMap[doc.unitCode]?.title) || doc.unitCode;
          } else {
            doc.unitTitle = doc.unitCode;
          }
        } catch {
          doc.unitTitle = doc.unitCode;
        }
      } else if (doc.unitTitle) {
        doc.unitTitle = plainTitle(doc.unitTitle) || doc.unitCode;
      }

      // Compute local IDE workspace paths & variant bank availability at runtime (never baked into drill JSON)
      if (Array.isArray(doc.problems)) {
        const variantBankCache = new Map<string, Array<Record<string, unknown>>>();
        const isMath =
          doc.subject !== "PRG" && !String(doc.unitCode || "").startsWith("PRG-");
        const wsDir = doc.drillId
          ? getDrillWorkspaceDir(doc.drillId, rootDir) ??
            path.join(getDrillWorkspacesDir(rootDir), doc.drillId)
          : null;
        for (const prob of doc.problems) {
          if (prob && typeof prob === "object") {
            if (isMath) {
              const variantCount = findVariantsForProblem(
                doc as Record<string, unknown>,
                prob as Record<string, unknown>,
                variantBankCache
              ).length;
              prob.hasVariants = variantCount > 0;
              if (variantCount > 0) {
                prob.similarCount = Math.min(variantCount, MAX_SIMILAR_TABS);
              }
            }
            if (doc.drillId && wsDir && prob.workspaceFile) {
              const mappedRel = remapWorkspaceFileForMode(
                prob.workspaceFile,
                doc.drillId
              ).replace(/\\/g, "/");
              const absFile =
                resolveInsideDrillWorkspace(mappedRel, doc.drillId, rootDir) ??
                path.resolve(rootDir, mappedRel);
              prob.workspaceFile = mappedRel;
              prob.workspaceDir = wsDir;
              prob.vscodeFolderUrl = `vscode://file/${wsDir}`;
              prob.vscodeUrl = `vscode://file/${absFile}`;
            }
          }
        }
      }

      return NextResponse.json(isReview ? redactDrillForReview(doc) : redactDrill(doc));
    }
  }

  return NextResponse.json({ error: "Drill not found" }, { status: 404 });
}
