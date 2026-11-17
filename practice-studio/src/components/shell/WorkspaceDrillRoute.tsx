import React, { Suspense } from "react";
import { redirect } from "next/navigation";
import { StudioClient } from "./StudioClient";
import { Workspace, drillHref, subjectOf } from "@/lib/routes";

interface WorkspaceDrillRouteProps {
  workspace: Workspace;
  drillId: string;
  searchParams: { q?: string | string[] };
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
  const q =
    typeof searchParams.q === "string"
      ? searchParams.q
      : Array.isArray(searchParams.q)
      ? searchParams.q[0]
      : undefined;

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
