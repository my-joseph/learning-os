import { redirect } from "next/navigation";
import { Workspace, drillHref, isLabId, labHref, subjectOf } from "@/lib/routes";

interface ResolveWorkspaceRouteInput {
  workspace: Workspace;
  drillId: string;
  searchParams: { q?: string | string[]; m?: string | string[] };
  isLabRoute?: boolean;
}

export interface ResolvedWorkspaceRoute {
  decodedId: string;
  q?: string;
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

/** Shared server route validation and redirect helper for `/math/[drillId]`, `/code/[drillId]`, and `/code/lab/[labId]`. */
export function resolveWorkspaceDrillRoute({
  workspace,
  drillId,
  searchParams,
  isLabRoute = false,
}: ResolveWorkspaceRouteInput): ResolvedWorkspaceRoute {
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

  return { decodedId, q };
}
