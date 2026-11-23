import React from "react";
import { redirect } from "next/navigation";
import { DrillNotFoundCard } from "@/components/shell/DrillNotFoundCard";
import { HomeRedirect } from "@/components/shell/HomeRedirect";
import { drillHref, parseLegacyQuery, subjectOf } from "@/lib/routes";

interface RootPageProps {
  searchParams: Record<string, string | string[] | undefined>;
}

export default function PracticeStudioRootPage({ searchParams }: RootPageProps) {
  const legacy = parseLegacyQuery(searchParams);
  if (legacy) {
    if (subjectOf(legacy.drillId)) {
      redirect(drillHref(legacy.drillId, legacy.qid));
    }
    return (
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <DrillNotFoundCard drillId={legacy.drillId} />
        </div>
      </div>
    );
  }

  return <HomeRedirect />;
}
