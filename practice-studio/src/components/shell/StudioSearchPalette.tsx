"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeftRight,
  BookOpen,
  CalendarDays,
  ClipboardCheck,
  FlaskConical,
  NotebookPen,
  Search,
} from "lucide-react";
import { Badge } from "@/components/ui/shadcn/Badge";
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandLoading,
} from "@/components/ui/shadcn/Command";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/shadcn/Dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/shadcn/Tooltip";
import { cn } from "@/lib/cn";
import { readRecentDrillIds } from "@/lib/lastDrillStorage";
import type { Workspace } from "@/lib/routes";
import {
  findSearchEntries,
  searchWorkspaceLabel,
  type SearchEntry,
  type SearchType,
} from "@/lib/studioSearch";

const types = [
  { value: "all", label: "All" },
  { value: "drill", label: "Drills" },
  { value: "lab", label: "Labs" },
  { value: "unit", label: "Units" },
] as const;

const icons = { drill: NotebookPen, lab: FlaskConical, unit: BookOpen };

export function useStudioSearchShortcut(onOpen: () => void) {
  const [isMac, setIsMac] = useState(false);

  useEffect(() => {
    setIsMac(navigator.platform.startsWith("Mac"));
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        event.defaultPrevented || event.repeat || event.isComposing ||
        !(event.metaKey || event.ctrlKey) || event.altKey || event.shiftKey ||
        event.key.toLowerCase() !== "k"
      ) return;
      event.preventDefault();
      onOpen();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onOpen]);

  return isMac ? "⌘K" : "Ctrl K";
}

export function StudioSearchTrigger({
  shortcut,
  onClick,
  compact = false,
  className,
}: {
  shortcut: string;
  onClick: () => void;
  compact?: boolean;
  className?: string;
}) {
  const trigger = (
    <button
      type="button"
      data-sidebar-row={compact ? undefined : "search"}
      aria-label="Search"
      aria-haspopup="dialog"
      aria-keyshortcuts={shortcut === "⌘K" ? "Meta+K" : "Control+K"}
      onClick={onClick}
      className={cn(
        "inline-flex shrink-0 items-center gap-2 rounded-md text-sm text-zinc-700 transition-colors hover:bg-zinc-200/50 focus-visible:outline-none motion-reduce:transition-none dark:text-zinc-300 dark:hover:bg-zinc-700/40",
        compact
          ? "size-11 justify-center focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 lg:size-8"
          : "h-8 w-full px-1.5 text-left",
        className
      )}
    >
      <Search aria-hidden="true" className="size-4 shrink-0" />
      {!compact && (
        <>
          <span className="flex-1">Search</span>
          <kbd aria-hidden="true" className="font-sans text-xs text-zinc-600 dark:text-zinc-400">
            {shortcut}
          </kbd>
        </>
      )}
    </button>
  );

  if (!compact) return trigger;
  return (
    <Tooltip>
      <TooltipTrigger asChild>{trigger}</TooltipTrigger>
      <TooltipContent side="bottom">Search ({shortcut})</TooltipContent>
    </Tooltip>
  );
}

interface SearchAction {
  id: string;
  title: string;
  icon: typeof CalendarDays;
  run: () => void;
}

interface StudioSearchPaletteProps {
  open: boolean;
  onClose: () => void;
  onCloseAutoFocus: (event: Event) => void;
  workspace: Workspace;
  entries: SearchEntry[];
  dueIds: readonly string[];
  loading: boolean;
  loadError: boolean;
  dueLoading: boolean;
  dueError: boolean;
  reviewHref: string;
  switchHref: string | null;
  onReviewSync?: () => void;
  onNavigate: (href: string) => void;
}

function EnterHint() {
  return (
    <kbd aria-hidden="true" className="invisible ml-auto shrink-0 font-sans text-xs text-zinc-600 group-data-[selected=true]:visible dark:text-zinc-400">
      ↵
    </kbd>
  );
}

function SearchResults({
  onClose,
  workspace,
  entries,
  dueIds,
  loading,
  loadError,
  dueLoading,
  dueError,
  reviewHref,
  switchHref,
  onReviewSync,
  onNavigate,
}: Omit<StudioSearchPaletteProps, "open" | "onCloseAutoFocus">) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState<SearchType>("all");
  const [selectedId, setSelectedId] = useState("");
  const otherWorkspace = workspace === "math" ? "code" : "math";
  const [recentIds] = useState(() => [
    ...readRecentDrillIds(workspace),
    ...readRecentDrillIds(otherWorkspace),
  ]);
  const inputRef = useRef<HTMLInputElement>(null);
  const search = query.trim();
  const matches = useMemo(
    () => findSearchEntries(entries, search, type, workspace),
    [entries, search, type, workspace]
  );
  const matchById = new Map(matches.map((entry) => [entry.id, entry]));
  const dueSet = new Set(dueIds);
  const due = search ? [] : Array.from(dueSet).flatMap((id) => {
    const entry = matchById.get(id);
    return entry?.workspace === workspace ? [entry] : [];
  });
  const recents = search ? [] : recentIds.flatMap((id) => {
    const entry = matchById.get(id);
    return entry && !dueSet.has(id) && entry.kind !== "unit" ? [entry] : [];
  });
  const seen = new Set([...due, ...recents].map((entry) => entry.id));
  const results = search || type !== "all"
    ? matches.filter((entry) => !seen.has(entry.id))
    : [];

  const navigate = (href: string) => {
    onClose();
    onNavigate(href);
  };

  const actions: SearchAction[] = [];
  if (!search && type === "all") {
    actions.push({
      id: "daily-review",
      title: "Daily review",
      icon: CalendarDays,
      run: () => navigate(reviewHref),
    });
    if (onReviewSync) {
      actions.push({
        id: "review-sync",
        title: "Review & Sync",
        icon: ClipboardCheck,
        run: () => {
          onClose();
          onReviewSync();
        },
      });
    }
    if (switchHref) {
      actions.push({
        id: "switch-workspace",
        title: `Switch to ${searchWorkspaceLabel[otherWorkspace]}`,
        icon: ArrowLeftRight,
        run: () => navigate(switchHref),
      });
    }
  }

  const ids = [...due, ...recents, ...results, ...actions].map((entry) => entry.id);
  const selected = ids.includes(selectedId) ? selectedId : ids[0] ?? "";
  const resultsLabel = type === "all" ? "Results" : types.find(({ value }) => value === type)?.label;

  const selectType = (next: SearchType) => {
    setType(next);
    setSelectedId("");
    inputRef.current?.focus();
  };

  const renderEntry = (entry: SearchEntry) => {
    const Icon = icons[entry.kind];
    return (
      <CommandItem key={entry.id} value={entry.id} onSelect={() => navigate(entry.href)}>
        <Icon aria-hidden="true" className="size-4 shrink-0 text-zinc-500 dark:text-zinc-400" />
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">{entry.title}</span>
          <span className="block truncate font-display text-xs text-zinc-600 dark:text-zinc-400">
            {entry.context}
          </span>
        </span>
        {entry.workspace !== workspace && (
          <Badge variant="outline" className="shrink-0 text-zinc-600 dark:text-zinc-300">
            {searchWorkspaceLabel[entry.workspace]}
          </Badge>
        )}
        <EnterHint />
      </CommandItem>
    );
  };

  return (
    <Command
      label="Search Practice Studio"
      value={selected}
      onValueChange={setSelectedId}
      shouldFilter={false}
      loop
      vimBindings={false}
      className="flex min-h-0 flex-col"
      onKeyDown={(event) => {
        if (event.nativeEvent.isComposing || event.altKey || event.ctrlKey ||
            event.metaKey || event.shiftKey) return;
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        const index = types.findIndex(({ value }) => value === type);
        const delta = event.key === "ArrowRight" ? 1 : -1;
        selectType(types[(index + delta + types.length) % types.length].value);
      }}
    >
      <div className="flex min-h-12 shrink-0 items-center gap-3 pl-4 pr-16">
        <Search aria-hidden="true" className="size-4 shrink-0 text-zinc-500 dark:text-zinc-400" />
        <CommandInput
          ref={inputRef}
          autoComplete="off"
          placeholder="Search drills, labs, and units"
          value={query}
          onValueChange={(value) => {
            setQuery(value);
            setSelectedId("");
          }}
        />
      </div>
      <div role="group" aria-label="Result type" className="flex shrink-0 gap-1 border-b border-zinc-200 px-3 pb-2 dark:border-zinc-800 sm:gap-2">
        {types.map(({ value, label }) => (
          <button
            key={value}
            type="button"
            aria-pressed={value === type}
            onClick={() => selectType(value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") event.stopPropagation();
            }}
            className="min-h-11 rounded-md px-3 text-sm text-zinc-600 transition-colors hover:bg-zinc-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-600 aria-pressed:bg-zinc-200/70 aria-pressed:font-medium aria-pressed:text-zinc-900 motion-reduce:transition-none dark:text-zinc-400 dark:hover:bg-zinc-800 dark:focus-visible:ring-indigo-400 dark:aria-pressed:bg-zinc-700/70 dark:aria-pressed:text-zinc-100 sm:min-h-8"
          >
            {label}
          </button>
        ))}
      </div>
      <CommandList label="Search results" className="min-h-28 py-1.5">
        {due.length > 0 && <CommandGroup heading="Needs attention">{due.map(renderEntry)}</CommandGroup>}
        {!search && type === "all" && (dueLoading || dueError) && (
          <p role="status" className="px-4 pb-1 pt-2 text-sm text-zinc-500 dark:text-zinc-400">
            {dueLoading ? "Loading due reviews…" : "Due reviews could not be loaded."}
          </p>
        )}
        {recents.length > 0 && <CommandGroup heading="Recents">{recents.map(renderEntry)}</CommandGroup>}
        {results.length > 0 && <CommandGroup heading={resultsLabel}>{results.map(renderEntry)}</CommandGroup>}
        {actions.length > 0 && (
          <CommandGroup heading="Actions">
            {actions.map(({ id, title, icon: Icon, run }) => (
              <CommandItem key={id} value={id} onSelect={run}>
                <Icon aria-hidden="true" className="size-4 shrink-0 text-zinc-500 dark:text-zinc-400" />
                {title}
                <EnterHint />
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {loading ? (
          <CommandLoading label="Loading search results" className="px-4 py-5 text-sm text-zinc-500 dark:text-zinc-400">
            Loading practice items…
          </CommandLoading>
        ) : loadError ? (
          <p role="status" className="px-4 py-5 text-sm text-zinc-500 dark:text-zinc-400">
            Some practice items could not be loaded.
          </p>
        ) : ids.length === 0 && (
          <p role="status" className="px-4 py-5 text-sm text-zinc-500 dark:text-zinc-400">
            {search ? "No matching results." : `No ${resultsLabel?.toLowerCase()} in this workspace.`}
          </p>
        )}
      </CommandList>
      <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1 border-t border-zinc-200 bg-surface-panel px-4 py-2 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
        {[
          ["Close", "Esc"],
          ["Change type", "← →"],
          ["Open", "↵"],
        ].map(([label, key]) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            {label}
            <kbd className="rounded border border-zinc-200 px-1 font-sans dark:border-zinc-700">{key}</kbd>
          </span>
        ))}
      </div>
    </Command>
  );
}

export function StudioSearchPalette({ open, onClose, onCloseAutoFocus, ...props }: StudioSearchPaletteProps) {
  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next) onClose(); }}>
      <DialogContent
        className="flex max-h-[min(40rem,calc(100dvh-2rem))] max-w-xl flex-col overflow-hidden bg-white p-0 dark:bg-background [&>button]:right-2 [&>button]:top-0.5"
        onCloseAutoFocus={onCloseAutoFocus}
      >
        <DialogTitle className="sr-only">Search Practice Studio</DialogTitle>
        <DialogDescription className="sr-only">
          Find a drill, lab, unit, or practice action.
        </DialogDescription>
        {open && <SearchResults {...props} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  );
}
