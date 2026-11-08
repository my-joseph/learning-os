import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { DrillListItem } from "@/types/drill";
import { getDrillsDataDir } from "@/lib/paths";

export async function GET() {
  const dataDir = getDrillsDataDir();

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

        const problems = Array.isArray(doc.problems) ? doc.problems : [];
        const questionCount = doc.config?.questionCount || problems.length || 0;
        const answeredCount = problems.filter(
          (p: { state?: { score?: number | null; skipped?: boolean; userInput?: string } }) =>
            (p.state?.score !== null && p.state?.score !== undefined) ||
            p.state?.skipped === true ||
            Boolean(p.state?.userInput && p.state.userInput.trim())
        ).length;
        const liveScore = problems.reduce(
          (acc: number, p: { state?: { score?: number | null } }) => acc + (p.state?.score || 0),
          0
        );

        let practiceStatus: "Ready" | "In Progress" | "Graded" | "Needs Retry" =
          doc.sessionSummary?.practiceStatus || "Ready";
        if (practiceStatus === "Ready" && answeredCount > 0) {
          practiceStatus = "In Progress";
        }

        const subject: "MATH" | "PRG" =
          doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-")
            ? "PRG"
            : "MATH";

        items.push({
          drillId: doc.drillId,
          subject,
          unitCode: doc.unitCode,
          unitTitle: doc.unitTitle || doc.unitCode,
          createdAt: doc.createdAt || "",
          questionCount,
          difficultyMode: doc.config?.difficultyMode || "Mixed Exam Mode",
          practiceStatus,
          score: doc.sessionSummary?.score ?? liveScore,
          maxScore: doc.sessionSummary?.maxScore ?? questionCount,
          answeredCount,
          localFilePath: filePath,
        });
      } catch {
        continue;
      }
    }
  }

  const statusOrder: Record<string, number> = {
    "In Progress": 0,
    Ready: 1,
    "Needs Retry": 2,
    Graded: 3,
  };

  items.sort((a, b) => {
    const orderA = statusOrder[a.practiceStatus || "Ready"] ?? 1;
    const orderB = statusOrder[b.practiceStatus || "Ready"] ?? 1;
    if (orderA !== orderB) return orderA - orderB;
    return b.createdAt.localeCompare(a.createdAt);
  });
  return NextResponse.json({ drills: items });
}
