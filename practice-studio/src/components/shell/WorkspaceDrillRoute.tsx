import React, { Suspense } from "react";
import { redirect } from "next/navigation";
import { StudioClient } from "./StudioClient";
import { Workspace, drillHref, isLabId, labHref, subjectOf } from "@/lib/routes";

interface WorkspaceDrillRouteProps {
  workspace: Workspace;
  drillId: string;
  searchParams: { q?: string | string[]; m?: string | string[] };
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/** Shared server route handler for `/math/[drillId]` and `/code/[drillId]`. */
export function WorkspaceDrillRoute({
  workspace,
  drillId,
  searchParams,
}: WorkspaceDrillRouteProps) {
  const decodedId = safeDecode(drillId);
  const rawParam = searchParams.q ?? searchParams.m;
  const q =
    typeof rawParam === "string"
      ? rawParam
      : Array.isArray(rawParam)
      ? rawParam[0]
      : undefined;

  if (isLabId(decodedId)) {
    redirect(labHref(decodedId, q));
  }

  const expected = subjectOf(decodedId);
  if (expected && expected !== workspace) {
    redirect(drillHref(decodedId, q));
  }

  return (
    <Suspense fallback={null}>
      <StudioClient workspace={workspace} drillId={decodedId} initialQuestionId={q} />
    </Suspense>
  );
}
