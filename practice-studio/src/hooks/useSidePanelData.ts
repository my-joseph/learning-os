"use client";

import { useState, useEffect, useMemo } from "react";
import type {
  DueTodayResponse,
  UnitMasteryContext,
  WeakSpotUnit,
  WeakSpotsResponse,
} from "@/lib/dueToday";
import type { Workspace } from "@/lib/routes";

interface ReviewItemsApiPayload {
  totalDue?: number;
  bySubject?: { MTH?: number; PRG?: number };
  estimatedMinutes?: number;
  nextDueDate?: string | null;
  items?: Array<{ drillId?: string; unitCode?: string }>;
}

export function useSidePanelData(
  workspace: Workspace,
  unitCode?: string | null,
  refreshKey?: string | null
) {
  const workspaceSubject = workspace === "code" ? "PRG" : "MTH";
  const otherSubject = workspace === "code" ? "MTH" : "PRG";

  const [dueReviewCount, setDueReviewCount] = useState<number>(0);
  const [reviewSessionSize, setReviewSessionSize] = useState<number>(0);
  const [otherWorkspaceDueCount, setOtherWorkspaceDueCount] = useState<number>(0);
  const [estimatedMinutes, setEstimatedMinutes] = useState<number>(0);
  const [nextDueDate, setNextDueDate] = useState<string | null>(null);
  const [dueUnitCodes, setDueUnitCodes] = useState<string[]>([]);
  const [dueReviewDrillIds, setDueReviewDrillIds] = useState<string[]>([]);
  const [dueTodayUnitCodes, setDueTodayUnitCodes] = useState<string[]>([]);
  const [dueLoading, setDueLoading] = useState(true);
  const [dueError, setDueError] = useState<string | null>(null);
  const [unitScheduleLoading, setUnitScheduleLoading] = useState(true);
  const [unitScheduleError, setUnitScheduleError] = useState(false);

  const [unitMasteryByCode, setUnitMasteryByCode] = useState<
    Record<string, UnitMasteryContext>
  >({});

  const [weakSpotUnits, setWeakSpotUnits] = useState<WeakSpotUnit[]>([]);
  const [weakLoading, setWeakLoading] = useState(false);
  const [weakError, setWeakError] = useState<string | null>(null);
  const [weakLoadedScope, setWeakLoadedScope] = useState<string | null>(null);
  const scope = unitCode?.trim() || null;

  useEffect(() => {
    let cancelled = false;
    setDueLoading(true);
    setDueError(null);
    setUnitScheduleLoading(true);
    setUnitScheduleError(false);

    fetch(`/api/review-items?limit=8&scope=${encodeURIComponent(`subject:${workspaceSubject}`)}`, {
      cache: "no-store",
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as ReviewItemsApiPayload;
      })
      .then((data) => {
        if (cancelled) return;
        const items = Array.isArray(data.items) ? data.items : [];
        const count =
          typeof data.totalDue === "number" ? data.totalDue : items.length;
        setReviewSessionSize(items.length);
        const otherCount =
          typeof data.bySubject?.[otherSubject] === "number"
            ? data.bySubject[otherSubject]!
            : 0;
        const minutes =
          typeof data.estimatedMinutes === "number" ? data.estimatedMinutes : 0;
        const codes = Array.from(
          new Set(
            items
              .map((it) => (typeof it?.unitCode === "string" ? it.unitCode : ""))
              .filter(Boolean)
          )
        );

        setDueReviewCount(Math.max(0, count));
        setOtherWorkspaceDueCount(Math.max(0, otherCount));
        setEstimatedMinutes(Math.max(0, minutes));
        setNextDueDate(typeof data.nextDueDate === "string" ? data.nextDueDate : null);
        setDueUnitCodes(codes);
        setDueReviewDrillIds(items.flatMap((item) =>
          typeof item?.drillId === "string" ? [item.drillId] : []
        ));
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setDueError(err instanceof Error ? err.message : "Failed to load reviews");
          setDueReviewCount(0);
          setOtherWorkspaceDueCount(0);
          setEstimatedMinutes(0);
          setDueUnitCodes([]);
          setDueReviewDrillIds([]);
        }
      })
      .finally(() => {
        if (!cancelled) setDueLoading(false);
      });

    // Unit schedules also feed Search. The side-panel queue counts item-level reviews.
    fetch("/api/due-today", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as DueTodayResponse;
      })
      .then((data) => {
        if (!cancelled) {
          setDueTodayUnitCodes(Array.isArray(data?.units)
            ? data.units.map(({ unitCode }) => unitCode)
            : []);
        }
        if (!cancelled && data?.unitMastery && typeof data.unitMastery === "object") {
          setUnitMasteryByCode(data.unitMastery);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDueTodayUnitCodes([]);
          setUnitScheduleError(true);
        }
      })
      .finally(() => {
        if (!cancelled) setUnitScheduleLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [workspaceSubject, otherSubject, refreshKey]);

  useEffect(() => {
    if (!scope) {
      setWeakSpotUnits([]);
      setWeakLoading(false);
      setWeakError(null);
      setWeakLoadedScope(null);
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
        if (!cancelled) {
          setWeakLoadedScope(scope);
          setWeakLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [scope, refreshKey]);

  const currentUnitMastery = useMemo(() => {
    if (!scope) return null;
    return unitMasteryByCode[scope] ?? null;
  }, [scope, unitMasteryByCode]);

  const weakScopeMatches = scope !== null && weakLoadedScope === scope;

  return {
    dueReviewCount,
    reviewSessionSize,
    otherWorkspaceDueCount,
    estimatedMinutes,
    nextDueDate,
    dueUnitCodes,
    searchDueIds: [...dueReviewDrillIds, ...dueTodayUnitCodes],
    searchDueLoading: dueLoading || unitScheduleLoading,
    searchDueError: Boolean(dueError) || unitScheduleError,
    currentUnitMastery,
    dueLoading,
    dueError,
    weakSpotUnits: weakScopeMatches ? weakSpotUnits : [],
    weakLoading: scope !== null && (weakLoading || !weakScopeMatches),
    weakError: weakScopeMatches ? weakError : null,
  };
}
