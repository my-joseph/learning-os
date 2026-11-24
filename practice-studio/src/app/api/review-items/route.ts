import { NextRequest, NextResponse } from "next/server";
import { isSafeId } from "@/lib/paths";
import {
  getDueReviewItems,
  parseReviewScope,
  completeReviewItem,
  type ReviewItem,
} from "@/lib/reviewItems";

export const dynamic = "force-dynamic";

function projectReviewItem(item: ReviewItem) {
  return {
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
  };
}

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
    const { scope: _omittedScope, ...rest } = result;
    void _omittedScope;
    return NextResponse.json({
      ...rest,
      items: result.items.map(projectReviewItem),
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
    const eventId = body?.eventId;
    if (!isSafeId(drillId) || !isSafeId(qid) || !isSafeId(eventId)) {
      return NextResponse.json({ ok: false, error: "Invalid drillId, qid, or eventId" }, { status: 400 });
    }
    const item = completeReviewItem(drillId, qid, eventId);
    if (!item) {
      return NextResponse.json({ ok: false, error: "No matching check for the current review cycle" }, { status: 409 });
    }
    return NextResponse.json({ ok: true, item: projectReviewItem(item) });
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ ok: false, error: errMsg }, { status: 500 });
  }
}
