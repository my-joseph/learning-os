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
import { Badge } from "@/components/ui/shadcn/Badge";
import { Button } from "@/components/ui/shadcn/Button";
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

const MARKS = {
  correct: { tone: statusTone.correct.tabMark, icon: Check },
  wrong: { tone: statusTone.wrong.tabMark, icon: X },
  assisted: { tone: statusTone.assisted.tabMark, icon: Check },
  partial: { tone: statusTone.assisted.tabMark, icon: Minus },
  skipped: { tone: statusTone.skipped.tabMark },
  usedHelp: { tone: statusTone.notTried.tabMark },
  untried: { tone: statusTone.notTried.tabMark },
};

function StatusMark({
  status,
  muted = false,
}: {
  status: SimilarTabStatus | RealTabStatus;
  muted?: boolean;
}) {
  const mark = MARKS[status];
  const Icon = "icon" in mark ? mark.icon : undefined;
  return (
    <Badge
      variant="tabMark"
      data-status={status}
      className={muted ? MUTED_UNTRIED_TAB_MARK : mark.tone}
      aria-hidden="true"
    >
      {Icon && <Icon className="size-space-2_5" strokeWidth={3} />}
    </Badge>
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

  const realAriaLabel = `Question ${questionNumber}${tabStatusAccessibleSuffix(realStatus)}`;
  const hasSimilarSlots = locked ? lockedSlots.length > 0 : tabs.length > 0;
  const showListError = !locked && tabs.length === 0 && Boolean(listError);
  const showListLoading = !locked && tabs.length === 0 && !listError && loadingList;

  return (
    <div className="flex items-center justify-between gap-space-2 border-b border-border -mx-space-4 px-space-4 sm:mx-0 sm:px-0">
      <Tabs
        value={effectiveSelected}
        activationMode="manual"
        onValueChange={(value) => onSelectTab(value as SimilarTabId)}
      >
        <TabsList
          ref={listRef}
          variant="similar"
          aria-label={`Question ${questionNumber} and similar questions`}
          onBlur={handleListBlur}
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
          >
            <StatusMark status={realStatus} />
            <span className="hidden sm:inline">
              Question <span className="font-sans tabular-nums">{questionNumber}</span>
            </span>
            <span className="sm:hidden font-sans tabular-nums">Q{questionNumber}</span>
          </TabsTrigger>

          {hasSimilarSlots && (
            <span
              aria-hidden="true"
              className={`sm:hidden shrink-0 pl-space-1 pr-space-0_5 text-xs select-none ${
                locked
                  ? "text-foreground-faint dark:text-surface-hover-strong opacity-secondary"
                  : "text-muted"
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
                  >
                    <StatusMark status="untried" muted />
                    <span className="hidden sm:inline">
                      Similar <span className="font-sans tabular-nums">{slot}</span>
                    </span>
                    <span className="sm:hidden font-sans tabular-nums">{slot}</span>
                  </TabsTrigger>
                );
              })
            : tabs.map((tab) => {
                const tabId = slotToTabId(tab.slot);
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
                  >
                    <StatusMark status={tab.status} />
                    <span className="hidden sm:inline">
                      Similar <span className="font-sans tabular-nums">{tab.slot}</span>
                    </span>
                    <span className="sm:hidden font-sans tabular-nums">{tab.slot}</span>
                  </TabsTrigger>
                );
              })}
        </TabsList>
      </Tabs>

      {showListError && (
        <div
          role="status"
          data-similar-list-error="true"
          className="flex items-center gap-space-2 shrink-0 py-space-1 text-xs text-muted"
        >
          <span className="truncate">{listError}</span>
          {onRetryList && (
            <Button
              variant="assistRetry"
              size="assistRetry"
              onClick={onRetryList}
              disabled={loadingList}
            >
              <RefreshCw
                className={`size-space-3 ${loadingList ? "animate-spin" : ""}`}
                aria-hidden="true"
              />
              <span>{loadingList ? "Retrying..." : "Retry"}</span>
            </Button>
          )}
        </div>
      )}

      {showListLoading && (
        <span
          role="status"
          className="shrink-0 py-space-1 text-xs text-foreground-faint"
        >
          Loading similar...
        </span>
      )}
    </div>
  );
};
