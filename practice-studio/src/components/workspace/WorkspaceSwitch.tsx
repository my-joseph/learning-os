"use client";

import React from "react";
import Link from "next/link";
import { m } from "motion/react";
import { Code2, Sigma, type LucideIcon } from "lucide-react";
import { settle } from "@/lib/motion";
import { Workspace } from "@/lib/routes";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";

export interface WorkspaceSwitchProps {
  variant: "rail" | "header" | "sidebar";
  workspace: Workspace;
  pillWorkspace: Workspace;
  onSelectWorkspace: (workspace: Workspace) => void;
  mathHref: string | null;
  codeHref: string | null;
  className?: string;
}

/** Shared icon-only Math / Programming segmented workspace switcher (vertical rail, compact header, and sidebar). */
export const WorkspaceSwitch: React.FC<WorkspaceSwitchProps> = ({
  variant,
  workspace,
  pillWorkspace,
  onSelectWorkspace,
  mathHref,
  codeHref,
  className,
}) => {
  const options: {
    id: Workspace;
    label: string;
    href: string | null;
    icon: LucideIcon;
  }[] = [
    { id: "math", label: "Math", href: mathHref, icon: Sigma },
    { id: "code", label: "Programming", href: codeHref, icon: Code2 },
  ];

  const isRail = variant === "rail";
  const isSidebar = variant === "sidebar";

  const defaultNavClassName = isRail
    ? "hidden lg:grid fixed left-3 top-1/2 -translate-y-1/2 z-40 grid-rows-2 items-center rounded-xl bg-zinc-100/95 dark:bg-zinc-800/80 backdrop-blur-md border border-zinc-200 dark:border-zinc-800 p-1 shadow-sm"
    : isSidebar
    ? "relative grid min-h-[44px] grid-cols-2 items-center rounded-lg bg-zinc-200/70 dark:bg-zinc-900/75 p-0.5 shrink-0 lg:h-9"
    : "relative grid lg:hidden grid-cols-2 items-center rounded-lg bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-800 p-0.5 shrink-0";

  const pillClassName = isRail
    ? "pointer-events-none absolute left-1 right-1 top-1 h-[calc(50%-4px)] rounded-lg bg-white dark:bg-zinc-900 shadow-sm"
    : isSidebar
    ? "pointer-events-none absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-white dark:bg-zinc-700/80 shadow-sm"
    : "pointer-events-none absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-white dark:bg-zinc-900 shadow-sm";

  const pillAnimate = isRail
    ? { y: pillWorkspace === "code" ? "100%" : "0%" }
    : { x: pillWorkspace === "code" ? "100%" : "0%" };

  const itemSizeCls = isRail
    ? "w-8 h-8 rounded-lg"
    : isSidebar
    ? "min-h-[44px] min-w-[44px] lg:min-h-9 lg:min-w-9 lg:w-9 lg:h-9 rounded-md"
    : "w-7 h-7 sm:w-8 sm:h-8 rounded-md";

  const tooltipSide = isRail ? "right" : "bottom";

  return (
    <nav aria-label="Workspace" className={className ?? defaultNavClassName}>
      <m.span
        aria-hidden
        className={pillClassName}
        initial={false}
        animate={pillAnimate}
        transition={settle}
      />
      {options.map((opt) => {
        const isActive = workspace === opt.id;
        const isShown = pillWorkspace === opt.id;
        const Icon = opt.icon;
        const cls = `relative z-10 inline-flex items-center justify-center ${itemSizeCls} transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 ${
          isShown
            ? "text-zinc-900 dark:text-zinc-100"
            : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200"
        }`;

        if (!opt.href) {
          return (
            <Tooltip key={opt.id}>
              <TooltipTrigger asChild>
                <span
                  aria-label={opt.label}
                  aria-current={isActive ? "page" : undefined}
                  aria-disabled={!isActive ? true : undefined}
                  className={`${cls} ${!isActive ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <Icon className="w-4 h-4 shrink-0" aria-hidden={true} />
                </span>
              </TooltipTrigger>
              <TooltipContent side={tooltipSide}>{opt.label}</TooltipContent>
            </Tooltip>
          );
        }
        return (
          <Tooltip key={opt.id}>
            <TooltipTrigger asChild>
              <Link
                href={opt.href}
                aria-label={opt.label}
                aria-current={isActive ? "page" : undefined}
                onClick={() => onSelectWorkspace(opt.id)}
                className={cls}
              >
                <Icon className="w-4 h-4 shrink-0" aria-hidden={true} />
              </Link>
            </TooltipTrigger>
            <TooltipContent side={tooltipSide}>{opt.label}</TooltipContent>
          </Tooltip>
        );
      })}
    </nav>
  );
};
