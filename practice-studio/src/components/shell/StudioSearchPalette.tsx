"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeftRight,
  CalendarDays,
  ClipboardCheck,
  Code2,
  Search,
  Sigma,
} from "lucide-react";
import { ListRow } from "@/components/ui/ListRow";
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
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
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
import { DrillRowActions } from "./DrillRowActions";

const types = [
  { value: "all", label: "All" },
  { value: "drill", label: "Drills" },
  { value: "lab", label: "Labs" },
  { value: "unit", label: "Units" },
] as const;

const workspaceIcons = { math: Sigma, code: Code2 };

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
  const triggerProps = {
    "aria-label": "Search",
    "aria-haspopup": "dialog" as const,
    "aria-keyshortcuts": shortcut === "⌘K" ? "Meta+K" : "Control+K",
    onClick,
  };
  const icon = <Search aria-hidden="true" className="size-space-4 shrink-0" />;
  if (!compact) {
    return (
      <ListRow
        {...triggerProps}
        data-sidebar-row="search"
        label="Search"
        leading={icon}
        touchTarget="expanded"
        trailing={<kbd aria-hidden="true" className="font-sans text-xs text-foreground-subtle">{shortcut}</kbd>}
        className={className}
      />
    );
  }

  const trigger = (
    <button
      {...triggerProps}
      type="button"
      className={cn(
        "inline-flex size-touch shrink-0 items-center justify-center gap-space-2 rounded-md text-sm text-foreground-control transition-colors duration-color ease-standard hover:bg-surface-selected/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent motion-reduce:transition-none dark:hover:bg-surface-selected/40 lg:size-control-sm",
        className
      )}
    >
      {icon}
    </button>
  );
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
  onResetDrill?: (id: string) => void;
  onDeleteDrill?: (id: string) => void;
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
  onResetDrill,
  onDeleteDrill,
}: Omit<StudioSearchPaletteProps, "open" | "onCloseAutoFocus">) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState<SearchType>("all");
  const [selectedId, setSelectedId] = useState("");
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
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
    const Icon = workspaceIcons[entry.workspace];
    const hasMenu = entry.kind === "drill" && onResetDrill && onDeleteDrill;
    const menuOpen = openMenuId === entry.id;
    const rowActive = selected === entry.id || menuOpen;
    return (
      <CommandItem
        key={entry.id}
        value={entry.id}
        onSelect={() => navigate(entry.href)}
        selected={rowActive}
        label={entry.title}
        leading={<Icon aria-hidden="true" className="size-space-4 shrink-0" />}
        trailing={hasMenu && (
          <DrillRowActions
            nodeId={entry.id}
            variant="search"
            tabIndex={rowActive ? 0 : -1}
            open={menuOpen}
            onTooltipEscape={onClose}
            onOpenChange={(open) => {
              if (open) setSelectedId(entry.id);
              setOpenMenuId(open ? entry.id : null);
            }}
            onReset={(id) => {
              onClose();
              onResetDrill(id);
            }}
            onDelete={(id) => {
              onClose();
              onDeleteDrill(id);
            }}
          />
        )}
      />
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
        const delta = event.key === "ArrowRight" ? 1 : -1;
        const edge = delta === 1 ? query.length : 0;
        const input = inputRef.current;
        if (query && (event.target !== input || input?.selectionStart !== edge ||
            input.selectionEnd !== edge)) return;
        event.preventDefault();
        const index = types.findIndex(({ value }) => value === type);
        selectType(types[(index + delta + types.length) % types.length].value);
      }}
    >
      <div className="flex min-h-control-lg shrink-0 items-center gap-space-3 pl-space-5 pr-space-12">
        <Search aria-hidden="true" className="size-space-4 shrink-0 text-muted" />
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
      <SegmentedChips
        label="Result type"
        options={types}
        value={type}
        onValueChange={selectType}
        className="border-b border-border px-space-3 pb-space-2"
      />
      <CommandList label="Search results" className="min-h-space-28 py-space-1_5">
        {due.length > 0 && <CommandGroup heading="Needs attention">{due.map(renderEntry)}</CommandGroup>}
        {!search && type === "all" && (dueLoading || dueError) && (
          <p role="status" className="px-space-5 pb-space-1 pt-space-2 text-sm text-muted">
            {dueLoading ? "Loading due reviews…" : "Due reviews could not be loaded."}
          </p>
        )}
        {recents.length > 0 && <CommandGroup heading="Recents">{recents.map(renderEntry)}</CommandGroup>}
        {results.length > 0 && <CommandGroup heading={resultsLabel}>{results.map(renderEntry)}</CommandGroup>}
        {actions.length > 0 && (
          <CommandGroup heading="Actions">
            {actions.map(({ id, title, icon: Icon, run }) => (
              <CommandItem
                key={id}
                value={id}
                onSelect={run}
                label={title}
                emphasis="normal"
                leading={<Icon aria-hidden="true" className="size-space-4 shrink-0" />}
              />
            ))}
          </CommandGroup>
        )}
        {loading ? (
          <CommandLoading label="Loading search results" className="px-space-5 py-space-5 text-sm text-muted">
            Loading practice items…
          </CommandLoading>
        ) : loadError ? (
          <p role="status" className="px-space-5 py-space-5 text-sm text-muted">
            Some practice items could not be loaded.
          </p>
        ) : ids.length === 0 && (
          <p role="status" className="px-space-5 py-space-5 text-sm text-muted">
            {search ? "No matching results." : `No ${resultsLabel?.toLowerCase()} in this workspace.`}
          </p>
        )}
      </CommandList>
      <div className="hidden shrink-0 flex-wrap items-center gap-x-space-4 gap-y-space-1 border-t border-border bg-surface-panel px-space-5 py-space-2 text-xs text-foreground-subtle sm:flex">
        {[
          ["Close", "Esc"],
          [query ? "Change type at text edges" : "Change type", "← →"],
          ["Open", "↵"],
        ].map(([label, key]) => (
          <span key={label} className="inline-flex items-center gap-space-1_5">
            {label}
            <kbd className="rounded border border-surface-selected px-space-1 font-sans">{key}</kbd>
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
        position="top"
        className="flex max-h-search max-w-search flex-col overflow-hidden bg-surface-raised p-space-0"
        closeButtonSize="xs"
        closeButtonClassName="right-space-4 top-space-2_5"
        overlayPreset="search"
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
