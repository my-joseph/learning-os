"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { DrillListItem } from "@/types/drill";
import { Workspace, workspaceOfListItem } from "@/lib/routes";
import { DrillFilter, StatusMessage } from "./types";

interface UseDrillListOptions {
  workspace: Workspace;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
}

/** Load, search, and filter available practice drills for the active workspace. */
export function useDrillList({ workspace, setStatus }: UseDrillListOptions) {
  const [drills, setDrills] = useState<DrillListItem[]>([]);
  const [drillSearch, setDrillSearch] = useState("");
  const [drillFilter, setDrillFilter] = useState<DrillFilter>("ALL");

  const loadDrillsList = useCallback(async () => {
    try {
      const res = await fetch("/api/drills");
      const data = await res.json();
      const list: DrillListItem[] = data.drills || [];
      setDrills(list);
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

  const filteredDrills = useMemo(() => {
    return workspaceDrills.filter((d) => {
      if (drillFilter === "UNFINISHED" && d.practiceStatus === "Graded") return false;
      if (drillFilter === "GRADED" && d.practiceStatus !== "Graded") return false;

      if (!drillSearch.trim()) return true;
      const q = drillSearch.toLowerCase();
      return (
        d.drillId.toLowerCase().includes(q) ||
        d.unitCode.toLowerCase().includes(q) ||
        (d.unitTitle || "").toLowerCase().includes(q)
      );
    });
  }, [workspaceDrills, drillFilter, drillSearch]);

  return {
    drills,
    workspaceDrills,
    drillSearch,
    setDrillSearch,
    drillFilter,
    setDrillFilter,
    filteredDrills,
    loadDrillsList,
  };
}
