import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk, loadVariantFromDisk } from "@/lib/paths";
import {
  addVariantDuration,
  allocateSimilarSlots,
  markVariantServed,
  readProgress,
  registerServedVariant,
  resetVariantProgress,
  resolveVariantToken,
  startProblemCycle,
  updateVariantSession,
} from "@/lib/progress";
import {
  canRevealVariantSteps,
  extractRevealedPart,
  formatWorkedExampleVariant,
  redactVariantForTry,
} from "@/lib/redact";
import {
  countCycleOriginalWrongAttempts,
  cycleAttempts,
  deriveTabStatuses,
  isInCycle,
  similarUnlock,
} from "@/lib/similarTabs";
import {
  collectSeenVariantIds,
  findVariantsForProblem,
  pickExampleVariant,
} from "@/lib/variants";
import { AttemptRecord, Problem, ProblemState, VariantSessionRecord } from "@/types/drill";

export const dynamic = "force-dynamic";

function resolveParams(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const drillId = searchParams.get("drillId") || searchParams.get("drill");
  const qid =
    searchParams.get("qid") || searchParams.get("q") || searchParams.get("problemId");
  const mode = searchParams.get("mode");
  const token = searchParams.get("token");
  return { drillId, qid, mode, token };
}

function sanitizeVariantAttemptsForClient(attempts?: AttemptRecord[]): AttemptRecord[] {
  if (!Array.isArray(attempts)) return [];
  return attempts.map((a) => {
    const copy: AttemptRecord = { ...a };
    delete copy.matchedTrap;
    return copy;
  });
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

export async function GET(req: NextRequest) {
  const { drillId, qid, mode, token } = resolveParams(req);

  if (!drillId || !qid || !isSafeId(drillId) || !isSafeId(qid)) {
    return NextResponse.json(
      { error: "Missing or invalid drillId or qid" },
      { status: 400 }
    );
  }
  if (mode !== "list" && mode !== "open" && mode !== "example") {
    return NextResponse.json(
      { error: "Invalid mode parameter; expected 'list', 'open', or 'example'" },
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
  const unitCode = typeof doc.unitCode === "string" ? doc.unitCode : undefined;

  if (mode === "list") {
    if (variants.length === 0 || !similarUnlock(state)) {
      return NextResponse.json({
        unlocked: false,
        tabs: [],
      });
    }

    const { state: nextState } = allocateSimilarSlots(drillId, unitCode, qid, variants);
    const tabs = deriveTabStatuses(nextState);
    const exampleViewedAt =
      typeof nextState.exampleViewedAt === "string" &&
      nextState.exampleViewedAt &&
      isInCycle(nextState.exampleViewedAt, nextState.cycleStartedAt)
        ? nextState.exampleViewedAt
        : null;

    return NextResponse.json({
      unlocked: true,
      tabs,
      exampleViewedAt,
    });
  }

  if (variants.length === 0) {
    return NextResponse.json(
      { error: "No variants available for this archetype." },
      { status: 404 }
    );
  }

  if (mode === "open") {
    if (!token || !isSafeId(token)) {
      return NextResponse.json(
        { error: "Missing or invalid token parameter" },
        { status: 400 }
      );
    }

    if (!similarUnlock(state)) {
      return NextResponse.json(
        { error: "Similar questions unlock after an attempt on the original question." },
        { status: 403 }
      );
    }

    const { slots, state: slotState } = allocateSimilarSlots(
      drillId,
      unitCode,
      qid,
      variants
    );
    const slotIndex = slots.indexOf(token);
    if (slotIndex < 0) {
      return NextResponse.json(
        { error: "Invalid similar question token for this problem." },
        { status: 403 }
      );
    }

    const rawRecord = slotState.variants?.[token];
    if (!rawRecord || typeof rawRecord.variantId !== "string" || !rawRecord.variantId) {
      return NextResponse.json(
        { error: "Variant not found" },
        { status: 404 }
      );
    }

    const loadedVar = loadVariantFromDisk(rawRecord.variantId);
    if (!loadedVar) {
      return NextResponse.json(
        { error: "Variant not found" },
        { status: 404 }
      );
    }

    const { record: servedRec, state: afterServeState } = markVariantServed(
      drillId,
      unitCode,
      qid,
      token
    );
    const effectiveRec = servedRec ?? rawRecord;
    const cycleStartedAt = afterServeState.cycleStartedAt ?? null;
    const cycleRecAttempts = cycleAttempts(effectiveRec.attempts, cycleStartedAt);
    const inCurrentCycle =
      !cycleStartedAt ||
      cycleRecAttempts.length > 0 ||
      isInCycle(effectiveRec.servedAt, cycleStartedAt);

    const hasCorrectInCycle = cycleRecAttempts.some((a) => a.verdict === "correct");
    const revealed: Record<string, unknown> = {};
    if ((effectiveRec.setupRevealed && inCurrentCycle) || hasCorrectInCycle) {
      const disp = extractRevealedPart(loadedVar.variant as Partial<Problem>, "display");
      if ("display" in disp && (disp.display || disp.plainText)) {
        revealed.display = disp.display;
        revealed.plainText = disp.plainText;
      }
    }
    if (
      hasCorrectInCycle ||
      (effectiveRec.stepsRevealed &&
        canRevealVariantSteps(effectiveRec, cycleStartedAt))
    ) {
      const stp = extractRevealedPart(loadedVar.variant as Partial<Problem>, "steps");
      if ("steps" in stp) {
        revealed.steps = stp.steps;
        revealed.answerDisplay = stp.answerDisplay;
        revealed.answerPlain = stp.answerPlain;
      }
    }

    return NextResponse.json({
      mode: "open",
      drillId,
      qid,
      token,
      slot: slotIndex + 1,
      total: slots.length,
      variant: redactVariantForTry(loadedVar.variant, token),
      session: {
        attempts: sanitizeVariantAttemptsForClient(cycleRecAttempts),
        hintsRevealed: inCurrentCycle ? effectiveRec.hintsRevealed || 0 : 0,
        setupRevealed: Boolean(effectiveRec.setupRevealed && inCurrentCycle),
        stepsRevealed: Boolean(
          effectiveRec.stepsRevealed &&
            canRevealVariantSteps(effectiveRec, cycleStartedAt)
        ),
        durationMs: inCurrentCycle ? effectiveRec.durationMs || 0 : 0,
        servedAt: effectiveRec.servedAt,
      },
      ...(Object.keys(revealed).length > 0 ? { revealed } : {}),
    });
  }

  // mode === "example" (existing worked-example path kept intact per binding scope change)
  const existingEx = findExistingExampleEntry(state);
  const exampleAlreadyViewedInCycle = Boolean(
    existingEx &&
      state?.exampleViewedAt &&
      isInCycle(state.exampleViewedAt, state.cycleStartedAt)
  );

  if (exampleAlreadyViewedInCycle && existingEx && existingEx.record.variantId) {
    const loadedEx = loadVariantFromDisk(existingEx.record.variantId);
    if (loadedEx) {
      return NextResponse.json({
        mode: "example",
        drillId,
        qid,
        token: existingEx.token,
        variant: formatWorkedExampleVariant(loadedEx.variant, existingEx.token),
        exampleViewedAt: state?.exampleViewedAt || existingEx.record.servedAt,
      });
    }
  }

  const origWrongs = countCycleOriginalWrongAttempts(state);
  if (origWrongs < 2) {
    return NextResponse.json(
      {
        error: "A worked example unlocks after 2 wrong attempts.",
        wrongAttempts: origWrongs,
      },
      { status: 403 }
    );
  }

  // Idempotent: if a worked example was already served in an earlier cycle, reuse it.
  if (existingEx && existingEx.record.variantId) {
    const loadedEx = loadVariantFromDisk(existingEx.record.variantId);
    if (loadedEx) {
      const { state: nextState } = registerServedVariant(
        drillId,
        unitCode,
        qid,
        existingEx.record.variantId,
        "example"
      );
      return NextResponse.json({
        mode: "example",
        drillId,
        qid,
        token: existingEx.token,
        variant: formatWorkedExampleVariant(loadedEx.variant, existingEx.token),
        exampleViewedAt: nextState.exampleViewedAt,
      });
    }
  }

  const seenIds = collectSeenVariantIds(state);
  const picked = pickExampleVariant(variants, seenIds);
  if (!picked) {
    return NextResponse.json(
      { error: "No variants available for this archetype." },
      { status: 404 }
    );
  }

  const pickedId = String(picked.variantId);
  const { token: exToken, state: nextState } = registerServedVariant(
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
    token: exToken,
    variant: formatWorkedExampleVariant(picked, exToken),
    exampleViewedAt: nextState.exampleViewedAt,
  });
}

const ALLOWED_ACTIONS = new Set([
  "reveal-steps",
  "reset",
  "duration",
  "start-cycle",
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
    if (action === "start-cycle") {
      if (!qid || !isSafeId(qid)) {
        return NextResponse.json({ ok: false, error: "Invalid qid" }, { status: 400 });
      }
      const loaded = loadProblemFromDisk(drillId, qid);
      if (!loaded) {
        return NextResponse.json({ ok: false, error: "Problem not found" }, { status: 404 });
      }
      const { cycleStartedAt } = startProblemCycle(
        drillId,
        typeof loaded.doc.unitCode === "string" ? loaded.doc.unitCode : undefined,
        qid
      );
      return NextResponse.json({ ok: true, cycleStartedAt });
    }
    if (action === "reset-question" || action === "reset-all") {
      const targetQid = typeof body.qid === "string" ? body.qid.trim() : undefined;
      if (action === "reset-question" && (!targetQid || !isSafeId(targetQid))) {
        return NextResponse.json({ ok: false, error: "Invalid qid" }, { status: 400 });
      }
      const loaded = targetQid ? loadProblemFromDisk(drillId, targetQid) : null;
      if (targetQid && !loaded) {
        return NextResponse.json({ ok: false, error: "Problem not found" }, { status: 404 });
      }
      resetVariantProgress(
        drillId,
        loaded && typeof loaded.doc.unitCode === "string" ? loaded.doc.unitCode : undefined,
        action === "reset-question" ? targetQid : undefined
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
    if (
      !similarUnlock(resolved.state) ||
      !Array.isArray(resolved.state.similarSlots) ||
      !resolved.state.similarSlots.includes(variantToken)
    ) {
      return NextResponse.json(
        { ok: false, error: "Invalid or locked similar question token" },
        { status: 403 }
      );
    }

    const loaded = loadProblemFromDisk(drillId, qid);
    const unitCode =
      loaded && typeof loaded.doc.unitCode === "string" ? loaded.doc.unitCode : undefined;

    const cycleRecAttempts = cycleAttempts(
      resolved.record.attempts,
      resolved.state.cycleStartedAt
    );
    const hasCorrectInCycle = cycleRecAttempts.some((a) => a.verdict === "correct");

    if (action === "reveal-steps") {
      if (!hasCorrectInCycle) {
        updateVariantSession(drillId, unitCode, qid, variantToken, { stepsRevealed: true });
      }
    } else if (action === "reset") {
      updateVariantSession(drillId, unitCode, qid, variantToken, { reset: true });
    } else if (action === "duration") {
      const durationMs =
        typeof body.durationMs === "number" && Number.isFinite(body.durationMs)
          ? body.durationMs
          : 0;
      if (durationMs > 0) {
        addVariantDuration(drillId, unitCode, qid, variantToken, durationMs);
      }
    }

    return NextResponse.json({ ok: true, token: variantToken, action });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
