"use client";

import React, { useMemo } from "react";
import { AnimatePresence, m } from "motion/react";
import { popover, presence } from "@/lib/motion";
import {
  CheckCircle2,
  ChevronDown,
  Clock,
  Search,
  X,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import { groupDrillsByUnit } from "@/lib/drillGrouping";
import { DrillFilter } from "@/hooks/types";

interface DrillSwitcherProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  switcherRef: React.RefObject<HTMLDivElement>;
  currentDrill: DrillDocument | null;
  drills: DrillListItem[];
  labs?: LabListItem[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
}

function StatusSummary({
  practiceStatus,
  progressText,
  inline = false,
}: {
  practiceStatus?: string;
  progressText: string;
  inline?: boolean;
}) {
  const status = practiceStatus || "Ready";
  const isGraded = status === "Graded";
  const isInProgress = status === "In Progress" || status === "Needs Retry";

  const statusTone = isGraded
    ? "text-emerald-700 dark:text-emerald-400"
    : isInProgress
    ? "text-amber-600 dark:text-amber-400"
    : "text-zinc-500 dark:text-zinc-400";

  return (
    <div
      className={
        inline
          ? "flex items-center gap-2 shrink-0"
          : "flex flex-col items-end shrink-0 gap-0.5"
      }
    >
      <span className={`inline-flex items-center gap-1 text-[11px] font-medium ${statusTone}`}>
        {isGraded ? (
          <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
        ) : (
          <Clock className="w-3 h-3" aria-hidden="true" />
        )}
        <span>{status}</span>
      </span>
      <span className="text-[11px] font-mono tabular-nums text-zinc-500 dark:text-zinc-400">
        {progressText}
      </span>
    </div>
  );
}

/** Searchable and filterable dropdown for switching between practice drills (and project labs). */
export const DrillSwitcher: React.FC<DrillSwitcherProps> = ({
  isOpen,
  onToggle,
  onClose,
  switcherRef,
  currentDrill,
  drills,
  labs = [],
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
}) => {
  const groupedEntries = useMemo(() => groupDrillsByUnit(drills), [drills]);

  const handlePick = (id: string) => {
    onSelectDrill(id);
    onClose();
  };

  return (
    <div className="relative min-w-0 flex-1 sm:flex-initial" ref={switcherRef}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-label="Switch practice drill"
        className="w-full sm:w-auto inline-flex items-center justify-between gap-2 h-9 px-3 rounded-lg bg-zinc-100/80 dark:bg-zinc-800/70 hover:bg-zinc-200/70 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-left transition-colors min-w-0"
      >
        <span className="text-xs sm:text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate max-w-[220px] sm:max-w-[300px] md:max-w-[360px]">
          {currentDrill
            ? currentDrill.unitTitle || currentDrill.unitCode
            : "Select practice drill"}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <m.div
            variants={popover}
            {...presence}
            style={{ transformOrigin: "top left" }}
            className="absolute left-0 mt-2 w-[min(calc(100vw-2rem),440px)] bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-lg p-3 z-50"
          >
            {/* Search Input */}
            <div className="flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 mb-2.5">
              <Search className="w-4 h-4 text-zinc-400 shrink-0" />
              <input
                type="text"
                value={drillSearch}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search by unit title, unit code, or drill ID..."
                aria-label="Search practice drills"
                className="w-full bg-transparent text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none"
                autoFocus
              />
              {drillSearch && (
                <button
                  type="button"
                  onClick={() => onSearchChange("")}
                  aria-label="Clear search"
                  className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5 mb-2.5 pb-2.5 border-b border-zinc-200 dark:border-zinc-800 text-xs">
              {[
                { id: "ALL", label: "All" },
                { id: "UNFINISHED", label: "Unfinished" },
                { id: "GRADED", label: "Synced" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => onFilterChange(tab.id as DrillFilter)}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                    drillFilter === tab.id
                      ? "bg-indigo-600 dark:bg-indigo-500 text-white"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Drills & Labs List */}
            <div className="max-h-80 overflow-y-auto space-y-1.5 pr-1">
              {groupedEntries.length === 0 && labs.length === 0 ? (
                <div className="py-6 text-center text-xs text-zinc-500 dark:text-zinc-400">
                  No drills match the selected filter.
                </div>
              ) : (
                <>
                  {groupedEntries.map((entry) => {
                    if (entry.kind === "single") {
                      const d = entry.drill;
                      const isSelected = d.drillId === selectedDrillId;

                      return (
                        <button
                          key={d.drillId}
                          type="button"
                          onClick={() => handlePick(d.drillId)}
                          className={`w-full text-left p-2.5 rounded-lg border transition-colors flex items-start justify-between gap-3 ${
                            isSelected
                              ? "bg-zinc-100 dark:bg-zinc-800/90 border-indigo-600 dark:border-indigo-500"
                              : "bg-zinc-50/60 dark:bg-zinc-950/50 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 border-zinc-200 dark:border-zinc-800"
                          }`}
                        >
                          <div className="min-w-0 flex-1 space-y-0.5">
                            <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                              {d.unitTitle || d.unitCode}
                            </div>
                            <div className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                              {d.unitCode} · {d.questionCount} Qs
                            </div>
                          </div>

                          <StatusSummary
                            practiceStatus={d.practiceStatus}
                            progressText={`${d.score ?? 0}/${d.maxScore ?? d.questionCount}`}
                          />
                        </button>
                      );
                    }

                    return (
                      <div
                        key={entry.key}
                        className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/40 dark:bg-zinc-950/40 p-1.5 space-y-1"
                      >
                        <div className="px-1.5 pt-1 pb-0.5 space-y-0.5">
                          <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                            {entry.unitTitle}
                          </div>
                          <div className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                            {entry.unitCode}
                          </div>
                        </div>

                        <div className="space-y-1">
                          {entry.items.map((item) => {
                            const d = item.drill;
                            const isSelected = d.drillId === selectedDrillId;

                            return (
                              <button
                                key={d.drillId}
                                type="button"
                                onClick={() => handlePick(d.drillId)}
                                className={`w-full text-left px-2.5 py-1.5 rounded-md border transition-colors flex items-center justify-between gap-3 ${
                                  isSelected
                                    ? "bg-zinc-100 dark:bg-zinc-800/90 border-indigo-600 dark:border-indigo-500"
                                    : "bg-white/80 dark:bg-zinc-900/60 hover:bg-zinc-100 dark:hover:bg-zinc-800/70 border-transparent"
                                }`}
                              >
                                <div className="min-w-0 flex items-baseline gap-1.5 truncate">
                                  <span className="text-xs font-medium text-zinc-800 dark:text-zinc-200">
                                    {item.setLabel}
                                  </span>
                                  <span className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                    · {d.questionCount} Qs
                                  </span>
                                </div>

                                <StatusSummary
                                  inline
                                  practiceStatus={d.practiceStatus}
                                  progressText={`${d.score ?? 0}/${d.maxScore ?? d.questionCount}`}
                                />
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}

                  {labs.length > 0 && (
                    <div className="pt-2 mt-1 border-t border-zinc-200 dark:border-zinc-800 space-y-1.5">
                      <div className="px-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        Labs
                      </div>
                      {labs.map((lab) => {
                        const isSelected = lab.id === selectedDrillId;

                        return (
                          <button
                            key={lab.id}
                            type="button"
                            onClick={() => handlePick(lab.id)}
                            className={`w-full text-left p-2.5 rounded-lg border transition-colors flex items-start justify-between gap-3 ${
                              isSelected
                                ? "bg-zinc-100 dark:bg-zinc-800/90 border-indigo-600 dark:border-indigo-500"
                                : "bg-zinc-50/60 dark:bg-zinc-950/50 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 border-zinc-200 dark:border-zinc-800"
                            }`}
                          >
                            <div className="min-w-0 flex-1 space-y-0.5">
                              <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                                {lab.title}
                              </div>
                              <div className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                {lab.chapterCode || lab.unitCode} · {lab.milestoneCount} Ms
                              </div>
                            </div>

                            <StatusSummary
                              practiceStatus={lab.practiceStatus}
                              progressText={`${lab.passedCount}/${lab.milestoneCount}`}
                            />
                          </button>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
};
