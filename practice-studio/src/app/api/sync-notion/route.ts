import { NextRequest, NextResponse } from "next/server";
import {
  getDrillsDataDir,
  getPythonBin,
  getWorkspaceRoot,
  isPilotMode,
  isSafeId,
  loadDrillFromDisk,
} from "@/lib/paths";
import {
  mergeDrillForNotionSync,
  runNotionDrillSync,
} from "@/lib/notionSyncRunner";
import { readProgress, stampSyncMetadata, writeProgress } from "@/lib/progress";
import { isLabId } from "@/lib/routes";
import { summaryFingerprint } from "@/lib/sessionSummary";
import type { SessionSummary } from "@/types/drill";

export async function POST(req: NextRequest) {
  try {
    const drillDoc = await req.json();
    const drillId = drillDoc.drillId;
    const unitCode = drillDoc.unitCode || "MTH-T02-C01-U01";

    if (!drillId) {
      return NextResponse.json({ ok: false, error: "Missing drillId" }, { status: 400 });
    }
    if (!isSafeId(drillId) || !isSafeId(unitCode)) {
      return NextResponse.json({ ok: false, error: "Invalid drillId or unitCode" }, { status: 400 });
    }
    if (isLabId(drillId)) {
      return NextResponse.json(
        {
          ok: false,
          error: "Labs must be submitted from the terminal with `npm run submit`, not drill sync.",
        },
        { status: 400 }
      );
    }

    // Merge & persist learner progress once via the canonical TS merge path so redacted
    // client state never overwrites server-owned fields (variantId, variantsSeen/Attempted,
    // matchedTrap), concurrent reviews/attempts/testRuns, or existing sync stamps on disk.
    writeProgress(drillDoc, { allowSyncStampUpdate: false });
    const mergedProgress = readProgress(drillId);

    // Rehydrate canonical server drill content with the merged server-side progress.
    const serverDoc = loadDrillFromDisk(drillId);
    const mergedDoc = mergeDrillForNotionSync(serverDoc, drillDoc, mergedProgress);

    // Progress is already saved above via writeProgress (progress/<DRILL_ID>.json);
    // Python sync runs with save_local=False and never rewrites drill content.
    const dataDir = getDrillsDataDir();

    // Call python notion sync helper
    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const isDryRun =
      Boolean(drillDoc.dryRun) ||
      process.env.NOTION_DRY_RUN === "1" ||
      process.env.NOTION_DRY_RUN === "true";

    const { code, stdout, stderr, timedOut } = await runNotionDrillSync({
      mergedDoc,
      rootDir,
      pythonBin,
      dataDir,
      isDryRun,
    });

    if (timedOut) {
      return NextResponse.json(
        {
          ok: false,
          timedOut: true,
          error: stderr || "Notion sync timed out.",
        },
        { status: 504 }
      );
    }

    if (code !== 0) {
      return NextResponse.json(
        { ok: false, error: stderr || `Sync helper exited with code ${code}` },
        { status: 500 }
      );
    }

    try {
      const outputLines = stdout
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
      const lastOutputLine = outputLines[outputLines.length - 1];
      if (!lastOutputLine) throw new Error("Sync helper produced no JSON output");
      const res = JSON.parse(lastOutputLine) as Record<string, unknown>;

      // Server is the source of truth for sync stamps: stamp ONLY on a real
      // (non-pilot, non-dry-run, non-degraded) successful sync and return them.
      const isRealSuccess =
        res &&
        typeof res === "object" &&
        res.ok === true &&
        !isDryRun &&
        !isPilotMode() &&
        !res.dryRun &&
        !res.pilotSkipped &&
        !res.degraded;

      if (isRealSuccess) {
        const rawPageId =
          (typeof res.drillPageId === "string" && res.drillPageId.trim()) ||
          (typeof res.notionPageId === "string" && res.notionPageId.trim()) ||
          null;
        const syncedSummary =
          mergedDoc.sessionSummary && typeof mergedDoc.sessionSummary === "object"
            ? (mergedDoc.sessionSummary as Partial<SessionSummary>)
            : null;
        const fingerprint = summaryFingerprint(syncedSummary);
        const stamped = stampSyncMetadata(drillId, {
          notionPageId: rawPageId,
          syncedFingerprint: fingerprint,
          unitCode,
        });
        return NextResponse.json({
          ...res,
          syncedToNotionAt: stamped.syncedToNotionAt,
          notionPageId: stamped.notionPageId,
          syncedFingerprint: stamped.syncedFingerprint,
        });
      }

      return NextResponse.json(res);
    } catch {
      return NextResponse.json(
        { ok: false, error: `Invalid response from sync helper: ${stdout}` },
        { status: 500 }
      );
    }
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
