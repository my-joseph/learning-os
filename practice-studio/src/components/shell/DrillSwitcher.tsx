"use client";

import React from "react";
import {
  CheckCircle2,
  ChevronDown,
  Clock,
  Search,
  Sigma,
  Terminal,
  X,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import { DrillFilter } from "@/hooks/types";

interface DrillSwitcherProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  switcherRef: React.RefObject<HTMLDivElement>;
  currentDrill: DrillDocument | null;
  drills: DrillListItem[];
  selectedDrillId: string;
  drillSearch: string;
  onSearchChange: (value: string) => void;
  drillFilter: DrillFilter;
  onFilterChange: (filter: DrillFilter) => void;
  onSelectDrill: (drillId: string) => void;
}

/** Searchable and filterable dropdown for switching between practice drills. */
export const DrillSwitcher: React.FC<DrillSwitcherProps> = ({
  isOpen,
  onToggle,
  onClose,
  switcherRef,
  currentDrill,
  drills,
  selectedDrillId,
  drillSearch,
  onSearchChange,
  drillFilter,
  onFilterChange,
  onSelectDrill,
}) => {
  return (
    <div className="relative" ref={switcherRef}>
      <button
        type="button"
        onClick={onToggle}
        className="inline-flex items-center gap-3 min-h-[48px] py-2 px-3.5 rounded-xl bg-slate-100 dark:bg-[#1d2333] hover:bg-slate-200/70 dark:hover:bg-[#252e42] border border-slate-200 dark:border-[#2c354d] text-left transition-colors"
      >
        {currentDrill?.subject === "PRG" ? (
          <Terminal className="w-4 h-4 text-sky-600 dark:text-sky-400 shrink-0" />
        ) : (
          <Sigma className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
        )}
        <div className="min-w-0 space-y-0.5">
          <div className="text-xs md:text-sm font-bold leading-snug text-slate-900 dark:text-white truncate max-w-[240px] sm:max-w-[360px] md:max-w-[440px]">
            {currentDrill
              ? `${currentDrill.unitTitle || currentDrill.unitCode} (${currentDrill.unitCode})`
              : "Select Practice Drill"}
          </div>
          {currentDrill && (
            <div className="text-[11px] font-mono leading-tight text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
              <span>{currentDrill.drillId}</span>
              <span>·</span>
              <span>{currentDrill.problems.length} Qs</span>
            </div>
          )}
        </div>
        <ChevronDown className="w-4 h-4 text-slate-600 dark:text-slate-400 shrink-0 ml-0.5" />
      </button>

      {/* Searchable & Filterable Drill Popover */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-[380px] sm:w-[480px] bg-white dark:bg-[#161c2a] border border-slate-200 dark:border-[#2c354d] rounded-2xl shadow-2xl p-3.5 z-50">
          {/* Search Input */}
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-[#10141f] border border-slate-200 dark:border-[#2c354d] rounded-xl px-3 py-2 mb-3">
            <Search className="w-4 h-4 text-slate-400 shrink-0" />
            <input
              type="text"
              value={drillSearch}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search by unit title, subject code (MTH, PRG), or drill ID..."
              className="w-full bg-transparent text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none"
              autoFocus
            />
            {drillSearch && (
              <button
                type="button"
                onClick={() => onSearchChange("")}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 mb-3 pb-2.5 border-b border-slate-200 dark:border-[#252f45] text-xs">
            {[
              { id: "ALL", label: "All" },
              { id: "UNFINISHED", label: "Unfinished" },
              { id: "GRADED", label: "Synced" },
              { id: "MATH", label: "MATH" },
              { id: "PRG", label: "PRG" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => onFilterChange(tab.id as DrillFilter)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                  drillFilter === tab.id
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 dark:bg-[#1d2436] text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-[#263047]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Drills List */}
          <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
            {drills.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-600 dark:text-slate-400">
                No drills match the selected filter.
              </div>
            ) : (
              drills.map((d) => {
                const isSelected = d.drillId === selectedDrillId;
                const isGraded = d.practiceStatus === "Graded";
                const isInProgress = d.practiceStatus === "In Progress";

                return (
                  <button
                    key={d.drillId}
                    type="button"
                    onClick={() => {
                      onSelectDrill(d.drillId);
                      onClose();
                    }}
                    className={`w-full text-left p-3 rounded-xl border transition-all flex items-start justify-between gap-3 ${
                      isSelected
                        ? "bg-indigo-50 dark:bg-indigo-600/20 border-indigo-500"
                        : "bg-slate-50/70 dark:bg-[#1b2233] hover:bg-slate-100 dark:hover:bg-[#232c42] border-slate-200/80 dark:border-[#2a344d]"
                    }`}
                  >
                    <div className="min-w-0 flex-1 space-y-1">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                            d.subject === "PRG"
                              ? "bg-sky-100 dark:bg-sky-500/20 text-sky-700 dark:text-sky-300"
                              : "bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300"
                          }`}
                        >
                          {d.subject || "MATH"}
                        </span>
                        <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                          {d.unitTitle || d.unitCode}
                        </span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-600 dark:text-slate-400">
                        {d.drillId} · {d.unitCode} · {d.questionCount} Qs
                      </div>
                    </div>

                    <div className="flex flex-col items-end shrink-0 gap-1">
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                          isGraded
                            ? "bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-500/30"
                            : isInProgress
                            ? "bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-500/30"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700"
                        }`}
                      >
                        {isGraded ? (
                          <CheckCircle2 className="w-3 h-3" />
                        ) : (
                          <Clock className="w-3 h-3" />
                        )}
                        <span>{d.practiceStatus || "Ready"}</span>
                      </span>
                      <span className="text-[11px] font-mono text-slate-600 dark:text-slate-400">
                        Score: {d.score ?? 0}/{d.maxScore ?? d.questionCount}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
