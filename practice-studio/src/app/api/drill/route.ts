import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getWorkspaceRoot } from "@/lib/paths";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json({ error: "Missing drill id" }, { status: 400 });
  }

  const rootDir = getWorkspaceRoot();
  const dataDir = path.join(rootDir, "drills", "data");

  if (!fs.existsSync(dataDir)) {
    return NextResponse.json({ error: "No data dir" }, { status: 404 });
  }

  const unitDirs = fs.readdirSync(dataDir);
  for (const unit of unitDirs) {
    const filePath = path.join(dataDir, unit, `${id}.json`);
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, "utf-8");
      return NextResponse.json(JSON.parse(content));
    }
  }

  return NextResponse.json({ error: "Drill not found" }, { status: 404 });
}
