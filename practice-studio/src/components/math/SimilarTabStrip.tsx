"use client";

import React, { useEffect, useRef, useState } from "react";
import { Check, Minus, RefreshCw, X } from "lucide-react";
import {
  buildLockedSimilarPlaceholders,
  RealTabStatus,
  SimilarTabId,
  SimilarTabStatus,
  SimilarTabSummary,
  slotToTabId,
  tabStatusAccessibleSuffix,
} from "@/lib/similarTabs";
import { MUTED_UNTRIED_TAB_MARK, statusTone } from "@/lib/statusTone";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/shadcn/Tabs";

export interface SimilarTabStripProps {
  problemId: string;
  questionNumber: number;
  realStatus: RealTabStatus;
  tabs: readonly SimilarTabSummary[];
  selectedTab: SimilarTabId;
  locked?: boolean;
  lockedSlotCount?: number;
  listError?: string | null;
  loadingList?: boolean;
  onRetryList?: () => void;
  onSelectTab: (tabId: SimilarTabId) => void;
}

/**
 * Shared tab status circle matching the Pagination Stepper colour language:
 * - not tried / usedHelp (unanswered): plain outlined circle (no colour)
 * - skipped: dashed outlined circle
 * - correct: filled green circle with ✓
 * - assisted (used help + correct) / partial: green outline circle (no fill) with ✓ or –
 * - wrong: filled rose circle with ✗
 */
function StatusMark({
  status,
  muted = false,
}: {
  status: SimilarTabStatus | RealTabStatus;
  muted?: boolean;
}) {
  if (status === "correct") {
    return (
      <span
        data-status="correct"
        className={`w-4 h-4 rounded-full ${statusTone.correct.tabMark} inline-flex items-center justify-center shrink-0`}
        aria-hidden="true"
      >
        <Check className="w-2.5 h-2.5" strokeWidth={3} />
      </span>
    );
  }
  if (status === "wrong") {
    return (
      <span
        data-status="wrong"
        className={`w-4 h-4 rounded-full ${statusTone.wrong.tabMark} inline-flex items-center justify-center shrink-0`}
        aria-hidden="true"
      >
        <X className="w-2.5 h-2.5" strokeWidth={3} />
      </span>
    );
  }
  if (status === "assisted") {
    return (
      <span
        data-status="assisted"
        className={`w-4 h-4 rounded-full ${statusTone.assisted.tabMark} inline-flex items-center justify-center shrink-0`}
        aria-hidden="true"
      >
        <Check className="w-2.5 h-2.5" strokeWidth={3} />
      </span>
    );
  }
  if (status === "partial") {
    return (
      <span
        data-status="partial"
        className={`w-4 h-4 rounded-full ${statusTone.assisted.tabMark} inline-flex items-center justify-center shrink-0`}
        aria-hidden="true"
      >
        <Minus className="w-2.5 h-2.5" strokeWidth={3} />
      </span>
    );
  }
  if (status === "skipped") {
    return (
      <span
        data-status="skipped"
        className={`w-4 h-4 rounded-full ${statusTone.skipped.tabMark} inline-block shrink-0`}
        aria-hidden="true"
      />
    );
  }
  if (status === "usedHelp") {
    return (
      <span
        data-status="usedHelp"
        className={`w-4 h-4 rounded-full ${statusTone.notTried.tabMark} inline-block shrink-0`}
        aria-hidden="true"
      />
    );
  }
  return (
    <span
      data-status="untried"
      className={`w-4 h-4 rounded-full inline-block shrink-0 ${
        muted ? MUTED_UNTRIED_TAB_MARK : statusTone.notTried.tabMark
      }`}
      aria-hidden="true"
    />
  );
}

/**
 * WAI-ARIA manual-activation tab strip for switching between the real question and
 * Similar 1..3 practice tabs inside a Math question card.
 * Shown by default including before the first attempt; similar tabs render as locked
 * ghost tabs (`aria-disabled="true"`) until the real question is attempted in the cycle.
 */
export const SimilarTabStrip: React.FC<SimilarTabStripProps> = ({
  problemId,
  questionNumber,
  realStatus,
  tabs,
  selectedTab,
  locked = false,
  lockedSlotCount,
  listError = null,
  loadingList = false,
  onRetryList,
  onSelectTab,
}) => {
  const lockedSlots = locked ? buildLockedSimilarPlaceholders(lockedSlotCount) : [];
  const effectiveSelected: SimilarTabId =
    locked || tabs.length === 0 ? "q" : selectedTab;

  const [focusedTab, setFocusedTab] = useState<SimilarTabId>(effectiveSelected);
  const tabRefs = useRef<Map<SimilarTabId, HTMLButtonElement | null>>(new Map());
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setFocusedTab(effectiveSelected);
    const btn = tabRefs.current.get(effectiveSelected);
    if (btn && typeof btn.scrollIntoView === "function") {
      btn.scrollIntoView({ inline: "nearest", block: "nearest" });
    }
  }, [effectiveSelected]);

  const handleListBlur = (event: React.FocusEvent<HTMLDivElement>) => {
    const nextTarget = event.relatedTarget as Node | null;
    if (!nextTarget || !listRef.current?.contains(nextTarget)) {
      setFocusedTab(effectiveSelected);
    }
  };

  const panelId = `panel-${problemId}`;
  const lockDescId = `similar-lock-desc-${problemId}`;
  const lockTooltip = `Answer Question ${questionNumber} first`;

  const baseTabClass =
    "inline-flex items-center justify-center gap-1.5 shrink-0 snap-start min-h-[44px] sm:min-h-0 sm:h-9 px-3 text-sm whitespace-nowrap border-b-2 -mb-px transition-colors rounded-none focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

  const selectedClass =
    "text-zinc-900 dark:text-zinc-100 font-semibold border-indigo-600 dark:border-indigo-400";
  const unselectedClass =
    "text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 border-transparent";
  const ghostClass =
    "text-zinc-400 dark:text-zinc-500 border-transparent cursor-not-allowed opacity-70 select-none";

  const realSelected = effectiveSelected === "q";
  const realAriaLabel = `Question ${questionNumber}${tabStatusAccessibleSuffix(realStatus)}`;
  const hasSimilarSlots = locked ? lockedSlots.length > 0 : tabs.length > 0;
  const showListError = !locked && tabs.length === 0 && Boolean(listError);
  const showListLoading = !locked && tabs.length === 0 && !listError && loadingList;

  return (
    <div className="flex items-center justify-between gap-2 border-b border-zinc-200 dark:border-zinc-800 -mx-4 px-4 sm:mx-0 sm:px-0">
      <Tabs
        value={effectiveSelected}
        activationMode="manual"
        onValueChange={(value) => onSelectTab(value as SimilarTabId)}
      >
        <TabsList
          ref={listRef}
          variant="underline"
          aria-label={`Question ${questionNumber} and similar questions`}
          onBlur={handleListBlur}
          className="flex h-auto min-h-0 items-center gap-1 min-w-0 overflow-x-auto overflow-y-hidden rounded-none bg-transparent p-0 dark:bg-transparent [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden snap-x -mb-px"
        >
          {locked && hasSimilarSlots && (
            <span id={lockDescId} className="sr-only">
              {lockTooltip}
            </span>
          )}

          <TabsTrigger
            value="q"
            ref={(el) => { tabRefs.current.set("q", el); }}
            id={`tab-${problemId}-q`}
            aria-controls={panelId}
            aria-label={realAriaLabel}
            tabIndex={focusedTab === "q" ? 0 : -1}
            onFocus={() => setFocusedTab("q")}
            className={`${baseTabClass} min-h-[44px] sm:min-h-0 bg-transparent shadow-none data-[state=active]:bg-transparent data-[state=active]:shadow-none ${realSelected ? selectedClass : unselectedClass}`}
          >
            <StatusMark status={realStatus} />
            <span className="hidden sm:inline">
              Question <span className="font-display tabular-nums">{questionNumber}</span>
            </span>
            <span className="sm:hidden font-display tabular-nums">Q{questionNumber}</span>
          </TabsTrigger>

          {hasSimilarSlots && (
            <span
              aria-hidden="true"
              className={`sm:hidden shrink-0 pl-1 pr-0.5 text-xs select-none ${
                locked
                  ? "text-zinc-400 dark:text-zinc-600 opacity-60"
                  : "text-zinc-500 dark:text-zinc-400"
              }`}
            >
              Similar
            </span>
          )}

          {locked
            ? lockedSlots.map((slot) => {
                const tabId = slotToTabId(slot);
                return (
                  <TabsTrigger
                    key={`locked-${tabId}`}
                    value={tabId}
                    disabled
                    type="button"
                    id={`tab-${problemId}-${tabId}`}
                    aria-disabled="true"
                    aria-controls={panelId}
                    aria-label={`Similar question ${slot}`}
                    aria-describedby={lockDescId}
                    title={lockTooltip}
                    className={`${baseTabClass} min-h-[44px] sm:min-h-0 bg-transparent shadow-none data-[state=active]:bg-transparent data-[state=active]:shadow-none ${ghostClass}`}
                  >
                    <StatusMark status="untried" muted />
                    <span className="hidden sm:inline">
                      Similar <span className="font-display tabular-nums">{slot}</span>
                    </span>
                    <span className="sm:hidden font-display tabular-nums">{slot}</span>
                  </TabsTrigger>
                );
              })
            : tabs.map((tab) => {
                const tabId = slotToTabId(tab.slot);
                const isSelected = effectiveSelected === tabId;
                const tabAriaLabel = `Similar question ${tab.slot}${tabStatusAccessibleSuffix(
                  tab.status
                )}`;
                return (
                  <TabsTrigger
                    key={tab.token}
                    value={tabId}
                    ref={(el) => {
                      tabRefs.current.set(tabId, el);
                    }}
                    id={`tab-${problemId}-${tabId}`}
                    aria-controls={panelId}
                    aria-label={tabAriaLabel}
                    tabIndex={focusedTab === tabId ? 0 : -1}
                    onFocus={() => setFocusedTab(tabId)}
                    className={`${baseTabClass} min-h-[44px] sm:min-h-0 bg-transparent shadow-none data-[state=active]:bg-transparent data-[state=active]:shadow-none ${isSelected ? selectedClass : unselectedClass}`}
                  >
                    <StatusMark status={tab.status} />
                    <span className="hidden sm:inline">
                      Similar <span className="font-display tabular-nums">{tab.slot}</span>
                    </span>
                    <span className="sm:hidden font-display tabular-nums">{tab.slot}</span>
                  </TabsTrigger>
                );
              })}
        </TabsList>
      </Tabs>

      {showListError && (
        <div
          role="status"
          data-similar-list-error="true"
          className="flex items-center gap-2 shrink-0 py-1 text-xs text-zinc-500 dark:text-zinc-400"
        >
          <span className="truncate">{listError}</span>
          {onRetryList && (
            <button
              type="button"
              onClick={onRetryList}
              disabled={loadingList}
              className="inline-flex items-center gap-1 shrink-0 min-h-[32px] sm:min-h-0 px-1.5 py-0.5 rounded font-medium text-indigo-600 dark:text-indigo-400 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 disabled:opacity-50"
            >
              <RefreshCw
                className={`w-3 h-3 ${loadingList ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              <span>{loadingList ? "Retrying..." : "Retry"}</span>
            </button>
          )}
        </div>
      )}

      {showListLoading && (
        <span
          role="status"
          className="shrink-0 py-1 text-xs text-zinc-400 dark:text-zinc-500"
        >
          Loading similar...
        </span>
      )}
    </div>
  );
};
