import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk, loadVariantFromDisk } from "@/lib/paths";
import {
  readProgress,
  registerServedVariant,
  resetVariantProgress,
  resolveVariantToken,
  updateVariantSession,
} from "@/lib/progress";
import {
  canRevealVariantSteps,
  extractRevealedPart,
  formatWorkedExampleVariant,
  redactVariantForTry,
} from "@/lib/redact";
import {
  countClusterWrongAttempts,
  countWrongAttempts,
  isSubstantiveVerdict,
} from "@/lib/reviewGuard";
import {
  collectSeenVariantIds,
  findVariantsForProblem,
  pickExampleVariant,
  pickUnseenVariant,
} from "@/lib/variants";
import { AttemptRecord, Problem, ProblemState, VariantSessionRecord } from "@/types/drill";

export const dynamic = "force-dynamic";

function resolveParams(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const drillId = searchParams.get("drillId") || searchParams.get("drill");
  const qid = searchParams.get("qid") || searchParams.get("q") || searchParams.get("problemId");
  const mode = searchParams.get("mode");
  return { drillId, qid, mode };
}

function sanitizeVariantAttemptsForClient(attempts?: AttemptRecord[]): AttemptRecord[] {
  if (!Array.isArray(attempts)) return [];
  return attempts.map((a) => {
    const copy: AttemptRecord = { ...a };
    delete copy.matchedTrap;
    return copy;
  });
}

function computeTryIndex(
  variantsMap: Record<string, VariantSessionRecord> | undefined,
  token: string
): number {
  if (!variantsMap) return 1;
  const tryTokens = Object.entries(variantsMap)
    .filter(([, rec]) => rec && rec.role === "try")
    .map(([tok]) => tok);
  const pos = tryTokens.indexOf(token);
  return pos >= 0 ? pos + 1 : tryTokens.length || 1;
}

function findExistingExampleEntry(
  state?: ProblemState | null
): { token: string; record: VariantSessionRecord } | null {
  if (!state?.variants || typeof state.variants !== "object") return null;
  for (const [token, rec] of Object.entries(state.variants)) {
    if (rec && rec.role === "example" && typeof rec.variantId === "string" && rec.variantId) {
      return { token, record: rec };
    }
  }
  return null;
}

function countRemainingUnseen(
  variants: Array<Record<string, unknown>>,
  state?: ProblemState | null
): number {
  const seen = new Set(collectSeenVariantIds(state));
  return variants.filter(
    (v) => typeof v.variantId === "string" && !seen.has(v.variantId)
  ).length;
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
  const { drillId, qid, mode } = resolveParams(req);

  if (!drillId || !qid || !isSafeId(drillId) || !isSafeId(qid)) {
    return NextResponse.json(
      { error: "Missing or invalid drillId or qid" },
      { status: 400 }
    );
  }
  if (mode !== "try" && mode !== "example" && mode !== "active") {
    return NextResponse.json(
      { error: "Invalid mode parameter; expected 'try', 'example', or 'active'" },
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
  const progress = readProgress(drillId);
  const state = (progress?.problems?.[qid] as ProblemState | undefined) ?? null;
  const total = variants.length;
  const unitCode = typeof doc.unitCode === "string" ? doc.unitCode : undefined;

  if (mode === "active") {
    const remainingCount = countRemainingUnseen(variants, state);
    const clusterWrongAttempts = countClusterWrongAttempts(state);
    const exampleViewedAt =
      typeof state?.exampleViewedAt === "string" && state.exampleViewedAt
        ? state.exampleViewedAt
        : null;

    let activePayload: Record<string, unknown> | null = null;
    const activeToken =
      typeof state?.activeVariant === "string" && state.activeVariant
        ? state.activeVariant
        : null;
    if (activeToken && state?.variants?.[activeToken]) {
      const rec = state.variants[activeToken];
      if (rec.role === "try" && typeof rec.variantId === "string" && rec.variantId) {
        const loadedVar = loadVariantFromDisk(rec.variantId);
        if (loadedVar) {
          const revealed: Record<string, unknown> = {};
          if (rec.setupRevealed) {
            const disp = extractRevealedPart(
              loadedVar.variant as Partial<Problem>,
              "display"
            );
            if ("display" in disp) {
              revealed.display = disp.display;
              revealed.plainText = disp.plainText;
            }
          }
          if (rec.stepsRevealed && canRevealVariantSteps(rec)) {
            const stp = extractRevealedPart(
              loadedVar.variant as Partial<Problem>,
              "steps"
            );
            if ("steps" in stp) {
              revealed.steps = stp.steps;
              revealed.answerDisplay = stp.answerDisplay;
              revealed.answerPlain = stp.answerPlain;
            }
          }
          activePayload = {
            token: activeToken,
            index: computeTryIndex(state.variants, activeToken),
            total,
            remainingCount,
            variant: redactVariantForTry(loadedVar.variant, activeToken),
            session: {
              attempts: sanitizeVariantAttemptsForClient(rec.attempts),
              hintsRevealed: rec.hintsRevealed || 0,
              setupRevealed: Boolean(rec.setupRevealed),
              stepsRevealed: Boolean(rec.stepsRevealed),
              durationMs: rec.durationMs || 0,
              servedAt: rec.servedAt,
            },
            ...(Object.keys(revealed).length > 0 ? { revealed } : {}),
          };
        }
      }
    }

    let examplePayload: Record<string, unknown> | null = null;
    const existingEx = findExistingExampleEntry(state);
    if (existingEx && existingEx.record.variantId) {
      const loadedEx = loadVariantFromDisk(existingEx.record.variantId);
      if (loadedEx) {
        examplePayload = {
          token: existingEx.token,
          variant: formatWorkedExampleVariant(loadedEx.variant, existingEx.token),
        };
      }
    }

    return NextResponse.json({
      mode: "active",
      drillId,
      qid,
      active: activePayload,
      example: examplePayload,
      total,
      remainingCount,
      clusterWrongAttempts,
      exampleViewedAt,
    });
  }

  if (variants.length === 0) {
    return NextResponse.json(
      { error: "No variants available for this archetype." },
      { status: 404 }
    );
  }

  if (mode === "example") {
    const clusterWrongs = countClusterWrongAttempts(state);
    if (clusterWrongs < 2) {
      return NextResponse.json(
        {
          error: "A worked example unlocks after 2 wrong attempts.",
          wrongAttempts: clusterWrongs,
        },
        { status: 403 }
      );
    }

    // Idempotent: if a worked example was already served for this problem, return the same one.
    const existingEx = findExistingExampleEntry(state);
    if (existingEx && existingEx.record.variantId) {
      const loadedEx = loadVariantFromDisk(existingEx.record.variantId);
      if (loadedEx) {
        return NextResponse.json({
          mode: "example",
          drillId,
          qid,
          token: existingEx.token,
          variant: formatWorkedExampleVariant(loadedEx.variant, existingEx.token),
          exampleViewedAt: state?.exampleViewedAt || existingEx.record.servedAt,
          remainingCount: countRemainingUnseen(variants, state),
        });
      }
    }

    const activeToken =
      typeof state?.activeVariant === "string" && state.activeVariant
        ? state.activeVariant
        : null;
    const activeVariantId =
      activeToken && state?.variants?.[activeToken]?.variantId
        ? state.variants[activeToken].variantId
        : null;

    const seenIds = collectSeenVariantIds(state);
    const picked = pickExampleVariant(variants, seenIds, activeVariantId);
    if (!picked) {
      return NextResponse.json(
        { error: "No variants available for this archetype." },
        { status: 404 }
      );
    }

    const pickedId = String(picked.variantId);
    const { token, state: nextState } = registerServedVariant(
      drillId,
      unitCode,
      qid,
      pickedId,
      "example"
    );

    return NextResponse.json({
      mode: "example",
      drillId,
      qid,
      token,
      variant: formatWorkedExampleVariant(picked, token),
      exampleViewedAt: nextState.exampleViewedAt,
      remainingCount: countRemainingUnseen(variants, nextState),
    });
  }

  // mode === "try"
  const originalWrongAttempts = countWrongAttempts(state);
  if (originalWrongAttempts < 1) {
    return NextResponse.json(
      { error: "A similar question unlocks after a wrong attempt on the original question." },
      { status: 403 }
    );
  }

  // Refuse serving a new try while the current active try has no substantive attempt yet.
  const activeToken =
    typeof state?.activeVariant === "string" && state.activeVariant
      ? state.activeVariant
      : null;
  if (activeToken && state?.variants?.[activeToken]) {
    const activeRec = state.variants[activeToken];
    const hasAttemptedActive =
      Array.isArray(activeRec.attempts) &&
      activeRec.attempts.some((a) => isSubstantiveVerdict(a?.verdict));
    if (activeRec.role === "try" && !hasAttemptedActive) {
      return NextResponse.json(
        {
          error: "Attempt the current similar question before loading another one.",
          activeToken,
        },
        { status: 409 }
      );
    }
  }

  const seenIds = collectSeenVariantIds(state);
  const picked = pickUnseenVariant(variants, seenIds);
  if (!picked) {
    return NextResponse.json(
      {
        error: "You have already seen all available variants for this archetype.",
        allSeen: true,
      },
      { status: 404 }
    );
  }

  const pickedId = String(picked.variant.variantId);
  const { token, state: nextState } = registerServedVariant(
    drillId,
    unitCode,
    qid,
    pickedId,
    "try"
  );
  const index = computeTryIndex(nextState.variants, token);

  return NextResponse.json({
    mode: "try",
    drillId,
    qid,
    token,
    index,
    total,
    remainingCount: picked.remainingCount,
    variant: redactVariantForTry(picked.variant, token),
  });
}

const ALLOWED_ACTIONS = new Set([
  "hint",
  "reveal-steps",
  "reset",
  "deactivate",
  "reset-question",
  "reset-all",
]);

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as Record<string, unknown>;
    const drillId = typeof body.drillId === "string" ? body.drillId.trim() : "";
    const qid = typeof body.qid === "string" ? body.qid.trim() : "";
    const variantToken =
      typeof body.variantToken === "string" ? body.variantToken.trim() : "";
    const action = typeof body.action === "string" ? body.action.trim() : "";

    if (!isSafeId(drillId) || !ALLOWED_ACTIONS.has(action)) {
      return NextResponse.json(
        { ok: false, error: "Invalid drillId or variant action" },
        { status: 400 }
      );
    }
    if (action === "reset-question" || action === "reset-all") {
      const qid = typeof body.qid === "string" ? body.qid.trim() : undefined;
      if (action === "reset-question" && (!qid || !isSafeId(qid))) {
        return NextResponse.json({ ok: false, error: "Invalid qid" }, { status: 400 });
      }
      const loaded = qid ? loadProblemFromDisk(drillId, qid) : null;
      if (qid && !loaded) {
        return NextResponse.json({ ok: false, error: "Problem not found" }, { status: 404 });
      }
      resetVariantProgress(
        drillId,
        loaded && typeof loaded.doc.unitCode === "string" ? loaded.doc.unitCode : undefined,
        action === "reset-question" ? qid : undefined
      );
      return NextResponse.json({ ok: true });
    }

    if (!isSafeId(qid) || !isSafeId(variantToken)) {
      return NextResponse.json(
        { ok: false, error: "Invalid drillId, qid, or variantToken" },
        { status: 400 }
      );
    }
    const resolved = resolveVariantToken(drillId, qid, variantToken);
    if (!resolved) {
      return NextResponse.json(
        { ok: false, error: "Variant session not found" },
        { status: 404 }
      );
    }

    const loaded = loadProblemFromDisk(drillId, qid);
    const unitCode =
      loaded && typeof loaded.doc.unitCode === "string" ? loaded.doc.unitCode : undefined;

    if (action === "hint") {
      updateVariantSession(drillId, unitCode, qid, variantToken, { hintIncrement: 1 });
    } else if (action === "reveal-steps") {
      updateVariantSession(drillId, unitCode, qid, variantToken, { stepsRevealed: true });
    } else if (action === "reset") {
      updateVariantSession(drillId, unitCode, qid, variantToken, { reset: true });
    } else if (action === "deactivate") {
      updateVariantSession(drillId, unitCode, qid, variantToken, { deactivate: true });
    }

    return NextResponse.json({ ok: true, token: variantToken, action });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
