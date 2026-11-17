"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { DrillListItem } from "@/types/drill";
import { DrillFilter, StatusMessage } from "./types";

interface UseDrillListOptions {
  loadDrill: (id: string) => Promise<void>;
  setIsLoadingDrill: React.Dispatch<React.SetStateAction<boolean>>;
  setStatus: React.Dispatch<React.SetStateAction<StatusMessage | null>>;
}

/** Load, search, and filter the list of available practice drills. */
export function useDrillList({ loadDrill, setIsLoadingDrill, setStatus }: UseDrillListOptions) {
  const [drills, setDrills] = useState<DrillListItem[]>([]);
  const [selectedDrillId, setSelectedDrillId] = useState<string>("");
  const [drillSearch, setDrillSearch] = useState("");
  const [drillFilter, setDrillFilter] = useState<DrillFilter>("ALL");

  const loadDrillsList = useCallback(
    async (preferredId?: string) => {
      try {
        const res = await fetch("/api/drills");
        const data = await res.json();
        const list: DrillListItem[] = data.drills || [];
        setDrills(list);

        if (list.length > 0) {
          const targetId = preferredId || selectedDrillId || list[0].drillId;
          setSelectedDrillId(targetId);
          await loadDrill(targetId);
        } else {
          setIsLoadingDrill(false);
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        setStatus({ text: `Failed to fetch drills list: ${errMsg}`, type: "fail" });
        setIsLoadingDrill(false);
      }
    },
    [loadDrill, selectedDrillId, setIsLoadingDrill, setStatus]
  );

  useEffect(() => {
    loadDrillsList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredDrills = useMemo(() => {
    return drills.filter((d) => {
      if (drillFilter === "UNFINISHED" && d.practiceStatus === "Graded") return false;
      if (drillFilter === "GRADED" && d.practiceStatus !== "Graded") return false;
      if (drillFilter === "MATH" && d.subject !== "MATH") return false;
      if (drillFilter === "PRG" && d.subject !== "PRG") return false;

      if (!drillSearch.trim()) return true;
      const q = drillSearch.toLowerCase();
      return (
        d.drillId.toLowerCase().includes(q) ||
        d.unitCode.toLowerCase().includes(q) ||
        (d.unitTitle || "").toLowerCase().includes(q)
      );
    });
  }, [drills, drillFilter, drillSearch]);

  return {
    drills,
    selectedDrillId,
    setSelectedDrillId,
    drillSearch,
    setDrillSearch,
    drillFilter,
    setDrillFilter,
    filteredDrills,
    loadDrillsList,
  };
}
