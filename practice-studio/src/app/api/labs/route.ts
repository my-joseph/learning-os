import { NextResponse } from "next/server";
import { listLabsFromDisk } from "@/lib/labs";

export const dynamic = "force-dynamic";

export async function GET() {
  const labs = listLabsFromDisk();
  return NextResponse.json({ labs });
}
