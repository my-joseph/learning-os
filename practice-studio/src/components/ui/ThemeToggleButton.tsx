import React from "react";
import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";

export function ThemeToggleButton({
  theme,
  onToggle,
  className,
}: {
  theme: "light" | "dark";
  onToggle: () => void;
  className: string;
}) {
  const label = theme === "light" ? "Switch to dark mode" : "Switch to light mode";

  return (
    <Button
      variant="ghost"
      size="iconSm"
      onClick={onToggle}
      title={label}
      aria-label={label}
      className={className}
    >
      {theme === "light" ? (
        <Moon className="w-4 h-4" />
      ) : (
        <Sun className="w-4 h-4" />
      )}
    </Button>
  );
}
