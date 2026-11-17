"use client";

import React, { useState, useEffect } from "react";
import { Plus, RefreshCw, X } from "lucide-react";
import { DrillDocument } from "@/types/drill";
import { StatusMessage } from "@/hooks/types";

interface GeneratePopoverProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  popoverRef: React.RefObject<HTMLDivElement>;
  currentDrill: DrillDocument | null;
  onGenerated: (drillId: string) => Promise<void>;
  onStatusChange: (status: StatusMessage | null) => void;
}

/** Tucked drill-generation popover (hidden while deprecated template generator is retired). */
export const GeneratePopover: React.FC<GeneratePopoverProps> = ({
  isOpen,
  onToggle,
  onClose,
  popoverRef,
  currentDrill,
  onGenerated,
  onStatusChange,
}) => {
  const [cfgUnit, setCfgUnit] = useState("MTH-T02-C01-U01");
  const [cfgCount, setCfgCount] = useState(5);
  const [cfgDifficulty, setCfgDifficulty] = useState("ALL");
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (!currentDrill) return;
    if (currentDrill.unitCode) {
      setCfgUnit(currentDrill.unitCode);
    }
    if (currentDrill.config) {
      const allowedCounts = [5, 8, 10, 15, 20];
      const loadedCount = Number(currentDrill.config.questionCount);
      if (allowedCounts.includes(loadedCount)) {
        setCfgCount(loadedCount);
      } else {
        setCfgCount(5);
      }
      const allowedDiffs = ["ALL", "1", "2", "3", "4"];
      const loadedDiff = String(currentDrill.config.difficulty || "ALL").toUpperCase();
      if (allowedDiffs.includes(loadedDiff)) {
        setCfgDifficulty(loadedDiff);
      } else {
        setCfgDifficulty("ALL");
      }
    }
  }, [currentDrill]);

  const handleGenerateDrill = async () => {
    setIsGenerating(true);
    const engineLabel = cfgUnit.startsWith("PRG-") ? "Node.js" : "SymPy";
    onStatusChange({
      text: `Generating and verifying ${cfgCount} questions with ${engineLabel}...`,
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
        text: `Generated & verified ${data.drillId} (${cfgCount} questions)!`,
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
    /* Tucked Pre-Generation Config Popover (+ Generate). Hidden: it runs the deprecated template
       generator (math_engine.generate); drills are made with the new-math-drill skill instead. */
    <div className="relative shrink-0 hidden" ref={popoverRef}>
      <button
        type="button"
        onClick={onToggle}
        className="inline-flex items-center gap-1.5 h-10 px-3 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-indigo-50 dark:hover:bg-indigo-600/20 text-slate-700 dark:text-slate-200 hover:text-indigo-700 dark:hover:text-indigo-300 border border-slate-200 dark:border-[#2c354d] text-xs font-semibold transition-colors"
        title="Generate a new verified drill set"
      >
        <Plus className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Generate</span>
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-80 bg-white dark:bg-[#161c2a] border border-slate-200 dark:border-[#2c354d] rounded-2xl shadow-2xl p-4 z-50 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 dark:border-[#252f45] pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Generate New Drill Set (.json)
            </span>
            <button
              type="button"
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-2.5 text-xs">
            <div>
              <label className="block text-slate-600 dark:text-slate-400 mb-1 font-medium">
                Target Unit
              </label>
              <select
                value={cfgUnit}
                onChange={(e) => setCfgUnit(e.target.value)}
                className="w-full bg-slate-50 dark:bg-[#1d2333] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-2 text-xs text-slate-900 dark:text-slate-200"
              >
                <optgroup label="JavaScript & TypeScript (PRG-T01)">
                  <option value="PRG-T01-C01">
                    PRG-T01-C01 · JS Deep Dive (Mental Model)
                  </option>
                  <option value="PRG-T01-C04">
                    PRG-T01-C04 · Utility Toolkit (VS Code Katas)
                  </option>
                </optgroup>
                <optgroup label="Prealgebra (MTH-T01)">
                  <option value="MTH-T01-C01">MTH-T01-C01 · Whole Numbers</option>
                  <option value="MTH-T01-C02">MTH-T01-C02 · The Language of Algebra</option>
                  <option value="MTH-T01-C03">MTH-T01-C03 · Integers</option>
                  <option value="MTH-T01-C04">MTH-T01-C04 · Fractions</option>
                  <option value="MTH-T01-C05">MTH-T01-C05 · Decimals</option>
                  <option value="MTH-T01-C06">MTH-T01-C06 · Percents</option>
                  <option value="MTH-T01-C07">MTH-T01-C07 · Proportional &amp; Ratio</option>
                  <option value="MTH-T01-C08">MTH-T01-C08 · Exponents</option>
                  <option value="MTH-T01-C09">MTH-T01-C09 · Roots</option>
                  <option value="MTH-T01-C10">MTH-T01-C10 · Properties of Real Numbers</option>
                  <option value="MTH-T01-C11">MTH-T01-C11 · Solving Linear Equations</option>
                  <option value="MTH-T01-C12">MTH-T01-C12 · Math Models &amp; Geometry</option>
                  <option value="MTH-T01-C13">MTH-T01-C13 · Polynomials</option>
                  <option value="MTH-T01-C14">MTH-T01-C14 · Graphs</option>
                </optgroup>
                <optgroup label="Algebra &amp; Trigonometry (MTH-T02)">
                  <option value="MTH-T02-C01-U01">
                    MTH-T02-C01-U01 · Complex Numbers
                  </option>
                </optgroup>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1 font-medium">
                  Question Count
                </label>
                <select
                  value={cfgCount}
                  onChange={(e) => setCfgCount(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-[#1d2333] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-2 text-xs text-slate-900 dark:text-slate-200"
                >
                  <option value={5}>5 Questions</option>
                  <option value={8}>8 Questions</option>
                  <option value={10}>10 Questions</option>
                  <option value={15}>15 Questions</option>
                  <option value={20}>20 Questions</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 dark:text-slate-400 mb-1 font-medium">
                  Difficulty
                </label>
                <select
                  value={cfgDifficulty}
                  onChange={(e) => setCfgDifficulty(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-[#1d2333] border border-slate-200 dark:border-[#2c354d] rounded-lg px-2.5 py-2 text-xs text-slate-900 dark:text-slate-200"
                >
                  <option value="ALL">Mixed (L1–L4)</option>
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
              disabled={isGenerating}
              className="w-full inline-flex items-center justify-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold h-9 rounded-xl transition-colors shadow-sm"
            >
              {isGenerating ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Plus className="w-3.5 h-3.5" />
              )}
              <span>{isGenerating ? "Generating..." : "Generate Verified Set"}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
