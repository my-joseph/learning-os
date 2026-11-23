"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DrillListItem } from "@/types/drill";
import { drillHref, resolveLandingDrill } from "@/lib/routes";
import { readLastDrillId } from "@/lib/lastDrillStorage";

/** Redirect `/` to the last opened drill from localStorage, or the first drill in the list. */
export const HomeRedirect: React.FC = () => {
  const router = useRouter();
  const [emptyState, setEmptyState] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function resolveDestination() {
      try {
        const res = await fetch("/api/drills");
        if (!res.ok) throw new Error("Failed to load drills");
        const data = await res.json();
        const drills: DrillListItem[] = Array.isArray(data.drills) ? data.drills : [];
        const lastId = readLastDrillId();
        const targetId = resolveLandingDrill(drills, lastId);
        if (cancelled) return;
        if (targetId) {
          router.replace(drillHref(targetId));
        } else {
          setEmptyState("No practice drills are available yet.");
        }
      } catch {
        if (!cancelled) {
          setEmptyState("Unable to load practice drills right now.");
        }
      }
    }
    resolveDestination();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center">
        {emptyState ? (
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{emptyState}</p>
        ) : (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Opening Practice Studio...
          </p>
        )}
      </div>
    </div>
  );
};
