"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import { popover, presence, settle } from "@/lib/motion";
import { Reveal } from "@/components/motion/Reveal";
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Search,
  X,
} from "lucide-react";
import { DrillDocument, DrillListItem } from "@/types/drill";
import type { LabListItem } from "@/lib/labModel";
import {
  buildNavigableRows,
  buildPickerSections,
  clampKeyboardIndex,
  filterPickerItems,
  normalizeDrillPickerItems,
  normalizeLabPickerItems,
  stepKeyboardIndex,
  type PickerItem,
} from "@/lib/drillGrouping";
import { readRecentDrillIds } from "@/lib/lastDrillStorage";
import { isLabId, subjectOf, type Workspace } from "@/lib/routes";
import { DrillFilter } from "@/hooks/types";

type PickerTab = "drills" | "labs";

interface DrillSwitcherProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  switcherRef: React.RefObject<HTMLDivElement>;
  workspace?: Workspace;
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

function PickerItemRow({
  item,
  isSelected,
  isKeyboardActive,
  isPinnedCurrent = false,
  showSetInTitle = false,
  buttonRef,
  onPick,
}: {
  item: PickerItem;
  isSelected: boolean;
  isKeyboardActive: boolean;
  isPinnedCurrent?: boolean;
  showSetInTitle?: boolean;
  buttonRef?: (el: HTMLButtonElement | null) => void;
  onPick: (id: string) => void;
}) {
  const titleText =
    showSetInTitle && item.setLabel ? `${item.title} · ${item.setLabel}` : item.title;

  return (
    <button
      ref={buttonRef}
      type="button"
      onClick={() => onPick(item.id)}
      aria-current={isSelected ? "true" : undefined}
      className={`w-full text-left p-2.5 rounded-lg border transition-colors flex items-start justify-between gap-3 ${
        isPinnedCurrent && isSelected
          ? "bg-indigo-50/60 dark:bg-indigo-950/30 border-indigo-600 dark:border-indigo-500"
          : isSelected
          ? "bg-zinc-100 dark:bg-zinc-800/90 border-indigo-600 dark:border-indigo-500"
          : "bg-zinc-50/60 dark:bg-zinc-950/50 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 border-zinc-200 dark:border-zinc-800"
      } ${
        isKeyboardActive
          ? "ring-2 ring-indigo-500/70 dark:ring-indigo-400/70 bg-zinc-100/90 dark:bg-zinc-800/80"
          : ""
      }`}
    >
      <div className="min-w-0 flex-1 space-y-0.5">
        <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
          {titleText}
        </div>
        <div className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
          {item.unitCode} · {item.countLabel}
        </div>
      </div>

      <StatusSummary
        practiceStatus={item.practiceStatus}
        progressText={`${item.score}/${item.maxScore}`}
      />
    </button>
  );
}

/** Searchable, keyboard-navigable, Topic->Chapter grouped dropdown for drills and labs. */
export const DrillSwitcher: React.FC<DrillSwitcherProps> = ({
  isOpen,
  onToggle,
  onClose,
  switcherRef,
  workspace,
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
  const isCodeWorkspace =
    workspace === "code" ||
    (workspace === undefined && (labs.length > 0 || subjectOf(selectedDrillId) === "code"));

  const defaultTab: PickerTab =
    isCodeWorkspace && isLabId(selectedDrillId) ? "labs" : "drills";

  const [activeTab, setActiveTab] = useState<PickerTab>(defaultTab);
  const [recentIds, setRecentIds] = useState<string[]>([]);
  const [activeKeyboardIndex, setActiveKeyboardIndex] = useState<number>(-1);

  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const currentItemRef = useRef<HTMLButtonElement | null>(null);
  const rowRefs = useRef<Map<number, HTMLButtonElement | null>>(new Map());
  const wasOpenRef = useRef(isOpen);

  const drillItems = useMemo(() => normalizeDrillPickerItems(drills), [drills]);
  const labItems = useMemo(() => normalizeLabPickerItems(labs), [labs]);

  const activeItems = useMemo(
    () => (isCodeWorkspace && activeTab === "labs" ? labItems : drillItems),
    [isCodeWorkspace, activeTab, labItems, drillItems]
  );

  const otherTabMatchCount = useMemo(() => {
    if (!isCodeWorkspace || !drillSearch.trim()) return 0;
    const otherItems = activeTab === "labs" ? drillItems : labItems;
    return filterPickerItems(otherItems, drillSearch, drillFilter).length;
  }, [isCodeWorkspace, activeTab, drillItems, labItems, drillSearch, drillFilter]);

  const sections = useMemo(
    () =>
      buildPickerSections({
        items: activeItems,
        currentId: selectedDrillId,
        recentIds,
        search: drillSearch,
        filter: drillFilter,
      }),
    [activeItems, selectedDrillId, recentIds, drillSearch, drillFilter]
  );

  const [expandedTopics, setExpandedTopics] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedTopics)
  );
  const [expandedChapters, setExpandedChapters] = useState<Set<string>>(
    () => new Set(sections.defaultExpandedChapters)
  );

  // Sync tab, recent storage, expanded state, focus, and scroll when opening or switching drills.
  useEffect(() => {
    const justOpened = isOpen && !wasOpenRef.current;
    wasOpenRef.current = isOpen;

    if (!isOpen) return;

    const ws: Workspace = isCodeWorkspace ? "code" : "math";
    setRecentIds(readRecentDrillIds(ws));

    if (justOpened) {
      const nextTab: PickerTab =
        isCodeWorkspace && isLabId(selectedDrillId) ? "labs" : "drills";
      setActiveTab(nextTab);
      setActiveKeyboardIndex(drillSearch.trim() ? 0 : -1);
    }
  }, [isOpen, isCodeWorkspace, selectedDrillId, drillSearch]);

  // Reset expanded groups when picker opens, active tab changes, or selected drill changes.
  useEffect(() => {
    if (!isOpen) return;
    setExpandedTopics(new Set(sections.defaultExpandedTopics));
    setExpandedChapters(new Set(sections.defaultExpandedChapters));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, activeTab, selectedDrillId]);

  // Autofocus search and scroll current item into view when opened.
  useEffect(() => {
    if (!isOpen) return;
    const rafId = window.requestAnimationFrame(() => {
      searchInputRef.current?.focus();
      if (scrollContainerRef.current) {
        scrollContainerRef.current.scrollTop = 0;
      }
      currentItemRef.current?.scrollIntoView({ block: "nearest" });
    });
    return () => window.cancelAnimationFrame(rafId);
  }, [isOpen]);

  // Close on Escape even if focus moved outside the search input.
  useEffect(() => {
    if (!isOpen) return;
    const handleWindowKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
        triggerRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleWindowKeyDown);
    return () => window.removeEventListener("keydown", handleWindowKeyDown);
  }, [isOpen, onClose]);

  const navigableRows = useMemo(
    () => buildNavigableRows(sections, expandedTopics, expandedChapters),
    [sections, expandedTopics, expandedChapters]
  );

  const navIndexByKey = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of navigableRows) {
      map.set(`${row.section}:${row.id}`, row.navIndex);
    }
    return map;
  }, [navigableRows]);

  // Keep keyboard highlight clamped or auto-selected on first result while searching.
  useEffect(() => {
    setActiveKeyboardIndex((prev) =>
      clampKeyboardIndex(prev, navigableRows.length, sections.isSearching)
    );
  }, [navigableRows.length, sections.isSearching, drillSearch, activeTab, drillFilter]);

  // Scroll the keyboard-highlighted row into view as the user arrows through results.
  useEffect(() => {
    if (!isOpen || activeKeyboardIndex < 0) return;
    const el = rowRefs.current.get(activeKeyboardIndex);
    el?.scrollIntoView({ block: "nearest" });
  }, [isOpen, activeKeyboardIndex]);

  const handlePick = (id: string) => {
    if (drillSearch) {
      onSearchChange("");
    }
    onSelectDrill(id);
    onClose();
  };

  const toggleTopic = (topicCode: string) => {
    setExpandedTopics((prev) => {
      const next = new Set(prev);
      if (next.has(topicCode)) {
        next.delete(topicCode);
      } else {
        next.add(topicCode);
      }
      return next;
    });
  };

  const toggleChapter = (chapterCode: string) => {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(chapterCode)) {
        next.delete(chapterCode);
      } else {
        next.add(chapterCode);
      }
      return next;
    });
  };

  const handlePopoverKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveKeyboardIndex((prev) =>
        stepKeyboardIndex(prev, navigableRows.length, "down")
      );
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveKeyboardIndex((prev) =>
        stepKeyboardIndex(prev, navigableRows.length, "up")
      );
      return;
    }
    if (e.key === "Enter") {
      const target = e.target as HTMLElement | null;
      if (target && target.tagName === "BUTTON" && target !== searchInputRef.current) {
        return;
      }
      if (navigableRows.length === 0) return;
      const pickedRow =
        activeKeyboardIndex >= 0
          ? navigableRows[activeKeyboardIndex]
          : sections.isSearching
          ? navigableRows[0]
          : undefined;
      if (pickedRow) {
        e.preventDefault();
        handlePick(pickedRow.id);
      }
      return;
    }
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
      triggerRef.current?.focus();
    }
  };

  const registerRowRef = (navIndex: number | undefined, el: HTMLButtonElement | null) => {
    if (navIndex === undefined) return;
    if (el) {
      rowRefs.current.set(navIndex, el);
    } else {
      rowRefs.current.delete(navIndex);
    }
  };

  const showTreeHeading =
    !sections.isSearching &&
    (Boolean(sections.currentItem) || sections.continueItems.length > 0);

  return (
    <div className="relative min-w-0 flex-1 sm:flex-initial" ref={switcherRef}>
      <button
        ref={triggerRef}
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
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
            role="dialog"
            aria-label="Practice drill picker"
            onKeyDown={handlePopoverKeyDown}
            className="absolute left-0 mt-2 w-[min(calc(100vw-3rem),460px)] max-h-[70vh] flex flex-col overflow-hidden bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-lg p-3 z-50"
          >
            {/* Top Search Input */}
            <div className="shrink-0 flex items-center gap-2 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg px-3 py-2 mb-2">
              <Search className="w-4 h-4 text-zinc-400 shrink-0" />
              <input
                ref={searchInputRef}
                type="text"
                value={drillSearch}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder={
                  isCodeWorkspace
                    ? "Search drills, labs, chapters, or IDs..."
                    : "Search units, chapters, or drill IDs..."
                }
                aria-label="Search practice drills"
                className="w-full bg-transparent text-xs text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none"
                autoFocus
              />
              {drillSearch && (
                <button
                  type="button"
                  onClick={() => {
                    onSearchChange("");
                    searchInputRef.current?.focus();
                  }}
                  aria-label="Clear search"
                  className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Segmented Tabs (Programming only) & Quiet Status Filter */}
            <div className="shrink-0 flex flex-wrap items-center justify-between gap-2 pb-2.5 mb-2 border-b border-zinc-200 dark:border-zinc-800">
              {isCodeWorkspace ? (
                <div
                  role="tablist"
                  aria-label="Practice type"
                  className="relative grid grid-cols-2 items-center rounded-lg bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-800 p-0.5"
                >
                  <m.span
                    aria-hidden
                    className="absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-white dark:bg-zinc-900 shadow-sm"
                    initial={false}
                    animate={{ x: activeTab === "labs" ? "100%" : "0%" }}
                    transition={settle}
                  />
                  {[
                    { id: "drills" as const, label: "Drills", count: drills.length },
                    { id: "labs" as const, label: "Labs", count: labs.length },
                  ].map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        type="button"
                        role="tab"
                        aria-selected={isActive}
                        onClick={() => {
                          setActiveTab(tab.id);
                          setActiveKeyboardIndex(-1);
                        }}
                        className={`relative z-10 inline-flex items-center justify-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
                          isActive
                            ? "text-zinc-900 dark:text-zinc-100"
                            : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
                        }`}
                      >
                        <span>{tab.label}</span>
                        <span className="text-[11px] font-mono tabular-nums text-zinc-400 dark:text-zinc-500">
                          {tab.count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <span className="text-[11px] font-mono tabular-nums text-zinc-500 dark:text-zinc-400 px-1">
                  {sections.totalVisibleCount}{" "}
                  {sections.totalVisibleCount === 1 ? "drill" : "drills"}
                </span>
              )}

              {/* Quiet Status Filter */}
              <div
                role="group"
                aria-label="Filter by status"
                className="inline-flex items-center gap-0.5 rounded-lg p-0.5 bg-zinc-100/70 dark:bg-zinc-800/50"
              >
                {[
                  { id: "ALL" as const, label: "All" },
                  { id: "UNFINISHED" as const, label: "Unfinished" },
                  { id: "GRADED" as const, label: "Graded" },
                ].map((tab) => {
                  const isActive = drillFilter === tab.id;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      aria-pressed={isActive}
                      onClick={() => onFilterChange(tab.id)}
                      className={`px-2 py-0.5 rounded-md text-[11px] transition-colors ${
                        isActive
                          ? "bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 font-medium shadow-sm"
                          : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200"
                      }`}
                    >
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Scrollable Picker Body */}
            <div
              ref={scrollContainerRef}
              className="flex-1 min-h-0 overflow-y-auto overscroll-contain pr-1.5 space-y-3"
            >
              {sections.topicGroups.length === 0 ? (
                <div className="py-8 text-center space-y-2">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {isCodeWorkspace && activeTab === "labs"
                      ? "No labs match the current search or filter."
                      : "No drills match the current search or filter."}
                  </p>
                  {otherTabMatchCount > 0 && (
                    <button
                      type="button"
                      onClick={() =>
                        setActiveTab(activeTab === "labs" ? "drills" : "labs")
                      }
                      className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      Show {otherTabMatchCount} matching{" "}
                      {activeTab === "labs"
                        ? otherTabMatchCount === 1
                          ? "drill"
                          : "drills"
                        : otherTabMatchCount === 1
                        ? "lab"
                        : "labs"}
                    </button>
                  )}
                </div>
              ) : (
                <>
                  {/* 1. Current Section (pinned first) */}
                  {sections.currentItem && (
                    <section aria-label="Current" className="space-y-1.5">
                      <div className="px-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        Current
                      </div>
                      <PickerItemRow
                        item={sections.currentItem}
                        isSelected={true}
                        isPinnedCurrent={true}
                        showSetInTitle={true}
                        isKeyboardActive={
                          navIndexByKey.get(`current:${sections.currentItem.id}`) ===
                          activeKeyboardIndex
                        }
                        buttonRef={(el) => {
                          currentItemRef.current = el;
                          registerRowRef(
                            navIndexByKey.get(`current:${sections.currentItem!.id}`),
                            el
                          );
                        }}
                        onPick={handlePick}
                      />
                    </section>
                  )}

                  {/* 2. Continue Section (up to 3 recent / unfinished) */}
                  {sections.continueItems.length > 0 && (
                    <section aria-label="Continue" className="space-y-1.5">
                      <div className="px-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        Continue
                      </div>
                      <div className="space-y-1.5">
                        {sections.continueItems.map((item) => {
                          const navIdx = navIndexByKey.get(`continue:${item.id}`);
                          return (
                            <PickerItemRow
                              key={`continue:${item.id}`}
                              item={item}
                              isSelected={item.id === selectedDrillId}
                              showSetInTitle={true}
                              isKeyboardActive={navIdx === activeKeyboardIndex}
                              buttonRef={(el) => registerRowRef(navIdx, el)}
                              onPick={handlePick}
                            />
                          );
                        })}
                      </div>
                    </section>
                  )}

                  {/* 3. Full List Grouped by Topic -> Chapter */}
                  <section aria-label="Curriculum" className="space-y-1.5">
                    {showTreeHeading && (
                      <div className="px-1 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        {isCodeWorkspace && activeTab === "labs" ? "All labs" : "All drills"}
                      </div>
                    )}

                    <div className="space-y-1.5">
                      {sections.topicGroups.map((topic) => {
                        const isTopicExpanded =
                          sections.isSearching || expandedTopics.has(topic.topicCode);
                        const showTopicCode = topic.topicTitle !== topic.topicCode;

                        return (
                          <div
                            key={topic.topicCode}
                            className="rounded-lg border border-zinc-200/80 dark:border-zinc-800/90 bg-zinc-50/40 dark:bg-zinc-950/30 p-1.5"
                          >
                            <button
                              type="button"
                              aria-expanded={isTopicExpanded}
                              onClick={() => toggleTopic(topic.topicCode)}
                              className="w-full flex items-center justify-between gap-2 px-1.5 py-1 rounded-md hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60 text-left transition-colors"
                            >
                              <span className="flex items-center gap-1.5 min-w-0">
                                <ChevronRight
                                  className={`w-3.5 h-3.5 text-zinc-400 shrink-0 transition-transform duration-150 ${
                                    isTopicExpanded ? "rotate-90" : ""
                                  }`}
                                  aria-hidden="true"
                                />
                                <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                                  {topic.topicTitle}
                                </span>
                              </span>

                              <span className="flex items-center gap-1.5 shrink-0">
                                {showTopicCode && (
                                  <span className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                    {topic.topicCode}
                                  </span>
                                )}
                                <span className="text-[11px] font-mono tabular-nums text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
                                  {topic.itemCount}
                                </span>
                              </span>
                            </button>

                            <Reveal show={isTopicExpanded}>
                              <div className="pl-2 ml-2 mt-1 border-l border-zinc-200 dark:border-zinc-800 space-y-1">
                                {topic.chapters.map((chapter) => {
                                  const isChapterExpanded =
                                    sections.isSearching ||
                                    expandedChapters.has(chapter.chapterCode);
                                  const showChapterCode =
                                    chapter.chapterTitle !== chapter.chapterCode;

                                  return (
                                    <div key={chapter.chapterCode} className="space-y-1">
                                      <button
                                        type="button"
                                        aria-expanded={isChapterExpanded}
                                        onClick={() => toggleChapter(chapter.chapterCode)}
                                        className="w-full flex items-center justify-between gap-2 px-1.5 py-1 rounded-md hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60 text-left transition-colors"
                                      >
                                        <span className="flex items-center gap-1.5 min-w-0">
                                          <ChevronRight
                                            className={`w-3.5 h-3.5 text-zinc-400 shrink-0 transition-transform duration-150 ${
                                              isChapterExpanded ? "rotate-90" : ""
                                            }`}
                                            aria-hidden="true"
                                          />
                                          <span className="text-xs font-medium text-zinc-800 dark:text-zinc-200 truncate">
                                            {chapter.chapterTitle}
                                          </span>
                                        </span>

                                        <span className="flex items-center gap-1.5 shrink-0">
                                          {showChapterCode && (
                                            <span className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                              {chapter.chapterCode}
                                            </span>
                                          )}
                                          <span className="text-[11px] font-mono tabular-nums text-zinc-500 dark:text-zinc-400 bg-zinc-100/80 dark:bg-zinc-800/70 px-1.5 py-0.5 rounded">
                                            {chapter.itemCount}
                                          </span>
                                        </span>
                                      </button>

                                      <Reveal show={isChapterExpanded}>
                                        <div className="pl-2 ml-2 border-l border-zinc-200/80 dark:border-zinc-800/80 space-y-1 py-0.5">
                                          {chapter.entries.map((entry) => {
                                            if (entry.kind === "single") {
                                              const item = entry.item;
                                              const navIdx = navIndexByKey.get(
                                                `tree:${item.id}`
                                              );
                                              return (
                                                <PickerItemRow
                                                  key={entry.key}
                                                  item={item}
                                                  isSelected={item.id === selectedDrillId}
                                                  isKeyboardActive={
                                                    navIdx === activeKeyboardIndex
                                                  }
                                                  buttonRef={(el) =>
                                                    registerRowRef(navIdx, el)
                                                  }
                                                  onPick={handlePick}
                                                />
                                              );
                                            }

                                            return (
                                              <div
                                                key={entry.key}
                                                className={
                                                  entry.inlineInChapter
                                                    ? "space-y-1"
                                                    : "rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white/60 dark:bg-zinc-900/40 p-1.5 space-y-1"
                                                }
                                              >
                                                {!entry.inlineInChapter && (
                                                  <div className="px-1.5 pt-0.5 pb-0.5 space-y-0.5">
                                                    <div className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate">
                                                      {entry.unitTitle}
                                                    </div>
                                                    <div className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                                      {entry.unitCode}
                                                    </div>
                                                  </div>
                                                )}

                                                <div className="space-y-1">
                                                  {entry.items.map((setEntry) => {
                                                    const item = setEntry.item;
                                                    const isSelected =
                                                      item.id === selectedDrillId;
                                                    const navIdx = navIndexByKey.get(
                                                      `tree:${item.id}`
                                                    );
                                                    const isKeyboardActive =
                                                      navIdx === activeKeyboardIndex;

                                                    return (
                                                      <button
                                                        key={item.id}
                                                        ref={(el) =>
                                                          registerRowRef(navIdx, el)
                                                        }
                                                        type="button"
                                                        aria-current={
                                                          isSelected ? "true" : undefined
                                                        }
                                                        onClick={() => handlePick(item.id)}
                                                        className={`w-full text-left px-2.5 py-1.5 rounded-md border transition-colors flex items-center justify-between gap-3 ${
                                                          isSelected
                                                            ? "bg-zinc-100 dark:bg-zinc-800/90 border-indigo-600 dark:border-indigo-500"
                                                            : "bg-white/80 dark:bg-zinc-900/60 hover:bg-zinc-100 dark:hover:bg-zinc-800/70 border-transparent"
                                                        } ${
                                                          isKeyboardActive
                                                            ? "ring-2 ring-indigo-500/70 dark:ring-indigo-400/70"
                                                            : ""
                                                        }`}
                                                      >
                                                        <div className="min-w-0 flex items-baseline gap-1.5 truncate">
                                                          <span className="text-xs font-medium text-zinc-800 dark:text-zinc-200">
                                                            {setEntry.setLabel}
                                                          </span>
                                                          <span className="text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                                                            · {item.countLabel}
                                                          </span>
                                                        </div>

                                                        <StatusSummary
                                                          inline
                                                          practiceStatus={item.practiceStatus}
                                                          progressText={`${item.score}/${item.maxScore}`}
                                                        />
                                                      </button>
                                                    );
                                                  })}
                                                </div>
                                              </div>
                                            );
                                          })}
                                        </div>
                                      </Reveal>
                                    </div>
                                  );
                                })}
                              </div>
                            </Reveal>
                          </div>
                        );
                      })}
                    </div>
                  </section>
                </>
              )}
            </div>
          </m.div>
        )}
      </AnimatePresence>
    </div>
  );
};
