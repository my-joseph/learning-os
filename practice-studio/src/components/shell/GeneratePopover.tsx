"use client";

import React, { useState, useEffect, useId, useMemo, useRef } from "react";
import { AnimatePresence, m } from "motion/react";
import { dialogCard, fade, presence } from "@/lib/motion";
import { Plus, RefreshCw, X } from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import { StatusMessage } from "@/hooks/types";
import { Workspace } from "@/lib/routes";
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

  const cardRef = useRef<HTMLDivElement | null>(null);
  const unitSelectRef = useRef<HTMLSelectElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

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
    const allowedDiffs = ["ALL", "1", "2", "3", "4"];
    const loadedDiff = String(currentDrill.config.difficulty || "ALL").toUpperCase();
    setCfgDifficulty(allowedDiffs.includes(loadedDiff) ? loadedDiff : "ALL");
  }, [currentDrill]);

  // Capture trigger focus on open, focus Unit select, and restore focus on close.
  useEffect(() => {
    if (isOpen && !wasOpenRef.current) {
      previousFocusRef.current =
        document.activeElement instanceof HTMLElement ? document.activeElement : null;
      wasOpenRef.current = true;
      const rafId = requestAnimationFrame(() => unitSelectRef.current?.focus());
      return () => cancelAnimationFrame(rafId);
    }

    if (!isOpen && wasOpenRef.current) {
      wasOpenRef.current = false;
      const prev = previousFocusRef.current;
      previousFocusRef.current = null;
      if (prev && prev.isConnected) {
        prev.focus();
      }
    }
  }, [isOpen]);

  // Escape closes; Tab wraps within dialog controls while open.
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onClose();
        return;
      }

      if (e.key === "Tab" && cardRef.current) {
        const focusable = Array.from(
          cardRef.current.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          )
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [isOpen, onClose]);

  const handleGenerateDrill = async () => {
    if (!cfgUnit) return;
    setIsGenerating(true);
    const isPrg = cfgUnit.startsWith("PRG-");
    const engineLabel = isPrg ? "Node.js" : "SymPy";
    const itemNoun = isPrg ? "problems" : "questions";
    const selectedOption = unitOptions.find((u) => u.unitCode === cfgUnit);
    const unitLabel =
      selectedOption?.unitTitle && selectedOption.unitTitle !== cfgUnit
        ? selectedOption.unitTitle
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

  return (
    <AnimatePresence>
      {isOpen && (
        <m.div
          key="generate-drill-dialog"
          {...presence}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <m.div
            variants={fade}
            aria-hidden="true"
            onClick={onClose}
            className="fixed inset-0 bg-zinc-950/40 backdrop-blur-[1px]"
          />
          <m.div
            ref={cardRef}
            variants={dialogCard}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="relative z-10 w-full max-w-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-lg p-5 space-y-4 text-xs"
          >
            <div className="flex items-center justify-between">
              <h2
                id={titleId}
                className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
              >
                Generate drill set
              </h2>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close generator"
                className="inline-flex items-center justify-center w-7 h-7 rounded-lg text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
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
                className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/25 dark:focus-visible:ring-indigo-400/35 focus-visible:border-indigo-600 dark:focus-visible:border-indigo-400"
              >
                {unitOptions.length === 0 ? (
                  <option value="">No units available</option>
                ) : (
                  unitGroups.map((group) => (
                    <optgroup key={group.groupCode} label={group.groupCode}>
                      {group.items.map((u) => (
                        <option key={u.unitCode} value={u.unitCode}>
                          {u.unitTitle && u.unitTitle !== u.unitCode
                            ? `${u.unitCode} · ${u.unitTitle}`
                            : u.unitCode}
                        </option>
                      ))}
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
                  className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/25 dark:focus-visible:ring-indigo-400/35 focus-visible:border-indigo-600 dark:focus-visible:border-indigo-400"
                >
                  <option value={5}>5 Qs</option>
                  <option value={8}>8 Qs</option>
                  <option value={10}>10 Qs</option>
                  <option value={15}>15 Qs</option>
                  <option value={20}>20 Qs</option>
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
                  className="w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-2.5 py-2 text-xs text-zinc-900 dark:text-zinc-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600/25 dark:focus-visible:ring-indigo-400/35 focus-visible:border-indigo-600 dark:focus-visible:border-indigo-400"
                >
                  <option value="ALL">Mixed</option>
                  <option value="1">Level 1</option>
                  <option value="2">Level 2</option>
                  <option value="3">Level 3</option>
                  <option value="4">Level 4</option>
                </select>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGenerateDrill}
              disabled={isGenerating || !cfgUnit}
              className="w-full inline-flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold h-9 rounded-xl transition-colors"
            >
              {isGenerating ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Plus className="w-3.5 h-3.5" />
              )}
              <span>{isGenerating ? "Generating..." : "Generate set"}</span>
            </button>
          </m.div>
        </m.div>
      )}
    </AnimatePresence>
  );
};
