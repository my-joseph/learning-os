import { NextRequest, NextResponse } from "next/server";
import { isSafeId, loadProblemFromDisk, loadVariantFromDisk } from "@/lib/paths";
import { mutateProblemState, readProgress, resolveVariantToken, updateVariantSession } from "@/lib/progress";
import {
  canRevealVariantSteps,
  extractRevealedPart,
  isPartUnlocked,
  RevealPart,
} from "@/lib/redact";
import {
  currentPracticeCycle,
  loadPracticeDocument,
  practiceDuration,
  recordOriginalCheck,
  recordPracticeHelp,
  recordSelfScore,
  resetPractice,
} from "@/lib/practiceEvidence";
import {
  getReviewItemsSchedule,
  loadSavedReviewItems,
  reviewItemKey,
  writeReviewItemsStore,
} from "@/lib/reviewItems";
import { isSubstantiveVerdict } from "@/lib/reviewGuard";
import { cycleAttempts, similarUnlock } from "@/lib/similarTabs";
import { Problem, ProblemState } from "@/types/drill";

const VALID_PARTS = new Set<RevealPart>(["steps", "display", "solution"]);
const VALID_VARIANT_PARTS = new Set<RevealPart | "hint">(["steps", "display", "hint"]);

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
    if (!VALID_VARIANT_PARTS.has(partParam as RevealPart | "hint")) {
      return NextResponse.json(
        { error: "Invalid part parameter for variant; expected hint, steps, or display" },
        { status: 400 }
      );
    }
    const resolved = resolveVariantToken(drillId, problemId, variantToken);
    if (!resolved || !resolved.record.variantId) {
      return NextResponse.json({ error: "Variant not found" }, { status: 404 });
    }
    if (
      !similarUnlock(resolved.state) ||
      !Array.isArray(resolved.state.similarSlots) ||
      !resolved.state.similarSlots.includes(variantToken)
    ) {
      return NextResponse.json(
        { error: "Requested variant is locked or invalid for this problem" },
        { status: 403 }
      );
    }
    const loadedVariant = loadVariantFromDisk(resolved.record.variantId);
    if (!loadedVariant) {
      return NextResponse.json({ error: "Variant not found" }, { status: 404 });
    }

    const cycleRecAttempts = cycleAttempts(
      resolved.record.attempts,
      resolved.state.cycleStartedAt
    );
    const hasSubstantiveInCycle = cycleRecAttempts.some((a) =>
      isSubstantiveVerdict(a.verdict)
    );
    const hasCorrectInCycle = cycleRecAttempts.some((a) => a.verdict === "correct");

    if (partParam === "hint") {
      if (!hasCorrectInCycle) {
        updateVariantSession(drillId, loadedVariant.unitCode, problemId, variantToken, {
          hintIncrement: 1,
        });
      }
      return NextResponse.json({ checkpointHint: loadedVariant.variant.checkpointHint || "" });
    }

    const part = partParam as RevealPart;
    if (part === "display") {
      // Equation set-up is allowed on request; marks the variant as assisted only before a substantive attempt.
      if (!hasSubstantiveInCycle) {
        updateVariantSession(drillId, loadedVariant.unitCode, problemId, variantToken, {
          setupRevealed: true,
        });
      }
      return NextResponse.json(
        extractRevealedPart(loadedVariant.variant as Partial<Problem>, "display")
      );
    }

    // part === "steps": unlocked after a substantive attempt or explicit reveal-steps.
    if (!canRevealVariantSteps(resolved.record, resolved.state.cycleStartedAt)) {
      return NextResponse.json(
        { error: "Requested part is locked until earned" },
        { status: 403 }
      );
    }
    const recordInCycle =
      !resolved.state.cycleStartedAt ||
      (Boolean(resolved.record.servedAt) &&
        resolved.record.servedAt >= resolved.state.cycleStartedAt);
    if (!hasCorrectInCycle && !(recordInCycle && resolved.record.stepsRevealed)) {
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

/** Record a deliberate learner action against canonical practice content. */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { drillId, qid, action } = body;
    if (!isSafeId(drillId) || (action !== "reset-all" && !isSafeId(qid))) {
      return NextResponse.json({ error: "Invalid drillId or qid" }, { status: 400 });
    }
    const doc = loadPracticeDocument(drillId);
    const problem = doc?.problems.find((p) => p.id === qid);
    if (!doc || (!problem && action !== "reset-all")) {
      return NextResponse.json({ error: "Drill or problem not found" }, { status: 404 });
    }
    if (action === "reset-all") {
      return NextResponse.json({ cycleStartedAt: resetPractice(doc, doc.problems, { resetSummary: true }) });
    }
    if (!problem) return NextResponse.json({ error: "Problem not found" }, { status: 404 });
    if (action === "reset") {
      return NextResponse.json({ cycleStartedAt: resetPractice(doc, [problem]) });
    }
    if (action === "start-review" || action === "reset-review") {
      const key = reviewItemKey(drillId, qid);
      const saved = loadSavedReviewItems();
      const previous = readProgress(drillId)?.problems?.[qid] as ProblemState | undefined;
      const cycle = previous?.cycleStartedAt;
      if (body.cycleStartedAt !== undefined && body.cycleStartedAt !== (cycle ?? null)) {
        return NextResponse.json({ error: "The practice cycle has changed" }, { status: 409 });
      }
      const unfinished = cycle && previous.reviewBaseLevel !== undefined &&
        saved[key]?.completedCycle !== cycle;
      if (unfinished && action === "start-review") {
        return NextResponse.json({ cycleStartedAt: cycle });
      }
      const item = getReviewItemsSchedule()[key];
      if (!item && !unfinished) {
        return NextResponse.json({ error: "Review item is unavailable" }, { status: 409 });
      }
      // Preserve the starting schedule even if legacy evidence only existed in the old summary.
      if (item && item.lastReviewed !== saved[key]?.lastReviewed) {
        writeReviewItemsStore({ ...saved, [key]: item });
      }
      return NextResponse.json({
        cycleStartedAt: resetPractice(doc, [problem], {
          reviewBaseLevel: unfinished ? previous.reviewBaseLevel : item.level,
          keepReviewHelp: Boolean(unfinished),
        }),
      });
    }
    const cycle = currentPracticeCycle(drillId, qid);
    if (body.cycleStartedAt !== undefined && body.cycleStartedAt !== cycle) {
      return NextResponse.json({ error: "The practice cycle has changed" }, { status: 409 });
    }
    if (action === "skip") {
      const input = typeof body.input === "string" ? body.input : "";
      const event = recordOriginalCheck(
        doc, problem, cycle, input,
        { verdict: "skipped", message: "", components: [], diagnostics: [] },
        practiceDuration(body.durationMs),
        body.countHint === true
      );
      if (!event.eventId) {
        return NextResponse.json({ error: "This problem is already complete" }, { status: 409 });
      }
      return NextResponse.json(event);
    }
    if (action === "toggle-mistake" && body.tag !== "concept-gap" &&
        doc.mistakeTags?.some((tag) => tag.id === body.tag)) {
      mutateProblemState(drillId, doc.unitCode, qid, (state) => {
        const tags = new Set(state.mistakes);
        if (tags.has(body.tag)) tags.delete(body.tag);
        else tags.add(body.tag);
        state.mistakes = Array.from(tags);
      });
      return NextResponse.json({ ok: true });
    }
    if (action === "self-score" && (
      body.score === null || (typeof body.score === "number" && Number.isFinite(body.score))
    )) {
      recordSelfScore(doc, qid, body.score);
      return NextResponse.json({ ok: true });
    }
    if (action === "hint" || action === "setup" || action === "steps") {
      if (!recordPracticeHelp(doc, qid, action)) {
        return NextResponse.json({ error: "Requested part is locked until earned" }, { status: 403 });
      }
      return NextResponse.json({ ok: true });
    }
    return NextResponse.json({ error: "Invalid practice action" }, { status: 400 });
  } catch {
    return NextResponse.json({ error: "Could not record practice action" }, { status: 500 });
  }
}
