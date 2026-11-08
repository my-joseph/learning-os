import React from "react";
import { ArrowUpRight } from "lucide-react";
import { ReferenceBadge } from "@/types/drill";

export const NotionBadge: React.FC<{ badge: ReferenceBadge }> = ({ badge }) => {
  if (badge.notionUrl) {
    return (
      <a
        href={badge.notionUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sky-50 dark:bg-sky-500/10 text-sky-700 dark:text-sky-400 border border-sky-200 dark:border-sky-500/30 hover:bg-sky-100 dark:hover:bg-sky-500/20 transition-colors"
      >
        <ArrowUpRight className="w-3 h-3" />
        {badge.code} · {badge.title}
      </a>
    );
  }

  return (
    <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
      {badge.code}
    </span>
  );
};
