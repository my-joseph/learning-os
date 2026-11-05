import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { DrillListItem } from "@/types/drill";
import { getWorkspaceRoot } from "@/lib/paths";

export async function GET() {
  const rootDir = getWorkspaceRoot();
  const dataDir = path.join(rootDir, "drills", "data");

  if (!fs.existsSync(dataDir)) {
    return NextResponse.json({ drills: [] });
  }

  const items: DrillListItem[] = [];
  const unitDirs = fs.readdirSync(dataDir);

  for (const unit of unitDirs) {
    const fullUnitDir = path.join(dataDir, unit);
    if (!fs.statSync(fullUnitDir).isDirectory()) continue;

    const files = fs.readdirSync(fullUnitDir).filter((f) => f.endsWith(".json"));
    for (const file of files) {
      try {
        const filePath = path.join(fullUnitDir, file);
        const content = fs.readFileSync(filePath, "utf-8");
        const doc = JSON.parse(content);

        items.push({
          drillId: doc.drillId,
          unitCode: doc.unitCode,
          unitTitle: doc.unitTitle,
          createdAt: doc.createdAt || "",
          questionCount: doc.config?.questionCount || doc.problems?.length || 0,
          difficultyMode: doc.config?.difficultyMode || "Mixed Exam Mode",
          localFilePath: filePath,
        });
      } catch {
        continue;
      }
    }
  }

  items.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return NextResponse.json({ drills: items });
}
