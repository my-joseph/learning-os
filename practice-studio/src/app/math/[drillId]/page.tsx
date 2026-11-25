import React, { Suspense } from "react";
import { MathStudioClient } from "@/components/shell/MathStudioClient";
import { resolveWorkspaceDrillRoute } from "@/components/shell/WorkspaceDrillRoute";

interface MathDrillPageProps {
  params: { drillId: string };
  searchParams: { q?: string | string[] };
}

export default function MathDrillPage({ params, searchParams }: MathDrillPageProps) {
  const { decodedId, q } = resolveWorkspaceDrillRoute({
    workspace: "math",
    drillId: params.drillId,
    searchParams,
  });

  return (
    <Suspense fallback={null}>
      <MathStudioClient workspace="math" drillId={decodedId} initialQuestionId={q} />
    </Suspense>
  );
}
