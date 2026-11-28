import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk, loadVariantFromDisk } from "@/lib/paths";
import {
  addVariantDuration,
  markVariantServed,
  readProgress,
  recordVariantAttempt,
  registerServedVariant,
  resolveVariantToken,
  updateVariantSession,
} from "@/lib/progress";
import {
  canRevealVariantSteps,
  extractRevealedPart,
  formatWorkedExampleVariant,
  redactVariantForTry,
} from "@/lib/redact";
import { isSubstantiveVerdict } from "@/lib/reviewGuard";
import { scoreVariant } from "@/lib/scoring";
import {
  countCycleOriginalWrongAttempts,
  cycleAttempts,
  deriveTabStatuses,
  openedSimilarTokens,
  isInCycle,
  similarUnlock,
} from "@/lib/similarTabs";
import { hasCheckpointHint } from "@/lib/studioRules";
import {
  collectSeenVariantIds,
  findVariantsForProblem,
  pickExampleVariant,
  pickNextVariantForCycle,
  similarStateForVariants,
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

function openedVariantPayload(
  drillId: string,
  qid: string,
  token: string,
  slot: number,
  total: number,
  variant: Record<string, unknown>,
  state: ProblemState,
  record: VariantSessionRecord
) {
  const cycleStartedAt = state.cycleStartedAt ?? null;
  const cycleRecAttempts = cycleAttempts(record.attempts, cycleStartedAt);
  const inCurrentCycle =
    !cycleStartedAt ||
    cycleRecAttempts.length > 0 ||
    isInCycle(record.servedAt, cycleStartedAt);

  const hasCorrectInCycle = cycleRecAttempts.some((a) => a.verdict === "correct");
  const lastCycleAttempt =
    cycleRecAttempts.length > 0 ? cycleRecAttempts[cycleRecAttempts.length - 1] : null;
  const isSkippedInCycle = !hasCorrectInCycle && lastCycleAttempt?.verdict === "skipped";
  const revealed: Record<string, unknown> = {};
  if ((record.setupRevealed && inCurrentCycle) || hasCorrectInCycle || isSkippedInCycle) {
    const disp = extractRevealedPart(variant as Partial<Problem>, "display");
    if ("display" in disp && (disp.display || disp.plainText)) {
      revealed.display = disp.display;
      revealed.plainText = disp.plainText;
    }
  }
  if (
    hasCorrectInCycle ||
    isSkippedInCycle ||
    (record.stepsRevealed &&
      canRevealVariantSteps(record, cycleStartedAt))
  ) {
    const stp = extractRevealedPart(variant as Partial<Problem>, "steps");
    if ("steps" in stp) {
      revealed.steps = stp.steps;
      revealed.answerDisplay = stp.answerDisplay;
      revealed.answerPlain = stp.answerPlain;
    }
  }

  return {
    mode: "open",
    drillId,
    qid,
    token,
    slot,
    total,
    variant: redactVariantForTry(variant, token),
    session: {
      attempts: sanitizeVariantAttemptsForClient(cycleRecAttempts),
      hintsRevealed: inCurrentCycle ? record.hintsRevealed || 0 : 0,
      setupRevealed: Boolean(record.setupRevealed && inCurrentCycle),
      stepsRevealed: Boolean(
        record.stepsRevealed &&
          canRevealVariantSteps(record, cycleStartedAt)
      ),
      durationMs: inCurrentCycle ? record.durationMs || 0 : 0,
      servedAt: record.servedAt,
      skipped: isSkippedInCycle,
      divergedStep:
        inCurrentCycle && typeof record.divergedStep === "number" ? record.divergedStep : null,
      selfScore:
        inCurrentCycle && typeof record.selfScore === "number" ? record.selfScore : null,
      mistakes:
        inCurrentCycle && Array.isArray(record.mistakes)
          ? record.mistakes.filter((m): m is string => typeof m === "string")
          : [],
      mistakeNote:
        inCurrentCycle && typeof record.mistakeNote === "string" ? record.mistakeNote : "",
      revisitNote:
        inCurrentCycle && typeof record.revisitNote === "string" ? record.revisitNote : "",
    },
    ...(Object.keys(revealed).length > 0 ? { revealed } : {}),
  };
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
  const progress = readProgress(drillId);
  const state = progress?.problems?.[qid] as ProblemState | undefined;
  const unitCode = typeof doc.unitCode === "string" ? doc.unitCode : undefined;

  if (mode === "list") {
    if (!similarUnlock(state)) {
      return NextResponse.json({ unlocked: false, tabs: [] });
    }
    const variants = findVariantsForProblem(doc, problem);
    const tabs = deriveTabStatuses(state && similarStateForVariants(state, variants));
    return NextResponse.json({
      unlocked: true,
      tabs,
      exhausted: !pickNextVariantForCycle(variants, state, { drillId, problemId: qid }),
      exampleViewedAt:
        state?.exampleViewedAt && isInCycle(state.exampleViewedAt, state.cycleStartedAt)
          ? state.exampleViewedAt
          : null,
    });
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

    const variants = findVariantsForProblem(doc, problem);
    const slots = state ? similarStateForVariants(state, variants).similarSlots ?? [] : [];
    const slotIndex = slots.indexOf(token);
    if (slotIndex < 0) {
      return NextResponse.json(
        { error: "Invalid similar question token for this problem." },
        { status: 403 }
      );
    }

    const variantId = state?.variants?.[token]?.variantId;
    const variant = variants.find((candidate) => candidate.variantId === variantId);
    if (!variant) {
      return NextResponse.json({ error: "Variant not found" }, { status: 404 });
    }

    const served = markVariantServed(drillId, unitCode, qid, token);
    if (!served.record) {
      return NextResponse.json({ error: "Variant session not found" }, { status: 404 });
    }
    return NextResponse.json(openedVariantPayload(
      drillId, qid, token, slotIndex + 1, slots.length,
      variant, served.state, served.record
    ));
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

  const variants = findVariantsForProblem(doc, problem, { mode: "example" });
  const picked = pickExampleVariant(variants, collectSeenVariantIds(state));
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
  "open-next",
  "reveal-steps",
  "skip",
  "reset",
  "duration",
  "self-score",
  "toggle-mistake",
  "diverged-step",
  "note",
]);

function clampVariantSelfScore(val: unknown): 1 | 0.5 | 0 | null {
  if (val === null) return null;
  if (typeof val !== "number" || !Number.isFinite(val)) return null;
  if (val >= 1) return 1;
  if (val > 0) return 0.5;
  return 0;
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as Record<string, unknown>;
    const drillId = typeof body.drillId === "string" ? body.drillId.trim() : "";
    const qid = typeof body.qid === "string" ? body.qid.trim() : "";
    const variantToken =
      typeof body.variantToken === "string" ? body.variantToken.trim() : "";
    const action = typeof body.action === "string" ? body.action.trim() : "";

    if (!isSafeId(drillId) || !isSafeId(qid) || !ALLOWED_ACTIONS.has(action)) {
      return NextResponse.json(
        { ok: false, error: "Invalid drillId or variant action" },
        { status: 400 }
      );
    }
    if (action === "open-next") {
      const loaded = loadProblemFromDisk(drillId, qid);
      if (!loaded) {
        return NextResponse.json({ error: "Drill or problem not found" }, { status: 404 });
      }
      const state = readProgress(drillId)?.problems?.[qid] as ProblemState | undefined;
      if (!similarUnlock(state)) {
        return NextResponse.json(
          { error: "Similar questions unlock after an attempt on the original question." },
          { status: 403 }
        );
      }

      const { doc, problem } = loaded;
      const variants = findVariantsForProblem(doc, problem);
      const parent = { drillId, problemId: qid };
      const picked = pickNextVariantForCycle(variants, state, parent);
      if (!picked) {
        const tabs = deriveTabStatuses(state && similarStateForVariants(state, variants));
        return NextResponse.json({ exhausted: true, tabs });
      }

      const unitCode = typeof doc.unitCode === "string" ? doc.unitCode : undefined;
      const served = registerServedVariant(drillId, unitCode, qid, String(picked.variantId), "try");
      const tabs = deriveTabStatuses(similarStateForVariants(served.state, variants));
      return NextResponse.json({
        ...openedVariantPayload(
          drillId, qid, served.token, tabs.length, tabs.length,
          picked, served.state, served.state.variants![served.token]
        ),
        tabs,
        exhausted: !pickNextVariantForCycle(variants, served.state, parent),
      });
    }

    if (!isSafeId(variantToken)) {
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
      !openedSimilarTokens(resolved.state).includes(variantToken)
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
    const hasSubstantiveInCycle = cycleRecAttempts.some((a) => isSubstantiveVerdict(a.verdict));

    if (action === "reveal-steps") {
      if (!hasCorrectInCycle) {
        updateVariantSession(drillId, unitCode, qid, variantToken, { stepsRevealed: true });
      }
    } else if (action === "skip") {
      if (hasCorrectInCycle) {
        return NextResponse.json(
          { ok: false, error: "This similar question is already complete" },
          { status: 409 }
        );
      }
      const rawInput = typeof body.input === "string" ? body.input.trim() : "";
      const durationMs =
        typeof body.durationMs === "number" && Number.isFinite(body.durationMs)
          ? body.durationMs
          : undefined;
      const loadedVar = resolved.record.variantId
        ? loadVariantFromDisk(resolved.record.variantId)
        : null;
      const countHint =
        body.countHint === true &&
        Boolean(
          loadedVar &&
            hasCheckpointHint(
              typeof loadedVar.variant.checkpointHint === "string"
                ? loadedVar.variant.checkpointHint
                : undefined
            )
        );
      const ts = new Date().toISOString();
      const recorded = recordVariantAttempt(
        drillId,
        unitCode,
        qid,
        variantToken,
        {
          input: rawInput || "(Skipped)",
          ts,
          verdict: "skipped",
          kind: "variant",
        },
        durationMs,
        countHint ? { hintIncrement: 1 } : undefined
      );
      return NextResponse.json({
        ok: true,
        token: variantToken,
        action: "skip",
        ts: recorded?.record.attempts.at(-1)?.ts || ts,
        verdict: "skipped",
      });
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
    } else if (action === "self-score") {
      if (!hasSubstantiveInCycle) {
        return NextResponse.json(
          { ok: false, error: "Self-score requires a substantive attempt" },
          { status: 400 }
        );
      }
      const auto = scoreVariant(
        { ...resolved.record, selfScore: undefined },
        resolved.state.cycleStartedAt
      );
      if (auto.outcome === "skipped") {
        return NextResponse.json({ ok: true, token: variantToken, action, selfScore: 0 });
      }
      const requested = body.score === null ? null : clampVariantSelfScore(body.score);
      if (body.score !== null && requested === null) {
        return NextResponse.json({ ok: false, error: "Invalid score value" }, { status: 400 });
      }
      const maxAllowed = auto.score ?? 1;
      const capped =
        requested === null ? null : ((requested > maxAllowed ? maxAllowed : requested) as 1 | 0.5 | 0);
      updateVariantSession(drillId, unitCode, qid, variantToken, { selfScore: capped });
      return NextResponse.json({ ok: true, token: variantToken, action, selfScore: capped });
    } else if (action === "toggle-mistake") {
      const tag = typeof body.tag === "string" ? body.tag.trim() : "";
      const drillTags = Array.isArray(loaded?.doc?.mistakeTags)
        ? (loaded!.doc.mistakeTags as Array<{ id?: string }>)
        : [];
      if (!tag || tag === "concept-gap" || !drillTags.some((t) => t?.id === tag)) {
        return NextResponse.json({ ok: false, error: "Invalid mistake tag" }, { status: 400 });
      }
      updateVariantSession(drillId, unitCode, qid, variantToken, { toggleMistake: tag });
    } else if (action === "diverged-step") {
      const stepIdx = body.stepIdx;
      if (
        stepIdx !== null &&
        !(typeof stepIdx === "number" && Number.isSafeInteger(stepIdx) && stepIdx >= 0)
      ) {
        return NextResponse.json({ ok: false, error: "Invalid stepIdx" }, { status: 400 });
      }
      updateVariantSession(drillId, unitCode, qid, variantToken, { divergedStep: stepIdx });
    } else if (action === "note") {
      const patch: { mistakeNote?: string; revisitNote?: string } = {};
      if (typeof body.mistakeNote === "string") {
        patch.mistakeNote = body.mistakeNote.slice(0, 2000);
      }
      if (typeof body.revisitNote === "string") {
        patch.revisitNote = body.revisitNote.slice(0, 2000);
      }
      updateVariantSession(drillId, unitCode, qid, variantToken, patch);
    }

    return NextResponse.json({ ok: true, token: variantToken, action });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
