import { NextRequest, NextResponse } from "next/server";
import { isSafeId } from "@/lib/paths";
import { getRecentMistakes } from "@/lib/reviewItems";

export const dynamic = "force-dynamic";

export function GET(req: NextRequest) {
  const subject = req.nextUrl.searchParams.get("subject");
  const unit = req.nextUrl.searchParams.get("unit") || undefined;
  if ((subject !== "MTH" && subject !== "PRG") || (unit && !isSafeId(unit))) {
    return NextResponse.json({ error: "Invalid mistake scope" }, { status: 400 });
  }

  try {
    return NextResponse.json({ mistakes: getRecentMistakes(subject, unit) });
  } catch {
    return NextResponse.json({ error: "Could not load mistakes" }, { status: 500 });
  }
}
