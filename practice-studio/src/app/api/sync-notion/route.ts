import { createHash } from "node:crypto";
import fs from "node:fs";
import { NextRequest, NextResponse } from "next/server";
import {
  findCanonicalDrillFilePath,
  getDrillsDataDir,
  getPythonBin,
  getWorkspaceRoot,
  isPilotMode,
  isSafeId,
} from "@/lib/paths";
import { runNotionDrillSync, type NotionSyncRetry } from "@/lib/notionSyncRunner";
import {
  applyProgress,
  readPendingNotionSync,
  readProgress,
  stampSyncMetadata,
  writePendingNotionSync,
  writeProgress,
} from "@/lib/progress";
import { getNotionAttemptEvidence } from "@/lib/reviewGuard";
import { isLabId } from "@/lib/routes";
import { buildSessionSummary, getPersistedStatusOverride, summaryFingerprint } from "@/lib/sessionSummary";
import type { DrillDocument } from "@/types/drill";

const activeDrillSyncs = new Set<string>();

export async function POST(req: NextRequest) {
  let activeDrillId: string | undefined;
  try {
    const body = await req.json();
    const drillId = body?.drillId;

    if (!drillId) {
      return NextResponse.json({ ok: false, error: "Missing drillId" }, { status: 400 });
    }
    if (!isSafeId(drillId) || (body.unitCode && !isSafeId(body.unitCode))) {
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

    const canonicalPath = findCanonicalDrillFilePath(drillId);
    if (!canonicalPath) {
      return NextResponse.json({ ok: false, error: "Drill not found" }, { status: 404 });
    }
    const canonical = JSON.parse(fs.readFileSync(canonicalPath, "utf-8")) as DrillDocument;
    const { unitCode } = canonical;
    const problemIds = Array.isArray(canonical.problems) ? canonical.problems.map((p) => p?.id) : [];
    if (
      canonical.drillId !== drillId || !isSafeId(unitCode) ||
      problemIds.length === 0 || !problemIds.every(isSafeId) ||
      new Set(problemIds).size !== problemIds.length
    ) {
      return NextResponse.json({ ok: false, error: "Drill content is incomplete" }, { status: 422 });
    }
    if (isPilotMode()) {
      return NextResponse.json({ ok: true, pilotSkipped: true });
    }
    if (activeDrillSyncs.has(drillId)) {
      return NextResponse.json({ ok: false, error: "This drill is already syncing." }, { status: 409 });
    }
    activeDrillSyncs.add(drillId);
    activeDrillId = drillId;

    // Only previously saved progress can supply evidence. Ignore embedded state in
    // content files and leave problem-state writes to the ordered autosave path.
    const progress = readProgress(drillId);
    const mergedDoc = applyProgress<DrillDocument>({
      ...canonical,
      problems: canonical.problems.map((problem) => ({
        ...problem,
        state: { userInput: "", score: null, divergedStep: null, mistakes: [] },
      })),
    }, progress?.drillId === drillId ? progress : null);
    const isPrg = mergedDoc.subject === "PRG";
    if (!mergedDoc.problems.some(({ state }) => {
      const { attempted, skipped } = getNotionAttemptEvidence(state, isPrg);
      return attempted || skipped;
    })) {
      return NextResponse.json(
        { ok: false, error: "Save an attempt or skip before syncing to Notion." },
        { status: 409 }
      );
    }

    const requestedDate = body.sessionSummary?.attemptDate;
    const attemptDate = typeof requestedDate === "string" && /^\d{4}-\d{2}-\d{2}$/.test(requestedDate)
      ? requestedDate
      : undefined;
    const sessionSummary = buildSessionSummary(
      mergedDoc, getPersistedStatusOverride(body.sessionSummary), { attemptDate }
    );
    const isDryRun =
      body.dryRun === true ||
      ["1", "true", "yes"].includes(process.env.NOTION_DRY_RUN?.toLowerCase() ?? "");
    const fingerprint = summaryFingerprint(sessionSummary);
    // Resume a checkpoint only for the same content and saved attempt evidence.
    const checkpointFingerprint = createHash("sha256")
      .update(JSON.stringify({ ...mergedDoc, sessionSummary: fingerprint }))
      .digest("hex");
    const pending = isDryRun ? null : readPendingNotionSync(drillId);
    const retrying = pending?.fingerprint === checkpointFingerprint ? pending : null;
    if (retrying?.attemptDate) sessionSummary.attemptDate = retrying.attemptDate;
    writeProgress({ drillId, unitCode, sessionSummary }, { allowSyncStampUpdate: false });
    const rootDir = getWorkspaceRoot();

    const { code, stdout, stderr, timedOut } = await runNotionDrillSync({
      mergedDoc: { ...mergedDoc, sessionSummary },
      rootDir,
      pythonBin: getPythonBin(rootDir),
      dataDir: getDrillsDataDir(),
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

      const isRealSync = !isDryRun && !res.dryRun && !res.pilotSkipped && !res.degraded;
      if (isRealSync && res.partial === true) {
        writePendingNotionSync(drillId, {
          fingerprint: checkpointFingerprint,
          attemptDate: sessionSummary.attemptDate,
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
        { ok: false, error: "Invalid response from sync helper." },
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
