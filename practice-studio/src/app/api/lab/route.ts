import { NextRequest, NextResponse } from "next/server";
import { loadLabDetailFromDisk } from "@/lib/labs";
import { isSafeId } from "@/lib/paths";
import { isLabId } from "@/lib/routes";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id =
    searchParams.get("id") ||
    searchParams.get("labId") ||
    searchParams.get("lab");

  if (!id || !isSafeId(id) || !isLabId(id)) {
    return NextResponse.json(
      { error: "Missing or invalid lab id" },
      { status: 400 }
    );
  }

  const lab = loadLabDetailFromDisk(id);
  if (!lab) {
    return NextResponse.json({ error: "Lab not found" }, { status: 404 });
  }

  return NextResponse.json(lab);
}
