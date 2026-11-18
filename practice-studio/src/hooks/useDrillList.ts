"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { Workspace, workspaceOfListItem } from "@/lib/routes";
import { filterDrills, filterLabs } from "@/lib/drillGrouping";
import { DrillFilter, StatusMessage } from "./types";

interface UseDrillListOptions {
  workspace: Workspace;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
}

/** Load, search, and filter available practice drills (and project labs in Programming) for the active workspace. */
export function useDrillList({ workspace, setStatus }: UseDrillListOptions) {
  const [drills, setDrills] = useState<DrillListItem[]>([]);
  const [labs, setLabs] = useState<LabListItem[]>([]);
  const [drillSearch, setDrillSearch] = useState("");
  const [drillFilter, setDrillFilter] = useState<DrillFilter>("ALL");

  const loadDrillsList = useCallback(async () => {
    try {
      const [drillsRes, labsRes] = await Promise.all([
        fetch("/api/drills"),
        fetch("/api/labs").catch(() => null),
      ]);
      const data = await drillsRes.json();
      const list: DrillListItem[] = data.drills || [];
      setDrills(list);
      if (labsRes && labsRes.ok) {
        const labsData = await labsRes.json();
        setLabs(Array.isArray(labsData.labs) ? labsData.labs : []);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setStatus({ text: `Failed to fetch drills list: ${errMsg}`, type: "fail" });
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

  const filteredDrills = useMemo(
    () => filterDrills(workspaceDrills, drillSearch, drillFilter),
    [workspaceDrills, drillFilter, drillSearch]
  );

  const filteredLabs = useMemo(
    () => filterLabs(workspaceLabs, drillSearch, drillFilter),
    [workspaceLabs, drillFilter, drillSearch]
  );

  return {
    drills,
    labs,
    workspaceDrills,
    workspaceLabs,
    drillSearch,
    setDrillSearch,
    drillFilter,
    setDrillFilter,
    filteredDrills,
    filteredLabs,
    loadDrillsList,
  };
}
