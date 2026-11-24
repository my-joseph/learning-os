import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import {
  getDrillWorkspaceDir,
  getWorkspaceRoot,
  findCanonicalDrillFilePath,
  isCanonicalDrillId,
  isSafeId,
  loadDrillFromDisk,
  loadIdMapTitles,
  remapWorkspaceFileForMode,
  resolveInsideDrillWorkspace,
} from "@/lib/paths";
import { applyProgress, readPendingNotionSync, readProgress } from "@/lib/progress";
import { redactDrill, redactDrillForReview } from "@/lib/redact";
import { MAX_SIMILAR_TABS } from "@/lib/similarTabs";
import type { DrillDocument } from "@/types/drill";
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

  const raw = loadDrillFromDisk(id);
  if (!raw) return NextResponse.json({ error: "Drill not found" }, { status: 404 });

  const doc = applyProgress(raw as unknown as DrillDocument, readProgress(id));
  const pendingSync = readPendingNotionSync(id);
  if (pendingSync) doc.notionSyncProblems = pendingSync.retry.failedSteps;

  const rootDir = getWorkspaceRoot();
  if (!doc.unitTitle && doc.unitCode) {
    doc.unitTitle = plainTitle(loadIdMapTitles(rootDir).get(doc.unitCode)) || doc.unitCode;
  } else if (doc.unitTitle) {
    doc.unitTitle = plainTitle(doc.unitTitle) || doc.unitCode;
  }

  // Compute local IDE workspace paths & variant bank availability at runtime (never baked into drill JSON)
  if (Array.isArray(doc.problems)) {
    const variantBankCache = new Map<string, Array<Record<string, unknown>>>();
    const isMath =
      doc.subject !== "PRG" && !String(doc.unitCode || "").startsWith("PRG-");
    const wsDir = doc.drillId
      ? getDrillWorkspaceDir(doc.drillId, rootDir)
      : null;
    for (const prob of doc.problems) {
      if (prob && typeof prob === "object") {
        if (isMath) {
          const variantCount = findVariantsForProblem(
            doc as unknown as Record<string, unknown>,
            prob as unknown as Record<string, unknown>,
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
          if (!resolveInsideDrillWorkspace(mappedRel, doc.drillId, rootDir)) {
            delete prob.workspaceFile;
            continue;
          }
          const absFile = path.join(rootDir, mappedRel);
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
