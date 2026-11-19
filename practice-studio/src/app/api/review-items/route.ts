import { NextRequest, NextResponse } from "next/server";
import { isSafeId } from "@/lib/paths";
import {
  getDueReviewItems,
  parseReviewScope,
  recordReviewItemResult,
} from "@/lib/reviewItems";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const rawLimit = searchParams.get("limit");
    const rawToday = searchParams.get("today");
    const rawScope = searchParams.get("scope");

    let limit: number | undefined;
    if (rawLimit !== null && rawLimit.trim() !== "") {
      const parsed = Number(rawLimit);
      if (!Number.isInteger(parsed) || parsed < 0) {
        return NextResponse.json({ error: "Invalid limit" }, { status: 400 });
      }
      limit = parsed;
    }

    let today: string | undefined;
    if (rawToday !== null && rawToday.trim() !== "") {
      const trimmed = rawToday.trim();
      if (!/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
        return NextResponse.json({ error: "Invalid today date format" }, { status: 400 });
      }
      today = trimmed;
    }

    let scope: string | undefined;
    if (rawScope !== null && rawScope.trim() !== "") {
      try {
        const parsedScope = parseReviewScope(rawScope);
        if (parsedScope) {
          scope = `${parsedScope.kind}:${parsedScope.value}`;
        }
      } catch {
        return NextResponse.json({ error: "Invalid scope" }, { status: 400 });
      }
    }

    const result = getDueReviewItems({ today, limit, scope });
    // Never expose trap tags, archetype keys, or lastWrong before the learner answers (zero-leak rule).
    const safeItems = result.items.map((item) => ({
      drillId: item.drillId,
      qid: item.qid,
      unitCode: item.unitCode,
      subject: item.subject,
      commonTrapTag: null,
      archetypeKey: null,
      level: item.level,
      lastReviewed: item.lastReviewed,
      dueDate: item.dueDate,
      revisitNote: item.revisitNote,
    }));
    const { scope: _omittedScope, ...rest } = result;
    void _omittedScope;
    return NextResponse.json({
      ...rest,
      items: safeItems,
    });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: errMsg }, { status: 500 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as Record<string, unknown>;
    const drillId = body?.drillId;
    const qid = body?.qid;
    const correct = body?.correct;
    const hintsUsed = body?.hintsUsed;
    const date = body?.date;

    if (!isSafeId(drillId) || !isSafeId(qid)) {
      return NextResponse.json({ ok: false, error: "Invalid drillId or qid" }, { status: 400 });
    }
    if (typeof correct !== "boolean") {
      return NextResponse.json({ ok: false, error: "Field 'correct' must be a boolean" }, { status: 400 });
    }
    if (
      hintsUsed !== undefined &&
      typeof hintsUsed !== "boolean" &&
      (typeof hintsUsed !== "number" || !Number.isFinite(hintsUsed) || hintsUsed < 0)
    ) {
      return NextResponse.json({ ok: false, error: "Invalid 'hintsUsed' value" }, { status: 400 });
    }
    if (date !== undefined && (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}/.test(date.trim()))) {
      return NextResponse.json({ ok: false, error: "Invalid 'date' format" }, { status: 400 });
    }

    const item = recordReviewItemResult({
      drillId,
      qid,
      correct,
      hintsUsed: hintsUsed as boolean | number | undefined,
      date: typeof date === "string" ? date.trim().slice(0, 10) : undefined,
    });
    return NextResponse.json({ ok: true, item });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
