import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk } from "@/lib/paths";
import { readProgress, recordVariantSeen } from "@/lib/progress";
import { formatWorkedExampleVariant, redactVariantForTry } from "@/lib/redact";
import { countWrongAttempts } from "@/lib/reviewGuard";
import {
  findVariantsForProblem,
  pickExampleVariant,
  pickUnseenVariant,
} from "@/lib/variants";
import { ProblemState } from "@/types/drill";

export const dynamic = "force-dynamic";

function resolveParams(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const drillId = searchParams.get("drillId") || searchParams.get("drill");
  const qid = searchParams.get("qid") || searchParams.get("q") || searchParams.get("problemId");
  const mode = searchParams.get("mode");
  const exclude = searchParams.get("exclude");
  return { drillId, qid, mode, exclude };
}

export async function HEAD(req: NextRequest) {
  const { drillId, qid } = resolveParams(req);
  if (!drillId || !qid || !isSafeId(drillId) || !isSafeId(qid)) {
    return new NextResponse(null, { status: 400 });
  }
  const loaded = loadProblemFromDisk(drillId, qid);
  if (!loaded) {
    return new NextResponse(null, { status: 404 });
  }
  const variants = findVariantsForProblem(loaded.doc, loaded.problem);
  return new NextResponse(null, { status: variants.length > 0 ? 200 : 404 });
}

export async function GET(req: NextRequest) {
  const { drillId, qid, mode, exclude } = resolveParams(req);

  if (!drillId || !qid || !isSafeId(drillId) || !isSafeId(qid)) {
    return NextResponse.json(
      { error: "Missing or invalid drillId or qid" },
      { status: 400 }
    );
  }
  if (mode !== "try" && mode !== "example") {
    return NextResponse.json(
      { error: "Invalid mode parameter; expected 'try' or 'example'" },
      { status: 400 }
    );
  }
  if (exclude && !isSafeId(exclude)) {
    return NextResponse.json(
      { error: "Invalid exclude variantId" },
      { status: 400 }
    );
  }

  const loaded = loadProblemFromDisk(drillId, qid);
  if (!loaded) {
    return NextResponse.json(
      { error: "Drill or problem not found" },
      { status: 404 }
    );
  }

  const { doc, problem } = loaded;
  const variants = findVariantsForProblem(doc, problem);
  if (variants.length === 0) {
    return NextResponse.json(
      { error: "No variants available for this archetype." },
      { status: 404 }
    );
  }

  const progress = readProgress(drillId);
  const state = (progress?.problems?.[qid] as ProblemState | undefined) ?? null;
  const variantsSeen = Array.isArray(state?.variantsSeen)
    ? state.variantsSeen.filter((v): v is string => typeof v === "string")
    : [];

  if (mode === "example") {
    const wrongAttempts = countWrongAttempts(state);
    if (wrongAttempts < 2) {
      return NextResponse.json(
        {
          error: "A worked example unlocks after 2 wrong attempts on this question.",
          wrongAttempts,
        },
        { status: 403 }
      );
    }

    const picked = pickExampleVariant(variants, variantsSeen, exclude);
    if (!picked) {
      return NextResponse.json(
        { error: "No variants available for this archetype." },
        { status: 404 }
      );
    }

    return NextResponse.json({
      mode: "example",
      drillId,
      qid,
      variant: formatWorkedExampleVariant(picked),
    });
  }

  // mode === "try"
  const picked = pickUnseenVariant(variants, variantsSeen);
  if (!picked) {
    return NextResponse.json(
      {
        error: "You have already seen all available variants for this archetype.",
        allSeen: true,
      },
      { status: 404 }
    );
  }

  const variantId = String(picked.variant.variantId);
  const unitCode = typeof doc.unitCode === "string" ? doc.unitCode : undefined;
  recordVariantSeen(drillId, unitCode, qid, variantId);

  return NextResponse.json({
    mode: "try",
    drillId,
    qid,
    variant: redactVariantForTry(picked.variant),
    remainingCount: picked.remainingCount,
  });
}
