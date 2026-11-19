import { NextRequest, NextResponse } from "next/server";
import { getReviewScheduleForUnits } from "@/lib/dueToday";
import { isSafeId } from "@/lib/paths";

export const dynamic = "force-dynamic";

/** Read-only schedule lookup for the Review & Sync preview ("now Mastery N · next review …"). */
export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const rawUnits = searchParams.get("units") || "";
    const codes = rawUnits
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (codes.length === 0) {
      return NextResponse.json({ units: {} });
    }

    for (const code of codes) {
      if (!isSafeId(code)) {
        return NextResponse.json({ error: "Invalid unit code" }, { status: 400 });
      }
    }

    const units = getReviewScheduleForUnits(codes);
    return NextResponse.json({ units });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}
