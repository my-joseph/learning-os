"use client";

import React, { useEffect, useRef, useState } from "react";
import { Check, Circle, Minus, SkipForward, X } from "lucide-react";
import {
  nextTabIndexForKey,
  RealTabStatus,
  SimilarTabId,
  SimilarTabStatus,
  SimilarTabSummary,
  slotToTabId,
  tabStatusAccessibleSuffix,
} from "@/lib/similarTabs";

export interface SimilarTabStripProps {
  problemId: string;
  questionNumber: number;
  realStatus: RealTabStatus;
  tabs: readonly SimilarTabSummary[];
  selectedTab: SimilarTabId;
  onSelectTab: (tabId: SimilarTabId) => void;
}

function StatusMark({ status }: { status: SimilarTabStatus | RealTabStatus }) {
  if (status === "correct") {
    return (
      <Check
        className="w-3.5 h-3.5 shrink-0 text-emerald-700 dark:text-emerald-400"
        aria-hidden="true"
      />
    );
  }
  if (status === "wrong") {
    return (
      <X
        className="w-3.5 h-3.5 shrink-0 text-rose-600 dark:text-rose-400"
        aria-hidden="true"
      />
    );
  }
  if (status === "partial" || status === "assisted") {
    return (
      <Minus
        className="w-3.5 h-3.5 shrink-0 text-amber-700 dark:text-amber-400"
        aria-hidden="true"
      />
    );
  }
  if (status === "skipped") {
    return (
      <SkipForward
        className="w-3.5 h-3.5 shrink-0 text-zinc-400 dark:text-zinc-500"
        aria-hidden="true"
      />
    );
  }
  return (
    <Circle
      className="w-3.5 h-3.5 shrink-0 text-zinc-400 dark:text-zinc-500"
      aria-hidden="true"
    />
  );
}

/**
 * WAI-ARIA manual-activation tab strip for switching between the real question and
 * Similar 1..3 practice tabs inside a Math question card.
 */
export const SimilarTabStrip: React.FC<SimilarTabStripProps> = ({
  problemId,
  questionNumber,
  realStatus,
  tabs,
  selectedTab,
  onSelectTab,
}) => {
  const orderedIds: SimilarTabId[] = ["q", ...tabs.map((t) => slotToTabId(t.slot))];
  const [rovingTab, setRovingTab] = useState<SimilarTabId>(selectedTab);
  const tabRefs = useRef<Map<SimilarTabId, HTMLButtonElement | null>>(new Map());
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setRovingTab(selectedTab);
    const btn = tabRefs.current.get(selectedTab);
    if (btn && typeof btn.scrollIntoView === "function") {
      btn.scrollIntoView({ inline: "nearest", block: "nearest" });
    }
  }, [selectedTab]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>, currentId: SimilarTabId) => {
    const currentIndex = orderedIds.indexOf(currentId);
    if (currentIndex < 0) return;

    const nextIdx = nextTabIndexForKey(e.key, currentIndex, orderedIds.length);
    if (nextIdx !== null) {
      e.preventDefault();
      const targetId = orderedIds[nextIdx];
      setRovingTab(targetId);
      const targetEl = tabRefs.current.get(targetId);
      targetEl?.focus();
      if (targetEl && typeof targetEl.scrollIntoView === "function") {
        targetEl.scrollIntoView({ inline: "nearest", block: "nearest" });
      }
      return;
    }

    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelectTab(currentId);
    }
  };

  const handleListBlur = (e: React.FocusEvent<HTMLDivElement>) => {
    const nextTarget = e.relatedTarget as Node | null;
    if (!nextTarget || !listRef.current?.contains(nextTarget)) {
      setRovingTab(selectedTab);
    }
  };

  const panelId = `panel-${problemId}`;
  const baseTabClass =
    "inline-flex items-center justify-center gap-1.5 shrink-0 snap-start min-h-[44px] sm:min-h-0 sm:h-9 px-3 text-sm whitespace-nowrap border-b-2 -mb-px transition-colors rounded-t-md focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

  const selectedClass =
    "text-zinc-900 dark:text-zinc-100 font-semibold border-indigo-600 dark:border-indigo-400";
  const unselectedClass =
    "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 border-transparent";

  const realSelected = selectedTab === "q";
  const realAriaLabel = `Question ${questionNumber}${tabStatusAccessibleSuffix(realStatus)}`;

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={`Question ${questionNumber} and similar questions`}
      onBlur={handleListBlur}
      className="flex items-center gap-1 border-b border-zinc-200 dark:border-zinc-800 overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden snap-x -mx-4 px-4 sm:mx-0 sm:px-0"
    >
      <button
        ref={(el) => {
          tabRefs.current.set("q", el);
        }}
        type="button"
        role="tab"
        id={`tab-${problemId}-q`}
        aria-selected={realSelected}
        aria-controls={panelId}
        aria-label={realAriaLabel}
        tabIndex={rovingTab === "q" ? 0 : -1}
        onClick={() => onSelectTab("q")}
        onKeyDown={(e) => handleKeyDown(e, "q")}
        className={`${baseTabClass} ${realSelected ? selectedClass : unselectedClass}`}
      >
        <StatusMark status={realStatus} />
        <span className="hidden sm:inline">
          Question <span className="font-display tabular-nums">{questionNumber}</span>
        </span>
        <span className="sm:hidden font-display tabular-nums">Q{questionNumber}</span>
      </button>

      {tabs.length > 0 && (
        <span
          aria-hidden="true"
          className="sm:hidden shrink-0 pl-1 pr-0.5 text-xs text-zinc-500 dark:text-zinc-400 select-none"
        >
          Similar
        </span>
      )}

      {tabs.map((tab) => {
        const tabId = slotToTabId(tab.slot);
        const isSelected = selectedTab === tabId;
        const tabAriaLabel = `Similar question ${tab.slot}${tabStatusAccessibleSuffix(tab.status)}`;
        return (
          <button
            key={tab.token}
            ref={(el) => {
              tabRefs.current.set(tabId, el);
            }}
            type="button"
            role="tab"
            id={`tab-${problemId}-${tabId}`}
            aria-selected={isSelected}
            aria-controls={panelId}
            aria-label={tabAriaLabel}
            tabIndex={rovingTab === tabId ? 0 : -1}
            onClick={() => onSelectTab(tabId)}
            onKeyDown={(e) => handleKeyDown(e, tabId)}
            className={`${baseTabClass} ${isSelected ? selectedClass : unselectedClass}`}
          >
            <StatusMark status={tab.status} />
            <span className="hidden sm:inline">
              Similar <span className="font-display tabular-nums">{tab.slot}</span>
            </span>
            <span className="sm:hidden font-display tabular-nums">{tab.slot}</span>
          </button>
        );
      })}
    </div>
  );
};
