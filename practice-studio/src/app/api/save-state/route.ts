import { NextRequest, NextResponse } from "next/server";
import { isSafeId } from "@/lib/paths";
import { loadPracticeDocument } from "@/lib/practiceEvidence";
import { writeLearnerProgress } from "@/lib/progress";

/** Autosave of practice state: writes progress/<DRILL_ID>.json only, never the drill content file. */
export async function POST(req: NextRequest) {
  try {
    const drillDoc = await req.json();
    const drillId = drillDoc.drillId;
    const unitCode = drillDoc.unitCode;

    if (!drillId) {
      return NextResponse.json({ ok: false, error: "Missing drillId" }, { status: 400 });
    }
    if (!isSafeId(drillId) || (unitCode && !isSafeId(unitCode))) {
      return NextResponse.json({ ok: false, error: "Invalid drillId or unitCode" }, { status: 400 });
    }

    const canonicalDrill = loadPracticeDocument(drillId);
    if (!canonicalDrill || canonicalDrill.drillId !== drillId) {
      return NextResponse.json({ ok: false, error: "Drill not found" }, { status: 404 });
    }

    const progressFilePath = writeLearnerProgress(canonicalDrill, drillDoc);
    return NextResponse.json({ ok: true, progressFilePath });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
