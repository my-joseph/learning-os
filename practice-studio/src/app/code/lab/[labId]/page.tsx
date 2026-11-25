import React, { Suspense } from "react";
import { CodeStudioClient } from "@/components/shell/CodeStudioClient";
import { resolveWorkspaceDrillRoute } from "@/components/shell/WorkspaceDrillRoute";

interface CodeLabPageProps {
  params: { labId: string };
  searchParams: { m?: string | string[]; q?: string | string[] };
}

export default function CodeLabPage({ params, searchParams }: CodeLabPageProps) {
  const { decodedId, q } = resolveWorkspaceDrillRoute({
    workspace: "code",
    drillId: params.labId,
    searchParams,
    isLabRoute: true,
  });

  return (
    <Suspense fallback={null}>
      <CodeStudioClient
        workspace="code"
        drillId={decodedId}
        initialQuestionId={q}
        isLabRoute={true}
      />
    </Suspense>
  );
}
