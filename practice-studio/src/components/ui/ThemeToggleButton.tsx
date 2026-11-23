"use client";

import React from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";
import { cn } from "@/lib/cn";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/shadcn/Tooltip";

export function ThemeToggleButton({
  theme,
  onToggle,
  className,
}: {
  theme: "light" | "dark";
  onToggle: () => void;
  className?: string;
}) {
  const label = theme === "light" ? "Switch to dark mode" : "Switch to light mode";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="iconSm"
          onClick={onToggle}
          aria-label={label}
          className={cn("rounded-lg", className)}
        >
          {theme === "light" ? (
            <Moon className="w-4 h-4" aria-hidden="true" />
          ) : (
            <Sun className="w-4 h-4" aria-hidden="true" />
          )}
        </Button>
      </TooltipTrigger>
      <TooltipContent side="bottom">{label}</TooltipContent>
    </Tooltip>
  );
}
