import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk, loadVariantFromDisk } from "@/lib/paths";
import { readProgress } from "@/lib/progress";
import { extractRevealedPart, isPartUnlocked, RevealPart } from "@/lib/redact";
import { Problem, ProblemState } from "@/types/drill";

const VALID_PARTS = new Set<RevealPart>(["steps", "display", "solution"]);
const VALID_VARIANT_PARTS = new Set<RevealPart>(["steps", "display"]);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const variantId = searchParams.get("variantId");
  const drillId = searchParams.get("drill") || searchParams.get("drillId");
  const problemId = searchParams.get("q") || searchParams.get("qid") || searchParams.get("problemId");
  const partParam = searchParams.get("part");

  if (variantId) {
    if (!drillId || !problemId || !partParam) {
      return NextResponse.json(
        { error: "Missing drillId, qid, or part parameter" },
        { status: 400 }
      );
    }
    if (!isSafeId(variantId) || !isSafeId(drillId) || !isSafeId(problemId)) {
      return NextResponse.json(
        { error: "Invalid variantId, drillId, or qid" },
        { status: 400 }
      );
    }
    if (!VALID_VARIANT_PARTS.has(partParam as RevealPart)) {
      return NextResponse.json(
        { error: "Invalid part parameter for variant; expected steps or display" },
        { status: 400 }
      );
    }
    const loadedVariant = loadVariantFromDisk(variantId);
    if (!loadedVariant) {
      return NextResponse.json({ error: "Variant not found" }, { status: 404 });
    }
    const progress = readProgress(drillId);
    const state = (progress?.problems?.[problemId] as ProblemState | undefined) ?? null;
    const attempted = Array.isArray(state?.variantsAttempted)
      ? state.variantsAttempted.includes(variantId)
      : false;
    if (!attempted) {
      return NextResponse.json(
        { error: "Requested part is locked until earned" },
        { status: 403 }
      );
    }
    return NextResponse.json(
      extractRevealedPart(loadedVariant.variant as Partial<Problem>, partParam as RevealPart)
    );
  }

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
