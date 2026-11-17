import { NextResponse } from "next/server";
import { getDueTodayUnits } from "@/lib/dueToday";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json(getDueTodayUnits());
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}
