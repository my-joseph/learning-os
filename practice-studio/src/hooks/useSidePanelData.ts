"use client";

import { useState, useEffect } from "react";
import type {
  DueTodayResponse,
  DueTodayUnit,
  WeakSpotUnit,
  WeakSpotsResponse,
} from "@/lib/dueToday";

export function useSidePanelData(
  unitCode?: string | null,
  refreshKey?: string | null
) {
  const [dueUnits, setDueUnits] = useState<DueTodayUnit[]>([]);
  const [dueLoading, setDueLoading] = useState(true);
  const [dueError, setDueError] = useState<string | null>(null);

  const [weakSpotUnits, setWeakSpotUnits] = useState<WeakSpotUnit[]>([]);
  const [weakLoading, setWeakLoading] = useState(false);
  const [weakError, setWeakError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDueLoading(true);
    setDueError(null);

    fetch("/api/due-today", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as DueTodayResponse;
      })
      .then((data) => {
        if (!cancelled) {
          setDueUnits(Array.isArray(data.units) ? data.units : []);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setDueError(err instanceof Error ? err.message : "Failed to load due units");
        }
      })
      .finally(() => {
        if (!cancelled) setDueLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  useEffect(() => {
    const scope = unitCode?.trim();
    if (!scope) {
      setWeakSpotUnits([]);
      setWeakLoading(false);
      setWeakError(null);
      return;
    }

    let cancelled = false;
    setWeakLoading(true);
    setWeakError(null);

    fetch(`/api/weak-spots?scope=${encodeURIComponent(scope)}`, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as WeakSpotsResponse;
      })
      .then((data) => {
        if (!cancelled) {
          setWeakSpotUnits(Array.isArray(data.units) ? data.units : []);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setWeakError(err instanceof Error ? err.message : "Failed to load weak spots");
          setWeakSpotUnits([]);
        }
      })
      .finally(() => {
        if (!cancelled) setWeakLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [unitCode, refreshKey]);

  return {
    dueUnits,
    dueLoading,
    dueError,
    weakSpotUnits,
    weakLoading,
    weakError,
  };
}
