"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { Workspace, workspaceOfListItem } from "@/lib/routes";
import { StatusMessage } from "./types";

interface UseDrillListOptions {
  workspace: Workspace;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
}

/** Load available practice drills and project labs for the active workspace. */
export function useDrillList({ workspace, setStatus }: UseDrillListOptions) {
  const [drills, setDrills] = useState<DrillListItem[]>([]);
  const [labs, setLabs] = useState<LabListItem[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState(false);

  const loadDrillsList = useCallback(async () => {
    setCatalogLoading(true);
    setCatalogError(false);
    try {
      const [drillsRes, labsRes] = await Promise.all([
        fetch("/api/drills"),
        fetch("/api/labs").catch(() => null),
      ]);
      if (!drillsRes.ok) throw new Error(`HTTP ${drillsRes.status}`);
      const data = await drillsRes.json();
      const list: DrillListItem[] = data.drills || [];
      setDrills(list);
      if (labsRes && labsRes.ok) {
        const labsData = await labsRes.json();
        setLabs(Array.isArray(labsData.labs) ? labsData.labs : []);
      } else {
        setCatalogError(true);
      }
    } catch (err: unknown) {
      setCatalogError(true);
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Failed to fetch drills list: ${errMsg}`, type: "fail" });
    } finally {
      setCatalogLoading(false);
    }
  }, [setStatus]);

  useEffect(() => {
    loadDrillsList();
  }, [loadDrillsList]);

  const workspaceDrills = useMemo(
    () => drills.filter((d) => workspaceOfListItem(d) === workspace),
    [drills, workspace]
  );

  const workspaceLabs = useMemo(
    () => (workspace === "code" ? labs : []),
    [labs, workspace]
  );

  return {
    drills,
    labs,
    workspaceDrills,
    workspaceLabs,
    catalogLoading,
    catalogError,
    loadDrillsList,
  };
}
