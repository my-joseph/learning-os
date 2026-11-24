import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { DrillListItem, ProblemState } from "@/types/drill";
import { listDrillFiles, loadIdMapTitles } from "@/lib/paths";
import { cleanCurriculumTitle, parseCurriculumCodes } from "@/lib/drillGrouping";
import { plainTitle } from "@/lib/titleText";
import { applyProgress, readProgress } from "@/lib/progress";
import { isAwaitingReview, scoreProblem } from "@/lib/scoring";

export const dynamic = "force-dynamic";

export async function GET() {
  const idMapTitles = loadIdMapTitles();
  const items: DrillListItem[] = [];
  for (const filePath of listDrillFiles()) {
    try {
      const content = fs.readFileSync(filePath, "utf-8");
      const raw = JSON.parse(content);
      const doc = applyProgress(raw, readProgress(raw.drillId || path.basename(filePath, ".json")));

      const subject: "MATH" | "PRG" =
        doc.subject === "PRG" || String(doc.unitCode || "").startsWith("PRG-")
          ? "PRG"
          : "MATH";
      const isPrg = subject === "PRG";
      const problems = Array.isArray(doc.problems) ? doc.problems : [];
      const questionCount = doc.config?.questionCount || problems.length || 0;
      const answeredCount = problems.filter(
        (p: { state?: ProblemState }) => {
          const scored = scoreProblem(p.state, { isPrg });
          return (
            scored.outcome !== "notTried" ||
            isAwaitingReview(p.state, { isPrg }) ||
            Boolean(p.state?.userInput && p.state.userInput.trim())
          );
        }
      ).length;
      const liveScore = problems.reduce(
        (acc: number, p: { state?: ProblemState }) =>
          acc + (scoreProblem(p.state, { isPrg }).score ?? 0),
        0
      );
      const hasNotes =
        problems.some(
          (p: { state?: { mistakeNote?: string; mistakes?: unknown[] } }) =>
            Boolean(p.state?.mistakeNote && p.state.mistakeNote.trim()) ||
            (Array.isArray(p.state?.mistakes) && p.state.mistakes.length > 0)
        ) ||
        (Array.isArray(doc.sessionSummary?.mistakeCategories) &&
          doc.sessionSummary.mistakeCategories.length > 0);

      let practiceStatus: "Ready" | "In Progress" | "Graded" | "Needs Retry" =
        doc.sessionSummary?.practiceStatus || "Ready";
      if (practiceStatus === "Ready" && answeredCount > 0) {
        practiceStatus = "In Progress";
      }

      const { topicCode, chapterCode } = parseCurriculumCodes(
        doc.unitCode,
        doc.topicCode,
        doc.chapterCode
      );
      const unitTitle = plainTitle(doc.unitTitle) || doc.unitCode;
      const topicTitle =
        cleanCurriculumTitle(idMapTitles.get(topicCode)) || topicCode;
      const chapterTitle =
        cleanCurriculumTitle(idMapTitles.get(chapterCode)) ||
        (chapterCode === doc.unitCode ? unitTitle || chapterCode : chapterCode);

      items.push({
        drillId: doc.drillId,
        subject,
        unitCode: doc.unitCode,
        unitTitle,
        chapterCode,
        chapterTitle,
        topicCode,
        topicTitle,
        createdAt: doc.createdAt || "",
        questionCount,
        difficultyMode: doc.config?.difficultyMode || "Mixed Exam Mode",
        practiceStatus,
        score: doc.sessionSummary?.score ?? liveScore,
        maxScore: doc.sessionSummary?.maxScore ?? questionCount,
        answeredCount,
        hasNotes,
        localFilePath: filePath,
      });
    } catch {
      continue;
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
