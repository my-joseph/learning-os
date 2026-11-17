import React, { Suspense } from "react";
import { redirect } from "next/navigation";
import { StudioClient } from "@/components/shell/StudioClient";
import { drillHref, isLabId, subjectOf } from "@/lib/routes";

interface CodeLabPageProps {
  params: { labId: string };
  searchParams: { m?: string | string[]; q?: string | string[] };
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export default function CodeLabPage({ params, searchParams }: CodeLabPageProps) {
  const decodedId = safeDecode(params.labId);
  const rawMilestone = searchParams.m ?? searchParams.q;
  const milestone =
    typeof rawMilestone === "string"
      ? rawMilestone
      : Array.isArray(rawMilestone)
      ? rawMilestone[0]
      : undefined;

  if (!isLabId(decodedId) && subjectOf(decodedId)) {
    redirect(drillHref(decodedId, milestone));
  }

  return (
    <Suspense fallback={null}>
      <StudioClient
        workspace="code"
        drillId={decodedId}
        initialQuestionId={milestone}
      />
    </Suspense>
  );
}
