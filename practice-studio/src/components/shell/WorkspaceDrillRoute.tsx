import React, { Suspense } from "react";
import { redirect } from "next/navigation";
import { StudioClient } from "./StudioClient";
import { Workspace, drillHref, isLabId, labHref, subjectOf } from "@/lib/routes";

interface WorkspaceDrillRouteProps {
  workspace: Workspace;
  drillId: string;
  searchParams: { q?: string | string[]; m?: string | string[] };
  isLabRoute?: boolean;
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/** Shared server route handler for `/math/[drillId]`, `/code/[drillId]`, and `/code/lab/[labId]`. */
export function WorkspaceDrillRoute({
  workspace,
  drillId,
  searchParams,
  isLabRoute = false,
}: WorkspaceDrillRouteProps) {
  const decodedId = safeDecode(drillId);
  const rawParam = isLabRoute
    ? searchParams.m ?? searchParams.q
    : searchParams.q ?? searchParams.m;
  const q =
    typeof rawParam === "string"
      ? rawParam
      : Array.isArray(rawParam)
      ? rawParam[0]
      : undefined;

  if (isLabRoute) {
    if (!isLabId(decodedId) && subjectOf(decodedId)) {
      redirect(drillHref(decodedId, q));
    }
  } else {
    if (isLabId(decodedId)) {
      redirect(labHref(decodedId, q));
    }

    const expected = subjectOf(decodedId);
    if (expected && expected !== workspace) {
      redirect(drillHref(decodedId, q));
    }
  }

  return (
    <Suspense fallback={null}>
      <StudioClient
        workspace={workspace}
        drillId={decodedId}
        initialQuestionId={q}
        isLabRoute={isLabRoute || undefined}
      />
    </Suspense>
  );
}
