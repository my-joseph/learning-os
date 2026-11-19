import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk, loadVariantFromDisk } from "@/lib/paths";
import { readProgress, resolveVariantToken, updateVariantSession } from "@/lib/progress";
import {
  canRevealVariantSteps,
  extractRevealedPart,
  isPartUnlocked,
  RevealPart,
} from "@/lib/redact";
import { Problem, ProblemState } from "@/types/drill";

const VALID_PARTS = new Set<RevealPart>(["steps", "display", "solution"]);
const VALID_VARIANT_PARTS = new Set<RevealPart>(["steps", "display"]);

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const variantToken = searchParams.get("variantToken");
  const rawVariantId = searchParams.get("variantId");
  const drillId = searchParams.get("drill") || searchParams.get("drillId");
  const problemId =
    searchParams.get("q") || searchParams.get("qid") || searchParams.get("problemId");
  const partParam = searchParams.get("part");

  if (rawVariantId && !variantToken) {
    return NextResponse.json(
      { error: "Use opaque variantToken instead of variantId" },
      { status: 400 }
    );
  }

  if (variantToken) {
    if (!drillId || !problemId || !partParam) {
      return NextResponse.json(
        { error: "Missing drillId, qid, or part parameter" },
        { status: 400 }
      );
    }
    if (!isSafeId(variantToken) || !isSafeId(drillId) || !isSafeId(problemId)) {
      return NextResponse.json(
        { error: "Invalid variantToken, drillId, or qid" },
        { status: 400 }
      );
    }
    if (!VALID_VARIANT_PARTS.has(partParam as RevealPart)) {
      return NextResponse.json(
        { error: "Invalid part parameter for variant; expected steps or display" },
        { status: 400 }
      );
    }
    const resolved = resolveVariantToken(drillId, problemId, variantToken);
    if (!resolved || !resolved.record.variantId) {
      return NextResponse.json({ error: "Variant not found" }, { status: 404 });
    }
    const loadedVariant = loadVariantFromDisk(resolved.record.variantId);
    if (!loadedVariant) {
      return NextResponse.json({ error: "Variant not found" }, { status: 404 });
    }

    const part = partParam as RevealPart;
    if (part === "display") {
      // Equation set-up is allowed on request and marks subsequent attempts on the variant as assisted.
      updateVariantSession(drillId, loadedVariant.unitCode, problemId, variantToken, {
        setupRevealed: true,
      });
      return NextResponse.json(
        extractRevealedPart(loadedVariant.variant as Partial<Problem>, "display")
      );
    }

    // part === "steps": unlocked only after a substantive attempt or explicit give-up (stepsRevealed).
    if (!canRevealVariantSteps(resolved.record)) {
      return NextResponse.json(
        { error: "Requested part is locked until earned" },
        { status: 403 }
      );
    }
    if (!resolved.record.stepsRevealed) {
      updateVariantSession(drillId, loadedVariant.unitCode, problemId, variantToken, {
        stepsRevealed: true,
      });
    }
    return NextResponse.json(
      extractRevealedPart(loadedVariant.variant as Partial<Problem>, "steps")
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
