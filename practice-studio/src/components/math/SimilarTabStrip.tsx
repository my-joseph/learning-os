"use client";

import React, { useEffect, useRef, useState } from "react";
import { Check, Minus, Plus, X } from "lucide-react";
import {
  RealTabStatus,
  SimilarTabId,
  SimilarTabStatus,
  SimilarTabSummary,
  slotToTabId,
  tabStatusAccessibleSuffix,
} from "@/lib/similarTabs";
import { statusTone } from "@/lib/statusTone";
import { Badge } from "@/components/ui/shadcn/Badge";
import { IconButton } from "@/components/ui/shadcn/Button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/shadcn/Tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";

export interface SimilarTabStripProps {
  problemId: string;
  questionNumber: number;
  realStatus: RealTabStatus;
  tabs: readonly SimilarTabSummary[];
  selectedTab: SimilarTabId;
  locked?: boolean;
  exhausted?: boolean;
  error?: string | null;
  loading?: boolean;
  onAdd: () => void;
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

function StatusMark({ status }: { status: SimilarTabStatus | RealTabStatus }) {
  const mark = MARKS[status];
  const Icon = "icon" in mark ? mark.icon : undefined;
  return (
    <Badge variant="tabMark" data-status={status} className={mark.tone} aria-hidden="true">
      {Icon && <Icon className="size-space-2_5" strokeWidth={3} />}
    </Badge>
  );
}

export function SimilarTabStrip({
  problemId,
  questionNumber,
  realStatus,
  tabs,
  selectedTab,
  locked = false,
  exhausted = false,
  error = null,
  loading = false,
  onAdd,
  onSelectTab,
}: SimilarTabStripProps) {
  const openedTabs = locked ? [] : tabs;
  const activeTab = openedTabs.some((tab) => slotToTabId(tab.slot) === selectedTab)
    ? selectedTab
    : "q";
  const [focusedTab, setFocusedTab] = useState<SimilarTabId>(activeTab);
  const tabRefs = useRef(new Map<SimilarTabId, HTMLButtonElement>());
  const scrollRef = useRef<HTMLDivElement>(null);
  const addRef = useRef<HTMLButtonElement>(null);

  const lastSlot = openedTabs[openedTabs.length - 1]?.slot;

  useEffect(() => {
    setFocusedTab(activeTab);
    const button = tabRefs.current.get(activeTab);
    const row = scrollRef.current;
    if (!button || !row) return;
    const tabBounds = button.getBoundingClientRect();
    const rowBounds = row.getBoundingClientRect();
    const revealAdd = lastSlot !== undefined && slotToTabId(lastSlot) === activeTab;
    const right = revealAdd ? addRef.current?.getBoundingClientRect().right ?? tabBounds.right : tabBounds.right;
    if (tabBounds.left < rowBounds.left) {
      row.scrollLeft += tabBounds.left - rowBounds.left;
    } else if (right > rowBounds.right) {
      row.scrollLeft += right - rowBounds.right;
    }
  }, [activeTab, lastSlot]);

  const disabled = locked || exhausted || loading;
  const invite = !disabled && !error &&
    (realStatus === "wrong" || realStatus === "partial" || realStatus === "assisted");
  const tooltip = locked
    ? "Answer the question first"
    : loading
      ? "Loading similar questions"
      : exhausted
        ? "No more similar questions"
        : error ?? "Try a similar question";
  const descriptionId = `similar-add-${problemId}`;
  const panelId = `panel-${problemId}`;
  const entries = [
    { id: "q" as const, label: `Question ${questionNumber}`, status: realStatus },
    ...openedTabs.map((tab) => ({
      id: slotToTabId(tab.slot),
      label: `Similar ${tab.slot}`,
      status: tab.status,
    })),
  ];

  return (
    <Tabs
      ref={scrollRef}
      value={activeTab}
      activationMode="manual"
      className="flex min-w-0 items-center gap-space-1 overflow-x-auto overflow-y-hidden scrollbar-hidden border-b border-border"
      onValueChange={(value) => onSelectTab(value as SimilarTabId)}
    >
      <TabsList
        variant="similar"
        aria-label={`Question ${questionNumber} and similar questions`}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setFocusedTab(activeTab);
        }}
      >
        {entries.map(({ id, label, status }) => (
          <TabsTrigger
            key={id}
            value={id}
            ref={(element) => {
              if (element) tabRefs.current.set(id, element);
              else tabRefs.current.delete(id);
            }}
            id={`tab-${problemId}-${id}`}
            aria-controls={panelId}
            aria-label={`${label}${tabStatusAccessibleSuffix(status)}`}
            tabIndex={focusedTab === id ? 0 : -1}
            onFocus={() => setFocusedTab(id)}
          >
            <StatusMark status={status} />
            <span className="tabular-nums">{label}</span>
          </TabsTrigger>
        ))}
      </TabsList>
      <span id={descriptionId} className="sr-only" role={error ? "status" : undefined}>
        {tooltip}
      </span>
      <Tooltip>
        <TooltipTrigger asChild>
          <IconButton
            ref={addRef}
            size="sm"
            hitArea="tabAdd"
            tone="tabAdd"
            data-invite={invite || undefined}
            data-error={(!disabled && Boolean(error)) || undefined}
            aria-label="Try a similar question"
            aria-describedby={descriptionId}
            aria-disabled={disabled || undefined}
            aria-busy={loading || undefined}
            title={tooltip}
            onClick={() => {
              if (!disabled) onAdd();
            }}
          >
            <Plus className="size-space-4" aria-hidden="true" />
          </IconButton>
        </TooltipTrigger>
        <TooltipContent side="bottom">{tooltip}</TooltipContent>
      </Tooltip>
    </Tabs>
  );
}
