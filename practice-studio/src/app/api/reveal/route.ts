import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk } from "@/lib/paths";
import { readProgress } from "@/lib/progress";
import { extractRevealedPart, isPartUnlocked, RevealPart } from "@/lib/redact";
import { Problem, ProblemState } from "@/types/drill";

const VALID_PARTS = new Set<RevealPart>(["steps", "display", "solution"]);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const drillId = searchParams.get("drill") || searchParams.get("drillId");
  const problemId = searchParams.get("q") || searchParams.get("problemId");
  const partParam = searchParams.get("part");

  if (!drillId || !problemId || !partParam) {
    return NextResponse.json(
      { error: "Missing drill, q, or part parameter" },
      { status: 400 }
    );
  }
  if (!isSafeId(drillId) || !isSafeId(problemId)) {
    return NextResponse.json(
      { error: "Invalid drill or problem id" },
      { status: 400 }
    );
  }
  if (!VALID_PARTS.has(partParam as RevealPart)) {
    return NextResponse.json(
      { error: "Invalid part parameter; expected steps, display, or solution" },
      { status: 400 }
    );
  }

  const part = partParam as RevealPart;
  const loaded = loadProblemFromDisk(drillId, problemId);
  if (!loaded) {
    return NextResponse.json(
      { error: "Drill or problem not found" },
      { status: 404 }
    );
  }

  const progress = readProgress(drillId);
  const state = (progress?.problems?.[problemId] as ProblemState | undefined) ?? null;

  if (!isPartUnlocked(part, state)) {
    return NextResponse.json(
      { error: "Requested part is locked until earned" },
      { status: 403 }
    );
  }

  return NextResponse.json(extractRevealedPart(loaded.problem as Partial<Problem>, part));
}
