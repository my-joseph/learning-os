import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getDrillsDataDir, isSafeId } from "@/lib/paths";

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

    const unitDir = path.join(getDrillsDataDir(), unitCode);
    if (!fs.existsSync(unitDir)) {
      fs.mkdirSync(unitDir, { recursive: true });
    }

    const targetPath = path.join(unitDir, `${drillId}.json`);
    drillDoc.localFilePath = targetPath;
    fs.writeFileSync(targetPath, JSON.stringify(drillDoc, null, 2), "utf-8");

    return NextResponse.json({ ok: true, localFilePath: targetPath });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
