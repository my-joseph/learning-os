import { NextRequest, NextResponse } from "next/server";
import { isSafeId } from "@/lib/paths";
import { writeProgress } from "@/lib/progress";

/** Autosave of practice state: writes progress/<DRILL_ID>.json only, never the drill content file. */
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

    const progressFilePath = writeProgress(drillDoc);
    return NextResponse.json({ ok: true, progressFilePath });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
