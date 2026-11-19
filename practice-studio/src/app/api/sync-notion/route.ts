import { NextRequest, NextResponse } from "next/server";
import {
  getDrillsDataDir,
  getPythonBin,
  getWorkspaceRoot,
  isSafeId,
  loadDrillFromDisk,
} from "@/lib/paths";
import {
  mergeDrillForNotionSync,
  runNotionDrillSync,
} from "@/lib/notionSyncRunner";
import { isLabId } from "@/lib/routes";

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

    // Rehydrate canonical server drill content so redacted client docs keep full steps/answers when syncing.
    const serverDoc = loadDrillFromDisk(drillId);
    const mergedDoc = mergeDrillForNotionSync(serverDoc, drillDoc);

    // Progress is saved by notion_sync.drill_sync.save_drill_doc (progress/<DRILL_ID>.json);
    // the drill content file is never rewritten from the Studio.
    const dataDir = getDrillsDataDir();

    // Call python notion sync helper
    const rootDir = getWorkspaceRoot();
    const pythonBin = getPythonBin(rootDir);

    const isDryRun =
      Boolean(drillDoc.dryRun) ||
      process.env.NOTION_DRY_RUN === "1" ||
      process.env.NOTION_DRY_RUN === "true";

    const { code, stdout, stderr } = await runNotionDrillSync({
      mergedDoc,
      rootDir,
      pythonBin,
      dataDir,
      isDryRun,
    });

    if (code !== 0) {
      return NextResponse.json(
        { ok: false, error: stderr || `Sync helper exited with code ${code}` },
        { status: 500 }
      );
    }

    try {
      const res = JSON.parse(stdout);
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
