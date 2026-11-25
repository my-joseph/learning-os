import React, { Suspense } from "react";
import { CodeStudioClient } from "@/components/shell/CodeStudioClient";
import { resolveWorkspaceDrillRoute } from "@/components/shell/WorkspaceDrillRoute";

interface CodeDrillPageProps {
  params: { drillId: string };
  searchParams: { q?: string | string[] };
}

export default function CodeDrillPage({ params, searchParams }: CodeDrillPageProps) {
  const { decodedId, q } = resolveWorkspaceDrillRoute({
    workspace: "code",
    drillId: params.drillId,
    searchParams,
  });

  return (
    <Suspense fallback={null}>
      <CodeStudioClient workspace="code" drillId={decodedId} initialQuestionId={q} />
    </Suspense>
  );
}
