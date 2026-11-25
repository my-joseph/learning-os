import { defaultFilter } from "cmdk";
import { normalizeDrillPickerItems, normalizeLabPickerItems } from "./drillGrouping";
import { drillHref, subjectOf, type Workspace } from "./routes";
import type { DrillListItem } from "@/types/drill";
import type { LabListItem } from "./labModel";

export type SearchKind = "drill" | "lab" | "unit";
export type SearchType = "all" | SearchKind;

export interface SearchEntry {
  id: string;
  title: string;
  kind: SearchKind;
  context: string;
  chapterCode: string;
  workspace: Workspace;
  href: string;
}

export function buildSearchEntries(
  drills: readonly DrillListItem[],
  labs: readonly LabListItem[]
): SearchEntry[] {
  const entries: SearchEntry[] = [];
  const units = new Map<string, { entry: SearchEntry; createdAt: string }>();
  const items = [...normalizeDrillPickerItems(drills), ...normalizeLabPickerItems(labs)];

  for (const item of items) {
    const workspace = subjectOf(item.id);
    if (!workspace) continue;
    const href = drillHref(item.id);
    entries.push({
      id: item.id,
      title: item.setLabel ? `${item.title} · ${item.setLabel}` : item.title,
      kind: item.kind,
      context: item.unitCode,
      chapterCode: item.chapterCode,
      workspace,
      href,
    });

    if (!/^[A-Z]+-T\d+-C\d+-U\d+$/i.test(item.unitCode)) continue;
    const previous = units.get(item.unitCode);
    if (previous && previous.createdAt >= item.createdAt) continue;
    units.set(item.unitCode, {
      createdAt: item.createdAt,
      entry: {
        id: item.unitCode,
        title: item.kind === "drill" ? item.title : item.unitTitle || item.unitCode,
        kind: "unit",
        context: item.unitCode,
        chapterCode: item.chapterCode,
        workspace,
        href,
      },
    });
  }
  return [...entries, ...Array.from(units.values(), ({ entry }) => entry)];
}

export const searchWorkspaceLabel: Record<Workspace, string> = {
  math: "Math",
  code: "Program",
};

export function findSearchEntries(
  entries: readonly SearchEntry[],
  query: string,
  type: SearchType,
  workspace: Workspace
): SearchEntry[] {
  const candidates = type === "all"
    ? entries
    : entries.filter((entry) => entry.workspace === workspace && entry.kind === type);

  return candidates
    .map((entry) => ({
      entry,
      score: query
        ? defaultFilter(entry.id, query, [entry.title, entry.context, entry.chapterCode])
        : 1,
    }))
    .filter(({ score }) => score > 0)
    .sort((a, b) =>
      b.score - a.score ||
      Number(b.entry.workspace === workspace) - Number(a.entry.workspace === workspace)
    )
    .map(({ entry }) => entry);
}
