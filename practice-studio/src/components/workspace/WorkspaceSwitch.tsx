"use client";

import React from "react";
import Link from "next/link";
import { Code2, Sigma, type LucideIcon } from "lucide-react";
import { Workspace } from "@/lib/routes";
import { SegmentedNav, SegmentedNavItem } from "@/components/ui/shadcn/Tabs";
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

  return (
    <SegmentedNav
      aria-label="Workspace"
      variant={variant}
      activeIndex={pillWorkspace === "code" ? 1 : 0}
      className={className}
    >
      {options.map((opt) => {
        const isActive = workspace === opt.id;
        const Icon = opt.icon;
        const icon = <Icon className="size-space-4 shrink-0" aria-hidden />;
        const nameProps = { "aria-label": opt.label, "aria-current": isActive ? "page" as const : undefined };
        return (
          <Tooltip key={opt.id}>
            <TooltipTrigger asChild>
              <SegmentedNavItem selected={pillWorkspace === opt.id}>
                {opt.href ? (
                  <Link {...nameProps} href={opt.href} onClick={() => onSelectWorkspace(opt.id)}>
                    {icon}
                  </Link>
                ) : (
                  <span {...nameProps} aria-disabled={!isActive || undefined}>{icon}</span>
                )}
              </SegmentedNavItem>
            </TooltipTrigger>
            <TooltipContent side={variant === "rail" ? "right" : "bottom"}>{opt.label}</TooltipContent>
          </Tooltip>
        );
      })}
    </SegmentedNav>
  );
};
