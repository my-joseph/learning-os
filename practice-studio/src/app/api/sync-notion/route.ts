import { NextRequest, NextResponse } from "next/server";
import { createHash } from "node:crypto";
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
  type NotionSyncRetry,
} from "@/lib/notionSyncRunner";
import {
  readPendingNotionSync,
  readProgress,
  stampSyncMetadata,
  writePendingNotionSync,
  writeProgress,
} from "@/lib/progress";
import { isLabId } from "@/lib/routes";
import { summaryFingerprint } from "@/lib/sessionSummary";
import type { SessionSummary } from "@/types/drill";

const activeDrillSyncs = new Set<string>();

export async function POST(req: NextRequest) {
  let activeDrillId: string | undefined;
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
    if (activeDrillSyncs.has(drillId)) {
      return NextResponse.json({ ok: false, error: "This drill is already syncing." }, { status: 409 });
    }
    activeDrillSyncs.add(drillId);
    activeDrillId = drillId;

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
      process.env.NOTION_DRY_RUN === "true" ||
      process.env.NOTION_DRY_RUN === "yes";

    const syncedSummary =
      mergedDoc.sessionSummary && typeof mergedDoc.sessionSummary === "object"
        ? (mergedDoc.sessionSummary as Partial<SessionSummary>)
        : null;
    const fingerprint = summaryFingerprint(syncedSummary);
    // A checkpoint belongs to the same content and attempt evidence. Ignore the
    // new request's date and retain the original attempt date on a matching retry.
    const checkpointFingerprint = createHash("sha256")
      .update(JSON.stringify({
        ...mergedDoc,
        sessionSummary: fingerprint,
        notionSyncProblems: undefined,
      }))
      .digest("hex");
    const pending = isDryRun || isPilotMode() ? null : readPendingNotionSync(drillId);
    const retrying = pending?.fingerprint === checkpointFingerprint ? pending : null;
    if (retrying?.attemptDate && syncedSummary) {
      mergedDoc.sessionSummary = { ...syncedSummary, attemptDate: retrying.attemptDate };
    }

    const { code, stdout, stderr, timedOut } = await runNotionDrillSync({
      mergedDoc,
      rootDir,
      pythonBin,
      dataDir,
      isDryRun,
      retry: retrying?.retry,
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
      const { retry, ...res } = JSON.parse(lastOutputLine) as Record<string, unknown>;

      const isRealSync =
        !isDryRun &&
        !isPilotMode() &&
        !res.dryRun &&
        !res.pilotSkipped &&
        !res.degraded;
      if (isRealSync && res.partial === true) {
        writePendingNotionSync(drillId, {
          fingerprint: checkpointFingerprint,
          attemptDate: retrying?.attemptDate ?? syncedSummary?.attemptDate,
          retry: retry as NotionSyncRetry,
        });
      }

      if (isRealSync && res.ok === true && !res.partial) {
        const rawPageId =
          (typeof res.drillPageId === "string" && res.drillPageId.trim()) ||
          (typeof res.notionPageId === "string" && res.notionPageId.trim()) ||
          null;
        const stamped = stampSyncMetadata(drillId, {
          notionPageId: rawPageId,
          syncedFingerprint: fingerprint,
          unitCode,
        });
        if (pending) writePendingNotionSync(drillId, null);
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
        { ok: false, error: "Could not process the Notion sync result." },
        { status: 500 }
      );
    }
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  } finally {
    if (activeDrillId) activeDrillSyncs.delete(activeDrillId);
  }
}
