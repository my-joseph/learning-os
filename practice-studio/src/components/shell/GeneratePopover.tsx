"use client";

import React, { useState, useEffect, useId, useMemo, useRef } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/shadcn/Dialog";
import { DrillDocument, DrillListItem } from "@/types/drill";
import { StatusMessage } from "@/hooks/types";
import { Workspace } from "@/lib/routes";
import { plainTitle } from "@/lib/titleText";
import {
  buildGenerateUnitOptions,
  groupGenerateUnitOptions,
} from "@/lib/drillGrouping";

interface GeneratePopoverProps {
  isOpen: boolean;
  onClose: () => void;
  workspace: Workspace;
  drills: DrillListItem[];
  currentDrill: DrillDocument | null;
  onGenerated: (drillId: string) => Promise<void>;
  onStatusChange: (status: StatusMessage | null) => void;
}

/** Drill-generation dialog triggered from the header Generate button or empty state. */
export const GeneratePopover: React.FC<GeneratePopoverProps> = ({
  isOpen,
  onClose,
  workspace,
  drills,
  currentDrill,
  onGenerated,
  onStatusChange,
}) => {
  const titleId = useId();
  const descriptionId = useId();
  const unitFieldId = useId();
  const countFieldId = useId();
  const levelFieldId = useId();

  const unitOptions = useMemo(
    () => buildGenerateUnitOptions(drills, workspace, currentDrill),
    [drills, workspace, currentDrill]
  );
  const unitGroups = useMemo(
    () => groupGenerateUnitOptions(unitOptions),
    [unitOptions]
  );

  const [cfgUnit, setCfgUnit] = useState(
    () => currentDrill?.unitCode || unitOptions[0]?.unitCode || ""
  );
  const [cfgCount, setCfgCount] = useState(5);
  const [cfgDifficulty, setCfgDifficulty] = useState("ALL");
  const [isGenerating, setIsGenerating] = useState(false);

  const unitSelectRef = useRef<HTMLSelectElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Keep selected unit synced to currentDrill or first available workspace unit.
  useEffect(() => {
    if (currentDrill?.unitCode) {
      const hasMatch = unitOptions.some((u) => u.unitCode === currentDrill.unitCode);
      if (hasMatch) {
        setCfgUnit(currentDrill.unitCode);
        return;
      }
    }
    if (!unitOptions.some((u) => u.unitCode === cfgUnit)) {
      setCfgUnit(unitOptions[0]?.unitCode || "");
    }
  }, [currentDrill?.unitCode, unitOptions, cfgUnit]);

  useEffect(() => {
    if (!currentDrill?.config) return;
    const allowedCounts = [5, 8, 10, 15, 20];
    const loadedCount = Number(currentDrill.config.questionCount);
    setCfgCount(allowedCounts.includes(loadedCount) ? loadedCount : 5);
    const allowedDiffs = ["ALL", "1", "2", "3", "4", "5"];
    const loadedDiff = String(currentDrill.config.difficulty || "ALL").toUpperCase();
    setCfgDifficulty(allowedDiffs.includes(loadedDiff) ? loadedDiff : "ALL");
  }, [currentDrill]);

  const handleGenerateDrill = async () => {
    if (!cfgUnit) return;
    setIsGenerating(true);
    const isPrg = cfgUnit.startsWith("PRG-");
    const engineLabel = isPrg ? "Node.js" : "SymPy";
    const itemNoun = isPrg ? "problems" : "questions";
    const selectedOption = unitOptions.find((u) => u.unitCode === cfgUnit);
    const selectedTitle = plainTitle(selectedOption?.unitTitle);
    const unitLabel =
      selectedTitle && selectedTitle !== cfgUnit
        ? selectedTitle
        : cfgUnit;
    onStatusChange({
      text: `Generating and verifying ${cfgCount} ${itemNoun} with ${engineLabel}...`,
      type: "warn",
    });

    try {
      const res = await fetch("/api/generate-drill", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unitCode: cfgUnit,
          count: cfgCount,
          difficulty: cfgDifficulty,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Generation failed");

      onStatusChange({
        text: `Generated & verified ${unitLabel} (${cfgCount} ${itemNoun})!`,
        type: "pass",
      });
      onClose();
      await onGenerated(data.drillId);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      onStatusChange({ text: `Generation error: ${errMsg}`, type: "fail" });
    } finally {
      setIsGenerating(false);
    }
  };

  const countNoun =
    workspace === "code" || cfgUnit.startsWith("PRG-") ? "problems" : "questions";

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          onClose();
        }
      }}
    >
      <DialogContent
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onOpenAutoFocus={(e) => {
          previousFocusRef.current =
            document.activeElement instanceof HTMLElement ? document.activeElement : null;
          if (unitSelectRef.current) {
            e.preventDefault();
            unitSelectRef.current.focus();
          }
        }}
        onCloseAutoFocus={(e) => {
          e.preventDefault();
          const prev = previousFocusRef.current;
          previousFocusRef.current = null;
          if (prev && prev.isConnected) {
            prev.focus();
          }
        }}
        className="max-w-sm space-y-4 rounded-2xl bg-white p-5 text-xs shadow-lg dark:bg-zinc-900"
      >
        <div className="pr-10">
          <DialogTitle
            id={titleId}
            className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
          >
            Generate drill set
          </DialogTitle>
          <DialogDescription id={descriptionId} className="sr-only">
            Choose a unit, item count, and difficulty level to generate a drill set.
          </DialogDescription>
        </div>

        <div>
          <label
            htmlFor={unitFieldId}
            className="block text-zinc-500 dark:text-zinc-400 mb-1"
          >
            Unit
          </label>
          <select
            ref={unitSelectRef}
            id={unitFieldId}
            value={cfgUnit}
            onChange={(e) => setCfgUnit(e.target.value)}
            disabled={unitOptions.length === 0}
            className="w-full bg-surface-panel dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/25 dark:focus-visible:ring-indigo-400/35 focus-visible:border-indigo-600 dark:focus-visible:border-indigo-400"
          >
            {unitOptions.length === 0 ? (
              <option value="">No units available</option>
            ) : (
              unitGroups.map((group) => (
                <optgroup key={group.groupCode} label={group.groupCode}>
                  {group.items.map((u) => {
                    const cleanTitle = plainTitle(u.unitTitle);
                    return (
                      <option key={u.unitCode} value={u.unitCode}>
                        {cleanTitle && cleanTitle !== u.unitCode
                          ? `${u.unitCode} · ${cleanTitle}`
                          : u.unitCode}
                      </option>
                    );
                  })}
                </optgroup>
              ))
            )}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <label
              htmlFor={countFieldId}
              className="block text-zinc-500 dark:text-zinc-400 mb-1"
            >
              Count
            </label>
            <select
              id={countFieldId}
              value={cfgCount}
              onChange={(e) => setCfgCount(Number(e.target.value))}
              className="w-full bg-surface-panel dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/25 dark:focus-visible:ring-indigo-400/35 focus-visible:border-indigo-600 dark:focus-visible:border-indigo-400"
            >
              {[5, 8, 10, 15, 20].map((n) => (
                <option key={n} value={n}>
                  {n} {countNoun}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor={levelFieldId}
              className="block text-zinc-500 dark:text-zinc-400 mb-1"
            >
              Level
            </label>
            <select
              id={levelFieldId}
              value={cfgDifficulty}
              onChange={(e) => setCfgDifficulty(e.target.value)}
              className="w-full bg-surface-panel dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/25 dark:focus-visible:ring-indigo-400/35 focus-visible:border-indigo-600 dark:focus-visible:border-indigo-400"
            >
              <option value="ALL">Mixed</option>
              <option value="1">Level 1</option>
              <option value="2">Level 2</option>
              <option value="3">Level 3</option>
              <option value="4">Level 4</option>
              <option value="5">Level 5</option>
            </select>
          </div>
        </div>

        <Button
          type="button"
          variant="primary"
          onClick={handleGenerateDrill}
          disabled={isGenerating || !cfgUnit}
          className="w-full rounded-xl text-xs"
        >
          {isGenerating ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
          ) : (
            <Plus className="w-3.5 h-3.5" />
          )}
          <span>{isGenerating ? "Generating..." : "Generate set"}</span>
        </Button>
      </DialogContent>
    </Dialog>
  );
};
